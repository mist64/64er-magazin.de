"""Cut the figures out of a page, from the rects tesseract already gave us.

A figure is a VERTICAL GAP in a column that still contains ink.  Everything
else here is about telling a picture from the three things that look like one:

  body text tesseract failed to block   -> it has LINE STRUCTURE, a picture does not
  a picture split by text printed IN it -> merge across a thin text strip
  an advertisement                      -> step 020 already labelled it

Nothing in this file judges what the picture IS.  That is step 020's job: it
sees the page and the captions.  This only measures rectangles.
"""
import json
import os
import sys

import re

import numpy as np
from PIL import Image, ImageDraw

import r010_ocr_blocks as OB

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

MASTER_DPI = 600
SCALE = MASTER_DPI / OB.OCR_DPI

COL_OVERLAP = 0.5       # blocks sharing this much x-extent are one column
MIN_GAP_PX = 260        # a gap thinner than this is leading, not a figure
INK_LEVEL = 200         # grey below this counts as ink
MIN_INK = 0.02          # the gap must actually contain ink
MIN_RUN_PX = 24         # an inked run thinner than this is a rule, not picture
PAD = 8

# The printed rule around a picture, and one pixel past it -- the scan blurs the
# rule's inner edge, and a pixel of picture is cheaper than a pixel of border.
BORDER_DARK = 90
BORDER_FRAC = 0.90
BORDER_MAX_PX = 40
BORDER_RULE_MAX_PX = 30   # thicker than this is content, not a printed rule
BORDER_INSIDE_PX = 24     # look this far inside the band for the frame's margin
BORDER_INSIDE_FRAC = 0.35 # ...darker than this inside means content, not a rule
BORDER_OVERCUT = 1

# Body text tesseract failed to block looks exactly like a figure to a gap
# test.  It is told apart by LINE STRUCTURE: text is many short inked runs
# separated by white, a picture is one long one.
TEXT_MIN_RUNS = 3
TEXT_MAX_LONGEST = 0.40     # longest run below this fraction of the height
TEXT_LINE_FRAC = 0.35       # a row below this share of the mean is between lines
STROKE_CONTRAST = 55        # a pixel this much darker than its row's background
EMPTY_FRAC = 0.004          # a row/column with less mark than this is blank paper

# A picture can have text printed inside it ('Länge: 18' on p10), which splits
# the gap in two.  Two regions in one column separated by less than this, with
# overlapping x, are one picture.
MERGE_GAP_PX = 400

# A figure is kept only on POSITIVE evidence: the text above or below it is the
# magazine's own.  Testing for the absence of an ad instead let 68 figures
# through on 32 advertising pages, because a gap between an ad and a page
# FOOTER has no ad on both sides.
ARTICLE_NEIGHBOURS = {"body", "heading", "caption", "listing-inline"}
SKIP_PAGE_KINDS = {"ad", "toc"}

MIN_W_PX = 240
MIN_H_PX = 240
# MEASURED over the issue, sampling every twelfth page: the blank margin around
# the printed area is 0 to 73 px -- median 18 left, 48 right -- and the minimum
# is ZERO on all four sides, because this magazine prints full-bleed opener
# photographs that run to the trimmed edge.  Stage 03's A4 crop has already
# removed the scanner bed and the sheet-edge shadow, so there is nothing here to
# guard against, and 260 px was excluding real content from every figure that
# reaches the outer margin.  The fifteenth census found the fingerprint: 13 of
# 76 boxes ended at exactly x=4700, which is W - 260, shearing the right frame
# rule off each one.
MARGIN_PX = 12          # only enough to discount a one-pixel scan edge
# A box's own rule is one long thin region -- p8's editorial border came out
# 564x5724.  No printed picture in this magazine is anywhere near that thin.
MAX_CAPTIONS_INSIDE = 1   # more than this inside one box means it is two
DUPLICATE_FRAC = 0.80     # this much of the smaller box shared -> same artwork
FIT_PAD_PX = 40           # one x-height, for the hairlines outside the heavy ink
# THE SNAP, AND WHY IT IS THE CLOSED-RECTANGLE FORM.  Measured three ways:
#
#            colour   bw
#   none      79.5    33
#   per-side  64.3    32
#   closed    66.7    50
#
# Per-side snapping took whatever long dark run each edge met and made 13 crops
# over-large.  Requiring a CLOSED rectangle killed that outright -- the review
# that had found those 13 went looking again and reported "foreign-rule snaps:
# none found", checking two suspects by hand and confirming both were the
# figures' own rules.  It is what took the line-art bucket from 32% to 50%.
#
# I removed it once on the colour numbers alone and had to put it back: colour's
# regression is its own merges (the calendar, p28's cards), which arrived in the
# same build from the tint bridge, not from this.  Judging a shared change by
# one bucket is how that mistake happens.
FRAME_SNAP_PX = 220       # how far out to look for the enclosing rule
FRAME_RUN_FRAC = 0.80     # dark share of the box's width/height that IS a rule
FRAME_RULE_SEP_PX = 6     # runs closer than this are the same printed rule
FRAME_MAX_CANDIDATES = 4  # rules to consider per side, nearest first
MAX_ASPECT = 6.0
SCRAP_JOIN_PX = 260     # OCR scraps this close belong to one picture
# Conversion type, measured over the INK rather than the paper.  Paper is most
# of a framed figure and paper is neutral, so averaging the whole rectangle
# drags every reading toward grey.
PAPER_LEVEL = 215       # above this luminance is paper, not print
# A strip of bare paper this wide, running the full height of a box, is the
# boundary BETWEEN two printed objects -- nothing printed has one inside it.
GUTTER_MIN_PX = 90      # ~3.8 mm at 600 dpi; narrower than any column gutter
# A STRIP SOMETHING CROSSES IS NOT A SEPARATOR, so this is a COUNT of marks and
# not a share of them.  As a share it scaled with the box: the rows that severed
# p32's flowchart carried 6 or 7 marked pixels -- the connector arrow running
# between two decision boxes -- which across a 1904 px row is 0.32%, inside a
# 0.5% tolerance.  The census found the two halves emitted as 30-2 and 30-2b,
# overlapping by 3 px, "four files, zero usable figures".  A printed stroke at
# 600 dpi is at least four pixels, so anything above three is a crossing.
BARE_MAX_PX = 3         # marked pixels a truly separating strip may carry
# The vertical separation between two stacked figures is a DIFFERENT quantity
# from a column gutter and needs its own measurement: the magazine sets figures
# closer together down a column than the columns are apart.  MEASURED on p27,
# whose two greeting cards are separated by bare runs of 75 and 48 rows -- both
# below the 90 px gutter minimum, which is why they stayed merged.
BAND_MIN_PX = 64        # bare rows that separate two stacked figures
# A tint panel IS the figure; its edge is where the tint stops.
# MEASURED on p143's panel: a tinted row reads 0.60-0.82 marked, never 0.90 --
# the black boxes and white fields printed ON it are part of the figure and are
# not tint.  A row of body text on bare paper reads 0.1-0.3, so 0.55 separates
# them with room on both sides.
PANEL_TINT_FRAC = 0.55  # share of a row that must be marked to still be panel
PANEL_STEP_PX = 4       # rows per step while following it
PANEL_GAP_PX = 120      # unmarked run crossed if the tint resumes beyond it
PANEL_BARE_FRAC = 0.20  # ...but never across a row this bare: that is the edge
CAP_BESIDE_PX = 200     # panel this wide beside a caption means it is set INTO it
TINT_SAT = 22           # RGB max-min above this is ink/tint, not scanned paper
# Text printed ON a figure -- pin labels, a menu, a printout's edge digits --
# is figure matter, not a boundary.  Body text sits on bare paper.
BLOCK_TINT_FRAC = 0.55  # marked share above this means the block sits on ink
TINT_BLOCK_MAX_WORDS = 12   # ...and only a SHORT block; paragraphs are text
INK_MIN_PX = 400        # too little ink to measure: fall back to a loose mask
# MEASURED over all 158 crops of this issue: mean ink chroma is bimodal, but
# not around 18.  A genuinely coloured figure reads 120-171 with 73-89% of its
# ink strongly saturated; a neutral one reads 1.5-3.3 with 0.0%.  Between them
# sits a band of 46 crops at 18-45 with a saturated fraction of 0.000-0.012 --
# grey artwork carrying the scanner's colour cast, which a threshold of 18 put
# in the colour bucket.  That is why the dots bucket emptied when the bucket
# stopped being taken from the model: every screened chip diagram measured 20-22
# and was called colour before the screen test could run.
SAT_COLOUR = 50         # mean chroma of the INK above this -> colour
SAT_STRONG = 60         # a pixel this chromatic is unambiguously coloured
# MEASURED over every crop: the share of ink that is strongly chromatic is
# bimodal -- neutral crops run 0.000-0.035, genuinely coloured ones 0.288-0.89.
# At 0.06 the grey screened tint boxes of p55 landed in colour on 0.074, which
# is scanner cast on a black-on-grey panel, not colour ink.  0.15 sits in the
# empty middle of the measured gap.
SAT_STRONG_FRAC = 0.15  # ...and this share of the ink being so makes it colour
# The press screen of this issue, measured: 133 lpi at 45 degrees.  A crop is
# screened when its strongest periodicity sits at that ruling AND that angle;
# unscreened crops peak at 0 degrees, on the printer's or the scanner's own grid.
FFT_WIN = 256           # window the periodicity is measured in
SCREEN_PERIOD_LO = 3.2  # 190 lpi at 600 dpi
SCREEN_PERIOD_HI = 7.0  # 85 lpi
SCREEN_ANGLE = 45.0     # the screen angle itself
SCREEN_ANGLE_TOL = 6.0  # measured spread was 44.3-48.5 degrees
SCREEN_PEAK_MIN = 40.0  # peak over local median; true 54-411, false 9-66 at 0 deg
GRAY_LO, GRAY_HI = 90, 190   # the band a continuous tone actually lives in
GRAY_MIDTONE_FRAC = 0.20     # ...over this share of the area -> greyscale

# Screened-and-uniform is a tint, screened-and-varying is a picture.
TONE_CELLS = 12         # coarse grid the halftone is averaged away over
TONE_MIN_STD = 11.0     # coarse tone flatter than this is a flat fill
ENCLOSED_MIN_WORDS = 12 # a text block this big inside a region makes it text
ENCLOSED_COVER = 0.60   # ...when this much of that block falls inside
GROW_PX = 24            # step by which a scrap hull grows toward the text
SETTLE_ROUNDS = 3         # alternations of find-top / grow-wide; converges by 3
GROW_STEPS = 60
JOIN_PX = 90            # two regions this close, with nothing between, are one
OVERLAP_SAME = 0.55     # this much of the smaller region inside the larger = one figure
# 0.25 was too eager: two distinct figures that merely clip each other were
# merged, and the judge's "I can see this but it has no box" count rose 28 -> 39.
FRAME_SEARCH_PX = 90    # how far outside a candidate to look for its printed rule
FRAME_SPAN = 0.92       # a row/column this dark across the CANDIDATE is a rule
CAPTION_GAP_PX = 10     # keep this clear of a caption's first row
CAPTION_OPEN = re.compile(r"^(Bild|Tabelle|Abb\.?)\s*(\d+)")
CAPTION_MEASURE_MATCH = 0.25  # a block sharing this much width is above the figure
MAX_FIGURE_FRAC = 0.62        # no figure is taller than this share of the page
PANEL_MAX_FRAC = 0.92         # ...unless measured tint says so (see grow_to_panel)
STRUCTURAL_LABELS = ("caption", "header", "footer")  # always bound a figure
TOP_STOP_MIN_WORDS = 4        # fewer words than this may be lettering inside the figure
CLAIM_GAP_PX = 120        # a caption's own figure reaches this far past a piece
# THE MEASUREMENT THAT SAYS NO GAP THRESHOLD CAN WORK, recorded before the next
# agent spends another round tuning one.  MEASURED across this issue:
#
#   white band INSIDE one figure   p79 hardcopy 324 px, p60 hardcopy ~430 px
#   gap BETWEEN distinct figures   p52 boxes ~160 px, p74's three boxes ~110 px
#
# The intra-figure bands are LARGER than the inter-figure gaps, so the two
# populations overlap and no single value separates them.  Changing this
# constant from 300 to 120 demonstrated it precisely: p79 stayed split (324 >
# 120), p172 was newly split, and p74's three boxes still did not separate.
#
# The structure that does separate them is the printed rule rectangle, which
# exists on essentially every one of these figures.  framed_rects() below was
# written for exactly that and is currently UNCALLED.  It is not ready: tested
# over the issue it returns 0 rectangles on p74, whose three boxes are plainly
# framed, and 212 nested duplicates on p172.  Recall and dedup have to be fixed
# before it can carry the segmentation -- and it should carry it, because the
# alternative is tuning a constant that provably cannot work.
#
# ONE RULE FOR "PIECES OF THE SAME FIGURE", USED IN BOTH PLACES.  A caption
# claims only regions that touch (CLAIM_GAP_PX), but the uncaptioned path
# clustered anything within 300 px -- so p42's three screenshots, 168 and 204 px
# apart, became one cluster.  That cluster then failed the encloses-text test
# and fell back to its members, which is why p42 came out right; p23's cluster
# PASSED and was emitted whole, which is why its three figures came out as one.
# The seventeenth census put it exactly: the fallback "converts missing into
# merged on cluster-pass pages", and merges stayed at 8 while missing fell 9 to
# 4.  Tesseract over-segments a composite, but the pieces of one figure TOUCH.
FRAME_CLUSTER_PX = CLAIM_GAP_PX   # frames this close are one figure built of boxes
# Asymmetric on purpose -- see the merge in illustrations().
# MEASURED on p133, whose five chip pinouts sit side by side: the gaps BETWEEN
# two different figures there are 248, 300 and 378 px.  At 300 the join merged
# two separate chips into one box.  A fragment of a single object is separated
# by far less than a figure is from its neighbour, so the tolerance has to sit
# below the inter-figure gap, not above the gutter width.
ILLUS_JOIN_X = 150            # below the smallest observed gap between figures
ILLUS_JOIN_Y = 20             # narrow: only touching fragments, never past a caption
# ...or any distance at all, when the figure's own line work crosses the gap.
# The distance no longer gates the join, the PAPER does: a bridge needs either
# line work crossing it or a solid tint running through it, and neither happens
# by accident.  MEASURED: p40's calendar has 2000 px of unclaimed yellow field
# between the two ink islands the layout analysis proposed, so a 700 px cap
# rejected the only evidence that they are one figure.  Half the page width is
# now the limit, which is simply "not the far side of the sheet".
ILLUS_BRIDGE_MAX_PX = 700     # ...for line work, which reaches a gutter's width
ILLUS_BRIDGE_TINT_MAX_PX = 2400   # ...for a tint field, which reaches its own edge
ILLUS_BRIDGE_ROW_FRAC = 0.10  # share of rows carrying dark ink across it
# MEASURED on p40's calendar, whose unclaimed middle reads 0.697: a tint field
# is not solid, because the figure's own cells are knocked out of it in white.
# A bare gutter between two neighbours reads ~0.0, so this separates cleanly.
ILLUS_BRIDGE_TINT_FRAC = 0.55 # a tint field this present running through it
ILLUS_BRIDGE_BAND_FRAC = 0.60 # ...between pieces sharing this much of a band
FRAME_EDGE_MATCH = 0.80 # two rules this aligned in x are one frame's top+bottom
RULE_GAP_PX = 24        # a nick in a printed rule shorter than this is closed


def _runs(profile, thresh, min_len):
    out, start = [], None
    for i, v in enumerate(list(profile) + [0.0]):
        if v > thresh:
            if start is None:
                start = i
        else:
            if start is not None:
                if i - start >= min_len:
                    out.append((start, i))
                start = None
    return out


def strokes(grey, x0, y0, x1, y1):
    """Dark strokes against whatever this region's background happens to be.

    Absolute ink is the wrong measure.  Half this magazine's text sits on a
    SCREENED TINT, and the screen is ink: the whole panel reads as inked, the
    gaps between printed lines vanish, and every table, list and headline on a
    tint came out as a picture -- 24 of 34 boxes on one batch of pages.  What
    marks type is a stroke DARKER THAN ITS OWN BACKGROUND, so the background is
    measured per row and subtracted."""
    cell = grey[y0:y1, x0:x1].astype(np.int16)
    if cell.size == 0:
        return np.zeros(0)
    bg = np.median(cell, axis=1, keepdims=True)
    return (cell < bg - STROKE_CONTRAST).mean(axis=1)


def looks_like_text(grey, x0, y0, x1, y1):
    """Many short stroke runs with clear space between them: type, not picture."""
    rows = strokes(grey, x0, y0, x1, y1)
    if not rows.size or not rows.mean():
        return False
    runs = _runs(rows, TEXT_LINE_FRAC * rows.mean(), 1)
    if len(runs) < TEXT_MIN_RUNS:
        return False
    longest = max(r[1] - r[0] for r in runs)
    return longest < TEXT_MAX_LONGEST * (y1 - y0)


def encloses_text(rec, x0, y0, x1, y1):
    """Does this rectangle swallow a real piece of typesetting?

    A picture does not contain paragraphs.  A data table on a tint does -- that
    is all a table IS -- which is why no measure of ink, screen or tone tells
    the two apart, and why the tint gate lets p22's datasheet and p39's
    specification table through.  Step 020 already labelled every block; a
    region that encloses substantial labelled text is that text.

    Substantial, because a picture may legitimately carry a LABEL inside it --
    p10's screenshot has 'Länge: 18' printed in it, and rejecting on any
    enclosed word at all would throw the screenshot away with the table.
    """
    for b in rec["blocks"]:
        if b["label"] not in ARTICLE_NEIGHBOURS:
            continue
        if b.get("n_words", 0) < ENCLOSED_MIN_WORDS:
            continue
        bx0, by0, bx1, by1 = (v * SCALE for v in b["bbox"])
        ox = min(x1, bx1) - max(x0, bx0)
        oy = min(y1, by1) - max(y0, by0)
        if ox <= 0 or oy <= 0:
            continue
        if ox * oy > ENCLOSED_COVER * (bx1 - bx0) * (by1 - by0):
            return True
    return False


def uniform_tint(grey, x0, y0, x1, y1):
    """Screened and UNIFORM is a tint panel; screened and VARYING is a picture.

    This is the project's own physics (see scan2mrc/CLAUDE.md): the press
    screened a continuous-tone original, so a photograph's dot area varies
    across it, while a flat tint is one ink percentage everywhere.  Averaging
    the halftone away leaves that difference standing -- a tint collapses to a
    constant, a photograph does not.

    It is what separates a data table on a grey panel from a photograph, which
    no measure of ink can do: both are screened, and both are dark.
    """
    cell = grey[y0:y1, x0:x1]
    if cell.size == 0:
        return True
    h, w = cell.shape
    ch, cw = max(1, h // TONE_CELLS), max(1, w // TONE_CELLS)
    coarse = cell[:h // ch * ch, :w // cw * cw].reshape(
        h // ch, ch, w // cw, cw).mean(axis=(1, 3))
    return float(coarse.std()) < TONE_MIN_STD


def grow_to_text(rects, grey, x0, y0, x1, y1, W, H):
    """Expand a rectangle into CONTENT, stopping at text or at blank paper.

    A cluster of OCR scraps marks WHERE a picture is, not how big it is -- its
    hull stops at the last scrap, which is why boxes kept cutting yellow card
    grounds, photo backgrounds and screenshot borders.  So it has to grow.

    But growing until it MEETS text is unbounded in the direction where there
    is none: a column with nothing below it grew to the page edge and produced
    2121x6004 boxes down whole columns.  Each side therefore advances only
    while the strip it would add still carries marks.  The picture's own edge
    stops it, and text stops it earlier if text comes first.
    """
    def marked(a, b, c, d):
        cell = grey[int(b):int(d), int(a):int(c)]
        if cell.size == 0:
            return False
        bg = np.median(cell)
        return float((cell < bg - STROKE_CONTRAST).mean()) > EMPTY_FRAC

    def blocked(a, b, c, d):
        for (rx0, ry0, rx1, ry1), _lab in rects:
            if min(c, rx1) - max(a, rx0) > 0 and min(d, ry1) - max(b, ry0) > 0:
                return True
        return False

    for _ in range(GROW_STEPS):
        moved = False
        for side in range(4):
            if side == 0:
                a, b, c, d = x0 - GROW_PX, y0, x0, y1
            elif side == 1:
                a, b, c, d = x1, y0, x1 + GROW_PX, y1
            elif side == 2:
                a, b, c, d = x0, y0 - GROW_PX, x1, y0
            else:
                a, b, c, d = x0, y1, x1, y1 + GROW_PX
            if a < 0 or b < 0 or c > W or d > H:
                continue
            if blocked(a, b, c, d) or not marked(a, b, c, d):
                continue
            if side == 0: x0 -= GROW_PX
            elif side == 1: x1 += GROW_PX
            elif side == 2: y0 -= GROW_PX
            else: y1 += GROW_PX
            moved = True
        if not moved:
            break
    return x0, y0, x1, y1


def framed_rects(grey, W, H):
    """Find the printed rules directly, and make rectangles out of them.

    This magazine frames nearly every placed figure.  A rule is the figure's own
    edge -- it does not wander across a gutter the way an ink-grown box does,
    and it does not die where the picture goes pale.  Detecting frames FIRST and
    treating the ink evidence as secondary is what three rounds of vision review
    kept pointing at: "snap to the figure's own printed frame".

    A rectangle needs a long horizontal rule, another below it with much the
    same x-extent, and the two vertical rules that close them.
    """
    d = 4
    small = grey[::d, ::d] < BORDER_DARK
    # A printed rule is not continuous: the scan breaks it, and where a figure
    # meets its caption or another rule the corner drops out.  Close short gaps
    # along each direction before looking for runs, so a rule interrupted by a
    # few pixels is still one rule.  Without this only perfectly-printed frames
    # were found, and every figure whose rule had a nick fell through to the
    # much weaker gap and scrap sources.
    h_closed = small.copy()
    v_closed = small.copy()
    for k in range(1, RULE_GAP_PX // d + 1):
        h_closed |= np.roll(small, k, 1) & np.roll(small, -k, 1)
        v_closed |= np.roll(small, k, 0) & np.roll(small, -k, 0)
    sh, sw = small.shape
    minlen = int(MIN_W_PX / d)

    def runs_along(mask, axis):
        out = []
        n = mask.shape[0] if axis == 0 else mask.shape[1]
        for i in range(n):
            line = mask[i] if axis == 0 else mask[:, i]
            start = None
            for j, v in enumerate(list(line) + [False]):
                if v:
                    if start is None:
                        start = j
                elif start is not None:
                    if j - start >= minlen:
                        out.append((i, start, j))
                    start = None
        return out

    h = runs_along(h_closed, 0)
    v = runs_along(v_closed, 1)
    rects = []
    for a in range(len(h)):
        ya, xa0, xa1 = h[a]
        for b in range(a + 1, len(h)):
            yb, xb0, xb1 = h[b]
            if yb - ya < minlen // 2:
                continue
            ov = min(xa1, xb1) - max(xa0, xb0)
            if ov < FRAME_EDGE_MATCH * max(xa1 - xa0, xb1 - xb0):
                continue
            x0, x1 = max(xa0, xb0), min(xa1, xb1)
            # All four sides.  Three was right while frames were the PRIMARY
            # source and recall mattered more than precision; now that captions
            # carry the figures that have one, this path only has to catch the
            # uncaptioned opener or badge, and a half-closed rectangle is far
            # more often two rules that happen to line up.
            left = any(abs(c - x0) <= 3 and r0 <= ya + 3 and r1 >= yb - 3 for c, r0, r1 in v)
            right = any(abs(c - x1) <= 3 and r0 <= ya + 3 and r1 >= yb - 3 for c, r0, r1 in v)
            if left and right:
                rects.append([x0 * d, ya * d, x1 * d, yb * d])
    # keep only the outermost of any nest
    rects.sort(key=lambda r: -(r[2] - r[0]) * (r[3] - r[1]))
    keep = []
    for r in rects:
        if any(r[0] >= k[0] - 8 and r[1] >= k[1] - 8
               and r[2] <= k[2] + 8 and r[3] <= k[3] + 8 for k in keep):
            continue
        keep.append(r)
    return keep


def cut_captions(rec, x0, y0, x1, y1):
    """Shrink a region so it stops before a caption.

    64'er sets its bold captions flush under the figure with no white gap, so a
    rectangle around the picture nearly always swallows the caption line under
    it -- the single most repeated "EXTRA" in the crop review.  Step 020 already
    labelled those blocks; cut at the first one that starts inside the region's
    lower half.
    """
    for b in rec["blocks"]:
        # By label OR by what it says.  A caption is often labelled body, and
        # the printed "Bild 3." / "Tabelle 2." opening is unmistakable -- these
        # are the lines the crops kept swallowing on their way to the next
        # figure.
        first = " ".join(b["text"].split())[:24]
        if b["label"] != "caption" and not CAPTION_OPEN.match(first):
            continue
        bx0, by0, bx1, by1 = (v * SCALE for v in b["bbox"])
        if min(x1, bx1) - max(x0, bx0) < 0.35 * (bx1 - bx0):
            continue                       # not under this figure
        if y0 + 0.4 * (y1 - y0) < by0 < y1:
            y1 = min(y1, int(by0) - CAPTION_GAP_PX)
    return x0, y0, x1, y1


def snap_to_frame(dark, x0, y0, x1, y1, W, H):
    """Extend the box out to the figure's enclosing frame -- ALL FOUR SIDES OR NONE.

    A box fitted to interior content sits inside the frame that encloses it, and
    no fixed pad can reach that frame because the figure's internal margin is
    not a fixed distance.  The frame is, and it is where the magazine says the
    figure ends.

    But a frame is ONE RECTANGLE, and snapping each side independently is not
    the same thing.  Done per-side, every edge walks outward looking for a long
    dark run and takes whatever it meets -- a neighbouring listing's bottom
    rule, a page column rule, a running head, the previous figure's frame -- and
    swallows everything in between.  The fourteenth census found thirteen crops
    made over-large that way, and the same box taking a foreign top rule while
    missing its own bottom one.  So four runs are sought together and accepted
    only if they CLOSE: each side must be dark along the full extent of the
    rectangle the other three describe.  Nearest first, and if nothing closes,
    nothing moves.
    """
    def candidates(fixed_lo, fixed_hi, start, horizontal, outward):
        out = []
        for d in range(1, FRAME_SNAP_PX):
            i = start + d * outward
            if i < MARGIN_PX or i >= (H if horizontal else W) - MARGIN_PX:
                break
            line = dark[i, fixed_lo:fixed_hi] if horizontal \
                else dark[fixed_lo:fixed_hi, i]
            if line.size and float(line.mean()) >= FRAME_RUN_FRAC:
                if not out or abs(out[-1] - i) > FRAME_RULE_SEP_PX:
                    out.append(i)
            if len(out) >= FRAME_MAX_CANDIDATES:
                break
        return out

    tops = [y0] + candidates(x0, x1, y0, True, -1)
    bots = [y1 - 1] + candidates(x0, x1, y1 - 1, True, 1)
    lefts = [x0] + candidates(y0, y1, x0, False, -1)
    rights = [x1 - 1] + candidates(y0, y1, x1 - 1, False, 1)

    def closed(t, b, l, r):
        for line, lo, hi, horiz in ((t, l, r + 1, True), (b, l, r + 1, True),
                                    (l, t, b + 1, False), (r, t, b + 1, False)):
            seg = dark[line, lo:hi] if horiz else dark[lo:hi, line]
            if seg.size == 0 or float(seg.mean()) < FRAME_RUN_FRAC:
                return False
        return True

    for t in tops:
        for b in bots:
            for l in lefts:
                for r in rights:
                    if (t, b, l, r) == (y0, y1 - 1, x0, x1 - 1):
                        continue
                    if closed(t, b, l, r):
                        return l, t, r + 1, b + 1
    return x0, y0, x1, y1


def cut_inside_rule(grey, x0, y0, x1, y1):
    def band(profile):
        """The first THIN dark band near the edge -- a printed rule.

        A thickness limit is what makes this a rule detector rather than an
        edge trimmer.  Without it, a screen photograph's solid status bar is a
        full-width dark band at the bottom of the box, so the "frame" was found
        inside the picture and everything below it discarded: bottom shear was
        10 of 17 crops in the bw bucket, clipping exactly the last screen row
        (39-4, 39-5), the status line (39-3b) or the frame's own bottom rule
        (124-3).  A rule printed at 600 dpi is a few pixels; a status bar is
        tens of them.
        """
        first = None
        for i, v in enumerate(profile[:BORDER_MAX_PX]):
            if v >= BORDER_FRAC:
                if first is None:
                    first = i
            elif first is not None:
                if i - first > BORDER_RULE_MAX_PX:
                    return None
                # A FRAME HAS PAPER INSIDE IT.  Thickness alone does not
                # separate a rule from content: trim_blank has already removed
                # the blank margin, so a genuine rule and a screen dump's own
                # edge both sit flush at index 0.  What a frame has is the white
                # margin printed INSIDE it before the artwork starts; a screen
                # photograph's status bar has more picture immediately behind.
                # MEASURED: the trim moved an edge on 83 of 191 boxes by a
                # median of 10 px, which is precisely the "status line sliced
                # mid-glyph" the tenth census found on 39-3, 39-4 and 93-0.
                inside = profile[i:i + BORDER_INSIDE_PX]
                if len(inside) and float(np.mean(inside)) > BORDER_INSIDE_FRAC:
                    return None
                return first, i
        return None
    blk = grey[y0:y1, x0:x1] < BORDER_DARK
    t = band(blk.mean(axis=1)); b = band(blk.mean(axis=1)[::-1])
    l = band(blk.mean(axis=0)); r = band(blk.mean(axis=0)[::-1])
    if t: y0 += t[1] + BORDER_OVERCUT
    if b: y1 -= b[1] + BORDER_OVERCUT
    if l: x0 += l[1] + BORDER_OVERCUT
    if r: x1 -= r[1] + BORDER_OVERCUT
    return x0, y0, x1, y1


def classify(crop):
    """One of the four types tools/convert-scans.sh knows.

    Saturation is measured over the INK, not over the whole rectangle.  Paper is
    most of a framed figure and paper is neutral, so averaging the rectangle
    drags every measurement toward grey: the red "64'er Test" badge on white
    came out `bw`, and a colour portrait against a desaturated background came
    out `gray`.  What decides the conversion is what was PRINTED, so the paper
    is excluded before asking.
    """
    a = np.asarray(crop).astype(np.int16)
    lum = a.mean(axis=2)
    inked = lum < PAPER_LEVEL
    if inked.sum() < INK_MIN_PX:
        inked = lum < 250                      # nearly blank: use what there is
    chroma = (a.max(axis=2) - a.min(axis=2))
    sat = float(chroma[inked].mean()) if inked.any() else 0.0
    # ...and a colour figure need not be colourful everywhere: a red badge is
    # mostly black type on white with one saturated field.
    strong = float((chroma[inked] > SAT_STRONG).mean()) if inked.any() else 0.0
    if sat > SAT_COLOUR or strong > SAT_STRONG_FRAC:
        return "c"
    gg = np.asarray(crop.convert("L"))

    # THE SCREEN IS A PERIODICITY, SO IT IS MEASURED AS ONE.
    #
    # A median-filter delta was exhausted: at one scale it saw only fine
    # screens, at two it overlapped the clean class outright, and at four the
    # downsampling manufactured the pattern.  A halftone is not "high local
    # variance", it is a LATTICE, and a lattice is a peak in the Fourier
    # transform.  MEASURED over every crop in this issue, in the most toned
    # 256 px window of each: the press screen is 4.4-4.5 px at 44-48 degrees --
    # 133 lpi at 45 degrees, which is what a 1986 web-offset magazine screen is
    # -- with a peak 78 to 411 times the local median.  Everything unscreened
    # peaks at 0 degrees instead: the dot-matrix printer's own orthogonal grid,
    # or the scanner's.  The separation is total, with no overlap anywhere.
    #
    # It also settles a disagreement in favour of the eye: a reviewer reported
    # at 4x zoom that 151-0 and the p32 flowchart carried "an unambiguous press
    # halftone lattice" where the median test called them clean.  They measure
    # 4.5 px at 48.5 and 45.7 degrees.  They were screened.
    screen = screen_angle = 0.0
    if gg.shape[0] >= FFT_WIN and gg.shape[1] >= FFT_WIN:
        best, cell = -1.0, None
        for yy in range(0, gg.shape[0] - FFT_WIN + 1, max(1, (gg.shape[0] - FFT_WIN) // 6 or 1)):
            for xx in range(0, gg.shape[1] - FFT_WIN + 1, max(1, (gg.shape[1] - FFT_WIN) // 6 or 1)):
                c = gg[yy:yy + FFT_WIN, xx:xx + FFT_WIN]
                mid = float(((c > 90) & (c < 215)).mean())
                if mid > best:
                    best, cell = mid, c
        if cell is not None:
            c = cell.astype(np.float64)
            c = (c - c.mean()) * (np.hanning(FFT_WIN)[:, None] * np.hanning(FFT_WIN)[None, :])
            F = np.abs(np.fft.fftshift(np.fft.fft2(c)))
            m = FFT_WIN // 2
            ry, rx = np.mgrid[0:FFT_WIN, 0:FFT_WIN]
            rad = np.hypot(ry - m, rx - m)
            per = np.where(rad > 0, FFT_WIN / np.maximum(rad, 1e-9), 1e9)
            band = (per >= SCREEN_PERIOD_LO) & (per <= SCREEN_PERIOD_HI)
            if band.any():
                v = F[band]
                i = int(np.argmax(v))
                screen = float(v[i] / np.median(F[(per >= 3.0) & (per <= 20.0)]))
                screen_angle = float(np.degrees(np.arctan2((ry - m)[band][i],
                                                           (rx - m)[band][i])) % 90)
    if screen > SCREEN_PEAK_MIN \
            and abs(screen_angle - SCREEN_ANGLE) <= SCREEN_ANGLE_TOL:
        return "dots"
    # CONTINUOUS TONE MEANS REAL MID-TONE AREA.  The old test asked for "more
    # than 26 distinct grey levels in 40..215", and MEASURED across every crop
    # in the issue that number is 44 -- for all of them, screened chip and clean
    # line drawing alike.  It saturates, so it discriminated nothing, and the
    # gray bucket collapsed to "has some non-extreme pixels": four bilevel
    # dot-matrix printouts landed in it (54-1, 58-1, 79-1, 93-0) because
    # scanner blur on their dots reads as grey.  A photograph carries mid-tone
    # over a third of its area; nothing in this issue's line art exceeds 0.10.
    truemid = float(((gg > GRAY_LO) & (gg < GRAY_HI)).mean())
    if truemid > GRAY_MIDTONE_FRAC:
        return "gray"
    return "bw"


def caption_lines(rec):
    """Every printed "Bild 3." / "Tabelle 2." line, with the box it sits in.

    A caption block can carry more than one caption -- p23 sets "Bild 1." and
    "Bild 3." in one block for two figures side by side -- so the block is split
    by line and each caption keeps its own wording.
    """
    out = []
    for b in rec["blocks"]:
        lines = [" ".join(l.split()) for l in b["text"].split("\n") if l.strip()]
        hits = [l for l in lines if CAPTION_OPEN.match(l[:24])]
        if not hits:
            continue
        x0, y0, x1, y1 = (v * SCALE for v in b["bbox"])
        for i, line in enumerate(hits):
            m = CAPTION_OPEN.match(line[:24])
            out.append({"text": line, "kind": m.group(1).title(), "num": m.group(2),
                        "bbox": [int(x0), int(y0), int(x1), int(y1)],
                        "share": len(hits), "index": i, "block": b["id"]})
    return out


def widen(rects, x0, y0, x1, y1, W):
    """Grow a box sideways within its own height until real text stops it.

    An ALTO illustration region is a LOWER bound on a figure, the same way a
    caption's measure is: tesseract marks the picture-like body of a chip
    diagram and leaves the column of pin labels beside it outside, because a
    column of small isolated glyphs is not picture-like.  The union of those
    regions was used as the final box, so 131-3, 131-4 and 131-6 each came out
    missing an entire pin column.  Growth is what turns a lower bound into an
    edge, and now that a figure's own labels are no longer stoppers, it reaches
    them.
    """
    for _ in range(GROW_STEPS):
        moved = False
        for side in (0, 1):
            nx0 = x0 - GROW_PX if side == 0 else x0
            nx1 = x1 if side == 0 else x1 + GROW_PX
            if nx0 < MARGIN_PX or nx1 > W - MARGIN_PX:
                continue
            if any(min(nx1, rx1) - max(nx0, rx0) > 0
                   and min(y1, ry1) - max(y0, ry0) > 0
                   for (rx0, ry0, rx1, ry1), _l in rects):
                continue
            x0, x1 = nx0, nx1
            moved = True
        if not moved:
            break
    return x0, x1


def figure_above(rects, cap, W, H):
    """The rectangle a caption belongs to: directly above it, at its measure.

    This is the whole method, and it is the magazine's own typography rather
    than a guess about pixels.  A figure is set to the width of its caption and
    the caption is set immediately beneath it, so the caption gives the LEFT and
    RIGHT edges and the BOTTOM edge outright.  Only the top has to be found, and
    the first text above that shares the measure gives that.

    Everything the segmentation approach got wrong -- boxes snapped to the
    column grid, captions swallowed, figures split at a gutter, tables taken for
    pictures -- came from deriving those edges from ink instead of reading them
    off the page.
    """
    cx0, cx1 = cap["bbox"][0], cap["bbox"][2]
    # A block holding several captions describes several figures side by side;
    # each takes its share of the measure.
    if cap["share"] > 1:
        w = (cx1 - cx0) / cap["share"]
        cx0, cx1 = int(cx0 + cap["index"] * w), int(cx0 + (cap["index"] + 1) * w)
    bottom = cap["bbox"][1] - CAPTION_GAP_PX

    # THE CAPTION GIVES A LOWER BOUND ON WIDTH, NOT THE WIDTH.
    #
    # A caption is typeset to one text column.  A figure that is WIDER than its
    # caption -- a pinout or a screen dump spanning two columns, captioned under
    # one -- was being clipped to the narrower measure, and everything outside
    # that column was sliced away: 9 of 15 cut crops in a census, plus the cases
    # where one wide figure came out as several column-wide slices.
    #
    # So the caption's measure is where the figure certainly is, and it then
    # grows left and right until real text stops it.
    # THE BAND MUST BE THE FIGURE'S OWN HEIGHT, NOT THE WHOLE PAGE.
    #
    # Growing sideways against a band that ran from the page margin down to the
    # caption meant ANY text above the caption -- the article's headline three
    # columns up, body text at the top of the page -- blocked the growth.  A
    # wide figure captioned under one column could therefore never widen, which
    # is precisely the horizontal truncation a census pinned on 7 of 8 cut
    # crops.  Height and width have to settle together: the top is found at the
    # current width, the width then grows within that height, and a wider figure
    # may meet something new above it, which raises the top again.  Three rounds
    # converge on this issue.
    def find_top(x0, x1):
        t = MARGIN_PX
        for (rx0, ry0, rx1, ry1), _lab in rects:
            if ry1 >= bottom:
                continue                        # not above the caption
            overlap = min(x1, rx1) - max(x0, rx0)
            if overlap < CAPTION_MEASURE_MATCH * min(x1 - x0, rx1 - rx0):
                continue                        # not above this figure at all
            t = max(t, int(ry1) + CAPTION_GAP_PX)
        # A figure is not most of the page.  Where nothing is printed above the
        # caption -- it opens the column -- the top would otherwise fall back to
        # the page margin and take everything with it (p24 came out 4346x5684).
        if bottom - t > MAX_FIGURE_FRAC * H:
            t = int(bottom - MAX_FIGURE_FRAC * H)
        return t

    top = find_top(cx0, cx1)
    for _round in range(SETTLE_ROUNDS):
        for _ in range(GROW_STEPS):
            moved = False
            for side in (0, 1):
                nx0 = cx0 - GROW_PX if side == 0 else cx0
                nx1 = cx1 if side == 0 else cx1 + GROW_PX
                if nx0 < MARGIN_PX or nx1 > W - MARGIN_PX:
                    continue
                band = (nx0, top, nx1, bottom)
                if any(min(band[2], rx1) - max(band[0], rx0) > 0
                       and min(band[3], ry1) - max(band[1], ry0) > 0
                       for (rx0, ry0, rx1, ry1), _l in rects):
                    continue
                cx0, cx1 = nx0, nx1
                moved = True
            if not moved:
                break
        ntop = find_top(cx0, cx1)
        if ntop == top:
            break
        top = ntop
    return [cx0, top, cx1, bottom]


def illustrations(rec, dark, marked):
    """Tesseract's own verdict on where the pictures are, in master pixels.

    This is the primary source and it costs nothing: step 010's OCR pass already
    computed it, and only the TSV renderer threw it away.  On p8 it returns the
    portrait at 1452x1152+772+716 against a hand-measured 1355x1119+835+732 --
    slightly generous, which is the right direction, because the surplus is the
    printed rule and that is trimmed afterwards.
    """
    raw = []
    for r in rec.get("regions", ()):
        if r["kind"] != "illustration":
            continue
        x0, y0, x1, y1 = (int(v * SCALE) for v in r["bbox"])
        raw.append([x0, y0, x1, y1])

    # AN ILLUSTRATION IS A LAYOUT BLOCK, NOT AN OBJECT.
    #
    # Tesseract splits the page into columns first and classifies afterwards, so
    # a picture wider than the column grid comes back as one fragment per column
    # cell.  A census found this the dominant defect: 131-2 is exactly the left
    # pin column of a chip whose body begins at the crop's edge, 30-2 a 690 px
    # sliver of a flowchart cut on both sides, 172-00 a C 64 screen at aspect
    # 1.05 where the real thing is 1.6.
    #
    # The fragments of one object touch.  Union them BEFORE anything else looks
    # at them, so what leaves here is an object and not a cell of the grid.
    # The tolerance is ASYMMETRIC, because the geometry is.
    #
    # Fragments of one object are separated HORIZONTALLY by a column gutter,
    # which is wide; two different objects are separated VERTICALLY by a caption
    # and its leading, which is narrow.  One distance for both axes gets it
    # exactly backwards -- at 90 px each way the horizontal merge never fired
    # (the gutter is wider) while the vertical one always did, so a figure was
    # joined to the NEXT figure below it and still cut at the column wall.
    # A census found both failures on one page: p131's pinouts came out as
    # left-column slivers AND as a merged four-figure block.
    caps_y = [([v * SCALE for v in b["bbox"]], b["label"]) for b in rec["blocks"]
              if b["label"] == "caption"]

    def caption_between(a, b):
        lo, hi = min(a[3], b[3]), max(a[1], b[1])
        for (cx0, cy0, cx1, cy1), _l in caps_y:
            if lo <= cy0 <= hi and min(a[2], b[2]) - max(a[0], b[0]) > 0:
                return True
        return False

    def bridged(m, r):
        """Does line work run from one region into the other?

        An ALTO illustration is a LAYOUT block, so a figure wider than a column
        comes back as one region per column and the join has to put them back
        together.  Distance cannot decide it: the gutter between two halves of
        p30's flowchart is wider than the 248 px between two SEPARATE chips on
        p133, so any tolerance loose enough to repair the flowchart merges the
        chips.  The eleventh census caught this by its signature -- complementary
        pairs, 30-1 and 30-2 tiling one flowchart with the arrows severed at the
        seam, 131-5 and 131-7 the same two chips shorn on opposite sides.

        What separates the cases is on the paper: a split figure's own rules and
        arrows CROSS the gutter, and two neighbours have bare paper between
        them.  Measured on DARK ink rather than the marked mask, so that two
        chips sharing one screened tint panel are not bridged by the tint.
        """
        lo, hi = (m, r) if m[2] <= r[0] else (r, m)
        gx0, gx1 = int(lo[2]), int(hi[0])
        gy0, gy1 = int(max(m[1], r[1])), int(min(m[3], r[3]))
        if gx1 - gx0 <= 0 or gy1 - gy0 <= 0:
            return True                         # they touch or overlap already
        if gx1 - gx0 > ILLUS_BRIDGE_TINT_MAX_PX:
            return False
        strip = dark[gy0:gy1, gx0:gx1]
        if strip.size == 0:
            return False
        # Line work reaches only as far as a column gutter: widening this to the
        # tint bridge's span merged p27's two greeting cards, whose own rules
        # are strong enough to look like a crossing at any distance.  The two
        # tests get the reach their evidence justifies, not a shared constant.
        if gx1 - gx0 <= ILLUS_BRIDGE_MAX_PX \
                and float(strip.any(axis=1).mean()) > ILLUS_BRIDGE_ROW_FRAC:
            return True
        # A CONTINUOUS TINT FIELD IS ONE PRINTED OBJECT TOO.
        #
        # Line work is not the only thing that can run between two regions.
        # Where the figure is a tint hardcopy, the layout analysis proposes only
        # the ink islands ON the tint and leaves the flat field between them
        # unclaimed, so the pieces never rejoin: p40's calendar came out as two
        # narrow strips carrying the IDENTICAL caption, with the "SEPTEMBER 86"
        # head and the whole grid -- some 80% of the figure -- written to no
        # file at all.  The fourteenth census called this the mechanism that
        # destroys content, as against the merges which are merely loud.
        #
        # Bare paper still separates: this asks whether the gap is INKED, and a
        # gutter between two neighbours is not.  p133's chips each sit on their
        # own tint with white paper between, so they stay apart.
        # ...and only between pieces that share a BAND.  Two halves of one wide
        # figure lie at the same height; a tint bridge without that condition
        # reached between figures merely near each other and merged p27's two
        # greeting cards.  The overlap is measured against the shorter piece, so
        # a small island on a tint still joins the field it sits in.
        span = min(m[3], r[3]) - max(m[1], r[1])
        if span < ILLUS_BRIDGE_BAND_FRAC * min(m[3] - m[1], r[3] - r[1]):
            return False
        gap = marked[gy0:gy1, gx0:gx1]
        return gap.size > 0 and float(gap.mean()) > ILLUS_BRIDGE_TINT_FRAC

    merged = []
    for r in sorted(raw, key=lambda r: (r[1], r[0])):
        for m in merged:
            if ((min(m[2], r[2]) - max(m[0], r[0]) > -ILLUS_JOIN_X or bridged(m, r))
                    and min(m[3], r[3]) - max(m[1], r[1]) > -ILLUS_JOIN_Y
                    and not caption_between(m, r)):
                m[0], m[1] = min(m[0], r[0]), min(m[1], r[1])
                m[2], m[3] = max(m[2], r[2]), max(m[3], r[3])
                break
        else:
            merged.append(list(r))

    # A screened tint is picture-like to the layout analysis, so the page's own
    # furniture -- the black section banner, the tint behind a headline --
    # arrives as an illustration.  Those sit on a running head or a folio.
    furniture = [[v * SCALE for v in b["bbox"]] for b in rec["blocks"]
                 if b["label"] in ("header", "footer")]
    out = []
    for m in merged:
        if any(min(m[2], f[2]) - max(m[0], f[0]) > 0
               and min(m[3], f[3]) - max(m[1], f[1]) > 0 for f in furniture):
            continue
        out.append(m)
    return out


def figures(page):
    lab = os.path.join(OB.OUT_DIR, f"{page:03d}.labels.json")
    raw = os.path.join(OB.OUT_DIR, f"{page:03d}.json")
    src = lab if os.path.exists(lab) else raw
    rec = json.load(open(src, encoding="utf-8"))
    # Labels come from step 020's record, but the LAYOUT REGIONS come from step
    # 010's -- step 020 copies the blocks forward and a verdict written before
    # regions existed carries none, so reading them from labels.json silently
    # yields an empty list and every page returns no figures.
    if not rec.get("regions") and os.path.exists(raw):
        rec["regions"] = json.load(open(raw, encoding="utf-8")).get("regions", [])
    im = Image.open(os.path.join(OB.SRC_DIR, f"{page:03d}.png")).convert("RGB")
    W, H = im.size
    grey = np.asarray(im.convert("L"))
    # PAPER IS BRIGHT *AND* NEUTRAL.  Luminance alone cannot see a yellow tint
    # panel: yellow is the brightest ink there is and a 100% Y field measures
    # 220+, well above PAPER_LEVEL, so `grey < PAPER_LEVEL` reported p143's
    # panel as bare paper and every panel edge was invisible.  A tint is bright
    # but COLOURED, and the scanned paper is not.
    _rgb = np.asarray(im).astype(np.int16)
    marked = (grey < PAPER_LEVEL) | ((_rgb.max(axis=2) - _rgb.min(axis=2)) > TINT_SAT)
    if rec.get("page_kind") in SKIP_PAGE_KINDS:
        return [], rec, im

    blocks = [b for b in rec["blocks"] if b["label"] != "noise"]
    rects = [([v * SCALE for v in b["bbox"]], b["label"]) for b in blocks]
    # A FIGURE'S OWN LABELS ARE NOT ITS BOUNDARY.
    #
    # A chip's pin names, a menu's text column, the row of digits down the edge
    # of a printout: the OCR reads all of them as text, so growth stopped short
    # and the rectangle closed INSIDE the figure.  That is 12 of the 20 cut
    # crops in the seventh census -- 131-3, 131-4 and 131-6 lose an entire pin
    # column, 39-4, 39-5 and 93-0 lose a menu, 58-1, 58-2, 74-3 and 79-1 lose a
    # printout's right margin -- and it was the one defect five rounds of
    # geometry never touched.
    #
    # What separates them from body text is physical, not typographic: the
    # magazine's text is set on BARE PAPER, while a figure's labels sit on the
    # figure -- a screened tint, a coloured panel, or a reversed screen
    # photograph.  Measured with the same mask as everything else, a block of
    # body text reads 0.1-0.3 marked and a label on tint or in reverse reads
    # 0.6-1.0.  The word count is required as well, because a page that is one
    # big tint panel would otherwise disqualify its own body columns: labels are
    # short, paragraphs are not.
    def on_figure(b, bb):
        # A CAPTION IS ALWAYS A BOUNDARY.  It is short, and where the figures
        # are tint panels it sits against them, so it satisfied both halves of
        # the on-figure test and stopped being a stopper -- which let a box grow
        # straight up through the caption of the figure above and merge the two.
        # The ninth census found nine such merges in the colour bucket alone
        # (21-1, 27-2, 27-4, 39-3, 160-2, 172-0 stacked vertically).  Panel
        # growth has its own, narrower exemption for a figure's OWN caption.
        if b.get("label") == "caption":
            return False
        if b.get("n_words", 0) > TINT_BLOCK_MAX_WORDS:
            return False
        x0, y0, x1, y1 = (int(v) for v in bb)
        cell = marked[max(0, y0):y1, max(0, x0):x1]
        return cell.size > 0 and cell.mean() > BLOCK_TINT_FRAC

    # STRUCTURE IS NOT PROSE, SO THE WORD COUNT MUST NOT FILTER IT.
    #
    # The minimum exists to keep a stray two-word fragment from bounding a
    # figure.  Applied to captions, running heads and folios it removed the very
    # boundaries the layout is built from: MEASURED over this issue, 424
    # headers, 229 footers and 19 captions were dropped -- "Bild 2." is two
    # words.  The eleventh census named the consequence exactly, "caption is a
    # stopper for starts, not for growth", and its other two defect forms are
    # the same omission: boxes growing up into a rubric badge (24-1), a running
    # head (27-3) or an article deck (30-0).
    stoppers = [(bb, lab) for (bb, lab), b in zip(rects, blocks)
                if (lab in STRUCTURAL_LABELS
                    or b.get("n_words", 0) >= TOP_STOP_MIN_WORDS)
                and not on_figure(b, bb)]

    illus = illustrations(rec, grey < BORDER_DARK, marked)
    caps = caption_lines(rec)
    found, claimed = [], set()

    # --- A caption names a figure; the illustrations under it ARE that figure.
    #
    # Tesseract over-segments a composite: p27's two greeting cards came back as
    # eight illustrations and p31's one flowchart as five, because each panel and
    # node is separately picture-like.  The caption is what says how many figures
    # there really are, so every illustration sitting in a caption's band is
    # unioned into one.
    for cap in caps:
        cx0, cy0, cx1, cy1 = cap["bbox"]
        if cap["share"] > 1:
            w = (cx1 - cx0) / cap["share"]
            cx0, cx1 = int(cx0 + cap["index"] * w), int(cx0 + (cap["index"] + 1) * w)
        # A CAPTION'S BAND STOPS AT THE CAPTION ABOVE IT.  Reaching 62% of the
        # page upward, the band ran over the previous figure AND its caption, so
        # one caption claimed the illustrations of the figure above and unioned
        # both into a single crop.  The ninth census found nine of these merges
        # in the colour bucket alone -- 27-2 came out 2151x5512 px, holding
        # "Bild 1", its caption and "Bild 2".  A caption belongs to the figure
        # above it, so the previous caption's foot is where this figure starts.
        band_top = cy0 - int(MAX_FIGURE_FRAC * H)
        for other in caps:
            oy1 = other["bbox"][3]
            if oy1 >= cy0 or other is cap:
                continue
            if min(cx1, other["bbox"][2]) - max(cx0, other["bbox"][0]) <= 0:
                continue                        # a different column
            band_top = max(band_top, int(oy1) + CAPTION_GAP_PX)
        near = [i for i, r in enumerate(illus)
                if i not in claimed and r[3] <= cy0 + CAPTION_GAP_PX and r[3] >= band_top
                and min(cx1, r[2]) - max(cx0, r[0]) > CAPTION_MEASURE_MATCH * min(cx1 - cx0, r[2] - r[0])]
        # A CAPTION NAMES ONE FIGURE, NOT EVERYTHING ABOVE IT.
        #
        # Claiming every region in the band unioned separate figures whenever a
        # page carried one caption and several pictures: p42's three Spindizzy
        # screenshots came out as a single box, and the fifteenth census found
        # seven printed figures that existed in NO file for this reason -- two on
        # p42, one on p43, three book covers on p128.  They were not dropped by
        # any filter; they were absorbed.
        #
        # A figure may still arrive as several regions, because tesseract
        # over-segments a composite -- but those pieces TOUCH.  So the claim
        # starts at the region nearest the caption and grows only through gaps
        # narrower than the space the magazine leaves between two figures.
        # MEASURED on p42, whose three screenshots are 168 and 204 px apart.
        mine = []
        if near:
            near.sort(key=lambda i: -illus[i][3])
            mine = [near[0]]
            lo, hi = illus[near[0]][1], illus[near[0]][3]
            for i in near[1:]:
                r = illus[i]
                if min(hi, r[3]) - max(lo, r[1]) > -CLAIM_GAP_PX:
                    mine.append(i)
                    lo, hi = min(lo, r[1]), max(hi, r[3])
        if mine:
            claimed.update(mine)
            xs = [illus[i] for i in mine]
            box = [min(r[0] for r in xs), min(r[1] for r in xs),
                   max(r[2] for r in xs), max(r[3] for r in xs)]
            # The caption is a grouping key and a name -- never content.  The
            # union of several fragments reached past it and swallowed it whole
            # (131-4 carried "Bild 2. Anschlußplan des Prozessors 6510" between
            # two chips), so the box stops above the caption it belongs to.
            box[3] = min(box[3], cy0 - CAPTION_GAP_PX)
            # ...and it cannot start above the caption of the figure above it.
            # Bounding which regions may be CLAIMED is not enough: tesseract
            # sometimes returns one region spanning both figures, and then the
            # union is that single region.  p028's two greeting cards came back
            # as one 2142x6000 box on a 7015 px page with "Bild 3." swallowed in
            # the middle.  The band is a property of the figure, so it clips the
            # box as well as the claim.
            box[1] = max(box[1], band_top)
            box[0], box[2] = widen(stoppers, box[0], box[1], box[2], box[3], W)
        else:
            box = figure_above(stoppers, cap, W, H)   # no illustration: fall back
        found.append({"bbox": box, "ink": 0.0, "caption": cap["text"],
                      "kind": cap["kind"], "num": cap["num"],
                      "anchor": [cap["bbox"][0], cap["bbox"][2]],
                      "cap_bbox": list(cap["bbox"])})

    # --- An illustration no caption claims is an opener, a cover or a badge.
    leftover = [r for i, r in enumerate(illus) if i not in claimed]
    # NEVER CLUSTER ACROSS SOMETHING PRINTED BETWEEN THE TWO.
    #
    # This is the path an uncaptioned figure takes, and it consulted no text at
    # all: two regions close enough in both axes were merged whether or not a
    # caption or a paragraph was set between them.  That is how p28's two
    # greeting cards became one crop with the caption of the first swallowed in
    # the middle -- and the tenth census found every remaining caption defect to
    # be exactly this, an interior caption absorbed by a merge, after the
    # trailing-caption case had been fixed everywhere else.
    def parted(a, b):
        lo, hi = (a, b) if a[3] <= b[1] else (b, a)
        if lo[3] > hi[1]:
            return False                        # they overlap vertically
        for (rx0, ry0, rx1, ry1), _lab in stoppers:
            if ry0 >= lo[3] and ry1 <= hi[1] and \
                    min(hi[2], rx1) - max(hi[0], rx0) > 0:
                return True
        return False

    clustered, c_members = [], {}
    for r in sorted(leftover, key=lambda r: (r[1], r[0])):
        for c in clustered:
            if parted(c, r):
                continue
            if (min(c[2], r[2]) - max(c[0], r[0]) > -FRAME_CLUSTER_PX
                    and min(c[3], r[3]) - max(c[1], r[1]) > -FRAME_CLUSTER_PX):
                c_members.setdefault(id(c), [list(c)]).append(list(r))
                c[0], c[1] = min(c[0], r[0]), min(c[1], r[1])
                c[2], c[3] = max(c[2], r[2]), max(c[3], r[3])
                break
        else:
            clustered.append(list(r))
    # A CLUSTER THAT FAILS FALLS BACK TO ITS MEMBERS.  Rejecting the union threw
    # away every figure inside it: p42's three screenshots were clustered into
    # one box spanning two of them, that box enclosed the body text between
    # them, and BOTH were discarded -- which is why the fifteenth and sixteenth
    # censuses kept finding printed figures with "no box drawn on them at all"
    # (two on p42, one on p43, three covers on p128, p23's Bild 3).  The union
    # failing says the union is wrong, not that its parts are.
    checked = []
    for c in clustered:
        if not encloses_text(rec, *c):
            checked.append(c)
            continue
        checked.extend(m for m in c_members.get(id(c), ()) if not encloses_text(rec, *m))

    for x0, y0, x1, y1 in checked:
        if False:
            continue
        for px0, py0, px1, py1 in gutter_pieces(marked, x0, y0, x1, y1):
            found.append({"bbox": [px0, py0, px1, py1], "ink": 0.0,
                          "caption": None, "kind": None, "num": "0",
                          "anchor": [px0, px1]})

    # SPLITTING MUST NOT DELETE.  Keeping the anchor's piece and discarding the
    # rest is right only when every other piece has a caption of its own to be
    # found by.  Where it does not, the figure simply vanished: the thirteenth
    # census caught p24's Knebellaufwerk photograph and p172's IMAGES hardcopy
    # with no box and no file anywhere, and warned that the merge count had
    # fallen partly because the content was gone rather than separated.  This
    # project has deleted real content by subtraction before.  Every piece is
    # emitted; the anchor's keeps the caption and its number, the others become
    # uncaptioned figures and are numbered like any opener.
    split = []
    for f in sorted(found, key=lambda f: (f["bbox"][1], f["bbox"][0])):
        bx0, by0, bx1, by1 = trim_blank(marked, *f["bbox"])
        ax0, ax1 = f.get("anchor", [bx0, bx1])
        cb = f.get("cap_bbox")
        ay0, ay1 = (by1 - MIN_H_PX, by1) if cb is not None else (by0, by1)
        keep = cut_at_gutter(marked, bx0, by0, bx1, by1, ax0, ax1)
        keep = cut_at_band(marked, *keep, ay0, ay1)
        for px0, py0, px1, py1 in gutter_pieces(marked, bx0, by0, bx1, by1):
            for qx0, qy0, qx1, qy1 in band_pieces(marked, px0, py0, px1, py1):
                mine = (qx0 <= keep[0] and keep[2] <= qx1
                        and qy0 <= keep[1] and keep[3] <= qy1)
                g = dict(f, bbox=list(keep) if mine else [qx0, qy0, qx1, qy1])
                if not mine:
                    g.update(caption=None, kind=None, num="0", cap_bbox=None,
                             anchor=[qx0, qx1])
                split.append(g)

    out = []
    for f in split:
        x0, y0, x1, y1 = f["bbox"]
        y0, y1 = grow_to_panel(marked, x0, y0, x1, y1, H, stoppers,
                               f.get("cap_bbox"))
        x0, y0, x1, y1 = trim_blank(marked, x0, y0, x1, y1)
        x0, y0, x1, y1 = cut_inside_rule(grey, x0, y0, x1, y1)
        x0, y0, x1, y1 = snap_to_frame(grey < BORDER_DARK, x0, y0, x1, y1, W, H)
        if x1 - x0 < MIN_W_PX or y1 - y0 < MIN_H_PX:
            continue
        # No figure in this magazine is a ribbon.  A 350x2830 sliver is a column
        # of pin labels sheared off a chip diagram, not a picture -- the rewrite
        # dropped this guard and they came straight back.
        if max(x1 - x0, y1 - y0) > MAX_ASPECT * min(x1 - x0, y1 - y0):
            continue
        # A BOX HOLDING TWO CAPTIONS IS TWO FIGURES.  The caption is what says
        # how many figures there are, so a box that has swallowed two of them
        # has swallowed two figures and everything between: 131-5 came out as
        # four pinouts and two captions in one crop, while the same pinouts were
        # ALSO emitted individually -- the census found the same artwork in
        # three files.  Dropping the container leaves the per-caption boxes,
        # which are the figures.  One caption inside is normal: 64'er sets some
        # captions within the figure's own tint panel (p143).
        # Counted as LINES, not as blocks.  One block can set two captions side
        # by side (p23 sets "Bild 1." and "Bild 3." together), and collapsing
        # them by bounding box made a two-figure container look like a one-
        # caption figure -- the tenth census found four such boxes whose caption
        # text carries two "Bild N." matches.
        inside = [c for c in caps
                  if x0 <= c["bbox"][0] and c["bbox"][2] <= x1
                  and y0 <= c["bbox"][1] and c["bbox"][3] <= y1]
        if len(inside) >= MAX_CAPTIONS_INSIDE + 1:
            continue
        # TWO CAPTIONS CAN CLAIM THE SAME ARTWORK.  Where a figure carries more
        # than one caption -- a pair of chips captioned "Bild 3." and "Bild 4."
        # -- each caption unions the same regions and the same picture is cut
        # twice, each copy shorn on a different side.  The eleventh census found
        # 131-5 and 131-7 to be exactly this: the same two chips, one missing
        # its right column and the other its left.  Keep the larger.
        dup = None
        for k, o in enumerate(out):
            ox0, oy0, ox1, oy1 = o["bbox"]
            iw = min(x1, ox1) - max(x0, ox0)
            ih = min(y1, oy1) - max(y0, oy0)
            if iw <= 0 or ih <= 0:
                continue
            inter = iw * ih
            if inter > DUPLICATE_FRAC * min((x1 - x0) * (y1 - y0),
                                            (ox1 - ox0) * (oy1 - oy0)):
                dup = k
                break
        if dup is not None:
            o = out[dup]
            if (x1 - x0) * (y1 - y0) <= (o["bbox"][2] - o["bbox"][0]) * (o["bbox"][3] - o["bbox"][1]):
                continue                        # the one already kept is bigger
            out.pop(dup)
        # FITTING TO STRONG INK SHAVES THE THIN STROKES OUTSIDE IT.
        #
        # Frames and pin boxes are heavy; the labels beyond them are hairlines.
        # A box fitted to the heavy structure leaves nothing for them, and the
        # twelfth census found the damage to be a few pixels doing real harm:
        # p133's PLA lost the vertical stems of "F7 F6 F5 F4", which read as
        # "=7 =6 =5 =4", and "GND" sat on column 0 with its G cut.  The reviewer
        # put the fix exactly: a pad of one x-height clears all of them.
        #
        # It can only ever add paper or the figure's own outlying marks, because
        # it stops at a stopper -- the same boundary everything else here uses.
        for _ in range(FIT_PAD_PX):
            for side in range(4):
                nx0, ny0, nx1, ny1 = x0 - (side == 0), y0 - (side == 1), \
                                     x1 + (side == 2), y1 + (side == 3)
                if nx0 < MARGIN_PX or ny0 < MARGIN_PX \
                        or nx1 > W - MARGIN_PX or ny1 > H - MARGIN_PX:
                    continue
                if any(min(nx1, rx1) - max(nx0, rx0) > 0
                       and min(ny1, ry1) - max(ny0, ry0) > 0
                       for (rx0, ry0, rx1, ry1), _l in stoppers):
                    continue
                x0, y0, x1, y1 = nx0, ny0, nx1, ny1
        crop = im.crop((x0, y0, x1, y1))
        out.append({"bbox": [x0, y0, x1, y1], "w": x1 - x0, "h": y1 - y0,
                    "ink": f["ink"], "type": classify(crop),
                    "caption": f.get("caption"), "kind": f.get("kind"),
                    "num": f.get("num"), "crop": crop})
    return out, rec, im


def grow_to_panel(marked, x0, y0, x1, y1, H, stoppers, own_cap):
    """Extend the box down and up over its own tint panel.

    Where a figure is printed on a coloured panel, the PANEL is the object and
    its edge is where the tint stops.  Neither the OCR's illustration region nor
    the caption knows that: on p143 the region ended half way down the block
    diagram and the caption is set INSIDE the panel beside the figure rather
    than beneath it, so both the region union and the caption anchor cut the
    Netz/Transformator/RAM boxes off the bottom.

    Bare paper is the stop, which is why this cannot run away: over a picture on
    white paper the very first row outside the box is already paper and nothing
    moves.  Text is a stop too -- a tint panel that continues behind a body
    column belongs to the page, not to the figure.
    """
    if x1 - x0 < MIN_W_PX:
        return y0, y1

    def tinted(y):
        row = marked[y, x0:x1]
        return row.size and row.mean() > PANEL_TINT_FRAC
    def free(y):
        # A figure's OWN caption does not bound it.  64'er sets some captions
        # INSIDE the tint panel beside the artwork (p143) rather than beneath
        # it, and stopping there cut the bottom quarter -- the Netz,
        # Transformator and RAM boxes -- off the block diagram.
        #
        # ONLY its own, though.  Letting a panel through ANY caption let p040's
        # calendar grow down across "Bild 2. Der obere Teil eines
        # Kalender-Ausdrucks" and swallow the Graphic-Editor screenshot below
        # it: a caption that belongs to a DIFFERENT figure is exactly the
        # boundary between two figures.  Noise passes unconditionally -- it is
        # text the OCR read OFF the picture, so it is evidence the figure
        # continues.  Body text always stops it.
        for (rx0, ry0, rx1, ry1), lab in stoppers:
            if not (ry0 <= y <= ry1 and min(x1, rx1) - max(x0, rx0) > 0):
                continue
            if lab == "noise":
                continue
            if lab == "caption" and cap_inside \
                    and min(ry1, own_cap[3]) - max(ry0, own_cap[1]) > 0 \
                    and min(rx1, own_cap[2]) - max(rx0, own_cap[0]) > 0:
                continue                        # its own caption, INSIDE the panel
            return False
        return True
    # A PANEL HAS WHITE ON IT.  The figure's own boxes are knocked out of the
    # tint, so a strict row-by-row test stops at the first one: p143 halted at a
    # row reading 0.435 marked -- the white field around a box, well inside the
    # panel -- and left the Netz, Transformator and RAM boxes outside.  So a
    # short unmarked run is crossed if the tint resumes beyond it, exactly as
    # the rule detector already closes a nick in a printed rule.
    def edge(y, step):
        for d in range(0, PANEL_GAP_PX, PANEL_STEP_PX):
            yy = y + d * step
            if not (MARGIN_PX <= yy < H - MARGIN_PX):
                return None
            row = marked[yy, x0:x1]
            # BARE PAPER ENDS THE PANEL; A WHITE BOX ON IT DOES NOT.
            #
            # Crossing any short unmarked run let growth step over the gap
            # BETWEEN two stacked figures, merging them -- p27's two greeting
            # cards came out as one 2151x5512 crop.  Size cannot separate the
            # two cases, but the paper can: a white field knocked out of a panel
            # still has panel either side of it, while the gap between two
            # figures is bare edge to edge.  MEASURED: p143's internal white
            # field reads 0.435 marked across the box, p27's inter-card gap
            # reads 0.00.
            if row.size and row.mean() < PANEL_BARE_FRAC:
                return None
            # A STOPPER ENDS THE SCAN; IT IS NOT SOMETHING TO LOOK PAST.
            #
            # Failing one step and continuing meant the gap window simply
            # stepped OVER whatever blocked it, so a caption shorter than the
            # window was jumped: p028's "Bild 3." is 64 px tall against a 120 px
            # window, and the box ran from one greeting card through the caption
            # to the next, 6000 px of a 7015 px page.  This is why the tenth
            # census still found every remaining caption defect to be an
            # interior caption absorbed by a merge -- the boundary was being
            # tested and then skipped.
            if not free(yy):
                return None
            if tinted(yy):
                return yy + step * PANEL_STEP_PX
        return None

    # ...AND ONLY WHEN THE CAPTION IS PRINTED ON THE PANEL.
    #
    # "Is there panel BELOW the caption" was the wrong question and the eighth
    # census caught it being answered by the very thing it was meant to exclude:
    # where two tint panels or two pinouts are stacked with a caption between
    # them, the SECOND figure is the panel found below, so the box crossed the
    # caption and swallowed it -- 8 of the 9 remaining caption defects, and the
    # cause of every duplicate the census found.
    #
    # The question that actually separates the two layouts is whether the
    # caption sits ON the tint.  p143's is set inside the panel beside the
    # artwork, so its own rows are tinted; an ordinary caption is set on bare
    # paper beneath the figure, so they are not.  It reads the caption itself
    # rather than guessing from what lies beyond it.
    # A CAPTION INSIDE A PANEL HAS PANEL BESIDE IT.
    #
    # "Its own rows are tinted" is true of a caption set between two STACKED
    # tint figures as well -- it is printed on the card below it -- so p028's
    # "Bild 3." passed the test and growth ran down through it into the next
    # greeting card, 6000 px of a 7015 px page.  p143's caption is set into a
    # corner of its panel and has artwork to its left at the same height;
    # p028's spans the full measure with nothing beside it.  Looking sideways
    # at the caption's own row separates them.
    cap_inside = False
    if own_cap is not None:
        mid = int((own_cap[1] + own_cap[3]) / 2)
        if MARGIN_PX <= mid < H - MARGIN_PX and tinted(mid):
            row = marked[mid, x0:x1]
            beside = np.concatenate([row[:max(0, int(own_cap[0]) - x0)],
                                     row[max(0, int(own_cap[2]) - x0):]])
            cap_inside = (beside.size > CAP_BESIDE_PX
                          and float(beside.mean()) > PANEL_TINT_FRAC)

    # THE CLAMP HERE IS NOT THE ONE USED FOR A GUESS.  MAX_FIGURE_FRAC guards
    # the caption fallback, where a figure with nothing printed above it would
    # otherwise take the whole page.  Panel growth is not a guess -- every row
    # it crosses is measured tint and every stopper still stops it -- so it
    # inherited a cap it did not need, and cut a rectangle out of the middle of
    # every figure larger than 62% of the page.  The eighth census found seven:
    # 89-0, 39-1, 93-0, 58-2, 30-1, 30-2, 131-3.  This magazine prints
    # near-full-page schematics (the C 64 foldout, pp. 86-91).
    lim = int(PANEL_MAX_FRAC * H)
    while y1 - y0 < lim:
        nxt = edge(y1, 1)
        if nxt is None or nxt <= y1:
            break
        y1 = nxt
    while y1 - y0 < lim:
        nxt = edge(y0 - 1, -1)
        if nxt is None or nxt >= y0:
            break
        y0 = nxt
    return max(MARGIN_PX, y0), min(H - MARGIN_PX, y1)


def cut_at_gutter(marked, x0, y0, x1, y1, ax0, ax1):
    """Stop the box at a full-height strip of bare paper.

    Growing sideways stops at TEXT RECTANGLES, and that is not the same thing as
    stopping at the edge of the figure.  Where the OCR returned no rectangle --
    a table set on a tint, which it reads poorly -- the growth ran straight
    through it: p143's block diagram came out with the whole "Vergleichstabelle
    C 128" riding along beside it.

    The boundary the rectangles missed is physically on the paper.  Two printed
    objects side by side are separated by a strip of bare paper running the full
    height of both; no photograph, diagram or tint panel has one through its
    middle.  So the box is split at any such strip and the piece the CAPTION
    sits under is kept -- the caption is what says which of the two is ours.
    """
    cell = marked[y0:y1, x0:x1]
    if cell.size == 0 or x1 - x0 < 2 * GUTTER_MIN_PX:
        return x0, y0, x1, y1
    # a gutter column carries essentially no mark over the box's whole height
    blank = cell.sum(axis=0) <= BARE_MAX_PX
    segs, run = [], None
    for i, b in enumerate(list(blank) + [True]):
        if b and run is None:
            run = i
        elif not b and run is not None:
            if i - run >= GUTTER_MIN_PX:
                segs.append((run, i))
            run = None
    if run is not None and len(blank) + 1 - run >= GUTTER_MIN_PX:
        segs.append((run, len(blank)))
    if not segs:
        return x0, y0, x1, y1
    # the anchor's centre picks the piece to keep
    # WHEN THE ANCHOR'S CENTRE FALLS IN THE GAP, NEITHER TEST FIRES.
    #
    # A caption that spans both figures -- or an uncaptioned box, whose anchor is
    # the box itself -- has its midpoint in the very strip that separates them,
    # and a strip is neither "before" nor "after" it, so no cut was made at all.
    # MEASURED: every one of the five merges the twelfth census left had a
    # qualifying bare run inside it (24-2 a 105 px gutter, 172-0 a 209 px band,
    # 21-1 a 71 px band) and the splitter fired on none of them.  Falling in the
    # gap means the anchor cannot choose, so the larger piece is taken.
    mid = (ax0 + ax1) / 2 - x0
    for a, b in segs:
        if a < mid < b:
            mid = a if a > (x1 - x0) - b else b
            break
    lo, hi = 0, x1 - x0
    for a, b in segs:
        if b <= mid:
            lo = max(lo, b)
        elif a >= mid:
            hi = min(hi, a)
    if hi - lo < MIN_W_PX:
        return x0, y0, x1, y1
    return x0 + int(lo), y0, x0 + int(hi), y1


def cut_at_band(marked, x0, y0, x1, y1, ay0, ay1):
    """The same cut as cut_at_gutter, across rows instead of columns.

    A bare strip of paper separates two printed objects whichever way it runs,
    but only the vertical case was implemented, so two figures stacked in one
    column stayed merged.  Growth cannot catch these: the box is already
    spanning the gap before any scan starts -- p27's box is clamped to 62% of
    the page and lands with one greeting card above the gap and one below.  The
    caption says which piece is the figure, exactly as it does sideways.
    """
    cell = marked[y0:y1, x0:x1]
    if cell.size == 0 or y1 - y0 < 2 * BAND_MIN_PX:
        return x0, y0, x1, y1
    blank = cell.sum(axis=1) <= BARE_MAX_PX
    segs, run = [], None
    for i, b in enumerate(list(blank) + [True]):
        if b and run is None:
            run = i
        elif not b and run is not None:
            if i - run >= BAND_MIN_PX:
                segs.append((run, i))
            run = None
    if run is not None and len(blank) + 1 - run >= BAND_MIN_PX:
        segs.append((run, len(blank)))
    if not segs:
        return x0, y0, x1, y1
    # Same rule as cut_at_gutter: an anchor whose centre lands in the gap cannot
    # choose a side, so the larger piece is taken rather than no cut at all.
    mid = (ay0 + ay1) / 2 - y0
    for a, b in segs:
        if a < mid < b:
            mid = a if a > (y1 - y0) - b else b
            break
    lo, hi = 0, y1 - y0
    for a, b in segs:
        if b <= mid:
            lo = max(lo, b)
        elif a >= mid:
            hi = min(hi, a)
    if hi - lo < MIN_H_PX:
        return x0, y0, x1, y1
    return x0, y0 + int(lo), x1, y0 + int(hi)


def band_pieces(marked, x0, y0, x1, y1):
    """Every piece a bare horizontal band separates, top to bottom."""
    cell = marked[y0:y1, x0:x1]
    if cell.size == 0 or y1 - y0 < 2 * BAND_MIN_PX:
        return [(x0, y0, x1, y1)]
    blank = cell.sum(axis=1) <= BARE_MAX_PX
    out, start, run = [], 0, None
    for i, b in enumerate(list(blank) + [False]):
        if b and run is None:
            run = i
        elif not b and run is not None:
            if i - run >= BAND_MIN_PX:
                if run - start >= MIN_H_PX:
                    out.append((x0, y0 + start, x1, y0 + run))
                start = i
            run = None
    if len(blank) - start >= MIN_H_PX:
        out.append((x0, y0 + start, x1, y0 + len(blank)))
    return out or [(x0, y0, x1, y1)]


def gutter_pieces(marked, x0, y0, x1, y1):
    """Every printed object in the box, split at the paper strips between them.

    cut_at_gutter keeps the piece the caption sits under, which is right when
    there IS a caption to choose by.  With none -- two opening photographs
    placed side by side, which the census kept reporting as one crop containing
    two pictures -- choosing means throwing a real figure away.  So an
    uncaptioned box yields all of its pieces and each becomes a figure.
    """
    cell = marked[y0:y1, x0:x1]
    if cell.size == 0 or x1 - x0 < 2 * GUTTER_MIN_PX:
        return [(x0, y0, x1, y1)]
    blank = cell.sum(axis=0) <= BARE_MAX_PX
    out, start = [], 0
    run = None
    for i, b in enumerate(list(blank) + [False]):
        if b and run is None:
            run = i
        elif not b and run is not None:
            if i - run >= GUTTER_MIN_PX:
                if run - start >= MIN_W_PX:
                    out.append((x0 + start, y0, x0 + run, y1))
                start = i
            run = None
    end = len(blank)
    if end - start >= MIN_W_PX:
        out.append((x0 + start, y0, x0 + end, y1))
    return out or [(x0, y0, x1, y1)]


def trim_blank(marked, x0, y0, x1, y1):
    """Shave blank PAPER off the edges, keeping everything that carries marks.

    Blank means bright, not merely low-contrast.  Testing for "no strokes
    relative to the local median" calls a uniformly DARK area blank, because a
    dark region has no contrast against its own median -- and that quietly ate
    a quarter of every dark-bordered picture.  MEASURED on p172's game screen:
    a correct 2158x1473 box came out 1597x1469, losing 561 px of width, which
    is the whole of the "aspect 1.05 where a C 64 screen is 1.6" complaint.
    Every build shared this function, so every build inherited the damage.

    It reads the same "marked" mask as the panel tests, and for the same reason:
    a yellow tint is BRIGHTER than PAPER_LEVEL, so a luminance test called a
    tint panel blank and shaved it off -- which is what silently undid the panel
    growth on p143 until the mask was shared."""
    cell = marked[y0:y1, x0:x1]
    if cell.size == 0:
        return x0, y0, x1, y1
    ink = cell
    st = ink.mean(axis=1)
    colp = ink.mean(axis=0)
    ry = np.where(st > EMPTY_FRAC)[0]
    rx = np.where(colp > EMPTY_FRAC)[0]
    if ry.size:
        y0, y1 = y0 + int(ry[0]), y0 + int(ry[-1]) + 1
    if rx.size:
        x0, x1 = x0 + int(rx[0]), x0 + int(rx[-1]) + 1
    return x0, y0, x1, y1


def overlay(page, figs, im, dest):
    """The page with every detected figure boxed, for a human or a vision pass."""
    small = im.resize((im.size[0] // 5, im.size[1] // 5), Image.LANCZOS)
    d = ImageDraw.Draw(small)
    for i, f in enumerate(figs):
        x0, y0, x1, y1 = (v // 5 for v in f["bbox"])
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=4)
        d.rectangle([x0, y0 - 22, x0 + 96, y0], fill=(255, 0, 0))
        d.text((x0 + 4, y0 - 18), f"{i} {f['type']}", fill=(255, 255, 255))
    small.save(dest)


if __name__ == "__main__":
    DEST = os.path.join(OB.OUT_DIR, "figures")
    os.makedirs(DEST + "/crops", exist_ok=True)
    os.makedirs(DEST + "/overlay", exist_ok=True)
    for a in sys.argv[1:]:
        page = int(a)
        try:
            figs, rec, im = figures(page)
        except Exception as e:
            print(f"p{page:03d}: FAILED {type(e).__name__}: {e}", flush=True)
            continue
        for i, f in enumerate(figs):
            f["crop"].save(f"{DEST}/crops/p{page:03d}-{i}-{f['type']}.png")
        overlay(page, figs, im, f"{DEST}/overlay/p{page:03d}.png")
        json.dump([{k: v for k, v in f.items() if k != "crop"} for f in figs],
                  open(f"{DEST}/p{page:03d}.json", "w"), indent=1)
        print(f"p{page:03d}: {len(figs)} figure(s) "
              f"{[f'{f['w']}x{f['h']}:{f['type']}' for f in figs]}", flush=True)
