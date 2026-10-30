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
#   DOTS_BLUR   gaussian sigma (px) that smooths the screen before the two
#               tests; must flatten the screen's dots below DOTS_LOCAL, so a
#               coarser screen needs more; too much and hairlines fade
# HALF OF WHAT IS FREE (r000). This loop used to background EVERY file at once
# with a single `wait`: 38 crops meant 38 concurrent multithreaded magick, the
# shape that emergency-killed another user's model server on SH8607.
_CLAMP="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/img/issue_pdf/load_clamp.sh"
# shellcheck source=img/issue_pdf/load_clamp.sh
[ -r "$_CLAMP" ] && . "$_CLAMP"
JOBS="$(clamp_jobs "${JOBS:-}" 2>/dev/null || echo 4)"

DOTS_LOCAL=${DOTS_LOCAL:-20}
DOTS_SOLID=${DOTS_SOLID:-30}
DOTS_BLUR=${DOTS_BLUR:-1.5}

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
      dots) magick "$i" -colorspace CMYK -channel K -separate +channel -negate -blur 0x${DOTS_BLUR} \
              \( -clone 0 -lat 41x41-${DOTS_LOCAL}% \) \( -clone 0 -threshold ${DOTS_SOLID}% \) -delete 0 \
              -compose multiply -composite "$out" ;;
    esac &
    # sleep, NOT `wait -n`: this script runs under /bin/bash, which on macOS is
    # 3.2 and has no -n. It failed on every iteration and throttled nothing.
    while (( $(jobs -r | wc -l) >= JOBS )); do sleep 0.2; done
  done
done
wait
