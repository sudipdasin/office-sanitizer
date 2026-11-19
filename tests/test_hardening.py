import stat
import zipfile

from office_sanitizer.audit import scan_ooxml
from office_sanitizer.core import sanitize
from office_sanitizer.verify import verify_output
from test_core import fixture


def test_symlink_archive_rejected_everywhere(tmp_path):
    src, dst = tmp_path / 'source.docx', tmp_path / 'clean.docx'
    fixture(src)
    link = zipfile.ZipInfo('word/shortcut')
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr(link, 'secret.docx')
    assert scan_ooxml(src).status == 'incomplete'
    assert sanitize(src, dst).status == 'failed'
    assert not dst.exists()


def test_windows_drive_like_zip_entry_rejected(tmp_path):
    src, dst = tmp_path / 'source.docx', tmp_path / 'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('C:secret.xml', '<x/>')
    assert scan_ooxml(src).status == 'incomplete'
    assert sanitize(src, dst).status == 'failed'


def test_signed_package_audit_flags_and_cleaner_refuses(tmp_path):
    src, dst = tmp_path / 'source.docx', tmp_path / 'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('_xmlsignatures/sig1.xml', '<Signature/>')
    assert scan_ooxml(src).findings['digitally_signed_package'] == 1
    assert sanitize(src, dst).status == 'failed'


def test_error_reports_do_not_echo_sensitive_zip_names(tmp_path):
    src, dst = tmp_path / 'source.docx', tmp_path / 'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('../private-person@example.com.xml', '<x/>')
    r = sanitize(src, dst)
    assert r.status == 'failed'
    assert 'private-person@example.com' not in str(r.public_dict())


def test_verification_rejects_signature_in_original(tmp_path):
    src, dst = tmp_path / 'source.docx', tmp_path / 'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('_xmlsignatures/sig1.xml', '<Signature/>')
    with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w') as w:
        for info in z.infolist():
            if info.filename != 'docProps/core.xml':
                w.writestr(info, z.read(info.filename))
    assert verify_output(src, dst).status == 'failed'
