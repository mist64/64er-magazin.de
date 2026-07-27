#!/usr/bin/env python3
"""SPINE -- the background-colour boundary between this page and the neighbour that bled
into the A3 scan. Production detector; supersedes shear_spine.py and bg_spine.py.

THE ALGORITHM (five steps, all of them ordinary)
------------------------------------------------
  1. downscale to WORK_DPI. A 4x box average over a ~150-lpi screen IS the descreen.
  2. per row, take the top N_PEAKS local maxima of the colour difference to the next pixel,
     in a CHROMA-WEIGHTED space (a boundary can change hue at nearly constant brightness,
     and a luma-only or unweighted-RGB difference misses exactly those).
     NOT just the argmax: that assumes the fold is the STRONGEST edge in the window, and it
     often is not. Measured on p020, inside the +/-5mm window the argmax lands at 69,68,69,
     57,32,40 (IQR 5mm) -- at some heights the neighbour's own content is stronger, at
     others ours is, and the fold at ~57 is weaker than both. Offering several candidates
     per row lets the VOTE decide: the fold is the one x that recurs on every row, while
     content edges wander.
  3. restrict that argmax to the clip-hole line +/- CLIP_WIN_MM.
  4. Hough-vote for the line most rows agree on, over slants within STAPLE_ANG_TOL of the
     staple line.
  5. FIRE iff the longest UNBROKEN run of agreeing rows is at least MIN_RUN_MM.

WHY THIS, AFTER THREE MORE ELABORATE ATTEMPTS
---------------------------------------------
The earlier detectors (bg_spine's per-row thresholds, shear_spine's coarse median-step
argmax plus a 50%-crossing refit) were built to make the DETECTION robust. Measured
head-to-head on the same pages, this five-step version agrees with shear_spine to within
0.3 mm -- the line fit was never the hard part. What the elaborate versions were really
compensating for was the absence of steps 3 and 5.

  * STEP 3 does most of the work. Without the window the same code lands 10-12 mm off on
    p176/p128/p014: over a 30 mm band the strongest edge in most rows belongs to OUR page,
    not the neighbour. Plain least squares is worse still -- it averages our content over
    all rows and returns ~17-21 mm on every page, essentially page-independent.
  * STEP 5 is the fire/don't-fire test, and it is the only genuinely hard part. A boundary
    that is not there cannot be found; the question is whether the detector KNOWS that.

WHY THE LONGEST RUN, NOT THE INLIER FRACTION OR THE VARIANCE
------------------------------------------------------------
A justified TEXT COLUMN edge is straight and full-height, so it is just as "uniform" as a
fold -- that is what produced 24/24 false fires on the classified-ads pages in an earlier
generation. But a text column only carries ink at the GLYPH rows: between the lines there
is nothing at that x, so its agreeing rows form a periodic comb broken at every interline
gap. A real background boundary is unbroken. Measured:

    real boundary   p176 465, p172 516, p128 214, p047 389, p073 357, p170 241 rows
    text column     p053   8, p083   9, p067  10, p028   5, p159  64 rows
    cream/nothing   p100   6, p008   5 rows

The inlier FRACTION does not separate these: p020 (real, partial-height) scores 0.13 while
p067 (text column, false) scores 0.15 -- overlapping. The longest run separates them
(24 vs 10) because it is insensitive to how much of the page the neighbour covers.

MIN_RUN_MM is therefore a statement about the page, not a tuned number: "at least this much
CONTINUOUS background difference exists".

Outputs a line in 600-dpi page coordinates for the renderer, plus a JSON record and an
optional overlay. Everything spatial is in mm or derived from dpi.
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
# --------------------------------------------------------------------------- #
THUMB_DIR = "/Users/mist/DNB/8609/thumbs_600"
CLIP_JSON = "/Users/mist/DNB/8609/tmp/clip_holes.json"
OUT_DIR   = "/Users/mist/DNB/8609/tmp"

SRC_DPI   = 600         # the thumbnails
WORK_DPI  = 150         # analysis resolution; the 4x box downscale is also the descreen
MM        = 25.4

CHROMA_W  = 2.2         # weight on (R-G) and (G-B) vs L in the difference, so a hue step at
                        #   constant brightness counts as much as a tone step

CLIP_WIN_MM = 5.0       # HARD (user): the boundary lies within this of the clip-hole line.
                        #   This is what stops the argmax locking onto our own content.
X_LO_MM     = 3.0       # ignore the scan-edge shadow at the very border
BAND_MM     = 30.0      # analysed strip when there is no usable hole line

STAPLE_ANG_TOL = 1.0    # HARD (user): the boundary slant is within this of the staple line
ANG_STEP_DEG   = 0.03   # slant grid
STAPLE_MIN_HOLES = 5    # a staple line fitted from fewer holes is not a reference ...
STAPLE_MAX_RES_MM = 0.42  # ... nor is one whose own holes scatter more than this (=10px@600)

N_PEAKS    = 4          # candidate edges offered per row (see step 2)
PEAK_FRAC  = 0.25       # ... keeping only peaks at least this fraction of the row's best
# Cream vs coloured, for the extra side cut the renderer applies. Measured at the boundary
# over the fired pages: cream paper is L 195-210 with |R-G| <= 18, while every neighbour/ad
# background is either dark (L 49-103) or saturated (|R-G| up to 161) -- the groups do not
# overlap. Cutting at the 50% crossing leaves ~8px of the neighbour's ramp, which shows as a
# fringe against cream but is invisible against a coloured background.
CREAM_L_MIN  = 170.0
CREAM_CHROMA = 25.0
TOL_MM     = 0.5        # a row agrees with the line if its argmax is within this of it
# FIRE needs BOTH, and the magnitude is the primary one:
MIN_STEP   = 15.0       # the colour difference actually crossed by the fitted line (90th
                        #   pct over rows, in the chroma-weighted feature). Over 13 pages
                        #   labelled by eye: FALSE 7.1-11.1, REAL 17.8-103.8 (one disputed
                        #   at 9.6). This is what a cream-on-cream page fails -- its fit can
                        #   be long and straight yet the two sides are the same colour.
MIN_RUN_MM = 5.0        # ... and the longest unbroken run of agreeing rows. This kills the
                        #   TEXT-COLUMN combs (p053 8.6mm was the longest false comb before
                        #   the multi-peak change; cream pages 1.2-3.7mm) without rejecting
                        #   a short but genuine neighbour strip.
                        # NB an earlier revision used run length ALONE at 15mm. Across the
                        # full issue that is WRONG: the run distribution is not bimodal (24
                        # pages sit in 9-20mm), and by run alone p037 (19.8mm, cream on both
                        # sides, FALSE) outranks p160 (10.3mm, pink neighbour, REAL).


def staple_slant(clip_entry, fallback=None):
    """Slant (px x per px y, at SRC_DPI) of the staple line, or `fallback` if not trustworthy."""
    if not clip_entry:
        return fallback
    hs = [h for h in clip_entry.get("holes", []) if h[2]]
    if len(hs) < STAPLE_MIN_HOLES:
        return fallback
    x = np.array([h[0] for h in hs], float); y = np.array([h[1] for h in hs], float)
    coef, *_ = np.linalg.lstsq(np.stack([np.ones_like(y), y], 1), x, rcond=None)
    if np.abs(x - (coef[0] + coef[1] * y)).max() > STAPLE_MAX_RES_MM / MM * SRC_DPI:
        return fallback
    return float(coef[1])


def issue_staple_slant(clip):
    v = [staple_slant(c) for c in clip.values()]
    v = [x for x in v if x is not None]
    return float(np.median(v)) if v else 0.0


def detect(page, clip_entry, issue_slant=0.0, thumb_dir=THUMB_DIR):
    """Return the fitted boundary in 600-dpi page coordinates."""
    im = Image.open(os.path.join(thumb_dir, "%03d.png" % page)).convert("RGB")
    W, H = im.size
    s = WORK_DPI / SRC_DPI
    im = im.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BOX)   # step 1: descreen
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    parity = "even" if page % 2 == 0 else "odd"

    band = int(BAND_MM / MM * WORK_DPI)
    sub = a[:, w - band:][:, ::-1] if parity == "even" else a[:, :band]   # 0 = binding edge

    # step 2: chroma-weighted difference to the next pixel
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    f = np.stack([sub.mean(2), (R - G) * CHROMA_W, (G - B) * CHROMA_W], -1)
    d = np.linalg.norm(np.diff(f, axis=1), axis=2)
    d[:, :int(X_LO_MM / MM * WORK_DPI)] = 0

    # step 3: only look within CLIP_WIN_MM of the clip-hole line
    hole_in = None
    if clip_entry:
        hs = [hh for hh in clip_entry.get("holes", []) if hh[2]]
        if hs:
            hx = float(np.median([hh[0] for hh in hs])) * s
            hole_in = (w - hx) if parity == "even" else hx
    if hole_in is not None:
        c = hole_in - int(X_LO_MM / MM * WORK_DPI) * 0
        half = CLIP_WIN_MM / MM * WORK_DPI
        m = np.zeros(d.shape[1], bool)
        m[max(0, int(c - half)):int(c + half)] = True
        d[:, ~m] = 0

    # top-N local maxima per row -> (rows, N) candidate positions; -1 = unused slot
    interior = np.zeros_like(d, bool)
    interior[:, 1:-1] = (d[:, 1:-1] >= d[:, :-2]) & (d[:, 1:-1] >= d[:, 2:])
    dm = np.where(interior, d, 0.0)
    order = np.argsort(-dm, axis=1)[:, :N_PEAKS]
    vals = np.take_along_axis(dm, order, 1)
    cand = np.where(vals >= PEAK_FRAC * vals[:, :1], order.astype(float), -1.0)
    y = np.arange(h, dtype=float)
    yc = y.mean()

    # step 4: Hough vote, slants confined to the staple line +/- STAPLE_ANG_TOL
    sl0 = staple_slant(clip_entry, fallback=issue_slant) or 0.0
    sl0 = sl0 if parity == "odd" else -sl0                # band is mirrored on even pages
    lo = np.tan(np.arctan(sl0) - np.deg2rad(STAPLE_ANG_TOL))
    hi = np.tan(np.arctan(sl0) + np.deg2rad(STAPLE_ANG_TOL))
    tol = TOL_MM / MM * WORK_DPI
    ok = cand >= 0
    best = (-1, 0.0, 0.0)
    for m_ in np.arange(lo, hi + 1e-9, np.deg2rad(ANG_STEP_DEG)):
        pos = np.where(ok, cand - m_ * (y - yc)[:, None], np.nan)
        flat = pos[np.isfinite(pos)]
        if flat.size == 0:
            continue
        # a row agrees if ANY of its candidates does; count ROWS, not candidates
        hist, edges = np.histogram(flat, bins=np.arange(flat.min(), flat.max() + tol, tol))
        c0 = edges[int(np.argmax(hist))]
        agree = np.nanmin(np.abs(pos - c0), axis=1) <= tol
        k = int(np.nansum(agree))
        if k > best[0]:
            v = pos[agree]
            best = (k, float(np.nanmedian(v[np.abs(v - c0) <= tol])), float(m_))
    _, x0, slope = best

    # step 5: longest UNBROKEN run of agreeing rows
    line = x0 + slope * (y - yc)
    inl = np.nanmin(np.abs(np.where(ok, cand, np.nan) - line[:, None]), axis=1) <= tol
    dd = np.diff(np.concatenate(([0], inl.view(np.int8), [0])))
    starts, ends = np.where(dd == 1)[0], np.where(dd == -1)[0]
    runs = ends - starts
    longest = int(runs.max()) if len(runs) else 0
    run_mm = longest / WORK_DPI * MM

    # magnitude of the step the fitted line actually crosses
    xi = int(round(np.clip(x0, 8, d.shape[1] - 9)))
    o, ww = 3, 5
    o_col = np.median(f[:, max(0, xi - o - ww):max(1, xi - o)], axis=1)
    i_col = np.median(f[:, xi + o:xi + o + ww], axis=1)
    step = float(np.percentile(np.linalg.norm(i_col - o_col, axis=1), 90))
    found = (step >= MIN_STEP) and (run_mm >= MIN_RUN_MM)

    def _cream(c):
        return bool(c[0] >= CREAM_L_MIN and abs(c[1]) / CHROMA_W <= CREAM_CHROMA
                    and abs(c[2]) / CHROMA_W <= CREAM_CHROMA)
    c_out = np.median(o_col, axis=0); c_in = np.median(i_col, axis=0)
    ours_cream, neigh_cream = _cream(c_in), _cream(c_out)

    # -> 600-dpi page coordinates (inboard distance from the binding edge)
    k = SRC_DPI / WORK_DPI
    inb_top = (x0 + slope * (0 - yc)) * k
    inb_bot = (x0 + slope * (h - 1 - yc)) * k
    ang = float(np.rad2deg(np.arctan(slope)))
    return dict(page=page, parity=parity, found=bool(found),
                inboard_top=float(inb_top), inboard_bot=float(inb_bot),
                inboard_mid=float((inb_top + inb_bot) / 2),
                angle_deg=ang if parity == "odd" else -ang,
                run_mm=round(run_mm, 2), step=round(step, 1),
                ours_cream=ours_cream, neighbour_cream=neigh_cream,
                extra_cut=bool(ours_cream or not neigh_cream),
                inlier_frac=round(float(inl.mean()), 3),
                W=W, H=H,
                clip_inboard=None if hole_in is None else float(hole_in * k))


def overlay(page, r, thumb_dir=THUMB_DIR):
    im = Image.open(os.path.join(thumb_dir, "%03d.png" % page)).convert("RGB")
    W, H = im.size
    sc = 4
    small = im.resize((W // sc, H // sc), Image.LANCZOS)
    dr = ImageDraw.Draw(small)
    ax = (lambda inb: (W - inb) if r["parity"] == "even" else inb)
    if r["found"]:
        dr.line([ax(r["inboard_top"]) / sc, 0, ax(r["inboard_bot"]) / sc, H / sc],
                fill=(0, 255, 0), width=2)
    if r.get("clip_inboard"):
        dr.line([ax(r["clip_inboard"]) / sc, 0, ax(r["clip_inboard"]) / sc, H / sc],
                fill=(255, 60, 255), width=1)
    dr.rectangle([4, 4, 560, 34], fill=(0, 0, 0))
    dr.text((9, 12), "p%03d %s run=%.1fmm frac=%.2f ang=%+.3f"
            % (page, "FIRE" if r["found"] else "none", r["run_mm"], r["inlier_frac"],
               r["angle_deg"]), fill=(255, 255, 255))
    p = os.path.join(OUT_DIR, "spine_%03d.png" % page)
    small.save(p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--overlay", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    clip = json.load(open(CLIP_JSON))
    issue = issue_staple_slant(clip)
    out = {}
    for n in a.pages or range(1, 177):
        r = detect(n, clip.get("%03d" % n), issue)
        out["%03d" % n] = r
        d = "" if r["clip_inboard"] is None else " clipd=%+.0f" % (r["inboard_mid"] - r["clip_inboard"])
        print("p%03d %-4s %-4s x=%6.1f ang=%+6.3f run=%5.1fmm step=%6.1f%s"
              % (n, r["parity"], "FIRE" if r["found"] else "none", r["inboard_mid"],
                 r["angle_deg"], r["run_mm"], r["step"], d))
        sys.stdout.flush()
        if a.overlay:
            overlay(n, r)
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print("wrote", a.json)


if __name__ == "__main__":
    main()
