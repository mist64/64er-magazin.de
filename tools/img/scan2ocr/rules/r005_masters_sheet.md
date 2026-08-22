# 005 — Scan to 600 dpi master, SHEET variant

**Applies to:** all — but only where the descriptor says `"binding": "sheet"`.
A `"binding": "spread"` issue runs `r005_masters_spread` instead, and this
variant is then recorded in that issue's `LOG.md` as **not applicable —
binding**.

**Goal:** turn the raw ~2400 dpi scan of one loose sheet into the deskewed,
matted, graded **600 dpi masters** that `r010` OCRs and `r145` cuts figures
from. This is the first step of the chain; it owns everything between the
scanner and `r010`'s input.

This is a **program step**: the orchestrator runs it, checks the exit status and
runs the Verification block below. There is no editorial judgement in it and
nothing to dispatch.

## The two variants, and why the suffix is not an insertion

Step 005 exists in two **mutually exclusive** variants, chosen by the issue
descriptor's `binding`:

| variant | the frame holds | inner boundary |
|---|---|---|
| `r005_masters_spread` | a clipped **SPREAD** (8609, the monthlies) | facing-page colour boundary, clip holes as fallback, holes inpainted |
| `r005_masters_sheet` | one loose **SHEET** (SH8601) | the torn fringe: traced on a verso, a flush vertical cut on a recto |

**The suffix names the variant. It is not a step inserted after another one.**
This directory's history has suffixes (`9b`) as the symptom of bad numbering, so
it is worth saying plainly: these are alternatives at ONE step, exactly one of
them runs for a given issue, and neither is ever "005 then 005b". Both write
the same contract, `<tmp>/masters600/NNN.png`, and `r010` and `r145` read that
directory without knowing which variant filled it.

## What the paper actually is — measured, not assumed

SH8601's sheets were **torn off a glued spine**, one sheet per scan — 144 of
them A4 interior pages, and eight of them not (see *The eight pages that have no
paper to trace from*):

| | |
|---|---|
| residual skew | up to **1.08 deg** (`092`), typically 0.1–0.7 — the pages are NOT levelled |
| edge tilt AFTER levelling on the text | 0.14–1.12 deg — the sheet was guillotined at its own angle, so the paper edges are NOT parallel to the type |
| outer edge | guillotine-clean, straight, hard contrast against a near-black bed |
| inner edge | **torn** — a fringe of fibres standing proud of the paper body, wandering down the page |
| torn side | follows parity: a **verso** tears on the right, a **recto** on the left |
| beyond the sheet | black bed, and a saturated **yellow prop** further out |
| paper white | **uniform** across the sheet (a 3×3 grid of paper p90 varies by ≤4 levels) — no vignette to correct; the cast is global, R/B 1.163 |
| the other stock | the folded A3 **cover leaf** (001, 002, 147, 148) and the bound-in **Zahlkarte** (149–152) are a coated white, 100+ city-block from the interior's `W`. Neither the paper mask nor the grade's level lines describe them |

There are **no binder-clip holes and no neighbour page in frame**. The spread
variant's inner-boundary method has no input here and hole inpainting has
nothing to fill, which is why the two variants exist at all.

## Inputs

- the issue descriptor, `issues/<ISSUE>/issue.json`, read through
  `r000_issue.py` — `scan_dir`, `thumb_150`, `tmp`, `colors`, `binding`, `pages`
- `tools/img/cmyk_reconstruction/target/release/cmyk_reconstruction`, built
  (`cargo build --release` in `tools/img/cmyk_reconstruction`)
- the ICC pair in `tools/img/`: `USWebCoatedSWOP.icc`, `AdobeRGB1998.icc`
- `magick` (ImageMagick 7)
- Python 3.11+ with `numpy`, `scipy`, `pillow` — on this box `/usr/bin/python3`
  has all three

## Run

```bash
cd tools/img/scan2ocr/rules
python3 r005_masters_sheet.py            # every page in the descriptor
python3 r005_masters_sheet.py 6 41 56 92 # named pages
```

The only per-issue knob is `ISSUE = "SH8601"` at the top of the program. No CLI
flags, no environment knobs — every path is derived from the descriptor. Page
numbers are positional purely so the work can be split across processes, exactly
as in `r010`.

~45 s per page; ~2 h for 152 pages. Deterministic and local — no model is
called.

**After any change to this step, wipe `<tmp>/masters600` and start again from
page 1.** `r010`'s block ids and `r020`'s cache are keyed on the masters, and a
directory mixing two runs is not something any downstream check can see.

## Outputs

```
<tmp>/masters600/NNN.png         the OCR master — r010 reads this   (the contract)
<tmp>/masters600/NNN.stamp.txt   which profile and which curve made that master
<tmp>/figures600/NNN.png         the figure master — r145 reads this
<tmp>/cmyk2400/NNN.tif            the CMYK archival form, deflate-compressed
<tmp>/cmyk2400/NNN.colors.txt     the profile the separator was actually run with
<tmp>/debug600/NNN.png           the overlay: the four traced lines, in green
```

`<tmp>/masters600` is derived by `r000_issue.py`, because it is the contract the
rest of the chain depends on. The other three directories are this step's own
workings and are named in this step. `r010` and `r145` build their paths from
the page number, so the two sidecars sit beside the images they describe without
disturbing anything that counts files.

Every master is the **same size** — 231 × 304 mm at 600 dpi, 5457 × 7181 px —
because `r010`'s block geometry and `r145`'s figure crops share one coordinate
system. If each page had its own width, a block's page-fraction would mean
something different on every page. The traced page is anchored at its own
top-left **trim corner** and the shortfall is paper white.

The canvas is **derived** from the widest and tallest entry in `PAGE_CLASSES`,
not measured separately, so a page that passes the size gate cannot overflow it
— for **any** class, not only for A4. Two independent numbers there would
eventually disagree and truncate a page quietly; as it is, an overflow is
impossible and the step refuses one anyway rather than cropping. The price is
15 mm of extra fabricated white on the right of the 145 pages that are A4: the
cover leaf's fold flap has to fit, and a canvas per class would break the one
thing `r010` and `r145` rely on.

## The procedure

```
scan_dir/NNN.png
  -> measure skew on the 150 dpi THUMB (projection variance; scale-invariant)
  -> paper mask: distance from the profile's paper white
  -> is there enough paper here to trace from?          [picks the edge finder]
  -> check the torn side against parity                     [the parity gate]
  -> rotate to level, then RE-MEASURE the residual and assert it is ~0
  -> TRACE each page edge as a line, robustly:
       PAPER vs BED, 144 pages:
         clean edges  -> band MEDIANS of the per-row/col paper boundary
         verso fringe -> band 5th PERCENTILE of the per-row paper ends
         recto fringe -> NOT traced: one vertical line at p95 of the paper
                         starts plus ~1 mm
       INK vs BED, the 8 pages not printed on this issue's paper:
         all four edges -> band MEDIANS of the sheet's own boundary against
                           the bed, the sheet found as one connected region
  -> fill everything outside the traced page with paper white
  -> drop bed components that touch the frame AND lie mostly outside the page
  -> the traced page must match one of PAGE_CLASSES          [the size gate]
  -> separate to CMYK with tools/img/cmyk_reconstruction     [not reimplemented]
  -> two renders off that ONE separation: masters600 carries the black-point
     curve, figures600 does not
  -> masters600/NNN.png + NNN.stamp.txt, figures600/NNN.png,
     cmyk2400/NNN.tif + NNN.colors.txt, debug600/NNN.png
```

### Why the edges are TRACED and not cropped to

Levelling the text leaves the paper edges tilted, so an axis-aligned crop
inscribed in the page gives up **0.5–3.6 mm per edge** (measured on 041, 056,
092). Cropping to the page was tried first and cost too much. So each edge
becomes a **line**, and everything outside it is filled with paper white.

**The fill IS fabrication, and it is deliberate and explicit:** the wedge outside
a traced edge is paper that the scan frame did not contain. It is stated here so
that nobody later reads a clean margin as evidence about the copy.

### Traps, each one paid for during the prototype

- **The rotation sign.** `scipy.ndimage.rotate` (which measures) and
  `PIL.Image.rotate` (which applies) turn in opposite directions. Getting the
  sign wrong **doubled** the skew on p056, to −1.28 deg, and every downstream
  geometry check still passed because nothing re-measured. The step therefore
  re-measures the residual on the levelled page and fails if it exceeds
  `SKEW_RESIDUAL_MAX`.
- **Per-column extremes are not an edge.** "The last paper row in this column"
  is dragged outward by a few paper-coloured pixels in the bed transition and
  left **3.8 mm of bed** at the foot of p056. Clean edges come from the band
  **median** of the boundary, which those few pixels cannot move; only the
  fringe uses a low percentile.
- **Rows that cross full-bleed art are not edge samples.** Their "last paper
  pixel" collapses hundreds of px inward, and unfiltered they tilted p056's
  traced fringe by **+2.56 deg**. Samples more than `TRACE_OUTLIER_MM` (12 mm)
  off the median are dropped before the bands are formed.
- **A recto's torn edge must not be traced.** On a verso the tear sits inside
  the frame and wanders, so it has to be traced. On a recto it is flush with the
  frame edge: a few px cut perfectly vertically is always enough, and a fitted
  line there fits noise — it claimed **+0.62 deg** on p041, where the true edge
  is the frame.
- **The prop is not paper, and a distance ball cannot say so.** City-block
  distance from paper white has no notion of hue, and the yellow prop under the
  sheet reads (237,205,111) on p006 — distance **104** from the current
  W(209,175,157) and **108** from the W as first found, i.e. *inside* a 110 ball
  either way. The foot trace then ran into the prop and left **7 mm of
  prop and bed shadow** standing at the bottom of the master; the prototype's
  own p006 output has the same 7 mm. The separating measurement is **G − B**:
  among pixels the distance test calls paper it is 11 at p50 and 22–26 at p99,
  and across the prop it is 99–107, so the threshold sits in the middle of a
  70-level gap. It must **not** be the looser test the prototype used for the
  bed flood (`R+G > 300 AND B < 160 AND bright`) — that also matches ordinary
  warm paper, (215,174,154) passes it, which cost nothing where it was used but
  takes 6 % of the sheet out of the paper mask if reused here.
- **A bed flood must not eat a photo.** p006's board picture bleeds into the
  torn edge and connects to the bed through its own black chips; an
  unconstrained connectivity pass erased a third of it. A component is dropped
  only if **most of it lies outside** the traced page (`BED_OUTSIDE_FRAC`). A
  bed sliver is ~all outside; a photo is ~all inside.

### Accepted loss, decided explicitly

Where the tear ran into the type area, those characters are gone. Accepted — it
is a fact about this copy, not a defect of this step.

### Known defect, closed by the prop fix

The prototype left a sliver of bed and prop in p092's corner, where two fitted
lines meet and the bed component read as mostly inside the page. Excluding the
prop from the paper mask moved the foot trace onto the real trim and the sliver
is gone. Re-measured after the profile was re-measured, over a 6 mm band inside
each traced edge: p092 reads 0.55 % at the top and 0.25 % at the foot, p041
1.0 % at the top, and every run of it sits **inside** the trim, on the printed
section banner and the footer rule. No bed, no prop — see Verification step 4.

## The eight pages that have no paper to trace from

Tracing by paper colour needs paper. **Measured over all 152 thumbs** — the
fraction of the frame's rows (and columns) that are more than `BODY_PAPER_FRAC`
paper, the smaller of the two, sorted:

```
001 0.000   002 0.001   147 0.001   148 0.015
150 0.018   151 0.024   149 0.026   152 0.027
--------------------------------------------- and then nothing until
067 0.167   079 0.181   007 0.247   006 0.317  ...  146 0.968
```

Eight pages, and a gap of 0.14 to the ninth. They are the folded **A3 cover
leaf** (001, 002, 147, 148) and the bound-in **Zahlkarte** (149–152).

The reason is not only full bleed — 148 has ordinary white margins. It is that
**neither is printed on this issue's paper**: the cover leaf and the card are a
coated white stock, and the profile's `W` (209 175 157) describes the interior's
yellowed sheet, so a coated white sits 100+ levels of city-block distance away
and the paper mask does not see it as paper at all.

For those eight the edge comes from **ink vs bed** instead: the bed is
near-black, uniform and connected to the frame; a printed sheet is not; and the
sheet is **one connected region touching nothing else**. Same `BED_LUM`, same
prop test, same `trace()` — what changes is only which mask the boundaries are
read off, and that all four edges are traced as clean ones (a cover leaf's inner
edge is a **fold**, not a tear, and the card was cut on all four sides).

**The switch is that measurement, not a page number.** A page number would be a
lie about *why* the page is different and would not survive a re-scan;
`FULLBLEED_PAPER_FRAC` sits at 0.10, in the middle of a gap five times its own
width.

Two things had to be got right:

- **Fill the holes.** A photograph's own blacks are as dark as the bed. They are
  not connected to the frame, so they are holes in the sheet, and they are
  filled before the largest component is taken.
- **A one-pixel bridge is not part of a sheet.** On p151 the card connects to
  the lit top edge of the yellow prop through a **3 px strip** at the frame's
  left margin, and the traced foot then lands 94 mm below the card — a 205 mm
  card measured as 299. An opening of `SHEET_OPEN_MM` (1 mm) breaks every such
  bridge; measured on all eight pages, p151 is the only one whose traced size
  moves by more than 1 mm.

Where the sheet runs off the side of the frame the samples are a constant 0 (or
`w-1`) and the fitted line is that frame edge. That is the honest answer: the
scan does not contain the trim, so the traced width is a **lower bound** on the
leaf, not a measurement of it.

## The size gate — three classes, measured

A traced page must come out one of the sizes **this issue actually has**. A page
that matches none of them means a traced line ran away, and the fill would then
be eating type rather than bed.

| class | window | what lands there |
|---|---|---|
| **A4 sheet** | 210 × 297 ± 6 mm | the interior pages — 142 of the 144 that trace from paper land in 208.9–212.0 × 294.0–298.5 mm at thumb scale — and three of the four cover-leaf pages: 001 at 210.1 × 296.0, 147 at 215.0 × 296.0, 148 at 209.3 × 296.4 |
| **cover leaf** | 224 × 297 ± 7 mm | 002 at 223.2 × 295.7 |
| **Zahlkarte** | 146 × 205 ± 6 mm | 149–152 at 143.7 × 204.4, 144.1 × 204.6, 144.4 × 205.1, 144.5 × 203.5 |

**The cover is a folded A3 sheet**, so 001/002 and 147/148 are its two halves.
002 is the inside of the front half, and its scan holds the whole page **plus
~14 mm of the fold flap** — paper, part of this sheet, and kept. 001 and 147
have the same flap; their scan frames simply cut it off, which is why they
measure A4. The frame widths are 218.1 mm for 001 and 223.9 for 002, against
211.5–217.6 for the interior: it is the **frame** that is wider on those two
scans, and on both the sheet runs off the side of it.

**The Zahlkarte is a payment card** (Zahlkarte/Postüberweisung) printed blue on
a white card, bound into the back of the issue. It is an A5 leaf (148 × 210 mm)
with the frame cutting a few mm off two of its edges. It is genuinely not an A4
page and **not a defect**, so it passes as its own class rather than failing a
gate written for a different piece of paper.

The tolerance is per class because the evidence behind each is: ~145 pages for
A4, four for the card, one for the cover leaf. Two interior pages fall outside
every window — 007 and 117 — and both are trace failures rather than sizes this
issue has; see *Known outliers*.

## The grade — call the converter, render twice

The separation is **not reimplemented here**.
`tools/img/cmyk_reconstruction` already does the hard part and `colors.txt` was
written for it: 8 RGB anchors (W C M Y R G B K) plus 4 per-ink level lines. It
works in the DENSITY domain — `d = -log10(rgb/W)`, six polynomial features, a
least-squares solve against the seven ink targets, then full GCR
(`K = min(C,M,Y)`, subtracted from each). Because the paper white is the density
reference, the scan's global R/B 1.163 cast falls out for free.

```
cmyk_reconstruction --colors <profile> <in.png> <out.tiff>
magick <out.tiff> -profile USWebCoatedSWOP.icc -profile AdobeRGB1998.icc <rgb.png>
```

`colors` is **optional** in the descriptor. With no profile the grade falls back
to the **built-in anchor set** — the eight anchors the old separation compiled
in, copied into `BUILTIN_ANCHORS` rather than imported, because `scan2mrc` is
retired and `scan2ocr` must not reference it — and to identity levels, because a
level line is a per-ink contrast decision that must be measured, not guessed.

### One separation, two renders

The two consumers want different images, so both come off **one** separation:

| render | for | wants |
|---|---|---|
| `masters600/NNN.png` | `r010` OCR | contrast: type to solid black. The ICC render **with the black-point curve on it**. Clipping is a feature |
| `figures600/NNN.png` | `r145` figure cuts | fidelity: the straight ICC render. No clipped highlight, no crushed shadow, **no curve** |

Ink at ~66 is not a bug, it is honesty: 100% SWOP black is not RGB 0. The OCR
master boosts it anyway — tesseract binarises, so the boost costs nothing there
— which is exactly why there are two renders and not one.

**The curve is one issue-wide constant, never per page.** ImageMagick's
`-level 30%,100%`, and exactly that arithmetic:

```
out = clamp((in - 0.30 * 255) / (0.70 * 255) * 255)
```

The prototype measured a black point per page — the 2nd percentile of that
page's own ink — and stretched to it. That makes the same grey mean a different
thing on every page: a page whose darkest pixel is a photograph gets a different
transfer from the text page beside it, and nothing downstream can see that it
happened.

**30 % was chosen on the worst page, measured on all four.** "glyph p50" is the
median level of the pixels a glyph is made of in a body-text window — 0 is solid
black — and "paper p50" is the median of the paper beside it:

| level | none | 20 % | 25 % | 30 % | 35 % |
|---|---|---|---|---|---|
| glyph p50, 006 | 69 | 28 | 14 | **1** | 0 |
| glyph p50, 041 | 54 | 8 | 1 | **0** | 0 |
| glyph p50, 056 | 53 | 5 | 0 | **0** | 0 |
| glyph p50, 092 | 72 | 32 | 18 | **4** | 0 |
| paper p50 | 255/255/254/254 | — | — | unchanged | 041's paper starts to drop |

30 % is where the worst page's type goes solid black while the paper floor is
still untouched. 35 % buys nothing — the type is already there — and starts
eating paper, which is the one thing a black-point curve must never do.

**And the figure render must not have it.** A black-point curve crushes a
photograph: measured on p006's cover photo, this level drives the pure-black
area of the picture from **25 % to 42 %**. Type wants the crush; pictures do
not. `r145` cuts its pictures from `figures600`, which is why that render stays
straight.

(The implementation is four lines of numpy rather than a `magick` call, so the
curve costs no extra pass over a 110 megapixel image. It agrees with
`magick -level 30%,100%` to within one level — verified against it.)

### THE LEVELS ARE NOT TRUSTED, THEY ARE PROVEN

SH8601's `colors.txt` as written has `LK 90 95`, which maps K's 229–242 window
onto the full range: ordinary black text falls **below** the low point and is
clipped toward zero ink, and 93 % of the page snaps to pure white. The result
still looks like a page, which is what makes it dangerous — nothing downstream
can tell a washed-out master from a clean one.

So the grade is measured against the ungraded page it came from, and the step
**fails the page** rather than publishing it. Two independent checks:

| check | measured on p056 |
|---|---|
| the graded page must keep `GRADE_INK_KEEP` (0.70) of the scan's ink | ungraded 17.1 % inked; levels neutralised keeps 15.3 % (0.90), `colors.txt` as written keeps 5.7 % (**0.34**) |
| the darkest ink's p50 must sit `MIN_INK_CONTRAST` (120) below paper white | 201 with the levels neutralised, 162 with them as written |

The level lines have since been re-measured (`LC 5 100 / LM 4 100 / LY 5 100 /
LK 3 100`, against a re-measured white point `W 209 175 157`), and both checks
now pass on every page that is printed on this issue's paper. The profile as
first found is kept beside the current one as `colors_asfound.txt`; do not
neutralise the levels to get past a failure — re-measure them and re-run.

**Both checks are statements about the level lines, and the level lines were
measured on this issue's paper.** They cannot judge a page that is not printed
on it, because the two sides of the ratio then use two different papers: the raw
side measures ink as a distance from the *sheet's own* white (`STOCK_PCT`) and
the graded side from what the profile's `W` grades to. Measured on p149: the
card's pale cyan field sits 52 city-block from its own stock — ink, by the raw
test — and grades to 254, because relative to a `W` that is yellower and darker
than this card it has almost no density. The ratio reads **0.31** and the master
is, by eye, excellent: crisp blue type, the pale field gone to paper.

So on the eight `ink/bed` pages the two checks **report instead of refusing**,
the page's log line carries `GRADE UNPROVEN, not this issue's paper: …`, and one
weaker gate stays hard — the graded page must not have come out **blank**
(`GRADE_MIN_INK_FRAC`, 0.5 % of the canvas against a measured 2.9–85.9 %). If
the pale tint on the coated stock has to survive, the fix is a second measured
profile for that stock. That is a decision, not a looser constant here.

## The stamp — every artefact says which grade made it

A finished master used to carry no record of the numbers that produced it, and
this issue paid for that: `colors.txt` was re-measured, the four masters
standing in `masters600/` were now stale, and it took a **human eye noticing
yellow corners** to find out. Nothing mechanical could have.

So everything this step writes carries the grade's fingerprint — the 8 anchors,
the 4 level lines, the OCR level constant, and a 12-hex `grade-sha` over exactly
those — plus what was decided about the page's geometry:

| where | how |
|---|---|
| `masters600/NNN.png` | a PNG `tEXt` chunk keyed `r005` |
| `masters600/NNN.stamp.txt` | the same text, readable without opening a 110 megapixel PNG |
| `figures600/NNN.png` | PNG `Comment` |
| `cmyk2400/NNN.tif` | TIFF `ImageDescription` |
| `cmyk2400/NNN.colors.txt` | the profile file the separator was **actually run with**, kept rather than deleted with the scratch directory |
| the run's log | the whole block once at the top, and `grade <sha> level 30%` on every page line |

Three copies because each survives a different accident: the chunk survives the
file being copied out of `masters600/`, the sidecar survives not wanting to
decode the image, and the log survives the files being deleted.

Detecting a stale master is now a string comparison — see Verification step 5.

### A failed page leaves nothing publishable behind

A page that fails a gate is skipped, its four **publishable** artefacts are
deleted, its number is printed on stderr, and the process exits non-zero with
the list. The sweep does not abort at the first failure — 152 pages is two
hours, and losing it to page 002 means nobody ever sees what pages 003–152 do.
What the step never does is publish the page anyway.

`debug600/NNN.png` is the exception and is **kept**: nothing counts it, nothing
publishes it, and it is the one artefact that says why the page failed. It is
also written *before* the size gate rather than at the end of the page, because
a page that fails that gate never reaches the end — the message has always said
"look at `debug600/NNN.png`", and until now that file had just been deleted, if
it was ever written at all.

## The parity gate

The torn side must match parity on all 152 pages. A disagreeing page is
misfiled or mis-rotated, and finding that after a full-resolution sweep is
expensive, so it is checked on the **thumb**, before the 800 MB scan is opened.

A guillotined edge is straight to within a pixel row; a torn edge jitters from
row to row. So parity decides, and only a **confident** disagreement
(`ratio >= TORN_CONFIDENT_RATIO`) fails the page. Ambiguity passes.

**Re-measured over all 152 thumbs after `colors.txt` was re-measured**, because
this gate reads the paper mask and a new paper white is a new mask. Of the 144
pages that have a paper edge to read — the other 8 go to the ink/bed finder and
are not asked — **143 agree with parity, and they agree loudly**: the smallest
ratio among them is **2.73**, the median 11.98. Exactly one disagrees, p117 at
**1.64**, which is below every single agreeing page.

| | old W (214 195 186) | current W (209 175 157) |
|---|---|---|
| agreeing pages start at | 1.6 | **2.73** |
| disagreements | 002 at 1.33, 116 at 1.45 | 117 at 1.64 |
| floor | 1.6 | **2.5**, in the gap |

Leaving the floor at 1.6 would fail p117 for being misfiled, which it is not:
p117's paper mask sees only the cream panel inside a full-bleed dark ground, so
its jitter measurement means nothing. It fails the **size** gate two steps
later, which is the check that can say what is actually wrong with it.

## The debug overlay

One per page, always: the four traced lines drawn in green on the **levelled,
unfilled** page, at 1/5 scale. This is the artefact the user reviews, so it
deliberately shows the page as the tracer saw it — bed, fringe and all — with
the decision drawn on top.

## Verification

```bash
cd tools/img/scan2ocr/rules

# 1. every page produced all six artefacts, and nothing else did
python3 - <<'PY'
import os, r000_issue, r005_masters_sheet as R
iss = r000_issue.load(R.ISSUE)
for d, ext in ((R.OUT_MASTER, ".png"), (R.OUT_MASTER, ".stamp.txt"),
               (R.OUT_FIGURE, ".png"), (R.OUT_CMYK, ".tif"),
               (R.OUT_CMYK, ".colors.txt"), (R.OUT_DEBUG, ".png")):
    have = sorted(f[:3] for f in os.listdir(d) if f.endswith(ext))
    want = ["%03d" % p for p in iss.page_range]
    miss = [p for p in want if p not in have]
    print(f"{d.name:12s}{ext:12s} {len(have):3d}/{len(want)}  missing:",
          (miss[:12] + ["..."] if len(miss) > 12 else miss) or "none")
PY

# 2. every master is the SAME size, and it is the expected one (231 x 304 mm)
python3 - <<'PY'
from collections import Counter
from PIL import Image
import os, r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
sizes = Counter(Image.open(R.OUT_MASTER / f).size
                for f in sorted(os.listdir(R.OUT_MASTER)) if f.endswith(".png"))
want = (round(R.MASTER_W_MM * R.MM), round(R.MASTER_H_MM * R.MM))
print("expected", want, "| found", dict(sizes))
assert list(sizes) == [want], "masters are not one uniform size"
PY

# 3. RESIDUAL SKEW of the published masters is ~0 -- re-measured, not trusted.
#    This is the check the rotation-sign trap defeats when it is skipped.
python3 - <<'PY'
import numpy as np, os
from PIL import Image
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
for f in sorted(os.listdir(R.OUT_MASTER)):
    if not f.endswith(".png"):
        continue
    a = np.array(Image.open(R.OUT_MASTER / f).reduce(4).convert("L"), float)
    print(f, "residual %+.2f deg" % R.measure_skew(a))
PY

# 4. NO BED SURVIVES: a 6 mm band inside the TRACED PAGE's own four edges holds
#    no bed and no prop -- except where full-bleed art legitimately reaches the
#    trim.  Two things this check has to get right:
#      - the page's box inside the canvas is READ FROM THE STAMP, not guessed
#        from the pixels.  The fabricated margin and the page's own paper are
#        both white, and a bbox of "not quite white" guesses wrong on a master
#        whose paper the curve has pushed to 255.
#      - it reads figures600, the UNCURVED render.  BED_LUM was measured on
#        unclipped pixels; on the curved master a printed RED banner (lum 101)
#        lands at 35 and reads as bed.
python3 - <<'PY'
import numpy as np, os, re
from PIL import Image
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
b = int(6.0 * R.MM)
for f in sorted(os.listdir(R.OUT_MASTER)):
    if not f.endswith(".png"):
        continue
    s = (R.OUT_MASTER / f.replace(".png", ".stamp.txt")).read_text()
    pw, ph = (int(v) for v in re.search(r"^page-px\s+(\d+) (\d+)$", s, re.M).groups())
    rgb = np.array(Image.open(R.OUT_FIGURE / f).convert("RGB"))[:ph, :pw]
    lum, prop = rgb.mean(2), R.prop_mask(rgb)
    cells = []
    for k, sl in (("top", (slice(None, b), slice(None))),
                  ("bot", (slice(-b, None), slice(None))),
                  ("left", (slice(None), slice(None, b))),
                  ("right", (slice(None), slice(-b, None)))):
        cells.append("%s dark %6.3f%% prop %6.3f%%"
                     % (k, 100 * (lum[sl] < R.BED_LUM).mean(), 100 * prop[sl].mean()))
    print(f, "%-11s %s |" % (re.search(r"^page-class\s+(.*)$", s, re.M).group(1),
                             re.search(r"^page-size\s+(.*)$", s, re.M).group(1)),
          " | ".join(cells))
PY

# 5. THE STAMP: every master names the grade that made it, and it is the CURRENT
#    one.  This is the check that would have caught the three silently stale
#    masters -- a string comparison, not a judgement about colour.
python3 - <<'PY'
import os, re
from PIL import Image
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
for f in sorted(os.listdir(R.OUT_MASTER)):
    if not f.endswith(".png"):
        continue
    side = (R.OUT_MASTER / f.replace(".png", ".stamp.txt")).read_text()
    chunk = Image.open(R.OUT_MASTER / f).info.get("r005", "")
    sha = re.search(r"^grade-sha\s+(\S+)$", side, re.M).group(1)
    print(f, sha,
          "CURRENT" if sha == R.GRADE_SHA else "*** STALE -- re-run this page ***",
          "| chunk == sidecar" if chunk == side else "| *** CHUNK DISAGREES ***",
          "|", re.search(r"^edge-finder\s+(.*)$", side, re.M).group(1))
PY

# 6. THE CURVE: the OCR master's type is black and its paper is untouched, and
#    the FIGURE render did not get the curve.  A body-text window per page, in
#    mm from the traced page's top-left corner; "glyph" is the INTERIOR of the
#    strokes, chosen on the uncurved render and then measured in both.
python3 - <<'PY'
import numpy as np
from PIL import Image
from scipy import ndimage as ND
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
WINDOWS = {"006": (14, 100, 58, 180), "041": (16, 60, 60, 140),
           "056": (20, 60, 90, 140), "092": (12, 150, 45, 260)}
for stem, mm in sorted(WINDOWS.items()):
    box = tuple(int(v * R.MM) for v in mm)
    fig = np.array(Image.open(R.OUT_FIGURE / f"{stem}.png").crop(box).convert("L"), float)
    ocr = np.array(Image.open(R.OUT_MASTER / f"{stem}.png").crop(box).convert("L"), float)
    glyph = ND.binary_erosion(fig < 128, np.ones((3, 3)))
    paper = fig > 200
    print(f"p{stem} window {mm} mm | ink {glyph.mean():5.1%} | "
          f"glyph p50 {np.median(fig[glyph]):5.1f} -> {np.median(ocr[glyph]):5.1f} | "
          f"paper p50 {np.median(fig[paper]):5.1f} -> {np.median(ocr[paper]):5.1f}")
PY
```

### What it read, on the twelve pages verified

**1, 2, 3.** All twelve masters are 5457 × 7181 px, and every one re-measures
**+0.00 deg** of residual skew — including 092, whose scan is 1.08 deg out, and
152, whose scan is 0.62 deg out.

**4.** The bands, and every non-zero one accounted for:

| page | class | traced | non-zero bands | what it is |
|---|---|---|---|---|
| 001 | A4 sheet | 210.1 × 296.0 | top 7.9 %, left 18.6 % dark; 7.8–21.6 % "prop" on all four | the **full-bleed cover**: teal border and black photo to the trim, and the orange corner banners, which trip the prop test (see below) |
| 002 | cover leaf | 223.2 × 295.7 | left 14.0 % "prop", 0.13–0.17 % dark | the yellow `SOFTWEAR-SERVICE` panel running to the left trim |
| 006 | A4 sheet | 208.6 × 298.5 | right 27.4 % dark, bot 1.4 % | the C128 board photo bleeding to the torn edge; the foot is the printed rule, 2–3 mm **inside** the trim |
| 041 | A4 sheet | 208.2 × 296.8 | top 1.0 % "prop" | the printed section banner |
| 056 | A4 sheet | 210.7 × 297.7 | bot 0.53 % | the printed footer rule, 5–6 mm inside the trim |
| 092 | A4 sheet | 212.1 × 298.3 | top 0.55 %, bot 0.25 % | the same two |
| 147, 148 | A4 sheet | 215.0 × 296.0, 209.3 × 296.4 | ≤ 0.17 % | the footer rule |
| 149–152 | Zahlkarte | 143.7–144.5 × 203.5–205.1 | **0.000 % on every band** | — |

Every dark run was located before it was accepted: on 006, 056, 092 and 147 the
dark rows sit 2–6 mm **inside** the foot, which is where a printed rule is and
not where a paper edge is. **No bed and no prop survives on any of the twelve.**

**The prop column reads printed ink on a full-bleed page, and that is a
limitation of the check, not of the master.** `prop_mask` is "yellow and
bright", which is true of the physical prop under the sheet and equally true of
a printed orange banner. On the ink/bed pages the real prop cannot be there at
all: it is part of the bed mask that found the sheet in the first place.

**5.** Twelve of twelve masters carry `grade-sha 2b29e17a6be4`, the sha of the
current `colors.txt` plus `OCRLEVEL 30 100`; the PNG chunk equals the sidecar on
all twelve.

**6.** The curve, measured on the published pair:

| page | ink in window | glyph p50 figure → master | paper p50 figure → master |
|---|---|---|---|
| 006 | 5.1 % | 87 → **15** | 255 → 255 |
| 041 | 5.1 % | 95 → **26** | 255 → 255 |
| 056 | 10.3 % | 79 → **3** | 255 → 255 |
| 092 | 4.0 % | 87 → **15** | 255 → 255 |

Type goes from a mid-grey to near-black and the paper floor does not move at
all — which is the whole claim of `-level 30%,100%`. (These are higher than the
figures in the constant's own table because the glyph *set* is defined
differently: this check takes stroke interiors on the uncurved render and
measures the same pixels in both, which keeps the two columns comparable at the
cost of including more of the stroke's shoulder. The conclusion — worst page
solid, paper untouched — is the same either way, and both are recorded.)

**p117 fails, and nothing was published for it** — see below.

## Known outliers — two pages of 152 do not trace

Seven pages used to fail. Six of them were not outliers at all, only pages
printed on the **other stock** in this issue, and they now trace from ink vs bed
and pass as their own classes: 001, 002, 147 and 148 (the folded A3 cover leaf)
and 149–152 (the Zahlkarte). Two pages still fail, and **both are trace
failures, not size classes** — there is nothing about the paper that is
different, only about what the tracer can see.

### p117 — the tracer follows the panel, not the sheet

An ordinary A4 ad page — a te-wi book advertisement on a **full-bleed dark-brown
ground**. Both edge finders fail on it:

| finder | what it traces | why |
|---|---|---|
| paper vs bed (the one it takes: its paper fraction is 0.545, far above `FULLBLEED_PAPER_FRAC`) | **165.6 × 267.9 mm** | the paper mask sees only the ad's cream **panel** inside the dark ground, and traces that. `debug600/117.png` shows all four green lines sitting inside the printed border |
| ink vs bed, at the `BED_LUM` every other page uses | **170 × 115 mm** | the ad's brown ground measures lum 45–72 against a bed at 21–40; the flood walks straight into the page |

A bed threshold that does trace p117 exists — at `lum < 40` the ink/bed finder
returns 209–210 × 296 mm — but it is 30 levels below the one that works
everywhere else, and at that level the bed on 001, 006, 056 and 092 stops being
caught. It would be a constant tuned to one page, which is the thing this step
does not do.

### p007 — a foot traced from too narrow a base

**208.7 × 304.0 mm**, 7 mm too tall. The page is a full-page circuit-board
photograph with text only at the foot and in a caption column, so only **25 % of
the frame's columns** are more than `BODY_PAPER_FRAC` paper and the top and
bottom lines are fitted from that narrow base. The sheet is also **flush with
the frame at the top** (nothing above the red banner), so the head trace lands
at 0 and every millimetre of error at the foot goes straight into the height.
`debug600/007.png` shows it: three lines on the trim, and the foot line down in
the prop.

This one is worth re-measuring rather than deciding — the fix is a better rule
for which columns carry a top/bottom sample, not a looser gate — but it is one
page and the constants that would change are the ones 006, 041, 056 and 092 were
verified against.

### What happens to a failed page

Its four publishable artefacts are deleted, `debug600/NNN.png` is **kept** (it
is the artefact that explains the failure, and the size gate's message points at
it), the page is named on stderr, and the process exits non-zero with the list.
The disposition of 007 and 117 — crop by hand, re-trace, or accept the issue
without them — belongs in the issue's `LOG.md`. "The step refused it" is not a
decision.

### The tally

Fourteen pages have been run through the current code: **12 published, 2
failed**. The remaining 138 were traced at thumb resolution only, where all of
them land inside the A4 window (208.9–212.0 × 294.0–298.5 mm). A full sweep is
still the thing that settles the count, and it has not been run.

## Notes

- Constants live at the top of `r005_masters_sheet.py`, heavily commented, and
  everything describing paper is written in **millimetres**. No CLI knobs, no
  env knobs — different agents used an env surface differently once and produced
  numbers for files that never existed.
- **Read `FINDINGS.md` before changing anything here.**
- The prototype this step was verified against traced 006, 041, 056 and 092. Any
  change to the tracing constants should be re-measured on all four before a
  full sweep: 006 is the full-bleed-photo case, 041 the recto flush cut, 056 the
  bed-at-the-foot case, 092 the worst skew and the open corner defect.
- Since the ink/bed finder exists, **eight** more pages belong to that set:
  001 (a cover printed to all four trims), 002 (the fold flap, the only page in
  its class), 148 (white margins but the wrong stock — the case that proves the
  switch is about the stock and not about bleed) and 151 (the one-pixel bridge
  to the prop). Any change to `BED_LUM`, `SHEET_OPEN_MM` or
  `FULLBLEED_PAPER_FRAC` has to be re-measured on those four as well.
- A change to `PAGE_CLASSES` changes `MASTER_W_MM`/`MASTER_H_MM`, and therefore
  every master's pixel size and every page-fraction downstream of it. Wipe
  `masters600/` and start from page 1, as above — this is not a change that can
  be made for one page.
