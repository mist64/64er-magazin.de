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
PY="${PYTHON:-python3}"
cd "$DIR"
# The page count follows the chain's ISSUE constant, asked of the program
# rather than repeated here -- the literal 176 this replaces was 8609's, and
# would have run 24 pages past the end of a 152-page Sonderheft.
# Lanes: half the free RAM, capped by the cores -- r000_orchestration.md,
# *PARALLELISE TO HALF THE FREE RAM*. 3 GB a lane is a CONSERVATIVE GUESS
# (a 600 dpi master plus the cut-out), not a measurement: take the real peak off the next
# run with `ps -axo rss,comm` and put it here. The hardcoded -P 6 this
# replaces left 26 of 32 cores idle.
LANES=$("$PY" -c 'import r000_issue; print(r000_issue.lanes(3))')
echo "$(basename "$0"): $LANES lanes" >&2
seq "${1:-1}" "${2:-$("$PY" -c 'import r010_ocr_blocks as m; print(m.ISS.pages)')}" | OMP_NUM_THREADS=1 xargs -P "$LANES" -n 8 "$PY" r145_extract_figures.py
"$PY" r145_judge_figures.py
"$PY" r145_name_figures.py
