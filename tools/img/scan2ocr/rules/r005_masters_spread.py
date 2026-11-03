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
    SKEW_RESIDUAL_MAX, SKEW_COARSE, CLEAN_PCT, TRACE_BANDS, BODY_PAPER_FRAC,
    DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP,
    ANCHORS, LEVELS, HAVE_PROFILE, GRADE_SHA,
    SKEW_PEAK_MIN, SKEW_WEAK_MAX_DEG,
    PageFailed, measure_skew, skew_peakiness,
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
PROP_FOOT_MM = 15.0          # the backing's top is looked for this far up
PROP_AT_FOOT_MM = 2.0        # ...in columns whose backing starts within this of it
# THE FOOT UNDER THE SHEET IS NOT ALWAYS THE YELLOW PROP.  MEASURED on the
# derived 150 dpi thumbs, p050, foot median RGB and G-B:
#     8610/8611  248 215 112   G-B 103      the yellow prop
#     8612       249 216 113   G-B 103
#     8701        34  34  36   G-B  -1      a near-black BED, no prop at all
# `prop_mask` is a YELLOW test (G-B > 50 AND mean > 120), so on 8701 it sees
# nothing, prop_top() returns None, and every full-bleed page takes the frame's
# last row instead: the window sits ~7 mm low and the bed stays in the master.
# The sheet variant already knows this -- r005_masters_sheet.py builds its bed
# as `(lum < BED_LUM) | prop_mask(rgb)` -- and r005_a4_window.py says why in as
# many words: "a saturated prop (yellow on one side of the bed, red on the
# other -- BOTH, which is why saturation and not a yellow test)".
# So test for BACKING, not for yellow.  This variant had simply never met a bed
# the prop did not cover.
BED_LUM = 70                 # 0-255 mean channel; as the sheet variant
BACKING_BOT_MAX_MM = 12.0    # a backing line further up than this is INK, not bed


def backing_mask(rgb):
    """True where the pixel is BACKING: the dark bed, or the saturated prop."""
    return (rgb.mean(2, dtype=np.float32) < BED_LUM) | prop_mask(rgb)


def backing_top(rgb):
    """The backing's top boundary as a line y(x), or None if it cannot be read.

    Per column, the top of the backing RUN THAT TOUCHES THE FOOT -- not the
    first backing-coloured row in the foot: MEASURED on p001, the cover's
    orange banner sits inside the foot and pulled the first-row line 4.7 mm up
    on the left.  The run may start a few rows above the frame's last row,
    which is black where the levelling rotation left a wedge.

    BLACK INK TO THE BOTTOM TRIM LOOKS EXACTLY LIKE A BLACK BED, so the fitted
    line is gated against the frame's measured slack before it is believed: on
    8610's 195 sound pages the bottom trim sits 6.4-9.4 mm above the frame's
    foot, and 8701's black band measures 6.1-7.8 mm.  A line further up than
    BACKING_BOT_MAX_MM is a page whose ink runs off the foot, not the bed --
    say so and fall back to the frame row, which is the documented behaviour.
    """
    h, w = rgb.shape[:2]
    foot = backing_mask(rgb[h - int(PROP_FOOT_MM * MM):])[::-1]  # row 0 = the foot
    first = np.argmax(foot, axis=0)                              # first backing row up
    cols = np.where(foot.any(0) & (first <= PROP_AT_FOOT_MM * MM))[0]
    if len(cols) < TRACE_BANDS:
        print("  backing_top: %d columns reach the foot (< %d) -- no line; "
              "frame row used, cut() replaces it with the issue's foot"
              % (len(cols), TRACE_BANDS), flush=True)
        return None
    tops = np.empty(len(cols))
    for k, c in enumerate(cols):
        run = foot[first[c]:, c]
        end = first[c] + (int(np.argmin(run)) if not run.all() else len(run))
        tops[k] = h - end                                        # first non-prop row
    try:
        line = trace(tops, cols.astype(float), CLEAN_PCT, MM)
    except PageFailed as exc:
        print("  backing_top: the trace failed (%s) -- frame row used, cut() "
              "replaces it with the issue's foot" % exc, flush=True)
        return None
    up_mm = (h - 1 - float(np.polyval(line, w / 2.0))) / MM
    if up_mm > BACKING_BOT_MAX_MM:
        print("  backing_top: line sits %.1f mm above the frame foot (> %.1f) "
              "-- reading that as INK to the trim, not bed; frame row used"
              % (up_mm, BACKING_BOT_MAX_MM), flush=True)
        return None
    return line


# A LEAF NARROWER THAN A4 IS NEITHER PAPER NOR FULL BLEED.  MEASURED on 8701:
# p003/p004 are the bound-in reply card, about half the page wide, and the
# rest of the frame is the black bed -- 43/44 % of the master, in ONE column
# run touching the outer edge (p003 columns 2738-4937 of 4961, p004 0-2225).
# The card fills about half of every row, under BODY_PAPER_FRAC, so `body`
# read 0.00, the page was called full-bleed, `outer` was taken at the frame,
# the bed went into the master, and `unknown` certified 2 %.  Unlike a dark
# foot, this edge IS a step (card lum 200+ against bed 33), so it is traced:
# per row, the run of backing from the outer frame edge inward.  A row counts
# when that run is at least NARROW_BED_MIN_MM; the page counts when most rows
# do AND what lies just inside the boundary is bright -- p005, the control,
# is 21 % dark but in the artwork, not edge-contiguous, and is not touched.
NARROW_BED_MIN_MM = 20.0     # a bed run from the outer edge at least this wide
NARROW_ROWS_MIN = 0.6        # ...in at least this fraction of the rows
NARROW_STEP_LUM = 150        # and the leaf just inside the boundary this bright


def backing_outer(rgb, par):
    """The outer edge of a leaf narrower than A4, as x(y), or None."""
    h, w = rgb.shape[:2]
    bk = backing_mask(rgb)
    b = bk if par == "even" else bk[:, ::-1]          # column 0 = the outer edge
    run = np.argmin(b, axis=1)
    run[b.all(1)] = w
    rows = np.where(run >= NARROW_BED_MIN_MM * MM)[0]
    if len(rows) < NARROW_ROWS_MIN * h:
        return None
    x = run[rows].astype(float) if par == "even" else (w - 1 - run[rows]).astype(float)
    try:
        line = trace(x, rows.astype(float), CLEAN_PCT, MM)
    except PageFailed:
        return None
    xm = int(np.polyval(line, h / 2.0))
    # Clamped, and refused when empty: unclamped, an even page whose run
    # reaches the far edge gave an EMPTY slice, .mean() was nan, `nan < 150`
    # is False and an all-backing frame (a blank or failed scan) was accepted
    # as a narrow leaf; on an odd page a negative start silently read the
    # opposite side of the sheet.
    x0, x1 = ((xm + int(MM), xm + int(3 * MM)) if par == "even"
              else (xm - int(3 * MM), xm - int(MM)))
    x0, x1 = max(x0, 0), min(x1, w)
    if x1 <= x0:
        return None
    if rgb[int(h * .2):int(h * .8), x0:x1].mean() < NARROW_STEP_LUM:
        return None
    return line


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
                        pt = backing_top(rgb)
                        e["bot"] = np.array([0.0, h - 1.0]) if pt is None else pt
                    else:
                        e[key] = frame[key]
            return e
        except PageFailed:
            pass
    bot = backing_top(rgb)
    narrow = backing_outer(rgb, par)
    return {"top": frame["top"],
            "bot": np.array([0.0, h - 1.0]) if bot is None else bot,
            "outer": frame["outer"] if narrow is None else narrow,
            "source": "fullbleed" if narrow is None else "narrow",
            "body": body, "replaced": []}


# --- the fold: the clip holes --------------------------------------------
# The sheet was held in a rigid 6-hole binder clip whose punches left DARK
# TEARDROPS on the fold, 3 vertical pairs.  They are the one physical mark of
# the fold that survives on every sheet, and they are on the SAME line as the
# crease (seen on p100 at thumb scale).  MEASURED on 8610's sheets600 (the
# graded 600 dpi sheet, paper ~230, the holes 16-31 at their darkest), p100
# and p101 -- the two halves of one sheet, so the same six holes twice.  The
# finder itself runs earlier, on the levelled UNGRADED sheet (see measure()
# and measure_geometry()'s "read the sheet before the grade" note below); the
# full 200-page sweep found the fold there on 196/200 pages, so the
# thresholds below hold on the ungraded grey, not just on the graded PNG they
# were read off:
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
# THE CLIP IS A FACT ABOUT ONE PHYSICAL COPY, so the descriptor's `clip` block
# overrides these.  They are the fallback, measured on 8610, and they are NOT a
# default to rely on: applied to 8611 they fit 4 of 6 holes on every page and
# nothing failed, because 8611's clip has holes 3 and 4 sitting 3.3 mm higher --
# the same to 0.1 mm on every page, so a different clip or the same one re-set.
# The tell is a hole count that never reaches 6 on a clean page.  See
# r005_masters_spread.md, *The absolute prior*, for how to measure a new one.
_BUILTIN_HOLE_TEMPLATE_MM = (0.0, 13.35, 89.62, 102.92, 169.36, 182.95)
_BUILTIN_Y0_MM, _BUILTIN_Y0_TOL_MM = 59.0, 3.0

if ISS.clip is not None:
    HOLE_TEMPLATE_MM = ISS.clip.holes_mm
    HOLE_TEMPLATE_Y0_MM = ISS.clip.y0_mm
    HOLE_TEMPLATE_Y0_TOL_MM = ISS.clip.tol_mm
    CLIP_SOURCE = "descriptor"
else:
    HOLE_TEMPLATE_MM = _BUILTIN_HOLE_TEMPLATE_MM
    HOLE_TEMPLATE_Y0_MM = _BUILTIN_Y0_MM
    HOLE_TEMPLATE_Y0_TOL_MM = _BUILTIN_Y0_TOL_MM
    CLIP_SOURCE = "built-in (8610's clip)"

HOLE_TEMPLATE_TOL_MM = 0.75  # measured max 0.41, p95 0.30
HOLE_TEMPLATE_MIN = 4        # matches; 6 on an ordinary page, 4-5 with a torn or inked-over hole
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
                             # page is level.  MEASURED on 8610's sheets600
                             # (the graded PNG on disk, read for these figures;
                             # find_logo() itself runs earlier, on the levelled
                             # UNGRADED sheet -- see measure_geometry()):
                             # p010 0.941, p011 0.933 (the wordmark, 26.5 /
                             # 20.9 mm in from the outer edge); p100 and p101
                             # are ad pages without one and their best window
                             # is 0.290 / 0.292 -- the runner-up on the two
                             # logo'd pages is 0.247 / 0.234.  0.5 sits in
                             # the gap between the ceiling of a page without
                             # the wordmark (~0.29) and the floor of one with.
                             # The full 200-page sweep found the wordmark on
                             # 145/200 pages with no false positive found
                             # among the 62 pages looked at, so this threshold
                             # holds on the ungraded grey the finder reads.
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
    thumb_gray = np.array(thumb_rgb.convert("L"), float)
    angle = measure_skew(thumb_gray)
    # A flat skew profile may not move the page far (SKEW_PEAK_MIN, in
    # r005_masters): on 8701 p051 it put a level sheet 3 deg off, and the
    # residual pass, using the same instrument, confirmed it.  Refused, the page
    # is left as scanned and NOT re-levelled, because re-levelling would ask the
    # same blind instrument again.
    peak = skew_peakiness(thumb_gray)
    refused = peak < SKEW_PEAK_MIN and abs(angle) > SKEW_WEAK_MAX_DEG
    if refused:
        notes.append(f"SKEW refused: the profile has no peak (peak/median "
                     f"{peak:.2f} < {SKEW_PEAK_MIN}) and it asked for "
                     f"{angle:+.2f} deg (> {SKEW_WEAK_MAX_DEG}) -- levelled to 0. "
                     f"LOOK AT the page")
        angle = 0.0

    def levelled(a):
        f = Image.open(scan).convert("RGB")
        f = f.rotate(a, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
        return f, f.reduce(SCAN_REDUCE)

    def residual_of(im):
        return measure_skew(np.array(im.reduce(MASTER_DPI // THUMB_DPI)
                                     .convert("L"), float))

    full, img = levelled(angle)
    residual = residual_of(img)
    if refused:
        return angle, residual, full, img, notes
    if abs(residual) > SKEW_RESIDUAL_MAX:
        first, angle = residual, angle + residual
        full, img = levelled(angle)
        residual = residual_of(img)
        notes.append(f"SKEW re-levelled: residual was {first:+.2f}, "
                     f"corrected to {angle:+.2f} deg, now {residual:+.2f}")
        _lo, _hi, _ = SKEW_COARSE
        if not (_lo <= angle <= _hi):
            notes.append(f"SKEW total {angle:+.2f} deg is OUTSIDE the coarse "
                         f"sweep [{_lo:+.1f}, {_hi:+.1f}] -- the sweep clamped "
                         f"and the re-level pass added the rest. This is almost "
                         f"always ARTWORK printed tilted, not a tilted sheet "
                         f"(8612 p183: -6.60 applied). LOOK AT the page")
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
    if edges["source"] == "narrow":
        ox = float(np.polyval(edges["outer"], h / 2.0))
        notes.append(f"EDGES narrow leaf: {(ox if par == 'even' else w - 1 - ox) / MM:.1f} mm "
                     f"of bed from the outer frame edge -- a leaf printed NARROWER "
                     f"than A4 (a bound-in card); the bed is fabricated white, so "
                     f"`unknown` is large BY DESIGN. LOOK AT, not a failure")
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
        notes.append("LOGO not found -- the window is anchored on the fold "
                     "(or the inner frame edge when there is no fold) and "
                     "the bottom trim instead")
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


# A FOOT THE PAGE COULD NOT MEASURE TAKES THE ISSUE'S, NEVER THE FRAME ROW.
# MEASURED on 8701 (black bed), the bottom trim's depth above the frame foot,
# read off the geometry sidecars: 173 paper-traced feet 5.14-7.98 mm, median
# 7.45, sd 0.41; 16 of 19 full-bleed pages got a backing_top line inside that
# population (6.52-7.85).  THREE took the frame row at 0.00 mm -- p051, p178,
# p179 -- and kept 6-8 mm of bed in the master.  That cannot be cured with a
# threshold: on a dark full-bleed page the trim is a GRADIENT, not a step
# (p051 runs lum 32 -> 30 -> 28 -> 25 -> 18 over 2 mm, the sheet's edge-shadow
# on the bed), and the bed (lum 33) sits between the ink (17-25) and the paper
# (96).  So the depth is fitted issue-wide from the pages that can measure it,
# as the window is from the pages that carry a logo, and applied where a page
# cannot.  A foot shallower than FOOT_FRAME_MM is the frame row by construction.
FOOT_FRAME_MM = 3.0          # a foot this close to the frame's is the frame row
FOOT_OUTLIER_MM = 2.0        # the end gate: further than this from the median


def foot_depth_mm(g):
    w, h = g["sheet_px"]
    return (h - 1 - float(np.polyval(g["edges"]["bot"], w / 2.0))) / MM


def fit_foot(geoms):
    """Replace every frame-row foot with the issue's median depth; NOTE it.

    Returns (median_mm, replaced pages, outliers) -- the outliers are the
    pages whose foot, measured or not, sits further than FOOT_OUTLIER_MM from
    the issue's median, which is the check that would have named all three
    8701 pages without an eye."""
    depths = {g["page"]: foot_depth_mm(g) for g in geoms}
    sound = [d for d in depths.values() if d >= FOOT_FRAME_MM]
    if not sound:
        raise SystemExit(f"{VARIANT} cut: no page measured its foot")
    med = float(np.median(sound))
    replaced = []
    for g in geoms:
        if depths[g["page"]] < FOOT_FRAME_MM:
            w, h = g["sheet_px"]
            g["edges"]["bot"] = [0.0, h - 1.0 - med * MM]
            g.setdefault("notes", []).append(
                f"FOOT from the issue: the page's own foot sat "
                f"{depths[g['page']]:.2f} mm above the frame foot (the frame row, "
                f"bed kept) -- replaced with the issue median {med:.2f} mm over "
                f"{len(sound)} measured pages")
            replaced.append(g["page"])
            # Back into the sidecar, not only into this run's memory: the
            # sidecar is what a check reads (the foot audit over all 192 found
            # p179 that way), and left at 0.00 it re-flags a repaired page as
            # the defect on every future audit.  Written with the note, so the
            # sidecar, the stamp and the master say the same thing -- and a
            # later cut() reads a sound foot and keeps the note.
            (OUT_GEOM / f"{g['page']:03d}.json").write_text(json.dumps(g, indent=1))
    outliers = sorted((p, round(d, 2)) for p, d in depths.items()
                      if d >= FOOT_FRAME_MM and abs(d - med) > FOOT_OUTLIER_MM)
    return med, replaced, outliers


# MEASURED on 8701's finished masters, which is the wrong time to find out.
# Three carry a backing-coloured strip at an edge and NONE was reported:
# p028 right 0.8 mm over 98 % of the rows, p147 left 1.9 mm over 49 %, p103
# left 0.7 mm over 47 % -- the last of them the yellow prop, which came in
# because p103's fold was never found (`fold none`) so the inner side was not
# cut.  The check saw all three and dismissed them: the width floor was 2.0 mm
# and the height fraction 0.9.  A prop strip does not have to be wide to be
# wrong, and it does not have to run the full page: 0.7 mm of prop at 600 dpi
# is 17 px of saturated yellow down half a published page.
BED_RUN_FRAC = 0.4           # a column/row this much backing counts as bed
BED_RUN_LOOK_MM = 0.5        # a bed run from an edge wider than this: LOOK AT


# THE CLIP IS RIGID: FILL ALL SIX PUNCHES, NOT THE ONES THE FINDER LISTED.
# MEASURED on 8701: 74 of 192 pages filled fewer than 6 punches.  18 had no
# hole fold at all (source none/colour) and filled 0; 56 had a fold but the
# finder had listed only 4 or 5 candidates (p077, p102, p105, p108: "4 filled of
# 4"), so the punch it missed stayed in the master -- 27 of them survive the
# PDF's 35 % threshold.  A clip punch is damage from our disbinding, like the
# bed: it is never the plate and never the owner's question.
# Detection's job is to LOCATE the clip.  Once located, the six positions are
# the template's (HOLE_TEMPLATE_MM from HOLE_TEMPLATE_Y0_MM, issue-wide), and
# each is filled from what is actually on the page there:
#   1. a hole the fold already carries within HOLE_FILL_NEAR_MM -- kept as is;
#   2. else a relaxed local search around the template position for a dark,
#      punch-sized blob on a LIGHT surround (PUNCH_*);
#   3. else nothing: no punch is visible there, and painting blind could cover
#      ink (a full-bleed page, a screened box at the fold).
# Where the page has no fold line, x comes from the issue's median hole-fold
# distance from the inner frame edge and y from the issue's median template
# shift, each widened by the search window -- the same clip on every sheet.
PUNCH_WIN_X_MM = 3.0         # search half-width across the fold
PUNCH_WIN_Y_MM = 2.5         # ...and along it, around the template row
PUNCH_DIP = 30               # darker than the local surround by this (finder: 45)
PUNCH_ABS_MAX = 150          # and absolutely this dark (finder: 120)
PUNCH_MIN_MM = 0.3           # longest extent
PUNCH_MAX_MM = 4.0           # longest extent (a torn teardrop runs to 2.84)
PUNCH_RING_MM = 1.5          # the surround: this far beyond the blob's box...
PUNCH_RING_DARK_MAX = 0.15   # ...may be at most this fraction dark, or it is ink
PUNCH_ROW_TOL_MM = HOLE_TEMPLATE_TOL_MM   # a found blob must sit ON its template row
PUNCH_FOLD_TOL_MM = 1.0      # ...and on the fold line, where the page has one
PUNCH_FILL_MIN_MM = 2.0      # fill at least this diameter: r = max(d/2, 1.0) + 0.4
# ACCEPT ON THE ROW, THEN SIZE TO COVER.  MEASURED in the 8701 dry run: on p192
# the found blob was the punch and the disc was too small; on p179 the found
# blob was a fragment 1.6 mm above the punch, and a bigger disc there would
# only paint white beside a punch that still shows.  So a candidate is
# accepted only within PUNCH_ROW_TOL_MM of its row (and PUNCH_FOLD_TOL_MM of
# the fold, if known), and an accepted one is filled at no less than
# PUNCH_FILL_MIN_MM.  A page with no fold line has no known row either, so its
# row is fixed by agreement: at least two candidates on rows whose shifts
# agree within the tolerance, or nothing is accepted.
# A WHITE DISC IS ONLY AN IMPROVEMENT WHERE THE SURROUND IS PAPER.  The ring
# test stays on art-to-the-fold pages: a punch that cannot be located with
# confidence there is left, and the page is recorded, not smeared.


def punch_priors(geoms):
    """(median fold distance from the inner frame edge in mm, median template
    shift in mm) over the pages whose fold came from the holes."""
    dist, shift = [], []
    for g in geoms:
        f = g["fold"]
        if f["source"] != "holes" or not f["poly"] or not f["holes"]:
            continue
        w, h = g["sheet_px"]
        x = float(np.polyval(f["poly"], h / 2.0))
        dist.append((w - 1 - x) / MM if g["parity"] == "even" else x / MM)
        m, _, sh = template_score([c[1] for c in f["holes"]])
        if sh is not None:
            shift.append(sh)
    return float(np.median(dist)), float(np.median(shift)), float(np.percentile(dist, 5))


# A FOLD THAT DID NOT COME FROM THE HOLES IS NOT A FOLD.  MEASURED on 8701:
# the colour-boundary fallback put p092's fold 1.2 mm from the inner frame edge
# and p178's 0.8 mm -- it found the FAR side of the neighbour's white margin --
# and a page with no fold at all (p103, p111, p120, p147, p179) defaulted to
# the frame edge.  On a page anchored on its edges the window IS placed on the
# fold, so each of those masters was shifted about 10 mm into the neighbour's
# margin and lost the same at its outer trim (owner: "p92 cut wrong",
# "178/179 were cropped wrong. the black vs. white is the border").
# The clip is rigid, so where the holes did not give the fold, it is placed:
#   - on a FULL-BLEED page, where the ink stops (owner's ruling): per row, the
#     first run of FOLD_INK_RUN_MM that is >= FOLD_INK_FRAC ink, counted from
#     the inner frame edge; the neighbour's sparse type in its margin never
#     makes such a run.  MEASURED: p178 at x 5000 (ink ends 4984 by eye),
#     p179 at 237 (248), p147 8.4 mm in.
#   - otherwise, and wherever the ink stop or a colour fold lands outside
#     FOLD_BAND_MM of the issue's median hole-fold distance: AT that median.
#     MEASURED hole folds p5-p95 8.2-12.5 mm, median 10.26.
# A colour fold INSIDE the band is kept: p014/046/050 at 10.4-11.2 mm agree
# with the holes.  The ink stop reads 0 where the bed or the neighbour's own
# ink runs to the frame edge (p001, p029), which the band rejects.
FOLD_BAND_MM = 3.0           # accepted within this of the issue median hole-fold distance
FOLD_INK_BAND_MM = 25.0      # search this far in from the inner frame edge
FOLD_INK_RUN_MM = 3.0        # a run this long...
FOLD_INK_FRAC = 0.85         # ...this much ink is this page's art
FOLD_INK_LUM = 170           # ink: darker than this
FOLD_INK_CHROMA = 40         # ...or this saturated


def ink_stop_mm(rgb, par):
    """Median distance (mm) from the inner frame edge to where this page's ink starts, or None."""
    h, w = rgb.shape[:2]
    lum = rgb.mean(2)
    chroma = rgb.max(2).astype(int) - rgb.min(2)
    ink = (lum < FOLD_INK_LUM) | (chroma > FOLD_INK_CHROMA)
    b, run = int(FOLD_INK_BAND_MM * MM), int(FOLD_INK_RUN_MM * MM)
    strip = ink[:, w - b:][:, ::-1] if par == "even" else ink[:, :b]
    xs = []
    for y in range(int(h * .05), int(h * .95), 20):
        c = np.convolve(strip[y].astype(float), np.ones(run) / run, mode="valid")
        idx = np.flatnonzero(c >= FOLD_INK_FRAC)
        if len(idx):
            xs.append(idx[0])
    if len(xs) < 20:
        return None
    xs = np.asarray(xs, float)
    med = np.median(xs)
    return float(np.median(xs[np.abs(xs - med) < 1.5 * MM])) / MM


def fold_fallback(g, rgb, priors):
    """Re-place a fold that did not come from the holes; return a NOTE or None."""
    f = g["fold"]
    if f["source"] in ("holes", "inkstop", "p5", "median"):
        return None                                       # from the holes, or placed by a previous cut
    w, h = g["sheet_px"]
    dist_mm = priors[0]
    cur = None
    if f["poly"]:
        x = float(np.polyval(f["poly"], h / 2.0))
        cur = (w - 1 - x) / MM if g["parity"] == "even" else x / MM
    src, new = None, None
    if g["edges"]["source"] in ("fullbleed", "narrow"):
        d = ink_stop_mm(rgb, g["parity"])
        if d is not None and abs(d - dist_mm) <= FOLD_BAND_MM:
            src, new = "inkstop", d
    if new is None:
        if cur is not None and abs(cur - dist_mm) <= FOLD_BAND_MM:
            return None                                   # a colour fold that agrees
        # WHERE THE LINE ONLY MASKS, GUESS ON THE REVERSIBLE SIDE.  On a page
        # anchored on its wordmark the window is already right and the fold
        # only decides the neighbour-side mask.  Too far IN paints this page's
        # own inner margin white -- invisible and irreversible; too far OUT
        # leaves a sliver of the neighbour's margin, which the strip and BED
        # checks can see.  So a logo-anchored page takes the p5 of the hole
        # folds; an edges-anchored page, where the line PLACES the window and
        # the error is symmetric, takes the median (control, 2026-11-03).
        if g.get("anchor"):
            src, new = "p5", priors[2]
        else:
            src, new = "median", dist_mm
    x = (w - 1 - new * MM) if g["parity"] == "even" else new * MM
    f["poly"] = [0.0, float(x)]
    f["tilt_deg"] = 0.0                                   # a placed line is vertical
    old = f["source"]
    f["source"] = src
    return (f"FOLD re-placed ({old} -> {src}): {new:.2f} mm from the inner frame edge"
            + ("" if cur is None else f", was {cur:.2f} mm")
            + f" (issue median hole fold {dist_mm:.2f} mm, band +-{FOLD_BAND_MM})")


def fill_punches(g, gray, priors):
    """Add every visible clip punch to g["fold"]["holes"]; return (kept, found, none)."""
    w, h = g["sheet_px"]
    f = g["fold"]
    dist_mm, shift_mm = priors[0], priors[1]
    if f["poly"]:
        fold_x = lambda y: float(np.polyval(f["poly"], y))
        win_x = PUNCH_WIN_X_MM
    else:
        x = (w - 1 - dist_mm * MM) if g["parity"] == "even" else dist_mm * MM
        fold_x = lambda y: x
        win_x = PUNCH_WIN_X_MM + 2.0                    # the median, not this page's line
    own = [c for c in f["holes"]]
    if own:
        _, _, sh = template_score([c[1] for c in own])
        shift = sh if sh is not None else shift_mm
        win_y = PUNCH_WIN_Y_MM
    else:
        shift = shift_mm
        win_y = PUNCH_WIN_Y_MM + HOLE_TEMPLATE_Y0_TOL_MM
    kept = found = none = 0
    cands = {}                                   # row index -> [(px, py, d)]
    for j, t in enumerate(HOLE_TEMPLATE_MM):
        ty = (shift + t) * MM
        if any(abs(c[1] - ty) <= HOLE_FILL_NEAR_MM * MM for c in own):
            kept += 1
            cands[j] = None
            continue
        tx = fold_x(ty)
        x0, x1 = int(max(tx - win_x * MM, 0)), int(min(tx + win_x * MM, w))
        y0, y1 = int(max(ty - win_y * MM, 0)), int(min(ty + win_y * MM, h))
        cands[j] = []
        if x1 - x0 < 10 or y1 - y0 < 10:
            continue
        win = gray[y0:y1, x0:x1].astype(np.float32)
        local = ND.uniform_filter(win, int(HOLE_BG_MM * MM) | 1)
        dark = (win < local - PUNCH_DIP) & (win < PUNCH_ABS_MAX)
        lab, _ = ND.label(dark)
        for i, sl in enumerate(ND.find_objects(lab), 1):
            if sl is None:
                continue
            if sl[0].start == 0 or sl[1].start == 0 or sl[0].stop == win.shape[0] or sl[1].stop == win.shape[1]:
                continue                                 # runs out of the window: ink
            hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            d = max(hh, ww) / MM
            if d < PUNCH_MIN_MM or d > PUNCH_MAX_MM:
                continue
            r = int(PUNCH_RING_MM * MM)
            ry0, ry1 = max(sl[0].start - r, 0), min(sl[0].stop + r, win.shape[0])
            rx0, rx1 = max(sl[1].start - r, 0), min(sl[1].stop + r, win.shape[1])
            ring = dark[ry0:ry1, rx0:rx1].copy()
            ring[sl[0].start - ry0:sl[0].stop - ry0, sl[1].start - rx0:sl[1].stop - rx0] = False
            if ring.mean() > PUNCH_RING_DARK_MAX:
                continue                                 # sits in ink, not on paper
            cy, cx = ND.center_of_mass(lab[sl] == i)
            cands[j].append((float(x0 + sl[1].start + cx), float(y0 + sl[0].start + cy), float(d)))
    # the row: this page's own shift where it has detected holes; otherwise
    # the shift two or more candidates agree on
    if not own:
        offs = [(c[1] / MM - HOLE_TEMPLATE_MM[j]) for j, cs in cands.items() if cs for c in cs]
        best = None
        for o in offs:
            n = len({j for j, cs in cands.items() if cs
                     for c in cs if abs(c[1] / MM - HOLE_TEMPLATE_MM[j] - o) <= PUNCH_ROW_TOL_MM})
            if n >= 2 and (best is None or n > best[0]):
                best = (n, o)
        shift = best[1] if best else None
    for j, cs in cands.items():
        if cs is None:
            continue
        ok = []
        if shift is not None:
            ty = (shift + HOLE_TEMPLATE_MM[j]) * MM
            for px, py, d in cs:
                if abs(py - ty) > PUNCH_ROW_TOL_MM * MM:
                    continue
                if f["poly"] and abs(px - fold_x(py)) > PUNCH_FOLD_TOL_MM * MM:
                    continue
                ok.append((abs(py - ty), px, py, d))
        if ok:
            _, px, py, d = min(ok)
            f["holes"].append([px, py, max(d, PUNCH_FILL_MIN_MM)])
            found += 1
        else:
            none += 1
    return kept, found, none


# PIN THE WINDOW WHERE A WRONG EDGE COSTS CONTENT; LET THE SLACK FALL WHERE IT
# ONLY FABRICATES WHITE (owner, 2026-11-03).  At the gutter both directions of
# error cost content: short of the fold loses this page's own ink, past it
# brings in the neighbour's (8701 p178 carried 10.4 mm of p179 with readable
# type; p009/p010/p016 lost 1.3-2.7 mm of their inked gutter).  At the
# fore-edge a window placed from the fold can only OVERHANG -- it is a fixed
# 210 mm and no page is wider -- so its error there is white over blank paper.
# The wordmark does not remove the print-to-trim offset; it only chooses where
# the error lands, and it splits it across both edges including the costly one.
# MEASURED: the wordmark-to-fold distance is BIMODAL, split at the centre
# spread -- about 187.3 mm on pages of the front half, 183.5 mm on the back
# half, sd ~1 mm within each -- in 8701, 8611 and 8612 alike (8611/8612 from
# their cut-time sidecars under /Users/mist/DNB/861x/tmp/geometry, re-measured
# on 16 pages with this code to 0.00 mm).  One (S, B) per parity sits between
# the modes: on 8701, 92 of 115 pages with a certified fold were >= 0.5 mm off
# it under the wordmark; placed on the fold, 0 lost type at either edge, 39
# gained 0.5-4.2 mm of white beyond the scan frame at the fore-edge.
# So x comes from the fold wherever the fold is CERTIFIED; y stays on the
# wordmark (logo to bottom trim is unimodal, sd ~0.9 mm: head and foot are
# trimmed on the folded stack, common to both pages of a sheet).  A fold that
# is not certified keeps the wordmark's x, and the FOLD GATE says LOOK AT.
# 8609-8612 were cut on the wordmark and are NOT re-cut (owner: a pass over old
# issues is theirs to start).
FOLD_CERT_TEMPLATE = 4       # clip-template rows matched, at least
FOLD_CERT_MM = (6.0, 14.0)   # from the inner frame edge (hole folds measured 8.1-13.3)
FOLD_GATE_MM = 0.5           # master gutter edge vs the certified fold


def fold_mid_x(geom):
    w, h = geom["sheet_px"]
    return float(np.polyval(geom["fold"]["poly"], h / 2.0)) if geom["fold"]["poly"] else None


def fold_certified(geom):
    """The fold is from the clip's holes, matches the template, and sits where folds sit."""
    f = geom["fold"]
    x = fold_mid_x(geom)
    if f["source"] != "holes" or x is None or (f.get("template") or 0) < FOLD_CERT_TEMPLATE:
        return False
    w, _ = geom["sheet_px"]
    d = (w - 1 - x) / MM if geom["parity"] == "even" else x / MM
    return FOLD_CERT_MM[0] <= d <= FOLD_CERT_MM[1]


def fold_gate(geom, x0, logo_x0):
    """(verdict, note): the master's gutter edge against the certified fold."""
    x = fold_mid_x(geom)
    if not fold_certified(geom):
        return "LOOK AT", (f"FOLD GATE: LOOK AT -- the fold is not certified "
                           f"({geom['fold']['source']}), so nothing checks the gutter edge")
    gutter = x0 + MASTER_W_PX if geom["parity"] == "even" else x0
    off = (gutter - x) / MM
    extra = "" if logo_x0 is None else f"; the wordmark would have put it {(logo_x0 - x0) / MM:+.2f} mm"
    if abs(off) <= FOLD_GATE_MM:
        return "PASS", f"FOLD GATE: pass, gutter edge {off:+.2f} mm from the fold{extra}"
    return "LOOK AT", (f"FOLD GATE: LOOK AT -- gutter edge {off:+.2f} mm from the "
                       f"certified fold (> {FOLD_GATE_MM}){extra}")


# THE GATE ABOVE MEASURES ITS OWN ARITHMETIC ON A CERTIFIED PAGE: x0 was set
# from the fold, so "gutter vs fold" is zero by construction (control,
# 2026-11-03).  It only says whether anything vouches for the gutter.  What
# reads the ARTEFACT is the gutter white margin of the cut master -- master
# edge to this page's first ink, the GUTTER_MARGIN_PCT percentile over rows --
# against the median of its own half's certified pages.  A window past the
# fold shows as too much white (8701 p110/p112 on the plain fit: 12.2 / 11.6 mm
# against the back half's 8.7); a window short of it eats the margin.  Ink to
# the gutter (art, a bleed) reads under GUTTER_ART_MM and is reported apart:
# it cannot be told from a cut margin by the master alone.
GUTTER_STRIP_MM = 30.0       # look this far in from the gutter edge
GUTTER_INK_LUM = 140         # ink: darker than this (grey of the master)
GUTTER_MARGIN_PCT = 5        # percentile over rows of the first-ink distance
GUTTER_ART_MM = 3.0          # a margin under this is ink to the gutter
GUTTER_MAD_K = 4.0           # LOOK AT beyond this many MADs of the certified pages


def gutter_margin_mm(master, parity):
    """Master edge to first ink at the gutter, mm (percentile over rows), or None."""
    g = master[::2, ::2].mean(2)                              # 300 dpi grey
    n = int(GUTTER_STRIP_MM * MM / 2)
    y0, y1 = int(g.shape[0] * .06), int(g.shape[0] * .94)
    strip = g[y0:y1, -n:][:, ::-1] if parity == "even" else g[y0:y1, :n]
    # a speck at the edge is not a margin: 8701 p014's 1 px mark at the gutter
    # read 0.17 mm against a 10.4 mm margin until opened away
    ink = ND.binary_opening(strip < GUTTER_INK_LUM, np.ones((3, 3), bool))
    has = ink.any(1)
    if has.sum() < 50:
        return None
    return float(np.percentile(np.argmax(ink, 1)[has], GUTTER_MARGIN_PCT)) / (MM / 2)


def gutter_verdicts(margins, certified, n_pages):
    """{page: verdict}, and the per-half baseline: median and MAD over the
    certified pages whose margin is not ink to the gutter."""
    base = {}
    for half in ("front", "back"):
        v = [m for s, m in margins.items() if s in certified and m is not None
             and m >= GUTTER_ART_MM and ((int(s) <= n_pages // 2) == (half == "front"))]
        if v:
            med = float(np.median(v))
            base[half] = (med, float(np.median(np.abs(np.asarray(v) - med))) * 1.4826)
    out = {}
    for s, m in margins.items():
        half = "front" if int(s) <= n_pages // 2 else "back"
        if m is None:
            out[s] = "no ink in the gutter strip"
        elif m < GUTTER_ART_MM:
            out[s] = "ink to the gutter"
        elif half in base and abs(m - base[half][0]) > GUTTER_MAD_K * base[half][1]:
            out[s] = f"LOOK AT: {m - base[half][0]:+.2f} mm off the {half} half's mode"
        else:
            out[s] = "ok"
    return out, base


def half_of(geom, n_pages):
    return "front" if geom["page"] <= n_pages // 2 else "back"


def half_offsets(geoms, fit):
    """Median (wordmark-placed x0 - fold-placed x0) in px per (half, parity),
    over the logo pages with a certified fold."""
    acc = {}
    for g in geoms:
        if not g["anchor"] or not fold_certified(g):
            continue
        fx = fold_mid_x(g)
        lx = g["anchor"]["x"] - fit[g["parity"]][0]
        f0 = fx - MASTER_W_PX if g["parity"] == "even" else fx
        acc.setdefault((half_of(g, len(geoms)), g["parity"]), []).append(lx - f0)
    return {k: float(np.median(v)) for k, v in acc.items()}


def cut_page(geom, fit, sheet600, halves=None, n_pages=None):
    """The master: sheet600 with the unknown painted white, cut to the window."""
    notes = list(geom["notes"])
    w, h = geom["sheet_px"]
    source, ax, ay = anchor_of(geom)
    logo_x0 = None
    if source == "logo":
        S_, B_ = fit[geom["parity"]]
        x0, y0 = int(round(ax - S_)), int(round(ay - B_))
        if fold_certified(geom):
            logo_x0 = x0
            fx = fold_mid_x(geom)
            x0 = int(round(fx - MASTER_W_PX if geom["parity"] == "even" else fx))
        elif halves:
            # NO CERTIFIED FOLD: the wordmark, less its own half's offset.  The
            # one (S, B) per parity sits between the two modes, so a back-half
            # page placed on it alone is ~4 mm off (8701 p110/p112: gutter
            # margin 12.2/11.6 mm against the half's 8.7).
            k = (half_of(geom, n_pages), geom["parity"])
            if k in halves:
                x0 = int(round(x0 - halves[k]))
                notes.append(f"WINDOW x: no certified fold -- the wordmark, corrected by "
                             f"the {k[0]}-half {k[1]} median wordmark-to-fold offset "
                             f"{halves[k] / MM:+.2f} mm")
    else:
        x0, y0 = int(round(ax)), int(round(ay))
    verdict, gnote = fold_gate(geom, x0, logo_x0)
    notes.append(gnote)
    geom["_gate"] = (verdict, None if logo_x0 is None else (logo_x0 - x0) / MM)
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
    # WHAT THE PIXELS SAY, not what the trace thought.  `unknown` is built from
    # the traced edges alone, so it can only report the trace's own view: on
    # 8701 p003/p004 it certified 2 % for masters that were 44 % bed.  So the
    # window is also read for BED that survived as "known": a run of columns
    # from either side edge, or of rows from the foot, that is backing in more
    # than BED_RUN_FRAC of its pixels (over all rows, not only the known ones,
    # so it errs toward not firing).  Ink to the trim can do this too
    # (a black full-bleed ad), which is why it is a LOOK AT and not a fill.
    raw = np.zeros((MASTER_H_PX, MASTER_W_PX, 3), np.uint8)
    if sy1 > sy0 and sx1 > sx0:
        raw[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = sheet600[sy0:sy1, sx0:sx1]
    bed = backing_mask(raw) & ~unk
    def edge_run(fr):
        n = int(np.argmin(fr > BED_RUN_FRAC)) if not (fr > BED_RUN_FRAC).all() else len(fr)
        return n / MM
    col = bed.mean(0)
    bed_mm = {"left": edge_run(col), "right": edge_run(col[::-1]),
              "foot": edge_run(bed.mean(1)[::-1])}
    if max(bed_mm.values()) > BED_RUN_LOOK_MM:
        notes.append("BED in the window: " + ", ".join(
            f"{k} {v:.1f} mm" for k, v in bed_mm.items() if v > BED_RUN_LOOK_MM)
            + " of backing-coloured pixels the trace calls page -- bed, or ink "
              "to the trim. LOOK AT")
    if source != "logo":
        notes.append("ANCHOR from the page edges (fold + bottom trim): the "
                     "wordmark was not found")
    return master, frac, notes


def cut():
    geoms = [json.loads(p.read_text()) for p in sorted(OUT_GEOM.glob("[0-9][0-9][0-9].json"))]
    if not geoms:
        raise SystemExit(f"{VARIANT} cut: no geometry in {OUT_GEOM} -- run measure first")
    foot_med, foot_replaced, foot_out = fit_foot(geoms)
    print(f"foot: issue median {foot_med:.2f} mm; frame-row feet replaced: "
          f"{['%03d' % p for p in foot_replaced] or 'none'}; LOOK AT (> "
          f"{FOOT_OUTLIER_MM} mm from the median): "
          f"{[('%03d' % p, d) for p, d in foot_out] or 'none'}", flush=True)
    fit = fit_window(geoms)
    halves = half_offsets(geoms, fit)
    print("wordmark-to-fold, median per half and parity (mm): " + ", ".join(
        f"{k[0]} {k[1]} {v / MM:+.2f}" for k, v in sorted(halves.items())), flush=True)
    priors = punch_priors(geoms)
    print(f"punches: issue fold distance {priors[0]:.2f} mm, template shift "
          f"{priors[1]:.2f} mm", flush=True)
    OUT_MASTER.mkdir(parents=True, exist_ok=True)
    report = {"fit": {k: list(v) for k, v in fit.items() if k != "stats"},
              "half_offsets_mm": {f"{a} {b}": v / MM for (a, b), v in halves.items()},
              "stats": fit["stats"], "pages": {},
              "foot": {"median_mm": foot_med, "replaced": foot_replaced,
                       "outliers": foot_out}}
    look, margins = [], {}
    for g in geoms:
        stem = f"{g['page']:03d}"
        sheet = np.array(Image.open(OUT_SHEET600 / f"{stem}.png").convert("RGB"))
        fnote = fold_fallback(g, sheet, priors)
        if fnote:
            g.setdefault("notes", []).append(fnote)
            (OUT_GEOM / f"{stem}.json").write_text(json.dumps(g, indent=1))
        kept, found, none = fill_punches(g, sheet.mean(2), priors)
        if found:
            g.setdefault("notes", []).append(
                f"PUNCHES: {kept} detected, {found} more found at the clip "
                f"template's rows and filled, {none} not visible")
            (OUT_GEOM / f"{stem}.json").write_text(json.dumps(g, indent=1))
        master, frac, notes = cut_page(g, fit, sheet, halves, len(geoms))
        source, ax, ay = anchor_of(g)
        stamp = stamp_text(VARIANT, **{
            "page": f"{stem} of {ISSUE}", "phase": "cut",
            "master-px": f"{MASTER_W_PX} {MASTER_H_PX}",
            "skew": f"{g['skew']['angle']:+.2f} -> {g['skew']['residual']:+.2f} deg",
            "fold": f"{g['fold']['source']} n={g['fold']['n']}"
                    + (f" template {g['fold']['template']}" if g["fold"]["source"] == "holes" else "")
                    + (f" tilt {g['fold']['tilt_deg']:+.2f} deg" if g["fold"]["poly"] else ""),
            "holes": f"{len(g['fold']['holes'])} filled of {len(g['holes'])} candidates",
            # WHICH CLIP this page was fitted against, for the same reason the
            # grade-sha is here: a master carries no other record of it, and
            # applying the previous issue's clip fails silently at 4 of 6.
            "clip": f"{CLIP_SOURCE} y0 {HOLE_TEMPLATE_Y0_MM:.2f}"
                    f"+-{HOLE_TEMPLATE_Y0_TOL_MM:.2f}mm "
                    + " ".join(f"{v:.2f}" for v in HOLE_TEMPLATE_MM),
            "anchor": (f"logo ({ax:.0f}, {ay:.0f}) score {g['anchor']['score']:.2f}"
                       if source == "logo" else
                       f"edges: window top-left ({ax:.0f}, {ay:.0f}) from fold + bottom trim"),
            "window": f"S {fit[g['parity']][0]} B {fit[g['parity']][1]} ({g['parity']})"
                      + ("" if source != "logo" or not fold_certified(g)
                         else " -- x from the certified fold, y from S B")
                      + ("" if source == "logo" else " -- not used: edges anchor"),
            "unknown": f"{frac:.2%} of the window is fabricated white",
            "notes": "; ".join(notes) or "(none)",
        })
        save_master(master, OUT_MASTER / f"{stem}.png", stamp)
        margins[stem] = gutter_margin_mm(master, g["parity"])
        (OUT_MASTER / f"{stem}.stamp.txt").write_text(stamp, encoding="utf-8")
        verdict, logo_off = g.pop("_gate")
        report["pages"][stem] = {"anchor": source, "fold": g["fold"]["source"],
                                 "unknown": frac, "fold_gate": verdict,
                                 "logo_minus_fold_x0_mm": logo_off}
        if verdict != "PASS":
            look.append(stem)
        print(f"p{stem}: anchor {source} | fold {g['fold']['source']} | "
              f"unknown {frac:.2%}" + "".join(f"\n      NOTE p{stem}: {n}" for n in notes),
              flush=True)
    certified = {s for s, v in report["pages"].items() if v["fold_gate"] == "PASS"}
    gv, base = gutter_verdicts(margins, certified, len(geoms))
    for s, v in report["pages"].items():
        v["gutter_margin_mm"], v["gutter"] = margins.get(s), gv.get(s)
    report["gutter"] = {"baseline_mm": {k: {"median": a, "sd_mad": b} for k, (a, b) in base.items()},
                        "k_mad": GUTTER_MAD_K,
                        "look_at": [s for s, v in gv.items() if v.startswith("LOOK AT")],
                        "ink_to_gutter": [s for s, v in gv.items() if v == "ink to the gutter"]}
    offs = [v["logo_minus_fold_x0_mm"] for v in report["pages"].values()
            if v["logo_minus_fold_x0_mm"] is not None]
    report["fold_gate"] = {"look_at": look, "logo_minus_fold_x0_mm": {
        "n": len(offs), "median": float(np.median(offs)) if offs else None,
        "sd": float(np.std(offs)) if offs else None,
        "off_ge_0.5mm": sum(abs(o) >= FOLD_GATE_MM for o in offs)}}
    (OUT_GEOM / "fit.json").write_text(json.dumps(report, indent=1))
    print("fit:", json.dumps(report["fit"]), json.dumps(report["stats"]), flush=True)
    print(f"FOLD GATE: {len(look)} page(s) LOOK AT: {' '.join(look) or 'none'}; "
          f"the wordmark would have been >= {FOLD_GATE_MM} mm off the fold on "
          f"{report['fold_gate']['logo_minus_fold_x0_mm']['off_ge_0.5mm']} of {len(offs)} "
          f"fold-placed pages", flush=True)
    gl = report["gutter"]
    print("GUTTER MARGIN (the master's pixels): baseline " + ", ".join(
        f"{k} {v['median']:.2f} mm (sd {v['sd_mad']:.2f})" for k, v in gl["baseline_mm"].items())
        + f"; {len(gl['look_at'])} page(s) beyond {GUTTER_MAD_K} sd LOOK AT: "
        + (" ".join(f"{s} ({report['pages'][s]['gutter_margin_mm']:.2f})" for s in gl["look_at"]) or "none")
        + f"; ink to the gutter: {' '.join(gl['ink_to_gutter']) or 'none'}", flush=True)


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
