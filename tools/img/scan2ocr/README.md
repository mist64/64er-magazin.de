# scan2ocr — scans → article-text corpus

Extracts **article text and only article text** from a scanned 64'er issue: no running
heads, no folios, no ads, no Kleinanzeigen, no standalone type-in listings, no
facing-page slivers. One `.txt` per page; a page carrying no article yields an empty
file, which is a result and not a failure.

Sibling of `scan2mrc/`. Same inputs (the deskewed 600 dpi thumbs), same conventions:
constants at the top of each file heavily commented, no CLI knobs, no env knobs, a
debug overlay written for every page.

## Stages

```
A  ocr_blocks.py   thumbs_600/NNN.png -> 300 dpi grey -> tesseract TSV
                   -> NNN.json         blocks: bbox, features, geometric label
                   -> NNN.digest.txt   compact page brief for stage B
                   -> NNN_boxes.png    overlay
                   -> NNN.article.txt  PROVISIONAL text, from geometry alone

B  classify.py     one LLM call per page (digest + overlay image)
                   -> NNN.labels.json  final label per block
                   -> NNN_final.png    overlay, non-corpus content dimmed
C  classify.py     -> NNN.article.txt  the deliverable, overwriting stage A's guess

   collect.py      -> review/pNNN.png + review/pNNN.txt + review/INDEX.txt
                   flat folder for human review, most-suspicious-first index
```

Stage A is deterministic and local. Stage B is the only step that calls an LLM, and it
is asked the **one** question geometry cannot answer: is this block editorial matter or
is it advertising? An existing `NNN.labels.json` is reused rather than re-asked, so
changing what counts as article text is a rebuild, not 176 fresh calls.

## What the corpus text looks like

One line per **paragraph**, printed line breaks undone.

A hyphen at a line end is **marked, not resolved**: it becomes `¬`. German writes one
for three different reasons and no local rule separates them —

| printed | reading | correct output |
|---|---|---|
| `Zei-/chensatz` | soft hyphen | `Zeichensatz` |
| `Sprite-/Block` | compound | `Sprite-Block` |
| `Groß-/und Klein…` | suspended | `Groß- und Klein…` |

A case test gets the third wrong: `und` is lowercase, so "break before lowercase = soft
hyphen" yields `Großund`. A hyphen inside a printed line stays a plain `-`, so the two
are always tellable apart, and `tools/llm/hyphenation_check_and_correct.sh` can resolve
the marked ones exactly instead of guessing candidates with a regex.

## Measured facts — do not re-derive these the expensive way

Everything below was measured on issue 8609, at 300 dpi, page height 3594 px.

**Tesseract silently discards text on a screened tint.** p51's boxed "Checksummer und
MSE" sidebar — editorial text the corpus must contain — produced **0 characters** under
psm 3 and psm 4, and **1214** under psm 6 on the identical crop. Its layout analysis
decides the panel is a picture. Nothing downstream can recover from this because the
text never enters the pipeline. Hence the coverage-rescue pass: ink no block covers is
re-OCR'd with layout analysis off. Making that work needed three further guards —
uncovered cells bridge into one page-spanning web through rules and gutters, and rescued
regions span columns, which psm 6 interleaves line by line.

**Paragraph indents are unambiguous; tesseract's own paragraph numbering is not.**
Continuation lines sit at 0 ± 2 px from the block's median line start, paragraph openings
at +31 to +35. Lines beside a drop cap run to +121 and are *not* new paragraphs. For
comparison tesseract called p58's 11-line block one paragraph and p55's 26-line block
one paragraph; both plainly contain several.

**Reversed-out section bars need finding before inverting.** Inverting the whole header
band turns the paper dark and tesseract reads nothing. The bar's own white letters break
every horizontal dark run, so on a raw mask only its top and bottom edges register (p8:
runs of 330 px at rows 137–145 and 194–214, but 27–125 px through the lettering). A
horizontal closing bridges the letters. The bar is ~52 px tall against an 11–15 px sheet
edge shadow and an ~8 px rule, and spans as little as 13% of the page width, so an
average-darkness test misses it where a run-length test does not.

**Confidence is not evidence when geometry already decided.** p61's bar read
`_Fehlerteufelchen` — the correct section name — at conf **21.5**, because psm 7 on a
small inverted crop always scores low. Conf floors of 60 and of 40 both discarded it.

**Digit density separates listings from prose cleanly.** p58's hex dump: 0.50 and 0.63.
Every body block on seven test pages: 0.00–0.10. No overlap. `hex_line_frac` only reached
0.36 on the same blocks because OCR mangles some rows, so digit density is the better gate.

**Facing-page slivers land at x ≥ 0.99 with conf 3.8–40.** They are real text, so
confidence alone will not reject them — geometry must.

**300 dpi is right; higher is not better.** Unknown-word rate against a German dictionary
over p8/p55/p58 (~1980 words per condition): 300 box 19.85%, 300 lanczos 19.66, 350
19.52, 400 19.34, 402 19.49, 450 19.47, 600 native 19.75. The whole spread is 0.5 pp —
383 vs 394 words — where sampling noise on counts near 390 is already ±20. Nothing is
distinguishable. 300 also falls out of the 600 dpi source as an exact 0.5 box filter.

**`preserve_interword_spaces=1` does nothing here.** Word counts are identical with and
without it on p8/p55/p58 (858 / 742 / 750). It only pads spaces into the rendered txt,
and this pipeline joins words from the TSV itself. Tesseract still merges the occasional
word pair on tightly set justified lines (`dasursprüngliche` for "das ursprüngliche") —
that is the recognizer, not a setting.

## Related tools already in this repo

- `tools/llm/hyphenation_check_and_correct.sh` — the natural consumer of the `¬` marks.
  It currently *guesses* candidates with `grep -oE '\S*-[a-z]\S*|…'`, which both misses
  cases and fires on mid-line hyphens; the marker makes that set exact.
- `tools/llm/ocr_issue.sh` — an earlier take on stage A (tesseract TSV per page, block
  summaries with bbox and preview) but at 150 dpi off the PDF, with no rescue pass and no
  classification. Superseded by this directory for scan input; still fine for PDFs.
