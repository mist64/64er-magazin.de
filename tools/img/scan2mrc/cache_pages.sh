#!/bin/bash
# Cache the expensive per-page steps so MRC can be iterated on cheaply.
#
# Per page:  mrcpipe apply    (2400 dpi: ONE affine -> matte -> A4 crop -> separate -> grade -> GCR
#                              -> mirror + Telea fill; writes the display CMYK, the known mask,
#                              the page RGB, and the UNFILLED detect CMYK)
#            -> mrcpipe geometry   (per-channel lpi/angle; feeds adaptive background dpi)
#            -> mrcpipe detect     (the screen score the MRC render consumes)
#            -> DELETE the detect CMYK
#
# The detect grade keeps the shadows (lo=0) and is written UNCOMPRESSED, ~2.2 GB a page. It cannot
# be kept; everything derived from it (geometry + score) is small, so it is generated, consumed and
# dropped in one pass. Uncompressed is deliberate: the file lives about a minute, and LZW bought
# 24% on halftone noise for 44.5s of CPU.
#
# The apply is Rust as of efaf90773 -- pixel-identical to the Python it replaced (0 differing
# samples of 2,227,416,436 on the CMYK, 0 of 556,854,109 on the page RGB) and ~8x faster: ~50s a
# page against ~409s.
#
# PREREQUISITE, and the trap that cost a 7-hour run: page_geometry.json and page_geometry/NNN/
# must be CURRENT. They encode the matte cut profiles, so they are what actually applies a
# bed_matte change -- re-running THIS script alone will not pick one up, because the apply reads
# those profiles rather than recomputing them. When the matte, spine or crop window moves, rerun
# stack_render.py -> 03-crop/fit_window.py -> 03-crop/emit_geometry.py first.
#
# Idempotent: a page whose score and page RGB exist is skipped. FORCE=1 re-runs anyway, which is
# required whenever an upstream stage changed, since the skip test can only see that a file is
# there, not that it is still current.
#
# Usage: cache_pages.sh <first> <last>   -- run 2-3 disjoint ranges in parallel shells. Not more:
# mrcpipe is internally rayon-parallel, so extra lanes oversubscribe and throughput FALLS.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/rust_pipeline/target/release/mrcpipe"
T=/Users/mist/DNB/8609/tmp
mkdir -p "$T/score" "$T/screen_geom" "$T/render/deliver"

first=${1:-1}; last=${2:-176}
for i in $(seq "$first" "$last"); do
  n=$(printf "%03d" "$i")
  if [ "${FORCE:-0}" != "1" ]; then
    [ -s "$T/score/$n.npy" ] && [ -s "$T/render/deliver/${n}_page_rgb.png" ] && \
      { echo "$(date +%H:%M:%S) p$n cached, skip"; continue; }
  fi
  [ -d "$T/page_geometry/$n" ] || { echo "  p$n NO GEOMETRY -- run emit_geometry first"; continue; }
  det="$T/render/deliver/${n}_cmyk_detect.tif"
  echo "$(date +%H:%M:%S) p$n apply"
  "$MP" apply "$i" --out "$T/render/deliver" --inpaint --detect-too --page-rgb >/dev/null 2>&1 || \
    { echo "  p$n APPLY FAILED"; continue; }
  [ -s "$det" ] || { echo "  p$n no detect tif"; continue; }
  echo "$(date +%H:%M:%S) p$n geometry+detect"
  "$MP" geometry "$det" "$T/screen_geom/$n.json" --dpi 2400 >/dev/null 2>&1
  "$MP" detect "$det" "$T/score/$n" >/dev/null 2>&1
  rm -f "$det"                       # ~2.2 GB; everything needed from it is now extracted
  echo "$(date +%H:%M:%S) p$n done"
done
echo "range $first..$last complete"
