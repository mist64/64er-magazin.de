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
    SKEW_RESIDUAL_MAX, CLEAN_PCT,
    DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP,
    ANCHORS, LEVELS, HAVE_PROFILE, GRADE_SHA,
    PageFailed, measure_skew,
    separate_and_render, archive_cmyk, save_master, write_profile, stamp_text,
    paper_mask, boundaries, trace, tilt,
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
# The INNER side is NOT traced here.  The neighbour half of the sheet is paper
# too, and the paper mask cannot see the fold.  See fit_fold() (the clip
# holes) and neighbour_boundary() (the fallback).
EDGE_INSET_MM = 0.3          # inside its own line, as the sheet variant


def outer_edges(rgb, par):
    """dict(top, bot, outer): straight lines in 600 dpi sheet pixels.

    top/bot are y(x); outer is x(y).  Parity says which side is outer: an even
    page's neighbour is on the right, so its outer edge is the LEFT one.
    """
    rows, starts, ends, cols, tops, bots = boundaries(paper_mask(rgb))
    return {"top": trace(tops, cols, CLEAN_PCT, MM),
            "bot": trace(bots, cols, CLEAN_PCT, MM),
            "outer": trace(starts if par == "even" else ends, rows, CLEAN_PCT, MM)}


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
HOLE_ASPECT_MAX = 4.5        # long/short: measured <= 3.72; a clipped rule 5.2+
# The line through them: at least this many holes, within this of the line,
# spanning this fraction of the page height, and near-vertical.  Six holes on a
# rigid clip give a line to a fraction of a millimetre; three do not tell a
# column of bullets from a clip.
FOLD_TOL_MM = 0.5
FOLD_MIN_HOLES = 4
FOLD_MIN_SPAN = 0.5
FOLD_TILT_MAX = 1.0          # deg


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


def fit_fold(holes, h):
    """The line most holes agree on, or None.

    Every pair of holes proposes a line x = a*y + b; the proposal with the most
    holes within FOLD_TOL_MM wins, ties broken by residual; the winner is
    refitted by least squares over its inliers.  A proposal steeper than
    FOLD_TILT_MAX or whose inliers span less than FOLD_MIN_SPAN of the height
    is not a fold: a clip is rigid and the sheet is levelled.
    """
    if len(holes) < FOLD_MIN_HOLES:
        return None
    pts = np.array([(cx, cy) for cx, cy, _ in holes])
    best = None
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
            span = (pts[inl, 1].max() - pts[inl, 1].min()) / h
            if span < FOLD_MIN_SPAN:
                continue
            key = (n, -float(res[inl].mean()))
            if best is None or key > best[0]:
                best = (key, inl)
    if best is None:
        return None
    inl = best[1]
    poly = np.polyfit(pts[inl, 1], pts[inl, 0], 1)          # x = f(y)
    res = np.abs(pts[inl, 0] - np.polyval(poly, pts[inl, 1]))
    return {"poly": poly, "n": int(inl.sum()),
            "residual_mm": float(res.mean() / MM),
            "span": float((pts[inl, 1].max() - pts[inl, 1].min()) / h)}


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
    holes = find_holes(gray, par)
    fold = fit_fold(holes, h)
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
                     "top-trim y instead")
    return {
        "page": page, "parity": par, "sheet_px": [w, h],
        "skew": {"angle": angle, "residual": residual},
        "edges": {k: [float(v) for v in p] for k, p in edges.items()},
        "fold": {"source": source,
                 "poly": None if fold is None else [float(v) for v in fold["poly"]],
                 "n": 0 if fold is None else fold["n"],
                 "residual_mm": None if fold is None else fold["residual_mm"],
                 "tilt_deg": None if fold is None else tilt(fold["poly"])},
        "holes": [[float(a), float(b), float(c)] for a, b, c in holes],
        "anchor": None if logo is None else {"source": "logo", **logo},
        "notes": notes,
    }


# --- the debug overlay -----------------------------------------------------
# Edges green (the sheet variant's colour), fold magenta, holes circled in
# the same magenta, the wordmark's box blue.  The lines and circles are drawn
# at 600 dpi and reduced with the page; the text is drawn AFTER the reduction,
# because PIL's default font is ~11 px and would be 2 px tall otherwise.  A
# hole is ~0.7 mm = 16 px, and after the 5:1 reduction a 16 px circle would be
# an invisible 3 px ring, so the ring is drawn wide enough to survive it.
DEBUG_FOLD = (230, 0, 200)
DEBUG_LOGO = (0, 120, 255)
DEBUG_HOLE_RING_PX = 12 * DEBUG_REDUCE       # radius at 600 dpi; 12 px after


def draw_debug(img, geom, dest):
    """Edges green, fold magenta, holes circled, logo box blue, notes as text."""
    w, h = img.size
    overlay = img.copy()
    d = ImageDraw.Draw(overlay)
    for key in ("top", "bot"):
        p = geom["edges"][key]
        d.line([(x, np.polyval(p, x)) for x in range(0, w, DEBUG_STEP)],
               fill=DEBUG_COLOR, width=DEBUG_WIDTH)
    p = geom["edges"]["outer"]
    d.line([(np.polyval(p, y), y) for y in range(0, h, DEBUG_STEP)],
           fill=DEBUG_COLOR, width=DEBUG_WIDTH)
    if geom["fold"]["poly"]:
        p = geom["fold"]["poly"]
        d.line([(np.polyval(p, y), y) for y in range(0, h, DEBUG_STEP)],
               fill=DEBUG_FOLD, width=DEBUG_WIDTH)
    for cx, cy, dm in geom["holes"]:
        r = max(dm * MM, DEBUG_HOLE_RING_PX)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=DEBUG_FOLD, width=DEBUG_WIDTH)
    if geom["anchor"]:
        d.rectangle(geom["anchor"]["bbox"], outline=DEBUG_LOGO, width=DEBUG_WIDTH)
    small = overlay.resize((w // DEBUG_REDUCE, h // DEBUG_REDUCE), Image.LANCZOS)
    text = [f"p{geom['page']:03d} {geom['parity']}  fold:{geom['fold']['source']} "
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
          + (f" x={np.polyval(f['poly'], rgb.shape[0] / 2):.0f} tilt {f['tilt_deg']:+.2f}" if f["poly"] else "")
          + f" | logo {'%.2f' % anchor['score'] if anchor else 'none'}"
          + f" | grade {GRADE_SHA}"
          + "".join(f"\n      NOTE p{stem}: {n}" for n in notes), flush=True)


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
        raise SystemExit("cut: not built yet")   # the cut phase is a later task
