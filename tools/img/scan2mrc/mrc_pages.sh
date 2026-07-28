#!/bin/bash
# Render MRC PDFs for every page whose cached inputs have appeared, and keep watching for more.
#
# Per page:  mask the score with the sidecar  (unknown regions must not form clusters)
#            -> build the RGB page the MRC render wants, from the cached display CMYK
#            -> mrcpipe mrc --bg-dpi 150
#            -> delete the RGB page (173 MB, regenerable in ~20s)
#
# Background dpi is 150 because the measured screen ruling for this issue is 136-159 lpi and the
# halftone discarded everything above ~ruling/2 -- 200 dpi was above the information limit. On
# p007 that is 2.00MB -> 1.16MB for a 2.7-level difference in the photo, i.e. nothing visible.
#
# Idempotent on mrc/NNN.pdf; polls until every page is rendered or --once is given.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/rust_pipeline/target/release/mrcpipe"
PY=/opt/homebrew/bin/python3.11
T=/Users/mist/DNB/8609/tmp
BGDPI=${BGDPI:-150}
mkdir -p "$T/mrc"

once=0
[ "${1:-}" = "--once" ] && once=1

while :; do
  did=0; pend=0
  for i in $(seq 1 176); do
    n=$(printf "%03d" "$i")
    [ -s "$T/mrc/$n.pdf" ] && continue
    if [ ! -s "$T/score/$n.npy" ] || [ ! -s "$T/render/deliver/${n}_cmyk_display_filled.tif" ]; then
      pend=$((pend+1)); continue
    fi
    echo "$(date +%H:%M:%S) p$n mrc"
    $PY - "$n" <<'EOF' || { echo "  p$n prep failed"; continue; }
import sys, shutil, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
n = sys.argv[1]; T = "/Users/mist/DNB/8609/tmp"
s = np.load(f"{T}/score/{n}.npy")
kn = np.asarray(Image.open(f"{T}/render/deliver/{n}_known.png").convert("L")) > 127
H, W = kn.shape; hy, hx = s.shape; cy, cx = H // hy, W // hx
unk = 1 - kn[:hy * cy, :hx * cx].reshape(hy, cy, hx, cx).mean((1, 3))
np.save(f"{T}/score/{n}m.npy", np.where(unk > 0.25, 0.0, s).astype(np.float32))
shutil.copy(f"{T}/score/{n}_cov.npy", f"{T}/score/{n}m_cov.npy")
Image.open(f"{T}/render/deliver/{n}_cmyk_display_filled.tif").convert("RGB").save(
    f"{T}/render/deliver/{n}_page_rgb.png", compress_level=1)
EOF
    $MP mrc "$T/render/deliver/${n}_page_rgb.png" "$T/score/${n}m.npy" "$T/mrc/$n.pdf" \
        --bg-dpi "$BGDPI" >/dev/null 2>&1 && echo "  p$n -> $(du -h "$T/mrc/$n.pdf" | cut -f1)" \
        || echo "  p$n MRC FAILED"
    rm -f "$T/render/deliver/${n}_page_rgb.png" "$T/score/${n}m_cov.npy"
    did=$((did+1))
  done
  echo "$(date +%H:%M:%S) pass done: rendered $did, waiting on $pend"
  [ "$once" = 1 ] && break
  [ "$pend" = 0 ] && break
  sleep 120
done
echo "all available pages rendered"
