"""Library-generated Office files: no Office application or untrusted macros executed."""
import pytest
from office_sanitizer.audit import scan_ooxml
from office_sanitizer.workflow import guarded_sanitize


def test_real_hidden_excel_sheet_blocks_guarded(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    source, dest = tmp_path/'real.xlsx', tmp_path/'copy.xlsx'
    wb = openpyxl.Workbook()
    wb.create_sheet('Restricted')
    wb['Restricted'].sheet_state = 'veryHidden'
    wb.save(source)
    report = scan_ooxml(source)
    assert report.findings['excel_hidden_sheets'] == 1
    assert guarded_sanitize(source, dest).status == 'blocked'
    assert not dest.exists()


def test_real_powerpoint_notes_detected(tmp_path):
    pptx = pytest.importorskip('pptx')
    source = tmp_path/'slides.pptx'
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.notes_slide.notes_text_frame.text = 'CONFIDENTIAL client review'
    presentation.save(source)
    report = scan_ooxml(source)
    assert report.findings['powerpoint_notes_parts'] >= 1
    assert report.findings['classification_marking_candidates'] >= 1
    assert 'client review' not in str(report.as_dict())
