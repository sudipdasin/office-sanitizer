"""Offline/reproducible release-asset builders exclude sensitive local files."""
import hashlib
from pathlib import Path
import zipfile
from scripts.build_source_archive import create_archive, source_paths


def test_zip_whitelist_excludes_user_secrets_and_cache(tmp_path):
    (tmp_path/'office_sanitizer').mkdir()
    (tmp_path/'office_sanitizer'/'core.py').write_text('x=1\n')
    (tmp_path/'office_sanitizer'/'private.key').write_text('SUPER_SECRET')
    (tmp_path/'office_sanitizer'/'__pycache__').mkdir()
    (tmp_path/'office_sanitizer'/'__pycache__'/'core.pyc').write_bytes(b'SECRET')
    (tmp_path/'README.md').write_text('readme')
    (tmp_path/'user-data.docx').write_bytes(b'private')
    archive = tmp_path/'a.zip'
    create_archive(tmp_path, archive)
    with zipfile.ZipFile(archive) as z:
        assert z.namelist() == ['README.md', 'office_sanitizer/core.py']
        assert z.testzip() is None
        assert b'SUPER_SECRET' not in archive.read_bytes()


def test_archive_generation_is_reproducible(tmp_path):
    (tmp_path/'office_sanitizer').mkdir()
    (tmp_path/'office_sanitizer'/'module.py').write_text('print("hello")')
    first, second = tmp_path/'one.zip', tmp_path/'two.zip'
    create_archive(tmp_path, first)
    create_archive(tmp_path, second)
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()


def test_current_release_has_packaging_sources():
    root = Path(__file__).resolve().parents[1]
    names = {p.relative_to(root).as_posix() for p in source_paths(root)}
    for filename in ('office_sanitizer/updater.py', 'office_sanitizer/updater_guard.py',
                     'scripts/build_deb.sh', 'scripts/release_local.sh', 'tests/test_release_offline.py'):
        assert filename in names
