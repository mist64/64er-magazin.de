# 010 — OCR the scans into measured blocks

**Goal:** turn the deskewed, matted, A4-cropped, graded **600 dpi masters** into
one JSON per page describing every block on it: bbox, printed type size, indent,
ink density, a geometric label, and the block's text with the printed line
breaks undone. Plus the per-page block index every later bbox step reads.

This is a **program step**: the orchestrator runs it and checks the verification
block. There is no editorial judgement in it and nothing to dispatch.

## Inputs

- `SRC_DIR` — the graded 600 dpi masters, one PNG per page (constant at the top
  of `010_ocr_blocks.py`; produced by `scan2mrc`'s `pipeline.sh --only master,final`)
- `tesseract` 5.x with the **`deu`** traineddata

## Run

```bash
tools/img/scan2ocr/rules/010_ocr_blocks.sh          # all 176 pages
tools/img/scan2ocr/rules/010_ocr_blocks.sh 39 41    # a page range
```

The programs themselves live one level up in `tools/img/scan2ocr/` and keep
importable names — a Python module cannot start with a digit, and `classify`
imports `ocr_blocks`. The numbered `.sh` beside this file is the entry point,
and it carries the parallelism, which is not a detail: numpy stages want
`OMP_NUM_THREADS=1` and many lanes, and this box is shared with a job that
swap-thrashes if crowded.

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
out/blocks/pNNN.txt   the block index: bbox in MASTER pixels + text preview
```

`out/blocks/pNNN.txt` replaces the old rule `9b`, which re-OCR'd the
delivered PDF and reduced the TSV with awk. This step already OCR'd every page
and already knows every bbox, so the index is a projection of data we have. It
costs no OCR and cannot disagree with the corpus.

**Coordinate space — read before cropping.** The bboxes are in pixels of the
graded 600 dpi master, which is deskewed and A4-cropped. They are **not** in the
delivered PDF's page space; the PDF page is neither deskewed nor cropped, so the
two differ by a rotation and an offset. Crop from the master:

```bash
grep -iE "listing|tabelle|bild" out/blocks/p145.txt
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
  the text tells them apart. See `COLSPLIT_*` in `010_ocr_blocks.py`.
- a hyphen at a line end becomes `¬` rather than being resolved. German writes
  one for three different reasons and no local rule separates them; step 030
  resolves them.

## Verification

```bash
cd "$(dirname "$0")/.." 2>/dev/null || cd tools/img/scan2ocr
dir=$(python3 -c "import ocr_blocks; print(ocr_blocks.OUT_DIR)")

# 1. every page produced a JSON, a digest and an overlay
ls $dir/*.json | grep -vc 'labels' ; ls $dir/*.digest.txt | wc -l ; ls $dir/*_boxes.png | wc -l

# 2. the block index covers every page that has blocks
ls $dir/blocks/p*.txt | wc -l

# 3. no page silently produced nothing
python3 - <<'PY'
import glob, json, os
import ocr_blocks as OB
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
- Constants live at the top of `010_ocr_blocks.py`, heavily commented. No CLI knobs,
  no env knobs — different agents used an env surface differently once and
  produced numbers for files that never existed.
