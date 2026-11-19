"""Office-library interoperability checks against real generated OOXML files."""
from office_sanitizer.core import sanitize
from office_sanitizer.verify import verify_output
import pytest


def _check(source, output):
    result = sanitize(source, output)
    assert result.status == 'metadata_cleaned_content_unreviewed'
    assert verify_output(source, output).status == 'package_integrity_verified_content_unreviewed'


def test_real_word_document_roundtrip(tmp_path):
    docx = pytest.importorskip('docx')
    source, output = tmp_path/'word.docx', tmp_path/'word-clean.docx'
    doc = docx.Document()
    doc.add_paragraph('Safe Word round-trip fixture')
    doc.save(source)
    _check(source, output)
    assert 'Safe Word round-trip fixture' in '\n'.join(p.text for p in docx.Document(output).paragraphs)


def test_real_excel_workbook_roundtrip(tmp_path):
    openpyxl = pytest.importorskip('openpyxl')
    source, output = tmp_path/'book.xlsx', tmp_path/'book-clean.xlsx'
    wb = openpyxl.Workbook()
    wb.active['A1'] = 'Safe Excel round-trip fixture'
    wb.active['B2'] = '=1+2'
    wb.save(source)
    _check(source, output)
    result = openpyxl.load_workbook(output)
    assert result.active['A1'].value == 'Safe Excel round-trip fixture'
    assert result.active['B2'].value == '=1+2'


def test_real_powerpoint_deck_roundtrip(tmp_path):
    pptx = pytest.importorskip('pptx')
    source, output = tmp_path/'slides.pptx', tmp_path/'slides-clean.pptx'
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = 'Safe PowerPoint round-trip fixture'
    presentation.save(source)
    _check(source, output)
    reread = pptx.Presentation(output)
    assert reread.slides[0].shapes.title.text == 'Safe PowerPoint round-trip fixture'
