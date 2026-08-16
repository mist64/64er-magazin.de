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
# Screened-and-uniform is a tint, screened-and-varying is a picture.
TONE_CELLS = 12         # coarse grid the halftone is averaged away over
TONE_MIN_STD = 11.0     # coarse tone flatter than this is a flat fill
ENCLOSED_MIN_WORDS = 12 # a text block this big inside a region makes it text
ENCLOSED_COVER = 0.60   # ...when this much of that block falls inside
GROW_PX = 24            # step by which a scrap hull grows toward the text
GROW_STEPS = 60
JOIN_PX = 90            # two regions this close, with nothing between, are one
FRAME_SEARCH_PX = 90    # how far outside a candidate to look for its printed rule
FRAME_SPAN = 0.92       # a row/column this dark across the CANDIDATE is a rule
CAPTION_GAP_PX = 10     # keep this clear of a caption's first row
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
            # Three sides make a frame.  Requiring all four loses every figure
            # whose fourth rule is broken, hidden under a caption, or simply not
            # printed -- and a figure bounded on three sides is already located.
            left = any(abs(c - x0) <= 3 and r0 <= ya + 3 and r1 >= yb - 3 for c, r0, r1 in v)
            right = any(abs(c - x1) <= 3 and r0 <= ya + 3 and r1 >= yb - 3 for c, r0, r1 in v)
            if left or right:
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
        if b["label"] != "caption":
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
    """One of the four types tools/convert-scans.sh knows."""
    a = np.asarray(crop).astype(np.int16)
    sat = float((a.max(axis=2) - a.min(axis=2)).mean())
    if sat > 18:
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


def figures(page):
    lab = os.path.join(OB.OUT_DIR, f"{page:03d}.labels.json")
    src = lab if os.path.exists(lab) else os.path.join(OB.OUT_DIR, f"{page:03d}.json")
    rec = json.load(open(src, encoding="utf-8"))
    im = Image.open(os.path.join(OB.SRC_DIR, f"{page:03d}.png")).convert("RGB")
    W, H = im.size
    grey = np.asarray(im.convert("L"))

    if rec.get("page_kind") in SKIP_PAGE_KINDS:
        return [], rec, im
    blocks = [b for b in rec["blocks"] if b["label"] != "noise"]
    rects = [([v * SCALE for v in b["bbox"]], b["label"]) for b in blocks]
    rects.sort(key=lambda r: (r[0][0], r[0][1]))

    cols = []
    for r in rects:
        for c in cols:
            cx0 = min(q[0][0] for q in c); cx1 = max(q[0][2] for q in c)
            ov = min(cx1, r[0][2]) - max(cx0, r[0][0])
            if ov > COL_OVERLAP * min(cx1 - cx0, r[0][2] - r[0][0]):
                c.append(r); break
        else:
            cols.append([r])

    found = []
    for fx0, fy0, fx1, fy1 in framed_rects(grey, W, H):
        if fx1 - fx0 < MIN_W_PX or fy1 - fy0 < MIN_H_PX:
            continue
        if encloses_text(rec, fx0, fy0, fx1, fy1):
            continue
        found.append({"bbox": [fx0 + BORDER_OVERCUT, fy0 + BORDER_OVERCUT,
                               fx1 - BORDER_OVERCUT, fy1 - BORDER_OVERCUT],
                      "ink": 0.0, "col": (fx0, fx1), "framed": True,
                      "line_structure": bool(looks_like_text(grey, fx0, fy0, fx1, fy1)),
                      "flat_tone": bool(uniform_tint(grey, fx0, fy0, fx1, fy1))})

    # The candidate gaps in a column are not only the ones BETWEEN two text
    # blocks: p8's portrait sits above the first block in its column, so no
    # pair brackets it.  Bracket each column with the page's own margins.
    top = MARGIN_PX
    bot = H - MARGIN_PX
    for c in cols:
        c.sort(key=lambda r: r[0][1])
        cx0, cx1 = min(q[0][0] for q in c), max(q[0][2] for q in c)
        edge_a = ([cx0, top - MIN_GAP_PX - PAD, cx1, top], c[0][1])
        edge_b = ([cx0, bot, cx1, bot + MIN_GAP_PX + PAD], c[-1][1])
        for (a, la), (b, lb) in zip([edge_a] + c, c + [edge_b]):
            if la not in ARTICLE_NEIGHBOURS and lb not in ARTICLE_NEIGHBOURS:
                continue                       # an ad's own artwork
            gy0, gy1 = a[3] + PAD, b[1] - PAD
            if gy1 - gy0 < MIN_GAP_PX:
                continue
            cell = grey[int(gy0):int(gy1), int(cx0):int(cx1)]
            if cell.size == 0:
                continue
            ink = float((cell < INK_LEVEL).mean())
            if ink < MIN_INK:
                continue
            # THE GAP IS THE FIGURE.  Do not tighten to the ink: a picture is
            # dark in places and light in others, so bounding it by ink cuts
            # off every pale part and splits anything with two dark clusters.
            # Three vision passes over 46 pages said the same sentence -- "the
            # detector finds ink, not figures" -- and every CLIPPED and SPLIT
            # they found is that one mistake.  A flowchart is the pure case:
            # only its grey nodes are inked, so ink-bounding returns the nodes
            # and loses the diagram.
            #
            # The magazine sets a picture in a column-width slot between two
            # pieces of text.  That slot is the answer.  Only genuinely EMPTY
            # margin comes off.
            sx0, sy0 = int(cx0), int(gy0)
            st = strokes(grey, sx0, sy0, int(cx1), int(gy1))
            cols_p = (grey[sy0:int(gy1), sx0:int(cx1)].astype(np.int16)
                      < np.median(grey[sy0:int(gy1), sx0:int(cx1)]) - STROKE_CONTRAST).mean(axis=0)
            def edges(profile):
                nz = np.where(profile > EMPTY_FRAC)[0]
                return (int(nz[0]), int(nz[-1]) + 1) if nz.size else None
            ey, ex = edges(st), edges(cols_p)
            if not ey or not ex:
                continue
            x0 = sx0 + ex[0]; x1 = sx0 + ex[1]
            y0 = sy0 + ey[0]; y1 = sy0 + ey[1]
            x0, y0, x1, y1 = cut_inside_rule(grey, x0, y0, x1, y1)
            if x1 - x0 < MIN_W_PX or y1 - y0 < MIN_H_PX:
                continue
            if max(x1 - x0, y1 - y0) > MAX_ASPECT * min(x1 - x0, y1 - y0):
                continue
            # encloses_text is a REJECT: a region swallowing a labelled
            # paragraph is that paragraph.  looks_like_text and uniform_tint
            # are only EVIDENCE -- half the figures in this magazine are
            # pictures OF text (screenshots, hardcopies, character sets,
            # flowcharts), and rejecting on line structure threw away p29's
            # Newsroom printout, p32's flowchart and all four of p40's
            # screenshots along with the data tables.  That is the question
            # FINDINGS says no low-level statistic answers; step 020 reads the
            # page and answers it.
            if encloses_text(rec, x0, y0, x1, y1):
                continue
            found.append({"bbox": [x0, y0, x1, y1], "ink": round(ink, 3),
                          "col": (int(cx0), int(cx1)),
                          "line_structure": bool(looks_like_text(grey, x0, y0, x1, y1)),
                          "flat_tone": bool(uniform_tint(grey, x0, y0, x1, y1))})

    # A "noise" block is one scrap of garbage the OCR read off a picture, and a
    # picture yields several -- p12's book cover produced three, p27's cards
    # seven.  One box each shatters the figure; dropping them loses it entirely,
    # because a picture whose neighbouring text sits in different columns is
    # bracketed by no gap at all.  So CLUSTER them: scraps close together are
    # one picture, and the cluster's hull is its rectangle.
    scraps = []
    for bb in rec["blocks"]:
        if bb["label"] != "noise":
            continue
        x0, y0, x1, y1 = (int(v * SCALE) for v in bb["bbox"])
        scraps.append([x0, y0, x1, y1])
    def text_between(a, b):
        """Is there real typesetting between these two rectangles?"""
        ux0, uy0 = min(a[0], b[0]), min(a[1], b[1])
        ux1, uy1 = max(a[2], b[2]), max(a[3], b[3])
        for bb in rec["blocks"]:
            if bb["label"] not in ARTICLE_NEIGHBOURS or bb.get("n_words", 0) < 3:
                continue
            tx0, ty0, tx1, ty1 = (v * SCALE for v in bb["bbox"])
            if (min(ux1, tx1) - max(ux0, tx0) > 0.5 * (tx1 - tx0)
                    and min(uy1, ty1) - max(uy0, ty0) > 0.5 * (ty1 - ty0)):
                return True
        return False

    merged_scraps = []
    for sc in sorted(scraps, key=lambda r: (r[1], r[0])):
        for m in merged_scraps:
            # Close together AND with nothing printed between them.  Without the
            # second half a caption between two hardcopies is swallowed and the
            # pair becomes one figure (p28); with only the first half a wide
            # flowchart stays in column-slices (p31).
            if (min(m[2], sc[2]) - max(m[0], sc[0]) > -SCRAP_JOIN_PX
                    and min(m[3], sc[3]) - max(m[1], sc[1]) > -SCRAP_JOIN_PX
                    and not text_between(m, sc)):
                m[0] = min(m[0], sc[0]); m[1] = min(m[1], sc[1])
                m[2] = max(m[2], sc[2]); m[3] = max(m[3], sc[3])
                break
        else:
            merged_scraps.append(list(sc))

    article_ys = [(bb["bbox"][1] * SCALE, bb["bbox"][3] * SCALE)
                  for bb in rec["blocks"] if bb["label"] in ARTICLE_NEIGHBOURS]
    for x0, y0, x1, y1 in merged_scraps:
        # NO size test yet.  A scrap MARKS a picture; it is not its size.  The
        # recurring "64'er Test" rubric badge comes back as a 162x88 scrap
        # reading 'Tes', so filtering before the growth step threw the badge
        # away on every page that carries one -- the single most repeated miss
        # in the vision reports.
        if not any(abs(ay0 - y1) < 1200 or abs(y0 - ay1) < 1200 for ay0, ay1 in article_ys):
            continue
        if any(min(g["bbox"][2], x1) - max(g["bbox"][0], x0) > 0
               and min(g["bbox"][3], y1) - max(g["bbox"][1], y0) > 0 for g in found):
            continue
        x0, y0, x1, y1 = grow_to_text(rects, grey, x0, y0, x1, y1, W, H)
        if x1 - x0 < MIN_W_PX or y1 - y0 < MIN_H_PX:
            continue
        # The scrap path needs EVERY gate the gap path has.  Skipping the text
        # test here is what let p22's "Datenblatt" through: a data table on a
        # tint OCRs so badly that all 19 of its blocks come back labelled
        # "noise", so it arrives as a cluster of scraps -- and the stroke test
        # calls it text correctly the moment it is asked.
        if max(x1 - x0, y1 - y0) > MAX_ASPECT * min(x1 - x0, y1 - y0):
            continue
        if encloses_text(rec, x0, y0, x1, y1):
            continue
        found.append({"bbox": [x0, y0, x1, y1], "ink": 0.0, "col": (x0, x1),
                      "line_structure": bool(looks_like_text(grey, x0, y0, x1, y1)),
                      "flat_tone": bool(uniform_tint(grey, x0, y0, x1, y1))})

    # a picture split by text printed inside it is one picture
    found.sort(key=lambda f: (f["col"], f["bbox"][1]))
    merged = []
    for f in found:
        if merged:
            g = merged[-1]
            same_col = g["col"] == f["col"]
            near = f["bbox"][1] - g["bbox"][3] < MERGE_GAP_PX
            overlap = (min(g["bbox"][2], f["bbox"][2]) - max(g["bbox"][0], f["bbox"][0])) > 0
            if same_col and near and overlap:
                g["bbox"] = [min(g["bbox"][0], f["bbox"][0]), min(g["bbox"][1], f["bbox"][1]),
                             max(g["bbox"][2], f["bbox"][2]), max(g["bbox"][3], f["bbox"][3])]
                continue
        merged.append(f)

    # One last pass over EVERYTHING, gaps and scrap clusters alike: two regions
    # that touch with nothing printed between them are one figure.  p31's
    # printer-selection flowchart arrived as four vertical column slices, and
    # the judge downstream can only accept or reject a rectangle -- it cannot
    # merge two, so the geometry has to.
    changed = True
    while changed:
        changed = False
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                a, b = merged[i]["bbox"], merged[j]["bbox"]
                gap_x = max(a[0], b[0]) - min(a[2], b[2])
                gap_y = max(a[1], b[1]) - min(a[3], b[3])
                if gap_x > JOIN_PX or gap_y > JOIN_PX:
                    continue
                if text_between(a, b):
                    continue
                merged[i]["bbox"] = [min(a[0], b[0]), min(a[1], b[1]),
                                     max(a[2], b[2]), max(a[3], b[3])]
                merged.pop(j)
                changed = True
                break
            if changed:
                break

    out = []
    for f in sorted(merged, key=lambda f: (f["bbox"][1], f["bbox"][0])):
        x0, y0, x1, y1 = f["bbox"]
        crop = im.crop((x0, y0, x1, y1))
        out.append({"bbox": [x0, y0, x1, y1], "w": x1 - x0, "h": y1 - y0,
                    "ink": f["ink"], "type": classify(crop),
                    "line_structure": f.get("line_structure", False),
                    "flat_tone": f.get("flat_tone", False), "crop": crop})
    return out, rec, im


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
