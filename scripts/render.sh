#!/usr/bin/env bash
# Aufruf: render.sh <ausgabe.png> <ENGINE> <samples> <prozent> [kamera] [modus]
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b "${BLEND:-$DIR/../garten.blend}" -P "$DIR/render_cli.py" -- "$@"
