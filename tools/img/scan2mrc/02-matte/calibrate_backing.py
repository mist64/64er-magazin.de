#!/usr/bin/env python3
"""Derive WHAT THE BACKING IS for an issue, instead of hardcoding it.

bed_matte used to carry four colour thresholds and a list of which edges the cardboard insert
lies on. Every one of them was a fact about THIS scanner session written into the code, and each
was wrong somewhere: p044's ochre ad matched "yellowish" on the left, p001's teal cover nearly
matched it everywhere, and a per-page ink darker than the fixed bed luma could never be told
from bed. None of it needs to be assumed -- it is all visible in the scans.

THE ONE IDEA. Backing is the material that lies OUTSIDE the sheet. So it is common at the image
border and gone a few centimetres in, while paper and ink are the opposite. That is a measurable
property of a colour, and it needs no name:

    a colour is a BACKING MATERIAL of an edge  iff
        it covers the border ring on a large fraction of the issue's pages, AND
        its coverage COLLAPSES between the border and the page interior

Measured over 8609 (176 pages), mean coverage by depth:

    edge    cluster        0-3px    30-60    150-200   600-700
    top     dark neutral   0.862    0.031    0.033     0.160     -> backing (bed)
    bottom  yellow         0.993    0.991    0.033     0.000     -> backing (insert)
    left    dark neutral   0.154    0.025    0.015     0.134     -> backing, fewer pages
    any     cream          0.10     0.88     0.89      0.68      -> RISES: this is the paper

The insert coming out as bottom-only, on 176/176 pages, is the measurement that used to be the
hardcoded INSERT_EDGES=("bottom",). An issue with a blue insert at the top calibrates itself.

Output: backing_profile.json -- per edge, the backing clusters (centre, radius, prevalence).
bed_matte then refines each cluster on the page in front of it, which is what separates the bed
from a page's own black ink: they are different colours in the same scan, even where the fixed
threshold saw both as "dark".
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import sys, json, argparse, numpy as np
from collections import Counter
from multiprocessing import Pool
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------------------------------
# CONSTANTS  (spatial values @600dpi)
# ---------------------------------------------------------------------------------------------------
RING_600      = 3      # depth of the border ring that is sampled as "outside" material
INNER_600     = ((30, 60), (150, 200), (400, 500), (600, 700))
                       # SEVERAL interior bands, and the collapse is measured against the band
                       # where the colour is RAREST. One band cannot do it: a deep bed wedge
                       # (p044 top, ~230px) keeps the bed common at 150-200, while at 600-700 the
                       # page's own ink puts dark pixels back (0.134) and hides the collapse
                       # entirely. A material that stops at the sheet edge vanishes SOMEWHERE
                       # inboard; paper is ~0.9 in every band and so never does.
QUANT         = 16     # colour quantisation for the mode search (16 bins per channel)
MIN_BIN_FRAC  = 0.02   # a bin counts for a page-edge if it holds this much of the ring
MIN_PAGES     = 0.15   # ... and is a candidate material if it does so on this fraction of pages.
                       # Low on purpose: the sides only show bed on the ~39% of pages that did
                       # not lie straight on the platen, and those still must be cut.
COLLAPSE_MIN  = 3.0    # border coverage / interior coverage. Paper RISES (ratio ~0.1); the bed
                       # and the insert fall by 5x and 3000x. Anything in between is not a
                       # material that stops at the sheet edge.
MERGE_TOL     = 40     # bins within this max-channel distance are one material
RADIUS_MIN    = 28     # a cluster's radius is its measured spread, but never tighter than this
                       # (quantisation alone is +-8 per channel)
RADIUS_PCTL   = 90     # radius = this percentile of member-pixel distance from the centre


def _band(a, H, W, edge, lo, hi):
    if edge == "top":    return a[lo:hi]
    if edge == "bottom": return a[H - hi:H - lo]
    if edge == "left":   return a[:, lo:hi]
    if edge == "right":  return a[:, W - hi:W - lo]


EDGES = ("top", "bottom", "left", "right")


def _page(args):
    path, dpi = args
    ring = max(2, round(RING_600 * dpi / 600))
    a = np.asarray(Image.open(path).convert("RGB"))
    H, W, _ = a.shape
    out = {}
    for e in EDGES:
        b = _band(a, H, W, e, 0, ring).reshape(-1, 3)
        q = (b // QUANT).astype(np.int32)
        key = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
        cnt = Counter(key.tolist())
        hits = {int(k): v / key.size for k, v in cnt.items() if v / key.size >= MIN_BIN_FRAC}
        # border pixels are kept as PIXELS too, so border and interior coverage are measured the
        # same way. Comparing a sum of per-page bin prevalences (which reached 5.085) against a
        # pixel fraction made the cream paper look like it collapsed 7x on the sides.
        def _sub(band, cap=60000):
            return band[:: max(1, band.shape[0] // cap)]
        inner = [_sub(_band(a, H, W, e, round(lo * dpi / 600), round(hi * dpi / 600))
                      .reshape(-1, 3)) for lo, hi in INNER_600]
        out[e] = (hits, _sub(b), inner)
    return out


def _unkey(k):
    return np.array([(k // 1024) * QUANT + QUANT // 2,
                     ((k // 32) % 32) * QUANT + QUANT // 2,
                     (k % 32) * QUANT + QUANT // 2], float)


def calibrate(paths, dpi=600, jobs=4, verbose=True):
    with Pool(jobs) as p:
        res = p.map(_page, [(x, dpi) for x in paths])
    npages = len(res)
    profile = {}
    for e in EDGES:
        pages_with = Counter()
        for r in res:
            for k in r[e][0]:
                pages_with[k] += 1
        border_px = np.concatenate([r[e][1] for r in res], 0)
        inner_px = [np.concatenate([r[e][2][i] for r in res], 0) for i in range(len(INNER_600))]

        # candidate bins -> merged clusters, most prevalent first
        cands = [(k, v / npages) for k, v in pages_with.items() if v / npages >= MIN_PAGES]
        cands.sort(key=lambda t: -t[1])
        clusters = []
        for k, prev in cands:
            c = _unkey(k)
            for cl in clusters:
                if np.abs(np.asarray(cl["centre"]) - c).max() <= MERGE_TOL:
                    cl["members"].append((c, prev))
                    break
            else:
                clusters.append({"centre": list(c), "members": [(c, prev)]})

        kept = []
        for cl in clusters:
            cs = np.array([m[0] for m in cl["members"]])
            ws = np.array([m[1] for m in cl["members"]])
            centre = (cs * ws[:, None]).sum(0) / ws.sum()
            prev = float(max(ws))
            # border coverage vs interior coverage of the SAME colour, both as pixel fractions
            rad0 = max(RADIUS_MIN, MERGE_TOL)
            border_cov = float((np.abs(border_px - centre).max(1) <= rad0).mean())
            covs = [float((np.abs(px - centre).max(1) <= rad0).mean()) for px in inner_px]
            inner_cov = float(min(covs))
            collapse = (border_cov + 1e-6) / (inner_cov + 1e-6)
            rec = dict(centre=[round(float(x), 1) for x in centre],
                       prevalence=round(prev, 3),
                       border_cov=round(border_cov, 4),
                       inner_cov=round(inner_cov, 4),
                       collapse=round(collapse, 1),
                       radius=float(rad0),
                       backing=bool(collapse >= COLLAPSE_MIN))
            kept.append(rec)
        profile[e] = kept
        if verbose:
            print("%-7s" % e)
            for r in kept:
                print("   RGB(%5.1f,%5.1f,%5.1f)  on %3.0f%% of pages  border %.3f  inner %.3f"
                      "  collapse %7.1fx  -> %s"
                      % (*r["centre"], 100 * r["prevalence"], r["border_cov"], r["inner_cov"],
                         r["collapse"], "BACKING" if r["backing"] else "page"))
    return profile


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("-o", "--out", default="backing_profile.json")
    A = ap.parse_args()
    prof = calibrate(A.images, A.dpi, A.jobs)
    json.dump({"dpi": A.dpi, "n_pages": len(A.images), "edges": prof},
              open(A.out, "w"), indent=1)
    print("\nwrote %s" % A.out)
