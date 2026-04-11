#!/bin/bash
#
# extract_table.sh — tesseract-assisted table extraction pipeline
#
# Usage:
#   extract_table.sh <page_scan> <grep_pattern> <output_prefix>
#
# Arguments:
#   page_scan      path to the full page PNG (e.g. /tmp/8605_pages/p-082.png)
#   grep_pattern   regex to locate the target block (e.g. "EDC|CHC", "Punkte/cm", "Hauptprogramm")
#                  pass multiple alternatives with |. Case-insensitive.
#   output_prefix  prefix for all output files (e.g. /tmp/p82_routines)
#
# Steps performed:
#   1. Full-page tesseract TSV OCR                 → <prefix>_page.tsv
#   2. Per-block bbox + text summary               → <prefix>_blocks.txt
#   3. Locate target block via grep_pattern        → prints matching block lines
#   4. Crop target block from full-res page        → <prefix>_crop.png
#   5. Downsized crop (≤1800px) for vision Read    → <prefix>_crop_small.png
#   6. Second-pass OCR on the crop with --psm 6    → <prefix>_crop_ocr.txt
#
# Output files (always created with the same suffixes) are printed at the end.
# The subagent then Reads <prefix>_crop_small.png + <prefix>_crop_ocr.txt and
# assembles the final HTML table.
#
# Dependencies: tesseract (with deu), ImageMagick (magick), awk, grep.

set -eu

if [[ $# -ne 3 ]]; then
    sed -n '3,30p' "$0"
    exit 1
fi

PAGE="$1"
PATTERN="$2"
PREFIX="$3"

if [[ ! -f "$PAGE" ]]; then
    echo "Error: page scan '$PAGE' not found" >&2
    exit 1
fi

TSV="${PREFIX}_page.tsv"
BLOCKS="${PREFIX}_blocks.txt"
CROP="${PREFIX}_crop.png"
CROP_SMALL="${PREFIX}_crop_small.png"
CROP_OCR="${PREFIX}_crop_ocr.txt"

# Step 1: full-page tesseract TSV
# Note: tesseract on macOS can't read files from /tmp directly (sandboxing?).
# Piping via stdin is reliable regardless of input path.
echo "[1/6] Running tesseract TSV on $PAGE ..." >&2
cat "$PAGE" | tesseract - "${PREFIX}_page" -l deu tsv >/dev/null 2>&1

# Step 2: summarize blocks (bbox + first ~300 chars of text)
echo "[2/6] Summarizing blocks → $BLOCKS" >&2
awk -F'\t' 'NR>1 && $1==5 && $12!="" {
  b=$3;
  if (!(b in minL) || $7<minL[b]) minL[b]=$7;
  if (!(b in minT) || $8<minT[b]) minT[b]=$8;
  if (!(b in maxR) || $7+$9>maxR[b]) maxR[b]=$7+$9;
  if (!(b in maxB) || $8+$10>maxB[b]) maxB[b]=$8+$10;
  text[b]=text[b]" "$12;
}
END {
  for (b in text) {
    w = maxR[b]-minL[b]; h = maxB[b]-minT[b];
    printf "block=%s bbox=%dx%d+%d+%d text=%s\n",
      b, w, h, minL[b], minT[b], substr(text[b],1,300);
  }
}' "$TSV" | sort -t= -k1 > "$BLOCKS"

# Step 3: locate the target block by grep pattern
echo "[3/6] Searching blocks for pattern: $PATTERN" >&2
MATCHES=$(grep -iE "$PATTERN" "$BLOCKS" || true)
if [[ -z "$MATCHES" ]]; then
    echo "Error: pattern '$PATTERN' not found in any block." >&2
    echo "All blocks are in $BLOCKS — inspect manually and re-run with a better pattern." >&2
    exit 2
fi

# Pick the first match (if multiple, the subagent should narrow the pattern)
MATCH_COUNT=$(echo "$MATCHES" | wc -l | tr -d ' ')
if [[ "$MATCH_COUNT" -gt 1 ]]; then
    echo "Warning: $MATCH_COUNT blocks matched. Using the first; refine pattern if wrong." >&2
    echo "$MATCHES" >&2
fi
FIRST=$(echo "$MATCHES" | head -1)
BBOX=$(echo "$FIRST" | sed -n 's/.*bbox=\([0-9x+]*\).*/\1/p')

if [[ -z "$BBOX" ]]; then
    echo "Error: could not parse bbox from match line: $FIRST" >&2
    exit 3
fi

echo "[3/6] Target block: $FIRST" >&2
echo "[3/6] bbox=$BBOX" >&2

# Step 4: crop target block from full-res page
echo "[4/6] Cropping → $CROP" >&2
magick "$PAGE" -crop "$BBOX" +repage "$CROP"

# Step 5: downsized copy for vision
echo "[5/6] Resizing for vision → $CROP_SMALL" >&2
magick "$CROP" -resize '1800x1800>' "$CROP_SMALL"

# Step 6: second-pass OCR on the full-res crop
echo "[6/6] Second-pass tesseract on crop → $CROP_OCR" >&2
cat "$CROP" | tesseract - "${PREFIX}_crop_ocr" -l deu --psm 6 >/dev/null 2>&1

echo >&2
echo "Done. Outputs:" >&2
echo "  page TSV:     $TSV" >&2
echo "  blocks list:  $BLOCKS" >&2
echo "  crop (full):  $CROP" >&2
echo "  crop (small): $CROP_SMALL   ← Read this with vision" >&2
echo "  crop OCR:     $CROP_OCR     ← Read this as text scaffold" >&2

# Print the key outputs to stdout so callers can capture them
printf "CROP_SMALL=%s\nCROP_OCR=%s\n" "$CROP_SMALL" "$CROP_OCR"
