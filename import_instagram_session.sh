#!/bin/bash
# Import Instagram login from browser cookies (no password).
# Usage: bash import_instagram_session.sh auto
#        bash import_instagram_session.sh firefox
#        bash import_instagram_session.sh list
#        bash import_instagram_session.sh cookie /path/to/cookies.sqlite elena_03821

set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python3"
MODE="${1:-firefox}"
ARG2="${2:-}"
ARG3="${3:-}"

if [[ ! -x "$PY" ]]; then
  echo "  ✗ Missing .venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

case "$MODE" in
  list)
    "$PY" import_instagram_session.py --list-profiles
    ;;
  auto)
    ARGS=(--auto)
    [[ -n "$ARG2" ]] && ARGS+=(--username "$ARG2")
    "$PY" import_instagram_session.py "${ARGS[@]}"
    ;;
  cookie)
    [[ -n "$ARG2" ]] || { echo "  Usage: bash import_instagram_session.sh cookie /path/to/cookies.sqlite [username]"; exit 1; }
    ARGS=(--browser firefox --cookie-file "$ARG2")
    [[ -n "$ARG3" ]] && ARGS+=(--username "$ARG3")
    "$PY" import_instagram_session.py "${ARGS[@]}"
    ;;
  *)
    ARGS=(--browser "$MODE")
    [[ -n "$ARG2" ]] && ARGS+=(--username "$ARG2")
    "$PY" import_instagram_session.py "${ARGS[@]}"
    ;;
esac
