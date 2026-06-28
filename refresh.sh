#!/usr/bin/env bash
# Project 2:35 — pull fresh Garmin data, validate it, push to GitHub Pages.
# Usage:  ./refresh.sh
set -euo pipefail

cd "$(dirname "$0")"          # always run from the project folder

echo "==> activating venv"
source .venv/bin/activate

echo "==> fetching runs (you may be prompted for password / MFA)"
python3 fetch_runs.py

echo "==> fetching Garmin race predictions"
python3 fetch_predictions.py

echo "==> validating data before deploy"
python3 - <<'PY'
import json, sys
for fn in ("runs.json", "predictions.json"):
    try:
        data = json.load(open(fn))
    except Exception as e:
        sys.exit(f"FAIL: {fn} missing or invalid ({e}) — not deploying")
    if not data:
        sys.exit(f"FAIL: {fn} is empty — not deploying")
    print(f"ok: {fn} ({len(data)} records)")
PY

# only deploy if the data actually changed
if git diff --quiet -- runs.json predictions.json; then
    echo "==> no new data; nothing to deploy"
    exit 0
fi

echo "==> committing + pushing"
git add runs.json predictions.json
git commit -m "refresh data $(date +%Y-%m-%d)"
git push

echo "==> done. GitHub Pages will rebuild in about a minute."