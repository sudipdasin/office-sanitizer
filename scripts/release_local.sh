#!/usr/bin/env bash
# Local release builder. Never calls CI services and never accesses networks.
set -euo pipefail
cd "$(dirname "$0")/.."
export SOURCE_DATE_EPOCH=1577836800
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
VERSION="$(python -c 'from office_sanitizer import __version__;print(__version__)')"
DEB_VERSION="$(python - "$VERSION" <<'PY'
import re,sys
v=sys.argv[1]
m=re.fullmatch(r'(\d+\.\d+\.\d+)b(\d+)',v)
if not m:
 raise SystemExit('Refusing non-beta package version')
print(m.group(1)+'~beta'+m.group(2))
PY
)"
OUT="$1"
mkdir -p "$OUT"
OUT="$(realpath "$OUT")"
python -m compileall -q office_sanitizer tests scripts
python -m pytest -q
python scripts/build_wheel_offline.py --output "$OUT"
bash scripts/build_deb.sh "$DEB_VERSION" "$OUT"
python scripts/build_source_archive.py --output "$OUT/office-sanitizer-$VERSION-source.zip"
python - "$OUT" "$VERSION" "$DEB_VERSION" <<'PY'
import hashlib, pathlib, sys, zipfile, subprocess
out=pathlib.Path(sys.argv[1]); version=sys.argv[2]; deb_version=sys.argv[3]
files=[out/f'office-sanitizer_{deb_version}_all.deb',
       out/f'office_sanitizer-{version}-py3-none-any.whl',
       out/f'office-sanitizer-{version}-source.zip']
for file in files:
    if not file.is_file(): raise SystemExit(f'Expected artifact missing: {file.name}')
    if file.suffix in ('.zip','.whl'):
        with zipfile.ZipFile(file) as z:
            if z.testzip(): raise SystemExit('ZIP integrity failure')
subprocess.run(['dpkg-deb','--info',str(files[0])],capture_output=True,check=True)
(out/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}\n' for file in files))
print('Offline artifacts verified, checksums written to',out/'SHA256SUMS')
PY
