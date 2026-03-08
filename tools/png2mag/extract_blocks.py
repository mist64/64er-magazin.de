#!/usr/bin/env python3
"""Extract Tesseract text blocks from a page scan into per-block PNG + TXT files.

Usage:
    python3 extract_blocks.py <page_png> <output_dir>

Example:
    python3 extract_blocks.py issues/8604/png/053_600_cropped.png issues/8604/tmp/p053_blocks

Produces for each block with text:
    <output_dir>/block_NN.png  — cropped region from the page image (from 600 DPI source)
    <output_dir>/block_NN.txt  — OCR text with line structure preserved

Tesseract runs at 300 DPI (downscaled 50%) for optimal recognition.
Block crops are taken from the original 600 DPI source with coordinates scaled back up.
Font sizes from hOCR are annotated as {{fsize:N}} on paragraph first lines.
Output dir must NOT be in /tmp (Tesseract sandbox issue).
"""

import csv
import os
import re
import subprocess
import sys

INDENT_THRESHOLD = 15  # px at 300 DPI — above this = indented paragraph


def downscale_to_300(page_png, output_dir):
    """Downscale 600 DPI source to 300 DPI. Written to output_dir (not /tmp)
    because Tesseract/Leptonica can't read files from /tmp due to sandboxing."""
    out = os.path.join(output_dir, '_page_300.png')
    subprocess.run(
        ['magick', page_png, '+repage', '-resize', '50%', out],
        check=True, capture_output=True,
    )
    return out


def run_tesseract(page_png_300, output_dir):
    """Run Tesseract on 300 DPI image, produce TSV + hOCR, return parsed blocks dict."""
    base = os.path.join(output_dir, '_ocr')

    # Run TSV + hOCR in one call. Input file must be in a readable dir (not /tmp).
    subprocess.run(
        ['tesseract', page_png_300, base, '-l', 'deu',
         '-c', 'hocr_font_info=1', 'tsv', 'hocr'],
        check=True, capture_output=True,
    )

    # Parse TSV for structure + coordinates
    blocks = {}
    with open(base + '.tsv') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)
        for row in reader:
            level = int(row[0])
            block = int(row[2])
            par = int(row[3])
            line_num = int(row[4])
            left, top, w, h = int(row[6]), int(row[7]), int(row[8]), int(row[9])
            text = row[11] if len(row) > 11 else ''

            if level == 2:
                blocks.setdefault(block, {'bbox': (left, top, w, h), 'lines': {},
                                          'word_bboxes': [], 'par_first_x': {},
                                          'word_fsizes': {}})
            if level == 5 and text.strip():
                blocks.setdefault(block, {'bbox': (0, 0, 0, 0), 'lines': {},
                                          'word_bboxes': [], 'par_first_x': {},
                                          'word_fsizes': {}})
                key = (par, line_num)
                blocks[block]['lines'].setdefault(key, []).append(text)
                blocks[block]['word_bboxes'].append((left, top, w, h))
                if par not in blocks[block]['par_first_x']:
                    blocks[block]['par_first_x'][par] = left

    # Match hOCR font sizes to TSV words by sequential position
    _match_fsize_sequential(base + '.hocr', blocks)

    os.unlink(base + '.tsv')
    os.unlink(base + '.hocr')
    return blocks


def _match_fsize_sequential(hocr_path, blocks):
    """Match hOCR font sizes to TSV blocks/words by sequential text matching."""
    with open(hocr_path) as f:
        hocr_words = re.findall(
            r"x_fsize (\d+)'>(.*?)</span>", f.read()
        )

    # Build sequential list of TSV words across all blocks
    tsv_words = []
    for bnum in sorted(blocks):
        b = blocks[bnum]
        for key in sorted(b['lines']):
            par, line_num = key
            for word_num, text in enumerate(b['lines'][key], 1):
                tsv_words.append((bnum, par, line_num, word_num, text))

    # Match by position — both lists are in reading order
    for i, (bnum, par, line_num, word_num, text) in enumerate(tsv_words):
        if i < len(hocr_words):
            fsize = int(hocr_words[i][0])
            blocks[bnum]['word_fsizes'][(par, line_num, word_num)] = fsize


def get_image_size(png_path):
    """Return (width, height) of an image."""
    result = subprocess.run(
        ['magick', 'identify', '-format', '%w %h', png_path],
        check=True, capture_output=True, text=True,
    )
    parts = result.stdout.strip().split()
    return int(parts[0]), int(parts[1])


def extract_blocks(page_png, output_dir):
    """Extract all text blocks into output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # Downscale to 300 DPI for Tesseract (written to output_dir, not /tmp)
    page_300 = downscale_to_300(page_png, output_dir)
    img_w_300, img_h_300 = get_image_size(page_300)

    blocks = run_tesseract(page_300, output_dir)
    os.unlink(page_300)

    # Crop from the original 600 DPI source (strip canvas offset with +repage)
    # Tesseract coords are at 300 DPI; scale 2x for 600 DPI crops
    img_w_600, img_h_600 = img_w_300 * 2, img_h_300 * 2

    for bnum in sorted(blocks):
        b = blocks[bnum]
        if not b['lines']:
            continue
        x, y, w, h = b['bbox']
        if w < 5 or h < 5:
            continue

        # Scale to 600 DPI for cropping the original
        cx, cy, cw, ch = x * 2, y * 2, w * 2, h * 2

        prefix = os.path.join(output_dir, f'block_{bnum:02d}')

        # Write text with metadata annotations using {{tag}} syntax
        block_left = b['bbox'][0]
        par_first_x = b.get('par_first_x', {})
        word_fsizes = b.get('word_fsizes', {})
        prev_par = None

        # Determine the dominant (body) font size for this block
        from collections import Counter
        all_fsizes = list(word_fsizes.values())
        body_fsize = Counter(all_fsizes).most_common(1)[0][0] if all_fsizes else None

        with open(f'{prefix}.txt', 'w') as f:
            for key in sorted(b['lines']):
                par_num, line_num = key
                words = b['lines'][key]
                line_text = ' '.join(words)

                # Annotate first line of each paragraph
                if par_num != prev_par:
                    offset = par_first_x.get(par_num, block_left) - block_left
                    indent_tag = '{{indent}}' if offset > INDENT_THRESHOLD else '{{flush}}'

                    # Font size of first word
                    first_fsize = word_fsizes.get((par_num, 1, 1))
                    fsize_tag = ''
                    if first_fsize is not None and body_fsize is not None:
                        if first_fsize != body_fsize:
                            fsize_tag = f'{{{{fsize:{first_fsize}}}}}'

                    line_text = f'{indent_tag}{fsize_tag}{line_text}'
                    prev_par = par_num

                f.write(line_text + '\n')

        # Crop from 600 DPI source (+repage strips canvas offset)
        subprocess.run(
            ['magick', page_png, '+repage', '-crop', f'{cw}x{ch}+{cx}+{cy}',
             '+repage', f'{prefix}.png'],
            check=True, capture_output=True,
        )
        # Read back text for summary
        with open(f'{prefix}.txt') as f:
            text = f.read().strip()
        preview = text[:70].replace('\n', ' | ')
        print(f'block_{bnum:02d}  {cw:4d}x{ch:<4d}  {preview}')

    # Generate overview images: block-level bbox and word-tight bbox
    overview_path = os.path.join(output_dir, 'overview.png')
    _draw_overview(page_png, blocks, overview_path, use_word_bbox=False)
    print(f'\noverview        {overview_path}')

    overview_tight_path = os.path.join(output_dir, 'overview_tight.png')
    _draw_overview(page_png, blocks, overview_tight_path, use_word_bbox=True)
    print(f'overview_tight  {overview_tight_path}')


def _word_tight_bbox(block):
    """Compute tight bounding box from word-level bboxes, excluding drop-cap outliers."""
    wbs = block.get('word_bboxes', [])
    if not wbs:
        return block['bbox']
    # Filter out drop-cap outliers: words whose height is >2x the median word height
    heights = sorted(h for x, y, w, h in wbs)
    median_h = heights[len(heights) // 2]
    filtered = [(x, y, w, h) for x, y, w, h in wbs if h <= median_h * 2]
    if not filtered:
        filtered = wbs
    min_x = min(x for x, y, w, h in filtered)
    min_y = min(y for x, y, w, h in filtered)
    max_x2 = max(x + w for x, y, w, h in filtered)
    max_y2 = max(y + h for x, y, w, h in filtered)
    return (min_x, min_y, max_x2 - min_x, max_y2 - min_y)


def _draw_overview(page_png, blocks, overview_path, use_word_bbox=False):
    """Draw block rectangles and numbers on a 300 DPI copy of the page."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(page_png)
    # Strip canvas offset by re-creating
    clean = Image.new(img.mode, img.size, 'white')
    clean.paste(img)
    # Downscale to 300 DPI
    w2, h2 = clean.size[0] // 2, clean.size[1] // 2
    clean = clean.resize((w2, h2), Image.LANCZOS)

    draw = ImageDraw.Draw(clean)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for bnum in sorted(blocks):
        b = blocks[bnum]
        if not b['lines']:
            continue

        if use_word_bbox:
            x, y, w, h = _word_tight_bbox(b)
        else:
            x, y, w, h = b['bbox']
        if w < 5 or h < 5:
            continue

        # Draw rectangle
        draw.rectangle([x, y, x + w, y + h], outline='red', width=2)

        # Draw label with background
        label = f'{bnum:02d}'
        bbox = font.getbbox(label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lx, ly = x, max(0, y - th - 4)
        draw.rectangle([lx, ly, lx + tw + 6, ly + th + 4], fill='red')
        draw.text((lx + 3, ly + 1), label, fill='white', font=font)

    clean.save(overview_path)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__.strip())
        sys.exit(1)
    extract_blocks(sys.argv[1], sys.argv[2])
