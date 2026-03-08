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
    --paragraphs        Add [P]/[Pn] paragraph markers (indent/noindent)
    --dump-blocks       Show block summary with x/y ranges (for layout analysis)

Output goes to stdout. Redirect to _work/<NNN>_ocr.txt.
"""

import csv
import sys
import argparse
from collections import Counter, defaultdict


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
                'right_edge': 0,
                'total_word_width': 0,
                'total_char_count': 0,
                'words': [],
            }
        lines[key]['words'].append(w['text'])
        # Track minimum left for the line
        lines[key]['left'] = min(lines[key]['left'], w['left'])
        # Track maximum right edge for the line
        word_right = w['left'] + w['width']
        lines[key]['right_edge'] = max(lines[key]['right_edge'], word_right)
        # Accumulate for character width estimation
        lines[key]['total_word_width'] += w['width']
        lines[key]['total_char_count'] += len(w['text'])
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


def compute_band_margins(lines):
    """Compute per-band left margins and per-block right margins.

    Returns dict: band -> {left_margin, indent_threshold,
                           block_right: {block_id -> right_margin},
                           short_threshold}
    """
    by_band = defaultdict(list)
    for key, data in lines.items():
        by_band[data['band']].append(data)

    margins = {}
    for band, band_lines in by_band.items():
        if not band_lines:
            continue

        # Left margin: mode of left values binned to 10px
        left_bins = Counter(ln['left'] // 10 * 10 for ln in band_lines)
        left_margin = left_bins.most_common(1)[0][0]

        # Median character width from word-level aggregates
        total_w = sum(ln['total_word_width'] for ln in band_lines)
        total_c = sum(ln['total_char_count'] for ln in band_lines)
        char_width = total_w / total_c if total_c > 0 else 15

        # Per-block right margins: 90th percentile within each block
        by_block = defaultdict(list)
        for ln in band_lines:
            by_block[ln['block']].append(ln['right_edge'])
        block_right = {}
        for block_id, edges in by_block.items():
            edges.sort()
            idx = min(int(len(edges) * 0.9), len(edges) - 1)
            block_right[block_id] = edges[idx]

        margins[band] = {
            'left_margin': left_margin,
            'block_right': block_right,
            'indent_threshold': 2 * char_width,
            'continuation_threshold': char_width,
            'short_threshold': 5 * char_width,
        }

    return margins


def classify_paragraphs(by_band, band_margins):
    """Walk lines in band order and assign paragraph markers.

    Returns list of (marker, top, key, data) in output order.
    Markers: '[P]' = indented start, '[Pn]' = non-indented start, '' = continuation.
    """
    result = []
    for band in sorted(by_band.keys()):
        m = band_margins.get(band)
        prev_right_edge = None
        prev_left = None
        prev_block = None
        for i, (top, key, data) in enumerate(by_band[band]):
            if not m:
                marker = '[Pn]' if i == 0 else ''
            else:
                is_indented = data['left'] > m['left_margin'] + m['indent_threshold']
                # Use previous line's block right margin for short-line detection
                prev_block_right = m['block_right'].get(prev_block, 0) if prev_block else 0
                is_after_short = (prev_right_edge is not None and prev_block_right > 0 and
                                  prev_right_edge < prev_block_right - m['short_threshold'])
                # Continuation: indented but same left as previous line (e.g. drop-cap wrap)
                is_continuation = (is_indented and prev_left is not None and
                                   abs(data['left'] - prev_left) < m['continuation_threshold'])
                if is_continuation:
                    marker = ''
                elif is_indented:
                    marker = '[P]'
                elif i == 0 or is_after_short:
                    marker = '[Pn]'
                else:
                    marker = ''
            result.append((marker, top, key, data))
            prev_right_edge = data['right_edge']
            prev_left = data['left']
            prev_block = data['block']
    return result


def reconstruct(lines, annotate=False, paragraphs=False, band_margins=None):
    """Sort lines by band then top, return as text lines."""
    # Group by band
    by_band = defaultdict(list)
    for key, data in lines.items():
        by_band[data['band']].append((data['top'], key, data))

    # Sort each band by top
    for band in by_band:
        by_band[band].sort()

    # Classify paragraphs if requested
    if paragraphs and band_margins:
        classified = classify_paragraphs(by_band, band_margins)
    else:
        classified = []
        for band in sorted(by_band.keys()):
            for top, key, data in by_band[band]:
                classified.append(('', top, key, data))

    # Emit lines
    result = []
    for marker, top, key, data in classified:
        text = ' '.join(data['words'])
        parts = []
        if annotate:
            parts.append(f"b{data['block']:2d} B{data['band']} x={data['left']:4d} y={data['top']:4d}")
        if paragraphs and marker:
            parts.append(f"{marker:4s}")
        if parts:
            result.append('  '.join(parts) + '  ' + text)
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
    parser.add_argument('--paragraphs', action='store_true', help='Add [P]/[Pn] paragraph markers')
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

    band_margins = None
    if args.paragraphs:
        band_margins = compute_band_margins(lines)

    result = reconstruct(lines, annotate=args.annotate,
                         paragraphs=args.paragraphs,
                         band_margins=band_margins)

    for line in result:
        print(line)


if __name__ == '__main__':
    main()
