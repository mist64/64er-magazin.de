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
cd "$DIR"
# The page count follows the ISSUE constant in r010_ocr_blocks.py, asked of the
# program itself rather than repeated here -- a second place to say how long the
# issue is is a second place to forget.  The literal 176 this replaces was
# 8609's, and would have run 24 pages past the end of a 152-page Sonderheft.
FIRST="${1:-1}"
LAST="${2:-$("$PY" -c 'import r010_ocr_blocks as m; print(m.ISS.pages)')}"
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P 6 -n 8 "$PY" r010_ocr_blocks.py
"$PY" r010_blocks_index.py
