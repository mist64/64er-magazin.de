#!/usr/bin/env python3
"""Draw the MRC decision record as a 150 dpi overlay: outlines around every region, by DESTINATION.

The point of colouring by destination layer rather than by detector: "which layer do these pixels
come from in the final PDF" is the thing that goes wrong, and it is a question a human can answer
at a glance. A green outline around a headline glyph is wrong on sight -- no thresholds involved.
That is exactly how p062's "8" failed, and it was one box on an otherwise clean page.

This is a pure RENDERER of the JSONL. It re-implements no gate, so the picture cannot disagree
with the numbers, and any past run can be re-drawn without re-running the pipeline.

  draw_record.py <record.jsonl> <page-image> <out.png> [--all] [--diff <baseline.jsonl>]

--all       also outline the boring majority (TEXT clusters, rejected darkfill candidates)
--diff      colour by CHANGE against a baseline record instead: what moved, and which way

Outlines only, never fills -- a wash hides the content being judged.
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

# --- constants -------------------------------------------------------------------------------
OUT_DPI = 150          # the overlay's resolution; decision defects are all visible at this size
SRC_DPI = 600          # the record's bbox/centroid coordinate space (mw x mh in mrc.rs)
LINE_W = 2             # outline width in output px (1 is invisible on a busy scan)
MARK_R = 4             # radius for kdrop markers: a 4px@600 component is sub-pixel at 150, so
                       # dropped marks get a FIXED-SIZE ring, not a scaled outline, or the
                       # artifact meant to reveal them would show nothing
DIM = 0.55             # how much to fade the page under the overlay so outlines read clearly

# destination-layer palette. Stable across runs: you learn the colours once.
COL = {
    "bg":      (0, 200, 60),      # the 150 dpi contone background
    "k":       (90, 90, 255),     # the JBIG2 K stencil (only drawn with --all: it is most of a page)
    "dropped": (255, 40, 40),     # thrown away by the despeckle
    "cut":     (255, 0, 255),     # 02-matte: the edge cut line (magenta, the existing convention)
    "kept":    (0, 180, 255),     # 02-matte: an edge left uncut, drawn only with --all
}
# change palette for --diff
COL_DIFF = {
    "added":   (0, 220, 90),
    "removed": (255, 40, 40),
    "changed": (255, 150, 0),
}


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def key(r):
    """Stable spatial key. Component IDs are assignment order and shift whenever the mask moves,
    so joining on `cid` reports every row as changed. The bbox centre quantised to 8 px @600
    survives a small change in a region's extent while still separating neighbours."""
    if "bbox" in r:
        x0, y0, x1, y1 = r["bbox"]
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    elif "centroid" in r:
        cx, cy = r["centroid"]
    else:
        # no geometry: the row IS the unit. `edge` must be in the key or all four edges of a page
        # collapse onto each other and the diff reads every one as changed.
        return (r["kind"], r.get("page"), r.get("edge", ""), 0)
    return (r["kind"], r.get("page"), cx // 8, cy // 8)


def draw(rows, base, out, show_all=False, baseline=None, title=""):
    im = base.convert("RGB")
    W, H = im.size
    # The record's coordinates are always the 600 dpi page frame (mw x mh), whatever resolution the
    # base image happens to be -- so the bbox scale is fixed, and only the base needs resampling.
    sc = OUT_DPI / SRC_DPI
    k = OUT_DPI / _guess_dpi(W)
    im = im.resize((int(round(W * k)), int(round(H * k))), Image.LANCZOS)
    im = Image.blend(Image.new("RGB", im.size, (255, 255, 255)), im, DIM)
    d = ImageDraw.Draw(im)

    def box(r, colour):
        x0, y0, x1, y1 = r["bbox"]
        d.rectangle([x0 * sc, y0 * sc, x1 * sc, y1 * sc], outline=colour, width=LINE_W)

    def mark(r, colour):
        cx, cy = r["centroid"]
        x, y = cx * sc, cy * sc
        d.ellipse([x - MARK_R, y - MARK_R, x + MARK_R, y + MARK_R], outline=colour, width=LINE_W)

    def edge_line(r, colour):
        """A matte cut is a LINE at `depth` in from one edge, not a box. Coordinates are in the
        source frame the matte ran at (w/h in the row), so scale by that, not by SRC_DPI."""
        W0, H0 = r.get("w"), r.get("h")
        if not W0 or not H0:
            return
        kx, ky = im.size[0] / float(W0), im.size[1] / float(H0)
        dp = float(r.get("depth") or 0.0)
        if dp <= 0:
            return
        e = r.get("edge")
        if e == "top":
            d.line([(0, dp * ky), (im.size[0], dp * ky)], fill=colour, width=LINE_W)
        elif e == "bottom":
            y = im.size[1] - dp * ky
            d.line([(0, y), (im.size[0], y)], fill=colour, width=LINE_W)
        elif e == "left":
            d.line([(dp * kx, 0), (dp * kx, im.size[1])], fill=colour, width=LINE_W)
        elif e == "right":
            x = im.size[0] - dp * kx
            d.line([(x, 0), (x, im.size[1])], fill=colour, width=LINE_W)

    n = 0
    if baseline is not None:
        old = {key(r): r for r in baseline}
        new = {key(r): r for r in rows}
        for k, r in new.items():
            o = old.get(k)
            if o is None:
                c = COL_DIFF["added"]
            elif o.get("layer") != r.get("layer") or o.get("verdict") != r.get("verdict") \
                    or o.get("promoted") != r.get("promoted"):
                c = COL_DIFF["changed"]
            else:
                continue
            _draw_any(r, c, box, mark, edge_line)
            n += 1
        for k, r in old.items():
            if k not in new:
                _draw_any(r, COL_DIFF["removed"], box, mark, edge_line)
                n += 1
    else:
        for r in rows:
            kind, layer = r["kind"], r.get("layer")
            if kind == "cluster":
                if layer == "k" and not show_all:
                    continue
                box(r, COL.get(layer, (128, 128, 128)))
            elif kind == "darkfill":
                if not r.get("promoted") and not show_all:
                    continue
                box(r, COL["bg"] if r.get("promoted") else COL["k"])
            elif kind == "kdrop":
                mark(r, COL["dropped"])
            elif kind == "edge":
                if layer != "cut" and not show_all:
                    continue
                edge_line(r, COL.get(layer, (128, 128, 128)))
            else:
                continue
            n += 1

    d.text((6, 6), title, fill=(0, 0, 0))
    im.save(out)
    return n, im.size


def _draw_any(r, colour, box, mark, edge_line):
    """Dispatch on what geometry the row actually carries."""
    if "bbox" in r:
        box(r, colour)
    elif "centroid" in r:
        mark(r, colour)
    elif r.get("kind") == "edge":
        edge_line(r, colour)


def _guess_dpi(width_px):
    """A4 width is 210mm; infer the source dpi from the pixel width so the caller can hand this
    either the 600 dpi crop or the 2400 dpi page without saying which."""
    return round(width_px / (210.0 / 25.4) / 50.0) * 50.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("record")
    ap.add_argument("page_image")
    ap.add_argument("out")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--diff", default=None)
    A = ap.parse_args()
    rows = load(A.record)
    base = Image.open(A.page_image)
    bl = load(A.diff) if A.diff else None
    page = next((r.get("page") for r in rows if r.get("page")), "?")
    title = "p%s  %s%s" % (page, os.path.basename(A.record), "  DIFF" if bl else "")
    n, size = draw(rows, base, A.out, A.all, bl, title)
    print("%s: %d regions drawn at %dx%d" % (A.out, n, size[0], size[1]))


if __name__ == "__main__":
    main()
