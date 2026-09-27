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
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
cd "$DIR"
# The page count follows the ISSUE constant in r000_issue.py, asked of the
# program itself rather than repeated here -- a second place to say how long the
# issue is is a second place to forget.  The literal 176 this replaces was
# 8609's, and would have run 24 pages past the end of a 152-page Sonderheft.
FIRST="${1:-1}"
LAST="${2:-$("$PY" -c 'import r010_ocr_blocks as m; print(m.ISS.pages)')}"
# Lanes: half the free RAM, capped by the cores -- r000_orchestration.md,
# *PARALLELISE TO HALF THE FREE RAM*.  1.5 GB a lane is MEASURED on 8611:
# RSS sampled every 5 s across a 28-lane run peaked at 1.03 GB for the python
# and 0.21 GB for its tesseract, so ~1.25 GB, and 1.5 is that plus margin.
# (The 3 GB that stood here first was a guess, and it was 2.4x too high.)
# At this size the cores cap always binds first, which is the point: the
# hardcoded -P 6 this replaces left 26 of 32 idle and made an 78-second job
# take a quarter of an hour.
LANES=$("$PY" -c 'import r000_issue; print(r000_issue.lanes(1.5))')
echo "r010: $LANES lanes (~1.5 GB each, measured; half the free RAM)" >&2
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P "$LANES" -n 8 "$PY" r010_ocr_blocks.py
"$PY" r010_blocks_index.py
