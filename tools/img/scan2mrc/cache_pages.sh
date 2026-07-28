#!/bin/bash
# Cache the expensive per-page steps so MRC can be iterated on cheaply.
#
# Per page:  render (display CMYK, filled, + detect CMYK, unfilled)
#            -> screen geometry      (per-channel lpi/angle; feeds adaptive background dpi)
#            -> screen score         (the detect map the MRC render consumes)
#            -> DELETE the detect CMYK
#
# The detect grade keeps the shadows (lo=0), so it compresses ~7x worse than the display grade:
# 1.4 GB a page against 0.2 GB, i.e. ~250 GB for the issue. It cannot be kept. Everything derived
# from it (geometry + score) is small, so it is generated, consumed and dropped in one pass.
#
# Idempotent: a page whose score exists is skipped, so this can be re-run after an interruption.
#
# Usage: cache_pages.sh <first> <last>   -- run several disjoint ranges in parallel shells rather
# than using a worker pool; the multiprocessing Pool stalls after one task per worker on this
# machine and the cause is not yet understood.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/rust_pipeline/target/release/mrcpipe"
PY=/opt/homebrew/bin/python3.11
T=/Users/mist/DNB/8609/tmp
mkdir -p "$T/score" "$T/screen_geom"

first=${1:-1}; last=${2:-176}
for n in $(seq -w "$first" "$last"); do
  n=$(printf "%03d" "$((10#$n))")
  # both must exist: the page RGB is what the MRC render consumes and cannot be
  # reconstructed from the GCR'd CMYK afterwards (GCR is not invertible).
  [ -s "$T/score/$n.npy" ] && [ -s "$T/render/deliver/${n}_page_rgb.png" ] && \
    { echo "$(date +%H:%M:%S) p$n cached, skip"; continue; }
  det="$T/render/deliver/${n}_cmyk_detect.tif"
  echo "$(date +%H:%M:%S) p$n render"
  $PY "$HERE/render_page.py" "$((10#$n))" --jobs 1 --inpaint --detect-too --page-rgb >/dev/null 2>&1 || \
    { echo "  p$n RENDER FAILED"; continue; }
  [ -s "$det" ] || { echo "  p$n no detect tif"; continue; }
  echo "$(date +%H:%M:%S) p$n geometry+detect"
  $MP geometry "$det" "$T/screen_geom/$n.json" --dpi 2400 >/dev/null 2>&1
  $MP detect "$det" "$T/score/$n" >/dev/null 2>&1
  rm -f "$det"                       # 1.4 GB; everything needed from it is now extracted
  echo "$(date +%H:%M:%S) p$n done"
done
echo "range $first..$last complete"
