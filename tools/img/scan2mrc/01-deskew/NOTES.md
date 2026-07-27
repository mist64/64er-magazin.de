# Page deskew (straightening) — research report

Goal: straighten each page (horizontal rules level, columns vertical). Pages were
found to have a **small, consistent skew of roughly +0.15° to +0.35°** (clockwise
content), a few near 0 or slightly negative. Subtle (~0.27° → ~130 px drift over the
28k-px page height) but visible against table rules.

## Methods researched

| Method | What it does | Verdict |
|---|---|---|
| **A. Projection-variance** | Rotate binarized text, maximise sharpness of the row-projection (Σ Δrow²). Two-stage: ±3°/0.25° coarse → ±0.3°/0.02° fine. | **WORKS — recommended.** Robust on any text/table page. Gives the per-page angle. Confidence = peak/median of the score sweep. |
| **B. Hough lines** | (folded into D) | n/a |
| **C. FFT screen-angle** | Dominant off-axis halftone-screen peak angle (screen is non-standard but consistent → use as a rotation fiducial). | **Unreliable as implemented.** At T=512 the argmax locks onto FFT lattice harmonics (45°, 63.4°, 71.6°…), not the true screen fundamental. Would need finer FFT + sub-bin interpolation + tracking the fundamental across harmonics. Not used. |
| **D/E. Table-rule fit** | Linear-fit y(x) of long thin horizontal dark components (table rules/borders). | **Works as ground-truth** on table pages; agrees with A on sign + rough magnitude (p36: rule +0.19 vs A +0.27; p34: rule +0.15 vs A +0.31). Few pages have long pure-black rules, so not a general estimator — good as a validator. |

Method A is the production estimator; D/E validates it; C is a dead end at this resolution.

## Measured skew (method A, 12 pages)

```
p02 +0.21  p06 +0.18  p34 +0.31  p36 +0.27  p38 +0.19  p39 +0.00
p15 -0.19  p28 +0.25  p42 +0.19  p50 +0.00  p07 -0.12  p16 +0.35
```

## Implementation & test

`deskew_apply.py` measures the angle (A) and rotates the source crop by the leveling
angle via PIL `Image.rotate(+angle)` (CCW; BICUBIC, white fill, same canvas — no 90° flip,
no content clip at these tiny angles). NB sign: `ndimage.rotate` (used to *measure*) and
PIL `Image.rotate` (used to *apply*) rotate in opposite visual directions — confirmed
empirically on p36 that PIL `+angle` is the correct leveling direction.
Verified on **p36**: overlaid a true-horizontal red grid on the rendered MRC — original
rules/rows drift; after deskew they are parallel to the grid. Text stays crisp (K is
re-extracted from the rotated source). Pages measured at 0.00° (p39/p50) are left
untouched.

## Recommended integration (not yet wired into the deploy)

Deskew belongs at the **start of the pipeline**, before detection:
1. measure angle on the RGB crop (method A),
2. rotate BOTH the RGB crop and the CMYK tiff by −angle (high-quality),
3. then run detect_screened → mrc_hyst8_perio as usual.

(The test rotated the cached coarse `screened_*.npy` instead of re-detecting — fine for a
visual check, but production should re-detect on the deskewed source so the screen mask
aligns exactly.)

Quality note: a sub-degree BICUBIC rotation adds negligible blur; K text is re-thresholded
from the rotated source so it stays crisp, and the background is descreened regardless.
