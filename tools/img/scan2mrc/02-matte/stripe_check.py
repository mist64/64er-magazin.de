#!/usr/bin/env python3
"""Rule-1 check: what CONTIGUOUS backing-like stripe is left standing at the cut?

Independent of bed_matte's model on purpose -- a fixed crude "dark and neutral / bright and
saturated" test, and it only counts a run that starts AT the cut, so page ink deeper inside
cannot masquerade as residue (the mistake that made an earlier audit flag every dark ad).
"""
import os, sys, json
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
          "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np
from multiprocessing import Pool
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_matte as BM
Image.MAX_IMAGE_PIXELS = None

PROF = BM.load_profile()
DARK_L, DARK_S = 70, 25
BRIGHT_L, BRIGHT_S = 150, 60
MAXRUN = 200


def one(page):
    im = Image.open("/Users/mist/DNB/8609/thumbs_600/%03d.png" % page).convert("RGB")
    a = np.asarray(im)[..., :3].astype(np.float32)
    H, W, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    dtb, dlr = int(BM.WIN_TB_FRAC * H), int(BM.WIN_LR_FRAC * W)
    out = {}
    for edge in BM.EDGES:
        cut, dec, _m = BM.analyze_edge(a, lum, edge, 600, H, W, dtb, dlr, PROF)
        E = BM._orient1(a, edge, dtb, dlr, H, W)
        L = E.mean(2)
        S = E.max(2) - E.min(2)
        backish = ((L < DARK_L) & (S < DARK_S)) | ((L >= BRIGHT_L) & (S >= BRIGHT_S))
        D = E.shape[1]
        N = E.shape[0]
        c = np.clip(cut.astype(int), 0, D - 1)
        idx = np.arange(N)
        runs = np.zeros(N, int)
        cur = c.copy()
        alive = backish[idx, cur]
        for _ in range(MAXRUN):
            if not alive.any():
                break
            runs += alive
            cur = np.minimum(cur + 1, D - 1)
            alive &= backish[idx, cur]
        # rule 2: how much PAGE did we cut? distance from the cut back to the last
        # backing-coloured pixel in the run connected to the border
        idx2 = np.arange(D)[None, :]
        run_end = np.where(backish.any(1), backish.argmin(1), 0)
        over = np.clip(c - run_end, 0, None)
        out[edge] = dict(decision=dec, cut=float(np.median(cut)),
                         p95=float(np.percentile(runs, 95)),
                         frac=float((runs > 3).mean()),
                         over_p50=float(np.percentile(over, 50)),
                         over_p95=float(np.percentile(over, 95)))
    return page, out


if __name__ == "__main__":
    pages = list(range(1, 177))
    with Pool(4) as p:
        res = dict(p.map(one, pages))
    json.dump({str(k): v for k, v in res.items()}, open("/Users/mist/DNB/8609/tmp/stripes.json", "w"))
    print("%-7s %s" % ("edge", "pages with a stripe on >5% of scanlines | overcut"))
    for e in BM.EDGES:
        bad = [(k, v[e]) for k, v in res.items() if v[e]["frac"] > 0.05 and v[e]["p95"] > 3]
        bad.sort(key=lambda t: -t[1]["p95"])
        ov = np.array([v[e]["over_p50"] for v in res.values() if v[e]["decision"] == "CUT"])
        print("%-7s %3d   overcut p50 %5.1f  p90 %5.1f" % (
            e, len(bad), np.percentile(ov, 50) if ov.size else 0,
            np.percentile(ov, 90) if ov.size else 0))
        for k, m in bad[:6]:
            print("        p%-4d %4.0fpx on %3.0f%% of lines  (cut %5.0f, %s)"
                  % (k, m["p95"], 100 * m["frac"], m["cut"], m["decision"]))
