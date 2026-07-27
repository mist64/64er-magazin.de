#!/usr/bin/env python3
"""SELF-CHECK -- an objective, LABEL-FREE accuracy score for shear_spine.py.

Why this exists: every previous generation of this detector was judged by eyeballing a
handful of overlays, which is why it could churn for days without a stopping condition.
Neither of the checks here needs a single hand-marked page.

  A. SPLIT-HALF CONSISTENCY. Fit the top half and the bottom half of the page
     independently. If the line is a real measurement both halves land on the same line;
     the disagreement IS the estimator's own error bar, per page, in px and degrees.
     Reported at the page mid-height (dx_mid) so a slant disagreement is not double
     counted as a position one.

  B. SYNTHETIC RECOVERY. Paste a boundary of KNOWN offset and KNOWN slant onto a real
     gutter band (real paper, real halftone, real shading), then measure what comes back.
     This is ground truth without labelling: it bounds the best case and tells us whether
     a slant is recoverable AT ALL at a given colour-step size.

Usage:
  selfcheck.py --split [pages...]      split-half consistency (default: all fired pages)
  selfcheck.py --synth                 synthetic recovery sweep
"""
import os, sys, json, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shear_spine as S

JSON = "/Users/mist/DNB/8609/tmp/shear_v6.json"


def fit_rows(f, sx, parity, rows, clip_inb=None, staple_ang=None):
    """Run the PRODUCTION fit (coarse + 50%-crossing refine) restricted to `rows`."""
    r = S.fit_band(f, sx, parity, clip_inb=clip_inb, staple_ang=staple_ang, rows=rows)
    return r["x_peak"] * S.DS, r["ang"], r


def split(pages):
    """NB: the halves must be fitted under the SAME constraints production uses (clip
    window + staple slant), or the number measures a different estimator. An earlier
    version passed neither and reported a tail that production does not have."""
    d = json.load(open(JSON))
    clip = json.load(open(S.CLIP_JSON))
    issue_ang = S.issue_staple_slant(clip)
    rows_out = []
    for n in pages:
        f, sx, W, H, y0, parity, to_abs = S.load_band(n)
        c = clip.get("%03d" % n)
        ci = None
        if c is not None and c["confidence"] >= S.CLIP_CONF:
            ci = (c["W"] - c["column_x"]) if (n % 2 == 0) else c["column_x"]
        sa = S.staple_slant(c, fallback=issue_ang)
        h = f.shape[0]
        top = np.arange(0, h // 2)
        bot = np.arange(h // 2, h)
        xt, at, _ = fit_rows(f, sx, parity, top, ci, sa)
        xb, ab, _ = fit_rows(f, sx, parity, bot, ci, sa)
        v = d.get("%03d" % n, {})
        rows_out.append(dict(page=n, dx_mid=xt - xb, dang=at - ab,
                             x_full=v.get("inboard_mid"), ang_full=v.get("angle_deg"),
                             step=v.get("step"), x_top=xt, x_bot=xb, a_top=at, a_bot=ab))
        r = rows_out[-1]
        print("p%03d  dx_mid=%+7.1f px  dang=%+6.3f deg   (halves: x %6.1f/%6.1f  a %+.2f/%+.2f)"
              " step=%s" % (n, r["dx_mid"], r["dang"], xt, xb, at, ab, round(v.get("step", 0))))
    dx = np.abs([r["dx_mid"] for r in rows_out])
    da = np.abs([r["dang"] for r in rows_out])
    print("\nSPLIT-HALF over %d pages:" % len(rows_out))
    print("  |dx_mid| med %.1f px (%.2f mm)  p90 %.1f  max %.1f"
          % (np.median(dx), np.median(dx) / 600 * 25.4, np.percentile(dx, 90), dx.max()))
    print("  |dang|   med %.3f deg  p90 %.3f  max %.3f" % (np.median(da), np.percentile(da, 90), da.max()))
    json.dump(rows_out, open("/Users/mist/DNB/8609/tmp/selfcheck_split.json", "w"), indent=1)
    return rows_out


def synth(base_page=100, steps=(20, 40, 80, 160), slants=(0.0, 0.3, 0.8), offset_ref=250):
    """Paste a boundary of KNOWN offset and slant onto a real (neighbour-free) gutter band.

    The paste is ANTI-ALIASED and the truth is expressed in the same units the estimator
    returns (band px), so the numbers below measure the ESTIMATOR, not the harness. An
    earlier version truncated the paste position and compared against reference px, which
    manufactured a constant ~-8 px "bias" that was purely its own.
    """
    f, sx, W, H, y0, parity, to_abs = S.load_band(base_page)
    h, w, _ = f.shape
    ys = np.arange(h)
    xcol = np.arange(w)[None, :]
    print("synthetic on p%03d  band %dx%d  sx=%.4f  (true offset %.1f band px)"
          % (base_page, w, h, sx, offset_ref * sx))
    print("%6s %7s %10s %10s" % ("step", "slant", "dx_px", "dang_deg"))
    for st in steps:
        for sl_deg in slants:
            xb = offset_ref * sx / S.DS + np.tan(np.deg2rad(sl_deg)) * (ys - h / 2.0)
            wgt = np.clip(xb[:, None] - xcol, 0.0, 1.0)      # 1 outboard, 0 inboard, ramp
            g = f + st * wgt[:, :, None]
            x0, ang, _ = fit_rows(g, sx, parity, None)
            print("%6d %7.2f %10.2f %10.3f"
                  % (st, sl_deg, x0 - offset_ref * sx, ang - sl_deg))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", action="store_true")
    ap.add_argument("--synth", action="store_true")
    ap.add_argument("pages", nargs="*", type=int)
    a = ap.parse_args()
    if a.synth:
        synth()
    else:
        pg = a.pages or [v["page"] for v in json.load(open(JSON)).values() if v["found"]]
        split(sorted(pg))
