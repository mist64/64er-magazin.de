# 005 — Scan to 600 dpi master, SPREAD variant

**Applies to:** all — but only where the descriptor says `"binding": "spread"`.
A `"binding": "sheet"` issue runs `r005_masters_sheet` instead, and this
variant is then recorded in that issue's `LOG.md` as **not applicable —
binding**.

**Goal:** turn the raw ~2400 dpi scan of one half of a clipped A3 spread into
the levelled, graded, **logo-anchored exact-A4** 600 dpi master that `r010`
OCRs and `r145` cuts figures from. This is the first step of the chain; it
owns everything between the scanner and `r010`'s input.

This is a **program step**: the orchestrator runs it, checks the exit status and
runs the Verification block below. There is no editorial judgement in it and
nothing to dispatch.

## The two variants

Step 005 exists in two **mutually exclusive** variants, chosen by the issue
descriptor's `binding` (`r000_orchestration.md`, *VARIANTS*; and
`r005_masters_sheet.md`, *The two variants, and why the suffix is not an
insertion*, for why this is not a `9b`):

| variant | the frame holds | the inner boundary | the master |
|---|---|---|---|
| `r005_masters_spread` | half of a clipped **SPREAD** (8610, the monthlies) | the **fold**, found from the binder-clip holes on it | exact A4, anchored on the printed wordmark |
| `r005_masters_sheet` | one loose **SHEET** (SH8601) | the torn fringe, traced | the traced trim, on a shared canvas |

Both write the same contract, `<tmp>/masters600/NNN.png`, and `r010` and
`r145` read that directory without knowing which variant filled it. What the
two share in code — the skew measurement, the paper and prop masks, `trace()`,
the separator call, the GCR undo, the archive writers, the stamp — lives in
`r005_masters.py`, the step's library (no suffix: it is not a third variant),
and the sheet variant's output was checked byte-identical across the move.

## What the paper actually is — measured on 8610's thumbs, not assumed

The monthly was disbound into **A3 sheets**, held in a rigid 6-hole binder
clip, and each sheet scanned twice — one A4 half per frame, with some overlap.
So every frame holds, measured on the 150 dpi thumbs of pages 10/11, 50/51,
100/101, 150/151 and 199/200, and the holes on p100/p101's `sheets600`:

| region | what | measured |
|---|---|---|
| top | a grey bed strip | mean RGB ~(130–190, …), lum ~130–185 — NOT the near-black bed of SH8601 (`BED_LUM` 70 does not see it; the paper-distance mask does, at city-block ~200 from `W`) |
| bottom | the yellow prop | (250, 218, 113), ~40 px at 150 dpi = ~7 mm deep; on `sheets600` its top starts 6.6–6.8 mm above the foot |
| outer side | usually **off-frame** — the paper runs to the frame edge | the border strip reads paper (190–210) on most pages |
| inner side | the **fold**, then the neighbour half of the same sheet | p100 ↔ p101 is the centre spread; the neighbour is blank margin on some pages, content on others |
| on the fold | **6 clip holes** — 3 vertical pairs, dark teardrops on a faint crease | 8.3–10.5 mm in from the inner frame edge on p100, 10.1–12.2 on p101 (NOT the ~20 mm the thumbs suggested); 0.42–1.06 mm **across** the crease and 0.51–2.84 mm **along** it (the punch tore the paper along the fold; two of the six are over 2 mm long), aspect up to 3.72, filled 0.51–0.71 of their box; 155–184 grey levels below their surround on the graded sheet, where paper is ~230 and the holes 16–31 at their darkest |
| the nearest type to the holes | an ad column on p100 | 19.2 mm in on p100, ~22 on p101 — a 7 mm gap between the farthest hole and the nearest type |

Sheet pairing is `k ↔ 201−k`. Parity: **even page → neighbour on the RIGHT,
odd → LEFT** (the same as 8609).

Consequences, and the reason this variant exists:

- There is no torn fringe and no paper edge on the inner side; the sheet
  variant's inner-edge logic has no input. The inner boundary is the fold, and
  the paper mask cannot see a fold — the neighbour half is paper too. The
  holes are the one physical mark of the fold that survives on every sheet.
- The outer trim is often not in the frame, so a trace-based page box would be
  a **lower bound** on the page there, and print-to-trim registration varies
  from page to page: a box that aligned the paper would misalign the type.
  That is why the master is anchored on the **printed wordmark** — the
  "64'er" glyph in the outer-bottom corner, the same on every page, registered
  to the content — and not on the paper. 8609's masters were made this way,
  exact A4 with one rigid offset per parity, and the corpus was measured on
  them.
- Everything else the sheet variant does — skew, grade, stamps, the debug
  overlay, "publish and NOTE, never refuse" — transfers unchanged.

## Two phases

The window offsets are an **issue-wide fit** over per-page anchors, so this
step cannot be one pass per page. Two sub-commands, positional, no flags, no
environment knobs:

```bash
cd tools/img/scan2ocr/rules
../../../../.venv/bin/python r005_masters_spread.py measure          # every page in the descriptor
../../../../.venv/bin/python r005_masters_spread.py measure 10 11 100 101   # named pages
../../../../.venv/bin/python r005_masters_spread.py cut              # the whole issue
./r005_masters_spread.sh                                             # measure all pages, 6 lanes, then cut
./r005_masters_spread.sh 1 50                                        # measure pages 1..50, then cut
```

- **`measure [pages…]`** — per page, heavy (~4–5 min a page in one lane: the
  900 MB PNG decode, the rotation at 2400 dpi, the separator), idempotent, and
  parallel. It levels the scan, grades it, measures the geometry on the
  levelled sheet and writes `geometry/NNN.json` and the debug overlay. It is
  what a change to the grade or to any of the finders re-runs — on the
  affected pages only, since every page's measurement is independent of every
  other's.
- **`cut`** — issue-wide, seconds a page. It reads every `geometry/*.json`,
  fits the window, and cuts every master off `sheets600`. It is re-run alone
  after a change to the fit or the fills, and it is re-run after **any**
  `measure`, because the fit is over all pages: one re-measured page can move
  the window for its whole parity.
- **`r005_masters_spread.sh [FIRST [LAST]]`** — `measure` over the page range
  through `xargs -P 6 -n 5`, then `cut` once. The lane count is a fact about
  this box (32 cores, 550 GB; each lane holds a ~1.7 GB 2400 dpi sheet plus
  the separator's copy), and is in the wrapper's comment. The wrapper's
  `cut` is over **every** geometry file present, not the range given; and a
  lane that ends with a `FAILED` page exits 1, `xargs` then exits 123, and
  the wrapper (`set -e`) stops **before** `cut` — run `cut` by hand once the
  missing input is settled.

Inputs: the issue descriptor `issues/<ISSUE>/issue.json` via `r000_issue.py`
(`scan_dir`, `thumb_150`, `tmp`, `colors`, `binding`, `pages`; 8610 has
`"colors": null`, so the grade uses the built-in anchor set with identity
levels, and the program says so once at the top of its log);
`tools/img/cmyk_reconstruction/target/release/cmyk_reconstruction`, built; the
ICC pair in `tools/img/`; `magick`; the wordmark template
`tools/img/scan2ocr/template_64er_600.png` (a 394 × 131 px grey crop of the
wordmark at 600 dpi — kept beside `rules/`, which admits only `rNNN_` files);
and the repo `.venv` (Python 3.12 with `numpy`, `scipy`, `pillow`). The only
per-issue knob is `ISSUE` at the top of `r005_masters.py`. A page whose scan
or thumb is missing is the one thing that fails a page (`FAILED` on stderr,
the other pages done, exit status 1 at the end of the run); a separator that
is not built stops the run before any page, and a separator or `magick`
failure on a page is an uncaught error. `cut` stops only when there is no
geometry at all, or when a parity has no page with a wordmark to fit on.
Deterministic and local — no model is called.

**After any change to this step, wipe `<tmp>/masters600` and run `cut` again
over every page** — after `measure` on the affected pages, for a change to the
finders or the grade. `r010`'s block ids and `r020`'s cache are keyed on the
masters, and a directory mixing two fits is not something any downstream
check can see.

## `measure` — per page

```
scan_dir/NNN.png
  -> measure skew on the 150 dpi THUMB (projection variance; scale-invariant)
  -> rotate the 2400 scan to level; reduce 4:1; RE-MEASURE the residual on
     the 600 dpi reduce; over SKEW_RESIDUAL_MAX, re-level once from the
     corrected angle; still over, NOTE it and publish anyway
  -> the GEOMETRY, on the levelled 600 dpi sheet BEFORE the grade:
       top, bottom, outer edge  <- paper vs backing, traced (or the full-bleed case)
       the fold                 <- a line through the clip holes (or the colour fallback, or none)
       the anchor               <- the wordmark, by normalised cross-correlation
  -> the measure stamp (page, phase, skew, fold source, anchor score, notes)
  -> separate to CMYK with tools/img/cmyk_reconstruction at 2400, UNDO its GCR,
     ONE render, uncurved -> masters2400, reduced 4:1 -> sheets600
  -> geometry/NNN.json, debug600/NNN.png
```

Every measurement is a number in the JSON; **nothing is decided here** —
no cut, no fill, no window. That is `cut`'s job, once it can see every page.

### Skew and grade — verbatim from the sheet variant

The skew is measured on the thumb, applied to the 2400 dpi scan, and
re-measured on the levelled 600 dpi reduce; a residual over
`SKEW_RESIDUAL_MAX` (0.10 deg) re-levels once from the corrected angle, and a
residual still over it after that is NOTED and the page publishes anyway. The
two-pass arrangement, and the rotation-sign trap it exists for, are the sheet
rule's (*Traps*); nothing differs.

The grade is the sheet variant's too: the whole levelled 2400 dpi sheet goes
through `cmyk_reconstruction`, its GCR is undone (`c = c_final + k`), the
result is ICC-rendered once to AdobeRGB with no curve, and the 600 dpi sheet
is a 4:1 reduce of that render — grading first and averaging afterwards is
what antialiases thin type. **There is one master and no contrast curve**, for
the sheet rule's reason: `r145` cuts figures from the file `r010` OCRs.

The geometry, on the other hand, is measured on the levelled sheet **as
`level_page` hands it over, before the grade**: that is where `paper_mask` and
`prop_mask` were calibrated (the built-in `W` is the raw scan's paper), and
the hole and logo finders read its grey. The graded sheet exists only to be
cut into the master.

### The three outer edges — traced, or the full-bleed case

Top, bottom and the **outer** side are paper-vs-backing boundaries and are
traced exactly as the sheet variant traces a clean edge: per-row and per-column
first and last paper pixel over the page body (rows and columns more than
`BODY_PAPER_FRAC` paper), samples more than 12 mm off the median dropped, 24
bands, the band **median**, a straight line through the bands. Parity says
which side is outer: an even page's neighbour is on the right, so its outer
edge is the **left** one. Backing is whatever the paper mask does not see —
the grey bed strip at the top, which the paper-distance mask sees at
city-block ~200 from `W`, and the yellow prop at the foot (`prop_mask`,
G − B, the sheet rule's measurement). Where the paper runs off the frame the
samples are a constant 0 (or `w−1`) and the line is the frame edge: the scan
does not contain the trim, and the **window** — not this trace — decides the
page there.

**A full-bleed page has no paper for the mask to see, and a page is never
refused: the covers are art to the trim.** Measured, the fraction of rows /
columns whose paper fraction passes `BODY_PAPER_FRAC`, the smaller of the two
(the mask is colour-only, so the scale is immaterial):

```
p001 0.023   p200 0.005      the two covers
p010 0.879   p011 0.872      ordinary pages
p100 0.414   p101 0.724      the centre spread, an ad
```

`FULLBLEED_BODY_FRAC` sits at 0.15, in the gap between 0.023 and 0.414. The
switch is the measurement, not the exception: before it existed p200's trace
raised "12 usable edge samples for 24 bands", but p001's did not raise — it
traced the cover's title band as the "top", 67 mm down the page. Below the
threshold — or if the trace still raises `PageFailed` above it — the **frame
is the edge** on top and outside, and the bottom is the
**prop's top boundary**, which `prop_mask` sees on any page whatever its ink:
per column, the top of the prop run that **touches the foot** (starts within
`PROP_AT_FOOT_MM` = 2 mm of the frame's last row, looked for within
`PROP_FOOT_MM` = 15 mm of it), a `trace()` through those columns. The run
that touches the foot and not the first prop-coloured row: on p001 the cover's
orange banner sits inside the foot and pulled a first-row line 4.7 mm up on
the left. Fewer than 24 columns seeing the prop leaves the bottom at the
frame's last row. The source — `paper` or `fullbleed` — and the measured body
fraction go into the JSON, the overlay (orange lines instead of green) and a
NOTE.

The **inner** side is not traced. The neighbour half of the sheet is paper
too, and the paper mask cannot see the fold.

### The fold — a line through the clip holes

The clip's punches left dark teardrops on the fold, on the **same line as the
crease** (seen on p100 at thumb scale). Their measured position, size, shape
and darkness are in the table above; the constants follow them, each with a
margin:

| constant | value | measured |
|---|---|---|
| `HOLE_BAND_MM` | 16 | the holes are 8.3–12.2 mm in from the inner frame edge; the nearest type 19.2. **The band is the whole argument**: at 30 mm it held 96 (p100) / 108 (p101) candidates, and a text column's left edge is as collinear as a clip — the fit locked on the column both times. 16 sits in the gap. A fold beyond the band is a **miss** (no line, and the sweep reports it), not a wrong line — the safe way round |
| `HOLE_BG_MM`, `HOLE_DIP`, `HOLE_ABS_MAX` | 3.5, 45, 120 | a hole is 45 below its local mean over a 3.5 mm window **and** absolutely under 120: a hole, not a tint. Holes read 155–184 below their surround; a digit on white paper dips 165, so darkness cannot tell a hole from type, and the band must |
| `HOLE_MIN_MM` | 0.4 | longest extent; the satellite specks around a hole are 0.17–0.38 |
| `HOLE_MAX_MM` | 1.5 | across the crease (measured 0.42–1.06) |
| `HOLE_LONG_MAX_MM` | 4.0 | along it (measured 0.51–2.84; the next thing up is 16 mm) |
| `HOLE_FILL_MIN` | 0.40 | area over bounding box: a teardrop, not a line fragment (measured 0.51–0.71) |
| `HOLE_ASPECT_MAX` | 4.5 | measured ≤ 3.72; a clipped rule is 5.2+ |

A candidate is a dark blob in the inner 16 mm band of the levelled sheet's
grey that passes all of those, with its centre of mass and its longest extent
recorded. A blob that **touches either border of the band** — the frame edge
or the band's inner limit — is not a candidate: it is cut off, so its size and
centre are unknown. Measured on p101, the neighbour's screened boxes run to
the frame edge and their clipped ends line up at x = 15 to a tenth of a
millimetre, 15 of them — a fold, if they were allowed to vote.

**The line.** Every pair of candidates proposes a line `x = a·y + b`; a
proposal steeper than `FOLD_TILT_MAX` (1 deg — the clip is rigid and the sheet
is levelled) is dropped; the candidates within `FOLD_TOL_MM` (0.5 mm) of it
are its inliers; a proposal with fewer than `FOLD_MIN_HOLES` (4) inliers, or
whose inliers span less than `FOLD_MIN_SPAN` (half) of the frame height, is
not a fold. The proposal with the most inliers wins, ties broken by the
smaller mean residual, and the winner is refitted by least squares over its
inliers. Six holes on a rigid clip give a line to a fraction of a millimetre;
three do not tell a column of bullets from a clip. The JSON records the line,
the inlier count, the mean residual in mm and the tilt; the hole list records
every candidate, inlier or not, because `cut` fills all of them.

**This is a deliberate, measured deviation from the design.** The spec scored
candidate columns against a **rigid 3-pair template** — the six holes'
relative y-spacing as a constant of the issue, calibrated once. What is built
is the collinearity fit above: any ≥ 4 candidates on one near-vertical line
spanning half the page. On the six pages measured so far it locks on the
holes (p010 6 of 9 candidates, residual 0.17 mm; p011 6 of 7, 0.22; p100
8 of 9, 0.23; p101 9 of 15, 0.20; the covers 21 of 68 and 32 of 40 at
0.12 / 0.27 mm — a full-bleed page's ink **cracks along the crease**, every
crack is a hole-shaped candidate, and the line through them, 14.2 mm in on
p001 and 10.7 on p200, sits on the visible boundary between the two halves in
`debug600/001.png` and `200.png`). The template is the thing to add **only if
the full sweep shows false locks** — a fold reported on something that is not
one — and the constant to re-measure is then the pair spacing, from the
confident pages. A miss (`fold: none`) is not that evidence; the fallback and
the report cover a miss.

### The fold fallback — the neighbour's colour boundary

8609's winning spine signal, kept as the **fallback** for a page whose
candidates do not fit a line: where the neighbour bled in, dark fraction and
saturation step up together at one x, and the clean margin between is a band
of neither. In the inner 50 mm strip, in each of 28 horizontal bands, a column
is *content* if more than 5 % of its pixels are under lum 95 or its mean
colour's saturation (max − min over 255) exceeds 0.17; the first content run
in from the border that starts within 10 mm of the border (this page's own
type starts further in), is at least 0.85 mm wide (a speck is not) and does
not reach the strip's inner end (a full-bleed neighbour merges with the page)
gives one point: its page-facing edge. A line through the points, re-fitted up
to five times with samples more than 1.9 mm (~45 px) off it dropped; at least
6 bands must survive, and the tilt must be within 1.5 deg. The function can
also reject a line more than `NB_PRIOR_MM` (5 mm) from a prior fold x, but
**`measure` passes no prior**: it runs one page at a time with no view of the
issue, so the spec's "within ±5 mm of the issue-median fold offset" is not
applied. It finds a fold only where the neighbour has content — blank margin
gives no boundary, correctly, and the page then has `fold: none`.

A fold from the fallback is NOTED (`FOLD from the neighbour's colour
boundary`, with the band count, the residual and how many hole candidates
failed to fit); no fold at all is NOTED (`FOLD not found`) and **the inner
side is not cut** — the neighbour's half stays in the sheet, and the window,
placed by the wordmark (or, with no wordmark either, on the inner frame
edge), is what takes it out of the master. The source —
`holes` / `colour` / `none` — is in the JSON, the stamp and the fit report.

### The anchor — the 64'er wordmark

The wordmark is the same glyph on every page, not mirrored between parities,
print-registered to the content, in the **outer-bottom** corner: even pages
bottom-left (`<num>  64'er`), odd bottom-right (`64'er  <num>`). The finder is
zero-mean **normalised cross-correlation** of the template over a search
region of the levelled sheet's grey — the rows from 30 mm to 5 mm above the
foot, and the outer 48 % of the width — by FFT, valid mode. The page is
levelled before this runs, so there is no angle sweep.

Two things the finder had to get right, both measured:

- **The sums run in float64 with a variance floor.** The window variance is
  the difference of two ~3 × 10⁹ sums (51 614 px of paper at ~230), which
  single precision holds to ~256: on a synthetic blank page a flat window's
  variance came out 128 or −2180 where the truth is 0, and the numerator's
  rounding noise over that scored 522 at a blank spot. In float64 the same
  window is 10⁻⁷ — still a zero divisor waiting for a flatter page — so the
  variance is floored at `NCC_SIGMA_MIN` = one grey level of texture per
  pixel, not an epsilon.
- **The gate is 0.5.** Measured on 8610's `sheets600`: p010 scores 0.941, p011
  0.933 (the wordmark, 26.5 / 20.9 mm in from the outer edge); p100 and p101
  are ad pages without one and their best window is 0.290 / 0.292; the
  runner-up on the two logo'd pages is 0.247 / 0.234. `LOGO_SCORE_MIN` = 0.5
  sits in the gap between the ceiling of a page without the wordmark (~0.29)
  and the floor of one with. 8609 accepted 0.42 with an angle sweep; here the
  page is level.

The search band's last 1.7 mm is the yellow prop (it starts 6.6–6.8 mm above
the foot; the wordmark's baseline sits at 11.2–11.4 mm on p010/p011), and the
windows that overlap it score ≤ 0.29 — no spurious peak, so the band is not
clipped to the prop line. The anchor recorded is the wordmark's
**outer-bottom corner** — the box's left edge on an even page, its right edge
on an odd one, and its bottom — with the score and the box. Under the gate,
`anchor: null` and a NOTE.

### The debug overlay

One per page, always, `debug600/NNN.png` at 1/5 scale, on the **levelled,
ungraded, unfilled** sheet — the page as the finders saw it, with the
decisions drawn on top: the three edges **green** when traced from paper,
**orange** when they are the full-bleed frame + prop lines; the fold
**magenta**; every hole candidate ringed in the same magenta (the ring is drawn
wide enough to survive the reduction — a 0.7 mm hole would otherwise be an
invisible 3 px ring); the wordmark's box **blue**; and, top-left, one line of
text — page, parity, edge source, fold source, anchor score or `NONE` —
followed by the page's notes. Lines and rings are drawn at 600 dpi and reduced
with the page; the text is drawn after the reduction, because PIL's default
font is ~11 px.

### The measure log line and stamp

`p010: skew +0.24 -> +0.00 deg | edges T -0.15 B -0.27 O +0.24 | fold holes
n=6 x=5026 tilt +0.45 | logo 0.95 | grade cec3ff863b36`, with every NOTE on
its own indented line below. The measure-phase stamp — page, `phase measure`,
skew, fold source, anchor score, notes, over the grade block — goes into
`masters2400/NNN.png`, `cmyk2400/NNN.tif`, `NNN.colors.txt` and the `r005`
chunk of `sheets600/NNN.png`, as the sheet rule's *The stamp* describes.

## `cut` — issue-wide

```
geometry/*.json
  -> FIT one (S, B) per parity over the pages that have their own wordmark
  -> per page:
       the anchor: the wordmark through (S, B), or the page's own edges
       the UNKNOWN mask on sheets600: outside the three edges, beyond the
         fold, the hole discs -- painted paper white
       the window cut from that; where it overhangs the frame, white
  -> masters600/NNN.png (4961 x 7016, every page) + NNN.stamp.txt
  -> geometry/fit.json
```

### The fit

**One rigid (S, B) per parity** — the anchor's distance from the window's left
and top edge — chosen to minimise the **unknown** fraction inside the
210 × 297 mm window (bed, prop, beyond the fold, off the frame) summed over the
pages of that parity that carry their own wordmark. The unknown mask is
computed at 1/`FIT_SCALE` = 1/4 resolution (one step is 0.17 mm, under the
0.3 mm the edge inset already gives away), the window sums come from one
integral image per page over the mask **padded with unknown** (off the frame
is not this page), and every page's sums are accumulated on a common (S, B)
grid: **S spans the whole master width** and B spans `FIT_B_RANGE_MM`
(250–297 mm, the anchor being in the foot of the page). The search spans the
whole width because 8609's capped range once pinned the odd optimum to the cap
and reported a window mostly off the page. The argmin is the fit; a parity
with **no** logo'd page stops `cut` — there is nothing to fit on.

8609's fit was even S=568 B=6892, odd S=4416 B=6900 (600 dpi px), unknown
p50 1.38 % / 1.92 %. On the six pages measured so far — one logo'd page per
parity, so a fit in name only — this program lands **even S=592 B=6900, odd
S=4452 B=6908** — S larger by 24 / 36 px (1.0 / 1.5 mm), B by 8 px, than
8609's. The full sweep re-fits over every logo'd page and that number
replaces this one.

### Pages without a wordmark — placed on their physical edges

A page the finder returns no anchor for — covers, full-page ads, full-bleed
pictures — is **not** placed through the fit. Its window's top-left comes
directly from the two edges every page has whatever its ink: its **inner edge
on the fold** (the fold line at mid-height; the inner frame edge if there is
no fold at all) and its **foot on the bottom trim** (the traced or prop-derived
bottom line at mid-width) — so `x0 = fold − 4961` on an even page, `x0 =
fold` on an odd one, and `y0 = bottom − 7016` on both. No interpolation from
neighbours, whose placement on the scanner is unrelated to this page's. The
stamp says `anchor edges: window top-left (x, y) from fold + bottom trim`, the
page gets a NOTE, and `fit.json` lists it under `anchor: edges`.

### The fills

Everything the master should not show is painted **255 white** on the page's
`sheets600` before the window is cut, and the window is cut from that. The
**unknown mask** is:

- above the top line and below the bottom line, each moved 0.3 mm
  (`CUT_INSET_MM` = `EDGE_INSET_MM`) into the page, as the sheet variant;
- outside the outer line, moved 0.3 mm in;
- beyond the fold line, cut **on** the fold (`FOLD_INSET_MM` = 0: the holes
  are filled separately, so the line needs no margin);
- every hole candidate's disc — its own radius (half its longest extent) plus
  `HOLE_FILL_R_MM` = 0.4 mm — every candidate, not only the line's inliers,
  because a candidate is by construction a hole-shaped dark mark in the fold
  band whether or not it sat on the line;
- and, in the master, wherever the window overhangs the frame.

A page with `fold: none` has no inner fill: its master shows whatever of the
neighbour the window reaches. The **unknown fraction** stamped on every page
is the mask's share of the master's 4961 × 7016 px, overhang included.

### The stamp fields and the fit report

Every master carries, in its `r005` chunk and beside it in `NNN.stamp.txt`,
over the grade block the sheet rule describes: `page`, `phase cut`,
`master-px 4961 7016`, `skew` (angle → residual), `fold` (source, inlier
count, tilt), `holes` (the candidate count), `anchor` (`logo (x, y) score
0.95`, or `edges: window top-left (x, y) from fold + bottom trim`), `window`
(`S B (parity)`), `unknown` (`n.nn% of the window is fabricated white`) and
`notes` — every NOTE `measure` made plus `cut`'s own. Detecting a stale master
is a string comparison on `grade-sha`, Verification check 4.

`geometry/fit.json` holds the fit — `(S, B)` per parity; per parity the page
count fitted on and the mean unknown fraction at the optimum — and, per page,
the anchor source, the fold source and the unknown fraction. Verification
check 5 reads the whole report from it.

## The fill is fabrication, and it is stated

The white outside the traced edges, beyond the fold, in the hole discs and in
the frame overhang is **paper that the scan did not contain or that the clip
destroyed**. It is fabricated and it is deliberate, and it is stated here — and
in every stamp, as the unknown fraction — so that nobody later reads a clean
margin, a white corner or a hole-free fold as evidence about the copy. The
bed, the prop, the neighbour's half and the clip holes were all in the frame;
the master shows none of them, by decision, not by measurement.

What is **not** fabricated: the page's own ink up to the fold line (the cut
is on the line, with no inset); on a page whose fold came from the colour
boundary, the neighbour's blank margin between its content and the crease,
which is real scanned paper and stays for the window to take out — that
page's NOTE says which finder placed the line; and the neighbour's content on
a page with `fold: none`, which stays, because guessing a fold would be a
fabrication too.

## Outputs

```
<tmp>/masters600/NNN.png        the master r010 OCRs and r145 cuts from   (the contract)
<tmp>/masters600/NNN.stamp.txt  the stamp, readable without decoding the PNG
<tmp>/sheets600/NNN.png         the levelled, graded, UNCUT sheet at 600 dpi (the measure stamp in its chunk)
<tmp>/masters2400/NNN.png       the same at 2400 — a figure that runs to the trim still exists here
<tmp>/cmyk2400/NNN.tif          the separation, deflate-compressed, + NNN.colors.txt as the separator ran
<tmp>/geometry/NNN.json         every measurement `cut` reads: edges, fold, holes, anchor, skew, notes
<tmp>/geometry/fit.json         the window fit, the tallies, the per-page anchor / fold / unknown
<tmp>/debug600/NNN.png          the overlay the user reviews
```

`<tmp>/masters600` is derived by `r000_issue.py`, because it is the contract
the rest of the chain depends on; the other directories are this step's own
workings and are named in this step.

Every master is **4961 × 7016 px, exactly A4 at 600 dpi, every page**, so
`r010`'s block geometry and `r145`'s figure crops share one coordinate system.
8609's masters are 4960 × 7015 because they were reduced 4:1 from an
odd-sized 2400 window; one pixel is 0.04 mm and `r010`'s geometry is
fractional, so the two issues share a coordinate system to within that.

## Verification

```bash
cd tools/img/scan2ocr/rules
PY=../../../../.venv/bin/python

# 1. every page produced every artefact
$PY - <<'PY'
import os, r005_masters_spread as R
iss = R.ISS
for d, ext in ((R.OUT_MASTER, ".png"), (R.OUT_MASTER, ".stamp.txt"),
               (R.OUT_SHEET600, ".png"), (R.OUT_SHEET, ".png"),
               (R.OUT_CMYK, ".tif"), (R.OUT_CMYK, ".colors.txt"),
               (R.OUT_GEOM, ".json"), (R.OUT_DEBUG, ".png")):
    have = sorted(f[:3] for f in os.listdir(d) if f.endswith(ext) and f[:3].isdigit())
    want = ["%03d" % p for p in iss.page_range]
    miss = [p for p in want if p not in have]
    print(f"{d.name:12s}{ext:12s} {len(have):3d}/{len(want)}  missing:",
          (miss[:12] + ["..."] if len(miss) > 12 else miss) or "none")
PY

# 2. every master is 4961 x 7016
$PY - <<'PY'
from collections import Counter
from PIL import Image
import os, r005_masters_spread as R
Image.MAX_IMAGE_PIXELS = None
sizes = Counter(Image.open(R.OUT_MASTER / f).size
                for f in sorted(os.listdir(R.OUT_MASTER)) if f.endswith(".png"))
print("expected", (R.MASTER_W_PX, R.MASTER_H_PX), "| found", dict(sizes))
assert list(sizes) == [(R.MASTER_W_PX, R.MASTER_H_PX)]
PY

# 3. residual skew of every master, re-measured
$PY - <<'PY'
import numpy as np, os
from PIL import Image
import r005_masters_spread as R
from r005_masters import measure_skew
Image.MAX_IMAGE_PIXELS = None
worst = []
for f in sorted(os.listdir(R.OUT_MASTER)):
    if f.endswith(".png"):
        a = np.array(Image.open(R.OUT_MASTER / f).reduce(4).convert("L"), float)
        worst.append((abs(measure_skew(a)), f))
worst.sort(reverse=True)
print("worst residuals:", [(f, "%.2f" % r) for r, f in worst[:8]])
PY

# 4. every stamp names the current grade; chunk == sidecar
$PY - <<'PY'
import os, re
from PIL import Image
import r005_masters_spread as R
Image.MAX_IMAGE_PIXELS = None
stale = disagree = 0
for f in sorted(os.listdir(R.OUT_MASTER)):
    if not f.endswith(".png"): continue
    side = (R.OUT_MASTER / f.replace(".png", ".stamp.txt")).read_text()
    chunk = Image.open(R.OUT_MASTER / f).info.get("r005", "")
    stale += re.search(r"^grade-sha\s+(\S+)$", side, re.M).group(1) != R.GRADE_SHA
    disagree += chunk != side
print("stale", stale, "chunk!=sidecar", disagree)
PY

# 5. the fit, the anchor and fold tallies, the pages to look at
$PY - <<'PY'
import json, r005_masters_spread as R
from collections import Counter
r = json.loads((R.OUT_GEOM / "fit.json").read_text())
print("fit", r["fit"], r["stats"])
pages = r["pages"]
print("anchor", Counter(p["anchor"] for p in pages.values()))
print("fold  ", Counter(p["fold"] for p in pages.values()))
import numpy as np
for par in ("even", "odd"):
    u = [p["unknown"] for s, p in pages.items() if (int(s) % 2 == 0) == (par == "even") and p["anchor"] == "logo"]
    print(par, "unknown p50 %.2f%% p95 %.2f%%" % (100 * np.percentile(u, 50), 100 * np.percentile(u, 95)))
print("LOOK AT (no logo):", [s for s, p in pages.items() if p["anchor"] != "logo"])
print("LOOK AT (no fold):", [s for s, p in pages.items() if p["fold"] == "none"])
print("LOOK AT (unknown > 4%):", [s for s, p in pages.items() if p["unknown"] > 0.04])
PY

# 6. no bed, no prop in a 6 mm band inside the traced edges (on sheets600)
$PY - <<'PY'
import json, numpy as np, os
from PIL import Image
import r005_masters_spread as R
from r005_masters import prop_mask, MM
Image.MAX_IMAGE_PIXELS = None
b = int(6 * MM)
bad = []
for f in sorted(os.listdir(R.OUT_GEOM)):
    if not f[:3].isdigit(): continue
    g = json.loads((R.OUT_GEOM / f).read_text())
    rgb = np.array(Image.open(R.OUT_SHEET600 / f.replace(".json", ".png")).convert("RGB"))
    u = R.unknown_mask(g)
    inside = ~u
    lum = rgb.mean(2)
    band = (inside & ~np.roll(inside, b, 0)) | (inside & ~np.roll(inside, -b, 0))   # 6 mm inside top/bot
    dark = (lum[band] < 70).mean() if band.any() else 0
    prop = prop_mask(rgb)[band].mean() if band.any() else 0
    if dark > 0.02 or prop > 0.002: bad.append((f[:3], "%.3f" % dark, "%.4f" % prop))
print("bands with bed/prop:", bad or "none")
PY

# 7. contact sheet of the overlays, for the eye
magick montage $(ls /tmp/64er_8610/debug600/*.png | head -200) -tile 10x -geometry 200x282+2+2 /tmp/64er_8610/debug_contact.png
```

Check 6 reads a full-bleed page's own ink as "bed" or "prop" where it runs to
the trim — the same limitation the sheet rule records for its check 4 — so a
cover in that list is looked at, not counted as a failure. Its dark test is
the sheet variant's `BED_LUM` 70, which 8610's grey bed strip (lum 130–185)
passes: the check sees the prop and the black rotation wedge at the frame,
and a bed strip left inside the top line would show as a raised unknown
percentile in check 5 and on the contact sheet, not here. Check 5's three
`LOOK AT` lists are the pages to open in `debug600/` and `masters600/`; the
8609 reference for the unknown percentiles is even 1.38 / 2.30 %, odd
1.92 / 2.99 %.

## What it read, on the full sweep

Filled in after the full sweep.

## Notes

- Constants live at the top of each section of `r005_masters_spread.py`,
  heavily commented, and everything describing paper is in **millimetres**.
  No CLI knobs, no env knobs. The shared constants and functions are in
  `r005_masters.py`; a change there is a change to both variants, and the
  sheet variant's byte-identity gate (`r005_masters_sheet.md`) is what proves
  it did not move.
- **Read `FINDINGS.md` before changing anything here.**
- The six pages the constants were measured on: 010 and 011 (an ordinary
  spread, both wordmarks, the logo scores and the fit), 100 and 101 (the
  centre spread, an ad without a wordmark, the holes and their band), 001 and
  200 (the covers, full bleed, the frame + prop edges and the edges anchor).
  Any change to a hole, fold or logo constant is re-measured on all six before
  a sweep.
- A change to `MASTER_W_PX`/`MASTER_H_PX` changes every master's pixel size and
  every page-fraction downstream of it. Wipe `masters600/` and `cut` again —
  this is not a change that can be made for one page.
