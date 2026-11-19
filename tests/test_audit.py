import zipfile
from office_sanitizer.audit import scan_ooxml, REL_NS

def make_zip(path, body, extra=None):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('_rels/.rels', f'<Relationships xmlns="{REL_NS}"/>')
        z.writestr('word/document.xml', body)
        for key, value in (extra or {}).items():
            z.writestr(key, value)

def test_counts_sensitive_without_leaking_values(tmp_path):
    secret = 'secret.person@example.com'
    p = tmp_path / 'file.docx'
    make_zip(p, f'<doc><t>{secret}</t><del><t>old</t></del><vanish/></doc>')
    r = scan_ooxml(p)
    assert r.status == 'review_required'
    assert r.findings['email_addresses'] == 1
    assert r.findings['tracked_change_nodes'] == 1
    assert r.findings['hidden_content_markers'] == 1
    assert secret not in str(r.as_dict())
    assert str(tmp_path) not in str(r.as_dict())

def test_macro_embedded_and_external(tmp_path):
    p = tmp_path / 'file.docm'
    make_zip(p, '<doc/>', {
        'word/vbaProject.bin': b'VB',
        'word/embeddings/item.bin': b'file',
        'word/_rels/document.xml.rels': f'<Relationships xmlns="{REL_NS}"><Relationship Target="https://a.example" TargetMode="External"/></Relationships>',
    })
    r = scan_ooxml(p)
    assert r.findings['vba_project_parts'] == 1
    assert r.findings['embedded_objects'] == 1
    assert r.findings['external_relationships'] == 1

def test_empty_indicators(tmp_path):
    p = tmp_path / 'x.docx'
    make_zip(p, '<doc><t>ordinary content</t></doc>')
    assert scan_ooxml(p).status == 'no_indicators_detected'

def test_invalid_zip_fails_closed(tmp_path):
    p = tmp_path / 'bad.docx'
    p.write_bytes(b'not zip')
    assert scan_ooxml(p).status == 'incomplete'

def test_bad_xml_fails_closed(tmp_path):
    p = tmp_path / 'bad.docx'
    make_zip(p, '<broken')
    assert scan_ooxml(p).status == 'incomplete'

def test_traversal_fails_closed(tmp_path):
    p = tmp_path / 'bad.docx'
    make_zip(p, '<doc/>', {'../bad.xml': '<doc/>'})
    assert scan_ooxml(p).status == 'incomplete'
