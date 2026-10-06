# 005b — The A4 window, anchored on the 64'er logo

**Applies to:** **`binding: "sheet"` only.** Every issue of this magazine is
cut this way, but a SPREAD issue is already cut this way by step 005: the
spread variant anchors on the logo and writes an exact A4 window,
`MASTER_W_PX x MASTER_H_PX` = **4961 x 7016**, so `masters600` IS the A4
delivery. The sheet variant writes a traced-trim canvas of varying size
instead, and that is what this step turns into A4.

Running it on a spread issue produces `a4600`, a second crop computed a
different way from the same `sheets600`, which nothing downstream reads —
step 010 OCRs `masters600`, and for a spread issue so does the PDF. 8611
asked before running it rather than after, which is the only reason this
line is right.

**This rule is copied from the process that already solved it**, `03-crop`, and
is reproduced here so scan2ocr is self-contained. The wording of the principle
and the measured figures are the originals; only the fallback order is new,
because this magazine's Sonderhefte are not clip-bound and have no spine to
fall back to.

---

## Why the logo is the anchor — the principle, verbatim

> The "64'er" wordmark is print-registered to the page CONTENT. The sheet edge
> is not: print-to-cut registration varies, so anchoring on the paper edge
> would align the paper and misalign the type.

That is the whole reason the anchor exists. Cutting to the traced paper edge
produces a page whose *sheet* is square and whose *type* wanders by however much
the guillotine varied — 1–3 mm on SH8601. Cutting to the logo produces the
property the rest of the chain depends on:

> Cut every page to exactly **210 × 297 mm** (4961 × 7016 px @600 dpi) so the
> same content lands in the same place on every page, and the later stages need
> no per-page geometry.

## What the anchor is, and how well it is found

The wordmark sits in the **outer bottom corner**, is the same glyph on every
page (not mirrored between parities), and is template-matched
(`template_64er_600.png`). MEASURED on 8609: found on **129 of 176** pages,
confidence p50 **0.95**, parity correct on all 129.

Two cautions carried over from the original, both paid for once already:

- `logo_detect.py` reports coordinates in the **raw** thumb frame although its
  docstring claims the deskewed one. Transform the anchor through the same
  rotation the levelling used, and verify by landing it on the glyph — never by
  trusting a sign convention.
- Running the detector on a **page subset REWRITES** its whole output file with
  only those pages. Back it up first.

## The window is rigid, one offset pair per parity

> The window is RIGID relative to the anchor: one (S, B) pair per parity, not
> per page, because the point of anchoring on the logo is that the same content
> lands in the same place on every page.

`S` = the anchor's distance from the window's left edge, `B` = from its top
edge, fitted to minimise alpha inside the window over the pages that have their
own logo. 8609's fitted values, kept as the shape of the answer rather than as
constants to reuse:

```
even   S= 568  B=6892   mean alpha in window 1.27%
odd    S=4416  B=6900   mean alpha in window 1.90%
```

**S must span the full page width.** On odd pages the anchor is near the RIGHT
edge, and a search range capped at 900 px pinned the optimum to its own
boundary and reported 71 % alpha — a window mostly off the page.

Pages with no detected logo are **excluded from the fit** — an interpolated
anchor would drag the optimum toward its own error — but still receive a
window afterwards, from an anchor interpolated across same-parity neighbours
and marked as interpolated.

## A4 does not fit without alpha, and that is expected

> A4 fits alpha-free on **0 of 129** pages. The page simply is not 210 × 297 mm
> of known pixels once bed, neighbour, clip holes and the deskew wedge are
> removed, so the objective is not "avoid alpha" but "minimise it", and
> inpainting is structural rather than optional. The deficit is small and
> consistent (1–3 mm), i.e. a thin border, not a chunk.

And where the window overhangs the canvas, leave the output **transparent
rather than clamping the window** — clamping silently shifts the content and
destroys the one property the anchor exists to provide.

## The fallback order for this chain

The original falls back to a **spine** anchor where there is no logo. A
glue-bound issue has no spine, so for `binding: sheet` the order is:

1. **the 64'er logo**, where it is found — the anchor proper;
2. **paper-edge**, where a page has no detected logo;
3. **traced-edge**, for pages that carry no logo at all — the cover leaf and a
   bound-in card such as SH8601's Zahlkarte, which are not body pages and have
   no wordmark to register to.

**And an insert smaller than the issue's leaf keeps its measured size** rather
than being centred on an A4 window: SH8601's Zahlkarte is ~144 x 205 mm, and
padding it to A4 would fabricate 53% of the page. A4 is the geometry of the
ISSUE's leaves.

**ONE INSERT IS ONE OBJECT, AND ALL ITS PAGES ARE THE SAME SIZE.** A bound-in
card is a single physical thing, scanned once per side. Tracing it four times
gives four boxes that differ by tracing error, and shipping those verbatim tells
the reader the same card is four different sizes. MEASURED on SH8601's
Zahlkarte (149-152): `3395x4829`, `3404x4834`, `3410x4846`, `3413x4808` px — a
spread of **0.76 x 1.61 mm across the front and back of one card**.

Take the **max per axis**, for the same reason the A4 rule pads a sheet that
measures short: a box that traced short has CUT INTO the card, and content lost
to a short trace cannot be recovered downstream, while padding costs at most the
spread — 0.76 x 1.61 mm of the card's own paper. Pad **symmetrically**, so the
content stays where it sits on the card.

Group by **contiguous run**, never all inserts at once: an issue may bind in two
different cards, and unifying across them invents a size neither one is. The cover leaf is the opposite case and is trimmed, not
padded — its 223 mm width is a fold flap, not a larger page.

Record per page which of the three was used, beside the grade stamp, so a page
whose type sits differently from its neighbours can be explained rather than
re-derived.

## A PAGE WHOSE TRACE FAILS IS STILL CUT AUTOMATICALLY — NEVER BY HAND

**NAMING, because the numbers collide.** The three above — logo, paper-edge,
traced-edge — are the ANCHOR fallbacks, and they are implemented in
`r005_a4_window.py`. The three below are RECOVERIES for a page whose trace
failed outright, they are a different thing, and **they are not in the code**:
every build so far has re-derived them in a hand-written script (SH8603's
155/163/168, SH8604's 163). Call them recovery A, B and C, not fallback 1, 2
and 3. Implementing them in `r005_a4_window.py` is the open task; until then,
the builder writes the script and records which recovery it used in the stamp.

**Owner, 2026-10-04: "manual cropping is not an option for the PDF."** A hand
crop does not reproduce, is not recorded anywhere a later build can read, and
turns one person into the step. A page whose trace fails gets a BEST-EFFORT
window from the evidence that is there, and the result is published with a note
saying which fallback produced it.

The rule above assumes every page of an insert traced, so the run can take the
max per axis. It does not cover a page that failed OUTRIGHT — the trace found
no card at all and the page was published as an uncropped sheet. MEASURED:

| issue | traced | failed |
|---|---|---|
| SH8602 | 165 `143.1 x 208.0`, 166 `145.0 x 208.0`, 167 `143.1 x 208.4` | 168 (`212.7 x 304.2`, uncropped) |
| SH8603 | 181 `144.4 x 207.7` | 182, 183, 184 (`216.4 x 304.2`, uncropped) |

So, in order:

**Recovery A.** **A failed page of an INSERT takes its run's unified size.** The authority is
   **the run's own agreeing traces**, never a corpus constant: a bound-in card
   is whatever that issue bound in. MEASURED: SH8602 and SH8603's Zahlkarte read
   ~144 x 208 mm, SH8601's ~144 x 205 — but **SH8604's reads 149.9 x 206.9**,
   6 mm wider, because its card carries a printed "Wußten Sie schon …" flap.
   All four of its traces agree and its edges are clean, so the card is simply a
   different object. Read as a constant, the rule would have called all four
   failed.

   So the test is **agreement within the run**, not a match against ~144 x 208.
   A member has failed when it disagrees with its agreeing siblings, or when it
   reads at sheet size (216 x 304 mm) — that is the frame, not the card.

   **Anchoring:** on the page's own traced top-left corner where there is one;
   where there is not, on whichever edges ARE measurable (right or bottom
   against the bed), and NOT on the run's offset. MEASURED on SH8603: the run's
   offset put the window's right edge at 3438, past 183's card edge at 3431, so
   28% of 183's right 24 px band was bed. Check the window's edge bands for bed
   before accepting it.
**Recovery B.** **A failed page with surplus paper** (a wrapper back cover, 217 mm of paper
   in an A4 frame) is windowed on its **ink bounding box**, not the paper's.
**Recovery C.** **A failed page whose ground is full-bleed dark**, where a colour test for
   the prop cannot work because the sheet is already graded and separated, is
   cut from **row and column luminance profiles**: the prop shows as a step at
   the foot, the bed as a plateau darker than the page. MEASURED on SH8602/155:
   page lum ~6 -> ~105 -> ~200 at row ~7005; dark-brown ground ~10 against bed
   ~3, a step at x~4948.

Cut from `masters600`, pad outside the frame with paper white, write into
`<tmp>/a4600/`, and keep the automatic window as a backup. Note in the stamp
which fallback was used.

## Verification

1. Every body page is exactly 4961 × 7016 px.
2. The anchor lands on the glyph — check the overlay on a sample, per parity,
   rather than trusting the transform.
3. Content registration: the same element (the folio, the foot rule) sits within
   a pixel or two of the same place across a run of same-parity pages. This is
   the property the rule exists for and the only one that proves it worked.
4. Alpha inside the window is a thin border, not a chunk, and the per-page
   figure is recorded.
