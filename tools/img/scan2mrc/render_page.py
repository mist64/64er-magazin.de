#!/usr/bin/env python3
"""Render a page through the whole front end and emit ALL THREE artifacts, always.

    tmp/render/debug/NNN.tif          600 dpi, nothing removed: magenta hairlines on every cut
                                  boundary + the A4 window rect. This is what you judge from --
                                  an alpha render destroys the evidence (if a cut ate content,
                                  the content is gone and the page merely looks smaller), so the
                                  debug view leaves every pixel in place and only draws lines.
    tmp/render/a4_600/NNN.tif         600 dpi RGBA, cropped to the A4 window. Alpha = UNKNOWN.
                                  The cheap view for checking placement across the whole issue.
    tmp/render/deliver/NNN_cmyk_*.tif 2400 dpi CMYK, graded + GCR, sampled from the master in ONE
    tmp/render/deliver/NNN_known.png  affine; plus the 1-bit sidecar, because CMYK has no alpha and
                                  "unknown" is still true. Downstream MUST read the sidecar: a
                                  transparent region left as RGB(0,0,0) separates to solid K.

They are emitted together on purpose. Keeping them in separate tools meant the debug view and
the deliverable could silently drift apart -- and they did, when the window moved and only some
of the directories were regenerated.

The 600 dpi views come from the detection frame; the 2400 dpi deliverable is sampled from the
master. They are not the same pixels, which is exactly why 04-grade/verify_fullres.py exists.
"""
import os, sys, json, argparse, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
import scipy.ndimage as ndi
from multiprocessing import Pool
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "03-crop"))
sys.path.insert(0, os.path.join(HERE, "04-grade"))
import stack_render as SR
import emit_geometry as EG
import apply_fullres as AF

Image.MAX_IMAGE_PIXELS = None
ROOT = "/Users/mist/DNB/8609/tmp/render"
WINS = "/Users/mist/DNB/8609/tmp/crop_windows_v2.json"
HAIR = 3                       # px @600dpi; 1px is dropped by the resampler when viewed whole
COL_HAIR = (255, 0, 255)
COL_LOGO = (0, 220, 0)
COL_SPINE = (40, 120, 255)
LINE = 5


def _paint(a, y0, y1, x0, x1, col):
    H, W = a.shape[:2]
    y0, y1 = max(int(y0), 0), min(int(y1), H)
    x0, x1 = max(int(x0), 0), min(int(x1), W)
    if y1 > y0 and x1 > x0:
        a[y0:y1, x0:x1, :3] = col
        if a.shape[2] == 4:
            a[y0:y1, x0:x1, 3] = 255


def debug_png(rgba, win):
    """Hairline every cut boundary, then draw the window rect over it."""
    a = np.asarray(rgba).copy()
    unknown = a[..., 3] == 0
    if unknown.any():
        inner = ndi.binary_erosion(unknown, np.ones((2 * HAIR + 1, 2 * HAIR + 1), bool))
        a[unknown & ~inner, :3] = COL_HAIR
    a[..., 3] = 255                                   # debug view removes nothing
    col = COL_LOGO if win["src"] == "logo" else COL_SPINE
    x0, y0 = win["x0"], win["y0"]
    x1, y1 = x0 + win["w"], y0 + win["h"]
    if win.get("anchor"):
        ax, ay = win["anchor"]
        _paint(a, ay - 2, ay + 3, ax - 40, ax + 41, COL_HAIR)
        _paint(a, ay - 40, ay + 41, ax - 2, ax + 3, COL_HAIR)
    elif win.get("spine_x") is not None:
        sx = int(round(win["spine_x"]))
        for ty in range(max(y0, 0), y1, 160):
            _paint(a, ty, ty + 80, sx - 3, sx + 4, COL_HAIR)
    _paint(a, y0, y0 + LINE, x0, x1, col)
    _paint(a, y1 - LINE, y1, x0, x1, col)
    _paint(a, y0, y1, x0, x0 + LINE, col)
    _paint(a, y0, y1, x1 - LINE, x1, col)
    return Image.fromarray(a[..., :3], "RGB")


def crop600(rgba, win):
    """A4 window at 600 dpi. Overhang stays TRANSPARENT -- clamping would shift the content."""
    src = np.asarray(rgba)
    H, W = src.shape[:2]
    out = np.zeros((win["h"], win["w"], 4), np.uint8)
    x0, y0 = win["x0"], win["y0"]
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + win["w"], W), min(y0 + win["h"], H)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
    return Image.fromarray(out, "RGBA")


def _one(args):
    return render(*args)


def render(page, variant="display", knorm="known", skip_full=False, keep_rgb=False,
           inpaint=False, detect_too=False, page_rgb=False):
    t0 = time.time()
    win = json.load(open(WINS))["windows"][str(page)]
    for d in ("debug", "a4_600", "deliver"):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)

    rgba, ang, frac, src = SR.render(page, _CTX["priors"], _CTX["skew"],
                                     _CTX["spine"], _CTX["clip"], None)
    # UNCOMPRESSED TIFF. These are local intermediates, not artifacts to ship, and the disk has
    # room to spare -- so spending CPU to shrink them is spending the wrong resource. Measured on
    # a 5155x7198 debug page: raw TIFF 0.05s/111MB against default PNG 8.5s/68MB. The encoder was
    # more than TWICE the cost of the analysis it exists to show, to save 40MB.
    #   raw TIFF  0.05s  111MB      PNG level 1  3.06s   72MB
    #   PNG lvl 0 0.43s  111MB      PNG default  8.50s   68MB
    # The 2400dpi CMYK deliverable is the one place compression stays on: raw would be 2.23GB a
    # page, 392GB for the issue against ~180GB free, so there it buys something real.
    debug_png(rgba, win).save(os.path.join(ROOT, "debug", "%03d.tif" % page), compression=None)
    c6 = crop600(rgba, win)
    c6.save(os.path.join(ROOT, "a4_600", "%03d.tif" % page), compression=None)
    a6 = np.asarray(c6)[..., 3]

    rep = {"page": page, "src": win["src"], "skew": ang, "spine": src,
           "alpha600_pct": round(100.0 * float((a6 == 0).mean()), 3)}
    if not skip_full:
        AF.OUTD = os.path.join(ROOT, "deliver")
        rep.update({("full_" + k): v for k, v in
                    AF.run(page, knorm=knorm, write=True, variant=variant,
                           keep_rgb=keep_rgb, inpaint=inpaint,
                           detect_too=detect_too, page_rgb=page_rgb).items()})
    rep["secs"] = round(time.time() - t0, 1)
    return rep


_CTX = {}


def _init():
    _CTX["skew"] = SR.load_skew()
    _CTX["spine"] = json.load(open(SR.SPINE)) if os.path.exists(SR.SPINE) else {}
    _CTX["clip"] = json.load(open(SR.CLIPJS))
    _CTX["priors"] = json.load(open(SR.PRIORSF)) if os.path.exists(SR.PRIORSF) else {}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+", type=int)
    ap.add_argument("--variant", default="display", choices=("display", "detect"))
    ap.add_argument("--knorm", default="known", choices=("master", "crop", "known"))
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--detect-too", action="store_true",
                    help="also write the UNFILLED detect-graded CMYK for the screening analysis")
    ap.add_argument("--inpaint", action="store_true",
                    help="mirror-fill the edges and diffuse the holes in the deliverable")
    ap.add_argument("--page-rgb", action="store_true",
                    help="also write the RGB page the MRC render consumes (ALL.sh's contract: "
                         "graded CMYK, NOT GCR'd, through SWOP->AdobeRGB)")
    ap.add_argument("--keep-rgb", action="store_true",
                    help="also write the 1.67GB pre-separation RGB (verify_fullres reads it)")
    ap.add_argument("--skip-full", action="store_true",
                    help="600 dpi views only (the 2400 dpi apply is ~2.5 min/page)")
    A = ap.parse_args()
    _init()
    need = [p for p in A.pages
            if str(p) not in json.load(open(EG.OUTJ))["pages"]] if os.path.exists(EG.OUTJ) else A.pages
    if need and not A.skip_full:
        print("emitting geometry for %s ..." % need)
        EG._init()
        recs = [(p, json.load(open(WINS))["windows"][str(p)]) for p in need]
        res = [EG._one(r) for r in recs]
        cur = json.load(open(EG.OUTJ)) if os.path.exists(EG.OUTJ) else \
            {"dpi_out": EG.DPI_OUT, "a4_out": [EG.A4_W_OUT, EG.A4_H_OUT], "pages": {}}
        for r in res:
            cur["pages"][str(r["page"])] = r
        json.dump(cur, open(EG.OUTJ, "w"), indent=1)
    # 3 workers, not 4: the 2400dpi apply holds the sampled RGB (1.67GB), the unknown mask and
    # four CMYK planes at once, ~4.5GB per page. Four would be 18GB resident and this machine has
    # already been taken down once by over-parallelising image work.
    args = [(p, A.variant, A.knorm, A.skip_full, A.keep_rgb, A.inpaint, A.detect_too, A.page_rgb)
            for p in A.pages]
    if A.jobs > 1 and len(args) > 1:
        with Pool(A.jobs, initializer=_init) as pool:
            for r in pool.imap_unordered(_one, args):
                print(json.dumps(r), flush=True)
    else:
        for a in args:
            print(json.dumps(_one(a)), flush=True)
