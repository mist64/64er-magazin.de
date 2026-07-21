#!/bin/bash
# Montage bottom folio-strips in RAW SLOT order (no imposition), each labelled
# with its slot number. Complements make_audit.py (which sorts by ASSUMED page):
# raw order makes the imposition pattern directly visible, so you can read two
# folios you KNOW share a sheet (same group of 4 slots) and derive the true page
# count as  count = folio_a + folio_b - 1  (see RENUMBERING.md).
# Run from the scan dir (expects ./thumbs/Scan*.png|tiff).
# Usage: raw_montage.sh <OUT.png> <FIRST_SLOT> <LAST_SLOT>
set -u
SRC=thumbs
OUT="${1:?usage: raw_montage.sh OUT.png FIRST_SLOT LAST_SLOT}"
A="${2:?first slot}"; B="${3:?last slot}"
tmp=$(mktemp -d); i=0
for s in $(seq "$A" "$B"); do
  if [ "$s" -eq 0 ]; then f="$SRC/Scan.png"; else f="$SRC/Scan $s.png"; fi
  [ -f "$f" ] || f="$SRC/Scan $s.tiff"
  side=$([ $((i % 2)) -eq 0 ] && echo East || echo West)
  magick "$f" -rotate 0 -gravity South -crop 100%x14%+0+0 +repage \
    -gravity Center -crop 100%x50%+0+0 +repage -resize 760x \
    -gravity "$side" -background "#c8e6ff" -splice 96x0 \
    -pointsize 28 -fill blue -annotate +5+0 "s$s" \
    -bordercolor gray -border 1 "$tmp/$(printf %04d "$s").png"
  i=$((i+1))
done
montage "$tmp"/*.png -tile 2x -geometry +2+2 -background white "$OUT"
identify "$OUT"
