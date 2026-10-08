# SH8608 — WORKFLOW_ERRATA

Kept as the build runs (r340). One entry per place the instructions failed it.

## 005 — "r005_field.py runs FIRST, once" cannot run before PAUSE 1

**What the rule says.** r005_masters_sheet.md, *Run*: "`$PY r005_field.py   # ONCE, first`"
and "**`r005_field.py` runs first, once per issue**". The control brief for this
build repeated it: "`r005_field.py` runs FIRST, once, and it is not optional".

**What I did.** Planned to run it right after the descriptor and `colors.txt`,
before reporting PAUSE 1. `grep` showed `r005_field.py:714` calls
`R.first_action()`, which refuses an issue with no `binding`. So "first" means
"first after PAUSE 1", not "first thing in the build" — on an issue whose binding
is still open it cannot run at all.

**What it cost.** One grep, ~1 min; nothing run wrong.

**Suggested.** In *Run*: "`r005_field.py` runs once, AFTER PAUSE 1 is fully
answered and BEFORE the sweep — it calls `first_action()`, so with `binding` or
`paper` unanswered it refuses exactly as the sweep does."

## 005 — the colors.txt snippet cannot run before PAUSE 1 either

**What the rule says.** r005_masters_sheet.md: "**MEASURE `colors.txt` BEFORE
PAUSE 1, not after.** … The measuring method is in `r005_masters_spread.md`".
That method's snippet does `import r005_masters_spread as R` and iterates
`R.ISS.page_range` / `R.THUMB_DIR`. r000 says of the same module:
"`r005_masters_spread.py` refuses to load at all on an absent `binding`."

**What I did.** Did not run the snippet; wrote the same pool (body box
10-90 % x 12-88 %, `lum > 170`, `max-min < 40`, interior pages only) directly
against `<tmp>/thumb150`, plus the K check from *EXCEPT K*. Also note the snippet
pools `R.ISS.page_range` — ALL pages, wrapper included — while its comment says
"INTERIOR pages only"; nothing in it excludes `high_pages`.

**What it cost.** ~3 min, one script.

**Suggested.** Give r005_masters_sheet.md its own snippet that imports only
`r000_issue` (which loads with `binding` absent), reads `thumb_150`, and
excludes `paper.high_pages` explicitly — the step that must run before PAUSE 1
must not depend on a module that refuses to load before PAUSE 1.

## 005 / 006 — "2400 dpi marks colour" misses colour pages AND hand marks at 600 dpi

**What the rule says.** r005_masters_sheet.md, witness 2: "The owner scans
COLOUR pages at 2400 dpi and everything else at 600", refined to "read it as
'the owner SAW colour here'", with manual colour markings described as a reason
a page is at 2400. The control brief: "Some of those pages are at 2400 because
the owner's copy carries a MANUAL COLOUR MARKING".

**What I did.** Inspected the six interior 2400 dpi pages (004 010 015 021 025
034) for a marking-only page, as briefed: all six carry genuine plate colour
(printed red display type, blue type, rainbow logo, tinted illustration; 034's
script price is a printed face with a printed red rule). Then, unprompted, ran a
saturated-pixel census (chroma > 80) over ALL 166 thumbs and found:

- **plate colour on five 600 dpi pages**: 009 (15.8 % saturated), 026 (12.1),
  020 (4.5), 031 (3.3), 162 (0.7) — red ad, tinted diagrams, red rules,
  rainbow logo;
- **the hand marking is on a 600 dpi page**: p003, green highlighter over three
  lines of the Einleitung. Not at 2400 at all.

So on this issue dpi is neither sufficient nor necessary for colour, and the
marking the owner warned about would not have been found by looking where the
rule points.

**What it cost.** ~10 min, five commands. Without the census the p003 marking
would have reached r006 as a "colour page" or the PDF silently.

**Suggested.** In witness 2: "dpi is a HINT about colour, not a census. Run a
saturated-pixel census over every thumb (chroma `max-min > 80`, off the bed),
view the hits, and attribute each to PLATE or HAND before PAUSE 1. On SH8608
five colour pages were at 600 dpi and the one hand marking (p003, highlighter)
was on a 600 dpi page." And the same pointer in r006's plate-vs-hand section.

## 005 — the own-white gap does not separate the back cover leaf on SH8608

**What the rule says.** Witness 1: "The wrapper and any bound-in card sit far
from the interior with a clear gap", read per dpi, ties settled by the leaf
partner.

**What I did.** Computed it with the program's `paper_evidence()` against this
issue's `W 188 169 158`. 2400 dpi: 002 157, 165 136, 166 134 (wrapper/card),
then 164 99, 034 95, 025 94, 021 92, **163 87**, 010 80, 004 77, 015 77, 001 57.
The back cover leaf 163/164 lands INSIDE the 2400 interior band; only the
owner's answer puts it on the good stock. No contradiction — the owner answered
— but the witness would not have found it. Also: absolute distances are not
comparable to the rule's quoted SH8604 figures, because own-white is p90 of the
sheet and W is p2 of the pool; the 600 dpi interior baseline here is 60-70, not
~0-20.

**What it cost.** ~2 min.

**Suggested.** "Own-white is the sheet's p90 against the pool's p2, so the
interior baseline is ~60-70, not 0. A printed-tint back cover (SH8608 163/164)
does not separate from 2400 dpi interior colour pages; only the owner's answer
places it."

## 000 — a rule that saved me: read dpi from pHYs

The pHYs warning (r005 witness 2, and the control brief) gave the census in one
pass: 154 @ 600, 12 @ 2400, matching the brief exactly. Keep it.

## 000 — a rule that saved me: "LOOK at the mask on the darkest page"

The K check's darkest page (p135, 31 27 27) was confirmed on the rendered mask
to sit on the printed checksum bars of the listing, none in the bed. Cheap, and
the only way to know.

## 005 — the rules moved under this build at PAUSE 1 (0be19821)

Recorded per r340: control fixed the three PAUSE 1 findings above mid-build
(`0be19821`, r005_masters_sheet.md and r006_issue_pdf.md) — the colors.txt
recipe now imports `r005_masters_sheet`, "field runs first" now says "first of
the 005 programs, after PAUSE 1", and the dpi witness is no longer the
instrument for colour or markings. Nothing already done needed redoing: the
profile reproduces to the same p2 (188 169 158). Steps from here on run against
the post-`0be19821` text.

## 005 — the census that found p003 is not yet a step

**What the rule says.** After `0be19821`: "Sweep for colour and for markings
over EVERY page, independent of dpi (r006 has the measure)".

**What I did, with numbers.** On the 150 dpi thumbs, cropped 3-93 % x 4-96 % to
stay off bed and prop, the fraction of pixels with chroma `max-min > 80`.
Yellowed interior paper sits at chroma ~45, so 80 is clear of it. Results:
2400 dpi pages 1.0-25.1 %; 600 dpi 009 15.8, 026 12.1, 020 4.5, 031 3.3,
003 0.80, 162 0.74; then a tail from 005 at 0.19 % down, which on an overlay
(saturated px outlined, original colour kept) is orange foxing specks at the
margins only — no strokes. p003's 0.80 % was the highlighter. The deciding step
was LOOKING at the overlay of every hit above ~0.015 %, not the number: p003
and p162 score alike (0.80 / 0.74) and one is a hand, the other the rainbow logo.

**What it cost.** ~10 min, five commands. Cheap enough to run every issue.

**Suggested.** A step-005 item before PAUSE 1: "Run the saturation census
(chroma > 80 on the thumbs, off bed and prop) over every page, montage an
overlay of every page above 0.015 %, and attribute each hit PLATE / HAND /
FOXING in LOG.md. A number cannot tell a highlighter from a logo; the overlay
can." Ideally as a script beside r005_field.py so it is not re-typed.

## 005 — the Run section prescribes one process; r000 requires lanes

**What the rule says.** r005_masters_sheet.md *Run*: "`$PY r005_masters_sheet.py
# every page`" and "~45 s per page; ~2 h for 152 pages". r000: "Every step that
fans out over pages locally — 005 masters, … — sizes its lanes … none of them
may hardcode a number", `lanes(19)` for 005.

**What I did.** The program has no fan-out of its own (no `lanes(`, no pool),
so "every page" as written is one serial process. Ran it as
`xargs -P $(lanes(19)) -n 1 … r005_masters_sheet.py`, 2400 dpi pages queued
first. lanes(19) = 9 on this box today.

**What it cost.** One grep, ~1 min.

**Suggested.** In *Run*: "the program is serial; fan it out —
`seq 1 N | OMP_NUM_THREADS=1 xargs -P $("$PY" -c 'import r000_issue;
print(r000_issue.lanes(19))') -n 1 "$PY" r005_masters_sheet.py` — and queue the
2400 dpi pages first; 19 GB is their peak, a 600 dpi page needs far less."

## 005b — Verification checks 3 and 4 have no heredoc terminator, so they cannot run

**What the rule says.** r005_a4_window.md, *Verification*: check 3 opens
`$PY - <<'PY'` and ends at `"a detector outlier whose opposite edge ALSO moved
-- that is registration"` with no `PY` line; check 4 likewise ends at
`assert not bad, f"these pages are more than 5% invented: {bad}"` with no `PY`.
4 openers, 2 terminators in the block.

**What I did.** Ran the block as extracted. Check 3's Python received check 4's
comment lines and its `$PY - <<'PY'` and died `SyntaxError: invalid syntax`;
same again from 4 into 5. Added the two `PY` lines in a scratch copy and ran:
check 3 spread 0/0 px both parities (149 logo pages), check 4 body fabricated
max 2.16 % (p162). Both pass once they can run. So the two checks that prove
005b's purpose — registration and invention — have probably never run to the
end on a build that pasted the block.

**What it cost.** ~5 min, three commands.

**Suggested.** Add the two missing `PY` lines, and in r000's *A CHECK SHIPS
ONLY ONCE IT HAS BEEN SEEN TO FAIL*: "count `<<'PY'` against `^PY$` in every
Verification fence; they must be equal."

## 005b — check 1 asks for a `UNIFIED` tag the program never writes

**What the rule says.** Check 1: an off-size page passes only if its stamp
carries `UNIFIED` or `OVERRIDE`, "MEASURED on SH8605: … 197-200 at 3551x4923,
… each stamp carrying UNIFIED or OVERRIDE".

**What I did.** 165/166 (the Zahlkarte) were delivered at 3386x4921 and check 1
FAILED on both. `grep UNIFIED r005_a4_window.py` finds only the print line
`insert pages %d-%d unified to …`; `unify_inserts()` writes a stamp note only
when it PADS (`if not (dw or dh): continue`), and both sides of this card traced
the same size. So a correct, unpadded unification is undocumented in the stamp
and fails the check. Appended a factual `UNIFIED` line to both stamps (sidecar
and PNG chunk), saying the size, that no padding was needed, and that the
stamp's alpha/fabricated are the A4 window's.

**What it cost.** ~5 min.

**Suggested.** In `unify_inserts()`, write `UNIFIED insert A-B at WxH` into
every member's note, padded or not, and recompute alpha/fabricated after the cut
(the rule already asks for the latter).

## 005b — Recovery C does not say what to do when the sheet is tilted

**What the rule says.** Recovery C: "cut from row and column luminance
profiles"; Recovery A's anchoring advice: "on whichever edges ARE measurable".

**What I did.** p009 and p142 traced at 005 as `uncropped`, and 005b's
automatic paper-edge windows were wrong — p009's at x=150 cut 6.3 mm of left
content (the summary showed fabricated 0.00 %, exactly as the rule warns). On
p009 the profiles gave a clean right edge (4975, page → bed 3) and foot (7028,
an edge shadow, then prop); left/top flush with the frame; window (14, 12).
On p142 the dark ground (lum 5-9) vs bed (2-3) was just separable by mean+std,
but the PROP showed the sheet tilted ~0.25 deg to the levelled type: ramps
0→30 px left, 0→21 px top, 7018→7060 foot. An axis-aligned A4 does not fit
inside it (usable ~4939 x 6996). Centred the window on the deficit (20, 12)
and painted only the prop wedge connected to the window border white (0.09 %).

**What it cost.** ~25 min, ~10 commands, including one misleading montage of
my own making.

**Suggested.** Recovery C: "measure the prop fraction per column/row at each
edge, not only luminance: a ramp means the sheet is tilted against the type.
Then A4 will not fit; centre the window on the deficit and paint only the
border-connected prop/bed with paper white (FILL paint), recording the painted
fraction as fabricated." And: "the colour test for the prop DOES still work on
the graded master (G−B > 60, lum > 120) — it is the dark ground vs bed that is
hard, not the prop."

## 005 — Verification 4: the footer bar reads as "dark" on most pages

**What happened.** Check 4's bottom 6 mm band reads 2-9 % dark on many pages
(p032 8.7 %, p044 8.2 %). Cropped p032's foot: the printed "SONDERHEFT 8/86"
bar ends ~5 mm above the trim, inside the 6 mm band; no bed below it. The rule
accounts for "the printed footer rule, 5–6 mm inside the trim" on SH8601 only.

**Suggested.** In check 4's notes: "on SH8608-style footers the black
SONDERHEFT bar itself sits inside the 6 mm band, so bottom dark 2-9 % with 0 %
prop is the bar; crop one page to confirm and move on."

## 005b — the UNIFIED fix (1d449a34) writes its note where no stamp reads it

**Correction to my own entry above.** I had appended a UNIFIED line to the
165/166 stamps by hand. Control: a stamp is the record of what the PROGRAM did,
so a failing check on a correct build is fixed in the check or the program,
never in the record. Reverted by re-running r005_a4_window.py (6 min 25 s) and
re-applying the recoveries from `<tmp>/recover_005b.py`, which now carries both
p009 and p142 (p142's wedge paint had been an inline run, so it was not
reproducible either; it refuses to run on a4600 that already holds a recovery).

**What the fixed code does.** `unify_inserts()` now sets `w["note"]`
unconditionally, but `cut()`'s stamp writer never reads `win["note"]`: the only
note it emits is `fill_rep["note"]`, and that exists only under `FILL=mirror`.
The note goes to `<tmp>/a4win/a4_windows.json` and nowhere else — there it
reads `padded +0/+0 px …` for one side and `padded +19/+24 px …` for the
other, so one side of the card WAS padded and its stamp does not say so either.
Check 1 is therefore still red on 165/166 after the fix, honestly.

**What it cost.** ~15 min, 6 commands, plus the 6.5 min re-run.

**Suggested.** In `cut()`, emit `win.get("note")` as a stamp line (`UNIFIED
insert A-B at WxH: padded …`), and make check 1 look for the tag the program
writes. Then verify by re-running 005b and reading 165's stamp — the step that
was skipped for 1d449a34.

## 005b — a recovery script must be re-runnable, because 005b always re-cuts every page

**What the rule says.** *A PAGE WHOSE TRACE FAILS IS CUT BY A SCRIPT*: "the
builder writes the script and records which recovery it used in the stamp."

**What happened.** r005_a4_window.py has no per-page mode: any re-run (here,
to pick up a program fix) re-cuts all 166 pages and silently puts the WRONG
automatic windows back on p009 and p142. My first p142 recovery had been an
inline run, so it could not have been replayed. `recover_005b.py` now holds
both pages, re-copies the CURRENT automatic window to `a4600_auto/` each time,
and refuses to run on an a4600 that already holds an OVERRIDE.

**What it cost.** ~10 min to fold p142 into the script after the fact.

**Suggested.** "The recovery script lives in `<tmp>`, covers every recovered
page, is idempotent (refuses on a4600 that already carries OVERRIDE), and is
re-run after EVERY r005_a4_window.py run — that program re-cuts every page and
restores the wrong automatic windows. Record its path in LOG.md."

## 040 — the script has no listing-line test, and the rule's test misses assembler banners

**What the rule says.** "Test the line, not the run: it is a listing line if it
begins with a line number, or carries `PRINT` / `REM` / `POKE` / `SYS` / `DATA`
or a checksum `<NNN>` token. In a listing line, escape both."

**What happened.** The script pairs `**` within a line and has no listing-line
test, so two literal pairs survived its run and its own summary (`**bold**
pairs=0` — the pair regex cannot span the `\*` between them). Only the rule's
per-line `**` readout showed them:
- l.4383 `100 REM \*%** DATEN SCHREIBEN \*%**` — line number AND `REM`; the rule
  says escape, the script did not.
- l.4687 `**%\* STRING EINLESEN %%**` — an assembler section banner just before
  its fenced listing: no line number, no BASIC keyword, so even the rule's test
  misses it.
Both escaped (4 `**` → `\*\*`) on exactly those lines, from the orchestrator;
Discount then renders the asterisks literally (probe run).

**What it cost.** ~5 min.

**Suggested.** Implement the listing-line test in `r040_escape_asterisks.sh`,
and widen it: "…or the run sits in a banner line — the line is nothing but
`*`/`%`/`#`/`;` runs around ≤ 4 words in capitals — which is how listings mark
sections (SH8608 l.4687)."

## 060 — the wrapper's post-pass calls bare `python3`

**What happened.** r060_md_to_html.sh's fenced-code post-pass invokes `python3`
by bare name; CLAUDE.md and r000 require the repo venv. The sub-agent ran it
with `.venv/bin` first on PATH so `python3` resolved to the venv. r000's
`"$PY"` sweep fixed the Verification fences, not the wrappers' bodies.

**Suggested.** `PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"` at the top
of r060_md_to_html.sh and every other `.sh` here that calls python, and grep the
wrappers for a bare `python3` as part of r000's census.

## 080 — an open question in a rule is scoped by the sentence that introduces it

**What the rule said.** r080, *Eingabehinweise beside the Checksummer — AN OPEN
QUESTION, NOT A PRECEDENT*: "a later issue meeting this shape goes to the owner".

**What I did.** SH8608 prints the Checksummer on p129 and *Wie unsere
Basic-Programme einzugeben sind* on p130, two Inhalt lines, nothing shared.
The heading's SUBJECT (Eingabehinweise + Checksummer) matched, so I asked
control and built the reversible default (two articles) meanwhile. Control:
the corpus has shipped this exact shape 15+ times, never folded; what made
SH8603 hard was its GEOMETRY (shared page with a third article, its figures
printed on the Checksummer's page). Rule fixed in `a865bc40` with a
discriminator table.

**What it cost.** One round trip, no rework (the default was right).

**Suggested.** A general sentence in r000 or r340: "When a rule records an
open question, introduce it by WHAT MADE IT HARD (here: the piece shares a page
with a third article and its figures sit on another article's page), never by
its subject. A question scoped by subject catches every later issue that shares
the subject and none of the difficulty."

## 080 — the splitter wrapper also calls bare `python3`

Same class as r060's entry: r080_split.sh's embedded splitter runs as bare
`python3`. It worked only because it is stdlib-only. **Suggested.** the same
`PY=` line in every wrapper, and r000's census to cover wrapper bodies.

## 090 — three small defects the sub-agent hit

**Procedure step 1's fence is broken:** the `for p in 6 7; do` loop is cut off
by a nested ```bash block (the venv/SRC recipe pasted inside it), so the page
loop cannot be copied as written.

**Verification check 2 counts the commented-out placeholder** `<!-- <meta
name="64er.toc_category" content="XXX"> -->` that 080 writes, so before step 100
it always prints `missing from toc.txt: 'XXX'` — a check that fails on correct
output at the step it belongs to. Strip comments before matching (r000, *A check
that matches MARKUP also matches comments ABOUT markup*).

**"record both" is ambiguous** for a Sonderheft with no printed Rubriken box:
it does not say whether `Rubriken` goes into `toc.txt` for the Impressum. The
agent followed SH8602-05 (it does, last). **Suggested.** "A Sonderheft with no
Rubriken box still lists `Rubriken` last in toc.txt, for the Impressum (SH8602-
SH8605, SH8608); toc_entries.txt gets no line for it, since nothing is printed."

## 120 — check 3b splits on the closing dash bar, and TEDMON code at $1001 is not a routed case

**What the rule says.** Checks 3 and 3b split sections on `"----+…"` separators;
*Four cases the extractor does not route correctly* lists the misroutes.

**What happened.** SH08.D64 frames every section as `****` / `---c16-NN` /
`-- name --` / `----------------`. The all-dash CLOSING bar also matches the
split pattern, so 3b reported "SEPARATOR CARRIES NO PAGE NUMBER" for 9 sections
and its mapping was unusable; the agent re-keyed on the last NUMBERED separator.
Separately, four files at load address $1001 with no BASIC stub (TEDMON monitor
listings, article 87) were decoded as BASIC garbage; the fix came only by way of
check 4 case 2 → Remediation, and Remediation's display choices (Hypra-Ass /
MSE) may not fit a monitor listing.

**What it cost.** ~10 min of the sub-agent's run.

**Suggested.** 3b: "a section's page is its last NUMBERED separator; an
all-dash bar is a frame, not a section". And a fifth routing case: "machine code
at a `…01` load address with no BASIC stub (C 16 TEDMON at $1001, VC 20 at
$1201) — promote to .prg; how to DISPLAY it is 130's decision from the print."
Also: the rule asks for a LOG.md re-apply checklist, which a sub-agent confined
to `prg/` cannot write — say "return it in the report; the orchestrator logs it".

## 130 — check 6 assumes every printed "Listing N." has a description; and check 5 keeps a `<YYMM>`

**What the rule says.** Check 6 FAILs a `Listing N` caption with "nothing after"
it, on the claim that every printed caption carries a trailing description.

**What happened.** Basic-Kurs (p32/p34/p36) prints "Listing 4a", "Listing 4b",
"Listing 5" BARE — confirmed on the crops. Three FAILs on correct output.
Also: check 5's site-build line still reads `<YYMM>` after the documented
`issues/<YYMM>` substitution (`line 80: YYMM: No such file`), and r130 step 5
("remove the placed block from prg.txt") cannot be done by two parallel agents
sharing one worklist — the orchestrator did it after both, having proved every
non-intro filename was placed.

**What it cost.** ~5 min.

**Suggested.** Check 6: "bare `Listing N` is a FAIL only if the page prints a
description; a bare printed caption is `look`, confirmed on the crop (SH8608
Basic-Kurs)". Use one `$ID` variable for every `<YYMM>` in the block. And in
step 5: "when placement is split across agents, prg.txt is read-only to them;
the orchestrator removes placed blocks afterwards, after diffing worklist
filenames against placed `data-filename`s."

## 130 — a printed TEDMON dump WITH a disk file: who builds it, and the ASCII column

Both 130 agents generated the `<pre>` from the disk and checked it against the
print, and both dropped TEDMON's `:`+reverse-video ASCII column (SH8603/165 did
the same). The rule says the `<pre>` "carries the dump as printed" but not who
produces it (130 or 170) nor what happens to that column. **Suggested.** "A
TEDMON dump with a disk file is built at 130 FROM the file and checked row by
row against the print; the reverse-video ASCII column is dropped (unreadable,
derivable); differing bytes are a print/disk difference (r300)."

## 160 — a named box's intro text, and section rows inside one captioned box

**What the rule says.** "The `<figcaption>` ALWAYS goes BELOW the table"; "a
spanning header row that labels a section is a heading, not a row … only labels
that group *rows within* one table … stay as a spanning `<th>`".

**What happened.** p130's and p146's boxes print intro sentences inside the box
above the table; the agent used the figure-series clause and put them as `<p>`
inside the `<figure>`. p150's box has five section labels inside ONE ruled,
captioned box; splitting them into `<h2>` would have broken the figure, so they
stayed spanning `<th>`. Both readings are reasonable; neither is stated.

**Suggested.** "Text printed inside a named box above its table is a `<p>` inside
the `<figure>`, before the table. Section labels inside ONE ruled box under ONE
caption are spanning `<th>` rows — the heading rule is for labels that sit
between separate tables."

## 170 — an emulator test of a loader that WRITES to disk needs true drive emulation

**What happened.** With VICE's default fast-disk traps, the VC 20 format
loader printed `DATAS OK` but wrote 4 wrong bytes (+2 each at offsets 91, 273,
596, 816). With `-drive8truedrive` the written file is byte-identical to the disk.
A passing screen message over a corrupted output file.

**Suggested.** In r000's emulator recipe: "a program that writes a file is tested
with `-drive8truedrive`, and the written file is read back with c1541 and
compared — the screen alone does not prove the write."

## 170 — two listing types the table does not name, and VC 20 load addresses

r170's table of what becomes a disk file names Checksummer BASIC / MSE hex /
monitor dump / own format with row sum. SH8608 also had a DATA loader with ONE
total sum (79) and an input program with no sums (110); both were made prg files.
And the corpus is inconsistent for VC 20 BASIC load addresses (SH8501 $1201,
SH8503/SH8505 $1001/$0801, SH8603 tacco $0801). **Suggested.** add "a printed
BASIC program the disk lacks" as the general row, and "VC 20 + ≥8K BASIC at
$1201 unless the article POKEs otherwise".

## 180 — a Sonderheft whose own Impressum carries the editor key, in "Name (xx)" form

**What the rule says.** "For a Sonderheft, resolve against the nearest MONTHLY
Impressum instead" — "MEASURED over the corpus … 0 of 12 Sonderhefte do"; the
check greps `\b[a-z]{2} = [A-ZÄÖÜ]`.

**What happened.** SH8608's Impressum lists `Achim Hübner (ah), Karsten Schramm
(ks), …` — the key, in the other form; the grep finds nothing. The agent used
this issue's own Impressum with a `(xx)` grep. Also: the SILENT/UNDEFINED
one-liner keeps only the last slash token, so `tr` in `Name/tr/bj` reads SILENT;
check #3 needs a `<PREV_DIR>` that is undefined for a Sonderheft and matches
recurring rubrics by exact title.

**Suggested.** "Read the key from THIS issue's Impressum first, in either form
(`xx = Name` or `Name (xx)`); only if it has none, the nearest monthly's. Split
every slash token, not only the last. For a Sonderheft, PREV_DIR is the
previous Sonderheft, and match recurring rubrics by id, not title."

## 190 — two internal contradictions, reported independently by all three 190 agents

**1. Aside heading level.** *Set-off boxes*: "The aside's heading is an
**`<h2>`**". Later: "An aside's heading is one level below the article's highest
section heading … `h3` when the aside would otherwise be the only `h2`". All
three agents quoted both; it happened not to matter (10, 47, 94 have `<h2>`
sections). **Suggested.** delete the absolute sentence; keep the relative one.

**2. Dash lists.** Step 4: "Convert prose-looking enumeration to `<ul>`/`<ol>`
**only** when the print shows a real bullet glyph" — read literally, a printed
"–" IS a glyph. *Where PRINT and CORPUS PRECEDENT disagree*: dash lists stay
`<p>— …</p>` (8609–8611, the 8612 ruling). All three followed the precedent.
**Suggested.** step 4: "…only when the print shows a bullet (•); a printed dash
list stays `<p>— …</p>`, a numbered list interrupted by prose becomes numbered
run-in paragraphs".

**3. The closing-run check cannot express "the printed text ENDS in a table".**
157's Plachetta item ends in two tables then its byline, exactly as on p158; the
check (and r310) call it "table splits the byline from its text". Moving the
tables would separate them from the sentence they belong to. **Suggested.**
"a table that IS the last printed element before the byline stays; adjudicate
it, citing the page".

**What it cost.** Nothing to rework; each agent spent time quoting the conflict.

## 200 — check 2 assumes every Q&A page prints a banner

**What the rule says.** Briefing steps 2–3 crop the "envelope / letter motif at
the top of page <START>"; check 2 requires `<header>` + `<img src="<START>-0.png"`;
the only escape is "A BANNER NOT CUT YET IS NOT A FAILURE -- it is PAUSE 2 work".

**What happened.** SH8608 p8 (like SH8605/155) prints only the plain LESERFORUM
running-head bar — no motif. Check 2 is a permanent FAIL on correct output.
Also unstated: what to do with a question already `<strong>` from 190 (dropped,
per precedent), and that a non-rubric Q&A's head1 must be set here since 210
leaves Leserforum's alone.

**Suggested.** "Check 2 applies only where the page prints a banner motif; a
plain running-head bar is head1, not a banner."
