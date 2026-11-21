import zipfile
from office_sanitizer.audit import scan_ooxml
from office_sanitizer.workflow import guarded_sanitize
from test_core import fixture


def add(src, payload):
    with zipfile.ZipFile(src, 'a') as z:
        for k, v in payload.items():
            z.writestr(k, v)


def test_hidden_excel_sheet_and_rows(tmp_path):
    src = tmp_path/'file.xlsx'; fixture(src)
    add(src, {
        'xl/workbook.xml': '<workbook><sheets><sheet state="veryHidden"/></sheets></workbook>',
        'xl/worksheets/sheet1.xml': '<worksheet><row hidden="1"/><cols><col hidden="true"/></cols></worksheet>',
    })
    a = scan_ooxml(src)
    assert a.findings['excel_hidden_sheets'] == 1
    assert a.findings['excel_hidden_rows'] == 1
    assert a.findings['excel_hidden_columns'] == 1
    assert a.status == 'review_required'


def test_powerpoint_hidden_slide_and_notes(tmp_path):
    src = tmp_path/'deck.pptx'; fixture(src)
    add(src, {'ppt/slides/slide1.xml': '<p:sld xmlns:p="urn:test" show="0"/>',
              'ppt/notesSlides/notesSlide1.xml': '<n/>'})
    a = scan_ooxml(src)
    assert a.findings['powerpoint_hidden_slides'] == 1
    assert a.findings['powerpoint_notes_parts'] == 1


def test_excel_external_connections_and_cache(tmp_path):
    src = tmp_path/'book.xlsx'; fixture(src)
    add(src, {'xl/connections.xml': '<connections/>',
              'xl/externalLinks/externalLink1.xml': '<x/>',
              'xl/queryTables/queryTable1.xml': '<x/>',
              'xl/pivotCache/pivotCacheDefinition1.xml': '<x/>'})
    a = scan_ooxml(src)
    for key in ('excel_connection_parts', 'excel_external_link_parts',
                'excel_query_table_parts', 'excel_pivot_cache_parts'):
        assert a.findings[key] == 1


def test_word_external_field_and_custom_xml(tmp_path):
    src = tmp_path/'word.docx'; fixture(src)
    add(src, {'word/header1.xml': '<w:hdr xmlns:w="urn:test"><w:instrText>INCLUDETEXT hidden</w:instrText></w:hdr>',
              'customXml/item1.xml': '<customer>secret payload</customer>'})
    a = scan_ooxml(src)
    assert a.findings['word_external_field_candidates'] == 1
    assert a.findings['custom_xml_parts'] == 1
    assert 'secret payload' not in str(a.as_dict())


def test_guarded_blocks_new_exposures(tmp_path):
    src, dst = tmp_path/'book.xlsx', tmp_path/'out.xlsx'; fixture(src)
    add(src, {'xl/workbook.xml': '<workbook><sheet state="hidden"/></workbook>'})
    r = guarded_sanitize(src, dst)
    assert r.status == 'blocked'
    assert not dst.exists()


def test_normal_xml_not_false_positive(tmp_path):
    src = tmp_path/'book.xlsx'; fixture(src)
    add(src, {'xl/workbook.xml': '<workbook><sheet state="visible"/></workbook>'})
    a = scan_ooxml(src)
    assert 'excel_hidden_sheets' not in a.findings
