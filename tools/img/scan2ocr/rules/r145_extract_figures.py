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
MARGIN_PX = 260         # page edge; a column's free space starts here
# A box's own rule is one long thin region -- p8's editorial border came out
# 564x5724.  No printed picture in this magazine is anywhere near that thin.
MAX_ASPECT = 6.0
SCRAP_JOIN_PX = 260     # OCR scraps this close belong to one picture
# Conversion type, measured over the INK rather than the paper.  Paper is most
# of a framed figure and paper is neutral, so averaging the whole rectangle
# drags every reading toward grey.
PAPER_LEVEL = 215       # above this luminance is paper, not print
INK_MIN_PX = 400        # too little ink to measure: fall back to a loose mask
SAT_COLOUR = 18         # mean chroma of the INK above this -> colour
SAT_STRONG = 60         # a pixel this chromatic is unambiguously coloured
SAT_STRONG_FRAC = 0.06  # ...and this share of the ink being so makes it colour

# Screened-and-uniform is a tint, screened-and-varying is a picture.
TONE_CELLS = 12         # coarse grid the halftone is averaged away over
TONE_MIN_STD = 11.0     # coarse tone flatter than this is a flat fill
ENCLOSED_MIN_WORDS = 12 # a text block this big inside a region makes it text
ENCLOSED_COVER = 0.60   # ...when this much of that block falls inside
GROW_PX = 24            # step by which a scrap hull grows toward the text
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
TOP_STOP_MIN_WORDS = 4        # fewer words than this may be lettering inside the figure
FRAME_CLUSTER_PX = 300        # frames this close are one figure built of boxes
# Asymmetric on purpose -- see the merge in illustrations().
ILLUS_JOIN_X = 300            # wide enough to cross a column gutter
ILLUS_JOIN_Y = 20             # narrow: only touching fragments, never past a caption
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


def snap_to_frame(grey, x0, y0, x1, y1, W, H):
    """Snap to the picture's own printed rule, when it has one.

    Nearly every placed figure in this magazine sits inside a printed rule.
    That rule is the object's real edge, and it is a far better boundary than
    anything grown from ink: growth runs on where the ink stays dense (across
    gutters, into captions) and dies where the picture goes sparse (the pale
    half of a schematic, the head of a cartoon).  A rule does neither -- it is
    exactly where the figure ends.

    Searched only in a band around the candidate, and only accepted when a rule
    is found on OPPOSITE sides: one long dark run is a paragraph underline or a
    column rule, two facing each other is a frame.
    """
    sx0, sy0 = max(0, x0 - FRAME_SEARCH_PX), max(0, y0 - FRAME_SEARCH_PX)
    sx1, sy1 = min(W, x1 + FRAME_SEARCH_PX), min(H, y1 + FRAME_SEARCH_PX)
    win = grey[sy0:sy1, sx0:sx1]
    if win.size == 0:
        return x0, y0, x1, y1
    # Measure a rule across the CANDIDATE's own extent, not the search window's.
    # The window is deliberately wider than the figure, so a frame line spans
    # only part of it and never reached FRAME_SPAN -- which is why snapping
    # almost never fired and 61% of crops were still cut or over-grown.
    dark = win < BORDER_DARK
    rows = dark[:, x0 - sx0:x1 - sx0].mean(axis=1)
    cols = dark[y0 - sy0:y1 - sy0, :].mean(axis=0)

    def pick(profile, lo, hi):
        """Outermost run that spans the window, one before `lo`, one after `hi`."""
        idx = [i for i, v in enumerate(profile) if v >= FRAME_SPAN]
        before = [i for i in idx if i <= lo]
        after = [i for i in idx if i >= hi]
        return (max(before) if before else None, min(after) if after else None)

    t, b = pick(rows, y0 - sy0, y1 - sy0)
    l, r = pick(cols, x0 - sx0, x1 - sx0)
    if t is not None and b is not None:
        y0, y1 = sy0 + t + BORDER_OVERCUT, sy0 + b - BORDER_OVERCUT
    if l is not None and r is not None:
        x0, x1 = sx0 + l + BORDER_OVERCUT, sx0 + r - BORDER_OVERCUT
    return x0, y0, x1, y1


def cut_inside_rule(grey, x0, y0, x1, y1):
    def band(profile):
        first = None
        for i, v in enumerate(profile[:BORDER_MAX_PX]):
            if v >= BORDER_FRAC:
                if first is None:
                    first = i
            elif first is not None:
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
    med = np.median(np.stack([np.roll(np.roll(gg, dy, 0), dx, 1)
                              for dy in (-1, 0, 1) for dx in (-1, 0, 1)]), axis=0)
    screen = float(np.abs(med - gg).mean() / 255)
    mid = gg[(gg > 40) & (gg < 215)]
    levels = len(np.unique(mid // 4)) if mid.size else 0
    if screen > 0.055:
        return "dots"
    if levels > 26 and mid.size > 0.15 * gg.size:
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
    top = MARGIN_PX
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

    for (rx0, ry0, rx1, ry1), _lab in rects:
        if ry1 >= bottom:
            continue                            # not above the caption
        overlap = min(cx1, rx1) - max(cx0, rx0)
        if overlap < CAPTION_MEASURE_MATCH * min(cx1 - cx0, rx1 - rx0):
            continue                            # not above this figure at all
        top = max(top, int(ry1) + CAPTION_GAP_PX)
    # A figure is not most of the page.  Where nothing is printed above the
    # caption -- it opens the column -- the top would otherwise fall back to the
    # page margin and take everything with it (p24 came out 4346x5684).
    if bottom - top > MAX_FIGURE_FRAC * H:
        top = int(bottom - MAX_FIGURE_FRAC * H)
    return [cx0, top, cx1, bottom]


def illustrations(rec):
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

    merged = []
    for r in sorted(raw, key=lambda r: (r[1], r[0])):
        for m in merged:
            if (min(m[2], r[2]) - max(m[0], r[0]) > -ILLUS_JOIN_X
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
    if rec.get("page_kind") in SKIP_PAGE_KINDS:
        return [], rec, im

    blocks = [b for b in rec["blocks"] if b["label"] != "noise"]
    rects = [([v * SCALE for v in b["bbox"]], b["label"]) for b in blocks]
    stoppers = [(bb, lab) for (bb, lab), b in zip(rects, blocks)
                if b.get("n_words", 0) >= TOP_STOP_MIN_WORDS]

    illus = illustrations(rec)
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
        band_top = cy0 - int(MAX_FIGURE_FRAC * H)
        mine = [i for i, r in enumerate(illus)
                if i not in claimed and r[3] <= cy0 + CAPTION_GAP_PX and r[3] >= band_top
                and min(cx1, r[2]) - max(cx0, r[0]) > CAPTION_MEASURE_MATCH * min(cx1 - cx0, r[2] - r[0])]
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
        else:
            box = figure_above(stoppers, cap, W, H)   # no illustration: fall back
        found.append({"bbox": box, "ink": 0.0, "caption": cap["text"],
                      "kind": cap["kind"], "num": cap["num"]})

    # --- An illustration no caption claims is an opener, a cover or a badge.
    leftover = [r for i, r in enumerate(illus) if i not in claimed]
    clustered = []
    for r in sorted(leftover, key=lambda r: (r[1], r[0])):
        for c in clustered:
            if (min(c[2], r[2]) - max(c[0], r[0]) > -FRAME_CLUSTER_PX
                    and min(c[3], r[3]) - max(c[1], r[1]) > -FRAME_CLUSTER_PX):
                c[0], c[1] = min(c[0], r[0]), min(c[1], r[1])
                c[2], c[3] = max(c[2], r[2]), max(c[3], r[3])
                break
        else:
            clustered.append(list(r))
    for x0, y0, x1, y1 in clustered:
        if encloses_text(rec, x0, y0, x1, y1):
            continue
        found.append({"bbox": [x0, y0, x1, y1], "ink": 0.0,
                      "caption": None, "kind": None, "num": "0"})

    out = []
    for f in sorted(found, key=lambda f: (f["bbox"][1], f["bbox"][0])):
        x0, y0, x1, y1 = f["bbox"]
        x0, y0, x1, y1 = trim_blank(grey, x0, y0, x1, y1)
        x0, y0, x1, y1 = cut_inside_rule(grey, x0, y0, x1, y1)
        if x1 - x0 < MIN_W_PX or y1 - y0 < MIN_H_PX:
            continue
        crop = im.crop((x0, y0, x1, y1))
        out.append({"bbox": [x0, y0, x1, y1], "w": x1 - x0, "h": y1 - y0,
                    "ink": f["ink"], "type": classify(crop),
                    "caption": f.get("caption"), "kind": f.get("kind"),
                    "num": f.get("num"), "crop": crop})
    return out, rec, im


def trim_blank(grey, x0, y0, x1, y1):
    """Shave blank PAPER off the edges, keeping everything that carries marks.

    Blank means bright, not merely low-contrast.  Testing for "no strokes
    relative to the local median" calls a uniformly DARK area blank, because a
    dark region has no contrast against its own median -- and that quietly ate
    a quarter of every dark-bordered picture.  MEASURED on p172's game screen:
    a correct 2158x1473 box came out 1597x1469, losing 561 px of width, which
    is the whole of the "aspect 1.05 where a C 64 screen is 1.6" complaint.
    Every build shared this function, so every build inherited the damage."""
    cell = grey[y0:y1, x0:x1].astype(np.int16)
    if cell.size == 0:
        return x0, y0, x1, y1
    ink = cell < PAPER_LEVEL
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
