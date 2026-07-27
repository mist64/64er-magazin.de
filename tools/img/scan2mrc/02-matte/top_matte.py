#!/usr/bin/env python3
"""Top-wedge matte: mark the near-black bed wedge along the top edge as unknown (alpha 0).

Bed is NEAR-BLACK (<~15) and thin (1-5px @600, a wedge or very-thin trapeze); printed ink -- even
full-bleed dark ads (p047) -- stays lighter, so a LOW threshold separates bed from ink.
Guard: if a column's connected top-dark runs DEEPER than CAP it's not bed (it's ink touching the top)
-> keep that column. "If no wedge, keep" -- safe, since wrongly-kept pixels on a black bg are black too.

Steps: near-black connected to the TOP border, within a thin top band -> columnar downward-closure ->
per-column cap -> resolution-relative safety margin. Output RGBA (bed transparent).
"""
import argparse, numpy as np, cv2, scipy.ndimage as ndi
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

BED_THR   = 15     # bed near-black; gray paper-edge shadow (~19-36) and ink stay above
TOP_BAND  = 0.05   # bed sits in the top few % only
CAP_600   = 120    # max bed thickness in a column @600dpi (skew+non-flush); deeper => ink => keep
MARGIN_600 = 1     # resolution-relative safety margin

def top_matte(rgb, dpi):
    a = np.asarray(rgb); H, W, _ = a.shape
    s = dpi / 600.0
    cap = round(CAP_600 * s); margin = max(1, round(MARGIN_600 * s))
    dark = (a.mean(2) < BED_THR).astype(np.uint8)
    n, lbl = cv2.connectedComponents(dark, 8)
    bed = np.isin(lbl, list(set(np.unique(lbl[0, :])) - {0}))   # connected to top border
    bed[int(TOP_BAND * H):] = False
    cols = bed.any(0)
    lowest = (H - 1) - bed[::-1].argmax(0)                       # lowest bed row per column
    colh = np.where(cols, lowest + 1, 0)
    keep_col = colh <= cap                                       # thin => bed; deep => ink, keep
    fill = (np.arange(H)[:, None] <= lowest[None, :]) & cols[None, :] & keep_col[None, :]
    fill = ndi.binary_dilation(fill, iterations=margin)
    alpha = np.where(fill, 0, 255).astype(np.uint8)
    return np.dstack([a, alpha]), 100 * fill.mean(), int(colh[keep_col].max() if keep_col.any() else 0)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("out"); ap.add_argument("--dpi", type=int, default=600)
    A = ap.parse_args()
    rgba, pct, mh = top_matte(Image.open(A.img).convert("RGB"), A.dpi)
    Image.fromarray(rgba, "RGBA").save(A.out)
    print(f"{A.img}: cleared {pct:.3f}% (max bed height {mh}px) -> {A.out}")
