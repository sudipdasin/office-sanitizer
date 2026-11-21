#!/usr/bin/env bash
# Timestamp-controlled Debian package builder; no network or privilege required.
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${1:-4.1.0~beta1}"
OUT_DIR="${2:-dist}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(realpath "$OUT_DIR")"
PKG_DIR="$(mktemp -d)"
trap 'rm -rf "$PKG_DIR"' EXIT
install -d "$PKG_DIR/DEBIAN" "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/lib/python3/dist-packages/office_sanitizer" \
  "$PKG_DIR/usr/share/applications" "$PKG_DIR/usr/share/doc/office-sanitizer"
cp office_sanitizer/*.py "$PKG_DIR/usr/lib/python3/dist-packages/office_sanitizer/"
cp README.md LICENSE "$PKG_DIR/usr/share/doc/office-sanitizer/"
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: office-sanitizer
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: Office Sanitizer Community <noreply@invalid.example>
Depends: python3 (>= 3.10), python3-tk
Description: Offline Office document risk review and metadata-only sanitizer
 Privacy-first risk auditing and guarded OOXML metadata cleanup.
 It does not redact body content or certify confidential data clearance.
EOF
cat > "$PKG_DIR/usr/bin/office-sanitizer" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -m office_sanitizer "$@"
EOF
cat > "$PKG_DIR/usr/bin/office-sanitizer-gui" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -m office_sanitizer.gui "$@"
EOF
chmod 0755 "$PKG_DIR/usr/bin/office-sanitizer" "$PKG_DIR/usr/bin/office-sanitizer-gui"
cat > "$PKG_DIR/usr/share/applications/office-sanitizer.desktop" <<'EOF'
[Desktop Entry]
Name=Office Sanitizer
Comment=Offline Office privacy audit and metadata cleanup
Exec=office-sanitizer-gui
Terminal=false
Type=Application
Categories=Office;Utility;
EOF
find "$PKG_DIR" -exec touch -h -d '@946684800' {} +
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DIR/office-sanitizer_${VERSION}_all.deb" >/dev/null
printf 'Created %s\n' "$OUT_DIR/office-sanitizer_${VERSION}_all.deb"
