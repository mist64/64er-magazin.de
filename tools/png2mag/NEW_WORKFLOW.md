# NEW_WORKFLOW: Block-level OCR Pipeline

## Overview

Per-page, block-level extraction pipeline:

1. **Block detection + extraction** — `extract_blocks.py` runs Tesseract, crops per-block PNGs + annotated TXTs, writes `layout.txt` + `classify.txt` + `overview.png`.
2. **Classification agent** — Agent reads `layout.txt` + `overview.png`, edits `classify.txt` with block types and reading order.
3. **Apply classification** — `apply_classify.py` reads `classify.txt`, writes `headers.txt` + `body_blocks.txt`.
4. **Sub-agent correction** — Each body block's PNG + TXT goes to a sub-agent for OCR correction and HTML conversion.
5. **Concatenation** — `concat_blocks.py` joins block HTMLs with `{{newblock}}`/`{{newpage}}` markers.
6. **Join agent pass** — Agent fixes block/page boundaries: joins split paragraphs, resolves cross-block hyphens.
7. **Final assembly** — `assemble_article.py` wraps in article HTML shell with metadata from headers + TOC.

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

## Step 4: Sub-agent Correction

Prompt template: `tools/png2mag/block_agent_prompt.txt`

Script: `tools/png2mag/run_block_agents.py` (TODO)

```
python3 tools/png2mag/run_block_agents.py <blocks_dir>
```

For each block listed in `body_blocks.txt`:
1. Copy `block_NN.txt` → `block_NN.html`
2. Launch sub-agent with the prompt (substituting `{block_png}` and `{block_html}`)
3. Sub-agent reads the PNG and edits the .html in place — fixing OCR and adding markup

Sub-agents run independently per block. They can be parallelized.

## Step 5: Concatenation

Script: `tools/png2mag/concat_blocks.py` (TODO)

```
python3 tools/png2mag/concat_blocks.py <blocks_dir> [<blocks_dir2> ...]
```

Reads `body_blocks.txt` from each blocks_dir. Concatenates `block_NN.html` files in reading order into a single `article_draft.html`, with `{{newblock}}` on a line by itself between blocks from the same page, and `{{newpage:NNN}}` between pages.

For single-page articles, one blocks_dir. For multi-page, pass all page dirs in order.

Example output:
```html
<h1>Quizmaster</h1>
<p class="intro">Prüfungsvorbereitungen oder Party-Gag...</p>
{{newblock}}
<p>Zunächst eine Funktionsbeschreibung...</p>
{{newblock}}
<h3>Quiz erstellen</h3>
<p>Um Fragen und Titelbilder...</p>
{{newpage:054}}
<p>Continuation from previous page...</p>
{{newblock}}
...
```

## Step 6: Join Agent Pass

Prompt template: `tools/png2mag/join_agent_prompt.txt` (TODO)

The join agent receives `article_draft.html` + the full page PNG(s) for all pages of the article. It fixes block/page boundaries:

- **Split paragraphs**: When a paragraph is split across blocks (ending `</p>` + `{{newblock}}` + starting `<p>`), join into one `<p>`. Check the page image to confirm they are the same paragraph.
- **Cross-block hyphens**: If a block ends with a hyphenated word and the next starts with the continuation, join them (same rules as line-break hyphens).
- **Cross-page continuations**: Same as above but across `{{newpage}}` markers.
- **Reading order verification**: Confirm the text flows naturally. Flag if something looks wrong.
- **Remove all markers**: Delete all `{{newblock}}` and `{{newpage:NNN}}` lines.

Output: cleaned `article_draft.html` with no markers.

## Step 7: Final Assembly

Script: `tools/png2mag/assemble_article.py` (TODO)

```
python3 tools/png2mag/assemble_article.py <article_draft.html> <issue_dir> <start_page> <output_html>
```

The script drives everything. It reads the article body from `article_draft.html` and stamps in all metadata to produce the final HTML file.

### Metadata sources

| Field | Source | How |
|-------|--------|-----|
| `<title>` | article body | Script extracts from `<h1>` in the draft |
| `author` | article body | Script extracts from `<address class="author">` if present |
| `64er.issue` | issue dir name | Script derives from YYMM (e.g. `8604` → `4/86`) |
| `64er.pages` | start_page + page count | Script computes from blocks_dirs used |
| `64er.head1` | `headers.txt` | Script reads from step 3 output |
| `64er.head2` | `headers.txt` | Script reads from step 3 output |
| `64er.toc_title` | placeholder | `<!-- TODO -->` — filled in during manual QA |
| `64er.toc_category` | placeholder | `<!-- TODO -->` — filled in during manual QA |
| `64er.index_title` | placeholder | `<!-- TODO -->` — filled in during manual QA |
| `64er.index_category` | placeholder | `<!-- TODO -->` — filled in during manual QA |
| `64er.id` | agent | Script asks agent to choose a short id based on article content |

### Agent calls from the script

The script makes minimal agent calls for values it cannot determine mechanically:

- **`64er.id`**: Agent receives the article title + first paragraph and returns a short snake_case identifier (e.g. `quizmaster_listings`). Single-shot, no file editing.

### Output

The script produces the complete HTML file — no further agent involvement:

```html
<!DOCTYPE html>
<html lang="de">

<head>
    <title>Quizmaster</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../style.css">
    <meta name="author" content="">
    <meta name="64er.issue" content="4/86">
    <meta name="64er.pages" content="53-57">
    <meta name="64er.head1" content="Anwendung des Monats">
    <meta name="64er.head2" content="C 64">
    <!-- <meta name="64er.toc_title" content="TODO"> -->
    <!-- <meta name="64er.toc_category" content="TODO"> -->
    <!-- <meta name="64er.index_title" content="TODO"> -->
    <!-- <meta name="64er.index_category" content="TODO"> -->
    <meta name="64er.id" content="quizmaster_listings">
</head>

<body>
    <article>
        ...body content from article_draft.html...
    </article>
</body>
</html>
```

---

## Observations

- 300 DPI gives better block grouping than 600 DPI (16 blocks vs 22).
- Drop cap issue mostly resolved at 300 DPI — Tesseract merges the initial letter with body.
- No padding on crops — padding caused overlap between adjacent blocks.
- `{{fsize:N}}` reliably identifies titles (≥15), headers (6-14), and code (≤3). Italic subheadings have same fsize as body — sub-agent identifies these from the image.
