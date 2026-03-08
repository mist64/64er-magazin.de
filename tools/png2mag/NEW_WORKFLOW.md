# NEW_WORKFLOW: Block-level OCR Pipeline

## Overview

Per-page, block-level extraction pipeline:

1. **Block detection + extraction** — `extract_blocks.py` runs Tesseract, identifies blocks, classifies them (header/footer/body), crops PNGs, writes annotated TXT.
2. **Header/footer extraction** — Script separates headers and footers into `headers.txt`, removes them from the block set.
3. **Sub-agent correction** — Each body block's PNG + TXT goes to a sub-agent for OCR correction and HTML conversion.
4. **Concatenation** — Script concatenates corrected block HTMLs with `{{newblock}}` markers between them.
5. **Join agent pass** — A second agent pass fixes `{{newblock}}` boundaries: joins split paragraphs across blocks, resolves cross-block hyphens.
6. **Final assembly** — Wrap in article HTML shell with metadata from headers and TOC.

## Step 1: Block Detection and Extraction

Script: `tools/png2mag/extract_blocks.py`

```
python3 tools/png2mag/extract_blocks.py <page_png> <output_dir>
```

Output dir should be `issues/NNNN/tmp/pNNN_blocks/` (NOT `/tmp/` — Tesseract sandbox issue).

Produces per block:
- `block_NN.png` — cropped from 600 DPI source
- `block_NN.txt` — OCR text with `{{flush}}`/`{{indent}}` and `{{fsize:N}}` annotations

Also produces:
- `layout.txt` — compact layout summary (from `tsv_layout.py`) with block positions, sizes, font sizes, text previews
- `classify.txt` — initial classification file with all blocks set to `body`
- `overview.png` — annotated page image with numbered block rectangles

Key details:
- Downscales 600→300 DPI for Tesseract (its optimal DPI).
- Runs TSV + hOCR together for font size detection.
- Coordinates scaled 2x back to 600 DPI for cropping.

## Step 2: Header/Footer Classification

Prompt template: `tools/png2mag/classify_agent_prompt.txt`

A classification agent receives `layout.txt` + `overview.png` and edits `classify.txt`. Each TEXT block gets one of:
- `body` — article content
- `head1` — running header (article section name, e.g. "Anwendung des Monats")
- `head2` — running header (computer name, e.g. "C 64")
- `footer_issue` — issue line ("Ausgabe N/Monat JJJJ")
- `footer_page` — page number

For head1/head2, the corrected text is appended after a tab:
```
block_01: head2	C 64
block_17: head1	Anwendung des Monats
```

After classification, run `tools/png2mag/apply_classify.py`:

```
python3 tools/png2mag/apply_classify.py <blocks_dir> [<page_num>]
```

This reads `classify.txt` and produces:
- `headers.txt` — one line: `PAGE NNN: head1=... | head2=...`
- `body_blocks.txt` — one block number per line (body blocks only, used by steps 3-4)

## Step 3: Sub-agent Correction

Prompt template: `tools/png2mag/block_agent_prompt.txt`

For each body block:
1. Copy `block_NN.txt` → `block_NN.html`
2. Launch sub-agent with the prompt (substituting `{block_png}` and `{block_html}`)
3. Sub-agent reads the PNG and edits the .html in place — fixing OCR and adding markup

## Step 4: Concatenation

Script concatenates all `block_NN.html` files (body blocks only, in reading order) into `page_NNN.html`, with `{{newblock}}` on a line by itself between each block:

```html
<h3>Quiz erstellen</h3>
<p>Um Fragen und Titelbilder...</p>
{{newblock}}
<p>Einbau von Titelbildern</p>
<p>Wovon hängt es denn nun ab...</p>
{{newblock}}
...
```

For multi-page articles, page HTMLs are concatenated with `{{newpage:NNN}}` markers.

## Step 5: Join Agent Pass

A second agent receives the concatenated HTML + the full page image(s). It fixes block boundaries:

- Paragraphs split across blocks: remove `{{newblock}}`, join the `</p>` and `<p>` into one `<p>`.
- Hyphens at block boundaries: join words across blocks (same rules as line-break hyphens).
- Verify reading order is correct.
- Remove all `{{newblock}}` and `{{newpage}}` markers.

## Step 6: Final Assembly

Wrap the joined HTML body in the article shell:
- `<head>` metadata from TOC TSV + headers.txt
- `<article>` wrapper
- Standard stylesheet link

---

## Observations

- 300 DPI gives better block grouping than 600 DPI (16 blocks vs 22).
- Drop cap issue mostly resolved at 300 DPI — Tesseract merges the initial letter with body.
- No padding on crops — padding caused overlap between adjacent blocks.
- `{{fsize:N}}` reliably identifies titles (≥15), headers (6-14), and code (≤3). Italic subheadings have same fsize as body — sub-agent identifies these from the image.
