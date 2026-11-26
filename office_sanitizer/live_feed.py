"""Strict HTTPS release feed for CI-free XFCE distributions.

A hosted SHA-256 digest verifies transfer integrity, not publisher signing.
No document data is transmitted to this endpoint.
"""
from __future__ import annotations
import json
import re
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.parse import urlsplit

LIVE_ORIGIN = 'https://office-sanitizer-xfce-live.onrender.com'
LIVE_MANIFEST = LIVE_ORIGIN + '/release.json'
MAX_MANIFEST = 64 * 1024
MAX_PACKAGE = 100 * 1024 * 1024


class LiveFeedError(ValueError):
    """Never expose untrusted URLs or payloads in error messages."""


def _allowed_live_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == 'https' and
                parsed.hostname == 'office-sanitizer-xfce-live.onrender.com' and
                parsed.username is None and parsed.password is None and
                parsed.port in (None, 443) and not parsed.fragment and not parsed.query and
                (parsed.path == '/release.json' or
                 parsed.path.startswith('/downloads/office-sanitizer_')))
    except ValueError:
        return False


def valid_live_asset_url(url: str, tag: str, name: str) -> bool:
    from .updater_guard import deb_version
    expected = deb_version(tag) if isinstance(tag, str) else None
    return (isinstance(name, str) and expected is not None and
            name == f'office-sanitizer_{expected}_all.deb' and
            url == f'{LIVE_ORIGIN}/downloads/{name}' and _allowed_live_url(url))


class _SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed_live_url(newurl):
            raise LiveFeedError('Untrusted release redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_live(request, timeout=12):
    if not _allowed_live_url(request.full_url):
        raise LiveFeedError('Untrusted release feed origin')
    return build_opener(_SameOriginRedirect()).open(request, timeout=timeout)


def parse_live_manifest(raw: bytes, *, installed_version: tuple[int, int, int, int],
                        include_prerelease=True) -> dict | None:
    if len(raw) > MAX_MANIFEST:
        raise LiveFeedError('Release manifest too large')
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get('channel') != 'beta':
            raise ValueError('Invalid channel')
        version = data.get('version')
        if not isinstance(version, str):
            raise ValueError('Invalid version')
        match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)b(\d+)', version)
        if not match:
            raise ValueError('Invalid beta version')
        parsed = tuple(int(i) for i in match.groups())
        if not include_prerelease or parsed <= installed_version:
            return None
        if data.get('status') != 'human_review_required':
            raise ValueError('Invalid review status')
        asset = data['debian']
        if not isinstance(asset, dict):
            raise ValueError('Missing Debian asset')
        tag = 'v' + version.replace('b', '-beta.')
        name, size, digest, uri = (asset.get('name'), asset.get('size'),
                                   asset.get('sha256'), asset.get('url'))
        if (not isinstance(name, str) or
                not isinstance(uri, str) or uri != '/downloads/' + name or
                type(size) is not int or not 0 < size <= MAX_PACKAGE or
                not isinstance(digest, str) or
                not re.fullmatch(r'[0-9a-fA-F]{64}', digest) or
                not valid_live_asset_url(LIVE_ORIGIN + uri, tag, name)):
            raise ValueError('Invalid asset metadata')
        return {'tag': tag, 'name': name, 'size': size, 'digest': digest.lower(),
                'url': LIVE_ORIGIN + uri, 'source': 'render'}
    except (ValueError, TypeError, KeyError, OverflowError):
        raise LiveFeedError('Invalid public release manifest') from None


def find_live_update(*, installed_version: tuple[int, int, int, int],
                     include_prerelease=True, opener=open_live) -> dict | None:
    request = Request(LIVE_MANIFEST, headers={'Accept': 'application/json',
                                             'User-Agent': 'office-sanitizer-updater'})
    try:
        with opener(request, timeout=12) as response:
            raw = response.read(MAX_MANIFEST + 1)
    except Exception:
        raise LiveFeedError('Public release feed unavailable') from None
    return parse_live_manifest(raw, installed_version=installed_version,
                               include_prerelease=include_prerelease)
