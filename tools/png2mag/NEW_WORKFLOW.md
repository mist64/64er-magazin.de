# NEW_WORKFLOW: Block-level OCR Pipeline

## Quick Start

```
# Full run from scratch (single page)
python3 tools/png2mag/run_pipeline.py issues/8604 053 053 --clean

# Multi-page article
python3 tools/png2mag/run_pipeline.py issues/8604 053 057 --clean

# Resume after an agent step
python3 tools/png2mag/run_pipeline.py issues/8604 053 053 --step 5
```

The driver script `run_pipeline.py` orchestrates all steps. It pauses at agent steps (2, 4, 6) and prints manifests. Launch the agents from the conversation, then resume with `--step N`.

## Overview

Per-page, block-level extraction pipeline:

| Step | Type | Script/Prompt | What |
|------|------|---------------|------|
| 1 | Script | `extract_blocks.py` | Tesseract → per-block PNGs + TXTs + layout.txt + classify.txt |
| 2 | Agent | `classify_agent_prompt.txt` | Classify blocks (body/header/footer) + reading order |
| 3 | Script | `apply_classify.py` | headers.txt + body_blocks.txt |
| 4 | Agent | `block_agent_prompt.txt` | Per-block OCR correction + HTML conversion |
| 5 | Script | `concat_blocks.py` | Join block HTMLs with `{{newblock}}`/`{{newpage}}` markers |
| 6 | Agent | `join_agent_prompt.txt` | Fix overlaps, splits, duplicates, figure placement |
| 7 | Script | `assemble_article.py` | Wrap in article HTML shell with metadata |

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

## Steps 2-3: Classification Agent + Apply

Prompt template: `tools/png2mag/classify_agent_prompt.txt`

A classification agent receives `layout.txt` + `overview.png` and edits `classify.txt`. Each TEXT block gets one of:
- `body` — article content
- `head1` — running header (article section name, e.g. "Anwendung des Monats")
- `head2` — running header (computer name, e.g. "C 64")
- `footer_issue` — issue line ("Ausgabe N/Monat JJJJ")
- `footer_page` — page number
- `listing` — machine code/BASIC listing content (hex dumps, DATA lines). NOT transcribed.
- `listing_caption` — caption for a listing. Append corrected text after tab.
- `skip` — rules, image artifacts, noise

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
- `body_blocks.txt` — one block number per line (body blocks only, in reading order)
- `listings.txt` — one listing caption per line (only if listing_caption blocks found). These are appended as `<figure><pre>TODO</pre><figcaption>...</figcaption></figure>` at the end of the article by step 7.

## Step 4: Sub-agent Correction

Prompt template: `tools/png2mag/block_agent_prompt.txt`

The driver script (`run_pipeline.py --step 4`) copies each `block_NN.txt` → `block_NN.html` and writes `block_agent_manifest.json`. Launch one sub-agent per block (they can run in parallel). Each agent reads the block PNG + HTML and edits the HTML in place.

Key conversion rules (see prompt for full details):
- `{{indent}}` → `<p>`, `{{flush}}` → `<p class="noindent">`
- `{{fsize:N}}` ≥15 → `<h1>`, ≤3 → `<pre>`
- Bold standalone lines → `<h3>`
- Dash lists → `<ul><li>`
- Tabelle → `<figure>` with `<table>` + `<figcaption>`
- Bild → `<figure>` (no figcaption unless visible)
- Bare code → `<pre>` (no figure). Labeled Listing → `<figure><pre>...<figcaption>`
- Author → `<address class="author">`

## Step 5: Concatenation

Script: `tools/png2mag/concat_blocks.py`

```
python3 tools/png2mag/concat_blocks.py <blocks_dir> [<blocks_dir2> ...]
```

Reads `body_blocks.txt` from each blocks_dir. Concatenates `block_NN.html` files in reading order into `article_draft.html` (in the parent `tmp/` dir), with `{{newblock}}` between blocks and `{{newpage:NNN}}` between pages.

## Step 6: Join Agent Pass

Prompt template: `tools/png2mag/join_agent_prompt.txt`

The join agent receives `article_draft.html` + full page PNG(s) + overview PNG(s). It fixes:

- **Overlapping blocks**: Tesseract sometimes creates overlapping blocks. Keep the complete version, remove duplicate.
- **Split paragraphs**: Join `</p>` + `{{newblock}}` + `<p>` into one `<p>`.
- **Cross-block hyphens**: Join hyphenated words across block boundaries.
- **Duplicate content**: Deduplicate (e.g. author credit appearing in two blocks). Prefer better markup.
- **Figure/table placement**: Merge detached `<figcaption>` into `<figure>`. Place Tabelle/Bild after first reference. Listings at end of article. Author sticks to preceding paragraph.
- **Remove all markers**: Delete `{{newblock}}` and `{{newpage:NNN}}`.

## Step 7: Final Assembly

Script: `tools/png2mag/assemble_article.py`

```
python3 tools/png2mag/assemble_article.py <article_draft.html> <issue_dir> <start_page> <end_page>
```

Wraps the joined body HTML in the article shell. Extracts metadata mechanically:

| Field | Source |
|-------|--------|
| `<title>` | `<h1>` in the draft |
| `author` | `<address class="author">` if present |
| `64er.issue` | issue dir name (YYMM → M/YY) |
| `64er.pages` | start_page - end_page |
| `64er.head1`, `head2` | `headers.txt` from step 3 |
| `toc_*`, `index_*` | `<!-- TODO -->` placeholders for manual QA |
| `64er.id` | `TODO` placeholder |

Output: `issues/NNNN/PPP Title.html`

---

## Observations

- 300 DPI gives better block grouping than 600 DPI (16 blocks vs 22).
- Drop cap issue mostly resolved at 300 DPI — Tesseract merges the initial letter with body.
- No padding on crops — padding caused overlap between adjacent blocks.
- `{{fsize:N}}` reliably identifies titles (≥15), headers (6-14), and code (≤3). Italic subheadings have same fsize as body — sub-agent identifies these from the image.
