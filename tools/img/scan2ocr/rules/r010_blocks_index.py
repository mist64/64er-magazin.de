#!/usr/bin/env python3
"""
Step 010's block index: out/NNN.json -> blocks/pNNN.txt

Several later steps (130 place_figures, 150 place_images, 160 fill_tables,
170 transcribe_listings, 210 head_meta, 240 rubric_banners) need the bbox of a
named region on a page -- a caption, a listing, a header strip, a banner.

This used to be its own rule (9b), which re-ran tesseract over the delivered PDF
and reduced the TSV with awk.  Step 010 already OCR'd every page and already
knows every block's bbox, its label and its text, so the index is a projection
of data we have rather than a second OCR pass.  It costs no OCR and cannot
disagree with the corpus, which the awk pass could and did.

COORDINATE SPACE -- read this before cropping anything.  The bboxes here are in
the pixels of the GRADED 600 dpi MASTER (`SRC_DIR`), which is deskewed and
A4-cropped.  They are NOT in the delivered PDF's page space: the PDF page has
not been deskewed or cropped, so the two differ by a rotation and an offset.
Crop from the master, never from a PDF render:

    magick <SRC_DIR>/010.png -crop 1650x168+390+3195 out.png

`frac=` is the same box as a fraction of the page, for cropping at any other
resolution.
"""

import json
import os
import sys

from r010_ocr_blocks import OUT_DIR, OCR_DPI, SRC_DIR

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

DEST_DIR = os.path.join(OUT_DIR, "blocks")

# The master is 600 dpi and stage A measured at OCR_DPI, so every bbox is
# scaled by this to land in the pixels of the image you actually crop from.
MASTER_DPI = 600
SCALE = MASTER_DPI / OCR_DPI

# Enough of a block's text to find it with grep ("Listing 1. ...",
# "Tabelle 2. ...", "Bild 3. ..."), no more.
PREVIEW_CHARS = 200


def write_page(page):
    src = os.path.join(OUT_DIR, f"{page:03d}.json")
    if not os.path.exists(src):
        return 0
    rec = json.load(open(src, encoding="utf-8"))
    lines = []
    for b in sorted(rec["blocks"], key=lambda b: (b["bbox"][1], b["bbox"][0])):
        x0, y0, x1, y1 = (round(v * SCALE) for v in b["bbox"])
        f0, f1, f2, f3 = b["bbox_frac"]
        text = " ".join(b["text"].split())[:PREVIEW_CHARS]
        lines.append(f'block={b["id"]} label={b["label"]} '
                     f'bbox={x1 - x0}x{y1 - y0}+{x0}+{y0} '
                     f'frac={f0},{f1},{f2},{f3} text= {text}')
    os.makedirs(DEST_DIR, exist_ok=True)
    dest = os.path.join(DEST_DIR, f"p{page:03d}.txt")
    open(dest, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return len(lines)


if __name__ == "__main__":
    pages = [int(a) for a in sys.argv[1:]] or range(1, 177)
    total = sum(write_page(p) for p in pages)
    print(f"{total} blocks -> {DEST_DIR}/pNNN.txt   (crop source: {SRC_DIR})")
