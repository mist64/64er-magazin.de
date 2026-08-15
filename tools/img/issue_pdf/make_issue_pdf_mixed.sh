#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build a searchable issue PDF that ships bilevel pages as 600 dpi JBIG2 and the rest as
150 dpi guetzli JPEG, with the JPEG quality scaled to land just under 100 MB.

Usage: make_issue_pdf_mixed.sh <input_dir> <output.pdf> <issue_tag>

  MODE=allbw       every colour-free page goes to JBIG2, halftone or not
  MODE=nohalftone  only colour-free pages with NO halftone go to JBIG2 (default)

WHY TWO MODES. A halftone at 600 dpi is resolved DOTS, and dots are noise to a bilevel coder:
measured on 8609, lossless JBIG2 of a screened page came out 706 KB against 554 KB for the
guetzli JPEG it would replace -- bigger, and it looks like dots. Clean type goes the other way,
205 KB against 587 KB, at four times the resolution. `nohalftone` keeps only the pages that win;
`allbw` is the experiment that shows what the halftone pages cost.

THE PAGE TEST, both parts measured on the 600 dpi master, both conservative -- anything ambiguous
stays a JPEG:

  colour    per-pixel chroma (max-min of R,G,B) after a blur, thresholded at 12%, eroded.
            The blur matters: scanner CCD fringing puts colour on the edge of every black
            letter. So does using ABSOLUTE chroma rather than HSB saturation, which for a dark
            pixel is (max-min)/max and reads 40% on an R10 G8 B6 black.
  halftone  fraction of the page that is mid-tone at 150 dpi after a median filter and an
            erode. Text survives as thin edges the erode removes; a screened region is a
            solid field of mid-tone that survives.

REQUIRES the OCR cache from make_issue_pdf.sh (<input_dir>/.ocrcache/NNN.pdf and NNN_150.png).
Run that first -- this script reuses its OCR and its rasters and never re-runs tesseract.

NOT PDF/A. Ghostscript transcodes any image it cannot pass through, and it passes through only
JPEG, so a JBIG2 page cannot survive the gs PDF/A step -- the whole document is assembled with
pikepdf instead (assemble_pdf.py). The sRGB OutputIntent and the XMP are written, but nothing
here validates the result as PDF/A.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 3 ]]; then
  usage; [[ $# -ne 3 && "${1:-}" != "-h" && "${1:-}" != "--help" ]] && exit 2 || exit 0
fi

IN="${1%/}"; OUT="$2"; TAG="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${MODE:-nohalftone}"
PYBIN="$(ls -1d /opt/homebrew/Cellar/ocrmypdf/*/libexec/bin/python 2>/dev/null | sort -V | tail -1)"
ICC="$(ls -1 /opt/homebrew/Cellar/ghostscript/*/share/ghostscript/iccprofiles/srgb.icc 2>/dev/null | tail -1)"
CACHE="$IN/.ocrcache"
LOG="${OUT%.pdf}.build.log"
LIMIT=$((100*1000*1000))
QMIN=84; QMAX=97                 # guetzli's own floor is 84; it refuses to go below
NCPU="$(sysctl -n hw.ncpu)"
AUTHOR="Markt & Technik"
CREATOR="tesseract 5 + guetzli + jbig2enc + pikepdf"
TITLE="64'er $TAG"
# Page-test thresholds. Both are fractions of page area, and both are deliberately near zero: the
# question is "is there ANY colour ink / ANY screen", not "how much".
COLOUR_MAX=0.002
HALFTONE_MAX=0.002

[[ -n "$PYBIN" ]] || { echo "no ocrmypdf python (pikepdf) found"; exit 1; }
[[ -d "$CACHE" ]] || { echo "no OCR cache at $CACHE -- run make_issue_pdf.sh first"; exit 1; }
command -v jbig2 >/dev/null || { echo "jbig2enc not installed"; exit 1; }

mkdir -p "$CACHE/jbig2"
exec >> "$LOG" 2>&1
echo "=== $(date '+%H:%M:%S') mixed build $IN -> $OUT  mode=$MODE ==="

pages=""
for f in "$IN"/[0-9][0-9][0-9].png "$IN"/[0-9][0-9][0-9].tiff; do
  [[ -e "$f" ]] || continue
  b="$(basename "$f")"; pages="$pages ${b%.*}"
done
pages=$(printf '%s\n' $pages | sort -u)
echo "pages: $(echo $pages | wc -w)"

src_of() { if [[ -f "$IN/$1.png" ]]; then echo "$IN/$1.png"; else echo "$IN/$1.tiff"; fi; }

# ---- Phase 1: classify every page (cached; the measurement is ~1.5 s a page) --------------------
CLASS="$CACHE/pageclass.tsv"
if [[ ! -s "$CLASS" ]]; then
  echo "[classify] measuring colour and halftone"
  classify_one() {
    S="$1"; n=$(basename "$S"); n="${n%.*}"
    c=$(magick "$S" -resize 8.333% -blur 0x1.5 \
        \( -clone 0 -separate -evaluate-sequence max \) \
        \( -clone 0 -separate -evaluate-sequence min \) \
        -delete 0 -compose MinusSrc -composite \
        -threshold 12% -morphology Erode Octagon:1 -format "%[fx:mean]" info:)
    h=$(magick "$S" -resize 25% -colorspace Gray -statistic Median 3x3 -write mpr:g +delete \
        \( mpr:g -threshold 25% \) \( mpr:g -threshold 78% \) -compose MinusSrc -composite \
        -morphology Erode Octagon:2 -format "%[fx:mean]" info:)
    printf "%s\t%.5f\t%.5f\n" "$n" "$c" "$h"
  }
  export -f classify_one
  for n in $pages; do src_of "$n"; done | xargs -P "$NCPU" -I{} bash -c 'classify_one {}' \
      | sort > "$CLASS"
fi
echo "  classified $(wc -l < "$CLASS" | tr -d ' ') pages"

# ---- Phase 2: decide, per page, what carries it -------------------------------------------------
bilevel=""; contone=""
while IFS=$'\t' read -r n c h; do
  keep=0
  if awk "BEGIN{exit !($c < $COLOUR_MAX)}"; then
    if [[ "$MODE" == "allbw" ]]; then keep=1
    elif awk "BEGIN{exit !($h < $HALFTONE_MAX)}"; then keep=1; fi
  fi
  # page 1 carries the cleaned cover when there is one, so it is never bilevel
  [[ "$n" == "$(echo $pages | awk '{print $1}')" && -f "$CACHE/${n}_150.png" && -n "${TITLE_PNG:-}" ]] && keep=0
  if (( keep )); then bilevel="$bilevel $n"; else contone="$contone $n"; fi
done < "$CLASS"
echo "  bilevel: $(echo $bilevel | wc -w)   contone: $(echo $contone | wc -w)"

# ---- Phase 3: JBIG2 the bilevel pages, lossless (cached) ----------------------------------------
for n in $bilevel; do
  [[ -s "$CACHE/jbig2/$n.jb2" ]] && continue
  ( S="$(src_of "$n")"
    magick "$S" -colorspace Gray -auto-threshold OTSU -depth 1 "$CACHE/jbig2/$n.pbm"
    jbig2 -p "$CACHE/jbig2/$n.pbm" > "$CACHE/jbig2/$n.jb2"
    magick identify -format "%w %h" "$CACHE/jbig2/$n.pbm" > "$CACHE/jbig2/$n.dim"
    rm -f "$CACHE/jbig2/$n.pbm"
    echo "[jbig2] $n $(stat -f%z "$CACHE/jbig2/$n.jb2") bytes" ) &
  while (( $(jobs -r | wc -l) >= NCPU )); do wait -n; done
done; wait

# ---- Phase 4: quality search over the contone pages ---------------------------------------------
build_at() {  # $1=quality -> byte size of the assembled PDF
  local q="$1" qd="$CACHE/guetzli-q$1" man="$CACHE/manifest-$MODE-q$1.tsv"
  mkdir -p "$qd"
  for n in $contone; do
    [[ -s "$qd/$n.jpg" ]] && continue
    ( guetzli --quality "$q" "$CACHE/${n}_150.png" "$qd/$n.jpg" 2>/dev/null ) &
    while (( $(jobs -r | wc -l) >= NCPU )); do wait -n; done
  done; wait
  : > "$man"
  for n in $pages; do
    if [[ -s "$CACHE/jbig2/$n.jb2" ]] && [[ " $bilevel " == *" $n "* ]]; then
      read -r w h < "$CACHE/jbig2/$n.dim"
      printf "%s\tjbig2\t%s\t%s\t%s\n" "$CACHE/$n.pdf" "$CACHE/jbig2/$n.jb2" "$w" "$h" >> "$man"
    else
      read -r w h <<< "$(magick identify -format "%w %h" "$qd/$n.jpg")"
      printf "%s\tjpeg\t%s\t%s\t%s\n" "$CACHE/$n.pdf" "$qd/$n.jpg" "$w" "$h" >> "$man"
    fi
  done
  "$PYBIN" "$HERE/assemble_pdf.py" "$man" "$qd/out-$MODE.pdf" "$TITLE" "$AUTHOR" "$CREATOR" "$ICC" >/dev/null
  stat -f%z "$qd/out-$MODE.pdf"
}

lo=$QMIN; hi=$QMAX; best=""; bestf=""
while (( lo <= hi )); do
  mid=$(( (lo+hi)/2 ))
  sz=$(build_at "$mid")
  printf "[search] q=%d -> %d bytes (%.2f MB)\n" "$mid" "$sz" "$(awk "BEGIN{print $sz/1e6}")"
  if (( sz <= LIMIT )); then best="$mid"; bestf="$CACHE/guetzli-q$mid/out-$MODE.pdf"; lo=$((mid+1)); else hi=$((mid-1)); fi
done
[[ -n "$best" ]] || { echo "even q$QMIN exceeds $LIMIT"; exit 1; }
cp "$bestf" "$OUT"
echo "=== $(date '+%H:%M:%S') DONE -> $OUT  mode=$MODE q=$best  $(stat -f%z "$OUT") bytes ==="
echo "    bilevel $(echo $bilevel | wc -w) pages @600dpi JBIG2, contone $(echo $contone | wc -w) pages @150dpi guetzli q$best"
