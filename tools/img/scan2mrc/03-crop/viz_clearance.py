#!/usr/bin/env python3
"""Draw the three clearance measures on the page, so the numbers can be checked by eye.

  green   RAY   straight from the anchor along its own row/column
  blue    RECT  largest alpha-free rectangle (water-filled)
  red     BAND  where alpha coverage across the box exceeds the threshold
  magenta the anchor (outer-bottom corner of the 64'er wordmark)
Alpha itself is washed yellow so the three boxes can be read against it.
"""
import os, sys, json
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
STACK = "/Users/mist/DNB/8609/tmp/stack600"
CLEAR = "/Users/mist/DNB/8609/tmp/logo_clearance.json"
OUTD = "/Users/mist/DNB/8609/tmp/clearance"
SCALE = 6
COLS = {"ray": (0, 200, 0), "rect": (40, 90, 255), "band": (255, 0, 0)}


def draw(rec):
    n = rec["page"]
    im = Image.open(os.path.join(STACK, "%03d.png" % n))
    a = np.asarray(im)
    rgb = a[..., :3].copy()
    rgb[a[..., 3] == 0] = (255, 235, 120)          # alpha washed yellow
    im = Image.fromarray(rgb).resize((a.shape[1] // SCALE, a.shape[0] // SCALE), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    ax, ay = rec["anchor"][0] / SCALE, rec["anchor"][1] / SCALE
    for i, (k, col) in enumerate(COLS.items()):
        b = rec[k]
        x0 = ax - b["left"] / SCALE
        x1 = ax + b["right"] / SCALE
        y0 = ay - b["top"] / SCALE
        y1 = ay + b["bottom"] / SCALE
        d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=col, width=2)
    d.line([ax - 14, ay, ax + 14, ay], fill=(255, 0, 255), width=3)
    d.line([ax, ay - 14, ax, ay + 14], fill=(255, 0, 255), width=3)
    d.text((8, 8), "p%03d  ray L%d R%d T%d B%d | rect L%d R%d T%d B%d | band L%d R%d T%d B%d"
           % (n, rec["ray"]["left"], rec["ray"]["right"], rec["ray"]["top"], rec["ray"]["bottom"],
              rec["rect"]["left"], rec["rect"]["right"], rec["rect"]["top"], rec["rect"]["bottom"],
              rec["band"]["left"], rec["band"]["right"], rec["band"]["top"], rec["band"]["bottom"]),
           fill=(0, 0, 0))
    os.makedirs(OUTD, exist_ok=True)
    im.save(os.path.join(OUTD, "%03d.png" % n))
    return n


if __name__ == "__main__":
    recs = {r["page"]: r for r in json.load(open(CLEAR))["clearance"] if r.get("ok")}
    pages = [int(x) for x in sys.argv[1:]] or sorted(recs)[:6]
    for p in pages:
        if p in recs:
            print("wrote", draw(recs[p]))
