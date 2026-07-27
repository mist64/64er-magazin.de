#!/usr/bin/env python3
"""MEASURE how much real page exists around the LOGO on every page.

Purpose: the output crop is LOGO-ANCHORED -- the wordmark must land at the same output
position on every page (the logo wanders 9-11 mm relative to the sheet edges, so anchoring
on the edges would inherit that wander). The question this answers is therefore NOT "where
is the page edge in the scan" but:

    how far can a logo-anchored window extend in each direction before it runs off
    the real page, on the WORST page / on 95% of pages?

That is what fixes the window size. Only once the window is fixed do we know what a cut
into the margin actually costs, so this must be measured BEFORE the cut margins are tuned
-- not derived from a provisional crop.

For every page we report, in millimetres from the logo anchor:
    left, right, top, bottom  -- distance to the nearest UNKNOWN (alpha) pixel in that
                                 direction, i.e. to the page boundary the detectors found
                                 (bed / neighbour / hole line, whichever bounds first).

The alpha comes from the same stack the renderer builds, so what is measured is exactly
what a crop would get. Pages whose logo was INTERPOLATED rather than detected are reported
separately: their anchor carries the interpolation error, so pooling them would corrupt the
percentile that decides the window.

Outputs:
  tmp/extents.json  per page: anchor, four distances, logo confidence, source flags
  stdout            the distribution, and the limiting pages

Usage: measure_extents.py [pages...]
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stack_render as SR

Image.MAX_IMAGE_PIXELS = None

LOGO_JSON = "/Users/mist/DNB/8609/tmp/logo_positions.json"
OUT_JSON  = "/Users/mist/DNB/8609/tmp/extents.json"
DPI       = 600
MASTER    = 2400
SCALE     = MASTER // DPI          # logo_positions.json is in MASTER px
MM        = 25.4 / DPI             # one 600-dpi px in mm


def edge_depths(alpha):
    """Deepest UNINTERRUPTED alpha incursion from each of the four borders.

    Per scanline we take the LEADING run of alpha from that border, then the MAX over all
    scanlines. The cut lines are slanted (page skew) and curved (the sheet bows), so the
    incursion depth varies along the edge; a rectangular window has to clear the deepest
    one, not the typical one. Interior alpha (clip holes) is deliberately NOT counted --
    it does not bound the window, it just needs filling later.

    Returns (left, right, top, bottom) in px.
    """
    A = (alpha == 0)
    H, W = A.shape

    def lead(M):                      # M: rows x cols, leading run per row, max over rows
        run = np.where(M.any(1), M.argmin(1), M.shape[1])   # argmin of a bool = first False
        return int(run.max())

    left   = lead(A)
    right  = lead(A[:, ::-1])
    top    = lead(A.T)
    bottom = lead(A.T[:, ::-1])
    return left, right, top, bottom


def clearances(alpha, ax, ay):
    """Distance from the logo anchor to each border's deepest alpha incursion (px)."""
    H, W = alpha.shape
    l, r, t, b = edge_depths(alpha)
    return (ax - l, (W - r) - ax, ay - t, (H - b) - ay), (l, r, t, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    a = ap.parse_args()

    logos = {d["page"]: d for d in json.load(open(LOGO_JSON))}
    pages = a.pages or list(range(1, 177))
    out = []

    for n in pages:
        f = os.path.join(SR.OUT_DIR, "%03d.png" % n)
        if not os.path.exists(f):
            continue
        im = Image.open(f)
        alpha = np.asarray(im)[:, :, 3]
        L = logos.get(n)
        if not L:
            continue
        # the stack is DESKEWED and expanded; the logo was measured on the RAW scan, so map
        # it through the same rotation by rotating a marker (avoids the sign trap in NOTES).
        ax0, ay0 = L["anchor_x"] / SCALE, L["anchor_y"] / SCALE
        ang = SR.load_skew().get(n, 0.0)
        if abs(ang) > 1e-3:
            mk = Image.new("L", (L["page_w_600"], L["page_h_600"]), 0)
            mk.putpixel((int(np.clip(ax0, 0, L["page_w_600"] - 1)),
                         int(np.clip(ay0, 0, L["page_h_600"] - 1))), 255)
            mk = mk.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
            ys, xs = np.where(np.asarray(mk) > 0)
            if len(xs):
                ax0, ay0 = float(xs.mean()), float(ys.mean())
        dl, dr, du, dd = first_alpha(alpha, ax0, ay0)
        out.append(dict(page=n, found=bool(L["found"]), conf=round(L["confidence"], 3),
                        parity="even" if n % 2 == 0 else "odd",
                        anchor=[round(ax0, 1), round(ay0, 1)],
                        left_mm=round(dl * MM, 2), right_mm=round(dr * MM, 2),
                        up_mm=round(du * MM, 2), down_mm=round(dd * MM, 2)))
        print("p%03d %-4s logo=%-5s  left %6.1f  right %6.1f  up %6.1f  down %6.1f  mm"
              % (n, out[-1]["parity"], L["found"], out[-1]["left_mm"], out[-1]["right_mm"],
                 out[-1]["up_mm"], out[-1]["down_mm"]))

    json.dump(out, open(OUT_JSON, "w"), indent=1)
    if not out:
        print("no pages measured"); return

    for tag, sel in (("LOGO DETECTED", [o for o in out if o["found"]]),
                     ("LOGO INTERPOLATED", [o for o in out if not o["found"]])):
        if not sel:
            continue
        print("\n%s  (n=%d)" % (tag, len(sel)))
        for k in ("left_mm", "right_mm", "up_mm", "down_mm"):
            v = np.array([o[k] for o in sel])
            worst = min(sel, key=lambda o: o[k])
            print("   %-9s min %6.1f (p%03d)  p5 %6.1f  med %6.1f  max %6.1f"
                  % (k, v.min(), worst["page"], np.percentile(v, 5), np.median(v), v.max()))


if __name__ == "__main__":
    main()
