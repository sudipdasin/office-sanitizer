#!/usr/bin/env bash
# Render static delivery only: no confidential documents, Actions or CircleCI.
set -euo pipefail
cd "$(dirname "$0")/.."
# Render initializes Python/Poetry with stdout messages on first invocation;
# use shell tools for version substitution to avoid capturing bootstrap logs.
VERSION="$(awk -F '"' '/^version = / {print $2; exit}' pyproject.toml)"
case "$VERSION" in *b[0-9]*) ;; *) echo "Invalid beta version" >&2; exit 1 ;; esac
DEB_VERSION="$(printf '%s' "$VERSION" | sed -E 's/b([0-9]+)$/~beta\1/')"
if [ "$DEB_VERSION" = "$VERSION" ]; then echo "Debian beta mapping failed" >&2; exit 1; fi
printf 'Building XFCE portal version: %s\n' "$VERSION"
OUT="$1"
mkdir -p "$OUT/downloads"
OUT="$(realpath "$OUT")"
bash scripts/build_deb.sh "$DEB_VERSION" "$OUT/downloads"
python scripts/build_wheel_offline.py --output "$OUT/downloads"
python scripts/build_source_archive.py --output "$OUT/downloads/office-sanitizer-$VERSION-source.zip"
python - "$OUT" "$VERSION" "$DEB_VERSION" <<'PY'
import hashlib,json,pathlib,sys,zipfile
root=pathlib.Path(sys.argv[1]); version=sys.argv[2]; debver=sys.argv[3]
files=[root/'downloads'/f'office-sanitizer_{debver}_all.deb', root/'downloads'/f'office-sanitizer-{version}-source.zip', root/'downloads'/f'office_sanitizer-{version}-py3-none-any.whl']
deb=f'office-sanitizer_{debver}_all.deb'
source=f'office-sanitizer-{version}-source.zip'
wheel=f'office_sanitizer-{version}-py3-none-any.whl'
if any(name not in {p.name for p in files} for name in (deb,source,wheel)):
    raise SystemExit('A required distribution artifact is missing')
for p in files:
    if p.suffix in ('.zip','.whl'):
        with zipfile.ZipFile(p) as check:
            if check.testzip() is not None: raise SystemExit('Artifact integrity failure')
checksums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root/'downloads'/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name,value in checksums.items()))
release={'version':version,'channel':'beta','status':'human_review_required',
 'debian':{'name':deb,'url':'/downloads/'+deb,'size':(root/'downloads'/deb).stat().st_size,'sha256':checksums[deb]},
 'wheel':{'name':wheel,'url':'/downloads/'+wheel,'sha256':checksums[wheel]},
 'source':{'name':source,'url':'/downloads/'+source,'sha256':checksums[source]},
 'disclaimer':'Metadata-only: confidential documents require authorized human review.'}
(root/'release.json').write_text(json.dumps(release,indent=2)+'\n')
for name in ('styles.css','app.js'):
    (root/name).write_bytes((pathlib.Path('site')/name).read_bytes())
html=(pathlib.Path('site')/'index.html').read_text()
for placeholder,replacement in {'%%VERSION%%':version,'%%DEB_FILE%%':deb,'%%WHEEL_FILE%%':wheel,'%%ZIP_FILE%%':source}.items():
    html=html.replace(placeholder,replacement)
if '%%' in html: raise SystemExit('Unresolved website placeholder')
(root/'index.html').write_text(html)
print('Static XFCE release portal built:',root)
PY
