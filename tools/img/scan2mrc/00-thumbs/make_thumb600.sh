#!/bin/bash
# Serial 2400->600 dpi downscale (/4) of each master. One at a time (masters are ~900MB / ~1.8GB in RAM).
cd ~/DNB/8609
for f in master_2400/[0-9]*.png; do
  n=$(basename "$f")
  out="thumbs_600/$n"
  [ -s "$out" ] && continue
  magick "$f" -resize 25% -density 600 -units PixelsPerInch "$out"
  echo "$(date +%H:%M:%S) done $n ($(ls -la "$out" | awk '{print int($5/1024)"KB"}'))"
done
echo "ALL DONE: $(ls thumbs_600/[0-9]*.png | wc -l) pages"
