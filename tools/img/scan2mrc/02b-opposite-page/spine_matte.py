#!/usr/bin/env python3
"""02b spine / opposite-page matte (PRODUCTION, hardens the spine_v2.py prototype).

On the binding side of each split A3 scan the *neighbor* page bled in:
  even page: [ page content | clean inner margin | NEIGHBOR block | (border) ]  (neighbor near RIGHT border)
  odd  page: [ (border) | NEIGHBOR block | clean inner margin | page content ]  (neighbor near LEFT  border)

We find the SPINE line = the neighbor block's page-facing edge, and mark everything
BEYOND it (toward the binding, i.e. the neighbor) as alpha 0. Nothing on the current
page's side of the line is touched.

WINNING SIGNAL (from the 02b probe, see NOTES.md): the neighbor-content boundary --
ink density (dark_frac) + colour saturation step up together at the same x. The clean
inner margin is a band of ~0 dark / low sat; the neighbor block is a sharp jump. Gutter
shadow and staples are too weak in these flat scans to use as a primary locator.

HARDENING vs the prototype (this file supersedes spine_v2.py):
  * ANGLE CAP. The real spine is near-vertical after deskew (real slant <=~1 deg). We fit a
    straight line to the per-band boundary points with an outlier-resistant Theil-Sen; if the
    robust (unconstrained) fit tilts more than SPINE_ANGLE_MAX_DEG it is a FALSE lock onto a
    skewed neighbor IMAGE edge or a ragged coupon edge (the probe's p175 locked at -3.35 deg
    on a neighbor photo). Because a true spine essentially never exceeds the cap, an over-cap
    fit is treated as PROOF the boundary is not a spine -> the page is gated to LOW -> NO cut.
    We DO still constrain-refit the line to +-cap and report it for diagnostics (raw_tilt_deg
    vs tilt_deg), but we do NOT cut on it: masking a genuinely-tilted neighbor edge with a
    near-vertical line cannot both cover the neighbor and avoid eating the page margin at the
    divergent end, so leaving the whole strip for the later A4 crop is strictly safer than
    cutting at a wrong tilt. NOTES.md records this choice (reject-over-cap, chosen over
    constrained-refit-and-keep and over vertical-at-boundary-x).
  * CONFIDENCE GATE (HIGH/LOW like bed_matte). Cut only when there are enough evidence
    bands with a crisp neighbor boundary AND the fitted (capped) line has low residual.
    ~58% of pages are genuinely no-neighbor (clean margin to the border) -> LOW -> NO cut.

Detection runs on the 600-dpi thumb; full-res (2400) apply is done later in Rust by
scaling the fitted line x4. This module only measures + mattes the thumb.

CLI:  spine_matte.py IMG OUT --dpi N [--magenta] [--page P]
  writes an RGBA alpha matte (alpha 0 = neighbor/unknown); with --magenta writes a 50%
  magenta overlay over the cut region for visual judging. --page sets parity (else the
  leading integer of the filename is used).
"""
import argparse, json, re, numpy as np
from math import atan, tan, radians, degrees, copysign
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

# ---------------------------------------------------------------------------------------------------
# MAGIC CONSTANTS  (spatial constants are given @600dpi and scaled by dpi/600 so the tool is
#                   resolution-agnostic; NB / fractions / angles are dimensionless and NOT scaled)
# ---------------------------------------------------------------------------------------------------
INNER_W_600   = 1200    # width of the binding-side SEARCH band we look for the neighbor in (px @600)
NB            = 28       # number of horizontal bands the height is split into (one boundary pt each)

DARK_LUMA     = 95       # a pixel with luma < this is "dark/ink"
CONTENT_DARK  = 0.05     # a column with dark_frac  > this is "content" (ink)
CONTENT_SAT   = 0.17     # a column with sat_mean   > this is "content" (colour); sat = (max-min)/max in 0..1
SMOOTH_600    = 11       # column-profile smoothing kernel (px @600) -- tames single-column noise

CLEANRUN_600  = 70       # px of sustained clean columns that ends the neighbor block (@600)
BLOCKMIN_600  = 20       # the neighbor block must be at least this wide to count (@600) -- rejects specks
BORDER_NEAR_600 = 240    # the neighbor block must START within this many px of the binding border (@600);
                         #     a "content" block deeper than this is the page's OWN text -> reject the band
INTERIOR_GUARD_600 = 10  # if the block reaches this close to the interior edge of the search band it is a
                         #     full-bleed / merged block with no clean gap -> reject the band (@600)

SPINE_ANGLE_MAX_DEG = 1.5  # <<< ANGLE CAP. The deskewed spine slants <=~1 deg; anything steeper is a false
                         #     lock onto a skewed neighbor-image edge / ragged coupon. Fits over this are
                         #     constrain-refit to +-cap and re-checked; if still not a low-residual near-
                         #     vertical line the page is gated LOW (no cut). All ACCEPTED pages are <= this.
RESID_THR_600 = 45       # px residual: RANSAC inlier threshold AND the confidence residual gate (@600)
MIN_EVIDENCE_BANDS = 6   # need this many inlier boundary bands to trust a line (out of NB)
RANSAC_ITERS  = 4        # iterative Theil-Sen residual-reject passes

OVERCUT_600   = 6        # push the cut this many px PAST the boundary toward the PAGE (@600), so the whole
                         #     neighbor is removed; a few px of the page's own inner margin under the matte
                         #     is fine (the A4 crop trims it anyway). We never cut a full content column.
MARGIN_600    = 1        # perpendicular safety dilation of the cut mask (@600)


# ---------------------------------------------------------------------------------------------------
def _scale(v600, dpi):
    return max(1, round(v600 * dpi / 600))

def _is_even(page_no):
    return page_no % 2 == 0

def _page_no_from_name(name):
    m = re.search(r'(\d+)', name)
    return int(m.group(1)) if m else 0

def _sm(a, k):
    return np.convolve(a, np.ones(k) / k, mode='same')


def _col_signals(sub):
    """sub: H x W x 3 slice. Return per-column dark_frac and sat_mean over the band height."""
    rgb = sub.astype(np.float32)
    luma = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1)
    sat = np.where(mx > 1, (mx - mn) / np.maximum(mx, 1), 0)
    return (luma < DARK_LUMA).mean(0), sat.mean(0)


def _band_boundary(content, even, dpi):
    """content: bool over the INNER_W search columns in ABSOLUTE-x order (index 0 = interior-most
    of the search band, index -1 = binding border). Return the spine x in search-band coords =
    the page-facing edge of the neighbor block nearest the border, or None if this band gives no
    trustworthy boundary."""
    n = len(content)
    cleanrun  = _scale(CLEANRUN_600, dpi)
    blockmin  = _scale(BLOCKMIN_600, dpi)
    near      = _scale(BORDER_NEAR_600, dpi)
    guard     = _scale(INTERIOR_GUARD_600, dpi)
    if even:
        # neighbor sits near the border = HIGH index. Scan from the border inward.
        i = n - 1
        while i >= 0 and not content[i]:
            i -= 1
        if i < 0:
            return None
        if (n - 1) - i > near:
            return None                      # first content too far from border = page's own text
        outer_end = i
        clean = 0; edge = i
        while i >= 0:
            if content[i]:
                clean = 0; edge = i
            else:
                clean += 1
                if clean >= cleanrun:
                    break
            i -= 1
        if outer_end - edge < blockmin:
            return None                      # block too thin = speck/dust, not a page
        if edge <= guard:
            return None                      # block ran into the interior = full-bleed/merged, no gap
        return edge
    else:
        # neighbor sits near the border = LOW index. Scan from the border inward.
        i = 0
        while i < n and not content[i]:
            i += 1
        if i >= n:
            return None
        if i > near:
            return None
        outer_end = i
        clean = 0; edge = i
        while i < n:
            if content[i]:
                clean = 0; edge = i
            else:
                clean += 1
                if clean >= cleanrun:
                    break
            i += 1
        if edge - outer_end < blockmin:
            return None
        if edge >= n - guard:
            return None
        return edge


def _theil_sen(ys, xs):
    """Robust line x = a*y + b (a = dx/dy). Median of pairwise slopes, median intercept."""
    sl = []
    m = len(ys)
    for i in range(m):
        for j in range(i + 1, m):
            if ys[j] != ys[i]:
                sl.append((xs[j] - xs[i]) / (ys[j] - ys[i]))
    if not sl:
        return 0.0, float(np.median(xs))
    a = float(np.median(sl))
    b = float(np.median(xs - a * ys))
    return a, b


def _ransac(pts, thr, iters=RANSAC_ITERS):
    """Iterative Theil-Sen with residual rejection. pts = list of (y, x).
    Return a, b, inlier_pts, resid_std (over inliers)."""
    P = list(pts)
    a = b = 0.0
    for _ in range(iters):
        if len(P) < 4:
            break
        ys = np.array([p[0] for p in P], float); xs = np.array([p[1] for p in P], float)
        a, b = _theil_sen(ys, xs)
        keep = [(y, x) for (y, x) in P if abs(x - (a * y + b)) < thr]
        if len(keep) < 4:
            break
        if len(keep) == len(P):
            break
        P = keep
    ys = np.array([p[0] for p in P], float); xs = np.array([p[1] for p in P], float)
    if len(P) >= 2:
        a, b = _theil_sen(ys, xs)
        resid = float(np.std(xs - (a * ys + b)))
    else:
        resid = 999.0
    return a, b, P, resid


def _fit_capped(pts, dpi, H):
    """Fit the spine line with the angle cap enforced. Return a dict of fit info.

    Strategy (see module docstring / NOTES):
      1. Unconstrained robust RANSAC/Theil-Sen fit -> (a,b), inliers, residual, raw tilt.
      2. If |raw tilt| <= cap: keep it as-is (the normal near-vertical spine).
      3. If |raw tilt| >  cap: set over_cap=True and CONSTRAIN-REFIT -- clamp the slope magnitude
         to the cap and re-derive the intercept over the SAME inliers -- so tilt_deg/b report a
         within-cap line for diagnostics. The caller REJECTS over_cap pages (no cut): an over-cap
         raw fit means the boundary is a skewed neighbor-image / ragged edge, not the spine, and a
         capped line over a truly tilted edge would cut wrong. (We do NOT cut on the capped line.)"""
    thr = _scale(RESID_THR_600, dpi)
    a, b, inl, resid = _ransac(pts, thr)
    raw_tilt = degrees(atan(a))
    capped = False
    if abs(raw_tilt) > SPINE_ANGLE_MAX_DEG and len(inl) >= 2:
        capped = True
        a = copysign(tan(radians(SPINE_ANGLE_MAX_DEG)), a)
        ys = np.array([p[0] for p in inl], float); xs = np.array([p[1] for p in inl], float)
        b = float(np.median(xs - a * ys))
        resid = float(np.std(xs - (a * ys + b)))
    tilt = degrees(atan(a))
    over_cap = abs(raw_tilt) > SPINE_ANGLE_MAX_DEG
    return dict(a=a, b=b, inliers=inl, n_inliers=len(inl), resid=resid, raw_tilt_deg=raw_tilt,
                tilt_deg=tilt, capped=capped, over_cap=over_cap, resid_thr=thr)


# ---------------------------------------------------------------------------------------------------
def spine_matte(rgb, dpi, page_no=None, return_meta=False):
    """Matte the neighbor strip on the binding side of one page.

    rgb      : PIL image or HxWx3 array (the 600-dpi thumb, or any dpi if --dpi set).
    page_no  : page number (parity: even -> neighbor RIGHT, odd -> neighbor LEFT).
    Returns (rgba, pct_cleared, meta) if return_meta else (rgba, pct_cleared).
    Only cuts when confidence is HIGH; LOW confidence -> no cut (empty matte)."""
    a = np.asarray(rgb)[..., :3]
    H, W, _ = a.shape
    if page_no is None:
        raise ValueError("spine_matte needs page_no for parity")
    even = _is_even(page_no)
    inner_w = min(_scale(INNER_W_600, dpi), W)
    smooth  = _scale(SMOOTH_600, dpi)
    overcut = _scale(OVERCUT_600, dpi)

    if even:
        x_off = W - inner_w; sub = a[:, x_off:W, :]
    else:
        x_off = 0;           sub = a[:, 0:inner_w, :]

    pts = []                                  # (y_center, absolute_x) boundary points
    for bnd in range(NB):
        y0 = bnd * H // NB; y1 = (bnd + 1) * H // NB
        df, st = _col_signals(sub[y0:y1])
        df = _sm(df, smooth); st = _sm(st, smooth)
        content = (df > CONTENT_DARK) | (st > CONTENT_SAT)
        bx = _band_boundary(content, even, dpi)
        if bx is not None:
            pts.append(((y0 + y1) // 2, x_off + bx))

    meta = dict(page=page_no, even=even, n_evidence=len(pts), NB=NB, confidence="LOW",
                confident=False, cut_pct=0.0)

    mask = np.zeros((H, W), bool)
    if len(pts) >= MIN_EVIDENCE_BANDS:
        fit = _fit_capped(pts, dpi, H)
        meta.update(tilt_deg=round(fit['tilt_deg'], 3), raw_tilt_deg=round(fit['raw_tilt_deg'], 3),
                    capped=fit['capped'], n_inliers=fit['n_inliers'], resid_px=round(fit['resid'], 1),
                    x_top=round(fit['b'], 1), x_bot=round(fit['a'] * H + fit['b'], 1))
        # --- CONFIDENCE GATE: enough inlier bands, low residual, AND the robust fit is within the
        #     angle cap. An over-cap raw fit => the boundary is a skewed neighbor-image / ragged edge,
        #     not the near-vertical spine => reject (no cut), regardless of the constrained residual.
        confident = (fit['n_inliers'] >= MIN_EVIDENCE_BANDS
                     and fit['resid'] < fit['resid_thr']
                     and not fit['over_cap'])
        meta['confident'] = bool(confident)
        meta['confidence'] = "HIGH" if confident else "LOW"
        if fit['over_cap']:
            meta['reject_reason'] = (f"raw fit {fit['raw_tilt_deg']:+.2f} deg exceeds +-{SPINE_ANGLE_MAX_DEG} "
                                     f"cap (skewed neighbor-image / ragged edge, not a spine) -> no cut")
        elif not confident:
            meta['reject_reason'] = f"low evidence/residual (n_inliers={fit['n_inliers']}, resid={fit['resid']:.1f}px)"
        if confident:
            line_x = fit['a'] * np.arange(H) + fit['b']
            xs = np.arange(W)[None, :]
            if even:                          # neighbor is to the RIGHT (higher x)
                cut_x = (line_x - overcut)[:, None]
                mask = xs >= cut_x
            else:                             # neighbor is to the LEFT (lower x)
                cut_x = (line_x + overcut)[:, None]
                mask = xs <= cut_x
            if MARGIN_600 > 0:
                import scipy.ndimage as ndi
                mask = ndi.binary_dilation(mask, iterations=_scale(MARGIN_600, dpi))

    pct = 100.0 * mask.mean()
    meta['cut_pct'] = round(pct, 3)
    rgba = np.dstack([a.astype(np.uint8), np.where(mask, 0, 255).astype(np.uint8)])
    return (rgba, pct, meta) if return_meta else (rgba, pct)


# ---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("out")
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--page", type=int, help="page number (parity); default = integer in filename")
    ap.add_argument("--magenta", action="store_true", help="50%% magenta overlay over the cut region")
    A = ap.parse_args()
    page_no = A.page if A.page is not None else _page_no_from_name(A.img.rsplit('/', 1)[-1])
    rgba, pct, meta = spine_matte(Image.open(A.img).convert("RGB"), A.dpi,
                                  page_no=page_no, return_meta=True)
    if A.magenta:
        f = rgba.astype(np.float32); cut = f[..., 3] == 0
        out = f[..., :3]; out[cut] = 0.5 * out[cut] + 0.5 * np.array([255, 0, 255], np.float32)
        Image.fromarray(out.astype(np.uint8)).save(A.out)
    else:
        Image.fromarray(rgba, "RGBA").save(A.out)
    print(json.dumps(meta))
