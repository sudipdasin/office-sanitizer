"""Office Sanitizer CLI. All outputs are privacy-safe summaries."""
import argparse
import json
from pathlib import Path
from . import __version__
from .core import sanitize
from .audit import scan_ooxml
from .verify import verify_output
from .workflow import guarded_sanitize

def main():
    parser = argparse.ArgumentParser(description=f"Office Sanitizer v{__version__} — risk audit or metadata-only cleanup")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="Required for sanitization; omitted for audit")
    parser.add_argument("--audit", action="store_true", help="Read-only risk inspection (no file output)")
    parser.add_argument("--verify-output", type=Path, help="Independently verify one sanitized file against one original")
    parser.add_argument("--guarded", action="store_true", help="Preflight, clean and independently verify; block risky inputs")
    args = parser.parse_args()
    if args.verify_output is not None:
        if len(args.files) != 1 or args.audit or args.guarded or args.output is not None:
            parser.error("--verify-output requires exactly one original file and no --audit/--output")
        checked = verify_output(args.files[0], args.verify_output)
        print(json.dumps(checked.as_dict()))
        return 0 if checked.status == "package_integrity_verified_content_unreviewed" else 1
    if args.audit and args.guarded:
        parser.error("--audit and --guarded cannot be combined")
    if not args.audit and args.output is None:
        parser.error("--output is required for sanitization; use --audit for read-only inspection")
    if args.output is not None and not args.audit:
        args.output.mkdir(parents=True, exist_ok=True)
    complete = True
    for path in args.files:
        if args.audit:
            report = scan_ooxml(path)
            print(json.dumps({"file_name": path.name, **report.as_dict()}))
            complete = complete and report.status != "incomplete"
        elif args.guarded:
            result = guarded_sanitize(path, args.output / path.name)
            print(json.dumps({"result": result.as_dict()}))
            complete = complete and result.status == "metadata_only_copy_requires_human_review"
        else:
            result = sanitize(path, args.output / path.name)
            print(json.dumps({"file_name": path.name, **result.public_dict()}))
            complete = complete and result.status == "metadata_cleaned_content_unreviewed"
    return 0 if complete else 1

if __name__ == "__main__":
    raise SystemExit(main())
