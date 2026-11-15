# 325 — Read the whole issue, for sense

**Applies to:** all — OCR damage is a property of the scan, not of the issue kind.

**Goal:** find the transcription errors that no pattern can describe, by READING
every word of every article as a reader would, and confirming each suspicion
against the printed page.

---

## The dump cross-checker: what it reads, and what it does not

`r325_dump_crosscheck.py <issue-dir>` disassembles each printed byte run with
da65 and compares it to the printed mnemonic. It reads the **monitor-dump**
form (`0c047  ce 46 c0  dec $c046`), with or without a comment column.

Two forms it does NOT read, so do not take its silence as coverage:

- **assembler source with no byte column** (`a 0b30 jsr $795c ;CHKKOM`). There
  are no bytes, so there is nothing to cross-check. It skips these rather than
  reporting them, which it used to do six times per issue to no purpose.
- **the hex-row form** (`a599 : 00 06 … de`, nine columns). 132 rows of it in
  8611 alone, all unread. If you are tempted to treat the last column as a line
  checksum: eight algorithms were tried against those 132 rows — plain sum,
  sum with the address bytes, sum with carry, XOR, XOR with the address,
  one's complement — and **none scored above chance**. Either it is data, or
  the algorithm is something else. Do not guess; read the page.

Expect a **small** number of findings: 8611 2, SH8601 9, 8609 and 8610 0. A
flood means a form it cannot parse, not an issue full of errors.

## A DUMP WITH A DISK WITNESS IS VERIFIED BY COMPARISON, NOT BY EYE

**Where our hand-typed `<pre>` can be compared byte for byte against the
program on the disk, that comparison IS the coverage, and reading the rows with
an eye adds nothing.** The disk file is a better witness than a reader: it is
exact, it is complete, and it costs no image budget (r000, *AN AGENT'S PICTURES
RUN OUT*). Crops are for the rows that have no such witness.

MEASURED on SH09, 2026-11-14: article 30's Listing 21 is 445 rows, of which
**365 were never opened as images** — their bytes verified against the disk by
the step-120 comparison, their columns measured by arithmetic. The eye went to
the 80 rows that are not covered that way, and to Tabelle 5 of article 79,
~500 cells with no witness at all.

**Say it exactly in the coverage line, and never as "read in full".** The form
is *"N rows not read by eye; bytes verified against `prg/<name>` by <which
check>; columns measured at <pitch>"* — three different claims with three
different warrants. A coverage statement that rounds this to "read" is the
false-displayed-list failure in a politer costume, and §33 is what that costs.

**This does not reach a dump with NO disk file**, which is most of them, nor a
table of numbers, nor anything whose value is the glyph rather than the byte.
And it does not excuse the ROW STRUCTURE: how many rows there are, where they
break and what sits in the comment column are still the page's, and still
arithmetic (*A SPACING QUESTION IS ARITHMETIC*).

## Why this exists: every other pass is blind in the same way

By the time this step runs, the issue has been through r280 (word cleanup),
r290 (headings) and **r330's Step 0** (the reprint leads, so you know which
articles have a second independent witness). The three end-of-issue gates —
r310 (invariants), r320 (omission) and **r330's body** — run AFTER this step,
because this step changes prose and all three reason over finished text; see
r000, *THE RUN ORDER AT THE END OF AN ISSUE IS NOT THE NUMERIC ORDER*.

This sentence used to list all five as already run. Together with r330's old
*"Run order — LAST, after rule 300"* heading it formed a circle, and SH8608
resolved it the only way the two texts allowed: it ran 330 before 325, and
threw the partial run away.

Every one of those passes, before this step or after it, is **pattern-driven or
diff-driven**:

| pass | what it does | what it cannot see |
|---|---|---|
| r280 | substitutes from a fixed table of confusions | anything not on the table |
| a glyph sweep | greps for `©`, `%`, `$`, unbalanced `»«`, `O`/`0`, `l`/`1` | anything nobody thought to grep |
| r310 | regex invariants over the markup | prose that is valid HTML |
| r320 | counts blocks kept against blocks dropped | whether the kept text is *right* |
| r330 | diffs a reprint against its original | the articles with no reprint, and errors BOTH printings share |

They confirm suspicions. They cannot have suspicions of their own.

MEASURED on SH8601: after all of the above had run and the issue was believed
finished, the owner opened an article and read
`<h2>Die Befehle zur $priteprogrammierung</h2>`. Valid HTML, plausible shape,
wrong — and invisible to every gate. That is the class this step is for.

**And a scope note in a brief is a scope note in the result.** SH8601's glyph
sweep was told "do not touch headings" — meaning *do not restructure them* —
and it read that as *do not look there*. The 247 headings went unswept, which is
exactly where the example above was hiding. **Say what to READ separately from
what to EDIT.**

## What is in scope

Everything in the article except listings:

- every `<p>`, including `<p class="intro">` and `<p class="source">`;
- **every heading, `<h1>`–`<h6>`** — see above;
- `<figcaption>`, `<aside>`, `<address class="author">`, and **table cells** —
  a wrong digit in a register table reads as plausible and is wrong;
- screen dumps, monitor dumps and command syntax that sit in `<p>` rather than
  `<pre>` — they are prose as far as the markup is concerned.

**`<pre>` — ONLY THE DISK'S IS OUT OF SCOPE.** The distinction is the attribute,
not the tag:

| | source | proofread? |
|---|---|---|
| `<pre data-filename="…">` | the generator fills it from `prg/` | **no** — the disk owns it |
| `<pre>` with text in the file | somebody typed it from the page | **YES — it is transcription like any other** |

MEASURED on SH8601: 31 blocks are disk-backed and **68 are hand transcriptions**
— 44 of them in one article. They are the monitor dumps, screen dumps and short
code examples the magazine sets INSIDE the body text, and no listing is missing
on their account: every `Listing N` the articles cite has its own figure.

**The dump cross-checker reads FEWER forms than it claims, and silence is not
coverage.** Besides the two unread forms it names, it also skips SMON
`>, C000 A9 C0 LDA #$C0`, the monitor `.,  081A  A9 CC  LDA #$CC`, and
assembler listings with line-number / location / code columns — 95 instruction
rows in one half of SH8602 alone. **It must print how many rows it PARSED**, so
that "0 parsed" reads differently from "0 wrong". (The same defect as r320's
dropped-listings companion, which reported a clean 0 on two issues while
examining nothing.)

**AND IT STILL DOES NOT.** MEASURED on SH8608: `r325_dump_crosscheck.py`
printed one UNPARSEABLE line and nothing else, and counted with its own LINE
regex it had parsed **0 of the 164** hand-typed dump rows in article 67 —
every dump there is TEDMON's `>addr bb bb … :` form, which it does not read.
That is the commonest dump form in a C 16 issue, so on such an issue the
checker currently examines nothing and says so only by being quiet. Reader E
had to check those dumps another way (Bild 2 byte for byte against the Plus/4
BASIC ROM at $8180-$81B7, and the H-command results against the ROM).

So until it prints `parsed N of M` and reads the `>` row form, **do not treat
its silence as coverage**: count the hand-typed dump rows yourself and say in
the report how many the checker actually read. Its recommended `pdftotext` locator also does not exist
before step 006.

**In a hand-typed `<pre>`, LINE STRUCTURE is in scope.** Most of the damage
there is not word-level at all: lines joined together, two lines run into one,
a line break inserted where the print has none. "Word-level substitutions only"
does not obviously permit re-breaking them, and it must — on 8612 a hand-typed
listing had **21 printed lines missing** and every other gate was green.

Two things that can only be checked mechanically:

- **Monospace spacing, by glyph column — and the method is MEASURED, not
  estimated.** `TAB(15) "B"` against `TAB(15)  "B"` is invisible in prose
  reading and obvious when the columns are lined up against the crop. "Compare
  column positions" left the how open, and eye estimates were wrong more than
  once on SH8604. Get the **glyph pitch** instead: either the x-step between
  consecutive tesseract character boxes on the line, or the spacing of ink
  segments in a column-sum profile of the crop. MEASURED on SH8604's
  typewriter face: **~41.6 px at 600 dpi**. With the pitch in hand, a column
  index is `round((x - x0) / pitch)` and a missing space is arithmetic.
- **A run of repeated characters must be COUNTED.** Two agents disagreed 20
  against 21 on a run of colons in one BASIC line. Count them in the crop
  programmatically; do not eyeball a run of more than about four.

**A brief that says "skip `<pre>`" therefore leaves the least-checked text in the
issue unchecked.** Mine did, and the blocks it excused read `1da` for `lda`,
`#804` for `#$04`, `bp1` for `bpl`, `a 00645` for `a 00b45`. Say
"skip `<pre data-filename>`" instead.

### An assembler dump CHECKS ITSELF — use that, do not eyeball hex

A wrong byte is indistinguishable from a right one by reading. But a monitor
dump carries the same information twice, so the two halves can be cross-checked
mechanically before anyone looks at a page:

```
a 00b40  a2 04     ldx #$04
  ^addr  ^bytes    ^mnemonic + operand
```

1. **The bytes encode the mnemonic.** Disassemble `a2 04` — it must be
   `ldx #$04`. A mismatch is either OCR damage or a magazine error, and either
   way it is a candidate that a reader would never have spotted.
2. **Addresses advance by instruction length.** `a 00b40` + 2 bytes must be
   followed by `a 00b42`. A gap or a repeat localises the damage to one line.

Run both over every dump, THEN take the survivors to the page. This is how a
hex pass reaches accuracy that reading cannot: the machine finds the candidates,
and vision decides each one — the same division of labour as everywhere else in
this chain, applied to material where human reading is weakest.



## What to look for

Read for MEANING, not for patterns. **If a sentence makes you re-read it, that
is the signal.** The recurring shapes, as a prompt rather than a checklist:

- a word that is neither German nor a product/technical term — `$priteprogrammierung`,
  `Tarthau<steine`, `wenri`;
- lost or inserted word spaces — `StringinFAC`, `damitderZ80`, `Zwischenkabelangeschlossen`;
- a glyph substituted for a plausible neighbour — `©` for C, `%` for `?«`,
  `$` for S, `l` for 1, `O` for 0, `»` read as s;
- a sentence that does not parse, a clause that contradicts itself, a number
  that cannot be right in its context;
- a heading that is really a paragraph tail, or that has swallowed listing text;
- hex addresses and figures mangled — `$8 A27`, `$lfff`, `154l`.

## ALWAYS VERIFY WITH VISION

**Every candidate, without exception**, before it is changed:

1. **Locate** — the block index at `<tmp>/ocr/out/blocks/pNNN.txt` gives bboxes;
   the article's pages are in its `64er.pages` meta. For a precise line,
   `pdftotext -f N -l N -bbox <issue pdf>` gives word boxes (PDF pt × 600/72 =
   600 dpi px). Use it **only as a locator**.
2. **Crop and LOOK** — `masters600/NNN.png` at that box, read with your own
   eyes, magnified where the glyph is ambiguous. SH8601 needed 200–400% to tell
   a digit `1` from a lower-case `l`, and a wide round capital `O` from a zero.
3. **Decide from what you saw.** Never from the PDF's text layer: it is raw
   tesseract, i.e. the thing being checked wearing a different hat — see r000,
   *the PDF's text layer is a CANDIDATE SOURCE, not authority*.

Nothing here is unverifiable. Every word is on a page available at 600 dpi; the
only genuine exception is print too damaged to read, which SH8601 never once
produced.

## TYPOS IN PRINT REMAIN TYPOS IN THE HTML

This is the whole discipline of the step, and the reason a reading pass is
dangerous without it: a reader who has just found three real errors is primed to
"fix" the fourth thing that looks wrong.

MEASURED on SH8601, all verified at magnification and all KEPT:

```
Beipielprogramm                p090      nebenanderliegene       8512 p78
80x200 = 1600 Byte             p054      »MANDELBROT1»           p046
zwischen $0 uns $1fff          p060      »Punkt löschen»         p054
Listing 1. Alle »ALLE SPRITES« p043      «SPRITE 4,1,6,1,1,0,0«  p103
»Rescue on Fractalus,          p106      dem »%«-Zeichen         p081
Warte- / stehenden             p104      GRAFIK (for GRAPHIC)    p054
```

You are finding OUR misreadings of the page. You are never correcting the
magazine. When the page prints the odd thing, record it as printed and move on.

## A MAGAZINE ERROR THAT MISLEADS IS A FUTURETEUFELCHEN CANDIDATE — RECORD IT

*Typos in print remain typos in the HTML* is about the TEXT, and it does not
change. But where the page is not merely mis-set but actually MISLEADING — an
arithmetic result that is wrong, a cross-reference to something that does not
exist, a figure numbered against its own caption — the archive has a place to
say so beside the text without altering it: `<aside class="futureteufelchen">`,
see r300.

**You do not add one.** Reading is how candidates are found. Record the
passage, what appears wrong, and the crop — then move on. A list of candidates
is a report, never a worklist.

**THE OWNER'S DEFAULT IS NO FUTURETEUFELCHEN — and that is now stated, because
not stating it turned every candidate into a question.** Print errors stay as
printed, recorded in LOG.md only, and they **do not go on the owner decision list**.
MEASURED on SH8605: the nine r325 readers recorded 66 candidates (D21–D86), the
hand-over report listed every one, and the owner was asked them one at a time —
answering "leave it" to D20 through D30 and then: *"did you learn yet"* (owner,
2026-10-08).

**The one standing exception:** a REPRINT whose original carried a printed
erratum (a Fehlerteufelchen) that the reprint lacks. That one gets a
Futureteufelchen, saying which erratum is missing here and what it says — check
every reprint in `REPRINTS.md` against its original's errata. Owner, 2026-10-07:
*"if it's a reprint and original has an erratum that is missing in the reprint,
make it a Futureteufelchen."*

So "record them and stop" means record them IN THE LOG and stop. A candidate
list is still a report — it is just not a report the owner is asked to read.

**FIRST, RE-READ THE GLYPHS THE CLAIM RESTS ON. RUNNING IT PROVES NOTHING
ABOUT THE PRINT.** SH8604's p71 `51103 IF 01<>0 AND 02<>0 …` was reported as
printed with digit zeros, and "confirmed" by running the line as transcribed in
x64sc, where it misbehaves — which is exactly what you would expect, because
the transcription was wrong. The print is `O1`/`O2` and correct: on the crop
at 2-3× the letter measures 113-115 px against 106-107 px for the digits on
the same line, and is visibly rounder. The signal was there all along — the
raw OCR read `01<>0O`, a digit AND a letter at one position.

So, before a candidate goes on the list:

- **Re-read every glyph the claim depends on, at ≥ 3× on the crop**, and
  **measure** the ambiguous ones — `O` vs `0`, `1` vs `l` vs `I`, `S` vs `$`,
  `8` vs `B` — against known instances of both on the SAME LINE, where the
  face and the exposure are the same.
- **A candidate whose only evidence is our own transcription is a candidate
  OCR ERROR first.** Running the transcribed text shows that THAT TEXT fails;
  it says nothing about what the page prints. Where the two readings behave
  differently, the one that behaves as the article DESCRIBES is the likelier
  print.

### "THE GLYPHS ARE IDENTICAL" MEANS THE GLYPH CANNOT DECIDE — NOT THAT THE FACT IS UNKNOWN

Owner, 2026-10-07: *"you can research the truth."*

When two readings look the same on the paper, that is a statement about the
ink, and it is where the work starts rather than where it stops. **Before
recording anything as unresolvable, go through these.** They are ordered by
cost, and each has settled a real case:

1. **Improve the evidence.** A low-resolution original is not a dead end: a
   150 ppi PDF page rendered at 300 dpi, greyscale, autocontrast, cropped at
   3-6x is legible. It settled 7 claims against 8404's Tabelle 1 — and
   REFUTED all 7. See r330, *no 2400 dpi scan is not a dead end*.
2. **Look at the SERIES the item belongs to.** 8407's Bild 3 pinout has a
   `D0`/`DO` ambiguity, and the same table lists `D1` through `D7`. A
   Centronics connector's data lines are D0-D7. The series decides; the glyph
   never had to.
3. **Look for a REDUNDANT ENCODING in the artefact itself.** 8607's ESC/P
   table prints each command beside its decimal code, so the table checks
   itself: *Linken Rand setzen* is `ESC l`, because the row's own code cannot
   be 27 49 when `ESC 1` already is. **49 of its 55 rows are self-consistent,
   which is also what makes the other 6 findable** — see below.
4. **Consult the external standard.** ESC/P, ASCII, BASIC syntax, a PETSCII
   table, a connector pinout. These are published and knowable, and the
   magazine was describing them rather than inventing them.

   **But CITE it, do not recall it.** Routes 2 and 3 are self-validating: the
   series and the redundant encoding are both ON THE PAGE, so the check is
   cheap, certain and repeatable by the next reader. Route 4 is a different
   confidence class — it rests on what you believe the standard says, and
   nothing in the artefact contradicts you if you are wrong. Use it for ONE
   doubt you can state and support, with the source named. **Do not sweep a
   whole table against a standard you are reciting from memory**: 122 rows of
   recalled semantics will produce confident findings at some unknown error
   rate, and there is no blind second reading for "is this what ESC/P says".
   Without a citable reference to hand, the honest outcome is to leave the
   remaining rows alone and say so.
5. **Let the LANGUAGE decide.** SH8505's `ln solchen oder ähnlichen Fällen`
   is optically undecidable — measured, the bar is h57 against a known `l` at
   h58, and cap-height equals ascender-height in that face — but `ln` is not a
   German word and the sentence opens a paragraph. Applied on that basis, and
   recorded as linguistic rather than optical evidence.

**Record WHICH of these you tried.** "Unresolvable" with nothing behind it is
a guess wearing a disposition's clothes. And say which kind of evidence
settled it, because a reader needs to know whether they are being told about
the paper or about ESC/P.

### A SELF-CHECKING TABLE CHECKS THE WHOLE TABLE, NOT JUST YOUR ONE DOUBT

Once you find that an artefact carries a redundant encoding, run it over
EVERY row, not only the cell you were asked about. MEASURED on 8607's ESC/P
table: checking all 55 commands against their printed decimal codes confirmed
49 and found **6 disagreements** — `ESC !` 27 94 (should be 33), `ESC 2` 27 60
(50), `ESC l` 27 49 (108), `ESC \` 27 47 (92), `ESC %` 27 97 (37), `ESC u`
27 115 (117). Three of the six have the shape of an OCR digit slip (6/5, 9/3,
5/7) and three do not, so some are probably ours and some probably the
magazine's — which the scan decides, and which is the difference between a
THEIRS finding and a Futureteufelchen candidate.

The cost was one pass over a table that was already open.

Two things make that report decidable, and both are the reporter's job:

- **Say what a reader who typed it in would EXPERIENCE**, and order the list by
  that. "The print is wrong" cannot be ruled on; "this `+` should be `=`, so the
  SYS-line trick silently produces nothing" can. A wrong digit that is harmless
  in the common case and fatal in another belongs low on the list, with both
  halves stated.
- **Say whether that impact was REASONED or RUN.** An impact worked out from
  the arithmetic is worth having and is not the same claim as one seen in an
  emulator — r000's patching section has the petcat/x64sc procedure and the
  same distinction. Mark each row, and never let "would crash" stand unmarked
  when nothing was executed.

## A SPACING QUESTION IS ARITHMETIC, AND ARITHMETIC NEEDS NO PICTURE

**How many spaces stand between two tokens of a monospaced listing is a
measurement, not a reading, and the cheapest way to answer it is not to look at
all.** Take the glyph x-positions out of `labels.json` / `blocks/pNNN.txt`, or
an ink-column profile of the crop, derive the pitch from two reference glyphs
ON OR BESIDE THE LINE IN QUESTION, and divide. The answer is a column number,
and it carries its own proof.

MEASURED on SH09, 2026-11-14 — six sites settled this way in the r325 triage,
**none of them opened as an image**:

| site | the arithmetic |
|---|---|
| `64` p77 `LDY #>ALT ;POINTER` | pitch 44.8 px from `LDA`@438 to `;DEM`@1065 = 14 cols. `#`/`>` start at 616/697 on both lines; `A` of ALT at 766 on the LDA line, 808 on the LDY line = **+42 px = one cell**. `;POINTER`@1066 = `;DEM`@1065, so one space fewer after ALT |
| `64` p71 `JMP LOOP1` | pitch 41 px from the `...` dots at 2795/2836/2877; mnemonics at 2782/2783, operand `L` at 2949 (LOOP2) against 2990 (LOOP1) = **+41 px = one extra cell** |
| `64` p76 asterisk box | 19 asterisk runs after `;` at 41.5 px pitch, top row 2513..3260, bottom 2517..3264; the closing `*` at 3259 = col 19 — **counted, not eyeballed**, and the box was one star too wide |
| `30` p43 `03C1 4C 08 AF JMP` | pitch 51.8 px; address-to-mnemonic offset 726 px on 03C1 against 725 and 726 on its neighbours — JMP sits in the shared mnemonic column |
| `111` p111/p112 Bild 1 | pitch ~41.6 px from `$C056`@286 to `QUICKSORT`@619 = 8 cells; descriptions at +327..332 px = **8 cells, so column 16, not 15** — twenty-odd lines of a reference table corrected from one pitch and two anchors |

**Why this beats looking, on both counts.** It answers what the eye cannot:
SH8607 recorded these sites as *undecidable* because the face drifts 36-44 px
across a line, and a drifting pitch defeats a GLOBAL constant — not a local
one. Two anchors beside the site give the pitch where the site is. And it
costs no image budget at all (r000, *AN AGENT'S PICTURES RUN OUT*), so it does
not compete with the crops that genuinely need an eye.

**Record the arithmetic, not the verdict.** Every line above carries its pitch,
its anchors and its offsets, so the next build can check the sum instead of
re-reading the page. A bare "col 16" would be a claim; the numbers are
evidence.

### WHERE THE ARITHMETIC BREAKS: A GLYPH WIDER THAN ITS CELL

**`#`, `<` and `>` in the typewriter face do not advance one cell, and no
whole-cell sum across one of them is valid.** MEASURED on SH09 p077,
2026-11-14, by ink columns on the `LDA #<ALT` / `LDY #> ALT` pair the triage
settled:

| quantity | measurement |
|---|---|
| ink width of `#`, `<`, `>` | **53, 53, 52 px** |
| advance `#` -> next glyph | **80 and 81 px** = 1.93 cells at the 41.5 px pitch |
| advance `<` -> `ALT` | 69 px = **1.66 cells** |
| advance `>` -> `ALT` | 110 px = **2.65 cells** |

**Two readers reported this differently and both were right**: one said "two
cells" (the ADVANCE, 80 px), one said "52-53 px" (the INK). They are different
quantities — the ink is what you see, the advance is what moves the grid — and
for these glyphs neither is a whole cell.

**So never compute an absolute column across a wide glyph. Compare like with
like instead.** On that pair every shared landmark agrees to the pixel —
mnemonic at 437/438, `#` at 616/616, `<`/`>` at 696/697, `;` at 1065/1065 — and
only `ALT` moves, 765 against 807. **+42 px = one cell = one space.** Exact,
and it never counts the wide glyphs at all. That is the method: find the same
construct on the same page, align the landmarks, read the difference.

**With no comparable line the site is undecidable: keep the transcription and
record it.** SH09's `GET#1 ... IF ST<>64` on p040 is one, correctly left alone
with an erratum. *Undecidable* now has exactly one meaning — **no legible
comparison** — and is no longer a verdict on a drifting face.

**It does NOT replace vision for what a glyph IS** — a comma against a full
stop, `O` against `0`, a dust speck against a colon. Those are shape questions
and they need the picture. Pitch arithmetic answers WHERE, never WHAT.

## A LISTING'S COLUMNS ARE THE PAGE'S, NOT A HOUSE STYLE — BUT ITS LINE BREAKS ARE NOT

**Re-lay a hand-typed listing to the columns the print sets.** This is not a
new rule; it is r000's *CONSISTENCY WITH THE PAGE BEATS CONSISTENCY WITH
ITSELF* applied where it is easiest to forget: *"Match the page, site by site;
do not normalise."*

The machine-name exception does not reach here, twice over. It exists only
because "match the page" had **no answer to give** — a thin gap measuring
neither a closed pair nor a word space — whereas a monospaced listing answers
exactly, by arithmetic, at a measured pitch (see *A SPACING QUESTION IS
ARITHMETIC*). And that exception explicitly excludes anything inside `<pre>` or
`<code>`, "where the string is typed in by a reader".

MEASURED on SH09, 2026-11-14: article 64's p068 prints **two spaces after the
address and the comment at column 22**, at 41.5 px pitch, where our HTML had
one space and column 18 — normalised consistently, and consistently unlike the
page.

**AND THE REPRINT IS NOT THE AUTHORITY FOR ITS OWN LAYOUT EITHER.** SH8608/79
is the earlier printing of that article and our HTML of it collapses the
columns the same way. Its page does not: SH8608 p80 prints `LDA #$01`, a wide
gap, then `;LOGISCHE FILENUMMER 1`. **So the reprint's HTML was evidence of our
habit, not of the paper**, and a reader who cites it is citing us. MEASURED
over the corpus: of 250 assembler `<pre>` blocks, **15 collapse every comment
to one space, in four issues** (8601, SH8601, SH8602, SH8608) — a 6 % residue,
so re-laying to the page is also what the other 235 already do. CORPUS_QUEUE 12
holds the fifteen.

**Expect r330 to flag the divergence and do NOT answer it by re-normalising.**
SH09 matching its own page while SH8608's HTML does not is the correct state
until the queue item is run; record it as a known whitespace divergence with
the pitch measurement beside it.

### The print's LINE BREAKS are not re-laid

Only the gaps **within** a line are the print's. Text too long for the column
wraps onto a continuation line — SH8608 p80's `;SEKUNDÄRADRESSE 1 = DATEN AUF
BAND` / `SCHREIBEN` — and that break is the column's width, not the listing's
structure.

**The test is what the text IS, not what it is called.** Prose inside the box
joins with a space: a comment, and equally **a listing's title or a note set
inside its frame**, which SH09's reader M joined on Listings 9, 10 and 12 and
was right to — the rule said "comment" only because a comment was the case in
front of me, and a title broken at the box width is the same break for the same
reason. Code joins without a space.

### BUT A CONTINUATION'S INDENT CAN BE A CHOICE, AND THEN IT STAYS

**Join a continuation whose indent carries no information — one sitting in the
column the wrapped text already occupies. Keep it, as its own line, where the
print puts it somewhere the wrap would not have gone**, because then the indent
is a decision about meaning and joining destroys it. The test is arithmetic, so
it is decidable at every site.

MEASURED on SH09's article 111, Bild 1 — a hand-typed memory map, both lines in
the same `<pre>`, both broken at the box width, and they go opposite ways:

| line | measured | verdict |
|---|---|---|
| `Mit Anfangsadresse DIM's` / `vergleichen` | `vergleichen` sits at **col 16**, the column every description in the block starts at | **join** — the wrap had nowhere else to go |
| `SYNTAX: SYS 49164, (linkes Grenzelement),` / `(rechtes Grenzelement)` | `(rechtes` starts at **x=3453, exactly under `(linkes` at 3453** — col 19, which is neither the description column nor the margin | **keep** — the typist aligned the second argument under the first |

The wrap was forced in both; **the indent was chosen in only one**, and that is
the whole distinction. A continuation at the running column is overflow. A
continuation parked under a particular word is the same kind of statement as an
assembler listing's comment column, which this rule already preserves.

SH8608 p80's `;SEKUNDÄRADRESSE 1 = DATEN AUF BAND` / `SCHREIBEN` is the first
kind: `SCHREIBEN` sits in the comment column, so it joins. That earlier example
is unchanged, and this test is why. The standing
convention stands: **no column-wrap `<br>`**. A re-lay that reproduced the
print's line breaks would import this copy's column width into a medium that
has none.

## Granularity

Word-level substitutions only — r000's *OCR cleanup granularity* applies in
full. Do not rewrite sentences, do not "improve" wording, do not modernise
spelling (`daß`, `muß`, `Adreß` stay).

## How to run it

Split the issue by WORD COUNT, not by article count, and give each reader three
to five articles of roughly equal weight — SH8601's 29 articles are 80,242
prose words, which balanced into seven groups of ~11,400. Tell each reader what
is peculiar about its articles: a reference table of ROM entry points, a
masthead of names and addresses, a bibliography, an ISBN list, a crossword. That
is where the errors nothing else can see actually live.

Readers must work in small steps and report as they go. A reader that goes
silent for a long stretch gets killed by the watchdog and loses its work.

**AND SPLIT BY CROPS BEFORE WORD COUNT, BECAUSE THE CROPS ARE WHAT RUN OUT.**
A reader gets about fifty images in its whole life (r000, *A SUB-AGENT GETS
ABOUT FIFTY PICTURES*), so the unit of planning is **forty crops per reader**,
not an article and not a word count. SH09 needed ~762 crops for 168 pages —
nineteen reader-lives, which is why seven long-lived readers could not do it at
any price.

So this step runs in **waves**:

1. Estimate the crops: the sites a reader must see with its own eyes, not the
   pages. Divide by forty. That is the number of readers, and they run in
   waves of a few at a time, not all at once.
2. Each reader reads a crop ONCE, writes its reading down immediately, and
   never opens that crop again. The image is a witness, not storage.
3. At forty crops, or at the first `[media removed]`, the reader **stops
   looking**, finishes the readings it already has, and hands back a list of
   what it did not see. That list is the next wave's input, not a failure.
4. The orchestrator commits each wave's yield before starting the next, and
   reconciles `crops read / crops seen` per reader. Any gap means the cap bit.
   **THESE COMMITS ARE LOCAL AND DO NOT BREACH THE ONE-COMMIT RULE.** SH10's
   builder read them as a conflict with the owner's standing order — one
   squashed commit per issue, permission asked every time — and held the
   yields as uncommitted files instead. There is no conflict: the squash is
   built from `origin/main` in a throwaway worktree, so local commits never
   reach him. SH09 had **103 of them and pushed as ONE**. The order governs
   the PUSH; committing as you go is what protects the work, and 80,851 words
   across 8 readers is many hours to hold in an uncommitted directory.
   **COMMIT BY PATHSPEC, `issues/<ID>` only** — control commits rule files
   into the same working tree continuously, and a bare `git commit` sweeps
   them into the wave (r000, *Commit & staging discipline*).

**The yield goes to `issues/<ID>/reviewed/r325-<reader>.txt` and is committed
as each article finishes.** Not to `LOG.md`: git does not track it, and SH09
put 723 KB of reader output there, where a killed reader lost all of it. LOG.md
keeps the coverage statement and the narrative; the FIX, REJECT and
PRINT-ERROR tables are evidence and live in `reviewed/`.

## Verification

1. Every fix carries `was -> is`, the page, and the crop it was read from.
2. Every REJECTED candidate is recorded too, with the same evidence — the
   rejects are how the next run knows what the magazine really prints, and
   SH8601's reject list is the table above.
3. Each reader states its honest coverage: what it read in full, and what (if
   anything) it skimmed.
3b. **Each reader reports `crops read / crops actually seen`, and the list of
   crops it did not see.** A report without those two numbers is not finished:
   they are the only way the orchestrator can tell a reader that looked from
   one that was handed blanks. Reader-seen must equal reader-read, or the
   remainder is re-dispatched to a FRESH reader, never retried in place.
4. `generate.py --issues <ID> --future --join` exits 0.

## Recorded in LOG.md

The fix table, the reject table, and the coverage statement, per reader.

## FOUR GAPS MET BY NINE READERS ON SH8607

1. **Verification 4 cannot pass before the owner's `title.png` exists.**
   `generate.py --issues <ID> --future --join` stops on `FileNotFoundError`.
   Every reader reported it. **Run it on a scratch copy** with
   `<tmp>/title_source_150.png` as the stand-in — never copied into `issues/`.
   The full recipe is in r000's end gate.
2. **The locator advice names `pdftotext -bbox <issue pdf>`, which does not
   exist during the build** (r000: the page image is `masters600`). Readers
   used `labels.json` `bbox_frac`. **Name that instead.**
3. **"Monospace spacing, by glyph column" assumes a fixed pitch.** SH8607's
   typewriter-like faces drift 36-44 px, so `""` vs `" "` is undecidable at
   several sites. **Say the fallback: keep the transcription and record the
   site as undecidable.** Do not let a reader invent a space from a drifting
   column.

   > **SUPERSEDED, 2026-11-14 — MEASURE THE PITCH LOCALLY AND IT IS DECIDABLE.**
   > See *A SPACING QUESTION IS ARITHMETIC* below. The drift defeats a GLOBAL
   > pitch, not a measurement; take two reference glyphs beside the site and
   > the column falls out. "Undecidable" is now the fallback when no reference
   > pair is legible, not the answer to a drifting face.
4. **An image can fail to load silently for a sub-agent** ("media removed", a
   request limit). Two readers first believed they had checked pages they had
   never seen; one said so, and a second reader re-did them with vision.
   **In the 325 brief: for every crop you rely on, confirm the image actually
   loaded, and report the pages you could not see.**

   > **ERRATUM, 2026-11-14 — THE REMEDY WAS WORSE THAN THE FAULT.** SH09's
   > brief turned this into *"Re-read later, or list the page as not seen"*,
   > and seven readers spent **445 M input-token equivalents in 107 minutes**
   > -- 2.5x a whole normal build -- re-reading pictures that could never
   > arrive: **17,107 crop reads
   > over 762 crops, about 98 % of them blank, 56 edits to show for it**, and
   > the step unfinished when the weekly limit killed them. The cap is on the
   > REQUEST and a request only grows, so retrying is the one action guaranteed
   > not to work. **`[media removed]` is a STOP, not a retry** — see r000,
   > *A SUB-AGENT GETS ABOUT FIFTY PICTURES*, which is binding here and
   > everywhere else. The diagnosis above stands; only the remedy was wrong.

**Also, for r280 Pass 3:** step 010 joins a line break after `Low/` or `-/`
**with a space** — 14 sites in SH8607's Memory Map ("Low-/ High", "VC 20/ C 64").
A space after `/` before a capital is a line-break join; the print sets `x/Y`
closed mid-line.
