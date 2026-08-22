#!/usr/bin/env python3
"""
Step 005, SHEET variant -- raw 2400 dpi scan -> the 600 dpi masters r010 reads.

This is the first step of the chain.  It owns everything between the scanner and
`r010_ocr_blocks.py`, and it exists in two mutually exclusive variants selected
by the issue descriptor's `binding`:

    r005_masters_spread   the frame holds a clipped SPREAD  (8609, the monthlies)
    r005_masters_sheet    the frame holds one loose SHEET   (SH8601)   <- this file

The suffix NAMES THE VARIANT.  It is not a step inserted after another one --
this directory's history has suffixes (`9b`) as the symptom of bad numbering,
and that is not what is happening here.  Exactly one variant runs for a given
issue; the other is recorded in the issue's LOG.md as not applicable.

What this variant is for.  SH8601's sheets were TORN OFF A GLUED SPINE, one A4
sheet per scan.  Measured on the raw scans:

    residual skew           up to 1.08 deg (p092); the pages are NOT levelled
    edge tilt after level.  0.14-1.12 deg -- the sheet was guillotined at its
                            own angle, so the paper edges are NOT parallel to
                            the type
    outer edge              guillotine-clean, hard contrast against a near-black
                            bed
    inner edge              TORN: a fringe of fibres standing proud of the paper
                            body, wandering down the page
    torn side               follows parity -- a verso tears on the right, a
                            recto on the left
    beyond the sheet        black bed, and a saturated yellow prop further out

The pipeline:

    scan_dir/NNN.png
      -> measure skew on the 150 dpi thumb (projection variance, scale-invariant)
      -> rotate to level, then RE-MEASURE and assert the residual is ~0
      -> paper mask: distance from the profile's paper white
      -> TRACE each page edge as a line
           clean edges  -> band medians of the per-row/col paper boundary
           verso fringe -> band 5th percentile of per-row paper ends
           recto fringe -> NOT traced: one vertical line at p95 of paper starts
                           plus ~1 mm
      -> fill everything outside the traced page with paper white
      -> drop bed components that touch the frame AND lie mostly outside the page
      -> separate to CMYK with tools/img/cmyk_reconstruction  (see THE GRADE)
      -> two renders off that ONE separation: the OCR master carries a
         black-point curve, the figure master is the straight ICC render
      -> <tmp>/masters600/NNN.png, <tmp>/figures600/NNN.png,
         <tmp>/cmyk2400/NNN.tif, <tmp>/debug600/NNN.png, and beside each master
         the STAMP that says which profile produced it

A page whose stock this issue's paper white does not describe -- the folded A3
cover leaf (001, 002, 147, 148) and the bound-in Zahlkarte (149-152) -- has its
edges found from INK vs BED instead, and the switch is the measured paper
fraction, not a page number.  See FULLBLEED_PAPER_FRAC.

Why the edges are TRACED and not cropped to.  Levelling the text leaves the
paper edges tilted, so an axis-aligned crop inscribed in the page gives up
0.5-3.6 mm PER EDGE (measured on 041, 056, 092).  Cropping was tried first and
cost too much.  So each edge becomes a line and everything outside it is filled
with paper white.  The fill IS fabrication, and it is deliberate and explicit:
the wedge outside a traced edge is paper that the scan frame did not contain.

ACCEPTED LOSS, decided explicitly: where the tear ran into the type area those
characters are gone.  Accepted -- it is a fact about this copy, not a defect of
this step.

KNOWN DEFECT, closed: the prototype left a sliver of bed and prop in p092's
corner, where two fitted lines meet and the bed component read as mostly inside
the page.  Excluding the yellow prop from the PAPER MASK (see PROP_YELLOW_MIN)
moved the foot trace onto the real trim and the sliver is gone.

WHAT THIS VARIANT CANNOT DO: separate the bed from a page whose own ink is as
dark as the bed and runs to the trim.  p117 is that page -- a te-wi ad on a
full-bleed dark-brown ground -- and BOTH edge finders fail on it: the paper mask
traces the ad's cream PANEL (169 x 268 mm) and the ink/bed flood walks into the
brown ground (170 x 115 mm).  It fails the size gate, which is the right
outcome; it is one A4 page that cannot be traced, not a size class.  See
r005_masters_sheet.md.

No CLI flags, no environment knobs -- see the README.  The only per-issue knob is
ISSUE below; everything else comes from the issue descriptor.  Page numbers are
positional arguments purely so the work can be split across processes, exactly
as in r010.
"""

import hashlib
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin
from scipy import ndimage as ND
from scipy.ndimage import rotate as scipy_rotate

import r000_issue

Image.MAX_IMAGE_PIXELS = None  # the raw scans are ~580 megapixels

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see ../README.md)
#
# Everything describing PAPER is written in millimetres and converted once, so
# the numbers stay readable against a ruler and survive a change of resolution.
# ---------------------------------------------------------------------------

# The one per-issue knob lives in r000_issue.py and is IMPORTED, never declared
# here: it used to sit at the top of all seven programs, and seven copies of one
# value is six chances for a half-swapped chain.  Every path below comes from
# issues/<ISSUE>/issue.json.
from r000_issue import ISSUE

# The descriptor's `binding` names the variant, and this file IS the "sheet"
# one.  A "spread" issue -- the frame holds a clipped spread, as 8609's scans do
# -- belongs to r005_masters_spread, which is a different geometry problem
# (facing-page colour boundary, clip holes as fallback, hole inpainting).  The
# check below is not defensive politeness: run on a spread this would trace the
# facing page's outer edge as this page's inner one and fill the whole of one
# page with paper white.
BINDING = "sheet"

# --- resolutions -----------------------------------------------------------
# The scans are ~2400 dpi (20232x28751).  The masters are 600 dpi: r010 wants
# 300 dpi for tesseract and takes a clean 2:1 box filter down to it, and r145
# wants the extra stop for figure crops.  4 is an exact integer reduction, so
# no resampling filter touches the ink on the way down.
SCAN_DPI = 2400
MASTER_DPI = 600
SCAN_REDUCE = SCAN_DPI // MASTER_DPI          # 4
THUMB_DPI = 150                               # the thumb/ renders beside the scans
MM = MASTER_DPI / 25.4                        # px per mm in master space
THUMB_MM = THUMB_DPI / 25.4                   # px per mm in thumb space

# --- skew ------------------------------------------------------------------
# Skew is measured on the 150 dpi THUMB, not on the master.  The measurement is
# a projection-variance score, which is scale-invariant, and the thumb is 256x
# smaller: measuring on the master would cost minutes per page and answer the
# same.  Coarse sweep first, then a fine sweep around the winner.
SKEW_COARSE = (-3.0, 3.0, 0.2)                # deg: from, to, step
SKEW_FINE_SPAN, SKEW_FINE_STEP = 0.3, 0.02    # deg around the coarse winner
# The score is computed on a crop that excludes the sheet edges and the bed:
# the bed/paper boundary is a huge straight contrast step and would otherwise
# dominate the projection profile and measure the GUILLOTINE angle instead of
# the type angle.  Fractions of the frame.
SKEW_CROP = (0.06, 0.95, 0.04, 0.96)          # top, bottom, left, right
# "Ink" for the skew measurement: this far below the crop's own mean, in units
# of its own standard deviation.  Deliberately loose -- the score only needs the
# text lines to show up as rows, not a clean binarisation.
SKEW_INK_SIGMA = 0.4

# THE ROTATION SIGN TRAP.  scipy.ndimage.rotate (which MEASURES) and
# PIL.Image.rotate (which APPLIES) turn in opposite directions in array space.
# Feeding the measured angle through with the wrong sign DOUBLED the skew on
# p056, to -1.28 deg, and every downstream geometry check still passed because
# nothing re-measured.  So the residual is re-measured on the levelled page and
# asserted here.  Measured residuals after levelling: |0.02| deg or better.
SKEW_RESIDUAL_MAX = 0.10                      # deg

# --- the torn side must match parity (the issue-level gate) -----------------
# A guillotined edge is straight to within a pixel row; a torn edge jitters from
# row to row.  Mean |difference| between consecutive rows' paper boundary, in
# thumb pixels, separates them.
#
# The gate is: parity decides, and a CONFIDENT disagreement is a failure -- a
# page that is misfiled or mis-rotated, which is expensive to discover after a
# full-resolution sweep.  Ambiguity passes.
#
# RE-MEASURED over all 152 thumbs after colors.txt was re-measured, because this
# gate reads the PAPER mask and a new paper white is a new mask.  Of the 144
# pages that have a paper edge to read (the other 8 go to the ink/bed finder and
# are not asked), 143 agree with parity, and they agree LOUDLY: the smallest
# ratio among them is 2.73, the median 11.98.  Exactly one disagrees -- p117, at
# 1.64, which is below every single agreeing page.  There is a clean gap between
# 1.64 and 2.73 and the floor goes in it.
#
# The old floor was 1.6, measured against the OLD paper white, where the
# agreeing pages started at 1.6 and two pages disagreed at 1.33 and 1.45.  With
# the corrected W the separation is four times wider, and leaving the floor at
# 1.6 would fail p117 for being misfiled -- which it is not.  p117 is a page
# whose paper mask sees only the cream panel inside a full-bleed dark ground, so
# its jitter measurement means nothing; it fails the size gate two steps later,
# which is the check that can actually say what is wrong with it.
TORN_CONFIDENT_RATIO = 2.5

# --- the paper mask --------------------------------------------------------
# A pixel is paper if its city-block distance from the profile's paper white is
# under this AND it is not the prop (below).  MEASURED: paper white is uniform
# across the sheet (a 3x3 grid of paper p90 varies by <=4 levels), so one global
# threshold is enough and there is no vignette to correct.  110 sits well clear
# of the black bed and still admits a lightly screened tint as paper.
PAPER_DIST = 110
# THE PROP IS NOT PAPER, AND A DISTANCE BALL CANNOT SAY SO.  City-block distance
# has no notion of hue, and the yellow prop under the sheet reads (237,205,111)
# on p006 -- distance 108 from W(214,195,186), i.e. INSIDE the ball.  The foot
# trace then ran into the prop and left 7 mm of prop and bed shadow standing at
# the bottom of the master, and the same 7 mm stands in the prototype's output.
#
# The separating measurement is G - B, which is how yellow a bright pixel is.
# MEASURED on the 006/041/056/092 thumbs: among pixels the distance test calls
# paper, G - B is 11 at p50 and 22-26 at p99 -- the paper is warm, not yellow.
# Across the prop it is 99-107.  Nothing lives between, so the threshold sits in
# the middle of a gap 70 levels wide.
#
# It must NOT be the looser test the prototype used for the bed flood
# (R+G > 300 AND B < 160 AND bright).  That one also matches ordinary warm paper
# -- (215,174,154) passes it -- which cost nothing there, because the flood only
# ever looked at frame-connected components that were mostly outside the page,
# but takes 6% of the sheet out of the paper mask if it is reused here.
PROP_YELLOW_MIN = 50        # G - B
PROP_LUM_MIN = 120          # ...and the prop is bright; the bed is not
# A row (column) is part of the page body only if this much of it is paper.
# Rows above the top edge or below the foot are mostly bed and must not
# contribute an edge sample.
BODY_PAPER_FRAC = 0.5

# --- the pages this issue's paper white does not describe: INK vs BED -------
# Tracing by paper colour needs paper.  MEASURED over all 152 thumbs -- the
# fraction of the frame's rows (and columns) that are more than BODY_PAPER_FRAC
# paper, smaller of the two, sorted:
#
#     001 0.000   002 0.001   147 0.001   148 0.015
#     150 0.018   151 0.024   149 0.026   152 0.027
#     -------------------------------------------------- and then nothing until
#     067 0.167   079 0.181   007 0.247   006 0.317  ...  146 0.968
#
# EIGHT pages, and a gap of 0.14 to the ninth.  They are the folded A3 COVER
# LEAF (001, 002, 147, 148) and the bound-in ZAHLKARTE (149-152), and the reason
# is not only full bleed -- 148 has ordinary white margins.  It is that neither
# is printed on THIS ISSUE'S PAPER: the cover leaf and the card are a coated
# white stock, and the profile's W (209 175 157) describes the interior's
# yellowed sheet, so a coated white sits 100+ levels of city-block distance away
# and the paper mask does not see it as paper at all.
#
# For those eight the edge comes from INK vs BED instead: the bed is near-black
# and uniform, a printed sheet is not, and the sheet is ONE CONNECTED REGION
# touching nothing else.  Same BED_LUM, same prop test, same trace() -- what
# changes is only which mask the boundaries are read off.
#
# THE SWITCH IS THE MEASUREMENT ABOVE, NOT A PAGE NUMBER.  A page number would
# be a lie about why the page is different and would not survive a re-scan; the
# floor sits in the middle of a gap five times its own width.
FULLBLEED_PAPER_FRAC = 0.10
# ...and the sheet must be found as a SOLID region: a one-pixel bridge is not
# part of a sheet.  On p151 the card connects to the lit top edge of the yellow
# prop through a 3 px strip at the frame's left margin, and the traced foot then
# lands 94 mm below the card -- a 205 mm card measured as 299.  An opening
# of this radius breaks every such bridge; MEASURED on all eight pages, p151 is
# the only one whose traced size moves by more than 1 mm.
SHEET_OPEN_MM = 1.0

# --- tracing the edges -----------------------------------------------------
# The edge samples are binned into this many bands down (or across) the page and
# one statistic is taken per band, then a straight line is fitted through the
# band statistics.  Bands rather than raw samples because a single row can be
# arbitrarily bad and a least-squares fit has no defence against it.
TRACE_BANDS = 24
# PER-COLUMN EXTREMES ARE NOT AN EDGE.  "The last paper row in this column" is
# dragged outward by a few paper-coloured pixels in the bed transition, and left
# 3.8 mm of bed at the foot of p056.  A clean edge therefore comes from the band
# MEDIAN of the boundary, which those few pixels cannot move.
CLEAN_PCT = 50
# The torn fringe is the opposite problem: fibres stand PROUD of the paper body,
# so the median boundary sits out in the fringe.  A low percentile lands on the
# paper body instead and cuts the fringe off.
FRINGE_PCT = 5
# ROWS THAT CROSS FULL-BLEED ART ARE NOT EDGE SAMPLES.  Their "last paper pixel"
# collapses hundreds of px inward, and unfiltered they tilted p056's traced
# fringe by +2.56 deg.  Drop any sample further than this from the median before
# the bands are formed.
TRACE_OUTLIER_MM = 12.0
# How far INSIDE its own traced line each edge is placed, so the line's own
# width and the last of the bed/fringe transition fall outside the page.
CLEAN_INSET_MM = 0.3
FRINGE_INSET_MM = 0.3
# THE RECTO FRINGE IS NOT TRACED.  On a verso the tear sits inside the frame and
# wanders, so it has to be traced.  On a RECTO it is flush with the frame edge:
# there is nothing to trace, a few px cut perfectly vertically is always enough,
# and a fitted line there fits noise -- it claimed +0.62 deg on p041, where the
# true edge is the frame.  So the recto's torn edge is ONE VERTICAL LINE at the
# 95th percentile of the per-row paper starts, plus this much.
RECTO_FLUSH_PCT = 95
RECTO_FLUSH_MM = 1.0

# --- dropping the bed ------------------------------------------------------
# A line fit cannot clear a corner sliver: where two edges meet, each line is
# extrapolated past its own samples and a wedge of bed can survive (p092's
# bottom-left).  Bed TOUCHES THE FRAME and is bed-COLOURED; printed ink, even
# full-bleed, is surrounded by paper.  So what is connected to the frame through
# bed-like pixels only is dropped -- that never reaches a red banner.
BED_LUM = 70                                  # 0-255; the scanner bed.  The prop
# is the other half of "not paper" and is defined with the paper mask above,
# because that is where its being mistaken for paper first does damage.
# ...but "touches the frame and is dark" ALSO describes a full-bleed PHOTO that
# runs off the torn edge.  On p006 the board picture connects to the bed through
# its own black chips, and an unconstrained flood erased a third of it.  So a
# component only goes if MOST OF IT LIES OUTSIDE the traced page.  A bed sliver
# is ~all outside; a photo is ~all inside.
BED_OUTSIDE_FRAC = 0.5

# --- the page, and the canvas it is placed on ------------------------------
# The traced page must come out one of the sizes THIS ISSUE ACTUALLY HAS.  A
# page that matches none of them means a traced line ran away, and the fill
# would then be eating type rather than bed.
#
# MEASURED, tracing all 152 thumbs -- paper-vs-bed where there is paper, ink-vs
# -bed on the eight where there is not:
#
#   A4 sheet     145 interior pages land in 205.0-212.4 x 294.3-298.3 mm (A4 to
#                within 5 mm across and 3 mm down), and so do three of the four
#                cover-leaf pages: 001 at 210.5x296.4, 147 at 215.4x296.6 and
#                148 at 209.7x296.6.
#   cover leaf   002 traces 223.7x296.3.  The cover is a FOLDED A3 SHEET and 002
#                is the inside of its front half, so the scan holds the whole
#                page PLUS ~14 mm of the FOLD FLAP -- paper, part of this sheet,
#                and kept.  001 and 147 have the same flap; their scan frames
#                simply cut it off, which is why they measure A4.  On all three
#                the sheet runs off the side of the frame, so these widths are
#                LOWER BOUNDS on the leaf and not measurements of a trim.
#   Zahlkarte    149-152, a bound-in payment card (Zahlkarte/Postueberweisung)
#                printed blue on a white card: 144.2x205.2, 144.4x205.1,
#                145.0x205.9 and 147.9x206.3 mm.  An A5 leaf (148x210) with the
#                frame cutting a few mm off two of its edges.  GENUINELY NOT AN
#                A4 PAGE and not a defect -- it passes as its own class rather
#                than failing a gate written for a different piece of paper.
#
# Each class is (name, width mm, height mm, tolerance mm).  The tolerance is per
# class because the evidence behind each is: 148 pages for A4, four for the
# card, one for the cover leaf.
PAGE_CLASSES = (
    ("A4 sheet",   210.0, 297.0, 6.0),
    ("cover leaf", 224.0, 297.0, 7.0),
    ("Zahlkarte",  146.0, 205.0, 6.0),
)
# Every master is the SAME size, because r010's block geometry and r145's figure
# crops share ONE coordinate system: if each page had its own width, a block's
# page-fraction would mean something different on every page.  The canvas is
# DERIVED from the classes above rather than measured separately, so that a page
# which passes the size gate cannot possibly overflow it -- two independent
# numbers here would eventually disagree and truncate a page quietly.  The
# shortfall is paper white: the same fabrication, and the same justification, as
# the wedge outside a traced edge.
#
# The page is anchored at its own top-left TRIM CORNER, which is the one
# landmark every sheet has in the same place relative to its type.
#
# It is derived from the WIDEST and TALLEST class, not from A4, so the invariant
# holds for every class: 231 x 304 mm, 5457 x 7181 px.  That is 15 mm wider than
# the canvas an A4-only issue would need, and it is the price of the cover
# leaf's fold flap fitting without being truncated -- every A4 page carries
# 15 mm more fabricated white on the right.  The alternative, a canvas per class, breaks
# the one thing r010 and r145 rely on: that a page fraction means the same
# thing on every page.
MASTER_W_MM = max(w + tol for _, w, _, tol in PAGE_CLASSES)
MASTER_H_MM = max(h + tol for _, _, h, tol in PAGE_CLASSES)

# --- the grade -------------------------------------------------------------
# The separation is NOT reimplemented here.  tools/img/cmyk_reconstruction does
# it, and colors.txt was written for it: 8 RGB anchors plus 4 per-ink level
# lines.  It works in the DENSITY domain -- d = -log10(rgb/W), six polynomial
# features, a least-squares solve against the seven ink targets, then full GCR
# (K = min(C,M,Y), subtracted from each).  Because the paper white is the density
# reference, the scan's global R/B 1.163 cast falls out for free.
CMYK_TOOL = "cmyk_reconstruction/target/release/cmyk_reconstruction"
ICC_CMYK = "USWebCoatedSWOP.icc"
ICC_RGB = "AdobeRGB1998.icc"

# `colors` is OPTIONAL in the descriptor.  With no profile the grade falls back
# to the built-in anchor set -- the eight anchors the old separation compiled in
# -- so an issue without a measured profile still renders.  They are COPIED here
# rather than imported: scan2mrc is retired and scan2ocr must not reference it.
# Named in cmyk_reconstruction's vocabulary, where R = M+Y, G = C+Y, B = C+M.
BUILTIN_ANCHORS = {
    "W": (201, 195, 188),
    "C": (38, 140, 165),
    "M": (192, 37, 66),
    "Y": (201, 159, 61),
    "R": (185, 34, 31),      # was COLOR_MY
    "G": (42, 109, 44),      # was COLOR_CY
    "B": (36, 44, 79),       # was COLOR_CM
    "K": (16, 17, 17),
}
# ...and with no profile there is nothing measured to stretch by, so the levels
# are the identity.  A level line is a per-ink contrast decision and must be
# MEASURED per issue; guessing one is how a page gets washed out.
BUILTIN_LEVELS = {"LC": (0, 100), "LM": (0, 100), "LY": (0, 100), "LK": (0, 100)}

# THE LEVELS ARE NOT TRUSTED, THEY ARE PROVEN.  SH8601's colors.txt as written
# has `LK 90 95`, which maps K's 229-242 window onto the full range: ordinary
# black text falls below the low point and is clipped toward ZERO INK, and 93% of
# the page snaps to pure white.  The page still looks like a page, which is what
# makes it dangerous -- nothing downstream can tell washed-out from clean.  So
# the grade is measured against the ungraded page it came from and the step FAILS
# rather than publishing it.
#
# A pixel counts as inked when it is this far below the graded paper white.
INK_CONTRAST = 60
# ...and this far, in city-block RGB distance, from the paper of the UNGRADED
# page.  "The paper" is the profile's W for a page printed on this issue's
# paper, and the SHEET'S OWN white for one that is not: on the coated cover leaf
# and the card, W is 100+ levels away from the stock, so measuring against it
# calls the whole blank sheet ink (p002: 85.7% of the page "inked" before the
# grade, p149: 39.5%) and the ink-keep gate then fails a perfectly good page for
# deleting paper.  This percentile of the pixels inside the traced page is that
# sheet's paper: high enough to sit in the paper rather than in the ink, low
# enough that a specular highlight cannot set it.
RAW_INK_DIST = 90
STOCK_PCT = 90
# The grade is MEASURED AND REPORTED, never gated -- see the long note where
# these numbers are computed.  A gate on ink-keep failed 10 of 152 pages on the
# first full sweep and was wrong on all 10: they were the issue's most
# tint-heavy pages, and a screened tint demodulating into a flat fill is the
# pipeline working, not ink loss.  Two numbers still go in the log every page,
# because the failure the gate was built for (the old LK 90 95 turning black
# type into blank paper) is loud enough for a human to see in a thumbnail:
INK_DARK_PCT = 5.0          # "the darkest ink" = this percentile of the page
# The graded paper white is measured on the page's OWN paper.  On a page printed
# on a stock this profile does not describe -- the cover leaf, the card -- there
# is almost none of it, and a p50 taken over a handful of light-ink pixels is
# not a paper white.  Below this fraction of the canvas the reference is taken
# from the FABRICATED MARGIN instead: it is filled with exactly W and graded
# through the same separation, so it is by construction "what paper white grades
# to" on this page.  Which one was used is printed, because the two are not the
# same measurement and a reader must not have to guess.
PAPER_PROBE_MIN_FRAC = 0.05

# --- there is no OCR contrast curve, and that is deliberate ---------------
# There was one here: `-level 30%,100%`, one issue-wide constant, applied to
# masters600 while a second uncurved render fed the figures.  It existed to fix
# grey type -- and grey type was a symptom of the separator's GCR, which left
# printed black as K ALONE (100% single K renders about 50 through SWOP, not 0).
# undo_gcr() fixes that at the source, so the curve has nothing left to do:
# MEASURED on p056, glyph p50 37 -> 20 and 0% -> 39.6% of glyph pixels solid
# black, which is where 8609's existing masters already sit (p010: 31, 42.1%).
#
# It also had to go for a second reason, which is the more important one: THERE
# IS ONLY ONE MASTER.  r145_extract_figures.py reads r010_ocr_blocks.SRC_DIR --
# the same directory r010 OCRs -- so a curve on the OCR master is a curve on
# every published figure, and a curve crushes photographs (MEASURED on p006:
# pure-black area of the cover photo 25% -> 42%).


# --- the debug overlay -----------------------------------------------------
# One per page, always: the four traced lines drawn in green on the LEVELLED,
# UNFILLED page.  This is the artefact the user reviews, so it shows the page as
# the tracer saw it -- bed, fringe and all -- with the decision drawn on top.
DEBUG_REDUCE = 5
DEBUG_COLOR = (0, 230, 0)
DEBUG_WIDTH = 5
DEBUG_STEP = 40             # px between polyline vertices

# ---------------------------------------------------------------------------
# The issue descriptor -- the one place any step learns WHERE an issue lives
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent                   # .../scan2ocr/rules
IMG_DIR = HERE.parents[1]                                # .../tools/img

ISS = r000_issue.load(ISSUE)
if ISS.binding != BINDING:
    raise SystemExit(
        f"r005_masters_sheet: {ISSUE} has binding={ISS.binding!r}, not "
        f"{BINDING!r}. This issue belongs to r005_masters_spread. Record this "
        f"variant in its LOG.md as not applicable rather than forcing it.")

SCAN_DIR = Path(ISS.scan_dir)
THUMB_DIR = Path(ISS.thumb_150)
# r000_issue derives <tmp>/masters600 because r010 and r145 read it and the
# contract belongs there.  The other three are this step's own workings -- the
# figure render, the archival separation, the overlay the user reviews -- so
# they are named here, beside it.
OUT_MASTER = Path(ISS.masters600)
# The deskewed, graded, UNCROPPED sheet at full resolution.  It is the thing
# every other artefact of this page is derived from, and it is kept: a figure
# that bleeds off the trimmed page still exists on the sheet.
OUT_SHEET = Path(ISS.tmp) / "masters2400"
OUT_CMYK = Path(ISS.tmp) / "cmyk2400"
OUT_DEBUG = Path(ISS.tmp) / "debug600"
OUT_DIRS = (OUT_MASTER, OUT_SHEET, OUT_CMYK, OUT_DEBUG)


# ---------------------------------------------------------------------------
# The ink profile
# ---------------------------------------------------------------------------

def read_profile(path):
    """(anchors, levels) from a cmyk_reconstruction colors.txt, or the built-ins.

    Same grammar the tool parses: `W 214 195 186` and `LK 90 95`, `#` comments.
    A missing file is not an error -- `colors` is optional in the descriptor.
    """
    anchors = dict(BUILTIN_ANCHORS)
    levels = dict(BUILTIN_LEVELS)
    if not path or not os.path.exists(path):
        return anchors, levels, False
    for line in open(path, encoding="utf-8"):
        parts = line.split("#", 1)[0].split()
        if len(parts) == 4 and parts[0] in anchors:
            anchors[parts[0]] = tuple(float(v) for v in parts[1:])
        elif len(parts) == 3 and parts[0] in levels:
            levels[parts[0]] = tuple(float(v) for v in parts[1:])
    return anchors, levels, True


ANCHOR_KEYS = ("W", "C", "M", "Y", "R", "G", "B", "K")
LEVEL_KEYS = ("LC", "LM", "LY", "LK")


def profile_text(anchors, levels):
    """The 8 anchors and 4 level lines, in cmyk_reconstruction's own grammar.

    ONE function produces this text and everything else quotes it: the file
    handed to the separator, the stamp written beside every master, and the
    digest the two are compared by.  Two spellings of the same profile would
    eventually disagree, and the disagreement would look like a stale master.
    """
    return "".join(
        ["%s %g %g %g\n" % ((k,) + tuple(anchors[k])) for k in ANCHOR_KEYS] +
        ["%s %g %g\n" % ((k,) + tuple(levels[k])) for k in LEVEL_KEYS])


def write_profile(anchors, levels, dest):
    """The profile cmyk_reconstruction will actually be run with, written out.

    It is written even when it came from a colors.txt, and it is KEPT beside the
    archived CMYK rather than thrown away with the scratch directory, so the
    archive and the render are traceable to the exact numbers used rather than
    to a file that may since have been re-measured.  This issue's colors.txt has
    been re-measured once already, and three of the four masters standing in the
    output directory afterwards were silently stale.
    """
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(f"# {ISSUE} -- profile as used by r005_masters_sheet\n")
        fh.write(f"# source: {ISS.colors or 'built-in anchors, identity levels'}\n")
        fh.write(profile_text(anchors, levels))


ANCHORS, LEVELS, HAVE_PROFILE = read_profile(ISS.colors)
PAPER_RGB = np.array(ANCHORS["W"], float)

# THE GRADE'S FINGERPRINT.  A finished master carries no record of which numbers
# produced it, and this issue proved what that costs: colors.txt was re-measured,
# three of the four masters beside it were now stale, and it took a human eye
# noticing yellow corners to find out.  Everything that can change a pixel goes
# in -- the 8 anchors, the 4 level lines, and the OCR level -- and the digest is
# written into every artefact this step produces.  Comparing a master with the
# current profile is then a string comparison, not a judgement about colour.
GRADE_TEXT = profile_text(ANCHORS, LEVELS)
GRADE_SHA = hashlib.sha1(GRADE_TEXT.encode("utf-8")).hexdigest()[:12]


def stamp_text(**fields):
    """The stamp that says which profile made this page.

    Written three ways, because each of them is the one that survives a
    different accident: as a PNG/TIFF text chunk INSIDE every render (survives
    the file being copied somewhere else), as NNN.stamp.txt beside the master
    (readable without opening a 110 megapixel PNG), and as the profile file
    handed to the separator, kept in cmyk2400/.
    """
    head = [f"r005_masters_sheet {ISSUE} -- the grade as used for this page",
            f"grade-sha    {GRADE_SHA}",
            f"profile      {ISS.colors or '(none -- built-in anchors)'}",
            f"render       ONE master, uncurved -- r010 OCRs it and r145 "
            f"cuts figures from it"]
    body = [f"{k:<12s} {v}" for k, v in fields.items()]
    return "\n".join(head + body + [""] + GRADE_TEXT.rstrip().split("\n")) + "\n"


class PageFailed(Exception):
    """One page did not pass one of this step's gates.

    Raised rather than exited, for one reason: a sweep over 152 pages at ~45 s a
    page is 2 hours, and losing it to page 002 would mean nobody ever sees what
    pages 003-152 do.  The failure is still loud and still blocking -- the page's
    outputs are DELETED so a stale master cannot pass a later "every page has a
    master" check, the page is named on stderr, and the process exits non-zero
    with the list.  What it is not is silent, and what it does not do is publish
    the page anyway.
    """


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def skew_score(ink, angle):
    """Variance of the row-sum profile after rotating the ink mask by `angle`.

    Level text puts every line's ink into few rows, which maximises the squared
    difference between neighbouring rows of the projection.  Scale-invariant,
    which is why it can be measured on the thumb and applied to the master.
    """
    profile = scipy_rotate(ink, angle, reshape=False, order=1,
                           mode="constant").sum(1)
    return float(((profile[1:] - profile[:-1]) ** 2).sum())


def measure_skew(gray, around=None):
    """Skew of the TYPE, in degrees, from a greyscale array.

    `around` skips the coarse sweep and refines about a known angle.  The coarse
    pass is what costs, so the two-stage arrangement is: sweep the whole range on
    the 150 dpi thumb, then REFINE ON THE 600 dpi PAGE.  The thumb is 1/16 scale
    and a fine step of a hundredth of a degree is beyond what it can resolve --
    on p116 (three filter-curve graphs, sparse text, the graph rules competing
    with the text baselines in the projection score) the thumb said -0.52 and the
    levelled page still read +0.22.  The angle is scale-invariant; the MEASUREMENT
    is not.
    """
    h, w = gray.shape
    t, b, l, r = SKEW_CROP
    crop = gray[int(h * t):int(h * b), int(w * l):int(w * r)]
    ink = (crop < crop.mean() - SKEW_INK_SIGMA * crop.std()).astype(np.float32)
    if around is not None:
        fine = np.arange(around - SKEW_FINE_SPAN,
                         around + SKEW_FINE_SPAN + SKEW_FINE_STEP / 2,
                         SKEW_FINE_STEP)
        return float(max(fine, key=lambda a: skew_score(ink, a)))
    lo, hi, step = SKEW_COARSE
    coarse = max(np.arange(lo, hi + step / 2, step),
                 key=lambda a: skew_score(ink, a))
    fine = np.arange(coarse - SKEW_FINE_SPAN,
                     coarse + SKEW_FINE_SPAN + SKEW_FINE_STEP / 2, SKEW_FINE_STEP)
    return float(max(fine, key=lambda a: skew_score(ink, a)))


def prop_mask(rgb):
    """True where the pixel is the saturated yellow prop under the sheet."""
    green_over_blue = rgb[:, :, 1].astype(int) - rgb[:, :, 2]
    return ((green_over_blue > PROP_YELLOW_MIN) &
            (rgb.mean(2, dtype=np.float32) > PROP_LUM_MIN))


def paper_mask(rgb):
    """True where the pixel is paper: near the paper white, and not the prop."""
    near = np.abs(rgb.astype(int) - PAPER_RGB).sum(2) < PAPER_DIST
    return near & ~prop_mask(rgb)


def _edges(mask, rows, cols):
    """First/last True per given row and column: the raw edge samples."""
    h, w = mask.shape
    starts = np.array([np.argmax(mask[y]) for y in rows], float)
    ends = np.array([w - 1 - np.argmax(mask[y][::-1]) for y in rows], float)
    tops = np.array([np.argmax(mask[:, x]) for x in cols], float)
    bots = np.array([h - 1 - np.argmax(mask[:, x][::-1]) for x in cols], float)
    return rows, starts, ends, cols, tops, bots


def boundaries(mask):
    """Per-row and per-column first/last paper pixel, over the page body only.

    Returns (body_rows, starts, ends, body_cols, tops, bots).  A row outside the
    body is mostly bed and carries no edge information.
    """
    return _edges(mask,
                  np.where(mask.mean(1) > BODY_PAPER_FRAC)[0],
                  np.where(mask.mean(0) > BODY_PAPER_FRAC)[0])


def box_open(mask, r_px):
    """Morphological opening with a square element, done with box means.

    ND.binary_opening with a 49 px element over a 37 megapixel master is minutes
    of work; a box mean is two separable passes and answers the question this
    step is actually asking -- "is there room for a square this size inside the
    region?".  The 0.999/0.001 thresholds rather than 1 and 0 are float32
    hygiene, and they buy one useful thing besides: a couple of stray pixels
    inside the element do not veto it.
    """
    k = 2 * int(round(r_px)) + 1
    eroded = ND.uniform_filter(mask.astype(np.float32), k) > 0.999
    return ND.uniform_filter(eroded.astype(np.float32), k) > 0.001


def find_sheet(rgb, mm_px):
    """The sheet as ONE connected region, found from INK vs BED, not from paper.

    For the eight pages whose stock the profile's W does not describe; see
    FULLBLEED_PAPER_FRAC.  The bed is near-black, uniform and connected to the
    frame; the sheet is whatever the frame-connected bed is not.  Holes are
    filled (a photograph's own blacks are not bed), the region is opened so a
    one-pixel bridge cannot annex the prop (p151), and the largest component is
    the sheet.
    """
    lum = rgb.mean(2, dtype=np.float32)
    bed = (lum < BED_LUM) | prop_mask(rgb)
    lab, _ = ND.label(bed)
    touching = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    touching.discard(0)
    if not touching:
        raise PageFailed("r005: ink-vs-bed found no bed at the frame at all -- "
                         "this is not a sheet on a bed")
    outer = np.isin(lab, sorted(touching))
    sheet = box_open(ND.binary_fill_holes(~outer), SHEET_OPEN_MM * mm_px)
    lab, n = ND.label(sheet)
    if n == 0:
        raise PageFailed("r005: ink-vs-bed found no sheet -- the frame is bed "
                         "from edge to edge")
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return ND.binary_fill_holes(lab == int(sizes.argmax()))


def sheet_boundaries(comp):
    """boundaries(), but scaled to the REGION rather than to the frame.

    BODY_PAPER_FRAC asks whether half the FRAME's width is paper, which is the
    right question for an A4 sheet filling an A4-ish frame and the wrong one for
    a 146 mm card lying in a 215 mm frame.  A row belongs to the body here if it
    carries at least half of what the region's median row carries.
    """
    rc, cc = comp.sum(1), comp.sum(0)
    if not rc.any():
        raise PageFailed("r005: ink-vs-bed found an empty sheet")
    return _edges(comp,
                  np.where(rc > 0.5 * np.median(rc[rc > 0]))[0],
                  np.where(cc > 0.5 * np.median(cc[cc > 0]))[0])


def page_class(w_mm, h_mm):
    """The name of the size class this traced page matches, or None.

    Nearest match when the windows overlap, so the answer does not depend on the
    order of the table.
    """
    hits = sorted((abs(w_mm - w) + abs(h_mm - h), name)
                  for name, w, h, tol in PAGE_CLASSES
                  if abs(w_mm - w) <= tol and abs(h_mm - h) <= tol)
    return hits[0][1] if hits else None


def trace(vals, idx, pct, mm_px):
    """A robust line through a per-row/column edge sample: bands, then a fit.

    `pct` picks the statistic per band -- CLEAN_PCT for a guillotined edge,
    FRINGE_PCT for a torn one.  Samples far off the median are dropped first:
    they are rows crossing full-bleed art, not edge samples at all.
    """
    keep = np.abs(vals - np.median(vals)) < TRACE_OUTLIER_MM * mm_px
    vals, idx = vals[keep], idx[keep]
    # np.array_split hands back EMPTY bands when there are fewer samples than
    # bands, np.percentile of an empty band is nan, and np.polyfit through nans
    # returns a line of nans that every later test then happily passes.
    if len(vals) < TRACE_BANDS:
        raise PageFailed(f"r005: only {len(vals)} usable edge samples for "
                         f"{TRACE_BANDS} bands -- there is no edge here to fit")
    bands = np.array_split(np.arange(len(vals)), TRACE_BANDS)
    xs = [idx[b].mean() for b in bands]
    ys = [np.percentile(vals[b], pct) for b in bands]
    return np.polyfit(xs, ys, 1)               # (slope, intercept)


def torn_side(mask, mm_px):
    """('left'|'right', confidence ratio) from the row-to-row edge jitter.

    A guillotined edge is straight to within a pixel row; a torn edge jitters.
    See TORN_CONFIDENT_RATIO for what was measured over all 152 thumbs.
    """
    rows, starts, ends, _, _, _ = boundaries(mask)

    def jitter(v):
        v = v[np.abs(v - np.median(v)) < TRACE_OUTLIER_MM * mm_px]
        return float(np.mean(np.abs(np.diff(v)))) if len(v) > 1 else 0.0

    jl, jr = jitter(starts), jitter(ends)
    ratio = max(jl, jr) / max(min(jl, jr), 1e-6)
    return ("right" if jr > jl else "left"), ratio


# ---------------------------------------------------------------------------
# The grade
# ---------------------------------------------------------------------------

def separate_and_render(src_png, cmyk_tiff, rgb_png, profile_txt, stamp):
    """RGB -> CMYK (the existing tool) -> RGB (the ICC pair).  One separation.

    The separation is the archival form and the source of BOTH renders; the tool
    is called, never reimplemented.  CMYK -> RGB goes through US Web Coated SWOP
    and then AdobeRGB1998, the profiles that live in tools/img/.  `-set comment`
    puts the stamp in the PNG's own tEXt chunk -- this render is the UNCURVED
    one, and the stamp says so.
    """
    tool = IMG_DIR / CMYK_TOOL
    if not tool.exists():
        raise SystemExit(f"r005: {tool} is not built -- "
                         f"cargo build --release in tools/img/cmyk_reconstruction")
    subprocess.run([str(tool), "--colors", str(profile_txt),
                    str(src_png), str(cmyk_tiff)], check=True)
    undo_gcr(cmyk_tiff)
    subprocess.run(["magick", str(cmyk_tiff),
                    "-profile", str(IMG_DIR / ICC_CMYK),
                    "-profile", str(IMG_DIR / ICC_RGB),
                    "-density", str(MASTER_DPI), "-set", "units", "PixelsPerInch",
                    "-set", "comment", stamp,
                    str(rgb_png)], check=True)


def undo_gcr(cmyk_tiff):
    """Put back what the separator's GCR took out.  THIS IS WHY TYPE IS BLACK.

    cmyk_reconstruction solves C, M, Y and then applies full GCR: K = min(C,M,Y),
    subtracted from each of the three.  That is the MRC renderer's reconstruction
    choice -- it makes CMY pure colour and K all neutral -- and it is wrong for a
    viewable master, because it leaves printed black type as K ALONE.  100% single
    K through SWOP renders about 50, not 0: grey type on white paper.

    MEASURED on p056: with the GCR left in, the glyph median is 37 and NOT ONE
    glyph pixel is solid black.  Undone, the median is 20 and 39.6% of glyph
    pixels are solid black -- which is where this project's existing masters sit
    (8609 p010: median 31, 42.1% solid).  The photo on p006 keeps its gradation
    either way (p25 0 / p50 62 / p75 124 / p95 220 against a published 8609
    figure's 8.7 / 71 / 151 / 191).

    The undo is exact, not an approximation: the tool wrote c_final = c - k, so
    c = c_final + k recovers the solved value.  Black type comes back as all four
    inks -- a rich black -- and renders where it belongs.
    """
    a = np.array(Image.open(cmyk_tiff)).astype(np.int16)
    k = a[:, :, 3]
    for i in range(3):
        a[:, :, i] = np.clip(a[:, :, i] + k, 0, 255)
    Image.fromarray(a.astype(np.uint8), mode="CMYK").save(cmyk_tiff)


def archive_cmyk(cmyk_tiff, dest, stamp):
    """The CMYK archival form, losslessly compressed, with the stamp in it.

    The tool writes an uncompressed CMYK TIFF -- 141 MB for one A4 page at 600
    dpi, 21 GB for the issue.  Deflate keeps the pixels and the CMYK colourspace
    and costs a fraction of that.  The stamp lands in TIFF ImageDescription.
    """
    subprocess.run(["magick", str(cmyk_tiff), "-compress", "zip",
                    "-density", str(MASTER_DPI), "-set", "units", "PixelsPerInch",
                    "-set", "comment", stamp,
                    str(dest)], check=True)


def save_master(arr, dest, stamp):
    """The OCR master, with the stamp as a PNG tEXt chunk.

    In the file, not only beside it: a master that has been copied out of
    masters600/ still says which profile and which curve made it.
    """
    meta = PngImagePlugin.PngInfo()
    meta.add_text("r005", stamp)
    Image.fromarray(arr).save(dest, pnginfo=meta)


# ---------------------------------------------------------------------------
# One page
# ---------------------------------------------------------------------------

def tilt(poly):
    return math.degrees(math.atan(poly[0]))


def process(page):
    # THIS STEP DOES NOT REFUSE A PAGE.  Everything that used to be a gate --
    # parity, skew residual, page class, canvas fit, the grade's ink numbers --
    # is measured, published, and NOTED here.  A note goes in the page's log
    # line and in its stamp, so a page that needs a human eye is findable with
    # grep instead of missing from the output.  The one thing that still stops
    # a page is a missing input file: there is nothing to publish.
    notes = []
    stem = f"{page:03d}"
    scan = SCAN_DIR / f"{stem}.png"
    thumb = THUMB_DIR / f"{stem}.png"
    for p in (scan, thumb):
        if not p.exists():
            raise PageFailed(f"r005 p{stem}: missing input {p}")

    # --- skew, measured on the thumb ---------------------------------------
    thumb_rgb = Image.open(thumb).convert("RGB")
    angle = measure_skew(np.array(thumb_rgb.convert("L"), float))

    # --- which edge finder? -------------------------------------------------
    # Asked on the thumb, before the 800 MB scan is opened, because it costs
    # 0.2 s there instead of 45.  See FULLBLEED_PAPER_FRAC: how much of this
    # frame the profile's paper white can see decides it, not the page number.
    thumb_mask = paper_mask(np.array(thumb_rgb))
    body_h = (thumb_mask.mean(1) > BODY_PAPER_FRAC).mean()
    body_w = (thumb_mask.mean(0) > BODY_PAPER_FRAC).mean()
    from_ink = min(body_h, body_w) < FULLBLEED_PAPER_FRAC
    finder = "ink/bed" if from_ink else "paper/bed"

    # --- the parity gate, off the same thumb -------------------------------
    # It reads the jitter of the PAPER boundary, so it can only be asked where
    # there is a paper boundary.  On the ink/bed pages there is none to read --
    # and nothing to read it from either: the cover leaf's inner edge is a FOLD,
    # not a tear, and the card was cut on all four sides.  Skipped, and said.
    expected = "right" if page % 2 == 0 else "left"
    side, ratio = ("not measurable", 0.0)
    if not from_ink:
        side, ratio = torn_side(thumb_mask, THUMB_MM)
        if side != expected and ratio >= TORN_CONFIDENT_RATIO:
            notes.append(f"TORN SIDE reads {side} (ratio {ratio:.2f}) but "
                         f"parity says {expected} -- misfiled or mis-rotated?")

    # --- level, then RE-MEASURE the residual --------------------------------
    # LEVEL AT 2400, REDUCE AFTERWARDS.  The scan is rotated at full resolution
    # and everything downstream is derived from that -- the grade included.  The
    # other order (reduce, then rotate, then grade at 600) averages the ink away
    # before the grade can see whether it was on the paper, and thin black type
    # is exactly what that loses.
    full = Image.open(scan).convert("RGB")
    full = full.rotate(angle, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
    img = full.reduce(SCAN_REDUCE)
    def residual_of(im):
        return measure_skew(np.array(im.reduce(MASTER_DPI // THUMB_DPI)
                                     .convert("L"), float))

    residual = residual_of(img)
    # ITERATE ONCE rather than refuse.  The thumb and the levelled page can
    # disagree -- p116 is three filter-curve graphs with sparse text, where the
    # graph rules compete with the text baselines in the projection score --
    # and applying the residual is self-correcting whatever the cause.
    if abs(residual) > SKEW_RESIDUAL_MAX:
        first, angle = residual, angle + residual
        full = Image.open(scan).convert("RGB")
        full = full.rotate(angle, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
        img = full.reduce(SCAN_REDUCE)
        residual = residual_of(img)
        notes.append(f"SKEW re-levelled: residual was {first:+.2f}, "
                     f"corrected to {angle:+.2f} deg, now {residual:+.2f}")
    if abs(residual) > SKEW_RESIDUAL_MAX:
        notes.append(f"SKEW still {residual:+.2f} deg after a second pass "
                     f"(allowed {SKEW_RESIDUAL_MAX}) -- published anyway")

    arr = np.array(img)
    h, w = arr.shape[:2]
    mask = paper_mask(arr)

    # --- trace the four edges ----------------------------------------------
    if from_ink:
        # No paper to trace from, so the edge is the sheet's own boundary
        # against the bed.  All four are traced the same way: there is no torn
        # fringe on these pages to model -- the cover leaf's inner edge is a
        # fold and the card is cut -- and the band MEDIAN is what a cut or
        # folded edge wants.  Where the sheet runs off the frame the samples are
        # a constant 0 (or w-1) and the fitted line is that frame edge, which is
        # the honest answer: the scan does not contain the trim.
        sheet = find_sheet(arr, MM)
        rows, starts, ends, cols, tops, bots = sheet_boundaries(sheet)
        left = trace(starts, rows, CLEAN_PCT, MM)
        right = trace(ends, rows, CLEAN_PCT, MM)
        in_l = in_r = CLEAN_INSET_MM * MM
    else:
        rows, starts, ends, cols, tops, bots = boundaries(mask)
        # The two torn sides are NOT the same problem; see RECTO_FLUSH_MM.
        if expected == "right":                               # verso
            left = trace(starts, rows, CLEAN_PCT, MM)         # clean, traced
            right = trace(ends, rows, FRINGE_PCT, MM)         # fringe, traced
            in_l, in_r = CLEAN_INSET_MM * MM, FRINGE_INSET_MM * MM
        else:                                                 # recto
            left = np.array([0.0, np.percentile(starts, RECTO_FLUSH_PCT)
                             + RECTO_FLUSH_MM * MM])          # flush, VERTICAL
            right = trace(ends, rows, CLEAN_PCT, MM)          # clean, traced
            in_l, in_r = 0.0, CLEAN_INSET_MM * MM
    top = trace(tops, cols, CLEAN_PCT, MM)
    bot = trace(bots, cols, CLEAN_PCT, MM)

    ys, xs = np.arange(h), np.arange(w)
    xl = np.polyval(left, ys) + in_l
    xr = np.polyval(right, ys) - in_r
    yt = np.polyval(top, xs) + CLEAN_INSET_MM * MM
    yb = np.polyval(bot, xs) - CLEAN_INSET_MM * MM
    keep = ((xs[None, :] >= xl[:, None]) & (xs[None, :] <= xr[:, None]) &
            (ys[:, None] >= yt[None, :]) & (ys[:, None] <= yb[None, :]))

    # --- drop the bed that a line fit cannot clear --------------------------
    lum = arr.mean(2, dtype=np.float32)
    bedlike = (lum < BED_LUM) | prop_mask(arr)
    lab, _ = ND.label(bedlike)
    touching = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    touching.discard(0)
    dropped = 0
    if touching:
        labels = np.array(sorted(touching))
        total = ND.sum(np.ones_like(lab, bool), lab, labels)
        outside = ND.sum(~keep, lab, labels)
        doomed = labels[(outside / np.maximum(total, 1)) > BED_OUTSIDE_FRAC]
        if len(doomed):
            keep &= ~np.isin(lab, doomed)
            dropped = len(doomed)

    # --- the debug overlay: the traced lines on the LEVELLED, UNFILLED page --
    # Written HERE, before the size gate, and not at the end: it is the artefact
    # that explains a FAILED page, and a failed page never reaches the end.  The
    # size gate's own message says "look at debug600/NNN.png", which was a lie
    # while this sat below the raise.
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    for i in range(0, h - DEBUG_STEP, DEBUG_STEP):
        for poly in (left, right):
            draw.line((np.polyval(poly, i), i,
                       np.polyval(poly, i + DEBUG_STEP), i + DEBUG_STEP),
                      fill=DEBUG_COLOR, width=DEBUG_WIDTH)
    for i in range(0, w - DEBUG_STEP, DEBUG_STEP):
        for poly in (top, bot):
            draw.line((i, np.polyval(poly, i),
                       i + DEBUG_STEP, np.polyval(poly, i + DEBUG_STEP)),
                      fill=DEBUG_COLOR, width=DEBUG_WIDTH)
    overlay.resize((w // DEBUG_REDUCE, h // DEBUG_REDUCE),
                   Image.LANCZOS).save(OUT_DEBUG / f"{stem}.png")

    # --- the traced page, and the fixed canvas it is placed on --------------
    x0 = int(math.floor(min(xl.min(), xr.min())))
    x1 = int(math.ceil(max(xl.max(), xr.max())))
    y0 = int(math.floor(min(yt.min(), yb.min())))
    y1 = int(math.ceil(max(yt.max(), yb.max())))
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, w - 1), min(y1, h - 1)
    page_w_mm, page_h_mm = (x1 - x0) / MM, (y1 - y0) / MM
    klass = page_class(page_w_mm, page_h_mm)
    if klass is None:
        # IF WE CANNOT CROP, DO NOT CROP.  A trace that lands outside every page
        # class has found something that is not the sheet -- p117's tracer locked
        # onto the cream panel inside a dark-ground ad -- and a wrong crop throws
        # print away silently.  The whole levelled sheet is published instead,
        # with the note saying why, and the page is still there to be looked at
        # and re-cut.
        notes.append(f"NOT CROPPED: the trace gave {page_w_mm:.1f} x "
                     f"{page_h_mm:.1f} mm, which matches no page class "
                     f"({finder}); publishing the whole levelled sheet instead. "
                     f"See debug600/{stem}.png")
        x0, y0, x1, y1 = 0, 0, w - 1, h - 1
        keep = np.ones_like(keep)
        page_w_mm, page_h_mm = (x1 - x0) / MM, (y1 - y0) / MM
        klass = "uncropped sheet"

    cw, ch = int(round(MASTER_W_MM * MM)), int(round(MASTER_H_MM * MM))

    if y1 - y0 > ch or x1 - x0 > cw:
        # Never truncate: grow the canvas for this page and say so.  A page
        # bigger than the canvas is a geometry problem to look at, not a reason
        # to withhold the pixels.
        notes.append(f"CANVAS grown to {max(cw, x1 - x0)}x{max(ch, y1 - y0)} px "
                     f"for a {x1 - x0}x{y1 - y0} page -- the uniform "
                     f"{cw}x{ch} canvas did not fit it")
        cw, ch = max(cw, x1 - x0), max(ch, y1 - y0)

    def place(src, fill):
        """Crop to the traced page and anchor it at the canvas's top-left."""
        cut = src[y0:y1, x0:x1]
        out = np.full((ch, cw) + src.shape[2:], fill, dtype=src.dtype)
        out[:cut.shape[0], :cut.shape[1]] = cut
        return out

    # Outside the traced page is the measured PAPER WHITE, so the density-domain
    # solver sees exactly zero density there rather than a near-white it has to
    # resolve into some faint ink.
    filled = arr.copy()
    filled[~keep] = PAPER_RGB.astype(np.uint8)
    canvas = place(filled, 0)
    canvas_paper = place(mask & keep, False)
    # See STOCK_PCT: what counts as ink is a distance from the paper THIS SHEET
    # is printed on, which is only the profile's W where the profile describes
    # the sheet.  Sampled 1 pixel in 16 -- a percentile of 2 million pixels and
    # of 30 million is the same percentile, and one of them costs nothing.
    stock_rgb = PAPER_RGB
    if from_ink:
        small = arr[::4, ::4][keep[::4, ::4]]
        if len(small):
            stock_rgb = np.percentile(small, STOCK_PCT, axis=0)
    canvas_ink = place((np.abs(arr.astype(int) - stock_rgb).sum(2) > RAW_INK_DIST)
                       & keep, False)
    # the canvas margin is fabricated paper, not scan -- it is neither
    canvas_page = place(np.ones((h, w), bool), False)
    canvas[~canvas_page] = PAPER_RGB.astype(np.uint8)

    # The stamp every artefact of this page carries.  Built BEFORE the render,
    # because it describes what the render is about to be done with.
    stamp = stamp_text(**{
        "page": f"{stem} of {ISSUE}",
        "page-class": klass,
        "page-size": f"{page_w_mm:.1f} x {page_h_mm:.1f} mm",
        # The traced page in canvas pixels, anchored at 0,0.  Written down
        # rather than left to be re-derived: every check that wants to look at
        # the page and not at the fabricated margin needs this box, and
        # recovering it from the pixels means guessing which white is which.
        "page-px": f"{x1 - x0} {y1 - y0}",
        "canvas-px": f"{cw} {ch}",
        "notes": "; ".join(notes) if notes else "(none)",
        "edge-finder": finder,
        "skew": f"{angle:+.2f} -> {residual:+.2f} deg",
    })

    with tempfile.TemporaryDirectory(prefix=f"r005_{ISSUE}_{stem}_") as work:
        work = Path(work)
        # KEPT, not thrown away with `work`: this is the profile the separator
        # was actually run with, sitting beside the archive it produced.
        profile_txt = OUT_CMYK / f"{stem}.colors.txt"
        write_profile(ANCHORS, LEVELS, profile_txt)
        src_png, cmyk_tiff = work / "in.png", work / "sep.tiff"
        full.save(src_png)
        separate_and_render(src_png, cmyk_tiff,
                            OUT_SHEET / f"{stem}.png", profile_txt, stamp)
        archive_cmyk(cmyk_tiff, OUT_CMYK / f"{stem}.tif", stamp)
    (OUT_MASTER / f"{stem}.stamp.txt").write_text(stamp, encoding="utf-8")

    # The 600 dpi master comes OFF the graded 2400 sheet -- one grade, one
    # reduce, in that order -- and only then is it cut to the traced page.
    sheet600 = np.array(Image.open(OUT_SHEET / f"{stem}.png")
                        .convert("RGB").reduce(SCAN_REDUCE))
    sheet600 = sheet600[:h, :w]
    graded = np.full_like(sheet600, 255)
    graded[keep] = sheet600[keep]
    graded = place(graded, 255)
    glum = graded.mean(2, dtype=np.float32)

    # --- prove the grade before publishing it -------------------------------
    # See PAPER_PROBE_MIN_FRAC for the second reference and when it is used.
    # An ink/bed page is by definition one whose stock the paper mask cannot
    # see, so what that mask does select on it is a biased scrap -- the yellowest
    # corner of a coated white -- and its p50 is not a paper white.  The margin
    # is the reference there, always, not only when the scrap is small.
    probe, probe_name = canvas_paper, "own paper"
    if from_ink or canvas_paper.mean() < PAPER_PROBE_MIN_FRAC:
        probe, probe_name = ~canvas_page, "fabricated margin"
    paper_white = float(np.percentile(glum[probe], 50)) if probe.any() else 255.0
    inked = (glum < paper_white - INK_CONTRAST) & canvas_page
    raw_ink_frac = float(canvas_ink.mean())
    ink_frac = float(inked.mean())
    # `<=`, not `<`: p006's photo puts well over INK_DARK_PCT of the page
    # on the exact clipped minimum, and a strict test then selects NOTHING
    # and reports the page as having no ink at all.
    dark = glum[glum <= np.percentile(glum, INK_DARK_PCT)]
    ink_p50 = float(np.median(dark))

    # BOTH CHECKS ARE STATEMENTS ABOUT THE LEVEL LINES, AND THE LEVEL LINES WERE
    # MEASURED ON THIS ISSUE'S PAPER.  On an ink/bed page they are not: the raw
    # side is measured against the SHEET'S OWN white (STOCK_PCT) and the graded
    # side against what the profile's W grades to, which are two different
    # papers, so the ratio between them is not the quantity the gate was built
    # to read.  MEASURED on p149: the card's pale cyan field sits 52 city-block
    # from its own stock -- ink by the raw test -- and grades to 254, because
    # relative to a W that is yellower and darker than this card it has almost
    # no density.  The ratio reads 0.31 and the master is, by eye, excellent:
    # crisp blue type, the pale field gone to paper.  Failing it there would be
    # a false diagnosis pointing at LC/LM/LY/LK, which are not the problem.
    #
    # So on those eight pages the two checks REPORT instead of refusing, and one
    # weaker gate stays hard: the page must not have come out blank.  If the
    # pale tint on the coated stock has to survive, the fix is a second measured
    # profile for that stock -- a decision, not a looser constant here.
    # THE GRADE IS NOT GATED.  It measures and REPORTS, and that is all.
    #
    # There was a gate here -- ink kept must be >= 0.70 of the scan's -- and on
    # a full 152-page sweep it failed 10 pages: 005 010 028 047 049 063 086 115
    # 124 138.  Every one was looked at, and every one was CORRECT: crisp black
    # type, clean tint, paper white.  p063 is the clearest case at 0.51.
    #
    # The metric was wrong, not the pages.  It counts INKED PIXELS, and all ten
    # are pages carrying a large SCREENED TINT: on the paper that tint is a
    # field of halftone dots with white between them, so it counts as heavily
    # inked; rendered correctly it becomes a smooth flat fill, which is the same
    # ink over a fraction of the pixels.  A dot field demodulating into a fill
    # is the pipeline WORKING, and the check read it as ink loss.  It selected
    # precisely the ten most tint-heavy pages in the issue.
    #
    # A coverage-based metric (the integral of ink, which demodulation conserves)
    # would not have that fault -- but the check has now cost more than it has
    # ever caught, and the failure it was built for is loud, not subtle: the old
    # LK 90 95 turned black type into blank paper, which is visible in a
    # thumbnail.  So the numbers go in the log for a human to notice, and the
    # step publishes the page.
    unproven = [f"ink kept {ink_frac / raw_ink_frac:.2f}"] if raw_ink_frac > 0 else []
    unproven.append(f"dark contrast {paper_white - ink_p50:.0f}")

    # --- the OCR master: the SAME curve on every page ------------------------
    # ONE master, UNCURVED.  r010 OCRs this file and r145 cuts the article
    # figures out of the same file (r145_extract_figures.py reads
    # r010_ocr_blocks.SRC_DIR), so a contrast curve here would be a curve on
    # every published figure.  Type is black because the separation's GCR is
    # undone -- see undo_gcr() -- not because of a curve.
    save_master(graded, OUT_MASTER / f"{stem}.png", stamp)

    print(f"p{stem}: skew {angle:+.2f} -> {residual:+.2f} deg | "
          f"edges L {tilt(left):+.2f} R {tilt(right):+.2f} "
          f"T {tilt(top):+.2f} B {tilt(bot):+.2f} deg | "
          f"{finder} | page {page_w_mm:.1f}x{page_h_mm:.1f} mm [{klass}] | "
          f"filled {(~keep[y0:y1, x0:x1]).mean() * 100:.2f}% | "
          f"bed comps {dropped} | torn {side} ({ratio:.2f}) | "
          f"paper {paper_white:.0f} ({probe_name}) ink {ink_p50:.0f} "
          f"({ink_frac:.1%} of {raw_ink_frac:.1%}) | "
          f"grade {GRADE_SHA}"
          + (" | grade: " + "; ".join(unproven) if unproven else "")
          + ("".join(f"\n      NOTE p{stem}: {n}" for n in notes)), flush=True)


if __name__ == "__main__":
    if not HAVE_PROFILE:
        print(f"r005: {ISSUE} has no colors profile -- grading with the built-in "
              f"anchor set and identity levels", flush=True)
    # The grade, in full, once per run and before any page is written: the eight
    # anchors, the four level lines and the OCR level are what decide every pixel
    # published below, and a run whose log does not name them cannot be audited
    # afterwards.  The same text goes into every artefact; see stamp_text.
    print(stamp_text(**{"run": f"{len(sys.argv[1:]) or ISS.pages} page(s)"}),
          flush=True)
    pages = [int(a) for a in sys.argv[1:]] or list(ISS.page_range)
    failed = []
    for page in pages:
        try:
            process(page)
        except PageFailed as exc:
            # A page that failed a gate must leave NO PUBLISHABLE ARTEFACT
            # behind: one from an earlier run would otherwise still be sitting
            # there, and every check downstream of here counts files.
            #
            # The DEBUG OVERLAY is the exception and is deliberately kept.  It
            # is not published, nothing counts it, and it is the one artefact
            # that says WHY the page failed -- the size gate's own message ends
            # "look at debug600/NNN.png", and deleting it made that a lie.
            for d, ext in ((OUT_MASTER, "png"), (OUT_MASTER, "stamp.txt"),
                           (OUT_SHEET, "png"), (OUT_CMYK, "tif"),
                           (OUT_CMYK, "colors.txt")):
                stale = d / f"{page:03d}.{ext}"
                if stale.exists():
                    stale.unlink()
            print(f"p{page:03d} FAILED -- {exc}", file=sys.stderr, flush=True)
            failed.append(page)
    if failed:
        raise SystemExit(f"r005: {len(failed)} of {len(pages)} pages FAILED a "
                         f"gate: {', '.join('%03d' % p for p in failed)}. "
                         f"Nothing was published for them.")
