#!/bin/bash
# Step 030 -- put the pages back together into articles, write <YYMM>.md.
# One model call for the whole issue; everything else here is deterministic.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
cd "$DIR"
"$PY" r030_assemble.py
