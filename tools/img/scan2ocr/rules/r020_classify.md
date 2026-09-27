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

## The evaluation's truth can be a REFUSAL, and it is not truth

`r020_evaluate.py` asks a model to transcribe each page and scores the
pipeline against that reading. On a 1986 magazine the model may decline:

> *"I can't provide a full verbatim transcription of this page. It's
> copyrighted article text from the magazine … I can offer a summary and
> short quotes instead."*

`build_truth` already refused to write a SERVICE message (a session limit
once landed in 165 truth files). It did not refuse to write a **content**
refusal, and because it skips files that already exist, every summary became
this issue's permanent ground truth.

MEASURED on 8611: **43 of 192**, almost all of them article pages — only 53
of the pages that carry article text had usable truth at all. And the harm
was not the files, it was the number:

| | recall | precision | order | headings |
|---|---|---|---|---|
| as printed, all 192 | **0.733** | 0.767 | 0.999 | 0.744 |
| the 149 with real truth | **0.930** | 0.973 | 0.999 | 0.908 |

A reader budgeting from 0.733 goes looking for a regression that was never
there. `is_refusal()` now catches it in three places: `build_truth` will not
write one, `score()` will not score one already on disk, and the summary
prints how many pages it could not score before it prints any figure.

> **A score without its denominator is not a score.** Both of this file's
> earlier disasters were the same shape — 165 truth files of "session
> limit", and a stage B that died leaving 174 unclassified pages while the
> evaluation printed recall 0.505 as if it meant something.

A refusal is not deterministic: delete those truth files and most of them
transcribe on a second pass. Deleting them is the correct response, not a
workaround.

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

### The Impressum must survive stage B

The masthead reads like a list, so this step's prompt used to group it with the
table of contents and the corpus dropped it. Silently: ~90 kept-nothing pages
is normal in an issue half full of ads, so a missing Impressum hides inside a
legitimate population, and no check anywhere looked for it. It was rebuilt BY
HAND on 8610 (commit `10a8745a`) and on SH8601, and lost outright on 8611
before the pattern was noticed. The prompt is fixed; this is what says so next
time, and it runs at step 020 rather than at the end, where a fix is cheap.

```bash
$PY - <<'PYEOF'
import glob, io, json, os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_issue
from r000_issue import ISSUE
import r010_ocr_blocks as OB
OUT = OB.OUT_DIR
# The masthead's entries. A page that carries three or more DISTINCT ones is
# the Impressum; MEASURED on 8611, p187 has 10 and no other page has 2.
MAST = (r'Herausgeber|Chefredakteur|Stellv\. *Chefredakteur|Chef vom Dienst|'
        r'Anzeigenleit|Anzeigenpreise|Verlagsleit|Vertriebsleit|Druck:|'
        r'Verantwortlich|Urheberrecht|Erscheinungsweise|Bezugspreis|Redaktion:')
bad = []
for f in sorted(glob.glob(os.path.join(OUT, 'blocks', 'p*.txt'))):
    page = int(re.search(r'p(\d+)', os.path.basename(f)).group(1))
    hits = {m.group(0) for m in re.finditer(MAST, io.open(f, encoding='utf-8',
                                                          errors='replace').read())}
    if len(hits) < 3:
        continue
    lab = os.path.join(OUT, f'{page:03d}.labels.json')
    kept = 0
    if os.path.exists(lab):
        d = json.load(open(lab))
        kept = sum(1 for b in d.get('blocks', [])
                   if b.get('label') in OB.ARTICLE_LABELS)
    print(f'  p{page:03d}: {len(hits)} masthead labels, kept {kept}')
    if kept == 0:
        bad.append(page)
print(('HARD FAIL: the Impressum was dropped on %s' % bad) if bad
      else 'ok: every masthead page keeps blocks')
sys.exit(1 if bad else 0)
PYEOF
```

MEASURED on 8611: fires on p187, which carries **10** distinct masthead
entries, and on no other page of 192 — no other page has even 2. The
published-side companion is in `r310_issue_invariants.py`: exactly one article
with `64er.id="impressum"`, which 41 of 41 published issues satisfy.


```bash
# The venv, not bare python3 (numpy), and the ISSUE's page count, not
# another issue's: the literal 176 that stood here was 8609's and would
# have scored 16 pages short of a 192-page issue and 24 past a 152-page
# Sonderheft. r010_ocr_blocks.sh fixed this in its own file years ago;
# the same literal survived here.
PY=${PYTHON:-tools/img/scan2ocr/rules/../../../../.venv/bin/python}
PAGES=$("$PY" -c 'import r000_issue; from r000_issue import ISSUE
print(r000_issue.load(ISSUE).pages)')
cd tools/img/scan2ocr/rules
$PY r020_evaluate.py $(seq 1 $PAGES)       # scores against a vision reading
"$PY" r020_collect.py                      # review bundle: pNNN.png + pNNN.txt
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

## The dropped Impressum — a masthead sharing its page with an ad

Both issues built by this chain lost the Impressum, and by the same route. The
masthead is never alone on its page: it is one column, and the rest of the page
is apparatus or advertising. The page-level judgement then goes to the majority
of the page, the label comes back `ad` / `other`, **0 blocks are kept**, and the
masthead goes with it.

| | the page | what shares it | what the classifier said |
|---|---|---|---|
| SH8601 | p146 | a book ad and a dealer list, the left two thirds | `ad`/`toc`, 0 kept — 20 masthead blocks, correctly OCR'd, thrown away |
| 8610 | p195 | the Inserentenverzeichnis, the left column | `other`, 0 kept — 30 right-column blocks (x ≥ 3312) thrown away |

**The loss is invisible.** Nothing errors, nothing is malformed, no check in the
chain fires: the article count is simply one short — 28 articles for SH8601's 29
printed. Step 020's own scores do not see it either, because a page with no
kept blocks is not a page with a wrong block.

**The signature**, and it is cheap to grep for: a page whose **kept-block count
is 0** while its `blocks/pNNN.txt` holds a column of masthead labels —
`Herausgeber`, `Chefredakteur`, `Anzeigenleitung`, `Druck`. One column of those
on an `ad`-labelled page is an Impressum, every time; an ad has no reason to
carry them.

**The recovery is a rebuild, not a re-classification.** The block index is
authoritative and it survived: reconstruct the article from that page's blocks
plus a 600 dpi crop of the master, in the shape of the **previous issue's**
Impressum (same head metas, same `<article class="impressum">`, same
`<p><em>Label: </em>value</p>` run in the printed order), with the line-break
hyphens resolved. The prior issue decides OCR doubts one word at a time and
supplies the HTML shape — it does not supply content: 8610's masthead carries a
paragraph 8609's does not (the Aktionäre / Aufsichtsrat block), and that came
off the crop.

**What catches it is r000's end-of-issue article-set completeness gate** — the
printed TOC and the previous issue's recurring rubrics, Impressum among them,
compared against the split article set. Per-step verification cannot: this is an
omission, and omission reads as correct. The classifier's page-level call is
what to fix upstream; the reconstructed file is the repair, not the fix.

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