"""Shared conservative Office ZIP safety checks; no extraction or macro execution."""
from __future__ import annotations

import stat
import zipfile
from pathlib import PurePosixPath

MAX_MEMBERS = 10000
MAX_TOTAL = 512 * 1024 * 1024
MAX_RATIO = 200
MAX_XML_MEMBER = 32 * 1024 * 1024
MAX_XML_TOTAL = 128 * 1024 * 1024


def validate_package(z: zipfile.ZipFile) -> None:
    """Reject hostile OPC containers before writing or interpreting content."""
    infos = z.infolist()
    if len(infos) > MAX_MEMBERS or sum(x.file_size for x in infos) > MAX_TOTAL:
        raise ValueError('package size or member limit exceeded')
    names = [x.filename for x in infos]
    if len(set(names)) != len(names):
        raise ValueError('duplicate package entries')
    if '[Content_Types].xml' not in names or '_rels/.rels' not in names:
        raise ValueError('missing OPC package control files')
    xml_total = 0
    for info in infos:
        name = info.filename
        if name.endswith('.xml') or name.endswith('.rels') or name == '[Content_Types].xml':
            xml_total += info.file_size
            if info.file_size > MAX_XML_MEMBER or xml_total > MAX_XML_TOTAL:
                raise ValueError('XML inspection limits exceeded')
        path = PurePosixPath(name)
        if (not name or name.startswith('/') or '\\' in name or '\x00' in name or
                ':' in name or path.is_absolute() or any(part in ('.', '..') for part in name.split('/'))):
            raise ValueError('unsafe package entry')
        if info.flag_bits & 0x1:
            raise ValueError('encrypted archive entry unsupported')
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ValueError('unsupported ZIP compression')
        mode = (info.external_attr >> 16) & 0xffff
        if info.create_system == 3 and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError('non-regular archive entry')
        if info.file_size > 1024 * 1024 and info.file_size > MAX_RATIO * max(1, info.compress_size):
            raise ValueError('suspicious ZIP expansion ratio')
    if z.testzip() is not None:
        raise ValueError('ZIP CRC failure')


def contains_signatures(names: set[str]) -> bool:
    return any(n.lower().startswith('_xmlsignatures/') or '/_xmlsignatures/' in n.lower() for n in names)
