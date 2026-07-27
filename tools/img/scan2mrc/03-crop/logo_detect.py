#!/usr/bin/env python3
"""
64'er magazine logo + page-number detector  (issue 8609)
========================================================

Finds the bold "64'er" wordmark that sits in the OUTER-bottom corner of most
pages.  It is the rigid anchor for the A4 crop stage, so we need a precise,
repeatable reference point per page.

WHAT WE KNOW (verified on the scans)
------------------------------------
* The "64'er" wordmark is the SAME glyph on every page (a heavy 3D drop-shadow
  wordmark). It is NOT mirrored between parities -> single template works.
* The page NUMBER is always the OUTERMOST element; the wordmark sits just
  inboard of it.
      even pages -> bottom-LEFT corner:  "<num>  64'er"
      odd  pages -> bottom-RIGHT corner:  "64'er  <num>"
* Ad / full-bleed pages may lack the logo entirely -> reported found=False.

COORDINATE CONVENTION (read this)
---------------------------------
Detection runs on the 600-dpi thumbnails (thumbs_600/NNN.png). All OUTPUT
coordinates are in FULL-RES 2400-dpi MASTER pixels, i.e. 600-dpi pixels
multiplied by SCALE_600_TO_MASTER (=4). Origin = top-left of the (deskewed,
matted) page image, +x right, +y down. Page height is constant (7188 px @600,
28752 @master); widths vary per page (deskew crop), so x is measured from the
left edge of each page's own image.

The reported ANCHOR is the corner of the wordmark bounding box that is nearest
the page's outer-bottom corner:
      BL page -> wordmark (left , bottom)
      BR page -> wordmark (right, bottom)
We also emit the full wordmark bbox so the crop stage can choose its own point.

METHOD
------
1. Coarse localize at 150 dpi (fast) in both bottom corners with a downscaled
   template (multi-angle, normalized cross-correlation). Pick the better side.
2. Refine at 600 dpi in a small window around the coarse hit, sweeping a few
   small rotations (analog scan skew) to get a precise bbox + score.
3. Cross-check: confirm page-number ink exists on the OUTER side of the
   wordmark (raises/lowers confidence, never hard-rejects).
"""

import os, sys, json, glob
import numpy as np
import cv2
from PIL import Image

# ------------------------------------------------------------------------- #
#  TUNABLE CONSTANTS  (all lengths in pixels unless noted)                   #
# ------------------------------------------------------------------------- #
THUMB600_DIR   = "/Users/mist/DNB/8609/thumbs_600"   # precise, detection here
THUMB150_DIR   = "/Users/mist/DNB/8609/thumbs_150"   # fast, coarse pass
OUT_DIR        = "/Users/mist/DNB/8609/tmp"
TEMPLATE_600   = os.path.join(os.path.dirname(__file__), "template_64er_600.png")

SCALE_600_TO_MASTER = 4      # 2400-dpi master / 600-dpi thumb
DPI600_OVER_150     = 4      # 600 / 150

# --- search band in the 600-dpi image (page height ~7188) ---------------- #
# Wordmark baseline observed ~ h-420..h-300; give generous margin for scan
# placement variation. y measured from TOP; expressed as offset from bottom.
BAND_TOP_FROM_BOTTOM_600    = 640    # search rows: h-640 ..
BAND_BOTTOM_FROM_BOTTOM_600 = 150    #            .. h-150
# horizontal reach of each corner (fraction of page width) that may contain
# the wordmark.  Wordmark is inboard of the number but well within these.
CORNER_FRAC = 0.48

# --- template matching --------------------------------------------------- #
INK_THRESH        = 100      # grey < this = ink (for bbox / number band)
MATCH_ANGLES_150  = [-2.0, -1.0, 0.0, 1.0, 2.0]   # coarse rotation sweep
MATCH_ANGLES_600  = [-2.5, -1.5, -0.75, 0.0, 0.75, 1.5, 2.5]  # fine sweep
REFINE_WIN_PAD_600 = 90      # +/- window (600dpi px) around coarse hit for refine

# --- confidence gate ----------------------------------------------------- #
SCORE_MIN_ACCEPT  = 0.42     # below this on the 600 refine -> found=False
SCORE_STRONG      = 0.55     # at/above -> "strong" regardless of number band
NUMBER_BAND_GAP   = 60       # gap (600dpi px) from wordmark to number-band start
NUMBER_BAND_WIDTH = 340      # width (600dpi px) of number-band probe
NUMBER_MIN_INK_PX = 120      # min ink pixels in number band to count as present


# ------------------------------------------------------------------------- #
def _load_gray(path):
    return np.asarray(Image.open(path).convert("L"))


def _rotate_template(tmpl, angle):
    """Rotate template about center, white (255) background, keep size."""
    h, w = tmpl.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(tmpl, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def _match_multi(region, tmpl, angles):
    """Best normalized-CCOEFF match of tmpl (over angles) inside region.
    Returns (score, x, y, angle) with x,y = top-left of match in region coords."""
    best = (-2.0, 0, 0, 0.0)
    if region.shape[0] < tmpl.shape[0] + 2 or region.shape[1] < tmpl.shape[1] + 2:
        return best
    for ang in angles:
        t = _rotate_template(tmpl, ang) if ang != 0.0 else tmpl
        res = cv2.matchTemplate(region, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, mloc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), int(mloc[0]), int(mloc[1]), ang)
    return best


def _corner_region(gray, side, band_top, band_bot, corner_frac):
    """Return (subimg, ox, oy) for the given corner's search band."""
    h, w = gray.shape
    x0 = 0 if side == "L" else int(w * (1 - corner_frac))
    x1 = int(w * corner_frac) if side == "L" else w
    return gray[band_top:band_bot, x0:x1], x0, band_top


def _tight_bbox(gray, x0, y0, x1, y1, thresh):
    """Refine a bbox to the ink extent inside the given window (600dpi coords)."""
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(gray.shape[1], x1); y1 = min(gray.shape[0], y1)
    sub = gray[y0:y1, x0:x1]
    dark = sub < thresh
    ys = np.where(dark.sum(1) > 2)[0]
    xs = np.where(dark.sum(0) > 2)[0]
    if len(ys) == 0 or len(xs) == 0:
        return None
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def _number_band_present(gray, wm_bbox, side, thresh):
    """Check there is ink on the OUTER side of the wordmark (the page number)."""
    x0, y0, x1, y1 = wm_bbox
    if side == "R":  # number is to the RIGHT
        bx0 = x1 + NUMBER_BAND_GAP
        bx1 = bx0 + NUMBER_BAND_WIDTH
    else:            # number is to the LEFT
        bx1 = x0 - NUMBER_BAND_GAP
        bx0 = bx1 - NUMBER_BAND_WIDTH
    bx0 = max(0, bx0); bx1 = min(gray.shape[1], bx1)
    if bx1 <= bx0:
        return False, 0
    band = gray[y0:y1, bx0:bx1]
    ink = int((band < thresh).sum())
    return ink >= NUMBER_MIN_INK_PX, ink


# ------------------------------------------------------------------------- #
def detect_page(num, tmpl600, tmpl150):
    """Detect the logo on one page. Returns a result dict (master coords)."""
    p600 = os.path.join(THUMB600_DIR, f"{num:03d}.png")
    p150 = os.path.join(THUMB150_DIR, f"{num:03d}.png")
    g600 = _load_gray(p600)
    g150 = _load_gray(p150)
    h6, w6 = g600.shape

    band_top_6 = h6 - BAND_TOP_FROM_BOTTOM_600
    band_bot_6 = h6 - BAND_BOTTOM_FROM_BOTTOM_600
    # 150dpi band scaled down
    h1, w1 = g150.shape
    s = w1 / w6                      # 150/600 horiz scale (~0.25)
    band_top_1 = int(band_top_6 * (h1 / h6))
    band_bot_1 = int(band_bot_6 * (h1 / h6))

    # ---- 1) coarse pass @150 on both sides ---- #
    coarse = {}
    for side in ("L", "R"):
        reg, ox, oy = _corner_region(g150, side, band_top_1, band_bot_1, CORNER_FRAC)
        sc, mx, my, ang = _match_multi(reg, tmpl150, MATCH_ANGLES_150)
        coarse[side] = dict(score=sc, x=ox + mx, y=oy + my, ang=ang)

    exp_side = "L" if num % 2 == 0 else "R"   # expected parity
    # choose side: prefer the higher-scoring side
    best_side = max(coarse, key=lambda k: coarse[k]["score"])

    # ---- 2) refine @600 around coarse hit ---- #
    th, tw = tmpl600.shape
    # map coarse 150 top-left -> 600 top-left
    cx6 = int(coarse[best_side]["x"] / s)
    cy6 = int(coarse[best_side]["y"] * (h6 / h1))
    rx0 = max(0, cx6 - REFINE_WIN_PAD_600)
    ry0 = max(0, cy6 - REFINE_WIN_PAD_600)
    rx1 = min(w6, cx6 + tw + REFINE_WIN_PAD_600)
    ry1 = min(h6, cy6 + th + REFINE_WIN_PAD_600)
    region = g600[ry0:ry1, rx0:rx1]
    sc, mx, my, ang = _match_multi(region, tmpl600, MATCH_ANGLES_600)
    mtx0 = rx0 + mx           # matched template top-left (600dpi)
    mty0 = ry0 + my

    # tighten to actual ink bbox inside matched template footprint
    bbox600 = _tight_bbox(g600, mtx0, mty0, mtx0 + tw, mty0 + th, INK_THRESH)
    if bbox600 is None:
        bbox600 = (mtx0, mty0, mtx0 + tw, mty0 + th)

    num_present, num_ink = _number_band_present(g600, bbox600, best_side, INK_THRESH)

    # ---- confidence ---- #
    found = sc >= SCORE_MIN_ACCEPT
    conf = float(sc)
    if found and sc < SCORE_STRONG and not num_present:
        # weak match with no supporting number band -> distrust
        found = False

    # anchor = wordmark bbox corner nearest the page's outer-bottom corner
    bx0, by0, bx1, by1 = bbox600
    if best_side == "L":
        ax6, ay6 = bx0, by1
    else:
        ax6, ay6 = bx1, by1

    m = SCALE_600_TO_MASTER
    return dict(
        page=num,
        found=bool(found),
        side=("BL" if best_side == "L" else "BR"),
        expected_side=("BL" if exp_side == "L" else "BR"),
        parity_ok=bool(best_side == exp_side),
        confidence=round(conf, 4),
        angle_deg=round(float(ang), 2),
        number_band_present=bool(num_present),
        number_band_ink=int(num_ink),
        # anchor + bbox in FULL-RES 2400dpi MASTER coordinates
        anchor_x=int(ax6 * m),
        anchor_y=int(ay6 * m),
        bbox_master=[int(bx0 * m), int(by0 * m), int(bx1 * m), int(by1 * m)],
        # keep 600dpi bbox too (handy for drawing / debug)
        bbox_600=[int(bx0), int(by0), int(bx1), int(by1)],
        page_w_600=int(w6), page_h_600=int(h6),
    )


def main():
    tmpl600 = _load_gray(TEMPLATE_600)
    th, tw = tmpl600.shape
    tmpl150 = cv2.resize(tmpl600, (tw // DPI600_OVER_150, th // DPI600_OVER_150),
                         interpolation=cv2.INTER_AREA)

    pages = sorted(int(os.path.basename(p)[:3])
                   for p in glob.glob(os.path.join(THUMB600_DIR, "*.png")))
    if len(sys.argv) > 1:               # optional subset: python logo_detect.py 50 51 89
        pages = [int(x) for x in sys.argv[1:]]

    results = []
    for n in pages:
        r = detect_page(n, tmpl600, tmpl150)
        results.append(r)
        flag = "" if r["found"] else "  <-- NOT FOUND"
        par = "" if r["parity_ok"] else f"  [side={r['side']} exp={r['expected_side']}]"
        print(f"p{n:03d} {r['side']} conf={r['confidence']:.3f} "
              f"ax={r['anchor_x']} ay={r['anchor_y']} numInk={r['number_band_ink']}{par}{flag}")

    out = os.path.join(OUT_DIR, "logo_positions.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    nfound = sum(r["found"] for r in results)
    print(f"\n{nfound}/{len(results)} found. wrote {out}")


if __name__ == "__main__":
    main()
