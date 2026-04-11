# Table Extraction Workflow

How to extract a table from a 1980s German magazine scan into clean HTML. Use this when you encounter a `TODO TABLE` placeholder, or when a missing `Bild N` turns out to be a table rather than a figure.

## When to use this workflow

- The target is a **data table** (rows of cells with short text values), not a schematic diagram
- The source is a scanned magazine page at roughly 150 dpi (`/tmp/<issue>_pages/p-NNN.png`)
- You need verbatim accuracy for values and descriptions — pure vision-only transcription produces too many errors on dense table text

For diagrams with circles, arrows, or spatial layout as meaning, keep them as images (see `img_workflow.md`).

## Tools required

- `tesseract` (5.x with `deu` language pack) — `brew install tesseract tesseract-lang`
- `magick` (ImageMagick) — for cropping and resizing
- Vision (via `Read` on PNGs) — for inspection and OCR error correction

**NO Python / PIL / Pillow.** Shell + `tesseract` + `magick` only.

## The pipeline

### Step 1 — Tesseract TSV on the full page

Run tesseract with `tsv` output to get word-level bounding boxes grouped by layout block:

```bash
tesseract /tmp/8605_pages/p-082.png /tmp/p82_ocr -l deu tsv
```

This writes `/tmp/p82_ocr.tsv` with columns:

```
level  page_num  block_num  par_num  line_num  word_num  left  top  width  height  conf  text
```

- `level=2` rows are **blocks** (layout regions — the thing we care about)
- `level=4` rows are lines
- `level=5` rows are words

### Step 2 — Summarize each block

Group rows by `block_num`, compute each block's bounding box from the union of its word bboxes, and extract a short preview of the block's text. One line per block. Save to `/tmp/<prefix>_blocks.txt`:

```bash
awk -F'\t' 'NR>1 && $1==5 && $12!="" {
  b=$3;
  if (!(b in minL) || $7<minL[b]) minL[b]=$7;
  if (!(b in minT) || $8<minT[b]) minT[b]=$8;
  if (!(b in maxR) || $7+$9>maxR[b]) maxR[b]=$7+$9;
  if (!(b in maxB) || $8+$10>maxB[b]) maxB[b]=$8+$10;
  text[b]=text[b]" "$12;
}
END {
  for (b in text) {
    printf "block=%s bbox=%dx%d+%d+%d text=%s\n",
      b, maxR[b]-minL[b], maxB[b]-minT[b], minL[b], minT[b],
      substr(text[b],1,200);
  }
}' /tmp/p82_ocr.tsv | sort > /tmp/p82_blocks.txt
```

Now `/tmp/p82_blocks.txt` gives you block numbers, pixel bboxes, and the first ~200 characters of each block's OCR text.

### Step 3 — Identify the target block

Two signals decide which block is the table:

1. **Grep the OCR text for a known cell value.** If the article text references values or labels that should appear in the table (e.g. row headers "EDC", "CHC", "MVC"), grep the blocks file:
   ```bash
   grep -i "EDC.*CHC" /tmp/p82_blocks.txt
   ```
   The matching block is almost certainly your target.

2. **Cross-check visually.** Render a low-res thumbnail of the full page and `Read` it:
   ```bash
   magick /tmp/8605_pages/p-082.png -resize 1200x1200\> /tmp/p82_thumb.png
   ```
   Confirm that the block you picked is in the expected spot on the page.

### Step 4 — Crop just that block

Use the bbox from Step 2 and crop the full-resolution scan:

```bash
magick /tmp/8605_pages/p-082.png -crop 1100x1600+120+340 /tmp/p82_table.png
```

If the resulting crop exceeds 2000 px on any axis, also produce a resized copy so it can be safely `Read`:

```bash
magick /tmp/p82_table.png -resize '1800x1800>' /tmp/p82_table_small.png
```

(The resized copy is for vision; the full-res crop is for the second OCR pass.)

### Step 5 — Second-pass OCR on the crop

Run tesseract again, this time on the isolated block, with a PSM hint that matches the block's layout:

- `--psm 6` — "assume a single uniform block of text" (good for compact tables)
- `--psm 4` — "assume a single column of text of variable sizes" (good for narrow tables with variable row heights)

```bash
tesseract /tmp/p82_table.png /tmp/p82_table_ocr -l deu --psm 6
```

This writes `/tmp/p82_table_ocr.txt`. Cropping the block first cuts out the surrounding page noise and usually gives much cleaner text than the full-page OCR from Step 1.

### Step 6 — Vision-corrected HTML assembly

Now `Read` two things in parallel:

1. The cropped image (`/tmp/p82_table_small.png` if resized, else `/tmp/p82_table.png`) — this is the **ground truth**.
2. The second-pass OCR text (`/tmp/p82_table_ocr.txt`) — this is the **scaffold**.

Then:

- Walk through the OCR text row by row.
- For each row, verify values against the image. Fix OCR substitutions (`1` ↔ `l` ↔ `I`, `O` ↔ `0`, `rn` ↔ `m`, `cl` ↔ `d`).
- Preserve old German spelling exactly as printed (`daß`, `muß`, `läßt`, `Schloß`, `ß` — do not modernize).
- Preserve typos printed in the original (`TPYE` for `TYPE`, `SHURE` for `SURE`). The magazine's errors are part of the historical record.
- If a cell is truly illegible even after cropping + OCR, write `[ILLEGIBLE]` rather than guessing.

The OCR text exists on disk — **that is the source**, not your memory. This is the same anti-memory rule as `WORKFLOW.md`: text in context may feel like memory, but it's a file read. Do not compose from general knowledge of the article.

### Step 7 — Emit the HTML

Choose the right HTML shape based on what the scan shows:

- **Bordered data table with headers** → plain `<table>` with `<th>` header row.
- **Borderless glossary/key list** → `<table class="plain">` with no header row.
- **Table with a real caption** → wrap the whole `<table>` in `<figure>` with `<figcaption>`. A "real caption" is text printed on the scan in one of these strict forms:
  - `Tabelle: …`
  - `Tabelle N: …` or `Tabelle N. …`
  - `Bild N: …` or `Bild N. …` (for tables that are labeled as numbered figures)

  Only these explicit caption markers count. **Do NOT promote section headings, bold titles above a table, or OCR'd fragments to `<figcaption>`.** A bold title like "Erklärung der einzelnen Bearbeitungsroutinen" sitting above a table is a heading, not a caption — leave it as-is in the surrounding HTML (typically an `<h3>` or nothing) and emit a bare `<table>`.
- **Table with a heading or no marker at all** → bare `<table>`, no `<figure>`.

Column count should match what's visually on the scan, not what's logically convenient. If a row label and its parenthetical full name share a single cell on the scan, keep them in one `<td>`; don't split into two columns.

## Delegation

This entire pipeline (Steps 1–6) is a good fit for a subagent because:

- It's self-contained and purely mechanical.
- The main thread never needs to see the page pixels — only the final HTML comes back as text.
- The pipeline runs fast once `tesseract` is installed.

Give the subagent the full pipeline spelled out (see `img_workflow.md`'s subagent-delegation rules for the general principle). Ask it to return **only** the final `<table>...</table>` block, plus a short note if any cell was `[ILLEGIBLE]`.

## When you can't decide — log, don't delete

If a TODO, heading, or stray fragment in the HTML looks wrong or orphaned and you can't find a corresponding source on the scan, **do not silently delete it**. Write an entry in the issue's `LOG.md` (create it if it doesn't exist) describing:

- the file and location
- the exact content
- what you looked for and where
- possibilities you considered
- what action a reviewer should take

Then leave the HTML alone and move on. A human can decide later — a deleted orphan cannot be retrieved without scanning git history.

Similarly, when a table cell's value is uncertain even after OCR + vision, prefer a best-effort guess with a LOG.md entry listing the unclear cells over `[ILLEGIBLE]` — but only if the semantic context makes one reading clearly more plausible than the alternatives. When in doubt, `[ILLEGIBLE]` is safer.

## Common pitfalls

- **Skipping Step 1 and jumping straight to vision.** Vision-only transcription on dense table text drops values, transposes digits, and silently invents cells. The second-pass OCR scaffold catches this.
- **Running OCR on the full page and stopping.** Full-page OCR mixes the target table with neighboring columns, ads, and captions. Always crop in Step 4 before the second OCR pass.
- **Resizing before the second OCR pass.** Tesseract does better on the full-resolution crop than on a downscaled one. Only resize for the vision Read, not for the OCR input.
- **Trusting the first subagent that reads the OCR output.** If a subagent reports values and says "I flagged some uncertainty," do not paste its text as-is. Either re-run the pipeline or ask a second subagent to verify the uncertain cells against the crop.
- **Fabricating illegible cells.** If Step 6 can't resolve a cell, write `[ILLEGIBLE]`. The reader can be told to check the scan; a plausible-looking wrong value cannot be retracted.
