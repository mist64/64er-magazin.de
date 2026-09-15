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
  parallel. It levels the scan, measures the geometry on the levelled sheet,
  then grades it, and writes `geometry/NNN.json` and the debug overlay. It is
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
levels, and the program says so at the top of its log — once per process, so
once per `xargs` lane invocation of 5 pages, ~40 times in a sweep log, each
time followed by the run stamp);
`tools/img/cmyk_reconstruction/target/release/cmyk_reconstruction`, built; the
ICC pair in `tools/img/`; `magick`; the wordmark template
`tools/img/scan2ocr/template_64er_600.png` (a 394 × 131 px grey crop of the
wordmark at 600 dpi — kept beside `rules/`, which admits only `rNNN_` files);
and the repo `.venv` (Python 3.12 with `numpy`, `scipy`, `pillow`). The only
per-issue knob is `ISSUE` at the top of `r000_issue.py`, which `r005_masters.py`
imports. A page whose scan
or thumb is missing is the one thing that fails a page (`FAILED` on stderr,
the other pages done, exit status 1 at the end of the run); a separator that
is not built stops the process on its first page — inside
`separate_and_render`, after that page has been levelled and measured — and a
separator or `magick` failure on a page is an uncaught error. `cut` stops only when there is no
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

**A page that is not full-bleed can still carry ink to the trim on one side**,
and there the trace follows the ink's inner boundary. The sweep showed it:
p027, a purple ad ground, traced its top 27.2 mm down and its bottom 15.7 mm
up at −4.05°; p092, a 0.80-paper page with a red band across its top, its top
15.2 mm down at +2.49°; p149, a black column, its outer edge 13.5 mm in at
+0.96°; p177 its bottom 16.4 mm up at −5.97°; p057 its outer edge at −1.49°
into a photo — and the masters were painted white there. The body fraction
cannot see this (p092 is 0.80 paper); the **frame** can. It is 304.3 mm high
for 297 of page and 7 of prop, so on the 195 sound pages the top trim sits
0–1.1 mm below the frame's top, the bottom 6.4–9.4 mm above its foot, the
outer trim 0–5.7 mm in (the frame's slack over A4 beyond the fold is at most
8 mm), and no sound edge tilts more than 0.82° on a levelled page. So each
traced edge is checked against the frame — `EDGE_TOP_MAX_MM` 3,
`EDGE_BOT_MAX_MM` 12, `EDGE_OUTER_MAX_MM` 8, `EDGE_TILT_MAX` 1° — and an
edge beyond that is ink: **that edge alone** takes the full-bleed line (the
frame row or column, the prop's top), the other two traces are kept, the
source stays `paper`, and the JSON's `edges.replaced` and a NOTE say which
edge, how deep the trace ran and how tilted. The safe direction: a page
narrower than A4 whose trim really is 9 mm in would show bed in its outer
margin, and never lose ink.

The **inner** side is not traced. The neighbour half of the sheet is paper
too, and the paper mask cannot see the fold.

### The fold — a line through the clip holes

The clip's punches left dark teardrops on the fold, on the **same line as the
crease** (seen on p100 at thumb scale). Their measured position, size, shape
and darkness are in the table above; the constants follow them, each with a
margin:

| constant | value | measured |
|---|---|---|
| `HOLE_BAND_MM` | 16 | the holes are 8.3–12.2 mm in from the inner frame edge; the nearest type 19.2. **The band is the whole argument**: at 30 mm it held 96 (p100) / 108 (p101) candidates, and a text column's left edge is as collinear as a clip — the fit locked on the column both times. 16 sits in the gap. A fold beyond the band is a **miss** (no line, and the sweep reports it), not a wrong line — the safe way round. The band keeps the page's **own** type out; the **neighbour's**, which the frame can clip into the band, is the template's job (below) |
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
the frame edge and their clipped ends line up at x = 15 mm from the frame
edge to a tenth of a millimetre, 15 of them — a fold, if they were allowed to
vote.

**The line.** Every pair of candidates proposes a line `x = a·y + b`; a
proposal steeper than `FOLD_TILT_MAX` (1 deg — the clip is rigid and the sheet
is levelled) is dropped; the candidates within `FOLD_TOL_MM` of it are its
inliers, and a proposal with fewer than `FOLD_MIN_HOLES` (4) is not scored.
`FOLD_TOL_MM` is **across** the crease, where a torn hole's centre of mass
moves: it was 0.5 (the holes are 0.42–1.06 mm across) until the sweep showed
four pages — p064, p083, p117, p137 — whose four detected holes sit 0.8–0.9
mm apart across the line, so that no line held them and the page had no fold
(two of them without a wordmark to place the window by either). At **0.8** all
four fit and no other page's line moves more than 0.4 mm; what keeps a text
column out is not this tolerance but the template.

**Which line: the clip's template, not the count.** The spec scored candidate
columns against a **rigid 3-pair template** — the six holes' relative
y-spacing as a constant of the issue, calibrated once — and the first build
did not: it took the line with the most inliers, on the argument that six
holes on a rigid clip are more collinear than anything else in a 16 mm band,
and left the template for the sweep to demand. The sweep demanded it. On
**25 of 200 pages** the most collinear thing in the band was the
**neighbour's justified column edge**: where the frame reaches more than the
neighbour's inner margin past the fold, its line-end hyphens, commas and
letter fragments are clipped by the frame edge, and the ones that do not
touch it are hole-shaped, 0.4–3.7 mm in, and collinear to 0.1 mm — 15 to 152
of them against six holes (p061: 22 at 0.6 mm, p086: 64 at 1.9, p189: 50 at
2.3). The true holes were in the band on every one of those pages, at
8.5–14.8 mm, and lost the vote. On a page with a wordmark the wrong line is
harmless to the master (the window excludes the strip either way) but the
report is a lie; on an edges-anchored page it moves the window by ~10 mm.

The template was then **measured** on the 75 pages whose six holes were the
line's only inliers: from the first hole, `HOLE_TEMPLATE_MM` = (0, 13.35,
89.62, 102.92, 169.36, 182.95) — the gaps 13.35 / 76.27 / 13.30 / 66.44 /
13.59 mm with sd 0.14–0.19 mm — and once shifted onto a page's six no hole
deviates more than 0.41 mm (p95 0.30). `HOLE_TEMPLATE_TOL_MM` = 0.75. Every
distinct inlier set is **scored**: for every hypothesis "inlier *k* is
template hole *j*", the number of the six positions with an inlier within the
tolerance and the RMS of those offsets; the best hypothesis is the line's
score. Lines rank by **matches, then RMS, then inliers, then residual**; under
`HOLE_TEMPLATE_MIN` = 4 matches a line is not a fold. Four matches also
replace the old half-height span rule: pairs 1+2 span 103 mm and are the clip
(p092, p109, p124 — their other holes off the line or under ink); four random
specks within 0.75 mm of four template positions are not. The winner is
refitted by least squares over its inliers; the JSON records the line, the
inlier count, the template matches and RMS, the mean residual and the tilt;
the hole list records every candidate, inlier or not, because `cut` fills all
of them.

**What the template does and does not tell apart.** Measured on 8610, a
neighbour column reaches at most **5** matches, at RMS 0.31–0.45 (the six
pages that get there: p084, 086, 091, 187, 189, 193); the holes score 6 on
those pages, and where only five holes are seen they fit at RMS ≤ 0.30 and
win on RMS. That 0.30-against-0.31 margin is a fact about **8610's
fragments** — line ends are ragged, so a column's y's are irregular and
match the template only by chance — and not a property of the scorer. A
perfectly **regular** column at body-text pitch is a different thing: the
template's gaps (13.35 / 76.27 / 13.30 / 66.44 / 13.59 mm) are near-multiples
of some pitches, and a synthetic column alone at 4.5 mm pitch scores 4
matches at RMS 0.24, at 4.7 mm **6** at RMS 0.41 — 8 of the 26 pitches from
3.5 to 6.0 mm pass `HOLE_TEMPLATE_MIN` (the unit test
`…regular_column_alone_KNOWN_LIMITATION` keeps the case). Where the holes are
also on the page it still loses to them on matches or RMS; alone — the holes
torn, inked over or off the line — it would be reported as the fold. The
refusal would be a regularity test on the inliers' spacing (a clip has six
marks, type has a pitch); not built, because no page of 8610 was that.

**The absolute prior.** The clip is one rigid object and it sat against the
same stop of the scanner for every sheet: over the 196 pages with a hole
fold, the best template shift — hole 1's y in the frame — is 58.05–59.97 mm
on 192 of them (mean 58.91), and the four outside were the pages where the
shift was arbitrary: p005 / p038 / p163 (a screen or a cracked crease dense
enough that any shift matches) and **p084 at 65.9 — the one fake that had
stood**. So a hypothesis counts only if its shift is within
`HOLE_TEMPLATE_Y0_TOL_MM` = 3 mm (three times the spread; a 0.5° levelling
rotation about the sheet's centre moves y at the fold by under 1 mm) of
`HOLE_TEMPLATE_Y0_MM` = 59.0. Replayed over the 200 stored candidate lists
it changed two pages: p084's fake lost its shift and the four true holes,
which fit at 0.8 mm, became the fold at 12.9 mm; p005's shift pinned on its
real holes (10.33 → 10.28 mm). It does **not** kill a regular column — its
fitting shifts recur every pitch, so one always lands inside ±3 mm. It is a
fact about the operator's placement, re-measured per issue like the
template; an issue whose clip sat elsewhere reports `fold none` on every
page, and checks 5 and 8 say so.

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
**orange** when they are the full-bleed frame + prop lines (per edge: a
traced page with one edge given up to the frame shows that one orange); the fold
**magenta**; every hole candidate ringed in the same magenta (the ring is drawn
wide enough to survive the reduction — a 0.7 mm hole would otherwise be an
invisible 3 px ring); the wordmark's box **blue**; and, top-left, one line of
text — page, parity, edge source, fold source, anchor score or `NONE` —
followed by the page's notes. Lines and rings are drawn at 600 dpi and reduced
with the page; the text is drawn after the reduction, because PIL's default
font is ~11 px.

### The measure log line and stamp

`p010: skew +0.24 -> +0.00 deg | edges T -0.15 B -0.27 O +0.24 | fold holes
n=6 t=6/0.08 x=5026 tilt +0.45 | logo 0.95 | grade cec3ff863b36` (`t=` the
template matches and RMS in mm, on a hole fold), with every NOTE on
its own indented line below. The measure-phase stamp — page, `phase measure`,
skew, fold source, anchor score, notes, over the grade block — goes into
`masters2400/NNN.png`, `cmyk2400/NNN.tif` and the `r005` chunk of
`sheets600/NNN.png`, as the sheet rule's *The stamp* describes;
`NNN.colors.txt` is the profile as the separator ran it (`write_profile`'s
header and the anchor and level lines), with no stamp fields.

### The NOTEs `measure` and `cut` write

Every NOTE is one line, prefixed by its finder, in the log (indented under
the page line), the stamp's `notes` field, the overlay's text and the JSON's
`notes` list. The prefixes, verbatim from the program:

| prefix | when |
|---|---|
| `SKEW re-levelled: residual was ±n.nn, corrected to ±n.nn deg, now ±n.nn` | the first residual was over `SKEW_RESIDUAL_MAX` and a second pass ran |
| `SKEW still ±n.nn deg after a second pass (allowed 0.1) -- published anyway` | the second pass did not bring it under |
| `EDGES fullbleed: paper body n.nn -- top/outer at the frame, bottom from the prop` | the paper body fraction was under `FULLBLEED_BODY_FRAC` (or the trace raised) |
| `EDGES top|bot|outer from the frame|prop: the paper trace ran n.n mm in at ±n.nn deg -- ink to the trim` | a traced edge was beyond `EDGE_*_MAX_MM` or tilted over `EDGE_TILT_MAX`; that edge is the frame's (the prop's, for the bottom) |
| `FOLD from the neighbour's colour boundary (n bands, residual n.nn mm) -- n hole candidates did not fit a line` | no hole line; the fallback found the neighbour's boundary |
| `FOLD not found: n hole candidates, no colour boundary -- the inner side is not cut` | neither |
| `LOGO not found -- the window is anchored on fold x and bottom-trim y instead` | the best NCC window scored under `LOGO_SCORE_MIN` |
| `ANCHOR from the page edges (fold + bottom trim): the wordmark was not found` | `cut`'s own, on every page without a wordmark (so it accompanies `LOGO not found`) |

### `geometry/NNN.json`

One object per page, keys and types as `measure_geometry` writes them; every
coordinate is a pixel on the levelled 600 dpi sheet, `x` across, `y` down,
polynomials in `numpy.polyval` order (highest power first):

```
page          int          the page number
parity        "even"|"odd"
sheet_px      [w, h]       ints, the levelled sheet's size
skew          {angle: float deg applied to the scan, residual: float deg re-measured on the sheet}
edges         {top:   [a, b]   floats, y = a·x + b   (traced, or the frame's first row)
               bot:   [a, b]   floats, y = a·x + b   (traced, or the prop's top)
               outer: [a, b]   floats, x = a·y + b   (traced, or the frame's outer column)
               source: "paper"|"fullbleed"
               body:   float   the paper-body fraction the switch was made on
               replaced: [[name, depth_mm, tilt_deg], ...]   traced edges given up for the frame / prop
                         on a "paper" page (name "top"|"bot"|"outer"; floats); [] when none}
fold          {source: "holes"|"colour"|"none"
               poly:   [a, b] floats, x = a·y + b, or null when "none"
               n:      int    inliers of the line (0 when "none"; the band count when "colour")
               residual_mm: float or null   mean |x| residual of the inliers
               template:        int         template matches (0 unless "holes")
               template_rms_mm: float|null  RMS of the matched y offsets (null unless "holes")
               tilt_deg: float or null}
holes         [[cx, cy, size_mm], ...]   floats; EVERY candidate, inlier or not; size = longest extent
anchor        null, or {source: "logo", x: int, y: int, score: float, bbox: [x0, y0, x1, y1]}
              x, y = the wordmark's OUTER-BOTTOM corner; bbox = the template's box, ints
notes         [str, ...]    the NOTEs above, in the order they were made
```

`geometry/fit.json` is `cut`'s: `{"fit": {"even": [S, B], "odd": [S, B]},
"stats": {parity: {"pages": n, "mean_unknown": f}}, "pages": {"NNN":
{"anchor": "logo"|"edges", "fold": source, "unknown": f}}}`.

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
p50 1.38 % / 1.92 %. On the six pages measured first — one logo'd page per
parity, a fit in name only — this program landed even S=592 B=6900, odd
S=4452 B=6908. The full sweep, over 83 even and 62 odd logo'd pages, lands
**even S=556 B=6904, odd S=4416 B=6904**: odd S is 8609's to the pixel, even
S is 12 px (0.5 mm) smaller, B 12 / 4 px larger (*What it read*).

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
  band whether or not it sat on the line. **Measured on the sweep, that
  argument fails on a screen:** 42 pages carry candidates on the page side
  of the fold beyond the six holes — crease specks and cracks, ≤ 38 discs
  and ≤ 73 mm² a page on 41 of them — and on **p005**, whose coarse-screened
  picture starts at the crease, 518 dots of the picture are painted white,
  1137 mm², the first ~5 mm of the picture along the inner edge (*What it
  read*). The fill that would not do this paints the line's inliers within
  2 mm of a template position (the holes and their torn fragments) and
  nothing else; not changed on this sweep, recorded as p005's gap;
- and, in the master, wherever the window overhangs the frame.

A page with `fold: none` has no inner fill: its master shows whatever of the
neighbour the window reaches. The **unknown fraction** stamped on every page
is the mask's share of the master's 4961 × 7016 px, overhang included.

### The stamp fields and the fit report

Every master carries, in its `r005` chunk and beside it in `NNN.stamp.txt`,
over the grade block the sheet rule describes: `page`, `phase cut`,
`master-px 4961 7016`, `skew` (angle → residual), `fold` (source, inlier
count, template matches on a hole fold, tilt), `holes` (the candidate count), `anchor` (`logo (x, y) score
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

# 8. where the fold is: x from the inner frame edge, inliers, template matches -- the outliers
$PY - <<'PY'
import json, numpy as np, r005_masters_spread as R
from r005_masters import MM
rows = []
for p in sorted(R.OUT_GEOM.glob("[0-9][0-9][0-9].json")):
    g = json.loads(p.read_text()); w, h = g["sheet_px"]; f = g["fold"]
    if not f["poly"]: continue
    x = np.polyval(f["poly"], h / 2)
    rows.append((g["page"], f["source"], (w - 1 - x) / MM if g["parity"] == "even" else x / MM, f["n"], f["template"]))
d = [r[2] for r in rows if r[1] == "holes"]
print("hole folds: x mm p5 %.1f p50 %.1f p95 %.1f | n==6: %d | template 6/5/4: %d/%d/%d" % (
    np.percentile(d, 5), np.percentile(d, 50), np.percentile(d, 95), sum(r[3] == 6 for r in rows),
    *[sum(r[4] == m for r in rows) for m in (6, 5, 4)]))
print("LOOK AT (x < 5 mm -- the neighbour's column?):", [(r[0], "%.1f" % r[2], r[3], r[4]) for r in rows if r[2] < 5])
print("LOOK AT (n > 12 -- cracks or a screen?):", [(r[0], r[3]) for r in rows if r[3] > 12])
PY
```

Check 8 is the one that found the sweep's false-lock class (*Which line*,
above): a hole fold under 5 mm from the frame edge is the neighbour's column
until looked at, and a line with more than 12 inliers is a crease cracking
through ink or a coarse screen, and its x is then only as good as the crease.
Check 3's projection measure has no type to read on a full-bleed cover; a
cover in its list is measured on its one line of type before it is believed.

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

2026-09-15, all 200 pages of 8610, `r005_masters_spread.sh` (6 lanes, 12:46 →
17:03, 4.3 h wall-clock against the wrapper's 2.5 h estimate), then the
Verification block; then three changes on its evidence — the template, the
edge gates, the prior — 88 distinct pages re-measured (86 for the fold, 057
and 149 for the edges, 005 and 084 again for the prior) and every page cut
again; then the block again. Grade
`cec3ff863b36`. No `FAILED`, no `SKEW` NOTE on any page (the residual after
levelling is ≤ 0.02° on all 200).

### The checks, final state

```
1  masters600 .png/.stamp.txt, sheets600, masters2400, cmyk2400 .tif/.colors.txt, geometry, debug600: 200/200 each
2  every master 4961 x 7016
3  worst residuals: 200.png 0.60 -- then 0.02 (163, 147, 091, 002, 133, 004, 003)
4  stale 0, chunk != sidecar 0
5  fit even S=556 B=6904 (83 pages, mean unknown 1.52 %), odd S=4416 B=6904 (62 pages, 1.79 %)
   anchor logo 145 / edges 55; fold holes 196 / colour 3 / none 1
   unknown (logo pages) even p50 1.77 % p95 2.46 %, odd p50 1.86 % p95 2.71 %
   LOOK AT: no logo -- the 55 below; no fold -- 111; unknown > 4 % -- none
6  bands with bed/prop: 001 002 003 004 005 023 027 057 067 092 104 119 147 149 151 159 163 177 187 198 199 200
   (every one an ad or cover whose own ink reads as "bed"; the prop column is <= 0.015 everywhere but p001 0.099,
   p005 0.090, p002 0.049 -- prop-coloured ink: the cover's orange banner, a yellow ad ground)
7  debug_contact.png
8  hole folds: x mm p5 7.4 p50 9.8 p95 13.4 | n == 6: 112 | template 6/5/4: 131/50/15
   LOOK AT x < 5 mm: (82, 0.9, colour), (119, 1.7, colour)
   LOOK AT n > 12: 001 002 005 014 021 024 038 041 082 160 163 177 180 187 196 199 200
```

The fit: 8609's was even S=568 B=6892, odd S=4416 B=6900; 8610's odd S is
8609's to the pixel, even S 12 px (0.5 mm) smaller, B 12 / 4 px larger — the
same layout, as the anchor argument predicted. The unknown percentiles are
8609's (1.38 / 2.30, 1.92 / 2.99) within half a point; they rose from the
first pass's 1.58 / 1.57 because 25 pages now have their real fold and the
neighbour's strip inside the window is marked, not shown. Check 3's p200 is
the back cover, art to the trim: the projection measure has no type there;
its one line of type (the health warning) reads 0.18–0.20°, and the same
measure on the levelled sheet said −0.02°, so the cover is ~0.2° off, the
scan's own skew measured on art. Accepted; the one page in the issue whose
level is not proven by its type.

### What the first pass read, and what was changed on it

The first pass fitted even S=552 B=6904, odd S=4420 B=6904; anchor logo 145 /
edges 55; fold holes 195 / colour 1 / none 4; unknown > 4 % on 027 092 149
177. The NOTE classes: `LOGO not found` 55 pages (all looked at below: every
one an ad, a cover or a form page, none with the wordmark — no false
negative, and no false positive on the three pages with a large "64'er" in
their body, p154, p159 and p191, because the search band is the foot); `EDGES
fullbleed` 9 (001 003 004 151 163 187 194 198 200); `FOLD not found` 4 (083
111 117 137); `FOLD from the neighbour's colour boundary` 1 (064, at −0.1 mm
— the frame edge); `SKEW` none.

Two classes appeared, both fixed on measurement, both in *`measure`* above
(the prior came in a review round after them, on p084's evidence):

1. **The neighbour's column as the fold** (*Which line*): 25 pages, found by
   tabulating fold x over the 200 JSONs (now check 8). The template was
   measured on 75 pages and added; `FOLD_TOL_MM` went 0.5 → 0.8 on the four
   `none` pages' evidence; `FOLD_MIN_SPAN` went. 86 pages' fold entries
   changed; all 86 re-measured.
2. **The paper trace on ink to the trim** (*The three outer edges*): 027 092
   149 177 (the four > 4 % pages) and 057; the frame gates were measured
   and added; the five re-measured.

The 112 pages no change touched were not re-measured; their
`geometry/NNN.json` was given the two new keys (`fold.template`,
`fold.template_rms_mm` from `fit_fold` over the stored candidates, asserted
to return the stored line to 1e-9; `edges.replaced = []`, asserted against
the gates) so that the schema above holds on every file. Then `masters600/`
was wiped and `cut` run over all 200.

### The pages looked at (overlay and master, 12 %; the inner 40 mm at 1/5; strips at 600 dpi where it mattered)

Right / wrong is about the master. **Wrong at the end: p111 (placement) and
p005 (the fill)**. 62 pages:

| page | what it is, what happened | verdict |
|---|---|---|
| p001 | front cover, odd, full-bleed (body 0.03): frame + prop edges; the crease cracks through the art, 25 candidates on it, template 4 at 14.3 mm; edges anchor | right |
| p002 | Computerspiel-Riesen ad, even, no wordmark; first pass locked 18 crease specks at 10.5 mm, now the six holes (template 6) at 10.0 | right |
| p003 / p004 | the inside-cover sheet, a black card of order forms, full-bleed (0.00): frame + prop; 6 holes at 12.7 / 10.3 | right |
| p005 | ad, odd, **no wordmark**, a coarse-screened picture whose left edge **is** the crease: 643 dot candidates (all at 8–16 mm — the picture; the neighbour's side is blank), 205 inliers on the line; looked at in 600 dpi strips at the three pair rows, the six holes sit on the picture's edge at 10.0–10.6 mm and the line runs through them (template 6, and with the prior its shift is on them): the fold is a measurement, 10.3 mm. The window is placed on it: the master's left edge is the picture's edge, its right edge 2.67 mm white (the outer trim is off the 217.8 mm frame). **What is wrong is the fill**: every candidate is painted white, and 518 of them are dots of the picture on the page side — 1137 mm², the picture's first ~5 mm along the whole inner edge scalloped away (55 % of the master's inner 8 mm is white); unknown 3.69 %, the sweep's highest | **wrong** — the fill, not the placement |
| p196 | its sheet-mate, even, logo 0.95; the same picture in its frame at 0–11 mm from the inner edge, 1156 candidates, 204 inliers, the six holes among them at 9.8–10.6; 102 candidate discs on its own side — the picture's ~1 mm of bleed past the fold, gutter | right |
| p009 | article, odd, logo 0.95; a satellite speck had joined the six (n=7, x 9.1); now the six, 10.5 | right |
| p010, p093, p110, p150 | controls, ordinary logo pages: 6 / 5 / 6 / 6 holes at 8.1 / 9.8 / 8.8 / 13.0 | right |
| p013 | maxell ad, odd, no wordmark; edges anchor, 6 holes at 10.2; the ad's address line sits on its trim | right |
| p014 | article, even; 22 crease specks at 7.1 → the six at 7.7 | right |
| p020 | article, even; the pair-1 holes torn in two (four specks at y 57.7–76.7) had made the six; now the five that fit the template, 6.4 mm | right |
| p021 | article, odd; 19 fragments of a picture edge at 7.1 → 4 holes at 12.2 (the other two are under the neighbour's picture) | right |
| p023 | "Profis helfen Einsteigern", an advertorial with an address foot, no wordmark; edges anchor, 6 holes at 9.7 | right |
| p024 | article, even; 34 → 37 crease specks with the holes among them, 9.0 | right |
| p027 | Murder on the Mississippi ad, purple ground to the trim, no wordmark: **top traced 27.2 mm down, bottom 15.7 mm up at −4.05°** — the window sat 8.7 mm high and the top 27 mm went white; also the fold on 22 screen specks at 9.5 instead of the holes at 7.1. Now: top from the frame, bottom from the prop, the six holes (template 6), unknown 3.18 % — the outer trim off the frame | wrong, then right |
| p041 | article, odd; the neighbour's column (27 fragments at 4.0) → 21 crease specks + the six holes at 7.8, template 6 rms 0.03 | right |
| p042 | article, even; 12 at 8.3 → 6 at 9.6 | right |
| p057 | Atari ST ad (Kasparow), no wordmark; the outer trace ran into the photo at −1.49° and the bottom at +1.15° → both from the frame / prop; 6 holes at 9.6 | right |
| p061 | listing page, odd, logo 0.97; **22 line-end fragments of the neighbour's column at 0.6 mm** (σ 0.08) beat the five visible holes at 8.5–10.4; now 5 at 9.8, template 5 | right (report was wrong) |
| p064 | Listing des Monats, even, logo 0.92; first `colour` at −0.1 mm (the frame edge, a false boundary); four holes 0.9 mm apart across the crease → at 0.8: holes n=4 template 4 at 8.2 | right |
| p067 | C64-Bibel ad, odd, no wordmark, **edges-anchored on a fold at 1.5 mm** (43 fragments) — the master was shifted 9 mm; now the six holes at 10.8 | wrong, then right |
| p082 | article, even, logo 0.89; the column (5 fragments at 0.6) beat three scattered true holes; now no hole line and the colour fallback at 0.9 mm — the neighbour's column edge again, not the fold; the master is placed by the wordmark and the window takes the strip out | right (fold x wrong, harmless) |
| p083 / p117 | article / classifieds, odd, logo 0.96 / 0.97; `fold none` at 0.5 (four holes, 0.8–0.9 across) → holes n=4 template 4 at 8.8 / 10.1 | right |
| p084 | article, even, logo 0.93; the neighbour's column, 58 inliers at 1.5 mm, template 5 rms 0.36 with its shift at 65.9 mm — the one fake the template let stand; the absolute prior (review round) refused that shift and the four true holes, collinear at 0.8 mm, are the fold at 12.9 mm, template 4 | right |
| p086 | article, even, logo 0.93; 152 fragments, the column at 1.9 → the six at 13.5 | right |
| p091 | article, odd; 36 at 0.7 → the six at 9.5 | right |
| p092 | Interface-Inclusive ad, even, no wordmark: **a red band across the top, the top traced 15.2 mm down** and the band went white; the four true holes (pairs 1+2, span 103 mm) had been refused by the span rule. Now top from the frame, holes n=4 template 4 at 7.8 | wrong, then right |
| p104, p121, p147, p175 | Data Becker / Printfor / Sybex / Epson ads, no wordmark, edges anchor; 5 / 5 / 9 / 5 holes at 8.6 / 9.9 / 11.7 / 11.6 | right |
| p109 | Bücher zu Amiga/C128 ad, odd, no wordmark, **edges-anchored on 14 fragments at 1.0 mm**; now the four holes at 10.4 | wrong, then right |
| p111 | ALI ad, odd, no wordmark, **`fold none`**: three true holes at 10.2–10.8 (the fourth is 5 mm off), six fragments at 0.7–0.9, the neighbour blank so no colour boundary; the window sits on the inner frame edge, 10.5 mm short — 10 mm of the neighbour's blank margin on the left, the ad's outer margin cut on the right | **wrong** — the known consequence of no fold and no wordmark; nothing measured it |
| p116, p118, p120, p124, p152, p154, p158 | even pages, the column at 1.4–3.1 → the holes at 14.5 / 14.3 / 14.1 / 13.9 / 12.8 / 12.9 / 11.6 (p154 edges-anchored: was 11 mm off) | right |
| p119 | classifieds, odd, logo 0.95; 33 fragments at 1.4 → no hole line, colour fallback at 1.7 mm (the column edge; harmless) | right (fold x wrong, harmless) |
| p129 | Final Cartridge ad, odd, no wordmark, edges on 12 fragments at 2.4 → the six at 11.1 | wrong, then right |
| p137 | Bildschirmtext ad, odd, no wordmark, `fold none` → the window on the frame edge, 11 mm short; at 0.8: holes n=4 template 4 at 11.2 | wrong, then right |
| p149 | printer ad, odd, no wordmark: **a black column on the outer side, the outer edge traced 13.5 mm in** and 13 mm of the ad went white (unknown 8.0 %); now the frame, unknown 0.8 % | wrong, then right |
| p159, p181, p187 | Sammelboxen ad / PLAN ad / Bard's Tale ad, odd, no wordmark, edges on the column at 0.6 / 3.2 / 2.2 → the holes at 10.2 / 13.5 / 12.8 (p187 full-bleed, 14 inliers with the holes among the art's cracks) | wrong, then right |
| p160 | Sonderhefte ad, even, no wordmark; 22 crease cracks through the blue ground, the holes among them, 12.0 | right |
| p163, p194, p198, p200 | full-bleed (0.04 / 0.08 / 0.01 / 0.005): a star-field ad, Thai Boxing, order cards on a tinted ground, the back cover; frame + prop; 69 / 6 / 6 / 35 on the crease at 10.0 / 10.2 / 12.4 / 11.0 | right |
| p174 | article, even; 18 at 6.4 → the six at 8.8 | right |
| p177 | PC-Magazin ad, odd, no wordmark: **bottom traced 16.4 mm up at −5.97°**, a wedge of the foot went white and the window sat high; top 4.9 mm at +2.93° too. Now both from the frame / prop; 31 crease specks with 4 holes, 11.5 | wrong, then right |
| p183, p185, p189, p193, p195 | odd article pages, logo; the column at 3.0 / 3.8 / 2.3 / 2.2 / 2.4 → the six at 13.2 / 13.4 / 12.4 / 12.5 / 12.5 | right |
| p191 | Programm-Service page with a 30 mm "64'er" in its body; the finder searches the foot only, edges anchor, 6 holes at 12.7 | right |
| p197 | order-form page, odd, no wordmark, 5 holes at 14.7 | right |
| p199 | S+S Soft ad, odd, no wordmark; 15 screen specks at 14.7 → no hole line (the holes are at 15.4, at the band's limit, three of them inside); colour fallback at 15.0, on the boundary of p002's art, which runs to its trim | right |

**The colour fallback, measured on this sweep:** it finds the *page-facing
edge of the neighbour's content*, which is the fold only when the neighbour
is printed to its trim (p199, its neighbour p002). With a neighbour that has
a margin it reports the neighbour's column edge, ~10 mm from the fold (p082
0.9, p119 1.7, and p064's −0.1 on the first pass). The spec's ±5 mm prior on
the issue's median fold would reject those, and `measure` has no median; the
hole fold's p5–p95 on this issue is 7.4–13.4 mm. Not changed: both pages
have the wordmark and the fallback never decided a master here.

**The 8609 reference** for the unknown percentiles stands. Two masters are
wrong at the end and the report names both: p111, the one page this variant
cannot place (no fold, no wordmark, a blank neighbour), and p005, placed
right and bitten by the fill along its inner 5 mm.

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
  a sweep. The template, `FOLD_TOL_MM` and the edge gates were measured on
  the full sweep's 200 geometry files (*What it read*), and a change to any
  of them is first replayed over those — `fit_fold` is a pure function of the
  stored candidates, and the gates of the stored lines — before a page is
  re-measured.
- A change to `MASTER_W_PX`/`MASTER_H_PX` changes every master's pixel size and
  every page-fraction downstream of it. Wipe `masters600/` and `cut` again —
  this is not a change that can be made for one page.
