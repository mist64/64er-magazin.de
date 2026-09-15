"""
Step 005, the library both variants share.

Step 005 exists in two mutually exclusive variants, r005_masters_sheet and
r005_masters_spread, selected by the descriptor's `binding`.  Everything
between the scanner and the page GEOMETRY is the same job in both -- the skew
measurement, the paper and prop masks, the robust edge trace, the separation
and its GCR undo, the stamp -- and lived once in the sheet variant.  It lives
here now, with the same names and the same comments, so that a change to the
grade is one change.  The variants keep what differs: which edges exist, how
the inner boundary is found, and what the canvas is.

This module has NO binding check.  It loads the descriptor because the grade
and the paths depend on it; which variant is allowed to run is the variant's
own first line.  Not a step: nothing runs when it is executed.
"""

import hashlib
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin
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
# ROWS THAT CROSS FULL-BLEED ART ARE NOT EDGE SAMPLES.  Their "last paper pixel"
# collapses hundreds of px inward, and unfiltered they tilted p056's traced
# fringe by +2.56 deg.  Drop any sample further than this from the median before
# the bands are formed.
TRACE_OUTLIER_MM = 12.0

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


def write_profile(anchors, levels, dest, variant):
    """The profile cmyk_reconstruction will actually be run with, written out.

    It is written even when it came from a colors.txt, and it is KEPT beside the
    archived CMYK rather than thrown away with the scratch directory, so the
    archive and the render are traceable to the exact numbers used rather than
    to a file that may since have been re-measured.  This issue's colors.txt has
    been re-measured once already, and three of the four masters standing in the
    output directory afterwards were silently stale.
    """
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(f"# {ISSUE} -- profile as used by {variant}\n")
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


def stamp_text(variant, **fields):
    """The stamp that says which profile made this page.

    Written three ways, because each of them is the one that survives a
    different accident: as a PNG/TIFF text chunk INSIDE every render (survives
    the file being copied somewhere else), as NNN.stamp.txt beside the master
    (readable without opening a 110 megapixel PNG), and as the profile file
    handed to the separator, kept in cmyk2400/.
    """
    head = [f"{variant} {ISSUE} -- the grade as used for this page",
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
    # ...and a pHYs chunk, so the file states its own resolution.  Without it a
    # 600 dpi master reads as "72, undefined" to everything downstream, and a
    # page whose scale is a guess is a page that gets placed at the wrong size.
    Image.fromarray(arr).save(dest, pnginfo=meta,
                              dpi=(MASTER_DPI, MASTER_DPI))


def tilt(poly):
    return math.degrees(math.atan(poly[0]))
