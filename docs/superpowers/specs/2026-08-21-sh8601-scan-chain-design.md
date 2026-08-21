# SH8601 through a self-contained scan2ocr — design

**Date:** 2026-08-21
**Goal:** publish the Sonderheft 1/86 (`issues/SH8601`) as per-article HTML plus
figure PNGs, from its own 2400 dpi scans, the way `issues/8609` is published —
and in doing so make `scan2ocr` self-contained, parameterised by issue rather
than hardcoded to 8609.

---

## 1. What exists

**The scans.** `/Users/mist/DNB/SH8601/master_2400/SH8601/NNN.png`, 152 pages,
no gaps, ~20050x28751 px (~2400 dpi), ~800 MB each. Beside them: `thumb/`
(152 pages at 150 dpi), `colors.txt` (this issue's ink profile), and
`widths.txt` — **dead**, it belongs to the retired `ALL*.sh` route and nothing
in the current chain reads it.

**The chain.** `tools/img/scan2ocr/rules/rNNN_*` — `r010` OCR to measured
blocks, `r020` classify, `r030` assemble to one `.md`, then `r040`–`r320`
editorial steps to published HTML. It is driven per `r000_orchestration.md`.

**What is NOT ours any more.** `tools/img/scan2mrc/` is the old pipeline. Every
rule must be self-contained in `scan2ocr`; scan2ocr must not reference it.

**Already deleted.** `issues/SH8601/SH8601.md`, an untrusted PDF-OCR of this
issue (commit `2c9a92f9f`). `issues/SH8601/REPRINTS.md` keeps its one useful
residue — which articles are claimed reprints of monthlies — as unverified
leads.

## 2. What the scans actually are — measured, not assumed

The sheets were **torn off a glued spine**, one A4 sheet per scan. Measured:

| | |
|---|---|
| residual skew | up to **1.08 deg** (`092`), typically 0.1-0.7 deg — the pages are NOT levelled |
| edge tilt AFTER levelling on text | 0.14-1.12 deg — the sheet was guillotined at its own angle, so paper edges are NOT parallel to the type |
| page width | varies **1254-1288** px at 150 dpi between scanning batches |
| outer edge | guillotine-clean, straight, hard contrast against a near-black bed |
| inner edge | **torn**: a fringe of fibres standing proud of the paper body, wandering down the page |
| torn side | follows parity — verso tears on the right, recto on the left (checked on 040/041) |
| below the sheet | black bed, and a saturated **yellow prop** further out; both far from paper white |
| bed band | bottom 35-59 px, right/left 1-44 px at 150 dpi, varying per page |

Consequences, stated because each one killed a simpler design:

- Skew of 0.5 deg is ~44 px of drift across a 600 dpi page width. `r010`'s
  column and gap geometry is built on straight text. **Deskew is required.**
- The inner edge cannot be fitted as a line, because it is not one.
- There are **no binder-clip holes and no neighbour page in frame**. The 8609
  inner-boundary method (colour boundary against the facing page, clip holes as
  fallback) has no input here, and hole inpainting has nothing to fill.
- Levelling the text leaves the paper edges tilted, so an axis-aligned crop
  inscribed in the page gives up **0.5-3.6 mm per edge** (measured on 041, 056,
  092). The edges are therefore TRACED as lines, and what falls outside them is
  filled with paper white. Cropping to them was tried first and cost too much.
- The two torn sides are not the same problem. On a **verso** the tear sits
  inside the frame and wanders: it must be traced. On a **recto** the tear is
  flush with the frame edge: a few px cut perfectly vertically is always enough,
  and a fitted line there fits noise (it claimed +0.62 deg on p041).
- Paper white is **uniform across the sheet** (3x3 grid of paper p90 varies by
  <=4 levels): there is no vignette to correct. The cast is global, R/B 1.163.

## 3. Design

### 3.1 The issue descriptor

One file per issue, `issues/<ID>/issue.json`, read by every step:

```json
{ "id": "SH8601", "kind": "sonderheft", "binding": "sheet", "pages": 152,
  "scan_dir": "/Users/mist/DNB/SH8601/master_2400/SH8601",
  "thumb_150": "/Users/mist/DNB/SH8601/master_2400/SH8601/thumb",
  "tmp":       "/Users/mist/DNB/SH8601/tmp",
  "colors":    "/Users/mist/DNB/SH8601/master_2400/SH8601/colors.txt",
  "pdf":       "64er_Sonderheft_1986-01.pdf" }
```

`colors` is **optional**. Absent, the grade uses the built-in anchor set (the
eight RGB anchors the old separation compiled in), so an issue without a
measured profile still renders.

scan2ocr keeps its "constants at the top of the file, no CLI knobs, no env
knobs" convention: each program gets **one** constant, `ISSUE = "SH8601"`, and
derives every path from the descriptor. This replaces five hand-edited absolute
paths (`r010:51,52`, `r020_classify:35`, `r020_evaluate:46,47`,
`r020_collect:24`).

### 3.2 Step 005 — scan to 600 dpi master, in two variants

New first step, inside scan2ocr, owning everything between the raw scan and
`r010`'s input. It exists in **two mutually exclusive variants**, selected by
`binding`:

| variant | for | inner boundary |
|---|---|---|
| `r005_masters_spread` | the frame holds a clipped SPREAD (8609, the monthlies) | facing-page colour boundary, clip holes as fallback, holes inpainted |
| `r005_masters_sheet` | the frame holds one loose SHEET (SH8601) | the torn fringe: traced on a verso, a flush vertical cut on a recto |

**The suffix names the variant, it is not an insertion.** `r000_orchestration.md` must
say this explicitly, because this directory's history has suffixes (`9b`) as the
symptom of bad numbering. Here the two variants are alternatives at ONE step,
chosen by the descriptor, never a step inserted after another. Exactly one variant runs for a given issue; the other
is recorded in `LOG.md` as not applicable. Both write the same contract:

```
<tmp>/masters600/NNN.png   — 600 dpi, levelled, cut, graded, one per page
```

`r010` and `r145` read that directory and are otherwise untouched.

**`r005_masters_sheet`, the path we build now.** Prototyped and verified on
pages 006, 041, 056, 092 (prototype: `trace.py` in the session scratchpad):

```
scan_dir/NNN.png
  -> measure skew on the 150 dpi thumb (projection variance; scale-invariant)
  -> rotate to level, then VERIFY residual ~0            [see the sign trap below]
  -> paper mask: distance from the colors.txt paper white
  -> TRACE each edge as a line, robust:
       clean edges  -> band medians of the per-row/col paper boundary
       verso fringe -> band 5th percentile of per-row paper ends
       recto fringe -> NOT traced: one vertical line, p95 of paper starts + ~1 mm
  -> fill everything outside the traced page with paper white
  -> drop bed components that touch the frame AND lie mostly outside the page
  -> separate to CMYK with tools/img/cmyk_reconstruction (see 3.3)
  -> two renders: an OCR master and an unclipped figure master
  -> masters600/NNN.png (+ the CMYK archival form)
```

Traps, each one paid for during the prototype:

- **The rotation sign.** scipy (which measures) and PIL (which applies) rotate in
  opposite directions. Applying the measured sign DOUBLED the skew to -1.28 deg
  on p056. The rule must re-measure residual skew and assert it is ~0.
- **Per-column extremes are not an edge.** "Last paper row in this column" is
  dragged out by a few paper-coloured pixels in the bed transition and left
  **3.8 mm of bed** at the foot of p056. Clean edges come from the row/column
  paper FRACTION; only the fringe is per-row.
- **Rows that cross full-bleed art are not edge samples.** Their "last paper
  pixel" collapses inward and tilted p056's traced fringe by +2.56 deg. Drop
  samples more than ~12 mm off the median before fitting.
- **A bed flood must not eat a photo.** p006's board picture bleeds into the torn
  edge and connects to the bed through its own black chips; an unconstrained
  connectivity pass erased a third of it. A component is only dropped if MOST OF
  IT lies outside the traced page.

**Accepted loss, decided explicitly:** where the tear ran into the type area,
those characters are gone. Accepted — it is a fact about this copy.

**Closed:** the p092 corner sliver, and a band of prop at the foot of several
pages. Both had one cause -- the yellow prop is (237,205,111), city-block
distance **108** from the old paper white, INSIDE the 110 threshold, so the paper
mask counted the prop as paper. A hue test separates them (G-B is 11-26 on
paper, 99-107 on the prop). Fixing it also moved the traced pages from ~210x301
to **true A4, 210x297**.

**Three sheet classes, not one.** The size gate must know them apart:

| class | pages | edge finding |
|---|---|---|
| interior A4 sheet | 003-148 | paper vs bed |
| A3 cover sheet, full bleed | 001 (218 mm), 002 (224 mm) | **no paper visible** -- ink vs bed |
| bound-in payment card, blue stock | 149-152 (~143 x 204 mm) | its own window |

(117 measures 163 x 278 and is still to be classified.)

**Gate:** the torn side must match parity on all 152 pages. It is measurable on
the thumbs (the torn side has high variance in where paper starts down the
column; the cut side has almost none). A disagreeing page is misfiled or
mis-rotated, and finding that after a full-res sweep is expensive.

### 3.3 The grade — reuse the CMYK converter, render twice

`tools/img/cmyk_reconstruction/` already does the hard part, and `colors.txt` was
written for it: 8 RGB anchors (W C M Y R G B K) plus 4 per-ink level lines. It
works in the DENSITY domain -- `d = -log10(rgb/W)`, six polynomial features, a
least-squares solve against the seven ink targets, then full GCR
(`K = min(C,M,Y)`, subtracted from each). Because the paper white is the density
reference, the global R/B 1.163 cast falls out for free.

Measured on p056, same traced page:

| grade | paper p50 | pure white | ink p50 | crushed |
|---|---|---|---|---|
| naive linear map | 254,253,251 | 56% | 20,9,8 | 3.8% |
| CMYK + colors.txt levels | 255,255,255 | 88% | 71,69,70 | 0% |
| CMYK, levels neutralised | 254,254,251 | 65% | 66,66,71 | 0% |

Two conclusions:

- **The level lines in SH8601's `colors.txt` are not usable as written.**
  `LK 90 95` maps K's 229-242 window onto the full range, so ordinary black text
  falls below the low point and is clipped toward zero ink; it also snapped 88%
  of the page to pure white. They must be re-measured per issue and proven.
- **Ink at ~66 is not a bug, it is honesty.** 100% SWOP black is not RGB 0. The
  naive map's 20,9,8 is a contrast boost.

The two consumers want different images, so the step renders both from ONE
separation:

| render | for | wants |
|---|---|---|
| `masters600/NNN.png` | `r010` OCR | contrast: type to black, paper to white. Clipping is a feature |
| the unclipped ICC render | `r145` figure cuts | fidelity: no clipped highlight, no crushed shadow |

**The measured profile, 2026-08-21.** Both of `colors.txt`'s halves were wrong,
and in the same direction: the file described paper cleaner than this paper is.
The values as found are kept beside it as `colors_asfound.txt`.

- **White point `W 214 195 186` -> `209 175 157`.** `W` is the DENSITY
  REFERENCE: everything is `-log10(rgb/W)`, so paper lighter than `W` clamps to
  zero ink and paper darker than it **is reported as ink**. Clean paper measures
  `217 192 179` at p50 and `209 175 157` at its yellowed 5th percentile, so the
  old anchor -- bluer than the paper -- forced the solver to explain the gap as
  yellow ink. That was the yellow in the corners. Taking the yellowed end as the
  reference puts corner paper at 255,255,255 (corner pure-white 50% -> 72% on
  p006) and costs one level of ink.
- **Levels `LC 50 90 / LM 30 70 / LY 30 70 / LK 90 95` -> `LC 5 100 / LM 4 100 /
  LY 5 100 / LK 3 100`.** The `high` points are all 100 because nothing measures
  below full: the anchors round-trip to C 255, M 255, Y 249, K 245. The `low`
  points are the p99 of that ink over bare INTERIOR paper (the aged rim is
  browner and must never set them).

**The OCR curve: `-level 30%,100%`, ONE ISSUE-WIDE CONSTANT.** Never per page --
every page of an issue gets the same numbers. Chosen on the WORST page:

| level | glyph p50, 006 / 041 / 056 / 092 | paper p50 |
|---|---|---|
| none | 69 / 54 / 53 / 72 | 255 / 255 / 255 / 254 |
| 25% | 14 / 1 / 0 / 18 | 255 / 255 / 254 / 254 |
| **30%** | **1 / 0 / 0 / 4** | 255 / 255 / 254 / 254 |
| 35% | 0 / 0 / 0 / 0 | 255 / **254** / 254 / 254 |

25% was tuned on the easiest page and left two pages grey at 14 and 18. At 35%
paper starts coming down, which is the curve eating paper rather than blur.

**A master must record the profile that made it.** Three of the four test
masters were silently stale after the profile changed, and it took a human
eye noticing yellow edges to catch it. The per-page report carries the profile
path, its anchors, its levels and the OCR constant.

### 3.4 `kind` drives the editorial steps

Every `rNNN_*.md` gains an `Applies to:` header — `all` / `monthly` /
`sonderheft`. A step whose kind does not match is **recorded in `LOG.md` as
"not applicable — kind"**: a verified outcome, never a silent skip.

Classified by reading all 32 rules. **Three of them corrected my first pass**,
and the evidence is recorded in each rule's own header:

| rule | verdict | why |
|---|---|---|
| `r200_leserforum` | monthly | no Sonderheft has one: zero `article class="qa"` across `SH85*` |
| `r220_index_meta` | monthly | the Jahresinhaltsverzeichnis CSVs are keyed by monthly `YYMM`; **0** Sonderheft rows. 7 of 8 published Sonderhefte carry no `index_category`; `SH8501`'s 27 look mis-routed off monthly `8501` |
| `r240_rubric_banners` | monthly | all three banners are monthly rubrics; no Sonderheft carries a rubric banner |
| `r300_fehlerteufelchen_errata` | **all — my spec was WRONG** | it does not build a rubric, it applies errata printed in LATER monthlies to this issue, and later monthlies corrected Sonderheft articles too: **26** articles across `SH8501`-`SH8508` already carry the aside. Marking it monthly would have silently dropped that |
| everything else | all | |

**No rule is `sonderheft`-only** — an honest outcome. Nothing in the editorial
chain exists only for a Sonderheft; the Sonderheft-specific work is step 005,
selected by `binding`, not by `kind`.

`r210_head_meta` stays `all` despite my "no department running heads" claim:
Sonderhefte do print running heads and the corpus captures them (`SH8507` has
`head1` on 27 of 28 articles). Whether SH8601's print has them is a per-page
fact the rule already tests for, not a kind fact.

`r100_toc_category` and `r030_assemble` take their facts from the descriptor and
from the issue's own TOC instead of from 8609. In `r030` the compiled-in
`TOC_PAGES = (6, 7)` is replaced by discovery from step 020's own `toc` labels —
with two traps handled: the cover is labelled `toc` (display type), and 8609's
p171 back-matter index outscores the real contents pages 7973 to 2129, so
neither "highest score" nor a plain threshold works.

### 3.5 Cutting scan2mrc loose

Seven sites reference it. Renames are not enough at two of them:

| file | line | action |
|---|---|---|
| `README.md` | 9, 43, 80 | rewrite: the input is `r005`, not a sibling tool |
| `rules/r010_ocr_blocks.md` | 14 | same |
| `rules/r010_ocr_blocks.py` | 5, 51, 54 | docstring, `SRC_DIR`, the dpi note |
| `rules/r020_evaluate.py` | 46 | `SRC_DIR` |
| `rules/r145_extract_figures.py` | 487 | **copy the press-physics paragraph into scan2ocr's own `FINDINGS.md`** and point there |
| `rules/r000_verify_numbering.sh` | 80-81 | the staging check becomes "nothing from `issues/` is staged" |
| `rules/r020_classify.py` | 304 | comment refers to `thumbs_150`; say what `r005` produces |

### 3.6 Reprints

Seven of this issue's articles are claimed reprints of monthlies
(`REPRINTS.md`). They are **OCR'd and built like every other article** —
nothing is copied from the monthly's HTML.

New final step, `r330_reprint_compare`: after the issue is built, diff each
reprint against its published monthly. Two independent transcriptions of the
same printed text disagree exactly where one of them mis-transcribed, so the
diff finds **our** errors on both sides.

The two versions are **not required to agree** — the magazine re-set and
re-edited reprints. And **errors printed in the magazine STAY**; the comparison
never "fixes" the source.

## 4. Verification

| gate | what it proves |
|---|---|
| 8609's block index and published corpus unchanged through `r010` | the descriptor refactor and `r005A` changed no conclusion. Geometry may differ by a pixel; conclusions may not. |
| torn side matches parity, 152/152 | the issue is correctly filed and rotated |
| every page yields a `masters600/NNN.png` at the expected size | no silent drop |
| `r000_verify_numbering.sh` passes, and no `scan2mrc` string remains under `scan2ocr/` | self-containment |
| `r310_issue_invariants.py`, `r320_coverage_check.py` | as for any issue |

## 5. Out of scope, named so it is not forgotten

- **The issue PDF.** `generate.py` warns and continues without one
  (`generate.py:616`). 8609's came from the old MRC route, whose renderer was
  deleted. `tools/img/issue_pdf/` exists; wiring it up is separate work.
- **`r005_masters_spread`.** Written as a spec and a home for the clipped path,
  but the monthlies already have their masters. Implementing it is not needed to
  publish SH8601.
- **`pubdate.txt` for SH8601.** A publishing decision, not a pipeline one.
