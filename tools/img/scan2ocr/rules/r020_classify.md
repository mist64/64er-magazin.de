# 020 — Label every block, decide reading order, render per-page markdown

**Applies to:** all — geometry and per-page role judgement. Nothing in it knows what a Leserforum or a Sonderheft is.

**Goal:** ask a model the one question geometry cannot answer — is this block
editorial matter the magazine wrote, or advertising / apparatus? — then let it
decide **reading order**, assign each kept block a **role**, and choose the
reading of any block step 010 flagged as holding two things side by side.
Render the result as one markdown-shaped `.txt` per page.

This is a **program step** that calls a model once per page. The orchestrator
runs it; there is nothing to dispatch to a sub-agent, because the per-page
judgement *is* the model call.

## Inputs

`out/NNN.json` + `out/NNN.digest.txt` + `out/NNN_boxes.png` from step 010.
The overlay goes to the model as well as the digest: the decisive evidence for
an ad is usually visual (a bordered half-page with a product shot), and the
block ids are drawn on the overlay so the two can be tied together.

## Run

```bash
tools/img/scan2ocr/rules/r020_classify.sh
```

Four lanes, one model call per uncached page.

## Outputs

```
out/NNN.labels.json   final label, reading order, role and reading per block
out/NNN_final.png     overlay with everything not going into the corpus dimmed
out/NNN.article.txt   the per-page deliverable: article text and nothing else
```

A page carrying no article yields an **empty file**. That is a result, not a
failure.

## Caching

The verdict is cached in `NNN.labels.json` and reused, so re-rendering the text
is free. It is discarded and re-asked when either changes:

- **the blocks** — an id set that no longer matches. A cache keyed on the page
  alone once applied stale labels to renumbered ids and the corpus scored 0.822
  instead of 0.917 with no error anywhere.
- **the question** — `prompt_key`, a hash of the prompt. Without it every prompt
  improvement is silently discarded: the answers keep coming from the cache and
  the sweep looks like the rule did nothing.

## Label decides inclusion, role decides rendering

Keeping those orthogonal is what lets the markdown layer sit on top without
disturbing the classification. Roles: `title` `intro` `section` `subsection`
`code` `body`, plus `source` and `row` assigned by measurement rather than by
the model.

**A role cannot change in the middle of a sentence.** Tesseract ends a block
wherever the type changes and the magazine changes type inside a standfirst, so
a block boundary can fall mid-sentence — p39 sets `…Der Name des Freundes:`
small and `Print Shop Companion`, which finishes that sentence, large. Two
blocks, one standfirst. Size and weight say what a block is only when it starts
something new.

## Verification

```bash
cd tools/img/scan2ocr/rules
python3 r020_evaluate.py $(seq 1 176)      # scores against a vision reading
python3 r020_collect.py                    # review bundle: pNNN.png + pNNN.txt
```

`r020_evaluate.py` reports four numbers, deliberately **not** combined because they
imply different fixes: recall (we are losing article text), precision (we are
keeping non-article text), order (the flow is broken), headings (the markdown
structure is wrong). It refuses to score pages that were never classified.

Read `WORST.txt`, not the mean, and look at `review/pNNN.png` before believing a
bad score — on p76 the vision truth is wrong and the pipeline is right.

⚠️ **Scores are only comparable within one set of `truth/` files.** Regenerating
truth re-bases every number.

**Verify on all 176, never on the handful that motivated the change.** Two rules
in this pipeline's history looked perfect on their test pages and were reverted
after a full sweep; the numbers are in `FINDINGS.md`.

## A TINTED BOX ACROSS THE COLUMNS SCRAMBLES THE READING ORDER

**This issue's most damaging defect class, and the hardest to see.** Where a
band of tinted boxes or tables cuts across the text columns, each column is
split into an upper and a lower half. The extractor then emits the six (or
four) half-columns as independent blocks — and orders them wrongly, welding the
head of one column to the tail of another.

The result is **grammatical and meaningless**, which is why nothing catches it.
MEASURED on SH8601 p124, where three columns are cut by a band of four tinted
tables (Tabellen 1–4), the article read:

```
Für die RS232-Routine nach einem Moment wieder »vernünftigen« Text liefern.
…kann die Basicsen, für die der Speicher des C 64 zu klein war.
```

Two sentences, each a graft. Valid German at a glance, past r310, r320, r330
and a green build, and only found by a human reading the article.

**It has now happened twice on one issue.** r000 records the same failure on
p090, where `--psm 3` interleaved a tinted box with the surrounding body
columns. Two instances is a pattern, not an accident: **wherever a page has a
tinted box or table band interrupting its columns, verify the reading order
explicitly against the page.**

How the p124 order was recovered, as the worked method:

1. Render the FULL page and look at it — column x-centres and band y-extents
   (p124: columns at x≈330 / 1815 / 3305; bands at y≈520–2020 and 4880–6650).
2. Derive the printed order from that geometry — column by column, upper half
   then lower half:
   `col1-upper → col1-lower → col2-upper → col2-lower → col3-upper → col3-lower`
3. **Confirm every join by reading the two fragments as one sentence** at 600
   dpi. `…Mit Bit 4 wird die Übertragungsart und über die` + `Bits 5,6 und 7
   die Parität bestimmt (siehe Tabelle 2).` A join that does not read as one
   sentence is the wrong join.
4. Place each table after the paragraph that first cites it.

Record the reconstruction in LOG.md with the crop that establishes the geometry.
This is step 030's class — block order — not a word-level fix, and must be
reported as such rather than smuggled in as a typo repair.

## A paragraph's orphan line labelled as a heading — fixed in step 010

When the print leaves a short final (or initial) line of a paragraph alone in
the column, the corpus used to emit it as `### …`, and it reached the article as
an `<h3>`. The signature is that the "heading" is the **grammatical continuation**
of the neighbouring paragraph. From 8609: `### Puffern` (…werden in den Puffern),
`89 Mark.`, `MHz.`, `128.`, `8000.`, `Codes drucken kann, zeigt dieses
Programm.`, plus a BASIC continuation line (`LB = BY-HB*256`) and a layout
pointer (`Listing und Beschreibung ab Seite 54`).

**This is not the model's doing.** MEASURED over the 8609 corpus, 107 of the 110
paragraphs that reached the Markdown as `### ` were marked by stage A's
`para_subhead`, not by a `subsection` role the model assigned — and every one of
the false ones came from stage A measuring boldness as ink coverage of the line's
bounding box, which a short line inflates whatever face it is in. The fix is in
`r010_ocr_blocks.py` (stroke weight, measured per word); see its rule file and
`FINDINGS.md` §3. After it, `###` over the issue went **80 → 39**, with `#` and
`##` unchanged, precision 0.958 → 0.962 and recall unmoved.

Word count is NOT the discriminator, and neither is anything else the model can
see in the digest — `HiRes Colossal` (2 words) is a real heading on the same page
where `Puffern` (1 word) is not. Do not try to fix this class in the prompt.

What is left for step 290: a headline whose two halves are separated by OCR
garbage off an adjacent graphic still arrives split — p137's
`Wie zählen die ® .. ®` + `### Zweifingerlinge?`. See its "A heading that is
really a paragraph tail" section.