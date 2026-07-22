#!/bin/bash
# Regenerate 150-dpi thumbnails FROM the rotated full-res PNGs (not the tiffs).
# This doubles as verification: every full PNG is read back, so a truncated or
# corrupt full PNG shows up as a failed/garbage thumb.
# Full PNGs are already upright and 2400 dpi, so this is a pure 6.25% downscale
# (2400 * 0.0625 = 150 dpi) — no rotation.
# Usage: thumbs_from_full.sh <DIR>
#   reads   DIR/NNN.png        (rotated full res)
#   writes  DIR/thumb/NNN.png  (150 dpi) — overwrites existing
set -u
DIR="${1:?usage: thumbs_from_full.sh DIR (dir of NNN.png full-res pages)}"
mkdir -p "$DIR/thumb"; export DIR
export MAGICK_THREAD_LIMIT=2
thumbone(){
  f="$1"; b=$(basename "$f" .png)
  magick "$f" -alpha off -scale 6.25% -units PixelsPerInch -density 150 \
    -define png:compression-level=9 "$DIR/thumb/$b.png" && echo "done $b" || echo "FAIL $b"
}
export -f thumbone
echo "START $(date +%T)"
find "$DIR" -maxdepth 1 -name '[0-9]*.png' -print0 | xargs -0 -P 12 -I {} bash -c 'thumbone "$1"' _ "{}"
echo "ALLDONE $(date +%T)"
