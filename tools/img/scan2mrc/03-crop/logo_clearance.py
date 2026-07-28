#!/usr/bin/env python3
"""How much page is there around the logo, before the alpha starts?

The A4 crop is anchored on the "64'er" wordmark, so the question that decides the window is:
from that anchor, how far can we go in each direction before hitting UNKNOWN pixels (scanner
bed, neighbour page, clip holes, deskew wedge)?

"How far" has three defensible answers and they disagree, so all three are measured. They are
not competing estimates of one number -- they answer different questions:

  RAY   straight along the anchor's own row/column to the first transparent pixel.
        Simple and exact, but a single clip hole on that row truncates it, so it UNDERSTATES
        the usable area. Its gap to BAND is a direct measure of how much local damage there is.

  RECT  the largest alpha-free rectangle around the anchor. Answers "what window fits with no
        alpha at all", so one bad corner shrinks it -- which is the honest answer to that
        question, but a pessimistic answer to "what window is usable".
        NOTE "largest" is realised as water-filling: all four sides grow together in steps, and
        a side stops when the strip it would add contains alpha. Maximum-AREA is ill-posed here
        (area trades width against height arbitrarily) and O(H^2) to compute; water-filling is
        deterministic, order-independent and answers the same practical question.

  BAND  the distance at which alpha coverage ACROSS the perpendicular extent exceeds a
        threshold. Robust to holes and nicks, and it matches how a crop actually fails: a
        sliver of alpha in a corner is inpaintable, a full band across the page is not.

All three are measured on the DESKEWED renders (tmp/stack600), which is the frame the crop
window lives in -- logo_detect.py reports RAW-frame coordinates (its docstring claims otherwise),
so the anchor is transformed through the same rotation the render used, and that transform is
verified by landing it on the wordmark (tmp/frame_check.png).

Pages with no detected logo are EXCLUDED, not interpolated: their anchor carries interpolation
error and pooling it would corrupt the very percentiles the window is chosen from.
"""
import os, sys, json, re, argparse
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from multiprocessing import Pool
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------------------------
STACK   = "/Users/mist/DNB/8609/tmp/stack600"     # the LATEST alpha render
LOGOS   = "/Users/mist/DNB/8609/tmp/logo_positions.json"
SKEWF   = "/Users/mist/DNB/8609/tmp/skew_all.txt"
OUT     = "/Users/mist/DNB/8609/tmp/logo_clearance.json"
DPI     = 600
MASTER_OVER_600 = 4        # logo_detect reports 2400-dpi master px
BAND_THRESH = 0.01         # BAND: alpha fraction across the perpendicular extent that counts
                           # as "a band, not a sliver". 1% of 7200 rows = 72 rows.
RECT_STEP  = 4             # RECT: water-filling step in px (0.17mm); finer costs time, coarser
                           # quantises the answer
DIRS = ("left", "right", "top", "bottom")


def load_skew():
    ang = {}
    for ln in open(SKEWF):
        m = re.search(r"/(\d+)\.png:\s*([+-]?\d+\.\d+)\s*deg", ln)
        if m:
            ang[int(m.group(1))] = float(m.group(2))
    return ang


def fwd(pt, ang, src_wh, dst_wh):
    """Map a raw-frame point through Image.rotate(ang, expand=True) -- verified visually."""
    x, y = pt
    W, H = src_wh
    W2, H2 = dst_wh
    t = np.deg2rad(ang)
    dx, dy = x - W / 2.0, y - H / 2.0
    return (np.cos(t) * dx + np.sin(t) * dy + W2 / 2.0,
            -np.sin(t) * dx + np.cos(t) * dy + H2 / 2.0)


def clearance_ray(opaque, ax, ay):
    """First transparent pixel along the anchor's own row / column."""
    row = opaque[ay]
    col = opaque[:, ax]
    def run(v, i, back):
        seg = v[:i][::-1] if back else v[i + 1:]
        bad = np.flatnonzero(~seg)
        return int(bad[0]) if bad.size else int(seg.size)
    return {"left": run(row, ax, True), "right": run(row, ax, False),
            "top": run(col, ay, True), "bottom": run(col, ay, False)}


def clearance_rect(opaque, ax, ay):
    """Water-filling: grow all four sides together; a side stops when its next strip has alpha."""
    H, W = opaque.shape
    ii = np.cumsum(np.cumsum((~opaque).astype(np.int32), 0), 1)     # integral of TRANSPARENT

    def bad(y0, y1, x0, x1):
        """any transparent pixel in [y0,y1) x [x0,x1) ?"""
        y0 = max(y0, 0); x0 = max(x0, 0); y1 = min(y1, H); x1 = min(x1, W)
        if y1 <= y0 or x1 <= x0:
            return True
        s = ii[y1 - 1, x1 - 1]
        if y0:
            s -= ii[y0 - 1, x1 - 1]
        if x0:
            s -= ii[y1 - 1, x0 - 1]
        if y0 and x0:
            s += ii[y0 - 1, x0 - 1]
        return s > 0

    d = {k: 0 for k in DIRS}
    alive = {k: True for k in DIRS}
    if not opaque[ay, ax]:
        return d                                  # anchor itself is transparent
    while any(alive.values()):
        for k in DIRS:
            if not alive[k]:
                continue
            n = d[k] + RECT_STEP
            y0, y1 = ay - d["top"], ay + d["bottom"] + 1
            x0, x1 = ax - d["left"], ax + d["right"] + 1
            if k == "left":
                strip = (y0, y1, ax - n, x0)
            elif k == "right":
                strip = (y0, y1, x1, ax + n + 1)
            elif k == "top":
                strip = (ay - n, y0, x0, x1)
            else:
                strip = (y1, ay + n + 1, x0, x1)
            if bad(*strip):
                alive[k] = False
            else:
                d[k] = n
    return d


def clearance_band(opaque, ax, ay, thresh=BAND_THRESH, iters=3):
    """Distance at which alpha coverage across the perpendicular extent exceeds `thresh`.

    The perpendicular extent is the CURRENT BOX, not the whole canvas, and that is not a detail:
    measured across the full canvas every column already contains the top bed cut and the bottom
    insert cut (~2.5% of its rows), so every column exceeds any sane threshold and the measure
    collapses to 0 in all four directions. The extent has to be the region we would actually
    keep -- which depends on the answer, so it is iterated from the RAY box. Converges in 2-3
    passes because each pass can only shrink the box.
    """
    H, W = opaque.shape
    tr = ~opaque
    box = clearance_ray(opaque, ax, ay)
    for _ in range(iters):
        y0, y1 = max(ay - box["top"], 0), min(ay + box["bottom"] + 1, H)
        x0, x1 = max(ax - box["left"], 0), min(ax + box["right"] + 1, W)
        if y1 <= y0 or x1 <= x0:
            return {k: 0 for k in DIRS}
        colfrac = tr[y0:y1, :].mean(0)      # per column, over the box's rows only
        rowfrac = tr[:, x0:x1].mean(1)      # per row, over the box's columns only

        def run(frac, i, back):
            seg = frac[:i][::-1] if back else frac[i + 1:]
            bad = np.flatnonzero(seg > thresh)
            return int(bad[0]) if bad.size else int(seg.size)

        new = {"left": run(colfrac, ax, True), "right": run(colfrac, ax, False),
               "top": run(rowfrac, ay, True), "bottom": run(rowfrac, ay, False)}
        if new == box:
            break
        box = new
    return box


def one(rec):
    n = rec["page"]
    im = Image.open(os.path.join(STACK, "%03d.png" % n))
    al = np.asarray(im)[..., 3]
    opaque = al > 0
    ang = _SKEW.get(n, 0.0)
    raw_wh = (rec["page_w_600"], rec["page_h_600"])
    ax, ay = fwd((rec["anchor_x"] / MASTER_OVER_600, rec["anchor_y"] / MASTER_OVER_600),
                 ang, raw_wh, im.size)
    ax, ay = int(round(ax)), int(round(ay))
    H, W = opaque.shape
    if not (0 <= ax < W and 0 <= ay < H):
        return {"page": n, "ok": False, "why": "anchor outside canvas"}
    return {"page": n, "ok": True, "parity": "even" if n % 2 == 0 else "odd",
            "anchor": [ax, ay], "size": list(im.size), "skew": ang,
            "ray": clearance_ray(opaque, ax, ay),
            "rect": clearance_rect(opaque, ax, ay),
            "band": clearance_band(opaque, ax, ay)}


_SKEW = {}


def _init():
    global _SKEW
    _SKEW = load_skew()


def mm(px):
    return px / DPI * 25.4


def report(res):
    ok = [r for r in res if r.get("ok")]
    print("pages with a detected logo : %d" % len(ok))
    for meas in ("ray", "rect", "band"):
        print("\n%s  (px @600dpi / mm)" % meas.upper())
        print("  %-6s %-6s %8s %8s %8s %8s" % ("parity", "dir", "min", "p5", "p50", "p95"))
        for par in ("even", "odd"):
            g = [r for r in ok if r["parity"] == par]
            if not g:
                continue
            for d in DIRS:
                v = np.array([r[meas][d] for r in g], float)
                print("  %-6s %-6s %8s %8s %8s %8s" % (
                    par, d,
                    "%.0f/%.1f" % (v.min(), mm(v.min())),
                    "%.0f/%.1f" % (np.percentile(v, 5), mm(np.percentile(v, 5))),
                    "%.0f/%.1f" % (np.percentile(v, 50), mm(np.percentile(v, 50))),
                    "%.0f/%.1f" % (np.percentile(v, 95), mm(np.percentile(v, 95)))))
    print("\nHOW MUCH THE MEASURES DISAGREE (median over pages, px)")
    print("  %-6s %10s %10s %10s" % ("dir", "band-ray", "band-rect", "ray-rect"))
    for d in DIRS:
        a = np.array([r["ray"][d] for r in ok], float)
        b = np.array([r["rect"][d] for r in ok], float)
        c = np.array([r["band"][d] for r in ok], float)
        print("  %-6s %10.0f %10.0f %10.0f" % (d, np.median(c - a), np.median(c - b),
                                               np.median(a - b)))
    print("\nTIGHTEST PAGES (smallest BAND clearance, the measure a crop actually fails on)")
    for d in DIRS:
        g = sorted(ok, key=lambda r: r["band"][d])[:5]
        print("  %-6s %s" % (d, "  ".join("p%03d:%d" % (r["page"], r["band"][d]) for r in g)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("pages", nargs="*", type=int)
    A = ap.parse_args()
    logos = json.load(open(LOGOS))
    recs = [r for r in logos if r["found"]]
    if A.pages:
        recs = [r for r in recs if r["page"] in A.pages]
    skipped = [r["page"] for r in logos if not r["found"]]
    with Pool(A.jobs, initializer=_init) as pool:
        res = pool.map(one, recs)
    json.dump({"clearance": res, "no_logo": skipped}, open(OUT, "w"), indent=1)
    report(res)
    print("\nEXCLUDED (no logo detected): %d pages" % len(skipped))
    print("  " + " ".join("p%03d" % p for p in skipped))
    print("\nwrote %s" % OUT)
