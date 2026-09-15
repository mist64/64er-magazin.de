#!/bin/bash
# Step 005, SPREAD variant -- measure every page in parallel, then cut.
#
# measure is ~4-5 min a page in one lane (the 900 MB PNG decode, the 2400 dpi
# rotation, the separator) and holds a 2400 dpi RGB sheet, ~1.7 GB, plus the
# separator's own copy.  6 lanes: this box has 32 cores and 550 GB, so memory
# is not the bound; the disk and the decode are, and 6 is what the other
# numpy-heavy steps here run without contending (see r010_ocr_blocks.sh).
# cut is seconds a page and runs alone: it needs EVERY page's geometry before
# it can fit the window, so it cannot start until the last lane is done.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
cd "$DIR"
# The page count follows the ISSUE constant in r000_issue.py, asked of the
# program itself rather than repeated here -- as r010_ocr_blocks.sh does.
FIRST="${1:-1}"
LAST="${2:-$("$PY" -c 'import r005_masters_spread as m; print(m.ISS.pages)')}"
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P 6 -n 5 "$PY" r005_masters_spread.py measure
"$PY" r005_masters_spread.py cut
