# crop — A4 window, anchored on the logo

Cut every page to exactly **210 × 297 mm** (4961 × 7016 px @600 dpi) so the same content lands in
the same place on every page, and the later stages need no per-page geometry.

## Why the logo is the anchor

The "64'er" wordmark is print-registered to the page CONTENT. The sheet edge is not: print-to-cut
registration varies, so anchoring on the paper edge would align the paper and misalign the type.
The wordmark is the same glyph on every page (not mirrored between parities), sits in the outer
bottom corner, and is found on 129/176 pages at confidence p50 0.95 with parity correct on all
129.

    logo_detect.py     template match -> tmp/logo_positions.json  (129/176)

**Frame caution:** `logo_detect.py` reports coordinates in the RAW thumb frame, although its
docstring claims the deskewed one. Everything downstream transforms the anchor through the same
rotation `stack_render.py` used; that transform is verified by landing it on the glyph, not by
trusting PIL's sign convention.

**Footgun:** running `logo_detect.py` with a page subset REWRITES `logo_positions.json` with only
those pages. Back it up first.

## How much page is there around the anchor

`logo_clearance.py` measures the distance from the anchor to the alpha, in each direction, three
ways — they answer different questions and they disagree:

    RAY   along the anchor's own row/column to the first transparent pixel.
          One clip hole on that row truncates it, so it UNDERSTATES the usable area.
    RECT  largest alpha-free rectangle around the anchor (water-filled -- max-AREA is ill-posed
          and O(H^2)). Honest answer to "what fits with zero alpha", but dominated by the CLIP
          HOLES, which are alpha inside the page: it falls >500px short of BAND on 48 pages
          upward and 27 leftward.
    BAND  distance at which alpha coverage across the box exceeds 1%. Robust, and matches how a
          crop actually fails: a sliver in a corner is inpaintable, a full band is not.

BAND's perpendicular extent must be the CURRENT BOX, not the canvas: measured across the whole
canvas every column already contains the top bed cut and the bottom insert cut (~2.5% of its
rows), so every column exceeds any sane threshold and the measure collapses to 0 everywhere. It
is iterated from the RAY box instead.

Median clearance (px @600dpi / mm), BAND:

    parity   left            right           top             bottom
    even     567 / 24.0      4376 / 185.2    6877 / 291.1    102 / 4.3
    odd      4374 / 185.2    512 / 21.7      6877 / 291.1     94 / 4.0

The logo sits ~22 mm from the outer edge and only **~4 mm above the bottom alpha** — the bottom is
by far the binding constraint.

## The window does not fit without alpha

    available extent vs A4, median deficit (BAND):  even 23px wide / 36px tall
                                                    odd  81px wide / 38px tall

**A4 fits alpha-free on 0 of 129 pages.** The page simply is not 210 × 297 mm of known pixels once
bed, neighbour, clip holes and the deskew wedge are removed. So the objective is not "avoid alpha"
but "minimise it", and inpainting is structural rather than optional. The deficit is small and
consistent (1–3 mm), i.e. a thin border, not a chunk.

## Fitting and applying

`fit_window.py` searches ONE rigid (S, B) offset pair per parity — S = anchor's distance from the
window's left edge, B = from its top edge — minimising alpha inside the window over the pages that
have their own logo:

    even  S= 568  B=6892   mean alpha in window 1.27%  (p50 1.38, p95 2.30)
    odd   S=4416  B=6900   mean alpha in window 1.90%  (p50 1.92, p95 2.99)

S must span the full page width: on odd pages the anchor is near the RIGHT edge (S≈4416), and a
range capped at 900 pinned the optimum to its own boundary and reported 71% alpha — a window
mostly off the page.

The 47 pages with no detected logo are excluded from the FIT (an interpolated anchor would drag
the optimum toward its own error) but do get a window afterwards, from an anchor interpolated
across same-parity neighbours, marked `src: interpolated`.

    fit_window.py      -> tmp/crop_windows_v2.json   (offsets + per-page window)
    viz_window.py      -> tmp/crop_preview/NNN.png   window drawn on the render, full 600dpi
                          green = own logo, orange = interpolated anchor, magenta = the anchor
    crop_a4.py         -> tmp/a4/NNN.png             the crop applied, every page exactly A4
    viz_clearance.py   -> tmp/clearance/NNN.png      the three clearance boxes drawn

Where the window overhangs the rendered canvas, `crop_a4.py` leaves the output TRANSPARENT rather
than clamping the window: clamping would silently shift the content and destroy the one property
the logo anchor exists to provide.

## Files

    logo_detect.py     wordmark template match (raw frame)
    logo_clearance.py  three clearance measures -> tmp/logo_clearance.json
    fit_window.py      per-parity A4 offsets -> tmp/crop_windows_v2.json
    crop_a4.py         apply the window -> tmp/a4/
    viz_clearance.py   / viz_window.py    overlays

    crop_fit.py        SUPERSEDED by fit_window.py  (and its tmp/crop_windows.json predates both
                       the matte and the spine rewrite -- do not quote its coverage numbers)
    viz_crop.py        SUPERSEDED by viz_window.py
