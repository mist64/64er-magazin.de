#!/bin/bash
# Unified per-issue CMYK pipeline.
# Consumes:
#   <cwd>/NNN.png        — source pages (600 or 2400 dpi, auto-detected)
#   <cwd>/widths.txt     — per-page kept width in 150-dpi-resize px
# Produces under <out_dir>/:
#   150/                 sRGB 150 dpi, uncropped
#   150_cropped/         sRGB 150 dpi, cropped to A4
#   600/                 sRGB 600 dpi, uncropped
#   600_cropped/         sRGB 600 dpi, cropped to A4
#   600_bw_cropped/      1-bit 600 dpi, cropped (only for pure-B&W pages)
#   lq/                  150_cropped for color pages, 600_bw_cropped for B&W
#   hq/                  600_cropped for color pages, 600_bw_cropped for B&W
#   saturation.txt       per-page max RGB-sat + bw/col flag
# All outputs are TIFF (LZW for color, Group4 for bilevel). Filenames: NNN.tiff.
#
# Usage: pipeline.sh <out_dir> [--layout=book|standard] [--fizz=N]
#
# Layout chooses the cropping convention:
#   standard: page is in the source as-is. ODD pages take the rightmost
#             crop_w pixels of the 150-resize, gravity west.
#             EVEN pages take the leftmost crop_w pixels, gravity east.
#   book:     scan layout is [page WEST] [black bg EAST].
#             ODD  pages skip FIZZ px on the west (fizz cut), gravity west.
#             EVEN pages take leftmost crop_w, gravity east.
#
# Run from the issue's PNG directory.

set -e

LAYOUT=standard
FIZZ=12

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <out_dir> [--layout=book|standard] [--fizz=N]"
  exit 1
fi
out=$1
shift
for arg in "$@"; do
  case "$arg" in
    --layout=*) LAYOUT="${arg#*=}";;
    --fizz=*)   FIZZ="${arg#*=}";;
    *) echo "unknown arg: $arg"; exit 1;;
  esac
done

if [ "$LAYOUT" != "book" ] && [ "$LAYOUT" != "standard" ]; then
  echo "--layout must be book or standard"; exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICC_CMYK="$SCRIPT_DIR/USWebCoatedSWOP.icc"
ICC_RGB="$SCRIPT_DIR/AdobeRGB1998.icc"
CONVERT_PY="$SCRIPT_DIR/convert.py"

a4_w=1240
a4_h=1754
a4_w_600=$((a4_w * 4))
a4_h_600=$((a4_h * 4))
FIZZ_600=$((FIZZ * 4))

DPI_THRESH=10000
SAT_MAX_THRESH=175
BILEVEL_THRESH="65%"

d150="$out/150"
d150c="$out/150_cropped"
d600="$out/600"
d600c="$out/600_cropped"
d600bw="$out/600_bw_cropped"
d600sp="$out/600_spot_cropped"
dlq="$out/lq"
dhq="$out/hq"
mkdir -p "$out" "$d150" "$d150c" "$d600" "$d600c" "$d600bw" "$d600sp" "$dlq" "$dhq"

sat_log="$out/saturation.txt"
[ -f "$sat_log" ] || echo "# pid max_sat bw_flag (threshold max<$SAT_MAX_THRESH)" > "$sat_log"

cleanup() { rm -f /tmp/pipeline.$$.*.tiff; }
trap cleanup EXIT

while IFS=':' read -r pid crop_w; do
  pid="${pid//[[:space:]]/}"
  crop_w="${crop_w//[[:space:]]/}"
  case "$pid" in '#'*|'') continue;; esac
  [ -z "$crop_w" ] && continue

  src="${pid}.png"
  if [ ! -f "$src" ]; then
    echo "! missing $src"
    continue
  fi

  flq="$dlq/${pid}.tiff"
  if [ -e "$flq" ]; then
    echo "skip $pid (lq exists)"
    continue
  fi

  echo "== $pid =="

  src_w=$(magick identify -format "%w" "$src")
  if [ "$src_w" -gt "$DPI_THRESH" ]; then
    src_dpi=2400
    resize_150="6.25%"
    resize_600="25%"
  else
    src_dpi=600
    resize_150="25%"
    resize_600="100%"
  fi
  echo "   src ${src_w}px → ${src_dpi}dpi"

  tmp_cmyk=/tmp/pipeline.$$.cmyk.tiff
  tmp_cmyk_c=/tmp/pipeline.$$.cmyk_c.tiff

  echo "   * convert.py"
  /usr/bin/python3 "$CONVERT_PY" "$src" "$tmp_cmyk"

  echo "   * contrast"
  magick "$tmp_cmyk" \
    -colorspace CMYK \
    -channel C -level 50%,90% \
    -channel M -level 30%,70% \
    -channel Y -level 30%,70% \
    -channel K -level 90%,95% \
    +channel -colorspace CMYK \
    -density ${src_dpi} -set units PixelsPerInch \
    "$tmp_cmyk_c"
  # NOTE: keep $tmp_cmyk (pre-contrast) — bilevel reads K from it, since
  # contrast's K-level 90%,95% would flatten the K channel for bilevel use.

  f150="$d150/${pid}.tiff"
  f600="$d600/${pid}.tiff"
  f150c="$d150c/${pid}.tiff"
  f600c="$d600c/${pid}.tiff"
  f600bw="$d600bw/${pid}.tiff"
  f600sp="$d600sp/${pid}.tiff"

  echo "   * 600 sRGB"
  magick "$tmp_cmyk_c" \
    -resize ${resize_600} \
    -profile "$ICC_CMYK" -profile "$ICC_RGB" \
    -density 600 -set units PixelsPerInch \
    -compress LZW \
    "$f600"

  echo "   * 150 sRGB"
  magick "$tmp_cmyk_c" \
    -resize ${resize_150} \
    -profile "$ICC_CMYK" -profile "$ICC_RGB" \
    -density 150 -set units PixelsPerInch \
    -compress LZW \
    "$f150"

  w150=$(magick identify -format "%w" "$f150")
  if [ $((10#$pid % 2)) -eq 0 ]; then
    gravity=east
    x0_150=0
  else
    gravity=west
    if [ "$LAYOUT" = "book" ]; then
      x0_150=$FIZZ
    else
      x0_150=$((w150 - crop_w))
    fi
  fi
  crop_w_600=$((crop_w * 4))
  x0_600=$((x0_150 * 4))

  echo "   * crop 150 (${crop_w}+${x0_150} gravity ${gravity})"
  magick "$f150" \
    -crop ${crop_w}x${a4_h}+${x0_150}+0 \
    -background white -gravity ${gravity} \
    -extent ${a4_w}x${a4_h} \
    -compress LZW \
    "$f150c"

  echo "   * crop 600"
  magick "$f600" \
    -crop ${crop_w_600}x${a4_h_600}+${x0_600}+0 \
    -background white -gravity ${gravity} \
    -extent ${a4_w_600}x${a4_h_600} \
    -compress LZW \
    "$f600c"

  echo "   * saturation"
  max_sat_int=$(/usr/bin/python3 -c "
from PIL import Image
import numpy as np
Image.MAX_IMAGE_PIXELS = None
arr = np.array(Image.open('$f150c').convert('RGB'), dtype=int)
r, g, b = arr[...,0], arr[...,1], arr[...,2]
s = np.maximum.reduce([r,g,b]) - np.minimum.reduce([r,g,b])
print(int(s.max()))
")

  # K-bilevel (600 dpi, cropped) from pre-contrast CMYK — used both as
  # the final output for pure-B&W pages AND as the black-mask input for
  # spot_render.py (preserves halftone dot patterns).
  tmp_bw=/tmp/pipeline.$$.bw.tiff
  echo "   * K bilevel"
  magick "$tmp_cmyk" \
    -channel K -separate +channel \
    -resize ${resize_600} \
    -threshold ${BILEVEL_THRESH} -negate \
    -type BiLevel -depth 1 \
    -density 600 -set units PixelsPerInch \
    "$tmp_bw"
  magick "$tmp_bw" \
    -crop ${crop_w_600}x${a4_h_600}+${x0_600}+0 \
    -background white -gravity ${gravity} \
    -extent ${a4_w_600}x${a4_h_600} \
    -type BiLevel -depth 1 \
    -compress Group4 \
    "$f600bw"
  rm "$tmp_bw"

  # always produce a 3-colour render using K bilevel as black mask
  echo "   * 3-colour (paper+K-bilevel+canonical spot ink)"
  /usr/bin/python3 "$SCRIPT_DIR/spot_render.py" "$f600c" "$f600sp" "$f600bw"

  if [ "$max_sat_int" -lt "$SAT_MAX_THRESH" ]; then
    bw_flag=BW
    echo "   * lq/hq = bw (max_sat=${max_sat_int})"
    cp "$f600bw" "$flq"
    cp "$f600bw" "$dhq/${pid}.tiff"
  elif /usr/bin/python3 "$SCRIPT_DIR/spot_render.py" --check "$f600c" >/dev/null 2>&1; then
    bw_flag=spot
    echo "   * lq/hq = spot (max_sat=${max_sat_int})"
    cp "$f600sp" "$flq"
    cp "$f600sp" "$dhq/${pid}.tiff"
  else
    bw_flag=col
    echo "   * lq/hq = color (max_sat=${max_sat_int})"
    cp "$f150c" "$flq"
    cp "$f600c" "$dhq/${pid}.tiff"
  fi

  echo "$pid $max_sat_int $bw_flag" >> "$sat_log"

  rm "$tmp_cmyk" "$tmp_cmyk_c"
done < widths.txt

echo "done. outputs in $out/"
