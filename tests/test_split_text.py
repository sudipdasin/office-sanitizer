"""Audit risks that span formatted OOXML runs, without leaking values."""
import zipfile
from office_sanitizer.audit import scan_ooxml
from office_sanitizer.workflow import guarded_sanitize
from test_core import fixture

def test_split_email_detected(tmp_path):
    src = tmp_path / "input.docx"
    fixture(src)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr("word/split.xml", "<p><t>janet.</t><t>private@example</t><t>.org</t></p>")
    result = scan_ooxml(src)
    assert result.status == "review_required"
    assert result.findings["email_addresses"] == 1
    assert "janet.private@example.org" not in str(result.as_dict())

def test_split_email_blocks_guarded(tmp_path):
    src, dst = tmp_path / "input.docx", tmp_path / "output.docx"
    fixture(src)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr("word/split.xml", "<p><t>janet</t><t>@example.org</t></p>")
    assert guarded_sanitize(src, dst).status == "blocked"
    assert not dst.exists()

def test_confidentiality_marking_across_runs(tmp_path):
    src = tmp_path / "input.docx"
    fixture(src)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr("word/marking.xml", "<p><t>CONFI</t><t>DENTIAL</t></p>")
    result = scan_ooxml(src)
    assert result.status == "review_required"
    assert result.findings["classification_marking_candidates"] == 1

def test_marking_does_not_leak(tmp_path):
    src = tmp_path / "input.docx"
    fixture(src)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr("word/marking.xml", "<p><t>TOP SECRET NOFORN</t></p>")
    report = scan_ooxml(src).as_dict()
    assert report["findings"]["classification_marking_candidates"] >= 1
    assert "TOP SECRET" not in str(report)

def test_sensitive_attribute_scanned(tmp_path):
    src = tmp_path / "input.docx"
    fixture(src)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr("word/attr.xml", '<p who="sensitive@example.com"/>')
    assert scan_ooxml(src).findings["email_addresses"] == 1
