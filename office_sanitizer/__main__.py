import argparse
import json
from pathlib import Path
from . import __version__
from .core import sanitize

def main():
    parser = argparse.ArgumentParser(description=f"Office Sanitizer v{__version__}: metadata-only")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    statuses = []
    for path in args.files:
        result = sanitize(path, args.output / path.name)
        statuses.append(result.status)
        print(json.dumps({"file": path.name, **result.public_dict()}))
    return 0 if all(s == "metadata_cleaned_content_unreviewed" for s in statuses) else 1

if __name__ == "__main__":
    raise SystemExit(main())
