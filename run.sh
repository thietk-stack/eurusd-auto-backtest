#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export FROM="${FROM:-2010-01-01}"
export TO="${TO:-2026-10-30}"
export OOS="${OOS:-2015-01-01}"
mkdir -p data results
echo "EU/USD HISTORICAL DATA DOWNLOAD: source Dukascopy, NOT Exness trade records."
if [ ! -d node_modules ]; then npm install --no-audit --no-fund; fi
python3 -m pip install -r requirements.txt
node scripts/download.mjs
python3 scripts/real_backtest.py --data-dir data --from "$FROM" --to "$TO" --oos "$OOS" --target 2000 --out results
