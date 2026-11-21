"""Conservative Office-specific exposure inventory.

Only returns count labels, never contents, target URLs or package member names.
Presence does not prove sensitivity. Absence does not certify safe disclosure.
"""
from collections import Counter
from xml.etree import ElementTree as ET


def package_exposures(name: str) -> Counter[str]:
    low = name.lower()
    out: Counter[str] = Counter()
    if low.startswith('customxml/'):
        out['custom_xml_parts'] += 1
    if low.startswith('xl/externallinks/'):
        out['excel_external_link_parts'] += 1
    if low.startswith('xl/connections') and low.endswith('.xml'):
        out['excel_connection_parts'] += 1
    if low.startswith('xl/querytables/'):
        out['excel_query_table_parts'] += 1
    if low.startswith('xl/pivotcache/'):
        out['excel_pivot_cache_parts'] += 1
    if low.startswith('ppt/notesslides/') and low.endswith('.xml'):
        out['powerpoint_notes_parts'] += 1
    if (low.startswith('word/embeddings/') or low.startswith('xl/embeddings/')
            or low.startswith('ppt/embeddings/')):
        out['embedded_payload_parts'] += 1
    if (low.startswith('word/activex/') or low.startswith('xl/activex/')
            or low.startswith('ppt/activex/')):
        out['activex_parts'] += 1
    if low.startswith('word/afchunk') or low.startswith('word/altchunk'):
        out['word_alternative_content_parts'] += 1
    if low.startswith('xl/printersettings/'):
        out['excel_printer_settings_parts'] += 1
    return out


def xml_exposures(name: str, root: ET.Element) -> Counter[str]:
    """Review indicators for structural Office state that cannot be silently removed."""
    low = name.lower()
    out: Counter[str] = Counter()
    if low == 'xl/workbook.xml':
        for node in root.iter():
            local = node.tag.rsplit('}', 1)[-1]
            if local == 'sheet' and node.get('state', '').lower() in ('hidden', 'veryhidden'):
                out['excel_hidden_sheets'] += 1
            elif local == 'definedName' and node.get('hidden', '').lower() in ('1', 'true'):
                out['excel_hidden_defined_names'] += 1
    if low.startswith('xl/worksheets/') and low.endswith('.xml'):
        for node in root.iter():
            local = node.tag.rsplit('}', 1)[-1]
            if local == 'row' and node.get('hidden', '').lower() in ('1', 'true'):
                out['excel_hidden_rows'] += 1
            if local == 'col' and node.get('hidden', '').lower() in ('1', 'true'):
                out['excel_hidden_columns'] += 1
    if low.startswith('ppt/slides/') and low.endswith('.xml'):
        if root.tag.rsplit('}', 1)[-1] == 'sld' and root.get('show', '').lower() in ('0', 'false'):
            out['powerpoint_hidden_slides'] += 1
    if low.startswith('word/') and low.endswith('.xml'):
        for node in root.iter():
            if node.tag.rsplit('}', 1)[-1] in ('instrText', 'fldSimple'):
                value = node.text or node.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instr', '')
                if any(k in value.upper() for k in ('INCLUDETEXT', 'INCLUDEPICTURE', 'DDE', 'LINK ')):
                    out['word_external_field_candidates'] += 1
    return out
