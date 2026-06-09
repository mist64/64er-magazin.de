#!/usr/bin/env python3
"""
Compute the canonical sRGB-ish triple that the color pipeline emits for each
single/pair CMYK ink. The exact same profile chain the pipeline uses
(USWebCoatedSWOP.icc → AdobeRGB1998.icc) is applied to a 1×1 CMYK swatch.

Prints a Python dict for paste-in. Run once after profile changes.
"""
import os, subprocess, tempfile
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICC_CMYK = os.path.join(SCRIPT_DIR, "USWebCoatedSWOP.icc")
ICC_RGB  = os.path.join(SCRIPT_DIR, "AdobeRGB1998.icc")

INKS = {
    # name : (C, M, Y, K) at 100 % coverage per channel
    "K":  (0,   0,   0,   255),
    "C":  (255, 0,   0,   0),
    "M":  (0,   255, 0,   0),
    "Y":  (0,   0,   255, 0),
    "MY": (0,   255, 255, 0),  # red
    "MC": (255, 255, 0,   0),  # blue
    "CY": (255, 0,   255, 0),  # green
}

def canonical(cmyk):
    with tempfile.NamedTemporaryFile(suffix=".tiff", delete=False) as f:
        Image.new("CMYK", (1, 1), cmyk).save(f.name)
        out = subprocess.check_output([
            "magick", f.name,
            "-profile", ICC_CMYK,
            "-profile", ICC_RGB,
            "-format",
            "%[fx:int(255*p{0,0}.r+0.5)] %[fx:int(255*p{0,0}.g+0.5)] %[fx:int(255*p{0,0}.b+0.5)]",
            "info:"
        ]).decode().strip()
    os.unlink(f.name)
    return tuple(int(x) for x in out.split())

table = {name: canonical(cmyk) for name, cmyk in INKS.items()}
print("CANONICAL_INK_RGB = {")
for name, rgb in table.items():
    print(f"    {name!r}: {rgb},")
print("}")
