#!/usr/bin/env python3
"""Concatenate corrected block HTMLs into a single article draft.

Usage:
    python3 tools/png2mag/concat_blocks.py <blocks_dir> [<blocks_dir2> ...]

Example:
    # Single page
    python3 tools/png2mag/concat_blocks.py issues/8604/tmp/p053_blocks

    # Multi-page article
    python3 tools/png2mag/concat_blocks.py issues/8604/tmp/p053_blocks issues/8604/tmp/p054_blocks

Reads body_blocks.txt from each blocks_dir. Concatenates block_NN.html files
in reading order with {{newblock}} markers between blocks and {{newpage:NNN}}
between pages.

Output: article_draft.html in the first blocks_dir's parent (tmp/) directory.
"""

import os
import re
import sys


def read_body_blocks(blocks_dir):
    """Read body_blocks.txt and return list of block numbers."""
    path = os.path.join(blocks_dir, 'body_blocks.txt')
    if not os.path.exists(path):
        print(f'Error: {path} not found', file=sys.stderr)
        sys.exit(1)
    blocks = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                blocks.append(int(line))
    return blocks


def extract_page_num(blocks_dir):
    """Extract page number from dir name like p053_blocks -> 053."""
    m = re.search(r'p(\d{3})_blocks', blocks_dir)
    return m.group(1) if m else '???'


def concat_blocks(blocks_dirs):
    """Concatenate all block HTMLs across pages into article_draft.html."""
    parts = []

    for i, blocks_dir in enumerate(blocks_dirs):
        page_num = extract_page_num(blocks_dir)
        body_blocks = read_body_blocks(blocks_dir)

        if i > 0:
            parts.append(f'{{{{newpage:{page_num}}}}}')

        for j, bnum in enumerate(body_blocks):
            html_path = os.path.join(blocks_dir, f'block_{bnum:02d}.html')
            if not os.path.exists(html_path):
                print(f'Warning: {html_path} not found, skipping', file=sys.stderr)
                continue

            if j > 0:
                parts.append('{{newblock}}')

            with open(html_path) as f:
                content = f.read().strip()
            parts.append(content)

    # Write to parent dir of first blocks_dir
    parent = os.path.dirname(blocks_dirs[0].rstrip('/'))
    output_path = os.path.join(parent, 'article_draft.html')
    with open(output_path, 'w') as f:
        f.write('\n'.join(parts) + '\n')

    total_blocks = sum(len(read_body_blocks(d)) for d in blocks_dirs)
    print(f'article_draft   {output_path}  ({total_blocks} blocks, {len(blocks_dirs)} page(s))')
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)
    concat_blocks(sys.argv[1:])
