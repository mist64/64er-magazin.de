#!/bin/bash
# Step 005, SPREAD variant -- measure every page in parallel, then cut.
#
# measure is ~3.5 min a page in one lane (the 900 MB PNG decode, the 2400 dpi
# rotation, the flat field, the separator, the ICC pair).
#
# THE LANE COUNT IS MEASURED AT RUN TIME, not fixed.  It used to be 6 with a
# comment saying memory was not the bound -- true, but it left 26 of 32 cores
# idle for two hours.  Every lane is ONE core (OMP_NUM_THREADS=1 below, so
# numpy and ImageMagick each stay single-threaded and do not contend), so the
# machine decides:
#
#   cores   this box has 32; leave 4 for everything else.
#   memory  AS MANY LANES AS FIT IN HALF THE FREE RAM.  Half, not all: the
#           other half is the margin that keeps this off the swap when
#           something else on the machine wants memory mid-sweep, and a sweep
#           that starts swapping is slower than one that never grew.
#           MEASURED on 8611: a lane peaks at ~19 GB -- python holding the
#           2400 dpi sheet (~14 GB) or, while it waits on the separator,
#           python idle (~9 GB) plus magick's own copy (~9 GB).  ImageMagick
#           at Q16 HDRI holds a 590 Mpx 4-channel page at 8 bytes a channel,
#           which is where its share comes from.
#
# Whichever is smaller wins.  On a box with a 350 GB model server resident
# that is memory; with it stopped it is cores.  Both happened on one afternoon,
# which is why this is measured at run time and not written down as a number.
LANE_GB=19
CORES=$(sysctl -n hw.physicalcpu)
FREE_GB=$(vm_stat | awk '/page size/{ps=$8} /Pages free/{f=$3} /Pages inactive/{i=$3} /Pages speculative/{s=$3} END{printf "%d", (f+i+s)*ps/1073741824}')
LANES=$(( CORES - 4 ))
MEM_LANES=$(( FREE_GB / 2 / LANE_GB ))          # HALF the free RAM, never all
[ $MEM_LANES -lt $LANES ] && LANES=$MEM_LANES
[ $LANES -lt 2 ] && LANES=2
echo "r005: $LANES lanes ($CORES cores, ${FREE_GB} GB free," \
     "half of it at ~${LANE_GB} GB a lane)" >&2
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
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P "$LANES" -n 5 "$PY" r005_masters_spread.py measure
"$PY" r005_masters_spread.py cut
