import zipfile
from office_sanitizer.core import sanitize
from office_sanitizer.verify import verify_output
from test_core import fixture


def test_valid_sanitization_roundtrip(tmp_path):
    src, dst = tmp_path / 'a.docm', tmp_path / 'out.docm'
    fixture(src, macro=True)
    result = sanitize(src, dst)
    assert result.verified
    checked = verify_output(src, dst)
    assert checked.status == 'package_integrity_verified_content_unreviewed'
    assert checked.removed_metadata_parts == 1


def test_detects_mutated_macro(tmp_path):
    src, dst = tmp_path / 'a.docm', tmp_path / 'out.docm'
    fixture(src, macro=True)
    with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w') as w:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == 'word/vbaProject.bin':
                data = b'different'
            if info.filename == 'docProps/core.xml':
                continue
            w.writestr(info, data)
    assert verify_output(src, dst).status == 'failed'


def test_detects_extra_hidden_part(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'out.docx'
    fixture(src)
    with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w') as w:
        for info in z.infolist():
            if info.filename != 'docProps/core.xml':
                w.writestr(info, z.read(info.filename))
        w.writestr('extra.bin', b'private')
    assert verify_output(src, dst).status == 'failed'


def test_detects_dangling_target(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'out.docx'
    fixture(src)
    with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w') as w:
        for info in z.infolist():
            if info.filename != 'docProps/core.xml':
                w.writestr(info, z.read(info.filename))
    assert verify_output(src, dst).status == 'failed'


def test_missing_files_fail_closed(tmp_path):
    assert verify_output(tmp_path / 'missing.docx', tmp_path / 'other.docx').status == 'failed'


def test_never_overwrite_existing_output(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'existing.docx'
    fixture(src)
    dst.write_bytes(b'keep')
    assert sanitize(src, dst).status == 'failed'
    assert dst.read_bytes() == b'keep'


def test_signed_package_rejected(tmp_path):
    src, dst = tmp_path / 'a.docx', tmp_path / 'output.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('_xmlsignatures/sig1.xml', '<Signature/>')
    assert sanitize(src, dst).status == 'failed'
    assert not dst.exists()
