#!/usr/bin/env python3
"""p023, paper tint at the fore edge and the top, inside the page box: the before/after proof for regrade_023.py.

Definition as SH09 reviewed/colour-030-031.txt: paper = Rec.601 lum >= 185; a paper pixel is TINTED if
max-min of its RGB >= 6.  Bands 0-3 / 3-6 / 6-10 mm inside the box edge, 20 mm clear of the corners.
p023 is a recto, so the fore edge is the right.  Usage: tint_023.py X0 Y0 X1 Y1  (the page box in masters600/023.png).
Run with ISSUE=SH10.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
a = np.array(Image.open(R.OUT_MASTER / "023.png").convert("RGB")).astype(np.int16)[y0:y1 + 1, x0:x1 + 1]
h, w, _ = a.shape
mm, c = R.MM, int(20 * R.MM)
lum = a @ np.array([0.299, 0.587, 0.114])
for edge in ("fore", "top"):
    cells = []
    for lo, hi in ((0, 3), (3, 6), (6, 10)):
        l, u = int(lo * mm), int(hi * mm)
        sl = (slice(c, h - c), slice(w - u, w - l)) if edge == "fore" else (slice(l, u), slice(c, w - c))
        b, Lb = a[sl].reshape(-1, 3), lum[sl].ravel()
        p = b[Lb >= 185]
        t = (p.max(1) - p.min(1)) >= 6
        cells.append(f"{lo}-{hi} mm: paper {len(p) / len(b):5.1%} tinted {t.mean():5.1%} R-B {(p[:, 0] - p[:, 2]).mean():+5.1f}")
    print(f"{edge:4s} | " + " | ".join(cells))
