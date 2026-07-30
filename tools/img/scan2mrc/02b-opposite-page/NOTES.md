# 02b — Opposite-page / spine detection: signal probe

Goal of step 02b: find the **spine (fold) line** on the binding side of each split
page and mark everything BEYOND it (the neighbor page that bled into the A3 scan)
as unknown/alpha. This note records a probe of which signal locates the spine most
reliably, and the spine's measured geometry.

Input probed: `/Users/mist/DNB/8609/thumbs_600/NNN.png` (600 dpi, RGB, ~5200×7188).
Master = these ×4 (2400 dpi). EVEN page → neighbor overlap on the **RIGHT** edge;
ODD page → **LEFT** edge (binding/spine side).

Scripts here:
- `spine.py`       — **production detector.** Supersedes everything below.
- `spine_matte.py` — applies the spine line as alpha (hardened from the `spine_v2` prototype).
- `bg_spine.py`, `clip_holes.py`, `hole_masks.py` — supporting analysis still in use.

The probe that produced the findings below used five more scripts (`probe_spine.py`,
`diag_profiles.py`, `overlay_spine.py`, `simple_spine.py`, `spine_v2.py`) plus
`shear_spine.py` and its scorer `selfcheck.py`. All were superseded by `spine.py` and have
been **deleted** — 1388 lines that no longer ran and that a reader had to rule out one by one.
The findings they established are recorded below, which is the part worth keeping; the code
itself is in git history if it is ever needed again.

All outputs go to `/Users/mist/DNB/8609/tmp/` only.

---

## Candidate signals — findings

**1. Gutter shadow (luma trough near the fold): WEAK / unreliable here.**
The `paper60` column profile (60th-pct luma = paper shade with ink excluded) is nearly
FLAT (~195–205) across the whole inner band on every page probed — these scans are flat,
there is no strong fold shadow. A faint vertical fold line is visible on some pages
(e.g. p070, p100, montage) but it is too shallow to threshold reliably. **Do not use as
the primary signal.** Only a fallback where nothing else exists.

**2. Neighbor-page content boundary (ink-density + colour step): THE WINNER.**
Where the neighbor page bled in, `dark_frac` (fraction of dark px), `sat_mean` (colour),
and even the halftone speck count all **step up together at the same x** and agree. The
clean-paper margin between this page and the neighbor is a band of ~0 dark_frac / low sat;
the neighbor block is a sharp jump. Detected robustly by: find the ink/colour block
**nearest the binding border**, cut at its page-facing edge. Crisp and repeatable
(residuals typically 1–8 px over a 7188 px height). Cross-validated against shadow/specks
on p010 (all three agreed at the fold).

**3. Staple / clip holes & fold specks: present but NOT independently usable.**
Isolated dark dots (dust/perforations) do run down the gutter (visible in every edge crop),
and fold-dirt smudges appear (e.g. brown blobs on p040/p041). But the specks are sparse and
the "speck count" signal is dominated by neighbor **halftone** dots, so it collapses into
signal #2 rather than adding independent information. Not a reliable standalone line anchor.

**4. White gutter gap: used implicitly, not a positive locator.**
The clean margin IS the gap that separates page from neighbor (the CLEANRUN test that ends
the neighbor block). It never locates the spine by itself — it only bounds signal #2.

---

## Geometry of the spine

- **Straight, not curved.** RANSAC line residuals across 79 confident pages: mean 3.9 px,
  p90 8.4 px, over a 7188 px height. A straight line fits; no measurable curvature. Theil-Sen
  / iterative-reject line fit is sufficient — no polynomial/spline needed.
- **Near-vertical, small tilt.** Confident-page tilt: mean −0.01°, std 0.46°; the bulk within
  **±0.4°**. A handful reach ~0.8–1.2° (p014, p024, p106). One outlier −3.35° (p175) is NOT
  fold tilt — it is a **skewed neighbor photo edge** (the user's "images skewed vs text" case);
  the cut still correctly follows the neighbor's real content edge.
- **Tilt vs page text:** the fitted line tracks the neighbor-INK edge. On text-neighbor pages
  this ≈ the fold and is near-vertical (page text is deskewed to ~0°, so they roughly agree).
  On image-neighbor pages the edge can carry the neighbor image's own skew (p175) — a few
  hundredths to a few degrees off the fold. For masking that is fine (we want the neighbor's
  edge, not the abstract fold).
- **Spine position:** even pages ~median **79 px** inside the RIGHT border (range −4…354);
  odd pages ~median **45 px** inside the LEFT border (range −7…~300). i.e. the split usually
  left only a thin neighbor sliver, but the amount varies widely and is NOT parity-dependent.

## Even vs odd
Fully symmetric — mirror the same logic (neighbor near RIGHT border for even, LEFT for odd).
No reliability difference. Confident: 47 even / 32 odd. The *amount* of neighbor bleed varies
per page (thin sliver → wide coupon/ad), driven by how the A3 scan was split, not by parity.

---

## Recommended approach for the real 02b

1. **Primary signal = neighbor-content boundary** (`spine_v2.py` logic): per horizontal band
   (~28 bands), compute per-column `dark_frac` (luma<95) and `sat_mean`; `content = dark_frac>0.05
   OR sat>0.17`. Find the content block that **starts within ~240 px of the binding border**
   (gate rejects the page's own text) and whose width ≥ ~20 px; the band's boundary point =
   that block's page-facing edge. Reject bands where the block reaches the interior band limit
   (full-bleed / merged → no clean gap).
2. **Fit** a straight line to the band points with **iterative Theil-Sen** (residual-reject at
   ~45 px). Report tilt + residual.
3. **Confidence gate:** confident iff ≥6 evidence bands AND residual < 45 px. On this issue that
   is **~74/176 pages (~42%)** after the interior-limit guard.
4. **Fallback for low-confidence pages (~58%)** — verified to be pages with **no neighbor bleed**
   (clean margin all the way to the border; see `nc_montage.png`). Since there is nothing to
   remove, the safe action is: **do not crop / mark nothing** (or, if a nominal cut is required,
   use a conservative fixed offset = the per-issue median spine offset from the border, ~45–80 px,
   which sits in clean margin and removes no page content). The faint gutter shadow could refine
   this but is too weak to depend on.
5. **Apply at full res (2400 dpi):** detect on the 600-dpi thumb (fast), scale the fitted line
   ×4 for the master. Cut ON the line; everything OUTWARD → alpha/unknown.

### Failure cases / limitations (honest)
- **No-neighbor pages** (majority): no crisp signal. Handled by fallback above; low risk because
  nothing needs removing. If a page truly needs a spine there, only the faint gutter shadow or a
  fixed offset is available — low confidence.
- **Full-bleed to the binding** (page content runs to the border with no clean gap): the
  content-boundary method cannot separate page from neighbor → interior-limit guard rejects it
  (goes to fallback). None cleanly hit in the sample, but it is the real hard case.
- **Skewed neighbor images** (p175): the fitted edge follows the neighbor image's own skew, not
  the fold. Acceptable for masking (removes exactly the neighbor), but the reported "tilt" is not
  the fold angle — don't feed it back as a page-deskew estimate.
- **Ragged neighbor edges** (notched coupons, rotated text, e.g. p011): boundary points scatter →
  high residual → correctly gated to not-confident rather than producing a wrong line.
- The gutter shadow being weak means we have **no independent geometric confirmation** of the
  fold on no-neighbor pages; confidence there is inherently limited.

### Evidence (probe overlays inspected in `/Users/mist/DNB/8609/tmp/`)
- Correct near-vertical fits: `spine_010,016,040,041,133,141.png` (green line on the
  page/neighbor boundary; neighbor colour/text strip outward of it).
- No-neighbor / low-confidence: `spine_070,100.png` + `nc_montage.png` (008,060,112,065,113,127) —
  clean margin, faint fold only, correctly flagged.
- Skewed-neighbor edge case: `spine_175.png` (−3.35°, neighbor photo edge).
- Diagnostics: `diag_010.png`, `diag_011.png` (flat paper60 = no shadow; crisp dark/sat/speck step).

---

## PRODUCTION TOOL — `spine_matte.py`  (hardened, supersedes `spine_v2.py`)

`spine_v2.py` is kept as the readable prototype; **`spine_matte.py` is the deliverable** and
matches the `02-matte/bed_matte.py` conventions: a commented resolution-relative constants block
at top (spatial constants @600dpi, scaled by `dpi/600`), a `spine_matte(rgb, dpi, page_no,
return_meta)` callable returning `(rgba, pct_cleared, meta)`, and a CLI
`spine_matte.py IMG OUT --dpi N [--magenta] [--page P]` that writes an RGBA alpha matte
(alpha 0 = neighbor/unknown) and, with `--magenta`, a 50% magenta overlay over the cut region.

### Final method
1. **Per-band neighbor-content boundary** (unchanged winning signal): split the height into
   `NB=28` bands; over the binding-side `INNER_W=1200px` search strip compute per-column
   `dark_frac` (luma<95) and `sat_mean`; `content = dark_frac>0.05 OR sat>0.17`. Take the
   neighbor block nearest the border (must START within `BORDER_NEAR=240px` of the border →
   rejects the page's own text; width ≥ `BLOCKMIN=20px` → rejects specks; must not reach the
   interior guard → rejects full-bleed/merged). The block's page-facing edge = that band's
   boundary point.
2. **Robust line fit** — iterative Theil-Sen with residual reject at `RESID_THR=45px`.
3. **ANGLE CAP `SPINE_ANGLE_MAX_DEG = 1.5°`** (the new hard requirement). The deskewed spine is
   near-vertical (real slant ≤~1°). If the robust *raw* tilt exceeds ±1.5° it is a false lock on
   a **skewed neighbor image edge or ragged coupon**, not the spine.
4. **Confidence gate (HIGH/LOW).** HIGH ⟺ `n_inliers ≥ 6` **AND** `resid < 45px` **AND** the raw
   fit is **within the ±1.5° cap**. Only HIGH pages are cut; LOW → **no cut** (empty matte).
5. **Cut:** everything BEYOND the (capped) line toward the binding → alpha 0, with a small
   `OVERCUT=6px` toward the page so the whole neighbor is removed (a few px of the page's own
   inner margin under the matte is fine — the A4 crop trims it). Even → neighbor RIGHT, odd →
   neighbor LEFT (fully symmetric, mirror logic).
6. Detection is on the 600-dpi thumb; **full-res (2400) apply is a later Rust step** (scale the
   fitted line ×4) — not built here.

### The angle-cap decision (why REJECT-over-cap, not refit-and-keep)
When the raw fit exceeds the cap we **reject the page (→ no cut)** rather than force a capped line
and cut on it. Considered alternatives per the brief:
- **(a) constrain-refit to |angle|≤cap and keep** — rejected. A near-vertical line laid over a
  *genuinely tilted* neighbor edge cannot both cover the neighbor and avoid eating the page margin
  at the divergent end; it produces a wrong-tilt cut. (We still *compute* the capped line and report
  `tilt_deg` vs `raw_tilt_deg` for diagnostics — we just don't cut on it.)
- **(b) vertical line at boundary x** — same problem, plus it ignores the measured edge entirely.
- **chosen: reject → no cut.** A true spine essentially never exceeds 1.5° (probe: only p175 did,
  and it was a skewed photo edge), so an over-cap fit is strong evidence the boundary is *not* the
  spine. Leaving the whole strip for the downstream A4 crop is strictly safer than a wrong-tilt cut,
  and is consistent with how ragged-edge pages (p011) are already handled (no cut, residue → A4 crop).
  This directly satisfies the requirement that p175's −3.35° lock is now **rejected**, not cut.

Verified over all 176 pages: **every ACCEPTED page has |tilt| ≤ 1.5°** (see run report), and
p175 / p069 (+4.85°) / p157 (+11.14°) — all skewed-neighbor / full-bleed-montage edges — are now
**rejected with zero cut**.

### Even vs odd
Fully symmetric: even → neighbor near the RIGHT border, odd → near the LEFT (binding) border. Same
thresholds, same gate; parity comes from `page_no` (CLI derives it from the filename integer if
`--page` is absent).

### Failure cases / limitations (honest, as shipped)
- **No-neighbor pages** (the majority): clean margin to the border → few/no evidence bands → LOW →
  no cut. Correct (nothing to remove). No independent geometric confirmation of the fold exists
  (gutter shadow too weak), so we deliberately never invent a cut here.
- **Skewed-neighbor images** (p175 −3.35°): now **rejected by the angle cap** → no cut; the neighbor
  strip is left for the A4 crop. (Trade-off: we no longer remove that neighbor in 02b, but we never
  risk a wrong-tilt cut into page content.)
- **Full-bleed / merged to the binding** (e.g. p157, a full-bleed montage ad whose neighbor edge is
  a steep +11°): interior-guard and/or the angle cap reject it → no cut. The hard case; left for the
  A4 crop.
- **Ragged neighbor edges** (notched coupons, p011): scattered boundary points → high residual →
  LOW → no cut (residue left for A4 crop).
- **Over-cut bias is intentional and bounded:** the 6px overcut only reaches into the page's own
  inner *margin* (trimmed at A4 crop); the border-near + block-width + interior guards ensure a full
  content column is never taken.

### Evidence — production overlays (`--magenta`, inspected in `/Users/mist/DNB/8609/tmp/spm_NNN.png`)
- Confident even cuts: `spm_010, spm_016, spm_040.png` — magenta covers exactly the RIGHT neighbor
  strip beyond a near-vertical line; page content clean.
- Confident odd cuts: `spm_041, spm_133, spm_141.png` — magenta over the LEFT neighbor page bleed;
  page content clean.
- No-neighbor (zero magenta): `spm_008.png` (even), `spm_100.png` (even), `spm_011.png` (odd,
  ragged coupon left uncut).
- Rejected by angle cap (zero magenta): `spm_175.png` (raw −3.35°), `spm_069.png` (raw +4.85°),
  `spm_157.png` (raw +11.14°, full-bleed montage).
</content>

---

## CURRENT TOOL — `shear_spine.py` (supersedes `bg_spine.py`)  [v6]

Scope (set by the user): detect the **background-colour difference** between this page and
the neighbour that bled into the A3 scan, and only that. Cream-on-cream is unobservable and
is out of scope. "The line" is the 50% crossing of the printed colour step.

NOTE on the sheet: most spreads are two pages on ONE folded sheet (no paper edge, no ridge),
and this holds for EVERY page (confirmed by the user): each scan is half of an A3 flatbed
scan with some overlap, always A3 sheets. There is no paper edge and no shadow ridge
anywhere in the issue. (An earlier revision of this note claimed p020 was a physical page
edge with a separate sheet behind it — that was a misreading and is false.)

### Two stages — detection and localisation want opposite things
```
COARSE  A(x0,theta) = || SUM_y D( x0 + tan(theta)*(y-yc), y ) ||
        D = median(f, 1.8mm inboard) - median(f, 1.8mm outboard),  f = [L, (R-G)k, (G-B)k]
FINE    project the band onto the axis joining the two background colours;
        the boundary is the per-row ZERO CROSSING; the line is the MODE of those crossings.
```
The MEDIAN in the coarse stage is essential (a mean treats "ink is present" as a background
change, so every classified-ads text column fires — 24/24 inspected false fires were exactly
that), but robustness costs localisation: **a median does not ramp across a boundary, it
switches, so the coarse response is a PLATEAU ~2w wide, not a peak.** The argmax then picks
an arbitrary plateau edge, and in (x0, slant) space that plateau is a RIDGE — which is why a
free slant fit returned 0.7 deg of noise, uncorrelated with the page skew (r=-0.05) or the
staple line (r=-0.04), i.e. larger than the entire plausible range. Hence the fine stage.

### Objective validation — `selfcheck.py`, no hand-labelled pages
* **Synthetic recovery** (known offset + slant pasted on a real gutter band):
  position error **-3 band px** (exactly the harness's own half-pixel ramp definition),
  slant error **<=0.005 deg**. Before the fine stage: **-37 px and up to 0.36 deg**.
* **Split-half consistency** on pages where the test is valid (neighbour spans both halves,
  ext>=0.5, n=18): median |dx| **1.8 px = 0.08 mm**, p90 46 px.
  Both checks must run under the SAME constraints as production (clip window + staple slant)
  or they measure a different estimator — an earlier version passed neither and reported a
  tail production does not have.

### Constraints from the user — both hard, both physical
* **+/-5 mm from the CLIP-HOLE line.** Colour alone provably cannot do this: "cream | our own
  solid black panel" (false) and "cream neighbour | our full-bleed gray ad" (true) are the
  SAME measurement. The hole-free alternative (outboard-strip uniformity) was tested and
  FAILS — false fires score 1.4-2.7, cleaner than true ones at 18-47. Used as a search BOUND
  only; position and slant remain a pure colour measurement.
* **Slant within 1 deg of the STAPLE LINE** (fitted through the hole centres). Tightened to
  **0.5 deg** on evidence: accepted fits split into a clean group at <=0.47 and a tail at
  >=0.83, and every tail page with a trustworthy staple line was visibly wrong.
* **The staple reference is itself quality-gated** (>=5 holes, <=10 px residual). p073/p104
  fit +0.93 deg from 4 holes scattering 18.7 px — 4 sigma off the issue median — which would
  have vetoed two CORRECT boundaries. Bad references fall back to the issue median slant.
* **Slant is only measurable with enough span** (its standard error goes as 1/span). Below
  35% extent the slant is INHERITED from the staples and only the offset is fitted. This
  fixed the visibly wrong diagonals on p023 (-0.63 deg) and p024 (-0.30 deg) at extents of
  0.16/0.11, without discarding correct low-extent pages (p170's gray ad spans 20%).

A fit that rails against any bound is REJECTED, never clamped — clamping is what hid the old
detector's misdetections.

### Decision
`step >= STEP_MIN` (30.0, chosen on a PLATEAU: any cut from 15 to 35 selects the same set)
AND not railed AND a minimum extent. `z` is reported but is NOT a gate — it is high for a
crisp text-column edge (p053 z=17.3) and low for a genuine partial-height neighbour (p073
z=5.8).

### Result over the issue (176 pages)
**46 fire.** Every line within **4.8 mm** of the clip column and **0.45 deg** of the staple
slant. Slant spread **0.186 deg** (was 0.575 with a free fit), full range only +/-0.32 deg —
no diagonals remain. Slant inherited from the staples on 23 of 46.
Contact sheet `/Users/mist/DNB/8609/tmp/sheet_v6.png`; per-page overlays `tmp/shear_NNN.png`
(green = fitted line, magenta = clip column, an independent cross-check not fed to the fit).

Vision-verified this round: p020 (the reported failure), p023, p024, p132, p157, p175, p002,
p124, p038, p139 — all correct after the fixes; p153 correctly rejected.

### Known residual limitation
Pages where OUR OWN content edge (a solid panel) happens to lie within 5 mm of the gutter are
indistinguishable from a true boundary by any measurement here (p058/p080/p097/p119 are the
candidates). They are bounded to <=5 mm, i.e. inside the gutter margin, so the error is small,
but they are not resolved.

### Not built
Full-res (2400 dpi) apply. Detection is on the 600-dpi thumb; scale the fitted line x4.
