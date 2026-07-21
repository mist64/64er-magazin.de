#!/bin/bash
# Rotate raw cut scans upright at full res AND emit a 150-dpi thumb, in one
# magick decode per file, in parallel. Run ONLY after the set is verified
# complete + correctly ordered (see RUNBOOK.md / make_audit.py).
# Usage: rotate.sh <SRC_DIR> <OUT_DIR>
#   writes  OUT_DIR/Scan*.png        (full res, ~2400 dpi, PNG level 9)
#           OUT_DIR/thumb/Scan*.png  (150 dpi)
# Resumable: skips a file only when BOTH its full and thumb outputs exist, so a
# killed job redoes any half-written page. Launch detached to survive teardown:
#   nohup bash rotate.sh /Volumes/S/scan/<ISSUE> /Volumes/S/scan/<ISSUE>-png \
#         > /Volumes/S/scan/<ISSUE>-png/rotate.log 2>&1 &
set -u
SRC="${1:?usage: rotate.sh SRC_DIR OUT_DIR}"
OUT="${2:?usage: rotate.sh SRC_DIR OUT_DIR}"
mkdir -p "$OUT/thumb"; export OUT
export MAGICK_THREAD_LIMIT=4
rotone(){
  f="$1"; b=$(basename "$f" .tiff)
  [ -f "$OUT/$b.png" ] && [ -f "$OUT/thumb/$b.png" ] && { echo "skip $b"; return; }
  magick "$f" -alpha off -units PixelsPerInch -density 2400 \
    \( -clone 0 -rotate 270 -define png:compression-level=9 +write "$OUT/$b.png" \) \
    \( -clone 0 -scale 6.25% -units PixelsPerInch -density 150 -rotate 270 \
       -define png:compression-level=9 +write "$OUT/thumb/$b.png" \) \
    null:
  echo "done $b $(date +%T)"
}
export -f rotone
echo "START $(date +%T)  jobs=8"
find "$SRC" -maxdepth 1 -name 'Scan*.tiff' -print0 | xargs -0 -P 8 -I {} bash -c 'rotone "$1"' _ "{}"
echo "ALLDONE $(date +%T)"
