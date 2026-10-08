#!/usr/bin/env python3
"""
Step 005's FIELD MEASUREMENT -- the paper-yellowing field, once per paper class.

Run this ONCE per issue, before r005_masters_sheet.py, and again only if the
scans or the paper map change:

    cd tools/img/scan2ocr/rules
    ../../../../.venv/bin/python r005_field.py

It writes one file per paper class beside that class's `colors.txt`
(`field_low.txt`, `field_high.txt`), and r005_masters_sheet.py reads it and
applies it to every page of that class immediately before the CMYK separation.
It is not part of r005_masters_sheet.py because it is not a per-page
measurement and must not be one: it is a fit over a WHOLE CLASS, it costs about
as much as one page of grading per page measured, and recomputing it inside
every page would both waste that and -- far worse -- produce 190 fields that do
not agree with each other.

WHAT THE FIELD IS.  The interior stock has not browned evenly.  MEASURED on
SH8605 over 190 raw pages: the clean substrate 2 mm from the foot of the sheet
needs 1.34x more blue and 1.23x more green than that same sheet's own centre to
read as the same paper; at the fore edge 1.19/1.15, at the top 1.23/1.17, at
the gutter 1.07/1.06, and R is nearly flat throughout (1.03-1.05).  Three channels moving by
different amounts is the signature of YELLOWING -- a scanner vignette is grey
and moves all three together.  The grade cannot see any of it, because
`d = -log10(rgb/W)` has ONE W for the whole page.

Everything below was measured during the prototype and is settled.  Each point
is here because getting it wrong was tried and cost something.

(1) MEASURE ON THE RAW SCANS, never on the graded page.  The grade clips 66-84 %
    of each page to pure 255; the signal is not attenuated there, it is gone.
    This program therefore levels the scan itself (through
    r005_masters_sheet.level_and_trace) rather than reading masters600 -- which
    is also what makes it runnable on an issue that has no masters yet, as it
    must be, since the field has to exist before the masters it corrects.

(2) ANCHOR ON EACH PAGE'S OWN TRACED BOX.  See FIELD_PAGE_MM in
    r005_masters_sheet.py: the registered A4 window is placed on the 64'er
    wordmark, and the paper's own edge wanders over an 11.0 mm range inside it,
    which is wider than the whole steep part of the field.  The block grid is
    centred on the traced page centre and masked to the traced page.  This was
    the single biggest error in the first pass.

(3) THE INK IS A COVARIATE, NOT A NUISANCE TO BE FILTERED OUT.  Within a page,
    "distance from the trim" and "inside the text block" are nearly the same
    variable: MEASURED, the horizontal margins are ink-free out to 14 mm and the
    interior runs 18-20 % ink coverage, so the ink step lands exactly where the
    field is steepest.  And the ink really does change the paper around it.  The
    decisive control holds the BLOCK POSITION exactly constant and compares the
    pages on which that block happens to carry ink against the pages on which
    the same block is clean -- position cannot confound that -- and the paper
    level falls monotonically with coverage: -0.70 DN at 7-12 %, -2.02 at
    12-20 %, -3.56 at 20-30 %, -14.12 above 45 %.

    NO PERCENTILE REMOVES IT.  Measured: the same bias is -3.85 DN at p85,
    -3.77 at p95, -3.78 at p98, and -3.65 at p85 taken INSIDE the ink-free
    population only.  The first pass blamed the selector and was wrong.

    So it is regressed out.  The model is fitted on the whole per-page cube,

        log paper[m,j,i] = c + page_m + v_j + h_i + b(ink[m,j,i]) + resid

    with b non-parametric (one level per ink-coverage quantile bin), and the
    field is read off at b(ink = 0): clean substrate, which is what the grade
    needs.  The leverage that identifies b against the positional factors is
    that different PAGES put their ink in different places -- which is why this
    is a per-class fit and cannot be a per-page one.

(4) SEPARABLE AND MONOTONE, four half-profiles.  log gain = gx(x) + gy(y), and
    each of the four halves (gutter, fore, top, bottom) is monotone
    non-decreasing outward from the page centre and exactly 0 there.  Monotone
    because the browning is a diffusion front from an edge and cannot have a
    bright ring in it; a free fit grows one, out of the ink collinearity above.
    MEASURED cost of the constraint: whole-page mean |residual| rises from
    0.60/0.50/0.48 DN (free additive fit) to 2.07/1.18/0.93 (monotone) -- the
    price is paid in the corners, where the separable product over-predicts the
    browning by 2-4 DN, and it is worth paying to not invent a ring.

(5) MIRROR BY PARITY, at application time: an odd page is a recto (fore edge
    right), an even page a verso (fore edge left).

The amplitude, the application (an ink-anchored affine map and NOT a multiply),
and the two per-page anchors are r005_masters_sheet.py's -- see FIELD_ALPHA and
FlatField.apply() there.

THE SHEET VARIANT ONLY.  It imports r005_masters_sheet for the levelling, the
masks and the tracer, and r005_masters_sheet.first_action() refuses an issue
whose `binding` is not "sheet" -- so running this on a spread-bound issue stops
with that refusal rather than measuring the wrong geometry.
r005_masters_spread shares no code with either file and gets no field; see
r005_masters_sheet.md, Notes.

READ-ONLY on the scans.  It writes nothing but the field files.
"""

import math
import os
import sys
import time
from datetime import date
from multiprocessing import Pool

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import nnls

import r000_issue
import r005_masters_sheet as R
from r005_masters_sheet import ISSUE, MM, PageFailed

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see ../README.md)
# ---------------------------------------------------------------------------

# --- the block grid --------------------------------------------------------
# The page is reduced to 4 mm blocks before anything is fitted, because the
# quantity being measured is not a pixel property: it is "what colour is the
# clean paper here", and that needs a population of pixels to find the paper in.
# 4 mm is 94 px at MASTER_DPI, which holds 2209 samples at STRIDE 2 -- enough
# for a percentile -- and is small against the 6 mm over which the field does
# most of its moving.
BLOCK_MM = 4.0
# 53 x 75 blocks = 212 x 300 mm, centred on the TRACED PAGE CENTRE: the whole
# of an A4 page plus a block of slack on each side, so that a page 2 mm wider
# than the median still has its own edge inside the grid.
NX, NY = 53, 75
# Every second pixel in each direction, i.e. one in four.  A percentile of 2209
# samples and of 8836 is the same percentile, and one of them costs nothing.
STRIDE = 2
# A block with fewer valid (inside the traced page, not dropped bed) samples
# than this has no population to take a percentile of.  At the page edge a
# block is often half outside the traced line.
MIN_PIX = 400
# --- what counts as paper inside a block, and what counts as ink -----------
# "Paper" is the mean RGB of the pixels at or above this percentile of the
# block's own luminance.  85 and not 98: a block's top 2 % is specular fibre
# and scanner noise, and 85 still sits above the halftone dots of a light tint.
# The choice has been swept (98/95/85/60/40/25, and the same percentiles taken
# inside the ink-free population only) and it does not matter much, because the
# ink bias every one of them carries is regressed out rather than selected away
# -- see (3) in the docstring.
PAPER_PCT = 85
# A pixel is INK, for the purpose of the coverage figure, if its luminance is
# this far below the block's own near-top level (its 97th percentile).  70 DN
# is well below any tint and well above the paper's own grain.
INK_DROP = 70.0
INK_CORE_PCT = 97
# --- the fit ---------------------------------------------------------------
# Ink-coverage bins for b(ink): quantiles of the observed coverage, so each bin
# carries a comparable number of blocks, with the three cleanest edges pinned
# by hand because that end is where the field is read off and it must be
# resolved -- bin 0 is "no ink at all" and is the anchor.
NINK = 24
INK_PIN = (0.0, 0.005, 0.02)
# Iterations of the robust (median) four-factor polish.  40 is well past
# convergence: MEASURED, the edge gains move by less than 1e-4 after 20.
POLISH_ITERS = 40
# A bin with fewer blocks than this does not get to move its own level.
POLISH_MIN_BIN = 200
# The monotone half-profile is a non-negative sum of 14 ramps in
# t = log((1+D)/(1+e)) -- a log scale in DISTANCE FROM THE EDGE, so the knots
# crowd where the field moves, then smoothed with a Gaussian of 0.10 in t and
# made monotone by a cumulative maximum.  14 knots resolves the 2 mm edge step
# without fitting the block noise; the smoothing is what keeps the first knot
# from becoming a step.
NKNOT = 14
SMOOTH_T = 0.10
# The written profile is sampled every half-millimetre of distance from the
# page centre.  MEASURED: the steepest part of the field moves 0.0135 of gain
# per mm, so linear interpolation between half-millimetre samples is wrong by
# under 0.001 of gain -- 0.2 DN on paper -- and the file stays something a
# person can read.
STEP_MM = 0.5

# --- when a class gets an IDENTITY field instead of a fit ------------------
# A field is a fit over a class, and a class too small to fit one does not get
# a guessed one.  It gets an IDENTITY field, written down as such, with the
# reason in the file -- because "no file" and "a stock that cannot support a
# fit" are different facts and a master must be able to say which of them made
# it.
#
# MEASURED, on SH8605's own 190 fitted pages: the field was refitted on random
# subsets of n pages, six draws each, and the gain 2 mm from each of the four
# edges compared against the full fit.  |dgain| over the twelve
# (side, channel) pairs, mean of the worst pair and the worst seen:
#
#     n pages      6      12      18      24      32      48      96
#     mean worst  .0291   .0191   .0109   .0085   .0113   .0086   .0042
#     max  worst  .0475   .0344   .0191   .0116   .0245   .0120   .0065
#
# 0.01 of gain is about 2 DN of paper -- the point below which the correction
# is better than nothing at every edge rather than only on average -- and 24
# is where both columns first sit under it; at 12 the worst edge is out by
# 0.034, which is a tenth of the whole bottom-edge correction applied in the
# wrong direction.  Between 18 and 48 the curve is flat, so the floor is not
# sensitive to where in that range it is put.
#
# It is a statement about the INK COVARIATE and not about pixel counts: one
# page already provides ~3000 blocks, but b(ink) is identified only by pages
# putting their ink in DIFFERENT PLACES, and that is what runs out first.
FIELD_MIN_PAGES = 24
# ...and a class holding more than one PIECE OF PAPER cannot have one field
# either, however many pages it has.  A field is four profiles indexed by
# distance from one edge of one page; fitted across two sizes it is anchored on
# neither.  SH8605's `high` class is exactly that: the folded A3 wrapper's four
# halves (001, 002, 195, 196) plus the bound-in Zahlkarte (197-200).
#
# THE TEST IS AN EXPLICIT ONE, and it is made on the THUMBS -- the production
# tracer, the production constants, at THUMB_DPI -- so that the question is
# answered in 0.1 s a page instead of by opening every scan.  MEASURED on
# SH8605's thumbs:
#
#   low   (192 pages)   209.8 x 296.5 mm at p50, interdecile spread 1.4 x 0.6 mm
#   high  (8 pages)     the wrapper 210-214 x 296-298, the card 150 x 208 --
#                       an interdecile spread of 63 x 89 mm
#
# It is the INTERDECILE spread and not min-max, because the question is whether
# the class has two MODES and not whether one page's trace failed: SH8605's low
# class contains p035, whose trace locked onto the interior of a dark-ground ad
# and reads 173.6 x 254.6 mm, and min-max over the class would therefore be
# 45 mm and the whole interior would lose its correction over one bad page.
# That page is rejected by name where it belongs, one page at a time, by the
# traced-box test in measure_page().
#
# 10 mm is seven times the measured within-stock spread and a sixth of the gap
# to the Zahlkarte, so it sits in the middle of a gap 60 mm wide.
FIELD_SIZE_SPREAD_MM = 10.0
FIELD_SIZE_DECILE = (10, 90)

# --- parallelism -----------------------------------------------------------
# One lane holds one levelled page and its masks.  MEASURED peak RSS on
# SH8605's 36.6 Mpx frames: 3.3 GB, dominated by the bicubic rotation of the
# whole frame and by the connected-component labelling of the bed mask (one
# int32 per pixel).  It scales with the FRAME, so the cost is quoted per
# megapixel of the scan and multiplied by the frame this issue actually has --
# a 2400 dpi issue is sixteen times the page and gets correspondingly fewer
# lanes, which is the honest answer rather than a swap storm.
FIELD_LANE_GB_PER_MPX = 3.3 / 36.6


# ---------------------------------------------------------------------------
# One page: 4 mm blocks of "what colour is the clean paper here"
# ---------------------------------------------------------------------------

def _bin_edges(centre, n):
    """n block edges of BLOCK_MM, centred on `centre` (a pixel coordinate)."""
    bs = BLOCK_MM * MM
    return centre + (np.arange(n + 1) - n / 2.0) * bs


def block_stats(t):
    """(paper, ink, count) per 4 mm block of one traced page.

    paper[j,i] = the mean RGB of the brightest PAPER_PCT of the block
    ink[j,i]   = the fraction of the block that is ink, by INK_DROP
    count[j,i] = valid samples, for the record

    One sort and one reverse cumulative sum per block gives both the upper-tail
    mean and the ink fraction, which is why this is affordable at all.
    """
    arr, keep = t.arr, t.keep
    x0, y0, x1, y1 = t.box
    h, w = t.h, t.w
    xb = np.clip(np.round(_bin_edges(0.5 * (x0 + x1), NX)).astype(int), 0, w)
    yb = np.clip(np.round(_bin_edges(0.5 * (y0 + y1), NY)).astype(int), 0, h)

    paper = np.full((NY, NX, 3), np.nan, np.float32)
    ink = np.full((NY, NX), np.nan, np.float32)
    cnt = np.zeros((NY, NX), np.int32)

    af = arr.astype(np.float32)
    lum = af @ R.FIELD_LUM
    for j in range(NY):
        ya, yz = yb[j], yb[j + 1]
        if yz - ya < 4:
            continue
        lr, cr, vr = lum[ya:yz:STRIDE], af[ya:yz:STRIDE], keep[ya:yz:STRIDE]
        for i in range(NX):
            xa, xz = xb[i], xb[i + 1]
            if xz - xa < 4:
                continue
            v = vr[:, xa:xz:STRIDE].ravel()
            nv = int(v.sum())
            cnt[j, i] = nv
            if nv < MIN_PIX:
                continue
            L = lr[:, xa:xz:STRIDE].ravel()[v]
            C = cr[:, xa:xz:STRIDE].reshape(-1, 3)[v]
            o = np.argsort(L, kind="stable")
            Ls, Cs = L[o], C[o]
            rc = np.cumsum(Cs[::-1], axis=0)[::-1]      # rc[k] = sum of Cs[k:]
            n = Ls.size
            core = Ls[min(n - 1, int(INK_CORE_PCT / 100.0 * n))]
            k0 = int(np.searchsorted(Ls, core - INK_DROP))
            ink[j, i] = k0 / float(n)
            k = min(n - 1, int(PAPER_PCT / 100.0 * n))
            paper[j, i] = rc[k] / float(n - k)
    return paper, ink, cnt


def measure_page(page):
    """(page, measurement, rejection) for one page.  Exactly one of the last two.

    EVERY REJECTION IS NAMED, and lands in the field file's own provenance.
    MEASURED on SH8605: two pages fail, p035 (its trace matched no page class
    at all, so the box recorded for it is the whole 215.3 x 304.2 mm sheet) and
    p193 (the trace lost 5 mm of width and recorded 204.2 x 297.1).

    AND THE HONEST SIZE OF WHAT THIS BUYS, measured rather than asserted:
    refitting with p193's bad box included moves the fitted gain 2 mm from the
    edges by at most 0.00016, which is nothing.  One bad box in 190 pages
    cannot bend a median-polished fit, and a comment here used to claim it
    could.  The gate earns its place for two other reasons:

      - THE APPLICATION, where it is not an average.  Each page's correction is
        anchored on ITS OWN box, so a page whose box is not its page has its
        whole gain field placed wrong -- and r005_masters_sheet.py reads this
        same test and leaves such a page uncorrected rather than guessing.
      - A SMALL CLASS, where one bad box IS a large share.  A class of 24 is
        the floor, and at 24 pages a single whole-sheet box is 4 % of the fit.

    So it is a gate on both halves and the number above is why it is a gate and
    not a warning.
    """
    try:
        t = R.level_and_trace(page).locate()
    except PageFailed as exc:
        return page, None, str(exc)
    except Exception as exc:                       # a scan this step cannot read
        return page, None, f"{type(exc).__name__}: {exc}"
    if t.klass == "uncropped sheet":
        return page, None, ("the trace matched no page class, so there is no "
                            "traced page to anchor a field on")
    if not R.field_box_ok(t.page_w_mm, t.page_h_mm):
        return page, None, R.field_box_complaint(t.page_w_mm, t.page_h_mm)
    paper, ink, cnt = block_stats(t)
    if np.isfinite(paper[..., 0]).sum() < 0.25 * NX * NY:
        return page, None, (f"only {int(np.isfinite(paper[..., 0]).sum())} of "
                            f"{NX * NY} blocks are measurable")
    pc, k, _ = R.page_anchors(t.arr, t.keep, t.box, None)
    return page, dict(paper=paper, ink=ink, cnt=cnt, box=t.box,
                      pc=pc, k=k, recto=(page % 2 == 1)), None


# ---------------------------------------------------------------------------
# The fit
# ---------------------------------------------------------------------------

def polish4(L, inkbin, nbin):
    """L[m,j,i] ~ c + page_m + v_j + h_i + b_k, by medians.

    Medians and not least squares: a block can be arbitrarily bad -- a run of
    specular fibre, a sticker, a tear -- and a mean has no defence.  b is
    anchored at bin 0, the cleanest, so that `c` is the level of CLEAN paper and
    v, h are read off there.
    """
    ok = np.isfinite(L)
    M, J, I = L.shape
    pg, v, h = np.zeros(M), np.zeros(J), np.zeros(I)
    b, c = np.zeros(nbin), 0.0
    flat_bin = inkbin.ravel()
    for _ in range(POLISH_ITERS):
        def resid():
            return L - c - pg[:, None, None] - v[None, :, None] \
                     - h[None, None, :] - b[inkbin]
        r = resid()
        pg += np.nan_to_num(np.nanmedian(np.where(ok, r, np.nan), axis=(1, 2)))
        r = resid()
        v += np.nan_to_num(np.nanmedian(np.where(ok, r, np.nan), axis=(0, 2)))
        r = resid()
        h += np.nan_to_num(np.nanmedian(np.where(ok, r, np.nan), axis=(0, 1)))
        rf = np.where(ok, resid(), np.nan).ravel()
        for kk in range(nbin):
            m = flat_bin == kk
            if m.sum() > POLISH_MIN_BIN:
                d = np.nanmedian(rf[m])
                if np.isfinite(d):
                    b[kk] += d
        for a in (pg, v, h):
            d = np.median(a)
            a -= d
            c += d
        c += b[0]
        b -= b[0]                       # the CLEANEST bin is the anchor
    return c, pg, v, h, b


def _t(e, D):
    """Distance from the EDGE -> the fit's own abscissa.  0 at the centre."""
    return np.log((1.0 + D) / (1.0 + np.asarray(e, np.float64)))


def _ramps(d, D, kn):
    t = _t(np.clip(D - np.asarray(d, np.float64), 0.0, None), D)
    B = np.zeros((t.size, len(kn) - 1))
    for m in range(len(kn) - 1):
        B[:, m] = np.clip((t - kn[m]) / (kn[m + 1] - kn[m]), 0.0, 1.0)
    return B


def fit_axis(dsig, y, D):
    """Two monotone half-profiles on one axis, with one shared free intercept.

    `dsig` is the signed distance of each sample from the page centre, in mm,
    and `y` the log gain wanted there.  The two halves share the intercept
    because the centre is ONE place: they must agree there, and what they agree
    on is not known in advance.  Returns (d grid, negative half, positive half,
    intercept) with both halves 0 at d = 0 and non-decreasing outward.
    """
    ok = np.isfinite(y)
    dsig = np.asarray(dsig, np.float64)[ok]
    y = np.asarray(y, np.float64)[ok]
    T = _t(0.0, D)
    kn = np.linspace(0.0, T, NKNOT + 1)
    dA = np.where(dsig < 0, -dsig, 0.0)
    dB = np.where(dsig > 0, dsig, 0.0)
    X = np.hstack([np.ones((dsig.size, 1)), -np.ones((dsig.size, 1)),
                   _ramps(dA, D, kn), _ramps(dB, D, kn)])
    coef, _ = nnls(X, y)
    a = coef[0] - coef[1]
    dd = np.linspace(0.0, D, 4001)
    tt = np.linspace(0.0, T, 4001)
    Bt = np.zeros((4001, NKNOT))
    for m in range(NKNOT):
        Bt[:, m] = np.clip((tt - kn[m]) / (kn[m + 1] - kn[m]), 0.0, 1.0)
    out = []
    for cf in (coef[2:2 + NKNOT], coef[2 + NKNOT:]):
        prof = gaussian_filter1d(Bt @ cf, SMOOTH_T * 4000 / T, mode="nearest")
        prof = np.maximum.accumulate(prof - prof[0])
        out.append(np.maximum.accumulate(
            np.interp(_t(np.clip(D - dd, 0.0, None), D), tt, prof)))
    return dd, out[0], out[1], a


def fit_class(stats):
    """The four monotone half-profiles per channel, from a class's pages.

    `stats` is the list measure_page() produced, already filtered to the pages
    that may be fitted.  Returns (profiles, half, centre, floor, report lines).
    """
    pages = np.array([s["page"] for s in stats])
    paper = np.array([s["paper"] for s in stats], np.float64)
    ink = np.array([s["ink"] for s in stats], np.float64)
    box = np.array([s["box"] for s in stats])

    # Half-width and half-height of the traced page, in mm: the MEDIAN over the
    # class, because the profiles are one set of numbers for the class and have
    # to be indexed by one length.  The spread is +-1 mm (see FIELD_PAGE_MM),
    # and a page wider than the median simply reads its outermost half
    # millimetre at the edge gain, which is where the monotone profile has
    # flattened anyway.
    Dx = float(np.median(box[:, 2] - box[:, 0]) / 2.0 / MM)
    Dy = float(np.median(box[:, 3] - box[:, 1]) / 2.0 / MM)

    # MIRROR THE VERSOS INTO RECTO ORIENTATION before pooling.  The gutter is
    # the bound edge and the fore edge the trimmed one, and they are physically
    # different -- 1.07 against 1.19 of blue at 2 mm -- so pooling without the
    # mirror averages the two into one wrong profile.
    even = np.array([not s["recto"] for s in stats])
    paper[even] = paper[even][:, :, ::-1, :]
    ink[even] = ink[even][:, :, ::-1]

    bs = BLOCK_MM * MM
    XC = (np.arange(NX) - NX / 2.0 + 0.5) * bs / MM
    YC = (np.arange(NY) - NY / 2.0 + 0.5) * bs / MM

    iv = ink[np.isfinite(ink)]
    edges = np.unique(np.concatenate(
        [np.array(INK_PIN),
         np.quantile(iv[iv > INK_PIN[-1]], np.linspace(0, 1, NINK - len(INK_PIN)))]))
    inkbin = np.clip(np.searchsorted(edges, np.nan_to_num(ink, nan=0.0),
                                     side="right") - 1, 0, len(edges) - 1)

    prof, rep = {}, []
    for c, cn in enumerate("RGB"):
        with np.errstate(all="ignore"):
            L = np.log(paper[..., c])
        cst, pg, v, h, b = polish4(L, inkbin, len(edges))
        ddx, p_gut, p_fore, _ = fit_axis(XC, -h, Dx)
        ddy, p_top, p_bot, _ = fit_axis(YC, -v, Dy)
        gx = np.arange(0.0, Dx + 0.5 * STEP_MM, STEP_MM)
        gy = np.arange(0.0, Dy + 0.5 * STEP_MM, STEP_MM)
        prof[cn] = {
            "gutter": np.exp(np.interp(gx, ddx, p_gut)),
            "fore":   np.exp(np.interp(gx, ddx, p_fore)),
            "top":    np.exp(np.interp(gy, ddy, p_top)),
            "bottom": np.exp(np.interp(gy, ddy, p_bot)),
        }
        rep.append(f"{cn}: clean-paper level exp(c) = {math.exp(cst):.1f} DN; "
                   f"ink term b(ink) in DN at a 200 level: "
                   + " ".join(f"{edges[kk]:.2f}:{200 * (math.exp(b[kk]) - 1):+.1f}"
                              for kk in range(0, len(edges), 4)))

    centre = np.median(np.array([s["pc"] for s in stats
                                 if s["pc"] is not None]), axis=0)
    floor = np.median(np.array([s["k"] for s in stats
                                if s["k"] is not None]), axis=0)
    return prof, (Dx, Dy), centre, floor, rep


def edge_table(prof, half, step=STEP_MM):
    """The headline numbers: fitted gain at e mm from each edge, per channel."""
    L = ["fitted gain at distance e from the page edge, per channel:",
         "  e mm |      gutter        |        fore        |"
         "        top         |       bottom",
         "       |   R      G      B  |   R      G      B  |"
         "   R      G      B  |   R      G      B"]
    for e in (0.5, 2, 6, 12, 25, 50):
        row = f"  {e:4g} |"
        for side in R.FIELD_SIDES:
            D = half[0] if side in ("gutter", "fore") else half[1]
            for cn in "RGB":
                g = prof[cn][side]
                row += " %.4f" % np.interp(max(D - e, 0.0),
                                           np.arange(len(g)) * step, g)
            row += " |"
        L.append(row)
    return L


# ---------------------------------------------------------------------------
# One paper class
# ---------------------------------------------------------------------------

def thumb_page_mm(page):
    """(w, h) of the traced page in mm, measured on the 150 dpi THUMB.

    The production tracer at THUMB_DPI: the same paper and sheet masks, the
    same boundaries() and trace(), the same percentiles -- only the resolution
    differs, which is the whole point.  It costs 0.1 s against the 20 s a
    levelled scan costs, and it is accurate to about 3 mm (MEASURED: p193 reads
    207.3 here and 204.2 at MASTER_DPI), which is a tenth of what the mixed-
    paper test has to resolve and nowhere near enough to decide a page's own
    anchor.  So it is used for THAT QUESTION ONLY; the per-page traced-box test
    in measure_page() is made at full resolution.
    """
    from PIL import Image
    rgb = np.array(Image.open(R.THUMB_DIR / f"{page:03d}.png").convert("RGB"))
    m = R.paper_mask(rgb)
    if R.mask_paper_frac(m) < R.FULLBLEED_PAPER_FRAC:
        rows, st, en, cols, tp, bt = R.sheet_boundaries(
            R.find_sheet(rgb, R.THUMB_MM))
    else:
        rows, st, en, cols, tp, bt = R.boundaries(m)
    h, w = m.shape
    ys, xs = np.arange(h), np.arange(w)
    xl = np.polyval(R.trace(st, rows, R.CLEAN_PCT, R.THUMB_MM), ys)
    xr = np.polyval(R.trace(en, rows, R.CLEAN_PCT, R.THUMB_MM), ys)
    yt = np.polyval(R.trace(tp, cols, R.CLEAN_PCT, R.THUMB_MM), xs)
    yb = np.polyval(R.trace(bt, cols, R.CLEAN_PCT, R.THUMB_MM), xs)
    return ((xr.max() - xl.min()) / R.THUMB_MM,
            (yb.max() - yt.min()) / R.THUMB_MM)


def size_spread(pages):
    """(w decile pair, h decile pair, spread_mm) over a class's traced pages.

    See FIELD_SIZE_SPREAD_MM: the INTERDECILE spread, so that one page whose
    trace ran away cannot deny a whole class its correction.
    """
    lo, hi = FIELD_SIZE_DECILE
    f = np.array([thumb_page_mm(p) for p in pages])
    w = (float(np.percentile(f[:, 0], lo)), float(np.percentile(f[:, 0], hi)))
    h = (float(np.percentile(f[:, 1], lo)), float(np.percentile(f[:, 1], hi)))
    return w, h, float(max(w[1] - w[0], h[1] - h[0]))


def write_identity(grade, reason, extra=()):
    """An identity field, WRITTEN DOWN.  See FIELD_MIN_PAGES.

    Not skipping the file is the whole point: `no file` means nobody has
    measured this stock and `mode identity` means somebody measured it and
    found it cannot be fitted.  Both produce the same pixels and the same
    digest, and a master has to be able to say which of them it was.
    """
    dest = R.field_path(grade)
    prov = [f"measured {date.today().isoformat()} by r005_field.py",
            "",
            "THIS CLASS GETS NO FITTED FIELD, and that is a measurement, not an",
            "omission.  Its pages are corrected by nothing at all, exactly as",
            "they were before this step existed.  `mode identity` here and a",
            "MISSING file are different facts and produce the same pixels: this",
            "one says the class was measured and cannot support a fit.",
            f"reason: {reason}"] + list(extra)
    R.write_field(dest, grade, R.field_text("identity"), prov)
    print(f"r005_field: {grade.klass or 'single'} -> IDENTITY ({reason})\n"
          f"            {dest}", flush=True)
    return dest


def do_class(klass, pages):
    """Measure and write ONE paper class's field."""
    grade = R.GRADES[klass]
    name = klass or "single"
    have = [p for p in pages
            if (R.SCAN_DIR / f"{p:03d}.png").exists()
            and (R.THUMB_DIR / f"{p:03d}.png").exists()]
    missing = sorted(set(pages) - set(have))
    print(f"\nr005_field: paper class `{name}` -- {len(have)} of {len(pages)} "
          f"page(s) have a scan and a thumb", flush=True)

    # BOTH TESTS, ALWAYS, and every reason recorded.  They are independent
    # facts about the class -- "too few pages" and "more than one piece of
    # paper" -- and a class that fails both says so, because reading only the
    # first reason off a file is how the second one gets fixed and the field
    # still does not appear.  SH8605's `high` class fails both.
    (wlo, whi), (hlo, hhi), spread = size_spread(have)
    size_line = (f"traced pages (on the thumbs) {wlo:.1f}-{whi:.1f} x "
                 f"{hlo:.1f}-{hhi:.1f} mm, p{FIELD_SIZE_DECILE[0]}-"
                 f"p{FIELD_SIZE_DECILE[1]} -- spread {spread:.1f} mm, allowed "
                 f"{FIELD_SIZE_SPREAD_MM:g}")
    print(f"            {size_line}", flush=True)
    blocking = []
    if len(have) < FIELD_MIN_PAGES:
        blocking.append(f"{len(have)} page(s), and a field needs at least "
                        f"{FIELD_MIN_PAGES} (FIELD_MIN_PAGES)")
    if spread > FIELD_SIZE_SPREAD_MM:
        blocking.append(f"more than one piece of paper in this class -- "
                        f"{size_line}")
    if blocking:
        return write_identity(grade, "; ".join(blocking),
                              extra=[""] + ["  " + b for b in blocking])

    # One lane's cost scales with the FRAME, which is the thing that is opened,
    # rotated and labelled -- not with the traced page inside it.
    from PIL import Image
    with Image.open(R.SCAN_DIR / f"{have[0]:03d}.png") as im:
        mpx = im.size[0] * im.size[1] / 1e6
    lane_gb = max(1.0, FIELD_LANE_GB_PER_MPX * mpx)
    lanes = r000_issue.lanes(lane_gb)
    t0 = time.time()
    print(f"            measuring on {lanes} lane(s) "
          f"({lane_gb:.1f} GB each)", flush=True)
    with Pool(lanes) as pool:
        out = pool.map(measure_page, have, chunksize=1)
    stats, rejected = [], []
    for page, m, why in out:
        if m is None:
            rejected.append((page, why))
        else:
            m["page"] = page
            stats.append(m)
    for page, why in rejected:
        print(f"            REJECT p{page:03d}: {why}", flush=True)
    print(f"            {len(stats)} page(s) fitted, {len(rejected)} rejected, "
          f"{time.time() - t0:.0f}s", flush=True)

    if len(stats) < FIELD_MIN_PAGES:
        return write_identity(
            grade, f"only {len(stats)} of {len(have)} page(s) survived the "
                   f"traced-box test, and a field needs at least "
                   f"{FIELD_MIN_PAGES}",
            extra=["rejected:"] + [f"  p{p:03d}  {w}" for p, w in rejected])

    prof, half, centre, floor, rep = fit_class(stats)
    prov = [f"measured {date.today().isoformat()} by r005_field.py",
            "",
            f"{len(stats)} page(s) of class `{name}` fitted; "
            f"{len(rejected)} rejected, {len(missing)} without a scan or thumb",
            f"pages: " + " ".join(f"{s['page']:03d}" for s in stats),
            size_line,
            "",
            "METHOD -- measured on the RAW levelled scans at "
            f"{R.MASTER_DPI} dpi, never on the graded page (the grade clips "
            "most of",
            "the paper to 255 and the signal is gone).  Each page's own TRACED "
            "PAGE BOX is the anchor:",
            f"the block grid is {NX} x {NY} blocks of {BLOCK_MM:g} mm centred "
            "on the traced page centre and masked to",
            "the traced page.  Paper per block = the mean RGB of its brightest "
            f"{100 - PAPER_PCT} %.  The INK coverage",
            "is regressed OUT as a covariate rather than filtered out "
            f"(log paper = c + page + v_row + h_col + b(ink)),",
            f"b non-parametric over {NINK} coverage bins, and the field is "
            "read at b(ink = 0) = clean substrate.",
            "The four half-profiles are monotone outward from the page centre "
            "by construction and are",
            "normalised to a centre gain of exactly 1.0; the versos were "
            "mirrored into recto orientation",
            "before pooling, and r005_masters_sheet.py mirrors them back by "
            "page parity.",
            "",
            "the ink term, per channel:"] \
        + [f"  {line}" for line in rep] \
        + ["",
           f"half-page: {half[0]:.2f} x {half[1]:.2f} mm "
           f"(median of the class's traced boxes, halved)",
           f"centre-paper / ink-floor below are the class MEDIANS of the "
           f"per-page anchors; a page that",
           f"cannot measure its own falls back on them.",
           ""] \
        + edge_table(prof, half) \
        + ([""] + ["rejected:"] + [f"  p{p:03d}  {w}" for p, w in rejected]
           if rejected else []) \
        + ([f"no scan or thumb: " + " ".join(f"{p:03d}" for p in missing)]
           if missing else [])

    body = R.field_text("fitted", STEP_MM, half, centre, floor, prof)
    dest = R.field_path(grade)
    R.write_field(dest, grade, body, prov)
    print("\n".join("            " + l for l in edge_table(prof, half)),
          flush=True)
    print(f"r005_field: {name} -> FITTED on {len(stats)} page(s)\n"
          f"            {dest}", flush=True)
    return dest


def main():
    # The same two questions, before anything is measured: the field is part of
    # the grade and is measured PER PAPER CLASS, so an issue that has not said
    # which pages are on which paper cannot have one measured at all.
    R.first_action()
    pages = [int(a) for a in sys.argv[1:]] or list(R.ISS.page_range)
    print(f"r005_field {ISSUE}: the paper-yellowing field, per paper class, "
          f"over {len(pages)} page(s)", flush=True)
    if R.ISS.paper is None:
        do_class(None, pages)
    else:
        for klass in r000_issue.PAPER_CLASSES:
            mine = [p for p in pages if R.ISS.paper.klass(p) == klass]
            if not mine:
                print(f"\nr005_field: paper class `{klass}` has no page in "
                      f"this run", flush=True)
                continue
            do_class(klass, mine)
    print("\nr005_field: done.  r005_masters_sheet.py will read these files; "
          "every stamp it writes names the field that made the page.",
          flush=True)


if __name__ == "__main__":
    main()
