#!/bin/zsh
set -euo pipefail

# Usage: ./scripts/scrape_cc.sh [YEAR] [OUTDIR]
# Examples:
#   ./scripts/scrape_cc.sh          -> scrapes 2025 to tmp
#   ./scripts/scrape_cc.sh 2024     -> scrapes 2024 to tmp
#   ./scripts/scrape_cc.sh 2024 myout -> scrapes 2024 to myout

DEFAULT_YEAR=2025
DEFAULT_OUTDIR=tmp

YEAR=${1:-$DEFAULT_YEAR}
OUTDIR=${2:-$DEFAULT_OUTDIR}

# Resolve repo root (assumes script lives in repo/scripts)
SCRIPT_DIR=$(cd "$(dirname "$0")"/.. && pwd)

# Prefer repo virtualenv python if present
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
if [[ -x "$VENV_PYTHON" ]]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON=$(command -v python3 || command -v python)
fi

if [[ -z "$PYTHON" ]]; then
  echo "No python executable found in PATH and no .venv detected. Install Python or create .venv." >&2
  exit 2
fi

echo "Using python: $PYTHON"
echo "Scraping year: $YEAR -> output dir: $OUTDIR"

# Create outdir if missing
mkdir -p "$OUTDIR"

"$PYTHON" "$SCRIPT_DIR/tools/scrape_cc_catalog.py" --skip-placeholder --year "$YEAR" --outdir "$OUTDIR"

echo "Done. JSON -> $OUTDIR/cc_catalog.json, CSV -> $OUTDIR/cc.csv (unless --no-csv was used)." 
