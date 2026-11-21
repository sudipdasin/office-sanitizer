import importlib
import json
from pathlib import Path
from office_sanitizer.batch import choose_files, process_batch
from test_core import fixture


def test_choose_files_nonrecursive(tmp_path):
    fixture(tmp_path / 'one.docx')
    deeper = tmp_path / 'nested'
    deeper.mkdir()
    fixture(deeper / 'two.docx')
    assert [x.name for x in choose_files([tmp_path])] == ['one.docx']
    assert [x.name for x in choose_files([tmp_path], recursive=True)] == ['two.docx', 'one.docx'] or set(x.name for x in choose_files([tmp_path], recursive=True)) == {'one.docx', 'two.docx'}


def test_unsafe_symlinks_are_skipped(tmp_path):
    source = tmp_path/'source.docx'
    fixture(source)
    (tmp_path/'alias.docx').symlink_to(source)
    assert choose_files([tmp_path]) == [source.resolve()]


def test_batch_audit_no_output(tmp_path):
    source = tmp_path/'source.docx'
    fixture(source)
    reports = process_batch([source], mode='audit')
    assert len(reports) == 1
    assert reports[0].index == 1
    assert 'source.docx' not in json.dumps(reports[0].as_dict())
    assert list(tmp_path.glob('*.docx')) == [source]


def test_guarded_batch_generates_review_copy(tmp_path):
    source = tmp_path/'source.docx'
    fixture(source)
    output = tmp_path/'out'
    reports = process_batch([source], mode='guarded', output_dir=output)
    assert reports[0].verified
    assert reports[0].status == 'metadata_only_copy_requires_human_review'
    assert (output/'source.docx').exists()


def test_collision_block_all(tmp_path):
    a, b = tmp_path/'a', tmp_path/'b'
    a.mkdir(); b.mkdir()
    fixture(a/'same.docx'); fixture(b/'same.docx')
    reports = process_batch([a/'same.docx', b/'same.docx'], mode='guarded', output_dir=tmp_path/'out')
    assert len(reports) == 2
    assert all(x.status == 'blocked' and x.reasons == ('filename_collision',) for x in reports)
    assert not (tmp_path/'out'/'same.docx').exists()


def test_invalid_batch_mode(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        process_batch([], mode='redact')


def test_gui_import_headless():
    module = importlib.import_module('office_sanitizer.gui')
    assert callable(module.main)
