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
    on the fold  6 clip holes, 3 vertical pairs, ~0.6 mm dark teardrops

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

import math
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ND

from r005_masters import (
    ISSUE, ISS, MM, SCAN_REDUCE, MASTER_DPI, THUMB_DPI,
    SKEW_RESIDUAL_MAX, CLEAN_PCT,
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
# too, and the paper mask cannot see the fold.  See fold_line().
EDGE_INSET_MM = 0.3          # inside its own line, as the sheet variant

# `tilt` is not called in this file -- nothing here needs the angle, only the
# poly.  It is re-exported so a caller (the geometry printer that lands in a
# later task, and tests/test_r005_spread.py meanwhile) can score any poly this
# module traces via `r005_masters_spread.tilt`, the same as the sheet variant
# calls it on its own traced edges, without a second import of r005_masters.
__all__ = ("parity", "outer_edges", "EDGE_INSET_MM", "find_holes", "fit_fold", "tilt")


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


def measure(page):
    stem = f"{page:03d}"
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    angle, residual, full, img, notes = level_page(page)
    stamp = stamp_text(VARIANT, **{"page": f"{stem} of {ISSUE}",
                                   "phase": "measure",
                                   "skew": f"{angle:+.2f} -> {residual:+.2f} deg",
                                   "notes": "; ".join(notes) or "(none)"})
    grade_page(stem, full, stamp)
    print(f"p{stem}: skew {angle:+.2f} -> {residual:+.2f} deg | grade {GRADE_SHA}"
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
        raise SystemExit("cut: not built yet")   # replaced in Task 9
