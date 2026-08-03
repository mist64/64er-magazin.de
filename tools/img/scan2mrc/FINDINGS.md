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
* Pasted-in ad artwork brings its own rulings: **100–105 lpi** on p092, **110–134 lpi** across the
  ad/catalog section, and a genuine **181 lpi @ 24°** full-page ad on p073.
  (An earlier note claimed 81 lpi on p092. Re-measured directly on 8609 with the per-ink field: it
  is 100–105, and nothing on that page sits at 80–90. The 81 was not corroborated — treat page
  numbers inherited from the 8608 notes with the same suspicion.)

So the useful band is **75–220 lpi**. The old detector's 139–192 missed the 133 lpi tints and the
whole ad section, catching them only through spectral leakage.

**The low edge is derivable, and 75 is where the data puts it.** Over 20 pages, the ruling histogram
of real content (coherent, non-follower blocks; N=102,697) is EMPTY between **55 and 95 lpi** — 7
blocks, 0.01%. Below that sat 13,781 firing blocks whose angles were near-uniform across the
admissible range, where real screens concentrate hard at 40–50° and 130–140°: broadband 1/f energy
leaking into the band's low corner, not a structure. A subharmonic-lock explanation was tested and
disproved — only 5.4% had a cross-ink peak at 2×/2.5×/3× their own ruling.

**True Y is probably on-axis (~0/90°)** and is therefore removed by the axis cut that rejects type.
What the old geometry stage reported as "Y@45" may be its diagonal or K bleed. Trust C/M/K angles.

**A greyscale photo and a grey tint box have IDENTICAL geometry** (both K@45°). They differ only in
whether the dot area varies. Geometry alone can never separate them — that is what the
uniform/varying test is for.

**Three plates cannot share an angle** — they are set apart precisely to avoid moiré. So when two or
more inks report the same ruling AND angle in the same block, that is ONE structure appearing in
several channels, never several screens. It happens two ways, and they need opposite responses:

* *Crosstalk.* A strong plate's halftone echoes faintly into the other channels at a fraction of the
  amplitude. Reject the weak ones — see the follower rule below.
* *A neutral image.* Before GCR, a grey halftone puts near-equal ink in C, M, Y and K, so one screen
  appears in all four at COMPARABLE depth. Measured on p073: C/M/K all 181 lpi @ 24°, depths
  24/28/39. Do NOT reject these by geometry — that is the signature of a neutral (greyscale) region
  and belongs to routing as "this is class 2", not to detection as "these are artifacts".

The amplitude ratio is what tells the two apart, which is why the follower rule is a ratio test and
not a pure geometry test.

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
  The check is cheap and worth storing: sample the band magnitude at HALF the peak frequency along
  the same direction (and at 2/5 of it, the (2,1) lattice point). Two extra floats per block per ink
  settle the question for a whole issue. Applied to p073's suspicious 181 lpi: the half-frequency
  magnitude is 1.3–1.9× the band median, indistinguishable from p007's genuine 160 lpi screens
  (1.3–1.7), so there is no fundamental beneath it and **181 lpi is real**.

* **A ratio is not a measurement.** `peak/median` is scale-invariant, so a 5-level ripple scores like
  a 200-level screen. Every prominence test needs an absolute amplitude test beside it. This cost a
  full round: stage A's first version reported all four inks screened on a black-and-white page.
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

## 2b. THE GRADE IS NOT A VALID CONTONE INPUT — neutral content comes out mauve

Measured on p073, whose printer photograph is neutral grey on paper:

| | C | M | Y | K | naive RGB | B−G |
|---|---|---|---|---|---|---|
| raw scan | — | — | — | — | 122 / 113 / 110 | −3 (warm) |
| display grade (C 50-90, M 30-70, Y 30-70, K 90-95) | 18.5 | 51.3 | **4.7** | 79.8 | 162 / 141 / 172 | **+31** |
| detect grade (C 0-90, M 0-70, Y 0-70, K 0-95) | 35.6 | 38.2 | 2.8 | 231 | 19 / 20 / 23 | +3 |

**The mechanism, in three steps, none of which is a bug on its own:**

1. **The geometric separation is not neutral-preserving.** Computed directly from `separate.rs`'s anchor
   constants, a pure grey maps to strongly unequal inks, and the imbalance *changes sign* along the
   axis:

   | grey | 200 | 170 | 140 | 120 | 100 | 80 | 60 | 40 |
   |---|---|---|---|---|---|---|---|---|
   | C | 2 | 48 | 94 | 125 | 156 | 188 | 220 | 252 |
   | M | 3 | 20 | 48 | 72 | 102 | 140 | 189 | 255 |
   | Y | 13 | 5 | 28 | 47 | 70 | 100 | 139 | 193 |

2. **The display grade does not compensate for it** — it was fitted to make TYPE crisp (the K level
   "clips moderate/rich-black K, keeping only near-solid black"), and nobody asked what it does to a
   photograph. Y is already the smallest channel and its `lo` of 30% clips it to zero across most of
   the mid-tones, while C and M survive.

3. **GCR cannot repair it.** It subtracts `min(C,M,Y)`, which is 0 once Y has clipped, so it removes
   nothing at all.

Net: every neutral mid-tone in a photograph loses its yellow and renders blue/mauve. Blue is the
absence of yellow.

**Do NOT fix this by adjusting the Y level.** The C:M:Y ratio is not constant along the grey axis —
at grey 200 Y is the LARGEST channel, at 170 C is ten times Y — so no single per-channel (lo, hi)
pair can straighten it. It needs either a per-channel curve fitted to the separation's own grey-axis
response, or a neutral-axis subtraction that replaces `min(C,M,Y)` with "the response this separation
gives for a neutral of this lightness".

**This is roadmap step 7** ("measure the real ink/paper colours → feed the grade instead of the
hardcoded levels"), and it is a precondition for the contone layer being colour-correct at all. It is
also the same lesson as the two grades in stage B: one grade fitted for the bilevel layer's benefit
is not automatically valid for the contone layer. Two purposes, two inputs.

---

## 2c. WHAT THE DETECTOR MUST BE FED, and what actually separates a screen from type

Measured 2026-08-02/03 over 12,812 hand-labelled blocks on p073, p007 and p092 (photographs, tint
bars, body text, display type, solid ink, paper).

**The input must be unclipped at BOTH ends, and must NOT be GCR'd.**

* *GCR deletes the evidence.* It subtracts min(C,M,Y), and once the separation is neutral-calibrated
  that minimum IS the whole of a neutral — so it zeroes all three chromatic channels wherever the
  content is grey, which is exactly what a b&w photograph or a grey tint is. Feeding the detector
  GCR'd planes took p073's left machine from C 27 / M 65 / Y 158 firing blocks to C 0 / M 0 / Y 0.
* *Clipping destroys it.* With the old detect ceilings (C 90, M 70, Y 70, K 95), **37.6% of p073,
  20% of p007 and 17.5% of p092** had the most-inked channel more than half saturated at 255, and
  in those tiles the AC RMS collapses to 6.2 against 41 where detection works. A halftone clipped
  flat has no modulation left and no statistic downstream can recover it.

**What separates screened from unscreened, ranked by AUC on that set:**

| statistic | AUC | per page | note |
|---|---|---|---|
| `agree` — fraction of the 8 neighbours measuring the same ruling and angle | **0.941** | .978/.969/.929 | the only one that is best on EVERY page |
| `conc` — share of the block's AC energy at the peak | **0.920** | .872/.965/.935 | best purely local; no neighbourhood needed |
| `prom` — peak/median in the band | 0.882 | .850/.941/.888 | swings by page |
| `depth` — amplitude of the fundamental | 0.882 | .817/.947/.901 | **orders the classes backwards, see below** |
| `harm` — fundamental + 2nd + 3rd harmonic | 0.871 | | rejected, see below |
| `lpi` | 0.869 | .924/.974/.758 | an artifact of the band edge, do not use |
| `acrms` | 0.616 | .507/.493/.705 | rejected, below chance on one page |

`agree` matters because a page-portable ranking is the only kind that can carry a fixed threshold.
It also encodes what a screen physically IS: a lattice covering an area. Type's rhythm belongs to the
words in one tile and agrees with nothing.

**`depth` is duty-cycle dependent and must not gate.** It measures the fundamental alone, and a light
tint's narrow dots put their energy in harmonics. Measured on p073: the printer body, unambiguously
screened, reads depth 2.9–7.9 while body text reads 8.8–15.4 — the wrong way round. Any threshold
that accepts the body accepts text.

**A peak AT the band edge is the band edge.** A spectrum whose energy merely rises toward low
frequency — unscreened paper, soft background — has no interior maximum, so its peak lands wherever
the band is cut off, and every such block reports a screen there. Analyse a wider band than you
accept: 55–240 lpi analysed, 95–225 accepted. The gap is the measured empty stretch in the
real-content ruling histogram (7 blocks of 102,697 between 55 and 95 lpi).

**Absorption of adjacent solid ink is no longer needed** and is disabled. It existed because a
photograph's solid shadow could never fire; with `conc` and `agree` it fires directly. Measured on
p073, coverage against absorption reach: photo 1.00 and shadow 0.98 at reach 0, unchanged at reach 8,
while the solid red banner — not a picture at all — goes from 0.03 to 0.48. Five points on one machine
against forty-five points of false coverage.

---

## 2d. THE SEPARATION IS AN APPROXIMATION, and where it bends

The eight anchors are the corners of the CMY cube (W=000 … K=111), each a measured RGB, and the
separation inverts that map. Two things follow that cost real quality:

* *The old plane-ratio inversion was wrong in the interior.* It fitted two planes per ink through
  three of the four corners of a face; a real ink face is not planar, so the ignored corner misses
  by up to 22 (K misses the cyan face by 21.2, magenta by 21.9, yellow by 4.3) and every interior
  point is interpolated through that error. Replaced by a true trilinear inversion (Newton, 64³
  lattice): exact at all eight corners, and differing from the plane ratio by up to 31 levels in dark
  and saturated colours.
* *A visually neutral grey is NOT an equal-CMY mix.* Under these anchors the model's equal-CMY locus
  sits at R−G +22 while a real neutral measures R−G +9 — ordinary press grey balance, more cyan than
  magenta and yellow. So `min(C,M,Y)` is not the neutral component, and GCR cannot find it. The
  neutral calibration (sample the W→K axis, record each channel's response, invert it) is therefore
  **grey-balance-aware GCR**, not a hack, and a proper cube inversion does not remove the need for it.
  Substituting the measured paper for the W anchor makes the gap wider, not narrower — it is not
  stale anchors.

**The level stretch is the only destructive step in the grade.** In p073's photograph it put 74.8% of
C, 50.8% of Y and 35.4% of M hard on zero — which is also why the page read warm, since C is clipped
hardest and M least, so what survives is M and Y. Neither the contone nor the detector has any use
for contrast. The aggressive K level (90,95) was never a grade at all: it was the STENCIL's solidity
test wearing a grade's clothes, and belongs there explicitly.

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
