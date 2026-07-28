#!/usr/bin/env python3
"""Milestone 1 reference apply: master scan -> deskewed, matted, A4-cropped, graded CMYK.

ONE affine. The output grid is inverse-mapped straight onto the raw master, so the deskew
rotation and the A4 crop cost a single interpolation between them; nothing is ever rotated at
full canvas size and then thrown away.

Order is geometry -> separate -> grade -> GCR. Grade and GCR are per-pixel and would commute
with geometry, but RESAMPLING does not commute with GCR: interpolating C/M/Y/K independently can
break min(C,M,Y)=0, so all resampling happens before the separation, on RGB.

    THE K CHANNEL IS NOT PER-PIXEL. convert.py normalises K over the GLOBAL min/max of the
    distance-to-black over the whole image, so cropping changes it. Worse, the unknown pixels
    (bed, insert, and the black the rotation invents) take part in that min/max unless excluded
    -- black bed is at distance ~28 from color_k and would set dmin. Three defensible choices,
    all computed here so the difference is a measurement rather than an argument:
        master  reproduce the old behaviour: min/max over every pixel of the full master
        crop    min/max over the cropped page, unknown pixels included
        known   min/max over the KNOWN pixels of the cropped page   <- default
    --knorm selects which one is written; the report prints all three.

Alpha rides alongside as a 1-bit sidecar, because CMYK has no alpha channel and "unknown" is
still true at this stage. Downstream stages MUST read it: a transparent region left as RGB(0,0,0)
separates to solid K and reads as a large black cluster to the MRC classifier.
"""
import os, sys, json, argparse, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
MASTER = "/Users/mist/DNB/8609/master_2400"
GEOJ = "/Users/mist/DNB/8609/tmp/page_geometry.json"
GEOD = "/Users/mist/DNB/8609/tmp/page_geometry"
OUTD = "/Users/mist/DNB/8609/tmp/cmyk_a4"
STRIP = 2048                     # output rows per strip; bounds peak memory

# --- convert.py anchor colours (identical to rust_pipeline/src/separate.rs) -------------------
COLOR_C = np.array([38., 140., 165.]);  COLOR_CM = np.array([36., 44., 79.])
COLOR_CY = np.array([42., 109., 44.]);  COLOR_M = np.array([192., 37., 66.])
COLOR_MY = np.array([185., 34., 31.]);  COLOR_Y = np.array([201., 159., 61.])
COLOR_K = np.array([16., 17., 17.]);    COLOR_W = np.array([201., 195., 188.])
LEVELS_DISPLAY = {"c": (50., 90.), "m": (30., 70.), "y": (30., 70.), "k": (90., 95.)}


def plane(p1, p2, p3):
    nrm = np.cross(p2 - p1, p3 - p1)
    return nrm, -float(np.dot(nrm, p1)), float(np.linalg.norm(nrm))


def cmy_channel(px, pa, pb):
    """ratio of distances to two planes -> 0..255, inverted (convert.py extract_cmy)."""
    na, da, nna = pa
    nb, db, nnb = pb
    d1 = np.abs(px @ na + da) / nna
    d2 = np.abs(px @ nb + db) / nnb
    g = d1 / np.maximum(d1 + d2, 1e-12) * 255.0
    return (255 - g.astype(np.uint8)).astype(np.uint8)


def level(v, lo_pct, hi_pct):
    lo, hi = 255.0 * lo_pct / 100.0, 255.0 * hi_pct / 100.0
    t = np.clip((v.astype(np.float32) - lo) / (hi - lo), 0.0, 1.0)
    return np.floor(t * 255.0 + 0.5).astype(np.uint8)


def affine(corners, W_out, H_out):
    """Output pixel centres -> source coordinates, from the rectangle's four corners."""
    TL, TR, BR, BL = [np.array(c, np.float64) for c in corners]
    ex = (TR - TL) / W_out
    ey = (BL - TL) / H_out
    return TL, ex, ey


def sample_rgb(master, xs, ys):
    """Bilinear sample; returns (rgb float32, inside mask)."""
    H, W = master.shape[:2]
    inside = (xs >= 0) & (xs <= W - 1) & (ys >= 0) & (ys <= H - 1)
    x0 = np.clip(np.floor(xs), 0, W - 2).astype(np.int32)
    y0 = np.clip(np.floor(ys), 0, H - 2).astype(np.int32)
    fx = (xs - x0).astype(np.float32)[..., None]
    fy = (ys - y0).astype(np.float32)[..., None]
    p00 = master[y0, x0].astype(np.float32)
    p01 = master[y0, x0 + 1].astype(np.float32)
    p10 = master[y0 + 1, x0].astype(np.float32)
    p11 = master[y0 + 1, x0 + 1].astype(np.float32)
    top = p00 + (p01 - p00) * fx
    bot = p10 + (p11 - p10) * fx
    return top + (bot - top) * fy, inside


def alpha_for(geo, npz, xt, yt):
    """UNKNOWN mask in the output frame, from the matte PARAMETERS (re-rasterised, not upscaled).

    xt, yt are raw 600-dpi thumb coordinates for each output pixel."""
    Wt, Ht = geo["thumb_size"]
    unk = np.zeros(xt.shape, bool)

    def at(arr, pos, n):
        i = np.clip(pos, 0, n - 1)
        i0 = np.floor(i).astype(np.int32)
        i1 = np.minimum(i0 + 1, n - 1)
        f = (i - i0).astype(np.float32)
        return arr[i0] * (1 - f) + arr[i1] * f

    top = at(npz["bed_top"], xt, npz["bed_top"].shape[0])
    bot = at(npz["bed_bottom"], xt, npz["bed_bottom"].shape[0])
    lef = at(npz["bed_left"], yt, npz["bed_left"].shape[0])
    rig = at(npz["bed_right"], yt, npz["bed_right"].shape[0])
    unk |= yt < top
    unk |= yt > (Ht - 1 - bot)
    unk |= xt < lef
    unk |= xt > (Wt - 1 - rig)

    inb = npz["spine_inb"]
    if float(inb.max()) >= 0:
        d = at(inb, yt, inb.shape[0])
        if geo["parity"] == "even":          # binding on the RIGHT for even pages
            unk |= xt > (Wt - 1 - d)
        else:
            unk |= xt < d

    hs = npz["holes_shape"]
    holes = np.unpackbits(npz["holes"], axis=-1)[:, :int(hs[1])].astype(bool)
    hx = np.clip(np.round(xt), 0, hs[1] - 1).astype(np.int32)
    hy = np.clip(np.round(yt), 0, hs[0] - 1).astype(np.int32)
    unk |= holes[hy, hx]
    return unk


def run(page, knorm="known", write=True):
    t0 = time.time()
    geo = json.load(open(GEOJ))["pages"][str(page)]
    npz = np.load(os.path.join(GEOD, "%03d.npz" % page))
    W_out, H_out = geo["out_size"]
    master = np.asarray(Image.open(os.path.join(MASTER, "%03d.png" % page)).convert("RGB"))
    TLm, exm, eym = affine(geo["corners_master"], W_out, H_out)
    TLt, ext, eyt = affine(geo["corners_thumb"], W_out, H_out)

    rgb = np.zeros((H_out, W_out, 3), np.uint8)
    unk = np.zeros((H_out, W_out), bool)
    u = np.arange(W_out, dtype=np.float64) + 0.5
    for y0 in range(0, H_out, STRIP):
        y1 = min(y0 + STRIP, H_out)
        v = np.arange(y0, y1, dtype=np.float64)[:, None] + 0.5
        xs = TLm[0] + u[None, :] * exm[0] + v * eym[0]
        ys = TLm[1] + u[None, :] * exm[1] + v * eym[1]
        s, inside = sample_rgb(master, xs, ys)
        rgb[y0:y1] = np.clip(s + 0.5, 0, 255).astype(np.uint8)
        xt = TLt[0] + u[None, :] * ext[0] + v * eyt[0]
        yt = TLt[1] + u[None, :] * ext[1] + v * eyt[1]
        unk[y0:y1] = (~inside) | alpha_for(geo, npz, xt, yt)
    del master

    # --- K normalisation: three candidates, one written ---------------------------------
    flat = rgb.reshape(-1, 3).astype(np.float32)
    kd = np.sqrt(((flat - COLOR_K.astype(np.float32)) ** 2).sum(1))
    known = (~unk).reshape(-1)
    cand = {"crop": (float(kd.min()), float(kd.max())),
            "known": (float(kd[known].min()), float(kd[known].max()))}
    m = np.asarray(Image.open(os.path.join(MASTER, "%03d.png" % page)).convert("RGB"))
    mf = m.reshape(-1, 3).astype(np.float32)
    kdm = np.sqrt(((mf - COLOR_K.astype(np.float32)) ** 2).sum(1))
    cand["master"] = (float(kdm.min()), float(kdm.max()))
    del m, mf, kdm
    dmin, dmax = cand[knorm]
    span = max(dmax - dmin, 1e-12)

    pa_c, pb_c = plane(COLOR_C, COLOR_CM, COLOR_CY), plane(COLOR_M, COLOR_Y, COLOR_W)
    pa_m, pb_m = plane(COLOR_M, COLOR_CM, COLOR_MY), plane(COLOR_C, COLOR_Y, COLOR_W)
    pa_y, pb_y = plane(COLOR_Y, COLOR_CY, COLOR_MY), plane(COLOR_C, COLOR_M, COLOR_W)

    C = np.empty((H_out, W_out), np.uint8); M = np.empty_like(C)
    Y = np.empty_like(C); K = np.empty_like(C)
    for y0 in range(0, H_out, STRIP):
        y1 = min(y0 + STRIP, H_out)
        px = rgb[y0:y1].reshape(-1, 3).astype(np.float64)
        c = cmy_channel(px, pa_c, pb_c); mm = cmy_channel(px, pa_m, pb_m)
        yy = cmy_channel(px, pa_y, pb_y)
        d = np.sqrt(((px - COLOR_K) ** 2).sum(1))
        kv = np.clip(((d - dmin) / span * 255.0).astype(np.int64), 0, 255).astype(np.uint8)
        k = (255 - kv)
        sh = (y1 - y0, W_out)
        c = level(c.reshape(sh), *LEVELS_DISPLAY["c"]); mm = level(mm.reshape(sh), *LEVELS_DISPLAY["m"])
        yy = level(yy.reshape(sh), *LEVELS_DISPLAY["y"]); k = level(k.reshape(sh), *LEVELS_DISPLAY["k"])
        neu = np.minimum(np.minimum(c, mm), yy)                    # GCR
        C[y0:y1] = c - neu; M[y0:y1] = mm - neu; Y[y0:y1] = yy - neu
        K[y0:y1] = np.clip(k.astype(np.int16) + neu, 0, 255).astype(np.uint8)

    rep = {"page": page, "out_size": [W_out, H_out], "knorm": knorm,
           "k_candidates": {k: [round(a, 2), round(b, 2)] for k, (a, b) in cand.items()},
           "unknown_pct": round(100.0 * float(unk.mean()), 3),
           "gcr_ok": bool(int(np.minimum(np.minimum(C, M), Y).max()) == 0),
           "mean": {"C": round(float(C.mean()), 2), "M": round(float(M.mean()), 2),
                    "Y": round(float(Y.mean()), 2), "K": round(float(K.mean()), 2)},
           "secs": round(time.time() - t0, 1)}
    if write:
        os.makedirs(OUTD, exist_ok=True)
        Image.merge("CMYK", [Image.fromarray(x) for x in (C, M, Y, K)]).save(
            os.path.join(OUTD, "%03d_cmyk.tif" % page), compression="tiff_lzw")
        Image.fromarray((~unk).astype(np.uint8) * 255).convert("1").save(
            os.path.join(OUTD, "%03d_known.png" % page), optimize=True)
        Image.fromarray(rgb).save(os.path.join(OUTD, "%03d_rgb.png" % page))
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+", type=int)
    ap.add_argument("--knorm", default="known", choices=("master", "crop", "known"))
    ap.add_argument("--no-write", action="store_true")
    A = ap.parse_args()
    out = []
    for p in A.pages:
        r = run(p, A.knorm, not A.no_write)
        out.append(r)
        print(json.dumps(r))
    json.dump(out, open("/Users/mist/DNB/8609/tmp/fullres_report.json", "w"), indent=1)
