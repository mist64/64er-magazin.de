#!/usr/bin/env python3
"""Exact per-hole SHAPE segmentation for the binder-clip holes.

Builds on top of ``clip_holes.py`` which already detects the 6 clip-hole
POSITIONS per page very well. Here we turn each DETECTED hole position into an
EXACT pixel shape: the dark teardrop / comma / torn-paper region, plus a small
dilation ("the black AND a little more") so the mask fully covers the punch and
its ragged, anti-aliased, torn rim.

Why local-contrast (not a global white threshold)
-------------------------------------------------
Holes sit on WHITE paper OR on coloured stock (light-blue / tan coupons). A
global "dark pixel" threshold tuned for white paper misses holes on darker
stock and over-grabs on it. Instead we segment each hole in a LOCAL window as
"darker than the local surround": we estimate the surrounding paper level with
a large box-mean and keep pixels a good fraction below it. That is invariant to
the paper colour and to gentle shading.

Per hole
--------
  1. Crop a local window around the detected (x, y).
  2. resp = localmean(window) - window   (darkness relative to surround; works
     on any paper colour, same idea as clip_holes._strong_teardrops).
  3. Threshold at a FRACTION of the local hole depth (so the medium-dark torn
     rim and the teardrop TAIL are included, not just the black core), with an
     absolute floor so flat paper never triggers.
  4. Keep the connected component that CONTAINS the detected centre (or, if the
     centre landed just off the punch, the nearest component within a radius),
     restricted to a plausible hole size so an adjacent rule/graphic is not
     swept in. If the component is implausibly large the threshold is raised
     until it is (peels a connected rule/tint off the punch).
  5. DILATE by a small resolution-relative amount -> the "a little more".

The union of the (found) holes' shapes is the page hole mask. found=False holes
(occluded / buried in ink) have no reliable shape and are SKIPPED (left for the
later alpha step); they are reported in ``skipped``.

Spatial constants are at the 600-dpi reference resolution (REF_W x REF_H) and
scaled by the actual page size, so the same code runs at the 2400-dpi master.

Reusable API:
  segment_hole_shapes(gray, res) -> {mask, holes:[{...}|None x6], skipped:[i...]}
      gray : 2-D luminance array of the full page.
      res  : the dict returned by clip_holes.detect_clip_holes(...).

CLI:
  hole_masks.py PAGE.png [--parity even|odd] [--template T] [--test-overlay OUT]
  hole_masks.py --batch DIR --out OUTDIR [--test-overlay] [--template T]
"""
import sys, os, json, glob, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import (uniform_filter, label, binary_dilation, binary_erosion,
                           generate_binary_structure)

import clip_holes as ch
from clip_holes import Template, detect_clip_holes, parity_of, REF_W, REF_H

# ---------------------------------------------------------------------------
# CONSTANTS  (reference resolution: 600-dpi thumb, REF_W x REF_H)
# Everything spatial is scaled by s=(sx+sy)/2 (holes are ~isotropic), areas by
# sx*sy. Tuned by eye on white-paper, coloured-coupon, torn and faint holes.
# ---------------------------------------------------------------------------

# --- local window around a detected hole ------------------------------------
WIN_HALF   = 95    # half-size of the crop around the hole centre (px). Must hold
                   # the whole teardrop (bbox <= WH_MAX=85) PLUS enough paper
                   # surround for a stable local-mean background estimate.

# --- local-contrast background (same idea as clip_holes) --------------------
BG_WIN     = 81    # box size for the local-mean paper background (px). Large vs
                   # the hole so the hole barely pulls the surround down.

# --- shape threshold (fraction of the local hole DEPTH) ---------------------
# resp = localmean - value  (0 on paper, large & positive on the hole).
# We keep pixels whose resp exceeds a FRACTION of this hole's own depth, so the
# threshold auto-adapts to strong vs faint holes. A LOWER fraction includes more
# of the medium-dark torn rim + teardrop tail (good: dilation then finishes it);
# too low starts eating paper texture -> the absolute floor + component/size
# gates stop that.
DEPTH_PCT  = 99.5  # percentile of resp (within the window) taken as "hole depth".
                   # Must be HIGH: the punch is a small fraction of the window, so
                   # a lower percentile lands in near-paper noise and underestimates
                   # depth (drops strong small holes). 99.5 = the dark core.
THR_FRAC   = 0.34  # keep resp > THR_FRAC * depth ...
THR_ABS    = 22    # ... and always resp > THR_ABS levels (flat paper never fires)

# --- component selection / size sanity --------------------------------------
CENTRE_R   = 34    # if the detected centre pixel is not itself dark, accept the
                   # nearest dark component whose centroid is within this radius.
AREA_MIN   =   20  # px^2 @600dpi: a real punch is at least this big
AREA_MAX   = 2600  # px^2 @600dpi: bigger than the biggest torn hole -> we grabbed
                   # a rule/tint; raise the threshold and re-segment to peel it off
SHRINK_STEP = 1.25 # multiply the threshold by this each time area > AREA_MAX
SHRINK_MAX  = 8    # give up after this many shrink passes (keep best-effort blob)

# --- radial extent cap (peels off ATTACHED long structures) -----------------
# A punch - even a big torn one - is compact: it fits inside this radius of the
# detected centre. Horizontal form RULES, diagonal scratches and the coupon's
# vertical border can be exactly as dark as the hole and TOUCH it, so the
# connected component leaks along them. We clip the component to this disk and
# re-take the piece containing the centre, which lops the leaking line off while
# keeping the whole teardrop + tail. Bounds the damage on genuinely occluded
# holes (where hole and rule overlap) to a small rounded cap (flagged imperfect).
MAX_RAD    = 72    # px @600dpi: max radius of a real punch from its centre

# --- thin-structure removal (peels off lines that pass THROUGH the hole) -----
# A form rule / scratch / the coupon's vertical dashed border can run straight
# through the hole centre, so the radial cap alone still leaves a thin bar. Such
# leaks are THIN (a few px); the punch and even its teardrop TAIL are fatter. A
# morphological opening removes structures thinner than ~2*OPEN_PX while keeping
# the blob+tail, then we re-take the central piece. If opening would erase the
# hole (centre sat on a thin part), we keep the un-opened shape instead.
OPEN_PX    = 4     # px @600dpi: opening radius (removes <~8px-thick attachments)
OPEN_KEEP  = 0.35  # revert to un-opened shape if opening leaves < this fraction

# --- final rule-leak reject (a thick horizontal form rule THROUGH the hole) --
# When a bold form rule runs straight through the punch it is too thick for the
# opening to remove, so the shape comes out WIDE (across the inboard/x axis) and
# THIN (short in y). A real punch - even torn - is never that flat. Such holes
# are genuinely occluded: emit NO shape (leave them to the later alpha step).
RULE_W     = 70    # px @600dpi: x-extent above which a flat shape is a rule leak
RULE_H     = 30    # px @600dpi: ... AND y-extent below this (thin) -> reject

# --- dilation: "the black AND a little more" --------------------------------
DILATE_PX  = 5     # grow the segmented shape by ~this many px @600dpi to cover
                   # the ragged torn rim + anti-aliased edge (the "a little more")


# ---------------------------------------------------------------------------
def _segment_one(gray, W, H, x, y, s, sxsy):
    """Segment one hole shape around (x, y). Returns (mask_full_HxW_bool, info)
    or (None, None) if no plausible dark shape is found there.

    mask is returned as a boolean array the size of the whole page (sparse: only
    the window region is ever True) so callers can just OR them together.
    """
    half = int(round(WIN_HALF * s))
    x0 = max(0, x - half); x1 = min(W, x + half + 1)
    y0 = max(0, y - half); y1 = min(H, y + half + 1)
    win = gray[y0:y1, x0:x1]
    if win.size == 0:
        return None, None
    cx, cy = x - x0, y - y0          # hole centre in window coords

    bgwin = max(11, int(round(BG_WIN * s)) | 1)
    bg = uniform_filter(win, size=bgwin, mode="nearest")
    resp = bg - win                  # darkness relative to local surround

    depth = float(np.percentile(resp, DEPTH_PCT))
    if depth < THR_ABS:
        return None, None            # nothing meaningfully dark here

    amin = AREA_MIN * sxsy
    amax = AREA_MAX * sxsy
    cr = CENTRE_R * s
    struct = generate_binary_structure(2, 2)   # 8-connectivity

    thr = max(THR_ABS, THR_FRAC * depth)
    comp = None
    for _ in range(SHRINK_MAX + 1):
        m = resp > thr
        if not m.any():
            break
        lab, n = label(m, structure=struct)
        # pick the component containing the centre, else nearest centroid within cr
        cid = lab[cy, cx] if (0 <= cy < lab.shape[0] and 0 <= cx < lab.shape[1]) else 0
        if cid == 0:
            best = None
            for i in range(1, n + 1):
                ys, xs = np.where(lab == i)
                d = np.hypot(xs.mean() - cx, ys.mean() - cy)
                if d <= cr and (best is None or d < best[0]):
                    best = (d, i)
            if best is None:
                break
            cid = best[1]
        cmask = lab == cid
        # radial cap: clip to a disk around the centre + keep the central piece,
        # lopping off any long rule/scratch/border the component leaked along.
        yy, xx = np.ogrid[:cmask.shape[0], :cmask.shape[1]]
        disk = (xx - cx) ** 2 + (yy - cy) ** 2 <= (MAX_RAD * s) ** 2
        cmask &= disk
        lab2, n2 = label(cmask, structure=struct)
        if 0 <= cy < lab2.shape[0] and 0 <= cx < lab2.shape[1] and lab2[cy, cx] > 0:
            cmask = lab2 == lab2[cy, cx]
        area = int(cmask.sum())
        if area < amin:
            break
        if area <= amax:
            comp = cmask
            break
        thr *= SHRINK_STEP          # too big: peel off connected rule/tint, retry
    if comp is None:
        return None, None

    # peel thin attachments (rule/scratch/coupon-border through the hole) via an
    # opening, keeping the fat blob+tail; revert if it would erase the hole.
    or_ = max(1, int(round(OPEN_PX * s)))
    opened = binary_erosion(comp, struct, iterations=or_)
    opened = binary_dilation(opened, struct, iterations=or_)
    if opened[cy, cx]:
        lab3, _ = label(opened, structure=struct)
        oc = lab3 == lab3[cy, cx]
        if oc.sum() >= max(amin, OPEN_KEEP * comp.sum()):
            comp = oc

    # reject a thick horizontal-rule leak (wide + thin -> genuinely occluded)
    ys0, xs0 = np.where(comp)
    if (xs0.max() - xs0.min()) > RULE_W * s and (ys0.max() - ys0.min()) < RULE_H * s:
        return None, None

    # dilate: "the black AND a little more" (cover ragged torn rim + AA edge)
    rad = max(1, int(round(DILATE_PX * s)))
    comp = binary_dilation(comp, structure=struct, iterations=rad)

    ys, xs = np.where(comp)
    bbox = (int(xs.min() + x0), int(ys.min() + y0),
            int(xs.max() + x0), int(ys.max() + y0))
    full = np.zeros((H, W), dtype=bool)
    full[y0:y1, x0:x1] = comp
    info = {"cx": x, "cy": y, "area": int(comp.sum()), "bbox": bbox,
            "depth": round(depth, 1), "thr": round(float(thr), 1)}
    return full, info


def segment_hole_shapes(gray, res):
    """Exact per-hole shapes for a page.

    gray : 2-D luminance array of the full page.
    res  : dict from clip_holes.detect_clip_holes (holes / column_x / ...).
    Returns dict:
      mask    : HxW bool, union of the 6 (found) hole shapes (dilated).
      holes   : list of 6, each {cx,cy,area,bbox,depth,thr} or None (skipped).
      skipped : list of hole indices with no reliable shape (found=False, or
                segmentation found nothing) -> left for the later alpha step.
    """
    W, H = res["W"], res["H"]
    sx, sy = W / REF_W, H / REF_H
    s = (sx + sy) / 2.0
    sxsy = sx * sy
    mask = np.zeros((H, W), dtype=bool)
    holes = []
    skipped = []
    for i, (x, y, found, c) in enumerate(res["holes"]):
        if not found or x is None:
            holes.append(None); skipped.append(i); continue
        m, info = _segment_one(gray, W, H, int(x), int(y), s, sxsy)
        if m is None:
            holes.append(None); skipped.append(i); continue
        mask |= m
        info["recovered"] = bool(res.get("recovered", [False] * 6)[i])
        holes.append(info)
    return {"mask": mask, "holes": holes, "skipped": skipped}


def segment_path(path, parity=None, tmpl=None):
    im = Image.open(path).convert("L")
    W, H = im.size
    g = np.asarray(im, float)
    res = detect_clip_holes(g, W, H, parity or parity_of(path), tmpl)
    seg = segment_hole_shapes(g, res)
    return res, seg


# ---------------------------------------------------------------------------
# TEST overlay (visual verification only): fill the EXACT shapes with a 50%
# SOLID colour (magenta). The later real step turns this mask into ALPHA; the
# solid fill is purely so a human / vision pass can confirm the shapes hug the
# real holes. Constant-circle (green outline, from clip_holes) drawn for compare.
# ---------------------------------------------------------------------------
FILL_RGB   = (255, 0, 255)   # solid magenta over the exact segmented shape
FILL_ALPHA = 128             # 50%
CIRCLE_RGB = (0, 220, 0)     # green: the OLD constant-radius circle, for compare
SKIP_RGB   = (255, 40, 40)   # red: holes with no shape (skipped -> future alpha)

def make_test_overlay(path, res, seg, out_path, crop_margin=True):
    base = Image.open(path).convert("RGB")
    W, H = base.size
    sx = W / REF_W; s = (sx + H / REF_H) / 2.0

    # exact-shape fill layer (50% solid magenta)
    fill = np.zeros((H, W, 4), dtype=np.uint8)
    m = seg["mask"]
    fill[m] = (*FILL_RGB, FILL_ALPHA)
    ov = Image.fromarray(fill, "RGBA")

    # comparison strokes: old constant circle + skip markers
    d = ImageDraw.Draw(ov)
    r = int(38 * sx)                       # same radius clip_holes.make_overlay uses
    for i, (x, y, found, c) in enumerate(res["holes"]):
        if x is None:
            x = res["column_x"]
        if found and seg["holes"][i] is not None:
            d.ellipse([x - r, y - r, x + r, y + r], outline=(*CIRCLE_RGB, 255),
                      width=max(2, int(3 * sx)))
        else:
            d.ellipse([x - r, y - r, x + r, y + r], outline=(*SKIP_RGB, 255),
                      width=max(2, int(3 * sx)))
            d.line([(x - r, y - r), (x + r, y + r)], fill=(*SKIP_RGB, 255), width=2)

    comp = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    if crop_margin and res["column_x"] is not None:
        cx = res["column_x"]; pad = int(300 * sx)
        comp = comp.crop((max(0, cx - pad), 0, min(W, cx + pad), H))
    comp.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?", help="NNN.png")
    ap.add_argument("--parity", choices=["even", "odd"])
    ap.add_argument("--template")
    ap.add_argument("--test-overlay", nargs="?", const="AUTO",
                    help="write the 50%%-solid-colour shape test render")
    ap.add_argument("--batch")
    ap.add_argument("--out", default="/Users/mist/DNB/8609/tmp")
    args = ap.parse_args()
    tmpl = Template.from_json(json.load(open(args.template))) if args.template else Template()

    def outp(page):
        n = os.path.splitext(os.path.basename(page))[0]
        return os.path.join(args.out, f"holeshape_{n}.png")

    if args.batch:
        paths = sorted(glob.glob(os.path.join(args.batch, "[0-9]*.png")))
        os.makedirs(args.out, exist_ok=True)
        for p in paths:
            res, seg = segment_path(p, tmpl=tmpl)
            n = sum(1 for h in seg["holes"] if h is not None)
            print(f"{os.path.basename(p)} shapes={n}/6 skipped={seg['skipped']}")
            if args.test_overlay is not None:
                make_test_overlay(p, res, seg, outp(p))
        return

    if not args.page:
        ap.error("give a PAGE.png or --batch DIR")
    res, seg = segment_path(args.page, args.parity, tmpl)
    n = sum(1 for h in seg["holes"] if h is not None)
    print(f"{args.page} shapes={n}/6 skipped={seg['skipped']}")
    for i, h in enumerate(seg["holes"]):
        print(f"  hole{i}: " + ("SKIP" if h is None else
              f"area={h['area']} bbox={h['bbox']} depth={h['depth']} thr={h['thr']}"))
    if args.test_overlay is not None:
        op = outp(args.page) if args.test_overlay == "AUTO" else args.test_overlay
        make_test_overlay(args.page, res, seg, op)
        print("test overlay ->", op)


if __name__ == "__main__":
    main()
