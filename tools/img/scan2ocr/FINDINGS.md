# scan2ocr — findings

What was measured on issue 8609, and what was tried and reverted. The second
half is the more valuable one: every reverted idea below looked obviously right,
and three of them were verified on a handful of pages before a full sweep showed
they made the corpus worse.

All figures are at 300 dpi, page 2480×3507, from the graded A4-cropped 600 dpi
masters.

---

## 1. Tesseract silently discards text on a screened tint

Its page-layout analysis decides a tinted panel is a picture and never OCRs it.
p51's boxed "Checksummer und MSE" sidebar — editorial text the corpus must
contain — produced **0 characters** under psm 3 and psm 4, and **1214** under
psm 6 on the identical crop.

Nothing downstream can recover from this: the text never enters the pipeline. It
is why the **coverage-rescue pass** exists — ink no block covers is re-OCR'd with
layout analysis off. Making that work needed four further mechanisms, each of
which failed visibly without the others:

| problem | fix | measured |
|---|---|---|
| uncovered cells bridge into one page-spanning web through rules and gutters | drop cells with too few text-like neighbours; grow the covered mask; require a component to fill its own box | first attempt returned one component covering x 0.09–0.94, y 0.04–0.91 of p51 |
| a rescued region spans two columns and psm 6 interleaves them line by line | recursive XY-cut | "schalten. abläufe festgelegt. Ganz nach / Ihren Vorstellungen." |
| a gutter is clean only over part of a region's height | cut rows first, then columns, recursively | the same gutter cuts cleanly across 1258 px and not at all across 1360 px |
| the cut lands on the ink, leaving no white margin | pad each rect by 8 px | p9's heading band came out 42 px tall and psm 6 read **nothing**; padded to 57 px it read "Computerzeit für Grafikfreunde" perfectly |

Related: the gutter is not clean. Scan speckle and drop shadows leave ink in it,
so a near-zero test scores its longest run at 22 px (under the 24 px minimum)
while a 2 % tolerance scores the same gutter at 34 px. Text columns run 0.20–0.87
ink, so the tolerance clears the dirt by an order of magnitude.

---

## 2. On a screened tint, confidence is not evidence

This is the one that costs the most time to rediscover. Tesseract is
**confidently wrong** on tint: p11's bottom-right panel returned

> `die unterschied. der Organisation und de Ai Inhaltsverzei nisses.`

at **conf 91.0**. No confidence gate catches that, and because the block counted
as covered, the rescue never re-read the region — it re-read only the scraps
around it, and the two readings then overlapped.

What *does* separate the cases is the background itself:

| region | fraction of pure-white pixels |
|---|---|
| tint panels (p51, p9, p11) | 0.004 / 0.006 / 0.009 |
| plain columns | 0.668 / 0.719 |

Two orders of magnitude. A confident block now masks its ink only where it sits
on **paper**; on a tint the region is always re-read.

---

## 3. Typography, measured

| thing | signal | measurement |
|---|---|---|
| paragraph opening | first-line indent | **+31 to +35 px**; continuation lines 0 ± 2 |
| line beside a drop cap | same | **+121 px** — indented, but *not* a new paragraph |
| bold run-in subhead | ink coverage in the line's box | **0.401 / 0.427 / 0.522** against 119 body lines whose median is 0.248 and whose **maximum** is 0.311 |
| listing vs prose | digit density | hex dump **0.50 / 0.63**; every body block on 7 pages **0.00–0.10** |
| section bar | unbroken dark run + height | ~52 px tall; sheet-edge shadow 11–15 px; hairline rule ~8 px |
| source note | line height vs the page's own **median body** line height | **below 0.85×** is uniformly a source note — 46 blocks of 969, the `Info:` lines clustering at **0.66–0.67**. The 0.85–0.95 band is ordinary body, including 26- and 28-line blocks on p145. |

**Leading does not find subheads.** The obvious hypothesis — a subhead has extra
space above it — is false here: `Zielblock` measures **0.81** of the block's line
pitch and `Spritenummer` **0.98**. The compositor set them tight. Boldness works;
leading does not.

The source-note ratio is taken **per page** (type size varies between pages) and
from the **median** (so one odd block cannot move it). A useful side effect: the
same measurement catches every `Fortsetzung von/auf Seite N` cross-reference,
which is the page-link signal article reconstruction needs.

**Tesseract's own paragraph numbering is not usable.** It called p58's 11-line
block one paragraph and p55's 26-line block one paragraph; both plainly contain
several.

---

## 4. Things that turn out not to matter

Each of these is a plausible tuning lever that measurably does nothing, so nobody
needs to try them again.

| lever | result |
|---|---|
| **OCR dpi** | unknown-word rate 300 dpi 19.85 %, 350 19.52, 400 19.34, 402 19.49, 450 19.47, 600 native 19.75. Whole spread 0.5 pp on counts whose sampling noise is already ±20. 300 also falls out of the 600 dpi source as an exact ½ box filter. |
| **`preserve_interword_spaces=1`** | word counts **identical** with and without on three pages (858 / 742 / 750). It only pads the rendered txt; this pipeline joins words from the TSV itself. `dasursprüngliche` stays merged either way — that is the recognizer, not a setting. |
| **binarizing the whole page** | does *not* make the main pass find a tint panel, and costs accuracy: 18.28 % grey → 18.69 Otsu → 19.05 Sauvola. Binarisation belongs only in the rescue crop. |
| **descreening for accuracy** | word counts unchanged (71–76) across every variant; only confidence inflates (83.7 → 93.2). Descreening matters for **structure** — it restores the gutters that make a cut possible — not for reading. |

**Reading from the graded master rather than the raw thumbs does help**, though:
unknown-word rate 19.85 % → 19.08 %, mean confidence 88.1 → 88.7 — and it removes
the facing-page sliver problem entirely, since an A4-cropped page has no facing
page.

---

## 5. Tried, measured, reverted

**Do not re-implement these without reading the numbers.**

### Splitting a block at an internal column gutter — reverted twice
Tesseract sometimes puts two columns in one block and every line then spans both:
p10's vendor addresses read `8910 Landsberg 2300 Kiel` — across instead of down,
which is factually wrong text. Cutting at a gutter no word crosses fixes that in
principle. Over all 176 pages: **recall 0.942 → 0.650, precision 0.945 → 0.594,
and 52 pages began emitting text where vision sees none.** It did not even fix
p10, because the `SUPER-SPIEL FÜR C 16` heading spans both columns so no x-range
is uncrossed. `split_block_columns()` is still in `ocr_blocks.py`, unwired.

The lesson generalises: where tesseract's blocking is wrong, the evidence is the
**text** reading across, not the geometry. That is stage B's job — it sees the
page and decides reading order.

### "This reads like German prose, so it cannot be a listing" — reverted
Stage B insists p51's standing Checksummer sidebar is a listing because its
*subject* is listings; no prompt wording moved it, including quoting the sidebar
verbatim. Two vetoes were tried. Digit density failed immediately (a BASIC
listing built from string constants carries few digits — it reinstated 37
paragraphs of listing on p56). German function-word density looked *perfect* on
the pages to hand — p56's listing blocks score **0.000**, every one; the sidebar
0.276–0.333; body text 0.182–0.325; nothing in between — and it fixed p51 while
leaving five listing pages clean. Across all 176: **recall 0.938 → 0.863,
precision 0.951 → 0.848, and fourteen pages** in the listings section started
emitting listing text again. A REM-commented listing carries plenty of German.

### Joining paragraphs on "does not end with a full stop" — reverted, then narrowed
A paragraph ending on `Die` is half a paragraph — correct, and worth fixing.
Applied broadly it cost **recall 0.934 → 0.908** for 0.007 precision, because
list items, bylines and headings legitimately end without a full stop. Narrowed
to a closed set of German function words it costs **0.002 recall** and removes
**all 36** dangling paragraph ends in the corpus. Same idea; scope decided it.

### Skipping a rescue component that overlaps a confident block — reverted
Intended to stop a rescue re-reading text already read well. It cost p51 its
entire rescued sidebar (**recall 1.00 → 0.60**) and p9 its panel, because a
component's cells can be genuinely uncovered while its bounding box merely grazes
a confident block. Resolved instead by keeping both readings and dropping the
loser on confidence — with the tint exception from §2.

---

## 6. Bugs worth recognising by their signature

**A label the prompt offers must be a label the code accepts.** `caption` was
offered to stage B and excluded from the corpus, but was missing from
`VALID_LABELS`, so every block the model correctly called a caption failed
validation and fell back to its **geometric** label — which is `body`. Figure
captions, table titles and listing instructions were silently reinstated as
article text.

*Signature:* two rounds of prompt edits produced **byte-identical output**. When
a prompt change provably changes nothing, suspect the answer is being discarded,
not that the model is stubborn.

**A cached verdict is only valid for the blocks it was made about.** Stage B's
cache was keyed on the page alone, so after stage A renumbered its blocks the
cached labels applied to ids that no longer existed, nearly everything fell back
to the geometric guess, and the corpus scored 0.822 instead of 0.917 — with no
error anywhere. Id sets are now compared.

**A service error is not data.** Hitting the account session limit wrote *"You've
hit your session limit"* into 165 truth files, and because truth generation skips
files that already exist, those would have been ground truth forever. Separately,
an auth expiry killed pages 84–176 of a sweep, was counted as a per-page error,
and the evaluation still **printed a mean built on 93 dead pages**. Both are
guarded now; `evaluate.py` refuses to score pages that were never classified.

**Single-word blocks are content.** `MIN_BLOCK_WORDS = 2` deleted them as grit.
Tesseract decides where a block ends, so on p40 it split a column's opening line,
put the first word in a block of its own, and the rule removed it — the corpus
read `von Zeilen und sowie eine Fill-Funktion`, missing `Spalten`. Measured over
ten pages: 28 single-word blocks discarded, **14 at conf ≥ 90 and real**.

---

## 7. The ground truth is not infallible

On **p76** the vision transcription is wrong and the pipeline is right. The page
documents four Hypra-Basic modules, each with `Funktion:` / `Syntax:` /
`Parameter:` / `Beispiele:` prose the magazine wrote. Vision saw
`Listing 1. Modulnummer: 36`, assumed listings, and stopped after 6 paragraphs;
the pipeline emits 50. Its 0.13 precision is a false alarm.

Checked for systemic rot: exactly **one** page shows the pattern (recall ≥ 0.85
while emitting ≥ 2× truth). Excluding it, precision is 0.949. So the harness
holds up — but a bad score is a reason to look at `review/pNNN.png`, not a
verdict.

---

## 8. Assembling articles (stage D)

**The unit is the paragraph, not the page.** A page routinely holds the end of
one article and the start of the next, so grouping whole pages into articles
cannot express the issue. Stage D cuts one flat paragraph stream at confirmed
boundaries instead.

**Candidate boundaries must include every page's first paragraph, not only the
blocks stage B called headlines.** MEASURED: 133 candidates = 82 titles + 41
page-starts + 10 continuation markers, and the page-starts recovered three real
headlines the page pass had missed entirely — `THORN EMI GIBT AUF` (p11),
`NEUE CP/M-SOFTWARE FÜR DEN C 128` (p12), `DIM-ANWEISUNG AUFHEBEN?` (p15).

**`drop` matters as much as `start`.** A display headline arrives from OCR as
fragments, sometimes across a page break — `Wie` / `funktioniert` (p124) then
`ein` / `Comnuter?` (p125) — and a continuation page reprints the headline. 13
of 133 candidates are drops. Without the action the corpus grows four spurious
one-line articles out of one headline.

**The boundary cache must be keyed on the prompt, not on the candidate count.**
Three prompt revisions in a row would otherwise have replayed the first answer.
Same failure class as stage B's block-id cache; the key is a hash of the whole
question.

**The table of contents must come from pages 6–7 only.** Stage B labels the
cover `toc` as well, and the cover is nothing but OCR noise off display type;
taking every `toc`-labelled block filled the evidence with 6 KB of garbage
before the real contents were reached.

**A continuation is confirmed in both directions.** "Fortsetzung auf Seite 146"
is joined to page 146 only when the marker there points back. All five jumps in
this issue (32↔146, 127↔169, 131↔133, 138↔142, 162↔164) are symmetric, so a
one-way match would be evidence of a misread, not of a jump.

**A page can resume an interrupted article AND finish a different one.** Page 146
carries the second half of the p30 printer survey, then the end of the MPS 802
review that ran onto it from p145 — resuming mid-word, `...in der La-` /
`ge amerikanisch`, with nothing between the two but a change of subject. Every
paragraph after a continuation marker is therefore a candidate, with a `resume`
action for "the continuation ends here and the page goes back to what it
interrupted". Without it the survey swallowed the review's ending.

**After a cross-page join, the merged paragraph keeps the page it STARTED on.**
Reading `out[-1]["page"]` to decide "is this the first paragraph of a new page"
then answers yes for every remaining paragraph of that page, and the whole page
merges into one. MEASURED on p146, whose second paragraph vanished into its
first. Track the last page seen separately.

**A trailing hyphen at a COLUMN or PAGE break is a line-break hyphen too.**
`reflow()` only sees the lines inside one block, so p8's `Jack Tramiel ver-` /
`folgte in Amerika` — two blocks — was joined with a space into `ver- folgte`.
145 joins across the issue carry a trailing hyphen; most are genuine suspended
hyphens (`Informations- und`, `Fach- und`) that must keep it, the rest soft ones
(`Pro- gramme`, `vor- handen`) that must lose it, and nothing local separates
them. All three join sites now share one `join_text()` that marks it.

**Each paragraph's own first-line indent decides whether it continues the one
before — not its page's first indent.** After a continuation splice the joined
paragraph is not the first on its page: reading the page's indent welded the
assembler course onto an unrelated notice about the Austrian edition on p140.

**A department and a column are both one article; they differ in where the title
comes from.** A *department* is a run of pages under a standing running head for
which the magazine prints no headline at all — `Aktuelles` (p8–12, 22 news
items), `Leserforum` (p15–16, 22 reader questions). Its title is the running
head, which is the one place a running head may become a title, and the opening
boundary needs `keep_heading` so the first item's headline survives as a `##`
instead of being eaten as the title. A *column* prints its headline —
`Tips & Tricks für Einsteiger`, `Die CP/M-Ecke (Teil 3)` — and that is the title.

Neither follows from the running head alone: `Tips & Tricks` runs over p62–96,
most of it full articles. Left to inference this flipped a dozen articles
between runs.

**Hyphens are resolved over the distinct words, not the occurrences** — the
answer is a property of the word, and the issue's 4287 marks are only 3459
different words. Two 1986 traps, both present and both got right: pre-reform
`ck` splits as `k-k` (`Druk¬ker` → `Drucker`, `Blök¬ken` → `Blöcken`) while
`Druck¬kopf` is a genuine compound and stays `Druckkopf`; and pre-reform
spelling is preserved, never modernised (`Jahres¬schluß` → `Jahresschluß`).
`Ra¬darund` → `Radar- und` carries a soft hyphen and a suspended hyphen in one
token, which no local rule reaches.

---

## 9. Known open defects

- **Paragraph granularity in list-like content.** Address lists and BASIC listing
  lines arrive as one paragraph where a reader sees several (p133, p055, p075,
  p062). The clearest case is p146: its 54-line manufacturer list is correctly
  *included* but arrives as one or two paragraphs against vision's 18.
- **p10's vendor addresses still read across two columns** — see §5 for why the
  obvious fix is worse than the defect.
- **p091 / p089** — foldout schematic pages whose title never survives OCR.
- **p167** — a `Wettbewerb` prize page; stage B calls it an ad, vision calls it
  editorial. The running head says editorial; three prompt attempts did not move
  it. One page, left as a documented divergence.
- **Character-level OCR errors** — `»/om` for `»Vom`, `aufein`, `dasursprüngliche
  Spritein`. Measured as unaffected by dpi, by `preserve_interword_spaces`, and by
  binarisation. These are the recognizer's, and belong to
  `tools/llm/ocr_error_correction.sh` and `spell_check_and_correct.sh`.
