#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/build/appimage"
APPDIR="$BUILD_DIR/AppDir"
DIST_DIR="$BUILD_DIR/dist"
VENV_DIR="$BUILD_DIR/venv"

if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "This build script currently supports x86_64 Linux only." >&2
    exit 1
fi

if ! command -v xdotool >/dev/null 2>&1; then
    echo "xdotool is required to build the AppImage. Install it with: sudo apt install xdotool" >&2
    exit 1
fi

mkdir -p "$BUILD_DIR" "$DIST_DIR"
python3 -m venv --system-site-packages "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip pyinstaller
"$VENV_DIR/bin/python" -m PyInstaller \
    --noconfirm --clean --onedir --name HomeKeyClicker \
    --specpath "$BUILD_DIR/spec" \
    --workpath "$BUILD_DIR/work" \
    --distpath "$BUILD_DIR/pyinstaller-dist" \
    "$ROOT_DIR/home_key_clicker.py"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp -a "$BUILD_DIR/pyinstaller-dist/HomeKeyClicker" "$APPDIR/usr/lib/home-key-clicker"
cp "$(command -v xdotool)" "$APPDIR/usr/bin/xdotool"

# Bundle xdotool's non-glibc libraries so it runs on systems without xdotool installed.
while IFS= read -r library; do
    [[ -f "$library" ]] || continue
    case "$(basename "$library")" in
        libc.so*|libm.so*|libpthread.so*|libdl.so*|librt.so*|ld-linux*) continue ;;
    esac
    cp -L "$library" "$APPDIR/usr/lib/$(basename "$library")"
done < <(ldd "$(command -v xdotool)" | awk '{ for (i = 1; i <= NF; i++) if ($i ~ /^\//) { print $i; break } }')

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HERE/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$HERE/usr/lib/home-key-clicker/HomeKeyClicker" "$@"
APPRUN
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/xdotool"

cat > "$APPDIR/home-key-clicker.desktop" <<'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Home Key Clicker
Comment=Send the Home key to selected windows on a timer
Exec=AppRun
Icon=home-key-clicker
Terminal=false
Categories=Utility;
DESKTOP

cat > "$APPDIR/home-key-clicker.svg" <<'ICON'
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect x="8" y="14" width="112" height="100" rx="18" fill="#18212d"/>
  <rect x="22" y="28" width="84" height="70" rx="12" fill="#10151d" stroke="#38bdf8" stroke-width="4"/>
  <path d="M40 54h48M40 70h48" stroke="#526579" stroke-width="6" stroke-linecap="round"/>
  <rect x="43" y="78" width="42" height="12" rx="5" fill="#38bdf8"/>
  <text x="64" y="88" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="700" fill="#082f49">HOME</text>
</svg>
ICON
cp "$APPDIR/home-key-clicker.svg" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps/home-key-clicker.svg"

APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"
if [[ ! -x "$APPIMAGETOOL" ]]; then
    curl --fail --location --retry 3 \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        --output "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

OUTPUT="$DIST_DIR/HomeKeyClicker-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$OUTPUT"
echo "Built $OUTPUT"
