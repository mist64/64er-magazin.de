#!/usr/bin/env python3
"""Bed matte: mark the scanner backing at each page edge as unknown (alpha 0).

Backing = the scanner bed (lid / backing sheet / its shadow) and the coloured cardboard
insert (yellow, at the bottom of this issue). The page must not be cut.

THE ALGORITHM -- three steps, one code path for all four edges, and the middle step is the
SHARED core in ../linefit.py that 02b/spine.py also uses:

  1. PER LINE, CANDIDATE TRANSITIONS. Orient the edge so axis1 runs from the border inward.
     A pixel is BACKING if it is BLACKISH (dark AND neutral -> bed) or YELLOWISH (bright AND
     saturated -> cardboard). Offer the first N_CAND backing->page transitions per line.
  2. ROBUST LINE FIT (linefit.fit): the (offset, slope) most lines agree on, then LSQ on the
     inliers, plus a bounded quadratic for the sheet's bow.
  3. MARGIN AND DECISION, kept OUT of the fit: a fixed overcut, and independent tests for
     whether this edge should be cut at all.

WHY THE REWRITE. The previous version walked to the FIRST non-backing pixel -- ONE candidate
per line -- so a single anomalous pixel ruined that line, and the damage was repaired
downstream with an outlier fence, a coverage percentile, depth smoothing, gap bridging and a
strip extension. Each was a workaround for not having a robust fit, and they fought:

    walk stops in a transition blur -> gap bridging -> leapt through an ad's black TEXT
                                                       (p044 bottom 160 -> 292)
    deep outlier lines              -> MAD fence    -> too tight left bed standing on p003,
                                                       too loose over-cut p044 by 44px
    spiky depths                    -> smoothing    -> fit disagreed with what it must cover
    bed strip after the blur        -> extension    -> combed p005's halftone per column

A MODE fit needs none of it. Deleted here: OUTLIER_K, FENCE_MIN_600, COVER_PCT, SLACK,
SMOOTH_D_600, GAP_BRIDGE_600, STRIP_*, PAGECUT_FRAC, and the learned-prior acceptance path.

RULES (from the user):
  1. every backing pixel must be cut -- leaving a stripe is a FAIL
  2. subject to that, cut as few of OUR pixels as possible

CONSTRAINT: full-bleed dark pages (p047, p069) have real black ink to the very edge, and
SOLID black ink is separable from bed by neither colour nor texture. Those edges are left
uncut deliberately -- see the INK and vote tests.
"""
import os, sys, json, argparse, numpy as np, scipy.ndimage as ndi
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import linefit

Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------------------------------
# CONSTANTS  (spatial values @600dpi, scaled by dpi/600)
# ---------------------------------------------------------------------------------------------------
WIN_TB_FRAC   = 0.08     # top/bottom search depth as a fraction of image HEIGHT
WIN_LR_FRAC   = 0.16     # left/right search depth as a fraction of image WIDTH (bars are wide)

# --- step 1: what IS backing (positive material test) -----------------------------------------------
# NOTHING about the backing is written here any more. WHICH materials are backing, WHAT colour
# they are and WHICH edges they lie on come from calibrate_backing.py, which measures them over
# the issue: backing is the material that covers the border ring and vanishes inboard. It found
# the bed on top/left/right and the insert on the bottom of 176/176 pages, and correctly refused
# the cream paper everywhere. The old BED_LUMA/BED_SAT/INSERT_LUMA/INSERT_SAT/INSERT_EDGES were
# the same facts guessed instead of measured, and each broke somewhere (p044's ochre ad matched
# "yellowish" on a left edge with no insert on it; p001's teal cover nearly did too).
RING_600      = 3        # border ring used to refine a material on the page in front of us
SEED_STEP     = 8        # quantisation for finding the ring's densest colour peak
SPREAD_PCTL   = 90       # per-page radius = this percentile of the peak's own spread ...
SPREAD_K      = 1.5      # ... times this
RADIUS_FLOOR  = 12       # ... never tighter than this (scanner noise on a flat material)
GROW_ITERS    = 2        # re-measure the material over its connected region this many times
MIN_RING_FRAC = 0.02     # a material must hold this much of the ring to be present on this page
DEEP_FRAC     = 0.75     # the deep part of the search window, used to re-run the calibration's
COLLAPSE_MIN  = 3.0      # collapse test on THIS page (see page_materials)
                         # PER-PAGE REFINEMENT IS THE POINT. The issue-wide bed sits at L26, but
                         # a scan's bed and that same scan's blackest INK are different colours:
                         # measured on p069, bed L20.0 against ad ink L39.7. One fixed threshold
                         # can never split those (across the issue the two distributions overlap
                         # completely: bed L5-51, ink L15-45); the same page's own ring splits
                         # them easily. This is why the full-bleed dark pages were "irreducible".
N_CAND        = 12       # ALL the backing->page transitions in the window (up to this many),
                         # not the first few. Taking the FIRST transitions biases the histogram
                         # toward the border: any texture starting at the page edge then yields
                         # a spurious peak, which is how p005's right edge -- the green comic
                         # running full-bleed, no bed at all -- produced a "line" at d=17 with
                         # 0.63 agreement. With every transition offered, a screen gives
                         # scattered candidates and no dominant peak, and a real bed edge still
                         # gives one; the fit then tells bed from texture by itself.
MIN_DEPTH_600 = 3        # ignore transitions shallower than this (a flush paper edge)
MIN_RUN_600   = 8        # a candidate needs this much backing before it and page after it
RUN_FRAC      = 0.7      # ... of which this fraction must match (grain tolerance, see below)

# --- step 2: the shared robust fit ------------------------------------------------------------------
SLOPE_MAX_DEG = 1.1      # DERIVED: the sheet edge is straight, so in the raw frame its tilt IS
                         # the page skew -- measured over 176 pages: median 0.13, p95 0.34,
                         # max 0.78 deg. Steeper is a lock onto tilted content.
BACKING_PURITY = 0.90    # a DEEPER line is only accepted if this fraction of what it encloses
                         # is actually backing. Votes alone do not justify going deeper: a deep
                         # line inside the page collects them too (p015's top jumped 20 -> 395px
                         # cutting content). p001's extra region is transition blur + bed strip,
                         # i.e. all backing, so it qualifies; page content does not. This is
                         # rule 1 stated directly -- extend the cut only over real backing.
DEEPEST_FRAC  = 0.60     # among lines reaching this fraction of the best line's agreement,
                         # take the DEEPEST -- see linefit.fit(prefer_deepest). p001's bottom
                         # carries two real boundaries (insert, then a 6px bed strip past a
                         # transition blur) and the plain mode picks the shallower one.
VOTE_TOL_600  = 6        # a line agrees with the fit if a candidate is within this
CURVE_MAX_600 = 40       # max bow across the range the curve is APPLIED to (the sheet bows in
                         # the scanner: 8-13px measured along an edge)

# --- step 3: margin and decision (kept out of the fit) ----------------------------------------------
OVERCUT_600   = int(os.environ.get("BM_OVERCUT", 4))
MIN_BACKING_FRAC = 0.15  # cut only if this fraction of lines shows any backing; below it the
                         # edge is clean page (p015's right edge is paper to the border, and a
                         # cut there destroys content nothing downstream can recover)
MIN_CONTRAST  = 10.0     # ... and the winning line must stand out from the typical line by
                         # this factor (linefit's peak contrast). This REPLACES a vote-fraction
                         # gate, which measured nothing: with ~10 candidates per line an
                         # arbitrary offset agrees with 50-90% of lines by chance, so a screened
                         # edge carrying no boundary scored 0.66 while p001's real insert edge
                         # scored 0.45 and was thrown away. Measured over the issue the two
                         # classes are far apart in contrast -- real boundaries 12-7000, the
                         # scattered kind 1-6.
MIN_VOTE_FRAC = 0.20     # a floor only, to keep linefit's deepest-preference from selecting a
                         # line almost no scanline supports.
SCREEN_BOX_600 = 7       # band-pass window; the ~150lpi screen period is 4px @600dpi
SCREEN_MAX    = 13       # a REGION whose band-pass energy exceeds this is printed ink, not
                         # backing (p047's ad ~29; bed and cardboard 2-10). Judged over the
                         # region, NEVER per pixel: at a boundary it measures the boundary,
                         # which is what rejected p001's 6px strip (18.9) and its blur (25.3).

EDGES = ("top", "bottom", "left", "right")


# ---------------------------------------------------------------------------------------------------
def screen_energy(lum, dpi):
    """Band-pass RMS: how much halftone screen a pixel sits in."""
    b = max(3, round(SCREEN_BOX_600 * dpi / 600))
    hp = lum - ndi.uniform_filter(lum, b)
    return np.sqrt(np.maximum(ndi.uniform_filter(hp * hp, b), 0))


def _orient1(a, edge, dtb, dlr, H, W):
    """axis0 = along the edge, axis1 = depth inward from the border (extra axes preserved)."""
    if edge == "top":    return a[:dtb].swapaxes(0, 1)
    if edge == "bottom": return a[H - dtb:][::-1].swapaxes(0, 1)
    if edge == "left":   return a[:, :dlr]
    if edge == "right":  return a[:, W - dlr:][:, ::-1]


def _deorient(mask_edge, edge, H, W, dtb, dlr):
    m = np.zeros((H, W), bool)
    if edge == "top":      m[:dtb]        = mask_edge.T
    if edge == "bottom":   m[H - dtb:]    = mask_edge.T[::-1]
    if edge == "left":     m[:, :dlr]     = mask_edge
    if edge == "right":    m[:, W - dlr:] = mask_edge[:, ::-1]
    return m


def page_materials(rgb_edge, edge, profile, dpi):
    """The backing materials PRESENT ON THIS PAGE at this edge, refined to this page's colours.

    profile gives each material's issue-wide centre and a generous radius. On this page we look
    at the border ring only, take the densest colour peak inside that radius, and measure the
    peak's own spread -- so the accepted colour becomes as tight as the material actually is
    here. That tightness is what tells the bed from the page's own black ink.

    Returns [(centre, radius), ...]; empty if this edge shows no backing on this page.
    """
    ring = max(2, round(RING_600 * dpi / 600))
    r = rgb_edge[:, :ring].reshape(-1, 3)
    out = []
    for m in profile.get(edge, []):
        if not m.get("backing"):
            continue
        c0, rad = np.array(m["centre"], np.float32), float(m["radius"])
        sel = r[np.abs(r - c0).max(1) <= rad]
        if sel.shape[0] < MIN_RING_FRAC * r.shape[0]:
            continue                                   # material absent from this page's edge
        q = (sel // SEED_STEP).astype(np.int32)
        key = q[:, 0] * 4096 + q[:, 1] * 64 + q[:, 2]
        u, cnt = np.unique(key, return_counts=True)
        k = int(u[int(np.argmax(cnt))])
        peak = np.array([(k // 4096) * SEED_STEP, ((k // 64) % 64) * SEED_STEP,
                         (k % 64) * SEED_STEP], np.float32) + SEED_STEP / 2
        near = sel[np.abs(sel - peak).max(1) <= max(RADIUS_FLOOR * 2, SEED_STEP * 3)]
        if near.shape[0] < 32:
            near = sel
        centre = np.median(near, 0)
        spread = float(np.percentile(np.abs(near - centre).max(1), SPREAD_PCTL))
        radius = float(np.clip(SPREAD_K * spread, RADIUS_FLOOR, rad))

        # GROW THE MATERIAL TO ITS OWN EXTENT. The ring is the most evenly lit part of the
        # backing; deeper in, where the sheet lifts off the platen, the same cardboard is
        # shadowed and falls outside a tolerance derived from the ring alone. Measured on p015's
        # bottom that truncated the insert at 41px in shadowed columns against 135px in lit ones,
        # and the "boundary" wobbled +-45px -- which is what destroyed the fit, not any real
        # waviness (the scan shows a clean straight edge there).
        # Re-measure the colour over the region actually CONNECTED to the border, twice. The
        # issue-wide cluster radius stays the hard cap, so this can widen to cover a gradient but
        # never wander off the material the calibration found.
        # THE COLLAPSE TEST THE CALIBRATION USES, NOW ON THIS PAGE, AND IT IS ALSO WHAT STOPS THE
        # GROWTH. A colour matching the issue's backing is backing HERE only if it too stops at
        # the sheet edge. Ink that runs to the border keeps covering the deep band; bed cannot.
        # Without it, a page whose border ring IS ink refines the "bed" onto its own ad -- p069's
        # left ring peaked at L47 and the ad would have been cut as bed.
        # Growth must obey the same rule. Grown blindly, p069's TOP merged its 30px flat-black bed
        # strip into the textured near-black ad below it, the merged material no longer collapsed,
        # and the edge was dropped with the strip left standing. So: keep the WIDEST tolerance
        # that still collapses, and never a wider one.
        deep = rgb_edge[:, int(DEEP_FRAC * rgb_edge.shape[1]):]

        def collapses(c, rr):
            cov_ring = float((np.abs(r - c).max(1) <= rr).mean())
            cov_deep = float((np.abs(deep - c).max(2) <= rr).mean())
            return (cov_ring + 1e-6) / (cov_deep + 1e-6) >= COLLAPSE_MIN

        best = (centre, radius) if collapses(centre, radius) else None
        for _ in range(GROW_ITERS):
            if best is None:
                break
            m = np.abs(rgb_edge - centre).max(2) <= radius
            lab, nl = ndi.label(m)
            if nl:
                keep = np.unique(lab[:, 0])                    # components touching the border
                m &= np.isin(lab, keep[keep > 0])
            if m.sum() < 64:
                break
            px = rgb_edge[m]
            centre = np.median(px, 0)
            spread = float(np.percentile(np.abs(px - centre).max(1), SPREAD_PCTL))
            radius = float(np.clip(SPREAD_K * spread, RADIUS_FLOOR, rad))
            if not collapses(centre, radius):
                break                                          # grew into the page: keep `best`
            best = (centre, radius)
        if best is not None:
            out.append(best)
    return out


def page_colours(profile, edge):
    """The clusters the calibration judged to be PAGE (the paper): centre, radius."""
    return [(np.array(m["centre"], np.float32), float(m["radius"]))
            for m in profile.get(edge, []) if not m.get("backing")]


def is_backing(rgb, mats):
    """Positive material test: within tolerance of one of this page-edge's backing colours."""
    m = np.zeros(rgb.shape[:2], bool)
    for centre, rad in mats:
        m |= np.abs(rgb - centre).max(2) <= rad
    return m


def candidates(back, dpi):
    """Step 1: up to N_CAND backing->page transition depths per line (-1 = unused)."""
    N, D = back.shape
    md = max(2, round(MIN_DEPTH_600 * dpi / 600))
    # A CANDIDATE IS A BOUNDARY BETWEEN TWO SUSTAINED RUNS, not a pixel flip. The cardboard
    # insert has visible grain, so a bare flip test fires all through it and the candidates
    # scatter: measured over the issue, the bottom edge's peak contrast came out 1.2-1.8 (the
    # true boundary standing out no better than any other depth) while the smooth bed gave
    # 13-286. Requiring backing before AND page after for RUN px removes the grain, and unlike
    # the old first-transition walk it introduces no bias toward the border.
    run = max(2, round(MIN_RUN_600 * dpi / 600))
    cs = np.concatenate([np.zeros((N, 1), np.int32),
                         np.cumsum(back.astype(np.int32), 1)], 1)      # (N, D+1)
    d = np.arange(D)[None, :]
    lo = np.maximum(d - run + 1, 0)
    before = np.take_along_axis(cs, d + 1, 1) - np.take_along_axis(cs, lo, 1)
    hi = np.minimum(d + 1 + run, D)
    after = np.take_along_axis(cs, hi, 1) - np.take_along_axis(cs, d + 1, 1)
    trans = np.zeros_like(back)
    trans[:, :-1] = back[:, :-1] & ~back[:, 1:]          # last backing px before page
    # MAJORITY, not unanimity: the cardboard's grain and the odd speck knock single pixels out
    # of the (deliberately tight) per-page colour tolerance, and an all-or-nothing run test then
    # rejected the insert boundary outright -- the bottom edge's backing_frac fell from 0.99 to
    # 0.09 and every insert cut was lost.
    trans &= (before >= RUN_FRAC * np.minimum(run, d + 1)) & (after <= (1 - RUN_FRAC) * run)
    trans &= np.arange(D)[None, :] >= md
    out = np.full((N, N_CAND), -1.0)
    rows = np.arange(N)
    for k in range(N_CAND):
        has = trans.any(1)
        first = np.where(has, trans.argmax(1), 0)
        out[:, k] = np.where(has, first + 1.0, -1.0)
        trans[rows[has], first[has]] = False              # consume it, look for the next
    return out


def analyze_edge(rgb, lum, edge, dpi, H, W, dtb, dlr, profile):
    """Return (cut_depth per line, decision, metrics)."""
    E = _orient1(rgb, edge, dtb, dlr, H, W)
    L = _orient1(lum, edge, dtb, dlr, H, W)
    D = L.shape[1]
    mats = page_materials(E, edge, profile, dpi)
    if not mats:
        return np.zeros(L.shape[0]), "CLEAN(no backing)", dict(
            backing_frac=0.0, vote_frac=0.0, slope=0.0, angle_deg=0.0,
            median_depth=0.0, ink=0.0, purity=0.0, mats=0, contrast=0.0)
    back = is_backing(E, mats)
    # What we may enclose is backing OR the sheet-edge blur between backing and paper -- what it
    # must NOT contain is PAGE. Testing "is backing" instead was too strict once the per-page
    # colour radius tightened: the blur stopped counting as backing and every real bed wedge was
    # rejected as MIXED. The page colours come from the same calibration.
    notpage = ~is_backing(E, page_colours(profile, edge))
    cand = candidates(back, dpi)
    N = L.shape[0]
    yy = np.arange(N, dtype=np.float64) - N / 2.0
    idx = np.arange(D)[None, :]

    def _pure(offset, slope):
        """Is what this line encloses predominantly backing? (see BACKING_PURITY)"""
        ln = np.clip(offset + slope * yy, 0, D)
        inside = idx < ln[:, None]
        n = int(inside.sum())
        return n > 0 and float(notpage[inside].mean()) >= BACKING_PURITY

    line, vote_frac, sl, contrast = linefit.fit(cand, tol=max(2.0, VOTE_TOL_600 * dpi / 600),
                                      slope_max_deg=SLOPE_MAX_DEG,
                                      curve_max=CURVE_MAX_600 * dpi / 600,
                                      prefer_deepest=DEEPEST_FRAC,
                                      min_vote_frac=MIN_VOTE_FRAC,
                                      accept=_pure)
    line = np.clip(line, 0, D)

    backing_frac = float((cand >= 0).any(1).mean())
    Sc = screen_energy(L, dpi)
    sel = (np.arange(D)[None, :] < line[:, None]) & back
    ink = float(np.median(Sc[sel])) if sel.any() else 0.0

    m = dict(backing_frac=backing_frac, vote_frac=vote_frac, slope=float(sl),
             angle_deg=float(np.rad2deg(np.arctan(sl))),
             median_depth=float(np.median(line)), ink=ink, mats=len(mats),
             contrast=float(min(contrast, 1e6)),
             mat_colours=[[round(float(x)) for x in c] + [round(r)] for c, r in mats])

    # What we are about to cut must actually BE backing. Without this the halftone's dark
    # dots pass the blackish test on most lines and yield a consistent shallow "boundary":
    # p005's right edge is the green comic running full-bleed, no bed at all, and it cut 17px
    # of it (backing_frac 0.93, vote 0.64, ink 8.4 -- under every other test). Purity is
    # rule 1 and rule 2 stated together: cut backing, and only backing.
    _in = np.arange(D)[None, :] < line[:, None]
    m["purity"] = float(notpage[_in].mean()) if _in.any() else 0.0
    if backing_frac < MIN_BACKING_FRAC:
        return np.zeros(L.shape[0]), "CLEAN(no backing)", m
    if m["purity"] < BACKING_PURITY:
        return np.zeros(L.shape[0]), "MIXED(not backing)", m
    if contrast < MIN_CONTRAST:
        return np.zeros(L.shape[0]), "LOW(no line)", m
    if ink >= SCREEN_MAX:
        return np.zeros(L.shape[0]), "INK(screened)", m
    return np.clip(line + round(OVERCUT_600 * dpi / 600), 0, D), "CUT", m


def load_profile(path=None):
    """The issue's measured backing materials (calibrate_backing.py)."""
    path = path or os.environ.get("BM_PROFILE") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "backing_profile.json")
    with open(path) as f:
        return json.load(f)["edges"]


def bed_matte(rgb, dpi, priors=None, page_no=None, return_meta=False, profile=None):
    """Matte one page.

    `priors` / `page_no` are accepted for call compatibility and UNUSED: the decision is made
    from the edge itself. The learned-prior acceptance path is gone -- it existed to rescue
    low-confidence edges by matching a per-issue typical depth, and it is what let a
    0.7%-backing edge on p015 be accepted and cut 35mm of clean paper.
    """
    if profile is None:
        profile = load_profile()
    a = np.asarray(rgb)[..., :3].astype(np.float32)
    H, W, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    dtb, dlr = int(WIN_TB_FRAC * H), int(WIN_LR_FRAC * W)

    mask = np.zeros((H, W), bool)
    meta = {}
    for edge in EDGES:
        D = dtb if edge in ("top", "bottom") else dlr
        cut, decision, m = analyze_edge(a, lum, edge, dpi, H, W, dtb, dlr, profile)
        m["decision"] = decision
        m["cut_px"] = float(np.median(cut))
        meta[edge] = m
        if decision == "CUT":
            mask |= _deorient(np.arange(D)[None, :] < cut[:, None], edge, H, W, dtb, dlr)

    rgba = np.dstack([a.astype(np.uint8), np.where(mask, 0, 255).astype(np.uint8)])
    return (rgba, 100.0 * mask.mean(), meta) if return_meta else (rgba, 100.0 * mask.mean())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("out", nargs="?")
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--page", type=int)
    ap.add_argument("--magenta", action="store_true", help="50%% magenta over the cut regions")
    ap.add_argument("--priors", help="accepted and ignored (call compatibility)")
    A = ap.parse_args()
    rgba, pct, meta = bed_matte(Image.open(A.img).convert("RGB"), A.dpi,
                                page_no=A.page, return_meta=True)
    print("%s: bed cleared %.3f%%" % (A.img, pct))
    for e in EDGES:
        m = meta[e]
        print("   %-7s %-18s depth %6.1f  backing %.2f  vote %.2f  ctr %5.1f  ink %5.1f  ang %+.2f  mats %s"
              % (e, m["decision"], m["median_depth"], m["backing_frac"],
                 m["vote_frac"], m["contrast"], m["ink"], m["angle_deg"], m.get("mat_colours", [])))
    if A.out:
        if A.magenta:
            f = rgba.astype(np.float32); cut = f[..., 3] == 0
            out = f[..., :3]
            out[cut] = 0.5 * out[cut] + 0.5 * np.array([255, 0, 255], np.float32)
            Image.fromarray(out.astype(np.uint8)).save(A.out)
        else:
            Image.fromarray(rgba, "RGBA").save(A.out)
