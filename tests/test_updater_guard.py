"""Adversarial update provenance tests (all entirely offline)."""
import io
from urllib.request import Request
import pytest
from office_sanitizer.updater_guard import (
    is_trusted_origin, valid_asset_url, _TrustedRedirect, open_trusted,
    deb_version, deb_identity_matches,
)
from office_sanitizer.updater import UpdateError, _download_verified

TAG = 'v9.0.0-beta.2'
NAME = 'office-sanitizer_9.0.0~beta2_all.deb'
URL = f'https://github.com/sudipdasin/office-sanitizer/releases/download/{TAG}/{NAME}'


def test_allow_exact_release_asset():
    assert valid_asset_url(URL, TAG, NAME)


@pytest.mark.parametrize('url', [
    'http://github.com/sudipdasin/office-sanitizer/releases/download/v9.0.0-beta.2/' + NAME,
    'https://github.com.evil.example/sudipdasin/office-sanitizer/releases/download/' + TAG + '/' + NAME,
    'https://github.com:444/sudipdasin/office-sanitizer/releases/download/' + TAG + '/' + NAME,
    'https://user@github.com/sudipdasin/office-sanitizer/releases/download/' + TAG + '/' + NAME,
    URL + '?redirect=https://evil.example',
    URL + '#fragment',
    URL.replace(TAG, 'v9.0.0-beta.3'),
    URL.replace(NAME, 'other.deb'),
])
def test_malicious_asset_urls_rejected(url):
    assert not valid_asset_url(url, TAG, NAME)


def test_redirect_allowlist_blocks_external_destination():
    handler = _TrustedRedirect()
    req = Request(URL)
    with pytest.raises(ValueError, match='untrusted'):
        handler.redirect_request(req, None, 302, 'moved', {}, 'https://attacker.invalid/payload')
    assert is_trusted_origin('https://release-assets.githubusercontent.com/asset?token=a', redirect=True)
    assert not is_trusted_origin('https://release-assets.githubusercontent.com.evil.test/asset', redirect=True)


def test_reject_untrusted_initial_request_before_network():
    with pytest.raises(ValueError):
        open_trusted(Request('http://evil.example/file'))


def test_debian_release_version_conversion():
    assert deb_version(TAG) == '9.0.0~beta2'
    assert deb_version('v9.0.0') == '9.0.0'
    assert deb_version('v9.0.0b1') is None


def test_download_verified_rejects_forged_asset_identity(tmp_path):
    candidate = {'name': NAME, 'tag': TAG, 'url': URL.replace(TAG, 'v99.0.0'),
                 'digest': '0'*64, 'size': 1}
    with pytest.raises(UpdateError, match='identity'):
        _download_verified(candidate, tmp_path, opener=lambda req, timeout: io.BytesIO(b'x'))
    assert not list(tmp_path.iterdir())


def test_debian_identity_real_package_and_mismatch(tmp_path):
    import subprocess
    pkg = tmp_path / 'pkg'
    (pkg/'DEBIAN').mkdir(parents=True)
    (pkg/'DEBIAN'/'control').write_text(
        'Package: office-sanitizer\nVersion: 9.0.0~beta2\nArchitecture: all\n'
        'Maintainer: Example <example@example.invalid>\nDescription: test package\n')
    target = tmp_path / 'test.deb'
    subprocess.run(['dpkg-deb', '--build', str(pkg), str(target)], check=True, capture_output=True)
    assert deb_identity_matches(target, TAG)
    assert not deb_identity_matches(target, 'v9.0.0-beta.3')
    assert not deb_identity_matches(tmp_path/'missing.deb', TAG)
