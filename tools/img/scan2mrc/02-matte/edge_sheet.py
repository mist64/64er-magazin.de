#!/usr/bin/env python3
"""Vision check: render each page's four edge bands with the APPLIED cut drawn on them.

Independent of the detector's own arithmetic -- it renders what was actually cut, so the
question "did it do the right thing" is answered by looking, not by re-running the same maths.
Green line = where the cut lands. Everything above/left of it is discarded.
"""
import os, sys, json
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
          "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_matte as BM
Image.MAX_IMAGE_PIXELS = None

BAND = 260          # depth of the band shown, px @600dpi
COLS = 900          # width each strip is scaled to
PROF = BM.load_profile()


def strip(page):
    im = Image.open("/Users/mist/DNB/8609/thumbs_600/%03d.png" % page).convert("RGB")
    a = np.asarray(im)[..., :3].astype(np.float32)
    H, W, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    dtb, dlr = int(BM.WIN_TB_FRAC * H), int(BM.WIN_LR_FRAC * W)
    tiles = []
    for edge in BM.EDGES:
        cut, dec, m = BM.analyze_edge(a, lum, edge, 600, H, W, dtb, dlr, PROF)
        band = BM._orient1(a, edge, dtb, dlr, H, W)[:, :BAND]      # (N, BAND, 3)
        img = Image.fromarray(band.astype(np.uint8)).transpose(Image.TRANSPOSE)
        img = img.resize((COLS, BAND), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        n = len(cut)
        for i in range(0, COLS):
            v = cut[min(n - 1, int(i * n / COLS))]
            if 0 < v < BAND:
                d.line([(i, v), (i, v)], fill=(0, 255, 0), width=1)
                d.line([(i, v - 1), (i, v + 1)], fill=(0, 255, 0))
        d.text((4, 4), "p%03d %s %s %.0fpx" % (page, edge, dec.split("(")[0],
                                               float(np.median(cut))), fill=(255, 0, 255))
        tiles.append(img)
    out = Image.new("RGB", (COLS, 4 * (BAND + 6)), (255, 255, 255))
    for i, t in enumerate(tiles):
        out.paste(t, (0, i * (BAND + 6)))
    return out


def one(p):
    strip(p).save("/Users/mist/DNB/8609/tmp/edges/%03d.png" % p)
    return p


if __name__ == "__main__":
    os.makedirs("/Users/mist/DNB/8609/tmp/edges", exist_ok=True)
    pages = [int(x) for x in sys.argv[1:]]
    with Pool(4) as pool:
        for p in pool.imap_unordered(one, pages):
            pass
    print("wrote", len(pages))
