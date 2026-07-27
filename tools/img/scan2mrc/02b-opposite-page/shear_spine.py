#!/usr/bin/env python3
"""SPINE detector -- the background-colour boundary between this page and its neighbour.

WHAT WE ARE LOOKING FOR
-----------------------
Each scan is HALF of an A3 sheet, so the binding-side strip of every page image contains a
sliver of the NEIGHBOUR page. "The line" is the 50% crossing of the printed colour step
where one background ends and the other begins.

  Parity:  EVEN page -> neighbour hugs the RIGHT edge
           ODD  page -> neighbour hugs the LEFT  edge

NOTE on the sheet: most spreads are two pages printed on ONE folded sheet (no paper edge,
no shadow ridge -- a purely printed step). But not all: p020 clearly shows a PHYSICAL page
edge with a separate sheet behind it, whose content carries its own angle. Both cases exist
in this issue and the estimator below does not assume either.

This tool fires ONLY where the two backgrounds genuinely differ over at least part of the
height. Cream-on-cream is unobservable and is explicitly NOT its job.

TWO STAGES -- detection and localisation want opposite things
-------------------------------------------------------------
COARSE (robust, threshold-free). Argmax over (x0, slant) of the accumulated median step
field, pooling the full page height:

    A(x0, theta) = || SUM_y  D( x0 + tan(theta)*(y - yc), y ) ||
    D(x, y)      = median(f, w inboard) - median(f, w outboard)
    f            = [L, (R-G)*k, (G-B)*k]   on the descreened, median-filtered band

  * Pooling the height turns a 1-2 level per-row step into a razor peak. A per-row
    threshold cannot see it -- that is what killed the old bg_spine.py (DEPART=3.2 over
    PERSIST=44 px, required in EVERY row).
  * The vector sum, normed at the end, keeps a boundary that steps in a CONSTANT colour
    direction and cancels photo edges that do not.
  * The MEDIAN is essential: a mean treats "ink is present" as a background change, so
    every classified-ads text column fires (24/24 inspected false fires were exactly that).
    The square median filter also wipes printed VERTICAL RULES, which are otherwise the
    most coherent x-gradient on the page (p176 locked on the EPSON ad's frame rule), and
    the wide windows ignore the gutter SHADING ramp.

FINE (precise). Robustness costs localisation: a median does not ramp across a boundary,
it switches, so the coarse response is a PLATEAU ~2w wide, not a peak -- measured as a
constant -37 ref px bias, independent of step size, and in (x0, slant) space that plateau
is a RIDGE, which is why a free slant fit returned 0.7 deg of noise uncorrelated with
anything real. So the coarse fit is used only to read the two BACKGROUND COLOURS either
side; the band is projected onto the axis joining them, and the boundary is the per-row
ZERO CROSSING of that projection -- literally the 50% point of the step. The line is the
MODE of those crossings (Hough), then least squares on the inliers.

Verified by synthetic recovery (known offset and slant pasted on a real gutter band):
position error -3 band px = the harness's own half-pixel definition, slant error <=0.005
deg. Before the fine stage: -37 px and up to 0.36 deg.

Side colours and the step size are measured only on the rows that ACTUALLY carry the step,
or a partial-height neighbour averages away (p170's gray ad spans 21% of the page: its
step read 5 instead of 331).

CONSTRAINTS FROM THE USER (both hard, both physical)
----------------------------------------------------
  * The boundary lies within +/-5 mm of the CLIP-HOLE line. Colour alone provably cannot
    do this: "cream | our own solid black panel" (false) and "cream neighbour | our
    full-bleed gray ad" (true) are the same measurement, and only position separates them.
    Used as a search BOUND -- position and slant remain a pure colour measurement.
  * The boundary slant is within 1 deg of the STAPLE LINE's slant (fitted through the 6
    hole centres; tight, median max-residual ~5 px). Our own free slant estimate was
    noisier than the entire plausible range, so this bound is pure gain.
A fit that rails against either bound is REJECTED, never clamped -- clamping is what hid
the old detector's misdetections.

DECISION: step >= STEP_MIN (the colour difference actually crossed), not railed, and a
minimum extent. `z` is reported but is NOT a gate -- it is high for a crisp text-column
edge and low for a genuine partial-height neighbour.

Objective, label-free validation lives in selfcheck.py (split-half consistency + synthetic
recovery). Outputs go to OUT_DIR, never into the source tree.

CLI:
  shear_spine.py NNN [NNN ...] [--overlay] [--json OUT]
  shear_spine.py --all [--overlay] [--json OUT]
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, median_filter, uniform_filter1d

Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------- #
#  CONSTANTS                                                                   #
#  Spatial values are given at the REFERENCE resolution (600-dpi thumb,        #
#  REF_W wide) and scaled by sx = W/REF_W, so the same code runs at 2400 dpi.  #
# --------------------------------------------------------------------------- #
THUMB_DIR = "/Users/mist/DNB/8609/thumbs_600"
OUT_DIR   = "/Users/mist/DNB/8609/tmp"
CLIP_JSON = "/Users/mist/DNB/8609/tmp/clip_holes.json"

REF_W = 5200            # reference page width the px constants below were chosen at

# --- analysis band on the binding side -------------------------------------- #
BAND      = 760         # width of the binding-side strip we analyse, ref px
EDGE_SKIP = 16          # ignore the very scan edge (bed shadow / clipped column), ref px
X_LO      = 90          # search window for the boundary, as distance INBOARD from the
                        #   binding edge. Must clear the dark SCAN-EDGE border (~55 ref px)
                        #   or that border out-steps every real boundary (p176 locked on it).
X_HI      = 470         #   binding edge, ref px. The A3 split left a neighbour sliver of
                        #   0..~350 ref px, so a "boundary" deeper than this is inside our
                        #   own page (a text column, an inset card) -- not the gutter.
Y_MARGIN  = 0.04        # drop this fraction of rows top and bottom -- the scanner bed
                        #   wedge / yellow backing there is not page and would dominate.

# --- descreen / background field -------------------------------------------- #
DS        = 6           # downscale factor. 600 dpi / 6 ~= 100 dpi, so the ~150-lpi
                        #   halftone averages into a solid background colour.
MED_XY    = 5           # square median on the downscaled band (=30 ref px = 1.3 mm).
                        #   Median is EDGE-PRESERVING but wipes any structure thinner
                        #   than the kernel: text strokes, hairlines and -- crucially --
                        #   printed VERTICAL RULES, which are otherwise the single most
                        #   coherent x-gradient on a magazine page and win the argmax
                        #   (observed: p176 locked on the EPSON ad's frame rule).

# --- clip-hole prior (search BOUND only, never the answer) ------------------- #
# The line itself is measured purely from colour. The clip column only limits WHERE we
# look, because colour alone provably cannot do that job: "cream | our own solid black
# panel" and "cream neighbour | our full-bleed gray ad" are the SAME signature, and the
# first is a false fire (p067/p071/p057/p028) while the second is a true one (p047/p170).
# Position is the only thing that separates them. Measured on the 37 accepted fires:
# every correct one sat within 77 px of the clip column, every false one beyond 160.
REF_DPI   = 600         # the reference thumbnails are 600 dpi
CLIP_WIN_MM = 5.0       # HARD CONSTRAINT (from the user): the background-difference line
                        #   lies within +/- 5 mm of the clip-hole line. Expressed in mm and
                        #   converted by REF_DPI so it survives a change of resolution.
CLIP_WIN  = CLIP_WIN_MM / 25.4 * REF_DPI          # = 118 ref px
CLIP_CONF = 0.7         # minimum clip_holes confidence to trust the column

# --- colour feature --------------------------------------------------------- #
CHROMA_W  = 2.2         # weight on (R-G) and (G-B) vs luma, so a near-neutral colour
                        #   step (pale green/pink neighbour) counts like a tone step.

# --- step operator / accumulation ------------------------------------------- #
STEP_W    = 7           # half-window of the SIGNED STEP operator, downscaled px
                        #   (=42 ref px = 1.8 mm each side). We compare the mean colour
                        #   of a wide window on each side, NOT a local gradient: a real
                        #   background boundary is a SUSTAINED step, a rule/edge of a
                        #   content block is not. A thin line inside the window shifts
                        #   both means by ~its area fraction -> near-zero response.
                        #   Matched filter for a step -> response peaks exactly on it.
ANG_MAX   = 1.6         # slant search range, degrees. The sheet is deskewed to ~0.3 deg;
                        #   a printed boundary cannot be far off vertical.
ANG_STEP  = 0.02        # slant resolution, degrees (~2 ref px over the page height).

# --- fine localisation (the 50% crossing) ----------------------------------- #
FINE_OFFS   = 9         # sample the two side colours this far from the coarse line, ds px
FINE_WIN    = 7         # ... over this many columns, ds px
FINE_SMOOTH_Y = 9       # smooth the projection along y only (never across the boundary)
FINE_SEARCH = 14        # look for the crossing within this many ds px of the coarse line
FINE_TOL    = 2.5       # a row is an inlier if its crossing is within this of the line
MIN_ROWS_FINE  = 60     # need this many rows with a usable crossing to trust the fine fit
# A slant is only MEASURABLE with enough LEVER ARM: its standard error scales as 1/span.
# What matters is the vertical SPAN the inliers cover, NOT how many of them there are --
# p012/p165 had 35% of rows but all of them inside rows 0.65..1.0, so their slant was fitted
# on the bottom third and extrapolated over the whole page (-0.32 deg against a +0.11 deg
# staple line). Conversely p045 has only 47% of rows but they span the FULL height, so its
# slant is perfectly well determined. Below the span floor we do not fit a slant at all: we
# inherit the staple line's and fit the offset only. Rejecting those pages instead would
# throw away correct detections (p170's gray ad spans 20% of the page and is right), while
# free-fitting them produced the visibly wrong diagonals on p023 and p024.
SPAN_SLANT_MIN = 0.5    # inliers must cover at least this fraction of the page height ...
EXT_SLANT_MIN = 0.20    # ... and be at least this fraction of all rows, to fit our own slant
STAPLE_MIN_HOLES = 5    # a staple line fitted from fewer holes is not a reference ...
STAPLE_MAX_RES = 10.0   # ... nor is one whose own holes scatter more than this (ref px).
                        #   p073/p104 fit +0.93 deg from 4 holes with 18.7 px residual --
                        #   4 sigma off the issue median -- which would have vetoed two
                        #   CORRECT boundaries. Bad references fall back to the issue median.
STAPLE_ANG_TOL = 0.5    # HARD CONSTRAINT (user): the boundary slant is within this many
                        #   degrees of the STAPLE line's slant. A larger difference is
                        #   very unlikely, so it is a misdetection, not a measurement.
                        #   Set to 0.5, not the stated 1.0: the accepted fits split into a
                        #   clean group at <=0.47 and a tail at >=0.83, and every page in
                        #   that tail with a TRUSTWORTHY staple line (p023 -1.06, p024
                        #   +1.13, p153 +1.16, all with 6 holes and <5 px residual) is
                        #   visibly wrong -- the line cuts diagonally across text, and all
                        #   three have an extent of only ~0.15.
                        #   The staple line is tight (max-residual ~5 px over 6 holes)
                        #   while our own free slant fit had 0.7 deg of noise -- larger
                        #   than the entire plausible range -- so this bound is pure gain.

# --- decision --------------------------------------------------------------- #
# z (accumulator peak in robust sigma) is REPORTED but is NOT a gate: it measures how
# dominant the winning line is within the band, which is high for a crisp text-column edge
# and low for a genuine but partial-height neighbour (p053 false z=17.3 vs p073 true
# z=5.8). The physically meaningful quantity is the size of the colour difference itself.
EXT_FRAC  = 0.35        # a row is in the EXTENT if its response reaches this fraction of
                        #   the extent top decile
EXT_MIN   = 0.06        # report an extent only if it covers at least this of the height
SMOOTH_Y  = 21          # smoothing of the per-row response (downscaled rows)
STEP_MIN  = 30.0        # FIRE iff the median colour step actually crossed by the fitted
                        #   line must be at least this (feature units), i.e. the two
                        #   backgrounds really do differ. Chosen ON A PLATEAU: any cut from
                        #   15 to 35 yields the SAME 42 pages, so the value is not a knife
                        #   edge. 60 was too high -- it rejected real pale pink / gray / blue
                        #   neighbours (p017, p160, p162, p153, p165, p125, p038). We can
                        #   afford a low cut because the +/-5 mm clip constraint bounds any
                        #   false positive to within the gutter margin anyway.

# --- overlay ---------------------------------------------------------------- #
OV_SCALE  = 4           # overlay downscale for viewing
COL_LINE  = (0, 255, 0)
COL_CLIP  = (255, 60, 255)


# --------------------------------------------------------------------------- #
def feat(rgb):
    """Colour-aware background vector f = [L, (R-G)*w, (G-B)*w]."""
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.stack([rgb.mean(-1), (R - G) * CHROMA_W, (G - B) * CHROMA_W], -1)


def load_band(page, thumb_dir=THUMB_DIR):
    """Return (band_feature_HxWx3 downscaled, sx, W, H, parity, to_abs).

    The band is oriented so that column index 0 == the binding edge, for BOTH
    parities (even pages are mirrored), so all downstream code is parity-free.
    """
    p = "%03d" % page
    im = Image.open(os.path.join(thumb_dir, p + ".png")).convert("RGB")
    W, H = im.size
    sx = W / REF_W
    parity = "even" if page % 2 == 0 else "odd"
    band = int(BAND * sx)
    if parity == "even":
        sub = im.crop((W - band, 0, W, H)).transpose(Image.FLIP_LEFT_RIGHT)
        to_abs = lambda inb: W - 1 - inb
    else:
        sub = im.crop((0, 0, band, H))
        to_abs = lambda inb: inb
    y0 = int(Y_MARGIN * H); y1 = H - y0
    sub = sub.crop((0, y0, band, y1))
    bw, bh = max(4, sub.size[0] // DS), max(4, sub.size[1] // DS)
    d = np.asarray(sub.resize((bw, bh), Image.BOX), np.float32)
    f = feat(d)
    if MED_XY > 1:
        f = median_filter(f, size=(MED_XY, MED_XY, 1))
    return f, sx, W, H, y0, parity, to_abs


def step_field(f, wm):
    """Signed STEP response: median(f over wm px inboard) - median(f over wm px outboard).

    MEDIAN, not mean. A mean treats "ink is present here" as a background change, so the
    edge of a dense TEXT COLUMN reads as a step just as strongly as a real colour boundary
    -- and a text column is long, straight and perfectly coherent, so it wins the argmax.
    (Observed: 24/24 inspected fires on the classified-ads pages sat on a column edge with
    identical cream paper on both sides of the true gutter.) A window median at the typical
    10-20% ink coverage returns the BACKGROUND on either side, so a text column responds
    ~0 while a teal/gray/red neighbour still responds fully. It is equally correct where
    the background is dark and the ink light (full-bleed ads) -- no polarity assumption.

    The two windows are adjacent and wm wide, so the response peaks on the boundary, and a
    slow gutter-shading ramp (no step) is ignored.
    """
    h, w, c = f.shape
    B = median_filter(f, size=(3, wm, 1))          # robust local background field
    D = np.zeros_like(f)
    D[:, wm:w - wm] = B[:, 2 * wm:] - B[:, :w - 2 * wm]
    return D


def accumulate(D, angles, xs, yc, rows=None):
    """A(x0, theta) = || SUM_y D(x0 + tan(theta)*(y-yc), y) ||  over the given rows.

    Returns (A [n_ang x n_x], Vec [n_ang x n_x x 3]) -- the vector sum is kept so the
    dominant colour direction of the winning line can be read back for the extent test.
    """
    h, w, c = D.shape
    ys = np.arange(h, dtype=np.float32) if rows is None else rows.astype(np.float32)
    Dr = D if rows is None else D[rows]
    Vec = np.empty((len(angles), len(xs), c), np.float32)
    for ai, a in enumerate(angles):
        sl = np.tan(np.deg2rad(a))
        # sample every (x0, y): x = x0 + sl*(y-yc)
        xx = xs[None, :] + sl * (ys[:, None] - yc)             # (nrows, nx)
        yy = np.repeat(np.arange(len(ys))[:, None], len(xs), 1)
        for ch in range(c):
            s = map_coordinates(Dr[..., ch], [yy.ravel(), xx.ravel()],
                                order=1, mode="nearest").reshape(xx.shape)
            Vec[ai, :, ch] = s.sum(0)
    return np.linalg.norm(Vec, axis=-1), Vec


def staple_slant(clip_entry, fallback=None):
    """Slant (deg, +x per +y) of the staple line, or `fallback` if it is not trustworthy.

    The clip is rigid, so a well-found line is tight (median max-residual 4.9 px over 6
    holes). But a line fitted from 4 holes that scatter 18 px is NOT a reference: p073 and
    p104 both yield +0.93 deg that way, 4 sigma off the issue median, which would veto two
    correct boundaries. Quality is judged on the holes themselves, not on the answer."""
    if not clip_entry:
        return fallback
    hs = [h for h in clip_entry.get("holes", []) if h[2]]
    if len(hs) < STAPLE_MIN_HOLES:
        return fallback
    x = np.array([h[0] for h in hs], float); y = np.array([h[1] for h in hs], float)
    coef, *_ = np.linalg.lstsq(np.stack([np.ones_like(y), y], 1), x, rcond=None)
    if np.abs(x - (coef[0] + coef[1] * y)).max() > STAPLE_MAX_RES:
        return fallback
    return float(np.rad2deg(np.arctan(coef[1])))


def issue_staple_slant(clip):
    """Median staple slant over the whole issue -- the fallback reference for pages whose
    own staple line is too poorly determined to use."""
    v = [staple_slant(c) for c in clip.values()]
    v = [x for x in v if x is not None]
    return float(np.median(v)) if v else 0.0


def refine_crossing(f, xl, sx):
    """Locate the boundary as the 50% CROSSING of the step, per row, sub-pixel.

    The coarse median step field is deliberately robust, and robustness costs
    localisation: a median does not ramp across a boundary, it switches, so a step yields
    a PLATEAU ~2*STEP_W wide rather than a peak. The argmax then picks an arbitrary
    plateau edge (measured: a constant -37 ref px bias, independent of step size) and in
    (x0, slant) space the plateau is a RIDGE -- which is why the free slant fit returned
    noise uncorrelated with the staple line.

    So: use the coarse fit only to read the two BACKGROUND COLOURS either side, project
    the band onto the axis joining them, and take the zero crossing of that projection.
    That is precisely "the 50% crossing of the printed step", with no threshold.

    Returns (crossings, valid) in downscaled px, one per row.
    """
    h, w, _ = f.shape
    ys = np.arange(h)
    o, ww = FINE_OFFS, FINE_WIN
    xi = np.clip(np.round(xl), o + ww, w - o - ww - 1).astype(int)  # round, not floor:
                                                    #   a floor here biases the sampled side
                                                    #   colours and the search centre by up to
                                                    #   1 ds px (= 6 ref px) toward the edge.
    out = np.stack([np.median(f[y, xi[y] - o - ww:xi[y] - o], axis=0) for y in range(h)])
    inn = np.stack([np.median(f[y, xi[y] + o:xi[y] + o + ww], axis=0) for y in range(h)])
    # Estimate the boundary's colour direction and size from the rows that ACTUALLY have
    # a boundary. A plain median over all rows destroys a partial-height neighbour: p170's
    # gray ad spans 21% of the page, so a global median made its step read 5 instead of 321.
    diff = inn - out
    mag = np.linalg.norm(diff, axis=1)
    sel = mag >= max(0.5 * STEP_MIN, 0.5 * np.percentile(mag, 90))
    if sel.sum() < MIN_ROWS_FINE:
        sel = np.ones(h, bool)
    c_out = np.median(out[sel], axis=0); c_in = np.median(inn[sel], axis=0)
    u = c_in - c_out
    n = float(np.median(mag[sel]))                    # step size, measured on those rows
    un = float(np.linalg.norm(u))
    if un < 1e-6 or n < 1e-6:
        return None, None, 0.0
    u = u / un
    mid = (c_in + c_out) / 2.0
    p = (f - mid) @ u                                 # <0 outboard, >0 inboard
    p = uniform_filter1d(p, FINE_SMOOTH_Y, axis=0)    # pool rows, not columns

    cross = np.full(h, np.nan)
    for y in range(h):
        a = max(1, xi[y] - FINE_SEARCH); b = min(w - 1, xi[y] + FINE_SEARCH)
        seg = p[y, a:b]
        sgn = np.sign(seg)
        k = np.where((sgn[:-1] < 0) & (sgn[1:] >= 0))[0]
        if k.size:
            j = k[np.argmin(np.abs(k + a - xi[y]))]    # crossing nearest the coarse line
            d = seg[j + 1] - seg[j]
            cross[y] = a + j + (0.0 if d == 0 else -seg[j] / d)
    return cross, np.isfinite(cross), float(n)


def _pick_peak(Z):
    """Pick the OUTERMOST strong peak of the accumulator Z[angle, x].

    Z is collapsed over angle (each x keeps its best slant), local maxima are found
    with PEAK_SEP non-maximum suppression, and every maximum reaching PEAK_KEEP of the
    global best is a candidate. The neighbour page lies beyond ALL of this page's own
    content, so the correct one is the candidate closest to the binding edge (smallest
    x index). Returns (angle_index, x_index).
    """
    prof = Z.max(axis=0)
    best = prof.max()
    cand = []
    for i in range(len(prof)):
        lo, hi = max(0, i - PEAK_SEP), min(len(prof), i + PEAK_SEP + 1)
        if prof[i] == prof[lo:hi].max() and prof[i] >= PEAK_KEEP * best:
            if not cand or i - cand[-1] > PEAK_SEP:
                cand.append(i)
    xi = cand[0] if cand else int(np.argmax(prof))
    return int(np.argmax(Z[:, xi])), xi


def parabola(y0, y1, y2):
    """Sub-sample peak offset of three equally spaced samples with the max at y1."""
    den = (y0 - 2 * y1 + y2)
    return 0.0 if den == 0 else 0.5 * (y0 - y2) / den


def transitions(f, lo, hi):
    """Per-row boundary b(y) = the OUTERMOST strong background STEP in the search window.

    Why the step field and not "does this pixel match my page's background": the paper
    darkens smoothly toward the fold (gutter shading), so an absolute match test never
    terminates -- the run walks past the real boundary into shaded paper (observed on
    p176). The step operator differences two ~1.8 mm windows, so a slow shading ramp
    responds barely at all while a printed background change responds fully. It is also
    blind to hairlines/rules, which the median filter has already removed.

    Outermost, not innermost: the neighbour lies beyond everything of ours. Rows that
    cross the NEIGHBOUR's own content (e.g. p176's orange box, outboard of its teal
    background) do vote for the wrong x -- they are a minority, and the Hough mode in
    detect() ignores them. That is exactly the job a mode does and a regression cannot.

    The threshold is DERIVED per page: k x the MAD of the step field itself (the page's
    own background noise), not a fixed level. Returns (b, thr).
    """
    h, w, _ = f.shape
    D = step_field(f, STEP_W)
    mag = np.linalg.norm(D, axis=-1)
    thr = max(TOL_MIN, TOL_K * 1.4826 * np.median(np.abs(mag - np.median(mag))))
    win = np.zeros_like(mag, bool)
    win[:, int(lo):int(hi) + 1] = True
    strong = (mag >= thr) & win
    b = np.where(strong.any(1), strong.argmax(1), 0).astype(np.float32)
    return b, thr


def fit_band(f, sx, parity, clip_inb=None, staple_ang=None, rows=None):
    """Fit the boundary line on a prepared band. Shared by detect() and selfcheck.py so
    the objective checks exercise exactly the production path.

    Two stages, because detection and localisation want opposite things:
      COARSE -- argmax over (x0, slant) of the accumulated median step field. The median
        makes it blind to ink coverage (vital: otherwise every text column fires) but that
        same robustness destroys sub-pixel localisation, see refine_crossing().
      FINE   -- read the two background colours either side of the coarse line, project
        the band onto the axis joining them, take the per-row ZERO CROSSING (the 50% point
        of the printed step), and fit the line as the MODE of those crossings.

    `rows` restricts both stages to a subset of rows (used by the split-half check).
    """
    h, w, _ = f.shape
    yc = h / 2.0
    D = step_field(f, STEP_W)

    lo = max(STEP_W + 1, int(X_LO * sx / DS))
    hi = min(w - STEP_W - 1, int(X_HI * sx / DS))
    if clip_inb is not None:
        lo = max(lo, int((clip_inb - CLIP_WIN * sx) / DS))
        hi = min(hi, int((clip_inb + CLIP_WIN * sx) / DS))
    if hi <= lo + 2:
        lo, hi = max(STEP_W + 1, int(X_LO * sx / DS)), min(w - STEP_W - 1, int(X_HI * sx / DS))
    xs = np.arange(lo, hi + 1, dtype=np.float32)

    # slant search window in BAND coordinates (the band is mirrored on even pages)
    band_staple = 0.0 if staple_ang is None else (staple_ang if parity == "odd" else -staple_ang)
    a_lo = max(-ANG_MAX, band_staple - STAPLE_ANG_TOL)
    a_hi = min(ANG_MAX, band_staple + STAPLE_ANG_TOL)
    angles = np.arange(a_lo, a_hi + 1e-9, ANG_STEP, dtype=np.float32)

    A, Vec = accumulate(D, angles, xs, yc, rows=rows)
    bg = np.median(A); mad = np.median(np.abs(A - bg)) + 1e-6
    ai, xi = np.unravel_index(np.argmax(A), A.shape)
    z = float((A[ai, xi] - bg) / (1.4826 * mad))
    x_coarse = float(xs[xi]); ang = float(angles[ai])

    ys = np.arange(h, dtype=np.float32)
    xl = x_coarse + np.tan(np.deg2rad(ang)) * (ys - yc)
    cross, ok, sep = refine_crossing(f, xl, sx)
    if rows is not None and ok is not None:
        keep = np.zeros(h, bool); keep[rows] = True
        ok = ok & keep

    railed = False
    sl = np.tan(np.deg2rad(ang)); x_peak = x_coarse; n_in = 0; span = (0.0, 0.0)
    if cross is None or ok.sum() < MIN_ROWS_FINE:
        railed = True
    else:
        cy, cx = ys[ok], cross[ok]
        best = (-1, x_coarse, ang)
        for aa in angles:                        # Hough: the MODE over the crossings
            t = np.tan(np.deg2rad(aa))
            pos = cx - t * (cy - yc)
            med = np.median(pos)
            m = np.abs(pos - med) <= FINE_TOL
            if int(m.sum()) > best[0]:
                best = (int(m.sum()), float(np.median(pos[m])), float(aa))
        n_in, x_peak, ang = best
        sl = np.tan(np.deg2rad(ang))
        for _ in range(2):                       # tighten by least squares on the inliers
            m = np.abs(cx - (x_peak + sl * (cy - yc))) <= FINE_TOL
            if m.sum() >= MIN_ROWS_FINE:
                M = np.stack([np.ones(int(m.sum())), (cy[m] - yc)], 1)
                coef, *_ = np.linalg.lstsq(M, cx[m], rcond=None)
                x_peak, sl = float(coef[0]), float(coef[1])
                ang = float(np.rad2deg(np.arctan(sl)))
                if not (a_lo - 1e-6 <= ang <= a_hi + 1e-6):
                    railed = True               # slant left the staple window -> reject
                    ang = float(np.clip(ang, a_lo, a_hi)); sl = np.tan(np.deg2rad(ang))
                n_in = int(m.sum())
        m = np.abs(cx - (x_peak + sl * (cy - yc))) <= FINE_TOL
        if m.any():
            span = (float(cy[m].min()) / h, float(cy[m].max()) / h)

    # Not enough span to measure a slant -> inherit the staple slant, refit the offset only.
    span_cov = (span[1] - span[0]) if n_in else 0.0
    if cross is not None and ok is not None and ok.sum() >= MIN_ROWS_FINE \
            and (span_cov < SPAN_SLANT_MIN or n_in / float(h) < EXT_SLANT_MIN):
        cy, cx = ys[ok], cross[ok]
        sl = np.tan(np.deg2rad(band_staple)); ang = float(band_staple)
        pos = cx - sl * (cy - yc)
        med = np.median(pos)
        m = np.abs(pos - med) <= FINE_TOL
        if m.sum() >= MIN_ROWS_FINE:
            x_peak = float(np.median(pos[m])); n_in = int(m.sum())
            span = (float(cy[m].min()) / h, float(cy[m].max()) / h)

    railed = bool(railed or x_peak <= xs[0] + 0.5 or x_peak >= xs[-1] - 0.5)
    return dict(x_peak=x_peak, sl=sl, ang=ang, z=z, step=sep, n_in=n_in,
                ext=n_in / float(h), span=span, railed=railed, h=h)


def detect(page, thumb_dir=THUMB_DIR, clip_inb=None, staple_ang=None):
    f, sx, W, H, y0, parity, to_abs = load_band(page, thumb_dir)
    r = fit_band(f, sx, parity, clip_inb, staple_ang)
    inb_mid = (r["x_peak"] + 0.5) * DS
    ang_page = r["ang"] if parity == "odd" else -r["ang"]
    half = r["h"] / 2 * DS
    return dict(page=page, parity=parity,
                found=bool(r["step"] >= STEP_MIN and not r["railed"] and r["ext"] >= EXT_MIN),
                railed=bool(r["railed"]),
                column_x=float(to_abs(inb_mid)), inboard_mid=float(inb_mid),
                inboard_top=float(inb_mid - r["sl"] * half),
                inboard_bot=float(inb_mid + r["sl"] * half),
                angle_deg=float(ang_page), staple_deg=staple_ang, z=r["z"],
                step=r["step"], vote_frac=r["ext"], n_vote=r["n_in"],
                extent_span=r["span"], W=W, H=H, y_off=y0)


def overlay(page, r, thumb_dir=THUMB_DIR, clip=None):
    p = "%03d" % page
    im = Image.open(os.path.join(thumb_dir, p + ".png")).convert("RGB")
    W, H = im.size
    sc = OV_SCALE
    small = im.resize((W // sc, H // sc), Image.LANCZOS)
    dr = ImageDraw.Draw(small)
    par = r["parity"]
    yA, yB = r["y_off"], H - r["y_off"]

    def abs_x(inb):
        return (W - 1 - inb) if par == "even" else inb
    xt, xb = abs_x(r["inboard_top"]), abs_x(r["inboard_bot"])
    if r["found"]:
        dr.line([xt / sc, yA / sc, xb / sc, yB / sc], fill=COL_LINE, width=2)
    if clip is not None:
        dr.line([clip / sc, 0, clip / sc, H / sc], fill=COL_CLIP, width=1)
    dr.rectangle([4, 4, 640, 40], fill=(0, 0, 0))
    dr.text((10, 12), "p%s %s  %s  x=%.0f ang=%+.3f step=%.1f vote=%.2f"
            % (p, par, "FIRE" if r["found"] else "none", r["inboard_mid"],
               r["angle_deg"], r["step"], r["vote_frac"]), fill=(255, 255, 255))
    out = os.path.join(OUT_DIR, "shear_%s.png" % p)
    small.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--overlay", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    pages = list(range(1, 177)) if a.all else a.pages
    clip = {}
    if os.path.exists(CLIP_JSON):
        clip = json.load(open(CLIP_JSON))

    issue_ang = issue_staple_slant(clip) if clip else 0.0
    out = {}
    for n in pages:
        c = clip.get("%03d" % n)
        cx = c["column_x"] if c else None
        ci = None
        if c is not None and c["confidence"] >= CLIP_CONF:
            ci = (c["W"] - cx) if (n % 2 == 0) else cx
        r = detect(n, clip_inb=ci, staple_ang=staple_slant(c, fallback=issue_ang))
        if cx is not None:
            cinb = (c["W"] - cx) if r["parity"] == "even" else cx
            r["clip_inboard"] = cinb
            r["clip_delta"] = r["inboard_mid"] - cinb
        out["%03d" % n] = r
        print("p%03d %-4s %-4s x=%6.1f ang=%+6.3f step=%5.1f vote=%.2f n=%4d clipd=%s"
              % (n, r["parity"], "FIRE" if r["found"] else "none", r["inboard_mid"],
                 r["angle_deg"], r["step"], r["vote_frac"], r["n_vote"],
                 ("%+.0f" % r["clip_delta"]) if "clip_delta" in r else "-"))
        if a.overlay:
            overlay(n, r, clip=(None if cx is None else cx))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print("wrote", a.json)


if __name__ == "__main__":
    main()
