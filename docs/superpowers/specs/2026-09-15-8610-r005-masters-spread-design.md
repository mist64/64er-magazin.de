# 8610 through scan2ocr: the `r005_masters_spread` variant — design

**Date:** 2026-09-15
**Goal:** publish the October 1986 monthly (`issues/8610`) from its own 2400 dpi
scans through `tools/img/scan2ocr`, the way SH8601 was — and to do that, build
the second variant of step 005, `r005_masters_spread`, which the SH8601 design
(`2026-08-21-sh8601-scan-chain-design.md` §5) explicitly deferred.

---

## 1. What exists

**The scans.** `/Volumes/S/png/8610/NNN.png`, 200 pages, no gaps, ~20 400–21 000
× 28 751 px (~2400 dpi, 8.5–8.75 × 11.98 in), ~900 MB each, 8-bit RGB. Beside
them `thumb/` (200 pages at 150 dpi, 1312 × 1797) and two logs of the rotation
and thumb passes. **Never written to.** No `colors.txt` — the grade uses the
built-in anchor set (decided: `colors: null`, as 8609).

**The chain.** `tools/img/scan2ocr/rules/rNNN_*`, driven per
`r000_orchestration.md`. One issue descriptor, `issues/<ID>/issue.json`, read by
`r000_issue.py`; one constant `ISSUE` selects the issue for every step.

**Step 005 today.** Only `r005_masters_sheet.{py,md}` exists (SH8601, loose
torn sheets). 8609's masters were made by the retired `tools/img/scan2mrc`
(skew → holes → spine → stack → logo → clear → window → geom → mrcpipe), which
is hardcoded to `/Users/mist/DNB/8609`, needs 600 dpi thumbs and a Rust build,
and which scan2ocr must not reference. Its **measurements** are the input to
this design; its code is not reused.

**Stale things found on the way, fixed as part of this work:**

- `r005_masters_sheet.md` describes two renders, an OCR curve and page refusal;
  commit `7b9aa90b` removed all three from the `.py` (one uncurved master, GCR
  undone, every page published with notes). The spec is brought back in line
  before it is used as the model for the spread spec.
- `issues/SH8601/issue.json` points at `/Users/mist/DNB/SH8601`, which no longer
  exists; the scans are at `/Volumes/S/png/SH8601`. `issues/8609/issue.json`
  names `masters600` at `/Users/mist/DNB/8609/tmp/master600/final`; they are at
  `/Users/mist/DNB/8609/final`. Both descriptors are corrected.
- No Python on this machine has numpy + scipy + pillow together (`/usr/bin/python3`
  is 3.9 with numpy and PIL only; the repo `.venv` and the homebrew 3.12–3.14
  installs are empty). A fresh `.venv` on 3.12 with `numpy scipy pillow
  anthropic` is set up inline before anything runs.

## 2. What the scans are — measured on the thumbs, not assumed

Same physical form as 8609. The magazine was disbound into **A3 sheets**, held
in a rigid 6-hole binder clip, and each sheet scanned twice — one A4 half per
frame, with some overlap. So every frame holds:

| region | what | measured (150 dpi thumbs, pages 10/11/50/51/100/101/150/151/199/200) |
|---|---|---|
| top | a grey bed strip | mean RGB ~(130–190, …), lum ~130–185 — NOT the near-black bed of SH8601 (`BED_LUM` 70 does not see it; the paper-distance mask does) |
| bottom | the yellow prop | (250, 218, 113), ~40 px = ~7 mm deep |
| outer side | usually **off-frame** — paper runs to the frame edge | border strip reads paper (190–210) on most pages |
| inner side | the **fold**, then the neighbour half of the same sheet | p100 ↔ p101 is the centre spread; neighbour is blank margin on some pages, content on others |
| on the fold | **6 clip holes** — 3 vertical pairs, ~0.6 mm, dark teardrops | visible on p100 at thumb scale, in a tight column on a faint crease |

Sheet pairing is `k ↔ 201−k`. Parity: **even page → neighbour on the RIGHT,
odd → LEFT** (same as 8609).

Consequences:

- There is no torn fringe and no paper edge on the inner side; the sheet
  variant's inner-edge logic has no input. The inner boundary is the fold.
- The outer trim is often not in the frame, so a trace-based page box would be
  a lower bound on the page there. That, and print-to-trim registration, is why
  the master is anchored on the **printed wordmark** and not on the paper —
  decided: the 8609 geometry (logo-anchored exact A4) rather than the sheet
  variant's traced-trim canvas.
- Everything else the sheet variant does — skew, grade, stamps, the debug
  overlay, "publish and NOTE, never refuse" — transfers unchanged.

## 3. Design

### 3.1 One program, two phases

The window offsets are an **issue-wide fit** over per-page anchors, so the
step cannot be one pass per page. Two sub-commands, positional, no flags:

```
r005_masters_spread.py measure [pages…]   # per page, heavy, parallel (~45 s/page)
r005_masters_spread.py cut                # issue-wide: fit the window, cut every master
r005_masters_spread.sh                    # measure over all pages (xargs -P), then cut
```

`measure` is idempotent per page and is what a code change to the geometry or
grade re-runs. `cut` is cheap (seconds per page, reads `sheets600`) and is
re-run alone after a change to the fit or the fills.

### 3.2 `measure` — per page

1. **Skew** on the 150 dpi thumb; rotate the 2400 scan; re-measure the
   residual on the reduced page, re-level once if over `SKEW_RESIDUAL_MAX`.
   Verbatim from the sheet variant.
2. **Grade** the whole levelled sheet — separate with `cmyk_reconstruction`,
   undo its GCR, ICC to AdobeRGB — and write `masters2400/NNN.png`,
   `cmyk2400/NNN.tif` + `NNN.colors.txt`, `sheets600/NNN.png` (a 4:1 reduce).
   Verbatim from the sheet variant. One grade, uncurved.
3. **Geometry**, on the levelled 600 dpi sheet, written to `geometry/NNN.json`:
   - **top, bottom, outer edge** — `trace()` on the paper-vs-backing boundary,
     band medians, exactly the sheet variant's clean-edge path. Backing = the
     paper-distance mask's complement (grey bed) OR `prop_mask` (yellow). An
     off-frame outer edge traces as the frame edge (constant samples), which
     the sheet variant already treats as "the scan does not contain the trim".
   - **fold** — from the clip holes. Candidates: dark blobs (local-contrast
     threshold, as `clip_holes.py` established) inside the inner 25 mm band,
     0.4–2 mm across, filled and roughly round (rejects rules, type, the
     neighbour's edge). Score candidate columns against the **rigid 3-pair
     template** (the clip is rigid; the relative y-spacing is a constant of the
     issue, calibrated once from the confident pages, the column x and a global
     y offset vary per page) and penalise columns with many non-template blobs
     (photo texture). Accept with ≥4 holes on a line, residual ≤0.3 mm,
     |tilt| ≤1°. **Fallback:** the neighbour-content boundary — per-band
     dark-fraction/saturation step nearest the inner border, Theil–Sen line,
     ≥6 bands, residual ≤ 45 px@600, |tilt| ≤1.5°, and within ±5 mm of the
     issue-median fold offset. **Neither:** `fold: null`, no inner cut, NOTE.
     The source (`holes` / `colour` / `none`) is recorded.
   - **logo anchor** — normalised cross-correlation of `template_64er_600.png`
     (copied from scan2mrc into `rules/`, so the directory stands alone) over
     the outer-bottom corner of the sheet; parity decides which corner. Accept
     at confidence ≥ 0.8 (8609: p50 0.95 on 129/176). Else `anchor: null`.
   - **holes** — the accepted hole blobs' bounding discs, for the fill in `cut`.
4. **Debug overlay** `debug600/NNN.png` at 1/5 scale: traced edges green,
   fold magenta, holes circled, logo box, and the page's notes as text.

Every measurement is a number in the JSON; nothing is decided here.

### 3.3 `cut` — issue-wide

1. Read every `geometry/*.json`. **Fit one (S, B) per parity** — the anchor's
   offset from the window's left and top edge — minimising the **unknown**
   fraction inside the 210 × 297 mm window (bed, prop, beyond the fold, off
   the frame) over the pages that have their own logo. The same objective as
   8609's `fit_window.py`; the search spans the whole page width (8609's
   capped range pinned the odd-page optimum to its own boundary).
2. **Pages without a logo:** anchor = fold x and top-trim y, both measured on
   that page — physical page edges, not an interpolation from neighbours whose
   placement on the scanner is unrelated. Source recorded in the stamp.
3. **Per page**, on `sheets600/NNN.png`: everything outside the page — beyond
   the fold, outside the traced top/bottom/outer edges, off the frame — and the
   hole discs are set to **255 white**, then the window is cut. Where the window
   overhangs the frame the overhang is white. The fill is fabrication and is
   stated as such in the rule, exactly as the sheet variant states it.
4. Write `masters600/NNN.png`, **4961 × 7016 px, every page**, with the `r005`
   tEXt chunk and `NNN.stamp.txt`: grade sha, skew, edges, fold source and
   tilt, hole count, anchor source and confidence, S/B, unknown % in window,
   notes. Write `geometry/fit.json`: the offsets, per-parity unknown p50/p95,
   the page lists by anchor source.

### 3.4 Shared code: `r005_masters.py`

The sheet variant cannot be imported — it loads the descriptor at import and
`SystemExit`s when `binding != "sheet"`. The parts both variants need move to
`r005_masters.py` (no suffix: the step's library, not a third variant):
profile reading and the built-in anchors, `stamp_text` and the grade sha,
`measure_skew`, `paper_mask` / `prop_mask`, `trace`, `separate_and_render`,
`undo_gcr`, `archive_cmyk`, `save_master`. Constants keep their names and
comments. Each variant keeps its own edge finders, page classes and `process`.

**Gate:** two SH8601 pages (041, 056) rendered from `/Volumes/S/png/SH8601`
before and after the extraction are **byte-identical** in `masters600`. The
sheet variant's behaviour does not change; only where its functions live.

### 3.5 The descriptor

```json
{ "id": "8610", "kind": "monthly", "binding": "spread", "pages": 200,
  "scan_dir":  "/Volumes/S/png/8610",
  "thumb_150": "/Volumes/S/png/8610/thumb",
  "tmp":       "/tmp/64er_8610",
  "colors":    null,
  "pdf":       "64er_1986-10.pdf" }
```

`/tmp/64er_8610` is accepted knowing it is cleared on reboot; the output is
~2–2.5 GB per page (`masters2400` + `cmyk2400`), ~450 GB of 712 free.

## 4. Outputs

```
<tmp>/masters600/NNN.png        the master r010 OCRs and r145 cuts from   (the contract)
<tmp>/masters600/NNN.stamp.txt  the stamp, readable without decoding the PNG
<tmp>/sheets600/NNN.png         the levelled, graded, UNCUT sheet at 600 dpi
<tmp>/masters2400/NNN.png       the same at 2400
<tmp>/cmyk2400/NNN.tif          the separation, + NNN.colors.txt
<tmp>/geometry/NNN.json         every measurement `cut` reads
<tmp>/geometry/fit.json         the window fit
<tmp>/debug600/NNN.png          the overlay the user reviews
```

## 5. Verification (the `.md`'s block, runnable)

1. 200/200 of every artefact present, nothing else.
2. Every master is 4961 × 7016.
3. Residual skew of every master re-measured ~0.
4. Every stamp carries the current grade sha; chunk == sidecar.
5. Unknown-in-window p50 / p95 per parity from `fit.json`; the 8609 figures
   (even 1.38 / 2.30 %, odd 1.92 / 2.99 %) are the reference.
6. Fold source tally: holes / colour / none, with the `none` pages listed for
   a look at `debug600`.
7. Logo tally: found / fallback, listed.
8. No bed and no prop in a 6 mm band inside the traced edges, measured on
   `sheets600` (uncurved), read off the stamp's boxes.
9. A contact sheet of `debug600/` for the eye.

## 6. Out of scope

- Re-rendering 8609's masters with this variant. They exist and the corpus was
  measured on them.
- The issue PDF and `pubdate.txt` — publishing decisions, as for SH8601.
- Steps 010–330 for 8610: run per `r000_orchestration.md` once 005 is verified;
  nothing in them is designed here.
