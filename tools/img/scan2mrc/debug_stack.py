#!/usr/bin/env python3
"""
DEBUG STACK VIEW -- all front-end stages composited on one image, in pipeline order.
=====================================================================================
For each page, show (600-dpi thumb):
  1. 02  bed matte     -> MAGENTA 50% over the bed/yellow cut regions (all 4 sides).
  2. 02b opposite page -> CYAN 50% over the neighbor-strip cut (spine side), when confident.
  3. 01  deskew        -> the whole painted composite is ROTATED by the page's measured
         skew angle (PIL +angle, expand); pixels ADDED by the rotation (the corner wedges,
         which are genuinely "unknown") are tinted ORANGE.
  4. 03  A4 crop        -> the axis-aligned A4 rectangle (RED), anchored to the deskewed
         logo position with the GLOBAL A/B/S constants -- i.e. the crop as it lands in the
         final deskewed frame.

Order matters: matte + spine are detected/painted on the RAW thumb (that is the frame they
were computed in, same as crop_windows.json), THEN the composite is deskewed, THEN the crop
rect is drawn axis-aligned in the deskewed frame. So the slightly-tilted matted page edges
sit inside a straight A4 box -- which is exactly what the crop step does.

The logo anchor is mapped raw->deskewed WITHOUT sign math: we rotate a one-pixel marker with
the identical rotate() call and read back its new location (dodges the ndimage-vs-PIL sign
gotcha in 01-deskew/NOTES.md).

Usage:  debug_stack.py [pages...]     (default: a curated mix)
Output: tmp/stack_NNN.png
"""
import os, sys, re, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "02-matte"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "02b-opposite-page"))
from bed_matte import bed_matte
from spine_matte import spine_matte
Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
# --------------------------------------------------------------------------- #
THUMB   = "/Users/mist/DNB/8609/thumbs_600"
SKEW    = "/Users/mist/DNB/8609/tmp/skew_all.txt"
CROP    = "/Users/mist/DNB/8609/tmp/crop_windows.json"
PRIORSF = os.path.join(os.path.dirname(__file__), "02-matte/priors.json")
OUT     = "/Users/mist/DNB/8609/tmp"

SCALE       = 4                       # master 2400 -> 600 thumb
BLEND       = 0.5                     # overlay opacity for matte/spine tints
COL_BED     = (255,   0, 255)         # magenta  -- 02 bed/yellow matte
COL_SPINE   = (  0, 210, 255)         # cyan     -- 02b opposite-page matte
COL_DESKEW  = (255, 150,   0)         # orange   -- pixels added by the deskew rotation
COL_CROP    = (255,   0,   0)         # red      -- 03 A4 crop rectangle
CROP_LW     = 5                       # crop rect line half-width (px)

DEFAULT = [4, 16, 41, 84, 89, 47]     # big-skew / spine / top-wedge / odd-schematic / no-logo


def load_skew():
    """page -> leveling angle (deg), the Method-A value to feed PIL Image.rotate(+angle)."""
    ang = {}
    for ln in open(SKEW):
        m = re.search(r"/(\d+)\.png:\s*([+-]?\d+\.\d+)\s*deg", ln)
        if m:
            ang[int(m.group(1))] = float(m.group(2))
    return ang


def tint(base, mask, color):
    """Blend `color` at BLEND opacity into `base` (uint8 HxWx3) where mask is True."""
    if not mask.any():
        return
    idx = mask
    base[idx] = ((1 - BLEND) * base[idx] + BLEND * np.array(color)).astype(np.uint8)


def main():
    crop = {p["page"]: p for p in json.load(open(CROP))["pages"]}
    meta = json.load(open(CROP))
    A_m = meta["vertical"]["A_below_baseline"]        # master px
    B_m = meta["vertical"]["B_above_baseline"]
    S_m = meta["horizontal"]["spine_vs_logo_offset"]  # {"even":+, "odd":-}
    A4_W_m = meta["A4_W"]
    # to 600-thumb px
    A_b, B_b = A_m / SCALE, B_m / SCALE
    Se, So   = S_m["even"] / SCALE, S_m["odd"] / SCALE
    W4       = A4_W_m / SCALE

    priors = json.load(open(PRIORSF))
    skew   = load_skew()
    pages  = [int(x) for x in sys.argv[1:]] or DEFAULT

    for n in pages:
        im = Image.open(os.path.join(THUMB, f"{n:03d}.png")).convert("RGB")
        rgb = np.asarray(im).copy()
        H, W = rgb.shape[:2]

        # -- 02 bed matte + 02b spine, detected on the RAW thumb --------------- #
        bed_rgba, _, _  = bed_matte(im, 600, priors=priors, page_no=n, return_meta=True)
        spn_rgba, _, _  = spine_matte(im, 600, page_no=n, return_meta=True)
        bed_cut   = np.asarray(bed_rgba)[:, :, 3] == 0
        spine_cut = np.asarray(spn_rgba)[:, :, 3] == 0
        tint(rgb, bed_cut,   COL_BED)
        tint(rgb, spine_cut, COL_SPINE)

        # -- 01 deskew: rotate the painted composite; mark rotation-added px ---- #
        ang = skew.get(n, 0.0)
        comp = Image.fromarray(rgb)
        valid = Image.new("L", (W, H), 255)                 # 255 = real pixel
        if abs(ang) > 1e-3:
            comp  = comp.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
            valid = valid.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
        out = np.asarray(comp).copy()
        added = np.asarray(valid) == 0                       # pixels created by the rotation
        out[added] = COL_DESKEW
        Hn, Wn = out.shape[:2]

        # -- map the logo anchor raw -> deskewed frame (marker rotate) --------- #
        ax_m, ay_m = crop[n]["anchor_x"] / SCALE, crop[n]["anchor_y"] / SCALE
        mk = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mk).ellipse([ax_m-3, ay_m-3, ax_m+3, ay_m+3], fill=255)
        if abs(ang) > 1e-3:
            mk = mk.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
        ys, xs = np.where(np.asarray(mk) > 0)
        ax, ay = (xs.mean(), ys.mean()) if len(xs) else (ax_m, ay_m)

        # -- 03 A4 crop rect in the deskewed frame (axis-aligned) -------------- #
        y0, y1 = ay - B_b, ay + A_b
        if crop[n]["parity"] == "even":       # logo left, spine right
            x1 = ax + Se; x0 = x1 - W4
        else:                                  # logo right, spine left
            x0 = ax + So; x1 = x0 + W4

        img = Image.fromarray(out)
        dr = ImageDraw.Draw(img)
        for w in range(-CROP_LW, CROP_LW + 1):
            dr.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=COL_CROP)
        dr.ellipse([ax-9, ay-9, ax+9, ay+9], fill=(255, 220, 0))   # anchor dot
        tag = crop[n]["confidence"]
        dr.rectangle([8, 8, 760, 74], fill=(0, 0, 0))
        dr.text((18, 20), f"p{n:03d} {crop[n]['parity']} [{tag}]  skew {ang:+.2f}deg  "
                          f"magenta=bed cyan=spine orange=deskew red=A4", fill=(255, 255, 255))

        outp = os.path.join(OUT, f"stack_{n:03d}.png")
        img.save(outp)
        print("wrote", outp, f"({Wn}x{Hn}) skew={ang:+.2f}")


if __name__ == "__main__":
    main()
