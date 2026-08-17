# 145 — Cut the article figures out of the masters

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

**Then LOOK at them.** The counts above cannot tell a photograph from a data
table, which is the whole difficulty of this step. Open
`$OUT/figures/png/c/` and read a sample, and read the overlays in
`$OUT/figures/overlay/` for the pages with the most boxes.

## Known limits — MEASURED, not guesses

**This step is not finished.** Eleven vision censuses have scored the whole
corpus, each looking at every crop and judging it GOOD / CUT / EXTRA / JUNK:

| census | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| good % | 34 | 40 | 34 | 31 | 37 | 34 | 33 | 42 | 46 | 39 | — |

The first seven are flat: five different detection methods, all inside one
standard error of each other. What moved the number was not a better detector
but finding, one at a time, the places where a boundary the paper *states* was
either not consulted or consulted and then ignored.

The buckets diverge sharply, and that is the honest headline:

| bucket | latest good % |
|---|---|
| `c/` colour photographs, covers, tint panels | ~52-65 |
| `bw/` line art, hardcopies, screen dumps | 30 (doubled from 15) |
| `dots/` screened diagrams and pinouts | 29 |

Colour figures are close to usable. **Everything still broken is line art.**

### What is left, as mechanisms

- **Bottom loss on framed artwork** — 11 of 20 bw crops. The screen-dump case is
  fixed and verified ("every screen photograph keeps its status line"); what
  remains is thin frame rules and line drawings whose ink fades out at the edge.
- **Label columns still sheared on four pinouts** — a chip's pin names sit
  outside the screened body of the chip, and where the region and the caption
  both stop at the body, nothing extends the box to them.
- **Page furniture absorbed** — a screened headline banner is physically
  indistinguishable from a figure's screened box fills, so `124-1` and `124-2`
  pull in the banner and a body column with it.
- **Coarse screens are not reliably detected.** See the note in `classify()`:
  the median-delta method is exhausted at two scales, and a periodicity
  measurement is the honest next step.

### What was fixed, and what it cost to find

Every one of these was a boundary already present on the paper:

| the boundary | how it was being missed |
|---|---|
| a figure's own labels | read as text, so they bounded the figure instead of belonging to it |
| paper is bright AND neutral | a yellow tint measures 220+, so luminance called every tint panel bare paper |
| a strip of bare paper | growth stopped only at OCR rectangles, and ran through whatever had none |
| a tint panel's edge | the region ended half way down and the caption was set inside the panel |
| a caption | short and against a panel, so it passed the "sits on the figure" test and stopped bounding |
| a caption above | its band reached 62% of the page up, over the previous figure |
| a stopper | ended one step of the growth scan, which then looked past it |
| a frame rule | any dark band near an edge, so a screen dump's status bar was trimmed as a frame |
| line work across a gutter | distance alone cannot tell a split figure from two neighbours |

