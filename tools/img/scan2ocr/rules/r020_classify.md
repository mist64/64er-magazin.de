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

## EVERY labels.json RECORDS THE MODEL THAT MADE IT

`rec["model"]` and `rec["transport"]` are written on every page. These labels
are a MODEL'S JUDGEMENT — which block is a caption, which is noise, what order
a reader goes in — and a judgement from a different model is not a worse
version of the same answer, it is a different answer that nothing downstream
can distinguish.

**MEASURED, 2026-11-03: five issues were labelled by the wrong model and nobody
knew.** `r000_llm._call_api` passed `model=MODEL`; `_call_cli` passed nothing,
so the CLI took the invoking session's default. SH8605, SH8606, SH8607, SH8608
and 8701 — four of them published — were classified by Fable, against the Opus
this chain chooses in a comment directly above its `MODEL` constant, *"the
cheaper tiers get wrong often enough to matter"*.

It surfaced only because Fable ran out of tokens, months later, and then it
looked like an account-wide outage. **The substitution was wrong AND invisible,
and only the second let it survive.** One line in the file it produced would
have shown it the first time anyone opened one.

So: whatever produces an artefact stamps itself into it. Check it when reading
a label file from a build you did not run, and when an issue's labels disagree
with what you see on the page.

The CLI's own per-session transcripts under
`~/.claude/projects/<cwd-slug>/` carry `"model"`, `usage` and `totalCostUSD`,
and step 020 runs with `cwd=<tmp>/masters600`, so each issue's calls are filed
in their own directory. That is how the five were identified after the fact,
and it is also how to total an issue's token cost — 8701's 192 pages came to
$86.53, $0.45 a page.

### A stamp cannot describe the run that came before it — and do not re-ask for one

On 8701 the stamp was added **during** the re-ask it was meant to document: 128
pages ran on the commit before it, 64 on the commit after, so two thirds of a
correct Opus build carries no `model` field. The temptation is to make the
record whole. Both ways of doing that are wrong:

- **Re-asking the 128 is not a provenance fix, it is a rebuild.** The calls are
  not deterministic, so the new labels differ, and differing labels move block
  boundaries and the reading order — steps 030 onward would re-run on two
  thirds of the issue to obtain a string that is already known. Paying $58 to
  make an artefact self-describing is defensible; paying it to *re-decide* the
  issue's text is not.
- **Hand-writing the field is worse than leaving it blank.** A provenance field
  typed in by whoever believes they know is exactly the record this chain
  learned not to trust. An absent stamp says *"look it up"*; a hand-written one
  says *"stop looking"*, with no way to tell the two apart later.

So the gap stays, and the EVIDENCE moves into the repo: lift the per-page
model, cost and timestamp out of the CLI transcript into the issue's
`reviewed/` ledger, and cite **that** file. `~/.claude/projects/` is a cache —
it rotates, it is outside the repo, and it is not on the machine of whoever
reads the ledger next. The stamp then fills itself in the next time 020
re-asks a page, which is soon enough.

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

| issue | denominator | recall | precision | order | headings |
|---|---|---|---|---|---|
| 8611 | all 192, refusals scored as truth | **0.733** | 0.767 | 0.999 | 0.744 |
| 8611 | the 149 refusal-free, **mixed** | **0.930** | 0.973 | 0.999 | 0.908 |
| SH10 | all 168, refusal-free, **mixed** | **0.892** | 0.962 | 0.995 | 0.799 |
| SH10 | the 129 **with article text** | **0.860** | 0.951 | 0.994 | 0.738 |

A reader budgeting from 0.733 goes looking for a regression that was never
there.

**AND THE DENOMINATOR IS NOT THE ONLY THING THE TABLE HIDES: A PAGE WITH NO
ARTICLE TEXT SCORES 1.00 AND LIFTS THE MEAN.** `score()` reads

```python
recall = len(pairs) / len(truth) if truth else (1.0 if not ours else 0.0)
```

so every ad, form, cover leaf and standalone listing whose truth is
`NO_ARTICLE_TEXT` contributes a perfect 1.00 to a **mixed** row. SH10 has 39
such pages: 0.892 mixed against 0.860 on the 129 that carry article text.

**SO ONLY ROWS OF THE SAME KIND COMPARE.** MEASURED, 2026-11-15, in one
exchange that got this wrong in both directions inside ten minutes: control
asserted that non-article pages DRAG the mean down and that SH10's 168 was not
comparable to 8611's 149 (both false — they lift it, and both rows are
refusal-free mixed rows, so those two DO compare); the builder then compared
SH10's article-only 0.860 against 8611's mixed 0.930 and read a shortfall that
is partly the same artefact (also false). The honest reading of the rows above
is SH10 about **4 points below 8611 on recall and 11 on headings, like for
like**, and 8611 has no article-only row because its truth files are gone.

**AND A GAP AT 020 IS NOT A LOSS FROM THE ISSUE.** SH10's missing recall is
concentrated in printed TABLES dimmed as noise — p098 (a full-page CP/M BDOS
function table), p021, p097, p147 — which are **step 160 Pass 3's work**. Text
that arrives as a table is not text that was lost. The gate that settles it is
**r320**, the omission check, and those pages are named in its brief so it has
to account for each one instead of reporting a total.

**AND COUNT THE HEADINGS, DO NOT READ THEIR SCORE.** SH10's headings figure of
0.738 says nothing actionable; the count does. 365 `#` lines in the truth, 197
of them not headings in ours, across 59 pages — and **98 of those 197 are two
reference-list shapes**: 73 Kochrezepte Kernel-routine entries (p141–148) and
25 Impressum labels, where the vision truth chose a heading per entry. Those
are a 160/290 question about table-shaped reference lists, not a classifier
defect. What was left after removing them was a thin tail of 1–7 a page, and
two real misses worth 290's attention: SH10 p123, whose own article title
(`»Zeichensetzereien« auf dem C 128`) is not a heading on its page though 030
titled the article with it, and p007's Q&A question heads. **Concentrated and
spread mean different fixes, and the mean cannot tell them apart.** `is_refusal()` now catches it in three places: `build_truth` will not
write one, `score()` will not score one already on disk, and the summary
prints how many pages it could not score before it prints any figure.

> **A score without its denominator is not a score.** Both of this file's
> earlier disasters were the same shape — 165 truth files of "session
> limit", and a stage B that died leaving 174 unclassified pages while the
> evaluation printed recall 0.505 as if it meant something.

A refusal is not deterministic: delete those truth files and most of them
transcribe on a second pass. Deleting them is the correct response, not a
workaround.

**Budget two extra passes.** MEASURED on 8611, deleting and re-asking each
time: **43 refused → 18 recovered → 6 more → 19 left**. So **24 of 43, 56 %,
come back over two further passes**, and what remains is a hard core that
keeps declining. 19 of 192 unscorable is the floor to plan for, not a failure
to chase; say the denominator and move on.

### The truth is keyed on the prompt that produced it

`labels.json` carries `PROMPT_KEY` and re-asks when the classify prompt
changes. `truth/` had no equivalent, so when the truth prompt was fixed to
stop excluding the masthead, the classifier re-asked and **the truth did
not** — p187 kept scoring against a stale `NO_ARTICLE_TEXT` until the file
was moved aside by hand. One page here; a wider change to that prompt would
have left every truth file stale with nothing to say so.

Each truth file now opens with `<!-- truth-key: … -->` and `build_truth`
re-asks any file that does not carry the current one. When you change
`TRUTH_PROMPT`, either let it re-ask or migrate deliberately and **write
which in `LOG.md`** — on 8611 the 173 existing files were stamped rather than
re-asked, because the masthead clause was the only semantic change and the
one page it affected had already been rebuilt.

> A cached answer to a question nobody is asking any more is not an answer.
> That now applies to both caches at this step, which is the only reason the
> second one was noticed.

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

## WHICH MODEL — measured, not assumed

`r000_llm.py` sends this step's prompt and overlay to `claude-opus-5`. A local
model is cheaper and needs no credentials, so the substitution was measured
rather than argued: **GLM-5.3-Flash (oQ4e, 320B/18B active, multimodal, served
by oMLX)** was given this file's `PROMPT` *unmodified*, with the same overlay
and digest, on 15 pages of 8611 spanning every `page_kind`, and its verdict
diffed against the Opus verdict that shipped.

| | `reasoning_effort: low` | `high` |
|---|---|---|
| block labels agreeing | 90.4% (639/707) | 90.7% on the 9 hardest (559/616; low scored 89.6% on the same 9) |
| reading order identical | 12/15 pages | 7/9 pages |
| `page_kind` identical | 11/15 pages | 6/9 pages |
| cost | 50 s/page — **2.8 h** per 200-page issue | 183 s/page — **10.2 h** |

`high` buys **+1.1 points for 3.7x the time**, and it is not an improvement so
much as a reshuffle: it fixed p006 (9/17 -> 16/17) and p059 (30/39 -> 39/39) and
broke p136 (113/113 -> 106/113) and p102 (63/63 -> 59/63). Neither setting is a
substitute for Opus here.

**Read the agreement number with the label taxonomy in hand.** Two thirds of the
disagreements (49 of 68) were GLM saying `noise` where Opus said `ad`, on
ad-heavy pages like p092 and p139. `ARTICLE_LABELS` is `{heading, body,
listing-inline}`, so `ad` and `noise` are excluded alike: that class costs
overlay colours and nothing else. **An agreement percentage over all labels
measures the wrong thing.** What to measure instead, and what the harness now
reports:

- **article blocks in the truth's `order` that are missing from the
  candidate's** — text LOST. p094 agreed on all 39 labels and dropped id35,
  80 words of body, out of the reading order. Label agreement cannot see this.
- **non-article blocks added to `order`** — garbage INJECTED. p075 relabelled
  two `noise` blocks (`'e! N e! 8/2 5/64/1'`, read off a screened tint) as
  `body`; p006 turned 8 `toc` blocks, `INHALT` and a 243-word entry list among
  them, into `heading`/`body`.
- **`page_kind`**, which is wrong on a third of pages at either effort and
  drives how later steps treat the page.

**So this step stays on Opus** — it is ~350 calls an issue, the CLI transport
needs no API key, and a wrong label here is invisible until the article reads
wrong. What the local model is worth is a **second opinion**: 2.8 h for a whole
issue, and after filtering the `ad`/`noise` class the disagreement set was 19
blocks over 15 pages, about **1.3 per page** — a review surface a person can
actually look at, and one that finds the decider's slips as readily as the
challenger's. Use it to disagree, not to decide.

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

### A SOURCE NOTE IS SMALLER THAN THE BODY **AND SHORT** — A PANEL IS ONLY SMALLER

`source` is assigned by measurement: a body block whose line height is under
`SOURCE_LINE_RATIO` (0.85) of its page's body median is a note — "Info: …",
"Bezugsquelle: …", a publisher's address, "Fortsetzung von Seite 32". Smaller
type alone, though, also describes the **boxed review panel** the magazine sets
beside an article ("Was kostet …?", "Gesamturteil:", "Preis und
Bezugsquelle:"), which is body text and a lot of it.

MEASURED over 8702's 184 pages — every body block under 0.90 of its page's
median, 45 of them: **every genuine note is 1–7 lines** (the longest, p012's
Bezugsadresse, carries two addresses in one block), and **every false one is 8
lines or more** — the panels on p036 and p039 at 8, 11, 14, 14 and 33. The
ratio alone cannot separate them: genuine notes run from 0.672 to 0.856 and the
panels sit at 0.724–0.810, inside that range. `SOURCE_MAX_LINES` = 7 falls
between the two populations, where the data put it. Issue-wide the change moves
20 paragraphs on two pages: p036 16 → 4 source paragraphs, p039 14 → 6.

A long address is not an exception to the ceiling: p10's vendor list arrives as
ten separate blocks of one or two lines and p146's as twenty-one, which
`SOURCE_JOIN` puts back together afterwards.

**What this does NOT fix**, recorded because it is one block and will come
back: 8702 p039's two-line tip id4023 measures 0.846 of the page's median
against its own column's 1.00, and is demoted. `line_h_frac` is the median word
height over the block's lines, and two lines are a small sample of a noisy
statistic. The line PITCH is the stable quantity and r010 measures it already
inside `paragraphs()` without recording it; emitting it per block is the fix,
on the next issue that re-runs 010 — re-running it here would invalidate the
whole LLM pass for one block.

## A BLOCK BOUNDARY IS NOT A PARAGRAPH BREAK, AND THE INDENT IS NOT THE ONLY WITNESS

`join_runons` decided a block boundary on the first-line indent alone: a
paragraph running over the foot of a column is flush, a new paragraph is
indented, *the page states which it is*. True — wherever the magazine indents
paragraph openings. **8702 does not**, and the test then says "join" every
time, with nothing to say otherwise.

MEASURED on 8702, 2026-11-17: p153's 50-line block starts flush and so does
every block around it (every line within ±2 px of its own median at 600 dpi),
and p039's adventure tips are set flush AND justified to the full measure on
the last line — last-line fill 0.997–1.000 over all 41 tips, so neither the
indent nor the ragged last line carries anything. p153's eight body blocks
became **one 4234-character paragraph** against the truth's five, and p039's
tips became one paragraph per GAME, 1570 characters for THE PAWN.

What the page does still say is **leading**, which is the evidence
`paragraphs()` already uses inside a block — it simply stopped at the block
edge. The gap between two blocks, over the earlier block's own line pitch:

| | |
|---|---|
| true continuation (p153 7→8, 8→9) | 0.20, 0.30 |
| new paragraph, same column (p153 3→4) | 1.46 |
| new paragraph, tip to tip (p039, 41 of them) | 1.53–1.87 |
| new paragraph across a figure (p153 9→21, 21→31) | 14.7, 15.1 |

Nothing lies between 0.30 and 1.46. `block_follows()` returns `column` (the
two blocks do not share a column — the classic break, where only the indent and
the sentence can speak), `run` (same column, under `BLOCK_GAP_RUN_MAX` = 0.60
of the pitch — consecutive lines split for some other reason: a tint, an inline
figure, a rescue pass) or `gap` (same column, extra leading). **Space is a
paragraph break in any typography**, so `gap` vetoes the join — unless the
sentence before it is unfinished, which is exactly what an inline figure looks
like and the one case where leading does not mean a new paragraph.

The distance is measured in both directions, so a column read UPWARDS — r010's
`rot180` pass — measures the same as one read downwards.

**VALIDATED over the whole issue against its 184 truth pages**: the sum of
|paragraphs − truth| falls 754 → 703; 14 pages come closer, 167 are untouched,
and 3 move away — two of them `NO_ARTICLE_TEXT` ad pages where the count means
nothing, and p174, where the new break puts "Schicken Sie Ihre Erfahrungen an:"
on its own line above the address. p039 goes 8 → 41 paragraphs (truth 64), p153
1 → 4 (truth 5). **And not one page gains or loses a character**: whitespace
removed, every page's text is identical before and after. This moves where
paragraphs break and nothing else.

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

**THIS GATE IS A PRESENCE TEST AND CANNOT SEE A WRONG IMPRESSUM.** It asks
whether the masthead page kept ANY blocks. SH8605's p194 kept 20 of them with 8
distinct labels, so the gate passed — while the corpus had the masthead
interleaved with the Depot-Händler ad that shares the page, which is the defect
(the Impressum column is one of three on that page and its blocks alternate with
the ad's in reading order).

**And the obvious strengthening does not work — do not re-attempt it.** The
errata that produced this paragraph proposed: *a masthead label present in
`blocks/pNNN.txt` and absent from `NNN.article.txt` is a HARD fail.* Tried
against SH8605's own artefacts, it reads **clean on the issue whose Impressum
was wrong**: all 8 labels (Chefredakteur, Stellv. Chefredakteur, Redaktion:,
Verlagsleit, Vertriebsleit, Verantwortlich, Urheberrecht, Druck:) are in BOTH
files. What was wrong was the ORDER and the values between the labels, and no
label-set comparison can see that.

**What did see it was `r020_evaluate.py`, at recall 0.19 — so it is not
optional.** Two builds (SH8603, SH8604) left that evaluation "pending" and this
is what it is for: of the first four steps of SH8605, the one real defect was
found by nothing else. Run it, and read `WORST.txt`.


```bash
# The venv, not bare "$PY" (numpy), and the ISSUE's page count, not
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
plus a 600 dpi crop of the master, **in the shape of the previous issue's
Impressum — open it and copy its markup.** Do not copy the shape from here:
there is no house shape, and the example that stood in this sentence
(`<article class="impressum">` with a `<p><em>Label: </em>value</p>` run) is
none of the corpus's three. MEASURED: SH8604 has a plain `<article>` with
`<p><strong>Label:</strong> value</p>` and `<hr>`; SH8603 uses
`<em>Label: </em>`; SH8601 `<strong>Label</strong>:` with one `<hr />`. The
PREVIOUS ISSUE wins over any example written down here, which is what SH8605
did, correctly. Resolve the line-break hyphens. The prior issue decides OCR doubts one word at a time and
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

## PROSE OCR'd INTO A LISTING BLOCK IS INVISIBLE TO EVERY TEXT STEP (SH8607)

SH8607 p151: the ruled box *"Wichtiger Hinweis zum Abtippen — Bitte beachten
Sie den neuen Checksummer 128 …"* was OCR'd as the HEAD of block 7, labelled
`listing-standalone` (byline + box + the kernel 128 dump). From there it was
invisible all the way through: **020** drops listing blocks from the text by
design, **130** replaced the dump with the disk embed, **190** walked the page
but the box was never in the HTML to repair, and **r320**'s UNACCOUNTED half
excludes listing blocks. It survived to 290, found by an agent comparing bold
heads against the page, and was restored from the crop.

**A `listing-standalone` block whose leading lines are prose — no line number,
no hex address, sentence punctuation — is split.** At the very least r320 must
list it as "prose inside a listing block" so a human looks.

### The prompt must name the issue it is actually reading

**MEASURED, 2026-11-03, by the 8701 build: every classification prompt in the
chain said "issue 9/September 1986".** It was 8609's string, hardcoded, and it
went to the model on all 448 of 8701's calls — Fable's and Opus's alike — and
on every page of every issue built since 8609. Three prompts carried it
(`r020_classify.py`, `r020_evaluate.py`, `r145_judge_figures.py`) and a comment
in `r010_ocr_blocks.py` repeated it.

The folio example is in the prompt so the model recognises the foot of the page,
so the impact is probably small: the footer is identified by position and shape
as much as by its words. **That is not the point.** It is a wrong fact handed to
a judgement step on every page for five issues, and like the unnamed model
above, nothing in any output would ever have shown it. The builder found it by
reading a prompt, not by running a gate.

It now comes from the descriptor — `Issue.label`, `Issue.self_phrase` and
`Issue.folio_hint` in `r000_issue.py`, derived from the id, because for a
monthly the issue number IS the month and a stored copy could only disagree
with it. **A Sonderheft gets `label is None`** and a prompt that describes it
truthfully instead of inventing a folio form nobody has looked at; fabricating
one there would reintroduce this very defect a level down.

Two traps if you touch these strings:

- **`r145`'s prompt is NOT an f-string.** It is `.format()`ed per page with
  `{page}`, `{cands}` and `{caps}`, so making it one consumed the fields and
  raised `NameError` on import. It substitutes by `replace()` on a
  `__ISSUE_PHRASE__` placeholder. The other two take no format fields and are
  f-strings.
- **Grep for the string before believing it is gone.** Four files held it and
  only three were prompts.
