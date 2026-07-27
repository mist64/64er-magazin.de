#!/usr/bin/env python3
"""FULL FRONT-END STACK -> deskewed RGBA page, for visual review.

Runs every detection stage that exists and bakes the result into one RGBA image per page:

  02  bed_matte    -> alpha 0 on the scanner bed / yellow backing at all four edges
  02b shear_spine  -> alpha 0 beyond the background-colour boundary (neighbour page),
                      on pages where that boundary is detectable
  02b hole_masks   -> alpha 0 on the exact binder-clip hole shapes
  01  deskew       -> the whole RGBA is rotated by the page's measured angle, expanding
                      the canvas; pixels ADDED by the rotation are alpha 0 too

ORDER MATTERS. The mattes are detected in the RAW scan frame (that is the frame their
metadata was computed in), composited there, and only THEN rotated -- so a slightly tilted
page edge ends up straight, which is what the later A4 crop expects.

Alpha is UNKNOWN, not white: nothing is fabricated here. A later fill/inpaint step decides
what (if anything) goes into those pixels.

Usage:
  stack_render.py [pages...]        default: all 176
  stack_render.py --montage         also write a downscaled contact sheet
Output: OUT_DIR/NNN.png  (RGBA, 600 dpi, deskewed)
"""
import os, sys, json, re, argparse
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "02-matte"))
sys.path.insert(0, os.path.join(HERE, "02b-opposite-page"))
from bed_matte import bed_matte
import shear_spine as S
import clip_holes as CH
import hole_masks as HM

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
# --------------------------------------------------------------------------- #
THUMB   = "/Users/mist/DNB/8609/thumbs_600"
SKEW    = "/Users/mist/DNB/8609/tmp/skew_all.txt"
SPINE   = "/Users/mist/DNB/8609/tmp/shear_v7.json"
CLIPJS  = "/Users/mist/DNB/8609/tmp/clip_holes.json"
PRIORSF = os.path.join(HERE, "02-matte/priors.json")
OUT_DIR = "/Users/mist/DNB/8609/tmp/stack600"

DPI        = 600
SPINE_OVER = 6      # cut this many px PAST the spine line toward the page, so the whole
                    #   neighbour goes; it only eats our own inner margin, which the A4
                    #   crop discards anyway.

# --- fallback for pages with no detectable background difference ------------ #
# ~130 of 176 pages are cream-on-cream: the neighbour is there but is the same colour as
# our margin, so no colour boundary exists to find. There we cut on the CLIP-HOLE LINE.
# That is justified by measurement, not convenience: over the 46 pages where the boundary
# IS detectable, (boundary - hole column) has a median of -2.7 px = -0.12 mm, i.e. the hole
# line is an UNBIASED estimator of the boundary. No systematic correction is needed.
# Its scatter is +/-44 px (1.9 mm) though, and on 48% of pages the true boundary lies
# INBOARD of the holes -- so cutting exactly on the line would leave a neighbour sliver
# about half the time. Hence the overcut below.
HOLE_OVERCUT = 44   # cut this far INBOARD of the hole line (= 1 sigma of the measured
                    #   scatter, 1.9 mm). Costs nothing: the logo-anchored A4 window's inner
                    #   edge already sits ~7 mm inboard of the holes on every page, so these
                    #   pixels are discarded by the crop regardless.
HOLE_MIN     = 4    # need at least this many located holes to fit the fallback line
MONT_W     = 150    # per-page width in the contact sheet
CHECKER    = 24     # checkerboard square size (px) used to VISUALISE alpha in the montage


def load_skew():
    ang = {}
    for ln in open(SKEW):
        m = re.search(r"/(\d+)\.png:\s*([+-]?\d+\.\d+)\s*deg", ln)
        if m:
            ang[int(m.group(1))] = float(m.group(2))
    return ang


def _cut_outboard(shape, inb, parity):
    """Alpha-0 everything OUTBOARD of the per-row inboard distance `inb`."""
    H, W = shape
    xx = np.arange(W)[None, :]
    if parity == "even":                       # neighbour on the RIGHT
        return xx >= (W - inb[:, None])
    return xx <= inb[:, None]                  # neighbour on the LEFT


def spine_mask(shape, rec, parity, clip_entry):
    """Cut the neighbour page off.

    Preferred: the measured background-colour boundary. Where no colour difference exists
    (cream-on-cream, ~130 of 176 pages) fall back to the CLIP-HOLE line -- see HOLE_OVERCUT
    for why that is a sound estimator and why over-cutting there is free. Returns
    (mask, source) where source is "colour", "holes" or "none".
    """
    H, W = shape
    ys = np.arange(H, dtype=np.float32)

    if rec and rec.get("found"):
        inb = rec["inboard_top"] + (rec["inboard_bot"] - rec["inboard_top"]) * (ys / max(1, H - 1))
        return _cut_outboard((H, W), inb - SPINE_OVER, parity), "colour"

    hs = [h for h in (clip_entry or {}).get("holes", []) if h[2]]
    if len(hs) < HOLE_MIN:
        return np.zeros((H, W), bool), "none"
    hx = np.array([h[0] for h in hs], float); hy = np.array([h[1] for h in hs], float)
    coef, *_ = np.linalg.lstsq(np.stack([np.ones_like(hy), hy], 1), hx, rcond=None)
    xline = coef[0] + coef[1] * ys                      # absolute x of the hole line
    inb = (W - xline) if parity == "even" else xline
    return _cut_outboard((H, W), inb - HOLE_OVERCUT, parity), "holes"


def render(page, priors, skew, spine, clip, tmpl):
    p = "%03d" % page
    path = os.path.join(THUMB, p + ".png")
    im = Image.open(path).convert("RGB")
    W, H = im.size
    parity = "even" if page % 2 == 0 else "odd"

    unknown = np.zeros((H, W), bool)

    # -- 02 bed / yellow backing ------------------------------------------------
    bed_rgba, _, _ = bed_matte(im, DPI, priors=priors, page_no=page, return_meta=True)
    unknown |= (np.asarray(bed_rgba)[:, :, 3] == 0)

    # -- 02b neighbour page beyond the background boundary ----------------------
    sm, src = spine_mask((H, W), spine.get(p), parity, clip.get(p))
    unknown |= sm

    # -- 02b binder-clip holes (exact shapes) -----------------------------------
    res = clip.get(p)
    if res:
        gray = np.asarray(im.convert("L"), np.float32)
        try:
            seg = HM.segment_hole_shapes(gray, res)
            unknown |= seg["mask"].astype(bool)
        except Exception as e:                 # a hole that cannot be segmented is left
            print("  p%s hole shapes failed: %s" % (p, e))

    # -- compose RGBA in the RAW frame -----------------------------------------
    rgba = np.dstack([np.asarray(im), np.where(unknown, 0, 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA")

    # -- 01 deskew: rotate, expanding; rotation-added pixels are unknown too ----
    ang = skew.get(page, 0.0)
    if abs(ang) > 1e-3:
        out = out.rotate(ang, resample=Image.BICUBIC, expand=True,
                         fillcolor=(0, 0, 0, 0))
    return out, ang, float(unknown.mean()), src


def montage(pages, out_path):
    """Contact sheet with alpha shown as a checkerboard, so cuts are visible at a glance."""
    tiles = []
    for n in pages:
        f = os.path.join(OUT_DIR, "%03d.png" % n)
        if not os.path.exists(f):
            continue
        im = Image.open(f)
        w = MONT_W; h = int(im.size[1] * w / im.size[0])
        im = im.resize((w, h), Image.LANCZOS)
        bg = Image.new("RGB", im.size, (255, 255, 255))
        a = np.indices((im.size[1], im.size[0])).sum(0) // CHECKER % 2
        chk = np.where(a[..., None], np.uint8(210), np.uint8(255)).repeat(3, 2)
        bg = Image.fromarray(chk.astype(np.uint8))
        bg.paste(im, (0, 0), im)
        tiles.append(bg)
    if not tiles:
        return
    cols = 16
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 4), rows * (th + 4)), (30, 30, 30))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
    sheet.save(out_path)
    print("montage ->", out_path, sheet.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--montage", action="store_true")
    a = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    priors = json.load(open(PRIORSF))
    skew = load_skew()
    spine = json.load(open(SPINE)) if os.path.exists(SPINE) else {}
    clip = json.load(open(CLIPJS))
    tmpl = None
    pages = a.pages or list(range(1, 177))

    for n in pages:
        try:
            out, ang, frac, src = render(n, priors, skew, spine, clip, tmpl)
            f = os.path.join(OUT_DIR, "%03d.png" % n)
            out.save(f)
            print("p%03d skew %+0.2f  unknown %5.2f%%  spine=%-6s %s"
                  % (n, ang, 100 * frac, src, out.size))
        except Exception as e:
            print("p%03d FAILED: %s" % (n, e))
    if a.montage:
        montage(pages, "/Users/mist/DNB/8609/tmp/stack600_montage.png")


if __name__ == "__main__":
    main()
