#!/bin/bash
# Generate 150-dpi upright thumbnails from raw cut scans, in parallel.
# Fast input for audits (make_audit.py) BEFORE the expensive full-res rotate.
# Usage: thumbs.sh <SRC_DIR> <OUT_DIR>
#   SRC_DIR: dir of Scan.tiff (slot 0), Scan 1..N.tiff
#   OUT_DIR: where Scan*.png thumbs are written (created if missing)
# Resumable: skips any thumb that already exists.
set -u
SRC="${1:?usage: thumbs.sh SRC_DIR OUT_DIR}"
OUT="${2:?usage: thumbs.sh SRC_DIR OUT_DIR}"
mkdir -p "$OUT"; export OUT
export MAGICK_THREAD_LIMIT=2   # keep per-proc threads low so the -P fan-out wins
thumbone(){
  f="$1"; b=$(basename "$f" .tiff)
  [ -f "$OUT/$b.png" ] && { echo "skip $b"; return; }
  magick "$f" -alpha off -scale 6.25% -units PixelsPerInch -density 150 -rotate 270 \
    -define png:compression-level=9 "$OUT/$b.png"
  echo "done $b"
}
export -f thumbone
echo "START $(date +%T)"
find "$SRC" -maxdepth 1 -name 'Scan*.tiff' -print0 | xargs -0 -P 12 -I {} bash -c 'thumbone "$1"' _ "{}"
echo "ALLDONE $(date +%T)"
