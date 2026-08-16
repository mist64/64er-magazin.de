# scan2ocr — scans → article-text corpus

Extracts **article text and only article text** from a scanned 64'er issue, as
markdown: no running heads, no folios, no ads, no Kleinanzeigen, no standalone
type-in listings, no facing-page slivers. One `.md`-shaped `.txt` per page; a
page carrying no article yields an empty file, which is a result and not a
failure.

Sibling of `scan2mrc/`. Same conventions: constants at the top of each file
heavily commented, no CLI knobs, no env knobs, a debug overlay for every page.

**Before changing anything, read [`FINDINGS.md`](FINDINGS.md).** It holds what
was measured on this issue, and — more usefully — the things that were tried,
looked obviously right, and made the corpus worse. Several of them are the kind
of idea that occurs to everyone.

---

## Current state

Measured against a vision reading of all 176 pages of issue 8609:

| | |
|---|---|
| recall | 0.947 |
| precision | 0.952 |
| order | 0.996 |
| headings | 0.876 |
| corpus | ~412,000 chars over 91 pages |
| assembled | 54 articles, ~398,000 chars |

⚠️ **Scores are only comparable within one set of `truth/` files.** Regenerating
truth (any change to `TRUTH_PROMPT`) re-bases every number. When you regenerate,
re-measure the baseline before claiming an improvement against an older figure.

---

## Requirements

- `tesseract` 5.x with the **`deu`** traineddata (`brew install tesseract tesseract-lang`)
- Python 3.11+ with `pillow`, `numpy`; `anthropic` optional (see *Transport*)
- Input: the deskewed, matted, A4-cropped, graded **600 dpi** masters produced by
  `scan2mrc` (`pipeline.sh --only master,final`), one PNG per page

Paths are constants at the top of each file — `SRC_DIR`, `OUT_DIR` — pointing at
the working issue. Change them there, per issue; there is no flag.

---

## Running it

Every script takes page numbers as arguments. Stage A is CPU-bound and
parallelises; stages B/C call a model and self-parallelise.

```sh
# Stage A — OCR + measurement (local, no model, ~15 min for 176 pages)
seq 1 176 | OMP_NUM_THREADS=1 xargs -P 6 -n 8 python ocr_blocks.py

# Stage B + C — classification, reading order, markdown (one model call per page)
python classify.py $(seq 1 176)

# Stage D — pages back into articles, one markdown file for the whole issue
python assemble.py

# Score against a vision reading (builds truth/ on first run, then scores)
python evaluate.py $(seq 1 176)

# Gather what a human should look at
python collect.py
```

**After any change to stage A, wipe `OUT_DIR` and start from page 1.** Stage B
caches its verdict per page in `NNN.labels.json` and reuses it, which makes
re-rendering the text free — but the cache is keyed to the block ids stage A
produced, and it is discarded automatically if they no longer match.

---

## Stages and outputs

```
A  ocr_blocks.py   thumbs/NNN.png -> 300 dpi grey -> tesseract TSV
                   -> NNN.json         blocks: bbox, features, geometric label
                   -> NNN.digest.txt   compact page brief for stage B
                   -> NNN_boxes.png    overlay
                   -> NNN.article.txt  PROVISIONAL text, from geometry alone

B  classify.py     one model call per page (digest + overlay image)
                   -> NNN.labels.json  final label, role and reading order
                   -> NNN_final.png    overlay, non-corpus content dimmed
C  classify.py     -> NNN.article.txt  the deliverable, overwriting A's guess

D  assemble.py    ONE model call for the whole issue (article boundaries)
                   -> 8609.md          every article, in issue order
                   -> articles.json    the structure, machine-readable
                   -> hyphens.json     resolved line-break hyphens (cache)

   evaluate.py     -> truth/NNN.txt    a vision reading of the same page
                   -> report.jsonl     per-page scores
                   -> WORST.txt        pages whose signals disagree, worst first
   collect.py      -> review/pNNN.png + review/pNNN.txt + review/INDEX.txt
```

Stage A is deterministic and local. Stage B is the only step that calls a model,
and is asked the **one** question geometry cannot answer: is this block editorial
matter or is it advertising? Stage B also decides **reading order** and assigns
each kept block a **role**; geometry cannot see a sentence continuing across a
column, and neither can a rule.

**Label decides inclusion, role decides rendering.** Keeping those orthogonal is
what lets the markdown layer sit on top without disturbing the classification.

---

## The corpus text

Markdown, one line per **paragraph**, blank line between paragraphs:

| | |
|---|---|
| `# ` | the headline of an article starting on this page |
| `> ` | the standfirst between headline and body |
| `## ` | a standalone section heading, set on its own line |
| `### ` | a bold run-in subhead opening a paragraph (`Ursprungsblock`, `Zielblock`) |
| ` ``` ` | a short code fragment quoted inside the prose |
| *(no prefix)* | role `row` — one record of a table. Renders like body but is never reflowed into the paragraph beside it |
| `<p class="source">` | a source note set in a smaller face — `Info: …`, a publisher address, an ISBN/price credit, `Fortsetzung von Seite 32`. Markdown cannot express it, so it is emitted as HTML, which markdown passes through. **Consecutive source notes are one note**, joined with `<br>`: p10's vendor list is set as ten separate lines and p146's as twenty-one, and the line breaks are the address's structure rather than typesetting. 75 blocks over the issue become 32. |

---

## Stage D — pages back into articles

Stage C answers "what is on this page". Stage D answers the three questions that
only exist once the pages are back together:

| question | how |
|---|---|
| where does an article begin and end? | one model call for the whole issue. A page can hold the end of one article and the start of the next, so the unit is the **paragraph**, not the page |
| does a paragraph continue over the page break? | the same test as a column break — the continuation is not indented, or the paragraph before it ends on a German function word. Until this stage existed, **every page boundary was a false paragraph break** |
| where does an interrupted article resume? | `Fortsetzung auf Seite 146`. Five such jumps in this issue, each confirmed in both directions before the two halves are joined |

The model is shown every candidate boundary — each page's first paragraph, every
block the page pass called a headline, every `Fortsetzung` cross-reference — with
the running head above it, the text before it, and the issue's table of contents
off pages 6–7. It returns `start` / `continue` / `drop` per candidate, plus a
clean title for each start. Everything else in the stage is deterministic.

`drop` matters as much as `start`: a display headline arrives from OCR as
fragments (`Wie` / `funktioniert` / `ein` / `Comnuter?` across two pages), and a
continuation page reprints the headline. The first fragment becomes the article
title, the rest are dropped.

The page range in the title — `# Wie funktioniert ein Computer? [124-127, 169-171]`
— falls out of the grouping. A page carrying two articles appears in **both**
ranges: lossy for that page, correct for both articles.

**Bylines** sit in parentheses at the very end of the last paragraph, welded
onto the sentence by OCR because that is how it is printed. Two forms, 41
occurrences each: `(bs)` — an editor's initials, a news item written in house —
and `(Knut Smoczyk/tr)` — a reader's name, then the editor who took it in. Both
end in exactly two lowercase letters. Kept verbatim, always split into their own
paragraph.

**A department or a column is ONE article containing many items**, and the two
differ only in where the title comes from:

| | title | example |
|---|---|---|
| **department** | the **running head** — the magazine prints no headline for the run | `Aktuelles [8-12]`, 22 news items as `##`; `Leserforum [15-16]`, 22 reader questions as `##` |
| **column** | the **printed headline** | `Tips & Tricks für Einsteiger [64-65]`, 8 tips as `##`; `Die CP/M-Ecke (Teil 3)` |

The department case is the one place the running head becomes a title, and it
needs `keep_heading` on the opening boundary so the first item's headline is not
swallowed as the title.

A shared running head never merges by itself: `Tips & Tricks` runs over pages
62–96, most of which carry full articles (`Module für Hypra-Basic`, `HiRes
Colossal`). And a headline naming a specific product or event is an article even
when it shares a page — `Professionell und preiswert` (a Forth compiler test) is
not a section of the assembler comparison beside it.

Left to inference this flipped a dozen articles between runs, so every part of
it is stated in the prompt with examples.

---

## Hyphens

A hyphen at a line end is **marked, not resolved** by stages A–C: it becomes `¬`
— at a line break inside a block, and equally at a **column or page break**,
which is the same physical fact. (p8's `Jack Tramiel ver-` / `folgte in Amerika`
came out as `ver- folgte` while only line breaks were marked; 145 joins across
the issue have a trailing hyphen, most of them genuine suspended hyphens that
must keep it.) German writes
one for three different reasons and no local rule separates them —

| printed | reading | correct output |
|---|---|---|
| `Zei-/chensatz` | soft hyphen | `Zeichensatz` |
| `Sprite-/Block` | compound | `Sprite-Block` |
| `Groß-/und Klein…` | suspended | `Groß- und Klein…` |

A case test gets the third wrong (`und` is lowercase, so "break before lowercase
= soft hyphen" yields `Großund`). A hyphen *inside* a printed line stays a plain
`-`, so the two are always tellable apart — which is the point of marking rather
than guessing candidates with a regex, as
`tools/llm/hyphenation_check_and_correct.sh` has to.

**Stage D resolves them**, over the *distinct* broken words rather than the
occurrences — the answer is a property of the word, and the issue's 4287 marks
are only 3459 different words. Two 1986-specific traps, both present here:

- Pre-reform orthography splits `ck` as `k-k`: `Druk¬ker` → `Drucker`,
  `Blök¬ken` → `Blöcken`. But `Druck¬kopf` is a genuine compound and stays
  `Druckkopf`. 13 such pairs in the issue; a naive joiner gets them all wrong.
- Pre-reform spelling (`daß`, `muß`) must be **preserved**, never modernised.

Results are cached in `hyphens.json`, so a re-render is free.

---

## The harness

`evaluate.py` has a vision model transcribe each page under the same rules the
pipeline follows, then scores us against it. Vision misreads characters too, so
it is not truth in an absolute sense — but it fails in completely different ways
from tesseract-plus-geometry, so where the two disagree is where the bugs are.

Four numbers, deliberately **not** combined, because they imply different fixes:

| | low means |
|---|---|
| **recall** | we are LOSING article text — a dropped panel, a skipped column |
| **precision** | we are KEEPING non-article text — ad copy, OCR gibberish off a photo |
| **order** | the flow is broken — columns interleaved, a headline stranded |
| **headings** | the markdown structure is wrong — level, or missing entirely |

Matching is fuzzy at token level; chasing character identity would only
re-measure tesseract's error rate. Markdown prefixes are stripped before
matching, so the first three stay comparable across the markdown work.

**How to use it.** Read `WORST.txt`, not the mean. A mean moves for reasons that
have nothing to do with the change you made. And when a page scores badly, look
at `review/pNNN.png` before believing it: on p76 the truth was wrong and the
pipeline was right (see `FINDINGS.md`).

**Verify on all 176, never on the handful that motivated the change.** Two rules
in this pipeline's history looked perfect on their test pages and were reverted
after a full sweep — details in `FINDINGS.md`.

`evaluate.py` refuses to score pages that were never classified, rather than
printing a mean over stage A's provisional guesses.

---

## Transport

`llm.py` is the only place either stage talks to a model, and it picks:

- **API** (preferred) — the Anthropic SDK, when credentials resolve:
  `ANTHROPIC_API_KEY`, or an `ant auth login` profile the zero-arg client finds
  on its own. Real rate-limit handling; prompt caching across pages; no
  dependency on an interactive session.
- **CLI** — `claude -p`, otherwise. Works with no key at all, which is why it
  came first, but it inherits the Claude Code session's OAuth: it is subject to
  session limits and to token-refresh races between concurrent workers. **Two
  full sweeps were lost to this.**

Both raise `ServiceUnavailable` on a service error rather than letting the
message be written as data.

---

## Related tools already in this repo

- `tools/llm/hyphenation_check_and_correct.sh` — the natural consumer of the `¬`
  marks. It currently *guesses* candidates with `grep -oE '\S*-[a-z]\S*|…'`,
  which both misses cases and fires on mid-line hyphens; the marker makes that
  set exact.
- `tools/llm/ocr_error_correction.sh`, `spell_check_and_correct.sh` — the
  remaining character-level errors are theirs to fix; see `FINDINGS.md` for why
  they are not fixable here.
- `tools/llm/ocr_issue.sh` — an earlier take on stage A (tesseract TSV per page,
  block summaries with bbox and preview) at 150 dpi off the PDF, with no rescue
  pass and no classification. Superseded for scan input; still fine for PDFs.
