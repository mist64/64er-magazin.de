#!/usr/bin/env python3
"""The contract between the 600-dpi detection stages and the full-res apply.

Everything the apply needs, expressed so that ONE affine sample produces the final A4 page:

  tmp/page_geometry.json   per page: skew angle, the A4 window as a ROTATED RECTANGLE in raw
                           master pixels (its four corners), the output size, parity, and where
                           the anchor came from.
  tmp/page_geometry/NNN.npz  the matte, as the PARAMETERS it was fitted with rather than as a
                           bitmap: per-scanline cut depth for each bed edge and for the spine,
                           in raw 600-dpi pixels, plus the clip-hole shapes as a packed bitmap.

WHY A ROTATED RECTANGLE AND NOT "ROTATE THEN CROP". The window was chosen in the deskewed,
expanded frame. Reproducing that at 2400 dpi would mean rotating a 600 MP image (1.8 GB as RGB),
matching PIL's expand convention exactly, cropping, and discarding ~90% of the work. Expressed as
a rectangle in the ORIGINAL master, the apply inverse-maps the output grid straight onto the
master in a single interpolation -- cheaper, and with no canvas convention to replicate.

WHY LINES AND NOT A BITMAP. The bed and spine cuts are straight lines. Upscaling a 600-dpi mask
x4 quantises them into 4-px stairs; re-rasterising from the per-scanline depths reproduces the
line at full resolution. Only the clip holes are irregular, and they are the one thing here that
gets inpainted anyway.

The transform is the same one verified in logo_clearance.py by landing the anchor on the glyph.
"""
import os, sys, json, re, argparse
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
from multiprocessing import Pool
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "02-matte"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "02b-opposite-page"))
import stack_render as SR
import bed_matte as BM
import hole_masks as HM

Image.MAX_IMAGE_PIXELS = None

THUMB = "/Users/mist/DNB/8609/thumbs_600"
MASTER = "/Users/mist/DNB/8609/master_2400"
WINS = "/Users/mist/DNB/8609/tmp/crop_windows_v2.json"
OUTJ = "/Users/mist/DNB/8609/tmp/page_geometry.json"
OUTD = "/Users/mist/DNB/8609/tmp/page_geometry"
DPI_OUT = 2400
A4_W_OUT = int(round(210.0 / 25.4 * DPI_OUT))       # 19843
A4_H_OUT = int(round(297.0 / 25.4 * DPI_OUT))       # 28063


def inv(pt, ang, src_wh, dst_wh):
    """Deskewed-frame point -> RAW-frame point (inverse of stack_render's rotate+expand)."""
    X, Y = pt
    W, H = src_wh
    W2, H2 = dst_wh
    t = np.deg2rad(ang)
    xr, yr = X - W2 / 2.0, Y - H2 / 2.0
    dx = np.cos(t) * xr - np.sin(t) * yr
    dy = np.sin(t) * xr + np.cos(t) * yr
    return dx + W / 2.0, dy + H / 2.0


def _one(args):
    n, w = args
    im = Image.open(os.path.join(THUMB, "%03d.png" % n))
    W, H = im.size
    mw, mh = Image.open(os.path.join(MASTER, "%03d.png" % n)).size
    ang = _SKEW.get(n, 0.0)

    # the deskewed canvas size stack_render produced (PIL expand geometry)
    if abs(ang) > 1e-3:
        dw, dh = im.rotate(ang, expand=True).size
    else:
        dw, dh = W, H

    # window corners in the deskewed frame -> raw thumb frame -> raw master frame
    x0, y0, ww, hh = w["x0"], w["y0"], w["w"], w["h"]
    corners_d = [(x0, y0), (x0 + ww, y0), (x0 + ww, y0 + hh), (x0, y0 + hh)]   # TL TR BR BL
    corners_t = [inv(p, ang, (W, H), (dw, dh)) for p in corners_d]
    sx, sy = mw / float(W), mh / float(H)          # exact per-page scale, not a hardcoded 4
    corners_m = [(x * sx, y * sy) for x, y in corners_t]

    # --- the matte, as parameters ---------------------------------------------------------
    a = np.asarray(im.convert("RGB"))[..., :3].astype(np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    dtb, dlr = int(BM.WIN_TB_FRAC * H), int(BM.WIN_LR_FRAC * W)
    bed = {}
    for edge in BM.EDGES:
        cut, dec, _m = BM.analyze_edge(a, lum, edge, 600, H, W, dtb, dlr, _PROF)
        bed[edge] = np.asarray(cut, np.float32)     # depth inward from THAT border, per scanline
        bed[edge + "_dec"] = np.array([dec])

    parity = "even" if n % 2 == 0 else "odd"
    rec = _SPINE.get("%03d" % n)
    ys = np.arange(H, dtype=np.float32)
    if rec and rec.get("found"):
        inb = rec["inboard_top"] + (rec["inboard_bot"] - rec["inboard_top"]) * (ys / max(1, H - 1))
        inb = inb + SR.SPINE_OVER + (SR.SPINE_EXTRA if rec.get("extra_cut") else 0)
        ssrc = "colour+" if rec.get("extra_cut") else "colour"
    else:
        hi = SR.hole_line_inb(_CLIP.get("%03d" % n), H, W, parity)
        inb = (hi + SR.HOLE_OVERCUT) if hi is not None else np.full(H, -1.0, np.float32)
        ssrc = "holes" if hi is not None else "none"

    holes = np.zeros((H, W), bool)
    ce = _CLIP.get("%03d" % n)
    if ce:
        try:
            holes = HM.segment_hole_shapes(np.asarray(im.convert("L"), np.float32),
                                           ce)["mask"].astype(bool)
        except Exception:
            pass

    os.makedirs(OUTD, exist_ok=True)
    np.savez_compressed(os.path.join(OUTD, "%03d.npz" % n),
                        bed_top=bed["top"], bed_bottom=bed["bottom"],
                        bed_left=bed["left"], bed_right=bed["right"],
                        spine_inb=np.asarray(inb, np.float32),
                        holes=np.packbits(holes, axis=-1), holes_shape=np.array([H, W]))
    return {
        "page": n, "angle_deg": ang, "parity": parity,
        "thumb_size": [W, H], "master_size": [mw, mh], "scale": [sx, sy],
        "deskewed_size": [dw, dh],
        "corners_master": [[round(x, 2), round(y, 2)] for x, y in corners_m],
        "corners_thumb": [[round(x, 3), round(y, 3)] for x, y in corners_t],
        "out_size": [A4_W_OUT, A4_H_OUT],
        "anchor_src": w["src"], "spine_src": ssrc,
        "bed_decisions": {e: str(bed[e + "_dec"][0]) for e in BM.EDGES},
    }


_SKEW, _SPINE, _CLIP, _PROF = {}, {}, {}, None


def _init():
    global _SKEW, _SPINE, _CLIP, _PROF
    _SKEW = SR.load_skew()
    _SPINE = json.load(open(SR.SPINE)) if os.path.exists(SR.SPINE) else {}
    _CLIP = json.load(open(SR.CLIPJS))
    _PROF = BM.load_profile()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("pages", nargs="*", type=int)
    A = ap.parse_args()
    wins = json.load(open(WINS))["windows"]
    items = sorted((int(k), v) for k, v in wins.items())
    if A.pages:
        items = [it for it in items if it[0] in A.pages]
    with Pool(A.jobs, initializer=_init) as pool:
        res = pool.map(_one, items)
    res.sort(key=lambda r: r["page"])
    json.dump({"dpi_out": DPI_OUT, "a4_out": [A4_W_OUT, A4_H_OUT],
               "pages": {str(r["page"]): r for r in res}}, open(OUTJ, "w"), indent=1)
    print("wrote %s and %d npz" % (OUTJ, len(res)))
    for r in res[:4]:
        print("  p%03d ang %+.2f  corners_master TL %s BR %s  %s/%s" % (
            r["page"], r["angle_deg"], r["corners_master"][0], r["corners_master"][2],
            r["anchor_src"], r["spine_src"]))
