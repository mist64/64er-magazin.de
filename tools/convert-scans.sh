#!/bin/bash
# Convert scanned images to final output in ./
# bw/   -> 600 dpi bilevel (no resize)
# gray/ -> 150 dpi grayscale (resize 25%)
# c/    -> 150 dpi color (resize 25%)

for dir in bw gray c; do
  [ -d "$dir" ] || continue
  for i in "$dir"/*.png; do
    [ -f "$i" ] || continue
    out="./${i##*/}"
    case "$dir" in
      bw)   magick "$i" -colorspace CMYK -channel K -separate +channel -threshold 50% -negate "$out" ;;
      gray) magick "$i" -colorspace CMYK -channel K -separate +channel -negate -resize 25% "$out" ;;
      c)    magick "$i" -resize 25% "$out" ;;
    esac &
  done
done
wait
