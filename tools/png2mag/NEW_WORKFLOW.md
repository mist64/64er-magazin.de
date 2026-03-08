# NEW_WORKFLOW: Block-level OCR Pipeline

## Overview

Per-page, block-level extraction pipeline. Each magazine page is processed as follows:

1. **Block detection + extraction** — Tesseract identifies text blocks; each is cropped to PNG + TXT.
2. **Sub-agent correction** — Each block's PNG + OCR text goes to a sub-agent for visual verification.
3. **Assembly** — Corrected blocks are combined into final article HTML.

## Step 1 + 2: Block Detection and Extraction

Script: `tools/png2mag/extract_blocks.py`

```
python3 tools/png2mag/extract_blocks.py <page_png> <output_dir>
```

Produces per block: `block_NN.png` (cropped from 600 DPI source) and `block_NN.txt` (OCR text).

Key details:
- Input PNGs are 600 DPI masters. The script downscales to 300 DPI for Tesseract (its optimal DPI).
- Block coordinates from 300 DPI are scaled 2x back to 600 DPI for cropping the original.
- No padding is added — Tesseract's exact bounding boxes are used to avoid overlap between adjacent blocks.
- Canvas offset (`+repage`) is stripped before cropping.

### Example: Page 053 Block Map (at 300 DPI / after downscale)

| Block | Size (600dpi) | Content summary |
|-------|---------------|-----------------|
| 01 | 404x188 | "C 64" (header left) |
| 03 | 2218x804 | "Quizmaster" title + subtitle |
| 04 | 2208x320 | Body start (drop cap "Z" merged) |
| 06 | 2216x1252 | Body continuation |
| 09 | 2218x2600 | "Quiz erstellen" section (large) |
| 14 | 2214x402 | "Einbau von Titelbildern" |
| 17 | 1576x200 | "Anwendung des Monats" (header right) |
| 18 | 2218x4126 | Right column (large) |
| 23 | 2212x870 | "Hinweise zum Eintippen" |
| 27-28 | ~2200x150 | Titelbild continuation sentences |
| 29 | 2214x910 | "Der Zeichensatz" |
| 31 | 680x132 | Footer "Ausgabe 4/April 1986" |
| 33 | 1964x1098 | Memory address table + attribution |
| 37 | 1466x160 | "Tabelle 1" caption |
| 38 | 668x196 | Page number "53" |

## Step 3: Sub-agent Correction

Prompt template: `tools/png2mag/block_agent_prompt.txt`

For each block:
1. Copy `block_NN.txt` → `block_NN.html`
2. Launch sub-agent with the prompt (substituting `{block_png}` and `{block_html}`)
3. Sub-agent reads the PNG and edits the .html in place — fixing OCR and adding markup

### Observations

- 300 DPI gives better block grouping than 600 DPI (16 blocks vs 22). Fewer fragmented paragraphs.
- Drop cap issue mostly resolved — Tesseract merges the initial letter with the body at 300 DPI.
- No padding added — padding caused overlap between adjacent blocks (e.g. blocks 04 and 06 shared 75px + 40px padding).
