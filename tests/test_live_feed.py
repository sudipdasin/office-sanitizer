"""Offline adversarial tests for the CI-independent Render update channel."""
import hashlib
import io
import json
import pytest
from office_sanitizer.live_feed import (
    LIVE_ORIGIN, LiveFeedError, parse_live_manifest,
    valid_live_asset_url, _allowed_live_url, find_live_update,
)
from office_sanitizer.updater import _download_verified, find_update, UpdateError

TAG = 'v4.3.0-beta.9'
NAME = 'office-sanitizer_4.3.0~beta9_all.deb'
URL = LIVE_ORIGIN + '/downloads/' + NAME


def manifest():
    return {'version': '4.3.0b9', 'channel': 'beta', 'status': 'human_review_required',
            'debian': {'name': NAME, 'url': '/downloads/' + NAME, 'size': 4,
                       'sha256': hashlib.sha256(b'abcd').hexdigest()}}


def parse(data, **kwargs):
    return parse_live_manifest(json.dumps(data).encode(), installed_version=(4, 3, 0, 1), **kwargs)


def test_valid_asset_and_tag():
    candidate = parse(manifest())
    assert candidate['tag'] == TAG and candidate['url'] == URL
    assert candidate['source'] == 'render'


def test_stable_only_and_downgrade_ignored():
    assert parse(manifest(), include_prerelease=False) is None
    assert parse_live_manifest(json.dumps(manifest()).encode(),
                               installed_version=(4, 3, 0, 10)) is None


@pytest.mark.parametrize('change', [
    lambda obj: obj['debian'].update(name='../private.deb'),
    lambda obj: obj['debian'].update(url='https://evil.example/evil.deb'),
    lambda obj: obj['debian'].update(url='/downloads/../../etc/passwd'),
    lambda obj: obj['debian'].update(sha256='bad-hash'),
    lambda obj: obj['debian'].update(size=True),
    lambda obj: obj['debian'].update(size=100 * 1024 * 1024 + 1),
    lambda obj: obj.update(version='4.3.0b9;bad'),
    lambda obj: obj.update(status='classified_clearance'),
])
def test_invalid_manifest_fails_closed(change):
    data = manifest()
    change(data)
    with pytest.raises(LiveFeedError):
        parse(data)


def test_untrusted_hostname_and_http_rejected():
    for url in ('http://office-sanitizer-xfce-live.onrender.com/release.json',
                'https://office-sanitizer-xfce-live.onrender.com.evil.test/release.json',
                LIVE_ORIGIN + ':444/release.json',
                LIVE_ORIGIN + '/downloads/bad.deb?query=yes'):
        assert not _allowed_live_url(url)
    assert not valid_live_asset_url(URL.replace('beta9', 'beta8'), TAG, NAME)


def test_verified_render_download_and_wrong_asset_blocked(tmp_path):
    candidate = parse(manifest())
    output = _download_verified(candidate, tmp_path, opener=lambda req, timeout: io.BytesIO(b'abcd'))
    assert output.read_bytes() == b'abcd'
    with pytest.raises(UpdateError):
        _download_verified(dict(candidate, url=LIVE_ORIGIN + '/downloads/wrong.deb'),
                           tmp_path, opener=lambda req, timeout: io.BytesIO(b'abcd'))


def test_live_feed_can_be_read_without_network():
    candidate = find_live_update(installed_version=(4, 3, 0, 1),
                                 opener=lambda req, timeout: io.BytesIO(json.dumps(manifest()).encode()))
    assert candidate['name'] == NAME


def test_fallback_survives_github_outage():
    def gh_failure(request, timeout):
        raise OSError('temporarily unavailable')
    candidate = find_update(opener=gh_failure,
                            live_opener=lambda req, timeout: io.BytesIO(json.dumps(manifest()).encode()))
    assert candidate['source'] == 'render' and candidate['tag'] == TAG


def test_feed_size_limit():
    with pytest.raises(LiveFeedError):
        parse_live_manifest(b'x' * (64*1024+1), installed_version=(4, 3, 0, 1))
