"""Strict, offline-testable trust boundaries for optional Debian updates.

GitHub Release SHA-256 digests protect against transfer corruption, but they
are not a substitute for publisher signatures or signed APT repository metadata.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

RELEASE_PREFIX = '/sudipdasin/office-sanitizer/releases/download/'
_REDIRECT_DOMAINS = {'github.com', 'release-assets.githubusercontent.com'}


def is_trusted_origin(url: str, *, redirect: bool = False) -> bool:
    """Reject HTTP, non-standard ports, credentials, lookalikes and fragments."""
    try:
        parsed = urlsplit(url)
        allowed = _REDIRECT_DOMAINS if redirect else {'github.com'}
        return (parsed.scheme == 'https' and parsed.hostname in allowed
                and parsed.port in (None, 443) and parsed.username is None
                and parsed.password is None and not parsed.fragment)
    except ValueError:
        return False


def valid_asset_url(url: str, tag: str, filename: str) -> bool:
    """Require download path to match selected release tag AND exact asset name."""
    if not (isinstance(url, str) and isinstance(tag, str) and isinstance(filename, str)):
        return False
    if not re.fullmatch(r'v?\d+\.\d+\.\d+(?:-beta\.\d+|b\d+)?', tag):
        return False
    if not re.fullmatch(r'office-sanitizer_[0-9A-Za-z.+~_-]+_all\.deb', filename):
        return False
    parsed = urlsplit(url)
    expected = deb_version(tag)
    return (is_trusted_origin(url) and not parsed.query
            and expected is not None and filename == f'office-sanitizer_{expected}_all.deb'
            and parsed.path == RELEASE_PREFIX + quote(tag, safe='') + '/' + quote(filename, safe=''))


class _TrustedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_trusted_origin(newurl, redirect=True):
            raise ValueError('untrusted download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_trusted(request, timeout=12):
    """Use TLS and disallow redirects outside GitHub-controlled hosts."""
    url = request.full_url
    is_release_api = (
        url == 'https://api.github.com/repos/sudipdasin/office-sanitizer/releases?per_page=30'
    )
    if not (is_release_api or is_trusted_origin(url, redirect=True)):
        raise ValueError('untrusted update request')
    opener = build_opener(_TrustedRedirect())
    return opener.open(request, timeout=timeout)


def deb_version(tag: str) -> str | None:
    """Expected Debian Version for v4.3.0-beta.1 -> 4.3.0~beta1."""
    if not re.fullmatch(r'v?\d+\.\d+\.\d+(?:-beta\.\d+)?', tag):
        return None
    return tag.lstrip('v').replace('-beta.', '~beta')


def deb_identity_matches(package: Path, tag: str) -> bool:
    """Fail closed unless Debian's own archive metadata matches the release."""
    version = deb_version(tag)
    if not version:
        return False
    try:
        fields = subprocess.run(
            ['dpkg-deb', '--field', str(package), 'Package', 'Version', 'Architecture'],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    values = {}
    for line in fields:
        if ': ' in line:
            key, value = line.split(': ', 1)
            values[key] = value
    return (values.get('Package') == 'office-sanitizer'
            and values.get('Architecture') == 'all'
            and values.get('Version') == version)
