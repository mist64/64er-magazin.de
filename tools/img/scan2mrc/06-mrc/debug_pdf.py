#!/usr/bin/env python3
"""The DEBUG PDF: every page at 150 dpi from the graded, cropped source, with every detection
outlined and colour-coded by what the renderer decided it was.

The deliverable PDF shows the RESULT; this shows the DECISIONS that produced it, so a wrong call
is visible as a wrong-coloured box rather than having to be inferred from a soft glyph or a black
blob. It is a pure renderer of the JSONL decision record -- it re-implements no gate, so the
picture cannot disagree with the numbers.

  debug_pdf.py                      all pages -> tmp/8609_debug.pdf
  debug_pdf.py --pages 1 62 154     a subset
  debug_pdf.py --jobs 3

WHAT THE COLOURS MEAN
  green    RGB image      a colour photo/artwork region -> drawn from the 150 dpi contone background
  blue     gray image     a neutral continuous-tone region -> same background, no colour
  per-ink  single colour  an accent-ink stencil at 600 dpi (C, M, Y, MY, MC, ...)
  --       K              deliberately NOT drawn: the black stencil is most of the page, so
                          outlining it would bury everything else
"""
import argparse
import glob
import json
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
from multiprocessing import Pool                                       # noqa: E402
from PIL import Image, ImageDraw                                       # noqa: E402

Image.MAX_IMAGE_PIXELS = None
T = "/Users/mist/DNB/8609/tmp"
SRC = os.path.join(T, "render", "deliver")
REC = os.path.join(T, "mrc")
PNG = os.path.join(T, "dbg", "debugpages")
# The 150 dpi base is a SIDE EFFECT of `mrcpipe mrc` (written next to the PDF as NNN_base150.png),
# so this tool never decodes the 426 MB page RGB itself -- one code path produces the pixels, one
# consumes them. The local fallback below exists only for pages rendered before that landed.
BASE = os.path.join(T, "mrc")
OUT = os.path.join(T, "8609_debug.pdf")

OUT_DPI = 150
SRC_DPI = 600          # the record's bbox coordinate space (mw x mh in mrc.rs)
PAGE_DPI = 2400        # the page RGB on disk
LINE = 2
DIM = 0.62             # fade the page so outlines read; outlines only, never fills

COL_MEDIA = {"rgb": (0, 190, 60), "gray": (40, 110, 255)}
# a reversed box (white lettering on a solid dark fill) also ends up in the contone background,
# but by a different decision than step 7 -- worth its own colour so a wrong promotion is visible
COL_DARKFILL = (255, 130, 0)
COL_UNKNOWN_INK = (150, 150, 150)

# Overlapping detections are the normal case -- an ink stencil sits inside a photo, a reversed box
# sits inside a tint. Coincident outlines would hide each other, so each TYPE is nudged right and
# down by its own multiple of NUDGE. Read the nesting order off the offsets: the outermost box is
# the earliest type.
NUDGE = 3
NUDGE_ORDER = ["rgb", "gray", "darkfill", "C", "M", "Y", "MY", "MC", "CY"]


def nudge_for(kind):
    try:
        return NUDGE * NUDGE_ORDER.index(kind)
    except ValueError:
        return NUDGE * len(NUDGE_ORDER)


def rect(d, bbox, sc, colour, kind, width):
    o = nudge_for(kind)
    x0, y0, x1, y1 = bbox
    d.rectangle([x0 * sc + o, y0 * sc + o, x1 * sc + o, y1 * sc + o],
                outline=colour, width=width)
# accent-ink outline colours: the ink's own hue, brightened enough to see on paper
COL_INK = {"C": (0, 175, 210), "M": (225, 0, 140), "Y": (200, 165, 0),
           "MY": (230, 60, 30), "MC": (140, 40, 200), "CY": (0, 160, 90)}


def one(page):
    src = os.path.join(SRC, "%03d_page_rgb.png" % page)
    rec = os.path.join(REC, "%03d.jsonl" % page)
    out = os.path.join(PNG, "%03d.png" % page)
    if not (os.path.exists(src) and os.path.exists(rec)):
        return page, "missing input"
    # The 2400 dpi source is ~426 MB and decoding it dominates (41s of a 41s page), so the 150 dpi
    # rendition is cached: the overlay is the part that changes when a gate moves, not the page.
    bcache = os.path.join(BASE, "%03d_base150.png" % page)
    if os.path.exists(bcache):
        im = Image.open(bcache).convert("RGB")
    else:
        im = Image.open(src).convert("RGB")
        w, h = im.size
        k = OUT_DPI / PAGE_DPI
        im = im.resize((int(round(w * k)), int(round(h * k))), Image.LANCZOS)
    im = Image.blend(Image.new("RGB", im.size, (255, 255, 255)), im, DIM)
    d = ImageDraw.Draw(im)
    sc = OUT_DPI / SRC_DPI

    rows = [json.loads(l) for l in open(rec)]
    n_img = n_ink = n_df = 0
    inks = set()
    for r in rows:
        if r["kind"] == "cluster" and r.get("layer") == "bg":
            m = r.get("media") or "rgb"
            rect(d, r["bbox"], sc, COL_MEDIA.get(m, (128, 128, 128)), m, LINE)
            n_img += 1
        elif r["kind"] == "ink":
            nm = r["ink"]
            inks.add(nm)
            rect(d, r["bbox"], sc, COL_INK.get(nm, COL_UNKNOWN_INK), nm, LINE)
            n_ink += 1
        elif r["kind"] == "darkfill" and r.get("promoted"):
            rect(d, r["bbox"], sc, COL_DARKFILL, "darkfill", LINE)
            n_df += 1

    # header: page number and a legend of what is actually on THIS page
    d.rectangle([0, 0, im.size[0], 15], fill=(255, 255, 255))
    lbl = "p%03d   %d image  %d ink  %d reversed-box" % (page, n_img, n_ink, n_df)
    d.text((4, 3), lbl, fill=(0, 0, 0))
    x = 250
    for nm, c in (("RGB image", COL_MEDIA["rgb"]), ("gray image", COL_MEDIA["gray"]),
                  ("reversed box", COL_DARKFILL)):
        d.rectangle([x, 4, x + 9, 12], outline=c, width=2)
        d.text((x + 13, 3), nm, fill=(0, 0, 0))
        x += 96
    for nm in sorted(inks):
        c = COL_INK.get(nm, (255, 140, 0))
        d.rectangle([x, 4, x + 9, 12], outline=c, width=2)
        d.text((x + 13, 3), nm, fill=(0, 0, 0))
        x += 40
    d.text((x + 6, 3), "(K not outlined)", fill=(90, 90, 90))
    os.makedirs(PNG, exist_ok=True)
    im.save(out)
    return page, "%d img %d ink %d revbox" % (n_img, n_ink, n_df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="*", type=int)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--png-only", action="store_true")
    A = ap.parse_args()
    pages = A.pages or sorted(int(os.path.basename(f)[:3])
                              for f in glob.glob(os.path.join(SRC, "*_page_rgb.png")))
    with Pool(A.jobs) as pool:
        for p, msg in pool.imap_unordered(one, pages):
            print("  p%03d %s" % (p, msg), flush=True)
    if A.png_only:
        return
    fs = [os.path.join(PNG, "%03d.png" % p) for p in pages]
    fs = [f for f in fs if os.path.exists(f)]
    first = Image.open(fs[0]).convert("RGB")
    rest = [Image.open(f).convert("RGB") for f in fs[1:]]
    first.save(A.out, save_all=True, append_images=rest, resolution=OUT_DPI)
    print("wrote %s  (%d pages, %.1f MB)" % (A.out, len(fs), os.path.getsize(A.out) / 1e6))


if __name__ == "__main__":
    main()
