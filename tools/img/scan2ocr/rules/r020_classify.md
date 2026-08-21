# 020 — Label every block, decide reading order, render per-page markdown

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

## Known false positive: a paragraph's orphan line labelled as a heading

When the print leaves a short final (or initial) line of a paragraph alone in
the column, the segmenter makes it its own block and the classifier labels it
`heading`/`title`; step 030 then writes it into the Markdown as `### …`, and it
reaches the article as an `<h3>`.

The signature is that the "heading" is the **grammatical continuation** of the
neighbouring paragraph. From 8609: `### Puffern` (…werden in den Puffern),
`89 Mark.`, `MHz.`, `128.`, `8000.`, `Codes drucken kann, zeigt dieses
Programm.`, plus a BASIC continuation line (`LB = BY-HB*256`) and a layout
pointer (`Listing und Beschreibung ab Seite 54`).

Real headings in this magazine are set in a heavy sans display face,
noticeably larger than body text; the false positives are body-face text at
body size. Word count is NOT the discriminator — `HiRes Colossal` (2 words) is
a real heading on the same page where `Puffern` (1 word) is not.

Until the classifier distinguishes them, step 290 must catch the residue: see
its "A heading that is really a paragraph tail" section.