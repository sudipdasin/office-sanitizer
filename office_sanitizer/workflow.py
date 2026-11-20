"""Guarded local workflow: preflight -> metadata clean -> integrity -> postflight.

Never constitutes classification clearance, document redaction, or safe-sharing approval.
Reports contain indicator counts rather than matched values or filesystem paths.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from .audit import scan_ooxml
from .core import sanitize
from .verify import verify_output


@dataclass
class WorkflowResult:
    status: str = "blocked"
    reason_codes: list[str] = field(default_factory=list)
    before_findings: dict[str, int] = field(default_factory=dict)
    after_findings: dict[str, int] = field(default_factory=dict)
    verified: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def guarded_sanitize(source: str | Path, output: str | Path) -> WorkflowResult:
    """Generate metadata-only copy only when preflight has no nonmetadata indicators.

    Output still requires manual review. Existing outputs and originals are not overwritten.
    """
    result = WorkflowResult()
    src, dst = Path(source), Path(output)
    if dst.exists() or dst.is_symlink():
        result.reason_codes.append("destination_exists")
        return result
    pre = scan_ooxml(src)
    result.before_findings = pre.findings
    if pre.status == "incomplete":
        result.reason_codes.append("preflight_incomplete")
        return result
    removable_metadata_indicators = {
        "metadata_parts", "zip_member_timestamps", "zip_member_comments",
        "zip_member_extra_fields", "zip_archive_comment",
    }
    risky = {key: value for key, value in pre.findings.items()
             if key not in removable_metadata_indicators and value > 0}
    if risky:
        result.reason_codes.append("preflight_indicators_require_review")
        return result
    cleaned = sanitize(src, dst)
    if cleaned.status != "metadata_cleaned_content_unreviewed":
        result.reason_codes.append("sanitize_failed")
        return result
    check = verify_output(src, dst)
    post = scan_ooxml(dst)
    result.after_findings = post.findings
    result.verified = (check.status == "package_integrity_verified_content_unreviewed"
                       and post.status != "incomplete")
    if not result.verified:
        try:
            dst.unlink()
        except OSError:
            result.reason_codes.append("unsafe_output_cleanup_failed")
        result.reason_codes.append("postflight_failed")
        return result
    if any(v > 0 for k, v in post.findings.items() if k not in removable_metadata_indicators):
        try:
            dst.unlink()
        except OSError:
            result.reason_codes.append("unsafe_output_cleanup_failed")
        result.verified = False
        result.reason_codes.append("postflight_indicators_require_review")
        return result
    result.status = "metadata_only_copy_requires_human_review"
    result.reason_codes.append("not_a_confidentiality_clearance")
    return result
