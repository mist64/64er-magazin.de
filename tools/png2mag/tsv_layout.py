#!/usr/bin/env python3
"""
Page layout analysis for LLM-driven block ordering.

Reads Tesseract TSV files (one per page), optionally paired with hOCR files
for font size information, and produces a compact, LLM-friendly page layout
summary suitable for a sub-agent to determine reading order.

Output includes:
- Page dimensions
- HRULE/VRULE one-liners for thin blocks
- IMAGE blocks (bounding box only, no words)
- TEXT blocks with line count, median word height, font size, and text preview

Usage:
    # Single page (TSV only)
    python3 tools/png2mag/tsv_layout.py tmp/022_ocr.tsv

    # Single page with hOCR for font size
    python3 tools/png2mag/tsv_layout.py tmp/022_ocr.tsv --hocr tmp/022_ocr.hocr

    # Multi-page article
    python3 tools/png2mag/tsv_layout.py tmp/020_ocr.tsv tmp/021_ocr.tsv tmp/022_ocr.tsv \\
      --hocr tmp/020_ocr.hocr tmp/021_ocr.hocr tmp/022_ocr.hocr
"""

import csv
import re
import sys
import argparse
from collections import Counter, defaultdict
from statistics import median
from html.parser import HTMLParser


# ---------------------------------------------------------------------------
# TSV reading
# ---------------------------------------------------------------------------

def read_block_boxes(tsv_path):
    """Parse level=2 rows for block bounding boxes.

    Returns dict mapping block_num -> (left, top, width, height).
    """
    blocks = {}
    with open(tsv_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['level'] == '2':
                block_num = int(row['block_num'])
                blocks[block_num] = (
                    int(row['left']),
                    int(row['top']),
                    int(row['width']),
                    int(row['height']),
                )
    return blocks


def read_page_size(tsv_path):
    """Parse level=1 row for page dimensions.

    Returns (width, height).
    """
    with open(tsv_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['level'] == '1':
                return int(row['width']), int(row['height'])
    return 2480, 3508  # fallback


class BlockInfo:
    """Aggregated word-level data for one block."""
    __slots__ = ('word_count', 'line_count', 'word_heights', 'lines', 'full_text')

    def __init__(self):
        self.word_count = 0
        self.line_count = 0
        self.word_heights = []
        self.lines = defaultdict(list)  # (par, line) -> [word_text, ...]
        self.full_text = ''


def read_word_data(tsv_path):
    """Parse level=5 rows, group by block_num.

    Returns dict mapping block_num -> BlockInfo with word_count, line_count,
    median_word_height, per-line word lists, and full_text.
    """
    blocks = defaultdict(BlockInfo)
    line_keys_seen = defaultdict(set)  # block -> set of (par, line)

    with open(tsv_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['level'] != '5':
                continue
            text = row['text'].strip()
            if not text:
                continue

            block_num = int(row['block_num'])
            par_num = int(row['par_num'])
            line_num = int(row['line_num'])
            height = int(row['height'])

            info = blocks[block_num]
            info.word_count += 1
            info.word_heights.append(height)
            info.lines[(par_num, line_num)].append(text)
            line_keys_seen[block_num].add((par_num, line_num))

    # Post-process: compute line counts and full text
    for block_num, info in blocks.items():
        info.line_count = len(line_keys_seen[block_num])
        # Build full text in line order
        sorted_keys = sorted(info.lines.keys())
        text_lines = [' '.join(info.lines[k]) for k in sorted_keys]
        info.full_text = '\n'.join(text_lines)

    return dict(blocks)


# ---------------------------------------------------------------------------
# hOCR reading
# ---------------------------------------------------------------------------

class HOCRFSizeParser(HTMLParser):
    """Extract per-block modal x_fsize from hOCR output.

    hOCR blocks are <div class="ocr_carea"> with id="block_1_N".
    Words are <span class="ocrx_word"> with title containing x_fsize.
    """

    def __init__(self):
        super().__init__()
        self._current_block = None
        self._block_fsizes = defaultdict(list)  # block_num -> [fsize, ...]
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '')
        title = attrs_dict.get('title', '')
        tag_id = attrs_dict.get('id', '')

        # Track block context
        if 'ocr_carea' in classes and tag_id:
            # id format: block_1_N
            m = re.search(r'block_\d+_(\d+)', tag_id)
            if m:
                self._current_block = int(m.group(1))

        # Extract x_fsize from word spans
        if 'ocrx_word' in classes and self._current_block is not None:
            m = re.search(r'x_fsize\s+(\d+)', title)
            if m:
                self._block_fsizes[self._current_block].append(int(m.group(1)))

        self._tag_stack.append((tag, self._current_block))

    def handle_endtag(self, tag):
        if self._tag_stack:
            popped_tag, popped_block = self._tag_stack.pop()
            # If we're closing a block-level div, reset block context
            if popped_tag == 'div' and popped_block is not None:
                # Only reset if this was the block div
                if not any(t == 'div' and b == popped_block for t, b in self._tag_stack):
                    if self._current_block == popped_block:
                        self._current_block = None

    def get_modal_fsizes(self):
        """Return dict mapping block_num -> modal x_fsize."""
        result = {}
        for block_num, fsizes in self._block_fsizes.items():
            if fsizes:
                result[block_num] = Counter(fsizes).most_common(1)[0][0]
        return result


def read_hocr_fsize(hocr_path):
    """Parse hOCR file and extract modal x_fsize per block.

    Returns dict mapping block_num -> modal font size (int).
    """
    if hocr_path is None:
        return {}
    with open(hocr_path) as f:
        content = f.read()
    parser = HOCRFSizeParser()
    parser.feed(content)
    return parser.get_modal_fsizes()


# ---------------------------------------------------------------------------
# Block classification
# ---------------------------------------------------------------------------

def classify_block(block_id, bbox, word_info, page_height):
    """Classify a block as HRULE, VRULE, IMAGE, or TEXT.

    No SKIP logic — the LLM sub-agent decides what is a running header,
    page number, or footer based on context and position.

    Args:
        block_id: block number
        bbox: (left, top, width, height) from level=2
        word_info: BlockInfo or None (None = no words in block)
        page_height: page height in pixels

    Returns one of: "HRULE", "VRULE", "IMAGE", "TEXT"
    """
    left, top, width, height = bbox

    # Rule detection: very thin blocks
    if height <= 10 and width > 10:
        return "HRULE"
    if width <= 10 and height > 10:
        return "VRULE"

    # Image: block exists but has zero words
    if word_info is None or word_info.word_count == 0:
        return "IMAGE"

    return "TEXT"


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_rule(bbox):
    """Format a HRULE or VRULE one-liner.

    Returns e.g. "HRULE y=177  x=173..2368" or "VRULE x=172  y=897..1760"
    """
    left, top, width, height = bbox
    if height <= 10:
        return f"HRULE y={top}  x={left}..{left + width}"
    else:
        return f"VRULE x={left}  y={top}..{top + height}"


def _sentence_split(text):
    """Split text into rough sentences (period/question/exclamation followed by space or end)."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def format_text_preview(word_info):
    """Build text preview: first + last sentence with ellipsis in between.

    If the block has <= 2 sentences, show complete text.
    """
    text = word_info.full_text.strip()
    # Collapse internal newlines to spaces for preview
    text = re.sub(r'\s+', ' ', text)

    sentences = _sentence_split(text)
    if len(sentences) <= 2:
        return text

    first = sentences[0]
    last = sentences[-1]
    # Ensure first sentence ends with punctuation
    if not re.search(r'[.!?]$', first):
        first += ' ' + sentences[1] if len(sentences) > 1 else ''
    return f"{first} … {last}"


def format_block_line(block_id, classification, bbox, word_info=None, fsize=None):
    """Format one block entry for the output.

    TEXT blocks include line count, median height, fsize, and preview.
    IMAGE blocks show just the bounding box.
    """
    left, top, width, height = bbox

    if classification in ("HRULE", "VRULE"):
        return format_rule(bbox)

    parts = [f"Block {block_id:2d}  {classification:<5s}  {left},{top}  {width}x{height}"]

    if classification == "TEXT" and word_info is not None:
        med_h = int(median(word_info.word_heights)) if word_info.word_heights else 0
        stats = f"  {word_info.line_count}ln h={med_h}"
        if fsize is not None:
            stats += f" f={fsize}"
        parts.append(stats)
        preview = format_text_preview(word_info)
        return ''.join(parts) + '\n  "' + preview + '"'

    return ''.join(parts)


# ---------------------------------------------------------------------------
# Page formatting
# ---------------------------------------------------------------------------

def extract_page_num(tsv_path):
    """Try to extract a page number from the filename like tmp/022_ocr.tsv -> 022."""
    m = re.search(r'(\d{3})_ocr\.tsv$', tsv_path)
    if m:
        return m.group(1)
    m = re.search(r'(\d+)_ocr\.tsv$', tsv_path)
    if m:
        return m.group(1).zfill(3)
    return '???'


def format_page(tsv_path, hocr_path=None):
    """Orchestrate: read TSV (and optional hOCR), classify blocks, format output.

    Returns the complete formatted string for one page.
    """
    page_width, page_height = read_page_size(tsv_path)
    block_boxes = read_block_boxes(tsv_path)
    word_data = read_word_data(tsv_path)
    fsize_data = read_hocr_fsize(hocr_path)

    page_num = extract_page_num(tsv_path)
    lines = [f"Page {page_num}  {page_width}x{page_height}", ""]

    # Collect rules first, then other blocks
    rules = []
    blocks = []

    for block_id in sorted(block_boxes.keys()):
        bbox = block_boxes[block_id]
        w_info = word_data.get(block_id)
        cls = classify_block(block_id, bbox, w_info, page_height)

        if cls in ("HRULE", "VRULE"):
            rules.append(format_rule(bbox))
        else:
            fsize = fsize_data.get(block_id)
            blocks.append(format_block_line(block_id, cls, bbox, w_info, fsize))

    # Output: rules first, then blank line, then blocks
    if rules:
        lines.extend(rules)
        lines.append("")

    lines.extend(blocks)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Page layout analysis for LLM-driven block ordering')
    parser.add_argument('tsv_files', nargs='+', help='Tesseract TSV file(s), one per page')
    parser.add_argument('--hocr', nargs='*', default=None,
                        help='hOCR file(s) for font size (same order as TSV files)')
    args = parser.parse_args()

    # Validate hOCR count matches TSV count
    hocr_files = args.hocr or []
    if hocr_files and len(hocr_files) != len(args.tsv_files):
        print(f"Error: {len(args.tsv_files)} TSV files but {len(hocr_files)} hOCR files",
              file=sys.stderr)
        sys.exit(1)

    # Pad hOCR list with None if not provided
    if not hocr_files:
        hocr_files = [None] * len(args.tsv_files)

    for i, (tsv_path, hocr_path) in enumerate(zip(args.tsv_files, hocr_files)):
        if i > 0:
            print()  # blank line between pages
        print(format_page(tsv_path, hocr_path))


if __name__ == '__main__':
    main()
