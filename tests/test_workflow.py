import zipfile

from office_sanitizer.workflow import guarded_sanitize
from test_core import fixture


def test_guarded_success_requires_review(tmp_path):
    src, dst = tmp_path / 'in.docx', tmp_path / 'out.docx'
    fixture(src)
    result = guarded_sanitize(src, dst)
    assert result.status == 'metadata_only_copy_requires_human_review'
    assert result.verified and dst.exists() and src.exists()
    assert result.after_findings.get('metadata_parts', 0) == 0
    assert 'not_a_confidentiality_clearance' in result.reason_codes
    assert str(tmp_path) not in str(result.as_dict())


def test_guarded_rejects_macro_without_modifying(tmp_path):
    src, dst = tmp_path / 'in.docm', tmp_path / 'out.docm'
    fixture(src, macro=True)
    original = src.read_bytes()
    result = guarded_sanitize(src, dst)
    assert result.status == 'blocked'
    assert 'preflight_indicators_require_review' in result.reason_codes
    assert src.read_bytes() == original and not dst.exists()


def test_guarded_rejects_sensitive_content(tmp_path):
    src, dst = tmp_path / 'in.docx', tmp_path / 'out.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('word/sensitive.xml', '<p>john.doe@example.com</p>')
    result = guarded_sanitize(src, dst)
    assert result.status == 'blocked' and not dst.exists()
    assert result.before_findings['email_addresses'] == 1
    assert 'john.doe@example.com' not in str(result.as_dict())


def test_guarded_rejects_existing_output(tmp_path):
    src, dst = tmp_path / 'in.docx', tmp_path / 'out.docx'
    fixture(src)
    dst.write_bytes(b'KEEP')
    assert guarded_sanitize(src, dst).status == 'blocked'
    assert dst.read_bytes() == b'KEEP'


def test_guarded_rejects_invalid_input(tmp_path):
    src, dst = tmp_path / 'bad.docx', tmp_path / 'out.docx'
    src.write_bytes(b'not zip')
    result = guarded_sanitize(src, dst)
    assert result.status == 'blocked' and not dst.exists()
    assert 'preflight_incomplete' in result.reason_codes


def test_audit_opaque_package_part_names(tmp_path):
    from office_sanitizer.audit import scan_ooxml
    src = tmp_path / 'private.docx'
    fixture(src)
    with zipfile.ZipFile(src, 'a') as z:
        z.writestr('word/embeddings/secret-person-name.bin', b'embedded')
    report = scan_ooxml(src).as_dict()
    assert report['findings']['embedded_objects'] == 1
    assert 'secret-person-name' not in str(report)
    assert all(part.startswith('part:') for part in report['flagged_parts'])
