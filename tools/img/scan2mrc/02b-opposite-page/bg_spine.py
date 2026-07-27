#!/usr/bin/env python3
"""Background-colour SPINE detector for scanned 64'er magazine pages.

THE SPINE (user's definition) = the visible NEIGHBOUR-PAGE BOUNDARY in the binding
(inner) margin: the line where the CURRENT page's background ends and the adjacent
(neighbour) page's differently-coloured / differently-toned region begins.

  Parity:  EVEN page -> inner margin on the RIGHT   (neighbour hugs the right edge)
           ODD  page -> inner margin on the LEFT    (neighbour hugs the left  edge)

Fire ONLY when a REAL neighbour background difference exists (gray ad vs white page,
white page vs green/blue/pink neighbour, red ad vs white neighbour, ...). On a
white-on-white margin -> return NONE (a separate clip-hole detector covers those).

THE LINE-FIT ARCHITECTURE (dense, per-row -- supersedes the sparse-stripe fit)
-----------------------------------------------------------------------------
The old detector fit the boundary from only ~7 sparse per-stripe medians, so the
slant wobbled (p176 teal gave 0.21 deg instead of ~0.29, others locked on tilted
content or held vertical wrongly). The bg-colour difference is cleanly detectable,
so we fit the line DENSELY and robustly instead:

  0. DESCREEN.  The neighbour/current backgrounds are HALFTONE-screened at 600 dpi;
     per-pixel colour is dot-noisy. We downscale the deskewed binding band ~DS x
     (-> ~100 dpi) and blur slightly in x, so each screen averages into a SOLID
     background colour and the boundary is crisp. All classification happens there;
     the fitted line is scaled back to the working (600-dpi) resolution at the end.

  1. CURRENT-PAGE PAPER `P`.  Robust median of the page's bright, low-chroma pixels
     (the dominant paper tone), used as the reference "current background".

  2. PER ROW, EDGE-TONE DEPARTURE.  `e_r` = the tone of the outermost few valid
     columns (touching the page edge) = this row's NEIGHBOUR tone. Walk inward while
     the tone matches `e_r`; the boundary is where it makes a SUSTAINED departure
     (>= DEPART for >= PERSIST px). This is symmetric: the neighbour may be a colour
     (teal/green/pink) OR the cream binding margin of a page whose CURRENT content is
     a full-bleed ad (p047 gray / p170 gray / p073 red) -- either way the boundary is
     where the coherent edge tone ends.

  3. REAL-BOUNDARY GATE (per row).  Keep a row only if one side genuinely differs
     from the current paper `P`: score = max(|e_r - P|, |inner - P|) >= SCORE_MIN.
     This (a) rejects cream-margin -> cream-content edges (coupon perforations, faint
     folds, blank margins -> white-on-white), and (b) naturally handles PARTIAL-height
     neighbours: only the rows that actually HAVE a neighbour survive (p172 top-green,
     p024/p011 bottom coupon, p175 lower photo), so the fit is not pulled off by the
     blank part of the page.

  4. ROBUST LINE FIT.  Theil-Sen + inlier reject over the (hundreds-thousands of)
     kept per-row boundary points -> the slant is exactly determined.
       * PARTIAL height (inliers span < SLANT_MIN_SPAN of the page) -> hold VERTICAL
         (do NOT extrapolate a slant from a short segment).
       * FULL height -> fit the real slant.
       * |angle| > MAX_ANGLE -> the detection is WRONG (skewed content lock), return
         NONE. NEVER clamp a too-steep fit to vertical (a clamp hides a misdetection).

FUNDAMENTAL LIMIT (honest): a cream binding margin that is the CURRENT page's OWN
margin is pixel-identical to a cream NEIGHBOUR margin; when the current page also
carries a colour form/box near the binding (p153 giro coupon, p166 giro form) the
"boundary" is genuinely ambiguous from colour alone (cf. CLAUDE.md: image-vs-content
is not separable by low-level stats). We lean on the clip-hole prior + tightness
there; residual ambiguous fires are reported, not hidden.

Reusable API:  detect_bg_spine(rgb, valid, parity, paper=None, prior_col=None) -> dict
CLI:           bg_spine.py NNN.png [--parity ..] [--overlay OUT] [--json]
               bg_spine.py --batch DIR --out OUTDIR

Everything spatial is expressed at a REFERENCE resolution (600-dpi thumb) and scaled
by sx=W/REF_W so the same code runs at the 2400-dpi master.
"""
import sys, os, json, glob, argparse, re
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d
Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------
# CONSTANTS  (reference resolution: 600-dpi thumb, REF_W wide)
# ---------------------------------------------------------------------------
REF_W = 5200                     # reference page width these px numbers were tuned at

# --- descreen (classification is done on a downscaled + x-blurred band) ------
DS          = 6                  # downscale factor: 600 dpi / 6 ~= 100 dpi -> the
                                 #   ~150-lpi screen averages into a solid bg colour.
BLUR        = 1.2                # extra gaussian blur (in downscaled px, along x)
BAND_FRAC   = 0.16               # width of the spine-side band we analyse
EDGE_SKIP   = 14                 # skip the very page edge (scan-edge shadow), ref px
EDGESTRIP   = 40                 # width of the per-row edge-tone (neighbour) sample, ref px

# --- feature (colour-aware background vector) --------------------------------
FEAT_SCALE  = np.array([8.0, 4.5, 4.5])   # L, R-G, G-B normalisers (chroma up-weighted
                                  #   so a near-neutral pink/blue step fires like luma)

# --- where the boundary may sit (distance INBOARD from the page edge), ref px -
MINW        = 90                 # reject page-edge / edge-shadow / fill locks
MAXW        = 470                # reject current-page content locks deep inboard
PRIOR_OUT   = 110                # if a clip-hole prior col is given, search only
PRIOR_IN    = 110                #   [prior-PRIOR_OUT(outboard), prior+PRIOR_IN(inboard)]
MINRUN      = 34                 # neighbour region must be >= this wide (kills thin
                                 #   rules / crop-marks / clip teardrops), ref px

# --- edge-tone departure (the per-row boundary) -----------------------------
DEPART      = 3.2                # sustained tone change (feat units) = a real boundary
PERSIST     = 44                 # ... that must persist this many ref px inward
UNIF        = 3.0                # neighbour region (edge..boundary) max mean per-chan
                                 #   std -> a real neighbour is ~one tone; content is not

# --- real-boundary gate: TWO paths, one side must be a genuine neighbour bg ---
# A row's boundary is REAL iff EITHER:
#   PATH A -- the EDGE tone is clearly a neighbour colour/tone (differs from paper):
#             |edge - P| >= EDGE_MIN.  Covers teal/green/pink/blue/gray neighbours
#             touching the page edge (p176/p128/p160/p172/p011/p024/p175).
#   PATH B -- the edge is paper (the cream binding margin) but the CURRENT page is a
#             full-bleed ad: the inner side is a SOLID non-paper block that FILLS
#             inboard (|inner-P| and |inner_deep-P| >= INNER_MIN and inner std < SOLID).
#             Covers p047/p170 gray ads, p073 red banner.
# Cream-margin -> current text column / coupon perforation / faint fold / giro form
# (p172 lower rows, p153, p166, p088): edge=paper (fails A) and inner is textured
# paper/ink that does NOT fill inboard (fails B) -> correctly NOT a neighbour.
EDGE_MIN    = 4.0                # PATH A: |edge - P| threshold (feat units)
INNER_FILL_W = 3.0               # PATH B: inboard span checked = [bnd : bnd+FILL_W*PERSIST]
INNER_NP_THR = 3.5               # PATH B: a pixel is "non-paper" if |feat - P| >= this
INNER_NP_FRAC = 0.60             # PATH B: >= this FRACTION of the inboard span must be
                                 #   non-paper -> the current page is a full-bleed ad that
                                 #   FILLS inboard (p047/p170 gray, p073 red). Robust to ad
                                 #   text/logos (a minority). A cream margin -> text column
                                 #   / coupon panel / giro form is mostly paper -> fails.
INNER_D0    = 0.5                # inner tone sampled over [bnd+D0*PERSIST : bnd+D1*PERSIST]
INNER_D1    = 1.5                #   -- just past the boundary (for reporting/step)
PAPER_PCT   = 60                 # paper P = median of pixels brighter than this luma pct
PAPER_CHROMA = 40                #   and |R-G|+|G-B| < this (drop coloured content)

# --- robust fit + fire/none decision ----------------------------------------
FIT_TOL     = 25                 # Theil-Sen inlier tolerance (ref px)
MIN_ROWS    = 45                 # need >= this many kept+inlier rows to report a spine
XSTD_MAX    = 26                 # inlier boundary-x std (ref px) must be <= this (tight)
INL_FRAC    = 0.45               # >= this fraction of kept rows must be inliers
SLANT_MIN_SPAN = 0.55            # fit a slant only if inliers span >= this fraction of the
                                 #   height; else hold VERTICAL (partial-height coupon).
MAX_ANGLE   = 1.2                # |slant| above this => MISDETECTION => return NONE (reject)
DARK_NEIGH  = 80                 # a solid DARK, NEUTRAL edge tone (L<this ...
DARK_CHROMA = 22                 #   ... and |R-G|+|G-B|<this) is a gutter shadow / frame
                                 #   bar, not a neighbour page -> reject.

# --- confidence -------------------------------------------------------------
CONF_FULL_ROWS = 300             # this many inlier rows -> full completeness score
XCONSIST_TOL   = 18              # boundary-x std (ref px) for a "tight" column


# ---------------------------------------------------------------------------
def _theilsen(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    sl = [(xs[j]-xs[i])/(ys[j]-ys[i])
          for i in range(len(xs)) for j in range(i+1, len(xs)) if ys[j] != ys[i]]
    m = float(np.median(sl)) if sl else 0.0
    return m, float(np.median(xs - m*ys))


def _feat(rgb):
    """Colour-aware background vector f = [L, R-G, G-B] / FEAT_SCALE."""
    R, G, Bc = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.stack([rgb.mean(-1), R - G, G - Bc], -1) / FEAT_SCALE


def _paper_estimate(rgb, valid):
    """Current-page paper P: robust median of the page's bright, low-chroma pixels
    (the dominant paper tone), in FEAT units. Robust to a partial neighbour and to
    current-page content (text/ads darker or coloured)."""
    f = _feat(rgb)
    L = f[..., 0] * FEAT_SCALE[0]
    chroma = np.abs(f[..., 1]) * FEAT_SCALE[1] + np.abs(f[..., 2]) * FEAT_SCALE[2]
    if valid.sum() < 100:
        return np.median(f.reshape(-1, 3), axis=0)
    thr = np.percentile(L[valid], PAPER_PCT)
    m = valid & (L > thr) & (chroma < PAPER_CHROMA)
    if m.sum() < 1000:
        m = valid & (L > thr)
    return np.median(f[m], axis=0)


def detect_bg_spine(rgb, valid, parity, paper=None, prior_col=None):
    """Detect the background-colour spine on a DESKEWED page.

    rgb      : (H,W,3) float or uint8, already deskewed.
    valid    : (H,W) bool - True for real pixels, False for deskew-fill/invalid.
    parity   : 'even' (right margin) or 'odd' (left margin).
    prior_col: optional clip-hole column x (absolute) - centres the search + cross-check.
    Returns dict: found, x_top, x_bot, column_x, angle_deg, step, n_stripes,
                  confidence, parity, W, H, points [(x,y)].
    """
    rgb = np.asarray(rgb, np.float32)
    H, W = rgb.shape[:2]
    sx = W / REF_W
    band = max(1, int(BAND_FRAC * W))
    empty = {"found": False, "x_top": None, "x_bot": None, "column_x": None,
             "angle_deg": 0.0, "step": 0.0, "n_stripes": 0, "confidence": 0.0,
             "parity": parity, "W": W, "H": H, "points": []}

    # --- current-page paper reference ------------------------------------------
    P = _paper_estimate(rgb, valid)

    # --- extract the spine-side band, oriented so index 0 = the page edge ------
    if parity == "even":
        sub = rgb[:, W - band:][:, ::-1]; vsub = valid[:, W - band:][:, ::-1]
        def to_abs(inb):  return W - 1 - inb
    else:
        sub = rgb[:, :band]; vsub = valid[:, :band]
        def to_abs(inb):  return inb

    # --- descreen: downscale + x-blur so the halftone -> solid bg colour -------
    BWd = max(4, sub.shape[1] // DS); Hd = max(4, sub.shape[0] // DS)
    subi = Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8)).resize((BWd, Hd), Image.BILINEAR)
    subd = np.asarray(subi, np.float32)
    vd = np.asarray(Image.fromarray((vsub * 255).astype(np.uint8)).resize((BWd, Hd), Image.BILINEAR),
                    np.float32) > 200
    fd = _feat(subd)
    for k in range(3):
        fd[..., k] = gaussian_filter1d(fd[..., k], BLUR, axis=1)

    # --- search window (inboard distance from edge), narrowed by the clip prior -
    prior_inb = None
    if prior_col is not None:
        prior_inb = (W - prior_col) if parity == "even" else prior_col
    lo_inb, hi_inb = MINW * sx, MAXW * sx
    if prior_inb is not None:
        lo_inb = max(lo_inb, prior_inb - PRIOR_OUT * sx)
        hi_inb = min(hi_inb, prior_inb + PRIOR_IN * sx)

    es = max(1, int(EDGE_SKIP * sx / DS))
    estrip = max(2, int(EDGESTRIP * sx / DS))
    minrun = max(1, int(MINRUN * sx / DS))
    persist = max(2, int(PERSIST * sx / DS))
    maxw_d = int(MAXW * sx / DS)

    pts, erows, irows, steps = [], [], [], []
    for r in range(Hd):
        vr = vd[r]; fr = fd[r]
        idx = np.where(vr[es:])[0]
        if idx.size < estrip + minrun:
            continue
        oc = es + idx[0]                                   # outermost valid column
        strip = fr[oc:oc + estrip][vr[oc:oc + estrip]]
        if strip.shape[0] < estrip * 0.5:
            continue
        e_r = np.median(strip, axis=0)                     # this row's neighbour tone
        d = np.linalg.norm(fr - e_r, axis=1)               # departure from edge tone
        bnd = None
        x = oc + estrip
        hi = min(oc + maxw_d, BWd - persist)
        while x < hi:
            if not vr[x]:
                x += 1; continue
            if d[x] >= DEPART:                             # THIS pixel has departed = the edge
                seg = d[x:x + persist][vr[x:x + persist]]  # ... and it must sustain inward
                if seg.size >= persist * 0.5 and np.median(seg) >= DEPART:
                    bnd = x; break                         # bnd = the transition itself (no
                                                           #   persist/2 offset -> was ~16px inboard)
            x += 1
        if bnd is None or (bnd - oc) < minrun:
            continue
        inb = bnd * DS + DS // 2
        if inb < lo_inb or inb > hi_inb:
            continue
        # neighbour region (edge..boundary) must be ~one tone (a coherent bg)
        reg = fr[oc:bnd][vr[oc:bnd]]
        if reg.shape[0] >= 5 and float(np.mean(np.std(reg, axis=0))) > UNIF:
            continue
        # inner tone just past the boundary (for reporting/step)
        i0 = bnd + int(INNER_D0 * persist); i1 = min(bnd + int(INNER_D1 * persist), BWd)
        iseg = fr[i0:i1][vr[i0:i1]]
        i_r = np.median(iseg, axis=0) if iseg.shape[0] >= 3 else fr[min(bnd + persist, BWd - 1)]
        eP = float(np.linalg.norm(e_r - P))
        iP = float(np.linalg.norm(i_r - P))
        pathA = eP >= EDGE_MIN                                     # colored/dark neighbour at edge
        # PATH B: the inboard span is DOMINANTLY non-paper (a full-bleed ad fills it)
        pathB = False
        if not pathA:
            f0 = bnd; f1 = min(bnd + int(INNER_FILL_W * persist), BWd)
            fseg = fr[f0:f1][vr[f0:f1]]
            if fseg.shape[0] >= 5:
                np_frac = float(np.mean(np.linalg.norm(fseg - P, axis=1) >= INNER_NP_THR))
                pathB = np_frac >= INNER_NP_FRAC
        if not (pathA or pathB):
            continue
        pts.append((to_abs(inb), r * DS + DS // 2))
        erows.append(e_r); irows.append(i_r); steps.append(max(eP, iP))

    if len(pts) < MIN_ROWS:
        return empty

    px = np.array([p[0] for p in pts], float)
    py = np.array([p[1] for p in pts], float)

    # --- robust fit: cluster near median x, then iterate Theil-Sen -------------
    med = np.median(px)
    inl = np.abs(px - med) < 2.4 * FIT_TOL * sx
    if inl.sum() < MIN_ROWS:
        return empty
    m, bb = _theilsen(px[inl], py[inl])
    for _ in range(3):
        inl = np.abs(px - (m * py + bb)) < FIT_TOL * sx
        if inl.sum() < MIN_ROWS:
            return empty
        m, bb = _theilsen(px[inl], py[inl])

    pxi, pyi = px[inl], py[inl]
    xstd = float(np.std(pxi))
    frac = inl.sum() / len(px)
    if xstd > XSTD_MAX * sx or frac < INL_FRAC:
        return empty

    yspan = (pyi.max() - pyi.min()) / H
    if yspan >= SLANT_MIN_SPAN:
        m, bb = _theilsen(pxi, pyi)
        ang = float(np.degrees(np.arctan(m)))
        if abs(ang) > MAX_ANGLE:                    # too steep => MISDETECTION, not a real
            return empty                            #   spine -> reject (never clamp)
    else:                                           # partial-height -> hold vertical
        m, bb = 0.0, float(np.median(pxi)); ang = 0.0

    x_top = m * 0 + bb
    x_bot = m * H + bb
    column_x = float(np.median(pxi))

    # --- reject a solid DARK, NEUTRAL edge = binding-gutter shadow / frame bar --
    nt = np.median(np.array(erows), axis=0) * FEAT_SCALE
    eL = float(nt[0]); echr = float(abs(nt[1]) + abs(nt[2]))
    if eL < DARK_NEIGH and echr < DARK_CHROMA:
        return empty

    # --- confidence: completeness x strength x tightness x prior agreement -----
    comp = min(1.0, inl.sum() / CONF_FULL_ROWS)
    strength = float(np.clip((np.median(steps) - EDGE_MIN) / (12.0 - EDGE_MIN), 0.15, 1.0))
    tight = 1.0 if xstd <= XCONSIST_TOL * sx else 0.65
    conf = comp * (0.5 + 0.5 * strength) * tight
    if prior_col is not None:
        agree = abs(column_x - prior_col)
        if agree <= 120 * sx:
            conf = min(1.0, conf * 1.15)
        elif agree > 300 * sx:
            conf *= 0.5
    conf = round(float(np.clip(conf, 0.0, 1.0)), 3)

    return {"found": True, "x_top": float(x_top), "x_bot": float(x_bot),
            "column_x": float(column_x), "angle_deg": round(ang, 3),
            "step": round(float(np.median(steps)), 2), "n_stripes": int(inl.sum()),
            "confidence": conf, "parity": parity, "W": W, "H": H,
            "points": [(float(a), float(b)) for a, b in zip(px, py)]}


# ---------------------------------------------------------------------------
# Deskew helper (own-paper fill + validity mask) -- matches the pipeline step.
# ---------------------------------------------------------------------------
def deskew_page(im, angle_deg, parity):
    """Rotate by +angle_deg (expand), fill the rotation-added corners with THIS
    page's own inner-margin paper colour, and return (rgb float32, valid mask)."""
    rgb0 = np.asarray(im.convert("RGB"), np.float32)
    W = rgb0.shape[1]
    bw = max(1, int(0.12 * W))
    band = rgb0[:, W - bw:] if parity == "even" else rgb0[:, :bw]
    paper = np.median(band.reshape(-1, 3), axis=0)
    rot = im.convert("RGB").rotate(angle_deg, resample=Image.BICUBIC, expand=True,
                                   fillcolor=(0, 0, 0))
    rr = np.asarray(rot, np.float32)
    ones = Image.new("L", im.size, 255)
    valid = np.asarray(ones.rotate(angle_deg, resample=Image.NEAREST, expand=True),
                       np.uint8) > 127
    rr[~valid] = paper
    return rr, valid, paper


def parity_of(name):
    base = os.path.splitext(os.path.basename(name))[0]
    d = "".join(c for c in base if c.isdigit())
    return "even" if int(d) % 2 == 0 else "odd"


def load_skew(path):
    d = {}
    if path and os.path.exists(path):
        for ln in open(path):
            m = re.match(r".*?(\d{3})\.png:\s*([+-]?[\d.]+)\s*deg", ln)
            if m:
                d[int(m.group(1))] = float(m.group(2))
    return d


# ---------------------------------------------------------------------------
def make_overlay(rgb, valid, res, out_path, prior=None, crop=True):
    """ORANGE = bg-colour spine (this detector). Optional CYAN = clip prior column.
    Drawn at 50% opacity, alpha-composited."""
    base = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    H, W = rgb.shape[:2]; sx = W / REF_W
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    A = 128
    if prior is not None:
        d.line([(int(prior), 0), (int(prior), H)], fill=(0, 190, 255, A),
               width=max(2, int(4 * sx)))
    cx = None
    if res["found"]:
        cx = res["column_x"]
        d.line([(int(res["x_top"]), 0), (int(res["x_bot"]), H)],
               fill=(255, 140, 0, A), width=max(3, int(7 * sx)))
        for (x, y) in res["points"]:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 60, 0, A))
    comp = Image.alpha_composite(base, ov).convert("RGB")
    if crop:
        c = cx if cx is not None else (prior if prior is not None else
                                       (W - 260 * sx if res["parity"] == "even" else 260 * sx))
        pad = int(360 * sx)
        comp = comp.crop((int(max(0, c - pad)), 0, int(min(W, c + pad)), H))
    comp.save(out_path)
    return out_path


def _clip_prior(gray, W, H, parity):
    """Optional clip-hole column cross-check (if clip_holes.py is importable)."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, here)
        import clip_holes as ch
        tp = "/Users/mist/DNB/8609/tmp/clip_template.json"
        tmpl = ch.Template.from_json(json.load(open(tp))) if os.path.exists(tp) else ch.Template()
        r = ch.detect_clip_holes(gray, W, H, parity, tmpl)
        return r["column_x"], r["confidence"]
    except Exception:
        return None, 0.0


def run_page(path, parity=None, skew=0.0, prior=True):
    par = parity or parity_of(path)
    im = Image.open(path)
    rgb, valid, paper = deskew_page(im, skew, par)
    H, W = rgb.shape[:2]
    pc, pconf = (_clip_prior(rgb.mean(2), W, H, par) if prior else (None, 0.0))
    res = detect_bg_spine(rgb, valid, par, paper=paper,
                          prior_col=(pc if (pc is not None and pconf >= 0.5) else None))
    res["clip_col"] = pc; res["clip_conf"] = pconf
    return rgb, valid, res, pc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?")
    ap.add_argument("--parity", choices=["even", "odd"])
    ap.add_argument("--skew", type=float, default=None)
    ap.add_argument("--skewfile", default="/Users/mist/DNB/8609/tmp/skew_all.txt")
    ap.add_argument("--overlay", nargs="?", const="AUTO")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-prior", action="store_true")
    ap.add_argument("--batch")
    ap.add_argument("--out", default="/Users/mist/DNB/8609/tmp")
    args = ap.parse_args()
    skews = load_skew(args.skewfile)

    def one(path):
        n = int("".join(c for c in os.path.basename(path) if c.isdigit())[:3])
        sk = args.skew if args.skew is not None else skews.get(n, 0.0)
        return n, run_page(path, args.parity, sk, prior=not args.no_prior)

    if args.batch:
        paths = sorted(glob.glob(os.path.join(args.batch, "[0-9]*.png")))
        os.makedirs(args.out, exist_ok=True)
        results = {}
        for p in paths:
            n, (rgb, valid, res, pc) = one(p)
            results[f"{n:03d}"] = {k: v for k, v in res.items() if k != "points"}
            if args.overlay:
                make_overlay(rgb, valid, res, os.path.join(args.out, f"spine_{n:03d}.png"), prior=pc)
            print(f"p{n:03d} {res['parity']} found={res['found']} "
                  f"x={('%.0f'%res['column_x']) if res['found'] else '   -':>5} "
                  f"ang={res['angle_deg']:+.2f} step={res['step']:.1f} "
                  f"n={res['n_stripes']:4d} conf={res['confidence']:.2f} clip={pc}")
        json.dump(results, open(os.path.join(args.out, "bg_spine.json"), "w"), indent=2)
        return

    if not args.page:
        ap.error("give PAGE.png or --batch DIR")
    n, (rgb, valid, res, pc) = one(args.page)
    if args.json:
        print(json.dumps({k: v for k, v in res.items() if k != "points"}, indent=2))
    else:
        print(f"p{n:03d} {res['parity']} found={res['found']} col={res['column_x']} "
              f"ang={res['angle_deg']} step={res['step']} n={res['n_stripes']} "
              f"conf={res['confidence']} clip={pc}")
    if args.overlay:
        op = args.overlay
        if op == "AUTO":
            op = f"/Users/mist/DNB/8609/tmp/spine_{n:03d}.png"
        make_overlay(rgb, valid, res, op, prior=pc)
        print("overlay ->", op)


if __name__ == "__main__":
    main()
