"""Privacy-aware batch orchestration: no paths or matched content in reports."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import Counter
from pathlib import Path
from typing import Iterable

from .core import SUPPORTED
from .audit import scan_ooxml
from .workflow import guarded_sanitize


@dataclass(frozen=True)
class BatchItem:
    index: int
    status: str
    verified: bool
    counts: dict[str, int]
    reasons: tuple[str, ...]

    def as_dict(self):
        return asdict(self)


def choose_files(paths: Iterable[str | Path], *, recursive: bool = False) -> list[Path]:
    """Deterministic order, skip symlinks, and never follow directory symlinks."""
    files = []
    for candidate in paths:
        item = Path(candidate)
        if item.is_symlink():
            continue
        if item.is_file() and item.suffix.lower() in SUPPORTED:
            files.append(item)
        elif item.is_dir():
            iterator = item.rglob('*') if recursive else item.iterdir()
            files.extend(p for p in iterator if p.is_file() and not p.is_symlink()
                         and p.suffix.lower() in SUPPORTED
                         and not any(parent.is_symlink() for parent in p.parents))
    return sorted({p.resolve() for p in files}, key=lambda p: str(p))


def process_batch(files: Iterable[str | Path], *, mode: str = 'audit',
                  output_dir: str | Path | None = None) -> list[BatchItem]:
    """Review-first audit or guarded metadata-only copy.

    Filename collisions are blocked; no output is overwritten. Caller must keep
    output outside scanned input tree for straightforward batch use.
    """
    if mode not in {'audit', 'guarded'}:
        raise ValueError('unsupported batch mode')
    if mode == 'guarded' and output_dir is None:
        raise ValueError('output_dir is required')
    sources = [Path(p) for p in files]
    counts = Counter(p.name.casefold() for p in sources)
    duplicates = {name for name, count in counts.items() if count > 1}
    root = Path(output_dir) if mode == 'guarded' else None
    unsafe_root = bool(root and (
        (root.exists() and not root.is_dir()) or
        any(component.is_symlink() for component in (root, *root.parents))
    ))
    report = []
    for index, src in enumerate(sources, 1):
        if mode == 'audit':
            result = scan_ooxml(src)
            report.append(BatchItem(index, result.status, False, result.findings,
                                    tuple(result.warnings)))
            continue
        if src.is_symlink():
            report.append(BatchItem(index, 'blocked', False, {}, ('source_is_symlink',)))
            continue
        if unsafe_root:
            report.append(BatchItem(index, 'blocked', False, {}, ('unsafe_output_directory',)))
            continue
        if src.name.casefold() in duplicates:
            report.append(BatchItem(index, 'blocked', False, {}, ('filename_collision',)))
            continue
        result = guarded_sanitize(src, Path(output_dir) / src.name)
        report.append(BatchItem(index, result.status, result.verified, result.before_findings,
                                tuple(result.reason_codes)))
    return report
