"""Independent conservative post-sanitization OOXML integrity verifier.

Verification is package-level, not an Office application compatibility or
confidentiality certification. Never includes extracted user content in reports.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import unquote, urlsplit
import hashlib
import posixpath
import zipfile

from .core import META_NAMES, CONTENT_NS, RELS_NS
from .security import validate_package, contains_signatures


@dataclass
class Verification:
    status: str = 'failed'
    unchanged_parts: int = 0
    removed_metadata_parts: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


def _part_target(relfile: str, target: str) -> str:
    """Resolve OPC internal targets (reject traversal and query components)."""
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise ValueError('unsupported internal relationship target')
    raw = unquote(parsed.path)
    if '\\' in raw or not raw:
        raise ValueError('invalid relationship path')
    if raw.startswith('/'):
        result = posixpath.normpath(raw.lstrip('/'))
    else:
        folder = posixpath.dirname(relfile)
        base = '' if folder == '_rels' else posixpath.dirname(folder)
        result = posixpath.normpath(posixpath.join(base, raw))
    if result == '..' or result.startswith('../') or result.startswith('/'):
        raise ValueError('relationship escapes package root')
    return result


def verify_output(original: str | Path, cleaned: str | Path) -> Verification:
    """Check macro bytes, unchanged content, removed props and OPC references.

    Does not mean documents are safe to share. Files must be validated in
    actual Office applications independently.
    """
    result = Verification()
    try:
        with zipfile.ZipFile(original) as src, zipfile.ZipFile(cleaned) as dst:
            validate_package(src)
            validate_package(dst)
            if contains_signatures(set(src.namelist()) | set(dst.namelist())):
                raise ValueError("signed package: cannot assert validity after rewriting")
            if src.testzip() is not None or dst.testzip() is not None:
                raise ValueError('ZIP integrity failure')
            a = set(src.namelist())
            b = set(dst.namelist())
            removable = META_NAMES | {name for name in a if name.startswith('docProps/thumbnail.')}
            removed = a & removable
            if a - b != removed or b - a:
                raise ValueError('unexpected parts added or removed')
            for name in b:
                old, new = src.read(name), dst.read(name)
                if name == '[Content_Types].xml' or name.endswith('.rels'):
                    ET.fromstring(new)
                elif hashlib.sha256(old).digest() != hashlib.sha256(new).digest():
                    raise ValueError('non-metadata part modified')
                if name.endswith('.xml'):
                    ET.fromstring(new)
            for name in b:
                if name.endswith('.rels'):
                    root = ET.fromstring(dst.read(name))
                    for rel in root:
                        if rel.tag != f'{{{RELS_NS}}}Relationship' or rel.get('TargetMode') == 'External':
                            continue
                        target = _part_target(name, rel.get('Target', ''))
                        if target not in b:
                            raise ValueError('dangling or missing internal relationship target')
            manifest = ET.fromstring(dst.read('[Content_Types].xml'))
            for el in manifest:
                if el.tag == f'{{{CONTENT_NS}}}Override':
                    target = el.get('PartName', '').lstrip('/')
                    if target not in b:
                        raise ValueError('dangling content-type override')
            result.unchanged_parts = sum(1 for n in b if n != '[Content_Types].xml' and not n.endswith('.rels'))
            result.removed_metadata_parts = len(removed)
            result.status = 'package_integrity_verified_content_unreviewed'
    except (OSError, ValueError, RuntimeError, ET.ParseError, zipfile.BadZipFile, KeyError):
        result.errors.append('package validation failed; do not distribute without review')
    return result
