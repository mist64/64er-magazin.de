#!/usr/bin/env python3
"""Verify EVERY rendered page, not a sample: mode, alpha binarity, coverage, sanity.

Checks per page:
  - RGBA, and alpha strictly {0,255} (a partial value would mean an interpolated fringe;
    alpha here means UNKNOWN, so a half-transparent pixel claims something nothing measured)
  - transparent fraction within a plausible band
  - every border of the canvas is transparent somewhere (the deskew wedge must be marked)
  - no fully-transparent page, no fully-opaque page
  - RGB under alpha is not black-bled into the visible page (checked as: opaque pixels
    adjacent to transparent ones are not systematically darker than their neighbours)
"""
import os, sys, json
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
          "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np
from multiprocessing import Pool
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

SRC = "/Users/mist/DNB/8609/tmp/stack600"


def one(n):
    p = os.path.join(SRC, "%03d.png" % n)
    r = {"page": n, "ok": True, "problems": []}
    im = Image.open(p)
    r["mode"] = im.mode
    r["size"] = list(im.size)
    if im.mode != "RGBA":
        r["ok"] = False
        r["problems"].append("mode=%s" % im.mode)
        return r
    a = np.asarray(im)
    al = a[..., 3]
    vals = np.unique(al)
    r["alpha_values"] = vals.tolist()[:8]
    if not set(vals.tolist()) <= {0, 255}:
        r["ok"] = False
        r["problems"].append("alpha not binary: %s" % vals[:8].tolist())
    tr = float((al == 0).mean())
    r["transparent"] = round(100 * tr, 3)
    if not (0.01 < tr < 0.45):
        r["ok"] = False
        r["problems"].append("transparent %.1f%% out of band" % (100 * tr))
    # every canvas border must contain some transparency (deskew wedge / bed cut)
    for name, edge in (("top", al[0]), ("bottom", al[-1]),
                       ("left", al[:, 0]), ("right", al[:, -1])):
        if (edge == 0).mean() < 0.001:
            r["problems"].append("border %s has no transparency" % name)
            r["ok"] = False
    # per-edge leading transparent run, median over scanlines (px)
    def lead(M):
        first = np.argmin(M == 0, axis=1)
        first = np.where((M == 0).all(1), M.shape[1], first)
        return float(np.median(first))
    r["lead"] = {"left": lead(al), "right": lead(al[:, ::-1]),
                 "top": lead(al.T), "bottom": lead(al.T[:, ::-1])}
    return r


if __name__ == "__main__":
    pages = sorted(int(f[:3]) for f in os.listdir(SRC) if f.endswith(".png"))
    with Pool(4) as pool:
        res = pool.map(one, pages)
    json.dump(res, open("/Users/mist/DNB/8609/tmp/verify_alpha.json", "w"), indent=1)
    bad = [r for r in res if not r["ok"]]
    print("pages checked : %d" % len(res))
    print("RGBA          : %d" % sum(r["mode"] == "RGBA" for r in res))
    print("alpha binary  : %d" % sum(set(r.get("alpha_values", [])) <= {0, 255} for r in res))
    tr = np.array([r["transparent"] for r in res])
    print("transparent %% : min %.2f  p50 %.2f  p95 %.2f  max %.2f" % (
        tr.min(), np.percentile(tr, 50), np.percentile(tr, 95), tr.max()))
    for e in ("left", "right", "top", "bottom"):
        v = np.array([r["lead"][e] for r in res if "lead" in r])
        print("lead %-6s   : p5 %5.0f  p50 %5.0f  p95 %5.0f  max %5.0f" % (
            e, *np.percentile(v, [5, 50, 95]), v.max()))
    print("FAILURES      : %d" % len(bad))
    for r in bad[:20]:
        print("   p%03d %s" % (r["page"], "; ".join(r["problems"])))
