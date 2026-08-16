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
```

**Then LOOK at them.** The counts above cannot tell a photograph from a data
table, which is the whole difficulty of this step. Open
`$OUT/figures/png/c/` and read a sample, and read the overlays in
`$OUT/figures/overlay/` for the pages with the most boxes.

## Known limits — MEASURED, not guesses

**This step is not finished.** A vision census over a *proportional* sample of
the 81 crops scored **11 good, 8 cut, 12 extra, 1 junk of 32 — 34% good**, and
that split badly by bucket:

| bucket | good |
|---|---|
| `c/` (photos, screenshots, covers) | 56% |
| `gray/` | 1 of 1 |
| `bw/` (line art, hardcopies, schematics) | **0 of 8** |
| `dots/` (screened diagrams, pinouts) | **0 of 5** |

Earlier censuses read 45–53%, but they sampled `c/` heavily and `bw/`+`dots/`
barely. Proportional sampling is the honest measure and it says half the corpus
— every diagram, schematic and pinout — is currently unusable.

### The one mechanism behind almost all of it

**The rectangle is snapped to the page's column grid, not to the figure's own
frame.** The census put it exactly: *every* cut edge is a straight vertical or
horizontal line at a gutter or a page-head rule, and none is a ragged content
edge. Both defect families fall out of that single fact:

- a figure **narrower** than a column has its box widened to the column, so the
  whole neighbouring text column rides along (EXTRA);
- a figure **wider** than a column is stopped dead at the column boundary and
  its remainder emitted as a separate crop (CUT) — which is also why one pinout
  sheet still comes out as three sliding windows and one flowchart as two halves
  whose arrows point into each other.

The gap source takes its x-extent from the column a block belongs to. That is
the line to cut: **a gap should be a page-wide band whose horizontal extent is
set by where text actually is, not by column membership.** Frame detection
already does the right thing when a rule exists; the gap fallback does not.

### Smaller, separate

- **Captions and page furniture are ink-dense**, so bold `Bild N.` lines and the
  black `Aktuelles` / `Extra` banners read as figure content. `cut_captions()`
  handles the labelled ones; these are the ones it misses.
- **The recurring `64'er Test` badge** is extracted correctly but three or four
  times per issue, once per article that carries it. It is page furniture, not a
  figure, and wants dedup or exclusion.
- **A multi-page foldout** (the C 64 schematic, pp. 86–91) yields one tile per
  page. Their traces are severed in the *original*, so no per-page extractor can
  fix it; they need stitching, or accepting as tiles.
- No type errors were found in the last census: routing to `c/gray/bw/dots` is
  working.
