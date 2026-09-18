#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  BAZEEVENT — Sync decor + DJ content from Instagram
#
#  Required (avoids HTTP 429 rate limits):
#    Log in at instagram.com in Firefox/Chrome, then (no password):
#    bash import_instagram_session.sh firefox
#    export INSTAGRAM_USERNAME=your_ig_login
#
#  Usage:
#    bash sync_instagram.sh
#    bash sync_instagram.sh --decor-only --decor-max 5
#    bash sync_instagram.sh --dj-only --dj-max 10 --dj-replace
#    bash sync_instagram.sh --allow-anonymous   # not recommended
# ═══════════════════════════════════════════════════════════

set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python3"
if [[ ! -x "$PY" ]]; then
  echo "  ✗ Missing .venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

DECOR_MAX=15
DJ_MAX=20
DOWNLOAD_VIDEOS=""
DJ_REPLACE=""
ALLOW_ANON=""
RUN_DECOR=1
RUN_DJ=1
PAUSE="${INSTAGRAM_SYNC_PAUSE:-90}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --decor-max) DECOR_MAX="$2"; shift 2 ;;
    --dj-max) DJ_MAX="$2"; shift 2 ;;
    --download-videos) DOWNLOAD_VIDEOS="--download-videos"; shift ;;
    --dj-replace) DJ_REPLACE="--replace"; shift ;;
    --allow-anonymous) ALLOW_ANON="--allow-anonymous"; shift ;;
    --decor-only) RUN_DJ=0; shift ;;
    --dj-only) RUN_DECOR=0; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

ANON_ARGS=()
if [[ -n "$ALLOW_ANON" ]]; then
  ANON_ARGS=("$ALLOW_ANON")
fi

if [[ -z "${INSTAGRAM_USERNAME:-}" ]] || [[ ! -f ".instagram/session-${INSTAGRAM_USERNAME}" ]]; then
  if [[ -z "$ALLOW_ANON" ]]; then
    echo ""
    echo "  ✗ Set up Instagram login before syncing (anonymous mode gets 429 easily)."
    echo "    Log in at instagram.com, quit browser, then:"
    echo "    bash import_instagram_session.sh firefox"
    echo "    export INSTAGRAM_USERNAME=your_ig_login"
    echo ""
    echo "  If you were just rate-limited, wait 15–60 minutes, then retry."
    echo "  To force anonymous anyway: bash sync_instagram.sh --allow-anonymous"
    exit 1
  fi
fi

if [[ "$RUN_DECOR" -eq 1 ]]; then
  echo ""
  echo "  ▸ Decor ← @bazevents20"
  "$PY" fetch_instagram_decor.py --max-posts "$DECOR_MAX" "${ANON_ARGS[@]}"
fi

if [[ "$RUN_DECOR" -eq 1 && "$RUN_DJ" -eq 1 ]]; then
  echo ""
  echo "  ⏸ Pausing ${PAUSE}s before DJ sync (reduces 429)…"
  sleep "$PAUSE"
fi

if [[ "$RUN_DJ" -eq 1 ]]; then
  echo ""
  echo "  ▸ DJ ← @fatoomdyab.dj"
  "$PY" fetch_instagram_dj.py --max-posts "$DJ_MAX" $DOWNLOAD_VIDEOS $DJ_REPLACE "${ANON_ARGS[@]}"
fi

if [[ "$RUN_DECOR" -eq 1 || "$RUN_DJ" -eq 1 ]]; then
  echo ""
  echo "  ▸ Updating index.html"
  "$PY" update_html_collections.py
  "$PY" update_dj_content.py
fi

echo ""
echo "  ✓ Done. Open index.html in a browser to review."
