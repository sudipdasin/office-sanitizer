"""Batch review must not write into linked or ambiguous destinations."""
from office_sanitizer.batch import process_batch
from test_core import fixture


def test_block_output_directory_symlink(tmp_path):
    source = tmp_path/'input.docx'
    fixture(source)
    real = tmp_path/'real'
    real.mkdir()
    linked = tmp_path/'linked'
    linked.symlink_to(real, target_is_directory=True)
    result = process_batch([source], mode='guarded', output_dir=linked)
    assert result[0].status == 'blocked'
    assert result[0].reasons == ('unsafe_output_directory',)
    assert not list(real.iterdir())


def test_block_nested_output_directory_symlink(tmp_path):
    source = tmp_path/'input.docx'
    fixture(source)
    real = tmp_path/'real'
    real.mkdir()
    (tmp_path/'linked').symlink_to(real, target_is_directory=True)
    result = process_batch([source], mode='guarded', output_dir=tmp_path/'linked'/'nested')
    assert result[0].reasons == ('unsafe_output_directory',)


def test_block_source_symlink(tmp_path):
    source = tmp_path/'input.docx'
    fixture(source)
    link = tmp_path/'alias.docx'
    link.symlink_to(source)
    report = process_batch([link], mode='guarded', output_dir=tmp_path/'out')
    assert report[0].reasons == ('source_is_symlink',)
    assert not (tmp_path/'out').exists()


def test_case_insensitive_collisions_fail_closed(tmp_path):
    first = tmp_path/'a'/'FILE.docx'
    second = tmp_path/'b'/'file.docx'
    first.parent.mkdir()
    second.parent.mkdir()
    fixture(first)
    fixture(second)
    items = process_batch([first, second], mode='guarded', output_dir=tmp_path/'out')
    assert all(item.reasons == ('filename_collision',) for item in items)
    assert not (tmp_path/'out').exists()


def test_plain_output_directory_remains_allowed(tmp_path):
    source = tmp_path/'input.docx'
    fixture(source)
    out = tmp_path/'normal'
    result = process_batch([source], mode='guarded', output_dir=out)
    assert result[0].verified
    assert (out/'input.docx').exists()


def test_block_output_path_that_is_a_file(tmp_path):
    source = tmp_path/'input.docx'
    fixture(source)
    dest = tmp_path/'output'
    dest.write_text('not a directory')
    result = process_batch([source], mode='guarded', output_dir=dest)
    assert result[0].reasons == ('unsafe_output_directory',)
    assert dest.read_text() == 'not a directory'
