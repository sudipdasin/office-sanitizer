"""Network-free updater version, URL, digest, and size security tests."""
import hashlib
import io
import pytest
from office_sanitizer import updater

def asset(tag='v9.0.0', digest=None, url='https://github.com/sudipdasin/office-sanitizer/releases/download/v9.0.0/office-sanitizer_9.0.0_all.deb', size=4):
    return {'tag_name': tag, 'draft': False, 'prerelease': False, 'assets': [{
        'name': 'office-sanitizer_9.0.0_all.deb', 'browser_download_url': url,
        'digest': digest or 'sha256:' + hashlib.sha256(b'test').hexdigest(),
        'size': size,
    }]}

def test_version_and_prerelease_order():
    assert updater._release_version('v4.2.0-beta.1') == (4, 2, 0, 1)
    assert updater._release_version('4.2.0b1') == (4, 2, 0, 1)
    assert updater._release_version('v4.2.0') > updater._release_version('v4.2.0-beta.42')
    assert updater._release_version('$(rm -rf)') is None

def test_newer_release_selected():
    assert updater._select_update([asset()])['tag'] == 'v9.0.0'

def test_unsigned_deb_ignored():
    bad = asset()
    bad['assets'][0]['digest'] = None
    assert updater._select_update([bad]) is None

def test_untrusted_host_ignored():
    assert updater._select_update([asset(url='https://evil.example/release.deb')]) is None

def test_http_url_ignored():
    assert updater._select_update([asset(url='http://github.com/sudipdasin/office-sanitizer/releases/download/v9.0.0/office-sanitizer_9.0.0_all.deb')]) is None

def test_draft_ignored():
    draft = asset()
    draft['draft'] = True
    assert updater._select_update([draft]) is None

def test_invalid_version_ignored():
    assert updater._select_update([asset(tag='v4.0.0;curl')]) is None

def test_download_hash_mismatch_fails_closed(tmp_path):
    candidate = updater._select_update([asset()])
    with pytest.raises(updater.UpdateError, match='SHA-256'):
        updater._download_verified(candidate, tmp_path, opener=lambda req, timeout: io.BytesIO(b'fail'))
    assert not list(tmp_path.iterdir())

def test_download_valid_hash(tmp_path):
    candidate = updater._select_update([asset()])
    out = updater._download_verified(candidate, tmp_path, opener=lambda req, timeout: io.BytesIO(b'test'))
    assert out.read_bytes() == b'test'

def test_download_size_limit(tmp_path):
    candidate = updater._select_update([asset(size=1)])
    with pytest.raises(updater.UpdateError, match='size'):
        updater._download_verified(candidate, tmp_path, opener=lambda req, timeout: io.BytesIO(b'test'))
    assert not list(tmp_path.iterdir())

def test_oversize_release_ignored():
    assert updater._select_update([asset(size=updater.MAX_DEB + 1)]) is None

def test_headless_import_and_cli_help():
    with pytest.raises(SystemExit) as exc:
        updater.main(['--help'])
    assert exc.value.code == 0
