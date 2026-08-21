# 145 — Cut the article figures out of the masters

**Applies to:** all — cutting figures out of the masters is kind-independent.

**Goal:** every photograph, screenshot, hardcopy, diagram, chart, cartoon and
rubric badge belonging to an article, cut from the graded 600 dpi master as its
own PNG, named the way step 150 expects and sorted into the four buckets
`tools/convert-scans.sh` converts.

This is a **program step**, but only half of it is a program. See *The split*.

## Inputs

- step 010's blocks (`<OUT_DIR>/NNN.json`) — every text rectangle on the page
- step 020's labels (`<OUT_DIR>/NNN.labels.json`) — what each block is, which is
  how advertising is kept out
- step 030's `articles.json` — which article a page belongs to, for the name
- the graded 600 dpi masters (`SRC_DIR`) — what is actually cropped

## Run

```bash
tools/img/scan2ocr/rules/r145_extract_figures.sh          # all 176 pages
tools/img/scan2ocr/rules/r145_extract_figures.sh 39 41    # a page range
```

## The split — and why it is not one program

Geometry **measures** rectangles. A model **judges** which of them are figures.

That division is forced, not stylistic. `FINDINGS.md` records that "is this a
picture or is it type" is not answerable from any low-level statistic, and this
step is where that bites hardest: **half this magazine's figures are pictures OF
text** — screen photographs, printer hardcopies, character-set samples,
flowcharts with labelled nodes. Every statistic that rejects a data table on a
tint also rejects those. MEASURED: making line structure a hard reject took
p29's Newsroom printout, p32's flowchart and all four of p40's screenshots out
along with the tables.

So the geometry does not decide. It measures, records its evidence
(`line_structure`, `flat_tone`, `ink`, `type`), and hands over.

```
r145_extract_figures.py   candidate rectangles + evidence + an overlay
r145_judge_figures.py     one model call per page, WITH the overlay and the
                          page's caption lines -> which are figures, their
                          number, their conversion type
r145_name_figures.py      named crops, sorted into png/{c,gray,bw,dots}/
```

## How a rectangle is found

**The caption is the anchor.** 64'er sets a figure to a measure and puts its
caption immediately beneath, so `Bild 3.` gives the figure's bottom edge, its
number, and a lower bound on its width outright. Only the top has to be found.
Everything the earlier ink-segmentation approach got wrong -- boxes snapped to
the column grid, captions swallowed, figures split at a gutter -- came from
deriving those edges from pixels instead of reading them off the page.

Then four measurements decide where the rectangle actually stops. Each was
forced by a defect a vision census named:

1. **Width and height settle together.** The caption's measure is a LOWER bound:
   a figure spanning two columns is captioned under one. So the box grows
   sideways until it meets text -- but the band it tests must be the figure's
   own height. Testing a band from the page margin down to the caption let a
   headline three columns up block the growth of a figure nowhere near it, and
   no wide figure could ever widen. Find the top at the current width, grow the
   width within that height, repeat. MEASURED: 84 boxes grew; p032's flowchart
   690 -> 1903 px, p023's printer photo 1061 -> 2108 px.

2. **Paper is bright AND neutral.** Yellow is the brightest ink there is -- a
   solid Y tint measures 220+, above `PAPER_LEVEL` -- so every luminance test
   in this file called a tint panel bare paper and could not see its edges at
   all. One mask, dark OR chromatic, is built per page and shared by all of
   them.

3. **A strip of bare paper is a boundary.** Growth stops at TEXT RECTANGLES,
   which is not the same as stopping at the figure. Where the OCR returns none
   -- a table set on a tint, which it reads poorly -- growth ran straight
   through: p143's block diagram came out with a whole comparison table beside
   it. Two printed objects are separated by paper running the full height of
   both; nothing printed has such a strip through its middle. The box is cut
   there, and the caption says which piece is the figure. With no caption to
   choose by, every piece becomes a figure instead -- discarding one would throw
   a real picture away.

4. **A tint panel IS the figure**, and its edge is where the tint stops --
   something neither the OCR region nor the caption knows. On p143 the region
   ended half way down and the caption is set INSIDE the panel beside the
   artwork, so both cut the bottom quarter off. Two things this needs: a panel
   has white printed on it, so a short unmarked run is crossed if the tint
   resumes beyond it; and only the figure's OWN caption is transparent, because
   a caption belonging to another figure is exactly the boundary between two.

Where a caption gives nothing -- an opening photograph, a cover -- the source is
tesseract's own ALTO `<Illustration>` regions, which step 010's OCR pass already
computed and only the TSV renderer threw away. They over-segment a composite
(p27's two greeting cards came back as eight), so they are joined; the join is
narrower than the smallest measured gap between two different figures (248 px on
p133) or it merges neighbours.

Finally: **a box holding two captions is two figures** and is dropped in favour
of the per-caption boxes, ribbons are rejected (no figure in this magazine is
one), and boxes enclosing text are rejected (a photograph does not contain a
text block; a frame does).

## Naming

Verified against issue 8608, where every image major number is an article start
page and never the page the picture sits on:

```
<start>-<n>.png     n is the printed caption number: "Bild 3" -> 3
<start>-0.png       an opening photograph, which carries no caption
<start>-00.png      ...and the next one, when -0 is taken
<start>-t<n>.png    a table too complex to transcribe, kept as an image
<start>-3a.png      two figures claiming one number (the repo already has this)
```

## Conversion buckets

`tools/convert-scans.sh` reads `png/{bw,gray,c,dots}/` and does the rest. The
four are physically different objects and the conversion differs accordingly:
colour and greyscale are scaled to 150 dpi, black-on-white is thresholded at
600, and a screened halftone is descreened before thresholding. The judge picks
the bucket, because it can see the picture.

## Verification

```bash
cd tools/img/scan2ocr/rules
OUT=$(python3 -c 'import r010_ocr_blocks as OB; print(OB.OUT_DIR)')

# 1. every kept figure produced a file, and no two share a name
python3 - "$OUT" <<'PY'
import json, os, sys, collections
d = sys.argv[1] + "/figures"
rows = json.load(open(f"{d}/png/figures.json"))
names = [r["name"] for r in rows]
dupes = [n for n, c in collections.Counter(names).items() if c > 1]
missing = [r["name"] for r in rows
           if not os.path.exists(f"{d}/png/{r['type']}/{r['name']}")]
print(f"figures {len(rows)}  duplicate names {dupes or 'none'}  missing files {missing or 'none'}")
sys.exit(1 if dupes or missing else 0)
PY

# 2. no figure was cut from an advertising page
python3 - "$OUT" <<'PY'
import json, sys
d = sys.argv[1]
rows = json.load(open(f"{d}/figures/png/figures.json"))
bad = []
for r in rows:
    k = json.load(open(f"{d}/{r['page']:03d}.labels.json", encoding="utf-8")).get("page_kind")
    if k in ("ad", "toc"):
        bad.append((r["name"], k))
print("figures on ad/toc pages:", bad or "none")
sys.exit(1 if bad else 0)
PY

# 3. every crop is a real image file of plausible size
find "$OUT/figures/png" -name '*.png' -size -2k | head

# 4. NO EDGE SITS ON A CONSTANT.  This is the check that caught the page-margin
#    bug: thirteen boxes shared the right edge 4700, which was W - MARGIN_PX and
#    not the page edge, and it had been shearing the right frame rule off every
#    figure that reached the outer margin.  An edge value repeated across many
#    figures is a clamp, not a boundary.
python3 - "$OUT" <<'EDGES'
import json, sys, collections
rows = json.load(open(sys.argv[1] + "/figures/png/figures.json"))
for i, side in ((0, "left"), (2, "right"), (1, "top"), (3, "bottom")):
    val, n = collections.Counter(r["bbox"][i] for r in rows).most_common(1)[0]
    print(f"{side:<7} most common edge {val} x{n}"
          + ("   <-- SUSPECT: an edge repeated this often is a clamp" if n > 5 else ""))
EDGES

# 5. NO FIGURE IS MOSTLY INSIDE ANOTHER.  Two captions claiming the same artwork,
#    or a cluster emitted alongside its own members, both show up here.
python3 - "$OUT" <<'OVERLAP'
import json, sys
rows = json.load(open(sys.argv[1] + "/figures/png/figures.json"))
bad = []
for i, a in enumerate(rows):
    for b in rows[i + 1:]:
        if a["page"] != b["page"]:
            continue
        ax0, ay0, ax1, ay1 = a["bbox"]
        bx0, by0, bx1, by1 = b["bbox"]
        iw = min(ax1, bx1) - max(ax0, bx0)
        ih = min(ay1, by1) - max(ay0, by0)
        if iw <= 0 or ih <= 0:
            continue
        share = iw * ih / min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0))
        if share > 0.5:
            bad.append((a["name"], b["name"], round(share, 2)))
print("overlapping pairs:", bad or "none")
OVERLAP

# 6. EVERY CAPTION IS SOURCED.  The caption used to come from the model's
#    reply, and the model reads the page image -- so where the OCR had missed a
#    caption it supplied the real text, and where it could not read one it
#    supplied a plausible one instead.  7 of 64 matched no OCR block on their
#    page; one read "Bild 2. Anschlussbelegung des CIA 6526" for a chip printed
#    "Bild 3. Die Pinbelegung des CIA 6526".  Invented metadata is worse than
#    missing metadata because it is not visible as missing.
python3 - "$OUT" <<'CAPS'
import json, re, sys, unicodedata
rows = json.load(open(sys.argv[1] + "/figures/png/figures.json"))
norm = lambda t: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", t).lower())
bad, capped = [], 0
for r in rows:
    if not r.get("caption"):
        continue
    capped += 1
    rec = json.load(open(f"{sys.argv[1]}/{r['page']:03d}.json", encoding="utf-8"))
    page = norm(" ".join(b.get("text", "") for b in rec["blocks"]))
    n = norm(r["caption"])
    if not any(n[:k] and n[:k] in page for k in (40, 28, 20, 14)):
        bad.append((r["name"], r["page"], r["caption"][:60]))
print(f"figures with a caption {capped}; unsourced {len(bad)}")
for n, p, c in bad:
    print(f"   UNSOURCED {n} p{p} {c!r}")
CAPS

# 7. EVERY CAPTION IS BOUND TO THE FIGURE IT IS PRINTED UNDER.  Sourcing is not
#    enough: a caption can be real, OCR'd and present on the page and still be
#    attached to the wrong figure.  131-2 held the 6510 with 131-3's "Bild 3" on
#    it while its own "Bild 2" sat directly beneath the crop, and every check
#    above passed.  A number bound to the wrong picture is worse than no number,
#    because the article's text refers to it.
python3 - "$OUT" <<'BIND'
import json, sys
rows = json.load(open(sys.argv[1] + "/figures/png/figures.json"))
bad = []
for r in rows:
    if not r.get("caption"):
        continue
    x0, y0, x1, y1 = r["bbox"]
    rec = json.load(open(f"{sys.argv[1]}/{r['page']:03d}.labels.json", encoding="utf-8"))
    hit = None
    for b in rec["blocks"]:
        if r["caption"][:18] not in b.get("text", ""):
            continue
        bx0, by0, bx1, by1 = (v * 2.0 for v in b["bbox"])   # 300 -> 600 dpi
        hit = (bx0, by0, bx1, by1)
        break
    if hit is None:
        continue                       # sourcing is check 6's job
    bx0, by0, bx1, by1 = hit
    if by0 < y0 or min(x1, bx1) - max(x0, bx0) < 0.5 * min(x1 - x0, bx1 - bx0):
        bad.append((r["name"], r["caption"][:40]))
print(f"captions bound below their figure and in its column: {len(rows) - len(bad)} ok, {len(bad)} misbound")
for n, c in bad:
    print(f"   MISBOUND {n} {c!r}")
BIND

**Then LOOK at them.** The counts above cannot tell a photograph from a data
table, which is the whole difficulty of this step. Open
`$OUT/figures/png/c/` and read a sample, and read the overlays in
`$OUT/figures/overlay/` for the pages with the most boxes.

## Known limits — MEASURED, not guesses

**This step is not finished.** Eighteen vision censuses have scored the corpus,
each looking at every crop and judging it GOOD / CUT / EXTRA / JUNK. Whole-corpus
figures for the first twelve, then per bucket as the reviews were split up:

| census | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| good % | 34 | 40 | 34 | 31 | 37 | 34 | 33 | 42 | 46 | 39 | 52 | 60 |

| bucket | 13 | 14 | 15 | 16 | 17 | 18 |
|---|---|---|---|---|---|---|
| `c/` | 79 | 64 | 67 | 67 | 72 | 73 |
| `bw/` | 33 | 32 | 50 | 55 | — | 48 |
| `dots/` | 56 | 50 | 40 | 47 | — | 41 |

The first seven are flat: five different detection methods, all inside one
standard error. What moved the number was never a better detector — it was
finding, one at a time, the places where a boundary the paper *states* was not
consulted, or was consulted and then ignored.

Read the percentages with care. Reviewers differ by ±5 points on the same build,
the buckets stopped being comparable file-for-file once figures started moving
between them, and the census that reported colour 73% did the arithmetic itself:
"on the 49 files common to both runs the prior GOOD count was also 36 — the GOOD
count did not move."

### What is fixed, and verified

Each of these was a boundary already present on the paper:

| the boundary | how it was being missed |
|---|---|
| a figure's own labels | read as text, so they bounded the figure instead of belonging to it |
| paper is bright AND neutral | a yellow tint measures 220+, so luminance called every tint panel bare paper |
| a strip of bare paper | growth stopped only at OCR rectangles and ran through whatever had none |
| a tint panel's edge | the region ended half way down; the caption was set inside the panel |
| a caption | short and against a panel, so it passed the "sits on the figure" test |
| a caption above | its band reached 62% of the page up, over the previous figure |
| a stopper | ended one step of the growth scan, which then looked past it |
| a frame rule | any dark band near an edge, so a screen dump's status bar was trimmed as one |
| line work across a gutter | distance alone cannot tell a split figure from two neighbours |
| the page margin | a 260 px guard cut every figure that reached the trimmed edge |
| a failed cluster | discarded the figures inside it instead of falling back to them |

Two measurements are settled and independently confirmed:

- **The press screen of this issue is 133 lpi at 45°** — 4.4–4.5 px pitch, peak
  78–411× the local median, unscreened crops peaking at 0° every time. A
  reviewer wrote its own FFT and agreed on the bucket of all 35 line-art crops.
- **The right-edge clamp is gone** — 13 boxes once shared the edge 4700; now
  zero do, and edges spread continuously to 4948.

### What is left, and why a constant will not do it

**No gap threshold can separate figures.** MEASURED: a figure's own internal
white band runs 324 px (p79) and ~430 px (p60), while the gap *between* distinct
figures runs ~160 px (p52) and ~110 px (p74's three boxes). The populations
overlap. Changing the clustering gap from 300 to 120 proved it — it resolved not
one merge, and created two new splits.

That leaves one mechanism with two signs, about 20% of crops:

- **the box is the hull of a contiguous ink/tint field, not of a figure.** Where
  the field bridges two figures they merge (`22-2`, `27-7`, `42-000`, `137-4`,
  `160-2`); where the figure extends past the field it is cut (`12-0`, `27-3`,
  `39-2`, `142-t1`).

Three things would address it, in order of expected value:

1. **Frame-first segmentation.** `framed_rects()` exists, is documented, and is
   *uncalled*. Four reviews have pointed at it. Its nest suppression is fixed
   (p172: 212 rectangles → 34); what remains is recall — it returns **zero** on
   p74, whose three boxes are plainly framed. Understand that and frames can
   carry the segmentation, which is the only structure that separates the two
   populations above.
2. **Caption binding by number.** Where the magazine sets captions ABOVE their
   figures (p133's two-column pinout spread) every binding slips one slot.
   Binding to the nearest figure in either direction was tried and reverted — it
   merged p133's five chips into three. Parse the printed number and match it to
   figure order instead.
3. **Non-rectangular masks.** `30-0` is an irregular cut-out photo with the
   standfirst set into its concavity: no rectangle can contain the figure without
   the text. This one is not a bug, it is a limit of the representation.

Still absent entirely: four printed figures that get no box at all (p23's Bild 3,
p40's charset specimen, p128's DFÜ cover, p168's labyrinth). All four are small
high-contrast type or line items — a principled hard case for a screen-based
detector, not a tuning miss.

