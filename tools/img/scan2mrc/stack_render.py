#!/usr/bin/env python3
"""FULL FRONT-END STACK -> deskewed RGBA page, for visual review.

Runs every detection stage that exists and bakes the result into one RGBA image per page:

  02  bed_matte    -> alpha 0 on the scanner bed / yellow backing at all four edges
  02b spine        -> alpha 0 beyond the background-colour boundary (neighbour page),
                      on pages where that boundary is detectable
  02b hole_masks   -> alpha 0 on the exact binder-clip hole shapes
  01  deskew       -> the whole RGBA is rotated by the page's measured angle, expanding
                      the canvas; pixels ADDED by the rotation are alpha 0 too

ORDER MATTERS. The mattes are detected in the RAW scan frame (that is the frame their
metadata was computed in), composited there, and only THEN rotated -- so a slightly tilted
page edge ends up straight, which is what the later A4 crop expects.

Alpha is UNKNOWN, not white: nothing is fabricated here. A later fill/inpaint step decides
what (if anything) goes into those pixels.

Usage:
  stack_render.py [pages...] [--jobs N]      default: all 176, N = cores-2
  stack_render.py --measure                  alpha geometry only -- NO full-size writes
  stack_render.py --montage                  also write a downscaled contact sheet
Output: OUT_DIR/NNN.png  (RGBA, 600 dpi, deskewed), tmp/extents.json

The per-page extents are computed on every run, so there is no "measurement mode" that skips
the image: the full 600-dpi RGBA is always written (it is what you actually inspect, and the
detectors have to run regardless). --measure only ADDS a 1-bit alpha per page, which is handy
for scripted geometry work but is not a substitute for looking at the page.
"""
import os, sys, json, re, argparse

# Pin the BLAS/OpenMP pools to ONE thread each, BEFORE numpy is imported.
# Each worker computes luma as a 37MP matmul, which BLAS parallelises internally. With 4
# worker PROCESSES that becomes 4 x N threads on 16 cores: measured 30 min of CPU in 10 min
# of wall time per worker, i.e. 3x oversubscription, and throughput collapsed from ~15s to
# ~60min per page. One thread per worker; the parallelism is across pages.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "02-matte"))
sys.path.insert(0, os.path.join(HERE, "02b-opposite-page"))
from bed_matte import bed_matte
import clip_holes as CH
import hole_masks as HM

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
# --------------------------------------------------------------------------- #
THUMB   = "/Users/mist/DNB/8609/thumbs_600"
SKEW    = "/Users/mist/DNB/8609/tmp/skew_all.txt"
SPINE   = "/Users/mist/DNB/8609/tmp/spine_all.json"
CLIPJS  = "/Users/mist/DNB/8609/tmp/clip_holes.json"
OUT_DIR = "/Users/mist/DNB/8609/tmp/stack600"
ALPHA_DIR = "/Users/mist/DNB/8609/tmp/stack_alpha"

DPI        = 600
SPINE_OVER = 6      # cut this many px PAST the spine line toward the page, so the whole
                    #   neighbour goes; it only eats our own inner margin, which the A4
                    #   crop discards anyway.
SPINE_EXTRA = 12    # ADDITIONAL cut where spine.py reports extra_cut, i.e. where OUR
                    #   side of the boundary is cream, or where both sides are coloured.
                    #   A printed edge is not sharp: cutting at the 50% crossing leaves
                    #   ~8 px of the neighbour's ramp (measured on p014 -- L196 at -8 px,
                    #   189 at -4, 165 at 0), which shows as a fringe against cream but is
                    #   invisible against a coloured background. Where OUR side is the
                    #   coloured one we deliberately do NOT cut further: the residue is
                    #   cream-on-cream and unnoticeable, and more cutting would eat real
                    #   content (p047/p170/p045 are full-bleed ads running to the fold).

# --- fallback for pages with no detectable background difference ------------ #
# ~130 of 176 pages are cream-on-cream: the neighbour is there but is the same colour as
# our margin, so no colour boundary exists to find. There we cut on the CLIP-HOLE LINE.
# That is justified by measurement, not convenience: over the 46 pages where the boundary
# IS detectable, (boundary - hole column) has a median of -2.7 px = -0.12 mm, i.e. the hole
# line is an UNBIASED estimator of the boundary. No systematic correction is needed.
# Its scatter is +/-44 px (1.9 mm) though, and on 48% of pages the true boundary lies
# INBOARD of the holes -- so cutting exactly on the line would leave a neighbour sliver
# about half the time. Hence the overcut below.
# RULE 1 (hard): every neighbour pixel must go. RULE 2: cut as few of OUR pixels as possible.
# Where no colour boundary exists we cut ON THE CLIP-HOLE LINE, as instructed -- not inboard
# of it. An earlier version added 5mm here, reasoning that the fold could be up to 5mm inboard
# of the holes and rule 1 wanted a guarantee. That was wrong twice over: it put the cut visibly
# off the holes on all 135 fallback pages, and it confused two different uses of the 5mm. The
# +/-5mm is how far from the holes the boundary may be SEARCHED FOR (spine.py's window); it is
# not a margin to bolt on once we have given up finding it and are using the holes themselves.
HOLE_OVERCUT = 0    # cut on the hole line
HOLE_MIN     = 4    # need at least this many located holes to fit the fallback line
A4_W = int(round(210.0 / 25.4 * DPI))     # 4961 px @600dpi
A4_H = int(round(297.0 / 25.4 * DPI))     # 7016 px
# --- review mode: TINT what would be cut, never remove it -------------------- #
# While the detectors are still converging, an alpha render destroys the evidence: if a cut
# ate real content the content is gone and the page merely looks smaller, so an over-cut and
# a correct cut are indistinguishable. Tinting leaves the pixels in place -- content visible
# UNDER the wash is a cut that went too far. This is the ACCEPTANCE.md --magenta convention,
# generalised to every stage, and the colours match debug_stack.py so they read the same.
# Lossless PNG at full 600 dpi: the defects being hunted are ~3px at 600dpi, and a lossy
# codec would invent and erase features at exactly the hard edges we are judging.
REVIEW_DIR = "/Users/mist/DNB/8609/tmp/review"
COL_HAIR   = (255, 0, 255)     # magenta hairline on every cut boundary
HAIRLINE_600 = int(os.environ.get("SR_HAIR", 3))
                    # line width in px @600dpi (~0.13mm). Not 1: a single 600-dpi pixel is
                    # dropped by the resampler as soon as the page is viewed fit-to-screen, so a
                    # true 1px hairline is invisible exactly when the whole page is being judged.
BLEND      = float(os.environ.get("SR_BLEND", 0.30))    # kept for the montage/alpha views
COL_BED    = (255,   0, 255)   # 02  bed / yellow backing
COL_SPINE  = (  0, 210, 255)   # 02b neighbour, MEASURED colour boundary
COL_HOLECUT= ( 40,  90, 255)   # 02b neighbour, hole-line FALLBACK (inferred, not measured)
COL_HOLES  = (255, 230,   0)   # 02b clip holes
COL_WEDGE  = (255, 140,   0)   # 01  pixels added by the deskew rotation
MONT_W     = 150    # per-page width in the contact sheet
CHECKER    = 24     # checkerboard square size (px) used to VISUALISE alpha in the montage


def load_skew():
    ang = {}
    for ln in open(SKEW):
        m = re.search(r"/(\d+)\.png:\s*([+-]?\d+\.\d+)\s*deg", ln)
        if m:
            ang[int(m.group(1))] = float(m.group(2))
    return ang


def _cut_outboard(shape, inb, parity):
    """Alpha-0 everything OUTBOARD of the per-row inboard distance `inb`."""
    H, W = shape
    xx = np.arange(W)[None, :]
    if parity == "even":                       # neighbour on the RIGHT
        return xx >= (W - inb[:, None])
    return xx <= inb[:, None]                  # neighbour on the LEFT


def hole_line_inb(clip_entry, H, W, parity):
    """Per-row inboard distance of the clip-hole line, or None."""
    hs = [h for h in (clip_entry or {}).get("holes", []) if h[2]]
    if len(hs) < HOLE_MIN:
        return None
    hx = np.array([h[0] for h in hs], float); hy = np.array([h[1] for h in hs], float)
    coef, *_ = np.linalg.lstsq(np.stack([np.ones_like(hy), hy], 1), hx, rcond=None)
    ys = np.arange(H, dtype=np.float32)
    xline = coef[0] + coef[1] * ys
    return (W - xline) if parity == "even" else xline


def spine_mask(shape, rec, parity, clip_entry):
    """Cut the neighbour page off, using the BEST available signal.

    The background-colour difference is the real boundary: where it exists it IS the fold,
    measured directly. The clip-hole line is only a decent proxy -- the clips did not go in
    at exactly the right spot, and they may sit either side of the fold or on it. So:

        colour boundary found  ->  cut there (+ the fringe margin)
        otherwise              ->  cut on the hole line + 5mm

    An earlier version took the INBOARD-MOST of the two, which is backwards: at hole+5mm the
    proxy almost always cut deeper, so it overrode the exact signal on 32 of the 41 pages
    where a boundary had actually been measured -- only 9/176 cuts were really colour-driven,
    and up to 5mm of page was spent insuring against an uncertainty already resolved. That
    union was introduced to contain p023, where the OLD detector fired 2.75mm outboard of the
    fold; the current one lands within 0.08mm there, so the reason no longer exists. Fix the
    detector, do not override every correct detection with a coarser estimator.

    Returns (mask, source).
    """
    H, W = shape
    ys = np.arange(H, dtype=np.float32)

    if rec and rec.get("found"):
        inb = rec["inboard_top"] + (rec["inboard_bot"] - rec["inboard_top"]) * (ys / max(1, H - 1))
        # NB the sign: inb is the distance INBOARD of the binding edge, so cutting further
        # toward our own page means a LARGER inb.
        inb = inb + SPINE_OVER + (SPINE_EXTRA if rec.get("extra_cut") else 0)
        return _cut_outboard((H, W), inb, parity), ("colour+" if rec.get("extra_cut") else "colour")

    hole_inb = hole_line_inb(clip_entry, H, W, parity)
    if hole_inb is None:
        return np.zeros((H, W), bool), "none"
    return _cut_outboard((H, W), hole_inb + HOLE_OVERCUT, parity), "holes"


def _masks(page, spine, clip, im):
    """Per-STAGE masks in the raw scan frame, kept separate so review can colour them by
    source and a wrong cut can be attributed to the detector that made it."""
    p = "%03d" % page
    W, H = im.size
    parity = "even" if page % 2 == 0 else "odd"

    bed_rgba, _, meta = bed_matte(im, DPI, return_meta=True, page_no=page)
    m_bed = (np.asarray(bed_rgba)[:, :, 3] == 0)

    m_spine, src = spine_mask((H, W), spine.get(p), parity, clip.get(p))

    m_holes = np.zeros((H, W), bool)
    res = clip.get(p)
    if res:
        try:
            m_holes = HM.segment_hole_shapes(np.asarray(im.convert("L"), np.float32),
                                             res)["mask"].astype(bool)
        except Exception as e:
            print("  p%s hole shapes failed: %s" % (p, e))
    return m_bed, m_spine, m_holes, src, meta


def render(page, skew, spine, clip, tmpl):
    """ALPHA render: what would actually be cut, as transparency."""
    im = Image.open(os.path.join(THUMB, "%03d.png" % page)).convert("RGB")
    W, H = im.size
    m_bed, m_spine, m_holes, src, _ = _masks(page, spine, clip, im)
    unknown = m_bed | m_spine | m_holes

    ang = skew.get(page, 0.0)
    known = Image.fromarray(np.where(unknown, 0, 255).astype(np.uint8), "L")
    rgb = im
    if abs(ang) > 1e-3:
        # RGB bicubic, ALPHA NEAREST, rotated separately and recombined. Rotating the RGBA
        # together interpolates the alpha into a soft fringe -- alpha here means UNKNOWN, and a
        # half-transparent pixel is a claim nothing measured -- and it also blends the RGB of the
        # transparent fill (black) into the page border underneath it.
        rgb = im.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
        known = known.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
    out = Image.fromarray(np.dstack([np.asarray(rgb), np.asarray(known)]), "RGBA")
    return out, ang, float((np.asarray(known) == 0).mean()), src


def render_review(page, skew, spine, clip):
    """REVIEW render: OUTLINE what WOULD be cut, remove nothing. Full page. See REVIEW_DIR.

    Magenta hairlines, not a tint wash. A wash states the verdict but hides the evidence under
    itself -- the pixels that decide whether a cut is right are the few on either side of the
    line, and those are exactly the ones a 30% wash recolours. An outline leaves every pixel
    untouched and puts the boundary where it can be compared against the scan directly.
    """
    im = Image.open(os.path.join(THUMB, "%03d.png" % page)).convert("RGB")
    W, H = im.size
    m_bed, m_spine, m_holes, src, meta = _masks(page, spine, clip, im)
    cutmask = m_bed | m_spine | m_holes

    out = im
    valid = Image.new("L", (W, H), 255)
    ang = skew.get(page, 0.0)
    cut_im = Image.fromarray(cutmask.astype(np.uint8) * 255)
    if abs(ang) > 1e-3:
        out = out.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
        valid = valid.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
        # NEAREST for the mask, and drawn AFTER the rotation: rotating an already-drawn line
        # bicubically smears the very hairline the render exists to show
        cut_im = cut_im.rotate(ang, resample=Image.NEAREST, expand=True, fillcolor=0)
    a = np.asarray(out).copy()
    invalid = np.asarray(valid) == 0
    cutrot = np.asarray(cut_im) > 127

    hair = max(1, int(round(HAIRLINE_600 * DPI / 600)))
    for mask in (cutrot, invalid):                 # the cut, and the rotation-invented wedge
        if not mask.any():
            continue
        inner = ndi.binary_erosion(mask, np.ones((2 * hair + 1, 2 * hair + 1), bool))
        a[mask & ~inner] = COL_HAIR
    out = Image.fromarray(a)

    dep = {e: round(np.median(meta[e].get("median_depth", 0)))
           for e in ("top", "bottom", "left", "right") if isinstance(meta.get(e), dict)}
    rec = spine.get("%03d" % page, {})
    dr = ImageDraw.Draw(out)
    txt = ("p%03d  skew %+.2f  bed t%s b%s l%s r%s  spine=%s  step=%s run=%smm"
           % (page, ang, dep.get("top"), dep.get("bottom"), dep.get("left"), dep.get("right"),
              src, rec.get("step"), rec.get("run_mm")))
    dr.rectangle([0, 0, 12 * len(txt), 40], fill=(0, 0, 0))
    dr.text((10, 14), txt, fill=(255, 255, 255))
    frac = float((m_bed | m_spine | m_holes).mean())
    return out, ang, frac, src


def montage(pages, out_path):
    """Contact sheet with alpha shown as a checkerboard, so cuts are visible at a glance."""
    tiles = []
    for n in pages:
        f = os.path.join(OUT_DIR, "%03d.png" % n)
        if not os.path.exists(f):
            continue
        im = Image.open(f)
        w = MONT_W; h = int(im.size[1] * w / im.size[0])
        im = im.resize((w, h), Image.LANCZOS)
        bg = Image.new("RGB", im.size, (255, 255, 255))
        a = np.indices((im.size[1], im.size[0])).sum(0) // CHECKER % 2
        chk = np.where(a[..., None], np.uint8(210), np.uint8(255)).repeat(3, 2)
        bg = Image.fromarray(chk.astype(np.uint8))
        bg.paste(im, (0, 0), im)
        tiles.append(bg)
    if not tiles:
        return
    cols = 16
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 4), rows * (th + 4)), (30, 30, 30))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
    sheet.save(out_path)
    print("montage ->", out_path, sheet.size)


_CTX = {}


def _init():
    """Load the shared per-issue metadata once per worker process."""
    _CTX["skew"] = load_skew()
    _CTX["spine"] = json.load(open(SPINE)) if os.path.exists(SPINE) else {}
    _CTX["clip"] = json.load(open(CLIPJS))


def _one(args):
    n, measure, review = args
    try:
        if review:
            out, ang, frac, src = render_review(n, _CTX["skew"],
                                                _CTX["spine"], _CTX["clip"])
            out.save(os.path.join(REVIEW_DIR, "%03d.png" % n))
            return dict(page=n, ok=True, ang=ang, frac=frac, src=src,
                        size=list(out.size), edges={})
        out, ang, frac, src = render(n, _CTX["skew"], _CTX["spine"],
                                     _CTX["clip"], None)
        alpha = np.asarray(out)[:, :, 3]
        depths = edge_depths(alpha)
        # ALWAYS write the full 600-dpi RGBA: the extents are computed either way, and the
        # only saving from skipping it was disk, which is not scarce -- while the cost was
        # having nothing to actually look at. --measure adds the 1-bit alpha alongside.
        out.save(os.path.join(OUT_DIR, "%03d.png" % n))
        if measure:
            Image.fromarray((alpha > 0).astype(np.uint8) * 255).convert("1").save(
                os.path.join(ALPHA_DIR, "%03d.png" % n), optimize=True)
        return dict(page=n, ok=True, ang=ang, frac=frac, src=src,
                    size=list(out.size), edges=depths)
    except Exception as e:
        return dict(page=n, ok=False, err=str(e))


def edge_depths(alpha, pct=(50, 95, 100)):
    """Leading alpha run from each border (left,right,top,bottom), at several percentiles
    over scanlines.

    NB the MAX is NOT a usable bound on a deskewed page: after rotation the extreme rows
    are almost entirely alpha (only a corner sliver of page is in them), so the max leading
    run is ~the page width and says nothing. Measured on p005: median 369 px, but 4318 px at
    row 20 and 5123 px at row 7042. The window is therefore decided by alpha INSIDE the
    candidate window (see window_alpha), not by these; they are kept only as a description
    of the edges.
    """
    A = (alpha == 0)

    def runs(M):
        full = M.all(1)
        r = np.where(M.any(1), M.argmin(1), 0)
        r = np.where(full, M.shape[1], r)          # an all-alpha row is a FULL incursion
        return [int(np.percentile(r, q)) for q in pct]

    return dict(left=runs(A), right=runs(A[:, ::-1]),
                top=runs(A.T), bottom=runs(A.T[:, ::-1]), pct=list(pct))


def window_alpha(alpha, ax, ay, B, A_, S, parity):
    """Alpha pixels inside the A4 window placed at the logo anchor.

    This is the quantity the crop is chosen to minimise: the user accepts alpha inside the
    final crop (it can be inpainted), so the question is not "does any alpha intrude" but
    "how little alpha can a LOGO-ANCHORED window contain". Offsets are in 600-dpi px:
      B  above the logo baseline, A_ below it   (B + A_ = A4_H)
      S  horizontal offset of the binding-side window edge from the logo anchor
    Returns (n_alpha, area, x0, y0).
    """
    H, W = alpha.shape
    y0 = int(round(ay - B)); y1 = y0 + A4_H
    if parity == "even":                      # logo left, binding right
        x1 = int(round(ax + S)); x0 = x1 - A4_W
    else:                                     # logo right, binding left
        x0 = int(round(ax + S)); x1 = x0 + A4_W
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(W, x1), min(H, y1)
    inside = 0
    if xs1 > xs0 and ys1 > ys0:
        inside = int((alpha[ys0:ys1, xs0:xs1] == 0).sum())
    outside = A4_W * A4_H - (xs1 - xs0) * (ys1 - ys0)   # window off the canvas = unknown too
    return inside + max(0, outside), A4_W * A4_H, x0, y0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--montage", action="store_true")
    ap.add_argument("--review", action="store_true",
                    help="tint what would be cut instead of removing it (the testing view)")
    ap.add_argument("--measure", action="store_true",
                    help="alpha + extents only; skip the full-size RGBA writes")
    ap.add_argument("--jobs", type=int, default=6,
                    help="6 by default: each worker holds several full-size float32 copies, "
                         "and 14 thrashed (1204s user vs 8050s system = mostly page faults)")
    a = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(ALPHA_DIR, exist_ok=True)
    os.makedirs(REVIEW_DIR, exist_ok=True)
    pages = a.pages or list(range(1, 177))

    res = []
    if a.jobs > 1 and len(pages) > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(a.jobs, initializer=_init) as pool:
            for r in pool.imap_unordered(_one, [(n, a.measure, a.review) for n in pages]):
                res.append(r)
                if r["ok"]:
                    e = r["edges"]
                    if e:
                        print("p%03d skew %+0.2f tinted %5.2f%% spine=%-11s edge med(l,r,t,b)=%d,%d,%d,%d"
                              % (r["page"], r["ang"], 100 * r["frac"], r["src"],
                                 e["left"][0], e["right"][0], e["top"][0], e["bottom"][0]))
                    else:
                        print("p%03d skew %+0.2f tinted %5.2f%% spine=%s"
                              % (r["page"], r["ang"], 100 * r["frac"], r["src"]))
                else:
                    print("p%03d FAILED: %s" % (r["page"], r["err"]))
                sys.stdout.flush()
    else:
        _init()
        for n in pages:
            r = _one((n, a.measure, a.review)); res.append(r)
            print(r)

    res.sort(key=lambda r: r["page"])
    json.dump(res, open("/Users/mist/DNB/8609/tmp/stack_meta.json", "w"), indent=1)
    ok = [r for r in res if r["ok"]]
    if ok and ok[0]["edges"]:
        print("\nleading alpha run per edge (px @600dpi), median over scanlines:")
        for e in ("left", "right", "top", "bottom"):
            v = np.array([r["edges"][e][0] for r in ok], float)
            print("   %-7s med %5.0f  p95 %5.0f  max %5.0f" % (e, np.median(v), np.percentile(v, 95), v.max()))
    if a.montage and not a.measure:
        montage(pages, "/Users/mist/DNB/8609/tmp/stack600_montage.png")


if __name__ == "__main__":
    main()
