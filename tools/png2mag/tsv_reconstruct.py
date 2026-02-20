#!/usr/bin/env python3
"""
Reconstruct reading-order text from Tesseract TSV output.

Reads a TSV file produced by `tesseract ... tsv`, groups words into lines,
assigns columns by x-coordinate clustering, and outputs text in column order.

Usage:
    python3 tools/tsv_reconstruct.py _work/021_ocr.tsv [--width 2480]

Options:
    --width W           Page width in pixels (default: 2480)
    --boundaries X,X,X  Explicit band boundaries (e.g. 400,1000,1600,2480)
    --annotate          Prefix each line with block/band/x/y metadata
    --dump-blocks       Show block summary with x/y ranges (for layout analysis)

Output goes to stdout. Redirect to _work/<NNN>_ocr.txt.
"""

import csv
import sys
import argparse
from collections import defaultdict


def read_tsv(path):
    """Read TSV and return list of word-level rows."""
    words = []
    with open(path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['level'] == '5' and row['text'].strip():
                words.append({
                    'block': int(row['block_num']),
                    'par': int(row['par_num']),
                    'line': int(row['line_num']),
                    'word': int(row['word_num']),
                    'left': int(row['left']),
                    'top': int(row['top']),
                    'width': int(row['width']),
                    'height': int(row['height']),
                    'conf': float(row['conf']),
                    'text': row['text'],
                })
    return words


def group_lines(words):
    """Group words into lines keyed by (block, par, line)."""
    lines = {}
    for w in words:
        key = (w['block'], w['par'], w['line'])
        if key not in lines:
            lines[key] = {
                'block': w['block'],
                'left': w['left'],
                'top': w['top'],
                'words': [],
            }
        lines[key]['words'].append(w['text'])
        # Track minimum left for the line
        lines[key]['left'] = min(lines[key]['left'], w['left'])
    return lines


def get_block_stats(lines):
    """Compute per-block min-left and y-range."""
    blocks = defaultdict(lambda: {'min_left': 99999, 'max_left': 0,
                                   'min_top': 99999, 'max_top': 0,
                                   'line_count': 0})
    for key, data in lines.items():
        b = blocks[data['block']]
        b['min_left'] = min(b['min_left'], data['left'])
        b['max_left'] = max(b['max_left'], data['left'])
        b['min_top'] = min(b['min_top'], data['top'])
        b['max_top'] = max(b['max_top'], data['top'])
        b['line_count'] += 1
    return dict(blocks)


def detect_bands(block_stats, page_width):
    """Auto-detect column bands from block x-positions using gap analysis.

    Uses median x-position of narrow blocks (width < 40% page) to avoid
    wide-spanning elements (tables, full-width headings) from bridging gaps.
    """
    if not block_stats:
        return [page_width]

    # Use median left of narrow blocks for clustering
    narrow_threshold = page_width * 0.4
    positions = []
    for bid, b in block_stats.items():
        block_width = b['max_left'] - b['min_left']
        if block_width < narrow_threshold:
            # Use min_left as the column indicator
            positions.append(b['min_left'])

    if not positions:
        # Fall back to all blocks if no narrow ones
        positions = [b['min_left'] for b in block_stats.values()]

    lefts = sorted(set(positions))
    if len(lefts) <= 1:
        return [page_width]

    # Find gaps between clusters
    gaps = []
    for i in range(1, len(lefts)):
        gap = lefts[i] - lefts[i - 1]
        gaps.append((gap, lefts[i - 1], lefts[i]))

    # Sort gaps by size, largest first
    gaps.sort(reverse=True)

    # Use significant gaps (> 10% of page width) as band boundaries
    threshold = page_width * 0.10
    boundaries = []
    for gap, left_val, right_val in gaps:
        if gap >= threshold:
            boundaries.append((left_val + right_val) // 2)

    boundaries.sort()
    boundaries.append(page_width)
    return boundaries


def assign_bands(lines, block_stats, boundaries):
    """Assign each line a band number based on its block's min_left."""
    for key, data in lines.items():
        block_left = block_stats[data['block']]['min_left']
        band = 0
        for i, boundary in enumerate(boundaries):
            if block_left < boundary:
                band = i + 1
                break
        data['band'] = band


def reconstruct(lines, annotate=False):
    """Sort lines by band then top, return as text lines."""
    # Group by band
    by_band = defaultdict(list)
    for key, data in lines.items():
        by_band[data['band']].append((data['top'], key, data))

    # Sort each band by top
    for band in by_band:
        by_band[band].sort()

    # Emit in band order
    result = []
    for band in sorted(by_band.keys()):
        for top, key, data in by_band[band]:
            text = ' '.join(data['words'])
            if annotate:
                result.append(f"b{data['block']:2d} B{data['band']} x={data['left']:4d} y={data['top']:4d}  {text}")
            else:
                result.append(text)

    return result


def dump_blocks(block_stats, boundaries):
    """Print block summary for layout analysis."""
    print(f"Band boundaries: {boundaries}")
    print(f"{'Block':>5}  {'Lines':>5}  {'x-range':>15}  {'y-range':>15}  {'Band':>4}")
    print("-" * 55)
    for block_id in sorted(block_stats.keys()):
        b = block_stats[block_id]
        # Determine band
        band = 0
        for i, boundary in enumerate(boundaries):
            if b['min_left'] < boundary:
                band = i + 1
                break
        print(f"{block_id:5d}  {b['line_count']:5d}  {b['min_left']:6d}-{b['max_left']:<6d}  "
              f"{b['min_top']:6d}-{b['max_top']:<6d}  B{band}")


def main():
    parser = argparse.ArgumentParser(description='Reconstruct text from Tesseract TSV')
    parser.add_argument('tsv_file', help='Input TSV file')
    parser.add_argument('--width', type=int, default=2480, help='Page width in pixels')
    parser.add_argument('--boundaries', type=str, default=None,
                        help='Explicit band boundaries, comma-separated (e.g. 400,1000,1600,2480)')
    parser.add_argument('--annotate', action='store_true', help='Add block/band/position metadata')
    parser.add_argument('--dump-blocks', action='store_true', help='Show block summary')
    args = parser.parse_args()

    words = read_tsv(args.tsv_file)
    lines = group_lines(words)
    block_stats = get_block_stats(lines)

    if args.boundaries:
        boundaries = [int(x) for x in args.boundaries.split(',')]
    else:
        boundaries = detect_bands(block_stats, args.width)

    if args.dump_blocks:
        dump_blocks(block_stats, boundaries)
        return

    assign_bands(lines, block_stats, boundaries)
    result = reconstruct(lines, annotate=args.annotate)

    for line in result:
        print(line)


if __name__ == '__main__':
    main()
