#!/usr/bin/env python3
"""SIMPLE spine fit, exactly as specified: per-row argmax of the colour difference between
neighbouring pixels, then fit a line through the resulting points.

This exists to TEST that specification against the elaborate shear_spine.py on the same
pages. If it does as well, shear_spine is over-built and should be replaced by this.

    1. downscale to ~DPI dpi (this is also the descreen: a 4x box average over a 150-lpi
       screen removes the halftone)
    2. per row, x = argmax |f(x+1) - f(x)| over the search band
    3. fit a line through the points

Step 3 is offered in three variants so the cost of robustness is explicit:
    lsq     plain least squares                       ("math 101")
    theil   Theil-Sen (median of pairwise slopes)
    hough   vote for the (x0, slope) with the most points within TOL

CLI: simple_spine.py [pages...] [--fit lsq|theil|hough] [--json OUT]
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

THUMB = "/Users/mist/DNB/8609/thumbs_600"
CLIP  = "/Users/mist/DNB/8609/tmp/clip_holes.json"

# Colour difference must be CHROMA-AWARE. A luma-only (or unweighted RGB) difference misses
# a boundary that changes hue at nearly constant brightness -- the Miami Vice ad is exactly
# that case. Difference is taken in [L, (R-G)*k, (G-B)*k].
CHROMA_W  = 2.2
DPI       = 150          # working resolution
SRC_DPI   = 600
BAND_MM   = 30.0         # binding-side strip to search, mm
X_LO_MM   = 3.0          # ignore the scan-edge shadow, mm
TOL_PX    = 3            # hough: point counts as agreeing within this many px (at DPI)


def points(page, win=None):
    """Step 1+2: per-row argmax of the adjacent-pixel colour difference."""
    im = Image.open(os.path.join(THUMB, "%03d.png" % page)).convert("RGB")
    W, H = im.size
    s = DPI / SRC_DPI
    im = im.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BOX)   # descreen
    a = np.asarray(im, np.float32)
    w = a.shape[1]
    band = int(BAND_MM / 25.4 * DPI)
    lo = int(X_LO_MM / 25.4 * DPI)
    parity = "even" if page % 2 == 0 else "odd"
    sub = a[:, w - band:][:, ::-1] if parity == "even" else a[:, :band]
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    f = np.stack([sub.mean(2), (R - G) * CHROMA_W, (G - B) * CHROMA_W], -1)
    d = np.linalg.norm(np.diff(f, axis=1), axis=2)        # |colour diff| to the next pixel
    d[:, :lo] = 0
    if win is not None:                                   # restrict to hole +/- win px
        c, hw = win
        m = np.zeros(d.shape[1], bool); m[max(0, int(c - hw)):int(c + hw)] = True
        d[:, ~m] = 0
    x = d.argmax(1).astype(float)
    y = np.arange(len(x), dtype=float)
    return x, y, d[np.arange(len(x)), x.astype(int)], parity, im.size


def fit(x, y, how):
    yc = y.mean()
    if how == "lsq":
        c = np.polyfit(y - yc, x, 1)
        return float(c[1]), float(c[0]), len(x)
    if how == "theil":
        i = np.random.default_rng(0).choice(len(x), min(400, len(x)), replace=False)
        xs, ys = x[i], y[i]
        sl = [(xs[b] - xs[a]) / (ys[b] - ys[a])
              for a in range(len(xs)) for b in range(a + 1, len(xs)) if ys[b] != ys[a]]
        m = float(np.median(sl))
        return float(np.median(x - m * (y - yc))), m, len(x)
    best = (-1, 0.0, 0.0)
    for m in np.arange(-0.03, 0.03001, 0.0005):           # +-1.7 deg
        pos = x - m * (y - yc)
        med = np.median(pos)
        k = int((np.abs(pos - med) <= TOL_PX).sum())
        if k > best[0]:
            best = (k, float(np.median(pos[np.abs(pos - med) <= TOL_PX])), float(m))
    return best[1], best[2], best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--fit", default="hough", choices=["lsq", "theil", "hough"])
    ap.add_argument("--json", default=None)
    ap.add_argument("--win-mm", type=float, default=0.0,
                    help="restrict the search to hole-line +/- this many mm (0 = whole band)")
    a = ap.parse_args()

    clip = json.load(open(CLIP))
    out = {}
    print("%-5s %8s %8s %7s %6s   %s" % ("page", "x0(mm)", "hole(mm)", "d(mm)", "slope", "n_in"))
    for n in a.pages or range(1, 177):
        c0 = clip.get("%03d" % n)
        win = None
        if c0 and a.win_mm:
            hx = c0["column_x"] * DPI / SRC_DPI
            h_in = (c0["W"] * DPI / SRC_DPI - hx) if n % 2 == 0 else hx
            win = (h_in - int(X_LO_MM / 25.4 * DPI), a.win_mm / 25.4 * DPI)
        x, y, mag, parity, size = points(n, win)
        x0, m, n_in = fit(x, y, a.fit)
        mm = 25.4 / DPI
        c = clip.get("%03d" % n)
        hole = None
        if c:
            hx = c["column_x"] * DPI / SRC_DPI
            hole = (c["W"] * DPI / SRC_DPI - hx) if parity == "even" else hx
        out["%03d" % n] = dict(page=n, parity=parity, x0_px=x0, slope=m, n_in=n_in,
                               x0_mm=x0 * mm, hole_mm=None if hole is None else hole * mm)
        print("p%03d %8.2f %8s %7s %6.4f   %d"
              % (n, x0 * mm, "-" if hole is None else "%.2f" % (hole * mm),
                 "-" if hole is None else "%+.2f" % ((x0 - hole) * mm), m, n_in))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
