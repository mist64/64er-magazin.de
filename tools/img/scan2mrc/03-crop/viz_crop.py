#!/usr/bin/env python3
"""Draw the 03-crop result on 600-dpi thumbs for vision review.
For each requested page: logo bbox (green outline), spine line (cyan), and the
A4 crop rectangle (red box) -- all mapped MASTER->600 by /SCALE. Saves
tmp/crop_NNN.png. Usage: viz_crop.py [pages...]  (default: a curated mix)."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None

SCALE = 4
THUMB = "/Users/mist/DNB/8609/thumbs_600"
CROP  = "/Users/mist/DNB/8609/tmp/crop_windows.json"
LOGO  = "/Users/mist/DNB/8609/tmp/logo_positions.json"
MATTE = "/Users/mist/DNB/8609/tmp/matte_cache.json"
OUT   = "/Users/mist/DNB/8609/tmp"

DEFAULT = [8, 16, 37, 53, 84, 89,       # found even/odd, incl top-wedge (84) / bottom-yellow
           47, 5, 90, 45, 163, 110]     # no-logo interp + full-bleed/deep-alpha cases


def main():
    crop = {p["page"]: p for p in json.load(open(CROP))["pages"]}
    logo = {p["page"]: p for p in json.load(open(LOGO))}
    matte = json.load(open(MATTE))
    pages = [int(x) for x in sys.argv[1:]] or DEFAULT

    for n in pages:
        im = Image.open(os.path.join(THUMB, f"{n:03d}.png")).convert("RGB")
        d = ImageDraw.Draw(im)
        c = crop[n]; x0, y0, x1, y1 = [v / SCALE for v in c["window"]]
        # A4 crop rectangle (red, thick)
        for w in range(6):
            d.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=(255, 0, 0))
        # logo bbox (green) -- only meaningful when found
        lo = logo[n]
        if lo["found"]:
            bx = [v for v in lo["bbox_600"]]
            for w in range(3):
                d.rectangle([bx[0]-w, bx[1]-w, bx[2]+w, bx[3]+w], outline=(0, 220, 0))
        # anchor point (yellow dot)
        ax, ay = c["anchor_x"]/SCALE, c["anchor_y"]/SCALE
        d.ellipse([ax-14, ay-14, ax+14, ay+14], fill=(255, 220, 0))
        # spine line (cyan) if detected
        sp = matte[str(n)]["spine"]
        if sp.get("conf") == "HIGH" and sp.get("x_top") is not None:
            d.line([sp["x_top"], 0, sp["x_bot"], im.size[1]], fill=(0, 210, 255), width=5)
        tag = c["confidence"]
        d.rectangle([10, 10, 620, 70], fill=(0, 0, 0))
        d.text((20, 22), f"p{n:03d} {c['parity']} [{tag}] alpha={c['alpha_frac']*100:.1f}%",
               fill=(255, 255, 255))
        outp = os.path.join(OUT, f"crop_{n:03d}.png")
        im.save(outp)
        print("wrote", outp, "win600", [round(v) for v in (x0, y0, x1, y1)])


if __name__ == "__main__":
    main()
