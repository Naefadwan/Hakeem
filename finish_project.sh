#!/bin/bash
# One-shot local setup: decor import, HTML sync, DJ sync (no Instagram API).
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python3"

echo "  ▸ Import new-set → decor sets"
"$PY" import_new_set.py

echo "  ▸ Seed decor titles"
"$PY" seed_decor_meta.py

echo "  ▸ Sync index.html collections + DJ data"
"$PY" update_html_collections.py
"$PY" update_dj_content.py

echo ""
echo "  ✓ Project assets synced. Open index.html or push for GitHub Pages."
