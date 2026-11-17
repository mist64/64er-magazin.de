# 300 — Apply cross-issue Fehlerteufelchen errata to this issue's articles

> **EVERY FUTURETEUFELCHEN NEEDS THE OWNER'S EXPLICIT OK BEFORE IT SHIPS.**
> Owner, 2026-11-15, on SH10: *"they ALWAYS need to be OKed by me. record
> this."* Drafting one is never the last step. The entry goes to him with its
> TEXT and its GROUNDS — which of the allowed cases it is, and the evidence —
> and it stays out of the published file until he says yes. SH10 had two
> written into the HTML on control's rulings alone and had to put them to him
> afterwards, which is the wrong order: an entry a reader could already have
> seen is not a proposal.
>
> This applies to BOTH allowed cases — our own repair or divergence, and a
> reprint missing its original's erratum. Neither is self-approving.
> 
> **This is OWNER INPUT 4** (r000, *THE SHAPE OF A BUILD*): the candidate
> list goes out with the crop worklist, each candidate carries its page, our
> divergence and the question in one sentence, they are asked ONE AT A TIME,
> and the HTML is blocked until every answer is back. A build that found none
> says so -- "0 Futureteufelchen candidates" -- because silence does not
> distinguish none-found from not-looked.

**Applies to:** all — **this is a correction to the spec's first pass.** The rule does not build a Fehlerteufelchen rubric — it applies errata printed in LATER monthlies to THIS issue's articles, and later monthlies corrected Sonderheft articles too. 26 articles across `SH8501`-`SH8508` already carry `<aside class="fehlerteufelchen">`, and the rule's own step 1 already routes `Sonderheft N/YY → issues/SH<YY><NN>/`.

**Goal:** the "Fehlerteufelchen" was 64'er's errata column. Corrections
for **this** issue's articles were printed in the Fehlerteufelchen rubric
of **later** issues. This rule harvests every such correction and applies
it to the affected article here: an `<aside class="fehlerteufelchen">` at
the end of the article, an in-text link to it, and — for code errata — a
matching fix in the `prg/*.txt` listing.

## THE RULE RUNS IN TWO DIRECTIONS AND HAD NO WORDS FOR THEM

**INBOUND** — errata printed in LATER issues that correct THIS issue's
articles. Everything lands in `issues/<this issue>/`.

**OUTBOUND** — the Fehlerteufelchen rubric printed in THIS issue, which
corrects EARLIER issues' articles. Everything lands in
`issues/<earlier issue>/` — its HTML, its `prg/*.txt`, its
`reviewed/errata_status.txt`. **This is authorised, it is the point of the
step, and you do not need to ask.** Both directions are already in this
file — outbound as a subordinate clause under *Run order* ("re-run over old
issues whenever a new issue is imported") and as `issues/<source-issue>/prg/`
in step 4 — but neither had a NAME, and the same words meant different issues
in the two directions ("this issue", "the source issue", "the FT-source
article"). 8702's builder had to invent INBOUND/OUTBOUND to report its own
work and then asked permission for an edit this rule already told it to make.
**A builder that invents a word to describe what it just did has found a hole
in the rule, not a lapse in itself** — the words are the rule's now.

**The two directions produce the SAME edit, reached from opposite sides** —
issue N's inbound pass over issue N+k's rubric, and issue N+k's outbound pass,
both end with the aside on the same article. That is why a skipped inbound
usually costs nothing: the later build repairs it. MEASURED on 8612, whose
step 300 was excused as a no-op and which today carries all four of its
errata — one applied outbound from 8701, three from 8702.

**It breaks at the NEWEST issue, which is exactly where the rule excused
it.** 8702's six inbound errata are printed in 3-8/87. Those issues are not
scanned and may not be built for years, so nothing will come from the other
side; the inbound pass is the only pass they will ever get. **The newer the
issue, the more its inbound pass is worth, and the rule had the slope
backwards.**

Two things do NOT follow from the outbound licence:

- **Only what this issue's rubric names.** The licence is to carry THIS
  issue's errata to the articles they name. It is not a licence to fix
  anything else noticed in the other issue on the way past.
- **A reprint is still not an edit of the original.** See *A REPRINT of a
  corrected page needs a Futureteufelchen* below: there the correction is
  OURS, made now, about the reprint in front of us.

## HOW OFTEN: essentially never. Count before you argue

**19 asides in 1,825 articles.** 31 of the 44 issues have NONE; 8 have one; 4
have two; the most any issue has ever had is 3. For scale, the magazine's own
errata appear 153 times — the archive adds its own voice eight times less often
than the magazine corrected itself.

So the question is **not** "does this candidate qualify". A qualification test
applied to a reading of a whole issue will pass a dozen things, and 8611's read
produced 18 candidates — which would have taken the corpus from 19 to 37, from
one issue out of 44.

The question is: **is there one thing in this issue a reader must be told, that
beats the best one already here?** Usually there is nothing, and that is the
normal outcome. 8611's is the calibre to measure against: Listing 1 on p78 is
not the routine the article promises but a different article's, and the
magazine never put it right. An entire listing absent, for the issue's life.

Against that, a wrong digit, a crash from one bad address, a note that plays
flat, a chart disagreeing with its own text — these are ordinary 1986, and the
corpus has passed over them 1,800 times. Record them in LOG.md and move on.
**The criterion below says what MAY be said; this says how rarely it is worth
saying.** Having only the first is what makes a list of 18 look reasonable.

## KEEP THE TEXT COMPACT

MEASURED over all 19 in the corpus, counting prose and excluding any generated
listing: **median 34 words**, quartiles 20 / 34 / 64. The shortest are nine
("Das Spiel liegt hier bereits als zusammengefaßte Datei vor"), and the three
above 84 are outliers, not the pattern.

So: **one or two sentences.** Say what the page gets wrong, say what is right,
and stop. Where the disk or `prg/` already has it right, that sentence is the
whole aside. Do not narrate how it was found, do not reason in the aside, and do
not restate the article. The evidence belongs in LOG.md and the commit message;
the reader wants the correction.

## WHEN a Futureteufelchen is added — the corpus's own criterion

**Owner, 2026-10-05: *"correcting typos that don't help anyone… doesn't help
anyone."*** That is the test, and it is the reason the four kinds below are the
four: each of them tells the reader something that changes what they can **do**
— a listing that will now run, a file that differs from the page in their
hands, a correction the magazine never printed, a fact they can act on. A
typo that costs the reader nothing gets nothing, however plainly wrong it is.

Ask it the owner's way first — *who is helped?* — and only then work through
the four. If the honest answer is "nobody, but it is wrong", that is a typo,
and typos in print remain typos.

MEASURED on SH8604: its Vorwort (p3) calls the same first course *Sonderheft
2/85* in one sentence and *Sonderheft 2/86* in the next. Obviously one of them
is wrong; **nobody is helped by being told which**, and no aside is written.

**THE DEFAULT IS NO, AND IT IS STRONGER THAN THIS SECTION READS.** The four
kinds below describe what the EXISTING asides are; they are not an invitation
to find more. The standing rule is the owner's, 2026-10-08: *print errors are
left as printed, and only a reprint missing its original's erratum earns an
aside*. Everything else has to clear that, not merely fit a kind.

MEASURED, 2026-11-02: the 8701 build put up six candidates, each with the page
quoted, the fact established, the German aside drafted and "who is helped"
answered — and **the owner took none of them.** Six would have been double the
corpus record in any case (22 asides across 14 issues, maximum 3 in one). The
six were a wrong address range, a typeset fusion that breaks a beginner's
example, two absent line references, a wrong part number, an off-by-one in a
command and a dropped hex digit: every one of them "the magazine got this
wrong, and a reader could act on it", which is the *smallest* of the four kinds
below (5 of 22) and the one the standing rule is pointed at.

**So read the table the other way round.** Twelve of the 22 — "we corrected it"
and "our files differ" — say something about what WE did or what OUR files
hold. That is what the aside is mostly for. When the only content is *the
magazine was wrong*, the answer is almost always to leave it, however
actionable it looks and however well the (a)-(d) case is made. Do not spend a
build drafting six of them.

Derived from all of them in the corpus, not from principle. Every one says
something **the archive knows and the page does not**, and falls into four
kinds:

| kind | n | what the aside actually says |
|---|---|---|
| we corrected it | 8 | "Der folgende Fehler wurde in Listing 6 behoben", "Im MSE-File ist es korrekt" |
| our files differ | 4 | "Listings 1 und 2 liegen hier bereits in der dekomprimierten Form vor" |
| the magazine never did | 2 | "Die 64'er hat diese Verwechslung nie richtiggestellt" |
| a fact checkable off the page | 5 | the C64's graphics base is `$E000`; `$97` stores to `MM,Y`; the C128D's numbered button is the drive's reset; here is the formula that generates the printed table |

**So "the print is wrong" is not the criterion, and an internal inconsistency
on its own is not one either** — that is a typo, and *typos in print remain
typos*. The aside exists to carry what we can assert, with its grounds.

Ask, in this order:

1. **Is the version in `prg/` or on the Programmservice disk correct?** This
   settles most cases with evidence instead of assertion, and it is what the
   dominant 8 do. Check before anything else.
2. **Do our files differ from the print** because of how the archive was built?
   Then say how.
3. **Did the magazine correct it later, or never?** `Fehlerteufelchen.md` is the
   record; "never" is itself worth stating, and both instances say so plainly.
4. **Is the correct fact verifiable off the page** — machine behaviour, CPU
   semantics, hardware, arithmetic that can be shown? Then state it and say how
   it was checked. r000's petcat/x64sc procedure can now settle a BASIC or
   assembler claim by running it.

If none of the four applies, record the candidate and leave it. A page that
merely contradicts itself gets no aside — and "record and leave it" means a
line in LOG.md, not a question for the owner. A candidate that fails the
who-is-helped test is **settled by this rule**, not escalated.

## TWO KINDS OF DEVIL: Fehlerteufelchen is THEIRS, Futureteufelchen is OURS

Both already exist in this site — CSS, an SVG each, and generator handling in
`generate.py` (`aside.fehlerteufelchen` / `aside.futureteufelchen`). 17 published
articles carry a Futureteufelchen.

| | who found it | when | what it is |
|---|---|---|---|
| `<aside class="fehlerteufelchen">` | the magazine | 1984-86 | a correction 64'er itself printed in a later issue's errata column |
| `<aside class="futureteufelchen">` | **us** | **2026** | an error in the printed magazine that **was never corrected back then**, found while making this archive |

A Futureteufelchen is signed by the modern finder where there is one
(`<address class="author">(Endurion, goloMAK)</address>`); most carry no byline.
It may also record a repair we made to a `prg/*.txt` listing — 8406/117's says
`Die folgenden Fehler wurden im Basic-Lader behoben:` and lists them.

**It does NOT change the article text.** *Typos in print remain typos in the
HTML* still holds: the page's error stays where the reader can see it, and the
Futureteufelchen stands beside it saying what is actually true.

**"The article text" includes its LISTINGS.** This is where the rule gets
argued with, because replacing a wrong listing with the right one feels like
repair rather than rewriting. It is rewriting. 8611 p78 prints a hex dump
headed `Name : screencopy $cf11` under the caption *"Listing 1. RS232 mit
4800 Bit/s. Bitte mit dem MSE eingeben."* — the wrong film went into that box
in 1986 and the magazine never corrected it. A sub-agent placed the disk's
correct RS232 program instead, marked `deviates from print, deliberately`,
which is the natural engineering instinct and the wrong answer: the page
printed Screencopy, so the article shows Screencopy, and the Futureteufelchen
beside it carries the correction and the program that should have been there.
A whole wrong listing is the same case as a wrong line, only larger.

### A FUTURETEUFELCHEN IS NEVER YOURS TO ADD — IT COMES FROM THE ISSUE OWNER

**This section is knowledge, not a worklist.** A Fehlerteufelchen is mechanical:
the magazine printed a correction, you route it and apply it. A Futureteufelchen
is an editorial statement in the archive's own voice, saying *the magazine was
wrong and here is what is true* — and that is a judgement about the subject
matter, not about the scan.

So: **find them, record them, and stop.** Never add one on your own judgement,
never add one in bulk, never treat a list of candidates as work to be worked
through.

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

What to hand over: the passage, what appears to be wrong, and the crop that
shows the page really prints it — the same evidence any other finding carries.

**What qualifies, from SH8601's reading pass** (all verified as printed, all
recorded, NONE acted on):

| page | what the magazine printed | why it is a candidate |
|---|---|---|
| p054 | `80x200 = 1600 Byte` | the arithmetic is wrong; it is 16000 |
| p032 | `»SHAPE DATA 2« (Listing 13)` | no such listing exists — p046's Listing 13 is `»SHAPE UND SPRITE«`, and no such file is on the disk |
| p018/020 | `maximal 200 KByte` | contradicts `170 KByte` two pages earlier in the same article |
| p145 | crossword clue `(92)` | the grid HAS a cell 92; the printed clue list jumps 90 -> 93 |
| p109 | `(acht Zeilen Länge)` | *Zeichen* is meant, not *Zeilen* |
| p026 | Bild 14/15 caption vs text | the magazine's own figure numbering disagrees with its prose |

And what does NOT qualify, however wrong it looks: a plain typo. `Beipielprogramm`,
`nebenanderliegene`, `»MANDELBROT1»`, `zwischen $0 uns $1fff` — the reader can
see what was meant, and an aside would say nothing they do not already know.
A Futureteufelchen earns its place by telling the reader something the page
misleads them about.

### A REPRINT of a corrected page needs a Futureteufelchen, not a copy of the Fehlerteufelchen

When an erratum corrected the ORIGINAL printing but this issue reprints the
uncorrected page, the finding — *this reprint is still wrong* — is **ours, made
now**. The magazine never said it. So it is a Futureteufelchen.

**ADAPT the wording; do not paste the original erratum.** It was written about
the other issue and cites ITS page numbers, which are meaningless here. Drop
them and describe the figure as it appears in THIS article, then say where the
original correction ran:

```html
<aside class="futureteufelchen" id="futureteufelchen">
    <h2>Futureteufelchen</h2>
    <p>Die in Bild 2 mit der Nummer 3 bezeichnete RESET-Taste ist in
       Wirklichkeit die RESET-Taste für das Diskettenlaufwerk. …</p>
    <p>Die 64'er hat diesen Fehler im Fehlerteufelchen der Ausgabe 5/86 für den
       Erstdruck in Ausgabe 1/86 richtiggestellt. Dieser Nachdruck übernimmt
       Bild 2 jedoch unverändert, so daß die Korrektur hier nie erschienen
       ist.</p>
</aside>
```

MEASURED on SH8601: `16 Der C 128 D im ersten Test` reprints 8601 pp 43-44;
8605's Fehlerteufelchen corrects Bild 2 of exactly those pages — the button
labelled 3 is the DRIVE's reset, item 4 the hardware reset, not the mains
switch. `issues/8601/43` carries the Fehlerteufelchen. The reprint carried
`3-Resettaste; 4-Netzschalter` and nothing else, so its reader saw a
known-wrong figure with the correction three issues away.

**Routing is why it was missed:** the erratum's heading names `Ausgabe 1/86,
Seite 43 und 44`, so step 1 sends it to the monthly and stops. After routing an
erratum, check `REPRINTS.md` and the r330 verdicts for an article in THIS issue
that reprints the cited pages.

Do not edit the other issue *for this* — r000, *the issue you are working on
is the scope*. **Read that narrowly: it is about the REPRINT case.** The
original printing already carries its own erratum and needs nothing; what is
wrong is the copy in front of us, so the entry goes here. It does **not**
countermand the OUTBOUND licence above, where carrying this issue's rubric
into the earlier issue's files is the whole job. Written flat, the sentence
sits four screens from that licence and contradicts it, which is how 8702's
builder came to ask whether it could write the records its own step requires.
The monthly already has its own aside; what is missing is the reprint's.

This is why prior issues carry 2–7 of these asides each (8601–8607) while a
freshly-built issue has **zero**: the errata live in issues that are
imported later, so this step is a **cross-issue enrichment**, not a
single-issue transform.

**It applies to Sonderhefte as well** — this rule builds no rubric, it consumes
one. A Sonderheft article can be corrected by a later monthly's Fehlerteufelchen
just like a monthly's can, and 26 articles across `SH8501`-`SH8508` already
carry the resulting aside. Step 1 below already routes
`Sonderheft N/YY → issues/SH<YY><NN>/`; that is not an edge case, it is half the
point of scanning every later issue's rubric.

## Run order — LAST (after rules 000–290)

This rule must run **after** every single-issue rule is done, because it:
- wraps a **figure caption / listing caption / table cell / inline value**
  in a link — so figures (rules 130/150), listings (rules 130/170) and tables
  (rule 160) must already be placed, and
- edits `prg/<name>.txt` — so the PRG extraction (rule 120) must be done, and
- must not be disturbed by later text passes — so heading case (260),
  autolink (270), OCR cleanup (280) and hierarchy (290) must already have run
  (they would otherwise re-touch the wrapped element).

It is also **re-run over old issues** whenever a new issue is imported, in
case the new issue's Fehlerteufelchen corrects an already-published article
(see step "Asymmetry" below). For issue `YYNN`, scan the Fehlerteufelchen
of **every issue after `YYNN`**.

## Full procedure

The exhaustive procedure — finding the rubric page in each candidate issue,
three-OCR-layer verification, building the `Fehlerteufelchen.md` index, the
`prg/*.txt` Style A/B patterns — is the **appendix at the foot of this file**.
Read it before running this rule. The essentials are distilled below.

## Inputs

- `Fehlerteufelchen.md` (repo root) — the cross-issue errata index. Each
  item: `**Article** (Ausgabe M/YY, Seite NNN)`. Build/extend it per the
  workflow doc from the later issues' Fehlerteufelchen rubrics.
- `fehlerteufelchen_pages/<issue>.pdf` — single-page rubric extracts,
  **untracked; never `git add` them, never name them in a commit message**
  (appendix step 10).
- The already-imported FT-source article HTML where available
  (`issues/<FT-issue>/<page> Fehlerteufelchen.html`) — the erratum text is
  transcribed from there / the scan, never composed from memory.

## For each erratum targeting an article in THIS issue

1. **Find the source article** by `<meta name="64er.pages">` start-page +
   title overlap (not filename). `Ausgabe N/YY → issues/YYNN/`,
   `Sonderheft N/YY → issues/SH<YY><NN>/`. If the article isn't imported
   yet, note and skip.

2. **Add the aside** at the very end of the article, immediately before
   `</article>` (and after the byline / any trailing listings — rule 130
   already reserves this as the last block):

   ```html
           <aside class="fehlerteufelchen" id="fehlerteufelchen">
               <h2>Fehlerteufelchen</h2>

               <p>… erratum paragraph(s), transcribed verbatim …</p>

               <!-- Korrektur im Programm angewendet -->
               <!-- 64'er M/YYYY -->
           </aside>
       </article>
   ```
   - `<h2>Fehlerteufelchen</h2>` is the heading (matches 8606; some early
     issues used `<h3>` — use **h2** going forward).
   - `<!-- 64'er M/YYYY -->` — **always**, names the issue the erratum
     appeared in.
   - **Status comment** (only when the erratum concerns a code listing),
     placed **above** the `64'er` line — exactly one of:
     - `<!-- Korrektur im Programm angewendet -->` — real code bug, fixed
       in the `prg/*.txt` (step 4).
     - `<!-- Disk-Version bereits korrigiert -->` — the `.D64` was patched
       after the print run; the printed listing was wrong but the disk
       works; `.txt` unchanged.
     - `<!-- Reiner Druckfehler -->` — print-only artifact (unreadable
       digit, hardware-schematic typo); disk was never wrong.
   - **Omit** the status comment entirely for non-code errata (figure
     caption, prices, addresses, reprints) — which is to say: the comment is
     mandatory wherever a PROGRAM could be affected, and absent where none
     could. *Every aside carries a disposition comment*, below, reads as
     unconditional and these two sentences were taken as contradicting each
     other on SH8603. They do not: **136 of the corpus's 161 asides carry no
     status comment**, because most errata correct prose, prices or a caption.
     The test is whether a reader with the disk would need to check anything.
   - If an old `<!-- Fehlerteufelchen … -->` placeholder comment exists,
     **delete it** — never ship both placeholder and aside.
   - **Multiple corrections to the SAME article → ONE aside.** An
     article corrected in more than one later issue (e.g. 8608's
     `17 Leserforum`: a Lichtorgel Watt fix *and* an SX vendor-name fix,
     both from 10/86) gets a single `<aside … id="fehlerteufelchen">`
     with one `<p>` per correction — `id` must stay unique on the page,
     and every in-text link (step 3) points at that one anchor. If the
     corrections came from different issues, list each `<!-- 64'er
     M/YYYY -->` trailer (one per correction, in issue order).

3. **Wrap the affected element** with the link (do NOT wrap anything inside
   the aside — that self-references):

   ```html
   <a href="#fehlerteufelchen" class="fehlerteufelchen_link">…</a>
   ```
   Wrap the most specific element the erratum addresses, per convention:
   Bild-N figcaption · a specific `<pre>` code line (when inline) · a
   table `<td>` · an inline price/value in prose · else the Listing-N
   figcaption (fallback when the listing is auto-generated from
   `data-filename` and individual lines can't be wrapped). If the article
   is a **reprint** missing that element, omit the wrap — the aside alone
   still carries the correction.

4. **Patch the source listing** `issues/<source-issue>/prg/<name>.txt` when
   the erratum fixes numbered Basic code (appendix step 8): header
   `;inkl. Fehlerteufelchen N/YYYY` after the `;<file>.prg ==XXXX==` line,
   then Style A (single inline `;Zeile X neu entspr. …` marker above the
   fixed line) or Style B (comment the old line with `;`, corrected line
   below). Disk-already-correct → header note only, no per-line markers.

## Anti-memory (mandatory)

Every erratum word must trace to the print: render the FT PDF page → OCR
(tesseract + paddle) → **Read the PNG multimodally** → write to
`_tmp/<issue>_ft.txt` → Read that file → edit the article. Never compose
erratum text from memory. Preserve original typos and German spelling
(`daß`, `muß`, »…«). See
the anti-memory rule in `r000_orchestration.md`.

## Asymmetry to watch (both sides!)

Past work sometimes patched only one side — the `.txt` was fixed but the
article aside was missing, or vice versa. For **every** item verify BOTH
the article aside AND the `prg/*.txt` fix exist.

## A prg whose printed erratum the owner left unapplied

The three disposition words cover "patched" and "left alone on purpose", but
not the state a build actually reaches most often: **the disk file carries the
bug, the magazine printed the correction, and the owner has ruled RECORD ONLY**
(downloads keep what the magazine shipped). That is neither "pending" nor
"patched", and none of the three words fits it.

Write it into the program file as a header comment, and say so in the aside:

```
;vor Fehlerteufelchen M/YYYY (Zeile N)
```

MEASURED on SH8602: `prg/spline 64.txt` line 670 and `prg/reset-helfer.txt`
line 190, both corrected by the magazine in 4/1986 and 5/1986, both left as
printed on the owner's ruling (2026-10-04).

## A CONDITIONAL erratum: the vocabulary gets a fourth word, because none of three was true

The three words claim something about a FILE: the disk already had it right, we
applied it, or the print alone was wrong. **An erratum whose change depends on
the reader's own hardware is none of those** — applying it would break the
readers it does not apply to, so the listing must stay as shipped, and saying
`Reiner Druckfehler` (a program IS affected), `Disk-Version bereits korrigiert`
(it was not) or `Korrektur im Programm angewendet` (it was not) would each be a
false statement about the file.

MEASURED on SH09 article 113: 8612's Fehlerteufelchen for Datev is reproduced
verbatim with its `64'er 12/1986` trailer, the correction is **conditional on
the reader's printer**, and `prg/datev.prg` is left unpatched. The builder
reported that none of the three words fits rather than picking the nearest one,
which is how a closed vocabulary is supposed to fail.

So: **`<!-- Bedingte Korrektur, nicht angewendet -->`**, the condition named in
the aside's prose, and the erratum named in a file, so the pair stays checkable
— the new word is in `r300_status_pairs.py`'s `STATUS` precisely so the check
still demands that record. **Which file depends on what the program is:**

- a program with a listing — its own header line, as ever:
  `;Fehlerteufelchen M/YYYY bedingt, nicht angewandt`
- **a RAW BINARY has no header line, and must not be given a fabricated one.**
  `generate.py` renders every `prg/*.txt` as a listing, so an invented text file
  would ship to readers as a program. Its record goes in
  `issues/<ID>/reviewed/errata_status.txt`, one tab-separated line of program,
  erratum and disposition:

```
datev.prg	Fehlerteufelchen 12/1986	bedingt, nicht angewandt: the correction depends on the reader's printer
```

  The named program must exist in `prg/`, or the line satisfies the gate while
  naming nothing — the check enforces that too.

**I added the word without asking where its evidence could live**, and for a
binary the answer was nowhere: SH09's build went red on a correct article with
no edit available that would clear it, and the builder came up rather than
inventing a file. A vocabulary and the places its evidence may live are one
change, not two. This
is the SECOND gap in a vocabulary declared closed (the first being a prg the
owner left unapplied, which took a `;vor Fehlerteufelchen` header instead of a
word). A vocabulary that keeps meeting states it cannot express is not closed;
it is under-measured. **Do not stretch an existing word to fit — a status
comment is read as a claim, and a false claim here tells a future build that
nothing needs checking.**

## AN ERRATUM WHOSE OWN REFERENCE IS WRONG, OR COLLIDES WITH THE ARTICLE'S

The erratum is a printed text and **it is reproduced verbatim** — r000, *print
errors: leave as printed*; the owner, 2026-10-08. But an erratum points at
something, and the pointer can be wrong or can mean something else over here.
Two states, both met on 8702's outbound pass, and ONE answer shape for both:
**the TEXT stays wrong, the LINK carries what we know, and a German HTML
comment states the mismatch.** Never repair the pointer inside the quotation —
a reader comparing our page with the print must find them identical.

### The erratum cites the wrong figure

MEASURED on 8702's 2/87 rubric → `issues/8612/52 Bauanleitung: Centronics-
Interface`: *"Weiterhin ist auf Seite 57 Bild 2 Vcc mit 50 Volt bezeichnet
worden."* The article's Bild 2 is a 1:1 PCB layout and carries no voltages at
all; **Bild 1**, the Programmiergerät schematic, prints `V_CC = V_DD = +50
volts typical` in its legend — verified by reading `issues/8612/52-1.png`. The
page number is right and the figure number is wrong.

So: wrap **Bild 1's** figcaption, because the link's job is to take the reader
to the thing the erratum is about, and leave the sentence alone.

```html
<!-- Das Fehlerteufelchen nennt Bild 2; die Angabe »+50 volts« steht in Bild 1. -->
<!-- Reiner Druckfehler -->
<!-- 64'er 2/1987 -->
```

The status comment here is NOT prescribed by this example — it comes from step
2's test, *whether a reader with the disk would need to check anything*. 8612/52
ships eleven programs and a schematic error invites exactly that question, so
`Reiner Druckfehler` answers it ("disk was never wrong"); 8702's `46
Anschlußprobleme` ships none and gets no comment at all. Read the test, not the
example: 8702's builder took the example as a rule and then had to ask which of
the two won. **An example that states a conclusion without its test will be
copied where the test does not hold.**

And where NONE of the vocabulary is true, omit. MEASURED on 8611/44 *Die Mäuse
breiten sich aus*: the 2/87 erratum adds a hardware condition — a 10 kOhm
resistor from Pin 9 to +5 V — and the article ships three programs. Nothing was
misprinted, no disk was patched, no listing was changed, and the reader's fix is
a soldering iron. `Reiner Druckfehler` would assert an error that does not
exist. This is the THIRD state this "closed" vocabulary has failed to express;
the answer is still to omit rather than to stretch a word, and to say so in
LOG.md.

The precedent for the comment is `issues/8611/50`, which already carries
`<!-- Das Ladeprogramm auf der Diskette ist anders numeriert: … -->` beside its
status comment: a short German statement of fact about a reference that does
not line up, next to the disposition and before the source trailer.

### The erratum prints its OWN listing, and "Listing 1" then means two things

An erratum that supplies a program refers to it by its own number, which
collides with the host article's numbering. MEASURED on 8702's 2/87 rubric →
`issues/8611/52 Das Ende aller Tippfehler`: the erratum says the patch *"(Listing
1)"* is to be typed in with the MSE — while the host article's **Listing 1 is
SPELL CHECK V1.0 itself**, the program being patched. Left as it stands, the
reader is told to run `NEW` and `SYS 49152` over the very program the patch is
meant to fix.

The corpus settled this in 8407/24, where the 8/84 erratum supplied two missing
programs: they are placed **inside the aside as ordinary figures, captioned by
NAME and never by number** — `»Wandler«`, `»Wandler 2«`. A caption with no
number cannot collide with one.

So, when an erratum prints a program:

1. It is **not optional**. The erratum is unusable without it, and the aside
   would be quoting a listing the reader cannot see.
2. The program goes into the **target** issue's `prg/`, and the figure inside
   the aside, captioned by its NAME in guillemets.
3. The host article's own Listing-N numbering is untouched.
4. The erratum's prose keeps its own "(Listing 1)" verbatim; the figure
   standing directly under it is what resolves the reference.

## THE SAME CORRECTION PRINTED MORE THAN ONCE

The magazine repeated itself. MEASURED on 8702's `164 Der Schlüssel zu Geos
(Teil 1)`, which is corrected in THREE later rubrics:

| rubric | cites | what it corrects |
|---|---|---|
| 3/87 p72 | 2/87 S.170 | Listing 3 Zeile 30020 only: `»B0=PEEK(AD)«` → `»B0=PEEK(AD) AND 191«` |
| 4/87 p73 | 2/87 S.164ff | Listing 3 Zeilen 1, 141, 660, 1170, 30020 |
| 8/87 p47 | 2/87 S.169 | the same five lines, reworded, and 30020 given IN FULL |

**Print all of them, in issue order, each with its own `<!-- 64'er M/YYYY -->`
trailer** — step 2's multiple-corrections shape, which already fits. Do not
collapse them to the fullest one, and do not drop the "redundant" ones:

- they are not redundant. 4/87 gives 30020 as a substitution within the line;
  8/87 gives the whole corrected line, `»AD=AD+1:B0=PEEK(AD) AND 191:SB=0«`,
  which is what a reader actually needs and what the disk holds (verified in
  `issues/8702/prg/gdm v1.0.txt` line 30020).
- choosing between them is editing the magazine. *We publish the plate*: it
  really did print the correction three times, over six months, and the three
  trailers tell the reader that.

One aside, one `id`, one `<p>` per rubric in issue order. The disposition is
judged once for the article, not once per paragraph — here all five lines are
already right on the disk, so `<!-- Disk-Version bereits korrigiert -->`.

**In the listing's header, give each rubric its own line.**
`r300_status_pairs.py` matches `Fehlerteufelchen M/YYYY`, so a combined
`;inkl. Fehlerteufelchen 3/1987 und 4/1987` records only the first — the second
rubric then has no file naming it and the check cannot see the difference
between that and a missing record. Three lines, one per issue:

```
;inkl. Fehlerteufelchen 3/1987 (Zeile 30020; Disk-Version bereits korrigiert)
;inkl. Fehlerteufelchen 4/1987 (Zeilen 1, 141, 660, 1170, 30020; dito)
;inkl. Fehlerteufelchen 8/1987 (dieselben Zeilen, dort vollständig; dito)
```

## `Fehlerteufelchen.md` IS A FINDING AID, NOT AN AUTHORITY

It was built by sweeping rubric pages, and the sweep made mistakes. MEASURED on
two pages read in full on 2026-11-17:

- **4/87 p73** was missing `Der Schlüssel zu Geos (Ausgabe 2/87, Seite 164ff)`
  entirely — an erratum against the issue then being built.
- **4/87 p73**'s `Brigant` is `Der C 64 als Speichergigant`, hyphenated across
  a column break as `Speicher-/gigant`.
- **8/87**'s rubric is on page **47**, not 48.

Three errors in two pages. So: **when you render a rubric page, you have the
whole page in front of you — read every item on it and correct the ledger.**
That cross-check is free, it is the only thing that catches a MISSING row (a
row that is not there cannot be checked against anything), and a missing row is
the failure that costs an issue its erratum. Fix the ledger in the same pass,
and say in LOG.md which rows you changed.

`Fehlerteufelchen.md` is corpus reference, so it belongs to control, not to the
build — hand the corrections over rather than making them.

## Verification

```bash
PY=${PYTHON:-.venv/bin/python}   # the repo venv; this block used to leave $PY unset
dir=issues/<YYMM>
# every aside is well-formed and anchored
grep -rl 'aside class="fehlerteufelchen" id="fehlerteufelchen"' "$dir"/*.html
# every aside names its source issue.
# NUL-separated, and read without word-splitting: EVERY article filename in
# this repo contains spaces ("62 Roulette C 128.html"), so `for f in $(grep
# -rl ...)` splits each one into fragments and reports a dozen missing files
# per issue.  It fails identically on issues that have been correct for
# months -- run it over SH8501's eight known-good asides and watch.
# NO NUL PIPELINE.  This read `grep -rl --null ... | while IFS= read -r -d ''`,
# on the theory that ugrep's -Z means --fuzzy so --null is the portable spelling.
# MEASURED 2026-10-10: neither ugrep NOR /usr/bin/grep emits a NUL for
# `-rl --null` over an explicit file list -- both print newlines -- so
# `read -d ''` never sees a terminator and the loop BLOCKS.  On SH8606 the whole
# Verification block hit the 120 s timeout and every check below this one was
# silently skipped; the first version of this loop, with -Z, had run zero times.
# The shell's own glob handles the spaces in every article filename.
for f in "$dir"/*.html; do
  grep -q 'class="fehlerteufelchen"' "$f" || continue
  # PER ASIDE AND PER CORRECTION, not per file.  A two-source aside -- one
  # <aside> with one <p> per correction, from DIFFERENT issues -- needs one
  # trailer each, in issue order, and a per-file `grep -q` passes as soon as
  # ONE of them is there.  SH8603's articles 146 and 81 are both this shape.
  $PY - "$f" <<'PYEOF'
import io, re, sys
s = io.open(sys.argv[1], encoding='utf-8').read()
# THIS CHECK HAD NEVER LOOKED AT ANYTHING.  Both patterns below were
# written as `\b` and the file actually held a literal BACKSPACE (0x08)
# in its place, so `<aside\x08` could not match any HTML ever written:
# the loop body never ran, nothing was printed, and the block exited 0
# on every issue since it was added -- including one with an aside
# carrying no trailer at all.  Worse than a FAIL that exits 0, because
# it produced no output to disbelieve.  Character classes instead: they
# say the same thing and cannot be eaten by whatever wrote the file.
for m in re.finditer(r'<aside[\s>][^>]*id="fehlerteufelchen"[^>]*>(.*?)</aside>',
                     s, re.S):
    body = m.group(1)
    # `<p` alone also matches `<pre`, so an aside quoting a corrected
    # listing counted its <pre> as a second correction and tripped the
    # 'look' line below on correct output (8701).
    ps = len(re.findall(r'<p[\s>]', body))
    tr = len(re.findall(r"<!-- 64'er ", body))
    # ONE TRAILER PER SOURCE ISSUE, not per correction: several corrections
    # can come from the SAME later issue, and then one trailer is right.  The
    # HTML cannot tell them apart, so a multi-correction aside with a single
    # trailer is a LOOK and only a missing trailer is a failure.  Measured
    # over the corpus: 159 erratum asides, 4 with NO trailer, 40 multi-
    # correction asides carrying one.
    if tr == 0:
        print('  FAIL %s: aside with no <!-- 64\'er M/YYYY --> trailer'
              % sys.argv[1])
    elif ps > 1 and tr == 1:
        print('  look %s: %d corrections, 1 trailer -- same issue for all?'
              % (sys.argv[1], ps))
PYEOF
done
# no orphan links (link present but no aside in same file)
for f in "$dir"/*.html; do
  grep -q 'href="#fehlerteufelchen"' "$f" && \
    ! grep -q 'id="fehlerteufelchen"' "$f" && echo "  $f: link with no aside"
done
# no leftover placeholder comments alongside an aside
grep -rl '<!-- Fehlerteufelchen' "$dir"/*.html

# THE LISTING'S OWN HEADER, WHICH THIS BLOCK USED TO IGNORE ENTIRELY, IS
# `r300_status_pairs.py` NOW.  Every other check here reads the asides, so an
# issue whose program files never got their `;inkl. Fehlerteufelchen M/YYYY`
# header note passed clean -- the always-GREEN mirror of a check that can never
# pass (r000).  MEASURED on SH8608: article 108's aside said `Disk-Version
# bereits korrigiert` while `prg/grafik c16.txt` carried no header note at all,
# and this block was happy.  A status comment is a claim about a FILE, so read
# the file.
#
# AND A BINARY PROGRAM HAS NO FILE TO PUT A HEADER IN, which the check did not
# allow for the moment the vocabulary grew a fourth word.  MEASURED on SH09
# article 113: `prg/datev.prg` is a raw binary printed as an MSE hexdump, the
# conditional status comment was correct, and the check went red on a correct
# build with no edit available that would clear it.  So the script reads
# `reviewed/errata_status.txt` as well -- durable, whitelisted, where
# dispositions already live.  DO NOT fabricate a `prg/<name>.txt` for a binary:
# generate.py renders `prg/*.txt` as a listing, so an invented text file would
# ship to readers as a program.
$PY tools/img/scan2ocr/rules/r300_status_pairs.py "$dir"

# ...AND ON EVERY ISSUE THE OUTBOUND PASS TOUCHED.  This whole block reads
# `$dir`, the issue being BUILT -- and an outbound pass puts its asides, its
# status comments and its records in OTHER issues, where nothing then checks
# them.  MEASURED on 8702: six asides were applied to 8701, 8612 and 8611, and
# the check on `issues/8702` is blind to all six.  Run it once per target:
for t in <the issues your rubric corrected>; do
  $PY tools/img/scan2ocr/rules/r300_status_pairs.py "issues/$t"
done
```

Cross-check against the full checklist in
the "Verification checklist" below.

## Notes

- Reference errata index: `/Fehlerteufelchen.md`.
- The rubric ran monthly 1986–1987, sporadically after; ~post-1988 it was
  folded into Basic-Corner / Tips & Tricks / Reparaturecke — so for a 1986
  issue, later 1986–1987 issues are the primary hunting ground.
- A cartoon-devil banner heads the rubric and is usually invisible to OCR —
  always confirm the rubric page visually (appendix step 1).

---

# Appendix — the procedure in full

Folded in from what used to be the separate fehlerteufelchen workflow doc,
which lived outside the rules directory.
A rule must be self-contained: r000 briefs a sub-agent with the rule file as its
primary instruction source, so a rule that points outward for its actual
procedure hands the sub-agent an incomplete spec.

How to find every Fehlerteufelchen rubric in a range of issues, index them in `Fehlerteufelchen.md`, and apply the corrections to both the source articles and their `.txt` listings.

## What Fehlerteufelchen is

The "Fehlerteufelchen" rubric was 64'er-Magazin's errata column. Each monthly issue (1986–1987 consistently, sporadic afterwards) had a 1-page rubric listing corrections for past articles. After ~1988 the rubric was discontinued or folded into other rubrics (Basic Corner, Tips & Tricks, Reparaturecke). A column header graphic appears at the page top — usually a small cartoon devil — and is often invisible to OCR.

## Pipeline

### 0. If this issue is the NEWEST in the corpus, this step is a no-op

This rule applies errata printed in **later** monthlies to **this** issue's
articles. If there is no later issue AT ALL, there is nothing to find and
nothing to apply: record that in `LOG.md` and go on.

**"NEWEST" MEANS NEWEST ANYWHERE, NOT NEWEST SCANNED.** This paragraph used to
say *"a later monthly that has not been scanned cannot correct anything, so for
the newest issue in `/Volumes/S/png/` there is nothing to find"*, which was
true only while `~/DNB/64er_OCR/` was believed gone. It is not (see *THE
`64er_OCR` SET IS NOT GONE*), and it holds every monthly to 1997. MEASURED on
8702: `Fehlerteufelchen.md` names six later errata for 2/87, in 3, 4, 5, 6 and
8/87 — all five issues are in that directory, none is scanned, and this
paragraph had already excused the step. **Being the newest SCAN is not being
the newest ISSUE**, and the three-source list above is the test.

Whatever you conclude, say it, do not leave it implied -- an agent that finds
no source for step 1 will otherwise assume the source is missing and go
looking for it. (The 2026-10-01 note here read *"8612 is the newest scan, so
8612's step 300 has no input by construction"*. The construction was the
belief about `64er_OCR`; 8612 has later issues like any other.)

### 1. Find the Fehlerteufelchen page in each candidate issue

**Where the later issue comes from.** It is one of three things and never a
fourth, in this order of preference:

- **already imported** -> the repo has it, `issues/<YYMM>/` (32 issues as of
  2026-10-01, each with its HTML and its own `64er_19XX-XX.pdf`). Grep the HTML;
  it is this project's own transcription and better than any OCR of a PDF.
- **scanned but not imported** -> `/Volumes/S/png/<YYMM>/`, the 2400 dpi masters.
- **neither** -> `~/DNB/64er_OCR/OCR-YYYY_MM_64er[_HIRES].pdf`, which is the
  only way to read an issue this project does not have. See below.

### THE `64er_OCR` SET IS NOT GONE. THIS RULE SAID IT WAS, FOR SIX WEEKS

This rule and `r000`'s dead-paths table both said **"gone and not coming
back"**, recorded 2026-10-01. MEASURED 2026-11-17, because 8702's builder
looked and said so: `~/DNB/64er_OCR/` holds **275 PDFs, 17 GB, 1984_04 through
SH97**, including every 1987 monthly. `pdftotext` yields a searchable (poor,
but searchable) layer, and `pdftoppm -r 200` renders a page that reads
cleanly — the 3/87 rubric on magazine page 72 was found and read that way,
cartoon devil and all, in two commands.

**What it cost.** 8702's INBOUND pass reported *"none applicable — the six
2/87 items are printed in 3/87-8/87, which aren't built yet, so they stay in
the ledger"*, which was correct reasoning from a false premise: all five
source issues (3, 4, 5, 6 and 8/87) are in that directory. Six errata
correcting 8702 would have been deferred to a build years away. **A rule that
declares an input dead removes it from every future build silently** — nobody
looks for what the rule says is not there, so the error cannot surface except
by accident, and here the accident was a builder reporting a directory listing
as an aside.

**What it is, and the limits.** It is a separately-OCR'd third-party set from
before this chain existed; its pages carry another site's watermark
(`64er-online.de`). So:

- it is a **FINDING AID and a READING source for a FOREIGN issue** — one this
  project neither publishes nor has scanned. That is the same standing the
  repo's own `issues/<YYMM>/64er_19XX-XX.pdf` already has here.
- it is **NEVER an input to the issue being built**, and nothing from it is
  ever published as an image. `r000`, *THE SCAN IS THE ONLY INPUT*, is
  untouched: the 2400 dpi masters remain the only source for OUR pages.
- the Anti-memory rule applies unchanged: render the page, **Read it
  multimodally**, and transcribe from what you see. The OCR layer locates the
  rubric; it never writes a word of the erratum.

Preference order for reading a later issue's rubric is therefore: the repo's
own transcription (best — it is this project's own work), then the issue's
scans, then this set.

So when you need a later issue the repo does not have:

```bash
pdftotext ~/DNB/64er_OCR/OCR-1987_03_64er_HIRES.pdf - | grep -n Fehlerteufelchen
pdftoppm -r 200 -f <pdf page> -l <pdf page> -png ~/DNB/64er_OCR/OCR-1987_03_64er_HIRES.pdf <tmp>/ft
```

`Fehlerteufelchen.md` already names the rubric's MAGAZINE page for every
indexed issue, and PDF page = magazine page − 2 in this set (verified on
3/87: rubric page 72 is PDF page 70). Confirm visually; the offset varies.

Heuristics, in priority order:

1. **TOC reference**: PDF pages 4-7 list Fehlerteufelchen entries like `Fehlerteufelchen ... 73`. The CSV has format `<title> <page>`. Apply per-issue offset (PDF page = magazine page − 2 typically; varies). When multiple page numbers, take the **largest** (rubric page, not inline-mention pages).
2. **First-5-lines header**: scan all pages for `Fehlerteufelchen` in the first 5 lines (top-of-page article header).
3. **Score-based fallback**: count `Zeile`, `Ausgabe N/MM`, `Seite N`, `korrigiert`, `muß` on each page. Page with highest score in mid-magazine is a candidate.

All three approaches need visual verification — OCR misses graphic banners. **Render each candidate to image and Read multimodally** to confirm.

### 2. Extract single-page PDFs

```bash
qpdf <source.pdf> --pages . <N> -- fehlerteufelchen_pages/<issue>.pdf
```

Save to `fehlerteufelchen_pages/<issue>.pdf` (untracked — do not commit; per user instruction).

### 3. Verify with three OCR layers

For 99%+ confidence:

1. **Tesseract** (`tesseract <img> - -l deu --psm 6`) — fast text layer.
2. **PaddleOCR PP-OCRv5** (`PaddleOCR(lang='german').predict(<img>)`) — better with stylized banners.
3. **Vision Read** on the rendered PNG — catches banners both OCR engines miss.

Keep only pages where at least one method finds the rubric. Remove false positives.

### 4. Assemble `Fehlerteufelchen.md`

One section per issue, ordered chronologically:

```markdown
## Ausgabe N/YY

Seite NNN

- **Article Name** (Ausgabe N/YY, Seite NNN)
- **Another Article** (Sonderheft N/YY, Seite NNN)
```

- Use **printed magazine page**, not PDF page, for "Seite NNN".
- Preserve German typography: `&`, `daß`, `muß`, »...«.
- Each item: article title + `Ausgabe X/YY` or `Sonderheft X/YY` + `Seite NNN` (preserve `ff` suffix).

### 5. Cross-check articles in repo

For each item in `Fehlerteufelchen.md`, find the source article. The pattern:
- `Ausgabe N/YY` → `issues/YYNN/<page> <title>.html` (where pages are determined by `<meta name="64er.pages">`)
- `Sonderheft N/YY` → `issues/SH<YY><NN>/<page> <title>.html`

Match by start-page + title overlap. Multi-page articles cover ranges; use `pages` meta from HTML, not filename.

**AN ERRATUM HEADED ONLY BY THE ISSUE HAS NOTHING TO MATCH ON — ROUTE IT BY THE
TOKEN IT NAMES.** 10/86 p80 prints an item headed just "Sonderheft 8/86", with
no article and no page: in "einem Basic-Listing", read »SYNTH.:130« / »SYNTH:132«
as FLASH-ON/OFF. Start-page overlap has nothing to work with, and
`Fehlerteufelchen.md` never indexed the item at all — its 10/86 list skips it —
so an index-driven run finds only that month's other item and this one is
invisible twice over.

So: **read every later rubric for items headed only by the issue**, and route
such an item by searching THIS issue's print for the token the erratum names.
On SH8608 a tesseract sweep over all 166 masters found »SYNTH« on exactly one
page (p122, Apple Panic Listing 3), which settled it. Then **add the missing
line to the index**, as `**Basic-Listings** (Sonderheft 8/86)`, so the next
index-driven run can see it.

Many references will be to articles not yet imported (in older or out-of-range issues / Sonderhefte). Note those, skip.

### 6. Add erratum aside to source article

If the article has no `<aside class="fehlerteufelchen">`, extract the erratum text from the FT source HTML (e.g. `issues/<FT-issue>/<FT-page> Fehlerteufelchen.html`) and insert at end of article:

```html
        <aside class="fehlerteufelchen" id="fehlerteufelchen">
            <h2>Fehlerteufelchen</h2>

            <p>... erratum paragraph(s) ...</p>

            <!-- Korrektur im Programm angewendet -->
            <!-- 64'er M/YYYY -->
        </aside>
    </article>
```

Trailing comments:
- `<!-- 64'er M/YYYY -->` — always; names the issue where the erratum appeared
- One of the following status comments, ABOVE the `<!-- 64'er ... -->` line, when the erratum involves a code listing:
  - `<!-- Korrektur im Programm angewendet -->` — Case 1: real code bug, fixed in the source `.txt` listing in `prg/` (Style A or B)
  - `<!-- Disk-Version bereits korrigiert -->` — Case 2: the `.D64` disk was patched after the print run, so the disk works even though the printed listing has the bug. The `.txt` may carry the same note `(...; Disk-Version bereits korrigiert)` in its header.
  - `<!-- Reiner Druckfehler -->` — Case 3: print-only artifact (unreadable digit, mis-printed line that users were instructed to type differently, hardware schematic typo). The disk was never wrong; no `.txt` change applicable.
- **Omit** the status comment entirely when the erratum is not about a code listing (hardware figure caption, prices, addresses, reprints without the affected element, etc.).

If a `<!-- Fehlerteufelchen ... -->` placeholder comment already exists in the article (old convention), **remove** it after adding the aside (don't keep both).

### 7. Wrap the affected element with a link

Look in the article body for the element the erratum addresses. Wrap it in:

```html
<a href="#fehlerteufelchen" class="fehlerteufelchen_link">...</a>
```

Common wrap targets (per existing convention):

- **Bild N figcaption** — when the erratum corrects a figure or its caption
- **Specific code line** inside a `<pre>` listing — when the line is inline in HTML
- **Table cell** `<td>` — when correcting a tabular value
- **Inline price / value** — when correcting a number in prose
- **Listing N figcaption** — fallback when the listing is auto-generated from `data-filename` (cannot wrap individual lines)

**Don't wrap content inside the aside itself** — that creates a self-referencing link.

If the article is a **reprint** without the affected element (e.g. a Sonderheft reprint that omitted some figures), **omit the wrap**. The aside alone still provides the correction.

### 8. Update the source listing `.txt` (if applicable)

If the erratum corrects code in a numbered Basic listing, find the source `.txt` in `issues/<source-issue>/prg/<name>.txt`.

**Style — three patterns observed:**

**Header** (always, right after `;<file>.prg ==XXXX==` line):
```
;inkl. Fehlerteufelchen N/YYYY
```
Optional parenthetical: `(Zeile X)`, `(Zeilen X, Y, Z)`, `(...; Disk-Version bereits korrigiert)`.

**Style A — single inline marker per fixed line:**
```
;Zeile 336 neu entspr. Fehlerteufelchen 4/1986
  336 goto 375
```
Place the marker comment right above the corrected line. Best for one or two changed lines.

**Style B — show old before new:**
```
;vor Fehlerteufelchen N/YYYY
;   1 poke650,128:ifpeek(1022)=0then5000
    1 clr:poke650,128:ifpeek(1022)=0then5000
```
Comment out the original line(s) with `;`, then put the corrected version below. Use when preserving the history aids the reader.

**Disk-already-correct case:** When the print typo never reached the disk version (e.g. an unreadable number that's clear in the binary), use header only:
```
;inkl. Fehlerteufelchen N/YYYY (Zeile NNN; Disk-Version bereits korrigiert)
```
No per-line markers — the .txt as extracted is already correct.

### 9. Asymmetry to watch for

Past contributor work (e.g. thierer's per-issue PRs) sometimes applied the fix to **only one side** — `.txt` was patched but the article aside was missing, or vice versa. When auditing, check **both** sides for every item.

### 10. Do not commit `fehlerteufelchen_pages/`

The single-page extract PDFs are working reference material, not part of the published site. Add to `.gitignore` or just don't `git add` them. Don't mention them in commit messages either.

## Verification checklist

For each erratum:
- [ ] Source article exists in repo (find via `64er.pages` meta + title)
- [ ] Aside present at end of article with `class="fehlerteufelchen" id="fehlerteufelchen"`
- [ ] Aside text matches print (preserve original typos, German spelling)
- [ ] `<a href="#fehlerteufelchen" class="fehlerteufelchen_link">` wraps the right body element (or absent if article is a reprint missing that element)
- [ ] Comment trailer `<!-- 64'er M/YYYY -->` names the FT issue
- [ ] If listing-related: status comment `<!-- Korrektur im Programm angewendet -->`, `<!-- Disk-Version bereits korrigiert -->` or `<!-- Bedingte Korrektur, nicht angewendet -->` above the issue trailer
- [ ] And the erratum named in a FILE: the listing's own `;Fehlerteufelchen M/YYYY …` header, or `reviewed/errata_status.txt` when the program is a raw binary (`r300_status_pairs.py` checks exactly this)
- [ ] If listing in `prg/<name>.txt`: header annotation + per-line markers in Style A or B (or disk-already-correct note)
- [ ] No duplicate erratum (e.g. both a placeholder comment AND an aside)
- [ ] If the erratum's own reference is wrong or collides (wrong Bild N, its own
      Listing N): text verbatim, link on the real element, German comment
      stating the mismatch
- [ ] If the erratum prints a program: it is in the target issue's `prg/`, and
      inside the aside as a figure captioned by NAME, not by number

For the issue as a whole:
- [ ] INBOUND: every later issue was actually READ, not assumed unavailable —
      the repo, then `/Volumes/S/png/`, then `~/DNB/64er_OCR/`
- [ ] OUTBOUND: `r300_status_pairs.py` run on EVERY issue this one's rubric
      touched, not only on the issue being built

## Anti-memory rule

When extracting text from the print scan:
1. Render PDF page → PNG
2. OCR (tesseract + paddle)
3. Visually verify with Read multimodal
4. Write to `_tmp/<issue>_ft.txt`
5. Read that file, then edit articles

Don't compose erratum text from memory or training knowledge — every word must trace to the print.

## Related

- Errata items index: `/Fehlerteufelchen.md`
- Standard PRG workflow: rule `r120_prg_from_d64.md`
- Anti-memory enforcement: `r000_orchestration.md`, "OCR cleanup granularity"

## PRINT/DISK DIFFERENCES: THE DEFAULTS, AND WHAT STILL GOES TO THE OWNER

This section read *EVERY PRINT/DISK DIFFERENCE IS AN OWNER DECISION, ALWAYS*,
from the owner's 2026-10-04 *"difference between the printed listing and the
disk — always ask me."* **Two later owner rulings narrowed that, and the
absolute outlived them.** It blocked three SH8606 items the corpus already
answers, and the build had to park on each one. An absolute in a rule costs a
builder a blocked item every time it fires.

The two rulings, and the corpus that matches them:

- **A print error stays as printed** (owner, 2026-10-08) — no Futureteufelchen.
- **An unimportant difference gets a German HTML comment and nothing else.**
  The corpus has shipped `<!-- Disk-Version bereits korrigiert -->` 12 times
  and `<!-- Korrektur im Programm angewendet -->` 8 times.
- **Where the page prints a MACHINE-READABLE FACT and our disk holds the right
  one, the disk wins and nothing is said.** Owner, 2026-11-17, verbatim: *"the
  correct version (i.e. disk iiuc) wins. no comments"*.

So decide these three yourself, in this order:

- **(a) The disk already carries the fix.** Header `;inkl. Fehlerteufelchen
  N/YYYY (Zeilen …; Disk-Version bereits korrigiert)` plus `<!-- Disk-Version
  bereits korrigiert -->`, and do NOT patch the `.txt`. **Verify that every
  line you name really is the corrected form** before claiming it is.
- **(b) The disk still carries the bug.** Patch it; keep the original as
  `;vor Fehlerteufelchen N/YYYY` with the old line commented out beneath it,
  header note `;inkl. Fehlerteufelchen N/YYYY (Zeilen …)`, and
  `<!-- Korrektur im Programm angewendet -->`.
- **(c) The erratum's own words make it conditional** — it tells a reader who
  uses some configuration to change something. Record it, and never write
  *Korrektur im Programm angewendet*, which would be a false claim about what
  the file contains.

- **(d) The page prints a fact the reader must TYPE OR LOAD, and it is wrong;
  our disk holds the right one.** Publish the right one, in the text, silently
  — no comment, no aside, no Futureteufelchen. Owner, 2026-11-17: *"the correct
  version (i.e. disk iiuc) wins. no comments"*.

  MEASURED on 8702 p087, the module box for Modul 55: the page prints `4)
  RESUME 49345-49381,0`; `prg/55modul.prg` reads `RESUME 49345 49382 0`, the
  four module ranges abut exactly, and the closing `JMP $A7AE` — `4c ae a7` —
  occupies 49380, 49381, 49382. A reader typing the printed number into the
  Modul-Schreiber loses the high byte and builds a half-written jump. The page
  now reads 49382.

  Applied in the same ruling to p050's prose, which sends the reader to the
  diskette for »DRUCKER« and »SEE FILE« while the disk holds `drucken` and
  `see film` — and the article's own captions already say DRUCKEN and SEE FILM.
  Both now read as the disk does. Control had ruled a German comment on each;
  the owner's answer removed them.

**THE BOUNDARY, AND IT IS NOT "IS THE MAGAZINE WRONG".** It is **do we ship a
file that proves the other reading, and must the reader act on it.** With no
file of ours behind it there is no correct version for the disk to win with, so
*print errors stay as printed* is untouched: 8702 keeps `Speicherzelle 53270
das Register 38` (53270 is register 22), `Bit 0 bis 3 … vertikal` (bits 0-2,
and horizontal), a `CLOSE 2` after an `OPEN 1`, and `525 möglichen Farben`
where 5⁴ is 625. Those mislead a reader who is reading; they do not break a
reader who is typing, and nothing we ship contradicts them.

An erratum's own text is a QUOTATION and is never touched by this — 8612/52's
aside keeps "Seite 57 Bild 2" though the fault is in Bild 1 (see *AN ERRATUM
WHOSE OWN REFERENCE IS WRONG*). The ruling is about OUR sentences, not the
magazine's.

**AND AN ERRATUM'S LINE SET IS THE LINES IT NAMES**, not every line that
matches the pattern. SH8606's MPS 802 erratum changes `,2` to `,1` at disk
lines 1040 and 1070. The same file carries `sys50442,1` at 6040 and
`sys50442,2` at 6060, and `sys50192,11,15,2` at line 25: the double-density
hardcopy block uses BOTH arguments, so `,2` there is a mode selector and not
the bug. A blanket substitution would have corrupted three working lines. Name
the set, then check the thing you are about to change is IN it (r000).

**What still goes to the owner:** a difference that changes what the program
DOES, with no erratum to lean on and none of (a)-(d) to fall back on — the
*Hyper-Graphics* shape below, where 12 instructions differ and nothing
anywhere explains why. Report it on the owner decision list, with the evidence.

Three shapes seen so far:

| shape | example |
|---|---|
| a published correction the disk already carries | *Farbdemo*, SH8603/21: the printed p22 listing is unusable, 8605's *Tips & Tricks* corrected it, the disk is the corrected version |
| an uncorrected divergence nobody noticed | *Hyper-Graphics*, SH8603/60: 12 instructions differ, no erratum anywhere |
| a disk file carrying a bug the magazine corrected later | *spline 64* and *reset-helfer*, SH8602 |

**On SH8603 the owner declined a note in both of its cases. That is the
outcome of two decisions, not a default for the next issue.** A first reading
of that run of refusals as a standing "say nothing" rule was wrong and is
withdrawn: where a difference is still open, *ask* — and the answer may differ
next time. What is no longer open is (a)-(c) above.

## When an erratum corrects a listing, check the disk file FIRST

The Programm-Service disk usually carries the **already-corrected** program, so
an erratum that fixes a listing line often describes a defect that exists only
in print. 8609's Bar-Codes erratum (11/86) says line 85 has two digits
transposed; `prg/ean-codes.txt` line 85 already reads
`85 data"0111011","0010001","1000100"` — exactly the corrected form.

So: add the aside (it records what the printed listing got wrong), and **do not
touch the `.txt`**. Only when the disk file also carries the error is there a
listing to repair, and that is a separate decision.

## Record the errata state in the listing's own `;` header

The `.txt` listings carry a `;` comment block after the `;name.prg ==addr==`
header, and the corpus already has a settled vocabulary for errata state. Use
it — do not invent wording, and do not leave the state unrecorded:

```
;vor Fehlerteufelchen 1/1987
;inkl. Fehlerteufelchen 8/1986 (Zeile 20; Disk-Version bereits korrigiert)
;inkl. Fehlerteufelchen 9/1986 (Zeile 230; Zeile 190 in der Disk-Version bereits korrigiert)
;Zeile 391 neu entspr. Fehlerteufelchen 4/1986
;Fehlerteufelchen 2/1985 (Zeile 3040) wurde darauf angewandt
```

So the two branches both have a home:

- **the disk already carries the fix** → `;inkl. Fehlerteufelchen N/YYYY (Zeile
  X; Disk-Version bereits korrigiert)`, and the `.txt` is left untouched
- **the disk is the pre-correction version** → `;vor Fehlerteufelchen N/YYYY`,
  and the `.txt` is left as the disk shipped; or, if the correction is applied,
  `;Zeile X neu entspr. Fehlerteufelchen N/YYYY` naming each changed line

Default to recording rather than patching: readers typed these programs from the
disk, so the disk state is the historical fact and the aside on the article
already documents what the print got wrong. Patch only deliberately, and then
say which lines changed.

Placement is after the `==addr==` header, before the first program line
(`8607/prg/farbenspiel.txt` is the model).

The other `;` forms in use, worth preserving when they exist: `;Quelle: <disk or
URL>`, `;Eingetippt von <name>`, `;version=simons`, `;*** Machine language part
skipped. ***`.

## Binary listings: check the bytes, record in LOG.md

An MSE/machine-code listing is stored as a `.prg`, which cannot carry a `;`
header. Two consequences:

1. **Check the bytes directly** rather than guessing. The printed erratum gives
   the corrected rows with their addresses; read the `.prg`'s load address from
   its first two bytes and compare each row. 8609's `viza.key.prg` matched the
   10/86 erratum at all five addresses, so the disk had shipped corrected and
   there was nothing to patch — settled in one command, no judgement needed.
2. **Record the finding in the issue's `LOG.md`**, since the file itself cannot
   hold the note. The `<aside class="fehlerteufelchen">` on the article still
   carries what the print got wrong; the LOG entry carries what the disk state
   is.

## Every aside carries a disposition comment

An erratum aside says what the print got wrong. It must ALSO say what happened
to the program, as an HTML comment immediately before the `<!-- 64'er N/YYYY -->`
source marker. The corpus vocabulary — use it verbatim, do not invent wording:

| comment | meaning |
|---|---|
| `<!-- Reiner Druckfehler -->` | the error exists only in the print; no program is affected (a wrong figure number, a garbled sentence) |
| `<!-- Disk-Version bereits korrigiert -->` | a program IS affected, but the Programm-Service disk already shipped the corrected version — nothing was patched |
| `<!-- Korrektur im Programm angewendet -->` | the correction was applied to the listing in `prg/` |
| `<!-- Bedingte Korrektur, nicht angewendet -->` | the erratum's change depends on the READER's hardware or configuration, so it cannot be applied unconditionally: the listing stays as shipped and the aside's prose states the condition |
| `<!-- Reiner Druckfehler -->` (again) | **also** the value for a real code bug in an article with NO program file at all — see below |

**A real code bug with no program file** has no word of its own, and the
vocabulary is closed. SH8603 met it on the print-only DATA-Erzeuger and used
`Reiner Druckfehler` (8607/79 does the same), which is defensible — there is
no `.txt` and no `.prg`, so nothing a reader has can be wrong, and the error
does exist only in the print. But note what it costs: the comment then tells a
future reader "no listing needs checking", which is true here only because
there IS no listing. **Say so in LOG.md whenever this value is used for that
reason**, so the distinction survives the aside.

```html
        <!-- Disk-Version bereits korrigiert -->
        <!-- 64'er 10/1986 -->
    </aside>
```

**AND THERE IS A FOURTH STATE: THE OWNER HAS NOT RULED YET.** *Every aside
carries a disposition comment* has no word for it, and the three above all
assert a conclusion. The state is real and common — a print/disk difference is
always the owner's call (below), so between finding one and hearing back there
is nothing legitimate to write. The answer is the one the `xref 7.0` paragraph
already arrived at, stated as the rule rather than left as a worked example:

> **An erratum whose disposition the owner has not decided STAYS UNMARKED.**
> No comment at all — not an invented fourth word, and not one of the three
> chosen as the closest fit. The open decision is named in `LOG.md` and carried
> to the owner decision list; the aside gets its comment when the answer comes back.

An unmarked aside is therefore a legitimate intermediate state, and a build
that ends with one is not finished. Do not let a checklist that counts
disposition comments push you into writing a conclusion you do not have.

The three are mutually exclusive and the choice is a **finding, not a guess**:

- for a `.txt` listing, diff the erratum's corrected lines against the file
- for a `.prg`, read the load address from the first two bytes and compare the
  erratum's rows byte for byte at their printed addresses

8609: `viza.key.prg` matched the 10/86 erratum at all five addresses and
`ean-codes.txt` already had the corrected line 85 — both
`Disk-Version bereits korrigiert`. `xref 7.0.txt` differs on all seven lines of
the 1/87 erratum, so it is NOT one of those two, and stays unmarked until the
listing is either patched (`Korrektur im Programm angewendet`) or the decision
is taken to leave it.

Getting this wrong is not cosmetic: `Reiner Druckfehler` on an erratum that
does affect a program tells a future reader no listing needs checking.
