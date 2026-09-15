#!/usr/bin/env python3
"""
Step 005, SPREAD variant -- raw 2400 dpi scan -> the 600 dpi masters r010 reads.

    r005_masters_spread   the frame holds a clipped SPREAD  (8610, the monthlies)  <- this file
    r005_masters_sheet    the frame holds one loose SHEET   (SH8601)

The suffix NAMES THE VARIANT; exactly one runs per issue (see r005_masters_sheet
for why that is not a `9b`).  Both write <tmp>/masters600/NNN.png.

What this variant is for.  The monthly was disbound into A3 SHEETS, held in a
rigid 6-hole binder clip, and each sheet was scanned twice, one A4 half per
frame with some overlap.  MEASURED on 8610's 150 dpi thumbs:

    top          a grey bed strip, lum ~130-185 -- NOT the near-black bed of
                 SH8601; the paper-distance mask sees it, BED_LUM would not
    bottom       the yellow prop, ~7 mm deep
    outer side   usually OFF-FRAME: the paper runs to the frame edge
    inner side   the FOLD, then the neighbour half of the same sheet -- blank
                 margin on some pages, its content on others
    on the fold  6 clip holes, 3 vertical pairs: dark teardrops 0.42-1.06 mm
                 across the crease and up to 2.84 mm along it (MEASURED on
                 p100/p101's sheets600)

Even page -> neighbour on the RIGHT, odd -> LEFT.  Sheet pairing is k <-> 201-k.

Why the master is anchored on the PRINTED WORDMARK and not on the paper: the
outer trim is often not in the frame, and print-to-trim registration varies,
so a trace-based page box would align the paper and misalign the type.  The
"64'er" wordmark is print-registered to the content, is the same glyph on
every page, and sits in the outer-bottom corner.  8609's masters were made
this way and the corpus was measured on them.

Two phases, because the window offsets are an ISSUE-WIDE fit:

    measure [pages..]   per page, heavy: level at 2400, grade, then measure the
                        geometry on the levelled 600 dpi sheet -> geometry/NNN.json
    cut                 issue-wide: fit ONE (S, B) per parity over the pages
                        that have their own logo, then cut every master off
                        sheets600 with paper-white fills -> masters600/NNN.png

`measure` is what a change to the grade or the finders re-runs; `cut` is
seconds a page and is re-run alone after a change to the fit or the fills.
Page numbers are positional so the work can be split across processes.  No
flags, no env knobs.
"""

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ND
from scipy.signal import fftconvolve

from r005_masters import (
    HERE, ISSUE, ISS, MM, SCAN_REDUCE, MASTER_DPI, THUMB_DPI,
    SKEW_RESIDUAL_MAX, CLEAN_PCT, TRACE_BANDS, BODY_PAPER_FRAC,
    DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP,
    ANCHORS, LEVELS, HAVE_PROFILE, GRADE_SHA,
    PageFailed, measure_skew,
    separate_and_render, archive_cmyk, save_master, write_profile, stamp_text,
    paper_mask, prop_mask, boundaries, trace, tilt,
)

Image.MAX_IMAGE_PIXELS = None

VARIANT = "r005_masters_spread"
BINDING = "spread"

# --- the master ------------------------------------------------------------
# Exactly A4 at 600 dpi, every page, anchored on the wordmark (see the module
# docstring).  4961 x 7016.  8609's masters are 4960 x 7015 because they were
# reduced 4:1 from an odd-sized 2400 window; one pixel is 0.04 mm and r010's
# geometry is fractional, so the two issues share a coordinate system to
# within that.
A4_W_MM, A4_H_MM = 210.0, 297.0
MASTER_W_PX = int(round(A4_W_MM * MM))       # 4961
MASTER_H_PX = int(round(A4_H_MM * MM))       # 7016

# ---------------------------------------------------------------------------
# The issue descriptor
# ---------------------------------------------------------------------------
if ISS.binding != BINDING:
    raise SystemExit(
        f"{VARIANT}: {ISSUE} has binding={ISS.binding!r}, not {BINDING!r}. "
        f"This issue belongs to r005_masters_sheet. Record this variant in its "
        f"LOG.md as not applicable rather than forcing it.")

SCAN_DIR = Path(ISS.scan_dir)
THUMB_DIR = Path(ISS.thumb_150)
OUT_MASTER = Path(ISS.masters600)
OUT_SHEET = Path(ISS.tmp) / "masters2400"
OUT_SHEET600 = Path(ISS.tmp) / "sheets600"
OUT_CMYK = Path(ISS.tmp) / "cmyk2400"
OUT_GEOM = Path(ISS.tmp) / "geometry"
OUT_DEBUG = Path(ISS.tmp) / "debug600"
OUT_DIRS = (OUT_MASTER, OUT_SHEET, OUT_SHEET600, OUT_CMYK, OUT_GEOM, OUT_DEBUG)


def parity(page):
    """'even' or 'odd'.  Even -> neighbour on the RIGHT, odd -> LEFT."""
    return "even" if page % 2 == 0 else "odd"


# --- the three outer edges -------------------------------------------------
# Top, bottom and the OUTER side are paper-vs-backing boundaries and are traced
# exactly as the sheet variant traces a clean edge: band medians of the
# per-row / per-column first and last paper pixel, a straight line through the
# bands.  Backing is whatever the paper mask does not see -- the grey bed strip
# at the top (lum ~130-185, MEASURED on 8610's thumbs; the paper-distance mask
# sees it at city-block ~200 from W, BED_LUM would not) and the yellow prop at
# the foot (prop_mask).  Where the paper runs off the frame the samples are a
# constant 0 (or w-1) and the line is the frame edge: the scan does not
# contain the trim, and the window -- not this trace -- decides the page.
#
# A FULL-BLEED page has no paper for the mask to see, and a page is never
# refused: the covers are art to the trim.  MEASURED, the fraction of rows /
# columns whose paper fraction passes BODY_PAPER_FRAC, the smaller of the two
# (8610's thumbs; the mask is colour-only, so the scale is immaterial):
#
#     p001 0.023   p200 0.005      the two covers -- p200's trace raised
#     p010 0.879   p011 0.872      "12 usable edge samples for 24 bands", p001
#     p100 0.414   p101 0.724      traced its title band as the "top" at 67 mm
#
# Below FULLBLEED_BODY_FRAC (or if a trace still raises above it) the frame
# is the edge on top and outside, and the bottom is the PROP's top boundary,
# which prop_mask sees on any page: per column, its first prop row in the
# foot of the frame.  The source is returned so the JSON and the overlay say
# which case this was.
#
# The INNER side is NOT traced here.  The neighbour half of the sheet is paper
# too, and the paper mask cannot see the fold.  See fit_fold() (the clip
# holes) and neighbour_boundary() (the fallback).
EDGE_INSET_MM = 0.3          # inside its own line, as the sheet variant
FULLBLEED_BODY_FRAC = 0.15   # in the gap between 0.023 (p001) and 0.414 (p100)
# A page that is NOT full-bleed can still carry ink to the trim on one side,
# and there the paper trace follows the ink's inner boundary, not the trim.
# MEASURED on the full 8610 sweep: p027 (a purple ad ground) traced its top
# 27.2 mm down and its bottom 15.7 mm up at -4.05 deg; p092 (a red band at
# the top of a 0.80-paper page) its top 15.2 mm down at +2.49 deg; p149 (a
# black column) its outer edge 13.5 mm in at +0.96 deg; p177 its bottom 16.4
# mm up at -5.97 deg; p057 its outer edge at -1.49 deg into a photo -- and
# the masters were painted white there.  The body fraction cannot see this
# (p092 is 0.80 paper).  The FRAME can: it is 304.3 mm high for 297 of page
# and 7 of prop, so on the 195 sound pages the top trim sits 0-1.1 mm below
# the frame's top, the bottom 6.4-9.4 mm above its foot, the outer trim
# 0-5.7 mm in (the frame's slack over A4 beyond the fold is at most 8 mm),
# and no sound edge tilts more than 0.82 deg on a levelled page.  A traced
# edge beyond those is ink, and that edge alone -- not the page -- takes the
# full-bleed line (the frame row / column, the prop's top), NOTEd, with the
# other two traces kept.
EDGE_TOP_MAX_MM = 3.0        # traced top further below the frame's top than this: ink
EDGE_BOT_MAX_MM = 12.0       # traced bottom further above the frame's foot than this: ink
EDGE_OUTER_MAX_MM = 8.0      # traced outer edge further into the frame than this: ink
EDGE_TILT_MAX = 1.0          # deg; a levelled page's trim is level
PROP_FOOT_MM = 15.0          # the prop's top is looked for this far up from the foot
PROP_AT_FOOT_MM = 2.0        # ...in columns whose prop starts within this of it


def prop_top(rgb):
    """The prop's top boundary as a line y(x), or None if too few columns see it.

    Per column, the top of the prop RUN THAT TOUCHES THE FOOT -- not the first
    prop-coloured row in the foot: MEASURED on p001, the cover's orange banner
    sits inside the foot and pulled the first-row line 4.7 mm up on the left.
    The run may start a few rows above the frame's last row, which is black
    where the levelling rotation left a wedge.
    """
    h, w = rgb.shape[:2]
    foot = prop_mask(rgb[h - int(PROP_FOOT_MM * MM):])[::-1]     # row 0 = the foot
    first = np.argmax(foot, axis=0)                              # first prop row up
    cols = np.where(foot.any(0) & (first <= PROP_AT_FOOT_MM * MM))[0]
    if len(cols) < TRACE_BANDS:
        return None
    tops = np.empty(len(cols))
    for k, c in enumerate(cols):
        run = foot[first[c]:, c]
        end = first[c] + (int(np.argmin(run)) if not run.all() else len(run))
        tops[k] = h - end                                        # first non-prop row
    try:
        return trace(tops, cols.astype(float), CLEAN_PCT, MM)
    except PageFailed:
        return None


def outer_edges(rgb, par):
    """dict(top, bot, outer, source, body): straight lines in 600 dpi sheet pixels.

    top/bot are y(x); outer is x(y).  Parity says which side is outer: an even
    page's neighbour is on the right, so its outer edge is the LEFT one.
    source is "paper" (traced) or "fullbleed" (frame + prop, see above); body
    is the measured paper body fraction either way.
    """
    mask = paper_mask(rgb)
    h, w = mask.shape
    body = float(min((mask.mean(1) > BODY_PAPER_FRAC).mean(),
                     (mask.mean(0) > BODY_PAPER_FRAC).mean()))
    frame = {"top": np.array([0.0, 0.0]),
             "outer": np.array([0.0, 0.0 if par == "even" else w - 1.0])}
    if body >= FULLBLEED_BODY_FRAC:
        try:
            rows, starts, ends, cols, tops, bots = boundaries(mask)
            e = {"top": trace(tops, cols, CLEAN_PCT, MM),
                 "bot": trace(bots, cols, CLEAN_PCT, MM),
                 "outer": trace(starts if par == "even" else ends, rows, CLEAN_PCT, MM),
                 "source": "paper", "body": body, "replaced": []}
            # each edge against the frame: how far in, and how tilted
            top_in = np.polyval(e["top"], w / 2) / MM
            bot_in = (h - 1 - np.polyval(e["bot"], w / 2)) / MM
            ox = np.polyval(e["outer"], h / 2)
            outer_in = (ox if par == "even" else w - 1 - ox) / MM
            for key, depth, limit in (("top", top_in, EDGE_TOP_MAX_MM),
                                      ("bot", bot_in, EDGE_BOT_MAX_MM),
                                      ("outer", outer_in, EDGE_OUTER_MAX_MM)):
                t = tilt(e[key])
                if depth > limit or abs(t) > EDGE_TILT_MAX:
                    e["replaced"].append([key, float(depth), float(t)])
                    if key == "bot":
                        pt = prop_top(rgb)
                        e["bot"] = np.array([0.0, h - 1.0]) if pt is None else pt
                    else:
                        e[key] = frame[key]
            return e
        except PageFailed:
            pass
    bot = prop_top(rgb)
    return {"top": frame["top"],
            "bot": np.array([0.0, h - 1.0]) if bot is None else bot,
            "outer": frame["outer"],
            "source": "fullbleed", "body": body, "replaced": []}


# --- the fold: the clip holes --------------------------------------------
# The sheet was held in a rigid 6-hole binder clip whose punches left DARK
# TEARDROPS on the fold, 3 vertical pairs.  They are the one physical mark of
# the fold that survives on every sheet, and they are on the SAME line as the
# crease (seen on p100 at thumb scale).  MEASURED on 8610's sheets600 (the
# graded 600 dpi sheet, paper ~230, the holes 16-31 at their darkest), p100
# and p101 -- the two halves of one sheet, so the same six holes twice:
#
#     where      8.3-10.5 mm in from the frame edge on p100, 10.1-12.2 on
#                p101 -- NOT the ~20 mm the thumbs suggested.  The nearest
#                type is 19.2 mm in on p100 (an ad column) and ~22 on p101.
#     size       0.42-1.06 mm ACROSS the crease, 0.51-2.84 mm ALONG it:
#                the punch tore the paper along the fold, and two of the
#                six are > 2 mm long.  Aspect up to 3.72.  Fill 0.51-0.71.
#     darkness   155-184 below the local surround.  NO gap to type: a digit
#                on white paper dips 165, so darkness cannot tell them apart
#                and the band must.
#
# The band is the whole argument.  At 30 mm it held 96 (p100) / 108 (p101)
# candidates, and a text column's left edge is as collinear as a clip: the
# fit locked on the column both times.  16 mm sits in the measured gap
# between the farthest hole (12.2) and the nearest type (19.2).  A fold
# beyond the band is a MISS (no line; the sweep reports it), not a wrong
# line -- the safe way round.
HOLE_BAND_MM = 16.0          # search this far in from the inner frame edge
HOLE_BG_MM = 3.5             # local-mean window for the contrast test
HOLE_DIP = 45                # a hole is this far below its local surround...
HOLE_ABS_MAX = 120           # ...and absolutely dark: a hole is a hole, not a tint
HOLE_MIN_MM = 0.4            # longest extent; the satellite specks are 0.17-0.38
HOLE_MAX_MM = 1.5            # ACROSS the crease (measured 0.42-1.06)
HOLE_LONG_MAX_MM = 4.0       # ALONG it (measured 0.51-2.84; next up is 16 mm)
HOLE_FILL_MIN = 0.40         # area / bbox: a teardrop, not a line fragment
HOLE_ASPECT_MAX = 4.5        # long/short: measured <= 3.72; a clipped printed rule reads 5.2+
# The line through them: at least this many holes, within this of the line,
# and near-vertical (the clip is rigid and the sheet is levelled).  The
# tolerance is ACROSS the crease, where a torn hole's centre of mass moves:
# MEASURED on the sweep, the four holes of p064, p083, p117 and p137 sit
# 0.8-0.9 mm apart across the line and no line held them at 0.5 mm (fold
# none on all four, two of them without a wordmark to place the window by);
# at 0.8 all four fit, no page moves more than 0.4 mm, and the template
# below -- not this tolerance -- is what keeps a text column out.
FOLD_TOL_MM = 0.8
FOLD_MIN_HOLES = 4
FOLD_TILT_MAX = 1.0          # deg
# WHICH line: the one that matches the clip's rigid 3-pair TEMPLATE, not the
# one with most holes.  MEASURED on the full 8610 sweep: with "most inliers
# wins" 25 of 200 pages locked on the NEIGHBOUR's justified column edge --
# the line-end hyphens, commas and letter fragments that the inner frame
# edge clips off, 0.4-3.7 mm in, hole-shaped and collinear to 0.1 mm, 15-152
# of them against six holes (p061 22 at 0.6 mm, p086 64 at 1.9, p189 50 at
# 2.3; the true holes on every one of those pages at 8.5-14.8 mm).  The six
# holes' y positions, over 75 pages where the six were the line's only
# inliers: gaps 13.35 / 76.27 / 13.30 / 66.44 / 13.59 mm, sd 0.14-0.19 mm,
# and no page's six deviate more than 0.41 mm (p95 0.30) from the template
# below once it is shifted onto them.  A line SCORES the template: for every
# "inlier k is hole j" hypothesis, how many of the six positions have an
# inlier within HOLE_TEMPLATE_TOL_MM, and the RMS of those offsets; the
# best hypothesis is the line's score.  Matches, then RMS, then inliers,
# then residual decide; under HOLE_TEMPLATE_MIN matches a line is not a
# fold.  Four matches replace the old half-height span rule: pairs 1+2 span
# 103 mm and are the clip (p092, p109, p124 -- their other holes are off
# the line or under type).
#
# WHAT THE TEMPLATE DOES AND DOES NOT TELL APART.  On 8610 a neighbour
# column fakes at most 5 matches, at RMS 0.31-0.45 (the six pages where it
# reaches 5: p084, 086, 091, 187, 189, 193); the holes score 6 there, and
# where only 5 holes are seen they fit at RMS <= 0.30 and win on RMS.  That
# 0.30-vs-0.31 margin is a fact about 8610's fragments -- line ends are
# ragged, so the column's y's are IRREGULAR and match the template only by
# chance -- not a property of the scorer.  A perfectly REGULAR column at
# body-text pitch is a different thing: the template's gaps (13.35, 76.27,
# 13.30, 66.44, 13.59) are near-multiples of some pitches, and a synthetic
# column alone at 4.5 mm pitch scores 4 at RMS 0.24, at 4.7 mm scores 6 at
# RMS 0.41; 8 of the 26 pitches from 3.5 to 6.0 mm pass HOLE_TEMPLATE_MIN
# (tests: the known-accepting case).  Where the holes are also seen it still
# loses on matches or RMS; alone -- the holes torn, inked over, or off the
# line -- it would be reported as the fold.  The test that would refuse it
# is a regularity test on the inliers' y spacing (a clip has six marks,
# type has a pitch), not built: no page of 8610 needed it.
#
# THE ABSOLUTE PRIOR.  The clip is one rigid object and it sat on the same
# stop of the scanner for every sheet: MEASURED over the 196 pages with a
# hole fold, the best template shift (hole 1's y in the frame) is 58.05-
# 59.97 mm on 192 of them (mean 58.91), and the four outside are the pages
# where it was arbitrary -- p005 / p038 / p163 (a screen or a cracked crease
# dense enough that any shift matches) and p084 (the fake, at 65.9).  So a
# hypothesis is only counted if its shift is within HOLE_TEMPLATE_Y0_TOL_MM
# of HOLE_TEMPLATE_Y0_MM: 3 mm is three times the measured spread, and a
# levelling rotation of 0.5 deg about the sheet's centre moves y at the fold
# by under 1 mm.  This kills a chance match (p084) and pins the dense pages'
# shift on their real holes; it does NOT kill a regular column, whose
# fitting shifts recur every pitch, so one always lands inside +-3 mm.  It
# is a fact about the operator's placement, re-measured per issue like the
# template; an issue whose clip sat elsewhere reports `fold none` on every
# page, and checks 5 and 8 say so.
HOLE_TEMPLATE_MM = (0.0, 13.35, 89.62, 102.92, 169.36, 182.95)
HOLE_TEMPLATE_TOL_MM = 0.75  # measured max 0.41, p95 0.30
HOLE_TEMPLATE_MIN = 4        # matches; 6 on an ordinary page, 4-5 with a torn or inked-over hole
HOLE_TEMPLATE_Y0_MM = 59.0   # hole 1's y in the frame: measured 58.05-59.97 (p5-p95), mean 58.91
HOLE_TEMPLATE_Y0_TOL_MM = 3.0
# WHICH inliers are the clip's punches, for the fill: those within this of a
# template position along the line.  An inlier elsewhere on the line is the
# crease -- a crack in the ink (p001: 25 inliers, 4 punches), a speck, or,
# on p005, the first dot column of a picture whose edge is the crease (205
# inliers, 19 punches; filling all 205 scalloped 530 mm2 off the picture's
# edge).  2 mm: a punch tore the paper up to 2.84 mm along the fold, so a
# fragment's centre sits within ~1.5 mm of it; the template itself is good
# to 0.41.
HOLE_FILL_NEAR_MM = 2.0


def find_holes(gray, par):
    """Hole-shaped dark blobs in the inner band: [(cx, cy, size_mm), ...].

    size_mm is the blob's longest extent.  A blob that touches either border
    of the band is not a candidate: it is cut off by the frame edge or by the
    band itself, so its size and centre are unknown.  MEASURED: on p101 the
    neighbour's screened boxes run to the frame edge and their clipped ends
    line up at x = 15 to a tenth of a millimetre, 15 of them -- a fold.
    """
    h, w = gray.shape
    band = int(HOLE_BAND_MM * MM)
    x0 = w - band if par == "even" else 0
    strip = gray[:, x0:x0 + band].astype(np.float32)
    local = ND.uniform_filter(strip, int(HOLE_BG_MM * MM) | 1)
    dark = (strip < local - HOLE_DIP) & (strip < HOLE_ABS_MAX)
    lab, n = ND.label(dark)
    holes = []
    for i, sl in enumerate(ND.find_objects(lab), 1):
        if sl is None:
            continue
        if sl[1].start == 0 or sl[1].stop == band:
            continue
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        d = max(hh, ww) / MM
        if d < HOLE_MIN_MM or ww / MM > HOLE_MAX_MM or hh / MM > HOLE_LONG_MAX_MM:
            continue
        if max(hh, ww) / max(min(hh, ww), 1) > HOLE_ASPECT_MAX:
            continue
        blob = lab[sl] == i
        if blob.sum() / (hh * ww) < HOLE_FILL_MIN:
            continue
        cy, cx = ND.center_of_mass(blob)
        holes.append((x0 + sl[1].start + cx, sl[0].start + cy, d))
    return holes


def template_score(ys):
    """(matches, rms_mm, shift_mm) of the clip template on the inlier y's (px):
    the best over every 'inlier k is template hole j' shift whose hole 1
    lands within HOLE_TEMPLATE_Y0_TOL_MM of HOLE_TEMPLATE_Y0_MM -- shift_mm
    is that hole 1's y; (0, 0.0, None) if no shift qualifies."""
    ys = np.sort(np.asarray(ys, float) / MM)
    t = np.asarray(HOLE_TEMPLATE_MM)
    shifts = (ys[:, None] - t[None, :]).ravel()
    shifts = shifts[np.abs(shifts - HOLE_TEMPLATE_Y0_MM) <= HOLE_TEMPLATE_Y0_TOL_MM]
    if not len(shifts):
        return 0, 0.0, None
    pos = shifts[:, None] + t[None, :]                                # (k, 6)
    idx = np.searchsorted(ys, pos)
    lo = ys[np.clip(idx - 1, 0, len(ys) - 1)]
    hi = ys[np.clip(idx, 0, len(ys) - 1)]
    dev = np.minimum(np.abs(pos - lo), np.abs(pos - hi))
    hit = dev <= HOLE_TEMPLATE_TOL_MM
    m = hit.sum(1)
    best = np.flatnonzero(m == m.max())
    rms = np.array([math.sqrt((dev[b][hit[b]] ** 2).mean()) for b in best])
    j = int(rms.argmin())                  # among the equal-best shifts, the tightest
    k = best[j]
    return int(m[k]), float(rms[j]), float(shifts[k])


def fit_fold(holes):
    """The line that matches the clip template, or None.

    Every pair of holes proposes a line x = a*y + b (dropped if steeper than
    FOLD_TILT_MAX); the holes within FOLD_TOL_MM are its inliers, and a
    proposal with fewer than FOLD_MIN_HOLES is not scored.  Each distinct
    inlier set is scored against HOLE_TEMPLATE_MM; the most template matches
    win, then the smallest template RMS, then the most inliers, then the
    smallest residual; fewer than HOLE_TEMPLATE_MIN matches is no fold.  The
    winner is refitted by least squares over its inliers; `holes` returns
    the inliers within HOLE_FILL_NEAR_MM along the line of a template
    position -- the clip's punches and their torn fragments, the only
    candidates `cut` fills.
    """
    if len(holes) < FOLD_MIN_HOLES:
        return None
    pts = np.array([(cx, cy) for cx, cy, _ in holes])
    seen, best = set(), None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[j]
            if abs(y2 - y1) < 1:
                continue
            a = (x2 - x1) / (y2 - y1)
            if abs(math.degrees(math.atan(a))) > FOLD_TILT_MAX:
                continue
            b = x1 - a * y1
            res = np.abs(pts[:, 0] - (a * pts[:, 1] + b))
            inl = res < FOLD_TOL_MM * MM
            n = int(inl.sum())
            if n < FOLD_MIN_HOLES:
                continue
            key = np.packbits(inl).tobytes()
            if key in seen:
                continue
            seen.add(key)
            m, rms, shift = template_score(pts[inl, 1])
            if m < HOLE_TEMPLATE_MIN:
                continue
            score = (m, -rms, n, -float(res[inl].mean()))
            if best is None or score > best[0]:
                best = (score, inl, shift)
    if best is None:
        return None
    (m, neg_rms, _, _), inl, shift = best
    poly = np.polyfit(pts[inl, 1], pts[inl, 0], 1)          # x = f(y)
    res = np.abs(pts[inl, 0] - np.polyval(poly, pts[inl, 1]))
    punches = np.abs(pts[:, 1][:, None] / MM - (shift + np.asarray(HOLE_TEMPLATE_MM))[None, :]
                     ).min(1) <= HOLE_FILL_NEAR_MM
    return {"poly": poly, "n": int(inl.sum()), "template": m, "template_rms_mm": -neg_rms,
            "residual_mm": float(res.mean() / MM),
            "holes": [holes[i] for i in np.flatnonzero(inl & punches)]}


# --- the fold fallback: the neighbour's content boundary ------------------
# 8609's winning spine signal, kept as the FALLBACK for a page whose holes do
# not fit a line: where the neighbour bled in, dark fraction and saturation
# step up together at one x, and the clean margin between is a band of
# neither.  Per horizontal band, the content block NEAREST the inner border
# that starts within NB_BORDER_NEAR_MM of it (rejects this page's own type),
# is at least NB_BLOCK_MIN_MM wide (rejects specks) and does not reach the
# interior limit (rejects full-bleed / merged) gives one boundary point; a
# robust line through the points is the boundary.  It finds a fold only where
# the neighbour has content -- blank margin gives NO boundary, correctly.
NB_BANDS = 28
NB_STRIP_MM = 50.0           # the inner search strip
NB_DARK_LUM = 95
NB_DARK_FRAC = 0.05
NB_SAT_MIN = 0.17            # (max-min)/255 of a column's mean colour
NB_BLOCK_MIN_MM = 0.85       # ~20 px @600
NB_BORDER_NEAR_MM = 10.0     # the block must START this close to the border
NB_RESID_MM = 1.9            # ~45 px @600: iterative reject
NB_MIN_BANDS = 6
NB_TILT_MAX = 1.5            # deg
NB_PRIOR_MM = 5.0            # within this of the issue's median fold, if known


def neighbour_boundary(rgb, par, prior_x=None):
    h, w = rgb.shape[:2]
    strip_w = int(NB_STRIP_MM * MM)
    if par == "even":
        strip = rgb[:, w - strip_w:]
        to_x = lambda i: w - strip_w + i          # strip index -> sheet x
        inward = lambda cols: cols[::-1]          # border-first order
    else:
        strip = rgb[:, :strip_w]
        to_x = lambda i: i
        inward = lambda cols: cols
    lum = strip.mean(2, dtype=np.float32)
    pts = []
    for band in np.array_split(np.arange(h), NB_BANDS):
        b = strip[band]
        dark = (lum[band] < NB_DARK_LUM).mean(0)
        mean = b.mean(0, dtype=np.float32)
        sat = (mean.max(1) - mean.min(1)) / 255.0
        content = (dark > NB_DARK_FRAC) | (sat > NB_SAT_MIN)
        c = inward(content)                        # index 0 = at the border
        # first content run from the border
        i = 0
        while i < len(c) and not c[i]:
            i += 1
        if i >= len(c) or i > NB_BORDER_NEAR_MM * MM:
            continue
        j = i
        while j < len(c) and c[j]:
            j += 1
        if j - i < NB_BLOCK_MIN_MM * MM or j >= len(c):    # too thin, or full-bleed
            continue
        edge = j                                    # page-facing edge, border-first index
        x = to_x(strip_w - edge) if par == "even" else to_x(edge)
        pts.append((band.mean(), x))
    if len(pts) < NB_MIN_BANDS:
        return None
    pts = np.array(pts)
    keep = np.ones(len(pts), bool)
    for _ in range(5):
        poly = np.polyfit(pts[keep, 0], pts[keep, 1], 1)
        res = np.abs(pts[:, 1] - np.polyval(poly, pts[:, 0]))
        new = res < NB_RESID_MM * MM
        if new.sum() < NB_MIN_BANDS or (new == keep).all():
            break
        keep = new
    if keep.sum() < NB_MIN_BANDS or abs(tilt(poly)) > NB_TILT_MAX:
        return None
    if prior_x is not None and abs(np.polyval(poly, h / 2) - prior_x) > NB_PRIOR_MM * MM:
        return None
    return {"poly": poly, "n": int(keep.sum()),
            "residual_mm": float(res[keep].mean() / MM)}


# --- the anchor: the 64'er wordmark ---------------------------------------
# The wordmark is the same glyph on every page, not mirrored between parities,
# print-registered to the content, in the OUTER-bottom corner: even pages
# bottom-left ("<num>  64'er"), odd bottom-right ("64'er  <num>").  8609 found
# it on 129/176 pages at a median score of 0.95 by normalised cross-
# correlation against this template; the pages without it are ads and
# full-bleed pictures.  The template is a 600 dpi grey crop of the wordmark,
# 394 x 131 px, kept in scan2ocr/ (rules/ admits only rNNN_ files).
#
# The page is levelled before this runs, so there is no angle sweep.
TEMPLATE_PATH = HERE.parent / "template_64er_600.png"
LOGO_BAND_TOP_MM = 30.0      # search rows h-30mm .. h-5mm: 8609 saw the
LOGO_BAND_BOT_MM = 5.0       # baseline at h-420..h-300 px (13-18 mm); 8610's
                             # sheets600 have it at h-11.2..11.4 mm (p010, p011)
                             # -- the band's last 1.7 mm is the yellow prop
                             # (starts h-6.6..6.8 mm), and the windows that
                             # overlap it score <= 0.29: no spurious peak, so
                             # the band is not clipped to the prop line
LOGO_CORNER_FRAC = 0.48      # ...and this fraction of the width, from the outer edge
LOGO_SCORE_MIN = 0.5         # 8609 accepted 0.42 with an angle sweep; here the
                             # page is level.  MEASURED on 8610's sheets600:
                             # p010 0.941, p011 0.933 (the wordmark, 26.5 /
                             # 20.9 mm in from the outer edge); p100 and p101
                             # are ad pages without one and their best window
                             # is 0.290 / 0.292 -- the runner-up on the two
                             # logo'd pages is 0.247 / 0.234.  0.5 sits in
                             # the gap between the ceiling of a page without
                             # the wordmark (~0.29) and the floor of one with.
NCC_SIGMA_MIN = 1.0          # grey levels: a window with less texture than this
                             # per pixel has no score (see ncc)


def load_template():
    return np.array(Image.open(TEMPLATE_PATH).convert("L"), np.float32)


TEMPLATE = load_template()


def ncc(region, tmpl):
    """Zero-mean normalised cross-correlation, valid mode, by FFT.

    The window sums run in float64 and the variance is floored at
    NCC_SIGMA_MIN.  The variance is the difference of two ~3e9 sums (51614
    px of paper at ~230), which single precision holds to ~256: MEASURED on
    a synthetic blank page, a flat window's variance came out 128 or -2180
    where the truth is 0, and the numerator's rounding noise over that
    scored 522 at a blank spot.  In float64 the same window is 1e-7 -- and
    that is still a zero divisor waiting for a flatter page, so the floor
    is one grey level of texture per pixel, not an epsilon.
    """
    t = (tmpl - tmpl.mean()).astype(np.float64)
    tn = math.sqrt(float((t * t).sum()))
    ones = np.ones_like(t)
    region = region.astype(np.float64)
    num = fftconvolve(region, t[::-1, ::-1], mode="valid")
    s1 = fftconvolve(region, ones, mode="valid")
    s2 = fftconvolve(region * region, ones, mode="valid")
    var = np.maximum(s2 - s1 * s1 / t.size, t.size * NCC_SIGMA_MIN ** 2)
    return (num / (np.sqrt(var) * tn)).astype(np.float32)


def find_logo(gray, par, tmpl):
    """The wordmark's outer-bottom corner, or None."""
    h, w = gray.shape
    th, tw = tmpl.shape
    y0, y1 = h - int(LOGO_BAND_TOP_MM * MM), h - int(LOGO_BAND_BOT_MM * MM)
    cw = int(w * LOGO_CORNER_FRAC)
    x0 = 0 if par == "even" else w - cw
    region = gray[y0:y1, x0:x0 + cw].astype(np.float32)
    if region.shape[0] < th or region.shape[1] < tw:
        return None
    m = ncc(region, tmpl)
    iy, ix = np.unravel_index(int(m.argmax()), m.shape)
    score = float(m[iy, ix])
    if score < LOGO_SCORE_MIN:
        return None
    bx0, by0 = x0 + int(ix), y0 + int(iy)
    bbox = (bx0, by0, bx0 + tw, by0 + th)
    x = bx0 if par == "even" else bx0 + tw
    return {"x": int(x), "y": int(by0 + th), "score": score, "bbox": bbox}


# ---------------------------------------------------------------------------
# measure, part 1: level and grade  (verbatim from the sheet variant)
# ---------------------------------------------------------------------------

def level_page(page):
    """Skew off the thumb, rotate the 2400 scan, re-measure, re-level once.

    Returns (angle, residual, full2400 PIL RGB, img600 PIL RGB, notes).  The
    same two-pass arrangement as the sheet variant, for the same reason: the
    thumb is 1/16 scale and cannot resolve a hundredth of a degree.
    """
    notes = []
    stem = f"{page:03d}"
    scan, thumb = SCAN_DIR / f"{stem}.png", THUMB_DIR / f"{stem}.png"
    for p in (scan, thumb):
        if not p.exists():
            raise PageFailed(f"r005 p{stem}: missing input {p}")
    thumb_rgb = Image.open(thumb).convert("RGB")
    angle = measure_skew(np.array(thumb_rgb.convert("L"), float))

    def levelled(a):
        f = Image.open(scan).convert("RGB")
        f = f.rotate(a, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
        return f, f.reduce(SCAN_REDUCE)

    def residual_of(im):
        return measure_skew(np.array(im.reduce(MASTER_DPI // THUMB_DPI)
                                     .convert("L"), float))

    full, img = levelled(angle)
    residual = residual_of(img)
    if abs(residual) > SKEW_RESIDUAL_MAX:
        first, angle = residual, angle + residual
        full, img = levelled(angle)
        residual = residual_of(img)
        notes.append(f"SKEW re-levelled: residual was {first:+.2f}, "
                     f"corrected to {angle:+.2f} deg, now {residual:+.2f}")
    if abs(residual) > SKEW_RESIDUAL_MAX:
        notes.append(f"SKEW still {residual:+.2f} deg after a second pass "
                     f"(allowed {SKEW_RESIDUAL_MAX}) -- published anyway")
    return angle, residual, full, img, notes


def grade_page(stem, full, stamp):
    """Separate the levelled 2400 sheet, undo the GCR, render once, reduce 4:1.

    Writes masters2400/NNN.png, cmyk2400/NNN.tif + NNN.colors.txt and
    sheets600/NNN.png.  Returns the sheets600 array (h, w, 3) uint8.
    """
    with tempfile.TemporaryDirectory(prefix=f"r005_{ISSUE}_{stem}_") as work:
        work = Path(work)
        profile_txt = OUT_CMYK / f"{stem}.colors.txt"
        write_profile(ANCHORS, LEVELS, profile_txt, VARIANT)
        src_png, cmyk_tiff = work / "in.png", work / "sep.tiff"
        full.save(src_png)
        separate_and_render(src_png, cmyk_tiff, OUT_SHEET / f"{stem}.png",
                            profile_txt, stamp)
        archive_cmyk(cmyk_tiff, OUT_CMYK / f"{stem}.tif", stamp)
    sheet = np.array(Image.open(OUT_SHEET / f"{stem}.png").convert("RGB")
                     .reduce(SCAN_REDUCE))
    save_master(sheet, OUT_SHEET600 / f"{stem}.png", stamp)
    return sheet


# ---------------------------------------------------------------------------
# measure, part 2: the geometry, on the levelled UNGRADED 600 dpi sheet
# ---------------------------------------------------------------------------
# The finders read the sheet as `level_page` hands it over, BEFORE the grade:
# that is where paper_mask / prop_mask were calibrated (the built-in W is the
# raw scan's paper), and the hole and logo finders read its grey.  The graded
# sheet is only for the master.

def measure_geometry(rgb, page, angle, residual, notes, tmpl):
    par = parity(page)
    h, w = rgb.shape[:2]
    gray = rgb.mean(2).astype(np.uint8)
    edges = outer_edges(rgb, par)
    if edges["source"] == "fullbleed":
        notes.append(f"EDGES fullbleed: paper body {edges['body']:.2f} -- top/outer "
                     f"at the frame, bottom from the prop")
    for key, depth, t in edges["replaced"]:
        notes.append(f"EDGES {key} from the {'prop' if key == 'bot' else 'frame'}: "
                     f"the paper trace ran {depth:.1f} mm in at {t:+.2f} deg -- ink to the trim")
    holes = find_holes(gray, par)
    fold = fit_fold(holes)
    source = "holes"
    if fold is None:
        nb = neighbour_boundary(rgb, par)
        if nb is not None:
            fold, source = nb, "colour"
            notes.append(f"FOLD from the neighbour's colour boundary "
                         f"({nb['n']} bands, residual {nb['residual_mm']:.2f} mm) "
                         f"-- {len(holes)} hole candidates did not fit a line")
        else:
            source = "none"
            notes.append(f"FOLD not found: {len(holes)} hole candidates, no "
                         f"colour boundary -- the inner side is not cut")
    logo = find_logo(gray, par, tmpl)
    if logo is None:
        notes.append("LOGO not found -- the window is anchored on fold x and "
                     "bottom-trim y instead")
    return {
        "page": page, "parity": par, "sheet_px": [w, h],
        "skew": {"angle": angle, "residual": residual},
        "edges": {**{k: [float(v) for v in edges[k]] for k in ("top", "bot", "outer")},
                  "source": edges["source"], "body": edges["body"],
                  "replaced": edges["replaced"]},
        "fold": {"source": source,
                 "poly": None if fold is None else [float(v) for v in fold["poly"]],
                 "n": 0 if fold is None else fold["n"],
                 "residual_mm": None if fold is None else fold["residual_mm"],
                 "template": fold.get("template", 0) if fold else 0,
                 "template_rms_mm": fold.get("template_rms_mm") if fold else None,
                 "tilt_deg": None if fold is None else tilt(fold["poly"]),
                 "holes": [[float(a), float(b), float(c)] for a, b, c in fold.get("holes", [])] if fold else []},
        "holes": [[float(a), float(b), float(c)] for a, b, c in holes],
        "anchor": None if logo is None else {"source": "logo", **logo},
        "notes": notes,
    }


# --- the debug overlay -----------------------------------------------------
# Edges green (the sheet variant's colour) when traced from paper, ORANGE when
# they are the full-bleed frame + prop lines, fold magenta, holes circled in
# the same magenta, the wordmark's box blue.  The lines and circles are drawn
# at 600 dpi and reduced with the page; the text is drawn AFTER the reduction,
# because PIL's default font is ~11 px and would be 2 px tall otherwise.  A
# hole is ~0.7 mm = 16 px, and after the 5:1 reduction a 16 px circle would be
# an invisible 3 px ring, so the ring is drawn wide enough to survive it.
DEBUG_FOLD = (230, 0, 200)
DEBUG_LOGO = (0, 120, 255)
DEBUG_FULLBLEED = (255, 140, 0)
DEBUG_HOLE_RING_PX = 12 * DEBUG_REDUCE       # radius at 600 dpi; 12 px after


def draw_debug(img, geom, dest):
    """Edges green, fold magenta, holes circled, logo box blue, notes as text."""
    w, h = img.size
    overlay = img.copy()
    d = ImageDraw.Draw(overlay)
    replaced = {r[0] for r in geom["edges"]["replaced"]}
    def edge_colour(key):
        return DEBUG_FULLBLEED if geom["edges"]["source"] != "paper" or key in replaced else DEBUG_COLOR
    for key in ("top", "bot"):
        p = geom["edges"][key]
        d.line([(x, np.polyval(p, x)) for x in range(0, w, DEBUG_STEP)],
               fill=edge_colour(key), width=DEBUG_WIDTH)
    p = geom["edges"]["outer"]
    d.line([(np.polyval(p, y), y) for y in range(0, h, DEBUG_STEP)],
           fill=edge_colour("outer"), width=DEBUG_WIDTH)
    if geom["fold"]["poly"]:
        p = geom["fold"]["poly"]
        d.line([(np.polyval(p, y), y) for y in range(0, h, DEBUG_STEP)],
               fill=DEBUG_FOLD, width=DEBUG_WIDTH)
    filled = {(cx, cy) for cx, cy, _ in geom["fold"]["holes"]}
    for cx, cy, dm in geom["holes"]:
        r = max(dm * MM, DEBUG_HOLE_RING_PX)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=DEBUG_FOLD,
                  width=DEBUG_WIDTH * (3 if (cx, cy) in filled else 1))   # the filled ones ring thick
    if geom["anchor"]:
        d.rectangle(geom["anchor"]["bbox"], outline=DEBUG_LOGO, width=DEBUG_WIDTH)
    small = overlay.resize((w // DEBUG_REDUCE, h // DEBUG_REDUCE), Image.LANCZOS)
    text = [f"p{geom['page']:03d} {geom['parity']}  edges:{geom['edges']['source']} "
            f"fold:{geom['fold']['source']} "
            f"anchor:{'logo %.2f' % geom['anchor']['score'] if geom['anchor'] else 'NONE'}"]
    ImageDraw.Draw(small).text((12, 12), "\n".join(text + geom["notes"]), fill=DEBUG_FOLD)
    small.save(dest)


def measure(page):
    stem = f"{page:03d}"
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    angle, residual, full, img, notes = level_page(page)
    rgb = np.array(img)                      # the levelled, UNGRADED 600 dpi sheet
    geom = measure_geometry(rgb, page, angle, residual, notes, TEMPLATE)
    f, anchor = geom["fold"], geom["anchor"]
    stamp = stamp_text(VARIANT, **{"page": f"{stem} of {ISSUE}",
                                   "phase": "measure",
                                   "skew": f"{angle:+.2f} -> {residual:+.2f} deg",
                                   "fold": f["source"],
                                   "anchor": f"logo {anchor['score']:.2f}" if anchor else "none",
                                   "notes": "; ".join(notes) or "(none)"})
    grade_page(stem, full, stamp)
    (OUT_GEOM / f"{stem}.json").write_text(json.dumps(geom, indent=1))
    draw_debug(img, geom, OUT_DEBUG / f"{stem}.png")
    print(f"p{stem}: skew {angle:+.2f} -> {residual:+.2f} deg | edges T {tilt(geom['edges']['top']):+.2f} "
          f"B {tilt(geom['edges']['bot']):+.2f} O {tilt(geom['edges']['outer']):+.2f} | "
          f"fold {f['source']} n={f['n']}"
          + (f" t={f['template']}/{f['template_rms_mm']:.2f}" if f["source"] == "holes" else "")
          + (f" x={np.polyval(f['poly'], rgb.shape[0] / 2):.0f} tilt {f['tilt_deg']:+.2f}" if f["poly"] else "")
          + f" | logo {'%.2f' % anchor['score'] if anchor else 'none'}"
          + f" | grade {GRADE_SHA}"
          + "".join(f"\n      NOTE p{stem}: {n}" for n in notes), flush=True)


# ---------------------------------------------------------------------------
# cut: the window
# ---------------------------------------------------------------------------
# ONE rigid (S, B) per parity: the anchor's distance from the window's left
# and top edge, chosen to minimise the UNKNOWN fraction inside the window --
# bed, prop, beyond the fold, off the frame -- over the pages that carry their
# own wordmark.  8609's fit: even S=568 B=6892, odd S=4416 B=6900 (600 dpi
# px), unknown p50 1.38 % / 1.92 %.  The search spans the whole page width;
# capping it once pinned the odd optimum to the cap and reported a window
# mostly off the page.  Fitted at 1/FIT_SCALE resolution: one step is 0.17
# mm, below the 0.3 mm the edge inset already gives away.
FIT_SCALE = 4
FIT_B_RANGE_MM = (250.0, 297.0)   # the anchor is 4-30 mm above the foot
FOLD_INSET_MM = 0.0               # cut ON the fold; the holes are filled separately
HOLE_FILL_R_MM = 0.4              # radius added to a hole's own before filling
# WHICH holes are filled: fold.holes -- the fold line's inliers at the
# template's positions, the clip's punches and their fragments -- and never
# the other candidates.  The first sweep filled every candidate, on the
# argument that a candidate is a hole-shaped dark mark in the fold band
# whether or not it sat on the line; MEASURED, that painted 518 dots of
# p005's coarse-screened picture white (1137 mm2, its first ~5 mm along the
# inner edge) and crease specks and cracks off 41 other pages; filling every
# inlier still took the picture's first dot column, which IS the crease
# (530 mm2).  A candidate off the line or off the template is ink, a speck,
# a crack or the picture, and stays.
CUT_INSET_MM = EDGE_INSET_MM


def unknown_mask(geom, scale=1):
    w, h = geom["sheet_px"]
    ws, hs = w // scale, h // scale
    ys = np.arange(hs) * scale
    xs = np.arange(ws) * scale
    mm = MM
    top = np.polyval(geom["edges"]["top"], xs) + CUT_INSET_MM * mm
    bot = np.polyval(geom["edges"]["bot"], xs) - CUT_INSET_MM * mm
    outer = np.polyval(geom["edges"]["outer"], ys)
    u = (ys[:, None] < top[None, :]) | (ys[:, None] > bot[None, :])
    if geom["parity"] == "even":
        u |= xs[None, :] < (outer + CUT_INSET_MM * mm)[:, None]
    else:
        u |= xs[None, :] > (outer - CUT_INSET_MM * mm)[:, None]
    if geom["fold"]["poly"]:
        fold = np.polyval(geom["fold"]["poly"], ys)
        if geom["parity"] == "even":
            u |= xs[None, :] > (fold - FOLD_INSET_MM * mm)[:, None]
        else:
            u |= xs[None, :] < (fold + FOLD_INSET_MM * mm)[:, None]
    for cx, cy, dm in geom["fold"]["holes"]:      # the clip's punches -- never the other candidates
        r = (dm / 2 + HOLE_FILL_R_MM) * mm / scale
        cy_, cx_ = cy / scale, cx / scale
        y0, y1 = max(int(cy_ - r) - 1, 0), min(int(cy_ + r) + 2, hs)
        x0, x1 = max(int(cx_ - r) - 1, 0), min(int(cx_ + r) + 2, ws)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        u[y0:y1, x0:x1] |= (yy - cy_) ** 2 + (xx - cx_) ** 2 <= r * r
    return u


def anchor_of(geom):
    """("logo", ax, ay) -- the wordmark, placed through the parity's (S, B) --
    or ("edges", x0, y0) -- the window's own top-left, placed directly on the
    page's PHYSICAL edges: its inner edge on the fold and its foot on the
    bottom trim (the prop's top).  The second is for pages without a wordmark
    -- covers, full-page ads -- and uses no fit at all: the two edges it needs
    are the two every page has, whatever its ink."""
    if geom["anchor"]:
        return "logo", geom["anchor"]["x"], geom["anchor"]["y"]
    w, h = geom["sheet_px"]
    bot_y = float(np.polyval(geom["edges"]["bot"], w / 2))
    if geom["fold"]["poly"]:
        fold_x = float(np.polyval(geom["fold"]["poly"], h / 2))
    else:
        fold_x = float(w - 1 if geom["parity"] == "even" else 0)
    x0 = fold_x - MASTER_W_PX if geom["parity"] == "even" else fold_x
    return "edges", x0, bot_y - MASTER_H_PX


def _window_sums(u, W, H):
    """Sum of `u` over every W x H window whose top-left is (x0, y0), for all
    x0 in [-W, w) and y0 in [-H, h): an integral image over `u` padded with
    UNKNOWN (off the frame is not this page)."""
    h, w = u.shape
    pad = np.ones((h + 2 * H, w + 2 * W), np.int64)
    pad[H:H + h, W:W + w] = u
    I = np.zeros((pad.shape[0] + 1, pad.shape[1] + 1), np.int64)
    I[1:, 1:] = pad.cumsum(0).cumsum(1)
    # window top-left at padded (py, px) -> sum = I[py+H, px+W] - I[py, px+W] - I[py+H, px] + I[py, px]
    py = np.arange(0, h + H)          # = y0 + H, y0 in [-H, h)
    px = np.arange(0, w + W)
    return (I[py[:, None] + H, px[None, :] + W] - I[py[:, None], px[None, :] + W]
            - I[py[:, None] + H, px[None, :]] + I[py[:, None], px[None, :]])


def fit_window(geoms):
    W, H = MASTER_W_PX // FIT_SCALE, MASTER_H_PX // FIT_SCALE
    out = {"stats": {}}
    for par in ("even", "odd"):
        acc, n = None, 0
        for g in geoms:
            if g["parity"] != par or not g["anchor"]:
                continue
            u = unknown_mask(g, FIT_SCALE)
            sums = _window_sums(u, W, H)                 # indexed by (y0+H, x0+W)
            ax, ay = g["anchor"]["x"] // FIT_SCALE, g["anchor"]["y"] // FIT_SCALE
            # window top-left (x0, y0) = (ax - S, ay - B); accumulate over (S, B)
            # on a common grid: S in [0, W), B in [Bmin, Bmax]
            Bs = np.arange(int(FIT_B_RANGE_MM[0] * MM) // FIT_SCALE,
                           int(FIT_B_RANGE_MM[1] * MM) // FIT_SCALE + 1)
            Ss = np.arange(0, W)
            y_idx = ay - Bs + H
            x_idx = ax - Ss + W
            ok_y = (y_idx >= 0) & (y_idx < sums.shape[0])
            ok_x = (x_idx >= 0) & (x_idx < sums.shape[1])
            grid = np.full((len(Bs), len(Ss)), W * H, np.int64)   # off-grid = all unknown
            grid[np.ix_(ok_y, ok_x)] = sums[np.ix_(y_idx[ok_y], x_idx[ok_x])]
            acc = grid if acc is None else acc + grid
            n += 1
        if n == 0:
            raise SystemExit(f"{VARIANT} cut: no {par} page has a logo anchor -- "
                             f"nothing to fit the window on")
        bi, si = np.unravel_index(int(acc.argmin()), acc.shape)
        S_, B_ = int(Ss[si] * FIT_SCALE), int(Bs[bi] * FIT_SCALE)
        out[par] = (S_, B_)
        out["stats"][par] = {"pages": n, "mean_unknown": float(acc[bi, si] / (n * W * H))}
    return out


def cut_page(geom, fit, sheet600):
    """The master: sheet600 with the unknown painted white, cut to the window."""
    notes = list(geom["notes"])
    w, h = geom["sheet_px"]
    source, ax, ay = anchor_of(geom)
    if source == "logo":
        S_, B_ = fit[geom["parity"]]
        x0, y0 = int(round(ax - S_)), int(round(ay - B_))
    else:
        x0, y0 = int(round(ax)), int(round(ay))
    u = unknown_mask(geom)
    painted = sheet600[:h, :w].copy()
    painted[u] = 255
    master = np.full((MASTER_H_PX, MASTER_W_PX, 3), 255, np.uint8)
    unk = np.ones((MASTER_H_PX, MASTER_W_PX), bool)
    sy0, sy1 = max(y0, 0), min(y0 + MASTER_H_PX, h)
    sx0, sx1 = max(x0, 0), min(x0 + MASTER_W_PX, w)
    if sy1 > sy0 and sx1 > sx0:
        master[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = painted[sy0:sy1, sx0:sx1]
        unk[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = u[sy0:sy1, sx0:sx1]
    frac = float(unk.mean())
    if source != "logo":
        notes.append("ANCHOR from the page edges (fold + bottom trim): the "
                     "wordmark was not found")
    return master, frac, notes


def cut():
    geoms = [json.loads(p.read_text()) for p in sorted(OUT_GEOM.glob("[0-9][0-9][0-9].json"))]
    if not geoms:
        raise SystemExit(f"{VARIANT} cut: no geometry in {OUT_GEOM} -- run measure first")
    fit = fit_window(geoms)
    OUT_MASTER.mkdir(parents=True, exist_ok=True)
    report = {"fit": {k: list(v) for k, v in fit.items() if k != "stats"},
              "stats": fit["stats"], "pages": {}}
    for g in geoms:
        stem = f"{g['page']:03d}"
        sheet = np.array(Image.open(OUT_SHEET600 / f"{stem}.png").convert("RGB"))
        master, frac, notes = cut_page(g, fit, sheet)
        source, ax, ay = anchor_of(g)
        stamp = stamp_text(VARIANT, **{
            "page": f"{stem} of {ISSUE}", "phase": "cut",
            "master-px": f"{MASTER_W_PX} {MASTER_H_PX}",
            "skew": f"{g['skew']['angle']:+.2f} -> {g['skew']['residual']:+.2f} deg",
            "fold": f"{g['fold']['source']} n={g['fold']['n']}"
                    + (f" template {g['fold']['template']}" if g["fold"]["source"] == "holes" else "")
                    + (f" tilt {g['fold']['tilt_deg']:+.2f} deg" if g["fold"]["poly"] else ""),
            "holes": f"{len(g['fold']['holes'])} filled of {len(g['holes'])} candidates",
            "anchor": (f"logo ({ax:.0f}, {ay:.0f}) score {g['anchor']['score']:.2f}"
                       if source == "logo" else
                       f"edges: window top-left ({ax:.0f}, {ay:.0f}) from fold + bottom trim"),
            "window": f"S {fit[g['parity']][0]} B {fit[g['parity']][1]} ({g['parity']})",
            "unknown": f"{frac:.2%} of the window is fabricated white",
            "notes": "; ".join(notes) or "(none)",
        })
        save_master(master, OUT_MASTER / f"{stem}.png", stamp)
        (OUT_MASTER / f"{stem}.stamp.txt").write_text(stamp, encoding="utf-8")
        report["pages"][stem] = {"anchor": source, "fold": g["fold"]["source"],
                                 "unknown": frac}
        print(f"p{stem}: anchor {source} | fold {g['fold']['source']} | "
              f"unknown {frac:.2%}" + "".join(f"\n      NOTE p{stem}: {n}" for n in notes),
              flush=True)
    (OUT_GEOM / "fit.json").write_text(json.dumps(report, indent=1))
    print("fit:", json.dumps(report["fit"]), json.dumps(report["stats"]), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("measure", "cut"):
        raise SystemExit(f"usage: {VARIANT}.py measure [pages..] | cut")
    if not HAVE_PROFILE:
        print(f"r005: {ISSUE} has no colors profile -- grading with the built-in "
              f"anchor set and identity levels", flush=True)
    print(stamp_text(VARIANT, **{"run": sys.argv[1]}), flush=True)
    if sys.argv[1] == "measure":
        pages = [int(a) for a in sys.argv[2:]] or list(ISS.page_range)
        failed = []
        for page in pages:
            try:
                measure(page)
            except PageFailed as exc:
                print(f"p{page:03d} FAILED -- {exc}", file=sys.stderr, flush=True)
                failed.append(page)
        if failed:
            raise SystemExit(f"r005: {len(failed)} page(s) had no input: "
                             f"{', '.join('%03d' % p for p in failed)}")
    else:
        cut()
