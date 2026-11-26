#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${1:-4.3.0~beta2}"
OUT_DIR="${2:-dist}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(realpath "$OUT_DIR")"
PKG_DIR="$(mktemp -d)"
trap 'rm -rf "$PKG_DIR"' EXIT
install -d "$PKG_DIR/DEBIAN" "$PKG_DIR/usr/bin" \
 "$PKG_DIR/usr/lib/python3/dist-packages/office_sanitizer" \
 "$PKG_DIR/usr/share/applications" "$PKG_DIR/etc/xdg/autostart" \
 "$PKG_DIR/usr/share/doc/office-sanitizer" "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"
cp office_sanitizer/*.py "$PKG_DIR/usr/lib/python3/dist-packages/office_sanitizer/"
cp README.md LICENSE "$PKG_DIR/usr/share/doc/office-sanitizer/"
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: office-sanitizer
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: Office Sanitizer Community <noreply@invalid.example>
Depends: python3 (>= 3.10), python3-tk, python3-gi, libnotify-bin, policykit-1 | polkitd
Recommends: xfce4-terminal
Description: Office Sanitizer XFCE privacy audit and metadata review
 Offline document-risk inspection, fail-closed metadata-only cleaning,
 and opt-in authenticated Debian update support. Does not redact content.
EOF
for entry in office-sanitizer office-sanitizer-gui office-sanitizer-update; do
  case "$entry" in
    office-sanitizer) mod=office_sanitizer ;;
    office-sanitizer-gui) mod=office_sanitizer.gui ;;
    office-sanitizer-update) mod=office_sanitizer.updater ;;
  esac
  printf '#!/bin/sh\nexec /usr/bin/python3 -m %s "$@"\n' "$mod" > "$PKG_DIR/usr/bin/$entry"
  chmod 0755 "$PKG_DIR/usr/bin/$entry"
done
cat > "$PKG_DIR/usr/share/applications/office-sanitizer.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Office Sanitizer
GenericName=Office Document Privacy Review
Comment=Offline Office metadata and risk inspection
Exec=office-sanitizer-gui
Icon=office-sanitizer
Terminal=false
Categories=Office;Utility;
StartupNotify=true
Keywords=Office;Document;Privacy;Audit;
EOF
cat > "$PKG_DIR/etc/xdg/autostart/office-sanitizer-update.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Office Sanitizer Update Check
Comment=Check for verified releases once a day at XFCE login
Exec=office-sanitizer-update --notify
Terminal=false
NoDisplay=true
OnlyShowIn=XFCE;
X-GNOME-Autostart-enabled=true
EOF
cat > "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/office-sanitizer.svg" <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
 <rect x="14" y="7" width="100" height="114" rx="14" fill="#185d7a"/>
 <path d="M38 30h52M38 48h52M38 66h34" stroke="#f4f9fc" stroke-width="7" stroke-linecap="round"/>
 <circle cx="78" cy="89" r="20" fill="#ffffff"/>
 <path d="m68 89 7 7 15-17" stroke="#268556" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
EOF
find "$PKG_DIR" -exec touch -h -d '@946684800' {} +
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DIR/office-sanitizer_${VERSION}_all.deb" >/dev/null
printf 'Created %s\n' "$OUT_DIR/office-sanitizer_${VERSION}_all.deb"
