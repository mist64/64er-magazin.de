#!/bin/bash
# Convert scanned images to final output in ./
# bw/   -> 600 dpi bilevel (no resize)
# gray/ -> 150 dpi grayscale (resize 25%)
# c/    -> 150 dpi color (resize 25%)
# dots/ -> 600 dpi bilevel, halftone dots removed (no resize)
#
# dots/ settings (override from the environment, e.g. DOTS_LOCAL=15 ./convert-scans.sh):
#   DOTS_LOCAL  how much darker (%) than its 41x41 surroundings a pixel must be
#               to count as ink; higher = less tint noise, more broken hairlines
#   DOTS_SOLID  grey level (%) below which a pixel is ink regardless; higher =
#               solid areas fill better, but a dark tint turns black
DOTS_LOCAL=${DOTS_LOCAL:-20}
DOTS_SOLID=${DOTS_SOLID:-30}

for dir in bw gray c dots; do
  [ -d "$dir" ] || continue
  for i in "$dir"/*.png; do
    [ -f "$i" ] || continue
    out="./${i##*/}"
    case "$dir" in
      bw)   magick "$i" -colorspace CMYK -channel K -separate +channel -threshold 50% -negate "$out" ;;
      gray) magick "$i" -colorspace CMYK -channel K -separate +channel -negate -resize 25% "$out" ;;
      c)    magick "$i" -resize 25% "$out" ;;
      # dots: black where locally darker than the surroundings (keeps hairlines
      # and coarse stipple, drops the fine tint) or globally darker than 30%
      # (keeps solid areas, which -lat alone would hollow out)
      dots) magick "$i" -colorspace CMYK -channel K -separate +channel -negate -blur 0x1 \
              \( -clone 0 -lat 41x41-${DOTS_LOCAL}% \) \( -clone 0 -threshold ${DOTS_SOLID}% \) -delete 0 \
              -compose multiply -composite "$out" ;;
    esac &
  done
done
wait
