#!/usr/bin/env python3
"""
Reconstruct article text from LLM-produced block ordering + Tesseract TSV.

Reads a JSON file describing per-page block ordering (produced by an LLM
sub-agent from tsv_layout.py output) and the corresponding TSV files.
Outputs concatenated body text in reading order, followed by non-body
blocks grouped by type (captions, asides, etc.).

Usage:
    python3 tools/png2mag/tsv_reading_order.py order.json tmp/022_ocr.tsv
    python3 tools/png2mag/tsv_reading_order.py order.json tmp/020_ocr.tsv tmp/021_ocr.tsv ...

JSON format expected:
{
  "pages": [
    {
      "page": "022",
      "body": [
        {"block": 5},
        {"block": 12, "type": "h2"},
        ...
      ],
      "non_body": [
        {"block": 16, "type": "caption"},
        {"block": 7, "type": "image"},
        ...
      ]
    }
  ]
}
"""

import json
import sys
import argparse

from tsv_layout import read_word_data, extract_page_num


# Non-body types that have extractable text content
TEXT_TYPES = {'caption', 'aside', 'listing'}

# Non-body types silently dropped (no text to extract)
SKIP_TYPES = {'header', 'footer', 'image', 'discard'}


def load_order(json_path):
    """Load and validate the JSON block ordering file."""
    with open(json_path) as f:
        data = json.load(f)
    if 'pages' not in data:
        print("Error: JSON must have a 'pages' key", file=sys.stderr)
        sys.exit(1)
    return data


def build_tsv_map(tsv_paths):
    """Map page numbers to TSV paths and preloaded word data.

    Returns dict: page_str -> {path, word_data}
    """
    tsv_map = {}
    for path in tsv_paths:
        page_num = extract_page_num(path)
        tsv_map[page_num] = {
            'path': path,
            'word_data': read_word_data(path),
        }
    return tsv_map


def get_block_text(word_data, block_num):
    """Get the full text for a block, or None if not found."""
    info = word_data.get(block_num)
    if info is None:
        return None
    return info.full_text


def format_marker(page, block_num, block_type=None):
    """Format a block marker line like [page 022, block 5] or [page 022, block 12, h3]."""
    if block_type:
        return f"[page {page}, block {block_num}, {block_type}]"
    return f"[page {page}, block {block_num}]"


def reconstruct(order_data, tsv_map):
    """Walk the ordering and produce output sections.

    Returns (body_lines, non_body_sections) where non_body_sections is
    a dict mapping type -> list of (marker, text) pairs.
    """
    body_lines = []
    non_body = {}  # type -> [(marker, text), ...]

    for page_info in order_data['pages']:
        page = page_info['page']

        if page not in tsv_map:
            print(f"Warning: page {page} in JSON but no matching TSV file",
                  file=sys.stderr)
            continue

        word_data = tsv_map[page]['word_data']

        # Body blocks
        for entry in page_info.get('body', []):
            block_num = entry['block']
            block_type = entry.get('type')
            text = get_block_text(word_data, block_num)
            if text is None:
                print(f"Warning: page {page} block {block_num} not found in TSV",
                      file=sys.stderr)
                continue
            marker = format_marker(page, block_num, block_type)
            body_lines.append(marker)
            body_lines.append(text)
            body_lines.append('')

        # Non-body blocks
        for entry in page_info.get('non_body', []):
            block_num = entry['block']
            block_type = entry.get('type', 'unknown')

            if block_type in SKIP_TYPES:
                continue

            text = get_block_text(word_data, block_num)
            if text is None:
                continue

            marker = format_marker(page, block_num, block_type)
            if block_type not in non_body:
                non_body[block_type] = []
            non_body[block_type].append((marker, text))

    return body_lines, non_body


def main():
    parser = argparse.ArgumentParser(
        description='Reconstruct article text from JSON block ordering + TSV files')
    parser.add_argument('json_file', help='JSON block ordering file')
    parser.add_argument('tsv_files', nargs='+', help='Tesseract TSV file(s)')
    args = parser.parse_args()

    order_data = load_order(args.json_file)
    tsv_map = build_tsv_map(args.tsv_files)

    body_lines, non_body = reconstruct(order_data, tsv_map)

    # Output body
    print('--- BODY ---')
    for line in body_lines:
        print(line)

    # Output non-body sections
    for section_type in sorted(non_body.keys()):
        entries = non_body[section_type]
        print(f'--- {section_type.upper()} ---')
        for marker, text in entries:
            print(marker)
            print(text)
            print()


if __name__ == '__main__':
    main()
