# matte — page isolation (alpha matting)

Find each page's **paper boundary** and mark everything outside it as **unknown (alpha 0)**: the
scanner bed (lid / backing sheet / its shadow), the coloured cardboard insert, and the sheet-edge
shadow between them. The neighbour strip and the clip holes are cut by `../02b-opposite-page/`
and composited alongside this in `../stack_render.py`.

Principle: keep every genuine page pixel (incl. outer excess); fabricate nothing. Unknown pixels
stay transparent until an explicit later fill step. The matte is built in the RAW scan frame and
rotated afterwards, so pre-existing and rotation-added wedges are both alpha 0.

Conventions: measurements are resolution-relative (1px @600dpi == 4px @2400dpi, same mm).

The spec is `ACCEPTANCE.md` (still current). Rules, in priority order:

1. every backing pixel must be cut — leaving a stripe is a FAIL
2. subject to that, cut as few of OUR pixels as possible

The order matters and the code reflects it: the evidence bar scales with what a cut COSTS, so a
4 px line enclosing nothing but backing is allowed on weaker evidence than a deep one.

CONSTRAINT (why "dark = bed" is not enough): full-bleed dark pages (e.g. p047 Star NG-10 ad) have
real black ink to every edge — the detector must locate the true PAPER EDGE, not border-connected
dark.

## Nothing about the backing is hardcoded

`calibrate_backing.py` measures what the backing IS, over the whole issue:

> backing = the material that covers the border ring and VANISHES inboard

That one test finds the bed on top/left/right, the yellow insert on the bottom of **176/176**
pages, and correctly refuses the cream paper everywhere. It replaced `BED_LUMA`, `BED_SAT`,
`INSERT_LUMA`, `INSERT_SAT` and `INSERT_EDGES` — the same facts guessed instead of measured, each
wrong somewhere (p044's ochre ad matched "yellowish" on a left edge that has no insert on it;
p001's teal cover nearly did too). Point it at another issue and it recalibrates.

    ./calibrate_backing.py <thumbs>/*.png --jobs 4 -o backing_profile.json

## The measurement that made it work: chroma, not luma

Bed and the sheet-edge shadow are one material family; page ink is not. No single RGB distance
can say that. Measured against each page's own bed:

    band                      dLuma   dChroma(normalised)
    sheet-edge shadow p015     36.6      1.9     -> must CUT
    sheet-edge shadow p047     33.3      4.6     -> must CUT
    insert, lit -> shadowed     ~8       0.9     -> must CUT
    ad ink p069                32.9     12.7     -> must KEEP
    comic ink p005             41.5     18.6     -> must KEEP
    ochre ad p044              51.0    127.3     -> must KEEP

Luma cannot separate those at all (33–51 either way); chroma separates them cleanly. So the
tolerances are two measured radii — **loose in luma, tight in chroma** — and chroma is compared as
a RATIO to luma (`CHROMA_STAB`), because a saturated material darkens INTO shadow: an absolute
chroma bound dropped the shaded insert and the bottom boundary "wobbled" ±45 px, which was never
real waviness (the scan shows a straight edge there).

## Pipeline inside bed_matte.py

1. **What is backing HERE** (`page_materials`) — refine the issue profile on this page's border
   ring, grow it through connected pixels to the material's real extent, keep the widest version
   that still STOPS at the sheet edge (judged per scanline, on most lines).
2. **Per-line candidates** (`candidates`) — depths where that material ends, as boundaries between
   two SUSTAINED runs rather than pixel flips (cardboard grain otherwise scatters them).
3. **Robust line fit** (`../linefit.py`) — the (offset, slope) most lines agree on, LSQ on the
   inliers, bounded quadratic for the sheet's bow. A vetoed line means "not that one", never "cut
   nothing".
4. **Finish the boundary** — walk past the fitted line through neutral shadow only, uniformly at a
   robust percentile, counting only scanlines where the walk TERMINATED (a shadow stripe ends; an
   ad just exhausts the budget).
5. **Decide** — `CUT` / `CLEAN(no backing)` / `MIXED(not backing)` / `LOW(no line)` /
   `INK(screened)` / `OVERRUN(past material)`.

## Current result (issue 8609, 600 dpi)

    top     176/176 cut (13-29px)      bottom  176/176 cut (140-159px)
    left    120 correctly clean        right   116 correctly clean

The independent audit went from 164 flagged page-edges to 11, and the largest remaining ones are
its own false positives: p044 top, p069 top, p004 left are full-bleed dark ADS — page ink at
chroma distance 12–127 from the bed, which a crude dark+neutral test cannot tell from backing.

**Known limit, by design:** where a dark ad reaches the border on nearly every scanline (p047 top)
the material never stops inside the window, so no boundary can be established and the edge is left
uncut.

## Files

    bed_matte.py           the matte (production)
    calibrate_backing.py   derives backing_profile.json for the issue
    backing_profile.json   the measured profile (regenerate per issue)

    audit_matte.py         issue-wide residue audit, INDEPENDENT colour test
    stripe_check.py        contiguous residue AND overcut, both directions
    edge_sheet.py          all four edges per page with the applied cut drawn -> tmp/edges/
    dump_edges.py          per-edge metrics for every page -> tmp/edge_metrics.json

DELETED (in git history if ever needed): learn_priors.py + priors.json — the learned-prior
acceptance path is gone; it is what let a 0.7%-backing edge on p015 be accepted and cut 35mm of
clean paper. bed_matte still ACCEPTED a `priors` argument and every caller loaded and threaded the
176-entry file, but the value was discarded, so a reader reasonably assumed it mattered.
Also deleted: top_matte.py, an early top-edge-only experiment.

Verification is deliberately NOT shared with the fitter: `audit_matte.py` and `stripe_check.py`
carry their own crude colour test, so a bug in the profile cannot hide from them, and
`edge_sheet.py` answers "did it do the right thing" by showing the pixels rather than re-running
the same arithmetic.
