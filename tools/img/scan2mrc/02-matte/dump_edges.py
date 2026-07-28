#!/usr/bin/env python3
"""Dump bed_matte's per-edge metrics for every page, for the raw-data pass."""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
          "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = "1"
import sys, json
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import bed_matte as BM
Image.MAX_IMAGE_PIXELS = None

PROF = BM.load_profile()


def one(n):
    _, pct, meta = BM.bed_matte(Image.open("/Users/mist/DNB/8609/thumbs_600/%03d.png" % n).convert("RGB"),
                                600, return_meta=True, profile=PROF)
    for e in meta:
        meta[e].pop("mat_colours", None)
    return n, pct, meta


if __name__ == "__main__":
    pages = [int(f[:3]) for f in sorted(os.listdir("/Users/mist/DNB/8609/thumbs_600")) if f.endswith(".png")]
    with Pool(4) as p:
        res = p.map(one, pages)
    json.dump({str(n): {"pct": pct, "edges": m} for n, pct, m in res},
              open("/Users/mist/DNB/8609/tmp/edge_metrics.json", "w"), indent=1)
    print("pages", len(res))
