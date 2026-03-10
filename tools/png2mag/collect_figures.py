#!/usr/bin/env python3
"""Collect available figures (images + captions) for an article.

Usage:
    python3 tools/png2mag/collect_figures.py <issue_dir> <start_page> <end_page>

Example:
    python3 tools/png2mag/collect_figures.py issues/8604 133 141

Reads:
- classify.txt from each page's blocks dir (for caption entries)
- Image files P-N.png in the issue dir

Output: prints a figures manifest to stdout (for piping into the agent prompt).
"""

import glob
import os
import re
import sys


def collect(issue_dir, start_page, end_page):
    """Collect all figure info for the article."""
    # 1. Collect captions from classify.txt
    captions = {}  # "Bild 1" -> caption text
    for p in range(int(start_page), int(end_page) + 1):
        classify_path = os.path.join(issue_dir, 'tmp', f'p{p:03d}_blocks', 'classify.txt')
        if not os.path.exists(classify_path):
            continue
        with open(classify_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # caption\tBild 7. Flußdiagramm...
                m = re.match(r'block_\d+:\s*caption\t(.+)', line)
                if m:
                    caption = m.group(1)
                    # Extract Bild/Tabelle number
                    bm = re.match(r'(Bild|Tabelle)\s+(\d+)', caption)
                    if bm:
                        key = f'{bm.group(1)} {bm.group(2)}'
                        captions[key] = caption

    # 2. Collect image files
    sp = int(start_page)
    images = sorted(glob.glob(os.path.join(issue_dir, f'{sp}-*.png')))
    image_fnames = [os.path.basename(img) for img in images]

    # 3. Split images into title images (-0*.png) and Bild images (-[1-9]*.png)
    title_images = []  # -0.png, -00.png, -01.png etc.
    image_map = {}  # "Bild N" -> [filenames]
    for fname in image_fnames:
        m = re.match(rf'{sp}-(0\d*|0)\.png$', fname)
        if m:
            title_images.append(fname)
            continue
        m = re.match(rf'{sp}-(\d+)', fname)
        if m:
            n = m.group(1)
            key = f'Bild {n}'
            image_map.setdefault(key, []).append(fname)

    # 4. Build manifest
    lines = []
    lines.append('## Available figures for this article')
    lines.append('')

    # Title images (no caption, go after intro)
    if title_images:
        lines.append('### Title images (place after intro, no caption)')
        for f in title_images:
            lines.append(f'- {f}')
        lines.append('')

    # Numbered Bild/Tabelle entries (have captions, go inline)
    lines.append('### Numbered figures (place inline near first text reference)')
    lines.append('')

    all_keys = set(list(captions.keys()) + list(image_map.keys()))
    bild_keys = sorted([k for k in all_keys if k.startswith('Bild')],
                       key=lambda k: int(re.search(r'\d+', k).group()))
    tabelle_keys = sorted([k for k in all_keys if k.startswith('Tabelle')],
                          key=lambda k: int(re.search(r'\d+', k).group()))

    for key in bild_keys + tabelle_keys:
        imgs = image_map.get(key, [])
        caption = captions.get(key, '')
        lines.append(f'- **{key}**')
        if imgs:
            lines.append(f'  Files: {", ".join(imgs)}')
        if caption:
            lines.append(f'  Caption: {caption}')
        lines.append('')

    # Any images not in either category
    mapped_files = set(title_images)
    for flist in image_map.values():
        mapped_files.update(flist)
    unmapped = [f for f in image_fnames if f not in mapped_files]
    if unmapped:
        lines.append('### Unmapped images (no Bild number detected)')
        for f in unmapped:
            lines.append(f'- {f}')
        lines.append('')

    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(__doc__.strip())
        sys.exit(1)
    print(collect(sys.argv[1], sys.argv[2], sys.argv[3]))
