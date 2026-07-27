#!/usr/bin/env python3
"""ISSUE-WIDE AUDIT of the bed matte, using a check INDEPENDENT of the detector's model.

verify_matte.py measures `leftover` over columns the detector itself calls `backing`. That
means it can only catch COVERAGE failures, never CLASSIFICATION failures: p001's bottom bed
strip was never classified as backing, so it contributed nothing to the metric and the page
passed while a black strip sat uncut in the render. This audit closes that hole.

For every page and edge it asks a question the detector does not get to define:

    beyond the cut, is there still a run of BACKING-COLOURED pixels connected to the border?

"Backing-coloured" is deliberately crude and fixed here (dark+neutral, or bright+saturated),
so a bug in _profile cannot hide from it. Anything it reports as residue is either real
uncut bed/insert, or a place where those colours legitimately belong to the page -- both are
worth looking at, which is the point.

Reports, per edge and over the issue:
    RESIDUE  deepest run of backing-coloured pixels left standing beyond the cut
    OVERCUT  cut depth minus the last backing-coloured pixel (page we spent)

Usage: audit_matte.py [--jobs N] [pages...]
"""
import os, sys, json, argparse

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_matte as B

Image.MAX_IMAGE_PIXELS = None
THUMB = "/Users/mist/DNB/8609/thumbs_600"
DPI = 600
EDGES = ("top", "bottom", "left", "right")

# Independent colour test -- NOT imported from bed_matte, deliberately.
DARK_L, DARK_S = 60, 15          # scanner bed / shadow
BRIGHT_L, BRIGHT_S = 150, 60     # cardboard insert
TOL = 3                          # px of slack before residue counts


def audit_page(page):
    im = Image.open(os.path.join(THUMB, "%03d.png" % page)).convert("RGB")
    a = np.asarray(im)[..., :3].astype(np.float32)
    H, W, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = a.max(2) - a.min(2)
    dtb, dlr = int(B.WIN_TB_FRAC * H), int(B.WIN_LR_FRAC * W)
    priors = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "priors.json")))
    rgba, pct, meta = B.bed_matte(im, DPI, priors=priors, page_no=page, return_meta=True)
    alpha = np.asarray(rgba)[:, :, 3]

    out = {}
    for edge in EDGES:
        L, S = B._orient(lum, sat, edge, dtb, dlr, H, W)
        A = B._orient1(alpha, edge, dtb, dlr, H, W)
        backish = ((L < DARK_L) & (S < DARK_S)) | ((L >= BRIGHT_L) & (S >= BRIGHT_S))
        cut = np.where((A == 0).any(1), (A == 0).argmin(1), 0)      # applied cut depth
        idx = np.arange(L.shape[1])[None, :]
        # backing-coloured, connected to the border through backing colour
        run_end = np.where(backish.any(1), backish.argmin(1), 0)
        residue = np.clip(run_end - cut - TOL, 0, None)
        overcut = np.clip(cut - run_end, 0, None)
        # depth at p95 and the FRACTION of lines affected. Not .max(): a single scanline
        # where a dark photo touches the edge is not a stripe, and reporting it made every
        # page look broken (p034's right edge: run_end p50=0, p95=3, max=833).
        out[edge] = (float(np.percentile(residue, 95)), float((residue > 0).mean()),
                     float(np.median(overcut)), meta.get(edge, {}).get("decision", "?"))
    return page, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    pages = a.pages or list(range(1, 177))

    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.jobs) as pool:
        res = dict(pool.map(audit_page, pages))

    print("%-7s %14s %12s %12s" % ("edge", "pages w/ stripe", "worst p95", "med_overcut"))
    for e in EDGES:
        # a STRIPE = residue on >5% of the lines of that edge
        bad = [p for p in res if res[p][e][1] > 0.05 and res[p][e][0] > TOL]
        r = np.array([res[p][e][0] for p in res])
        o = np.array([res[p][e][2] for p in res])
        print("%-7s %14d %12.0f %12.0f" % (e, len(bad), r.max(), np.median(o)))
        if bad:
            worst = sorted(bad, key=lambda p: -res[p][e][0])[:8]
            print("        worst: " + ", ".join("p%03d(%.0fpx on %.0f%%,%s)"
                  % (p, res[p][e][0], 100 * res[p][e][1], res[p][e][3]) for p in worst))
    json.dump({str(k): {e: v[e] for e in EDGES} for k, v in res.items()},
              open("/Users/mist/DNB/8609/tmp/audit_matte.json", "w"), indent=1)


if __name__ == "__main__":
    main()
