#!/usr/bin/env python3
"""ROBUST LINE FIT -- the shared core of every boundary detector in this pipeline.

Both problems in scan2mrc are the same problem: find a line so that all of one material is
on one side and as little of the other material as possible is on that side.

    02b/spine.py   per ROW: where does the neighbour's background end?
    02-matte       per LINE: where does the scanner bed / cardboard insert end?

They differ only in how CANDIDATES are produced (a chroma-difference peak vs a
backing->page material transition) and in the fire/don't-fire test afterwards. The fit in
between is identical, so it lives here once.

    fit(cand, ...) -> (line, vote_frac, slope)

WHY A MODE, NOT A REGRESSION. Each line contributes up to N candidates; the fit takes the
(offset, slope) that the most lines AGREE on. A line whose candidates are nonsense votes
where nobody else does and is ignored -- so no outlier fence, no coverage percentile, no
smoothing is required. Every one of those mechanisms was tried in bed_matte when its fit was
a constrained optimiser over a single first-hit candidate per line, and each one broke
something else:

    walk stops in a transition blur -> gap bridging -> leapt through an ad's black TEXT
    deep outlier lines              -> MAD fence    -> too tight left bed, too loose over-cut
    spiky depths                    -> smoothing    -> fit disagreed with what it must cover

MARGIN IS NOT PART OF THE FIT. This returns where the boundary IS. Any safety margin is the
caller's, added afterwards. Conflating the two (a coverage percentile that also set the
margin) is why tightening "cut less of our page" immediately broke "leave no stripe".
"""
import warnings
import numpy as np

ACCEPT_TRIES = 24     # max accept() evaluations per fit (each can cost a full-window mask)


def fit(cand, n_lines=None, tol=6.0, slope_max_deg=1.1, slope_step_deg=0.05,
        slope_center_deg=0.0, curve_max=0.0, min_frac=0.02, prefer_deepest=0.0,
        min_vote_frac=0.0, accept=None):
    """Fit one line through per-line candidate positions.

    cand             (N, K) candidate positions per line; negative = unused slot
    tol              a line agrees if one of its candidates is within this many px
    slope_max_deg    searched about slope_center_deg (a physical bound, e.g. page skew)
    curve_max        if > 0, allow a quadratic bow up to this peak-to-peak, bounded over the
                     range the curve is APPLIED to -- not over the points it was fitted on,
                     which is how an earlier version extrapolated a curve that cut 35mm of
                     clean paper
    prefer_deepest   if > 0, among lines whose agreement reaches this FRACTION of the best
                     line's, take the DEEPEST rather than the most popular. An edge can carry
                     two genuine boundaries -- p001's bottom is insert, then a transition
                     blur, then a 6px black bed strip, then page -- and the plain mode picks
                     the more populous shallower one, leaving the strip standing. "All the
                     backing on one side" (rule 1) means the deepest line that is still
                     properly supported. Leave at 0 where the deepest boundary is not wanted.
    min_vote_frac    a deeper line is only eligible if it keeps at least this fraction of ALL
                     lines in agreement. Without this the deepest-preference could pick a line
                     the caller's own decision test then rejects, so the edge was dropped
                     entirely and NOTHING was cut -- p044's bottom went from a correct cut to
                     188px standing on 92% of its lines.
    accept           optional callable(offset, slope) -> bool, consulted for the
                     deepest-preference. Votes alone are not enough to justify going deeper:
                     a deep line inside the page can still collect them (p015's top jumped
                     from 20px to 395px). The caller decides -- for bed_matte, a deeper line
                     is legitimate only if what it ENCLOSES is predominantly backing, which is
                     rule 1 stated directly.
    returns (line[N], vote_frac, slope, peak_contrast)
    """
    cand = np.asarray(cand, float)
    N = cand.shape[0] if n_lines is None else n_lines
    y = np.arange(N, dtype=np.float64)
    yc = N / 2.0
    ok = cand >= 0
    floor = max(8, int(min_frac * N))
    if ok.sum() < floor:
        return np.zeros(N), 0.0, 0.0, 0.0

    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN rows are lines with no candidate
        best = (-1, 0.0, 0.0)
        cands = []          # (votes, offset, slope) for the deepest-preference pass
        for deg in np.arange(slope_center_deg - slope_max_deg,
                             slope_center_deg + slope_max_deg + 1e-9, slope_step_deg):
            sl = np.tan(np.deg2rad(deg))
            pos = np.where(ok, cand - sl * (y - yc)[:, None], np.nan)
            flat = pos[np.isfinite(pos)]
            if flat.size == 0:
                continue
            lo, hi = float(flat.min()), float(flat.max())
            if hi - lo < tol:
                c0 = lo
            else:
                hist, edges = np.histogram(flat, bins=np.arange(lo, hi + tol, tol))
                c0 = float(edges[int(np.argmax(hist))] + tol / 2)
            # every histogram peak, not just the tallest: a second genuine boundary shows up
            # as a second peak, and prefer_deepest needs to see it
            if hi - lo < tol:
                peaks = [(int(np.isfinite(flat).sum()), lo)]
            else:
                peaks = [(int(h), float(edges[i] + tol / 2))
                         for i, h in enumerate(hist) if h > 0]
            for nvote, c in peaks:
                agree = np.nanmin(np.abs(pos - c), axis=1) <= tol
                n = int(agree.sum())
                if n <= 0:
                    continue
                v = pos[agree]
                v = v[np.isfinite(v)]
                v = v[np.abs(v - c) <= tol]
                off = float(np.median(v)) if v.size else c
                cands.append((n, off, float(sl)))
                if n > best[0]:
                    best = (n, off, float(sl))
        if cands and (prefer_deepest > 0 or accept is not None):
            thr = max(prefer_deepest * best[0], min_vote_frac * N)
            pool = [c for c in cands if c[0] >= thr]
            # one accept() call can cost a full-window mask, so collapse near-duplicate lines
            # and evaluate at most ACCEPT_TRIES of them, deepest (or best-supported) first
            seen, uniq = set(), []
            for c in sorted(pool, key=lambda c: (-c[1] if prefer_deepest > 0 else -c[0])):
                k = round(c[1] / max(tol, 1e-9))     # by DEPTH only -- including the slope in
                if k not in seen:                    # this key made 45 slope variants of one
                    seen.add(k)                      # bad depth eat the whole try budget
                    uniq.append(c)
            ok_pool = [c for c in uniq[:ACCEPT_TRIES]
                       if accept is None or accept(c[1], c[2])]
            if ok_pool:
                best = ok_pool[0] if prefer_deepest > 0 else max(ok_pool, key=lambda c: c[0])
            elif accept is not None:
                # NOTHING WELL-SUPPORTED IS ACCEPTABLE -- fall back to the best-supported line
                # that IS, rather than dropping the edge. Dropping it was a rule-1 failure: on
                # p130's top the deepest line ran 390px into the page, purity rightly vetoed it,
                # and the edge was then left entirely uncut even though 90% of its scanlines
                # showed real bed. A vetoed line means "not that one", never "cut nothing".
                seen = set()
                for c in sorted(cands, key=lambda c: -c[0]):
                    k = round(c[1] / max(tol, 1e-9))
                    if k in seen:
                        continue
                    seen.add(k)
                    if len(seen) > ACCEPT_TRIES:
                        break
                    if accept(c[1], c[2]):
                        best = c
                        break
        _, x0, sl = best

        # least squares on the agreeing lines, twice
        for _ in range(2):
            line = x0 + sl * (y - yc)
            near = np.abs(np.where(ok, cand, np.nan) - line[:, None])
            m = np.nanmin(near, axis=1) <= tol
            if int(m.sum()) < floor:
                break
            pick = np.where(ok, cand, np.nan)[m]
            sel = np.nanargmin(np.abs(pick - line[m][:, None]), axis=1)
            val = pick[np.arange(int(m.sum())), sel]
            A = np.stack([np.ones(int(m.sum())), y[m] - yc], 1)
            coef, *_ = np.linalg.lstsq(A, val, rcond=None)
            x0, sl = float(coef[0]), float(coef[1])
            deg = np.rad2deg(np.arctan(sl))
            lo_d, hi_d = slope_center_deg - slope_max_deg, slope_center_deg + slope_max_deg
            if not (lo_d <= deg <= hi_d):
                sl = float(np.tan(np.deg2rad(np.clip(deg, lo_d, hi_d))))

        line = x0 + sl * (y - yc)
        near = np.abs(np.where(ok, cand, np.nan) - line[:, None])
        m = np.nanmin(near, axis=1) <= tol
        vote_frac = float(m.mean())

        # PEAK CONTRAST -- how much the chosen line stands out from ANY other line at this slope.
        # vote_frac alone cannot answer that: with ~10 candidates per line, an arbitrary offset
        # collects 50-90% agreement by chance, so a screened edge with no boundary at all scored
        # 0.66 and a real bed edge scored 0.55. Contrast compares the winner against the typical
        # offset instead, and the two separate cleanly (a real boundary ~5x, texture ~1.2x).
        pos = np.where(ok, cand - sl * (y - yc)[:, None], np.nan)
        flat = pos[np.isfinite(pos)]
        contrast = 0.0
        if flat.size:
            lo, hi = float(flat.min()), float(flat.max())
            if hi - lo >= 2 * tol:
                centres = np.arange(lo, hi, tol) + tol / 2
                counts = np.array([int((np.nanmin(np.abs(pos - c), axis=1) <= tol).sum())
                                   for c in centres])
                nz = counts[counts > 0]
                med = float(np.median(nz)) if nz.size else 0.0
                contrast = float(int(m.sum()) / med) if med > 0 else 0.0
            else:
                contrast = float("inf")     # every candidate at one depth: a perfect boundary

        if curve_max > 0 and int(m.sum()) >= 32:
            pick = np.where(ok, cand, np.nan)[m]
            sel = np.nanargmin(np.abs(pick - line[m][:, None]), axis=1)
            val = pick[np.arange(int(m.sum())), sel]
            c2 = np.polyfit(y[m] - yc, val, 2)
            curve = np.polyval(c2, y - yc)
            if float(np.ptp(curve)) <= curve_max:      # bounded over the APPLIED range
                line = np.maximum(curve, line - tol)

    return line, vote_frac, float(sl), contrast
