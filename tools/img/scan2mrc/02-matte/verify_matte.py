#!/usr/bin/env python3
"""REGRESSION HARNESS for bed_matte. Run this after EVERY change to it.

The rule this enforces (from the user): verify everything you implement -- and not only where
the symptom was. Two bugs in one session came from checking a fix only on the pages that had
the reported defect:

  * the bow quadratic fixed the bottom-edge residue and, on a CLEAN edge with almost no
    backing, was fitted to ~50 scattered columns, extrapolated over 7188 rows and cut 35mm
    of real page (p015 right).
  * its own guard measured the bow over the FITTED points instead of the range the curve was
    APPLIED to, so it read "safe" precisely while the extrapolation ran away.

So every case below is checked, every run:

  MUST_CUT    an edge that carries bed/insert -- leaving a stripe is a FAIL (rule 1)
  MUST_KEEP   an edge that is clean page -- cutting it is a FAIL (rule 2, and it destroys
              content that no later stage can recover)
  BUDGET      how much page we spend on the edges we do cut

Usage:  verify_matte.py [--jobs N]
Exit code is non-zero if any expectation fails, so it can gate a commit.
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_matte as B

Image.MAX_IMAGE_PIXELS = None
THUMB = "/Users/mist/DNB/8609/thumbs_600"
DPI = 600

# (page, edge, expectation).  "cut" = must remove the backing there;
# "keep" = must not cut, that edge is page or clean paper to the border.
CASES = [
    # --- edges that genuinely carry backing (the reported symptoms) --------------
    (4,  "bottom", "cut"),  (5,  "bottom", "cut"),  (9,  "bottom", "cut"),
    (11, "bottom", "cut"),  (13, "bottom", "cut"),  (15, "bottom", "cut"),
    (1,  "top",    "cut"),  (3,  "top",    "cut"),
    (30, "top",    "cut"),  (50, "top",    "cut"),
    (89, "right",  "cut"),                      # wide black bar, centrefold
    # --- edges that are CLEAN and must be left alone (the blind spot) ------------
    (15, "right",  "keep"),                     # 35mm of paper was destroyed here
    (15, "left",   "keep"),
    (5,  "left",   "keep"),  (5,  "right",  "keep"),
    (47, "left",   "keep"),
    (30, "right",  "keep"),
]
MAX_LEFTOVER_PX = 3      # rule 1: backing left standing, per edge
MAX_KEEP_CUT_PX = 20     # rule 2: a "keep" edge may lose at most this (deskew slack)


def page_edges(args):
    """Measure what PRODUCTION actually does to one page, per edge.

    NB two mistakes this function made in its first version, both of which made it report
    failures the pipeline does not have (and would have masked real ones):
      * it called _brute_cut directly, bypassing bed_matte's CLEAN(no backing) gate, so it
        scored raw candidate cuts that are never applied;
      * it measured leftover backing over ALL columns, so a black CONTENT block touching the
        edge (p003's, p089's) counted as "backing left standing" -- 567px and 746px of it.
    So: the applied cut comes from the real alpha, and leftover is measured over the BACKING
    columns only.
    """
    page, edges = args
    im = Image.open(os.path.join(THUMB, "%03d.png" % page)).convert("RGB")
    priors = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "priors.json")))
    rgba, pct, meta = B.bed_matte(im, DPI, priors=priors, page_no=page, return_meta=True)
    alpha = np.asarray(rgba)[:, :, 3]

    a_ = np.asarray(im)[..., :3].astype(np.float32)
    H, W, _ = a_.shape
    lum = a_ @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = a_.max(2) - a_.min(2)
    dtb, dlr = int(B.WIN_TB_FRAC * H), int(B.WIN_LR_FRAC * W)

    A0 = (alpha == 0)
    applied = {
        "left":   A0[:, ::-1][:, ::-1],   # placeholder, replaced below
    }
    def lead(M):                          # applied cut depth per line, from the real alpha
        full = M.all(1)
        r = np.where(M.any(1), M.argmin(1), 0)
        return np.where(full, M.shape[1], r)

    depth = {"left": lead(A0), "right": lead(A0[:, ::-1]),
             "top": lead(A0.T), "bottom": lead(A0.T[:, ::-1])}

    out = {}
    for edge in edges:
        L, S = B._orient(lum, sat, edge, dtb, dlr, H, W)
        Sc = B.screen_energy(L, DPI)
        d, backing, nopage, sf = B._profile(L, S, DPI, Sc)
        cut = depth[edge].astype(float)
        # Leftover only over the CORE backing, using the detector's OWN outlier fence.
        # Without it, columns that are photometrically identical to bed but are actually
        # CONTENT (p003's black block: L31.3/sat2.0 vs bed L31.8/sat2.0; p089's schematic)
        # count as "backing left standing" -- 567px and 744px of it -- and the harness
        # demands the detector cut real page. The detector excludes them by a MAD fence and
        # is right to; the check has to agree on what it is measuring.
        lo = 0.0
        if backing.any():
            db = d[backing]
            med = np.median(db); mad = np.median(np.abs(db - med))
            core = backing & (d <= med + max(B.OUTLIER_K * 1.4826 * mad, B.FENCE_MIN_600))
            if core.any():
                lo = float(np.clip(d - cut, 0, None)[core].max())
        out[edge] = (lo, float(np.median(cut)), float(backing.mean()),
                     meta.get(edge, {}).get("decision", "?"))
    return page, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4,
                    help="4, deliberately. Each worker holds a 37MP page as float32 plus "
                         "derived copies; 12-16 workers exhausted 128GB and took the machine "
                         "down. Measure RSS before raising this.")
    a = ap.parse_args()

    by_page = {}
    for page, edge, want in CASES:
        by_page.setdefault(page, set()).add(edge)
    work = [(p, sorted(e)) for p, e in by_page.items()]

    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.jobs) as pool:
        res = dict(pool.map(page_edges, work))

    fails = []
    print("%-5s %-7s %-5s %9s %9s  %s" % ("page", "edge", "want", "leftover", "cut_px", "verdict"))
    for page, edge, want in CASES:
        leftover, cut_px, bfrac, dec = res[page][edge]
        if want == "cut":
            ok = leftover <= MAX_LEFTOVER_PX
            why = "leaves %.0fpx of backing (%s)" % (leftover, dec)
        else:
            ok = cut_px <= MAX_KEEP_CUT_PX
            why = "cuts %.0fpx of clean page (backing %.3f, %s)" % (cut_px, bfrac, dec)
        print("%-5d %-7s %-5s %9.1f %9.1f  %s" % (page, edge, want, leftover, cut_px,
                                                  "ok" if ok else "FAIL: " + why))
        sys.stdout.flush()
        if not ok:
            fails.append((page, edge, want, why))
    print()
    if fails:
        print("FAILED %d of %d" % (len(fails), len(CASES)))
        for f in fails:
            print("   p%03d %s (want %s): %s" % f)
        sys.exit(1)
    print("all %d expectations met" % len(CASES))


if __name__ == "__main__":
    main()
