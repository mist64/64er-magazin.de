# r005_masters_spread Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the clipped-spread variant of scan2ocr step 005 and run it over all 200 pages of issue 8610, producing logo-anchored exact-A4 600 dpi masters at `/tmp/64er_8610/masters600/`.

**Architecture:** One program `r005_masters_spread.py` with two positional phases: `measure` (per page, heavy: skew, grade, geometry JSON, debug overlay) and `cut` (issue-wide: fit one (S, B) window offset per parity over the logo anchors, then cut every master off `sheets600` with paper-white fills). The code both variants share — profile, stamp, skew, masks, tracing, the grade — moves to `r005_masters.py`, and the sheet variant imports it (gate: byte-identical SH8601 masters).

**Tech Stack:** Python 3.12 (`.venv`), numpy, scipy, pillow, pytest; `magick` (ImageMagick 7); `tools/img/cmyk_reconstruction` (Rust, already built).

**Spec:** `docs/superpowers/specs/2026-09-15-8610-r005-masters-spread-design.md`

## Global Constraints

- Never write under `/Volumes/S/png` (the 2400 dpi inputs). Temps go to `/tmp/64er_<ID>` (the descriptor's `tmp`) or the session scratchpad.
- scan2ocr conventions (`tools/img/scan2ocr/README.md`, `rules/r000_orchestration.md`): constants at the top of each file, heavily commented, in millimetres where they describe paper; **no CLI flags, no env knobs**; every `rNNN_*.md` has an `Applies to:` line and a runnable `## Verification` block; **`rules/` may contain only `rNNN_name.{md,sh,py}`** (`r000_verify_numbering.sh` check 1), so the logo template and the tests live in `tools/img/scan2ocr/`, not in `rules/`.
- scan2ocr must not reference `tools/img/scan2mrc` (self-containment). Copy what is needed; cite the measurement, not the file.
- Every master is 4961 × 7016 px (210 × 297 mm at 600 dpi), one `r005` tEXt chunk + `NNN.stamp.txt` beside it.
- The step never refuses a page: it measures, publishes, and NOTEs (7b9aa90b). The only fatal condition is a missing input file.
- Commits: explicit pathspecs, never `git add -A`; message trailer per the session's attribution lines.
- Python for every run: `.venv/bin/python` (Task 1 creates it). Run programs from `tools/img/scan2ocr/rules/` so sibling modules import by bare name.

---

## File structure

| file | responsibility |
|---|---|
| `tools/img/scan2ocr/rules/r005_masters.py` | **new, shared library**: profile + built-in anchors, grade sha, `stamp_text`, `PageFailed`, `measure_skew`, `paper_mask`/`prop_mask`, `_edges`/`boundaries`/`box_open`/`trace`, `separate_and_render`/`undo_gcr`/`archive_cmyk`/`save_master`, `tilt`. Loads the descriptor; does NOT check `binding`. |
| `tools/img/scan2ocr/rules/r005_masters_sheet.py` | existing; loses the moved code, imports it. Behaviour unchanged. |
| `tools/img/scan2ocr/rules/r005_masters_sheet.md` | existing; brought in line with the `.py` (one master, no curve, no refusal). |
| `tools/img/scan2ocr/rules/r005_masters_spread.py` | **new variant**: spread constants, `measure` and `cut` phases, edge/fold/logo finders, window fit, fills. |
| `tools/img/scan2ocr/rules/r005_masters_spread.sh` | **new**: `measure` over all pages in parallel, then `cut`. |
| `tools/img/scan2ocr/rules/r005_masters_spread.md` | **new**: the rule, with `Applies to:`, the procedure, and the Verification block. |
| `tools/img/scan2ocr/template_64er_600.png` | **new**: the wordmark template (copied from `scan2mrc/03-crop/`). |
| `tools/img/scan2ocr/tests/test_r005_spread.py` | **new**: pytest unit tests on synthetic images for the pure functions. |
| `issues/8610/issue.json` | **new** descriptor. |
| `issues/SH8601/issue.json`, `issues/8609/issue.json` | path fixes. |
| `tools/img/scan2ocr/README.md` | one paragraph: the two variants and the two phases. |

---

### Task 1: Environment and descriptors

**Files:**
- Create: `issues/8610/issue.json`
- Modify: `issues/SH8601/issue.json`, `issues/8609/issue.json`
- Create: `.venv/` (ignored by git)

**Interfaces:**
- Produces: `.venv/bin/python` with numpy, scipy, pillow, pytest, anthropic; `r000_issue.load("8610")` resolving.

- [ ] **Step 1: Build the venv (inline — the user sees the output)**

```bash
cd /Users/mist/Documents/git/64er-magazin.de
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install --quiet numpy scipy pillow pytest anthropic
.venv/bin/python -c "import numpy, scipy, PIL, pytest; print(numpy.__version__, scipy.__version__, PIL.__version__)"
```
Expected: three version strings, no traceback.

- [ ] **Step 2: Write the 8610 descriptor**

`issues/8610/issue.json`:
```json
{ "id": "8610", "kind": "monthly", "binding": "spread", "pages": 200,
  "scan_dir":  "/Volumes/S/png/8610",
  "thumb_150": "/Volumes/S/png/8610/thumb",
  "tmp":       "/tmp/64er_8610",
  "colors":    null,
  "pdf":       "64er_1986-10.pdf" }
```

- [ ] **Step 3: Fix the stale descriptors**

`issues/SH8601/issue.json` — scans moved to the S volume, the old tmp is gone:
```json
{ "id": "SH8601", "kind": "sonderheft", "binding": "sheet", "pages": 152,
  "scan_dir":  "/Volumes/S/png/SH8601",
  "thumb_150": "/Volumes/S/png/SH8601/thumb",
  "tmp":       "/tmp/64er_SH8601",
  "colors":    "/Volumes/S/png/SH8601/colors.txt",
  "pdf":       "64er_Sonderheft_1986-01.pdf" }
```
`issues/8609/issue.json` — only `masters600` changes: `"/Users/mist/DNB/8609/final"`.

- [ ] **Step 4: Verify all three resolve**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python r000_issue.py 8610 SH8601 8609
ls /Volumes/S/png/SH8601/colors.txt /Volumes/S/png/8610/thumb/200.png /Users/mist/DNB/8609/final/001.png
```
Expected: three `<Issue …>` blocks, every listed file exists.

- [ ] **Step 5: Commit**

```bash
git add issues/8610/issue.json issues/SH8601/issue.json issues/8609/issue.json
git commit -m "8610: issue descriptor; SH8601 and 8609 descriptors follow their scans to the S volume"
```

---

### Task 2: Bring `r005_masters_sheet.md` in line with the code

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_sheet.md`

The `.py` (commit `7b9aa90b`) renders ONE uncurved master, writes `masters2400/` and `sheets600/` instead of `figures600/`, undoes the separator's GCR, and never refuses a page. The `.md` still says the opposite in five places.

- [ ] **Step 1: Edit the Outputs block (lines 88–95)**

Replace with:
```
<tmp>/masters600/NNN.png         the master — r010 OCRs it, r145 cuts from it   (the contract)
<tmp>/masters600/NNN.stamp.txt   which profile made that master
<tmp>/sheets600/NNN.png          the levelled, graded, UNCUT sheet at 600 dpi
<tmp>/masters2400/NNN.png        the same at 2400 — a figure that bleeds off the trim still exists here
<tmp>/cmyk2400/NNN.tif           the CMYK archival form, deflate-compressed
<tmp>/cmyk2400/NNN.colors.txt    the profile the separator was actually run with
<tmp>/debug600/NNN.png           the overlay: the four traced lines, in green
```

- [ ] **Step 2: Edit the procedure block (lines 139–143)**

Replace the last four lines of the block with:
```
  -> separate to CMYK with tools/img/cmyk_reconstruction at 2400, UNDO its GCR
     (printed black is all four inks, not K alone — that is why type is black)
  -> ONE render, uncurved: masters2400, reduced 4:1 to sheets600, cut to the
     traced page -> masters600
  -> masters600/NNN.png + NNN.stamp.txt, sheets600/NNN.png, masters2400/NNN.png,
     cmyk2400/NNN.tif + NNN.colors.txt, debug600/NNN.png
```

- [ ] **Step 3: Replace the section "The grade — call the converter, render twice" (lines 295–405)**

New section text:
```markdown
## The grade — call the converter, undo its GCR, render once

The separation is **not reimplemented here**. `tools/img/cmyk_reconstruction`
does it, in the density domain, against the 8 anchors and 4 level lines of
`colors.txt` — or the built-in anchor set with identity levels when the
descriptor has no profile. It is run on the levelled **2400 dpi** sheet, and
the 600 dpi master is a 4:1 reduce of the graded result: grading first and
averaging afterwards is what antialiases thin type instead of deleting it.

**The separator's GCR is undone.** It moves `min(C,M,Y)` into K, which leaves
printed black as K alone, and 100 % single K renders about 50 through SWOP —
grey type. `c = c_final + k` recovers exactly what was subtracted. MEASURED on
p056: glyph p50 37 → 20, 0 % → 39.6 % of glyph pixels solid black, which is
where 8609's masters sit (p010: 31, 42.1 %). p006's photo keeps its gradation.

**There is ONE master and no contrast curve.** `r145_extract_figures.py` reads
the same file `r010` OCRs, so a curve on the master is a curve on every
published figure, and a curve crushes photographs. The uncurved render is the
master; the `-level 30%,100%` curve and the second render are gone.

**The grade is measured and REPORTED, never gated.** Two numbers go in every
page's log line — ink kept vs the raw scan, and the darkest ink's contrast to
paper. A gate on ink-keep once failed 10 of 152 pages and was wrong on all 10
(tint-heavy pages whose screened tint correctly demodulated into a flat fill).
```

- [ ] **Step 4: Fix the remaining refusal language**

- Section "A failed page leaves nothing publishable behind" (lines 433–446): retitle "**A page is never refused**" and replace the body with: "Parity, skew residual, page class, canvas fit and the grade are measured and NOTED — in the page's log line and in its stamp — and the page is published. A page that matches no size class is published as the whole levelled sheet with `NOT CROPPED` in its stamp. The only thing that stops a page is a missing input file."
- "The size gate" heading → "The size classes"; delete "and the fill would then be eating type rather than bed" claim's consequence sentence and say a mismatch publishes the uncropped sheet.
- Verification step 1: the artefact list becomes `(OUT_MASTER, ".png"), (OUT_MASTER, ".stamp.txt"), (OUT_SHEET, ".png"), (OUT_SHEET600, ".png"), (OUT_CMYK, ".tif"), (OUT_CMYK, ".colors.txt"), (OUT_DEBUG, ".png")`; steps 4 and 6 read `R.OUT_SHEET600` instead of `R.OUT_FIGURE`, and step 6's caption becomes "the master's type is black because the GCR is undone; there is no curve to compare" (keep the glyph/paper p50 print for the master only).
- Stamp table: `figures600/NNN.png | PNG Comment` → `sheets600/NNN.png` and `masters2400/NNN.png`.
- "Known outliers" → add one line at the top: "Since 7b9aa90b neither page fails: 117 publishes the whole levelled sheet with `NOT CROPPED`, 007 publishes its trace with a note."

- [ ] **Step 5: Check no stale term survives**

```bash
grep -nE "figures600|render twice|two renders|OCR curve|-level 30|refus|FAILED a gate|GRADE_INK_KEEP|MIN_INK_CONTRAST" tools/img/scan2ocr/rules/r005_masters_sheet.md
```
Expected: only historical mentions inside the grade section's "once failed" sentence. Every other hit is a miss — fix it.

- [ ] **Step 6: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_sheet.md
git commit -m "r005_masters_sheet.md: one uncurved master, GCR undone, no page refused -- as the code has been since 7b9aa90b"
```

---

### Task 3: Extract `r005_masters.py`, the shared library (gate: byte-identical SH8601 masters)

**Files:**
- Create: `tools/img/scan2ocr/rules/r005_masters.py`
- Modify: `tools/img/scan2ocr/rules/r005_masters_sheet.py`

**Interfaces:**
- Produces (in `r005_masters`): `ISSUE, ISS, HERE, IMG_DIR, SCAN_DPI, MASTER_DPI, SCAN_REDUCE, THUMB_DPI, MM, THUMB_MM, SKEW_*, PAPER_DIST, PROP_YELLOW_MIN, PROP_LUM_MIN, BODY_PAPER_FRAC, TRACE_BANDS, CLEAN_PCT, TRACE_OUTLIER_MM, CMYK_TOOL, ICC_CMYK, ICC_RGB, BUILTIN_ANCHORS, BUILTIN_LEVELS, INK_CONTRAST, RAW_INK_DIST, STOCK_PCT, INK_DARK_PCT, PAPER_PROBE_MIN_FRAC, DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP, ANCHORS, LEVELS, HAVE_PROFILE, PAPER_RGB, GRADE_TEXT, GRADE_SHA`; functions `read_profile(path) -> (anchors, levels, have)`, `profile_text(anchors, levels) -> str`, `write_profile(anchors, levels, dest, variant)`, `stamp_text(variant, **fields) -> str`, `class PageFailed(Exception)`, `skew_score(ink, angle)`, `measure_skew(gray, around=None) -> float`, `prop_mask(rgb) -> bool[h,w]`, `paper_mask(rgb) -> bool[h,w]`, `_edges(mask, rows, cols)`, `boundaries(mask)`, `box_open(mask, r_px)`, `trace(vals, idx, pct, mm_px) -> np.poly (slope, intercept)`, `separate_and_render(src_png, cmyk_tiff, rgb_png, profile_txt, stamp)`, `undo_gcr(cmyk_tiff)`, `archive_cmyk(cmyk_tiff, dest, stamp)`, `save_master(arr, dest, stamp)`, `tilt(poly) -> deg`.

- [ ] **Step 1: Render the BEFORE reference of two SH8601 pages with the unchanged code**

```bash
cd tools/img/scan2ocr/rules
grep -n '^ISSUE = ' r000_issue.py        # must read "SH8601" -- it does today
rm -rf /tmp/64er_SH8601
../../../../.venv/bin/python r005_masters_sheet.py 41 56 2>&1 | tail -4
mkdir -p /tmp/64er_SH8601_before && cp /tmp/64er_SH8601/masters600/041.* /tmp/64er_SH8601/masters600/056.* /tmp/64er_SH8601_before/
shasum -a 256 /tmp/64er_SH8601_before/*.png
```
Expected: two page lines ending in `grade <sha>`, two shasums. (~2 min per page; the scans are on the S volume.) If the run fails on a missing tool, the cause is `tools/img/cmyk_reconstruction/target/release/cmyk_reconstruction` or `magick` — fix inline, do not proceed without the reference.

- [ ] **Step 2: Create `r005_masters.py`**

Move, verbatim (docstrings and comments included), from `r005_masters_sheet.py` into the new module in this order: the module docstring below; imports; `from r000_issue import ISSUE`; the constants listed under *Produces* above (lines 131–161, 189–218 minus `BODY_PAPER_FRAC`'s neighbours that stay, 255–274 `TRACE_BANDS/CLEAN_PCT/TRACE_OUTLIER_MM`, 360–428 the grade block, 446–453 debug); the descriptor block **without** the `BINDING` check (`HERE`, `IMG_DIR`, `ISS = r000_issue.load(ISSUE)`); `read_profile`, `ANCHOR_KEYS`, `LEVEL_KEYS`, `profile_text`, `write_profile`, `ANCHORS/LEVELS/HAVE_PROFILE/PAPER_RGB`, `GRADE_TEXT/GRADE_SHA`, `stamp_text`, `PageFailed`, `skew_score`, `measure_skew`, `prop_mask`, `paper_mask`, `_edges`, `boundaries`, `box_open`, `trace`, `separate_and_render`, `undo_gcr`, `archive_cmyk`, `save_master`, `tilt`.

Two signatures gain a `variant` argument so the stamp header stays byte-identical per variant:

```python
def write_profile(anchors, levels, dest, variant):
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(f"# {ISSUE} -- profile as used by {variant}\n")
        fh.write(f"# source: {ISS.colors or 'built-in anchors, identity levels'}\n")
        fh.write(profile_text(anchors, levels))


def stamp_text(variant, **fields):
    head = [f"{variant} {ISSUE} -- the grade as used for this page",
            f"grade-sha    {GRADE_SHA}",
            f"profile      {ISS.colors or '(none -- built-in anchors)'}",
            f"render       ONE master, uncurved -- r010 OCRs it and r145 "
            f"cuts figures from it"]
    body = [f"{k:<12s} {v}" for k, v in fields.items()]
    return "\n".join(head + body + [""] + GRADE_TEXT.rstrip().split("\n")) + "\n"
```

Module docstring:
```python
"""
Step 005, the library both variants share.

Step 005 exists in two mutually exclusive variants, r005_masters_sheet and
r005_masters_spread, selected by the descriptor's `binding`.  Everything
between the scanner and the page GEOMETRY is the same job in both -- the skew
measurement, the paper and prop masks, the robust edge trace, the separation
and its GCR undo, the stamp -- and lived once in the sheet variant.  It lives
here now, with the same names and the same comments, so that a change to the
grade is one change.  The variants keep what differs: which edges exist, how
the inner boundary is found, and what the canvas is.

This module has NO binding check.  It loads the descriptor because the grade
and the paths depend on it; which variant is allowed to run is the variant's
own first line.  Not a step: nothing runs when it is executed.
"""
```

- [ ] **Step 3: Make the sheet variant import from it**

At the top of `r005_masters_sheet.py`, replace the moved definitions with one import, one name per line, listing only the names the sheet variant still uses (grep each: `grep -c NAME r005_masters_sheet.py`, drop any at 0):
```python
from r005_masters import (
    ISSUE, ISS, HERE, IMG_DIR,
    SCAN_DPI, MASTER_DPI, SCAN_REDUCE, THUMB_DPI, MM, THUMB_MM,
    SKEW_RESIDUAL_MAX, BODY_PAPER_FRAC, CLEAN_PCT, TRACE_OUTLIER_MM,
    INK_CONTRAST, RAW_INK_DIST, STOCK_PCT, INK_DARK_PCT, PAPER_PROBE_MIN_FRAC,
    DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP,
    ANCHORS, LEVELS, HAVE_PROFILE, PAPER_RGB, GRADE_SHA,
    PageFailed, measure_skew, prop_mask, paper_mask, _edges, boundaries,
    box_open, trace, separate_and_render, archive_cmyk, save_master,
    write_profile, stamp_text, tilt,
)
```
`BED_LUM`, `BED_OUTSIDE_FRAC`, `FULLBLEED_PAPER_FRAC`, `SHEET_OPEN_MM`, `FRINGE_PCT`, `CLEAN_INSET_MM`, `FRINGE_INSET_MM`, `RECTO_FLUSH_*`, `TORN_CONFIDENT_RATIO`, `PAGE_CLASSES`, `MASTER_W_MM/H_MM`, `BINDING`, `find_sheet`, `sheet_boundaries`, `page_class`, `torn_side`, `process`, `__main__` **stay** in the sheet file. Keep the binding check where it is, now reading `ISS.binding` from the import. Replace the two call sites: `write_profile(ANCHORS, LEVELS, profile_txt)` → `write_profile(ANCHORS, LEVELS, profile_txt, "r005_masters_sheet")`; `stamp_text(**{...})` → `stamp_text("r005_masters_sheet", **{...})` (both in `process` and in `__main__`).

- [ ] **Step 4: Import check**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python -c "import r005_masters_sheet as R; print(R.GRADE_SHA, R.MASTER_W_MM)"
../../../../.venv/bin/python -m pyflakes r005_masters_sheet.py r005_masters.py 2>/dev/null || ../../../../.venv/bin/pip install --quiet pyflakes && ../../../../.venv/bin/python -m pyflakes r005_masters_sheet.py r005_masters.py
```
Expected: the sha and `231.0`; pyflakes reports **no undefined names and no unused imports**.

- [ ] **Step 5: Render AFTER and compare byte-for-byte**

```bash
rm -rf /tmp/64er_SH8601
../../../../.venv/bin/python r005_masters_sheet.py 41 56 2>&1 | tail -4
cmp /tmp/64er_SH8601_before/041.png /tmp/64er_SH8601/masters600/041.png && cmp /tmp/64er_SH8601_before/056.png /tmp/64er_SH8601/masters600/056.png && diff /tmp/64er_SH8601_before/041.stamp.txt /tmp/64er_SH8601/masters600/041.stamp.txt && echo IDENTICAL
```
Expected: `IDENTICAL`. Any difference is a refactor bug — find it (a stamp header word, a constant left behind with a different value), never accept "close".

- [ ] **Step 6: Numbering check and commit**

```bash
tools/img/scan2ocr/rules/r000_verify_numbering.sh | tail -3
git add tools/img/scan2ocr/rules/r005_masters.py tools/img/scan2ocr/rules/r005_masters_sheet.py
git commit -m "r005: move what both variants share into r005_masters.py; SH8601 masters byte-identical"
```

---

### Task 4: Spread variant skeleton — `measure` levels and grades a page

**Files:**
- Create: `tools/img/scan2ocr/rules/r005_masters_spread.py`
- Modify: `tools/img/scan2ocr/rules/r000_issue.py` (`ISSUE = "8610"`)

**Interfaces:**
- Produces: `r005_masters_spread.measure(page)` writing `masters2400/NNN.png`, `sheets600/NNN.png`, `cmyk2400/NNN.tif`, `cmyk2400/NNN.colors.txt`; module constants `BINDING = "spread"`, `OUT_MASTER, OUT_SHEET, OUT_SHEET600, OUT_CMYK, OUT_GEOM, OUT_DEBUG, OUT_DIRS`, `VARIANT = "r005_masters_spread"`, `A4_W_MM = 210.0, A4_H_MM = 297.0`, `MASTER_W_PX = 4961, MASTER_H_PX = 7016`; helper `level_page(page) -> (angle, residual, full2400: PIL.Image, img600: PIL.Image, notes)`; `grade_page(stem, full2400, stamp)`.

- [ ] **Step 1: Flip the issue**

`r000_issue.py`: `ISSUE = "8610"`, and add the line `#     "8610"     the October 1986 monthly, 200 pages, clipped spreads` to the comment block above it.

- [ ] **Step 2: Write the skeleton**

```python
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

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ND
from scipy.signal import fftconvolve

import r000_issue
from r005_masters import (
    ISSUE, ISS, HERE, MM, THUMB_MM, SCAN_REDUCE, MASTER_DPI, THUMB_DPI,
    SKEW_RESIDUAL_MAX, BODY_PAPER_FRAC, CLEAN_PCT, TRACE_OUTLIER_MM,
    DEBUG_REDUCE, DEBUG_COLOR, DEBUG_WIDTH, DEBUG_STEP,
    ANCHORS, LEVELS, HAVE_PROFILE, PAPER_RGB, GRADE_SHA,
    PageFailed, measure_skew, paper_mask, prop_mask, boundaries, trace,
    separate_and_render, archive_cmyk, save_master, write_profile, stamp_text,
    tilt,
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
```

- [ ] **Step 3: Run one page**

```bash
cd tools/img/scan2ocr/rules && rm -rf /tmp/64er_8610 && time ../../../../.venv/bin/python r005_masters_spread.py measure 100 2>&1 | tail -3
ls -la /tmp/64er_8610/*/100.*
../../../../.venv/bin/python -c "
from PIL import Image; Image.MAX_IMAGE_PIXELS=None
im=Image.open('/tmp/64er_8610/sheets600/100.png'); print(im.size, im.info.get('dpi'), 'r005' in im.info)"
```
Expected: `p100: skew ±x.xx -> ±0.0x deg | grade …`; four files (`masters2400/100.png`, `sheets600/100.png`, `cmyk2400/100.tif`, `cmyk2400/100.colors.txt`); size ≈ (5100, 7188), dpi (600, 600), `True`. Open `sheets600/100.png` scaled and confirm black type on white paper, yellow prop at the foot, neighbour strip on the right.

- [ ] **Step 4: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py tools/img/scan2ocr/rules/r000_issue.py
git commit -m "r005_masters_spread: the skeleton -- measure levels and grades a page; ISSUE = 8610"
```

---

### Task 5: Outer edges — top, bottom, outer side, from paper vs backing

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`
- Create: `tools/img/scan2ocr/tests/test_r005_spread.py`, `tools/img/scan2ocr/tests/conftest.py`

**Interfaces:**
- Produces: `outer_edges(rgb600, par) -> dict(top=poly, bot=poly, outer=poly)` — each a `(slope, intercept)` numpy poly in 600 dpi sheet pixels; `top`/`bot` are `y = f(x)`, `outer` is `x = f(y)`; `EDGE_INSET_MM = 0.3`.

- [ ] **Step 1: conftest so the tests import the rules by bare name without loading a descriptor**

`tools/img/scan2ocr/tests/conftest.py`:
```python
"""The rules import each other by bare name from rules/, and r005_masters
loads the ISSUE descriptor at import.  Tests exercise pure functions on
synthetic arrays, so the descriptor only has to resolve -- 8610's does."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rules"))
```

- [ ] **Step 2: Write the failing test — a synthetic spread frame**

`tools/img/scan2ocr/tests/test_r005_spread.py`:
```python
import numpy as np
import pytest

import r005_masters_spread as S
from r005_masters import MM, PAPER_RGB

PAPER = tuple(int(v) for v in PAPER_RGB)     # the built-in W
BED = (135, 128, 124)                          # 8610's grey bed strip
PROP = (250, 218, 113)                         # the yellow prop


def synthetic_frame(par="even", w=5500, h=7300, top_bed_mm=1.0, prop_mm=7.0,
                    fold_from_edge_mm=20.0, neighbour_rgb=(90, 120, 200)):
    """A levelled 600 dpi spread frame: bed on top, prop below, paper to the
    outer frame edge, a neighbour strip beyond the fold on the inner side."""
    a = np.empty((h, w, 3), np.uint8)
    a[:] = PAPER
    a[:int(top_bed_mm * MM)] = BED
    a[h - int(prop_mm * MM):] = PROP
    fold = int(fold_from_edge_mm * MM)
    if par == "even":
        a[:, w - fold:] = neighbour_rgb
    else:
        a[:, :fold] = neighbour_rgb
    return a


def test_outer_edges_even():
    a = synthetic_frame("even")
    e = S.outer_edges(a, "even")
    h, w = a.shape[:2]
    assert abs(np.polyval(e["top"], w / 2) - 1.0 * MM) < 2 * MM * 0.1 + 3
    assert abs(np.polyval(e["bot"], w / 2) - (h - 7.0 * MM)) < 3
    assert abs(np.polyval(e["outer"], h / 2) - 0) < 3          # paper to the frame
    assert abs(S.tilt(e["top"])) < 0.05


def test_outer_edges_odd_is_mirrored():
    a = synthetic_frame("odd")
    e = S.outer_edges(a, "odd")
    h, w = a.shape[:2]
    assert abs(np.polyval(e["outer"], h / 2) - (w - 1)) < 3
```

- [ ] **Step 3: Run — expect failure**

```bash
cd tools/img/scan2ocr && ../../../.venv/bin/python -m pytest tests/test_r005_spread.py -v 2>&1 | tail -5
```
Expected: `AttributeError: module 'r005_masters_spread' has no attribute 'outer_edges'`.

- [ ] **Step 4: Implement**

Add after `parity()`:
```python
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


def outer_edges(rgb, par):
    """dict(top, bot, outer): straight lines in 600 dpi sheet pixels.

    top/bot are y(x); outer is x(y).  Parity says which side is outer: an even
    page's neighbour is on the right, so its outer edge is the LEFT one.
    """
    rows, starts, ends, cols, tops, bots = boundaries(paper_mask(rgb))
    return {"top": trace(tops, cols, CLEAN_PCT, MM),
            "bot": trace(bots, cols, CLEAN_PCT, MM),
            "outer": trace(starts if par == "even" else ends, rows, CLEAN_PCT, MM)}
```

- [ ] **Step 5: Run — expect pass**

Same command. Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add tools/img/scan2ocr/tests/conftest.py tools/img/scan2ocr/tests/test_r005_spread.py tools/img/scan2ocr/rules/r005_masters_spread.py
git commit -m "r005_masters_spread: trace the three outer edges from paper vs backing"
```

---

### Task 6: The fold — clip holes on a line

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`, `tools/img/scan2ocr/tests/test_r005_spread.py`

**Interfaces:**
- Produces: `find_holes(gray600, par) -> list[(cx, cy, d_mm)]` in sheet pixels; `fit_fold(holes, h) -> None | dict(poly=(slope, intercept) x(y), n=int, residual_mm=float, span=float)`; constants `HOLE_BAND_MM, HOLE_BG_MM, HOLE_DIP, HOLE_ABS_MAX, HOLE_MIN_MM, HOLE_MAX_MM, HOLE_FILL_MIN, HOLE_ASPECT_MAX, FOLD_TOL_MM, FOLD_MIN_HOLES, FOLD_MIN_SPAN, FOLD_TILT_MAX`.

**Deviation from the spec, stated:** the spec scores candidate columns against the rigid 3-pair template. This task fits a straight line through ≥4 collinear hole-shaped blobs spanning ≥50 % of the height, |tilt| ≤ 1°, and measures the result over the issue (Task 8, Task 11). The template is added only if the sweep shows false locks — a measured decision, recorded in the rule.

- [ ] **Step 1: Write the failing tests**

Append to the test file:
```python
def with_holes(a, par, fold_from_edge_mm=20.0, ys_mm=(30, 43, 130, 143, 230, 243),
               d_mm=0.7, x_jitter_mm=0.1):
    h, w = a.shape[:2]
    x = (w - fold_from_edge_mm * MM) if par == "even" else fold_from_edge_mm * MM
    r = d_mm * MM / 2
    yy, xx = np.mgrid[:h, :w]
    for i, y_mm in enumerate(ys_mm):
        cx = x + (x_jitter_mm * MM if i % 2 else -x_jitter_mm * MM)
        disc = (yy - y_mm * MM) ** 2 + (xx - cx) ** 2 <= r * r
        a[disc] = (20, 18, 18)
    return a, x


def test_find_holes_finds_six():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    gray = a.mean(2).astype(np.uint8)
    holes = S.find_holes(gray, "even")
    assert len(holes) == 6
    assert all(abs(cx - x) < 0.3 * MM for cx, cy, d in holes)
    assert all(0.5 < d < 1.0 for _, _, d in holes)


def test_find_holes_ignores_type_and_rules():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    h, w = a.shape[:2]
    a[int(100 * MM):int(100 * MM) + 4, w - int(24 * MM):w - int(16 * MM)] = 0   # a rule
    a[int(150 * MM):int(153 * MM), w - int(21 * MM):w - int(19 * MM)] = 0     # a 3 mm blob
    gray = a.mean(2).astype(np.uint8)
    assert len(S.find_holes(gray, "even")) == 6


def test_fit_fold_line():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    h = a.shape[0]
    fold = S.fit_fold(S.find_holes(a.mean(2).astype(np.uint8), "even"), h)
    assert fold is not None and fold["n"] == 6
    assert abs(np.polyval(fold["poly"], h / 2) - x) < 0.2 * MM
    assert abs(S.tilt(fold["poly"])) < 0.1


def test_fit_fold_refuses_three_holes():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even",
                      ys_mm=(30, 43, 130))
    assert S.fit_fold(S.find_holes(a.mean(2).astype(np.uint8), "even"),
                      a.shape[0]) is None
```

- [ ] **Step 2: Run — expect failure**

`../../../.venv/bin/python -m pytest tests/test_r005_spread.py -v -k holes_or_fold 2>&1 | tail -3` → AttributeError.

- [ ] **Step 3: Implement**

Add after `outer_edges`:
```python
# --- the fold: the clip holes --------------------------------------------
# The sheet was held in a rigid 6-hole binder clip whose punches left DARK
# TEARDROPS on the fold, 3 vertical pairs.  They are the one physical mark of
# the fold that survives on every sheet, and they are on the SAME line as the
# crease (seen on p100 at thumb scale).  MEASURED on 8610 p100: ~0.6 mm across,
# ~20 mm inboard of the frame edge, on a crease that runs through them.
HOLE_BAND_MM = 30.0          # search this far in from the inner frame edge
HOLE_BG_MM = 3.5             # local-mean window for the contrast test
HOLE_DIP = 45                # a hole is this far below its local surround...
HOLE_ABS_MAX = 120           # ...and absolutely dark: a hole is a hole, not a tint
HOLE_MIN_MM, HOLE_MAX_MM = 0.4, 2.0    # across; type is smaller, shadows larger
HOLE_FILL_MIN = 0.40         # area / bbox: a teardrop, not a line fragment
HOLE_ASPECT_MAX = 3.0        # long/short: rejects rules and the neighbour's edge
# The line through them: at least this many holes, within this of the line,
# spanning this fraction of the page height, and near-vertical.  Six holes on a
# rigid clip give a line to a fraction of a millimetre; three do not tell a
# column of bullets from a clip.
FOLD_TOL_MM = 0.5
FOLD_MIN_HOLES = 4
FOLD_MIN_SPAN = 0.5
FOLD_TILT_MAX = 1.0          # deg


def find_holes(gray, par):
    """Hole-shaped dark blobs in the inner band: [(cx, cy, diameter_mm), ...]."""
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
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        d = max(hh, ww) / MM
        if not HOLE_MIN_MM <= d <= HOLE_MAX_MM:
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
```

- [ ] **Step 4: Run — expect pass**

`../../../.venv/bin/python -m pytest tests/test_r005_spread.py -v 2>&1 | tail -3` → 6 passed.

- [ ] **Step 5: Try it on the real p100 and p101 sheets**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python r005_masters_spread.py measure 101 2>&1 | tail -1
../../../../.venv/bin/python -c "
import numpy as np; from PIL import Image; Image.MAX_IMAGE_PIXELS=None
import r005_masters_spread as S
for p in (100, 101):
    g = np.array(Image.open(f'/tmp/64er_8610/sheets600/{p:03d}.png').convert('L'))
    holes = S.find_holes(g, S.parity(p)); fold = S.fit_fold(holes, g.shape[0])
    print(p, len(holes), 'holes', [(int(x), int(y), round(d, 2)) for x, y, d in holes][:12])
    print('   fold', None if fold is None else (int(np.polyval(fold['poly'], g.shape[0]/2)), fold['n'], round(fold['residual_mm'], 2), round(fold['span'], 2), round(S.tilt(fold['poly']), 2)))"
```
Expected: 6–12 candidates per page, a fold with n ≥ 4, residual ≤ 0.3 mm, |tilt| ≤ 0.5°, at x ≈ w − 20 mm·MM (p100) / ≈ 20 mm·MM (p101). If the sheet is graded so hard the holes read <20 everywhere and `HOLE_DIP` finds too many blobs, tune ON EVIDENCE (print the blob stats) and record the numbers in the constant's comment. If fewer than 4 holes are found on either page, look at the strip (`magick sheets600/100.png -gravity East -crop 720x7188+0+0 +repage /tmp/64er_8610/strip100.png`) before changing anything.

- [ ] **Step 6: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py tools/img/scan2ocr/tests/test_r005_spread.py
git commit -m "r005_masters_spread: the fold, from the clip holes on a line"
```

---

### Task 7: The fold fallback — the neighbour-content boundary

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`, `tools/img/scan2ocr/tests/test_r005_spread.py`

**Interfaces:**
- Produces: `neighbour_boundary(rgb600, par, prior_x=None) -> None | dict(poly, n, residual_mm)`; constants `NB_BANDS, NB_STRIP_MM, NB_DARK_LUM, NB_DARK_FRAC, NB_SAT_MIN, NB_BLOCK_MIN_MM, NB_BORDER_NEAR_MM, NB_RESID_MM, NB_MIN_BANDS, NB_TILT_MAX, NB_PRIOR_MM`.

- [ ] **Step 1: Failing tests**

```python
def test_neighbour_boundary_finds_colour_step():
    a = synthetic_frame("even", fold_from_edge_mm=18.0, neighbour_rgb=(90, 120, 200))
    h, w = a.shape[:2]
    nb = S.neighbour_boundary(a, "even")
    assert nb is not None
    assert abs(np.polyval(nb["poly"], h / 2) - (w - 18.0 * MM)) < 1.0 * MM


def test_neighbour_boundary_none_on_blank_margin():
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    assert S.neighbour_boundary(a, "even") is None


def test_neighbour_boundary_rejects_far_from_prior():
    a = synthetic_frame("even", fold_from_edge_mm=18.0, neighbour_rgb=(90, 120, 200))
    h, w = a.shape[:2]
    assert S.neighbour_boundary(a, "even", prior_x=w - 40.0 * MM) is None
```

- [ ] **Step 2: Run — expect AttributeError**

- [ ] **Step 3: Implement**

```python
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
        x = to_x(strip_w - 1 - edge) if par == "even" else to_x(edge)
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
```

- [ ] **Step 4: Run — expect 9 passed**

- [ ] **Step 5: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py tools/img/scan2ocr/tests/test_r005_spread.py
git commit -m "r005_masters_spread: neighbour-content boundary as the fold fallback"
```

---

### Task 8: The logo anchor

**Files:**
- Create: `tools/img/scan2ocr/template_64er_600.png` (copy of `tools/img/scan2mrc/03-crop/template_64er_600.png`)
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`, `tools/img/scan2ocr/tests/test_r005_spread.py`

**Interfaces:**
- Produces: `TEMPLATE_PATH = HERE.parent / "template_64er_600.png"`, `load_template() -> float32[131, 394]`, `ncc(region, tmpl) -> float32 valid-mode map`, `find_logo(gray600, par, tmpl) -> None | dict(x, y, score, bbox=(x0, y0, x1, y1))` where `(x, y)` is the wordmark's OUTER-BOTTOM corner in sheet pixels; constants `LOGO_BAND_TOP_MM, LOGO_BAND_BOT_MM, LOGO_CORNER_FRAC, LOGO_SCORE_MIN`.

- [ ] **Step 1: Copy the template (a binary — its own commit)**

```bash
cp tools/img/scan2mrc/03-crop/template_64er_600.png tools/img/scan2ocr/template_64er_600.png
git add tools/img/scan2ocr/template_64er_600.png
git commit -m "scan2ocr: the 64'er wordmark template at 600 dpi, for the spread variant's anchor"
```

- [ ] **Step 2: Failing tests**

```python
def test_ncc_peaks_at_the_paste():
    rng = np.random.default_rng(0)
    tmpl = S.load_template()
    th, tw = tmpl.shape
    region = 200 + 10 * rng.standard_normal((th + 400, tw + 600)).astype(np.float32)
    region[150:150 + th, 300:300 + tw] = tmpl
    m = S.ncc(region, tmpl)
    y, x = np.unravel_index(m.argmax(), m.shape)
    assert (y, x) == (150, 300) and m.max() > 0.95


def test_find_logo_even_page_bottom_left():
    tmpl = S.load_template()
    th, tw = tmpl.shape
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    g = a.mean(2).astype(np.uint8)
    h, w = g.shape
    y0, x0 = h - int(16 * MM) - th, int(24 * MM)
    g[y0:y0 + th, x0:x0 + tw] = tmpl.astype(np.uint8)
    r = S.find_logo(g, "even", tmpl)
    assert r is not None and r["score"] > 0.9
    assert (r["x"], r["y"]) == (x0, y0 + th)          # outer-bottom corner: bottom-LEFT


def test_find_logo_odd_page_bottom_right():
    tmpl = S.load_template()
    th, tw = tmpl.shape
    a = synthetic_frame("odd", neighbour_rgb=PAPER)
    g = a.mean(2).astype(np.uint8)
    h, w = g.shape
    y0, x0 = h - int(16 * MM) - th, w - int(24 * MM) - tw
    g[y0:y0 + th, x0:x0 + tw] = tmpl.astype(np.uint8)
    r = S.find_logo(g, "odd", tmpl)
    assert r is not None and (r["x"], r["y"]) == (x0 + tw, y0 + th)


def test_find_logo_none_on_blank():
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    assert S.find_logo(a.mean(2).astype(np.uint8), "even", S.load_template()) is None
```

- [ ] **Step 3: Run — expect AttributeError**

- [ ] **Step 4: Implement**

```python
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
LOGO_BAND_BOT_MM = 5.0       # baseline at h-420..h-300 px (13-18 mm)
LOGO_CORNER_FRAC = 0.48      # ...and this fraction of the width, from the outer edge
LOGO_SCORE_MIN = 0.5         # 8609 accepted 0.42 with an angle sweep; here the
                             # page is level.  RE-MEASURE on the first six pages
                             # and record the scores beside this number.


def load_template():
    return np.array(Image.open(TEMPLATE_PATH).convert("L"), np.float32)


def ncc(region, tmpl):
    """Zero-mean normalised cross-correlation, valid mode, by FFT."""
    t = tmpl - tmpl.mean()
    tn = math.sqrt(float((t * t).sum()))
    ones = np.ones_like(t)
    num = fftconvolve(region, t[::-1, ::-1], mode="valid")
    s1 = fftconvolve(region, ones, mode="valid")
    s2 = fftconvolve(region * region, ones, mode="valid")
    var = np.maximum(s2 - s1 * s1 / t.size, 1e-6)
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
```

- [ ] **Step 5: Run — expect 13 passed**

- [ ] **Step 6: Measure the score on real pages**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python r005_masters_spread.py measure 10 11 2>&1 | tail -2
../../../../.venv/bin/python -c "
import numpy as np; from PIL import Image; Image.MAX_IMAGE_PIXELS=None
import r005_masters_spread as S
t = S.load_template()
for p in (10, 11, 100, 101):
    g = np.array(Image.open(f'/tmp/64er_8610/sheets600/{p:03d}.png').convert('L'))
    print(p, S.find_logo(g, S.parity(p), t))"
```
Expected: four hits with score ≥ 0.7, bbox in the outer-bottom corner (even: x0 within 12–30 mm of the left; odd: x1 within 12–30 mm of the right; y1 ≈ h − 13…18 mm). Crop one bbox with `magick` and look at it. Write the four scores into the `LOGO_SCORE_MIN` comment. If a score is < 0.5 on a page that visibly has the wordmark, the template does not match this issue's wordmark — cut a fresh one from p010's sheet at the bbox and re-run before lowering the gate.

- [ ] **Step 7: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py tools/img/scan2ocr/tests/test_r005_spread.py
git commit -m "r005_masters_spread: the wordmark anchor by normalised cross-correlation"
```

---

### Task 9: `measure` writes the geometry and the debug overlay

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`

**Interfaces:**
- Produces: `geometry/NNN.json` with keys `page, parity, sheet_px [w, h], skew {angle, residual}, edges {top: [a, b], bot: [a, b], outer: [a, b]}, fold {source: "holes"|"colour"|"none", poly: [a, b] | null, n, residual_mm, tilt_deg}, holes [[cx, cy, d_mm], ...], anchor {source: "logo"|null, x, y, score, bbox} | null, notes [..]`; `measure_geometry(rgb600, page, angle, residual, notes, tmpl) -> dict`; `draw_debug(img600, geom, dest)`.

- [ ] **Step 1: Implement `measure_geometry` and `draw_debug`; extend `measure`**

```python
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


DEBUG_FOLD = (230, 0, 200)
DEBUG_LOGO = (0, 120, 255)


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
        r = max(dm * MM, 12)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=DEBUG_FOLD, width=3)
    if geom["anchor"]:
        d.rectangle(geom["anchor"]["bbox"], outline=DEBUG_LOGO, width=DEBUG_WIDTH)
    text = [f"p{geom['page']:03d} {geom['parity']}  fold:{geom['fold']['source']} "
            f"anchor:{'logo %.2f' % geom['anchor']['score'] if geom['anchor'] else 'NONE'}"]
    d.text((60, 60), "\n".join(text + geom["notes"]), fill=DEBUG_FOLD)
    overlay.resize((w // DEBUG_REDUCE, h // DEBUG_REDUCE), Image.LANCZOS).save(dest)
```

In `measure`, after `grade_page`:
```python
    rgb = np.array(img)                      # the levelled, UNGRADED 600 dpi sheet
    geom = measure_geometry(rgb, page, angle, residual, notes, TEMPLATE)
    (OUT_GEOM / f"{stem}.json").write_text(json.dumps(geom, indent=1))
    draw_debug(img, geom, OUT_DEBUG / f"{stem}.png")
```
and the print line becomes:
```python
    f = geom["fold"]
    print(f"p{stem}: skew {angle:+.2f} -> {residual:+.2f} deg | edges T {tilt(geom['edges']['top']):+.2f} "
          f"B {tilt(geom['edges']['bot']):+.2f} O {tilt(geom['edges']['outer']):+.2f} | "
          f"fold {f['source']} n={f['n']}"
          + (f" x={np.polyval(f['poly'], rgb.shape[0] / 2):.0f} tilt {f['tilt_deg']:+.2f}" if f["poly"] else "")
          + f" | logo {'%.2f' % geom['anchor']['score'] if geom['anchor'] else 'none'}"
          + f" | grade {GRADE_SHA}"
          + "".join(f"\n      NOTE p{stem}: {n}" for n in notes), flush=True)
```
`TEMPLATE = load_template()` at module level, after the constants. The stamp in `measure` gains `"fold": source`, `"anchor": …`.

Note: `measure_geometry` reads the **ungraded** levelled sheet (`np.array(img)`), where the paper mask and the prop mask were calibrated; the hole and logo finders read its grey. The graded sheet is only for the master.

- [ ] **Step 2: Run six pages and look**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python r005_masters_spread.py measure 1 10 11 100 101 200 2>&1 | grep -v '^[A-Z]' | tail -20
magick /tmp/64er_8610/debug600/010.png /tmp/64er_8610/debug600/011.png +append -resize 1600x /tmp/64er_8610/debug_10_11.png
```
Open `debug_10_11.png` and the others. Expected: green lines on the bed strip, the prop's top and the outer frame edge; magenta line through circled holes on the fold; blue box on the wordmark; `fold holes n≥4` and `logo ≥0.7` on 010/011/100/101; the cover (001) and back cover (200) likely `logo none` — that is expected, and they must still show a fold or a NOTE.

- [ ] **Step 3: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py
git commit -m "r005_masters_spread: measure writes geometry/NNN.json and the debug overlay"
```

---

### Task 10: `cut` — fit the window per parity, cut every master

**Files:**
- Modify: `tools/img/scan2ocr/rules/r005_masters_spread.py`, `tools/img/scan2ocr/tests/test_r005_spread.py`

**Interfaces:**
- Produces: `unknown_mask(geom, scale=1) -> bool[h/scale, w/scale]` (True = not this page: beyond the traced edges, beyond the fold, hole discs); `anchor_of(geom) -> (x, y, source)`; `fit_window(geoms) -> dict(even=(S, B), odd=(S, B), stats)`; `cut_page(geom, fit) -> (master uint8[7016, 4961, 3], unknown_frac, notes)`; `cut()`; constants `FIT_SCALE = 4`, `FIT_S_RANGE`, `FIT_B_RANGE_MM`, `FOLD_INSET_MM = 0.0`, `HOLE_FILL_R_MM`.

- [ ] **Step 1: Failing tests**

```python
def synthetic_geom(page, w=5500, h=7300, fold_from_edge_mm=20.0, logo=True,
                   anchor_dx_mm=24.0, anchor_dy_mm=16.0):
    par = "even" if page % 2 == 0 else "odd"
    fold_x = w - fold_from_edge_mm * MM if par == "even" else fold_from_edge_mm * MM
    ax = anchor_dx_mm * MM if par == "even" else w - anchor_dx_mm * MM
    return {"page": page, "parity": par, "sheet_px": [w, h],
            "skew": {"angle": 0.0, "residual": 0.0},
            "edges": {"top": [0.0, 1.0 * MM], "bot": [0.0, h - 7.0 * MM],
                      "outer": [0.0, 0.0 if par == "even" else w - 1.0]},
            "fold": {"source": "holes", "poly": [0.0, fold_x], "n": 6,
                     "residual_mm": 0.1, "tilt_deg": 0.0},
            "holes": [[fold_x, 40 * MM, 0.7]],
            "anchor": ({"source": "logo", "x": int(ax), "y": int(h - anchor_dy_mm * MM),
                        "score": 0.9, "bbox": [0, 0, 0, 0]} if logo else None),
            "notes": []}


def test_unknown_mask_marks_bed_prop_neighbour_and_hole():
    g = synthetic_geom(100)
    u = S.unknown_mask(g)
    w, h = g["sheet_px"]
    assert u[2, w // 2] and not u[int(2 * MM), w // 2]          # bed strip / paper
    assert u[h - 3, w // 2]                                        # prop
    assert u[h // 2, w - 5] and not u[h // 2, w - int(25 * MM)]  # beyond fold / inside
    assert u[int(40 * MM), int(w - 20 * MM)]                      # the hole disc


def test_fit_window_recovers_the_layout():
    # The synthetic frame is 233 x 309 mm with 1 mm bed, 7 mm prop and the fold
    # 20 mm in from the inner edge, so the KNOWN region (212.7 x 300.7 mm) holds
    # a 210 x 297 window with a little slack: the objective is flat over that
    # slack and argmin takes the first minimum, i.e. the smallest S and B --
    # the window pushed against the fold and against the foot.  The expected
    # offsets follow from that, to within the 0.3 mm inset plus one grid step.
    geoms = [synthetic_geom(p) for p in range(10, 30)]
    fit = S.fit_window(geoms)
    tol = 1.0 * MM
    for par, page in (("even", 10), ("odd", 11)):
        g = synthetic_geom(page)
        w, h = g["sheet_px"]
        fold_x = g["fold"]["poly"][1]
        bot_y = g["edges"]["bot"][1]
        ax, ay = g["anchor"]["x"], g["anchor"]["y"]
        x0 = fold_x - S.MASTER_W_PX if par == "even" else fold_x
        y0 = bot_y - S.MASTER_H_PX
        S_, B_ = fit[par]
        assert abs(S_ - (ax - x0)) < tol, (par, S_, ax - x0)
        assert abs(B_ - (ay - y0)) < tol, (par, B_, ay - y0)


def test_cut_page_is_a4_and_white_where_unknown():
    g = synthetic_geom(100)
    fit = S.fit_window([synthetic_geom(p) for p in range(10, 30)])
    sheet = synthetic_frame("even")
    master, unknown_frac, notes = S.cut_page(g, fit, sheet)
    assert master.shape == (S.MASTER_H_PX, S.MASTER_W_PX, 3)
    assert (master[-5:] == 255).all()             # the prop band is white
    assert unknown_frac < 0.05
```

- [ ] **Step 2: Run — expect AttributeError**

- [ ] **Step 3: Implement**

```python
# ---------------------------------------------------------------------------
# cut: the window
# ---------------------------------------------------------------------------
# ONE rigid (S, B) per parity: the anchor's distance from the window's left
# and top edge, chosen to minimise the UNKNOWN fraction inside the window --
# bed, prop, beyond the fold, off the frame -- over the pages that carry their
# own wordmark.  8609's fit: even S=568 B=6892, odd S=4416 B=6900 (600 dpi
# px), unknown p50 1.38 % / 1.92 %.  The search spans the whole page width;
# capping it once pinned the odd optimum to the cap and reported a window
# mostly off the page.  Fitted at 1/FIT_SCALE resolution: one step is 0.17
# mm, below the 0.3 mm the edge inset already gives away.
FIT_SCALE = 4
FIT_B_RANGE_MM = (250.0, 297.0)   # the anchor is 4-30 mm above the foot
FOLD_INSET_MM = 0.0               # cut ON the fold; the holes are filled separately
HOLE_FILL_R_MM = 0.4              # radius added to a hole's own before filling
CUT_INSET_MM = EDGE_INSET_MM


def unknown_mask(geom, scale=1):
    w, h = geom["sheet_px"]
    ws, hs = w // scale, h // scale
    ys = np.arange(hs) * scale
    xs = np.arange(ws) * scale
    mm = MM
    top = np.polyval(geom["edges"]["top"], xs) + CUT_INSET_MM * mm
    bot = np.polyval(geom["edges"]["bot"], xs) - CUT_INSET_MM * mm
    outer = np.polyval(geom["edges"]["outer"], ys)
    u = (ys[:, None] < top[None, :]) | (ys[:, None] > bot[None, :])
    if geom["parity"] == "even":
        u |= xs[None, :] < (outer + CUT_INSET_MM * mm)[:, None]
    else:
        u |= xs[None, :] > (outer - CUT_INSET_MM * mm)[:, None]
    if geom["fold"]["poly"]:
        fold = np.polyval(geom["fold"]["poly"], ys)
        if geom["parity"] == "even":
            u |= xs[None, :] > (fold - FOLD_INSET_MM * mm)[:, None]
        else:
            u |= xs[None, :] < (fold + FOLD_INSET_MM * mm)[:, None]
    for cx, cy, dm in geom["holes"]:
        r = (dm / 2 + HOLE_FILL_R_MM) * mm / scale
        cy_, cx_ = cy / scale, cx / scale
        y0, y1 = max(int(cy_ - r) - 1, 0), min(int(cy_ + r) + 2, hs)
        x0, x1 = max(int(cx_ - r) - 1, 0), min(int(cx_ + r) + 2, ws)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        u[y0:y1, x0:x1] |= (yy - cy_) ** 2 + (xx - cx_) ** 2 <= r * r
    return u


def anchor_of(geom):
    """(x, y, source) in sheet px: the wordmark, else fold x and top-trim y."""
    if geom["anchor"]:
        return geom["anchor"]["x"], geom["anchor"]["y"], "logo"
    w, h = geom["sheet_px"]
    top_y = float(np.polyval(geom["edges"]["top"], w / 2))
    if geom["fold"]["poly"]:
        fold_x = float(np.polyval(geom["fold"]["poly"], h / 2))
    else:
        fold_x = float(w - 1 if geom["parity"] == "even" else 0)
    return fold_x, top_y, "fold+top"


def _window_sums(u, W, H):
    """Sum of `u` over every W x H window whose top-left is (x0, y0), for all
    x0 in [-W, w) and y0 in [-H, h): an integral image over `u` padded with
    UNKNOWN (off the frame is not this page)."""
    h, w = u.shape
    pad = np.ones((h + 2 * H, w + 2 * W), np.int64)
    pad[H:H + h, W:W + w] = u
    I = np.zeros((pad.shape[0] + 1, pad.shape[1] + 1), np.int64)
    I[1:, 1:] = pad.cumsum(0).cumsum(1)
    # window top-left at padded (py, px) -> sum = I[py+H, px+W] - I[py, px+W] - I[py+H, px] + I[py, px]
    py = np.arange(0, h + H)          # = y0 + H, y0 in [-H, h)
    px = np.arange(0, w + W)
    return (I[py[:, None] + H, px[None, :] + W] - I[py[:, None], px[None, :] + W]
            - I[py[:, None] + H, px[None, :]] + I[py[:, None], px[None, :]])


def fit_window(geoms):
    W, H = MASTER_W_PX // FIT_SCALE, MASTER_H_PX // FIT_SCALE
    out = {"stats": {}}
    for par in ("even", "odd"):
        acc, n = None, 0
        for g in geoms:
            if g["parity"] != par or not g["anchor"]:
                continue
            u = unknown_mask(g, FIT_SCALE)
            sums = _window_sums(u, W, H)                 # indexed by (y0+H, x0+W)
            ax, ay = g["anchor"]["x"] // FIT_SCALE, g["anchor"]["y"] // FIT_SCALE
            # window top-left (x0, y0) = (ax - S, ay - B); accumulate over (S, B)
            # on a common grid: S in [0, W), B in [Bmin, Bmax]
            Bs = np.arange(int(FIT_B_RANGE_MM[0] * MM) // FIT_SCALE,
                           int(FIT_B_RANGE_MM[1] * MM) // FIT_SCALE + 1)
            Ss = np.arange(0, W)
            y_idx = ay - Bs + H
            x_idx = ax - Ss + W
            ok_y = (y_idx >= 0) & (y_idx < sums.shape[0])
            ok_x = (x_idx >= 0) & (x_idx < sums.shape[1])
            grid = np.full((len(Bs), len(Ss)), W * H, np.int64)   # off-grid = all unknown
            grid[np.ix_(ok_y, ok_x)] = sums[np.ix_(y_idx[ok_y], x_idx[ok_x])]
            acc = grid if acc is None else acc + grid
            n += 1
        if n == 0:
            raise SystemExit(f"{VARIANT} cut: no {par} page has a logo anchor -- "
                             f"nothing to fit the window on")
        bi, si = np.unravel_index(int(acc.argmin()), acc.shape)
        S_, B_ = int(Ss[si] * FIT_SCALE), int(Bs[bi] * FIT_SCALE)
        out[par] = (S_, B_)
        out["stats"][par] = {"pages": n, "mean_unknown": float(acc[bi, si] / (n * W * H))}
    return out


def cut_page(geom, fit, sheet600):
    """The master: sheet600 with the unknown painted white, cut to the window."""
    notes = list(geom["notes"])
    w, h = geom["sheet_px"]
    ax, ay, source = anchor_of(geom)
    S_, B_ = fit[geom["parity"]]
    x0, y0 = int(round(ax - S_)), int(round(ay - B_))
    u = unknown_mask(geom)
    painted = sheet600[:h, :w].copy()
    painted[u] = 255
    master = np.full((MASTER_H_PX, MASTER_W_PX, 3), 255, np.uint8)
    unk = np.ones((MASTER_H_PX, MASTER_W_PX), bool)
    sy0, sy1 = max(y0, 0), min(y0 + MASTER_H_PX, h)
    sx0, sx1 = max(x0, 0), min(x0 + MASTER_W_PX, w)
    if sy1 > sy0 and sx1 > sx0:
        master[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = painted[sy0:sy1, sx0:sx1]
        unk[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = u[sy0:sy1, sx0:sx1]
    frac = float(unk.mean())
    if source != "logo":
        notes.append(f"ANCHOR from {source}: the wordmark was not found")
    return master, frac, notes


def cut():
    geoms = [json.loads(p.read_text()) for p in sorted(OUT_GEOM.glob("[0-9][0-9][0-9].json"))]
    if not geoms:
        raise SystemExit(f"{VARIANT} cut: no geometry in {OUT_GEOM} -- run measure first")
    fit = fit_window(geoms)
    OUT_MASTER.mkdir(parents=True, exist_ok=True)
    report = {"fit": {k: list(v) for k, v in fit.items() if k != "stats"},
              "stats": fit["stats"], "pages": {}}
    for g in geoms:
        stem = f"{g['page']:03d}"
        sheet = np.array(Image.open(OUT_SHEET600 / f"{stem}.png").convert("RGB"))
        master, frac, notes = cut_page(g, fit, sheet)
        ax, ay, source = anchor_of(g)
        stamp = stamp_text(VARIANT, **{
            "page": f"{stem} of {ISSUE}", "phase": "cut",
            "master-px": f"{MASTER_W_PX} {MASTER_H_PX}",
            "skew": f"{g['skew']['angle']:+.2f} -> {g['skew']['residual']:+.2f} deg",
            "fold": f"{g['fold']['source']} n={g['fold']['n']}"
                    + (f" tilt {g['fold']['tilt_deg']:+.2f} deg" if g["fold"]["poly"] else ""),
            "holes": str(len(g["holes"])),
            "anchor": f"{source} ({ax:.0f}, {ay:.0f})"
                      + (f" score {g['anchor']['score']:.2f}" if g["anchor"] else ""),
            "window": f"S {fit[g['parity']][0]} B {fit[g['parity']][1]} ({g['parity']})",
            "unknown": f"{frac:.2%} of the window is fabricated white",
            "notes": "; ".join(notes) or "(none)",
        })
        save_master(master, OUT_MASTER / f"{stem}.png", stamp)
        (OUT_MASTER / f"{stem}.stamp.txt").write_text(stamp, encoding="utf-8")
        report["pages"][stem] = {"anchor": source, "fold": g["fold"]["source"],
                                 "unknown": frac}
        print(f"p{stem}: anchor {source} | fold {g['fold']['source']} | "
              f"unknown {frac:.2%}" + "".join(f"\n      NOTE p{stem}: {n}" for n in notes),
              flush=True)
    (OUT_GEOM / "fit.json").write_text(json.dumps(report, indent=1))
    print("fit:", json.dumps(report["fit"]), json.dumps(report["stats"]), flush=True)
```
Replace the `raise SystemExit("cut: not built yet")` in `__main__` with `cut()`.

- [ ] **Step 4: Run — expect 16 passed**

- [ ] **Step 5: Cut the six measured pages**

```bash
cd tools/img/scan2ocr/rules && ../../../../.venv/bin/python r005_masters_spread.py cut 2>&1 | tail -10
../../../../.venv/bin/python -c "
from PIL import Image; Image.MAX_IMAGE_PIXELS=None
import glob
for f in sorted(glob.glob('/tmp/64er_8610/masters600/*.png')): print(f, Image.open(f).size)"
magick /tmp/64er_8610/masters600/010.png /tmp/64er_8610/masters600/011.png +append -resize 1600x /tmp/64er_8610/masters_10_11.png
```
Expected: six masters at (4961, 7016); on the montage the two pages have the same margins, type not clipped at any edge, no bed/prop/neighbour visible, holes gone, and the fabricated white at the fold is a thin strip. `unknown` ≤ 3 % on pages with a logo. The window fit from six pages is provisional — it is re-fitted over all 200 in Task 11.

- [ ] **Step 6: Commit**

```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.py tools/img/scan2ocr/tests/test_r005_spread.py
git commit -m "r005_masters_spread: cut -- fit the window per parity, cut every master with the unknown painted white"
```

---

### Task 11: The wrapper, the rule, and the full sweep

**Files:**
- Create: `tools/img/scan2ocr/rules/r005_masters_spread.sh`, `tools/img/scan2ocr/rules/r005_masters_spread.md`
- Modify: `tools/img/scan2ocr/README.md`

- [ ] **Step 1: The wrapper**

```bash
#!/bin/bash
# Step 005, SPREAD variant -- measure every page in parallel, then cut.
#
# measure is ~45 s a page and bound by the 900 MB PNG decode and the separator;
# 4 lanes is what this box sustains without swapping (each lane holds a 2400
# dpi RGB sheet, ~1.7 GB, plus the separator's own).  cut is seconds a page and
# runs alone: it needs EVERY page's geometry before it can fit the window.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
cd "$DIR"
FIRST="${1:-1}"
LAST="${2:-$("$PY" -c 'import r005_masters_spread as m; print(m.ISS.pages)')}"
seq "$FIRST" "$LAST" | OMP_NUM_THREADS=1 xargs -P 4 -n 5 "$PY" r005_masters_spread.py measure
"$PY" r005_masters_spread.py cut
```
`chmod +x`.

- [ ] **Step 2: The rule**

`r005_masters_spread.md` — header, then the sections below. Write it in the register of `r005_masters_sheet.md`: what was measured, why each decision, the verification.

```markdown
# 005 — Scan to 600 dpi master, SPREAD variant

**Applies to:** all — but only where the descriptor says `"binding": "spread"`.
A `"binding": "sheet"` issue runs `r005_masters_sheet` instead, and this
variant is then recorded in that issue's `LOG.md` as **not applicable —
binding**.

**Goal:** turn the raw ~2400 dpi scan of one half of a clipped A3 spread into
the levelled, graded, **logo-anchored exact-A4** 600 dpi master that `r010`
OCRs and `r145` cuts figures from.

Program step: the orchestrator runs it, checks the exit status, runs the
Verification block.

## What the paper actually is — measured on 8610's thumbs
(the table from the spec §2, verbatim)

## Two phases
(§3.1 of the spec; the three command lines; what re-runs what)

## `measure`
(§3.2: skew → grade → geometry; the three outer edges; the fold from the
holes with the constants' measured values; the colour-boundary fallback;
the anchor; the debug overlay. State the deviation: the fold is a line
through ≥4 collinear holes, not a template score; the template is added only
if the sweep shows false locks.)

## `cut`
(§3.3: the fit, the fallback anchor, the fills, the stamp fields)

## The fill is fabrication, and it is stated
(as the sheet rule: bed, prop, neighbour, holes, off-frame → paper white)

## Outputs
(§4 of the spec)

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
    band = inside & ~np.roll(inside, b, 0) | inside & ~np.roll(inside, -b, 0)   # 6 mm inside top/bot
    dark = (lum[band] < 70).mean() if band.any() else 0
    prop = prop_mask(rgb)[band].mean() if band.any() else 0
    if dark > 0.02 or prop > 0.002: bad.append((f[:3], "%.3f" % dark, "%.4f" % prop))
print("bands with bed/prop:", bad or "none")
PY

# 7. contact sheet of the overlays, for the eye
magick montage $(ls /tmp/64er_8610/debug600/*.png | head -200) -tile 10x -geometry 200x282+2+2 /tmp/64er_8610/debug_contact.png
```

## What it read, on the full sweep
(filled in after Task 11 Step 5 — the numbers, the pages looked at, what
each NOTE turned out to be)
```

- [ ] **Step 3: README paragraph**

In `tools/img/scan2ocr/README.md`, under *Requirements* where step 005's two variants are named, add: "`r005_masters_spread` runs in two phases — `measure` per page, `cut` once for the issue — because its A4 window is one fit per parity over the wordmark anchors of every page. `r005_masters_spread.sh` runs both."

- [ ] **Step 4: Numbering check, unit tests, commit**

```bash
tools/img/scan2ocr/rules/r000_verify_numbering.sh | tail -4
cd tools/img/scan2ocr && ../../../.venv/bin/python -m pytest tests -q 2>&1 | tail -2
git add tools/img/scan2ocr/rules/r005_masters_spread.sh tools/img/scan2ocr/rules/r005_masters_spread.md tools/img/scan2ocr/README.md
git commit -m "r005_masters_spread: the wrapper and the rule"
```

- [ ] **Step 5: The full sweep (background, ~2.5 h)**

```bash
cd tools/img/scan2ocr/rules && rm -rf /tmp/64er_8610 && nohup ./r005_masters_spread.sh > /tmp/64er_8610_r005.log 2>&1 &
```
Watch `grep -c '^p[0-9]' /tmp/64er_8610_r005.log` and `df -h /tmp`. When done: `grep -E 'FAILED|NOTE' /tmp/64er_8610_r005.log | sort | uniq -c | sort -rn | head -40`.

- [ ] **Step 6: Run the Verification block; look at every LOOK AT page**

Run every numbered check from Step 2. For each page the fit report lists — no logo, no fold, unknown > 4 % — open `debug600/NNN.png` and `masters600/NNN.png` (scaled) and write one line per page into the rule's *What it read* section: what the page is, what happened, whether it is right. Typical: covers and full-page ads have no wordmark (fold+top anchor is expected); a page whose neighbour is a full-bleed ad may have `fold colour`.

If a class of failure appears (e.g. > 10 pages with `fold none`, or a logo false-positive locking onto a headline), that is a constant to re-measure or the template scoring from the spec to add — do it, re-run `measure` on the affected pages (`r005_masters_spread.py measure N …`), then `cut`, then re-verify. Record the numbers in the constant's comment.

- [ ] **Step 7: LOG.md dispositions and commit**

`issues/8610/LOG.md` (git-ignored, the work log) — two entries per r000:
```markdown
## Step 005 (masters_spread) — ran and verified

<date>. 200/200 masters at 4961x7016, grade <sha>. Fit: even S=… B=…, odd S=… B=….
Anchor: logo N / fold+top N. Fold: holes N / colour N / none N. Unknown p50/p95: even …/…, odd …/….
Pages looked at: … (one line each, in r005_masters_spread.md "What it read").

## Step 005 (masters_sheet) — not applicable — binding

Variant selector: `issues/8610/issue.json` → `"binding": "spread"` → the `masters_spread` variant runs. No files touched.
```
Commit the rule with its filled-in results:
```bash
git add tools/img/scan2ocr/rules/r005_masters_spread.md tools/img/scan2ocr/rules/r005_masters_spread.py
git commit -m "r005_masters_spread: what the full 8610 sweep read"
```

---

## Self-review

**Spec coverage.** §1 stale things → Tasks 1, 2. §2 measured form → docstring (Task 4), rule (Task 11). §3.1 two phases → Tasks 4, 10, 11. §3.2 measure: skew/grade (4), edges (5), fold holes (6), colour fallback (7), anchor (8), JSON + overlay (9). §3.3 cut: fit, fallback anchor, fills, stamp, fit.json → Task 10. §3.4 shared library + byte-identity gate → Task 3. §3.5 descriptor → Task 1. §4 outputs → Tasks 4, 9, 10. §5 verification 1–9 → Task 11 Step 2 (checks 1–7; 8 = check 6; 9 = the contact sheet). §6 out of scope → none planned. **One stated deviation:** the fold uses a collinearity fit instead of the rigid-template score (Task 6), measured on the sweep before deciding to add the template.

**Type consistency.** `outer_edges` returns polys; `unknown_mask` reads `geom["edges"][k]` as lists — `np.polyval` accepts both. `fit_window` returns `{"even": (S, B), "odd": (S, B), "stats": …}` and `cut_page` indexes `fit[geom["parity"]]` — consistent. `anchor_of` returns 3-tuple; `cut` unpacks 3. `stamp_text(variant, **fields)` everywhere after Task 3. `find_logo` returns `x, y` = outer-bottom corner; `fit_window` uses `anchor["x"], anchor["y"]`; tests assert the corner convention.

**Placeholders.** None in code. Task 11 Step 2's rule body is an outline for prose the executor writes from the spec sections named — the Verification block and headings are complete.
