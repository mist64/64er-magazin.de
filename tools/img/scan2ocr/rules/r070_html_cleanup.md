# 070 — HTML cleanup: blockquote → intro, curly quotes → straight, `<br/>` → `<br>`

**Applies to:** all — house-style substitutions on the converted HTML; no issue-specific input.

**Goal:** turn the Discount output into the project's house style:
- the leading "intro" paragraph in each article comes through as
  `<blockquote><p>…</p></blockquote>`; convert to `<p class="intro">…</p>`
- curly typographic quotes from the OCR become straight ASCII
- `<br/>` (XHTML) becomes `<br>` (HTML5)

German guillemets `«» / »«` are kept — they're the magazine's authentic
quotation marks and stay verbatim.

## Inside `<pre>` these substitutions are CORRECT — do not make this step fence-aware

Steps 040, 050 and 060 all had to be taught to leave fenced code alone, and it
would be easy to conclude that any whole-file pass is wrong inside `<pre>`.
This one is not, and the difference is the whole point:

| the pass | inside `<pre>` | why |
|---|---|---|
| 040 `\*`, 050 `&lt;` | **wrong** | the escape is for Discount's inline parser, which does not run in a fence, so it ships literally |
| 060 `-G` padding | **wrong** | the renderer added it; it was never in the source |
| **070 curly → straight** | **RIGHT** | it restores what the source actually was |

**Ask what the source characters were, not whether it is a code block.** The
C64 character set has exactly ONE quote, `"` at 0x22 — there is no curly quote
in PETSCII — so a `"` or `"` inside a listing is an OCR misreading of a plain
quote and straightening it is a repair, not a corruption. `CHR$(27);"*"` is
what the magazine printed and what a reader must type; `CHR$(27);"*"` would not
run.

MEASURED over the published corpus, inside `<pre>`: **8610 has 0 curly quotes
and 102 straight; 8608 has 0 and 26.** 8609 has 8 curly that survived, and
those are a defect, not a precedent. On 8611 the pass changed 17 quotes on 9
lines inside `<pre>`, every one a BASIC string delimiter.

**"But what if a listing PRINTS a typographic quote?"** It cannot. Every
`<pre>` in this corpus holds PETSCII — a listing, a monitor dump, a screen
transcript — and PETSCII has no curly quote to print. `PRINT "…"` can only
contain characters the machine has. The question is worth asking and the
answer is closed, so this pass needs no exception.

### ANY STEP THAT ADDS TEXT AFTER 070 RUNS 070'S PASSES ON WHAT IT ADDS

070 is a one-time sweep, and the chain does not stop adding text at 070.
Steps 160 and 190 typeset tables and boxes from **fresh OCR**, i.e. text this
step has never seen. MEASURED on SH8604: 160 typeset 81's Texte-Datei `<pre>`
after 070 had run, and **four curly `”` survived into PETSCII text** —
exactly the defect the paragraph above explains cannot be real.

So: **160, 190, 170 and any other step that introduces text apply 070's quote
fold and dash pass to their own additions**, not to the file. It is the same
two substitutions, on a few lines, and it is cheaper than a sweep that has to
re-decide every quote in the issue.

### Where the straightening then goes wrong: the magazine's own name

`64'er` and `128'er` take an **apostrophe**. OCR reads it as a double quote
and this step dutifully straightens that to `"`, giving `64"er` — which looks
like ordinary text, survives a proof-read, and is the highest-frequency proper
noun in the corpus. MEASURED over every published issue: exactly **two**
occurrences, 8610 p9 (shipped that way) and 8611 mid-build. `r310` now fails
HARD on it. Both spellings of the apostrophe pass — the corpus uses ASCII `'`
and U+2019 about equally and neither is wrong.

## Substitutions

| from | to |
|---|---|
| `<blockquote><p>` | `<p class="intro">` |
| `</blockquote>` | *(removed)* |
| `<br/>` | `<br>` |
| `'` (U+2019 right single) | `'` |
| `'` (U+2018 left single) | `'` |
| `"` (U+201D right double) | `"` |
| `"` (U+201C left double) | `"` |
| `„` (U+201E German low double) | `"` |
| `&rsquo;`, `&lsquo;` | `'` |
| `&rdquo;`, `&ldquo;`, `&bdquo;` | `"` |
| `''` (two ASCII apostrophes) | `"` |

## Usage

```bash
tools/img/scan2ocr/rules/r070_html_cleanup.sh issues/8607/8607.html
```

In-place rewrite, idempotent (re-running on a cleaned file is a no-op).

## A SPACED DASH IN BODY TEXT IS AN EN DASH

` - ` becomes a spaced dash. MEASURED across the corpus: the monthlies run
**4,864 en/em against 755 hyphen**, so a dash is house style and the hyphen
form is drift confined to the chain-built Sonderhefte (SH8507 323/15, SH8601
224/16, SH8602 259/14 before this ruling). Owner, 2026-10-04.

### ...AND WHICH DASH IS THE ISSUE'S OWN, BECAUSE THE CORPUS HAS BOTH

That measurement counted **en and em together**. Counted apart, 2026-11-17,
over every published issue (spaced forms only):

| | en | em |
|---|---|---|
| monthlies 8404–8702 | 581 | 4,836 |
| 8610 / 8701 / 8702 | 0 / 0 / 0 | 171 / 90 / 120 |
| Sonderhefte SH8604, SH8606, SH09, SH10 | 296 / 220 / 131 / 298 | 0 / 0 / 0 / 1 |
| corpus | 2,649 | 5,099 |

**The monthlies are em and the recent Sonderhefte are en**, and the split
follows the lineage of the builds, not the printing. Writing en into a monthly
therefore adds a SECOND dash character to a file that already has one: 8702
would have shipped 5 en among 120 em.

So the pass writes the dash **the file itself already sets** — em if the file
holds more spaced em dashes than en, en otherwise, and en when it holds
neither, which is the ruling's default. The report names the choice and the
counts it was made from.

**Which one the corpus should settle on is the owner's ruling, and it is
open.** It is a visible typographic change across fifty published issues, so
nothing sweeps it until he says so. German practice is the spaced
Halbgeviertstrich (en); the monthlies' em dashes come from the OCR and the
model, not from a decision.

**This is in the script now.** It was not: the rule has required the pass
since the SH8602 harvest, `r070_html_cleanup.sh` had no dash substitution and
the Verification had no dash check, so **a run of the script alone passed 070
with 0 en dashes.** SH8603 and SH8604 both had to write the pass by hand in a
sub-agent (119 and 283 conversions), which also means the script's self-`git
add` staged half a step.

**Not converted:** anything inside `<pre>` or `<code>`; a numeric or page RANGE
(`10-20`, `S. 14-16`); a minus sign in a formula; key notation (`CTRL - ↑`);
and a hyphenated compound, which is not spaced anyway.

**What stays a hyphen is decided by the FLANKS, not by a word list.** Three
shapes keep it:

| # | shape | kept |
|---|---|---|
| 1 | **a range or arithmetic** — an operand on BOTH sides: a number, a `$` hex address, a closing paren, or a BASIC numeric FUNCTION about to open one | `COMPARE $C0D6 - $C115`, `(290 - 300)`, `(Zeile 1 - 20)`, `$7A00 - 7F20`, `(PEEK(45) + 256 * PEEK(46)) - 2)`, `($CB00 - 1)`, `1111 - 1024 > 80`, `POKE I,255 - PEEK(I)` |
| 2 | **an indexed item on both sides** — `<Word> <number-or-letter>` | `gleich Satz 1 - Satz 3`, `Mitte Satz 3 - Satz 3`, `vom Raum O - MZ 1` |
| 3 | **program text** — an ALL-CAPS token on both sides | `mit ON - GOTO`, `1 REM * INDEX-MAKER - ERSTELLT`, `»WE WERE DISCUSSING YOU - NOT ME«` |

and it converts `C 64 - Programmieren in Maschinensprache`,
`Vizawrite Classic 128 - Gutes noch besser?`, `nicht vom ROM - das eventuell
benötigt wird`, `C 64 - ACM (e.V.)` and `S. 77 - View BAM`.

**The function list in shape 1 is BASIC's, not a guess at what looks
technical.** With `[A-Z]{2,}\s*\(` instead, the test also kept
`C 64 - ACM (e.V.)`: an acronym before a bracket is indistinguishable from
`PEEK(`.

**NOT skipping `<p class="source">`,** which SH8604 proposed after shape 3 was
missing: measured, that element holds bibliography and credits, and one of its
4 spaced hyphens corpus-wide is `F. Kassera: C 64 - Programmieren in
Maschinensprache`, which has to convert. Shape 3 catches the `INDEX-MAKER`
case that prompted the proposal.

### The fixture, and what the test still cannot settle

20 cases: 13 from the published corpus and the 7 sites where SH8604's hand
pass disagreed with the first version of this test. **That version scored
11/20; this one scores 18/20.** Re-run against SH8604's own fixture
(`<tmp>/scratch_060_070/SH8604.post060.html` in, `SH8604.post070.html` the
hand result) the disagreement went from 14 differing lines to **one**.

The two it still gets wrong are both printed as **suspects**, because the
flank test is a default and not a verdict:

- **a bare number on the right.** A minus in `Es soll die Zahl - 12`, and a
  prose dash in `25 Zeilen - 121 Farbtöne`, `zu bleiben - 1000, 1024 oder 997
  Durchläufe` and `Audio-/Video-Buchse - 6poliger AV-Stecker`. Measured over
  the 21 corpus sites of that shape: ~18 arithmetic, 3 prose. Not decidable
  here.
- **a dash inside a `»…«` quotation**, which is how a program's printed
  output appears in mixed case — SH8604's `»We were discussing you - not me«`
  is Eliza's reply, and PETSCII has one hyphen and no en dash. This is the
  single remaining line in the fixture diff, and the report names it.

- **ARITHMETIC BETWEEN NAMED OPERANDS, which shape 1 does not cover.** Shape 1
  asks for a number, a `$` hex address, a closing paren or a BASIC function on
  both sides. It says nothing about a subtraction written in WORDS, and the
  pass converts it: SH10 `Endadresse – Anfangsadresse` is a minus sign, and 6
  such sites were restored by hand. A capitalised German noun naming an address
  or a length (`Endadresse`, `Anfangsadresse`, `Startadresse`, `Blocklaenge`)
  on both sides is arithmetic, not a dash. Same for key notation that the OCR
  broke: SH10's `<CTRL+ - >` is the page's `←`, and 050 escapes the brackets
  without touching what is inside them.
- **a lowercase word on BOTH sides** — `word - word` in the middle of a
  sentence. This is the shape a speck read as `-` lands in, and neither suspect
  above can see it: they are asked about **bare numbers** and **quotations**
  only. MEASURED on SH09: p012's speck was a suspect by luck (a digit followed
  it); p014's `verwendete - Befehl LOAD` was not a suspect at all, and was
  found only because someone scanned the KEPT list by eye. A real prose dash
  has this shape too, so it is a **suspect, not a verdict** — read it on the
  page. 2 confirmed specks on SH09, and **the issue's other 163 conversions
  were never read against the page, so the rate is unknown, not zero.**

**AND LIST EVERY CONVERSION WITH ITS PAGE, not only the suspects.** Both SH09
specks fell outside every suspect shape the script had, so a report of suspects
alone cannot bound this defect — it can only confirm the shapes already known.
Print each conversion with its page and line so the bulk can be spot-read. A
suspect list is a shortlist; it is not a census.

**The script prints every hyphen it kept and every suspect it converted.** One
further shape, not auto-detected: an OCR-spaced compound —
`FOR..NEXT - Schleife` — converted, where what it wants is the hyphen
**closed** (`FOR..NEXT-Schleife`), not widened. Read the kept list, the
suspect list and the `<h1>` lines before moving on.

## U+201A is never correct here, and is never folded silently

`‚` (U+201A, low-9 single quote) is **not** the German opening quote in this
corpus — the magazine sets `»«`. It is always an OCR error, but of three
different kinds, so no single replacement is right and the script only
**reports** it. MEASURED over 1,825 articles: 38 sites in 14 files.

| reads as | sites |
|---|---|
| a **comma** | `ausnutzen ‚kann`, `LOAD "??Name*" ‚8`, `str(‚dv)`, and `VOLDEF (n(‚n(‚n(,n))))` — where the innermost comma survived as a real one |
| an **opening quote** | `‚Computer Music'`, `die ‚Reihe Taschenbuch Telekommunikation` |
| pure **noise** | `Dollar-‚Zeichen`, `Joystick-‚Modus` |
| **any other punctuation the OCR has no glyph for** — `;` in a `PRINT` list, PETSCII `←` | `PRINT"FEHLER IN SEKTOR: ‚;TAB(20)ES` → `";` (SH8605 p27), `‚A Anfangszeilennummer` → `←A` (SH8605 p168) |

| **the mark plus the NEXT character are ONE glyph** | SH10 p069 `‚881` is `$81` — a low mark followed by an `8`, together read for `$`. The resolution deletes TWO characters and writes one |

**And that fifth kind arrived on the very next issue, as predicted.** It is
different in kind from the four above: those replace the mark, this one
replaces the mark AND the character after it, so a sweep that fixes `‚` in
place cannot express the answer. Read the `‚` with its neighbour before
deciding how many characters the site is.

**The table is what has been SEEN, not what can occur.** SH8605 resolved 38
sites against the page and two were none of the first three kinds — both BASIC
or monitor punctuation that tesseract has no glyph for at all, so it emitted the
nearest low mark. What got them right was the instruction below, not the table;
the table nearly suggested the wrong answer. A fourth kind on the next issue is
expected, not surprising.

Resolve each against the page. Note the contrast with `„` (U+201E, the German
low DOUBLE), which **is** a real quotation mark and folds to `"` in the table
above.

**AND THE SITE CAN BE LARGER THAN THE CHARACTER.** The table gives kinds for
the mark alone, which assumes the text around it is sound. SH09 p003's site sat
in a paragraph that 030 had interleaved with the OCR of a **picture**, a false
`<h3>` among it: no punctuation mark makes that passage right, because the
passage is not the page's.

**A resolved mark inside garbage is not a resolved site.** Where the `‚` sits
inside the OCR of a picture, or of two columns run together, resolve **the
passage** from the page — not the character. And record it, because it reaches
past this step: rewriting that passage changed the issue's `<h3>` count against
030's handover, and nothing else in the chain expects a heading count to move
at 070. Note the new count in `LOG.md`, so 290's hierarchy check and 310's
invariants are read against the right number.

**This step, not later.** A converted dash inside an `<h1>` changes the
headline, and r080 derives the FILENAME from the h1 — so the conversion has to
happen before the split, or whoever does it owns the rename. On SH8602, 158
sites changed and five headlines with them, which renamed five files.

**It also `git add`s the file it rewrote** (`git add "$1" 2>/dev/null || true`).
r000 warns that self-staging scripts plus a shared index have swept files into
the wrong commit three times, and r000's list now names this script too.

### THE STEP IS IDEMPOTENT OVER ITS OWN OUTPUT AND DESTRUCTIVE OVER A HAND FIX

**A re-run undoes every dash restored by hand.** The pass converts a spaced
hyphen between two words to an en dash; a human who put a MINUS back (shape 1b
above, SH10's 6 sites) has written exactly the input the pass converts. So
`r070_html_cleanup.sh` is idempotent over the file IT produced, and
**destructive over the file a reader corrected** — which is the state the file
is in for the rest of the build.

MEASURED on SH10, 2026-11-15: 6 restored minus signs, all 6 re-converted on a
second pass. Its `LOG.md` carries DO NOT RE-RUN 070 for that reason.

**So a hand fix at this step is not finished when the character is right.**
Either:

- record every site in `issues/<ID>/reviewed/070-hand-fixes.txt`, one
  `<line> <before> -> <after> <why>` per entry, so a re-run can re-apply them
  mechanically; or
- do not re-run the step at all, and say so in `LOG.md` loudly enough that a
  later operator fixing something else at 190 or 280 does not re-run it as
  housekeeping.

The first is better, because the second depends on somebody reading a log. And
note which way the risk points: the step is re-run most often exactly when
something ELSE has gone wrong, which is when the hand fixes are already there.

**Order matters: fold the curly quotes FIRST, then `''`.** As shipped, `''` → `"`
ran before the curly folding, so `TEDMON'’s` became `TEDMON''s` and a second run
would make it `TEDMON"s` — not idempotent after all. And `''` → `"` is simply
wrong for a mathematical double prime (`P''`, 8612 L2577), which survived only
by that ordering accident. A prime in a formula is legitimate; leave it.

## Verification

After running:

```bash
# The repo venv, not bare python3 (CLAUDE.md): the step modules import
# numpy, scipy and PIL, which the system python here does not have, so as
# `python3` this check failed at the import rather than checking anything.
PY=${PYTHON:-.venv/bin/python}
grep -c '<blockquote'        issues/8607/8607.html   # expect 0
grep -c 'class="intro"'      issues/8607/8607.html   # ≥1
grep -c '<br/>'              issues/8607/8607.html   # 0
grep -c '<br>'               issues/8607/8607.html   # >0
"$PY" -c "
import sys
s = open(sys.argv[1]).read()
for c in '‘’“”„':
    n = s.count(c)
    if n: print(f'  remaining {c!r}: {n}')
" issues/8607/8607.html                              # nothing reported

# THE DASH CHECK, which this block did not have -- so a script with no dash
# pass at all passed 070 clean on two issues running.
#
# THE INVARIANT IS THE RESIDUE, NOT THE COUNT OF CONVERSIONS.  The script's
# own report line `spaced hyphens left` must read 0: a spaced hyphen still
# standing in prose is the defect, and it is visible whether the pass ran or
# not.  `dashes written` is information, never a gate -- see below.
grep -c '‚'                issues/8607/8607.html   # 0 once resolved
```

**`dashes written=0` is NOT a failure**, and reading it as one is a check that
cannot pass. It said "zero en dashes is a failure" because, on the two issues
where the pass was missing entirely, 0 was the symptom. But an issue whose
prose sets its dashes correctly in the OCR needs no conversion at all, and
8702 is exactly that issue: 0 was the right answer and the gate called it a
failure. What distinguishes "did not run" from "nothing to do" is the residue,
which the script now counts and prints.

## Notes

- `r080_split.sh`'s embedded splitter already performs the same `&lsquo;`/`&rsquo;`/`&ldquo;`/`&rdquo;`/`''` replacements
  as part of its per-article cleanup. Doing it here too is harmless (step 080
  becomes a no-op for these) and keeps the pre-split HTML uniform if you ever
  want to look at it directly.
- German guillemets `«` `»` `‹` `›` are NOT touched — they're the magazine's
  real quotation marks.

## `‚` MUST REACH 0 BEFORE 080, AND A SCRIPT STEP DOES NOT RESOLVE IT (SH8607)

This rule says "resolve each against the page… This step, not later", and r000
classifies 040-070 as editorial-but-scripted. Neither says **who** resolves
them or that the step is not finished until the count is zero. A dispatch
briefed as "mechanical, no word fixes" — which is what "scripted" invites —
correctly stopped with **54 sites still open**, and the step reported done.

**Verification: `grep -c '‚' issues/<ID>/*.html` must be 0 before 080.** The
sites are resolved by a crop-reading pass with evidence per site, not by the
script.

Two more from the same build:

- **The dash pass is not idempotent.** `re.sub` takes non-overlapping matches,
  so a run like ` - - - ` leaves the middle untouched; run it to a fixed point
  or match the run.
- **r050's planted test writes to `/tmp/t50.md`**, against r000's scope rule.
  Write it into the step's own scratch directory.

## THE SELF-`git add` IS NOT THE DEFECT — THE HALF STEP WAS

The script stages the file it rewrote, and that is the chain's convention:
r060, r080 and r100 all do it, and r100 spells out why it stages its own files
and never `git add -u <dir>`. What made it wrong on SH8603 and SH8604 was that
the rule required a dash pass **the script did not perform**, so the file
entered the index with half the step done and the hand pass had to follow it.
That pass is in the script now, so the step stages a finished file.

What remains true, and is r000's law rather than this rule's: while a sibling
session shares the tree, commit by pathspec. A staged file is swept up by a
bare `git commit` whoever staged it.


## THE SPACED DASH FOLLOWS THE ISSUE'S OWN PRINT — THERE IS NO HOUSE STYLE

Delegated by the owner, 2026-11-18: *"dash, you decide."*

**Ruled: each issue takes the dash its own pages print, measured per issue, and
the corpus stays inconsistent because the magazine was.**

MEASURED across the published corpus: the monthlies run **4,836 em against 581
en**; the Sonderhefte run en. That is not drift in our transcription — it is
two different typesetting practices at Markt & Technik, and flattening them to
one character would be us editing the magazine's typography.

So `DASH = EM if n_em > n_en else EN`, measured on the issue in hand, stays
exactly as it is. The same reasoning as *print errors stay as printed* and as
the plate tilt on 8702's page 148: **a corpus-wide inconsistency that the
source really had is not a defect in the archive.**

What WOULD be a defect is an issue whose dash disagrees with its own pages, so
the per-issue measurement is the check and the report line (`dash used`) is how
it is seen. Do not "harmonise" an issue toward its neighbours.
