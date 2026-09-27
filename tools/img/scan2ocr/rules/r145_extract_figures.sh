#!/bin/bash
# Step 145 -- cut the article figures out of the graded masters.
#
# Three programs, because the work splits cleanly in two and the split is the
# point: geometry MEASURES rectangles, a model JUDGES which are figures.
#   r145_extract_figures.py   candidate rectangles + evidence, per page
#   r145_judge_figures.py     one model call per page: which are figures
#   r145_name_figures.py      named crops, sorted for tools/convert-scans.sh
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
cd "$DIR"
# The page count follows the chain's ISSUE constant, asked of the program
# rather than repeated here -- the literal 176 this replaces was 8609's, and
# would have run 24 pages past the end of a 152-page Sonderheft.
# Lanes: half the free RAM, capped by the cores -- r000_orchestration.md,
# *PARALLELISE TO HALF THE FREE RAM*.  3 GB a lane is STILL A GUESS (a 600 dpi
# master plus the cut-out); take the real peak off the next run with
# `ps -axo rss,comm | sort -rn | head` while it is going, and put it here.
# For scale, r010 holds the same kind of page and MEASURED 1.25 GB, so this is
# probably high -- but a guess that is written down as one is not a lie, and at
# this size the cores cap binds first either way.
LANES=$("$PY" -c 'import r000_issue; print(r000_issue.lanes(3))')
echo "r145: $LANES lanes (~3 GB each, A GUESS; half the free RAM)" >&2
seq "${1:-1}" "${2:-$("$PY" -c 'import r010_ocr_blocks as m; print(m.ISS.pages)')}" | OMP_NUM_THREADS=1 xargs -P "$LANES" -n 8 "$PY" r145_extract_figures.py
"$PY" r145_judge_figures.py
"$PY" r145_name_figures.py
