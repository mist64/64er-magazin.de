# FINDINGS — what the paper is, and what not to try again

Distilled 2026-08-02 from ~2500 lines of code comments and five R&D logs, immediately before
deleting all of it. Everything here was MEASURED on this issue (8609) or on 8608 before it. The code
that produced these numbers is gone; git has it (tag `pre-rewrite`). Nothing else from those files
is worth reading.

Read this before adding any threshold, band, or window size.

---

## 1. What is physically on the paper

**Two screen systems on one press.**

* Process photos: fixed per-ink angles **C 71° / M 19° / Y 45° / K 45°**, ~150–159 lpi. Colour-photo
  K drifts toward C's 71°.
* Design tint boxes: screened per LAYOUT, not per ink. Two-ink tints sit on the **{45°, 75°} pair**
  at ~150–152 lpi, and which ink takes which angle flips per box (green C@76/Y@45, orange
  M@45/Y@75). One-ink cyan tints are coarser, **~133 lpi @ 45°**. Grey boxes are **K@45° only**.
* Pasted-in ad artwork brings its own rulings: measured **81 and 102 lpi** on p092, **110–134 lpi**
  (pitch 18–20 px @2400) across the ad/catalog section.

So the useful band is roughly **80–200 lpi**, not the 139–192 the old detector used — it missed the
133 lpi tints and the whole ad section, catching them only through spectral leakage.

**True Y is probably on-axis (~0/90°)** and is therefore removed by the axis cut that rejects type.
What the old geometry stage reported as "Y@45" may be its diagonal or K bleed. Trust C/M/K angles.

**A greyscale photo and a grey tint box have IDENTICAL geometry** (both K@45°). They differ only in
whether the dot area varies. Geometry alone can never separate them — that is what the
uniform/varying test is for.

**Halftone exists only in mid-tones.** A solid highlight or solid shadow carries no dots at all, so
a photograph's flat areas correctly measure "not screened". Any block-level screening test must
therefore close gaps and fill holes before it forms regions, or every photo comes out shot through
with unscreened patches. Load-bearing, not cosmetic.

**Page skew is +0.15° to +0.35°**, measured by projection variance (see `01-deskew/NOTES.md`).

---

## 2. Traps in the measurement itself

* **600 dpi is Nyquist-marginal for a 150 lpi screen.** 4 px per cycle, and a 4× Box downsample has
  its first null exactly there. The old `screenseg` measured screening on a 600 dpi luma plane and
  survived only because the screens sit at 19/45/71°, where the 2D box response is ~0.6 instead of
  0. An axis-aligned screen would have vanished silently. **Measure screening at 2400 dpi.**
* **FFT argmax locks onto lattice harmonics.** At T=512 the screen-angle estimate landed on 45°,
  63.4°, 71.6° — the FFT lattice's own diagonals, not the screen fundamental. Any peak-picking needs
  sub-bin interpolation and a check that the peak is the fundamental, not a harmonic.
* **A smaller analysis window is not tighter.** T=160 collapsed real-screen retention 22196 → 5175
  because a 133 lpi screen (pitch 18 px) needs the frequency resolution of a large window to be
  resolved at all. Bloom was T-independent. Do not shrink the window to localise.
* **Scatter/anchor mismatch blooms the result.** The old detector computed a 240 px window and wrote
  the score to a 60 px grid cell at the window's TOP-LEFT — dilating every feature ~4 cells (2.5 mm)
  into the surrounding white. If a window's result is written to a grid, write it to the window's
  CENTRE, and remember the footprint is the window, not the cell.
* **Measure screening on graded, NOT GCR'd channels.** GCR is our reconstruction choice; the press
  laid physical C/M/Y/K dots. Use GCR for deciding which ink owns a mark, not for finding screens.

---

## 3. Negative results — do not retry

**Image-vs-text is not separable by any low-level CMYK statistic.** This is the single most
expensive lesson in the project: nine classifier generations (B1–B9), seven features, a
381-cluster vision-labelled ground-truth set. Measured collisions:

| | reads | correct answer |
|---|---|---|
| "PROFIS" wordmark | bodyK 59, objfK 0.28 | TEXT |
| circuit-board photo | bodyK 49, objfK 0.28 | IMAGE |
| p092 photo A / photo B | objfK 0.44 / 0.03 | both IMAGE |

Per-cluster matched-filter response: IMAGE p50 = 0.113, TEXT p50 = 0.160 — overlapping, and the
high-scoring "TEXT" clusters were text on tints, correctly screened. **The unit was wrong, not the
statistic**: a cluster holding a tint with type on it is a mixture, so any single number for it is
meaningless.

Specifically rejected, each with data:

* **Screen PRESENCE alone as a classifier** — "is K screened" is high for every neutral fill (box,
  table, photo alike) and low for colour content. A grey box and the Line-Spy photo both read 16.
* **Tonal-level counting** — a table quantises like a photo.
* **OCR-density gating** — the false positives are coloured non-text graphics.
* **Rectangularity** (`filled_frac` ≥ 0.93) to separate reversed boxes from bold glyphs — the
  populations touch (a kept box measures 0.9298). Flipped 144 components across 59 pages and
  destroyed p061's reversed menu bar, exactly the case it existed to protect.
* **Blank-white bloom fixes** (ink gate, gabor gate) — the bloom is invisible in the render (a blank
  cell descreens to white) and every fix cost real tint tone.

**And one caution about the current direction.** A 2026-06 prototype compared per-channel inverse
halftoning (demodulate each ink at its measured lpi) against the blanket YCbCr low-pass, pixel-zoomed
on p027's product boxes: **essentially identical sharpness**. Demodulation was not a visible quality
lever *for the descreened raster*. Do not sell it as one. Its value here is different and has to be
argued on its own terms: it yields the per-ink DOT AREA (which is what a flat fill needs to say "20%
C") and a coherence field that separates screen from line art — neither of which a low-pass gives at
any quality. If those two do not materialise, the low-pass is a perfectly good descreen and the
honest move is to keep it.

The current design does not ask "photo or type" anywhere. That is deliberate, and it is why.

---

## 4. Features deleted for destroying content — do not reintroduce

* **Text inpaint.** With no non-stencil neighbour in range, `num / den.max(1e-6)` returned 0 = BLACK.
  Since K is a black-only ImageMask, every white letter is background showing through a hole in the
  stencil — so it welded the counters shut and erased reversed lettering on **166 of 176 pages**. It
  also erased photographs wherever a photo had been misrouted to the stencil. Its only real saving
  (2.7% of bytes) came from deleting screened line art the stencil redraws anyway.
* **K despeckle (MIN_K) and accent-ink despeckle (MIN_CC).** Deleted ~17% of components on a median
  page. Small and unwanted are not the same thing: a period, a thin serif, an umlaut dot are all
  small. On p173 the despeckle was quietly sweeping up 1176 individual halftone dots the K detector
  had wrongly caught inside a screened region — masking a real defect instead of fixing it.
* **discard-small** (keep a cluster only if area ≥ 0.012·NY·NX). A product photo under ~1.9 cm
  failed it, so p104's all-small-ad page discarded every cluster and bilevelised every photo. It
  existed only to suppress the bloom above. Size cannot separate a small photo from small bloom.
* **darkfill** (promote solid dark fills to contone so knocked-out lettering survives). Five fitted
  thresholds plus a glyph veto, and it was compensating for the inpaint, not for a real gap. With
  the inpaint gone, both pages that justified it render correctly without it. A flat reversed box is
  exactly what a bilevel stencil reproduces perfectly.
* **k_only shield** (a page with max CMY coverage < 0.02 renders entirely bilevel). It covered **100
  of 176 pages** — including p092, whose two grey photographs were the motivating case for the
  screening segmentation. It hid the problem it was meant to survive.

Pattern: **every one of these made files smaller by deleting real content.** A size win that removes
marks is not a win. Correctness first.

---

## 5. Pages that are known to be hard — the judge set

Use these before claiming anything works.

| page | what it holds |
|---|---|
| **p092** | two grey photographs, screened at 81 and 102 lpi; page-level geometry says 0.97 consistent and is wrong |
| **p007** | contents page: tint bars with black + red type ON them, grey "9/86" numeral |
| **p073** | book covers — screened photos of screened originals |
| **p081** | "Akustikkoppler" heading + a screened logo |
| **p078/p079** | Commodore logos (screened decorative art), reversed header bars |
| **p036** | a real CHECKERBOARD in the "Marktübersicht" logo — must not be averaged away as a screen |
| **p040 / p050** | type on a grey box: strokes fatten and counters fill (p040); screen dots fuse into glyphs (p050) |
| **p084 / p085** | grey comparison tables — the classic "is it a photo" trap |
| **p104 / p107** | reversed white-on-dark boxes; small product photos |
| **p086** | full-page ad, magenta screened design plus cover photos |
| **p010 / p146** | photos that the old vote misrouted into the stencil |
| **p118 / p171** | dense classified ads; index page of type on a light-blue tint |
| **p003** | light text — the one page a fidelity scan flagged for real text loss |
| **p002 / p069 / p117** | controls: ordinary text page, dark full-page ad, heaviest K-over-image page |
