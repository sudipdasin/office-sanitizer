"""Non-destructive Office Open XML indicator audit. No document text in output."""
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib
from xml.etree import ElementTree as ET
import re
import zipfile
from .security import validate_package, contains_signatures
from .exposure import package_exposures, xml_exposures

# Review-only marking heuristic, never proof of document classification.
MARKING = re.compile(r"(?i)\b(?:TOP[\s-]+SECRET|SECRET[\s-]+NOFORN|CONFIDENTIAL|OFFICIAL[\s-]+SENSITIVE|CONTROLLED[\s-]+UNCLASSIFIED[\s-]+INFORMATION)\b")
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
            if archive.comment:
                counts["zip_archive_comment"] += 1
            validate_package(archive)
            names = {i.filename for i in infos}
            if contains_signatures(names):
                counts["digitally_signed_package"] += 1
                flagged.update(n for n in names if '_xmlsignatures/' in n.lower())
            for info in infos:
                name = info.filename
                exposure_counts = package_exposures(name)
                counts.update(exposure_counts)
                if exposure_counts:
                    flagged.add(name)
                low = name.lower()
                if info.comment:
                    counts["zip_member_comments"] += 1
                    flagged.add(name)
                if info.extra:
                    counts["zip_member_extra_fields"] += 1
                    flagged.add(name)
                if info.date_time != (1980, 1, 1, 0, 0, 0):
                    counts["zip_member_timestamps"] += 1
                    flagged.add(name)
                # A package member filename can itself carry private data.
                for indicator, pattern in SENSITIVE.items():
                    if pattern.search(name):
                        counts["zip_filename_" + indicator] += 1
                        flagged.add(name)
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
                xml_risks = xml_exposures(name, root)
                counts.update(xml_risks)
                if xml_risks:
                    flagged.add(name)
                out.parts_scanned += 1
                out.xml_bytes_scanned += len(data)
                # Join XML text runs so split Office-formatted values can
                # be detected. This is heuristic, not full content validation.
                combined_text = "".join(root.itertext())
                for label, regex in SENSITIVE.items():
                    hits = len(regex.findall(combined_text))
                    if hits:
                        counts[label] += hits
                        flagged.add(name)
                markings = len(MARKING.findall(combined_text))
                if markings:
                    counts["classification_marking_candidates"] += markings
                    flagged.add(name)
                for elem in root.iter():
                    for value in elem.attrib.values():
                        for label, regex in SENSITIVE.items():
                            hits = len(regex.findall(value))
                            if hits:
                                counts[label] += hits
                                flagged.add(name)
                        markings = len(MARKING.findall(value))
                        if markings:
                            counts["classification_marking_candidates"] += markings
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
            # Timestamps alone are a removable container-metadata signal,
            # not a reason to block an otherwise clean metadata-only workflow.
            actionable = {k: v for k, v in counts.items()
                          if k not in {"zip_member_timestamps"} and v > 0}
            out.status = "review_required" if actionable else "no_indicators_detected"
            out.warnings.append("Indicator scan only: does not certify safe sharing, sanitize VBA or remove sensitive content")
    except (OSError, ValueError, RuntimeError, ET.ParseError, zipfile.BadZipFile) as exc:
        out.status = "incomplete"
        out.warnings.append(f"Inspection failed ({type(exc).__name__}); do not release this file")
    out.findings = dict(sorted(counts.items()))
    # Filenames inside the archive may contain sensitive data; emit opaque IDs.
    out.flagged_parts = sorted("part:" + hashlib.sha256(n.encode("utf-8")).hexdigest()[:16] for n in flagged)
    return out
