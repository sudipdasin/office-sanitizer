"""Regression coverage for residual ZIP-container metadata (not OOXML XML)."""
import zipfile

from office_sanitizer.audit import scan_ooxml
from office_sanitizer.core import sanitize
from office_sanitizer.verify import verify_output
from office_sanitizer.workflow import guarded_sanitize
from test_core import fixture


def _source_with_zip_metadata(path):
    fixture(path)
    with zipfile.ZipFile(path, 'a') as z:
        z.comment = b'private archive comment: person@example.com'
    duplicate = path.with_suffix('.repacked')
    with zipfile.ZipFile(path) as original, zipfile.ZipFile(duplicate, 'w') as z:
        z.comment = original.comment
        for info in original.infolist():
            meta = zipfile.ZipInfo(info.filename, date_time=(2021, 5, 6, 7, 8, 10))
            meta.comment = b'private member comment'
            meta.extra = b'\x01\x00\x00\x00'
            z.writestr(meta, original.read(info.filename))
    duplicate.replace(path)


def test_scrub_zip_comments_extras_and_times(tmp_path):
    original, cleaned = tmp_path / 'input.docx', tmp_path / 'output.docx'
    _source_with_zip_metadata(original)
    previous_bytes = original.read_bytes()
    assert sanitize(original, cleaned).verified
    assert original.read_bytes() == previous_bytes
    with zipfile.ZipFile(cleaned) as z:
        assert z.comment == b''
        assert all(not i.comment and not i.extra and i.date_time == (1980, 1, 1, 0, 0, 0)
                   for i in z.infolist())
    assert verify_output(original, cleaned).status == 'package_integrity_verified_content_unreviewed'


def test_audit_flags_zip_metadata_without_echo(tmp_path):
    source = tmp_path / 'input.docx'
    _source_with_zip_metadata(source)
    report = scan_ooxml(source)
    assert report.status == 'review_required'
    assert report.findings['zip_archive_comment'] == 1
    assert report.findings['zip_member_comments'] >= 1
    assert report.findings['zip_member_extra_fields'] >= 1
    assert report.findings['zip_member_timestamps'] >= 1
    assert 'person@example.com' not in str(report.as_dict())


def test_guarded_mode_safely_scrubs_removable_zip_metadata(tmp_path):
    src, dst = tmp_path / 'input.docx', tmp_path / 'clean.docx'
    _source_with_zip_metadata(src)
    result = guarded_sanitize(src, dst)
    assert result.status == 'metadata_only_copy_requires_human_review' and dst.exists()


def test_audit_detects_sensitive_filename_without_disclosure(tmp_path):
    src = tmp_path / 'input.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('word/special-person@example.com.bin', b'placeholder')
    result = scan_ooxml(src)
    assert result.findings.get('zip_filename_email_addresses') == 1
    assert 'special-person@example.com' not in str(result.as_dict())


def test_public_cleanup_report_omits_member_names(tmp_path):
    src, dst = tmp_path / 'input.docx', tmp_path / 'clean.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('docProps/thumbnail.private-person@example.com', b'fake thumb')
    result = sanitize(src, dst)
    assert result.verified
    assert 'private-person@example.com' not in str(result.public_dict())
    assert result.public_dict()['removed_part_count'] >= 2
