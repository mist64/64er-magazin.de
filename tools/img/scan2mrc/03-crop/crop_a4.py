#!/usr/bin/env python3
"""Apply the fitted A4 window: tmp/stack600 -> tmp/a4, one exact 210x297mm page each.

Every output is EXACTLY A4_W x A4_H at 600 dpi, so the pages are directly comparable and the
later stages need no per-page geometry. Where the window overhangs the rendered canvas the
output is TRANSPARENT, not black and not clamped: those pixels are unknown for the same reason
the matte's are, and the crop is not the place to invent them. Clamping the window instead
would silently shift the content and break the one property the logo anchor exists to give --
that the same content lands in the same place on every page.

Alpha is carried through unchanged. Inpainting is a later, separate decision.
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
OUTD = "/Users/mist/DNB/8609/tmp/a4"


def one(item):
    n, w, A4 = item
    A4_W, A4_H = A4
    src = np.asarray(Image.open(os.path.join(STACK, "%03d.png" % n)))
    H, W = src.shape[:2]
    out = np.zeros((A4_H, A4_W, 4), np.uint8)          # transparent = unknown
    x0, y0 = w["x0"], w["y0"]
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + A4_W, W), min(y0 + A4_H, H)
    off = 0
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        off = A4_W * A4_H - (sx1 - sx0) * (sy1 - sy0)
    os.makedirs(OUTD, exist_ok=True)
    Image.fromarray(out, "RGBA").save(os.path.join(OUTD, "%03d.png" % n))
    al = out[..., 3]
    return {"page": n, "src": w["src"], "size": [int(A4_W), int(A4_H)],
            "alpha_pct": round(100.0 * float((al == 0).mean()), 3),
            "offcanvas_pct": round(100.0 * off / (A4_W * A4_H), 3)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("pages", nargs="*", type=int)
    A = ap.parse_args()
    cfg = json.load(open(WINS))
    A4 = cfg["A4"]
    items = [(int(k), v, A4) for k, v in cfg["windows"].items()]
    if A.pages:
        items = [it for it in items if it[0] in A.pages]
    items.sort()
    res = []
    with Pool(A.jobs) as pool:
        for r in pool.imap_unordered(one, items):
            res.append(r)
    # MERGE, never replace: a partial re-run (e.g. only the spine pages) used to overwrite the
    # full 176-page record with its own handful, leaving a report that looked complete and was
    # not -- the same silent staleness that made crop_windows.json untrustworthy.
    RPT = "/Users/mist/DNB/8609/tmp/a4_report.json"
    prev = {}
    if os.path.exists(RPT):
        try:
            prev = {r["page"]: r for r in json.load(open(RPT))}
        except Exception:
            prev = {}
    prev.update({r["page"]: r for r in res})
    json.dump([prev[k] for k in sorted(prev)], open(RPT, "w"), indent=1)
    a = np.array([r["alpha_pct"] for r in res])
    o = np.array([r["offcanvas_pct"] for r in res])
    print("pages            : %d  (all %dx%d)" % (len(res), A4[0], A4[1]))
    print("alpha in crop %%  : p50 %.2f  p95 %.2f  max %.2f" % (
        np.percentile(a, 50), np.percentile(a, 95), a.max()))
    print("off-canvas %%     : p50 %.2f  p95 %.2f  max %.2f" % (
        np.percentile(o, 50), np.percentile(o, 95), o.max()))
    for lab in ("logo", "spine", "interpolated"):
        g = [r for r in res if r["src"] == lab]
        if g:
            v = np.array([r["alpha_pct"] for r in g])
            print("  %-13s n=%3d  alpha p50 %.2f  p95 %.2f  max %.2f" % (
                lab, len(g), np.percentile(v, 50), np.percentile(v, 95), v.max()))
    worst = sorted(res, key=lambda r: -r["alpha_pct"])[:8]
    print("worst pages      : " + "  ".join("p%03d:%.2f%%(%s)" % (
        r["page"], r["alpha_pct"], r["src"][:6]) for r in worst))
