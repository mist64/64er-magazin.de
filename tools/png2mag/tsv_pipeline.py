#!/usr/bin/env python3
"""
OCR pipeline: page PNGs → Tesseract → layout analysis → LLM block ordering.

Runs OCR on all pages first, generates a combined layout summary, then
sends ALL pages to a single LLM call so the agent has a global view of
the article and can verify cross-page text continuity.

Usage:
    # All pages of an article (PNG must be 600 DPI cropped master)
    python3 tools/png2mag/tsv_pipeline.py png/020_600_cropped.png png/021_600_cropped.png ... --tmp ./tmp

    # Skip OCR if TSV/hOCR already exist
    python3 tools/png2mag/tsv_pipeline.py png/020_600_cropped.png ... --tmp ./tmp --skip-ocr

    # Custom model
    python3 tools/png2mag/tsv_pipeline.py png/020_600_cropped.png ... --tmp ./tmp --model opus

    # Save output to file
    python3 tools/png2mag/tsv_pipeline.py png/020_600_cropped.png ... --tmp ./tmp -o tmp/order.json
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Add tools dir to path so we can import siblings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tsv_layout import format_page, extract_page_num


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = r"""You are a layout analysis expert. You will receive page layout summaries
from ALL pages of an OCR'd magazine article. Your job is to classify and
order all blocks on every page.

The pages are from a German computer magazine (multi-column layout). Use
the block positions (x,y coordinates), sizes, font sizes (f=), line
counts, and text previews to make your decisions.

**Guidelines:**

- **Body** text blocks (small font, many lines) form the main article
  text flow.
- **H2 subheadings** (larger font, 1–3 lines, centered or free-standing
  between body blocks) are part of the body flow. Mark with `"type": "h2"`.
- Reading order within columns is top-to-bottom. Column order is
  generally left-to-right, but VERIFY by checking text continuity at
  block boundaries.
- **CRITICAL — text continuity check:** The text preview shows the first
  and last words/sentences of each block. Use these to verify reading
  order:
  - If Block A's preview ends with a hyphenated word fragment like
    "verschaf-" and Block B starts with "fen.", then B must immediately
    follow A.
  - Always check these continuation patterns to confirm the correct
    sequence, especially across column boundaries AND across page
    boundaries.
- **CRITICAL — cross-page continuity:** You have ALL pages of the
  article. Verify that the last body block on each page connects
  properly to the first body block on the next page. Check for
  hyphenated words, mid-sentence breaks, dangling prepositions, etc.
- **Asides/tables**: boxed or visually separated sections (spec tables,
  info boxes, sidebars) go into the `"asides"` dict. Each aside gets a
  short ID and an **ordered** block list (heading first, then content
  in reading order). Aside headings get `"heading": true`.
- Short blocks near images that start with "Bild N." are CAPTION blocks.
- Very short blocks at page top/bottom edges (especially with page
  numbers or magazine names) are HEADER/FOOTER — mark for discard.
- HRULEs and VRULEs are structural separators, not content — ignore them.

**Page layouts:**

{layout}

**Your output:**

First, show your reasoning: list the text continuity checks at block
boundaries (within and across pages) so the logic is visible. Then
output a JSON block.

The JSON must follow this exact structure:

```json
{{
  "pages": [
    {{
      "page": "020",
      "body": [
        {{"block": 5}},
        {{"block": 12, "type": "h2"}},
        {{"block": 13}}
      ],
      "asides": {{
        "specs": [
          {{"block": 6, "heading": true}},
          {{"block": 7}},
          {{"block": 15}}
        ],
        "lastminute": [
          {{"block": 26, "heading": true}},
          {{"block": 27}}
        ]
      }},
      "non_body": [
        {{"block": 1, "type": "header"}},
        {{"block": 16, "type": "caption"}},
        {{"block": 7, "type": "image"}}
      ]
    }}
  ]
}}
```

Rules:
- One page object per page, in page order.
- `body`: ordered list of article text blocks in reading order.
  Add `"type": "h2"` for subheadings. No type = regular body text.
- `asides`: dict mapping aside ID → ordered block list. Use a short
  descriptive slug as key (e.g. `"specs"`, `"lastminute"`, `"bio"`).
  Blocks within each aside are ordered (heading first, then content
  in reading order). Mark heading blocks with `"heading": true`.
  Omit `asides` key if a page has none.
- `non_body`: flat list for everything else. Each entry has `"block"`
  and `"type"`. Types: `"header"`, `"footer"`, `"caption"`, `"image"`,
  `"discard"`."""


# ---------------------------------------------------------------------------
# Phase 1: OCR (all pages)
# ---------------------------------------------------------------------------

def extract_page_num_from_png(png_path):
    """Extract page number from PNG filename like 027_600_cropped.png → 027."""
    basename = os.path.basename(png_path)
    m = re.match(r'(\d{3})', basename)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot extract page number from: {png_path}")


def run_ocr(png_path, tmp_dir, page_num):
    """Downscale 600→300 DPI, run Tesseract producing TSV + hOCR.

    Returns (tsv_path, hocr_path).
    """
    p300 = os.path.join(tmp_dir, f'{page_num}_300.png')
    ocr_base = os.path.join(tmp_dir, f'{page_num}_ocr')
    tsv_path = ocr_base + '.tsv'
    hocr_path = ocr_base + '.hocr'

    # Downscale
    if not os.path.exists(p300):
        print(f'  Downscaling {png_path} → {p300}', file=sys.stderr)
        subprocess.run(
            ['magick', png_path, '-resize', '50%', p300],
            check=True)
    else:
        print(f'  Reusing {p300}', file=sys.stderr)

    # Tesseract
    if not os.path.exists(tsv_path) or not os.path.exists(hocr_path):
        print(f'  Running Tesseract → {tsv_path}, {hocr_path}', file=sys.stderr)
        subprocess.run(
            ['tesseract', p300, ocr_base,
             '-l', 'deu', '--psm', '1',
             '-c', 'hocr_font_info=1', 'tsv', 'hocr'],
            check=True)
    else:
        print(f'  Reusing {tsv_path}, {hocr_path}', file=sys.stderr)

    return tsv_path, hocr_path


# ---------------------------------------------------------------------------
# Phase 2: LLM block ordering (single call, all pages)
# ---------------------------------------------------------------------------

def call_claude(prompt, model='sonnet'):
    """Call claude CLI in print mode, return response text.

    Uses --output-format json to get structured output, extracts the
    result text from the JSON envelope.
    """
    # Strip CLAUDECODE env var so claude -p works even when called
    # from within a Claude Code session during development/testing
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE'}

    result = subprocess.run(
        ['claude', '-p', '--model', model, '--output-format', 'json',
         '--no-session-persistence'],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    if result.returncode != 0:
        print(f'  claude CLI error (rc={result.returncode}):', file=sys.stderr)
        print(f'  stderr: {result.stderr[:500]}', file=sys.stderr)
        raise RuntimeError('claude CLI failed')

    # --output-format json wraps in {"type":"result","result":"..."}
    envelope = json.loads(result.stdout)
    return envelope.get('result', result.stdout)


def extract_json_from_response(text):
    """Extract JSON object from LLM response that may contain reasoning text.

    Looks for a JSON code block (```json...```) or the last { ... } block.
    """
    # Try ```json ... ``` first
    m = re.search(r'```json\s*\n(\{.*?\})\s*\n```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    # Try last top-level { ... }
    # Find all balanced braces (greedy from last {)
    depth = 0
    start = None
    last_obj = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                last_obj = text[start:i + 1]

    if last_obj:
        return json.loads(last_obj)

    raise ValueError('No JSON object found in LLM response')


def order_pages(combined_layout, model='sonnet'):
    """Send combined layout for all pages to LLM, get back block ordering JSON."""
    prompt = PROMPT_TEMPLATE.format(layout=combined_layout)
    print(f'  Calling Claude ({model}) with {combined_layout.count("Page ")} page(s)...',
          file=sys.stderr)
    response = call_claude(prompt, model=model)
    result = extract_json_from_response(response)

    # Validate basic structure
    if 'pages' not in result:
        raise ValueError(f'LLM response missing "pages" key: {list(result.keys())}')
    for page_obj in result['pages']:
        if 'page' not in page_obj:
            raise ValueError(f'Page object missing "page" key')
        if 'body' not in page_obj:
            raise ValueError(f'Page {page_obj.get("page", "?")} missing "body" key')

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='OCR pipeline: page PNGs → layout → LLM block ordering')
    parser.add_argument('png_files', nargs='+',
                        help='600 DPI cropped page PNG(s)')
    parser.add_argument('--tmp', required=True,
                        help='Directory for intermediate files (TSV, hOCR, etc.)')
    parser.add_argument('--model', default='sonnet',
                        help='Claude model to use (default: sonnet)')
    parser.add_argument('--skip-ocr', action='store_true',
                        help='Skip OCR if TSV/hOCR files already exist')
    parser.add_argument('--layout-only', action='store_true',
                        help='Stop after layout generation (skip LLM call)')
    parser.add_argument('-o', '--output',
                        help='Output JSON file (default: stdout)')
    args = parser.parse_args()

    os.makedirs(args.tmp, exist_ok=True)

    # Phase 1: OCR all pages
    print('Phase 1: OCR', file=sys.stderr)
    page_data = []  # list of (page_num, tsv_path, hocr_path)
    for png_path in args.png_files:
        page_num = extract_page_num_from_png(png_path)
        print(f'  Page {page_num}:', file=sys.stderr)

        tsv_path = os.path.join(args.tmp, f'{page_num}_ocr.tsv')
        hocr_path = os.path.join(args.tmp, f'{page_num}_ocr.hocr')

        if args.skip_ocr and os.path.exists(tsv_path) and os.path.exists(hocr_path):
            print(f'    Skipping OCR (--skip-ocr, files exist)', file=sys.stderr)
        else:
            tsv_path, hocr_path = run_ocr(png_path, args.tmp, page_num)

        page_data.append((page_num, tsv_path, hocr_path))

    # Phase 1b: Generate combined layout for all pages
    print('\nPhase 1b: Layout analysis', file=sys.stderr)
    layout_parts = []
    for page_num, tsv_path, hocr_path in page_data:
        layout = format_page(tsv_path, hocr_path)
        layout_parts.append(layout)
        print(f'  Page {page_num}: {layout.count(chr(10)) + 1} lines', file=sys.stderr)

    combined_layout = '\n\n'.join(layout_parts)

    if args.layout_only:
        print(combined_layout)
        return

    # Phase 2: Single LLM call with all pages
    print(f'\nPhase 2: LLM block ordering ({len(page_data)} pages)', file=sys.stderr)
    result = order_pages(combined_layout, model=args.model)

    # Summarize
    for page_obj in result['pages']:
        n_body = len(page_obj.get('body', []))
        n_aside = sum(len(v) for v in page_obj.get('asides', {}).values())
        n_non = len(page_obj.get('non_body', []))
        print(f'  Page {page_obj["page"]}: {n_body} body, {n_aside} aside, {n_non} non-body',
              file=sys.stderr)

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output + '\n')
        print(f'\nWrote {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
