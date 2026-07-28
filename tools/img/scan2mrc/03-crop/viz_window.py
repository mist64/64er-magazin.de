#!/usr/bin/env python3
"""Draw the A4 crop window on the rendered page, at full 600 dpi.

Input is tmp/stack600 (the alpha render) and tmp/crop_windows_v2.json (the fitted window).
The rectangle is drawn OPAQUE even where it crosses transparent pixels, so the line stays
visible exactly where it matters -- where the window overhangs the known page.

  green   window anchored on this page's OWN detected logo
  blue    window anchored on the SPINE (no logo on this page): horizontal from the measured
          fold, vertical searched for least alpha. Also measured -- a different colour because
          it is a different anchor, not because it is weaker.
  orange  anything inferred (interpolated anchor) -- should no longer occur
  magenta the anchor itself, where there is one
"""
import os, sys, json, argparse
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from multiprocessing import Pool
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
STACK = "/Users/mist/DNB/8609/tmp/stack600"
WINS = "/Users/mist/DNB/8609/tmp/crop_windows_v2.json"
OUTD = "/Users/mist/DNB/8609/tmp/crop_preview"
LINE = 5            # px @600dpi -- thicker than the 3px hairline because this line is compared
                    # against the page edge from across the whole sheet, not inspected locally
COL_LOGO = (0, 220, 0)
COL_SPINE = (40, 120, 255)
COL_INTERP = (255, 140, 0)
COL_ANCHOR = (255, 0, 255)


def paint(a, y0, y1, x0, x1, col):
    """Set an opaque block, clipped to the canvas."""
    H, W = a.shape[:2]
    y0, y1 = max(int(y0), 0), min(int(y1), H)
    x0, x1 = max(int(x0), 0), min(int(x1), W)
    if y1 <= y0 or x1 <= x0:
        return
    a[y0:y1, x0:x1, :3] = col
    a[y0:y1, x0:x1, 3] = 255


def one(item):
    n, w = item
    im = Image.open(os.path.join(STACK, "%03d.png" % n))
    a = np.asarray(im).copy()
    col = {"logo": COL_LOGO, "spine": COL_SPINE}.get(w["src"], COL_INTERP)
    x0, y0 = w["x0"], w["y0"]
    x1, y1 = x0 + w["w"], y0 + w["h"]
    paint(a, y0, y0 + LINE, x0, x1, col)          # top
    paint(a, y1 - LINE, y1, x0, x1, col)          # bottom
    paint(a, y0, y1, x0, x0 + LINE, col)          # left
    paint(a, y0, y1, x1 - LINE, x1, col)          # right
    if w.get("anchor"):
        ax, ay = w["anchor"]
        paint(a, ay - 2, ay + 3, ax - 40, ax + 41, COL_ANCHOR)
        paint(a, ay - 40, ay + 41, ax - 2, ax + 3, COL_ANCHOR)
    elif w.get("spine_x") is not None:            # mark the fold the window was placed from
        sx = int(round(w["spine_x"]))
        paint(a, y0, y1, sx - 2, sx + 3, COL_ANCHOR)
    os.makedirs(OUTD, exist_ok=True)
    Image.fromarray(a, "RGBA").save(os.path.join(OUTD, "%03d.png" % n))
    return n, w["src"], w.get("alpha_pct")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("pages", nargs="*", type=int)
    A = ap.parse_args()
    wins = json.load(open(WINS))["windows"]
    items = [(int(k), v) for k, v in wins.items()]
    if A.pages:
        items = [it for it in items if it[0] in A.pages]
    items.sort()
    with Pool(A.jobs) as pool:
        for n, src, pct in pool.imap_unordered(one, items):
            print("p%03d %-12s alpha %s" % (n, src, "%.2f%%" % pct if pct is not None else "n/a"))
