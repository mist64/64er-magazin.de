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

` - ` becomes ` – `. MEASURED across the corpus: the monthlies run **4,864
en/em against 755 hyphen**, so the en dash is house style; the hyphen form is
drift confined to the chain-built Sonderhefte (SH8507 323/15, SH8601 224/16,
SH8602 259/14 before this ruling). Owner, 2026-10-04.

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

Resolve each against the page. Note the contrast with `„` (U+201E, the German
low DOUBLE), which **is** a real quotation mark and folds to `"` in the table
above.

**This step, not later.** A converted dash inside an `<h1>` changes the
headline, and r080 derives the FILENAME from the h1 — so the conversion has to
happen before the split, or whoever does it owns the rename. On SH8602, 158
sites changed and five headlines with them, which renamed five files.

**It also `git add`s the file it rewrote** (`git add "$1" 2>/dev/null || true`).
r000 warns that self-staging scripts plus a shared index have swept files into
the wrong commit three times, and r000's list now names this script too.

**Order matters: fold the curly quotes FIRST, then `''`.** As shipped, `''` → `"`
ran before the curly folding, so `TEDMON'’s` became `TEDMON''s` and a second run
would make it `TEDMON"s` — not idempotent after all. And `''` → `"` is simply
wrong for a mathematical double prime (`P''`, 8612 L2577), which survived only
by that ordering accident. A prime in a formula is legitimate; leave it.

## Verification

After running:

```bash
grep -c '<blockquote'        issues/8607/8607.html   # expect 0
grep -c 'class="intro"'      issues/8607/8607.html   # ≥1
grep -c '<br/>'              issues/8607/8607.html   # 0
grep -c '<br>'               issues/8607/8607.html   # >0
python3 -c "
import sys
s = open(sys.argv[1]).read()
for c in '‘’“”„':
    n = s.count(c)
    if n: print(f'  remaining {c!r}: {n}')
" issues/8607/8607.html                              # nothing reported

# THE DASH CHECK, which this block did not have -- so a script with no dash
# pass at all passed 070 clean on two issues running.
grep -c ' – '              issues/8607/8607.html   # >0
grep -c '‚'                issues/8607/8607.html   # 0 once resolved
```

The en-dash count has no fixed expectation — it depends on the issue — but
**zero is a failure**, and the pass printing `en dashes written=0` on an
issue with body prose means it did not run.

## Notes

- `r080_split.sh`'s embedded splitter already performs the same `&lsquo;`/`&rsquo;`/`&ldquo;`/`&rdquo;`/`''` replacements
  as part of its per-article cleanup. Doing it here too is harmless (step 080
  becomes a no-op for these) and keeps the pre-split HTML uniform if you ever
  want to look at it directly.
- German guillemets `«` `»` `‹` `›` are NOT touched — they're the magazine's
  real quotation marks.
