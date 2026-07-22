#!/bin/bash
# Rotate cut scans upright at full res, in parallel. Run ONLY after the set is
# verified complete + correctly ordered (see RUNBOOK.md / make_audit.py).
# Full-res only -- thumbnails are generated afterwards by thumbs_from_full.sh,
# which reads these PNGs back (that read-back is the verification that they wrote
# correctly). Input tiffs may be named Scan*.tiff (pre-renumber) or NNN.tiff
# (already renumbered) -- any *.tiff is processed and keeps its basename.
# Usage: rotate.sh <SRC_DIR> <OUT_DIR>
#   writes  OUT_DIR/<base>.png   (full res, ~2400 dpi, PNG level 9)
# Resumable: skips a file whose output already exists. Launch detached to survive
# teardown:
#   nohup bash rotate.sh /Volumes/S/scan/<ISSUE> /Volumes/S/scan/<ISSUE>-png \
#         > /Volumes/S/scan/<ISSUE>-png/rotate.log 2>&1 &
set -u
SRC="${1:?usage: rotate.sh SRC_DIR OUT_DIR}"
OUT="${2:?usage: rotate.sh SRC_DIR OUT_DIR}"
mkdir -p "$OUT"; export OUT
export MAGICK_THREAD_LIMIT=4
rotone(){
  f="$1"; b=$(basename "$f" .tiff)
  [ -f "$OUT/$b.png" ] && { echo "skip $b"; return; }
  magick "$f" -alpha off -units PixelsPerInch -density 2400 \
    -rotate 270 -define png:compression-level=9 "$OUT/$b.png"
  echo "done $b $(date +%T)"
}
export -f rotone
echo "START $(date +%T)  jobs=8"
find "$SRC" -maxdepth 1 -name '*.tiff' -print0 | xargs -0 -P 8 -I {} bash -c 'rotone "$1"' _ "{}"
echo "ALLDONE $(date +%T)"
