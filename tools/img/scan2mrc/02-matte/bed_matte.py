#!/usr/bin/env python3
"""Bed matte: mark the scanner backing at each page edge as unknown (alpha 0).

Backing = whatever lies OUTSIDE the sheet: the scanner bed (lid / backing sheet / its shadow)
and the coloured cardboard insert. The page must not be cut.

NOTHING ABOUT THE BACKING IS WRITTEN IN THIS FILE. calibrate_backing.py measures it over the
issue -- backing is the material that covers the border ring and vanishes inboard -- and finds
the bed on top/left/right, the insert on the bottom of 176/176 pages, and correctly refuses the
cream paper everywhere. The old BED_LUMA / BED_SAT / INSERT_LUMA / INSERT_SAT / INSERT_EDGES
were those same facts guessed rather than measured, and each was wrong somewhere.

THE ALGORITHM -- three steps, one code path for all four edges, and the middle step is the
SHARED core in ../linefit.py:

  1. WHAT IS BACKING HERE, then PER-LINE CANDIDATE TRANSITIONS. The issue profile is refined on
     the page in front of us and grown to the material's real extent (page_materials), then each
     scanline offers the depths where that material ends (candidates).
  2. ROBUST LINE FIT (linefit.fit): the (offset, slope) most lines agree on, then LSQ on the
     inliers, plus a bounded quadratic for the sheet's bow.
  3. MARGIN AND DECISION, kept OUT of the fit: a fixed overcut, and independent tests for
     whether this edge should be cut at all.

TWO AXES, NOT ONE BALL. The bed and the sheet-edge shadow are one material family; page ink is
not, and no single RGB distance can say so. Measured against each page's own bed, the shadow
that MUST be cut sits 33-37 away in luma but 1.9-4.6 in chroma, while the ink that must be KEPT
sits a similar 33-51 in luma and 12.7-127 in chroma. So tolerances are loose in luma and tight
in chroma, and chroma is compared as a RATIO to luma (CHROMA_STAB) because a saturated material
darkens into shadow -- an absolute chroma bound dropped the shaded insert and the bottom
boundary "wobbled" +-45px, which was never real waviness.

WHY THE FIT IS A MODE. The first version walked to the FIRST non-backing pixel -- one candidate
per line -- so a single anomalous pixel ruined that line, and the damage was repaired downstream
with an outlier fence, a coverage percentile, depth smoothing, gap bridging and a strip
extension, each of which broke something else:

    walk stops in a transition blur -> gap bridging -> leapt through an ad's black TEXT
    deep outlier lines              -> MAD fence    -> too tight left bed standing on p003
    spiky depths                    -> smoothing    -> fit disagreed with what it must cover
    bed strip after the blur        -> extension    -> combed p005's halftone per column

A mode needs none of it. Deleted: OUTLIER_K, FENCE_MIN_600, COVER_PCT, SLACK, SMOOTH_D_600,
GAP_BRIDGE_600, STRIP_*, PAGECUT_FRAC, and the learned-prior acceptance path.

RULES (from the user, in this order):
  1. every backing pixel must be cut -- leaving a stripe is a FAIL
  2. subject to that, cut as few of OUR pixels as possible
The order matters and the code reflects it: the evidence bar scales with what a cut COSTS, so a
4px line enclosing nothing but backing is allowed on weaker evidence than a deep one.

REMAINING LIMIT: where a full-bleed dark ad reaches the border on nearly every scanline (p047's
top), the material never stops inside the window, so no boundary can be established and the edge
is left uncut by design.
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
CHROMA_STAB   = 40.0     # chroma is compared as a RATIO to luma, stabilised by this offset.
                         # An absolute chroma difference is wrong for a SATURATED material: as the
                         # cardboard insert falls into shadow its luma drops and its chroma drops
                         # with it, so a fixed chroma tolerance dropped the shadowed insert and the
                         # bottom boundary wobbled again. Normalised, the same insert reads 6.4-6.6
                         # from lit to shadowed, while the page ink that must be KEPT reads 16.7
                         # (p069 ad), 23.5 (p005 comic) and 127.3 (p044 ochre), and the sheet-edge
                         # shadow that must be CUT reads 2.7-5.9. The offset keeps the ratio stable
                         # where luma is near zero (the bed itself sits at L5-40).
GROW_L        = 2.0      # growth may reach this many measured luma-radii from the seed colour ...
GROW_C        = 2.0      # ... but barely further in CHROMA. That asymmetry IS the discrimination:
                         # the sheet-edge shadow that must be cut lies 33-37 from the bed in luma
                         # and 1.3-3.8 in chroma, while page ink that must be kept lies a similar
                         # 33-51 in luma but 10.6-144.7 in chroma. Loose in luma, tight in chroma.
RING_600      = 3        # border ring used to refine a material on the page in front of us
SEED_STEP     = 8        # quantisation for finding the ring's densest colour peak
SPREAD_PCTL   = 90       # per-page radius = this percentile of the peak's own spread ...
COVER_PCTL    = 99       # ... but after growth, a percentile that COVERS what was grown
SPREAD_K      = 1.5      # ... times this
RADIUS_FLOOR_L = 12      # ... never tighter than this in luma (scanner noise) ...
RADIUS_FLOOR_C = 3       # ... nor than this in chroma (normalised units)
GROW_ITERS    = 2        # re-measure the material over its connected region this many times
MIN_RING_FRAC = 0.02     # a material must hold this much of the ring to be present on this page
DEEP_FRAC     = 0.75     # the deep part of the search window, used to re-run the calibration's
STOP_FRAC     = 0.5      # ... and must stop within the window on this fraction of lines
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
OVERRUN_600   = 24       # a cut may exceed the material's p95 stop depth by this much
SHALLOW_600   = 25       # a cut this shallow (~1mm) is allowed on weaker evidence
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
INK_ERODE_600 = 4        # erode the region this far from its boundary before judging it
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

    The profile gives each material's issue-wide centre and tolerances. Here we (1) seed on the
    border ring of the page in front of us, (2) grow the material through connected pixels to its
    real extent, and (3) accept the widest version that still stops at the sheet edge.

    (1) SEEDING PER PAGE is what separates bed from a page's own black ink. Across the issue the
        two overlap completely (bed L5-51, ink L15-45); within one scan they are far apart
        (p069: bed L20 against its ad at L40).
    (2) GROWTH is needed because the ring is the most evenly lit part of the backing. Deeper in,
        where the sheet lifts off the platen, the same material is shadowed: p015's bottom insert
        ran to 135px in lit columns but the ring-derived tolerance saw only 41px in shadowed ones,
        and the resulting +-45px "wobble" is what wrecked the line fit -- not any real waviness.
        Growth is LOOSE IN LUMA AND TIGHT IN CHROMA (GROW_L / GROW_C), which is the whole trick:
        the sheet-edge shadow band sits far away in luma but on top of the bed in chroma, while
        page ink sits equally far in luma and far in chroma too.
    (3) ACCEPTANCE is the calibration's own collapse test, re-run per page on the connected
        region: real backing stops at the sheet edge, ink running to the border does not. It
        bounds the growth as well -- without that, p069's top merged its bed strip into the ad
        below and the whole edge was then dropped, leaving the strip standing.

    Returns [(centre, radius_luma, radius_chroma), ...]; empty if this edge shows no backing.
    """
    ring = max(2, round(RING_600 * dpi / 600))
    r = rgb_edge[:, :ring].reshape(-1, 3)
    dstart = int(DEEP_FRAC * rgb_edge.shape[1])
    out = []
    for spec in profile.get(edge, []):
        if not spec.get("backing"):
            continue
        c0 = np.array(spec["centre"], np.float32)
        rl0, rc0 = float(spec["radius_l"]), float(spec["radius_c"])

        dl, dc = dev(r, c0)
        in0 = (dl <= rl0) & (dc <= rc0)
        if in0.mean() < MIN_RING_FRAC:
            continue                                   # material absent from this page's edge
        sel = r[in0]

        q = (sel // SEED_STEP).astype(np.int32)
        key = q[:, 0] * 4096 + q[:, 1] * 64 + q[:, 2]
        u, cnt = np.unique(key, return_counts=True)
        k = int(u[int(np.argmax(cnt))])
        peak = np.array([(k // 4096) * SEED_STEP, ((k // 64) % 64) * SEED_STEP,
                         (k % 64) * SEED_STEP], np.float32) + SEED_STEP / 2
        near = sel[np.abs(sel - peak).max(1) <= max(RADIUS_FLOOR_L, SEED_STEP * 3)]
        if near.shape[0] < 32:
            near = sel
        centre = np.median(near, 0)

        def _radii(px, c, pctl=SPREAD_PCTL):
            a, b = dev(px, c)
            return (float(np.clip(SPREAD_K * np.percentile(a, pctl),
                                  RADIUS_FLOOR_L, rl0 * GROW_L)),
                    float(np.clip(SPREAD_K * np.percentile(b, pctl),
                                  RADIUS_FLOOR_C, rc0 * GROW_C)))

        rl, rc = _radii(near, centre)

        # the LOOSE envelope growth may explore, anchored on the ISSUE centre so it cannot drift:
        # re-centring it each pass let p005's top walk off the neutral bed into the green comic
        # beside it and cut 38px of artwork
        dl_e, dc_e = dev(rgb_edge, c0)
        loose = (dl_e <= rl0 * GROW_L) & (dc_e <= rc0 * GROW_C)

        def region_collapses(mask):
            """Does the material stop at the sheet edge on MOST scanlines?

            Per line, not pooled. Pooled coverage is a global veto, and it threw away the majority
            case: p003's top has a real 15px bed band on 57% of its scanlines, but the band also 
            touches a large black block that runs the full depth on the other 41%, so pooled deep
            coverage was 0.42 and the whole edge reported NO backing. Per line, 59% of scanlines
            show the material stopping, which is exactly the evidence the line fit then uses --
            while p069's left edge, where a full-bleed ad reaches the border on nearly every line,
            still fails as it must."""
            stops = ~mask[:, dstart:].any(1)
            return float(stops.mean()) >= STOP_FRAC

        def mask_for(c, a, b):
            """Pixels of this colour that are CONNECTED TO THE BORDER.

            Connectivity is not optional even for the seed. Judged on the bare colour, a
            text-heavy page counts its own black type as "this material, deep inside", and the
            collapse ratio then fails on a perfectly real bed wedge: p003's top measured ring 0.52
            against deep 0.18 = 2.9x, just under the bar, so the page reported NO backing at all
            and 15px of bed went uncut. Type is not connected to the border; bed is."""
            x, y = dev(rgb_edge, c)
            m = (x <= a) & (y <= b)
            lab, nl = ndi.label(m)
            if nl:
                keep = np.unique(lab[:, 0])
                keep = keep[keep > 0]
                m = np.isin(lab, keep) if keep.size else np.zeros_like(m)
            return m

        best = (centre, rl, rc) if region_collapses(mask_for(centre, rl, rc)) else None
        for _ in range(GROW_ITERS):
            if best is None:
                break
            seed = mask_for(centre, rl, rc)
            lab, nl = ndi.label(loose)
            m = seed
            if nl:
                touch = np.unique(lab[:, 0])               # components touching the border ...
                hit = np.unique(lab[seed])                 # ... that hold seed pixels
                keep = np.intersect1d(touch[touch > 0], hit[hit > 0])
                if keep.size:
                    m = np.isin(lab, keep)
            if m.sum() < 64 or not region_collapses(m):
                break                                      # grew into the page: keep `best`
            px = rgb_edge[m]
            centre = np.median(px, 0)
            # COVER the grown region, do not re-summarise it. A p90 refit threw the growth away
            # again -- the insert's grown region was right (ring 0.95, deep 0.000) but its p90
            # deviation is 6.7, so the refitted tolerance dropped exactly the shadowed tail that
            # had just been captured and the bottom boundary went back to wobbling +-45px.
            rl, rc = _radii(px, centre, COVER_PCTL)
            best = (centre, rl, rc)
        if best is not None:
            out.append(best)
    return out


def page_colours(profile, edge, rgb_edge=None, dpi=600):
    """The PAPER colours, refined on this page when the edge is given.

    The issue-wide paper cluster is not enough. Paper tone varies from page to page, and a page
    whose margin is warmer than the issue mean then reads as "not page" -- which is how p157's
    left edge, clean cream margin with no bed on it at all, scored purity 1.00 and had 241px
    (10mm) of its own margin cut away. Refined against the page's OWN interior, that margin is
    plainly paper. Measured from the deep band, where the paper is by definition."""
    out = []
    for m in profile.get(edge, []):
        if m.get("backing"):
            continue
        c0 = np.array(m["centre"], np.float32)
        rl, rc = float(m["radius_l"]), float(m["radius_c"])
        if rgb_edge is not None:
            deep = rgb_edge[:, int(DEEP_FRAC * rgb_edge.shape[1]):].reshape(-1, 3)
            dl, dc = dev(deep, c0)
            sel = deep[(dl <= rl * GROW_L) & (dc <= rc * GROW_C)]
            if sel.shape[0] >= 256:
                c0 = np.median(sel, 0)
                a, b = dev(sel, c0)
                rl = float(np.clip(SPREAD_K * np.percentile(a, COVER_PCTL),
                                   RADIUS_FLOOR_L, rl * GROW_L))
                rc = float(np.clip(SPREAD_K * np.percentile(b, COVER_PCTL),
                                   RADIUS_FLOOR_C, rc * GROW_C))
        out.append((c0, rl, rc))
    return out


def dev(px, centre):
    """(luma deviation, luma-normalised chroma deviation) from a centre colour.

    Two axes because one RGB distance cannot say "dark AND neutral", which is what the bed is;
    and the chroma axis is normalised by luma so a shaded saturated material stays itself.
    See CHROMA_STAB."""
    px = np.asarray(px, np.float32)
    c = np.asarray(centre, np.float32)
    l = px.mean(-1)
    l0 = float(c.mean())
    n = l + CHROMA_STAB
    n0 = l0 + CHROMA_STAB
    dl = np.abs(l - l0)
    dc = 100.0 * np.maximum(
        np.abs((px[..., 0] - px[..., 1]) / n - (c[0] - c[1]) / n0),
        np.abs((px[..., 1] - px[..., 2]) / n - (c[1] - c[2]) / n0))
    return dl, dc


def is_backing(rgb, mats):
    """Positive material test: within tolerance of one of these colours (centre, r_luma, r_chroma)."""
    m = np.zeros(rgb.shape[:2], bool)
    for centre, rl, rc in mats:
        dl, dc = dev(rgb, centre)
        m |= (dl <= rl) & (dc <= rc)
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
    notpage = ~is_backing(E, page_colours(profile, edge, E, dpi))
    N = L.shape[0]

    # THE BOUNDARY WE WANT IS WHERE THE PAGE BEGINS, not where the bed's exact colour ends.
    # Between the two lies the sheet-edge shadow -- a blur that is neither. It is outside the
    # sheet, so rule 1 says cut it; matching on backing colour alone stopped short of it and left
    # it standing (p015's top: bed colour ends at 5px, the page starts at ~27px, and the audit
    # rightly reported the 15px gap as residue on 63% of scanlines).
    # Candidates are therefore notpage->page transitions, but ONLY on scanlines whose border
    # actually shows backing. Without that restriction every line of body text deep in the page
    # would offer candidates, since text is "not page" too.
    ring = max(2, round(RING_600 * dpi / 600))
    edge_has_backing = back[:, :ring].any(1)
    cand = candidates(back, dpi)
    cand[~edge_has_backing] = -1.0
    yy = np.arange(N, dtype=np.float64) - N / 2.0
    idx = np.arange(D)[None, :]

    # JUDGED ONLY WHERE THE MATERIAL EXISTS. A bed wedge rarely spans the full edge, and on the
    # scanlines it does not reach, ANY cut is pure page -- averaging those in made even a 4px cut
    # look impure and rejected the edge (p144 top, p056 top). Overcutting clean scanlines is
    # rule 2's business (the margin), not rule 1's; purity's job is only to stop a line running
    # deep into content, which it still does: on a scanline that HAS bed, a 390px line encloses
    # 20px of bed and 370px of page and fails just as before.
    haslines = edge_has_backing if edge_has_backing.any() else np.ones(N, bool)

    def _pure(offset, slope):
        """Is what this line encloses predominantly NOT page? (see BACKING_PURITY)"""
        ln = np.clip(offset + slope * yy, 0, D)
        inside = (idx < ln[:, None]) & haslines[:, None]
        n = int(inside.sum())
        return n > 0 and float(notpage[inside].mean()) >= BACKING_PURITY

    line, vote_frac, sl, contrast = linefit.fit(cand, tol=max(2.0, VOTE_TOL_600 * dpi / 600),
                                      slope_max_deg=SLOPE_MAX_DEG,
                                      curve_max=CURVE_MAX_600 * dpi / 600,
                                      prefer_deepest=DEEPEST_FRAC,
                                      min_vote_frac=MIN_VOTE_FRAC,
                                      accept=_pure)
    line = np.clip(line, 0, D)

    backing_frac = float(edge_has_backing.mean())
    # SCREEN ENERGY IS A PROPERTY OF A REGION'S INTERIOR. Measured right up to the boundary it
    # measures the boundary: on p006/p010/p012/p014/p042 the cut is a ~5px bed strip with no
    # interior at all, the band-pass read 21-27 (i.e. "printed ink") and the veto threw away five
    # real strips that the audit had been reporting as residue for weeks. Erode the region first,
    # and if nothing survives, the region is too thin to carry a halftone -- so it cannot be the
    # screened ad this test exists to protect, and the veto simply does not apply.
    Sc = screen_energy(L, dpi)
    sel = (np.arange(D)[None, :] < line[:, None]) & back
    core = ndi.binary_erosion(sel, np.ones((1, 2 * max(2, round(INK_ERODE_600 * dpi / 600)) + 1)))
    ink = float(np.median(Sc[core])) if core.sum() >= 256 else 0.0

    m = dict(backing_frac=backing_frac, vote_frac=vote_frac, slope=float(sl),
             angle_deg=float(np.rad2deg(np.arctan(sl))),
             median_depth=float(np.median(line)), ink=ink, mats=len(mats),
             contrast=float(min(contrast, 1e6)),
             mat_colours=[[round(float(x)) for x in c] + [round(a), round(b)] for c, a, b in mats])

    # What we are about to cut must actually BE backing. Without this the halftone's dark
    # dots pass the blackish test on most lines and yield a consistent shallow "boundary":
    # p005's right edge is the green comic running full-bleed, no bed at all, and it cut 17px
    # of it (backing_frac 0.93, vote 0.64, ink 8.4 -- under every other test). Purity is
    # rule 1 and rule 2 stated together: cut backing, and only backing.
    _in = (np.arange(D)[None, :] < line[:, None]) & haslines[:, None]
    m["purity"] = float(notpage[_in].mean()) if _in.any() else 0.0
    if backing_frac < MIN_BACKING_FRAC:
        return np.zeros(L.shape[0]), "CLEAN(no backing)", m
    if m["purity"] < BACKING_PURITY:
        return np.zeros(L.shape[0]), "MIXED(not backing)", m
    # RULE 1 OUTRANKS RULE 2, so the evidence bar scales with what the cut COSTS. A deep line
    # needs real proof; a 4px line that encloses nothing but backing costs 0.2mm of margin even
    # if it is wrong, while refusing it leaves a visible stripe. Measured over the issue, the
    # thin strips sit at contrast 8-10 with purity ~1.0 and the genuinely spurious deep lines at
    # 2.0, so a single global bar had to sacrifice one or the other.
    # RULE 2 SANITY: the cut may not run far past where the material actually STOPS. The fit can
    # be dragged off by dark content when the real backing covers few scanlines -- p157's left has
    # bed on 15% of lines that ends by ~10px, and the line landed at 237px, cutting 10mm of the
    # page's own cream margin. Compare against where the material ends on the lines that have it.
    run = max(2, round(MIN_RUN_600 * dpi / 600))
    csb = np.concatenate([np.zeros((N, 1), np.int32), np.cumsum(back.astype(np.int32), 1)], 1)
    dd = np.arange(D)[None, :]
    solid = back & ((np.take_along_axis(csb, dd + 1, 1)
                     - np.take_along_axis(csb, np.maximum(dd - run + 1, 0), 1))
                    >= RUN_FRAC * np.minimum(run, dd + 1))
    stop = np.where(solid.any(1), D - 1 - np.argmax(solid[:, ::-1], 1), -1)
    have = stop >= 0
    m["stop_p95"] = float(np.percentile(stop[have], 95)) if have.any() else 0.0
    if float(np.median(line)) > m["stop_p95"] + OVERRUN_600 * dpi / 600:
        return np.zeros(L.shape[0]), "OVERRUN(past material)", m

    shallow = float(np.median(line)) <= SHALLOW_600 * dpi / 600
    if contrast < MIN_CONTRAST and not (shallow and m["purity"] >= BACKING_PURITY):
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
