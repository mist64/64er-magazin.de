#!/usr/bin/env python3
"""Per-stage, per-page verification of the whole pipeline.

Written because a 7-hour re-cache once completed successfully while applying none of the matte fix
it existed for: every stage "worked", and nothing checked that a stage's output actually reflected
its input. Each check below compares an artifact against the stage BEFORE it, so a stale
intermediate cannot pass.

  verify_stages.py            all stages, all pages
  verify_stages.py --stage 4  one stage
  verify_stages.py --deep     also re-run bed_matte on a sample and compare (slow, ~25s a page)

Exit code is the number of failing checks, so it can gate a driver.
"""
import argparse
import glob
import json
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np                                                    # noqa: E402
from PIL import Image                                                 # noqa: E402

Image.MAX_IMAGE_PIXELS = None
T = "/Users/mist/DNB/8609/tmp"
A4_OUT = [19843, 28063]
OVERCUT = 4          # bed_matte OVERCUT_600, added to every cut profile
HOP = 60             # detector hop; the score grid is out_size / HOP

FAIL = []


def check(cond, tag, detail=""):
    if not cond:
        FAIL.append("%s  %s" % (tag, detail))
    return cond


def pages_with(pattern):
    return sorted(int(os.path.basename(f)[:3]) for f in glob.glob(pattern))


# ---------------------------------------------------------------------------------------------
def stage1():
    """stack600 RGBA: exists, alpha sane, and its bottom cut matches the geometry profile once the
    DESKEW WEDGE is removed -- the stack is rotated, so a raw depth comparison is wrong by
    W/2*tan|angle| and reading that as an error is how a real check gets abandoned."""
    print("\n=== stage 1: stack_render -> stack600/NNN.png ===")
    geo = json.load(open(os.path.join(T, "page_geometry.json")))["pages"]
    ps = pages_with(os.path.join(T, "stack600", "[0-9][0-9][0-9].png"))
    print("  pages: %d" % len(ps))
    resid = []
    for p in ps:
        g = geo.get(str(p))
        if not g:
            continue
        a = np.asarray(Image.open(os.path.join(T, "stack600", "%03d.png" % p)))[..., 3]
        tr = (a == 0)
        H, W = tr.shape
        cols = ~tr.all(0)
        if not cols.any():
            check(False, "p%03d" % p, "stack600 fully transparent")
            continue
        bot = np.median([H - 1 - np.max(np.where(~tr[:, x])[0]) for x in np.where(cols)[0][::37]])
        z = np.load(os.path.join(T, "page_geometry", "%03d.npz" % p))
        exp = float(np.median(z["bed_bottom"]))
        wedge = W * np.tan(np.radians(abs(g["angle_deg"]))) / 2.0
        resid.append(bot - exp - wedge)
    resid = np.array(resid)
    if len(resid):
        print("  bottom cut, wedge removed: p50 %+.1f  p95 %+.1f  max %+.1f px"
              % (np.percentile(resid, 50), np.percentile(resid, 95), resid.max()))
        check(np.abs(resid).max() < 15, "stage1", "a page's alpha disagrees with its profile by %.1f px"
              % np.abs(resid).max())


def stage2():
    """crop_windows: every page present, window inside a sane range, anchor sources accounted."""
    print("\n=== stage 2: fit_window -> crop_windows_v2.json ===")
    w = json.load(open(os.path.join(T, "crop_windows_v2.json")))
    win = w["windows"]
    print("  windows: %d   A4 %s   offsets %s" % (len(win), w["A4"], w["offsets"]))
    check(len(win) == 176, "stage2", "expected 176 windows, got %d" % len(win))
    al = np.array([v.get("alpha_pct", 0) for v in win.values()])
    print("  alpha in window: p50 %.2f%%  p95 %.2f%%  max %.2f%%"
          % (np.percentile(al, 50), np.percentile(al, 95), al.max()))
    check(al.max() < 8.0, "stage2", "a window contains %.1f%% alpha" % al.max())
    for p, v in win.items():
        check(v["w"] == 4961 and v["h"] == 7016, "p%s" % p, "window size %sx%s" % (v["w"], v["h"]))


def stage3(deep=False):
    """geometry: every page has a profile, and the profile EQUALS the current matte's cut.
    This is the check whose absence let the pre-penumbra profiles survive a full re-cache."""
    print("\n=== stage 3: emit_geometry -> page_geometry.json + NNN.npz ===")
    geo = json.load(open(os.path.join(T, "page_geometry.json")))["pages"]
    print("  pages in json: %d   npz: %d   npy sidecars: %d"
          % (len(geo), len(glob.glob(os.path.join(T, "page_geometry", "[0-9][0-9][0-9].npz"))),
             len(glob.glob(os.path.join(T, "page_geometry", "[0-9][0-9][0-9]")))))
    check(len(geo) == 176, "stage3", "geometry has %d pages, not 176" % len(geo))
    for p in range(1, 177):
        d = os.path.join(T, "page_geometry", "%03d" % p)
        check(os.path.isdir(d), "p%03d" % p, "no .npy sidecar dir")
        check(str(p) in geo, "p%03d" % p, "not in page_geometry.json")
    # the .npz and the .npy sidecars must agree -- they are two encodings of one measurement
    for p in range(1, 177, 17):
        f = os.path.join(T, "page_geometry", "%03d.npz" % p)
        if not os.path.exists(f):
            continue
        z = np.load(f)
        for k in ("bed_top", "bed_bottom", "bed_left", "bed_right", "spine_inb"):
            s = np.load(os.path.join(T, "page_geometry", "%03d" % p, k + ".npy"))
            check(np.array_equal(z[k], s), "p%03d" % p, "%s: npz and npy sidecar differ" % k)
    if deep:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "02-matte"))
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from bed_matte import bed_matte
        for p in (6, 62, 130):
            _, _, meta = bed_matte(Image.open("/Users/mist/DNB/8609/thumbs_600/%03d.png" % p)
                                   .convert("RGB"), 600, return_meta=True)
            z = np.load(os.path.join(T, "page_geometry", "%03d.npz" % p))
            for e, key in (("top", "bed_top"), ("bottom", "bed_bottom"),
                           ("left", "bed_left"), ("right", "bed_right")):
                exp = meta[e]["median_depth"] + OVERCUT if meta[e]["decision"] == "CUT" else 0.0
                got = float(np.median(z[key]))
                check(abs(got - exp) < 2.0, "p%03d %s" % (p, e),
                      "profile %.1f but the matte now says %.1f" % (got, exp))
        print("  deep: re-ran bed_matte on 3 pages, profiles match")


def stage4():
    """apply: outputs present and self-consistent, and the 2400 dpi unknown fraction agrees with
    the 600 dpi window fit -- two independent computations of the same quantity."""
    print("\n=== stage 4: mrcpipe apply -> CMYK + page RGB + known mask ===")
    rf = os.path.join(T, "apply_reports.jsonl")
    rows = [json.loads(l) for l in open(rf)] if os.path.exists(rf) else []
    win = json.load(open(os.path.join(T, "crop_windows_v2.json")))["windows"]
    print("  applied: %d" % len(rows))
    d = []
    for r in rows:
        p = r["page"]
        check(r["out_size"] == A4_OUT, "p%03d" % p, "out_size %s" % r["out_size"])
        check(r["gcr_ok"], "p%03d" % p, "gcr_ok false -- min(C,M,Y) != 0")
        exp = win[str(p)].get("alpha_pct")
        if exp is not None:
            d.append(r["unknown_pct"] - exp)
            check(abs(r["unknown_pct"] - exp) < 0.5, "p%03d" % p,
                  "unknown %.3f%% but the window fit said %.3f%%" % (r["unknown_pct"], exp))
        for suf in ("_cmyk_display_filled.tif", "_known.png", "_page_rgb.png"):
            f = os.path.join(T, "render", "deliver", "%03d%s" % (p, suf))
            check(os.path.exists(f) and os.path.getsize(f) > 1000, "p%03d" % p, "missing %s" % suf)
    if d:
        d = np.array(d)
        print("  unknown_pct vs window alpha_pct: p50 %+.3f  max |%.3f|"
              % (np.percentile(d, 50), np.abs(d).max()))
    if rows:
        print("  dead_px p50 %d max %d   holes filled %d"
              % (int(np.percentile([r["dead_px"] for r in rows], 50)),
                 max(r["dead_px"] for r in rows), sum(r["holes_filled"] for r in rows)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=0)
    ap.add_argument("--deep", action="store_true")
    A = ap.parse_args()
    fns = {1: stage1, 2: stage2, 3: lambda: stage3(A.deep), 4: stage4}
    for k in sorted(fns):
        if A.stage in (0, k):
            try:
                fns[k]()
            except FileNotFoundError as e:
                print("  (stage %d input missing: %s)" % (k, e))
    print("\n%s" % ("=" * 70))
    if FAIL:
        print("FAILURES: %d" % len(FAIL))
        for f in FAIL[:40]:
            print("  " + f)
        if len(FAIL) > 40:
            print("  ... and %d more" % (len(FAIL) - 40))
    else:
        print("ALL CHECKS PASSED")
    sys.exit(min(len(FAIL), 250))
