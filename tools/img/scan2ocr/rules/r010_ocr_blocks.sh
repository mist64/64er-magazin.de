#!/bin/bash
# Step 010 -- OCR the scans into measured blocks, then build the block index.
#
# The programs sit beside this script and share its name -- the r prefix is what
# lets them, since a Python module name cannot start with a digit.  This wrapper
# is the numbered entry point, and it carries the
# invocation the rule documents -- the parallelism in particular, which is not
# a detail: numpy stages want OMP_NUM_THREADS=1 and many lanes, and this box is
# shared with a job that swap-thrashes if crowded.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
FIRST="${1:-1}"
LAST="${2:-176}"
cd "$DIR"
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P 6 -n 8 "$PY" r010_ocr_blocks.py
"$PY" r010_blocks_index.py
