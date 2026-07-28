#!/usr/bin/env python3
"""Try the inpainting on all 176 pages at 600 dpi, where it is ~16x cheaper than at 2400.

The fill method is a fidelity decision, so it should be judged on the whole issue before it is
baked into a 2.5-min-per-page full-res run. Same code as the deliverable uses (04-grade/inpaint):
edge bands mirrored, interior holes diffused.

Input  tmp/a4/NNN.png        600 dpi RGBA crop (alpha = unknown)
Output tmp/render/filled600/NNN.tif   RGB, filled
       tmp/fill600_report.json        per page: what was filled and how much

The alpha is NOT carried into the output on purpose -- the whole point of looking at these is to
see what the fill produced. The mask still exists in tmp/a4 if a later stage needs it.
"""
import os, sys, json, argparse, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from multiprocessing import Pool
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inpaint as IP

Image.MAX_IMAGE_PIXELS = None
SRC = "/Users/mist/DNB/8609/tmp/a4"
OUT = "/Users/mist/DNB/8609/tmp/render/filled600"   # +"_"+method for anything but mirror


def one(args):
    n, method = args
    t0 = time.time()
    a = np.asarray(Image.open(os.path.join(SRC, "%03d.png" % n)))
    rgb = np.ascontiguousarray(a[..., :3])
    known = a[..., 3] > 0
    unk_before = float((~known).mean())
    rgb, nh = IP.fill(rgb, known, method=method)
    outd = OUT if method == "mirror" else OUT + "_" + method
    os.makedirs(outd, exist_ok=True)
    Image.fromarray(rgb).save(os.path.join(outd, "%03d.tif" % n), compression=None)
    # did anything stay unfilled? (a fully-unknown row/column has nothing to mirror from)
    return {"page": n, "unknown_pct": round(100 * unk_before, 3), "holes_filled": nh,
            "secs": round(time.time() - t0, 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--method", default="mirror", choices=("mirror", "replicate", "mode"))
    ap.add_argument("pages", nargs="*", type=int)
    A = ap.parse_args()
    pages = A.pages or sorted(int(f[:3]) for f in os.listdir(SRC) if f.endswith(".png"))
    with Pool(A.jobs) as pool:
        res = pool.map(one, [(p, A.method) for p in pages])
    res.sort(key=lambda r: r["page"])
    json.dump(res, open("/Users/mist/DNB/8609/tmp/fill600_report_%s.json" % A.method, "w"), indent=1)
    u = np.array([r["unknown_pct"] for r in res])
    h = np.array([r["holes_filled"] for r in res])
    s = np.array([r["secs"] for r in res])
    print("pages          : %d" % len(res))
    print("unknown filled : p50 %.2f%%  p95 %.2f%%  max %.2f%%" % (
        np.percentile(u, 50), np.percentile(u, 95), u.max()))
    print("interior holes : %d pages had any, %d components total" % ((h > 0).sum(), h.sum()))
    print("time           : %.1f s/page (%.0f s total wall at %d jobs)" % (
        s.mean(), s.sum() / A.jobs, A.jobs))
