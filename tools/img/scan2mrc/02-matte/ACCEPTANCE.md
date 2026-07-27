# bed_matte acceptance criteria (the target the tuning loop must hit)

The matte marks NON-PAGE **backing** at each edge as unknown (alpha 0): scanner bed (lid + black
backing sheet, both blacks + the transition between them) and colored inserts (the yellow cardboard at
the bottom; could be blue at the top for another magazine). It must NOT cut page content.

## Hard rules
1. **Boundary is ALWAYS a straight line per edge** (never jagged/threaded).
2. **All backing beyond the line, minimum page beyond it** — cover all bed/yellow (incl. the thin taper
   of a wedge and a widening bar bottom), overshoot only a couple px. No black/yellow stripe left.
3. **Content is never cut.** Full-bleed dark ads and halftone/screened images are CONTENT — leave them.
   (A page whose edge is a textured screen, or dark ink with no solid paper just beyond, is content.)
4. Bias: a few px OVER-cut into page margin is fine (it's trimmed to A4 later); UNDER-cut (leaving a
   backing stripe) is not.
5. Resolution-relative (works at 150 & 600 dpi; test at 600).

## Test set (thumbs_600) and expected per-edge behavior
- **030, 050**: thin TOP bed wedge (backing black ~40) -> cut as a thin tilted straight line incl. the
  far corner; YELLOW BOTTOM -> cut (yellow+black+transition up to page). Sides: flush -> no cut.
- **089, 071**: centerfold -> one SIDE has a wide flat black BAR (outer) -> cut as a clean straight
  strip, no overshoot into the schematic/text; YELLOW BOTTOM -> cut. (089 bar = right; 071 = ?)
- **047**: full-bleed dark ad (Star NG-10). TOP/SIDES = content -> LEAVE. YELLOW BOTTOM -> cut.
- **005**: full-bleed GREEN HALFTONE comic. TOP/SIDES = content -> LEAVE (this is the hard one -- the
  halftone's light gaps must not be mistaken for page). YELLOW BOTTOM -> cut.
- (add more pages as needed: an even page with real LEFT bed; a clean text page with minimal bed.)

## How to judge
Run with `--magenta` (50% magenta over cut). Read the magenta PNG: cut regions must be exactly the
backing (bed/yellow), a straight line, no content under magenta, no backing left un-magenta. Report
per-edge cut px + the magenta path; the reviewer (with vision) makes the final call.

## Current open tension
Rejecting p005's halftone TOP while accepting p030's partial (~29% of columns) wedge. `solid` (solid
page just beyond) + line-fit inlier + MIN_LINES must separate them. Do NOT regress the others.
