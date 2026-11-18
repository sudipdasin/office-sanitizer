"""Fail-closed Office Open XML metadata sanitizer.

Only supported ZIP-based Office files are transformed. This removes selected
metadata, not sensitive document body or VBA source content.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from xml.etree import ElementTree as ET

SUPPORTED = {'.docx', '.docm', '.dotx', '.dotm', '.xlsx', '.xlsm', '.xltx',
             '.xltm', '.pptx', '.pptm', '.potx', '.potm', '.ppsx', '.ppsm'}
CONTENT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
META_NAMES = {'docProps/core.xml', 'docProps/app.xml', 'docProps/custom.xml'}
MAX_MEMBERS = 10000
MAX_UNCOMPRESSED = 512 * 1024 * 1024
MAX_RATIO = 200


@dataclass
class Result:
    source: str
    output: str | None = None
    status: str = 'failed'
    removed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    verified: bool = False
    macro_sha256_before: dict[str, str] = field(default_factory=dict)
    macro_sha256_after: dict[str, str] = field(default_factory=dict)

    def public_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if k not in ('source', 'output')}


def _safe_package(infos: list[zipfile.ZipInfo]) -> None:
    if len(infos) > MAX_MEMBERS:
        raise ValueError('Package contains too many entries')
    names = [i.filename for i in infos]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate package entry names')
    if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
        raise ValueError('Package exceeds decompressed-size limit')
    for i in infos:
        p = PurePosixPath(i.filename)
        if i.filename.startswith('/') or '\\' in i.filename or '..' in p.parts:
            raise ValueError('Unsafe entry name')
        if i.file_size > MAX_RATIO * max(1, i.compress_size) and i.file_size > 1024 * 1024:
            raise ValueError('Suspicious ZIP compression ratio')


def _macros(z: zipfile.ZipFile) -> dict[str, str]:
    return {name: hashlib.sha256(z.read(name)).hexdigest()
            for name in z.namelist() if name.lower().endswith('/vbaproject.bin')}


def _relationship_target(rels_file: str, target: str) -> str:
    folder = posixpath.dirname(rels_file)
    base = '' if folder == '_rels' else posixpath.dirname(folder)
    return (posixpath.normpath(posixpath.join(base, target.lstrip('/')))
            if not target.startswith('/') else target.lstrip('/'))


def _rewrite_xml(name: str, data: bytes, removed: set[str]) -> bytes:
    if name == '[Content_Types].xml':
        root = ET.fromstring(data)
        for node in list(root):
            if node.tag == f'{{{CONTENT_NS}}}Override' and node.get('PartName', '').lstrip('/') in removed:
                root.remove(node)
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if name.endswith('.rels'):
        root = ET.fromstring(data)
        for node in list(root):
            if node.tag == f'{{{RELS_NS}}}Relationship' and node.get('TargetMode') != 'External':
                if _relationship_target(name, node.get('Target', '').split('#')[0]) in removed:
                    root.remove(node)
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)
    return data


def sanitize(source: str | Path, output: str | Path) -> Result:
    src, dst = Path(source), Path(output)
    result = Result(source=str(src))
    if src.suffix.lower() not in SUPPORTED:
        result.warnings.append('Unsupported format: requires manual review; no output created')
        return result
    if not src.is_file() or src.resolve() == dst.resolve():
        result.warnings.append('Source unavailable or output would overwrite source')
        return result
    temp_name = None
    try:
        with zipfile.ZipFile(src) as zin:
            infos = zin.infolist()
            _safe_package(infos)
            if zin.testzip() is not None:
                raise ValueError('Corrupt ZIP member')
            names = set(zin.namelist())
            if '[Content_Types].xml' not in names or '_rels/.rels' not in names:
                raise ValueError('Invalid Office package: missing package manifest/relationships')
            ET.fromstring(zin.read('[Content_Types].xml'))
            ET.fromstring(zin.read('_rels/.rels'))
            to_remove = META_NAMES & names
            to_remove |= {n for n in names if n.startswith('docProps/thumbnail.')}
            before = _macros(zin)
            dst.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix='.office-sanitizer-', suffix='.tmp', dir=dst.parent)
            os.close(fd)
            with zipfile.ZipFile(temp_name, 'w') as zout:
                for info in infos:
                    if info.filename in to_remove:
                        continue
                    data = zin.read(info.filename)
                    if info.filename == '[Content_Types].xml' or info.filename.endswith('.rels'):
                        data = _rewrite_xml(info.filename, data, to_remove)
                    zout.writestr(info, data)
        with zipfile.ZipFile(temp_name) as verified:
            if verified.testzip() is not None:
                raise ValueError('Output ZIP failed CRC verification')
            remaining = set(verified.namelist())
            if remaining & to_remove:
                raise ValueError('Removed metadata unexpectedly persists')
            if _macros(verified) != before:
                raise ValueError('Macro content changed')
            if '[Content_Types].xml' not in remaining or '_rels/.rels' not in remaining:
                raise ValueError('Output package structurally incomplete')
            for name in remaining:
                if name.endswith('.rels'):
                    root = ET.fromstring(verified.read(name))
                    for rel in root:
                        if rel.tag != f'{{{RELS_NS}}}Relationship' or rel.get('TargetMode') == 'External':
                            continue
                        target = _relationship_target(name, rel.get('Target', '').split('#')[0])
                        if target in to_remove:
                            raise ValueError('Dangling relationship to removed metadata')
        os.replace(temp_name, dst)
        temp_name = None
        result.output = str(dst)
        result.removed = sorted(to_remove)
        result.status = 'metadata_cleaned_content_unreviewed'
        result.verified = True
        result.macro_sha256_before = before
        result.macro_sha256_after = before.copy()
        result.warnings.append('Body text, comments, hidden content, embedded objects, VBA source, and classification markings NOT sanitized')
        if before:
            result.warnings.append('VBA binary projects preserved byte-for-byte; secrets within VBA are NOT removed')
        return result
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile, RuntimeError) as exc:
        result.warnings.append(f'Sanitization failed: {type(exc).__name__}: {exc}')
        return result
    finally:
        if temp_name is not None and os.path.exists(temp_name):
            os.unlink(temp_name)
