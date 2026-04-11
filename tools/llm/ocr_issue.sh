#!/bin/bash
#
# ocr_issue.sh — one-shot OCR cache builder for a 64'er issue PDF
#
# Usage:
#   ocr_issue.sh <pdf_file> [cache_dir]
#
# Arguments:
#   pdf_file    path to the issue PDF (e.g. 64er_1986-05.pdf)
#   cache_dir   output directory (default: _cache in current working directory)
#
# What it does:
#   1. Extract every page of the PDF at 150 dpi as PNG     → <cache>/pages/p-NNN.png
#   2. Run tesseract TSV OCR (German) on every page        → <cache>/tsv/p-NNN.tsv
#   3. Summarize each page's blocks (bbox + preview text)  → <cache>/blocks/p-NNN.txt
#   4. Concatenate all block summaries into one index      → <cache>/all_blocks.txt
#
# The script is idempotent: if an output file already exists, it is skipped.
# Safe to re-run to finish a partial job.
#
# The resulting cache makes table extraction fast:
#   grep -i "Hauptprogramm" <cache>/all_blocks.txt
# tells you which page and which block on that page contains your text. Then
# extract_table.sh can crop + re-OCR just that block.
#
# Dependencies: pdftoppm (from poppler), tesseract (with deu), awk.

set -eu

if [[ $# -lt 1 || $# -gt 2 ]]; then
    sed -n '3,26p' "$0"
    exit 1
fi

PDF="$1"
CACHE="${2:-_cache}"

if [[ ! -f "$PDF" ]]; then
    echo "Error: PDF '$PDF' not found" >&2
    exit 1
fi

PAGES_DIR="$CACHE/pages"
TSV_DIR="$CACHE/tsv"
BLOCKS_DIR="$CACHE/blocks"
ALL_BLOCKS="$CACHE/all_blocks.txt"

mkdir -p "$PAGES_DIR" "$TSV_DIR" "$BLOCKS_DIR"

# Step 1: extract pages at 150 dpi if not already done
echo "[1/4] Extracting pages from $PDF at 150 dpi → $PAGES_DIR" >&2
if [[ -z "$(ls -A "$PAGES_DIR" 2>/dev/null)" ]]; then
    pdftoppm -r 150 "$PDF" "$PAGES_DIR/p" -png
    echo "       extracted $(ls "$PAGES_DIR" | wc -l | tr -d ' ') pages" >&2
else
    echo "       $PAGES_DIR already populated, skipping extraction" >&2
fi

# Count pages
PAGE_COUNT=$(ls "$PAGES_DIR" | wc -l | tr -d ' ')
echo "[1/4] $PAGE_COUNT pages available" >&2

# Step 2: tesseract TSV per page, parallelized
# Tesseract's internal OpenMP parallelism rarely saturates a multicore machine,
# so we run multiple tesseract processes in parallel — one per page.
# Each worker is limited to OMP_THREAD_LIMIT=1 so they don't stomp on each other.
PARALLEL="${OCR_PARALLEL:-20}"
echo "[2/4] Running tesseract TSV on each page (deu, default PSM, ${PARALLEL} workers)" >&2

# Collect the list of pages that still need OCR
NEEDED=$(mktemp)
for PAGE in "$PAGES_DIR"/p-*.png; do
    BASE=$(basename "$PAGE" .png)
    if [[ ! -f "$TSV_DIR/$BASE.tsv" ]]; then
        echo "$PAGE"
    fi
done > "$NEEDED"

TODO_COUNT=$(wc -l < "$NEEDED" | tr -d ' ')
SKIP_COUNT=$(( PAGE_COUNT - TODO_COUNT ))
echo "       $TODO_COUNT pages to OCR, $SKIP_COUNT already cached" >&2

if [[ "$TODO_COUNT" -gt 0 ]]; then
    # Use xargs -P for parallelism. Each worker pipes its page via stdin.
    # Pass TSV_DIR through the environment so the subshell can see it.
    export TSV_DIR
    < "$NEEDED" xargs -P "$PARALLEL" -I {} sh -c '
        PAGE="$1"
        BASE=$(basename "$PAGE" .png)
        # Pipe via stdin — tesseract on macOS has trouble reading /tmp paths.
        OMP_THREAD_LIMIT=1 tesseract - "$TSV_DIR/$BASE" -l deu tsv < "$PAGE" >/dev/null 2>&1
        printf "."
    ' _ {}
    echo >&2
fi
rm -f "$NEEDED"

echo "[2/4] OCR done: $TODO_COUNT new, $SKIP_COUNT cached" >&2

# Step 3: block summaries per page
echo "[3/4] Summarizing blocks per page → $BLOCKS_DIR" >&2
for TSV in "$TSV_DIR"/p-*.tsv; do
    BASE=$(basename "$TSV" .tsv)
    OUT="$BLOCKS_DIR/$BASE.txt"
    if [[ -f "$OUT" ]]; then
        continue
    fi
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
    }' "$TSV" | LC_ALL=C sort -t= -k1 > "$OUT"
done

# Step 4: combined index across all pages with page prefix
echo "[4/4] Building combined index → $ALL_BLOCKS" >&2
> "$ALL_BLOCKS"
for BF in "$BLOCKS_DIR"/p-*.txt; do
    BASE=$(basename "$BF" .txt)
    awk -v page="$BASE" '{print page " " $0}' "$BF" >> "$ALL_BLOCKS"
done

# Summary
echo >&2
echo "Done. Cache layout:" >&2
echo "  $PAGES_DIR/p-NNN.png      ($(ls "$PAGES_DIR" | wc -l | tr -d ' ') pages)" >&2
echo "  $TSV_DIR/p-NNN.tsv        ($(ls "$TSV_DIR" | wc -l | tr -d ' ') TSVs)" >&2
echo "  $BLOCKS_DIR/p-NNN.txt     ($(ls "$BLOCKS_DIR" | wc -l | tr -d ' ') summaries)" >&2
echo "  $ALL_BLOCKS                ($(wc -l < "$ALL_BLOCKS" | tr -d ' ') lines)" >&2
echo >&2
echo "Search the whole issue with:" >&2
echo "  grep -i 'your_text' $ALL_BLOCKS" >&2
echo "Each hit looks like: p-NNN block=M bbox=WxH+X+Y text=..." >&2
