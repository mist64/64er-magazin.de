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
seq "${1:-1}" "${2:-176}" | OMP_NUM_THREADS=1 xargs -P 6 -n 8 "$PY" r145_extract_figures.py
"$PY" r145_judge_figures.py
"$PY" r145_name_figures.py
