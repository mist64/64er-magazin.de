#!/usr/bin/env python3
"""FULL FRONT-END STACK -> deskewed RGBA page, for visual review.

Runs every detection stage that exists and bakes the result into one RGBA image per page:

  02  bed_matte    -> alpha 0 on the scanner bed / yellow backing at all four edges
  02b shear_spine  -> alpha 0 beyond the background-colour boundary (neighbour page),
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

--measure is the RESEARCH path: it runs the identical detector stack but writes only the
1-bit alpha and the per-page extents, skipping the ~90 MB RGBA PNG per page. Encoding that
photographic RGBA is the dominant cost, so --measure is ~10x cheaper and answers "how does
the window fit / how little alpha can we get" without producing 13 GB we then delete.
"""
import os, sys, json, re, argparse
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "02-matte"))
sys.path.insert(0, os.path.join(HERE, "02b-opposite-page"))
from bed_matte import bed_matte
import shear_spine as S
import clip_holes as CH
import hole_masks as HM

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
# --------------------------------------------------------------------------- #
THUMB   = "/Users/mist/DNB/8609/thumbs_600"
SKEW    = "/Users/mist/DNB/8609/tmp/skew_all.txt"
SPINE   = "/Users/mist/DNB/8609/tmp/shear_v8.json"
CLIPJS  = "/Users/mist/DNB/8609/tmp/clip_holes.json"
PRIORSF = os.path.join(HERE, "02-matte/priors.json")
OUT_DIR = "/Users/mist/DNB/8609/tmp/stack600"
ALPHA_DIR = "/Users/mist/DNB/8609/tmp/stack_alpha"

DPI        = 600
SPINE_OVER = 6      # cut this many px PAST the spine line toward the page, so the whole
                    #   neighbour goes; it only eats our own inner margin, which the A4
                    #   crop discards anyway.
SPINE_EXTRA = 12    # ADDITIONAL cut where shear_spine reports extra_cut, i.e. where OUR
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
# RULE 1 (hard): every neighbour pixel must go. Leaving any is a FAIL.
# RULE 2: subject to that, cut as few of OUR pixels as possible.
# The fold is never more than CLIP_WIN_MM from the hole line (the user's constraint, and
# shear_spine enforces it). So where the hole line is all we have, cutting at hole + 5mm is
# the TIGHTEST cut that PROVES rule 1 -- anything less can leave neighbour standing. The old
# value (44px = 1 sigma of the measured scatter) was a coverage estimate, not a guarantee, and
# under-cut on roughly a third of pages.
HOLE_OVERCUT = int(5.0 / 25.4 * 600)   # = 118 px @600dpi
HOLE_MIN     = 4    # need at least this many located holes to fit the fallback line
A4_W = int(round(210.0 / 25.4 * DPI))     # 4961 px @600dpi
A4_H = int(round(297.0 / 25.4 * DPI))     # 7016 px
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
    """Cut the neighbour page off, at whichever estimator cuts DEEPER.

    Two estimators, neither of which dominates:
      * the measured background-colour boundary, when one exists;
      * the clip-hole line, which the user reports may sit either side of the fold or dead
        on it (our own measurement agrees: median offset -2.7px, 48% either way).

    Where the fold itself is cream-on-cream the colour detector can only see the NEIGHBOUR's
    own content edge, which lies outboard of the fold and leaves a strip behind -- p023 fired
    2.75mm outboard of the hole line and left exactly that much neighbour showing.

    We therefore take the INBOARD-most of the two. The costs are asymmetric: cutting too deep
    only eats our own inner margin, which the logo-anchored A4 window discards anyway (its
    inner edge already sits ~7mm inboard of the holes on every page), whereas cutting too
    shallow leaves visible neighbour. Returns (mask, source).
    """
    H, W = shape
    ys = np.arange(H, dtype=np.float32)
    hole_inb = hole_line_inb(clip_entry, H, W, parity)

    if rec and rec.get("found"):
        inb = rec["inboard_top"] + (rec["inboard_bot"] - rec["inboard_top"]) * (ys / max(1, H - 1))
        inb = inb + SPINE_OVER + (SPINE_EXTRA if rec.get("extra_cut") else 0)
        src = "colour+" if rec.get("extra_cut") else "colour"
        if hole_inb is not None:
            hi = hole_inb + HOLE_OVERCUT
            if np.median(hi) > np.median(inb):
                src = src + "/hole"
            inb = np.maximum(inb, hi)
        return _cut_outboard((H, W), inb, parity), src

    if hole_inb is None:
        return np.zeros((H, W), bool), "none"
    return _cut_outboard((H, W), hole_inb + HOLE_OVERCUT, parity), "holes"


def render(page, priors, skew, spine, clip, tmpl):
    p = "%03d" % page
    path = os.path.join(THUMB, p + ".png")
    im = Image.open(path).convert("RGB")
    W, H = im.size
    parity = "even" if page % 2 == 0 else "odd"

    unknown = np.zeros((H, W), bool)

    # -- 02 bed / yellow backing ------------------------------------------------
    bed_rgba, _, _ = bed_matte(im, DPI, priors=priors, page_no=page, return_meta=True)
    unknown |= (np.asarray(bed_rgba)[:, :, 3] == 0)

    # -- 02b neighbour page beyond the background boundary ----------------------
    sm, src = spine_mask((H, W), spine.get(p), parity, clip.get(p))
    unknown |= sm

    # -- 02b binder-clip holes (exact shapes) -----------------------------------
    res = clip.get(p)
    if res:
        gray = np.asarray(im.convert("L"), np.float32)
        try:
            seg = HM.segment_hole_shapes(gray, res)
            unknown |= seg["mask"].astype(bool)
        except Exception as e:                 # a hole that cannot be segmented is left
            print("  p%s hole shapes failed: %s" % (p, e))

    # -- compose RGBA in the RAW frame -----------------------------------------
    rgba = np.dstack([np.asarray(im), np.where(unknown, 0, 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA")

    # -- 01 deskew: rotate, expanding; rotation-added pixels are unknown too ----
    ang = skew.get(page, 0.0)
    if abs(ang) > 1e-3:
        out = out.rotate(ang, resample=Image.BICUBIC, expand=True,
                         fillcolor=(0, 0, 0, 0))
    return out, ang, float(unknown.mean()), src


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
    _CTX["priors"] = json.load(open(PRIORSF))
    _CTX["skew"] = load_skew()
    _CTX["spine"] = json.load(open(SPINE)) if os.path.exists(SPINE) else {}
    _CTX["clip"] = json.load(open(CLIPJS))


def _one(args):
    n, measure = args
    try:
        out, ang, frac, src = render(n, _CTX["priors"], _CTX["skew"], _CTX["spine"],
                                     _CTX["clip"], None)
        alpha = np.asarray(out)[:, :, 3]
        depths = edge_depths(alpha)
        if measure:
            Image.fromarray((alpha > 0).astype(np.uint8) * 255).convert("1").save(
                os.path.join(ALPHA_DIR, "%03d.png" % n), optimize=True)
        else:
            out.save(os.path.join(OUT_DIR, "%03d.png" % n))
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
    ap.add_argument("--measure", action="store_true",
                    help="alpha + extents only; skip the full-size RGBA writes")
    ap.add_argument("--jobs", type=int, default=6,
                    help="6 by default: each worker holds several full-size float32 copies, "
                         "and 14 thrashed (1204s user vs 8050s system = mostly page faults)")
    a = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(ALPHA_DIR, exist_ok=True)
    pages = a.pages or list(range(1, 177))

    res = []
    if a.jobs > 1 and len(pages) > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(a.jobs, initializer=_init) as pool:
            for r in pool.imap_unordered(_one, [(n, a.measure) for n in pages]):
                res.append(r)
                if r["ok"]:
                    e = r["edges"]
                    print("p%03d skew %+0.2f unknown %5.2f%% spine=%-11s edge med(l,r,t,b)=%d,%d,%d,%d"
                          % (r["page"], r["ang"], 100 * r["frac"], r["src"],
                             e["left"][0], e["right"][0], e["top"][0], e["bottom"][0]))
                else:
                    print("p%03d FAILED: %s" % (r["page"], r["err"]))
                sys.stdout.flush()
    else:
        _init()
        for n in pages:
            r = _one((n, a.measure)); res.append(r)
            print(r)

    res.sort(key=lambda r: r["page"])
    json.dump(res, open("/Users/mist/DNB/8609/tmp/stack_meta.json", "w"), indent=1)
    ok = [r for r in res if r["ok"]]
    if ok:
        print("\nleading alpha run per edge (px @600dpi), median over scanlines:")
        for e in ("left", "right", "top", "bottom"):
            v = np.array([r["edges"][e][0] for r in ok], float)
            print("   %-7s med %5.0f  p95 %5.0f  max %5.0f" % (e, np.median(v), np.percentile(v, 95), v.max()))
    if a.montage and not a.measure:
        montage(pages, "/Users/mist/DNB/8609/tmp/stack600_montage.png")


if __name__ == "__main__":
    main()
