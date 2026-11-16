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
# A range handed over as ONE quoted argument -- r010_ocr_blocks.sh "163 168" --
# made `seq` print "invalid floating point argument", OCR'd NOTHING, rebuilt the
# block index without those pages, and exited 0: seq is not the last command of
# its pipeline, so `set -e` never saw it fail.  MEASURED on SH10, 2026-11-16;
# caught only by counting the outputs afterwards.  Two integers, or stop.
for v in FIRST LAST; do
  case "${!v}" in
    ''|*[!0-9]*) echo "r010: $v must be a single integer, got '${!v}'" >&2; exit 2 ;;
  esac
done
if (( FIRST < 1 || LAST < FIRST )); then
  echo "r010: bad page range $FIRST..$LAST" >&2; exit 2
fi
# Lanes: half the free RAM, capped by the cores -- r000_orchestration.md,
# *PARALLELISE TO HALF THE FREE RAM*.  1.5 GB a lane is MEASURED on 8611:
# RSS sampled every 5 s across a 28-lane run peaked at 1.03 GB for the python
# and 0.21 GB for its tesseract, so ~1.25 GB, and 1.5 is that plus margin.
# (The 3 GB that stood here first was a guess, and it was 2.4x too high.)
# At this size the cores cap always binds first, which is the point: the
# hardcoded -P 6 this replaces left 26 of 32 idle and made an 78-second job
# take a quarter of an hour.
# ${LANES:-...}: an INHERITED LANES wins.  A bare assignment here overwrote
# `LANES=1 ./step.sh`, so an owner instruction to run serially evaporated
# inside the script that was told to obey it.  (r000, PARALLELISE TO HALF.)
LANES="${LANES:-$("$PY" -c 'import r000_issue; print(r000_issue.lanes(1.5))')}"
echo "r010: $LANES lanes (~1.5 GB each, measured; half the free RAM)" >&2
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P "$LANES" -n 8 "$PY" r010_ocr_blocks.py
"$PY" r010_blocks_index.py
