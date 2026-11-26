#!/usr/bin/env python3
"""Offline deterministic source ZIP: only audited project files, no user data."""
from __future__ import annotations
import argparse
from pathlib import Path
import zipfile

SAFE_ROOTS = ('office_sanitizer', 'tests', 'scripts')
SAFE_FILES = ('README.md', 'CHANGELOG.md', 'RELEASE_VALIDATION.md',
              'pyproject.toml', 'LICENSE', '.gitignore')
EXCLUDED = {'.git', '.pytest_cache', '__pycache__', 'dist', 'build'}


def source_paths(root: Path) -> list[Path]:
    found = [root / item for item in SAFE_FILES if (root / item).is_file()]
    for directory in SAFE_ROOTS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob('*'):
            if not path.is_file() or path.is_symlink():
                continue
            if EXCLUDED.intersection(path.relative_to(root).parts):
                continue
            if path.suffix in ('.py', '.sh'):
                found.append(path)
    return sorted(set(found), key=lambda p: p.relative_to(root).as_posix())


def create_archive(root: Path, destination: Path) -> None:
    root = root.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as output:
        for file in source_paths(root):
            info = zipfile.ZipInfo(file.relative_to(root).as_posix(),
                                   date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 << 16)
            output.writestr(info, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('built source ZIP did not pass CRC verification')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    create_archive(args.root, args.output)
    print(args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
