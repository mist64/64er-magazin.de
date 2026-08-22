# 005b — The A4 window, anchored on the 64'er logo

**Applies to:** all — every issue of this magazine is cut this way.

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
ISSUE's leaves. The cover leaf is the opposite case and is trimmed, not
padded — its 223 mm width is a fold flap, not a larger page.

Record per page which of the three was used, beside the grade stamp, so a page
whose type sits differently from its neighbours can be explained rather than
re-derived.

## Verification

1. Every body page is exactly 4961 × 7016 px.
2. The anchor lands on the glyph — check the overlay on a sample, per parity,
   rather than trusting the transform.
3. Content registration: the same element (the folio, the foot rule) sits within
   a pixel or two of the same place across a run of same-parity pages. This is
   the property the rule exists for and the only one that proves it worked.
4. Alpha inside the window is a thin border, not a chunk, and the per-page
   figure is recorded.
