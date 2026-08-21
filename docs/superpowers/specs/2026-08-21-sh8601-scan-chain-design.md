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

## 3. Design

### 3.1 The issue descriptor

One file per issue, `issues/<ID>/issue.json`, read by every step:

```json
{ "id": "SH8601", "kind": "sonderheft", "binding": "glued", "pages": 152,
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
| `r005A_masters_clipped` | clip-bound issues (8609 and the monthlies) | facing-page colour boundary, clip holes as fallback, holes inpainted |
| `r005B_masters_glued` | glued issues (SH8601) | the torn fringe, cut inward by a fixed margin |

**The letter suffix means variant, not insertion.** `r000_orchestration.md` must
say this explicitly, because this directory's history has letters (`9b`) as the
symptom of bad numbering. Exactly one variant runs for a given issue; the other
is recorded in `LOG.md` as not applicable. Both write the same contract:

```
<tmp>/masters600/NNN.png   — 600 dpi, levelled, cut, graded, one per page
```

`r010` and `r145` read that directory and are otherwise untouched.

**`r005B`, the path we build now:**

```
scan_dir/NNN.png
  -> measure skew (projection variance on the 150 dpi thumb; scale-invariant)
  -> rotate to level
  -> classify every edge: paper / bed / prop   (paper is warm-light, bed near-black,
                                                prop saturated yellow — all far apart)
  -> outer, top, bottom: cut at the clean edge, a small fixed margin inside
  -> inner: find the fringe, cut INWARD BY A FIXED MARGIN
  -> grade (colors.txt when named, built-in anchors otherwise)
  -> 8:1 reduce to 600 dpi
  -> masters600/NNN.png
```

The fringe is reduced to one x per page from the per-row paper-start
distribution (a high percentile, not the extreme — one stray fibre must not move
the cut), then the fixed margin is applied inward from it.

**Accepted loss, decided explicitly:** on pages where the tear ran deep, the
fixed margin cuts into printed gutter. Those characters are gone. This is
accepted — it is a fact about this copy, and no re-render recovers it.

**Gate:** the torn side must match parity on all 152 pages. It is measurable on
the thumbs (the torn side has high variance in where paper starts down the
column; the cut side has almost none). A disagreeing page is misfiled or
mis-rotated, and finding that after a full-res sweep is expensive.

### 3.3 `kind` drives the editorial steps

Every `rNNN_*.md` gains an `Applies to:` header — `all` / `monthly` /
`sonderheft`. A step whose kind does not match is **recorded in `LOG.md` as
"not applicable — kind"**: a verified outcome, never a silent skip.

First pass: `r200_leserforum` and `r300_fehlerteufelchen_errata` are
monthly-only. `r100_toc_category` and `r030_assemble`'s department /
running-head logic take their facts from the descriptor instead of from 8609.

### 3.4 Cutting scan2mrc loose

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

### 3.5 Reprints

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
- **`r005A`.** Written as a spec and a home for the clipped path, but the
  monthlies already have their masters. Implementing it is not needed to publish
  SH8601.
- **`pubdate.txt` for SH8601.** A publishing decision, not a pipeline one.
