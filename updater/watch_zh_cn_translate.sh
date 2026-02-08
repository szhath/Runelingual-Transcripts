#!/usr/bin/env bash
set -euo pipefail

BASE="/Users/sage/.openclaw/workspace/Runelingual-Transcripts"
UPDATER="$BASE/updater"
LOG="$BASE/logs/zh_cn_translate.log"
PIDFILE="$BASE/logs/zh_cn_translate.pid"
MONLOG="$BASE/logs/zh_cn_watchdog.log"

mkdir -p "$BASE/logs"

start_job() {
  nohup bash -lc "cd '$UPDATER' && PYTHONUNBUFFERED=1 ZH_MAX_NEW=0 ZH_BATCH_SIZE=25 ZH_SLEEP_SEC=0.15 python3 translate_zh_cn_pinyin.py >> '$LOG' 2>&1" >/dev/null 2>&1 &
  echo $! > "$PIDFILE"
  echo "[$(date '+%F %T')] started translator pid $(cat "$PIDFILE")" >> "$MONLOG"
}

is_running() {
  [[ -f "$PIDFILE" ]] || return 1
  local pid
  pid=$(cat "$PIDFILE" 2>/dev/null || true)
  [[ -n "${pid:-}" ]] || return 1
  ps -p "$pid" >/dev/null 2>&1
}

if ! is_running; then
  start_job
fi

last_checked_line=0
while true; do
  if ! is_running; then
    echo "[$(date '+%F %T')] pid missing/dead, restarting" >> "$MONLOG"
    start_job
  fi

  if [[ -f "$LOG" ]]; then
    total_lines=$(wc -l < "$LOG" || echo 0)
    if (( total_lines > last_checked_line )); then
      new_chunk=$(sed -n "$((last_checked_line+1)),$((total_lines))p" "$LOG" 2>/dev/null || true)
      if echo "$new_chunk" | grep -q "AttributeError: 'NoneType' object has no attribute 'strip'"; then
        if is_running; then
          kill "$(cat "$PIDFILE")" >/dev/null 2>&1 || true
        fi
        echo "[$(date '+%F %T')] detected NoneType error; restarting" >> "$MONLOG"
        start_job
      fi
      last_checked_line=$total_lines
    fi
  fi

  sleep 20
done
