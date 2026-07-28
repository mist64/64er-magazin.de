#!/usr/bin/env python3
"""Does the full-res apply reproduce the decision made at 600 dpi?

Downscale the 2400-dpi A4 output by 4 and compare against tmp/a4/NNN.png, which was produced by
completely different code (PIL crop of the 600-dpi render) from the same geometry. Reports the
registration offset found by cross-correlation and the correlation at that offset, plus how much
the two alpha masks disagree.

A match is not a tautology: the full-res path inverse-maps a rotated rectangle onto the raw
master in one interpolation, while the 600-dpi path rotated the whole canvas and then cropped it.
If the rectangle, the scale, or the rotation convention were wrong, they would disagree.
"""
import os, sys, json
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
FULL = "/Users/mist/DNB/8609/tmp/cmyk_a4"
REF = "/Users/mist/DNB/8609/tmp/a4"


def best_offset(a, b, rad=6):
    """Integer offset maximising correlation, searched +-rad px."""
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    best = (-2, 0, 0)
    h, w = a.shape
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            aa = a[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
            bb = b[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
            c = float((aa * bb).mean())
            if c > best[0]:
                best = (c, dx, dy)
    return best


def check(page):
    f = Image.open(os.path.join(FULL, "%03d_rgb.png" % page)).convert("RGB")
    small = f.resize((f.width // 4, f.height // 4), Image.LANCZOS)
    ref = Image.open(os.path.join(REF, "%03d.png" % page))
    r = np.asarray(ref)
    # compare on a central patch, on luma, where content (not margin) dominates
    H, W = small.height, small.width
    cy, cx = H // 2, W // 2
    s = 700
    a = np.asarray(small.convert("L"), np.float32)[cy - s:cy + s, cx - s:cx + s]
    b = np.asarray(Image.fromarray(r[..., :3]).convert("L"), np.float32)[cy - s:cy + s, cx - s:cx + s]
    corr, dx, dy = best_offset(a, b)
    # alpha agreement
    known = np.asarray(Image.open(os.path.join(FULL, "%03d_known.png" % page)).convert("L")) > 127
    kn_small = np.asarray(Image.fromarray(known.astype(np.uint8) * 255).resize(
        (known.shape[1] // 4, known.shape[0] // 4), Image.NEAREST)) > 127
    ref_known = r[..., 3] > 0
    n = min(kn_small.shape[0], ref_known.shape[0]), min(kn_small.shape[1], ref_known.shape[1])
    dis = float((kn_small[:n[0], :n[1]] != ref_known[:n[0], :n[1]]).mean())
    return {"page": page, "corr": round(corr, 4), "offset_600px": [dx, dy],
            "offset_mm": [round(dx / 600 * 25.4, 3), round(dy / 600 * 25.4, 3)],
            "alpha_disagree_pct": round(100 * dis, 3),
            "size_full": [f.width, f.height], "size_ref": [ref.width, ref.height]}


if __name__ == "__main__":
    out = [check(int(p)) for p in sys.argv[1:]]
    for r in out:
        print(json.dumps(r))
    json.dump(out, open("/Users/mist/DNB/8609/tmp/verify_fullres.json", "w"), indent=1)
