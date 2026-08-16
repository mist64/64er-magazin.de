#!/bin/bash
# Step 030 -- put the pages back together into articles, write <YYMM>.md.
# One model call for the whole issue; everything else here is deterministic.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
cd "$DIR"
"$PY" 030_assemble.py
