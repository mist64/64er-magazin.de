# 010 — OCR the scans into measured blocks

**Goal:** turn the deskewed, matted, A4-cropped, graded **600 dpi masters** into
one JSON per page describing every block on it: bbox, printed type size, indent,
ink density, a geometric label, and the block's text with the printed line
breaks undone. Plus the per-page block index every later bbox step reads.

This is a **program step**: the orchestrator runs it and checks the verification
block. There is no editorial judgement in it and nothing to dispatch.

## Inputs

- `SRC_DIR` — the graded 600 dpi masters, one PNG per page (constant at the top
  of `r010_ocr_blocks.py`; produced by step 005 of this chain — `r005_masters_spread`
  or `r005_masters_sheet`, whichever the issue descriptor's `binding` selects. Both
  variants write the same `masters600/NNN.png` contract, so this step is unaffected
  by which one ran.)
- `tesseract` 5.x with the **`deu`** traineddata

## Run

```bash
tools/img/scan2ocr/rules/r010_ocr_blocks.sh          # all 176 pages
tools/img/scan2ocr/rules/r010_ocr_blocks.sh 39 41    # a page range
```

The programs sit beside this file and share its name. The `r` prefix is what
makes that possible: a Python module name cannot start with a digit, so
`r010_ocr_blocks` is importable by name where `010_ocr_blocks` was not. The
numbered `.sh` is the entry point, and it carries the parallelism, which is not
a detail: numpy stages want `OMP_NUM_THREADS=1` and many lanes, and this box is
shared with a job that swap-thrashes if crowded.

~15 minutes for 176 pages. Deterministic and local — no model is called.

**After any change to this step, wipe `OUT_DIR` and start again from page 1.**
Step 020 caches its verdict per page keyed on the block ids this step produces;
the cache is discarded automatically when they no longer match, but a partial
`OUT_DIR` mixing two runs is not something any downstream check can see.

## Outputs

```
out/NNN.json          blocks: bbox, features, geometric label, text
out/NNN.digest.txt    compact page brief for step 020
out/NNN_boxes.png     overlay — every block outlined, id printed
out/NNN.article.txt   PROVISIONAL text from geometry alone; step 020 overwrites it
<OUT_DIR>/blocks/pNNN.txt   the block index: bbox in MASTER pixels + text preview
```

`<OUT_DIR>/blocks/pNNN.txt` replaces the old rule `9b`, which re-OCR'd the
delivered PDF and reduced the TSV with awk. This step already OCR'd every page
and already knows every bbox, so the index is a projection of data we have. It
costs no OCR and cannot disagree with the corpus.

**Coordinate space — read before cropping.** The bboxes are in pixels of the
graded 600 dpi master, which is deskewed and A4-cropped. They are **not** in the
delivered PDF's page space; the PDF page is neither deskewed nor cropped, so the
two differ by a rotation and an offset. Crop from the master:

```bash
grep -iE "listing|tabelle|bild" <OUT_DIR>/blocks/p145.txt
magick <SRC_DIR>/145.png -crop 2136x574+390+3736 +repage /tmp/64er_crop.png
```

`frac=` on each line is the same box as a fraction of the page, for cropping a
render at any other resolution.

## What this step decides, and what it refuses to decide

It measures. Where a measurement has two defensible readings it produces **all
of them** and leaves the choice to step 020, which can read the text:

- a block whose lines all break at the same x holds two things side by side, and
  the block carries `read_alt` with the `rows` and `down` readings beside the
  default across-reading. A table row and a woven line are the same shape; only
  the text tells them apart. See `COLSPLIT_*` in `r010_ocr_blocks.py`.
- a hyphen at a line end becomes `¬` rather than being resolved. German writes
  one for three different reasons and no local rule separates them; step 030
  resolves them.

## Paragraphs and subheads inside a block — where `###` comes from

Roles from step 020 are per **block**, but a body block can hold headings, so
this step splits each block into paragraphs and marks which of them are subheads.
That mark is what step 030 writes as `### `, so a wrong mark here becomes an
`<h3>` in the published article.

The measurement is the **face**, made per word: `stroke_weight()` is the mean
length of a horizontal ink run, compared against the block's own median line.
Three rules follow from it, and all three exist because of a defect they fixed:

- **A word is bold, or it is not.** Weight is a property of the stroke. The
  earlier test used ink coverage of the line's bounding box, which a short line
  inflates through missing word spaces and missing descenders — that alone
  produced 51 of the 80 `###` in the 8609 corpus, every one of them a paragraph's
  orphan line (`### Puffern`, `### MHz.`, `### 89 Mark.`). See `FINDINGS.md` §3.
- **A change of face opens a paragraph — once.** The break belongs where the bold
  run begins; inside the run the short lines, hanging indents and leading are the
  compositor breaking lines. Per line it cut standfirsts into one paragraph per
  line and promoted the leftover fragment to a heading.
- **A subhead is bold in every word**, and at most `SUBHEAD_MAX_LINES` long. A
  glossary entry that opens with a bold run-in term and finishes in body type is
  a paragraph, not a heading.

Constants: `BOLD_STROKE_RATIO`, `SUBHEAD_MIN_BOLD_WORD_FRAC`, `SUBHEAD_MAX_LINES`,
each with its measurement in the comment above it.

## Verification

```bash
cd tools/img/scan2ocr/rules
dir=$(python3 -c "import r010_ocr_blocks as OB; print(OB.OUT_DIR)")

# 1. every page produced a JSON, a digest and an overlay
ls $dir/*.json | grep -vc 'labels' ; ls $dir/*.digest.txt | wc -l ; ls $dir/*_boxes.png | wc -l

# 2. the block index covers every page that has blocks
ls $dir/blocks/p*.txt | wc -l

# 3. no page silently produced nothing
python3 - <<'PY'
import glob, json, os
import r010_ocr_blocks as OB
empty = [f for f in sorted(glob.glob(os.path.join(OB.OUT_DIR, "[0-9][0-9][0-9].json")))
         if not json.load(open(f, encoding="utf-8"))["blocks"]]
print("pages with zero blocks:", [os.path.basename(f) for f in empty] or "none")
PY
```

A page with zero blocks is a failure unless it is genuinely blank — check its
overlay before accepting it.

## Notes

- **Read `FINDINGS.md` before changing anything here.** It records what was
  measured on this paper and, more usefully, the ideas that looked obviously
  right and made the corpus worse.
- Constants live at the top of `r010_ocr_blocks.py`, heavily commented. No CLI knobs,
  no env knobs — different agents used an env surface differently once and
  produced numbers for files that never existed.

## The drop-cap splice was corrupting text — gated 2026-08

`splice_dropcap()` removes an ornamental initial's word and prepends its letter
to the paragraph's first line. Its test accepted **any** word taller than
`DROPCAP_H_RATIO x median`, up to 4 characters, starting uppercase, **anywhere
in the block** — then prepended the letter to line 0 regardless of where the
match was found, and **deleted the word it matched**.

MEASURED over all 176 pages of 8609: it fired **173 times and was correct 4
times.**

The visible symptom was doubled initials (`WWichtig`, `DDer`, `BBrillant`,
`EEPSON`). The serious symptom was silent word **deletion**, which leaves
grammatical text that no spell-check or markup gate can see:

```
p21  "Bild 2 Schriftbildtest …"  ->  "B2 Schritildtest …"
p92  IBM        p87  DM        p102 Bei        p129 Wir
```

The gate tests what an ornamental initial physically is: exactly one character,
flush with the block's top-left, 2–4 body lines tall, in a block of >= 3 lines.
`DROPCAP_MAX_CHARS` is retired — taking `text[0]` of a 4-character token is what
let `'WW:'` (confidence 0.0) and `'De'` (9.2) through.

Validation: stage A re-run over all 176 pages before and after. 158 blocks
change, every one a corruption removal; no correct text is altered. Applying the
result to issue 8609 required **no** article edits — the hand review had already
caught every corruption that reached published text.

**Not changed: `rejoin_dropcap_lines()`** (same file) uses the same loose test.
It only reattaches lines to a block — geometry, not text — so a false positive
there merges lines rather than deleting words. It is a candidate for the same
gate, but it was identical in both validation runs, so tightening it would be
unvalidated. Do that as its own before/after experiment.

Note this does NOT fix drop caps the OCR never detects at all (`asin Ausgabe
4/86` for `Das in Ausgabe 4/86`), nor mid-word doublings (`Programmiierung`,
`Rüickumschlages`, `MO®S`), which are genuine tesseract misreads.
