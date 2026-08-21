# 330 — Compare each reprint against its already-published original

**Applies to:** all — reprinting is a property of an **article**, not of an issue kind: the trigger is a confirmed lead in `issues/<ID>/REPRINTS.md`, which any issue may carry. `ls issues/[0-9]*/REPRINTS.md` is empty today, but that records what has been scanned so far, not a property of monthlies — and classifying `sonderheft` on it would repeat the spec's rule 300 mistake, whose `monthly` guess would have silently dropped 26 Sonderheft asides. A monthly with no leads runs this rule and records "ran, zero leads", which is a checked outcome; `not applicable — kind` would not be.

**Goal:** a Sonderheft reprints articles that had already run in the monthlies.
Each such article has therefore been transcribed **twice, independently** — once
for the monthly (published, in `issues/<YYMM>/*.html`) and once here, from this
issue's own scan, by the same chain as every other article. Nothing was copied
over.

Two independent transcriptions of the same printed text disagree **exactly where
one of them mis-transcribed**. So the diff is a transcription-error finder for
**both** sides: it is the only check in the chain that can catch an error in an
issue that shipped months ago.

## What this rule is NOT

Read this section before the procedure. Every failure mode of this rule is a
version of forgetting one of these three sentences.

1. **The two versions are not required to agree.** The magazine re-set and
   re-edited its reprints: a different standfirst, cut or added paragraphs,
   retitled headings, renumbered figures, a temporal reference removed
   (`Ab dieser Ausgabe` → nothing), a cross-reference repointed
   (`Seite 54` → `Seite 110`). Those are **real differences**, printed on
   paper, and both sides keep what their own page prints.
2. **Errors printed in the magazine STAY.** This rule finds *our* errors, never
   the magazine's. A difference where both sides faithfully transcribe what
   their own page prints is **closed**, not fixed — the same standing rule that
   keeps `eröfffnet` and `Machin Lightning` in the corpus. "It reads wrong" is
   not evidence; see r000's *know which source is authoritative before
   "correcting"*.
3. **When the two disagree, the arbiter is the SCAN — not the other
   transcription.** The monthly's published HTML is a transcription, exactly as
   fallible as ours. It is a *lead*, never a verdict. A difference is settled by
   reading the printed page on each side; a difference nobody looked at a page
   for is `UNRESOLVED`, not "probably theirs".

## Run order — LAST, after rule 300

Later than everything, including rule 300:

- it compares **finished** HTML, so every text pass — heading case (260),
  autolink (270), OCR cleanup (280), hierarchy (290) — must already have run,
  or the diff reports our own pipeline against itself;
- rule 300 may add an `<aside class="fehlerteufelchen">` to either side, which
  is a block present on one side only and pure noise here if it lands later;
- a `THEIRS` finding re-opens a published issue, and that decision wants the
  current issue otherwise finished.

## Inputs

- `issues/<ID>/REPRINTS.md` — the **leads**. See the warning below.
- The built issue: `issues/<ID>/*.html`.
- The published monthlies: `issues/<YYMM>/*.html`.
- **This issue's scan** — `<OUT_DIR>/blocks/pNNN.txt` and 600 dpi crops of
  `<SRC_DIR>/NNN.png`, per the *page block index* recipe in
  `r000_orchestration.md`. This is the authority for our side.
- **The monthly's scan** — `~/DNB/64er_OCR/OCR-YYYY_MM_64er[_HIRES].pdf`,
  rendered to PNG and **read with your own eyes**. This is the authority for
  their side. Render the *page image*; the PDF's **text layer is void** (r000,
  *the PDF has no usable text layer*) — it is a third OCR of the same paper and
  proves nothing either way.
- `tools/img/scan2ocr/rules/r330_reprint_compare.py` — the deterministic half:
  `resolve`, `diff`, `verify`.

### The leads are untrusted

`REPRINTS.md` says so itself. The list was carried over from a deleted
PDF-OCR file (`SH8601.md`, removed 2026-08-21; commit history has it) which is
trusted for nothing — five of its seven reprint entries had `TODO Wiederholung`
where the body text should have been, i.e. it never transcribed them at all. It
also carries a list of articles claimed *not* to be reprints, equally unverified.

So a lead is a hypothesis. **Step 1 confirms or refutes it against the printed
page, before anything is diffed.** "Not actually a reprint" is a legitimate,
expected outcome and is recorded as one.

## Step 1 — confirm the lead against the printed page

For each row of the `## Leads` table in `REPRINTS.md`:

1. Find this issue's article and read **its printed page** (crop from
   `<SRC_DIR>`, per r000's block-index recipe).
2. Resolve the claimed original (step 2) and read **its printed page** from the
   monthly's scan PDF.
3. Decide, from the two pages, which verdict holds. `UNRESOLVED` is the
   honest answer whenever the pages did not settle it — including when step 2
   returns more than one candidate and neither page rules the other out:

| verdict | means |
|---|---|
| `CONFIRMED` | the same article, re-set. Same argument in the same order, same figures/listings, sentences recognisably shared. |
| `PARTIAL` | part of it. A multi-part series merged into one reprint (`8506/16 + 8507/17` is one lead with two originals — one row and one diff **per original**), or only a section reprinted. |
| `NOT-A-REPRINT` | same *topic*, different *text*. `REPRINTS.md` names this trap itself: `Welche Floppy für den C128?` is "near 8601/44 in topic, different text". Record it and stop — nothing is diffed. |
| `UNRESOLVED` | the original could not be identified: the page resolves to nothing (issue not imported), or to more than one article that the printed pages could not separate. Report every candidate for human review; nothing is diffed. |

**The confirmation is the two pages, not the diff.** The script's
`ALIGNED: n/m blocks paired (p%)` line is a corroborating shape and nothing more
— a genuine re-set reprint pairs nearly every paragraph, two unrelated articles
pair almost none. A high rate does not license skipping the pages, and a low
rate does not by itself refute a lead: a heavily re-edited reprint and a
mis-split article look alike from that number.

Also work the other list: `REPRINTS.md`'s *Claimed original content* section is
unverified too. Do not diff any of it, but if this issue's scan of one of those
articles obviously reproduces a monthly you recognise, say so in the report as a
**new lead** — do not act on it.

## Step 2 — locate the original article

The lead is `<YYMM>/<page>`, e.g. `8506/16`. The issue directory is
`issues/8506/`. The page is **not** the filename.

```bash
tools/img/scan2ocr/rules/r330_reprint_compare.py resolve 8506/16
```

It returns **every** article in that directory whose `<meta name="64er.pages">`
**range covers** the page — the same rule r300 step 1 uses, and for the same
reason. The filename carries only the *start* page, and four of SH8601's seven
leads point into the middle of a multi-page article: `8506/16` lives in
`16-24,26-28`, `8507/17` in `17-22`, `8512/78` in `78-82`.

**Never match by `<meta name="64er.id">`.** It is a rubric slug, not a key:
`bücher`, `leserforum`, `memory_map` and 197 others repeat across issues.

### A page number is not a key

A magazine page routinely carries the **end of one article and the start of the
next**, so a page can belong to two articles at once. This is not a corner case:
it happens on the very first live lead.

```
$ r330_reprint_compare.py resolve 8601/47
./issues/8601/44 Die neuen Laufwerke Commodore-1570_1571.html   pages=44-47
./issues/8601/47 Gestatten_ Wordstar.html                       pages=47-48

AMBIGUOUS: page 47 is shared by 2 articles.
```

Page 47 is the **last** page of the 1570/1571 drives review and the **first**
page of the WordStar test. The Sonderheft's `Test: WordStar` is a reprint of the
second — and the first is what sorts first, so anything that takes the leading
match takes the wrong article and never mentions that there was a choice.

So:

1. **`resolve` never selects.** It prints all candidates and exits **2** when
   there is more than one, so an ambiguous lead cannot be consumed as if it were
   settled. (Exit 0 = exactly one candidate; 1 = none; 2 = ambiguous.)
2. **Disambiguate by CONTENT, against this issue's article text** — which is the
   work step 1 is already doing. `--against` orders the candidates by how much
   prose they share with our article:

   ```bash
   r330_reprint_compare.py resolve 8601/47 \
       --against "issues/SH8601/<page> Test_ WordStar.html"
   ```

   On the case above that separates them 100%/100% against 2%/31%. The ordering
   is an **aid for which page to read first**; it does not pick, and `resolve`
   still exits 2. The verdict comes from the printed pages.
3. **The lead's title is a hint, not authority.** Two of the seven SH8601 leads
   are retitled in the Sonderheft — `Test: WordStar` for
   `Gestatten: Wordstar`, `Der C128D im ersten Test` for `Der C128 D im ersten
   Test` — so title agreement neither confirms a candidate nor eliminates one.
4. **A lead that cannot be disambiguated is `UNRESOLVED`**, reported for human
   review with every candidate named. Never a guess, and never "the one whose
   title looks closest".

Of SH8601's seven leads, exactly one is multi-candidate today: `8601/47`. The
other six resolve to a single article. That count is a fact about the current
corpus, not a property of leads — re-run `resolve` per lead every time; do not
carry this sentence forward as an assumption.

If **nothing** resolves, the original is in an issue that is not imported yet.
That is also `UNRESOLVED` — record it and move on; it is not a refutation of the
lead.

## Step 3 — normalise, then diff

```bash
tools/img/scan2ocr/rules/r330_reprint_compare.py diff \
    "issues/SH8601/<page> <title>.html" \
    "issues/8506/16 Erster ausführlicher Test PC 128 (Teil 1).html"
```

The script does the normalisation, and the exact boundary of what it normalises
is the whole point of having it:

**Removed, because it is an artifact of storage and would drown the signal:**

- **markup** — tags and attributes; text is extracted per block-level element
  (`p`, `h1`–`h6`, `li`, `figcaption`, `address`, `td`, `dt`, `dd`,
  `blockquote`), each block keeping its role so `p.intro` is visibly the
  standfirst;
- **entities** — `&amp;`, `&rsquo;` etc. resolved, so one side spelling a
  character as an entity is not a difference;
- **line breaks and indentation** — the HTML's own wrapping is invisible to the
  reader and must be invisible here; all whitespace collapses to one space,
  `<br>` becomes a space;
- **end-of-line hyphenation** — `Approximations- schleife` → `Approximationsschleife`,
  but **only** hyphen + whitespace + lowercase continuation, never a compound
  like `Assembler-Programm`. The joins are **counted and reported** at the foot
  of the diff rather than silently swallowed: a word left broken in published
  HTML is its own defect, so it must not vanish, but it must also not generate
  a difference on every wrapped line;
- **Unicode form** — NFC, plus no-break/thin/zero-width spaces mapped to a
  plain space or dropped.

**Deliberately NOT normalised**, because each is a place a transcription error
hides and normalising it would delete the finding:

spelling · case · punctuation · quotation marks (`»…«` vs `"…"`) · dashes
(`—` vs `-`) · numbers · `ß`/`ss` · spacing inside names (`C128` vs `C 128`).

**Excluded from the comparison:** `<pre>` / `<code>`. Program listings are not
transcribed prose — they come from the Programm-Service disk via rule 120, and
their errata state belongs to rule 300, not here.

The diff is two-level: blocks are aligned first (exact matches anchor it, the
rest pair by similarity), then differing blocks are diffed **word by word**.
That is what keeps a single re-worded sentence from reporting as two
whole-paragraph differences.

## Step 4 — present the differences for review

The report numbers every difference `D-001`, `D-002`, … in document order, and
that number is the handle everything downstream uses. Each entry shows the kind,
the block role, and the same window of context on both sides with the differing
tokens bracketed:

```
D-014  DIFFERS  <p>
  SH8601: …Ein 〈Rasterbildsdirm〉 setzt sich aus einzelnen Punkten ,…
  8506  : …Ein 〈Rasterbildschirm〉 setzt sich aus einzelnen Punkten ,…

D-015  ONLY IN 8506  <p>
  SH8601: …Punkte voneinander ist in 〈〉 Richtung der Achsen…
  8506  : …Punkte voneinander ist in 〈der〉 Richtung der Achsen…

D-016  BLOCK ONLY IN SH8601  <p.intro>
  SH8601: Der C 128 ist da — und mit ihm die Frage, was …
  8506  : (nothing aligned)
```

The kinds are named after the **side**, not after difflib's transform direction
(`ONLY IN 8506`, never `INSERT`), because at review time the only question is
which side has the words.

Present them to the user as the numbered list, grouped per pair, **with your
proposed disposition and its evidence against each one** — not as a wall of
diff for them to triage. The list is normally dominated by `PRINT`: a re-set
reprint differs from its original on purpose, and that is the expected shape,
not a problem to explain away.

## Step 5 — disposition every difference

Every `D-NNN` gets exactly one disposition. The vocabulary is closed — four
values, so the whole issue's outcome is greppable and so nobody invents a
fifth that means "I did not look":

| disposition | means | what happens |
|---|---|---|
| `PRINT` | both sides faithfully transcribe what their own page prints; the printed pages differ | **nothing.** Closed. This is the common case. |
| `OURS` | this issue's transcription misread its own printed page | fixed **here**, in `issues/<ID>/`, word-level only |
| `THEIRS` | the monthly's published transcription misread **its** printed page | **reported, not fixed** — see step 6 |
| `UNRESOLVED` | the scan could not settle it (page not in the corpus, region illegible, original issue not imported) | stays open in `LOG.md` as a known gap |

**Each disposition must cite the evidence that produced it**, and the evidence
is always a printed page:

- for **our** side: the `<OUT_DIR>/blocks/pNNN.txt` line, or a 600 dpi crop of
  `<SRC_DIR>/NNN.png` at that bbox, read multimodally;
- for **their** side: the monthly's page rendered from
  `~/DNB/64er_OCR/OCR-YYYY_MM_64er[_HIRES].pdf` and read multimodally.
  Magazine page ≠ PDF page — the offset is per-issue (commonly −2, but it
  varies); confirm you are on the right page by its folio, not by arithmetic.

A `PRINT` disposition needs evidence from **both** sides — that is precisely the
claim it makes. `OURS` needs our page. `THEIRS` needs theirs. A disposition with
no page behind it is `UNRESOLVED`, whatever it looks like.

Never reason from the other transcription ("8506 says `Rasterbildschirm`, so
ours is wrong"). That is the same shape as the `internsiv` regression: a related
but non-authoritative artifact used as an authority, and a print typo
"corrected" into something the print never said.

**Granularity.** Applying an `OURS` fix is a **word-level substitution and
nothing larger** — r000's *OCR cleanup granularity* rule applies in full, and
this rule is the place most likely to tempt you past it, because a
better-reading sentence is sitting right there in the other column. Copying a
phrase across from the monthly is re-typing from another source, not
transcribing our page. If a passage needs more than word-level repair, hand it
back: OCR the region again, or escalate.

## Step 6 — a `THEIRS` finding is REPORTED, never applied

A fix to the monthly's published HTML changes an **already-published issue**.
That is not part of building this one.

- **The sub-agent executing this rule must not edit any file outside
  `issues/<ID>/`.** Not one word. Every `THEIRS` finding goes into the report
  and into `LOG.md`, with the page evidence, and stops there.
- The orchestrator surfaces the list to the **user** and waits. Same care as
  rule 300 takes when it reaches into another issue: the evidence quoted, both
  pages named, and nothing landing until the user has actually said so.
- If the user approves, the fix lands in its **own commit**, staged by explicit
  pathspec (r000, *Commit & staging discipline*), with a message naming this
  issue as where the finding came from — so a reader of `issues/8506`'s history
  can see why a two-year-old article changed.
- If the correction concerns a **listing** in `prg/*.txt`, it does not happen
  here at all: r000's *Changing a listing ALWAYS goes to the user first*.

Two **kinds** of `THEIRS` finding deserve extra care rather than routine
handling, because each has a plausible innocent explanation: a difference inside
a **figure caption or table cell** (the two issues may genuinely print different
captions), and a difference in a **number** (r000: a genuine print typo such as
a backwards address range stays verbatim). Flag those to the user as such.

## Recording the result in `LOG.md`

One section, `## Step 330 (reprint_compare)`, in `issues/<ID>/LOG.md`. It is the
issue's disposition for this number, and `verify` parses it — the shape below is
a contract, not a suggestion.

First a table, one row per **lead × original** (so a `PARTIAL` lead with two
originals gets two rows):

```markdown
## Step 330 (reprint_compare)

| verdict | this issue | claimed | monthly file | D | OURS | THEIRS | PRINT | UNRESOLVED |
|---|---|---|---|---|---|---|---|---|
| CONFIRMED | `issues/SH8601/NN Ein Monitor ist genug.html` | 8510/16 | `issues/8510/16 Ein Monitor ist genug.html` | 12 | 1 | 0 | 11 | 0 |
| PARTIAL | `issues/SH8601/12 Rundgang durch die Hardware des C128.html` | 8506/16 | `issues/8506/16 Erster ausführlicher Test PC 128 (Teil 1).html` | 41 | 3 | 1 | 36 | 1 |
| PARTIAL | `issues/SH8601/12 Rundgang durch die Hardware des C128.html` | 8507/17 | `issues/8507/17 Erster ausführlicher Test_ C 128, Teil 2.html` | 28 | 0 | 0 | 28 | 0 |
| CONFIRMED | `issues/SH8601/NN Test_ WordStar.html` | 8601/47 | `issues/8601/47 Gestatten_ Wordstar.html` | 19 | 0 | 2 | 17 | 0 |
| NOT-A-REPRINT | `issues/SH8601/NN Welche Floppy für den C128_.html` | 8601/44 | — | — | — | — | — | — |
| UNRESOLVED | `issues/SH8601/NN Basic 7.0 – das starke Basic.html` | 8403/70 | — | — | — | — | — | — |
```

The two `PARTIAL` rows are the one merged reprint against each of its two
originals — one row, one `###` subsection and one diff per original.

Then one `###` subsection per diffed pair, its heading naming this issue's
**file basename**, with one line per difference:

```markdown
### `12 Rundgang durch die Hardware des C128.html` ← 8506/16

- D-001 PRINT — SH re-set standfirst; SH p12 crop and 8506 p16 crop both match
  their own page.
- D-014 OURS — SH p13 reads `Rasterbildschirm`; ours had `Rasterbildsdirm`.
  Fixed (one word).
- D-022 THEIRS — 8506 p18 reads `32 KByte`; the published 8506 HTML has
  `32 KByto`. REPORTED, not applied.
- D-031 UNRESOLVED — 8507 p21 is a full-bleed photo spread in our render;
  cannot read the caption. Left open.
```

**A lead whose page resolved to more than one article must show its work in the
same subsection**, one line per candidate that was *not* chosen:

```markdown
### `NN Test_ WordStar.html` ← 8601/47

- REJECTED `issues/8601/44 Die neuen Laufwerke Commodore-1570_1571.html` —
  p47 is that article's LAST page (`44-47`), and it is the tail of the drives
  review; our article's text is the WordStar test that STARTS on p47.
  Confirmed on the 8601 p47 render.
- D-004 THEIRS — …
```

and an `UNRESOLVED` lead lists **every** candidate it could not separate, with
what was tried — or, when the page resolves to nothing at all, says so:

```markdown
### `NN Basic 7.0 – das starke Basic.html` ← 8403/70

`resolve 8403/70` → no such issue directory: 3/84 is not imported. No candidate
to compare against; the lead stands untested. Reported for human review.
```

```markdown
### `NN Ein Monitor ist genug.html` ← 8510/16

- CANDIDATE `issues/8510/16 Ein Monitor ist genug.html` — p16 is its first page.
- CANDIDATE `issues/8510/14 …html` — p16 is its last page; the two share the
  page and our render of SH p9 is too dark along the gutter to tell which
  column our text continues. Left open.
```

`verify` re-resolves every lead itself and requires this: a `CONFIRMED` or
`PARTIAL` row on a shared page needs a `REJECTED` line for each other candidate,
and an `UNRESOLVED` row needs a `CANDIDATE` line for each. A single monthly file
named in the table is **not** evidence that there was only one to choose from —
that is exactly the gap this closes.

The table's columns are **positional** — `verify` reads them by index, so keep
the order and keep `—` in every cell a `NOT-A-REPRINT` row has nothing for. Each
`###` heading must name this issue's file basename, and when a lead has more
than one original (`PARTIAL`) it must also name the lead, `← 8506/16`, so the
two subsections are told apart.

Rules that make this an audit trail rather than a note:

- **Every lead in `REPRINTS.md` has a row**, including the refuted ones. A lead
  with no row is indistinguishable from a lead nobody got to — the exact failure
  r000 wrote the `not applicable — kind` discipline against.
- **The monthly file named must be one the lead page actually resolves to**, and
  where the page is shared, every other candidate carries a `REJECTED` line. A
  lead that could not be identified is verdict `UNRESOLVED` with a `CANDIDATE`
  line per candidate — never a quiet pick.
- **Every `D-NNN` the diff currently reports has exactly one disposition line**,
  the `D` column equals what the diff reports, and the four counts sum to `D`
  *and* match the lines below. `verify` checks all four of those, so a summary
  row cannot quietly say "all editorial" over a list that says otherwise.
- **`THEIRS` lines say `REPORTED`** (and, once the user has ruled, `APPLIED in
  <commit>` or `declined`).
- **`UNRESOLVED` is a known gap** and falls under r000's end-of-issue gate: by
  issue end it is closed or explicitly acknowledged by the user as permanent.
- If this issue has **no** `REPRINTS.md`, or it has zero leads, the section still
  exists and says so with the evidence line — `ls issues/<ID>/REPRINTS.md` →
  absent, or the leads table is empty. Ran-and-found-nothing is an outcome;
  silence is not.

## Anti-memory (mandatory)

Every word of evidence traces to a printed page you rendered and looked at.
Never settle a difference from what you know about the C 128, from what the
sentence "should" say, or from the other transcription. Write each rendered
page's reading into `issues/<ID>/_tmp/` first and read it back before editing
anything — the same discipline rule 300 uses for erratum text. Scratch renders
live in `issues/<ID>/_tmp/` or `/tmp/64er_<ID>_*`, never loose in the issue
directory.

## Evidence-in-report requirement

Per r000: a fix reported without evidence is treated as un-applied and
re-dispatched; the orchestrator does not re-do the verification itself. For this
rule the evidence form is, inline in the report, per disposition:

- `OURS` — the `blocks/pNNN.txt` line or the crop geometry read, and the
  before/after word;
- `THEIRS` — the monthly PDF page number rendered, the folio confirming it, and
  what that page reads;
- `PRINT` — both of the above, stated as "each side matches its own page";
- `UNRESOLVED` — what was rendered and why it did not settle it.

Bare counts are not evidence. A report that says "37 differences, all editorial"
is un-evidenced and gets re-dispatched.

## Verification

```bash
ID=SH8601                       # the issue being built
R=tools/img/scan2ocr/rules/r330_reprint_compare.py
fail=0

# 1. The gate: every lead has a verdict, every current difference has exactly
#    one disposition from the closed vocabulary, and every file the LOG names
#    exists.  Re-runs the diff, so the numbering it checks is the numbering the
#    next reader will see -- not the one the sub-agent happened to have.
python3 "$R" verify "issues/$ID" || fail=1

# 2. Nothing outside this issue was touched.  A THEIRS finding is REPORTED;
#    if the user approved a fix it is its own commit, so the tree is clean here.
git status --short -uno issues/ | grep -v "^.\{2\} \"\?issues/$ID/" && {
  echo "  a published issue was edited by this rule -- must be reported, not slipped in"; fail=1; }

# 3. Every THEIRS line carries its disposition word.
grep -n '^- D-[0-9]\{3\} THEIRS' "issues/$ID/LOG.md" \
  | grep -v -E 'REPORTED|APPLIED|declined' && {
  echo "  THEIRS finding with no REPORTED/APPLIED/declined state"; fail=1; }

# 4. Every UNRESOLVED is a known gap the end-of-issue sweep will see.
grep -c '^- D-[0-9]\{3\} UNRESOLVED' "issues/$ID/LOG.md"

exit $fail
```

`verify` alone fails when: the `## Step 330 …` section is missing; a lead in
`REPRINTS.md` has no row; a verdict is not one of the four; a file named in the
table does not exist; a pair has no `###` subsection; a difference has no
disposition, has two, uses a word outside the four, or is dispositioned but no
longer reported by the diff; or the table's counts disagree with the diff or
with the disposition lines beneath it.

It **re-resolves every lead itself**, and additionally fails when: the monthly
file named is not one of the articles covering that page; the page is shared and
another candidate has no `REJECTED` line; an `UNRESOLVED` lead has no
subsection, or lists fewer candidates than the page resolves to; or a lead that
does not resolve at all is recorded as `CONFIRMED`/`PARTIAL`.

One more trap it closes: a `REJECTED` line proves a choice was *written down*,
not that it was *right*. So `verify` also scores each rejected candidate's
shared text against this issue's article, and fails when a rejected one shares
far more of it than the chosen one does — a first-hit pick wearing a rejection
line as cover. The scores never decide which article is the original; they only
refuse to let the recorded decision contradict the text unexamined. When it
fires, re-read both printed pages.

Spot-check by hand, per r000's re-entry procedure: re-run one `diff` and read
three of its dispositions against the `LOG.md` lines.

## Notes

- **Precedent, and why this rule is shaped the other way round.** `SH8508` was
  built by *copying* each monthly's HTML into the Sonderheft and editing it to
  match (`issues/SH8508/CLAUDE.md`, "Step 4 — Create HTML from original"). That
  makes the two versions dependent: they agree because one is a copy, so their
  agreement proves nothing and their diff finds no transcription errors. This
  issue transcribes independently — that independence *is* the evidence, and
  it is why `REPRINTS.md` insists nothing be copied over.
- `SH8508` also carries a printed-source credit,
  `<p><strong>Nachdruck aus <a href="../8510/smon.html">64'er 10/85, S. 87</a>.</strong></p>`,
  on 14 articles. This rule neither adds nor removes one: whether SH8601's pages
  print such a credit is a transcription fact owned by the earlier steps. If a
  confirmed reprint here does print one, note it in the report — the user may
  want the convention applied — but do not add it on your own judgement.
- The `ALIGNED:` percentage in the diff header separates the cases cleanly in
  practice (100% for the same text, 4–5% for two unrelated articles), which is
  exactly why it is tempting to use as the confirmation. It is not the
  confirmation. Step 1 is.
