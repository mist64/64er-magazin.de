#!/usr/bin/env python3
"""Place the A4 crop window relative to the logo anchor, per parity.

The window is RIGID relative to the anchor: one (S, B) pair per parity, not per page, because
the point of anchoring on the logo is that the same content lands in the same place on every
page. S = anchor's distance from the window's LEFT edge, B = its distance from the TOP edge.

OBJECTIVE: minimise alpha inside the window. Not "avoid alpha" -- an A4 window fits alpha-free
on 0 of 129 pages (the page simply is not 210x297mm of known pixels once bed, neighbour, clip
holes and the deskew wedge are removed), so the question is only how little has to be inpainted
and where. Reported as a distribution, not a single number, because the tail is what hurts.

Searched on the LATEST render (tmp/stack600). Pages without a detected logo are excluded from
the FIT for the same reason they were excluded from the clearance stats -- an interpolated
anchor would drag the optimum toward its own error -- but they do get a window afterwards, from
an anchor interpolated across their same-parity neighbours, and it is marked as inferred.
"""
import os, sys, json, re, argparse
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from multiprocessing import Pool
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

STACK = "/Users/mist/DNB/8609/tmp/stack600"
CLEAR = "/Users/mist/DNB/8609/tmp/logo_clearance.json"
OUT = "/Users/mist/DNB/8609/tmp/crop_windows_v2.json"
DPI = 600
A4_W = int(round(210.0 / 25.4 * DPI))      # 4961
A4_H = int(round(297.0 / 25.4 * DPI))      # 7016
DS = 8                                     # downsample for the search (8px = 0.34mm)
S_RANGE = (0, A4_W, 8)                     # anchor-to-left-edge, px @600dpi. MUST span the full
                                           # page width: on odd pages the anchor sits near the
                                           # RIGHT edge, so S is ~4450, and a range capped at 900
                                           # pinned the optimum to its own boundary and reported
                                           # 71% alpha -- a window mostly off the page.
B_RANGE = (6700, 7010, 8)                  # anchor-to-top-edge


def _load_one(n):
    a = np.asarray(Image.open(os.path.join(STACK, "%03d.png" % n)))[..., 3]
    tr = (a == 0)
    H, W = tr.shape
    h, w = H // DS, W // DS
    ds = tr[:h * DS, :w * DS].reshape(h, DS, w, DS).any((1, 3))
    # summed-area table so any window costs 4 lookups instead of a slice-and-sum: the search is
    # ~24k offset pairs per page and the slicing version took minutes for a range 7x smaller
    ii = np.cumsum(np.cumsum(ds.astype(np.int32), 0), 1)
    return n, np.pad(ii, ((1, 0), (1, 0))), ds.shape


def load_masks(pages, jobs=4):
    """Downsampled TRANSPARENT masks as integral images; coarse pixel = alpha if ANY source is."""
    with Pool(jobs) as pool:
        return {n: (ii, shp) for n, ii, shp in pool.map(_load_one, pages)}


def alpha_in(entry, ax, ay, S, B):
    """Transparent COARSE pixels inside the A4 window; area falling OFF-canvas counts too."""
    ii, (h, w) = entry
    x0 = int(round((ax - S) / DS)); y0 = int(round((ay - B) / DS))
    x1 = x0 + A4_W // DS;           y1 = y0 + A4_H // DS
    cx0, cy0 = max(x0, 0), max(y0, 0)
    cx1, cy1 = min(x1, w), min(y1, h)
    if cx1 <= cx0 or cy1 <= cy0:
        return (A4_W // DS) * (A4_H // DS)
    inside = int(ii[cy1, cx1] - ii[cy0, cx1] - ii[cy1, cx0] + ii[cy0, cx0])
    off = (x1 - x0) * (y1 - y0) - (cx1 - cx0) * (cy1 - cy0)   # outside the canvas = unknown too
    return inside + off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    A = ap.parse_args()
    clr = json.load(open(CLEAR))
    recs = [r for r in clr["clearance"] if r.get("ok")]
    pages = [r["page"] for r in recs]
    anchors = {r["page"]: r["anchor"] for r in recs}
    sizes = {r["page"]: r["size"] for r in recs}
    print("loading %d masks ..." % len(pages))
    masks = load_masks(pages, A.jobs)
    total = (A4_W // DS) * (A4_H // DS)

    best = {}
    for par in ("even", "odd"):
        g = [n for n in pages if (n % 2 == 0) == (par == "even")]
        bs, bb, bv = None, None, None
        for S in range(*S_RANGE):
            for B in range(*B_RANGE):
                v = np.mean([alpha_in(masks[n], *anchors[n], S, B) for n in g])
                if bv is None or v < bv:
                    bs, bb, bv = S, B, v
        best[par] = (bs, bb)
        frac = 100.0 * bv / total
        print("%-5s n=%3d  S=%4d  B=%4d   mean alpha in window %.3f%%" % (par, len(g), bs, bb, frac))

    # distribution at the chosen offsets
    res = {}
    for par in ("even", "odd"):
        S, B = best[par]
        g = [n for n in pages if (n % 2 == 0) == (par == "even")]
        v = np.array([100.0 * alpha_in(masks[n], *anchors[n], S, B) / total for n in g])
        print("%-5s alpha%% p50 %.3f  p95 %.3f  max %.3f   (worst: %s)" % (
            par, np.percentile(v, 50), np.percentile(v, 95), v.max(),
            " ".join("p%03d:%.2f%%" % (g[i], v[i]) for i in np.argsort(v)[-4:][::-1])))
        for n, x in zip(g, v):
            res[n] = round(float(x), 4)

    # interpolate an anchor for the no-logo pages from same-parity neighbours
    windows = {}
    for n in pages:
        S, B = best["even" if n % 2 == 0 else "odd"]
        ax, ay = anchors[n]
        windows[n] = {"x0": int(ax - S), "y0": int(ay - B), "w": A4_W, "h": A4_H,
                      "anchor": [ax, ay], "src": "logo", "alpha_pct": res[n]}
    for n in clr["no_logo"]:
        same = sorted(p for p in pages if p % 2 == n % 2)
        if not same:
            continue
        lo = [p for p in same if p < n][-2:]
        hi = [p for p in same if p > n][:2]
        near = lo + hi
        ax = float(np.mean([anchors[p][0] for p in near]))
        ay = float(np.mean([anchors[p][1] for p in near]))
        S, B = best["even" if n % 2 == 0 else "odd"]
        windows[n] = {"x0": int(ax - S), "y0": int(ay - B), "w": A4_W, "h": A4_H,
                      "anchor": [int(ax), int(ay)], "src": "interpolated", "alpha_pct": None,
                      "from": near}
    json.dump({"A4": [A4_W, A4_H], "offsets": {k: list(v) for k, v in best.items()},
               "windows": {str(k): v for k, v in sorted(windows.items())}},
              open(OUT, "w"), indent=1)
    print("\nwrote %s  (%d windows, %d interpolated)" % (
        OUT, len(windows), sum(1 for w in windows.values() if w["src"] == "interpolated")))


if __name__ == "__main__":
    main()
