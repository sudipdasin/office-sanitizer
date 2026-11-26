#!/usr/bin/env python3
"""Build a deterministic, pip-installable wheel using only Python's stdlib."""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
from io import StringIO
from pathlib import Path
import re
import zipfile


def build_wheel(root: Path, output: Path) -> Path:
    root = root.resolve()
    match = re.search(r'^version\s*=\s*"([^"]+)"', (root / 'pyproject.toml').read_text(), re.M)
    if not match:
        raise ValueError('Missing package version')
    version = match.group(1)
    if not re.fullmatch(r'\d+\.\d+\.\d+b\d+', version):
        raise ValueError('Expected beta version')
    if f'__version__ = "{version}"' not in (root / 'office_sanitizer' / '__init__.py').read_text():
        raise ValueError('Package version mismatch')
    output.mkdir(parents=True, exist_ok=True)
    filename = output / f'office_sanitizer-{version}-py3-none-any.whl'
    info_dir = f'office_sanitizer-{version}.dist-info'
    entries = {
        f'{info_dir}/METADATA': (
            f'Metadata-Version: 2.2\nName: office-sanitizer\nVersion: {version}\n'
            'Summary: Offline OOXML privacy review and guarded metadata cleaning\n'
            'License: GPL-3.0-only\nRequires-Python: >=3.10\n'
        ).encode(),
        f'{info_dir}/WHEEL': b'Wheel-Version: 1.0\nGenerator: offline-stdlib-wheel\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        f'{info_dir}/entry_points.txt': (
            '[console_scripts]\n'
            'office-sanitizer = office_sanitizer.__main__:main\n'
            'office-sanitizer-gui = office_sanitizer.gui:main\n'
            'office-sanitizer-update = office_sanitizer.updater:main\n'
        ).encode(),
        f'{info_dir}/top_level.txt': b'office_sanitizer\n',
    }
    package = root / 'office_sanitizer'
    if package.is_symlink() or not package.is_dir():
        raise ValueError('Invalid package directory')
    for path in sorted(package.glob('*.py')):
        if path.is_symlink():
            raise ValueError('Symlinked source rejected')
        entries[f'office_sanitizer/{path.name}'] = path.read_bytes()
    if 'office_sanitizer/__main__.py' not in entries:
        raise ValueError('Missing CLI module')
    records = []
    for name, raw in sorted(entries.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=')
        records.append((name, 'sha256=' + digest, str(len(raw))))
    record_name = f'{info_dir}/RECORD'
    records.append((record_name, '', ''))
    buffer = StringIO(newline='')
    csv.writer(buffer, lineterminator='\n').writerows(records)
    entries[record_name] = buffer.getvalue().encode()
    with zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as wheel:
        for name, raw in sorted(entries.items()):
            spec = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            spec.compress_type = zipfile.ZIP_DEFLATED
            spec.external_attr = (0o644 << 16)
            wheel.writestr(spec, raw)
    with zipfile.ZipFile(filename) as check:
        if check.testzip() is not None:
            raise ValueError('Wheel CRC verification failed')
    return filename


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(build_wheel(args.root, args.output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
