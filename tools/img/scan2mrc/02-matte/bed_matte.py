#!/usr/bin/env python3
"""Bed matte: clear the scanner-bed backing (lid black + backing sheet + colored inserts) as unknown
(alpha 0) at each page edge, without cutting page content.

NEW ALGORITHM (single unified backing run per edge -- replaces the old brittle two-path dark/insert
version). Per edge (top/bottom/left/right), the array is oriented so axis1 runs from the BORDER inward.

  1. UNIFIED BACKING PROFILE d[x].  PAGE = light+neutral (luma>PAGE_LUMA AND saturation<PAGE_SAT,
     saturation = max-min channel). d[x] = index of the FIRST page pixel from the border. The run
     [0,d[x]) is the backing candidate and may be a MIX of black bed AND yellow insert AND their
     transition -- it is treated as ONE run (this is what fixes the p071 composite: yellow then a thin
     black shadow stripe then page -- the old insert path stopped at the end of the yellow and left the
     black stripe). A line is "backing" if its run is non-page and roughly uniform, measured as: a high
     fraction of run pixels are each dark-neutral OR saturated (NONPAGE_FRAC). We deliberately do NOT
     gate on raw luma std, because a genuine yellow+black composite run has a huge luma std yet is all
     backing; the non-page fraction is the correct "one uniform backing run" test. Flush column ->
     page at the border -> d=0 (not backing). Full-bleed column -> no page found in the window -> d
     marked "no page" (excluded from containment; counts against confidence).

  2. BRUTE-FORCE STRAIGHT CUT LINE over (slope,height). For a line L[x]=height+slope*(x-x_center):
       page_cut(L)     = sum over non-nopage cols of max(0, L[x]-d[x])   (page pixels cut -> MINIMIZE)
       backing_left(L) = sum over backing cols   of max(0, d[x]-L[x])   (backing left behind -> tiny)
     For each slope we pick the SMALLEST height whose backing_left <= SLACK*total_backing (page_cut
     grows with height, backing_left shrinks with height, so the smallest feasible height minimizes
     page_cut for that slope), then keep the slope with the least page_cut. Exact & cheap on the 1-D
     profile. Soft containment => a deep content-black outlier (e.g. p089 schematic ~558px vs the bar
     ~60px) is LEFT automatically because containing it would cost far too much page_cut. The cut is
     every pixel above the line over the whole edge (a couple px overcut into page margin is fine).

  3. CONFIDENCE. HIGH iff (a) solid neutral PAGE just beyond the cut line across the full width
     (>=BEYOND_PAGE_FRAC clean), AND (b) the best line's page_cut is ~0 relative to the backing
     (<=PAGECUT_FRAC*total_backing -- a straight line contains the backing cheaply), AND (c) enough
     backing columns (>=MIN_BACKING_FRAC) with few full-bleed no-page columns (<=MAX_NOPAGE_FRAC).
     LOW = full-bleed (no page beyond, or many no-page cols), crowded/jagged (large page_cut), unusual.

TWO-PASS: WITHOUT --priors this runs in PASS-1 MODE and cuts ONLY high-confidence edges (ambiguous
edges are left for pass 2). WITH --priors it runs in PASS-2 MODE: it additionally accepts a LOW-conf
edge whose candidate depth/angle match the learned typical for that edge+parity, and REJECTS an
atypically-deep candidate (full-bleed). Pass-2 is built but lightly tested; pass-1 is the deliverable.
"""
import argparse, json, numpy as np, scipy.ndimage as ndi
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------------------------------
# MAGIC CONSTANTS (all resolution-relative constants are given @600dpi and scaled by dpi/600)
# ---------------------------------------------------------------------------------------------------
WIN_TB_FRAC   = 0.08     # top/bottom search-window depth as a fraction of image HEIGHT
WIN_LR_FRAC   = 0.16     # left/right  search-window depth as a fraction of image WIDTH (bars are wide)

PAGE_LUMA     = 120      # PAGE (paper) is LIGHT: luma above this ...
PAGE_SAT      = 40       # ... AND NEUTRAL: saturation (max-min channel) below this. Yellow/blue backing
                         #     is saturated -> not page; black bed is dark -> not page.
# --- POSITIVE BED TEST (replaces "page = light+neutral, backing = the rest") ---------------------
# The old test defined PAGE as light AND neutral and took the first page pixel as the backing depth.
# On a FULL-BLEED page there is no such pixel anywhere in the window, so every column read as
# "no page" -> full-bleed -> LOW confidence -> the edge was left uncut. That is why p001 (dark teal
# cover, sat 106) and p003 (black block) kept their bed. We now detect the BED POSITIVELY. Measured
# medians (600-dpi thumbs):
#     bed              L 31-44   sat  2-3    screen  6-10
#     yellow insert    L 192     sat 137     screen  2.2
#     p001 teal cover  L 128     sat 120     screen 14.6   <- kept by luma+sat
#     p005 halftone    L  41     sat  40     screen  8.4   <- kept by SAT alone
#     p047 dark ad     L  39     sat   7     screen 29.1   <- kept by SCREEN alone
# All three terms are load-bearing: no two of them separate all of these cases.
BED_LUMA      = 55       # bed is VERY dark ...
BED_SAT       = 12       # ... and VERY neutral (this is what keeps p005's green halftone, sat 40) ...
SCREEN_MAX    = 13       # ... and UNSCREENED. Printed ink carries the halftone; the scanner backing
                         #     and the cardboard insert do not. Band-pass energy (L minus a 7px box
                         #     mean, RMS over 7px) -- the only term that keeps p047's dark ad (29).
INSERT_LUMA   = 150      # a COLOURED INSERT (cardboard) is also BRIGHT. Without this the solid teal
                         #     of p001's cover (L 104, sat 103, unscreened at the top edge where it is
                         #     a flat band) is indistinguishable from the yellow cardboard (L 192,
                         #     sat 137) and the whole cover reads as backing. A dark saturated region
                         #     is printed ink, not backing. NB: calibrated on this issue's yellow
                         #     insert -- a genuinely DARK coloured insert would need this re-measured.
SCREEN_BOX_600 = 7       # band-pass window @600dpi; ~the 150-lpi screen period is 4px there
DARK_LUMA     = 70       # a backing-run pixel counts as "dark-neutral" if luma < this ...
DARK_SAT      = 40       # ... and saturation < this (neutral). Covers lid black + backing sheet + shadow.
SAT_BACK      = 60       # a backing-run pixel counts as "saturated" (colored insert) if saturation >= this.
NONPAGE_FRAC  = 0.85     # a line is BACKING if >= this fraction of its run pixels are each dark-neutral
                         #     OR saturated (i.e. non-page). Yellow+black composite passes (~1.0); a run
                         #     riddled with mid-tone content pixels fails.
MIN_DEPTH_600 = 3        # ignore runs shallower than this (a flush paper edge, not backing) @600dpi

SLOPE_MAX_DEG  = 4.0     # brute-force slope range for the straight cut line (+- this many degrees)
SLOPE_STEP_DEG = 0.05    # slope grid step
SLACK          = 0.01    # backing_left budget as a fraction of the CORE-backing depth (cover ~all backing)
OUTLIER_K      = 3.0     # containment: within the de-sloped frame, backing columns whose depth exceeds
                         #     median + OUTLIER_K*1.4826*MAD are treated as deep CONTENT outliers and are
                         #     EXCLUDED from the coverage constraint (so a black content box touching the
                         #     edge, e.g. p005 bottom, is LEFT while the bulk yellow is still covered
                         #     tightly). A widening bar is a LINEAR ramp -> uniform after de-sloping ->
                         #     small MAD -> NOT excluded -> fully covered.
OVERCUT_600    = 2       # push the accepted line this many px past the backing (minimise white cut) @600

BEYOND_600       = 30    # depth of the "just beyond the cut" band used for the page-beyond test @600dpi
BEYOND_PAGE_FRAC = 0.50  # HIGH-conf (a): >= this fraction of that beyond-band (full width) must be PAGE
SAT_DOMINANT     = 0.60  # HIGH-conf (a) is ALSO satisfied if the backing runs are dominantly SATURATED
                         #     (median saturated-fraction >= this): a colored insert (yellow/blue) is proven
                         #     backing by its saturation, so clean page just beyond is not required -- this
                         #     rescues crowded yellow bottoms (p030) where content sits right above the yellow.
PAGECUT_FRAC     = 0.15  # HIGH-conf (b): page_cut <= this * total_backing (line contains backing cheaply)
MIN_BACKING_FRAC = 0.15  # HIGH-conf (c): >= this fraction of columns are backing
MAX_NOPAGE_FRAC  = 0.15  # HIGH-conf (c): <= this fraction of columns are full-bleed (no page in window)

PRIOR_DEPTH_TOL  = 0.60  # PASS-2: accept a low-conf edge if |depth-median|/median <= this (depth match)
PRIOR_ANGLE_TOL  = 2.0   # PASS-2: ... and |angle-median| <= this many degrees
PRIOR_REJECT_MUL = 1.8   # PASS-2: REJECT (never cut) a candidate deeper than this * learned median depth

MARGIN_600    = 1        # perpendicular safety dilation @600dpi

EDGES = ("top", "bottom", "left", "right")


# ---------------------------------------------------------------------------------------------------
def screen_energy(lum, dpi):
    """Band-pass RMS: how much halftone screen this pixel sits in.

    Printed ink is screened; the scanner backing and the cardboard insert are not. This is the
    only signal that separates a full-bleed DARK NEUTRAL ad (p047: screen 29) from the bed
    (screen 6-10), since those two are identical in luma and saturation."""
    b = max(3, round(SCREEN_BOX_600 * dpi / 600))
    hp = lum - ndi.uniform_filter(lum, b)
    return np.sqrt(np.maximum(ndi.uniform_filter(hp * hp, b), 0))


def _orient1(a, edge, dtb, dlr, H, W):
    if edge == "top":    return a[:dtb].T
    if edge == "bottom": return a[H-dtb:][::-1].T
    if edge == "left":   return a[:, :dlr]
    if edge == "right":  return a[:, W-dlr:][:, ::-1]


def _orient(lum, sat, edge, dtb, dlr, H, W, scr=None):
    """Return (L,S[,Sc]) with axis0 = along-edge (line index x), axis1 = depth from the border."""
    L = _orient1(lum, edge, dtb, dlr, H, W)
    S = _orient1(sat, edge, dtb, dlr, H, W)
    if scr is None:
        return L, S
    return L, S, _orient1(scr, edge, dtb, dlr, H, W)


def _deorient(mask_edge, edge, H, W, dtb, dlr):
    """Scatter an edge-oriented cut mask (N,D) back into a full (H,W) image mask."""
    m = np.zeros((H, W), bool)
    if edge == "top":    m[:dtb]      = mask_edge.T
    if edge == "bottom": m[H-dtb:]    = mask_edge.T[::-1]
    if edge == "left":   m[:, :dlr]   = mask_edge
    if edge == "right":  m[:, W-dlr:] = mask_edge[:, ::-1]
    return m


def _profile(L, S, dpi, Sc=None):
    """Step 1: per-line backing profile. Return d (first-page depth), backing mask, nopage mask.

    PAGE is now "not backing" under the positive bed/insert test (see BED_LUMA), so a full-bleed
    dark or saturated page still yields a page pixel and the edge is analysable."""
    N, D = L.shape
    min_depth = max(2, round(MIN_DEPTH_600 * dpi / 600))
    if Sc is None:
        page = (L > PAGE_LUMA) & (S < PAGE_SAT)
    else:
        unscreened = Sc < SCREEN_MAX
        is_bed    = (L < BED_LUMA) & (S < BED_SAT) & unscreened
        is_insert = (S >= SAT_BACK) & unscreened & (L >= INSERT_LUMA)   # bright smooth cardboard
        page = ~(is_bed | is_insert)
    haspage = page.any(1)
    d = page.argmax(1)                                    # first page pixel; 0 if page at border
    idx = np.arange(D)[None, :]
    run = idx < np.where(haspage, d, 0)[:, None]          # the pre-page backing run
    nonpage = ((L < DARK_LUMA) & (S < DARK_SAT)) | (S >= SAT_BACK)   # dark-neutral OR saturated
    cnt = np.clip(np.where(haspage, d, 0), 1, None)
    npf = np.where(run, nonpage, 0).sum(1) / cnt          # fraction of run that is non-page
    satfrac = np.where(run, S >= SAT_BACK, 0).sum(1) / cnt  # fraction of run that is saturated (insert)
    backing = haspage & (d >= min_depth) & (npf >= NONPAGE_FRAC)
    nopage = ~haspage
    return d, backing, nopage, satfrac


def _brute_cut(d, backing, nopage, D, dpi):
    """Step 2: brute-force the best straight cut line. Return (cut_depth[N], metrics dict)."""
    N = len(d)
    x = np.arange(N, dtype=np.float64)
    xc = N / 2.0
    overcut = round(OVERCUT_600 * dpi / 600)
    d = d.astype(np.float64)

    db = d[backing]                                       # backing target depths
    total_backing = float(db.sum())
    cols_np = ~nopage                                     # columns with a known page depth
    d_np = d[cols_np]
    xb = x[backing]
    x_np = x[cols_np]

    slopes = np.tan(np.deg2rad(np.arange(-SLOPE_MAX_DEG, SLOPE_MAX_DEG + 1e-9, SLOPE_STEP_DEG)))
    best = None
    for sl in slopes:
        eb_raw = db - sl * (xb - xc)                      # backing depths in the rotated (de-sloped) frame
        # robust MAD fence: exclude deep content outliers (a black box touching the edge) from coverage,
        # but keep a uniform (or linearly-ramping, now de-sloped) backing band fully in the constraint.
        med = np.median(eb_raw); mad = np.median(np.abs(eb_raw - med))
        fence = med + OUTLIER_K * 1.4826 * mad
        eb = np.sort(eb_raw[eb_raw <= fence])             # core backing to be covered
        core_total = float(np.clip(eb, 0, None).sum())
        budget = SLACK * core_total
        if core_total <= 0 or len(eb) == 0:
            h = 0.0
        else:
            csum = np.concatenate(([0.0], np.cumsum(eb)))  # prefix sums of sorted core eb
            tot = csum[-1]
            # smallest h with backing_left(h)=sum(eb[eb>h])-h*count(eb>h) <= budget (decreasing in h)
            hs = np.unique(np.concatenate((eb, eb + 1))); hs = hs[hs >= 0]
            k = np.searchsorted(eb, hs, side="right")
            above = (tot - csum[k]) - hs * (len(eb) - k)
            ok = np.where(above <= budget)[0]
            h = float(hs[ok[0]]) if len(ok) else float(eb[-1])
        # page_cut at this (slope,h): page pixels cut over all columns with a known page depth
        e_np = d_np - sl * (x_np - xc)
        page_cut = float(np.clip(h - e_np, 0, None).sum())
        if best is None or page_cut < best[0]:
            best = (page_cut, sl, h)

    page_cut, sl, h = best
    cut_depth = np.clip(h + sl * (x - xc) + overcut, 0, D)
    metrics = dict(page_cut=page_cut, total_backing=total_backing, slope=float(sl),
                   angle_deg=float(np.degrees(np.arctan(sl))), height=float(h),
                   backing_frac=float(backing.mean()), nopage_frac=float(nopage.mean()),
                   n_backing=int(backing.sum()),
                   median_depth=float(np.median(d[backing])) if backing.any() else 0.0)
    return cut_depth, metrics


def _page_beyond(L, S, cut_depth, dpi, D, Sc=None):
    """Step 3(a): fraction of the band just beyond the cut line (full width) that is clean PAGE.

    Uses the SAME page definition as _profile. With the old light+neutral test this returned ~0 on
    a full-bleed page -- the teal beyond p001's bed is page, but it is neither light nor neutral --
    so the edge could never reach HIGH confidence and was never cut."""
    beyond = max(3, round(BEYOND_600 * dpi / 600))
    idx = np.arange(D)[None, :]
    lo = np.clip(cut_depth.astype(int), 0, D - 1)
    hi = np.clip(cut_depth.astype(int) + beyond, 0, D)
    band = (idx >= lo[:, None]) & (idx < hi[:, None])
    if Sc is None:
        page = (L > PAGE_LUMA) & (S < PAGE_SAT)
    else:
        unscreened = Sc < SCREEN_MAX
        page = ~(((L < BED_LUMA) & (S < BED_SAT) & unscreened)
                 | ((S >= SAT_BACK) & unscreened & (L >= INSERT_LUMA)))
    return float((page & band).sum() / max(1, band.sum()))


def _confidence(metrics):
    """Step 3: HIGH iff (clean page beyond OR saturated insert), cheap containment, enough backing."""
    a = (metrics["page_beyond"] >= BEYOND_PAGE_FRAC) or (metrics["sat_frac"] >= SAT_DOMINANT)
    tb = max(1.0, metrics["total_backing"])
    b = metrics["page_cut"] <= PAGECUT_FRAC * tb
    c = (metrics["backing_frac"] >= MIN_BACKING_FRAC) and (metrics["nopage_frac"] <= MAX_NOPAGE_FRAC)
    return "HIGH" if (a and b and c) else "LOW"


def analyze_edge(lum, sat, edge, dpi, H, W, dtb, dlr, scr=None):
    """Full per-edge analysis: returns (cut_depth, confidence, metrics). Pure measurement, no policy."""
    L, S, Sc = _orient(lum, sat, edge, dtb, dlr, H, W, scr=scr)
    D = L.shape[1]
    d, backing, nopage, satfrac = _profile(L, S, dpi, Sc)
    if backing.sum() == 0:
        m = dict(page_cut=0.0, total_backing=0.0, slope=0.0, angle_deg=0.0, height=0.0,
                 backing_frac=0.0, nopage_frac=float(nopage.mean()), n_backing=0,
                 median_depth=0.0, page_beyond=0.0, sat_frac=0.0)
        return np.zeros(L.shape[0]), "NONE", m
    cut_depth, m = _brute_cut(d, backing, nopage, D, dpi)
    m["page_beyond"] = _page_beyond(L, S, cut_depth, dpi, D, Sc)
    m["sat_frac"] = float(np.median(satfrac[backing]))
    conf = _confidence(m)
    return cut_depth, conf, m


# ---------------------------------------------------------------------------------------------------
def bed_matte(rgb, dpi, priors=None, page_no=None, return_meta=False):
    """Matte one page. PASS-1 (priors=None): cut only HIGH-confidence edges. PASS-2 (priors given):
    also accept low-conf edges matching the learned typical, and reject atypically-deep candidates."""
    a = np.asarray(rgb)[..., :3].astype(np.float32); H, W, _ = a.shape
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = a.max(2) - a.min(2)
    scr = screen_energy(lum, dpi)
    dtb = int(WIN_TB_FRAC * H); dlr = int(WIN_LR_FRAC * W)
    parity = None if page_no is None else ("even" if page_no % 2 == 0 else "odd")

    mask = np.zeros((H, W), bool); meta = {}
    for edge in EDGES:
        D = dtb if edge in ("top", "bottom") else dlr
        cut_depth, conf, m = analyze_edge(lum, sat, edge, dpi, H, W, dtb, dlr, scr=scr)
        apply = (conf == "HIGH")
        decision = conf
        if priors is not None and conf != "HIGH" and m["n_backing"] > 0:
            pri = _lookup_prior(priors, edge, parity)
            if pri and pri.get("count", 0) >= 3:
                med, ang = pri["median_depth"], pri["median_angle"]
                if m["median_depth"] > PRIOR_REJECT_MUL * med:
                    apply, decision = False, "REJECT(deep)"     # atypically deep -> full-bleed -> leave
                elif med > 0 and abs(m["median_depth"] - med) / med <= PRIOR_DEPTH_TOL \
                        and abs(m["angle_deg"] - ang) <= PRIOR_ANGLE_TOL \
                        and ((m["page_beyond"] >= BEYOND_PAGE_FRAC) or (m["sat_frac"] >= SAT_DOMINANT)):
                    apply, decision = True, "PRIOR"             # matches learned typical AND has bed
                    #     evidence (clean PAGE just beyond, OR a saturated insert) -> accept. Without this
                    #     evidence gate the depth/angle match alone clips the dark top row of a full-bleed
                    #     image (p047 star, p005 halftone, p163 photo) whose depth happens to match the
                    #     top-wedge prior; requiring page-beyond leaves those (they are content, rule 3).
        if apply and cut_depth.max() > 0:
            edge_mask = np.arange(D)[None, :] < cut_depth[:, None]
            mask |= _deorient(edge_mask, edge, H, W, dtb, dlr)
        meta[edge] = dict(confidence=conf, decision=decision, cut_px=float(np.median(cut_depth)),
                          angle_deg=m["angle_deg"], **{k: m[k] for k in
                          ("page_cut", "total_backing", "backing_frac", "nopage_frac",
                           "n_backing", "median_depth", "page_beyond", "sat_frac")})

    mask = ndi.binary_dilation(mask, iterations=max(1, round(MARGIN_600 * dpi / 600)))
    rgba = np.dstack([a.astype(np.uint8), np.where(mask, 0, 255).astype(np.uint8)])
    pct = 100 * mask.mean()
    return (rgba, pct, meta) if return_meta else (rgba, pct)


def _lookup_prior(priors, edge, parity):
    node = priors.get(edge, {})
    if isinstance(node, dict) and parity in node:
        return node[parity]
    if isinstance(node, dict) and "median_depth" in node:
        return node
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("out"); ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--magenta", action="store_true", help="50%% magenta overlay on cut regions")
    ap.add_argument("--priors", help="priors.json -> PASS-2 mode (default: PASS-1, high-conf only)")
    ap.add_argument("--page", type=int, help="page number (for parity in pass-2)")
    A = ap.parse_args()
    priors = json.load(open(A.priors)) if A.priors else None
    rgba, pct, meta = bed_matte(Image.open(A.img).convert("RGB"), A.dpi, priors=priors,
                                page_no=A.page, return_meta=True)
    if A.magenta:
        f = rgba.astype(np.float32); cut = f[..., 3] == 0
        out = f[..., :3]; out[cut] = 0.5 * out[cut] + 0.5 * np.array([255, 0, 255], np.float32)
        Image.fromarray(out.astype(np.uint8)).save(A.out)
    else:
        Image.fromarray(rgba, "RGBA").save(A.out)
    mode = "PASS-2" if priors else "PASS-1"
    print(f"{A.img}: [{mode}] bed cleared {pct:.3f}% -> {A.out}")
    for e in EDGES:
        m = meta[e]
        print(f"   {e:6s} {m['decision']:12s} cut~{m['cut_px']:.0f}px ang={m['angle_deg']:+.2f} "
              f"pcut={m['page_cut']:.0f} tback={m['total_backing']:.0f} "
              f"bk={m['backing_frac']:.2f} nop={m['nopage_frac']:.2f} beyond={m['page_beyond']:.2f}")
