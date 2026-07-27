#!/usr/bin/env python3
"""Binder-clip-hole detector for scanned 64'er magazine pages.

The pages were bound with a rigid 6-hole binder clip whose punches left DARK
TEARDROP / comma-shaped (and, where the paper tore, larger irregular) marks in
the binding (inner) margin. They sit in a tight VERTICAL COLUMN, arranged as
3 vertical PAIRS. The clip is rigid, so the RELATIVE y-spacing of the 6 holes is
(nearly) fixed across the issue; the column x and a global y offset vary per page.

Binding side by parity:  EVEN page -> inner margin on the RIGHT
                         ODD  page -> inner margin on the LEFT

Ground-truth calibration (what a REAL hole is, vs the many distractors)
-----------------------------------------------------------------------
Verified by eye on pages 050/073/088/011/128/024 ... :
  * A hole is TEARDROP/torn shaped, MODERATE-TO-LARGE, and REASONABLY DARK.
    Tiny AND faint specks are FALSE POSITIVES -> we apply BOTH a size floor and
    a darkness/contrast floor, plus a shape (aspect + fill) test.
  * Reject the dark BINDING-EDGE SHADOW BAND at the page edge (skip outer band).
  * Reject horizontal form/table RULES (long thin -> high aspect ratio).
  * Reject the neighbour page's colour strip (its dark edge is low-fill, and it
    is at the wrong column).
  * Photo / coupon / graphic texture in the margin makes MANY strong dark blobs
    -> a plain "densest dark column" locks onto it. We defeat that by scoring
    each candidate column against the rigid 3-PAIR TEMPLATE and PENALISING
    columns that carry lots of extra (non-template) blobs. Real holes sit at ~6
    isolated template positions; texture does not.

Pipeline: strong-teardrop detect -> template+sparsity column/offset selection ->
snap 6 slots (fill from teardrops, second-chance recover occluded ones) ->
confidence; weak pages fall back to the issue-median column (a good spine prior).

Reusable API:  detect_clip_holes(gray, W, H, parity, tmpl) -> dict
Calibration :  calibrate(paths) -> Template   (issue column prior + template)
CLI:
  clip_holes.py PAGE.png [--parity even|odd] [--overlay [OUT]] [--json] [--template T]
  clip_holes.py --batch DIR --out OUTDIR [--overlay] [--template T]
  clip_holes.py --calibrate DIR [--out template.json]

Spatial constants are at the reference resolution (600-dpi thumb ~5200x7188) and
SCALED by the actual page size, so the same code runs at the 2400-dpi master.
"""
import sys, os, json, glob, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import uniform_filter, label, find_objects

# ---------------------------------------------------------------------------
# CONSTANTS  (reference resolution: 600-dpi thumb, REF_W x REF_H)
# Everything spatial is scaled by sx=W/REF_W (x) and sy=H/REF_H (y).
# ---------------------------------------------------------------------------
REF_W, REF_H = 5200, 7188        # reference page size these numbers were tuned at

# --- inner-margin search window (distance INBOARD from the page edge, px) ---
IN_LO   = 60      # skip the outer band: edge shadow band lives within ~55px
IN_HI   = 440     # holes seen 195-290px inboard; leave headroom both sides

# --- local-contrast (adaptive) dark-blob detector ---------------------------
BG_WIN     = 81   # box size for the local-mean / local-std background (px)
K_STD      = 2.2  # "dark" if value < localmean - K_STD*localstd ...
MIN_ABS    = 10   # ... and at least this many levels below local mean

# --- STRONG-teardrop gate (a candidate must be a real hole, not a speck/rule) -
C_HARD    = 45    # darkness floor: reject anything fainter than this (contrast)
A_MIN     = 24    # size floor (px^2): reject tiny marks
A_MAX     = 900   # size ceiling: reject big ink / shadow regions
WH_MAX    = 85    # reject blobs wider/taller than this (px)
ASP_MAX   = 3.4   # reject elongated shapes (aspect = long/short) -> table RULES
FILL_MIN  = 0.42  # reject sprawly shapes (area/bbox) -> line fragments, texture

# --- rigid 6-hole template (RELATIVE y of the 6 holes, px @600dpi) ----------
TMPL_REL = np.array([0, 312, 1887, 2208, 3866, 4170], dtype=float)  # 3 pairs
TMPL_Y0  = 1465.0                # typical absolute y of hole0 (@600dpi)
DY_RANGE = 270                   # +/- global y-offset search (px) - pages shift
DY_STEP  = 10
COL_INB  = 250.0                 # issue-prior inboard distance (px), fallback col
COL_LO   = 150.0                 # a candidate column must be >= this far inboard of the page
COL_HI   = 400.0                 # edge and <= this: the clip is a fixed physical position, so a
                                 # column outside this band is a spurious edge/texture lock
                                 # (e.g. p115 x104 beat the real x266 on chance template hits)

# --- template <-> column matching -------------------------------------------
X_TOL   = 36      # blob counts for column x if within this in x (px)
Y_TOL   = 50      # ... and within this of a template slot in y (px)
HIT_BONUS   = 25.0    # reward per matched template slot
EXTRA_PEN   = 22.0    # penalty per non-template blob in the column (kills texture)
CONTRAST_CAP = 150.0  # clamp per-hole contrast contribution when scoring

# --- occluded-slot second-chance recovery -----------------------------------
FB_WIN     = 25   # tight local-mean box (so a graphic edge can't hide the hole)
FB_MINDIP  = 12   # min darker-than-local-surround to accept a faint hole
FB_CMIN    = 8    # recovered dark region must be at least this compact (px^2)
FB_CMAX    = 700  # ... and no bigger (reject a swept-in line/graphic)

# --- confidence -------------------------------------------------------------
CONF_XSTD_MAX = 26.0   # column is "tight" if std of found xs <= this (px @600dpi)
WEAK_HITS     = 2      # <= this many template hits -> unreliable, use prior column


# ---------------------------------------------------------------------------
class Template:
    """Issue-wide geometry: rigid relative shape, typical y0, prior column."""
    def __init__(self, rel=TMPL_REL, y0=TMPL_Y0, col_inb=COL_INB):
        self.rel = np.asarray(rel, float)
        self.y0 = float(y0)
        self.col_inb = float(col_inb)   # median inboard distance (spine prior)

    def to_json(self):
        return {"rel": self.rel.tolist(), "y0": self.y0, "col_inb": self.col_inb}

    @staticmethod
    def from_json(d):
        return Template(np.array(d["rel"], float), float(d["y0"]),
                        float(d.get("col_inb", COL_INB)))


def parity_of(name):
    """even/odd from the page NUMBER in the filename (NNN.png)."""
    base = os.path.splitext(os.path.basename(name))[0]
    digits = "".join(ch for ch in base if ch.isdigit())
    return "even" if int(digits) % 2 == 0 else "odd"


def _strong_teardrops(gray, W, H, parity, sx, sy):
    """Adaptive-threshold dark blobs in the inner margin, gated to REAL holes.

    Returns [(x, y, area, contrast)] in ABSOLUTE page coords. contrast =
    localmean - value (darker-than-paper), so it works on ANY paper colour."""
    lo, hi = int(IN_LO * sx), int(IN_HI * sx)
    if parity == "even":
        x0, x1 = W - hi, W - lo
    else:
        x0, x1 = lo, hi
    x0 = max(0, x0); x1 = min(W, x1)
    strip = gray[:, x0:x1]
    win = max(11, int(round(BG_WIN * (sx + sy) / 2)) | 1)
    bg = uniform_filter(strip, size=win, mode="nearest")
    m2 = uniform_filter(strip * strip, size=win, mode="nearest")
    std = np.sqrt(np.maximum(m2 - bg * bg, 1.0))
    resp = bg - strip
    cand = resp > np.maximum(K_STD * std, MIN_ABS)
    amin = A_MIN * sx * sy
    amax = A_MAX * sx * sy
    whmax = WH_MAX * (sx + sy) / 2
    lab, _ = label(cand)
    out = []
    for i, sl in enumerate(find_objects(lab)):
        if sl is None:
            continue
        ys, xs = sl
        h = ys.stop - ys.start
        w = xs.stop - xs.start
        area = int((lab[sl] == i + 1).sum())
        if not (amin <= area <= amax) or w > whmax or h > whmax:
            continue
        asp = max(h, w) / max(1, min(h, w))
        fill = area / max(1, h * w)
        cy = (ys.start + ys.stop) // 2
        cx = (xs.start + xs.stop) // 2
        c = float(resp[cy, cx])
        if c < C_HARD or asp > ASP_MAX or fill < FILL_MIN:   # size+dark+shape gate
            continue
        out.append((cx + x0, cy, area, c))
    return out


def _recover_slot(gray, W, H, cx, ty, xtol, ytol):
    """Second-chance search for a hole occluded by ink at (cx, ty).

    Returns (x, y, contrast) of a compact dark dip, or None. A tight local
    background keeps a nearby graphic edge from masking the hole."""
    x0 = max(0, int(cx - xtol)); x1 = min(W, int(cx + xtol))
    y0 = max(0, int(ty - ytol)); y1 = min(H, int(ty + ytol))
    win = gray[y0:y1, x0:x1]
    if win.size == 0:
        return None
    bg = uniform_filter(win, size=FB_WIN, mode="nearest")
    resp = bg - win
    mx = float(resp.max())
    if mx < FB_MINDIP:
        return None
    yy, xx = np.unravel_index(np.argmax(resp), resp.shape)
    lab, _ = label(resp > mx * 0.6)
    comp = int((lab == lab[yy, xx]).sum())
    if FB_CMIN <= comp <= FB_CMAX:
        return (x0 + xx, y0 + yy, mx)
    return None


def detect_clip_holes(gray, W, H, parity, tmpl=None):
    """Detect the 6 binder-clip holes.

    gray   : 2-D array (luminance) of the full page.
    parity : 'even' (right margin) or 'odd' (left margin).
    Returns dict: holes [(x,y,found,contrast) x6 top->bottom], column_x (spine
    cue), n_found, recovered[6], hits (template slots matched by a strong hole),
    dy, confidence 0..1, parity, W, H."""
    if tmpl is None:
        tmpl = Template()
    sx, sy = W / REF_W, H / REF_H
    rel = tmpl.rel * sy
    y0 = tmpl.y0 * sy
    xtol, ytol = X_TOL * sx, Y_TOL * sy
    prior_col = (W - tmpl.col_inb * sx) if parity == "even" else (tmpl.col_inb * sx)
    empty = {"holes": [], "column_x": int(round(prior_col)), "n_found": 0,
             "recovered": [False] * 6, "hits": 0, "dy": 0, "confidence": 0.0,
             "parity": parity, "W": W, "H": H}

    blobs = _strong_teardrops(gray, W, H, parity, sx, sy)
    if len(blobs) < 2:
        return empty
    bx = np.array([b[0] for b in blobs], float)
    by = np.array([b[1] for b in blobs], float)
    bc = np.array([b[3] for b in blobs], float)

    # --- template + sparsity scored search over (column x, global offset dy) --
    best = None
    dys = np.arange(-DY_RANGE * sy, DY_RANGE * sy + 1, DY_STEP * sy)
    col_lo, col_hi = COL_LO * sx, COL_HI * sx
    for cx in np.unique(bx):
        inb_cx = (W - cx) if parity == "even" else cx      # inboard distance of this column
        if not (col_lo <= inb_cx <= col_hi):               # physically-implausible column
            continue
        dxok = np.abs(bx - cx) <= xtol
        ncol = int(dxok.sum())
        if ncol < 2:
            continue
        for dy in dys:
            slots = y0 + dy + rel
            sc = 0.0
            hits = 0
            for ty in slots:
                m = dxok & (np.abs(by - ty) <= ytol)
                if m.any():
                    sc += min(bc[m].max(), CONTRAST_CAP)
                    hits += 1
            extra = max(0, ncol - hits)               # non-template blobs = texture
            score = sc + hits * HIT_BONUS - extra * EXTRA_PEN - abs(dy) * 0.002
            if best is None or score > best[0]:
                best = (score, cx, dy, hits)
    if best is None:
        return empty
    _, cx, dy, hits = best
    slots = y0 + dy + rel

    # --- snap each of the 6 slots to the strong teardrop nearest the column ---
    holes, recovered, found_x = [], [False] * 6, []
    for k, ty in enumerate(slots):
        m = (np.abs(bx - cx) <= xtol) & (np.abs(by - ty) <= ytol)
        if m.any():
            idx = np.where(m)[0]
            j = idx[np.argmax(bc[idx])]
            holes.append((int(bx[j]), int(by[j]), True, float(bc[j])))
            found_x.append(bx[j])
        else:
            holes.append((None, int(round(ty)), False, 0.0))
    # column from the strong holes we actually landed on; else the selected cx.
    column_x = int(np.median(found_x)) if len(found_x) >= 1 else int(round(cx))
    # only OVERRIDE with the issue prior when the column is unsupported AND either
    # a wild inboard outlier or the alignment is weak - never discard a good column.
    inb = (W - column_x) if parity == "even" else column_x
    sane = (170 * sx) <= inb <= (345 * sx)
    if len(found_x) < 2 and (not sane or hits <= WEAK_HITS):
        column_x = int(round(prior_col))

    # second-chance recovery for occluded slots + snap remaining misses to column
    for k, (x, y, f, c) in enumerate(holes):
        if f:
            continue
        got = _recover_slot(gray, W, H, column_x, y, xtol, ytol)
        if got:
            recovered[k] = True
            holes[k] = (int(got[0]), int(got[1]), True, float(got[2]))
        else:
            holes[k] = (column_x, y, False, 0.0)

    n_found = sum(1 for h in holes if h[2])
    xstd = float(np.std(found_x)) if len(found_x) >= 2 else 0.0
    # confidence blends STRONG-hole support (hits) with completeness (n_found);
    # a loose column or near-zero strong support caps it (verify those by eye).
    conf = (0.4 * hits + 0.6 * n_found) / 6.0
    if xstd > CONF_XSTD_MAX * sx:
        conf *= 0.6
    if hits <= 1:                       # template barely locked -> unreliable
        conf = min(conf, 0.35)
    return {"holes": holes, "column_x": column_x, "n_found": n_found,
            "recovered": recovered, "hits": hits, "dy": int(round(dy)),
            "confidence": round(conf, 3), "parity": parity, "W": W, "H": H}


def detect_path(path, parity=None, tmpl=None):
    im = Image.open(path).convert("L")
    W, H = im.size
    g = np.asarray(im, float)
    return detect_clip_holes(g, W, H, parity or parity_of(path), tmpl)


def calibrate(paths, tmpl0=None):
    """Derive the issue geometry from many pages.

    Pools confident pages (>=5 template hits) to re-estimate the rigid RELATIVE
    shape, typical y0, and the median inboard column distance (spine prior).
    Defaults already match this issue; calibration tightens them for a new one.
    """
    if tmpl0 is None:
        tmpl0 = Template()
    rels, y0s, inbs = [], [], []
    for p in paths:
        r = detect_path(p, tmpl=tmpl0)
        if r["hits"] >= 5 and r["n_found"] == 6:
            H = r["H"]; W = r["W"]
            ys = np.array([h[1] for h in r["holes"]], float) / (H / REF_H)
            rels.append(ys - ys[0]); y0s.append(ys[0])
            inb = (W - r["column_x"]) if r["parity"] == "even" else r["column_x"]
            inbs.append(inb / (W / REF_W))
    if not rels:
        return tmpl0
    rel = np.median(np.array(rels), axis=0); rel -= rel[0]
    return Template(rel, float(np.median(y0s)), float(np.median(inbs)))


# ---------------------------------------------------------------------------
# Overlay (50% opacity, alpha-composited) - REQUIRED for vision verification.
# green = primary hole, yellow = recovered (faint/occluded), red = missing.
# ---------------------------------------------------------------------------
def make_overlay(path, res, out_path, crop_margin=True):
    base = Image.open(path).convert("RGB")
    W, H = base.size
    sx = W / REF_W
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx = res["column_x"]
    if cx is not None:
        d.line([(cx, 0), (cx, H)], fill=(0, 160, 255, 255), width=max(2, int(3 * sx)))
    r = int(38 * sx)
    rec = res.get("recovered", [False] * len(res["holes"]))
    for i, (x, y, found, c) in enumerate(res["holes"]):
        if x is None:
            x = cx
        col = (255, 210, 0, 255) if (found and rec[i]) else \
              (0, 220, 0, 255) if found else (255, 40, 40, 255)
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(3, int(5 * sx)))
        d.line([(x - r - 8, y), (x + r + 8, y)], fill=col, width=2)
        d.line([(x, y - r - 8), (x, y + r + 8)], fill=col, width=2)
    ov.putalpha(ov.split()[3].point(lambda a: a // 2))          # 50% opacity
    comp = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    if crop_margin and cx is not None:
        pad = int(360 * sx)
        comp = comp.crop((max(0, cx - pad), 0, min(W, cx + pad), H))
    comp.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?", help="NNN.png")
    ap.add_argument("--parity", choices=["even", "odd"])
    ap.add_argument("--overlay", nargs="?", const="AUTO")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--template")
    ap.add_argument("--batch")
    ap.add_argument("--out")
    ap.add_argument("--calibrate")
    args = ap.parse_args()

    tmpl = Template.from_json(json.load(open(args.template))) if args.template else Template()

    if args.calibrate:
        paths = sorted(glob.glob(os.path.join(args.calibrate, "[0-9]*.png")))
        t = calibrate(paths)
        outp = args.out or "clip_template.json"
        json.dump(t.to_json(), open(outp, "w"), indent=2)
        print("template ->", outp, t.to_json())
        return

    if args.batch:
        paths = sorted(glob.glob(os.path.join(args.batch, "[0-9]*.png")))
        outdir = args.out or "."
        os.makedirs(outdir, exist_ok=True)
        results = {}
        for p in paths:
            r = detect_path(p, tmpl=tmpl)
            n = os.path.splitext(os.path.basename(p))[0]
            results[n] = r
            if args.overlay:
                make_overlay(p, r, os.path.join(outdir, f"holes_{n}.png"))
            print(f"p{n} {r['parity']} colx={r['column_x']} found={r['n_found']}/6 "
                  f"hits={r['hits']} conf={r['confidence']}")
        json.dump(results, open(os.path.join(outdir, "clip_holes.json"), "w"), indent=2)
        print("json ->", os.path.join(outdir, "clip_holes.json"))
        return

    if not args.page:
        ap.error("give a PAGE.png, --batch DIR, or --calibrate DIR")
    r = detect_path(args.page, args.parity, tmpl)
    if args.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"{args.page} {r['parity']} column_x={r['column_x']} found={r['n_found']}/6 "
              f"hits={r['hits']} conf={r['confidence']} dy={r['dy']}")
        for i, (x, y, f, c) in enumerate(r["holes"]):
            tag = "FOUND" if f else "MISSING"
            if f and r["recovered"][i]:
                tag = "RECOVERED"
            print(f"  hole{i}: x={x} y={y} {tag} contrast={c:.0f}")
    if args.overlay:
        op = args.overlay
        if op == "AUTO":
            op = os.path.join("/Users/mist/DNB/8609/tmp",
                              f"holes_{os.path.splitext(os.path.basename(args.page))[0]}.png")
        make_overlay(args.page, r, op)
        print("overlay ->", op)


if __name__ == "__main__":
    main()
