# SH8605 — workflow errata

Where these rules failed this build, written as it happened (r340).

## r000 — a note FROM THE OWNER in the scan directory is neither a master nor a tool's leftover

**What the rule says.** r000, *THE NAME VARIES, THE RULE DOES NOT*: "Every derived artefact
you find in the scan directory is untrusted, whatever it is called … treat anything that is
not a `NNN.png` master as something a previous tool left behind."

**What I did with it.** `/Volumes/S/png/SH8605/` holds `00README.txt`: "160 missing from scan,
still have to be done!". Read literally, the rule makes it a tool's leftover to ignore. But it
is a human note about the INPUT, and if true it would mean `160.png` is a placeholder or a
duplicate, which is exactly what the chain cannot see. So I checked: `160.png` is dated
2025-10-16, four weeks after the README and every other master (2025-09-21), its md5 matches no
neighbour, and its footer reads folio 160 at the outer edge with the text continuing from 159
into 161. The note is stale; the page was scanned later, under different conditions (no
yellow prop at the foot).

**What it cost.** ~3 min, 3 commands. Cheap because I looked; free to miss had I applied the
rule as written.

**Suggested.** Add to r000 after "treat anything that is not a `NNN.png` master as something a
previous tool left behind": *"Except a note a human left — a `README`, a `.txt` in prose. It is
not an input, but it is a claim about the input: read it, and check the claim against the
masters it names (date, md5 against the neighbours, the folio in the footer) before the sweep.
SH8605's said page 160 was missing; it had been scanned four weeks later and the note never
removed."*

## (control relay) — "201 masters" counted the README

Not a rule defect; recorded because it would have mattered. The relay said `/Volumes/S/png/SH8605`
has 201 masters; it has 200 `NNN.png` plus `00README.txt`. The owner's "last 6 pages" is
therefore 195–200, not 196–201. r000's verification already counts `[0-9][0-9][0-9].png`, which
is right; the count in a message is not.

**Suggested.** None to the rules; the relay should count with the same glob the rules use.

## r005 — the dpi witness measures COLOUR, not stock

**What the rule says.** r005_masters_sheet, *What the step offers as evidence*, witness 2:
"**The scan resolution.** MEASURED on SH8602, SH8603 and SH8604: the pages scanned at 2400 dpi
are EXACTLY the wrapper and the card, the interior at 600."

**What I found.** SH8605 has 24 masters at 2400 dpi: the 8 good-stock pages AND 16 interior
pages (006, 007, 017–021, 024–026, 028–030, 032–034). Taken as stated, the witness puts 24
pages on the good stock.

**The cause, from the owner (2026-10-06, relayed):** *"several pages were color, for which i
was using 2400 dpi. but you dont have to treat them differently other than through dpi."* The
owner scans COLOUR pages at 2400 dpi. On SH8602–SH8604 the only colour pages happened to be the
wrapper and the card, so the witness looked like a stock marker; on SH8605 sixteen interior
pages are colour too. **The witness is not unreliable, it measures the wrong property.**

**And it contaminates witness 1.** A 2400 dpi scan reads the SAME paper ~30 city-block
whiter. Proved per leaf, where both sides are one physical sheet: 21/22 reads dist 29 on the
2400 side and 3 on the 600 side; 27/28 36 vs 2; 23/24 31 vs 4; 31/32 31 vs 9. So the own-white
gap on a mixed-dpi issue has a second population at 27–39 — and the cover p001, whose "own
white" is full-bleed art, lands at 41, inside that band. Sorted by distance alone, p001 does not
separate from the 2400 dpi interior pages; its leaf partner p002 (166) settles it.

The 16 are `low`, with no separate grade or class — the owner's second clause. (W does not
move with or without them: 64er_control recomputed p2 both ways, 189 169 158, over 22.6 M and
20.8 M paper px.)

**What it cost.** ~10 min, 4 commands.

**Suggested.** Replace witness 2 with: *"The scan resolution marks COLOUR, not stock — the
owner scans colour pages at 2400 dpi. On SH8602–SH8604 that was exactly the wrapper and the
card; on SH8605 it was those 8 plus 16 interior colour pages. A 2400 dpi scan also reads the
same paper ~30 city-block whiter than a 600 dpi one (SH8605, leaves 21/22, 23/24, 27/28,
31/32), so on a mixed-dpi issue read the own-white gap per dpi, and settle any page in doubt
against its leaf partner (n/n+1): one sheet of paper cannot be two stocks. A colour interior
page is `low` like any other; dpi is its only difference."*

## r005 — the edge-finder pre-fill missed a card page outright (rule saved me)

p198 (Zahlkarte) has paper frac 0.116 against `FULLBLEED_PAPER_FRAC` 0.10, so the edge finder
did not offer it. The rule's warning that the pre-fill is one-sided and must be unioned with the
own-white gap is exactly what caught it (dist 91). Recorded as a rule earning its length.

**Suggested.** Keep the warning verbatim through any harvest that shortens r005, and add this case as
its evidence: *"SH8605 p198 (paper frac 0.116 vs 0.10) was offered only by the own-white gap."*

## 005b — no runnable Verification, no Run section, and an env knob the rule never names

**What the rule says.** r005_a4_window.md's `## Verification` is four prose items ("Every body
page is exactly 4961 × 7016 px", "The anchor lands on the glyph — check the overlay…"). r000:
"Every rule `.md` in this directory **must** include a `## Verification` block with at least one
runnable check." The rule has no Run section either, and r005_masters_sheet says "No CLI knobs,
no env knobs" — but `r005_a4_window.py` reads `FILL` (`paint` | `mirror`, default `paint`) and
`A4_OUT` from the environment.

**What I did with it.** Read the program's `main()` to learn the invocation (no arguments =
measure and fit every page in `sheets600`, cut all), and SH8604's git-ignored `LOG.md` to learn
which `FILL` a build uses (the default, `paint`) and what its verification looked like in
practice. Neither is reachable from the rule: the next build without SH8604's LOG.md on disk
has neither.

**What it cost.** ~5 min, 4 commands.

**Suggested.** Add a `## Run` section: *"`$PY r005_a4_window.py` with no arguments measures
every page in `sheets600`, fits one (S, B) per parity, and cuts every page to `<tmp>/a4600`.
`FILL` defaults to `paint`, which every sheet issue so far has shipped; `mirror` is the
experiment r005 *The fill* describes and is not the default. `A4_OUT` redirects the cut for a
comparison run."* And make Verification 1, 3 and 4 runnable: a size census of `a4600`, the
foot-strip stack per parity (SH8604's LOG did it by hand: 040/060/080/120 and 041/061/081/121),
and the `fabricated` p50/p95/max the program already prints.

## r005 — the Verification block uses two interpreters, one of them undefined

**What the rule says.** r005_masters_sheet `## Verification` opens with `cd tools/img/scan2ocr/rules`
and runs checks 1–5 as `python3 - <<'PY'`; check 6 (rewritten in the SH8604 harvest) runs
`$PY - <<'PY'` and does `sys.path.insert(0, 'tools/img/scan2ocr/rules')`, a repo-root-relative
path. `$PY` is defined nowhere in the block, and bare `python3` is what r000 (*THE PAGE IMAGE
IS masters600*: "The repo venv, not bare python3 … MEASURED on 8611") and CLAUDE.md forbid.

**What I did.** Extracted the block, substituted `../../../../.venv/bin/python` for `python3`
in 1–5, and ran 6 separately with `PY` set. Pasted verbatim, 1–5 would run on the system
python and 6 would run `- <<'PY'` as a command (`$PY` empty) and fail.

**What it cost.** ~2 min, 1 command.

(The same in r010's Verification: it defines `PY` and uses it for the first two checks, then
runs check 3 as `python3 - <<'PY'`, which imports numpy through `r010_ocr_blocks`.)

**Suggested.** First line of the block: `PY=../../../../.venv/bin/python   # the repo venv; never bare python3`,
then `$PY -` in all six checks, and drop check 6's `sys.path.insert` (the block has already
`cd`'d into the rules dir).

## 005b — I read "recoveries" as automatic; the rule says they are not (rule fine, I was not)

**What the rule says.** r005_a4_window.md: "The three below are RECOVERIES for a page whose
trace failed outright … **they are not in the code** … the builder writes the script."

**What I did.** After 005 left p035 and p198 uncropped I reported to control that both had
"automatic recoveries in 005b". I had read the section heading — *A PAGE WHOSE TRACE FAILS IS
STILL CUT AUTOMATICALLY — NEVER BY HAND* — and not the NAMING paragraph under it. "Automatically"
there means "by a script, not by a person's crop"; it does not mean "by r005_a4_window.py".
Control caught it before 005b finished.

**What it cost.** One wrong report; ~2 min to correct. Would have cost a shipped page with bed
in it, since the 005b summary cannot see this failure (the rule's own SH8604 p163 measurement).

**Suggested.** Change the heading to *A PAGE WHOSE TRACE FAILS IS CUT BY A SCRIPT — NEVER BY
HAND, AND THE SCRIPT IS YOURS TO WRITE*, so the heading alone cannot be read as "the program
handles it". The body is right as it stands.

## r000 — the wrapper-header recipe only works from the rules directory

**What the rule says.** r000, *And the WRAPPERS are code, so run them*: "run its HEADER —
everything above the first `seq`/`xargs` — … `sed -n '1,/^seq /p' rNNN_step.sh | sed '$d' | bash`.
It exits 0 and prints the lane line, or the edit is not finished."

**What I did.** Ran it from the repo root on `r010_ocr_blocks.sh`. It printed
`/Users/…/64er-magazin.de/../../../../.venv/bin/python: No such file or directory` and **exited
0** (the failing line is in a `$(…)`, and the pipe's status is `bash`'s). Piped, `BASH_SOURCE[0]`
is empty, so the wrapper's `DIR="$(cd "$(dirname …)" && pwd)"` resolves to the CURRENT directory,
and `PY` to a path four levels above it. From `tools/img/scan2ocr/rules` it works and prints the
lane line. So the recipe's own pass condition ("exits 0") passed on a broken run.

**What it cost.** ~2 min, 2 commands.

**Suggested.** *"Run it FROM `tools/img/scan2ocr/rules` (piped, the wrapper's `BASH_SOURCE` is
empty and `DIR` becomes the current directory), and judge it by the lane line it prints, not by
the exit status — a failing `$(…)` inside the header still exits 0."*

## r020/r030 — nothing says the model-call steps must not overlap (rule gap, and my mistake)

**What the rules say.** r000 *NOT for model-call steps*: "four concurrent processes sharing one OAuth
file once took out pages 84-176 of an overnight run. Their `LANES = 4` is a different constant". That
is about lanes WITHIN a step. Nothing says two model-calling steps must not run AT ONCE.

**What I did.** Started r020's Verification (`r020_evaluate.py`, ~200 vision calls) in the
background and r030 (boundary call + hyphen batches) beside it, to save wall-clock. The evaluation
hit the session limit 148 times and scored 52 pages; r030 died in `dehyphenate()` on the same limit.

**What it cost.** Both steps re-run; ~20 min of model time spent for nothing, plus the wait for the
reset.

**Suggested.** In r000 under *NOT for model-call steps*: *"And never run two model-calling steps at
once — 020, 020's evaluation, 030 and 145 share one credential and one session allowance, and the
cheaper one is the one that gets starved. Run 020's evaluation AFTER 030, or not at all if the
allowance is tight; it is a score, and the chain does not read it."*

## r040 — two `**` in one OCR'd listing line "pair", and the bold-pair check cannot see them

**What the rule says.** "length == 2 → keep **only if it pairs within the paragraph**". Verification:
`'**bold** pairs : …'` with `\*\*[^*]+?\*\*` — "invariant by construction".

**What happened.** SH8605 l.2377 `20 PRINT"*%**%%* ZAHLEN RATENXXRX**` and l.3692 (a whole checksummed
BASIC listing in prose, `18 REM #**#*#* … #*%* ** <202> 28 POKE …`) each hold exactly two literal
`**`. Two in one paragraph pair, so both were kept as bold delimiters, and 060 would have wrapped
listing text in `<strong>`. The bold-pair check read **0** on both, because its pattern cannot span the
escaped `\*` that sits between the delimiters. The sub-agent found them by reading the diff; I escaped
them by hand.

**What it cost.** ~3 min.

**Suggested.** In r040's rule: *"A `**` pair is bold only if what it encloses is prose. Two `**` in a
line that is a BASIC/listing line (it begins with a line number, or carries `PRINT`/`REM`/`POKE`/
checksum `<NNN>` tokens) are literals: escape both."* And in the Verification, count **every**
unescaped `**` outside fences (`(?<![\\*])\*\*(?!\*)`) and print each line it sits on — a pair count
that cannot see a pair is the "check that never fires" r000 warns about.

## r060 — "`<br/>` > 0" fails on an issue that has nothing for `-G` to break

**What the rule says.** "A line ending in a single LF inside a paragraph becomes `…<br/>`" and
`grep -c '<br/>' … # >0`, with the SH8603 story of a loose grep passing when `-G` had not run.

**What happened.** SH8605's HTML has **0** `<br/>`. The sub-agent proved `-G` works (a two-line
probe through the same flags gives `Zeile eins<br/>`) and that this .md has no soft-wrapped prose
pair left: every adjacent-line pair ends in a hand-written `<br>` (the "Im folgenden Listing…"
source notes) or is a list item. So the check fails on correct output — the shape r000 calls worse
than no check, because it gets "fixed" by changing the transform.

**Also:** Discount 3.0.2.0 no longer produces `<p><pre>` for the rule's own example (fed raw: 0), so
that grep is a regression backstop now; and the `<strong>` "~90+" spot-check is 8607's number (0 here,
correctly — no bold in the source).

**What it cost.** ~2 min (the sub-agent's probe).

**Suggested.** Replace the `<br/>` expectation with a probe that cannot depend on the issue:
*"`printf 'Zeile eins\nZeile zwei\n' | markdown <the script's flags>` must print `<br/>`. Then count
`<br/>` in the issue as a readout — it is 0 on an issue whose .md has no soft-wrapped prose."*

## r070 — U+201A has more than three readings

**What the rule says.** *U+201A is never correct here*: "an OCR error, but of three different kinds"
— comma, opening quote, noise.

**What happened.** SH8605 resolved 38 sites against the page and two were none of the three: a
**semicolon** (p27, `PRINT"FEHLER IN SEKTOR: ";TAB(20)ES`) and the PETSCII **back-arrow** (p168,
`←A Anfangszeilennummer`). Both are BASIC/monitor punctuation that tesseract has no glyph for. The
rule's "resolve each against the page" was what got them right; the table nearly suggested the wrong
answer.

**Suggested.** Add to the table: *"| any other punctuation the OCR has no glyph for — `;` in a
`PRINT` list, PETSCII `←` | `";TAB(20)` (SH8605 p27), `←A` (SH8605 p168) |"* and end the section:
*"The table is what has been seen, not what can occur."*

## r080 — check 4 accepts the spaced separator its own rule forbids

**What the rule says.** *WHICH PAGES BELONG*: "The separator is a bare comma, no space … and
Verification 4's character class accepts a space, so nothing catches the drift." Check 4:
`grep -vE 'content="[0-9a-z,\- ]+"'`.

**What happened.** The script copies the h1's spec verbatim, and 030 writes it SPACED
(`[30-34, 36-38]`, `[90, 92-97, 100]`), so SH8605 got four spaced specs from the script; the
sub-agent rewrote them by hand. A planted `content="90 - 97"` passes check 4 silently. The rule
documents the gap instead of closing it.

**Suggested.** Check 4: `grep -vE 'content="[0-9a-z,-]+"'` — no space in the class (verified on SH8605
to fire on the planted `90 - 97` and stay silent on the issue). And either 030 or the splitter should
write the bare comma, so no build has to.

## r020 — the Impressum rebuild names a shape the previous issue does not have; and the gate passed a 0.19

**What the rule says.** *The dropped Impressum*: "in the shape of the **previous issue's** Impressum
(same head metas, same `<article class="impressum">`, same `<p><em>Label: </em>value</p>` run…)".

**What happened.** SH8604's Impressum (the previous issue) has a plain `<article>` and
`<p><strong>Label:</strong> value</p>` with `<hr>`; SH8603 uses `<em>Label: </em>`; SH8601
`<strong>Label</strong>:` with one `<hr />`. There is no house shape, and the rule's example is none
of the three's. The sub-agent followed "the previous issue's" over the example, which is right.

**Second, worse:** r020's gate ("a page that carries three or more DISTINCT masthead labels must keep
blocks") PASSED SH8605's p194 — 8 labels, 20 blocks kept — while the corpus had lost the Herausgeber
line and interleaved the rest. Only `r020_evaluate.py` (recall 0.19) showed it, and two builds
(SH8603, SH8604) left that evaluation "pending".

**What it cost.** One sub-agent rebuild (~2 min) — cheap because it was found at 080, not by a reader.

**Suggested.** (1) Replace the example with *"in the shape of the previous issue's Impressum —
open it and copy its markup; the corpus has used `<strong>Label:</strong>`, `<em>Label: </em>` and
`<strong>Label</strong>:`"*. (2) Strengthen the gate: *"…and the masthead page's kept text must carry
EVERY masthead label its block index shows"* — a label present in `blocks/pNNN.txt` and absent from
`NNN.article.txt` is a HARD fail. (3) Say that `r020_evaluate.py` is not optional: its WORST.txt found
the one real defect of this build's first four steps.

## r120 — check 3 cannot see a lost mid-disk separator, and a wrong `;version=` tag can round-trip clean

**What happened (sub-agent, planted on copies under `<tmp>/scratch_120/plant/`).** (1) Removing the
"6" separator raised check 3's orphan count 1 → 4, but removing a MID-disk separator ("77") let its
files fall silently under the previous one (69) and the count stayed at 1: check 3 only sees files
BEFORE the first separator. (2) A wrong `;version=3` tag on a V2 file round-tripped byte-identical
(`huellkurve`), because the program uses no token the two dialects disagree on — so check 4 cannot be
the evidence that a dialect is right.

**Also:** the LOG section the sub-agent wrote said the print/disk differences were "listed for PAUSE 2
in the step report" — which exists only in the conversation. I copied them into LOG.md.

**What it cost.** Nothing on this disk (every separator was checked by hand against `64er.pages`).

**Suggested.** Check 3: *"for each separator, the files under it must belong to an article whose
`64er.pages` contains that separator's page — print separator → files → article and look"*, not an
orphan count. Check 4: *"a clean round trip proves the bytes, not the dialect; decide the dialect by
decoding with `-2` and the candidate and diffing the two texts"* (which is what the sub-agent did).
And r120's report section: *"write the print/disk differences INTO LOG.md, one per line, as owner
decisions — never 'see the report'"*.

## r140 — check 3 still pipes its findings into `head -5`; and a reprint "tie" the rule already settles

**What happened.** (1) Check 3 ends `| head -5`, which r000 (*A CHECK SHIPS ONLY ONCE IT HAS BEEN SEEN
TO FAIL*) forbids: six bad ids would show as five. (2) The sub-agent called Hypra-Save a tie between
8508's `hyprasave` and SH8506's `hypra-save` (both 0.87 overlap) and broke it toward the title. The
rule had already decided it — a Sonderheft reprint takes the MONTHLY ORIGINAL's id — but the overlap
score cannot tell an original from an earlier reprint of it, so both looked equal. (3) The brief
limited the sub-agent to meta lines, so it could not write `reprints.txt`, which the rule assigns to
"whichever step runs the overlap pass first" — me, at 140.

**Suggested.** (1) Drop `| head -5` from check 3. (2) In *Check 4 CANNOT see a reprint*: *"When the
overlap finds the same text in several issues, the ORIGIN is the earliest MONTHLY among them — an
earlier Sonderheft carrying it is a reprint too, and its id does not count as a second vote."* (3)
*"The step that runs the overlap pass writes `reprints.txt`; brief the sub-agent to write it."*

## r200 — the header says `monthly`; the body says "any reader-question article"; a Sonderheft prints a band named Leserforum

**What the rule says.** Header: "**Applies to:** monthly — … `ls issues/SH85*/*eserforum*` is empty and
`grep -l 'article class="qa"' issues/SH85*/*.html` finds zero files." Body: "**THE Q&A SHAPE IS NOT
THE LESERFORUM'S ALONE** — this anatomy is the project's shape for **any** reader-question article", with
the warning that such an article "can pass the whole chain unrestructured".

**What I found.** SH8605/155 *Fragen & Antworten* is a reader-question article (each question with the
reader's name, then the answer), and the printed Inhalt files it under a band named **"Leserforum"**.
The header's evidence tests filenames in SH85xx only — it rules out a FILE NAME, not the input (exactly
the SH8601/220 mistake r000 *The evidence must rule out the INPUT* records). SH8603's *Fragen und
Antworten* shipped as a plain `<article>` with 0 `div.q`, which looks like the body's predicted miss.

**What I did.** Stopped before 200, asked the orchestrator (r000: a non-empty evidence line means the
header is wrong — stop, don't run behind the contract's back), ran 180 on the other 32 articles.

**Suggested.** Re-classify: *"**Applies to:** all — the Q&A shape is for any reader-question article;
a Sonderheft's is usually not called Leserforum (SH8603 'Fragen und Antworten zum C 16 und VC 20',
SH8605 'Fragen & Antworten' under a printed Leserforum band). The monthly Leserforum metas (head1,
`Rubriken`, id `leserforum`) are the monthly's; a Sonderheft's Q&A keeps its own."*

**Resolved mid-build (the rule moved under this build — r340's blocking-defect exception):** the
orchestrator re-classified r200 to `all` in `037862ad`, before 200 ran on SH8605. Two things worth
keeping from it, in the orchestrator's words: (1) the header's second piece of evidence was CIRCULAR —
no Sonderheft carried `class="qa"` *because this header told every Sonderheft build to skip the step*;
"nobody does X" is void evidence when the rule under review is what stops them. (2) The valuable half
is not "r200 said monthly": **a rule's header and its body disagreed, and the header is what gets read
first.** A build that trusts the header never reaches the warning in the body.
**Suggested (general, for r000 *`Applies to:`*):** *"When a rule's header and its body disagree, the
header is wrong until shown otherwise — and an `Applies to:` whose evidence is an absence the rule
itself caused is not evidence."*

## r200 — its Verification still hard-codes the Leserforum after the rule became `all`

**What happened.** On SH8605/155 r200's check reported `FAIL: head1 meta`, `FAIL: toc_category`, `FAIL: id
meta`: it requires `head1=Leserforum`, `toc_category=Rubriken`, `id=leserforum`. Those are the MONTHLY
rubric's values; the re-classification (037862ad) made the rule apply to any reader-question article,
whose head1 is its own running head ("Fragen & Antworten"), whose category is wherever the print files
it, and whose id follows its subject thread. Three permanent FAILs on correct output — r000's "a check
that fails on a good result gets fixed by undoing the transform". Also: the rule has no path for a
banner not cut yet (pointing `<img>` at a missing file would ship a broken image).

**Suggested.** Make the three meta checks conditional: *"only when the article IS the Leserforum
rubric (`64er.id=leserforum`); for any other Q&A article, check that head1 equals the printed running
head and that id/category were set by r140/r100"*. And: *"a banner not yet cut stays out of the HTML
(the `<h1>` remains) and goes on the crop worklist as `<page>-0.png`; the banner checks are deferred to
after PAUSE 2, like r150's."*

## r190 — its listing sweeps cannot see lowercase BASIC

**What happened.** r190's "broken-up listing" sweep requires `[A-Z]{2}` after the line number ("BASIC in
this corpus is CAPS"). SH8605's 101 *Dateiverwaltung für Einsteiger* prints its BASIC in lowercase
(`30 input "titel";t$(ad)`, `1 rem dimensionierung`) — 22 code regions sat in `<p>`, several glued onto
the end of a prose sentence, and the sweep reported 0. The part-B sub-agent found them by reading and
added a lowercase variant of its own.

**Suggested.** *"The CAPS test is a default, not a fact: a Sonderheft for beginners may print lowercase
BASIC (SH8605/101). Run the sweep a second time with `[a-z]{2,}` after the number and a BASIC keyword
list (`rem|print|input|poke|peek|goto|gosub|for|next|if|then|data|read|open|close|get`), and read every
hit."*

## r080 — a headline set ACROSS A SPREAD is checked on one page and truncated (my brief, and my check)

**What happened.** At 080 I briefed the sub-agent to crop "the headline from its start page" and
compare. SH8605's 20 prints "Die Ports" on p20 and "des C 64" on p21 in the same display type — one
headline across the spread. The sub-agent read p20 only, called the 030/Inhalt form "Die Ports des C64"
the Inhalt's wording, and shortened the h1 to "Die Ports"; I looked at the same one-page crop and
accepted it. 190 part A found the other half on p21. Fixed with a content edit + rename.

**What it cost.** One commit, the danger-zone rename; ~5 min. Would have shipped a truncated headline —
the exact defect r080's first paragraph exists to prevent.

**Suggested.** r080 *The `<h1>` is the printed headline, COMPLETE*: *"Read the headline off the SPREAD,
not the start page: a display headline can run across the gutter onto the facing page (SH8605/20 'Die
Ports' | 'des C 64'). Crop both pages' top halves side by side."*

## r220 — the routing check compares the CSV title unstripped, and a no-index_title row is invisible to it

**What happened.** (1) SH8605's row `Software-Test,Grafik,Grafikprogramme ,5/86,132,,` has a trailing
space; the rule says every cell is stripped, the apply script does strip it, the routing check does
not — so the row reported "matching no article" and also escaped the misroute test. (2) A row whose
title equals the article's `<title>` gets no `index_title`, so the check resolves it through `<title>`;
moving only its `index_category` to another file is invisible to both the routing check and the count
(the sub-agent checked all 22 single-row articles by hand).

**Suggested.** Strip `p[TITLE]` in the check; and route every row by its `index_category` LINE's file,
not by a title lookup — print `row → file that carries it` and compare with the nearest-preceding start.

## r250 — check 4 does not allow a `<table class="…source">` continuation

**What happened.** SH8605's 120 *Das Computerbüro* Info footer is `<p class="source">Info:</p>` followed by
`<table class="plain source">` (supplier / address pairs, built at 160 on the 8603/41 precedent). r250's
check 4 allows a source note to continue as `<ul|ol class="…source">` but not as a table, so it reports
"mid-section `<p class="source">`" on correct markup — a permanent finding on a correct issue.

**Suggested.** Add `table` to check 4's continuation allow-list (`(ul|ol|table)[^>]*class="[^"]*source`),
and say in the rule that a multi-column Info note is a `table.plain.source` (8603/41, SH8605/120).

## r000/r280 — a scanned copy can carry a previous reader's PEN corrections, and the OCR reads them as print

**What happened.** SH8605's copy has hand corrections in grey pen: p165 an `↑` drawn into a printed gap
in a listing line (the very misprint 8607's Fehlerteufelchen later corrects), p95 `2040` struck and `2041`
written over it. The chain transcribed the pen as print — the 164 listing read `6↑5` until step 300's
sub-agent zoomed in and saw grey ink. Nothing in the rules says a copy may be annotated.

**What it cost.** Caught at 300 by luck (an erratum pointed at the exact spot). Unknown how many others.

**Suggested.** In r000 *THE SCAN IS THE ONLY INPUT*: *"The scan is of ONE physical copy, and a copy can
carry a previous reader's corrections in pen or pencil (SH8605 p95, p165 — grey ink, often an erratum
applied by hand). Transcribe the PRINT, never the annotation: on a crop, pen is a different grey and
stroke weight from the black offset ink. When a listing line disagrees with the print by exactly what an
erratum says, look for pen first."* And in r325's brief: look for pen marks on every page read.

## r310 — the "closing run is a unit" check can never fire

**What happened (found by the r310-fix sub-agent).** Around lines 243–248 the regex
`<(…|p class="source"|address class="author")\b` needs a word boundary between `"` and `>`, where there is
none, so `<address class="author">` and `<p class="source">` never match and the check is silent on every
page. A planted figure between a last `<p>` and its byline was caught only by the separate byline-split
check. Fixing only the regex is wrong too: the check compares against any earlier figure/table/address,
not the element directly before, and with the regex fixed it reports 25 findings on SH8605, nearly all
false.

**Suggested.** Rewrite it to walk the article's top-level blocks in order and look only at what sits
directly between the last body `<p>` and the trailing `<address>`/`<p class="source">`; then plant both a
float and a correct closing run, per r000 *A CHECK SHIPS ONLY ONCE IT HAS BEEN SEEN TO FAIL*.

## r330 — the rule's six dispositions, the tool's four

**What happened (found by the r330 lane-B sub-agent).** r330 step 5 defines a closed vocabulary of SIX
dispositions — PRINT, OURS, THEIRS, MOVED, MARKUP, UNRESOLVED — and explains why MOVED and MARKUP were
added (SH8604's 93). `r330_reprint_compare.py:409` still has `DISPOSITIONS = {"OURS", "THEIRS", "PRINT",
"UNRESOLVED"}`, and the LOG table the tool parses positionally has four count columns. On SH8605's 135
Checksummer ← 8603/55 (14 differences: 10 MOVED — Tabelle 1 stored at a different point in the two HTML
files while both pages print it at the foot —, 1 MARKUP, 3 PRINT) a LOG written to the rule fails `verify`
twice: 11 lines outside the vocabulary, and the row's counts do not sum to D.

**What it cost.** The merge of step 330 waited on a decision the builder may not make: following the rule
fails the gate, passing it means writing PRINT where the rule says PRINT is false (MOVED is not "the printed
pages differ" — both pages print the table at the foot). Escalated to control.

**Resolved by control in 0aa71ed0:** `DISPOSITIONS` is the six; the LOG table is eleven cells (`… | MOVED |
MARKUP |`); a nine-cell row still verifies (SH8601–SH8604) but fails by name if it carries MOVED or MARKUP.
**The root cause is a harvest, not a lagging tool:** fc1e404f changed the rule's vocabulary without running
r340's own instruction — a harvest that changes a claim greps the rule set AND the code for the old one — so
a harvest introduced the very rule/tool split it exists to remove. The r340 line for that is control's.

**Suggested.** In r340 *A HARVEST THAT CHANGES A CLAIM GREPS FOR THE OLD ONE*: *"…and when the claim is a
closed vocabulary (dispositions, verdicts, kinds), grep the CODE for the set literal and change it in the same
commit, with the new word seen to pass verify."* (Control is writing its own r340 line; this is the builder's view.)

## r330 — the suspended-hyphen set lacks `bis`, so `Vier- bis Fünffache` is joined on both sides

**What happened (found by the r330 lane-C sub-agent).** `SOFT_HYPHEN` in `r330_reprint_compare.py`
(lines ~79–82) excludes the closed set `und|oder|bzw|beziehungsweise|sowie|wie|etc|usw` after a hyphen. `bis`
is not in it, so the range form `Vier- bis Fünffache` (SH8605 138's standfirst, as printed) normalises to
`Vierbis` on our side — and SH8505's published HTML, which really has the defect `Vierbis Fünffache`, then
normalises to the SAME string. The diff reported nothing: a THEIRS transcription error was hidden by the
normaliser, found only because the sub-agent read the page.

**Suggested.** Add `bis` (and check `zu`, `als`, `noch` style range/suspension words against the corpus)
to the set, with a planted `Vier- bis` vs `Vierbis` pair seen to produce a difference.

## r330 — `pubdate.txt` read as the original order; a lead pointing BACKWARDS in time had no verdict

**What happened.** Lane A's Step 0 found 114's tables shared with 8606/160 and 8607/92 and credited them as
originals ("Teilweiser Nachdruck aus 64'er 6/86 … 7/86"), reasoning from the site pubdates (SH8605
2026-10-31, 8606 2026-05-16, 8607 2026-06-14). Those are REPUBLICATION dates and invert the 1986 order; both
monthlies print this issue's errata (step 300), so both are younger. A false direction of copying would have
gone into a reader-facing credit. The orchestrator caught it on the errata evidence; none of the four verdicts
fitted (NOT-A-REPRINT skips the diff).

**Resolved mid-build by control in d3d01f15** (the rules moved under this build): new verdict `REVERSED`
(diffed like PARTIAL, no credit, one sentence on which issue is older and how known), and r330 now states that
`pubdate.txt` does not order the originals.

**Suggested.** Already landed. For the harvest: the strongest direction test is "who prints whose errata" —
put it in r330 Step 1 as the first check when a lead's original is near this issue's cover date.

## r000 — "commit by pathspec" silently commits the WHOLE worktree file, defeating a partial stage (rule fine, I was not)

**What happened.** 155 carried both cleared changes (three OURS fixes) and a held one (the reprint credit,
awaiting the owner). I staged only the fix hunks (`git apply --cached`), then committed with
`git commit -- <paths>` as r000 and the shared-worktree discipline require. A pathspec commit is `--only`: it
takes each named path FROM THE WORKTREE, so the held credit was committed too. Caught in the stat (46 lines
instead of 8), amended before anything else saw it (local, never pushed).

**What it cost.** Two commands to see, four to repair; nothing published.

**Suggested.** In r000's commit discipline: *"A pathspec commit commits the worktree version of each named
path, not the index. When a file holds changes that must NOT go in yet, write the file in the state you want
committed, commit it by pathspec, then restore the held change — never rely on a partial `git add`/`apply
--cached` together with a pathspec commit."*

## r310 — "tidy the line at 340" for an adjudication that belongs to another step's check

**What the rule says.** `r310_issue_invariants.py:553` prints, for every key in `adjudicated.txt` it finds fewer
instances of than declared: *"declared N, found M -- fewer than adjudicated; tidy the line at 340"*. r260 (lines
42–49) puts its own `heading-all-caps` adjudications in the same file, read with r310's loader by r260's check.

**What happened.** r310 has no `heading-all-caps` check, so it reports "declared 29, found 0" on every run and
tells the builder to remove the line at 340 — which would delete r260's 29 adjudications (the C 64 error
messages in 178, each checked on the page) and make r260's check fire again on the next run. Caught only
because LOG.md step 260 had recorded "informational, do not tidy it away"; at 340 the message reads as an
instruction.

**Suggested.** r310 reports the shortfall only for keys it CHECKS (its own key set), and lists foreign keys as
"owned by another step — not counted here"; or r310's message says *"tidy at 340 only if the key is r310's own
(see the key's owning rule)"*. Plant a foreign key to see it is not flagged.

## r150 — `r150_figure_captions.py` misses captions printed INSIDE a frame or on a tinted ground

**What happened.** The PAUSE 2 crop survey (every editorial page at 20 %, 600 dpi crops where needed) found
printed captions that `figure_captions.txt` does not list at all — **39** (counted from the worklist's "Missing from
figure_captions.txt altogether" list: 6 ×6, 20 ×2, 30 ×2, 40, 69, 77 ×8, 90, 101 ×4, 111, 149 ×10, 164 ×3; the
survey agent's summary said 46, which its own list does not support). Examples: 40 p57 "Bild 3. Ein Programm-Ablaufplan"
(caption inside a grey flowchart frame), 164 p175 "Bild 3. Ein normales Diskettendirectory" (caption inside
the framed screenshot), 30 p37 "Bild 15" (inside a shared print-sample frame), 149's sprite captions set two to
a frame. The extractor evidently takes captions from the block index's caption-like blocks, and a caption the
layout analysis folded into a figure/box region never reaches it. In the other direction three rows are false
IN_HTML: p106 "Bild 5." (matched the prose "(Bild 5)"), p151 "BILD 7" (a DATA line), p151 "Bild 11." (no figure).

**What it cost.** Nothing broke — the survey caught them — but a build that trusted the file as the crop list
would have handed the owner a worklist missing about a quarter of the figures.

**Suggested.** In r150 (first action) and the PAUSE 2 hand-over: *"`figure_captions.txt` is a lead, not the
worklist. The worklist comes from a look at every editorial page; captions printed inside frames or on tinted
ground are routinely missing from the file. A match on a prose reference `(Bild N)` or a DATA line `BILD N`
is not IN_HTML."* And in the script: require the match to be a `<figcaption>`.

## r330 — an unreadable original produced findings, not silence; a second reading of the same bad image cannot catch it

**What happened.** 8404 has no 2400 dpi scan, only its PDF's 150 ppi page images. Lane A read Tabelle 1 (pp122–123)
and the p17 Leserforum from those images and recorded **seven UNRESOLVED comma-vs-full-stop differences** in 90 ←
8404/119 that were headed for the owner as THEIRS candidates against 8404's published HTML, plus a THEIRS candidate
folded into a PRINT line (155 ← 8404/14 D-274, »vorbeziehungsweise«). The owner's method — render the PDF page at
300 dpi greyscale, autocontrast, crop the glyph at 3–6× — settled all of them in minutes: the seven separators are
FULL STOPS (8404's HTML is right; recast PRINT), and D-274's line-end hyphen is plain (8404's HTML is wrong; now
THEIRS). The blind second reading could not have caught the seven: both readers would have worked from the same
150 ppi image. Control codified the method in r330 (03660f0e) mid-build.

**What it cost.** Seven false accusations of a published file reached the owner's question list (D88) before they
were withdrawn; one real error sat under a PRINT label.

**Suggested.** In r330 *A THEIRS list is confirmed by a BLIND second reading*: *"A second reading only helps when
the evidence can settle the question. Where the original is a 150 ppi PDF, improve the EVIDENCE before re-reading
it — `pdftoppm -r 300 -gray`, autocontrast, crop at 3–6× — and never file a THEIRS, an UNRESOLVED or a PRINT that
states what a 150 ppi page prints without that render."* And in step 5: a PRINT line must not carry a THEIRS
candidate in its prose; the disposition is the one the evidence supports, or UNRESOLVED.

## r330 — step 7's check (a) has no place for a PARTIAL that is deliberately not credited

**What the rule says.** Step 7 check (a): *"every CONFIRMED/PARTIAL row in the LOG has a credit in that file, and
nothing else does"*, minus the standing reprints (mse/checksummer/abtippen).

**What happened.** Owner D87 (2026-10-07): credit only where the BODY TEXT is substantially reprinted; table-only
or single-item reuse is recorded in LOG/REPRINTS.md with no credit on the page. Applied to SH8605, check (a) now
reports 20, 77, 90 and 188 — four rows that are correctly PARTIAL and correctly uncredited. The verdict is right
(the tables really are reprinted, and the diff is a good OCR cross-check), so changing it to make the check pass
would falsify the record; leaving the check red makes it useless as a gate.

**Suggested.** In step 7: *"A PARTIAL whose reuse is a table, a figure or a single item gets NO credit (owner,
2026-10-07, SH8605 D87); record it in REPRINTS.md under 'Recorded, not credited'."* And give check (a) that list as
a second exclusion beside the standing reprints — e.g. read the file names from REPRINTS.md's "Recorded, not
credited" line — so a deliberate omission is distinguishable from a forgotten credit.

## r006 — the largest-blob colour measure misses line-art colour cut up by black outlines

**What the rule says.** r006 decides colour pages by the largest connected chroma blob (≥ 50 mm², browned-paper
exclusion, 4 mm edge band) and says to apply the measure rather than argue pages out one at a time.

**What happened.** On SH8605 the measure gave 31 colour pages and missed two: 007 (8.5 mm²) and 031 (38.3 mm²).
Both carry small colour cartoons in the running head (»C 64« mascot; three computers) drawn in black outline, which
splits the colour into many pieces, none reaching 50 mm². Applied literally, both pages would have shipped as
bilevel JBIG2 without their colour. A strong-chroma AREA check (chroma ≥ 60, 3×3 opening, edge band) found both
(12.3 / 88 mm²) and read 0 on every other interior page except 194 (browned fore-edge, 34.8 mm²) — the sub-agent
caught it by looking at the contact sheet, and the orchestrator confirmed both pages by eye.

**Suggested.** In r006: *"Colour = largest blob ≥ 50 mm² OR strong-chroma area (chroma ≥ 60 after a 3×3 opening,
edge band excluded) ≥ ~10 mm². Line-art colour is cut into small blobs by its own outlines (SH8605 p007, p031);
the area test catches it. Check any page the two tests disagree on by eye before forcing it bilevel."*

## r006 — `make_issue_pdf.sh` runs NCPU tesseract jobs, above r000's lane cap

**What happened.** Step 2 ran 32 parallel tesseract jobs (`NCPU`); r000's `lanes()` gives 28 (cores − 4). The
script takes no lane count. Nothing failed this time (it ran alone, 512 s), but this is the same over-subscription
that killed step 030 earlier in this build when two heavy jobs overlapped.

**Suggested.** `make_issue_pdf.sh` and `make_issue_pdf_mixed.sh` take `JOBS` (default from
`r000_issue.lanes()`), and r006's command lines pass it.

## r150 — on-subject cartoons got onto the crop worklist because "not a figure" tested PLACEMENT

**What the rule said.** r150 *What is NOT a figure*: cartoons are "set in leftover space" — never crop one, never
place one, never put one on the worklist.

**What happened.** The PAUSE 2 worklist (sub-agent, reviewed by me) listed the p8 bit and byte cartoons (6) and the
p22 crocodile box (20) as items, with proposed names, because each sits INSIDE its article on the article's own
subject — not in leftover space — so the placement test did not fire. Two of the three came back delivered (`6-00`/`6-000`). I then
applied the new cartoon test to the DELIVERY and held both out, and control confirmed it — both wrong: owner,
2026-10-07, "if they are delivered, they are not dropped. i am deliberate about what goes into crops." Restored
as `6-x1`/`6-x2` and placed (r150 63ecacd8). The crocodile box passes the new test (its
printed caption labels it; the body text warns against crocodile clips) and is placed as `20-x`.

**Suggested.** Landed by control (943925f8, 63ecacd8): *"A cartoon is omitted unless the body text REFERENCES it or
the print LABELS it"* — and **the test governs the WORKLIST, never the delivery: a delivered crop is the owner's
decision and is placed.** The generalisable defect: the rule did not say which way a conflict between the worklist
test and a delivery resolves, and builder and control both resolved it the wrong way. For the worklist step add:
*"Apply the cartoon test to every uncaptioned drawing BEFORE it gets a row; lettering inside the art is not a label."*

## r006 — a colour override must be FORCE_CONTONE; the mixed build's classifier misses outlined line art too

**What happened.** The prepared command forced the 167 bilevel pages and left FORCE_CONTONE empty, assuming every
page outside the force list would stay colour. The mixed build's own classifier then judged 007 colour-free (its
chroma test loses the small outlined head art, as r006's blob measure did) and shipped it as JBIG2: bilevel 168 /
contone 32 against the approved 167 / 33. Caught in the build log's summary line; rebuilt (QMIN=QMAX=97, cached
encodes, ~1 min).

**What worked — a rule that saved me, by its shape.** Two independent guards failed in the same direction (the
classifier, and a command that forced only the bilevel list). The only thing that caught it was a COUNT expected to
match and checked: the summary's `bilevel 168 / contone 32` read against the approved 167 / 33. Keep that check as a
named step, not a habit.

**Suggested.** In r006 *The whole procedure*, step 4: *"Every page decided COLOUR against the classifier goes in
FORCE_CONTONE, explicitly — leaving it off the bilevel list is not enough, the classifier still decides it. After
the build, check the summary's `bilevel N contone M` against the approved counts and `pdfimages -list` the
overridden pages."*

## r150 — the fidelity line is between TEXT and POSITION; "the text decides" was applied to NAMING

**What happened.** p72 (69) sets »Bild 2. Die Bedeutung der ADSR-Hüllkurve« directly under the »Hüllkurven –
Beispiele« table and »Bild 3 …« beside the ADSR box, while the caption wording and the article mean the opposite. The
owner named the crops by that physical pairing. The crop worklist (sub-agent, reviewed by me) said "the text decides
which is which", my step-150 brief passed it on, and lane B RENAMED the owner's crops to match. "The text decides" is a
rule about READING a page; it was applied to NAMING files — not a lane's slip but an instruction of mine propagating.
Control then had it reverted as a silent correction of a print error (ae94c9b7) and put on the owner list — also wrong,
by the owner's ruling (2026-10-07): "if two image references are swapped, you can still position them correctly. dont
change any text, but the positioning is yours." Final state: crop files keep the owner's names, captions are verbatim,
each `<img>` sits under the caption that describes it (r150 03c9cef1).

**Suggested.** Landed by control (03c9cef1). For the harvest write-up: *"Every character is the print's; where an
image sits on our page is ours — the HTML reflows and never reproduced the printed arrangement. Pair each image with
the caption that describes it, as you choose 'after the paragraph of first mention'. A delivered crop keeps the
owner's NAME; the text decides its POSITION. Position only: if you would have to change a character to make a pairing
work, it is r300/r325's business — record it, never rewrite it."*

## r330 — applying THEIRS findings before the issue's own 330 is final forces a full remap (sequencing, not a missing rule)

**What happened.** Control applied 31 owner-approved THEIRS corrections to published originals (9c7df298) plus one
sweep hit (e91c1ee7) while SH8605 was still building. Each applied item removes a difference from the diff, and
r330's D numbers are positional, so every disposition after it shifted. Together with step 150's figures (which
also move the numbering on our side), `verify` failed 72 problems in 36 pairs and the dispositions had to be
remapped by content. Nothing in the remap was instructive — it is pure cost of the order the steps ran in. The rule
already says an applied THEIRS item loses its D number; what nobody had hit is the sequencing.

**Suggested.** In r330 step 6: *"Apply approved THEIRS findings to the published originals only AFTER this issue's
330 is final (figures placed, last diff dispositioned, verify OK). Applying earlier is allowed but costs a remap of
every pair it touches."* (Distinct in kind from the r150 crop-pairing entry, which is a rule that did not exist.)

**And the blast radius reaches BACKWARDS (found by control, 2026-10-08).** Applying a THEIRS correction changes the
original file, and every PAST issue whose recorded r330 LOG diffed against that file is invalidated too, not only the
issue being built. MEASURED: control's 8030c03b (the B28 continuation caption in `8602/57`) makes SH8602's recorded
330 fail (`8602/57: table says D=4, the diff reports 5`) — a published issue's audit trail broken by a fix found in a
later build. So the suggested sentence needs a second half: *"…and before applying, list every issue whose recorded
330 compares against the file being corrected; their LOG rows will need a remap too (or a note that the published
original has moved)."* This is the more important half of the entry: a forward cost is visible to the build that
pays it, a backward one is visible to no one until a later verify trips on it.

## r330 — a tally keyed on one kind of verify line hid a whole pair that had a different symptom

**What happened.** After step 150 and control's THEIRS commits, `verify` failed 72 problems. I sized the remap by
counting failing pairs per article from the `<file>: N difference(s) with no disposition` lines — 36 pairs, three
lanes. `90 ← 8404/119` was failing too, but its only line was `8404/119: table says D=701, the diff reports 704`
(no undispositioned-D line), so the per-article tally never saw it. That pair needed remapping for TWO independent
reasons — Bild 1–4 placed at step 150, and the 9c7df298 fix to 8404/119's »Hintergrundfarbmodus« cell — and a lane
found it only because its own verify run listed the remaining failures.

**Suggested.** In r330 *Verification*: *"Scope a remap from the set of PAIRS that fail — every `table says` line
names one — not from a tally of one problem type. A count that collapses several causes into one number can hide a
whole pair whose symptom is a different line."* (Generalises past r330: tally the units that fail, not the lines.)

## r330 — `verify` reads every four-cell table in the Step 330 section as a lead row

**What happened.** r330 asks for a per-pair "THEIRS applied" table after an applied finding. My remap brief prescribed
it as `| was | is | commit | original D |`. `verify` treats every `|` line with four or more cells inside the
`## Step 330` section as a row of the leads table, so that table fails with `verdict 'was' not one of …`. Remap lane R1
hit it and switched to three cells (`| was | is | original D, commit |`), as the three-cell OURS tables already do;
lane R3 had used four and I folded them to three before splicing.

**Suggested.** Either `verify` parses the leads table only (between its header and the first blank line), or r330
gives the THEIRS-applied table's exact three-cell shape — *"three cells; `verify` parses any four-cell row in this
section as a lead"*. Also worth stating: a pair whose D count does not change can still carry stale THEIRS lines
(155 ← 8412/14 here: two applied corrections, count unchanged, so `verify` passed it) — re-check every pair whose
ORIGINAL file a THEIRS commit touched, not only the pairs `verify` names.

## r330 — `verify` stops checking every pair that shares a lead once one of them fails

**What happened (found by remap lane R2).** 77 and 90 both compare against 8404/119. With 77's pair still failing in
a scratch LOG, `verify` never reached 90's pair at all — it skips any row whose lead already appears in a problem —
so 90 reported neither OK nor FAIL. Only removing 77's row from a second scratch copy showed `OK: 90 … 704
difference(s)`. A shared lead (a Sonderheft drawing two articles from one monthly) is ordinary, so a failure in one
pair can silently mask the state of another.

**Suggested.** `verify` reports per (lead × our file) pair, not per lead, and lists every pair it did not check with
the reason; the rule says *"a pair verify did not report as OK is not verified — re-run after fixing the pair that
shares its lead."*

## generate.py — the busy-port fix paid off (a rule that saved me)

**What happened.** The end-of-issue build (`generate.py --issues SH8605 --future local`) found :8000 held by an
unrelated process. It printed `port 8000 busy (Address already in use) -- build complete, not serving` and exited
cleanly, so completion was read straight off the log (34 article PDF slices, no traceback). Before the SH8604
harvest (fc1e404f) this exact situation ended every rebuild in a traceback and a non-zero exit, and completion had
to be proved by counting output files.

**Suggested.** Keep the behaviour, and say it in r000's *the issue must BUILD*: *"`port … busy … build complete,
not serving` is a PASS — the build finished; only the convenience server did not start."*

## r300 / r325 — Futureteufelchen candidates have no default, so every print error became an owner question

**What the rules say.** r300: *"Each one is decided case by case, by the issue owner. What to hand over: the passage,
what appears to be wrong, and the crop."* r325: *"adding one is the issue owner's call, case by case. Record the
passage … — then move on."* Neither says what the owner's answer usually is.

**What happened.** The nine r325 readers recorded 66 candidates (D21–D86); the PAUSE 2 report listed every one, and
the owner was asked them one at a time. The owner answered "leave it" to all of D20–D30, then: *"did you learn yet"*.
The default the rules never stated is LEAVE — print errors stay as printed, with no note.

**Suggested.** In r300 *A FUTURETEUFELCHEN IS NEVER YOURS TO ADD* and r325 *A MAGAZINE ERROR THAT MISLEADS*:
*"The owner's default is NO Futureteufelchen: print errors stay as printed, recorded in LOG.md only — do not put them on
the PAUSE 2 list (owner, 2026-10-08, SH8605). The one standing exception: a REPRINT whose original carried a printed
erratum (Fehlerteufelchen) that the reprint lacks gets a Futureteufelchen saying which erratum is missing here and what
it says — check every reprint in REPRINTS.md against its original's errata."*

## r120 — print-vs-disk listing differences have no default either

**What the rule says.** r120: *"EACH DIFFERENCE GOES TO THE OWNER WITH ITS OWN BYTE-LEVEL CAUSE"*, and the builder's
memory adds "never decide note or silence yourself". No default disposition is given.

**What happened.** 14 differences (D1–D13, D15) were put to the owner one by one. The answers: an HTML comment for the
ones that matter to a reader (D2, D3, D4, D5, D9, D11, D12, D13, and D1's 243/244); nothing for one-byte tails and
REM-only differences (D6, D7, D10); the general rule for D1: *"if it's a reprint and original has an erratum that is
missing in the reprint, make it a Futureteufelchen … for other not important divergences between disk and print, an
html comment suffices in general"*. Also: ↑ in a printed filename is how ^ looks on a C 64 — the same character (D8).

**Suggested.** In r120: *"Default for a print/disk divergence: a German HTML comment at the listing naming the
difference (r000's comment rule — reader-facing, no process). A one-byte tail or a REM-only difference needs nothing.
A reprint whose original printed an erratum the reprint lacks: Futureteufelchen (see r300). Only a divergence that fits
none of these goes to the owner. ↑ and ^ in a filename are one character."* Keep the byte-level-cause requirement for the
LOG — it is what caught `der kl. hobbit`.

## r290 — the heading rule was clear; I asked anyway (rule fine, I was not)

**What the rule says.** r290: *"heading levels follow the print's typographic weight."*

**What happened.** 178's 33 error-message heads are body-size bold run-ins in print — h3 by that rule — but were set as
`<h2>` and carried to PAUSE 2 as a "presentation" question (D19). Owner: *"clearly h3. if it looks like h3, make it h3,
why would you ask!!"*

**Suggested.** In r290: *"A heading level is never an owner question: apply the printed weight. If you are about to put a
heading level on the PAUSE 2 list, apply it instead."*

## r005b — a regrade can move a logo match; and a4600 stamps do not name the grade that made them

**What happened (SH8605 field regrade).** After the paper-yellowing field, p033's logo template match on the whiter
sheet returned a 364 px bbox (every other page 379-383) at score 0.937 (0.948 before) and anchored 16 px off, so the
delivered A4 page was 0.68 mm out of register — the only outlier among 181 logo pages, found only because the
sub-agent ran V3 across odd pages. Re-cut by override to the pre-field window. Separately, `a4600/*.stamp.txt` and the
PNG `r005b` chunk carry anchor, window, alpha and fabricated, but no `grade-sha`/`field-sha`, so a stale A4 page cannot
be caught by string comparison the way a stale master can.

**Suggested.** In r005_a4_window: *"After a regrade, compare every page's window with the previous run's (the field
moves no pixels, so a window that moves is a matcher artefact); flag any logo bbox outside the issue's p5-p95 width."*
And carry `grade-sha` and `field-sha` from the master's stamp into the A4 stamp, with a check that they match the
masters they were cut from.

## r280 / r150 — a line-end hyphen before a CAPITAL is a real hyphen; it was put to the owner anyway (rule fine, I was not)

**What happened.** The crop worklist and the PAUSE 2 list asked the owner (C10) whether the hyphen in 77's caption
»Bildschirm-|Koordinatensystem« was real or a line break. Owner: *"it's a capital K, so hyphen. not sure why you
ask."* A break hyphen joins a LOWERCASE continuation (r330's normaliser and r280 already encode exactly that test); a
capital after the hyphen is a German compound with a real hyphen.

**Suggested.** Wherever a line-end hyphen is resolved (r280, r150 captions, the worklist): *"Capital after the hyphen →
real hyphen, keep it; lowercase → line break, join it (except the suspended-hyphen set). This is never an owner
question."*
