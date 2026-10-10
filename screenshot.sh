#!/usr/bin/env bash
# Screenshots + 00-best-home.png (headless Chrome). Prefers offline snapshot for the hero shot.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-4275}"
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser)"
mkdir -p screenshots dist
shot() {
  local url="$1" out="$2" size="$3"; shift 3 || true
  local prof; prof="$(mktemp -d /tmp/ravshot.XXXX)"
  "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --run-all-compositor-stages-before-draw --virtual-time-budget=14000 \
    --window-size="$size" --user-data-dir="$prof" --screenshot="$out" "$@" "$url" >/dev/null 2>&1
  rm -rf "$prof"; echo "  $out ($(wc -c < "$out") bytes)"
}
# Ensure offline hub exists
python3 export_snapshot.py
SNAP="file://$PWD/dist/ravens-film-room-snapshot.html"
shot "$SNAP?still=1&screen=war" screenshots/00-best-home.png 1440,1100
shot "$SNAP?still=1&screen=injuries" screenshots/01-injury-board.png 1440,1100
shot "$SNAP?still=1&screen=depth" screenshots/02-depth-chart.png 1440,1100
shot "$SNAP?still=1&screen=notes" screenshots/03-film-notes.png 1440,1200
shot "$SNAP?still=1&screen=film" screenshots/04-film-room.png 1440,1100
shot "$SNAP?still=1&screen=next" screenshots/05-next-game.png 1440,1100
if curl -fs "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
  U="http://127.0.0.1:$PORT"
  shot "$U/?still=1&screen=war" screenshots/06-live-war.png 1440,1100
fi
echo "screenshots done"
