# 005 — Scan to 600 dpi master, SHEET variant

**Applies to:** all — but only where the descriptor says `"binding": "sheet"`.
A `"binding": "spread"` issue runs `r005_masters_spread` instead, and this
variant is then recorded in that issue's `LOG.md` as **not applicable —
binding**.

**Goal:** turn the raw ~2400 dpi scan of one loose sheet into the deskewed,
matted, graded **600 dpi masters** that `r010` OCRs and `r145` cuts figures
from. This is the first step of the chain; it owns everything between the
scanner and `r010`'s input.

**The thumbs are DERIVED, not found.** `thumb_150` points into `<tmp>`; a
`thumb/` directory sitting beside the scans is not an input and is not trusted
(r000, *A `thumb/` you FIND beside the scans is NOT an input*). Every threshold
below was measured on thumbs made with `magick -scale 6.25%` from a 2400 dpi
master -- byte-identical to the set beside the scans, verified on 8610 p050 and
8612 p002/p050/p150 -- and does not transfer to a set made any other way.


This is a **program step**: the orchestrator runs it, checks the exit status and
runs the Verification block below. There is no editorial judgement in it and
nothing to dispatch.

## The first action — TWO QUESTIONS, asked before anything is graded

Step 005 is the chain's first step, and **its first action is to ask**. Two
properties of the physical copy decide everything below; neither can be
recovered from the pixels; and guessing either produces a **plausible-looking
wrong result that nothing downstream can see**:

| question, in the owner's terms | descriptor key | what it decides |
|---|---|---|
| **How is this issue bound?** A3 sheets held with **clips**, or A4 sheets torn off a **glued** spine? | `binding` | the **edge maths** — which variant of step 005 runs |
| **Which pages are printed on which paper?** the good white stock, or the cheap interior stock? | `paper` | the **grade**, per page |

If the descriptor carries no answer, the step prints the question — both options
in one line each, the evidence for answering it, and the JSON to paste back —
and **exits non-zero having written nothing**. No scan is opened, no output
directory is made. `first_action()` runs before the page list is even parsed.

**This is the ONE thing step 005 refuses over.** Everything else — parity, skew
residual, page class, canvas fit, every number the grade reports — it publishes
and *notes*, because everything else is a defect of a page that a human can see
in the artefact it published (see *A failed page leaves nothing publishable
behind*). An unanswered question is not a page defect and not a measurement: it
is a decision only the owner can make, with the copy in hand.

The two questions are asked **together**, and they are asked **before the
variant is chosen** — they are questions about the *issue*, they are the same
two whichever variant ends up running, and a descriptor with no `binding` cannot
be routed to a variant at all. The `binding != "sheet"` check ("this issue
belongs to `r005_masters_spread`") is the second half of the same function, and
runs after them.

### What the step offers as evidence

For the paper question it measures both of these on the 150 dpi thumbs, about
0.1 s a page — cheap enough to print for the whole issue, so the question comes
with the means to answer it rather than as a bare demand:

- **which pages took the ink-vs-bed edge finder** — the fraction of the frame's
  rows/columns that this issue's paper white can see, below
  `FULLBLEED_PAPER_FRAC`. This is the strongest signal the step has, and it is
  **one-sided**: it finds pages whose stock the paper mask is *blind* to, which
  is the same fact that makes the grade wrong on them. A good stock the mask
  happens to see will not show up, which is why the answer is the owner's and
  not this measurement's.
- **each page's own white** — the `STOCK_PCT` percentile of its non-bed pixels,
  printed against the low profile's `W`. On SH8601 the eight non-interior pages
  read 240–250 across the board; the interior reads 217 192 179.

**THE EDGE-FINDER PRE-FILL IS ONE WITNESS AND THE WEAKEST OF THREE.** It is
one-sided, and it produces both misses and false positives:

- SH8603: it offered `[1]` where the answer was eight pages.
- SH8604: it offered `[1, 60]`, and p060 is an INTERIOR page printed under a
  full-page salmon tint — its own white is 200 169 154, the interior's.

Two stronger witnesses, both free:

1. **The own-white gap.** Pool each page's own white and sort. The wrapper and
   any bound-in card sit far from the interior with a clear gap: SH8604 reads
   163 (136), 002 (125), 164-166 (91), 168 (90), 167 (85), then NOTHING until
   p016 at 20.
2. **The scan resolution.** MEASURED on SH8602, SH8603 and SH8604: the pages
   scanned at 2400 dpi are EXACTLY the wrapper and the card, the interior at
   600. Print the per-page dpi beside each candidate.

**THE CODE DOES NOT DO THIS YET.** `r005_masters_sheet.py` pre-fills from the
edge finder alone (`from_ink = paper_frac < FULLBLEED_PAPER_FRAC`), which is
the one-sided witness described above. Until that changes, compute the
own-white gap and the per-page dpi BY HAND before accepting a pre-fill, and
treat what the program offers as one of three witnesses rather than as the
answer. Flagged rather than silently prescribed, because a rule that describes
behaviour the code does not have reads as a missing step rather than an error.

Pre-fill from the UNION of the own-white gap and the edge-finder set, print
the dpi beside each, and say which witness produced each page. A page named by
only the edge finder is a candidate to check, not an answer. The owner confirms
it against the physical copy at PAUSE 1 regardless.

The step pre-fills `high_pages` with what the edge-finder evidence points at and
says, in the output, that it is a guess to be checked against the copy. **That
pre-fill is the one-sided witness the paragraph above tells you not to trust**,
so read it as one of the three and not as the procedure — this sentence used to
sit here reading like the step's answer.

**MEASURE `colors.txt` BEFORE PAUSE 1, not after.** The own-white gap is the
strongest of the three witnesses, and the figures the step prints come from
`ask_text()`, which needs `PAPER_RGB` / `LOW_GRADE` — i.e. a measured low
profile. A fresh issue has none, so without this the gap is computed against
the built-in `W` and compares the issue's pages to another issue's paper. The
measuring method is in `r005_masters_spread.md`; run it on this issue's own
interior first, then put the three witnesses to the owner together.

### The answer, recorded

```json
"binding": "sheet",
"paper": {
  "high": null,
  "low":  "/Users/mist/DNB/SH8601/master_2400/SH8601/colors.txt",
  "high_pages": [1, 2, 147, 148, 149, 150, 151, 152] }
```

`null` means **the built-in anchor set** (`BUILTIN_ANCHORS`, `W 201 195 188`,
identity levels) — not "missing". A path that does not exist is a **loud
error**, not a fallback: the whole point of the map is that nothing is graded
against numbers nobody chose. Validation lives in `r000_issue.py` and every
failure is a `SystemExit` — unknown key, wrong type, a page number outside
`1..pages`, a duplicate, or a descriptor carrying both `paper` and the legacy
`colors`.

SH8601's answer is above: **1, 2, 147, 148** (the folded A3 cover wrapper) and
**149–152** (the bound-in Zahlkarte) are high quality; the other 144 pages are
the interior stock.

## The two variants, and why the suffix is not an insertion

Step 005 exists in two **mutually exclusive** variants, chosen by the issue
descriptor's `binding` — which is **asked for** as the first action above, never
assumed. The field existed before the question did, and an absent or wrong value
selected the wrong edge maths in silence:

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
  `r000_issue.py` — `scan_dir`, `thumb_150`, `tmp`, `pages`, and the two
  **answers**, `binding` and `paper` (`paper.low` replaces the old whole-issue
  `colors`, which still loads for an issue that has not been migrated)
- one **field file per paper class**, beside that class's `colors.txt` —
  `field_low.txt`, `field_high.txt` — written by `r005_field.py`. A missing one
  is not an error: that class gets no flat-field correction and every stamp
  says so. See *The paper has not browned evenly*
- `tools/img/cmyk_reconstruction/target/release/cmyk_reconstruction`, built
  (`cargo build --release` in `tools/img/cmyk_reconstruction`)
- the ICC pair in `tools/img/`: `USWebCoatedSWOP.icc`, `AdobeRGB1998.icc`
- `magick` (ImageMagick 7)
- Python 3.11+ with `numpy`, `scipy`, `pillow` — use the repo venv
  (`.venv/bin/python`, CLAUDE.md). On this box `/usr/bin/python3`
  has all three

### Not every scan is 2400 dpi

The scan's resolution is READ per page from its PNG pHYs (`scan_dpi()`), and
the reduction to 600 follows from it: 4 at 2400, 1 at 600. SH8602's interior
(003–162) was scanned at 600 dpi and only its wrapper and card at 2400; the raw
TIFFs agree, so there is nothing higher to go back to. A 600 dpi page is
levelled, separated and graded at 600 and has **no `masters2400/NNN.png`**;
its `cmyk2400/NNN.tif` is the separation at 600, and its stamp says
`scan-dpi 600`. Measured on SH8602: the 2400 dpi path is pixel-identical to
the code before the change (p163); the 600 dpi path went from a 53 × 76 mm
trace to 209.2 × 296.9 mm (p050). Derive that issue's thumbs at
`150 / dpi`, i.e. `-scale 25%` for a 600 dpi master, not 6.25 %.

## Run

```bash
cd tools/img/scan2ocr/rules
../../../../.venv/bin/python r005_field.py                    # ONCE, first
../../../../.venv/bin/python r005_masters_sheet.py            # every page
../../../../.venv/bin/python r005_masters_sheet.py 6 41 56 92 # named pages
```

**`r005_field.py` runs first, once per issue**, and measures the
paper-yellowing field for each paper class — about 0.6 s a page on 28 lanes for
a 600 dpi issue, 119 s for SH8605's 192 interior pages. It writes
`field_<class>.txt` beside that class's `colors.txt` and nothing else. Run it
again only if the scans or the paper map change. Skipping it is not an error:
every class then gets an identity field and every stamp says
`field  identity -- not measured`, which is the state the step was in before
this correction existed.

**The repo venv, not `python3`** — CLAUDE.md requires it, and *Inputs* above
used to say "`/usr/bin/python3` has all three", which is a claim about one box.

**There is no per-issue knob in the program.** This said "the only per-issue
knob is `ISSUE = "SH8601"` at the top of the program"; the issue comes from
`ISSUE.txt` or `$ISSUE` through `r000_issue.py` (r000, *BEFORE ANYTHING
ELSE*), and the program reads it from there. A reader of r005 alone would
have edited the source to build their issue. No CLI
flags, no environment knobs beyond `$ISSUE` — every path is derived from the
descriptor. Page
numbers are positional purely so the work can be split across processes, exactly
as in `r010`.

~45 s per page; ~2 h for 152 pages. Deterministic and local — no model is
called.

**After any change to this step, wipe `<tmp>/masters600` and start again from
page 1.** `r010`'s block ids and `r020`'s cache are keyed on the masters, and a
directory mixing two runs is not something any downstream check can see. **A new
field file is such a change** — it has a new `field-sha`, which is exactly how
Verification 7b finds the masters it did not make.

## Outputs

```
issues/<ID>/field_low.txt        the paper-yellowing field, per paper class
issues/<ID>/field_high.txt       ...beside that class's colors.txt  (r005_field.py)
<tmp>/masters600/NNN.png         the OCR master — r010 reads this   (the contract)
<tmp>/masters600/NNN.stamp.txt   which profile and which curve made that master
<tmp>/sheets600/NNN.png          the uncropped graded sheet
(NO figures600/ — see below)
<tmp>/cmyk2400/NNN.tif            the CMYK archival form, deflate-compressed
<tmp>/cmyk2400/NNN.colors.txt     the profile the separator was actually run with
<tmp>/debug600/NNN.png           the overlay: the four traced lines, in green
<tmp>/title_source_150.png       the cover crop for the owner  (see below)
```

## HAND THE OWNER THEIR TWO FILES NOW — and do not stop

Two of PAUSE 2's deliverables are finished the moment this step is, and both
are work the owner does **by hand**. Owner, 2026-10-05: **as soon as either is
available, tell me and `open` it — and do not stop.** See r000, *An OWNER
DELIVERABLE is handed over the MOMENT it exists*.

```bash
# 1. the uncut, deskewed, colour-corrected 600 dpi pages -- for review
open "$TMPDIR_ISSUE/sheets600"

# 2. the 150 dpi cover crop, from which the owner makes issues/<ID>/title.png.
#    sheets600 is the graded sheet BEFORE the cut, so the crop comes off the
#    MASTER, which is the page: a plain /4 reduction of masters600/001.png.
"$PY" - <<'PYEOF'
import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
t = os.environ['TMPDIR_ISSUE']
src = f'{t}/a4600/001.png'          # binding=sheet; spread -> masters600/001.png
im = Image.open(src).convert('RGB')
w, h = im.size
W, H = round(w * .25), round(h * .25)
im.resize((W, H), Image.LANCZOS).save(f'{t}/title_source_150.png')
print(f'title_source_150.png  {W}x{H}  (25% of {src}, {w}x{h})')
PYEOF
open "$TMPDIR_ISSUE/title_source_150.png"
```

**Make the FILE, not a recipe.** SH8602 wrote the source master, the traced
page box, the target size and an export warning into its crop worklist and
produced no file, so the owner had to ask where it was. SH8603 produced
`title_source_150.png`, and that is the name.

**The cover comes from the SAME directory the PDF reads, reduced 25 %.** On a
`sheet` binding that is `a4600` (the A4 cut 005b makes), not `masters600` (the
traced-trim canvas, 5457×7181 on SH8604). `make_issue_pdf.sh` computes the
size it will accept as 25 % of `<A4>/001.png` and exits 1 on anything else.
Both `a4600` and a spread issue's `masters600` are 4961×7016, so the answer
is 1240×1754 today — as a consequence, not a constant. Compute it, and see
r006, *PIXEL SIZE DOES NOT PROVE A COVER WAS RETOUCHED*.

**On a sheet issue this means 005b must have run first**, since `a4600` is its
output. If you reach this hand-over before 005b, hand over `sheets600` now and
the cover crop when 005b finishes.

Then say, in one message: which directory holds the pages and how many, where
the title crop is, and that **nothing is blocked** — the chain is already on
the next step.

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
  -> ONE render off that ONE separation, UNCURVED (the curve was removed; see
     below -- there is no second render and nothing to compare against)
  -> masters600/NNN.png + NNN.stamp.txt, sheets600/NNN.png,
     cmyk2400/NNN.tif + NNN.colors.txt, debug600/NNN.png
```

### The fill: MIRROR the page into the band, do not paint a constant

**This is the older process's rule, ported here because it never was.** The
scan2mrc crop step fills a band that reaches the page border by **reflecting the
page's own pixels into it**, and only paints where reflection is not defensible.
Its two constants are the whole rule:

```
MIRROR_MAX_PX = 1200        # @2400 dpi = 12.7 mm
```

> *Beyond this distance from any known pixel, DO NOT MIRROR — fill with the
> page's own paper. Mirroring assumes the page plausibly continues just past the
> crop, which is true for a matte band. It is false for a large void: p003/p004
> are bound-in reply cards narrower than A4, so ~44% of the page has no sheet
> behind it at all, and reflecting there fabricates a mirrored copy of the card
> — which reads as real content and is worse than the black it replaced.*

And the fallback colour is **measured, not assumed**: the median of the KNOWN
pixels in the lightest quartile, per page, so a cream stock or a colour cast
fills with its own white rather than with 255.

**Both halves matter, and the second one is the one this chain gets wrong
today:** step 005 fills outside the traced page with the profile's `W` and the
A4 window pads with a literal `255`.

**Why SH8601 was NOT re-run to change this, measured rather than argued.** On
the delivered 150 dpi pages the fabricated strip is **0.0–1.4 mm**, and the real
graded paper immediately inside it sits at **p50 255, sd 2.3–4.8** — this
issue's grading already maps its paper to pure white, so a mirrored strip and a
painted strip differ by under three grey levels on a band a millimetre wide, and
the issue's 48 bilevel pages threshold both to the same white. Re-grading,
re-cutting and rebuilding a 152-page PDF for that is not worth it.

**It is worth it where the paper still has tone.** A matte or cream stock, a
band left by a deep cut into the fringe (this issue's deepest real cut is ~8 mm,
well inside the 12.7 mm cap), or any issue delivered without this issue's
aggressive white point will show a flat band against textured paper. Implement
the mirror there, with the cap and the measured-paper fallback, and record which
of the two filled each band.

### THE MASTER KEEPS THE PAPER'S OWN SIZE — A4 IS A DELIVERY CONVENTION

**DECIDED 2026-08 by the issue owner: keep.** `masters600/NNN.png` stays at
whatever the sheet physically measures; exact A4 is imposed later, by step 005b's
window, and only on what ships.

The question was whether to make the master itself exact A4 so every later step
inherits one geometry. It is tempting — it would remove a class of downstream
arithmetic — and it is wrong, for the same reason print typos stay: **the master
is the record of the paper.** SH8601's interior sheets run 209.2-212.1 x
296.0-298.6 mm, the cover leaf is 223 mm wide with its fold flap, and the
Zahlkarte is 144 x 205 mm. "This sheet measures 211.4 mm" is a fact about the
object; A4 is a decision about the delivery. Overwriting the first with the
second discards evidence to save arithmetic.

It would also have cost a re-run of r010, r020 and r030 on an issue already
verified — a real price for a change that improves nothing the reader sees.

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

The **grade** on those eight pages is a page number, and deliberately so: it
comes from the descriptor's `paper.high_pages`, which is the owner's answer and
not a measurement. There is nothing to defer to — the paper mask cannot see that
stock at all, which is the same fact that makes the grade wrong there. The two
are cross-checked every page: a page that takes the ink-vs-bed finder while the
map calls it `low` (or the reverse) gets a `PAPER MAP:` note in its log line and
in its stamp. A **note**, never a refusal — the map is the answer and this step
does not overrule it.

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

### Two papers, two profiles

**One white point cannot serve two stocks.** `W` is the *density reference*:
`d = -log10(rgb/W)`. Grade a good white sheet against a profile measured off
yellowed paper and every light tone is reported as carrying **less ink than it
does** — highlights clamp to zero — and mid-tone hue skews, because each channel
is normalised by a differently wrong number.

SH8601 was graded end to end with one profile, measured off the **interior**
stock: `W 209 175 157` with `LC 5 100 / LM 4 100 / LY 5 100 / LK 3 100`. That
white point is the *yellowed 5th percentile* of the interior paper and was
chosen to stop yellow corners — the right answer for 144 pages and the wrong one
for the other eight. Measured on p151, the white Zahlkarte, under that profile:
**ink kept 0.36, dark contrast 91**, on a master that is excellent by eye. The
step already said so in every log line; what it could not do was fix it, and the
note in the code said the fix was *a second measured profile for that stock — a
decision, not a looser constant here*.

**That decision was taken.** The descriptor names a profile per paper class and
`grade_for(page)` picks it per page:

| class | what it is | profile |
|---|---|---|
| `high` | white stock that was white when new — the folded cover wrapper, a bound-in card or insert | the **built-in anchor set**: `W 201 195 188, C 38 140 165, M 192 37 66, Y 201 159 61, K 16 17 17` and its overprints, with **identity levels** |
| `low` | the cheap interior stock, yellowish-grey from the start and browner now | this issue's **measured** `colors.txt` |

**For a NEW issue, measure it** — the procedure lives in
`r005_masters_spread.md`, *The profile is MEASURED for this issue's paper*
(pool the interior thumbs, take the low percentile per channel) and the result
goes to `issues/<ID>/colors.txt`. This rule used to say only that the file is
"measured" and then point at SH8601's existing one, so a new issue had nowhere
to look; SH8602 had to take the method from the spread rule.

The built-in anchors are the eight the old separation compiled in, copied into
`BUILTIN_ANCHORS` rather than imported (`scan2mrc` is retired and `scan2ocr` must
not reference it). They are not a fallback here — they *are* the high-quality
paper's profile, by the owner's decision: `W 201 195 188` is a white sheet, which
is what a cover wrapper and a card are. The levels stay the identity because
nobody has measured that stock; a level line is a per-ink contrast decision that
must be measured, not guessed. Either class may name a `colors.txt` of its own
once one is measured — `"high": null` is an answer, not a gap.

**The paper mask is a different question with a different answer.** It uses the
**low** class's `W` on every page, including the high-quality ones, because its
job is to find *this issue's own paper* against the bed and to notice the pages
that are not on it — which is exactly what the ink-vs-bed switch reads. A mask
that could see both stocks would see no difference between them and the switch
would have nothing to switch on.

An issue whose descriptor has no `paper` map is not graded at all: see *The
first action*. **That is not the same as a descriptor that is incomplete on
purpose.** r000's PAUSE 1 describes exactly that state — `binding` answered and
`paper` still absent, pending the owner — and `first_action()` handles it by
asking only the unanswered key. So "no `paper` map" here means an issue that
will never have one, not an issue that has not got there yet; do not read it as
a reason to invent one before PAUSE 1. The legacy whole-issue `colors` key still loads, for an issue not
yet migrated, and means what it always meant.

### One separation, two renders

The two consumers want different images, so both come off **one** separation:

| render | for | wants |
|---|---|---|
| `masters600/NNN.png` | `r010` OCR, `r145` figure cuts | the straight ICC render, **uncurved**. It was to carry a black-point curve for the OCR's sake; `undo_gcr()` fixes the problem the curve existed for, at the source, so there is nothing left for it to do — and one render serves both readers |
| ~~`figures600/NNN.png`~~ | — | **DOES NOT EXIST.** The code writes no `figures600` and has no `OUT_FIGURE`; this row described a second, UNCURVED render that was to feed the figure cuts. **It is void because THE CURVE ITSELF WAS REMOVED** (`r005_masters_sheet.py`: "there is no OCR contrast curve, and that is deliberate"; every stamp reads "ONE master, uncurved"). So there is one render and nothing to compare it against. MEASURED on SH8603: `sheets600` and `masters600` give the same glyph p50 (21/24/19/20 on 050/100/120/150) — because NEITHER is curved, not because both are. Reported on SH8602, reported again on SH8603, harvested 2026-10-05, corrected 2026-10-05 after SH8604 caught the inverted reading. |

**And checks 4 and 6 read `masters600`, not `sheets600`.** `sheets600` is the
UNCROPPED sheet and is offset from the master by the stamp's `sheet-box`
(SH8604 p041: offset `40 5`, 5071x7188 against the master's 5457x7181), so
slicing `[:ph, :pw]` off it reads the wrong region. The master is the canvas
every band in these checks is expressed in.

Ink at ~66 is not a bug, it is honesty: 100 % SWOP black is not RGB 0, and
tesseract binarises, so it does not need to be.

### THERE IS NO BLACK-POINT CURVE — the sections that described one are gone

This rule used to carry three of them: *The curve is one issue-wide constant*
with its `-level 30%,100%` arithmetic, the 30 %-chosen-on-the-worst-page table,
and *And the figure render must not have it*. **All three described code that
no longer exists** (`r005_masters_sheet.py`, *there is no OCR contrast curve,
and that is deliberate*): the curve was there to fix contrast that GCR had
flattened, `undo_gcr()` now fixes that at the source, and a curve on the OCR
master would be a curve on the only master `r145` has to cut figures from.
Every stamp reads `render ONE master, uncurved`.

They are deleted rather than left with a note, because a rule that describes a
transfer function nobody applies invites the next build to look for it — and
because this is the third issue to report them (SH8602, SH8603, SH8604). The
numbers are in the commit history if a curve is ever wanted again.

**Verification 6 goes with them.** It compared the curved master against the
uncurved figure render; neither term exists, so it measured nothing and read
as a passing check. If a contrast check is wanted, it is "glyph p50 on
`masters600`", one render, no comparison.

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

That was the state of it while **one** profile graded the whole issue. With the
paper map both sides of the ratio use the same paper on every page, because
every page is graded with its own stock's profile — see *Two papers, two
profiles*. The numbers still **report and never gate**: a gate on ink-keep
failed 10 of 152 pages on the first full sweep and was wrong on all 10 (they
were the issue's most tint-heavy pages, and a screened tint demodulating into a
flat fill is the pipeline working, not ink loss). Both numbers go in every log
line, because the failure they were built for — the old `LK 90 95` turning black
type into blank paper — is loud enough for a human to see in a thumbnail.

### The paper has not browned evenly — the flat-field correction

**The grade has one white point and the paper has many.** `W` is the density
reference, `d = -log10(rgb/W)`, so the same number is the reference at the page
centre and 2 mm from the trim. MEASURED on SH8605, on 190 of its 192 interior
pages, on the **raw** levelled scans: the clean substrate needs these gains to
read as the same paper as that page's own centre —

| distance from the edge | gutter | fore | top | bottom |
|---|---|---|---|---|
| 2 mm | R 1.025 G 1.063 B 1.074 | 1.052 / 1.147 / 1.186 | 1.044 / 1.169 / 1.226 | 1.036 / 1.229 / 1.340 |
| 12 mm | 1.004 / 1.024 / 1.037 | 1.005 / 1.030 / 1.043 | 1.011 / 1.059 / 1.081 | 1.019 / 1.111 / 1.152 |
| 50 mm | 1.004 / 1.010 / 1.012 | 1.005 / 1.005 / 1.005 | 1.002 / 1.003 / 1.004 | 1.000 / 1.005 / 1.008 |

*(SH8605's `low` class, 190 pages, `field_low.txt`.)*

A third of a stop of blue at the foot of the sheet, nothing at the centre, and
`R` almost flat. Three channels moving by different amounts is the signature of
**yellowing** — a scanner vignette is grey and moves all three together.

So the page is flattened **before** the separation, and the grade then works on
a page whose paper is one colour everywhere, which is what it has always
assumed. `r005_field.py` measures the field; this step reads it and applies it.
`r005_field.py`'s own docstring is the method and carries the measurements
behind each of its five decisions; the short version is:

1. **Measured on the raw scans, never on the graded page.** The grade clips
   66–84 % of each page to pure 255; the signal is not attenuated there, it is
   gone.
2. **Anchored on each page's own traced box.** The registered A4 window is
   placed on the 64'er wordmark, and the paper's own edge wanders over an
   **11.0 mm** range inside it — wider than the whole steep part of the field.
   This was the single biggest error in the first pass.
3. **The ink is regressed out as a covariate, not filtered out.** Within one
   page, "distance from the trim" and "inside the text block" are nearly the
   same variable, and the ink really does darken the paper around it: holding
   the block position exactly constant and comparing the pages where that block
   carries ink against the pages where it is clean, the paper level falls
   −0.70 DN at 7–12 % coverage, −2.02 at 12–20 %, −3.56 at 20–30 %, −14.12 above
   45 %. **No percentile removes it** (−3.85 at p85, −3.77 at p95, −3.78 at p98,
   −3.65 taken inside the ink-free population only): the first pass blamed the
   selector and was wrong. So `log paper = c + page + v_row + h_col + b(ink)`
   with `b` non-parametric, and the field is read at `b(ink = 0)` — clean
   substrate.
4. **Separable and monotone**: `log gain = gx(x) + gy(y)`, four half-profiles
   (gutter, fore, top, bottom), each non-decreasing outward from the page centre
   and exactly 0 there. Monotone because browning is a diffusion front from an
   edge and cannot contain a bright ring; a free fit grows one out of the ink
   collinearity above. The constraint costs: whole-page mean |residual| rises
   from 0.60/0.50/0.48 DN (free additive fit) to 2.07/1.18/0.93 (monotone), paid
   in the corners where the separable product over-predicts the browning by
   2–4 DN. Worth paying rather than inventing a ring.
5. **Mirrored by parity** at application time — an odd page is a recto (fore
   edge right), an even page a verso.

#### It is not a multiply

A multiply scales the ink with the paper, and **dense ink does not brown with
the substrate**: measured, the solid-black floor is flat with position, while
the paper around it is 33 % darker in blue at the foot of the page. A plain
multiply lifts that floor by up to 0.65 DN — small, but it is the one number on
the page known to be position-independent, so moving it is a measurable
fabrication. What is applied instead holds **both** ends fixed:

```
p_local = Pc / g
v'      = Pc - (Pc - K) * (p_local - v) / (p_local - K)
```

`p_local` → `Pc` (the browned paper here reads as the centre's paper), `K` → `K`
(the ink floor does not move), linear in between, with a soft knee above 235 so
that a highlight gradient rolls into 255 instead of clipping flat on it.

`Pc` and `K` are **measured on the page**, not taken from the class — over the
seven validated pages the centre paper runs R 184.0–211.2 and the ink floor
R 24.1–32.5 — and both are written into the page's stamp, because the field
file alone does not reproduce the pixels. A page that cannot measure one of its
own (a full-bleed colour page has no paper at its centre) falls back on the
class median, which is in the field file for exactly that reason, and **says so
in its note**.

#### The amplitude is 1.0, and that is a measurement

| alpha | paper \|R−B\| gap to the page's own centre |
|---|---|
| none | 16.42 DN |
| **1.00** | **3.31 DN** |
| 1.25 | 4.25 |
| 1.50 | 7.97 |
| 2.00 | 17.64 — *worse than no correction at all* |

Over-correcting does not trade neutrality for punch; past 1.0 the fitted field
keeps rising where the paper has stopped browning. 1.0 is the owner's decision
(2026-10-08) and the measured optimum, and it is a named constant,
`FIELD_ALPHA`, so the number is in the source rather than implied by its
absence.

#### One field per paper class — and a class that cannot have one

The field is a property of a **stock**, so it is measured and applied **per
paper class**, through the same `grade_for(page)` lookup that picks the anchors.
`field_low.txt` sits beside `colors.txt`; a class with no profile of its own
(`"high": null`) has its field beside the issue descriptor.

A class that cannot support a fit gets an **identity** field — gain 1.0
everywhere — and it is **written down** rather than skipped, because "no file"
and "a stock that cannot be fitted" are different facts and a master has to be
able to say which of them made it. Two explicit tests, both of which fire on
SH8605's `high` class:

| test | constant | SH8605 `high` |
|---|---|---|
| enough pages | `FIELD_MIN_PAGES` = 24 | **8 pages** |
| one piece of paper | `FIELD_SIZE_SPREAD_MM` = 10 | **88.8 mm** of interdecile spread — the wrapper traces 210–214 × 296–298 mm, the Zahlkarte 150 × 208 |

The page floor is **measured, not chosen.** SH8605's own field was refitted on
random subsets of *n* pages, six draws each, and the gain 2 mm from each edge
compared against the full fit — `|dgain|` over the twelve (side, channel) pairs:

| n pages | 6 | 12 | 18 | **24** | 32 | 48 | 96 |
|---|---|---|---|---|---|---|---|
| mean worst pair | .0291 | .0191 | .0109 | **.0085** | .0113 | .0086 | .0042 |
| max worst pair | .0475 | .0344 | .0191 | **.0116** | .0245 | .0120 | .0065 |

0.01 of gain is about 2 DN of paper — the point below which the correction is
better than nothing at *every* edge and not only on average — and 24 is where
both rows first sit under it. At 12 the worst edge is out by 0.034, a tenth of
the whole bottom-edge correction applied in the wrong direction. Between 18 and
48 the curve is flat, so the floor is not sensitive to where in that range it is
put. It is a statement about the **ink covariate** and not about pixel counts:
one page already gives ~3000 blocks, but `b(ink)` is identified only by pages
putting their ink in different places, and that is what runs out first.

The size test is the **interdecile** spread and not min–max, and is made on the
150 dpi thumbs with the production tracer, because the question is whether the
class has two modes and not whether one page's trace failed: SH8605's `low`
class contains p035, whose trace locks onto the interior of a dark-ground ad and
reads 173.6 × 254.6 mm, and min–max would therefore be 45 mm and the whole
interior would lose its correction over one bad page.

#### The guard on a bad traced box

`field_box_ok()` is **one** test, read by both halves: `FIELD_PAGE_MM` =
205–212 × 293–301 mm, tighter than `PAGE_CLASSES` on purpose, because the size
gate's ±6 mm asks *"would the fill eat type"* and a few mm of fabricated margin
is survivable, while the field asks *"where is the edge"* and the fitted gain
moves 13 % of its range over 4 mm there.

**And the honest size of what it buys, measured rather than asserted.**
Refitting SH8605's field with p193's bad box included moves the fitted gain
2 mm from the edges by at most **0.00016** — one bad box in 190 pages cannot
bend a median-polished fit, and this rule's first draft claimed it could. The
gate earns its place on the other side: the **application** is not an average
over pages, so a page whose box is not its page has its *whole* gain field
placed where the page is not, and nothing downstream can see it. On a class at
the 24-page floor one bad box is also 4 % of the fit, which is no longer
nothing.

`r005_field.py` **rejects such a page by name** and counts it in the field
file's own provenance; `r005_masters_sheet.py` leaves such a page uncorrected
and stamps it `field-sha` = the identity digest, so that the stamp is never a
claim about pixels the field did not touch. Measured on SH8605, exactly two
pages:

```
REJECT p035: the trace matched no page class, so there is no traced page to anchor a field on
REJECT p193: traced page 204.2 x 297.1 mm is outside the 205-212 x 293-301 mm a field can be anchored on
```

#### The switch, and the default

`FIELD_CORRECTION = True` in `r005_masters_sheet.py` — **on** is the default and
the owner's decision. `False` applies nothing on any class and says so in every
stamp (`field  identity -- switched off at FIELD_CORRECTION`). A module constant
and not a CLI flag, for the same reason nothing else here is one; it exists
because this correction is the one thing in this step that invents a tone the
scanner did not record, so it has to be possible to make the page without it
and compare.

A class with no field file at all is **not** a refusal, and that is deliberate
and consistent: a missing `colors.txt` is not a refusal either. The run prints
one line per class saying so and every stamp of every page of that class reads
`field  identity -- not measured -- <path>`. This step refuses over exactly two
things — see *The first action* — and "nobody has measured this stock's field
yet" is not one of them.

## The stamp — every artefact says which grade made it

A finished master used to carry no record of the numbers that produced it, and
this issue paid for that: `colors.txt` was re-measured, the four masters
standing in `masters600/` were now stale, and it took a **human eye noticing
yellow corners** to find out. Nothing mechanical could have.

So everything this step writes carries the grade's fingerprint — the 8 anchors,
the 4 level lines, and a 12-hex `grade-sha` over exactly those — plus
**`paper-class`**, the name of the class whose profile made this page, plus what
was decided about the page's geometry.

**And `field-sha` beside it, carried exactly the same way.** Two things decide a
pixel now: the profile, and the paper-yellowing field. A master that names one
of them cannot say what produced it. The digest is over the field's numbers
alone, as `grade-sha` is over the profile's alone; the `field` line says which
file they came from, whether it is fitted or identity, and at what alpha, and
`field-anchors` gives the page's own two ends of the affine map, which are
measured per page and are therefore not in the field file:

```
grade-sha    f02fda38752c
field-sha    59bbbe19fc02
field        .../issues/SH8605/field_low.txt (fitted, step 0.5 mm, alpha 1.00)
field-anchors Pc 211.2/190.8/179.3  K 24.8/22.3/21.5  (Pc own centre, K own floor)
```

A page the field could **not** be anchored on carries the *identity* digest and
`field  identity -- NOT APPLIED -- <why>`, never the fitted one: the stamp must
not be a claim about pixels the field did not touch.

The class is deliberately **not** in the digest. `grade-sha` answers *"were
these pixels made with these numbers?"*, which is a string comparison;
`paper-class` answers *"why those numbers?"*. A mixed-stock issue has **two
current grades**, and "is this master stale?" is only answerable once you know
which of them was supposed to make it — so both lines sit in the head of every
stamp:

```
grade-sha    cec3ff863b36
paper-class  high
profile      (none -- the built-in anchors, identity levels)
```


| where | how |
|---|---|
| `masters600/NNN.png` | a PNG `tEXt` chunk keyed `r005` |
| `masters600/NNN.stamp.txt` | the same text, readable without opening a 110 megapixel PNG |
| `sheets600/NNN.png` | PNG `Comment` |
| `cmyk2400/NNN.tif` | TIFF `ImageDescription` |
| `cmyk2400/NNN.colors.txt` | the profile file the separator was **actually run with**, kept rather than deleted with the scratch directory |
| `field_<class>.txt` | the field's own numbers, beside the class's `colors.txt`, with its provenance in `#` comments — which pages were fitted, which were rejected and why |
| the run's log | the whole block once at the top, and `grade <sha>` on every page line (it used to read `grade <sha> level 30%`, from the curve that is gone) |

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
row to row. So parity decides, and a **confident** disagreement
(`ratio >= TORN_CONFIDENT_RATIO`) is **NOTED on the page, not failed**.
Ambiguity passes silently.

**This rule used to say it "fails the page". The code has never done that** —
`r005_masters_sheet.py:1082` appends to `notes` and publishes — and the code is
right. Making it fail would have stopped SH8604 on **93 of its 160 interior
pages**, none of them misfiled: see *THESE NUMBERS ARE FROM 2400 dpi FRAMES*
below. The overlay and the size gate are the checks that can say what is
actually wrong with a page; this one can only say that something is worth a
look. Where a rule and its code tell two stories the build follows the code,
so the story that costs a reader time is the rule's.

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

### SH8604 READS THE OPPOSITE SIDE FROM SH8601 — AN OPEN QUESTION, NOT A BUG

**This paragraph used to blame the 600 dpi frame, and the numbers do not
support that.** It said the tighter frame cuts through the torn fringe at
x = 0, so the torn side shows no jitter and the clean edge wins. Two things
were then tried in `torn_side()` on that theory and **both are reverted**;
what follows is why, so that nobody re-derives them.

The gate fired on **93 of SH8604's 160** interior pages — 75 odd reading
"right", 18 even reading "left", ratios 2.6-8.5 — against **0 of SH8601's
150**. Frame-to-paper margins, median / p95 in mm:

| issue | pages | left p50 / p95 | right p50 / p95 |
|---|---|---|---|
| SH8601 | 150 | 0.34 / 1.02 | 4.23 / 7.45 |
| SH8602 | 165 | 0.00 / 0.17 | 4.06 / 5.42 |
| SH8603 | 181 | 0.17 / 0.34 | 5.59 / 7.11 |
| SH8604 | 165 | 0.17 / 0.64 | 5.25 / 7.25 |

**Every issue is near-flush on the left, SH8601 included** — and SH8601's gate
agrees with parity on 149 of 150. So the margin is not the variable, and
suppressing the gate on a flush frame would silence a working check on three
issues to quieten one.

The jitter is the variable, and it points the other way. Even pages, where
parity expects *right*:

| issue | left jitter p50 | right jitter p50 | reads | parity |
|---|---|---|---|---|
| SH8601 | 0.06 px | 0.29 px | right — torn | agrees |
| SH8604 | **0.35 px** | 0.20 px | **left** — torn | disagrees |

SH8604's left edge is not a clipped edge with no jitter. It is **six times
jitterier than SH8601's** and it is the torn one. So SH8604's sheets really do
present the opposite side, consistently across the issue, and the gate is
reporting something true.

**IT IS NOT AN OWNER QUESTION — THE PAGE ANSWERS IT. READ THE FOLIO.**
(Owner, 2026-10-06, when it was put to them: *"i dont have an answer for you,
there is no way for me to know this."* Quite right: nobody can tell from a
copy in the hand which way a scanner saw it. The print can.)

A 64'er page foots with the **folio at the OUTER edge** — so a recto carries it
bottom-right and a verso bottom-left — and the **`64'er` logo in the opposite
corner**, with `SONDERHEFT N/YY` centred between them. That is a fact about the
typesetting, independent of the scan, so it tells you directly whether a page
is the parity its number claims. Cut the bottom ~4 % of the A4 page full width
and look at it:

```bash
$PY - <<'PY'
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
for pg in (40, 41):                      # one even, one odd
    im = Image.open(f"<A4>/{pg:03d}.png").convert("L")
    w, h = im.size
    im.crop((0, int(h * .955), w, h)).reduce(3).save(f"/tmp/foot_{pg}.png")
PY
```

MEASURED on SH8604: p040 foots `40` left / `64'er` right, p041 foots `64'er`
left / `41` right. Swept over the whole issue by OCR'ing the four outer
corners and keeping only pages where exactly one corner reads the page's own
number — **odd: 57 right, 0 left; even: 64 left, 1 right**, 28 of 150 not
readable. **121 of 122 put the folio at the outer edge, so the scans are
correctly oriented and nothing is misfiled or rotated.** Which means the gate's
own sentence is the thing that is wrong here: what it measures is which
physical edge is rougher, and that is a property of how THIS issue's sheets
were separated — SH8601's rough edge is the gutter side, SH8604's is the fore
edge. Neither is evidence about filing.

**So, when the gate fires on a run of pages: check the folio once, on one odd
and one even page.** If the folio is at the outer edge, record "orientation
confirmed from the folio, torn side is the fore edge on this issue" in
`LOG.md` and carry on — the disagreement is a NOTE and nothing more. If the
folio is at the INNER edge, you really do have mirrored or rotated scans, and
THAT goes to the owner.

Do not re-tune `TORN_CONFIDENT_RATIO` to make the count go down — the ratios
are 2.6-8.5, i.e. the measurement is confident, not marginal — and do not
suppress the gate; it is cheap and one day it will catch a real misfile.

**Do not use a corner ink-fraction as a shortcut for the folio.** It reads
BACKWARDS: the `64'er` logo is a dense black blob and the folio is a few thin
digits, so the corner with more ink is the LOGO's. Measured over SH8604's 150
interior pages, median foot-corner ink: odd pages left 0.0381 / right 0.0173,
even pages left 0.0182 / right 0.0379 — consistent across the issue, and
exactly inverted from where the numbers are. Look at the strip.

The SH8601 numbers above remain correct for SH8601.

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
               (R.OUT_SHEET600, ".png"), (R.OUT_CMYK, ".tif"),
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
#      - it reads MASTERS600.  This said "it reads sheets600 (there is no
#        uncurved render)" and gave the reason as the curve: BED_LUM was
#        measured on unclipped pixels, and on a curved master a printed RED
#        banner (lum 101) would land at 35 and read as bed.  THERE IS NO CURVE
#        ANY MORE -- the code removed it and every stamp reads "ONE master,
#        uncurved" -- so the reason is void, and sheets600 is the wrong file
#        for a different reason: it is the UNCUT sheet, offset from the page by
#        the sheet box, so a band measured inside the traced page lands
#        somewhere else.  See "checks 4 and 6 read masters600, not sheets600".
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
    rgb = np.array(Image.open(R.OUT_MASTER / f).convert("RGB"))[:ph, :pw]
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
    # PER PAGE, not per issue: a mixed-stock issue has one current grade per
    # paper class, and the page's class decides which one this master owes.
    want = R.grade_for(int(f[:3]))
    print(f, sha, want.klass,
          "CURRENT" if sha == want.sha else "*** STALE -- re-run this page ***",
          "| chunk == sidecar" if chunk == side else "| *** CHUNK DISAGREES ***",
          "|", re.search(r"^edge-finder\s+(.*)$", side, re.M).group(1))
PY

# 6. CONTRAST, on the one render there is.  This check used to compare the
#    curved OCR master against the uncurved FIGURE render -- and BOTH of its
#    Image.open() calls already read OUT_MASTER, so it compared a file to
#    itself and the two columns were identical by construction.  Neither term
#    exists now (there is no curve and no figures600), so there is nothing to
#    compare: what is left worth measuring is whether the type is dark enough
#    and the paper floor untouched, ABSOLUTELY, on masters600.
#
#    Pick the windows on THIS issue -- they are mm from the traced page's
#    top-left corner and they must land on body text.  "glyph" is the INTERIOR
#    of the strokes (eroded), which is what an OCR threshold sees.
$PY - <<'PY'
import numpy as np, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
from PIL import Image
from scipy import ndimage as ND
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
WINDOWS = {"041": (16, 60, 60, 140)}      # <- this issue's body-text windows
for stem, mm in sorted(WINDOWS.items()):
    box = tuple(int(v * R.MM) for v in mm)
    a = np.array(Image.open(R.OUT_MASTER / f"{stem}.png").crop(box)
                 .convert("L"), float)
    glyph = ND.binary_erosion(a < 128, np.ones((3, 3)))
    paper = a > 200
    if not glyph.any():
        print(f"p{stem}: NO GLYPHS in {mm} mm -- wrong window"); continue
    print(f"p{stem} window {mm} mm | ink {glyph.mean():5.1%} | "
          f"glyph p50 {np.median(a[glyph]):5.1f} | "
          f"paper p50 {np.median(a[paper]):5.1f}")
    # The gate: tesseract binarises, so ~66 for 100 % SWOP black is fine;
    # what must not happen is the PAPER moving off its floor.
    if np.median(a[paper]) < 250:
        print(f"  FAIL p{stem}: paper p50 {np.median(a[paper]):.0f} < 250 -- "
              f"something is eating the paper")
PY

# 7. THE PAPER-YELLOWING FIELD.  Five checks, and each of them has been seen to
#    FAIL against a deliberately planted fault before it was trusted -- the
#    faults and what they printed are recorded under "What check 7 read" below.
#
# 7a. EVERY PAPER CLASS HAS A FIELD FILE, IT PARSES, AND IT ROUND-TRIPS.
#     FlatField re-emits the body through field_text() instead of digesting the
#     bytes it read, so this also catches a file this reader cannot reproduce
#     exactly -- which is the only way `field-sha` can lie.
python3 - <<'PY'
import r005_masters_sheet as R
for klass, f in sorted(R.FIELDS.items(), key=lambda kv: str(kv[0])):
    p = R.field_path(R.GRADES[klass])
    print(f"{str(klass):6s} {p}")
    print(f"       exists {p.exists()} | mode {f.mode} | field-sha {f.sha}")
    print(f"       {f.summary}")
    assert p.exists(), (f"no field file for paper class {klass!r} -- "
                        f"run r005_field.py")
    if f.mode == "fitted":
        body = "version 1" + p.read_text().split("version 1", 1)[1]
        assert body == f.text, "the field file does not re-emit identically"
        print(f"       half-page {f.half[0]:.2f} x {f.half[1]:.2f} mm, step "
              f"{f.step:g} mm, {len(f.gain['R']['bottom'])} samples/profile, "
              f"round-trips")
PY

# 7b. THE STAMP: every master names the FIELD that made it, and it is the
#     current one for that page's paper class -- or the IDENTITY digest, which
#     is what a page whose traced box the field could not be anchored on must
#     carry.  A string comparison, like check 5, and for the same reason.
python3 - <<'PY'
import hashlib, os, re
import r005_masters_sheet as R
ident = hashlib.sha1(R.field_text("identity").encode()).hexdigest()[:12]
bad = []
for f in sorted(os.listdir(R.OUT_MASTER)):
    if not f.endswith(".stamp.txt"):
        continue
    s = (R.OUT_MASTER / f).read_text()
    page = int(f[:3])
    sha = re.search(r"^field-sha\s+(\S+)$", s, re.M).group(1)
    w, h = (float(v) for v in
            re.search(r"^page-size\s+([\d.]+) x ([\d.]+) mm$", s, re.M).groups())
    anchored = R.field_box_ok(w, h)
    want = R.field_for(page).sha if anchored else ident
    ok = sha == want
    bad += [] if ok else [f]
    print(f"{f[:3]} {sha} {'anchored    ' if anchored else 'NOT ANCHORED'}",
          "CURRENT" if ok else f"*** WRONG or STALE (want {want}) ***",
          "|", re.search(r"^field\s+(.*)$", s, re.M).group(1))
assert not bad, f"{len(bad)} master(s) do not name the current field: {bad}"
PY

# 7c. CENTRE GAIN IS EXACTLY 1.0, per channel and either parity.  The whole
#     correction is defined relative to the page's own centre -- Pc is measured
#     there -- so a centre gain other than 1.0 is a global tone shift wearing a
#     flat field's clothes, and nothing downstream could see it.
python3 - <<'PY'
import numpy as np
import r005_masters_sheet as R
for klass, f in sorted(R.FIELDS.items(), key=lambda kv: str(kv[0])):
    if f.mode != "fitted":
        print(f"{str(klass):6s} identity -- gain is 1.0 everywhere")
        continue
    for recto in (True, False):
        g = f.gain_at([0.0], [0.0], recto)[0, 0]
        print(f"{str(klass):6s} {'recto' if recto else 'verso'} centre gain "
              f"R {g[0]:.6f} G {g[1]:.6f} B {g[2]:.6f}")
        assert np.allclose(g, 1.0, atol=1e-6), "centre gain is not 1.0"
PY

# 7d. ALL FOUR HALF-PROFILES ARE MONOTONE outward from the page centre, and
#     start at exactly 1.0.  Monotonicity is the constraint that keeps the ink
#     collinearity (see the rule) from putting a bright RING into the field,
#     and it is imposed by a cumulative maximum inside the fit -- so if it ever
#     stops holding, something between the fit and the file has reordered or
#     re-rounded the samples.
python3 - <<'PY'
import numpy as np
import r005_masters_sheet as R
for klass, f in sorted(R.FIELDS.items(), key=lambda kv: str(kv[0])):
    if f.mode != "fitted":
        print(f"{str(klass):6s} identity -- no profiles")
        continue
    for cn in "RGB":
        for side in R.FIELD_SIDES:
            g = f.gain[cn][side]
            d = np.diff(g)
            print(f"{str(klass):6s} {cn} {side:7s} centre {g[0]:.5f} -> edge "
                  f"{g[-1]:.5f}   worst step {d.min():+.5f}")
            assert g[0] == 1.0, f"{cn} {side} does not start at 1.0"
            assert d.min() >= 0.0, f"{cn} {side} is not monotone outward"
PY

# 7e. PAPER NEUTRALITY AT THE EDGES, MEASURED ON THE PUBLISHED MASTER.  This is
#     the check that the correction did what it is for: the ink-free paper in a
#     band 2/6/12/25 mm inside each traced edge must read as the same colour as
#     the page's own centre.  Bands are taken 20 mm clear of the corners, and a
#     band whose "paper" does not come out at 230 or above is full-bleed art and
#     is skipped -- otherwise a photograph running to the trim is measured as
#     yellowed paper.
#
#     MEASURED on SH8605's 099 120 114 162 008, built both ways: mean
#     |d(R-B)| to the page centre 6.12 DN with the field off and 0.58 with it
#     on, worst band 28.83 -> 2.87.  The ceilings below are ~3x the measured
#     value and under a third of the uncorrected one, so they sit in the middle
#     of a gap an order of magnitude wide.
python3 - <<'PY'
import re, sys
import numpy as np
from PIL import Image
import r005_masters_sheet as R
Image.MAX_IMAGE_PIXELS = None
PAGES = ["099", "120", "114", "162", "008"]   # <- this issue's sampled pages
BANDS, GUTTER_MM, HALF_MM, PAPER_MIN = (2, 6, 12, 25), 20.0, 1.5, 230.0
MEAN_MAX, WORST_MAX = 2.0, 6.0

def paper(rgb):
    C = rgb.reshape(-1, 3).astype(np.float64)
    L = C @ R.FIELD_LUM
    sel = C[L >= np.percentile(L, 85)]
    if len(sel) < 500:
        return None
    m = sel.mean(0)
    return m if m @ R.FIELD_LUM >= PAPER_MIN else None

gaps = []
for stem in PAGES:
    s = (R.OUT_MASTER / f"{stem}.stamp.txt").read_text()
    pw, ph = (int(v) for v in
              re.search(r"^page-px\s+(\d+) (\d+)$", s, re.M).groups())
    a = np.array(Image.open(R.OUT_MASTER / f"{stem}.png").convert("RGB"))[:ph, :pw]
    g, hw, c = int(GUTTER_MM * R.MM), int(HALF_MM * R.MM), int(18 * R.MM)
    ctr = paper(a[ph // 2 - c:ph // 2 + c, pw // 2 - c:pw // 2 + c])
    if ctr is None:
        print(f"p{stem}: no paper at the page centre -- skipped"); continue
    for name in ("bottom", "top", "gutter", "fore"):
        for d in BANDS:
            lo, hi = int(d * R.MM) - hw, int(d * R.MM) + hw
            sl = {"top": (slice(lo, hi), slice(g, pw - g)),
                  "bottom": (slice(ph - hi, ph - lo), slice(g, pw - g)),
                  "gutter": (slice(g, ph - g), slice(lo, hi)),
                  "fore": (slice(g, ph - g), slice(pw - hi, pw - lo))}[name]
            v = paper(a[sl])
            if v is None:
                continue
            gaps.append((stem, name, d,
                         (v[0] - v[2]) - (ctr[0] - ctr[2]),
                         (v @ R.FIELD_LUM) - (ctr @ R.FIELD_LUM)))
for name in ("bottom", "top", "gutter", "fore"):
    for d in BANDS:
        v = [x for x in gaps if x[1] == name and x[2] == d]
        if v:
            print(f"  {name:7s} {d:3d} mm   |d(R-B)| "
                  f"{np.mean([abs(x[3]) for x in v]):6.2f}   dL "
                  f"{np.mean([x[4] for x in v]):+7.2f}   n={len(v)}")
mean = np.mean([abs(x[3]) for x in gaps])
worst = max(gaps, key=lambda x: abs(x[3]))
print(f"  ALL BANDS: mean |d(R-B)| {mean:.2f} DN (max {MEAN_MAX}), "
      f"worst band p{worst[0]} {worst[1]} {worst[2]} mm "
      f"{abs(worst[3]):.2f} DN (max {WORST_MAX})")
assert mean <= MEAN_MAX, (f"the paper at the page edges is {mean:.2f} DN off "
                          f"the page's own centre -- the field is not working")
assert abs(worst[3]) <= WORST_MAX, f"band {worst[:3]} is {abs(worst[3]):.2f} DN off"
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
`colors.txt` of the day plus `OCRLEVEL 30 100`; the PNG chunk equals the
sidecar on all twelve. (The `OCRLEVEL` term is gone from the fingerprint with
the curve, so a master built today has a different sha for the same
`colors.txt` — which is correct: the fingerprint answers "were these pixels
made with these numbers".)

**6.** — **HISTORICAL. This row recorded the black-point curve, which no
longer exists**, and the figures below cannot be reproduced by the check as it
now stands (nor, as it turns out, by the check as it stood: both of its
`Image.open()` calls read `OUT_MASTER`, so the two columns were the same file).
Kept as the record of what the curve did when there was one:

| page | ink in window | glyph p50 figure → master | paper p50 figure → master |
|---|---|---|---|
| 006 | 5.1 % | 87 → **15** | 255 → 255 |
| 041 | 5.1 % | 95 → **26** | 255 → 255 |
| 056 | 10.3 % | 79 → **3** | 255 → 255 |
| 092 | 4.0 % | 87 → **15** | 255 → 255 |

**p117 fails, and nothing was published for it** — see below.

### What check 7 read, and the fault each check was seen to catch

**A check that has never been seen to fail is not a check.** Every one of 7a–7e
was run twice: once against a real build, and once against a deliberately
planted fault. Measured on SH8605 — `field_low.txt` fitted on 190 pages,
`field_high.txt` identity, and masters built for 099, 120, 114, 162, 008 and
193 both with the field and with `FIELD_CORRECTION = False`.

| check | on the real build | planted fault | what it printed |
|---|---|---|---|
| **7a** exists / parses / round-trips | `low` fitted `59bbbe19fc02`, 298 samples per profile, round-trips; `high` identity `038549436824` | `field_low.txt` removed | `AssertionError: no field file for paper class 'low' -- run r005_field.py` |
| | | `gain G top` renamed to `gain G middle` | `r005: …/field_low.txt: bad gain line gain G middle` |
| | | one sample respelled `1.00000` → `1.0` (same number) | `AssertionError: the field file does not re-emit identically` |
| **7b** the stamp names the current field | all six masters CURRENT; 193 `NOT ANCHORED`, carrying the identity digest | one digit of p120's `field-sha` changed | `120 59bbbe19fc03 … *** WRONG or STALE (want 59bbbe19fc02) ***` then `AssertionError: 1 master(s) do not name the current field: ['120.stamp.txt']` |
| **7c** centre gain is 1.0 | `1.000000 / 1.000000 / 1.000000`, both parities | the whole `gain B fore` profile × 1.003 | `AssertionError: centre gain is not 1.0` |
| **7d** four monotone profiles | worst step `+0.00000` on all twelve | one mid-profile sample of `gain B bottom` pushed down by 0.004 | `B bottom  centre 1.00000 -> edge 1.35234  worst step -0.00400` then `AssertionError: B bottom is not monotone outward` |
| **7e** paper neutrality at the edges | mean \|d(R−B)\| **0.58 DN**, worst band 2.87 | the same five pages built with `FIELD_CORRECTION = False` | `ALL BANDS: mean |d(R-B)| 6.12 DN (max 2.0), worst band p099 bottom 2 mm 28.83 DN` then `AssertionError: the paper at the page edges is 6.12 DN off the page's own centre -- the field is not working` |

A centre gain other than 1.0 is necessarily a profile that does not start at
1.0, so 7c's fault trips 7d as well; the reverse is not true, which is what the
7d fault shows.

**7e, band by band, on the published master** — five pages, mean over them:

| band | OFF \|d(R−B)\| | ON \|d(R−B)\| | OFF dL | ON dL |
|---|---|---|---|---|
| bottom 2 mm | 22.93 | 0.57 | −9.70 | +3.34 |
| bottom 6 mm | 20.75 | 0.57 | −8.32 | +3.34 |
| bottom 12 mm | 8.52 | 0.57 | +1.06 | +3.34 |
| top 2 mm | 16.59 | 0.57 | −5.79 | +3.34 |
| top 6 mm | 9.54 | 0.57 | −0.39 | +3.34 |
| gutter 2 mm | 5.95 | 0.57 | +1.79 | +3.34 |
| fore 2 mm | 4.50 | 0.57 | +1.86 | +3.34 |
| **all 16 bands** | **6.12** | **0.58** | +0.63 | +3.38 |

0.57 is the floor of the measurement, not a residual: on the graded master the
paper is at 255 and `R − B` of a clipped white is 0, so a band that reads 0.57
is a band that has become paper white like the centre. That is also why the
**raw** figures in *The amplitude is 1.0* (16.42 → 3.31 DN) are the ones to
quote for the method and these are the ones to quote for the artefact.

**And the bad-box guard, planted the other way round.** With `FIELD_PAGE_MM`
widened to 160–220 × 250–310 mm, p193 is accepted into the fit and
`field_box_ok(204.2, 297.1)` returns `True`, i.e. the application would correct
it too. p035 is *still* rejected, by the independent `uncropped sheet` test —
two guards, and only one of them is a millimetre range.

### The switch, proved against the masters that were already there

A one-off measurement, recorded because it cannot be re-run once this change is
the only code there is. SH8605's `masters600/` was built by the code *before*
this correction existed. Rebuilding 099, 120, 114, 162, 008, 193, 001 and 197
with `FIELD_CORRECTION = False`:

| page | field off | field on |
|---|---|---|
| 099 120 114 162 008 | **bit-identical** to the published master | 22–41 % of pixels move, max \|d\| 85–107 |
| 193 (box not anchorable) | bit-identical | **bit-identical** — the guard really does leave it alone |
| 001 197 (`high`, identity field) | bit-identical | **bit-identical** |

So the switch is a true switch: off, this step produces the same masters it
produced before `level_and_trace()`, `Traced.locate()`, `FlatField` and the
extra stamp lines existed. That is the check that the refactor moved code and
nothing else — including on the `ink/bed` pages, which the sampled low-class
pages never exercise.


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
- **The flat-field correction is in this variant only.** `r005_masters_spread`
  shares nothing with this file — it imports its constants and its grade from
  `r005_masters.py` — so a *spread*-bound issue gets no field, and its stamps
  carry no `field-sha`. Measuring a field for a clipped spread is a different
  geometry problem (two pages per frame, one of them with the facing page's
  gutter) and nobody has measured it.
- Levelling, masking and tracing now live in `level_and_trace()` /
  `Traced.locate()` rather than inline in `process()`, because `r005_field.py`
  needs **the same** four traced lines the master will be cut on — the field is
  anchored on that box. Two spellings of "where is the paper" would drift page
  by page and the drift would be invisible.
