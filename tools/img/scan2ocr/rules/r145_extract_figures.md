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

Three sources, in order of how much they can be trusted:

1. **Printed frames.** This magazine frames nearly every placed figure, and a
   rule is the figure's own edge: it does not wander across a gutter the way an
   ink-grown box does, and it does not die where the picture goes pale. A
   rectangle needs a long horizontal rule, another below it with much the same
   x-extent, and a vertical closing at least one end.

   **Three sides, and a rule may be broken.** The scan nicks a rule, a caption
   hides one, and sometimes the fourth is simply not printed. Demanding four
   perfect sides found only immaculate frames and dropped everything else to the
   weaker sources. MEASURED over the issue: closing nicks up to 24 px and
   accepting three sides took the kept figures from 86 to **103** and the
   judge's "I can see this but it has no box" count from 45 down to **28** --
   and it is what finally cut the recurring `64'er Test` rubric badge, the
   single most-repeated miss in every review.
2. **Gaps between text.** A figure sits in a column-width slot between two
   pieces of text. The slot is the figure — bounding it by ink instead is what
   three rounds of vision review kept objecting to.
3. **Clusters of OCR scraps.** Garbage the OCR read *off* a picture marks where
   one is. A picture yields several scraps, so they are clustered, and never
   across something printed between them.

Then: captions are cut off (64'er sets them flush under the figure with no white
gap), the printed rule is trimmed with one pixel to spare for scan blur, and
regions that touch with nothing between them are merged.

**A figure is kept only on positive evidence that it is article matter** — the
text above or below it is the magazine's own. Testing for the *absence* of an
advertisement instead let 68 figures through on 32 advertising pages, because a
gap between an ad and a page footer has no ad on both sides.

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

A vision pass over 71 of the finished crops scored **26 good, 17 cut, 26
carrying something extra, 2 junk** — that was before frames tolerated broken
rules, which lifted the kept count from 86 to 103 and cut the missing count from
45 to 28. The proportions have not been re-measured at that scale. What remains, and why:

- **A figure whose frame is not printed** falls back to the gap and scrap
  sources, which are much weaker. Most "cut" and "extra" crops are these.
- **Flowcharts with labelled nodes fragment.** Their nodes contain real text, so
  the merge step refuses to join across it — correctly, by the rule that keeps
  two figures with a caption between them apart. p31's printer-selection
  flowchart is the standing example.
- **Type is judged from the whole bounding box**, so a red badge on white can
  read as `bw`, and a colour portrait against a desaturated background as
  `gray`. 3 of 71 were misrouted.
- **~45 figures per issue are reported missing** by the judge, which reports
  what it can see with no box. That list is the honest recall measure and the
  right input to the next round of work.

The next mechanism worth building is frame detection that tolerates a broken or
partial rule, since a printed frame is by far the most reliable signal here and
everything else is a fallback.
