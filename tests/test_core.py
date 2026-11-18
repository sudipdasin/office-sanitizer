from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET
from office_sanitizer.core import sanitize, RELS_NS, CONTENT_NS


def fixture(path, macro=False, malicious=False):
    names = {
        '[Content_Types].xml': f'''<?xml version="1.0"?><Types xmlns="{CONTENT_NS}"><Override PartName="/docProps/core.xml" ContentType="a"/><Override PartName="/word/document.xml" ContentType="b"/></Types>''',
        '_rels/.rels': f'''<?xml version="1.0"?><Relationships xmlns="{RELS_NS}"><Relationship Id="x" Type="t" Target="docProps/core.xml"/><Relationship Id="y" Type="t" Target="word/document.xml"/></Relationships>''',
        'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>',
        'docProps/core.xml': '<private>Author Name</private>',
    }
    if macro:
        names['word/vbaProject.bin'] = b'fictional-macro-content\x00\xff'
    if malicious:
        names['../escape'] = 'bad'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, value in names.items():
            z.writestr(name, value)


def test_sanitize_metadata_and_keep_macro(tmp_path):
    src, dst = tmp_path / 'a.docm', tmp_path / 'output' / 'a.docm'
    fixture(src, macro=True)
    original = src.read_bytes()
    r = sanitize(src, dst)
    assert r.verified and r.status == 'metadata_cleaned_content_unreviewed'
    assert src.read_bytes() == original
    with zipfile.ZipFile(dst) as z:
        assert 'docProps/core.xml' not in z.namelist()
        assert z.read('word/vbaProject.bin') == b'fictional-macro-content\x00\xff'
        rels = ET.fromstring(z.read('_rels/.rels'))
        assert len(rels) == 1
    assert r.macro_sha256_before == r.macro_sha256_after


def test_legacy_rejected_no_fake_success(tmp_path):
    src, dst = tmp_path / 'a.doc', tmp_path / 'result.doc'
    src.write_bytes(b'legacy')
    r = sanitize(src, dst)
    assert r.status == 'failed' and not dst.exists()


def test_reject_traversal(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'clean.docx'
    fixture(src, malicious=True)
    r = sanitize(src, dst)
    assert not r.verified and not dst.exists()


def test_reject_inplace(tmp_path):
    src = tmp_path / 'a.docx'
    fixture(src)
    assert sanitize(src, src).status == 'failed'


def test_malformed_manifest_rejected(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'clean.docx'
    with zipfile.ZipFile(src, 'w') as z:
        z.writestr('[Content_Types].xml', '<broken')
        z.writestr('_rels/.rels', '<a/>')
    assert sanitize(src, dst).status == 'failed'
    assert not dst.exists()


def test_reports_redact_local_path(tmp_path):
    src, dst = tmp_path / 'private.docx', tmp_path / 'out.docx'
    fixture(src)
    r = sanitize(src, dst)
    assert str(tmp_path) not in str(r.public_dict())
