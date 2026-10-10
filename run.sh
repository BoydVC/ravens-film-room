#!/usr/bin/env bash
# Ravens Film Room: ./run.sh start|stop|restart|status|fetch|build|test|shot
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-4275}"; PID=data/server.pid; LOG=data/server.log
running(){ [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }
case "${1:-start}" in
  start)
    if running; then echo "already running (pid $(cat $PID)) on http://127.0.0.1:$PORT"; exit 0; fi
    [ -f data/research.json ] || python3 build_research.py
    [ -f data/film.json ] || python3 build_data.py
    [ -f data/scout.json ] || python3 build_scout.py
    PORT="$PORT" nohup python3 server.py >>"$LOG" 2>&1 &
    echo $! > "$PID"; sleep 0.6
    running && echo "started pid $(cat $PID) → http://127.0.0.1:$PORT" || { echo "failed; see $LOG"; exit 1; } ;;
  stop) if running; then kill "$(cat $PID)" 2>/dev/null || true; rm -f "$PID"; echo stopped; else echo "not running"; fi ;;
  restart) "$0" stop || true; sleep 0.3; "$0" start ;;
  status) if running; then echo "running pid $(cat $PID) → http://127.0.0.1:$PORT"; else echo "stopped"; fi ;;
  build) python3 build_research.py && python3 build_data.py && python3 build_scout.py && python3 export_snapshot.py && ./screenshot.sh ;;
  fetch) python3 fetch.py && "$0" build ;;
  test) python3 tests/smoke_test.py ;;
  shot) ./screenshot.sh ;;
  *) echo "usage: $0 start|stop|restart|status|fetch|build|test|shot"; exit 2 ;;
esac
