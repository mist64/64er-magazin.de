#!/bin/bash
# Step 020 -- label every block, decide reading order, render per-page markdown.
# One model call per uncached page; the program self-parallelises.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
cd "$DIR"
"$PY" r020_classify.py $(seq "${1:-1}" "${2:-176}")
