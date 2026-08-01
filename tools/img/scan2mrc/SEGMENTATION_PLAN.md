# Segmentation by screening, not by classification

## The rule

```
screened            -> contone (the 150 dpi background)
screened + uniform  -> flat fill (one colour, exact and tiny)
not screened        -> bilevel (600 dpi K / ink stencils)
```

Two physical questions, three destinations. No "is this a photo or is it type" anywhere.

Halftone means the original was continuous tone — the press screened it. No halftone means solid
ink: type, rules, line art. That is a fact about the paper, not a threshold fitted to a sample.

## Why the current design fails

Today the pipeline detects screening per block, groups the blocks into clusters, and then **throws
that away**: step 7 re-decides each cluster with CMYK statistics (`colorvar`, `satmean`, `tonevar`,
`bodyK`, `bodyC`, `objfK`) voting IMAGE vs TEXT. Everything that goes wrong follows from that vote.

Measured, on this issue:

* The features do not separate. p092 carries two grey photographs; `objfK` reads **0.44** on one and
  **0.03** on the other. A "PROFIS" wordmark reads `bodyK 59, objfK 0.28`; a circuit-board photo
  reads `bodyK 49, objfK 0.28`. Identical signatures, opposite correct answers.
* CLAUDE.md already records this as proven: image-vs-text is not separable by any low-level CMYK
  statistic. Seven features have now been tried and none separates.
* The fallback points at the destructive layer. A photo sent to bilevel is **destroyed** — tone and
  colour gone (p146, p092, p010). Type sent to contone is merely soft. The default is on the wrong
  side.
* Failures compound. Once a photo is voted TEXT it is rendered bilevel, its background is claimed by
  the tint detector and flat-filled, and its halftone dots were swept up by the despeckle. p010 is
  all three at once: yellow cable sleeves erased, colour gone, shaded backdrop replaced by flat pink.

Cluster-level measurement cannot rescue it either. A cluster containing a tint with type on it is a
*mixture* of screened and unscreened, so any single number for it is meaningless. Measured
per-cluster matched-filter response: IMAGE p50 = 0.113, TEXT p50 = 0.160 — overlapping, and the
high-scoring "TEXT" clusters are text on tints, correctly screened. The unit is wrong, not the
statistic.

## The design

**1. Per-block screening test.** Slide a window (~60 px at 600 dpi ≈ 10 screen cells — fine enough
to separate a tint from the type on it, coarse enough to fit a screen). Per channel C,M,Y,K.

**2. Per-block geometry.** Measure each block's own (lpi, angle) rather than using a page value.
Required, not an optimisation: p092 has consistency 0.97 at page level and still carries photographs
screened at **81 and 102 lpi**. Page-level geometry is wrong even where it is trusted, and 91 of 163
pages have `pitch_std` 4× higher than the trusted ones — the signature of more than one screen.

**3. Matched filter, not a band search.** Demodulate at the block's measured frequency:

```
    blind band (today)                    matched (proposed)
         . - - + - - .                          |    *
       /       |       \                        |   /
      |    ,---+---,    |                       |  / angle
      |    |   +   |    |                       + /- - - - >
       \   '---+---'   /
         ' - - + - - '
    any peak in a wide ring         only energy at THIS frequency
    -> type's broadband edges       -> type has no peak there
       land in it and pass             -> scores ~0
```

`P = |demod| / local AC RMS` = the share of local energy sitting at the screen frequency.
Prototype confirms the discrimination is there: p092's body type peaks **on-axis at 0°** (that is
line rhythm, not halftone), which the existing ±12° axis-cut already rejects.

**4. Group blocks into areas**, then **absorb solid-K regions into an adjacent screened area**.
This is the reversed-box case — a solid dark panel with knocked-out lettering next to or around
screened content — handled by adjacency instead of by the `darkfill` special case and its five
fitted thresholds.

**5. Uniform screened areas → flat fill.** Already implemented (`solid_rects`), and it is the
north-star treatment: measure the ink percentage and emit a fill, not a descreened raster.

**6. Delete step 7.** No IMAGE/TEXT vote, no `VOTE`/`TCV`/`TS`/`TT`/`BK`/`OBJF`/`BC`, no bodyK
rescue. Those constants exist only to answer a question this design never asks.

## What this replaces

| removed | why |
|---|---|
| step 7 IMAGE/TEXT vote | asks an unanswerable question |
| bodyK continuous-tone rescue | patch on that question |
| `darkfill` + glyph veto (5 thresholds) | adjacency handles reversed boxes |
| page-level screen geometry as the reference | wrong even when trusted |

Already removed this session for the same underlying reason — features that made files smaller by
deleting real content: the text inpaint, the K despeckle (`MIN_K`), the accent-ink despeckle
(`MIN_CC`).

## Risks, and what each needs before it is believed

* **Per-block geometry is noisy on small or weakly screened blocks.** Needs a confidence measure and
  a defined behaviour below it. Default must be contone: a wrong contone call costs bytes, a wrong
  bilevel call destroys the content.
* **Block boundaries may show** where a region is split between destinations. Needs feathering or a
  smoothed P field, and visual checking at edges of tints.
* **CLAUDE.md records that a previous per-pixel attempt "carved IMAGE out of words".** That used
  colour variation, not a matched filter, and at pixel rather than block scale. Still the thing most
  likely to go wrong — check words on tints specifically.
* **Coarse-screened pasted-in ads** (p092 at 103 lpi is the only convincing one) fall out naturally:
  screened is screened, whatever the ruling.

## Verification, before anything ships

The standing rule applies: no change lands without a machine-readable before/after and an overlay.

1. Known-answer set first: p092 (two photos, one currently right and one wrong), p146, p010, p069,
   p118, p098, p171, p027, plus the 13-region contact sheet in `tmp/photok/`.
2. Then all 176 via `pipeline.sh`, diffed with `05-mrc/diff_record.py`, overlays from
   `06-mrc/debug_pdf.py`.
3. Sizes only from a full run at the shipping settings (`--bg-dpi 150`, masked score). Every size
   quoted before those were fixed was for a file that would never have shipped.

## Order

1. per-block geometry + P map, written as a debug artifact only — nothing consumes it yet
2. compare P against the known-answer set; confirm it calls p092's two photos the same
3. route on P, delete step 7
4. absorb solid-K by adjacency, delete `darkfill`
5. full sweep, overlays, judge
