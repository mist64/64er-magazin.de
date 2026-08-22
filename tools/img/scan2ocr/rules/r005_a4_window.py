#!/usr/bin/env python3
"""
Step 005b -- the A4 window, ANCHORED ON THE 64'er LOGO.

    <tmp>/sheets600/NNN.png   the wordmark is FOUND and the window FITTED here
    <tmp>/masters600/NNN.png  the window is APPLIED here, and its `sheet-box`
                              stamp is the translation between the two frames
      ->  <tmp>/a4600/NNN.png            every page exactly 4961 x 7016

See rules/r005_a4_window.md for the rule.  This program is a PORT of the process
that already solved it, `scan2mrc/03-crop` (`logo_detect.py`, `logo_clearance.py`,
`fit_window.py`, `crop_a4.py`).  scan2mrc is retired, so nothing here imports
from it; the template `template_64er_600.png` was COPIED beside this file.

WHY THE LOGO IS THE ANCHOR -- the principle, in the original's words:

    The "64'er" wordmark is print-registered to the page CONTENT.  The sheet
    edge is not: print-to-cut registration varies, so anchoring on the paper
    edge would align the paper and misalign the type.

Step 005 traces the paper edge, and that trace is the right answer to the
question it asks -- where is this sheet.  It is the wrong answer to the question
delivery asks -- where is the TYPE.  A window placed on the trim aligns the
paper and lets the type wander by however much the guillotine varied (1-3 mm on
SH8601).  This step places the window on the wordmark instead.

WHAT IS DIFFERENT FROM THE ORIGINAL, and why
--------------------------------------------
* The original detected on the RAW thumbs and then had to transform the anchor
  through the levelling rotation -- and its docstring lied about which frame it
  reported, which the rule records as a caution paid for once already.  THAT
  WHOLE CLASS OF BUG IS GONE HERE: detection runs on `<tmp>/sheets600`, the
  deskewed, graded, UNCROPPED 600 dpi sheet, which is the same frame the window
  lives in.  There is no transform to get wrong.
* The original cross-checked a weak match by probing for the page NUMBER just
  outboard of the wordmark.  MEASURED on SH8601: that probe does not apply --
  this Sonderheft puts the folio at the OUTER bottom corner and the wordmark at
  the INNER one (p056: folio "56" at x~250, wordmark at x~4390 of a 5107 px
  frame), so there is no number band beside the wordmark to find.  The match
  score is the only evidence, and the distribution is reported so the gate can
  be argued with rather than assumed.
* The original's "alpha" was a real alpha channel on an RGBA render.  sheets600
  is RGB, so the equivalent -- pixels inside the window that are NOT this page's
  own paper -- is measured here: scanner bed, the coloured prop, and anything
  off the scan frame.  See page_mask().
* The original fell back to the SPINE where there was no logo.  A glue-bound
  Sonderheft has no spine in frame, so the fallback order is the one the rule
  records for this chain (logo / paper-edge / traced-edge).  Fallbacks 2 and 3
  are the same arithmetic on step 005's traced box; what separates them is which
  of step 005's two edge finders traced it, which is a measurement it already
  records per page rather than a list of page numbers.  See place().

ONE NUMBER TO READ WITH CARE: `alpha`, the fit's objective, is measured with
page_mask(), which fails where a page's own ink runs to the trim and bridges to
the bed -- p001 reports 97 % alpha and is a perfectly cut cover.  On those pages
read `fabricated` in the stamp instead: it is measured against step 005's traced
box and does not depend on the mask.

THE WINDOW IS RIGID -- one (S, B) pair per PARITY, not per page:

    S = the anchor's distance from the window's LEFT edge
    B = the anchor's distance from the window's TOP  edge

fitted to minimise alpha inside the window over the pages that have their OWN
logo.  Pages with no detected logo are EXCLUDED FROM THE FIT -- placing them
first and then fitting to them would drag the optimum toward their own error --
and are placed afterwards from what those pages actually have.

THE TRAP, carried over verbatim from the original because it has been paid for:
S MUST BE SEARCHED ACROSS THE FULL PAGE WIDTH.  On the parity whose anchor sits
near the RIGHT edge S is ~4400, and on 8609 a range capped at 900 px pinned the
optimum to its own boundary and reported 71 % alpha -- a window mostly off the
page.  Both searches assert afterwards that the optimum is not on a boundary.

A4 DOES NOT FIT WITHOUT ALPHA, and that is expected.  The page is not 210x297 mm
of known pixels once bed, prop and the deskew wedge are removed, so the
objective is not "avoid alpha" but "minimise it".  Where the window overhangs
what is known, the output is FABRICATED PAPER WHITE and the amount is recorded
per page -- the window is NEVER clamped, because clamping silently shifts the
content and destroys the one property the anchor exists to provide.

RUN
---
    python r005_a4_window.py              measure every page, fit, cut every page
    python r005_a4_window.py 056 063 110  measure every page, fit, cut ONLY these

Positional pages restrict the CUT, never the measurement and never the fit: a
per-parity offset fitted on three pages is not the offset, and the original's
recorded footgun was exactly this -- running its detector on a subset REWROTE
its whole output file with only those pages.  The measurement cache here MERGES
and the fit always runs over the whole issue.
"""

import json
import os
import re
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import cv2
import numpy as np
from multiprocessing import Pool
from PIL import Image, PngImagePlugin
from scipy import ndimage as ND

import r000_issue
from r000_issue import ISSUE

Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see ../README.md)
# ---------------------------------------------------------------------------

DPI = 600
A4_W = int(round(210.0 / 25.4 * DPI))          # 4961
A4_H = int(round(297.0 / 25.4 * DPI))          # 7016

# --- the template ----------------------------------------------------------
# 394 x 131 px at 600 dpi, cut from 8609 and COPIED here from the retired
# scan2mrc tree.  MEASURED on SH8601: it matches this Sonderheft UNCHANGED, at
# scale 1.0, on both parities -- 0.91-0.96 on the three pages it was checked
# against by hand (056, 063, 110), 0.917-0.981 over the 134 pages it is found on.
# The wordmark is the same glyph on every page and is NOT mirrored between
# parities, which is why one template serves both.
TEMPLATE = Path(__file__).resolve().parent / "template_64er_600.png"

# --- where the wordmark is looked for --------------------------------------
# MEASURED on SH8601: the matched template's top-left lands 325-456 px above the
# bottom of the 7188 px frame.  The band below is generous around that, and it
# is expressed as an offset from the BOTTOM because that is what the wordmark is
# registered to.
BAND_TOP_FROM_BOTTOM = 900
BAND_BOT_FROM_BOTTOM = 80
CORNER_FRAC = 0.48          # horizontal reach of each bottom corner, as a
                            # fraction of the frame width.  The two corners must
                            # not overlap by much or the parity vote is noise.
COARSE_REDUCE = 4           # coarse pass at 150 dpi, refine at 600
REFINE_PAD = 90             # +/- px @600 around the coarse hit
# The sheets are LEVELLED before they get here (step 005 asserts a residual
# under 0.10 deg), so the sweep is small.  It is not zero: levelling is measured
# on the type and the wordmark is 130 px tall, where a tenth of a degree is
# still a pixel.
MATCH_ANGLES = (-1.0, -0.5, 0.0, 0.5, 1.0)
INK_THRESH = 100            # grey < this = ink, for tightening the bbox
SCORE_MIN = 0.55            # below this -> found = False.  MEASURED over all
                            # 152 pages of SH8601 the score is BIMODAL and the
                            # gap is empty: 134 pages score 0.917-0.981 and 18
                            # score 0.077-0.347, with nothing whatever between.
                            # The gate sits in that void, so its exact value
                            # decides nothing -- which is the only condition
                            # under which a single-number gate is honest.

# --- the alpha the fit minimises -------------------------------------------
# sheets600 has no alpha channel, so "not this page" is measured.  Outside the
# sheet is the near-black scanner bed and, further out, a saturated prop (yellow
# on one side of the bed, red on the other -- BOTH, which is why saturation and
# not a yellow test).  Ink INSIDE the page is dark too, so a bare threshold
# would count black type as unknown and push the window away from the type; the
# component test is what separates them -- unknown is what is dark-or-saturated
# AND connected to the frame border.
BED_LUM = 70                # 0-255 mean channel
BED_SAT = 60                # max channel - min channel
MASK_REDUCE = 4             # the mask is built at 150 dpi; the objective's own
                            # granularity is DS below, four times coarser again
DS = 8                      # search granularity, px @600 dpi (8 px = 0.34 mm)

# --- the search ------------------------------------------------------------
# S spans the FULL page width.  Read the module docstring before narrowing it.
S_RANGE = (0, A4_W, DS)
# B is the anchor's distance from the window's TOP edge.  The wordmark sits in
# the bottom ~7 % of the page, so B is necessarily close to A4_H; the range is
# still wide enough that the optimum is interior, and it is asserted to be.
B_RANGE = (A4_H - 800, A4_H, DS)

# --- the fallbacks ---------------------------------------------------------
# Order, as the rule records it for this chain:
#   1  logo          the anchor proper
#   2  paper-edge    a body page whose wordmark was not detected
#   3  traced-edge   a page that carries no wordmark at all -- the cover leaf
#                    and the bound-in Zahlkarte, which are not body pages
# 2 and 3 place the window from the page's own measured box: centred, which is
# what this chain's delivery already did.  The one exception is a page box WIDER
# than A4 -- the cover leaf with its fold flap -- where centring would trim the
# flap off both sides.  The flap is on the BINDING side, and step 005 measures
# that side from parity (a verso tears on the right, a recto on the left), so
# the trim is taken there and the outer trim is kept flush.
SRC_LOGO = "logo"
SRC_PAPER = "paper-edge"
SRC_TRACED = "traced-edge"

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

ISS = r000_issue.load(ISSUE)
SHEETS = Path(ISS.tmp) / "sheets600"
# Read for its STAMP only, never for its pixels: step 005 records `sheet-box`
# (the traced page in the sheet frame) and `edge-finder` (which of the two edge
# finders traced it), and both are answers this step would otherwise have to
# guess at.  See sheet_box_of().
MASTERS = Path(ISS.masters600)
OUT_A4 = Path(ISS.tmp) / "a4600"
# The measurement cache: one record per page, MERGED never replaced.
CACHE = Path(ISS.tmp) / "a4win"
OUT_OVERLAY = CACHE / "preview"

JOBS = 6

# ---------------------------------------------------------------------------
# DETECTION
# ---------------------------------------------------------------------------


def _rot(t, ang):
    h, w = t.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    return cv2.warpAffine(t, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def _match(region, tmpl, angles):
    """Best TM_CCOEFF_NORMED match of tmpl over `angles`; (score, x, y, angle)."""
    best = (-2.0, 0, 0, 0.0)
    if region.shape[0] < tmpl.shape[0] + 2 or region.shape[1] < tmpl.shape[1] + 2:
        return best
    for a in angles:
        t = _rot(tmpl, a) if a else tmpl
        res = cv2.matchTemplate(region, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), int(loc[0]), int(loc[1]), float(a))
    return best


def _tight_bbox(gray, x0, y0, x1, y1):
    """Shrink the matched footprint onto the ink actually in it."""
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(gray.shape[1], x1), min(gray.shape[0], y1)
    sub = gray[y0:y1, x0:x1]
    dark = sub < INK_THRESH
    ys = np.where(dark.sum(1) > 2)[0]
    xs = np.where(dark.sum(0) > 2)[0]
    if not len(ys) or not len(xs):
        return None
    return (x0 + int(xs.min()), y0 + int(ys.min()),
            x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)


def detect(gray, tmpl):
    """Find the wordmark in either bottom corner of a LEVELLED 600 dpi sheet.

    Returns (found, side, score, angle, bbox) with bbox in sheet pixels.  Both
    corners are searched and the better score wins: the corner is EVIDENCE about
    the page, not an assumption from its number, so a mis-filed or mis-rotated
    sheet shows up as a parity disagreement instead of a silently wrong window.
    """
    H, W = gray.shape
    tmpl_c = cv2.resize(tmpl, (tmpl.shape[1] // COARSE_REDUCE,
                               tmpl.shape[0] // COARSE_REDUCE),
                        interpolation=cv2.INTER_AREA)
    y0b, y1b = H - BAND_TOP_FROM_BOTTOM, H - BAND_BOT_FROM_BOTTOM
    coarse = {}
    small = cv2.resize(gray, (W // COARSE_REDUCE, H // COARSE_REDUCE),
                       interpolation=cv2.INTER_AREA)
    hs, ws = small.shape
    for side in ("L", "R"):
        x0 = 0 if side == "L" else int(ws * (1 - CORNER_FRAC))
        x1 = int(ws * CORNER_FRAC) if side == "L" else ws
        reg = small[y0b // COARSE_REDUCE:y1b // COARSE_REDUCE, x0:x1]
        sc, mx, my, _a = _match(reg, tmpl_c, (0.0,))
        coarse[side] = (sc, (x0 + mx) * COARSE_REDUCE,
                        y0b + my * COARSE_REDUCE)

    side = max(coarse, key=lambda k: coarse[k][0])
    _sc, cx, cy = coarse[side]
    th, tw = tmpl.shape
    rx0, ry0 = max(0, cx - REFINE_PAD), max(0, cy - REFINE_PAD)
    rx1, ry1 = min(W, cx + tw + REFINE_PAD), min(H, cy + th + REFINE_PAD)
    sc, mx, my, ang = _match(gray[ry0:ry1, rx0:rx1], tmpl, MATCH_ANGLES)
    tx, ty = rx0 + mx, ry0 + my
    bbox = _tight_bbox(gray, tx, ty, tx + tw, ty + th) or (tx, ty, tx + tw, ty + th)
    return (sc >= SCORE_MIN, side, sc, ang, list(bbox))


def anchor_of(side, bbox):
    """The bbox corner the window is hung from: the FOOT, on the wordmark's side.

    Which corner is arbitrary as long as it is the same one on every page of a
    parity -- the offsets are fitted to whatever it is.  The foot corner is the
    original's choice and it is the sensible one: the wordmark's baseline is the
    least ambiguous edge of a drop-shadowed glyph.
    """
    x0, y0, x1, y1 = bbox
    return ([x0, y1] if side == "L" else [x1, y1])


# ---------------------------------------------------------------------------
# THE PAGE, AND WHAT IS NOT THE PAGE
# ---------------------------------------------------------------------------


def page_mask(rgb_small):
    """True where the 150 dpi sheet is this page; False for bed, prop, off-sheet.

    Dark-or-saturated pixels CONNECTED TO THE FRAME BORDER are outside.  The
    connectivity is the whole point: black type and a full-bleed dark ground are
    just as dark as the bed, and a bare threshold would count them as unknown
    and push the window off the type it is supposed to be registered to.

    It has a known failure and it is not hidden: on a page whose own ink runs to
    the trim -- the cover, p117's dark-ground ad -- the ink bridges to the bed
    and the component test eats the page.  Those are exactly the pages that
    carry no wordmark and take a fallback, and the fallback measures the page
    box from step 005's trace instead.  The measured page fraction is recorded
    per page so a bridge is visible rather than inferred.
    """
    a = rgb_small.astype(np.int16)
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    bed = (lum < BED_LUM) | (sat > BED_SAT)
    lab, _n = ND.label(bed)
    edge = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    edge.discard(0)
    if not edge:
        return np.ones(lum.shape, bool)
    return ~np.isin(lab, np.array(sorted(edge)))


def integral_of(page150):
    """Summed-area table of UNKNOWN pixels on the DS grid.

    The search costs ~78k offset pairs per page; four lookups each instead of a
    slice-and-sum is the difference between seconds and an afternoon.  A coarse
    cell counts as unknown if ANY source pixel in it is -- the pessimistic
    direction, so the fit cannot buy a low number by averaging a bad border away.
    """
    step = DS // MASK_REDUCE
    unk = ~page150
    h, w = unk.shape[0] // step, unk.shape[1] // step
    ds = unk[:h * step, :w * step].reshape(h, step, w, step).any((1, 3))
    ii = np.cumsum(np.cumsum(ds.astype(np.int32), 0), 1)
    return np.pad(ii, ((1, 0), (1, 0))), (h, w)


def alpha_at(entry, x0, y0):
    """Unknown COARSE cells in the A4 window whose top-left is (x0, y0) @600 dpi.

    Area falling OFF THE FRAME counts as unknown too -- it is exactly as unknown
    as the bed is, and not counting it is how a search learns to walk off the
    page.
    """
    ii, (h, w) = entry
    cx0, cy0 = int(round(x0 / DS)), int(round(y0 / DS))
    cx1, cy1 = cx0 + A4_W // DS, cy0 + A4_H // DS
    ax0, ay0 = max(cx0, 0), max(cy0, 0)
    ax1, ay1 = min(cx1, w), min(cy1, h)
    if ax1 <= ax0 or ay1 <= ay0:
        return (A4_W // DS) * (A4_H // DS)
    inside = int(ii[ay1, ax1] - ii[ay0, ax1] - ii[ay1, ax0] + ii[ay0, ax0])
    off = (cx1 - cx0) * (cy1 - cy0) - (ax1 - ax0) * (ay1 - ay0)
    return inside + off


CELLS = (A4_W // DS) * (A4_H // DS)


# ---------------------------------------------------------------------------
# MEASURE ONE PAGE
# ---------------------------------------------------------------------------


def sheet_box_of(page, gray):
    """Step 005's traced page box, IN THE SHEET FRAME, and which finder made it.

    Read from the master's stamp, where step 005 writes it.  A master rendered
    before step 005 recorded `sheet-box` is MIGRATED here instead of guessed at:
    the master is the sheet's own pixels moved to the canvas origin, so a patch
    of it locates itself in the sheet exactly -- 0.995-1.000 on every page of
    SH8601.  This branch exists only for masters that predate the field and can
    go once no such master is left.
    """
    st = (MASTERS / f"{page:03d}.stamp.txt").read_text(encoding="utf-8")
    finder = "ink/bed" if "ink/bed" in st else "paper/bed"
    m = re.search(r"sheet-box\s+(\d+) (\d+) (\d+) (\d+)", st)
    if m:
        return [int(v) for v in m.groups()], finder, 1.0
    pw, ph = (int(v) for v in
              re.search(r"page-px\s+(\d+) (\d+)", st).groups())
    mg = np.asarray(Image.open(MASTERS / f"{page:03d}.png").convert("L"))[:ph, :pw]
    cy, cx = ph // 2, pw // 2
    pat = mg[cy - 256:cy + 256, cx - 256:cx + 256]
    _n, sc, _n2, loc = cv2.minMaxLoc(
        cv2.matchTemplate(gray, pat, cv2.TM_CCOEFF_NORMED))
    x0, y0 = loc[0] - (cx - 256), loc[1] - (cy - 256)
    return [int(x0), int(y0), int(x0 + pw), int(y0 + ph)], finder, float(sc)


def measure(page):
    """Detect the wordmark and measure the page, from ONE read of the sheet."""
    src = SHEETS / f"{page:03d}.png"
    im = Image.open(src).convert("RGB")
    W, H = im.size
    gray = np.asarray(im.convert("L"))
    tmpl = np.asarray(Image.open(TEMPLATE).convert("L"))
    found, side, score, ang, bbox = detect(gray, tmpl)
    box, finder, box_sc = sheet_box_of(page, gray)

    small = np.asarray(im.reduce(MASK_REDUCE))
    pm = page_mask(small)
    ii, shp = integral_of(pm)
    rec = {"page": page, "frame": [W, H], "found": bool(found), "side": side,
           "score": round(float(score), 4), "angle": ang, "bbox": bbox,
           "anchor": anchor_of(side, bbox), "finder": finder,
           "page_frac": round(float(pm.mean()), 4), "sheet_box": box,
           "sheet_box_match": round(box_sc, 5)}
    np.savez_compressed(CACHE / f"{page:03d}.npz", ii=ii, shp=np.array(shp))
    return rec


def load_entry(page):
    z = np.load(CACHE / f"{page:03d}.npz")
    return z["ii"], tuple(int(v) for v in z["shp"])


# ---------------------------------------------------------------------------
# THE FIT
# ---------------------------------------------------------------------------


def fit(recs, entries):
    """One rigid (S, B) per parity, over the pages that have their OWN logo."""
    out = {}
    for par in ("even", "odd"):
        g = [r for r in recs
             if r["found"] and (r["page"] % 2 == 0) == (par == "even")]
        if not g:
            continue
        A = [(entries[r["page"]], r["anchor"]) for r in g]
        best = None
        for S in range(*S_RANGE):
            for B in range(*B_RANGE):
                v = 0
                for e, (ax, ay) in A:
                    v += alpha_at(e, ax - S, ay - B)
                if best is None or v < best[0]:
                    best = (v, S, B)
        _v, S, B = best
        # THE TRAP.  An optimum sitting on its own search boundary is not an
        # optimum, it is the edge of the box -- and that is precisely how the
        # original got 71 % alpha out of a search that reported success.
        if S <= S_RANGE[0] or S >= S_RANGE[1] - S_RANGE[2]:
            raise SystemExit(f"r005b: {par} S={S} is ON the boundary of "
                             f"{S_RANGE} -- widen the range, do not accept it")
        if B <= B_RANGE[0] or B >= B_RANGE[1] - B_RANGE[2]:
            raise SystemExit(f"r005b: {par} B={B} is ON the boundary of "
                             f"{B_RANGE} -- widen the range, do not accept it")
        v = np.array([100.0 * alpha_at(e, ax - S, ay - B) / CELLS
                      for e, (ax, ay) in A])
        out[par] = {"S": S, "B": B, "n": len(g),
                    "alpha_mean": round(float(v.mean()), 4),
                    "alpha_p50": round(float(np.percentile(v, 50)), 4),
                    "alpha_p95": round(float(np.percentile(v, 95)), 4),
                    "alpha_max": round(float(v.max()), 4)}
    return out


def place(rec, off, entry):
    """The window for one page, and which of the three fallbacks put it there."""
    page = rec["page"]
    par = "even" if page % 2 == 0 else "odd"
    if rec["found"] and par in off:
        ax, ay = rec["anchor"]
        x0, y0 = ax - off[par]["S"], ay - off[par]["B"]
        src = SRC_LOGO
    else:
        # No wordmark on this page.  Place from step 005's traced box for THIS
        # page -- measured on this sheet, so it carries no neighbour's error --
        # centred in the window, which is what this chain's delivery already
        # did with it.  Fallback 2 and fallback 3 are the same arithmetic on a
        # box found two different ways, and the LABEL is the difference: which
        # of step 005's two edge finders traced it says whether this is a body
        # page whose wordmark was missed (paper/bed) or a page that has no
        # wordmark to miss (ink/bed -- the cover leaf, the bound-in card).
        # THE ONE POINT WHERE THE RULE SAYS TWO THINGS.  r005_a4_window.md also
        # says a page with no detected logo gets "an anchor interpolated across
        # same-parity neighbours, marked as interpolated" -- a sentence carried
        # over from the original's README, where it is STALE: the original's
        # fit_window.py does not interpolate either, it places its no-logo pages
        # from the measured spine, and says in as many words that "an
        # interpolated logo anchor carried its neighbours' error into both
        # axes".  The fallback ORDER above is the newer statement and the one
        # the rule attributes to the issue owner, so it is what runs here.
        # MEASURED both ways on SH8601's 10 such pages: the two windows differ
        # by up to 160 px (6.8 mm), and the type-area probe cannot tell them
        # apart -- those pages are full-page ads whose layout is not the body
        # grid.  The choice is therefore recorded, not settled by this code.
        bx0, by0, bx1, by1 = rec["sheet_box"]
        bw, bh = bx1 - bx0, by1 - by0
        if bw > A4_W:
            # Wider than A4: the surplus is the cover leaf's fold flap, which
            # is on the BINDING side -- a verso is bound on the right, a recto
            # on the left.  Trim it there and keep the outer trim flush;
            # centring would take half the flap off the printed outer edge.
            x0 = bx0 if page % 2 else bx1 - A4_W
        else:
            x0 = bx0 - (A4_W - bw) // 2
        y0 = by0 - (A4_H - bh) // 2
        src = SRC_TRACED if rec["finder"] == "ink/bed" else SRC_PAPER
    a = alpha_at(entry, x0, y0)
    return {"x0": int(x0), "y0": int(y0), "w": A4_W, "h": A4_H,
            "src": src, "anchor": rec["anchor"] if rec["found"] else None,
            "score": rec["score"], "side": rec["side"],
            "alpha_pct": round(100.0 * a / CELLS, 4)}


# ---------------------------------------------------------------------------
# CUT
# ---------------------------------------------------------------------------


def cut(page, win, rec, out_dir=None):
    """Write the A4 page.  EXACTLY A4, and the window is NEVER clamped.

    THE PIXELS COME FROM THE MASTER, not from the sheet, and the window is
    translated into the master's frame by step 005's `sheet-box`.  The master is
    the same sheet with step 005's decision about what is page already applied:
    everything outside the traced edge is fabricated paper white.  Cutting from
    the sheet instead would deliver the scanner bed inside the A4 page wherever
    the window reaches past the trim -- which it does, by design, since A4 does
    not fit -- and would mean this step re-deciding, worse, a question 005 has
    already answered with a fitted line per edge.

    So there are two frames and one translation between them.  The window is
    FITTED in the sheet frame, because that is the frame the wordmark and the
    paper edge are both visible in; it is APPLIED in the master frame, because
    that is where the fill lives.

    Where the window reaches past the master canvas the output is paper white
    for the same reason and by the same fabrication.  Clamping the window to
    fit instead would shift the content by however far it had to move and
    destroy the one property this whole step exists to provide.
    """
    out_dir = Path(out_dir or OUT_A4)
    out_dir.mkdir(parents=True, exist_ok=True)
    src = np.asarray(Image.open(MASTERS / f"{page:03d}.png").convert("RGB"))
    H, W = src.shape[:2]
    bx0, by0 = rec["sheet_box"][0], rec["sheet_box"][1]
    out = np.full((A4_H, A4_W, 3), 255, np.uint8)
    x0, y0 = win["x0"] - bx0, win["y0"] - by0          # sheet frame -> master
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + A4_W, W), min(y0 + A4_H, H)
    off = A4_W * A4_H
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        off = A4_W * A4_H - (sx1 - sx0) * (sy1 - sy0)
    # What is FABRICATED: the part of the window that is not inside step 005's
    # traced page.  Not "how white is it" -- most of a text page is white paper
    # and that number says nothing.  Measured against the traced page's BOX, so
    # it is a lower bound: the wedges between the box and the fitted edge lines
    # are fabricated too, and `alpha` above is the measure that includes them.
    bw, bh = rec["sheet_box"][2] - bx0, rec["sheet_box"][3] - by0
    ix = max(0, min(x0 + A4_W, bw) - max(x0, 0))
    iy = max(0, min(y0 + A4_H, bh) - max(y0, 0))
    fab = 1.0 - (ix * iy) / float(A4_W * A4_H)
    meta = PngImagePlugin.PngInfo()
    stamp = (f"r005b a4_window  page {page:03d} of {ISSUE}\n"
             f"  anchor   {win['src']}"
             + (f" at {win['anchor']} in the sheet (corner {win['side']}, "
                f"template score {win['score']:.3f})" if win["anchor"] else
                f" -- no wordmark on this page; the best corner match was "
                f"{win['side']} at {win['score']:.3f}")
             + f"\n  window   {win['x0']} {win['y0']} {A4_W} {A4_H}  in the sheet"
               f"\n           {x0} {y0} {A4_W} {A4_H}  in the master"
               f"\n  alpha    {win['alpha_pct']:.2f}% of the window is not this "
               f"page (bed, prop, off-frame)"
               f"\n  fabricated {100.0 * fab:.2f}% of the delivered page lies "
               f"outside the traced page, of which "
               f"{100.0 * off / (A4_W * A4_H):.2f}% is off the master canvas\n")
    meta.add_text("r005b", stamp)
    Image.fromarray(out).save(out_dir / f"{page:03d}.png", pnginfo=meta,
                              dpi=(DPI, DPI))
    (out_dir / f"{page:03d}.stamp.txt").write_text(stamp, encoding="utf-8")
    return {"page": page, "src": win["src"], "fab_pct": round(100.0 * fab, 3),
            "offcanvas_pct": round(100.0 * off / (A4_W * A4_H), 3),
            "alpha_pct": win["alpha_pct"]}


def overlay(page, win, out_dir=None):
    """The window and the anchor drawn on the sheet, for a human to look at.

    green = own logo, blue = paper-edge, orange = traced-edge, magenta = anchor.
    Drawn OPAQUE so the line stays visible exactly where it matters -- where the
    window leaves the paper.
    """
    out_dir = Path(out_dir or OUT_OVERLAY)
    out_dir.mkdir(parents=True, exist_ok=True)
    a = np.asarray(Image.open(SHEETS / f"{page:03d}.png").convert("RGB")).copy()
    H, W = a.shape[:2]
    col = {SRC_LOGO: (0, 200, 0), SRC_PAPER: (40, 120, 255),
           SRC_TRACED: (255, 140, 0)}[win["src"]]

    def paint(y0, y1, x0, x1, c):
        y0, y1 = max(int(y0), 0), min(int(y1), H)
        x0, x1 = max(int(x0), 0), min(int(x1), W)
        if y1 > y0 and x1 > x0:
            a[y0:y1, x0:x1] = c

    if win["anchor"]:
        ax, ay = win["anchor"]
        paint(ay - 3, ay + 4, ax - 60, ax + 61, (255, 0, 255))
        paint(ay - 60, ay + 61, ax - 3, ax + 4, (255, 0, 255))
    x0, y0 = win["x0"], win["y0"]
    x1, y1 = x0 + A4_W, y0 + A4_H
    L = 6
    paint(y0, y0 + L, x0, x1, col)
    paint(y1 - L, y1, x0, x1, col)
    paint(y0, y1, x0, x0 + L, col)
    paint(y0, y1, x1 - L, x1, col)
    Image.fromarray(a).reduce(4).save(out_dir / f"{page:03d}.png")


# ---------------------------------------------------------------------------


def _measure_one(p):
    try:
        return measure(p)
    except FileNotFoundError:
        return None


def main():
    pages = [int(a) for a in sys.argv[1:]]
    all_pages = [p for p in ISS.page_range if (SHEETS / f"{p:03d}.png").exists()]
    CACHE.mkdir(parents=True, exist_ok=True)

    # MEASURE EVERY PAGE, always.  Merged into the cache, never replacing it.
    recs = {}
    cache_json = CACHE / "measured.json"
    if cache_json.exists():
        recs = {r["page"]: r for r in json.load(open(cache_json))}
    todo = [p for p in all_pages if p not in recs
            or not (CACHE / f"{p:03d}.npz").exists()]
    if todo:
        print(f"r005b: measuring {len(todo)} page(s) ...", flush=True)
        with Pool(JOBS) as pool:
            for r in pool.imap_unordered(_measure_one, todo):
                if r:
                    recs[r["page"]] = r
                    print("  p%03d %s score %.3f %s" % (
                        r["page"], r["side"], r["score"],
                        "" if r["found"] else "<-- NOT FOUND"), flush=True)
        json.dump([recs[k] for k in sorted(recs)], open(cache_json, "w"), indent=1)

    order = [recs[p] for p in all_pages]
    entries = {p: load_entry(p) for p in all_pages}

    off = fit(order, entries)
    for par, o in off.items():
        print("%-5s n=%3d  S=%4d B=%4d   alpha in window: mean %.3f%%  "
              "p50 %.3f  p95 %.3f  max %.3f" % (
                  par, o["n"], o["S"], o["B"], o["alpha_mean"],
                  o["alpha_p50"], o["alpha_p95"], o["alpha_max"]), flush=True)

    wins = {r["page"]: place(r, off, entries[r["page"]]) for r in order}
    OUT_A4.mkdir(parents=True, exist_ok=True)
    json.dump({"A4": [A4_W, A4_H], "offsets": off,
               "windows": {str(k): v for k, v in sorted(wins.items())}},
              open(CACHE / "a4_windows.json", "w"), indent=1)

    from collections import Counter
    print("windows: " + "  ".join("%s %d" % (k, v) for k, v in
                                  sorted(Counter(w["src"] for w in wins.values()).items())))
    done = []
    for p in (pages or all_pages):
        r = cut(p, wins[p], recs[p])
        overlay(p, wins[p])
        done.append(r)
        print("p%03d %-11s alpha %5.2f%%  fabricated %5.2f%%  (off-canvas %.2f%%)"
              % (p, r["src"], r["alpha_pct"], r["fab_pct"],
                 r["offcanvas_pct"]), flush=True)
    for lab in (SRC_LOGO, SRC_PAPER, SRC_TRACED):
        g = [r["fab_pct"] for r in done if r["src"] == lab]
        if g:
            print("  %-12s n=%3d  fabricated p50 %.2f%%  p95 %.2f%%  max %.2f%%"
                  % (lab, len(g), np.percentile(g, 50), np.percentile(g, 95),
                     max(g)))


if __name__ == "__main__":
    main()
