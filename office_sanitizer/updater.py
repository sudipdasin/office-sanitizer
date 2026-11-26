"""Automatic XFCE update checks; verified Debian releases require user approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from . import __version__
from .updater_guard import valid_asset_url, open_trusted, deb_identity_matches

RELEASES_URL = 'https://api.github.com/repos/sudipdasin/office-sanitizer/releases'
MAX_JSON = 2 * 1024 * 1024
MAX_DEB = 100 * 1024 * 1024
CHECK_INTERVAL = 86400

class UpdateError(Exception):
    """Safe user-facing errors; never include remote bodies or local document paths."""

def _release_version(tag):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:[-.]?beta[.-]?(\d+)|b(\d+))?', tag, re.I)
    if not match:
        return None
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    beta = match.group(4) or match.group(5)
    return major, minor, patch, int(beta) if beta is not None else 1000000

def _current_version():
    return _release_version(__version__) or (0, 0, 0, 0)

def _fetch_releases(*, opener=open_trusted):
    request = Request(RELEASES_URL + '?per_page=30', headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'office-sanitizer-update-checker/' + __version__,
    })
    try:
        with opener(request, timeout=12) as response:
            raw = response.read(MAX_JSON + 1)
    except Exception:
        raise UpdateError('Update check could not contact GitHub securely') from None
    if len(raw) > MAX_JSON:
        raise UpdateError('Unexpected release metadata size')
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        raise UpdateError('Invalid release metadata') from None
    if not isinstance(parsed, list):
        raise UpdateError('Unexpected release metadata')
    return parsed

def _select_update(releases, *, include_prerelease=True):
    choices = []
    for release in releases:
        if not isinstance(release, dict) or release.get('draft'):
            continue
        if release.get('prerelease') and not include_prerelease:
            continue
        tag = release.get('tag_name')
        version = _release_version(tag) if isinstance(tag, str) else None
        if version is None or version <= _current_version():
            continue
        for asset in release.get('assets', []):
            if not isinstance(asset, dict):
                continue
            name, uri = asset.get('name'), asset.get('browser_download_url')
            digest, size = asset.get('digest'), asset.get('size')
            if not (isinstance(name, str) and
                    re.fullmatch(r'office-sanitizer_[0-9A-Za-z.+~_-]+_all\.deb', name)):
                continue
            if not valid_asset_url(uri, tag, name):
                continue
            if not (isinstance(digest, str) and re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest)):
                continue
            if type(size) is not int or not 0 < size <= MAX_DEB:
                continue
            choices.append((version, {'tag': tag, 'name': name, 'url': uri,
                                      'digest': digest[7:].lower(), 'size': size}))
    return max(choices, key=lambda item: item[0])[1] if choices else None

def find_update(*, opener=open_trusted, include_prerelease=True):
    return _select_update(_fetch_releases(opener=opener), include_prerelease=include_prerelease)

def _download_verified(candidate, directory, *, opener=open_trusted):
    if not valid_asset_url(candidate.get('url'), candidate.get('tag'), candidate.get('name')):
        raise UpdateError('Invalid official release asset identity')
    target = directory / candidate['name']
    if target.exists():
        raise UpdateError('Update filename collision')
    request = Request(candidate['url'], headers={'User-Agent': 'office-sanitizer-updater/' + __version__})
    size = 0
    digest = hashlib.sha256()
    try:
        with opener(request, timeout=30) as response, target.open('xb') as stream:
            while chunk := response.read(256 * 1024):
                size += len(chunk)
                if size > MAX_DEB or size > candidate['size']:
                    raise UpdateError('Downloaded package exceeded expected size')
                stream.write(chunk)
                digest.update(chunk)
        if size != candidate['size'] or digest.hexdigest() != candidate['digest']:
            raise UpdateError('SHA-256 verification failed; update aborted')
    except UpdateError:
        target.unlink(missing_ok=True)
        raise
    except Exception:
        target.unlink(missing_ok=True)
        raise UpdateError('Update download failed') from None
    return target

def _notify(title, message):
    if shutil.which('notify-send'):
        subprocess.run(['notify-send', '--app-name=Office Sanitizer', title, message],
                       check=False, timeout=5)

def _cache_path():
    return Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'office-sanitizer' / 'last-update-check'

def _rate_limited():
    try:
        return time.time() - _cache_path().stat().st_mtime < CHECK_INTERVAL
    except OSError:
        return False

def _record_check():
    try:
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.touch(mode=0o600)
    except OSError:
        pass

def main(argv=None):
    parser = argparse.ArgumentParser(description='Office Sanitizer verified Debian update checker')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--notify', action='store_true', help='XFCE login check, once per day')
    group.add_argument('--install', action='store_true', help='Download and request authenticated APT install')
    parser.add_argument('--stable-only', action='store_true')
    args = parser.parse_args(argv)
    if args.notify and _rate_limited():
        return 0
    if args.notify:
        _record_check()
    try:
        candidate = find_update(include_prerelease=not args.stable_only)
    except UpdateError as error:
        if not args.notify:
            print(str(error))
        return 1
    if not candidate:
        if not args.notify:
            print('No newer verified Debian GitHub Release available.')
        return 0
    if args.notify:
        _notify('Office Sanitizer update available',
                f"Version {candidate['tag']} is available. Open the app to install it.")
        return 0
    print(f"Verified update available: {candidate['tag']} ({candidate['name']})")
    if not args.install:
        return 0
    if not shutil.which('pkexec') or not Path('/usr/bin/apt').is_file():
        print('Polkit and APT are required for an authenticated update')
        return 1
    try:
        answer = input('Download and request authenticated APT install? Type YES: ')
    except EOFError:
        return 1
    if answer != 'YES':
        print('Cancelled')
        return 1
    with tempfile.TemporaryDirectory(prefix='office-sanitizer-update-') as temp:
        root = Path(temp)
        os.chmod(root, 0o755)
        try:
            package = _download_verified(candidate, root)
        except UpdateError as error:
            print(str(error))
            return 1
        if not deb_identity_matches(package, candidate['tag']):
            print('Debian package identity does not match the selected release')
            return 1
        os.chmod(package, 0o644)
        return subprocess.run(['pkexec', '/usr/bin/apt', 'install', '-y', str(package)],
                              check=False).returncode

if __name__ == '__main__':
    raise SystemExit(main())
