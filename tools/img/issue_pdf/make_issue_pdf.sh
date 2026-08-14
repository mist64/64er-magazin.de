#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build a searchable, just-under-100MB PDF/A-3B for one 64'er issue.

Usage: make_issue_pdf.sh <input_dir> <output.pdf> <issue_tag>

  input_dir   folder with 001..NNN as .tiff or .png (page scans, 600 dpi A4)
  TITLE_PNG=  optional cleaned 150 dpi cover replacing page 1's image; must be EXACTLY the
              size page 1 reduces to (1240x1754 for a 4960x7015 page) or the build stops.
              Defaults to <input_dir>/title.png; the repo keeps them at issues/NNNN/title.png
  output.pdf  output PDF path
  issue_tag   e.g. "09/86"  ->  PDF Title "64'er 09/86"

Pipeline: tesseract OCR (deu, ~402dpi) text layer; guetzli 150dpi images (page 1's
image = title.png); binary-search guetzli quality so the final PDF/A lands just
below 100 MB; never rotate; PDF/A-3B; metadata via gs DOCINFO (CreationDate=today).

THE TWO RESOLUTIONS, because they look like an inconsistency and are not:
  * OCR reads a 402 dpi render (600 dpi source at 67%). Measured on issue 8608: at 300 or
    150 dpi tesseract truncates words at the image edges. 402 dpi cost nothing but time.
  * The delivered image is 150 dpi (25%), guetzli-encoded. swap_image.py puts that JPEG into
    the 402 dpi page PDF, so the text layer keeps its accuracy and the file keeps its size.

CACHING: OCR output and 150 dpi rasters live in <input_dir>/.ocrcache and are reused, so
re-running to re-tune quality only redoes the encode. Delete the cache to force a full rebuild.

ENCODER=fast  use ImageMagick JPEG instead of guetzli. Same pipeline, same cache, same PDF/A,
              minutes instead of hours -- at a worse bytes-for-quality ratio. Meant for getting
              a PDF in hand today; re-run without it for the keeper, and since the OCR and the
              150 dpi rasters are cached, that second run only redoes the encode.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 3 ]]; then
  usage; [[ $# -ne 3 && "${1:-}" != "-h" && "${1:-}" != "--help" ]] && exit 2 || exit 0
fi

IN="${1%/}"; OUT="$2"; TAG="$3"
# The ocrmypdf formula's interpreter, which ships pikepdf and Pillow. Newest wins -- pinning the
# version string is how this broke once, when the formula updated underneath it.
PYBIN="$(ls -1d /opt/homebrew/Cellar/ocrmypdf/*/libexec/bin/python 2>/dev/null | sort -V | tail -1)"
SWAP="$(cd "$(dirname "$0")" && pwd)/swap_image.py"
ICC="$(ls -1 /opt/homebrew/Cellar/ghostscript/*/share/ghostscript/iccprofiles/srgb.icc 2>/dev/null | tail -1)"
CACHE="$IN/.ocrcache"
# The cleaned 150 dpi cover that replaces page 1's image. Defaults to the input dir; the repo keeps
# the real ones per issue (issues/NNNN/title.png), which is not where the scans live.
TITLE_PNG="${TITLE_PNG:-$IN/title.png}"
LOG="${OUT%.pdf}.build.log"
LIMIT=$((100*1000*1000))        # 100 MB ceiling (decimal)
ENCODER="${ENCODER:-guetzli}"
# Quality search range, per encoder -- the two scales are not comparable. guetzli below 84 starts
# visibly smearing the halftone; ImageMagick's q70 is roughly where the screen begins to mottle.
if [[ "$ENCODER" == "fast" ]]; then QMIN=70; QMAX=95; else QMIN=84; QMAX=97; fi
LANG="deu"; PSM=3; OEM=3; OCRSCALE=67; DPITAG=402; IMGSCALE=25
NCPU="$(sysctl -n hw.ncpu)"
CREATOR="tesseract 5 + guetzli + Ghostscript"      # honest
AUTHOR="Markt & Technik"
TITLE="64'er $TAG"
NOW="$(date +"D:%Y%m%d%H%M%S%z" | sed 's/\(+[0-9][0-9]\)\([0-9][0-9]\)$/\1'"'"'\2'"'"'/')"

[[ -n "$PYBIN" ]] || { echo "no ocrmypdf python (pikepdf) found -- brew install ocrmypdf"; exit 1; }
[[ -s "$SWAP" ]]  || { echo "missing $SWAP"; exit 1; }
[[ -n "$ICC" ]]   || { echo "no ghostscript srgb.icc found -- brew install ghostscript"; exit 1; }

mkdir -p "$CACHE"
# log to file directly (NOT via `>(tee …)`: a tee child makes bare `wait` deadlock)
exec >> "$LOG" 2>&1
echo "=== $(date '+%H:%M:%S') build $IN -> $OUT  title='$TITLE' ==="

# page list 001..NNN, .tiff or .png (title.png is the page-1 image override, not a page itself)
# A shell loop, NOT `ls ... | xargs`: under `set -o pipefail` a glob that matches nothing (this
# input dir holds PNGs, no TIFFs) makes ls exit non-zero and takes the whole build down before it
# has listed one page. Which it did, at 22:22, with an empty log and exit 1.
pages=""
for f in "$IN"/[0-9][0-9][0-9].tiff "$IN"/[0-9][0-9][0-9].png; do
  [[ -e "$f" ]] || continue
  b="$(basename "$f")"; pages="$pages ${b%.*}"
done
pages=$(printf '%s\n' $pages | sort -u)
[[ -n "$pages" ]] || { echo "no NNN.tiff or NNN.png in $IN"; exit 1; }
echo "pages: $(echo $pages | wc -w)"

# the scan for a page number, whichever extension it was delivered in
src_of() {
  if   [[ -f "$IN/$1.tiff" ]]; then echo "$IN/$1.tiff"
  elif [[ -f "$IN/$1.png"  ]]; then echo "$IN/$1.png"
  else echo ""; fi
}

# ---- Phase 1: OCR each page -> searchable PDF (text + 402dpi image), cached ----
for n in $pages; do
  [[ -s "$CACHE/$n.pdf" ]] && continue
  src="$(src_of "$n")"; [[ -n "$src" ]] || { echo "missing page $n"; exit 1; }
  ( magick "$src" -resize ${OCRSCALE}% +repage -strip "$CACHE/${n}_o.png"
    tesseract "$CACHE/${n}_o.png" "$CACHE/$n" -l "$LANG" --psm "$PSM" --oem "$OEM" --dpi "$DPITAG" pdf 2>/dev/null
    rm -f "$CACHE/${n}_o.png"; echo "[ocr] $n" ) &
  while (( $(jobs -r | wc -l) >= NCPU )); do wait -n; done
done; wait

# ---- Phase 2: 150dpi rasters (page 1 = title.png, matched to page-1 dims), cached ----
first=$(echo $pages | awk '{print $1}')
dims=$(magick "$(src_of "$first")" -format "%[fx:round(w*$IMGSCALE/100)] %[fx:round(h*$IMGSCALE/100)]" info:)
W1=${dims% *}; H1=${dims#* }
for n in $pages; do
  [[ -s "$CACHE/${n}_150.png" ]] && continue
  if [[ "$n" == "$first" && -f "$TITLE_PNG" ]]; then
    # EXACT SIZE OR STOP. title.png is a 150 dpi cover that REPLACES page 1's image, so it has to
    # be the size that page 1 reduces to. The old `-resize WxH!` forced whatever it was given onto
    # that box -- a silent aspect-ratio distortion of the one page everybody looks at first.
    td=$(magick identify -format "%wx%h" "$TITLE_PNG")
    if [[ "$td" != "${W1}x${H1}" ]]; then
      echo "title.png is $td, page $first at ${IMGSCALE}% is ${W1}x${H1} -- refusing to rescale it"
      exit 1
    fi
    echo "[embed] $n <- $TITLE_PNG ($td, verbatim)"
    magick "$TITLE_PNG" +repage -strip "$CACHE/${n}_150.png"
  else
    magick "$(src_of "$n")" -resize ${IMGSCALE}% +repage -strip "$CACHE/${n}_150.png"
  fi
done

# PDF/A definition (ICC OutputIntent + DOCINFO metadata)
PDFADEF="$CACHE/pdfa_def.ps"
cat > "$PDFADEF" <<EOF
%!
[ /Title ($TITLE) /Author ($AUTHOR) /Creator ($CREATOR) /CreationDate ($NOW) /ModDate ($NOW) /DOCINFO pdfmark
[/_objdef {icc_PDFA} /type /stream /OBJ pdfmark
[{icc_PDFA} <</N 3>> /PUT pdfmark
[{icc_PDFA} ($ICC) (r) file /PUT pdfmark
[/_objdef {OutputIntent_PDFA} /type /dict /OBJ pdfmark
[{OutputIntent_PDFA} << /Type /OutputIntent /S /GTS_PDFA1
  /DestOutputProfile {icc_PDFA} /OutputConditionIdentifier (sRGB) /Info (sRGB) >> /PUT pdfmark
[{Catalog} <</OutputIntents [ {OutputIntent_PDFA} ]>> /PUT pdfmark
EOF

# build the full PDF/A at a given guetzli quality, return byte size
build_at() {  # $1=quality
  # NAMESPACED BY ENCODER: guetzli q88 and ImageMagick q88 are different images at the same path
  # otherwise, and the cache would hand a fast run's JPEG to a guetzli run silently.
  local q="$1" qd="$CACHE/$ENCODER-q$1"
  mkdir -p "$qd"
  for n in $pages; do
    [[ -s "$qd/$n.jpg" ]] && continue
    if [[ "$ENCODER" == "fast" ]]; then
      ( magick "$CACHE/${n}_150.png" -quality "$q" -strip -interlace none "$qd/$n.jpg" ) &
    else
      ( guetzli --quality "$q" "$CACHE/${n}_150.png" "$qd/$n.jpg" 2>/dev/null ) &
    fi
    while (( $(jobs -r | wc -l) >= NCPU )); do wait -n; done
  done; wait
  for n in $pages; do
    [[ -s "$qd/${n}_g.pdf" ]] && continue
    ( "$PYBIN" "$SWAP" "$CACHE/$n.pdf" "$qd/$n.jpg" "$qd/${n}_g.pdf" ) &
    while (( $(jobs -r | wc -l) >= NCPU )); do wait -n; done
  done; wait
  local gp=(); for n in $pages; do gp+=("$qd/${n}_g.pdf"); done
  gs -q -o "$qd/merged.pdf" -sDEVICE=pdfwrite -dAutoRotatePages=/None -dPassThroughJPEGImages=true "${gp[@]}" 2>/dev/null
  gs -dPDFA=3 -dBATCH -dNOPAUSE -dQUIET -sColorConversionStrategy=RGB -sDEVICE=pdfwrite \
     -dPDFACompatibilityPolicy=1 -dAutoRotatePages=/None -dPassThroughJPEGImages=true \
     -sOutputFile="$qd/out.pdf" "$PDFADEF" "$qd/merged.pdf" 2>/dev/null
  stat -f%z "$qd/out.pdf"
}

# ---- Phase 3: binary-search highest guetzli quality with size < LIMIT ----
lo=$QMIN; hi=$QMAX; best=""; bestf=""
while (( lo <= hi )); do
  mid=$(( (lo+hi)/2 ))
  sz=$(build_at "$mid")
  printf "[search] q=%d -> %d bytes (%.2f MB)\n" "$mid" "$sz" "$(awk "BEGIN{print $sz/1e6}")"
  if (( sz <= LIMIT )); then best="$mid"; bestf="$CACHE/$ENCODER-q$mid/out.pdf"; lo=$((mid+1)); else hi=$((mid-1)); fi
done
[[ -n "$best" ]] || { echo "even q$QMIN exceeds $LIMIT"; exit 1; }
cp "$bestf" "$OUT"
# gs PDF/A drops the DOCINFO /Title (Author/Creator/dates survive); set Title with
# exiftool (keeps PDF/A-3B; same tool the archive's own files use for XMP).
if command -v exiftool >/dev/null; then
  exiftool -overwrite_original -q -Title="$TITLE" -XMP-dc:Title="$TITLE" "$OUT"
fi
echo "=== $(date '+%H:%M:%S') DONE -> $OUT  q=$best  $(stat -f%z "$OUT") bytes  PDF/A-3B ==="
pdfinfo -meta "$OUT" 2>/dev/null | grep -iE 'pdfaid|conformance' | head -1
