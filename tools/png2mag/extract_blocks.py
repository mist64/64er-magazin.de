#!/usr/bin/env python3
"""Extract Tesseract text blocks from a page scan into per-block PNG + TXT files.

Usage:
    python3 extract_blocks.py [--no-merge] [--crop X,Y,W,H] <page_png> <output_dir>

Options:
    --no-merge       Disable block merging (useful for mixed article/ad pages)
    --crop X,Y,W,H   Restrict extraction to a sub-region (coordinates in 300 DPI px).
                      Useful for continuation pages where article wraps around ads.
                      Block positions in output are relative to the crop origin.

Example:
    python3 extract_blocks.py issues/8604/png/053_600_cropped.png issues/8604/tmp/p053_blocks
    python3 extract_blocks.py --no-merge --crop 125,1680,560,1700 page.png out/

Two-pass pipeline:
    Pass 1: Run Tesseract on full page to detect block bounding boxes.
            Write layout.txt + classify.txt from original segmentation.
    Pass 2: Merge nearby/overlapping blocks into clusters, then run
            Tesseract on each final block region (--psm 6 for merged,
            --psm 6 for single blocks too).
            Write block_NN.png + block_NN.txt only for final blocks.

Block crops are taken from the original 600 DPI source with coordinates scaled up.
Font sizes from hOCR are annotated as {{fsize:N}} on paragraph first lines.
Output dir must NOT be in /tmp (Tesseract sandbox issue).
"""

import csv
import os
import re
import subprocess
import sys
from collections import Counter

INDENT_THRESHOLD = 15  # px at 300 DPI — above this = indented paragraph
MERGE_GAP = 20         # px at 300 DPI — vertical gap below which adjacent blocks merge
MERGE_MIN_BLOCKS = 3   # minimum cluster size to trigger merge
IMAGE_MIN_SIZE = 80    # px at 300 DPI — IMAGE blocks smaller than this are ignored
IMAGE_MIN_WORDS = 3    # minimum words from OCR to promote IMAGE → text block
GAP_MIN_HEIGHT = 40    # px at 300 DPI — minimum vertical gap to probe for missing content
GAP_X_OVERLAP = 0.3    # fraction of x-overlap to consider two blocks in the same column
GAP_MIN_WORDS = 1      # minimum words to accept a gap-fill block (1 = catches headings)


# ── Pass 1: Block detection ──────────────────────────────────────

def downscale_to_300(page_png, output_dir):
    """Downscale 600 DPI source to 300 DPI."""
    out = os.path.join(output_dir, '_page_300.png')
    subprocess.run(
        ['magick', page_png, '+repage', '-resize', '50%', out],
        check=True, capture_output=True,
    )
    return out


def detect_blocks(page_png_300, output_dir):
    """Pass 1: Run Tesseract on full page to get block bounding boxes.
    Returns dict of block_num → bbox (x,y,w,h) at 300 DPI.
    Also writes layout.txt and classify.txt."""
    base = os.path.join(output_dir, '_ocr')

    subprocess.run(
        ['tesseract', page_png_300, base, '-l', 'deu',
         '-c', 'hocr_font_info=1', 'tsv', 'hocr'],
        check=True, capture_output=True,
    )

    # Parse TSV for block bboxes and text (for layout summary)
    blocks = {}
    with open(base + '.tsv') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)
        for row in reader:
            level = int(row[0])
            block = int(row[2])
            left, top, w, h = int(row[6]), int(row[7]), int(row[8]), int(row[9])
            text = row[11] if len(row) > 11 else ''

            if level == 2:
                blocks.setdefault(block, {'bbox': (left, top, w, h), 'has_text': False})
            if level == 5 and text.strip():
                blocks.setdefault(block, {'bbox': (0, 0, 0, 0), 'has_text': False})
                blocks[block]['has_text'] = True

    # Write layout summary from original segmentation
    _write_layout_summary(base + '.tsv', base + '.hocr', output_dir, blocks)

    os.unlink(base + '.tsv')
    os.unlink(base + '.hocr')

    # Split into text blocks and image blocks
    text_blocks = {b: data['bbox'] for b, data in blocks.items()
                   if data['has_text'] and data['bbox'][2] >= 5 and data['bbox'][3] >= 5}
    image_blocks = {b: data['bbox'] for b, data in blocks.items()
                    if not data['has_text'] and data['bbox'][2] >= IMAGE_MIN_SIZE
                    and data['bbox'][3] >= IMAGE_MIN_SIZE}
    return text_blocks, image_blocks


def _write_layout_summary(tsv_path, hocr_path, output_dir, blocks):
    """Write layout.txt and initial classify.txt."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from tsv_layout import format_page
    sys.path.pop(0)

    summary = format_page(tsv_path, hocr_path)
    layout_path = os.path.join(output_dir, 'layout.txt')
    with open(layout_path, 'w') as f:
        f.write(summary + '\n')
    print(f'layout          {layout_path}')

    classify_path = os.path.join(output_dir, 'classify.txt')
    if os.path.exists(classify_path):
        print(f'classify        {classify_path} (kept existing)')
        return
    with open(classify_path, 'w') as f:
        for bnum in sorted(blocks):
            b = blocks[bnum]
            if b['has_text'] and b['bbox'][2] >= 5 and b['bbox'][3] >= 5:
                f.write(f'block_{bnum:02d}: body\n')
    print(f'classify        {classify_path}')


# ── Block merging ────────────────────────────────────────────────

def _merge_cluster_bbox(bboxes):
    """Compute merged bounding box from list of (x,y,w,h) tuples."""
    x1 = min(x for x, y, w, h in bboxes)
    y1 = min(y for x, y, w, h in bboxes)
    x2 = max(x + w for x, y, w, h in bboxes)
    y2 = max(y + h for x, y, w, h in bboxes)
    return (x1, y1, x2 - x1, y2 - y1)


def _bbox_center_inside(outer, inner):
    """Check if inner bbox center falls within outer with MERGE_GAP margin."""
    ox1, oy1, ow, oh = outer
    ix, iy, iw, ih = inner
    cx, cy = ix + iw / 2, iy + ih / 2
    return (ox1 - MERGE_GAP <= cx <= ox1 + ow + MERGE_GAP and
            oy1 - MERGE_GAP <= cy <= oy1 + oh + MERGE_GAP)


def merge_blocks(block_bboxes):
    """Merge nearby/overlapping blocks into clusters.

    Returns list of final block specs: [(block_num, bbox_300), ...]
    where merged clusters get the lowest original block number."""
    bnums = sorted(block_bboxes.keys())
    by_y = sorted(bnums, key=lambda b: block_bboxes[b][1])

    # Phase 1: grow clusters from nearby blocks
    clusters = []
    assigned = set()

    for a in by_y:
        if a in assigned:
            continue
        ba = block_bboxes[a]
        cluster = {a}
        cx1, cy1 = ba[0], ba[1]
        cx2, cy2 = ba[0] + ba[2], ba[1] + ba[3]

        changed = True
        while changed:
            changed = False
            for b in by_y:
                if b in cluster:
                    continue
                bb = block_bboxes[b]
                bx1, by1 = bb[0], bb[1]
                bx2, by2 = bb[0] + bb[2], bb[1] + bb[3]

                v_gap = max(0, by1 - cy2, cy1 - by2)
                if v_gap > MERGE_GAP:
                    continue

                x_overlap = max(0, min(cx2, bx2) - max(cx1, bx1))
                min_w = min(cx2 - cx1, bb[2])
                if min_w > 0 and x_overlap / min_w < 0.3:
                    continue

                cluster.add(b)
                cx1, cy1 = min(cx1, bx1), min(cy1, by1)
                cx2, cy2 = max(cx2, bx2), max(cy2, by2)
                changed = True

        if len(cluster) >= MERGE_MIN_BLOCKS:
            clusters.append(cluster)
            assigned.update(cluster)

    # Phase 2: absorb orphans whose center falls inside a cluster bbox
    for cluster in clusters:
        merged = _merge_cluster_bbox([block_bboxes[b] for b in cluster])
        for b in by_y:
            if b in assigned:
                continue
            if _bbox_center_inside(merged, block_bboxes[b]):
                cluster.add(b)
                assigned.add(b)

    # Build final block list
    final = []
    for cluster in clusters:
        merged_bbox = _merge_cluster_bbox([block_bboxes[b] for b in cluster])
        bnum = min(cluster)
        print(f'merge           blocks {",".join(str(b) for b in sorted(cluster))} '
              f'→ block {bnum} ({merged_bbox[2]}x{merged_bbox[3]})')
        final.append((bnum, merged_bbox))

    # Add unmerged blocks
    for b in bnums:
        if b not in assigned:
            final.append((b, block_bboxes[b]))

    final.sort(key=lambda x: x[0])
    return final


# ── Gap detection ────────────────────────────────────────────────

def detect_gaps(final_specs, page_png_300, output_dir, img_w_300, img_h_300):
    """Find vertical gaps between consecutive blocks in the same column.

    Groups blocks into columns by x-overlap, then probes gaps >GAP_MIN_HEIGHT px
    between consecutive blocks (and after the last block before page bottom).
    Returns list of (block_num, bbox_300) for gap regions that contain text.
    Block numbers start at 90 to avoid collisions."""

    if not final_specs:
        return []

    # Group blocks into columns by x-overlap
    def x_overlap_frac(a, b):
        ax1, _, aw, _ = a
        bx1, _, bw, _ = b
        ax2, bx2 = ax1 + aw, bx1 + bw
        overlap = max(0, min(ax2, bx2) - max(ax1, bx1))
        min_w = min(aw, bw)
        return overlap / min_w if min_w > 0 else 0

    specs_by_num = {bnum: bbox for bnum, bbox in final_specs}
    assigned = set()
    columns = []

    # Sort by x position for column grouping
    sorted_specs = sorted(final_specs, key=lambda s: s[1][0])

    for bnum, bbox in sorted_specs:
        if bnum in assigned:
            continue
        col = [(bnum, bbox)]
        assigned.add(bnum)
        for bnum2, bbox2 in sorted_specs:
            if bnum2 in assigned:
                continue
            # Check overlap with any member of the column
            if any(x_overlap_frac(bbox2, cb) >= GAP_X_OVERLAP for _, cb in col):
                col.append((bnum2, bbox2))
                assigned.add(bnum2)
        columns.append(col)

    # For each column, find gaps between consecutive blocks
    gap_regions = []
    page_bottom = int(img_h_300 * 0.90)  # don't probe below 90% of page

    for col in columns:
        # Sort column blocks by y position
        col_sorted = sorted(col, key=lambda s: s[1][1])

        # Compute column x-extent (union of all block x-ranges)
        col_x1 = min(bbox[0] for _, bbox in col_sorted)
        col_x2 = max(bbox[0] + bbox[2] for _, bbox in col_sorted)

        for i in range(len(col_sorted)):
            _, bbox_a = col_sorted[i]
            y_end_a = bbox_a[1] + bbox_a[3]

            if i + 1 < len(col_sorted):
                _, bbox_b = col_sorted[i + 1]
                y_start_b = bbox_b[1]
            else:
                # Tail gap: after last block in column
                y_start_b = page_bottom

            gap_h = y_start_b - y_end_a
            if gap_h >= GAP_MIN_HEIGHT:
                gap_regions.append((col_x1, y_end_a, col_x2 - col_x1, gap_h))

    # Filter out gap regions that overlap >30% with existing blocks
    def overlaps_existing(gap_bbox):
        gx1, gy1, gw, gh = gap_bbox
        gx2, gy2 = gx1 + gw, gy1 + gh
        gap_area = gw * gh
        if gap_area <= 0:
            return True
        for _, bbox in final_specs:
            bx1, by1, bw, bh = bbox
            bx2, by2 = bx1 + bw, by1 + bh
            ox = max(0, min(gx2, bx2) - max(gx1, bx1))
            oy = max(0, min(gy2, by2) - max(gy1, by1))
            if ox * oy / gap_area > 0.3:
                return True
        return False

    gap_blocks = []
    next_bnum = 90

    for gap_bbox in gap_regions:
        if overlaps_existing(gap_bbox):
            continue

        # OCR the gap region
        block_data = ocr_region(page_png_300, gap_bbox, output_dir)
        if block_data is None:
            continue

        word_count = sum(len(words) for words in block_data['lines'].values())
        if word_count >= GAP_MIN_WORDS:
            # Find unused block number starting at 90
            while any(bnum == next_bnum for bnum, _ in final_specs) or \
                  any(bnum == next_bnum for bnum, _ in gap_blocks):
                next_bnum += 1
            gap_blocks.append((next_bnum, gap_bbox))
            print(f'gap→text        block {next_bnum} ({gap_bbox[2]}x{gap_bbox[3]}, '
                  f'{word_count} words, y={gap_bbox[1]})')
            next_bnum += 1

    return gap_blocks


# ── Pass 2: OCR each final block ─────────────────────────────────

def _match_fsize_sequential(hocr_path, blocks):
    """Match hOCR font sizes to blocks by sequential word position."""
    with open(hocr_path) as f:
        hocr_words = re.findall(
            r"x_fsize (\d+)'>(.*?)</span>", f.read()
        )

    tsv_words = []
    for bnum in sorted(blocks):
        b = blocks[bnum]
        for key in sorted(b['lines']):
            par, line_num = key
            for word_num, text in enumerate(b['lines'][key], 1):
                tsv_words.append((bnum, par, line_num, word_num, text))

    for i, (bnum, par, line_num, word_num, text) in enumerate(tsv_words):
        if i < len(hocr_words):
            fsize = int(hocr_words[i][0])
            blocks[bnum]['word_fsizes'][(par, line_num, word_num)] = fsize


def ocr_region(page_png_300, bbox_300, output_dir):
    """Run Tesseract --psm 6 on a cropped region, return parsed block data."""
    x, y, w, h = bbox_300
    crop_path = os.path.join(output_dir, '_block_crop.png')
    subprocess.run(
        ['magick', page_png_300, '+repage', '-crop', f'{w}x{h}+{x}+{y}',
         '+repage', crop_path],
        check=True, capture_output=True,
    )

    base = os.path.join(output_dir, '_block_ocr')
    subprocess.run(
        ['tesseract', crop_path, base, '-l', 'deu',
         '--psm', '6', '-c', 'hocr_font_info=1', 'tsv', 'hocr'],
        check=True, capture_output=True,
    )

    # Parse TSV — coordinates are relative to crop, offset to page space
    blocks = {}
    with open(base + '.tsv') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)
        for row in reader:
            level = int(row[0])
            block = int(row[2])
            par = int(row[3])
            line_num = int(row[4])
            left, top, bw, bh = int(row[6]), int(row[7]), int(row[8]), int(row[9])
            text = row[11] if len(row) > 11 else ''

            left += x
            top += y

            if level == 2:
                blocks.setdefault(block, {
                    'bbox': (left, top, bw, bh),
                    'lines': {}, 'word_bboxes': [], 'par_first_x': {},
                    'word_fsizes': {}})
            if level == 5 and text.strip():
                blocks.setdefault(block, {
                    'bbox': (x, y, w, h),
                    'lines': {}, 'word_bboxes': [], 'par_first_x': {},
                    'word_fsizes': {}})
                key = (par, line_num)
                blocks[block]['lines'].setdefault(key, []).append(text)
                blocks[block]['word_bboxes'].append((left, top, bw, bh))
                if par not in blocks[block]['par_first_x']:
                    blocks[block]['par_first_x'][par] = left

    _match_fsize_sequential(base + '.hocr', blocks)

    for ext in ['.tsv', '.hocr']:
        p = base + ext
        if os.path.exists(p):
            os.unlink(p)
    if os.path.exists(crop_path):
        os.unlink(crop_path)

    # Merge all sub-blocks into one (psm 6 may still split)
    if not blocks:
        return None

    all_lines = {}
    all_word_bboxes = []
    all_par_first_x = {}
    all_word_fsizes = {}
    for bdata in blocks.values():
        for k, v in bdata['lines'].items():
            all_lines[k] = v
        all_word_bboxes.extend(bdata['word_bboxes'])
        all_par_first_x.update(bdata['par_first_x'])
        all_word_fsizes.update(bdata['word_fsizes'])

    return {
        'bbox': (x, y, w, h),
        'lines': all_lines,
        'word_bboxes': all_word_bboxes,
        'par_first_x': all_par_first_x,
        'word_fsizes': all_word_fsizes,
    }


def write_block_txt(block_data, txt_path):
    """Write block text with {{indent}}/{{flush}}/{{fsize}} annotations."""
    block_left = block_data['bbox'][0]
    par_first_x = block_data.get('par_first_x', {})
    word_fsizes = block_data.get('word_fsizes', {})

    all_fsizes = list(word_fsizes.values())
    body_fsize = Counter(all_fsizes).most_common(1)[0][0] if all_fsizes else None

    prev_par = None
    with open(txt_path, 'w') as f:
        for key in sorted(block_data['lines']):
            par_num, line_num = key
            words = block_data['lines'][key]
            line_text = ' '.join(words)

            if par_num != prev_par:
                offset = par_first_x.get(par_num, block_left) - block_left
                indent_tag = '{{indent}}' if offset > INDENT_THRESHOLD else '{{flush}}'

                first_fsize = word_fsizes.get((par_num, 1, 1))
                fsize_tag = ''
                if first_fsize is not None and body_fsize is not None:
                    if first_fsize != body_fsize:
                        fsize_tag = f'{{{{fsize:{first_fsize}}}}}'

                line_text = f'{indent_tag}{fsize_tag}{line_text}'
                prev_par = par_num

            f.write(line_text + '\n')


# ── Overview drawing ─────────────────────────────────────────────

def _word_tight_bbox(block_data):
    """Compute tight bounding box from word-level bboxes, excluding drop-cap outliers."""
    wbs = block_data.get('word_bboxes', [])
    if not wbs:
        return block_data['bbox']
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


def draw_overview(page_png, final_blocks, overview_path, use_word_bbox=False):
    """Draw block rectangles and numbers on a 300 DPI copy of the page.
    final_blocks: dict of bnum → block_data."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(page_png)
    clean = Image.new(img.mode, img.size, 'white')
    clean.paste(img)
    w2, h2 = clean.size[0] // 2, clean.size[1] // 2
    clean = clean.resize((w2, h2), Image.LANCZOS)

    draw = ImageDraw.Draw(clean)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for bnum in sorted(final_blocks):
        b = final_blocks[bnum]
        if not b['lines']:
            continue

        if use_word_bbox:
            x, y, w, h = _word_tight_bbox(b)
        else:
            x, y, w, h = b['bbox']
        if w < 5 or h < 5:
            continue

        draw.rectangle([x, y, x + w, y + h], outline='red', width=2)

        label = f'{bnum:02d}'
        bbox = font.getbbox(label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lx, ly = x, max(0, y - th - 4)
        draw.rectangle([lx, ly, lx + tw + 6, ly + th + 4], fill='red')
        draw.text((lx + 3, ly + 1), label, fill='white', font=font)

    clean.save(overview_path)


# ── Image utility ────────────────────────────────────────────────

def get_image_size(png_path):
    """Return (width, height) of an image."""
    result = subprocess.run(
        ['magick', 'identify', '-format', '%w %h', png_path],
        check=True, capture_output=True, text=True,
    )
    parts = result.stdout.strip().split()
    return int(parts[0]), int(parts[1])


# ── Main entry point ─────────────────────────────────────────────

def extract_blocks(page_png, output_dir, no_merge=False, crop=None):
    """Extract all text blocks into output_dir.

    Args:
        crop: optional (x, y, w, h) in 300 DPI px to restrict extraction region.
              The 600 DPI source is cropped first, then the normal pipeline runs.
    """
    os.makedirs(output_dir, exist_ok=True)

    # If crop requested, pre-crop the 600 DPI source
    if crop:
        cx, cy, cw, ch = crop
        # Scale to 600 DPI
        crop_spec = f'{cw*2}x{ch*2}+{cx*2}+{cy*2}'
        cropped_png = os.path.join(output_dir, '_page_cropped_600.png')
        subprocess.run(
            ['magick', page_png, '+repage', '-crop', crop_spec,
             '+repage', cropped_png],
            check=True, capture_output=True,
        )
        print(f'crop            {crop_spec} (300 DPI: {cx},{cy} {cw}x{ch})')
        page_png = cropped_png

    page_300 = downscale_to_300(page_png, output_dir)
    img_w_300, img_h_300 = get_image_size(page_300)

    # Pass 1: detect block bboxes (writes layout.txt + classify.txt)
    text_bboxes, image_bboxes = detect_blocks(page_300, output_dir)

    # Merge nearby text blocks into clusters
    if no_merge:
        final_specs = [(b, bbox) for b, bbox in sorted(text_bboxes.items())]
    else:
        final_specs = merge_blocks(text_bboxes)

    # Try OCR on large IMAGE blocks — Tesseract sometimes misdetects
    # text in shaded/boxed regions as images
    promoted = []
    for bnum, bbox in sorted(image_bboxes.items()):
        block_data = ocr_region(page_300, bbox, output_dir)
        if block_data is None:
            continue
        word_count = sum(len(words) for words in block_data['lines'].values())
        if word_count >= IMAGE_MIN_WORDS:
            final_specs.append((bnum, bbox))
            promoted.append(bnum)
            print(f'image→text      block {bnum} ({bbox[2]}x{bbox[3]}, {word_count} words)')
        # else: truly an image, skip

    # Detect gaps between blocks
    gap_blocks = detect_gaps(final_specs, page_300, output_dir, img_w_300, img_h_300)
    final_specs.extend(gap_blocks)

    # Append promoted + gap blocks to classify.txt
    new_blocks = promoted + [bnum for bnum, _ in gap_blocks]
    if new_blocks:
        classify_path = os.path.join(output_dir, 'classify.txt')
        with open(classify_path) as f:
            existing = f.read()
        with open(classify_path, 'a') as f:
            for bnum in sorted(new_blocks):
                tag = f'block_{bnum:02d}:'
                if tag not in existing:
                    f.write(f'{tag} body\n')

    final_specs.sort(key=lambda x: x[0])

    # Pass 2: OCR each final block
    final_blocks = {}
    for bnum, bbox_300 in final_specs:
        block_data = ocr_region(page_300, bbox_300, output_dir)
        if block_data is None:
            continue
        final_blocks[bnum] = block_data

        # Scale to 600 DPI for cropping from original
        x, y, w, h = bbox_300
        cx, cy, cw, ch = x * 2, y * 2, w * 2, h * 2

        prefix = os.path.join(output_dir, f'block_{bnum:02d}')

        # Write annotated text
        write_block_txt(block_data, f'{prefix}.txt')

        # Crop from 600 DPI source
        subprocess.run(
            ['magick', page_png, '+repage', '-crop', f'{cw}x{ch}+{cx}+{cy}',
             '+repage', f'{prefix}.png'],
            check=True, capture_output=True,
        )

        with open(f'{prefix}.txt') as f:
            text = f.read().strip()
        preview = text[:70].replace('\n', ' | ')
        print(f'block_{bnum:02d}  {cw:4d}x{ch:<4d}  {preview}')

    os.unlink(page_300)

    # Generate overview images
    overview_path = os.path.join(output_dir, 'overview.png')
    draw_overview(page_png, final_blocks, overview_path, use_word_bbox=False)
    print(f'\noverview        {overview_path}')

    overview_tight_path = os.path.join(output_dir, 'overview_tight.png')
    draw_overview(page_png, final_blocks, overview_tight_path, use_word_bbox=True)
    print(f'overview_tight  {overview_tight_path}')


if __name__ == '__main__':
    args = []
    no_merge = False
    crop = None
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--no-merge':
            no_merge = True
        elif a == '--crop':
            i += 1
            parts = sys.argv[i].split(',')
            crop = tuple(int(p) for p in parts)
        elif a.startswith('--crop='):
            parts = a.split('=', 1)[1].split(',')
            crop = tuple(int(p) for p in parts)
        elif not a.startswith('--'):
            args.append(a)
        i += 1
    if len(args) != 2:
        print(__doc__.strip())
        sys.exit(1)
    extract_blocks(args[0], args[1], no_merge=no_merge, crop=crop)
