"""Non-destructive Office Open XML indicator audit. No document text in output."""
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib
from xml.etree import ElementTree as ET
import re
import zipfile
from .security import validate_package, contains_signatures

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SENSITIVE = {
    "email_addresses": re.compile(r"(?<![\w.@])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"),
    "cloud_access_key_candidates": re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])"),
}
MAX_XML_BYTES = 32 * 1024 * 1024
MAX_TOTAL_XML_BYTES = 128 * 1024 * 1024

@dataclass
class Audit:
    status: str = "incomplete"
    findings: dict[str, int] = field(default_factory=dict)
    flagged_parts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parts_scanned: int = 0
    xml_bytes_scanned: int = 0

    def as_dict(self) -> dict:
        return asdict(self)

def scan_ooxml(path: str | Path) -> Audit:
    """Inspect unencrypted OOXML conservatively. Never output matched content."""
    out = Audit()
    counts: Counter[str] = Counter()
    flagged: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            validate_package(archive)
            names = {i.filename for i in infos}
            if contains_signatures(names):
                counts["digitally_signed_package"] += 1
                flagged.update(n for n in names if '_xmlsignatures/' in n.lower())
            for info in infos:
                name = info.filename
                low = name.lower()
                if name.startswith("/") or "\\" in name or ".." in name.split("/"):
                    raise ValueError("unsafe package entry")
                if info.file_size > 1048576 and info.file_size > 200 * max(1, info.compress_size):
                    raise ValueError("suspicious compression ratio")
                for label, detected in (
                    ("vba_project_parts", low.endswith("/vbaproject.bin")),
                    ("embedded_objects", "/embeddings/" in low or low.startswith("embeddings/")),
                    ("metadata_parts", low.startswith("docprops/")),
                    ("collaboration_parts", "comment" in low or "/person" in low),
                ):
                    if detected:
                        counts[label] += 1
                        flagged.add(name)
                if not (low.endswith(".xml") or low.endswith(".rels") or name == "[Content_Types].xml"):
                    continue
                if info.file_size > MAX_XML_BYTES or out.xml_bytes_scanned + info.file_size > MAX_TOTAL_XML_BYTES:
                    raise ValueError("XML inspection size limit")
                data = archive.read(name)
                root = ET.fromstring(data)
                out.parts_scanned += 1
                out.xml_bytes_scanned += len(data)
                for elem in root.iter():
                    for value in [elem.text or "", *elem.attrib.values()]:
                        for label, regex in SENSITIVE.items():
                            hits = len(regex.findall(value))
                            if hits:
                                counts[label] += hits
                                flagged.add(name)
                    tag = elem.tag.rsplit("}", 1)[-1]
                    if tag in {"del", "ins", "moveFrom", "moveTo", "delText"}:
                        counts["tracked_change_nodes"] += 1
                        flagged.add(name)
                    if tag in {"vanish", "webHidden", "hidden"}:
                        counts["hidden_content_markers"] += 1
                        flagged.add(name)
                    if elem.tag == f"{{{REL_NS}}}Relationship" and elem.get("TargetMode") == "External":
                        counts["external_relationships"] += 1
                        flagged.add(name)
            out.status = "review_required" if counts else "no_indicators_detected"
            out.warnings.append("Indicator scan only: does not certify safe sharing, sanitize VBA or remove sensitive content")
    except (OSError, ValueError, RuntimeError, ET.ParseError, zipfile.BadZipFile) as exc:
        out.status = "incomplete"
        out.warnings.append(f"Inspection failed ({type(exc).__name__}); do not release this file")
    out.findings = dict(sorted(counts.items()))
    # Filenames inside the archive may contain sensitive data; emit opaque IDs.
    out.flagged_parts = sorted("part:" + hashlib.sha256(n.encode("utf-8")).hexdigest()[:16] for n in flagged)
    return out
