#!/usr/bin/env python3
"""Read classify.txt, extract headers into headers.txt, produce body_blocks.txt.

Usage:
    python3 tools/png2mag/apply_classify.py <blocks_dir> [<page_num>]

Example:
    python3 tools/png2mag/apply_classify.py issues/8604/tmp/p053_blocks 053

If page_num is omitted, it is inferred from the directory name (pNNN_blocks).

Input:  <blocks_dir>/classify.txt
Output: <blocks_dir>/headers.txt   — one line: PAGE NNN: head1=... | head2=...
        <blocks_dir>/body_blocks.txt — one block number per line (body blocks only, in reading order)
"""

import os
import re
import sys


def apply_classify(blocks_dir, page_num=None):
    classify_path = os.path.join(blocks_dir, 'classify.txt')
    if not os.path.exists(classify_path):
        print(f'Error: {classify_path} not found', file=sys.stderr)
        sys.exit(1)

    # Infer page number from dir name if not given
    if page_num is None:
        m = re.search(r'p(\d{3})_blocks', blocks_dir)
        if m:
            page_num = m.group(1)
        else:
            page_num = '???'

    head1 = None
    head2 = None
    body_blocks = []
    listing_captions = []

    with open(classify_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: block_NN: classification[\ttext]
            m = re.match(r'block_(\d+):\s+(\S+)(?:\t(.*))?', line)
            if not m:
                continue
            block_num = int(m.group(1))
            classification = m.group(2)
            text = m.group(3) or ''

            if classification == 'head1':
                head1 = text
            elif classification == 'head2':
                head2 = text
            elif classification == 'body':
                # Only include if the block file exists (merged blocks are gone)
                txt_path = os.path.join(blocks_dir, f'block_{block_num:02d}.txt')
                if os.path.exists(txt_path):
                    body_blocks.append(block_num)
                # else: block was merged into another, silently skip
            elif classification == 'listing_caption':
                listing_captions.append(text)
            elif classification == 'listing' and text:
                # Listing block with embedded caption (merged during extraction)
                listing_captions.append(text)
            # footer_issue, footer_page, listing (without caption), skip → ignored

    # Write headers.txt
    headers_path = os.path.join(blocks_dir, 'headers.txt')
    parts = []
    if head1:
        parts.append(f'head1={head1}')
    if head2:
        parts.append(f'head2={head2}')
    with open(headers_path, 'w') as f:
        f.write(f'PAGE {page_num}: {" | ".join(parts)}\n')
    print(f'headers         {headers_path}')

    # Write body_blocks.txt
    body_path = os.path.join(blocks_dir, 'body_blocks.txt')
    with open(body_path, 'w') as f:
        for bnum in body_blocks:
            f.write(f'{bnum:02d}\n')
    print(f'body_blocks     {body_path}  ({len(body_blocks)} blocks)')

    # Ensure .html exists for each body block (copy from .txt if missing)
    created_html = 0
    for bnum in body_blocks:
        txt_path = os.path.join(blocks_dir, f'block_{bnum:02d}.txt')
        html_path = os.path.join(blocks_dir, f'block_{bnum:02d}.html')
        if not os.path.exists(html_path):
            import shutil
            shutil.copy2(txt_path, html_path)
            created_html += 1
    if created_html:
        print(f'html_init       {created_html} .html files created from .txt')

    # Write listings.txt (if any listing captions found)
    if listing_captions:
        listings_path = os.path.join(blocks_dir, 'listings.txt')
        with open(listings_path, 'w') as f:
            for caption in listing_captions:
                f.write(caption + '\n')
        print(f'listings        {listings_path}  ({len(listing_captions)} listings)')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)
    blocks_dir = sys.argv[1]
    page_num = sys.argv[2] if len(sys.argv) > 2 else None
    apply_classify(blocks_dir, page_num)
