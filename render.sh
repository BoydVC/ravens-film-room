#!/usr/bin/env bash
# Screenshots with headless Chrome from the offline snapshot (+ live server if up). ?still=1 renders final animation state.
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-google-chrome}
SNAP="file://$PWD/dist/ravens-film-room-snapshot.html"
SCOUT="file://$PWD/dist/ravens-scouting-snapshot.html"
FLAGS=(--headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --virtual-time-budget=5000)
mkdir -p screenshots
shot(){ timeout 120 "$CHROME" "${FLAGS[@]}" --window-size="$2" --screenshot="$PWD/screenshots/$1.png" "$3" 2>/dev/null || echo "WARN: $1 timed out"; echo "screenshots/$1.png"; }
shot overview   1440,1500 "$SNAP?still=1"
shot full       1440,4200 "$SNAP?still=1"
shot week3-dal  1440,1500 "$SNAP?still=1&game=401872960"
shot week1-ind  1440,1500 "$SNAP?still=1&game=401872659"
shot mobile     430,2600  "$SNAP?still=1"
if [ -f dist/ravens-scouting-snapshot.html ]; then
  shot scout-overview 1440,1500 "$SCOUT?still=1"
  shot scout-full     1440,3350 "$SCOUT?still=1"
  shot scout-mobile   430,5200  "$SCOUT?still=1"
fi
if curl -sf http://127.0.0.1:4248/healthz >/dev/null; then
  shot live 1440,1500 "http://127.0.0.1:4248/?still=1"
  curl -sf http://127.0.0.1:4248/api/scout >/dev/null && shot scout-live 1440,1500 "http://127.0.0.1:4248/scout.html?still=1"
fi
