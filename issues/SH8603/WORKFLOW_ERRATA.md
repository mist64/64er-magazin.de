# SH8603 — workflow errata

Kept from the first confusion onward (r340). Harvested at the end, not during.

## 005 — the paper pre-fill proposes 1 of the 8 high-stock pages

**What the rule says.** r005_masters_sheet.md, *What the step offers as
evidence*: "The step pre-fills `high_pages` with what the edge-finder evidence
points at and says, in the output, that it is a guess to be checked against
the copy."

**What happened.** The pre-fill was `[1]`. The step's own evidence list (b)
then put 179, 002, 180, 181–184 at 59–122 city-block from the interior p50,
with a gap to the next page (p071, 21), and those seven plus 001 are exactly
the 2400 dpi pages, i.e. the wrapper and the card. SH8602 met the same case
(its LOG: "the paper mask sees 0.11–0.52 of these frames as interior paper").

**What is true.** The edge finder is one-sided (the rule says so); the
own-white gap is the stronger signal on these two Sonderhefte, and the scan
dpi split is a free third witness. No cost here beyond a montage (≈2 min);
the risk is an operator pasting `[1]` back unread.

**Suggested.** Pre-fill from the union of the edge-finder set and the pages
past the own-white gap, and print the per-page scan dpi beside each.

## 005 — "measure K on the darkest solid black" gives no procedure, and the obvious one measures the bed

**What the rule says.** r005_masters_spread.md, *EXCEPT K*: "when measuring
`W`, also take the darkest solid black across the interior and move the `K`
anchor to it if it sits below the built-in." The `W` measurement beside it is
a runnable snippet; this one is a sentence. (The sheet rule does not mention K
at all; the pointer came in a relay from control.)

**What I did.** Reused the W snippet's body box (10–90 % × 3–97 %) with
"lum < 70, low chroma, eroded". Every one of 176 pages reported ~40 000 solid
black px at 31 27 27: on a SHEET-variant thumb the frame holds the near-black
bed around the sheet, and a fixed fractional box does not exclude it. The bed
(raw ~21–40) is in the same range as printed black, so the answer looked
plausible.

**What is true.** Restricting to the sheet's own paper bbox (rows/cols > 30 %
paper, 2.5 mm inset) and looking at the mask on p073 put it on the printed
banner bars: p50 30 27 27, above K 16 17 17. Same number by luck — the bed and
this issue's black read alike — but on an issue with a darker black the first
method would have reported the bed. Cost ~5 min, 3 commands.

**Suggested.** A snippet for K next to the W one, cropping to the sheet (not a
frame fraction) for a sheet-variant thumb, and saying "look at the mask on the
darkest page" as part of it. Put the requirement in r005_masters_sheet.md too.

## 005 — the sheet Verification still names `figures600` (SH8602 found it; not harvested)

**What the rule says.** r005_masters_sheet.md Outputs and Verification 1, 4, 6
read `R.OUT_FIGURE` / `figures600`. **What is true.** Unchanged since SH8602's
entry: the code writes no `figures600` and has no `OUT_FIGURE`; checks 1, 4
and 6 die on `AttributeError` pasted verbatim. SH8602's errata (deleted in
56b7e343) had this as "005 — the sheet Verification names an output the code
no longer writes", plus check 4's printed-footer false positive (166/168
there, 165/184 here). Neither landed in r005_masters_sheet.md or HARVEST.md.
**What I did.** Same adaptation as SH8602: checks run on `masters600`/
`sheets600`, the footer band read as print. Cost ~5 min.
**Suggested.** Check the harvest of SH8602's 005 entries; it looks as if they
were dropped.

## 040 — "bullets are always `-`" is false again; the script's own count is not fence-aware

**What the rule says.** r040 Notes: "List bullets in this project are always
`-`, never `*` — so escaping every solitary `*` won't break lists." SH8602
already found 9 `* ` bullet lines; SH8603 has 13 (p47–49 region), some run
together mid-paragraph. **What happened.** Escaped as the rule says; the list
now renders as literal asterisks and has to be rebuilt downstream (190).
**Also (sub-agent):** the script's closing summary counts the whole file and
prints `solitary=2` for the two correctly untouched fenced `*` — exactly the
"a check must be as fence-aware as the transform" failure the Verification
docstring warns about; and the script still calls bare `python3` (works only
because it imports `re`). The rule says pairing is "within the paragraph",
the script tests per line; the `**` regex lacks `(?<!\*)`, so a `***` tail
counts as a delimiter. No effect here. SH8602's "keeps every `**`
unconditionally" no longer holds — the script now checks pairing.
**Suggested.** Either convert `^\* ` / ` \* ` bullet starts to `- ` before
escaping, or have the rule say outright that bullets are escaped and 190
rebuilds lists; fix the summary to skip fences.

## 050 — rule and script disagree in five small places (no effect on SH8603)

Found by the 050 sub-agent, checked against the files: (1) the rule says
escape `</` followed by a non-letter (`</>`, `</1>`); the script's pattern
`<(/?[a-zA-Z]…)>` never matches them, nor does the Verification regex. (2) The
rule's "idempotent: lookbehinds for `\`" — the script has none; it is
idempotent because entities do not match. (3) The script header still says it
"skips already-escaped \<...\>"; Pass 1 converts them. (4) The script's
closing count scans fences too, against the rule's own "outside fenced code
only". (5) The rule's whitelist names `big`; the script's `HTML_TAGS` and the
Verification `WHITE` set do not. Plus the bare `python3` again (venv put first
on PATH). Cost: none beyond the report.

## 030 — a "Fortsetzung von Seite N" glued to body text drops the whole paragraph, and the loss check calls it accounted

**What the rule says.** r030 Verification: "Every paragraph must be accounted
for: in an article, used as a title, dropped as a headline fragment, or a
cross-reference. Unexplained loss must be 0 — this is the check that catches a
boundary rule quietly eating text." **What happened.** Loss 0. At 060 the
sub-agent found p62's article reduced to `# [Fortsetzung von Seite 60] [62]`:
stream paragraph 887, 369 chars, is "Fortsetzung von Seite 60 gegen das
»größte« … umgeschrieben." — the marker and the continuation text are ONE OCR
paragraph. `FORTSETZUNG.search(text)` matches anywhere in it, so the whole
paragraph is filed as a cross-reference and `mark` counts it accounted. The
loss check certifies exactly the silent drop it exists to catch.
**What is true.** A cross-reference is a SHORT paragraph that is (almost) only
the marker. **Suggested.** Treat a FORTSETZUNG paragraph as a marker only when
the text minus the match is under ~20 chars; otherwise strip the marker and
keep the paragraph, and make the loss check count chars dropped as markers
(> 40 → report). Cost here: found by luck at 060 (a list-number survey);
nothing at 030 could have shown it.

## 060 — the list check reads a file the script deletes, and the `<br` spot-check passes on raw `<br>`

From the 060 sub-agent, confirmed: the rule's start-number check greps the
md, but `r060_md_to_html.sh` deletes `issues/<ID>/<ID>.md` and
`<tmp>/ocr/<ID>.md` is the pre-040 text, so the check needs a copy the rule
never says to take. `grep -c '<br'` > 0 passed only because of raw `<br>` in
`<p class="source">`; `-G` produced 0 `<br/>`. And the commonest list break
here is OCR dropping the space after the number (`2.$025D`, `2.Die`), which
the `^…\. ` grep cannot see.

## 040/050/060 — a body line that starts with `#` becomes an `<h1>`, and 080 would split an article on it

**What happened.** p164 prints a bullet wrapping onto "#1281/1282=$0501/0502."
(# = decimal, in contrast to $). The OCR kept the wrap as a separate line;
Discount read `#1281…` as an ATX heading (no space needed) and 060 shipped
`<h1>1281/1282=$0501/0502.</h1>` — losing the `#` and creating a 52nd `<h1>`
that 080 splits articles on. No rule checks `<h1>` count against 030's
article count; I noticed because `grep -c '<h1'` said 52 against 51 `#`.
**Suggested.** r040 (it already escapes markdown metacharacters) also escapes
a leading `#` on any line that is not one of 030's `# Title [pages]` lines;
r060 Verification compares `<h1>` count to 030's article count.

## r000 — the labels.json bbox is NOT in master pixels

r000 *page block index*: "The bboxes in `<OUT_DIR>/blocks/pNNN.txt` are **in
this file's pixels** (600 dpi), so a crop is the bbox verbatim". True of
`blocks/pNNN.txt`; r000 then sends you to `NNN.labels.json` for full text, and
that file's `bbox` is `[x0, y0, x1, y1]` at **300 dpi**. Cropping it verbatim
from masters600 gave the wrong region (the p164 intro); ×2 gave the line. Cost
2 commands. Say so where the recipe points at the JSON.

## 070 — the rule requires an en-dash pass the script does not do, and does not check

**What the rule says.** r070 "A SPACED DASH IN BODY TEXT IS AN EN DASH: ` - `
becomes ` – `" … "**This step, not later.** … r080 derives the FILENAME from
the h1". **What is true.** `r070_html_cleanup.sh` has no dash substitution and
the Verification block has no dash check, so a run of the script alone passes
070 with 0 en dashes. The sub-agent wrote its own pass (119 converted, 70 kept
by per-site judgement) — which also means the script's self-`git add` staged
only half of 070 (`MM` in the index). Also: U+201A `‚` (18 sites, mostly
misread commas) is not in the rule's quote table. Cost: one sub-agent script
plus a review of 189 sites. **Suggested.** Put the dash pass, with the
exclusion classes, into the script; add `grep -c ' – '` > 0 to Verification;
rule on U+201A.

## 110 — no rule for a Sonderheft whose README bullet is `unbekannt`; the Verification grep is still broken for SH ids

From the 110 sub-agent, confirmed: r110's Sonderheft paragraph assumes the
README bullet is "usually a BOUND" to write as a provisional date; SH 3/86's
is `unbekannt`, and the derivable bound (8605, ~11 Apr) is six months in the
past — useless as a pubdate for an issue being built. Precedent (SH8601,
SH8602) is a release day the owner picks; the rule never says so. The
Verification grep with `YYMM=SH8603` searches "86/SH" (no hit) and with
digits matches the MONTHLY bullet "03/86" — SH8602's errata reported this and
it was not harvested. The block also hardcodes `issues/8607` / `YYMM=8608`.
And "the README's bullet is the only source of truth" (Lessons) contradicts
the rule's own Vorschau derivation.

## 080 — four places the split rule and its script disagree

From the 080 sub-agent, checked in the output: (1) "The FILENAME keeps the
plain number" for lettered pages, but the script derives the filename from the
h1's `[pages]`, so `[21a]` would make `21a X.html` — letters have to be put
into the metas AFTER the script, which the rule does not say. (2) The script
turns ANY all-parenthesised paragraph into an `<address>` byline: 72's
`(Kassette nr = 1; Diskette nr = 8)` became the author meta. (3) The paired
check's inline-byline regex `\((?:…/)?[a-z]{2,3}\)` matches `(ost)`, `(von)`,
`(xx)` in prose — 3 of 4 hits false. (4) A leading `>` (C16 monitor prompt) is
eaten by Markdown as a blockquote and comes out as `<p class="intro">` after
070 — an escaping gap at 040/050 that only the paired listing exposed (intros
=2 on 14). Also 030: the p21 table box and p60's "Fortsetzung Text auf Seite
62" line were dropped before 080 ever saw them; the 030 loss check does not
count blocks it never put in the stream.

## 120 — the extractor's "V2" is petcat's BASIC 7.0 default; check 4's cases miss three real shapes

From the 120 sub-agent, confirmed by its evidence: r120 says the extractor
decodes "with default V2 mode", but bare `petcat` (VICE 3.9) uses the 7.0
table — C16 files came out readable but untagged (`key5,"dsave"…dec(`) and a
VC 20 file showed C16 keywords; only check 4 exposed it. Check 4's three cases
do not cover: petcat's own asymmetry ($9A → `{blu}` → $1F under `-w3`), a
BASIC extension petcat has no dialect for ("19 Grafik-Befehle"), and real
BASIC with its own machine code appended (`fast hardcopy` — looks like case 3
"trailing bytes", is not harmless). The stub test would also wrongly flag
`turbo-racer` (73-byte loader, bare `SYS`, no code appended). The archive
names A/B disks `SH0X/SH03A.D64`, not the Usage's `<YYMM>A.D64`.

## 100 — the script needs bash 5; one check counts the placeholder; an unmentioned helper contradicts the rule

From the 100 sub-agent, confirmed: `r100_toc_category.sh` fails `bash -n` under
macOS `/bin/bash` 3.2 ("unexpected EOF while looking for matching `"'", line
87 — backticks in a Python comment inside `$(cat <<'PY' …)`); it runs under
Homebrew bash 5. The rule's "exactly one toc_category" check greps
`<meta name="64er\.toc_category"` and so also counts the commented `XXX`
placeholder — a file with ONLY the placeholder passes (seen on a planted
copy). `r100_toc_title_apply.py` sits in rules/ unmentioned by r100.md and
contradicts it: writes toc_title equal to `<title>`, does not escape `&`,
cannot parse lettered pages (gave p21's entry to 14 Maschinensprache, left
77a/77b unmatched). Not used.

## 130 — MSE rendering assumes a C64 MSE dump; `data-range` is BASIC-only; verifier #6 vs verbatim captions

From the 130 sub-agent, confirmed in the files: the C16/VC 20 binaries here
are printed as TEDMON, VC-20 monitor or a game's own input-program dumps
(tacco at file−$200 with its own row format; penco 25-byte rows), but the 120
worklist and r130 default to `data-mse=mse1`, which renders addresses the
magazine never printed; `data-range` exists only for BASIC, so a binary's
address mismatch cannot be expressed. Verifier #6 (≥3 words after
"Listing N.") flags verbatim print captions like "Listing 2. »INT«" — 12
false hits. r130 says captions are verbatim; r170 says drop page pointers —
same captions ("Bitte beachten … Seite 76"), no precedence stated.

## 140 — the cross-issue check cannot see reprints, and its slug list is monthly-shaped

From the 140 sub-agent: check 4 compares against ONE previous issue, but a
Sonderheft built from monthly reprints takes its ids from the monthly
originals (here 8501, 8410/11, 8505 ×3, 8506, 8507, 8510). Only a text-overlap
pass over the whole corpus found the 8 reprints — and r330 needs that list
too, so the step that finds it should be told to record it. Check 4's slug
list has `bücher`/`cpm` but not `vorwort`/`checksummer`/`mse`/`impressum`/
`abtippen`, so against a Sonderheft it passes trivially; the Sonderheft
paragraph says these are "not in the list below" (the list is above it), and
`abtippen` is nowhere in the rule. `mse` does not recur on a VC 20/C16 issue.

## 160 — two checks can never reach zero; box prose has no owner

From the 160 sub-agent, confirmed in the verification output: check #5's
`(?:Tabelle|Bild)` flags every Bild photo reference and an unnumbered printed
"Tabelle." that the prose calls "Tabelle 1" — 8 permanent lines; check #7
lists every named-box caption the rule itself requires — 6 permanent lines. A
gate that always reports stops being read (r000). Pass 1 greps the 200-char
block preview and missed two captions split across OCR blocks (p96, p132);
grep `labels.json`. Sweep 2 (narrow columns) gave 1622 hits and 0 tables, as
on 8611/8612 — the visual walk found all 18 uncaptioned tables. And box PROSE
that is not a table (p3 Programmservice, p148 Wichtig!, p47's checklist) has
no rule that owns it; 030 drops such boxes and nothing downstream restores
them by mandate.

## 150 — the caption script's regex and "short = seen" shortcut; naming has gaps for shared start pages

From the 150 sub-agent: `r150_figure_captions.py` needs `Bild\s*\d`, so it
skips "Bild." and "Bild. 1."; takes captions only from blocks labelled
`caption` (missed p23 Bild 2, labelled listing-inline); and marks any caption
under 4 words IN_HTML (p146/p148 tables reported present while absent). r150's
naming has `-00` for a second article's LEAD image only — nothing names a
second article's TABLE, an unnumbered "Tabelle.", a whole screen-output crop,
or a figure printed on the page BEFORE its article starts (p76's Bild 1/2 for
77a). And 150's mapping assumes a figure's page is inside its article's
`64er.pages`, which 080 had left short for 31 (p38), 47 (p48), 58 (p59) and
most game listing pages — r320's page-coverage half is the check that sees
it, but it runs at the END; running it right after 080 would have fixed the
ranges before 130/150/160 depended on them.

## 170 — check 4 assumes one language per `<pre>`; monitor listings have a proof the rule does not name

From 170 part A: check 4 flags this course's boxes that print "Basic:" plus a
TEDMON monitor listing in ONE box (L9 9/30, L11 1/10 digit-led lines) — false
positives by construction. The rule's "prove it" assumes checksums; a monitor
listing proves itself (hex ↔ disassembly ↔ contiguous addresses), which found
nothing wrong here but would catch a misread byte — worth naming. Briefing 2b
("tesseract-locate the caption's bbox") fails where the box has no caption
block (L1, L14, L16–L18); page overviews located them.

## 170 — GLM-OCR is not byte-perfect on faint dot-matrix dumps; non-MSE row checksums are proof too

From 170 part B: r170 calls the local GLM-OCR "byte-perfect" on single-column
crops — measured on clean MSE print. On Penco's faint dot-matrix dump it read
~86 % of bytes right even on half-row crops, and on a two-column TEDMON dump
it sometimes emits the address and data columns as separate lists. Tacco's
own format carries a 16-bit row sum that proves a transcription as well as
MSE's; the rule's recreation table has rows only for MSE and Checksummer.

## 180 — monthly-shaped cases and a self-contradicting briefing

From the 180 sub-agent, checked: Case C gives the Vorwort to the chief editor;
a Sonderheft's Vorwort is signed by the Koordination (Georg Klinge, as on
SH8602). "A full-name signature takes NO parentheses" — this one is printed
with them, kept as printed as SH8602 did. The Impressum closed-vocabulary
check finds no `xx = Name` key in a Sonderheft masthead, so every initial is
"UNDEFINED". Briefing step 3 says "Expand initials → full names from the
previous issue's Impressum" while the guardrail says keep initials exactly as
printed. And `blocks/pNNN.txt` truncation hid ~40 of 50 bylines; the agent
had to use `NNN.json` — the r000 warning names labels.json, not the rule.

## 190 — `$TMPDIR_ISSUE` is undefined; the never-split rule moves mid-article tables away from their print position

From both 190 sub-agents: Verification check 2 writes `skipped_files.txt` to
`$TMPDIR_ISSUE`, which no rule defines — and two parallel parts would collide
on one path; both used their scratch dirs. The "never split the author from
their text" rule moved tables/figures that print floats MID-article to after
the byline in 9 files — a departure from print position nobody marks, and in
tension with "restore in print position" for boxes. And no rule owns lost
DROP CAPS before 190: 030/080 leave them, r310 gates them only at the end;
here 190 read ~38 of them off the crops.

## 210 — the check excludes the Vorwort it says to keep; the apply script escapes `&`; machine-label spacing unstated

From the 210 sub-agent, checked: check 1's exclusion grep lists `vorwort` as
"should NOT have head1" while its own comment and SH8602 give the Vorwort one;
its formula subtracts a Leserforum a Sonderheft does not have.
`r210_head_meta_apply.py` writes `Tips &amp; Tricks` via `html.escape`; the
corpus has the literal `&`. The rule's examples are all spaced (`C 64/VC 20`);
SH8603's bands are set closed — the rule should say the spacing follows the
band. No guidance for a lettered `b` start page whose band belongs to the `a`
article above it (77b).

## 220 — the Verification is monthly-only and the prose says the script lacks what it has

From the 220 sub-agent, confirmed: r220 says "the apply script reads only the
monthly layout … write one as part of this step" — `r220_index_meta_apply.py`
already has `parse_sonderheft_csv`. The Usage `cd`s to the repo root then
runs `../../tools/...` (only works from the issue dir), with bare `python3`.
Verification check 1 greps `^<YYMM>,` and the routing check filters on the
monthly columns, so both find 0 rows on a Sonderheft and PASS; the routing
check also skips lettered pages (`'21c'.isdigit()` False → KeyError if a row
lands there) and cannot see a misroute between lettered siblings. "Category
values must match TOPICS in generate.py" is false for the Sonderheft CSV
(7 categories match nothing; SH8602 the same).

## 260 — the "adjudicated.txt" hook the rule describes is not wired

From the 260 sub-agent, confirmed by reading both: r260's prose says its check
"reads `adjudicated.txt` the way r310 does" under `heading-all-caps`; the
Verification code reads no adjudication file, and r310 has no
`heading-all-caps` check, so an entry would make r310 report "declared N,
found 0". A heading kept in caps on purpose therefore cannot be cleared by
either check (SH8602's UNNEW is the standing example).

## 280 — briefing vs body on `<pre>`; checks still piped into `head`

From 280 part B: the rule's Briefing tells sub-agents to leave `<pre>` alone,
its body puts `<pre>` in scope (followed the body: 164 `JMP $DE60`). The
Verification still pipes checks 1 and 2 into `head`, which r000 (A CHECK
SHIPS ONLY ONCE IT HAS BEEN SEEN TO FAIL) forbids. The block index could not
locate most mid-paragraph words or the p148 box; the agent ran its own
tesseract word-box pass as a locator.

## 190 — "restore missing text" without first checking the text is not already in the file

**What happened.** 190A reported "Missing section 'Kleiner Epson ganz groß'
restored" in 43 and restored it under its h2. The text was NOT missing: 030
had glued it onto the end of the article's opening paragraph, in raw OCR
form. The issue then printed the section twice; 280A noticed it only because
a `©` survived in the raw copy. The same pass left two paragraphs in 6
ending with a copy of the heading it had split out. My own check at 190
compared the restored words against the OCR — which can only confirm the
text EXISTS, i.e. the opposite of the question.
**Suggested.** Before restoring any "missing" passage, grep the article for
its first and last 8 words; after any restoration or heading split, run a
repeated-12-word-window sweep over the file (it found exactly these here).
Put that sweep in r190's and r320's Verification.

## 290 — check 2 knows only the erratum-box exception; the aside override contradicts its examples; PRINTED marker still cited

From the 290 sub-agent, checked: check 2 labels every non-h2 aside heading
"rule 300 erratum box, or check it" although the rule's own header prescribes
h3 when the aside would be the only h2 (3, 47, 60 here) — permanent false
flags. "ONE LEVEL BELOW the article's highest section heading" contradicts
the rule's examples (aside at the SAME level as the body's top sections) —
followed the examples (= SH8602). r290's period section and r000's corollary
still point to the in-page `PRINTED` comment that r290 itself withdrew for
`adjudicated.txt`; r310's inline comment too.

## 300 — status vocabulary, a correction outside the rubric, per-file trailer check

From the 300 sub-agent, checked: step 2 says to omit the status comment for
non-code errata while "every aside carries a disposition comment" says it is
mandatory (136 of 161 corpus asides have none). The vocabulary has no word
for "a real code bug, but no program file" (DATA-Erzeuger, print-only) —
used `Reiner Druckfehler` (8607/79). The rule harvests only the rubric: 8605's
"Das seltsame Listing" (Tips & Tricks) corrects SH 3/86 p22 and has no home.
The trailer check is per FILE, so a two-source aside (146, 81) passes with
one trailer missing. The rule's `_tmp/` / `fehlerteufelchen_pages/` paths
conflict with r000's scratch confinement.

## r310 — a class-wide adjudication lets a NEW finding of that class through with exit 0

From the r310 sub-agent, planted: with `byline-split 2` adjudicated, a third,
unreviewed byline split makes r310 print only "ADJ byline-split declared 2,
found 3 -- MORE than adjudicated" and still exit 0 with HARD 0. An
adjudication should clear exactly its count; "MORE than adjudicated" should
be HARD. The single-item `<ol>` check has no adjudication hook, so a printed
one-item numbered list (14 p17) must be re-shaped to pass.

## 060/190/r310 — how the list defects were actually found (answer for the harvest)

The 52 `<li> wraps <p>` were found ONLY by r310 at the end of the chain;
nothing in r060's or r190's checks looks for `<li><p>` (grep of both rules and
r060's script: no such check). Discount emits them for every loose list, and
SH8603's course articles (14, 6, 76) are list-heavy.
The 2 single-`<li>` `<ol>`s (both in 14): r060's start-number survey DID list
the p19 LOAD list (html 725, "→3") as torn — and r060 says "the fix is
`<ol start="N">`, written at 190". 190 did exactly that, wrapping the lone
item 3 in `<ol start="3">` — which is the one-item-list shape r310 flags; the
print has 1., 2., a paragraph, then 3., so the right fix was numbered run-in
paragraphs (r310 sub-agent). The p17 PLOT one-item list ("1. Cursor setzen:",
no 2.) was never in r060's list at all. So r060's check earns its place for
FINDING torn lists, but its prescribed fix produces the defect r310 rejects
when prose separates the parts. Suggested: r060/r190 say "rejoin if
contiguous in print; if prose intervenes, numbered run-in `<p>N. …</p>`, not
`<ol start>`" — and r190's Verification runs r310's `<li><p>` and single-li
checks on its own output.

## r000 — machine-name spacing is now an owner rule, not "consistency with the page"

r000 *CONSISTENCY WITH THE PAGE* uses `C 64`/`C64` as its standing example of
matching the page site by site (owner decision 2026-08). On SH8603 the body
type sets a thin gap that measures neither closed nor a word space, the HTML
had both forms (325A: 165/99 in Part A alone), and 210 set the bands closed.
Owner, 2026-10-04: **"space. C 64, C 128, C 16, C 116, VC 20."** The harvest
should rewrite r000's example and r210's band guidance accordingly, and say
what the rule does NOT touch (program text, the CSV's verbatim index titles).

## 005b — the run's offset can put bed inside a failed card page's window

r005_a4_window's new fallback 1 anchors a failed insert page "on its own
traced top-left corner where there is one, else on the run's offset". Here
182–184 have no traced corner (the card is flush with the frame's top-left),
so the run's offset (181's 28 6) applies — and with the run's width it puts
the window's right edge at 3438, past 183's card (right edge 3431) and the
low band of 184's: 28 % of 183's right 24 px was bed. Anchoring on the page's
own measured RIGHT edge (bed step at lum < 60, three-band median) fixed it.
Suggested: when the top-left is not traceable, anchor on whichever edges ARE
measurable (right/bottom against the bed), and check the window's edge bands
for bed before accepting it.

## 330 — `verify` cannot parse D-1000 and up (FIXED UNDER THE BUILD — blocking)

**What the rule's tool did.** `r330_reprint_compare.py:410` `DISP_LINE =
re.compile(r"^\s*[-*]\s+D-(\d{3})…")`, and the rule's Verification greps
`D-[0-9]\{3\}` (lines 752, 757). SH8603's 31 is merged from three monthly
parts (8409/8410/8411) and each pair runs past 999 differences, so `verify`
reported 2311 undispositioned D-numbers and exited 1 although every one was
dispositioned in LOG.md. **Fixed at once** (r000: a defect that BLOCKS the
build is fixed then, and recorded here as having moved under it): `\d{3,}` in
the parser and both greps. Seen both ways: HEAD's tool → `FAIL: 6
problem(s)`, exit 1; fixed tool → `OK: 18 pair(s) verified`. Not pushed.
Other 330 findings for the harvest (from the sub-agent): check (b)'s regex
`[0-9]\{4\}` skips `../SH8507/…` links; the rule says a plain `<p><strong>`
credit, SH8601/SH8602 use `class="nachdruck"` (copied the corpus); Step 0's
~0.5 threshold misses real merged/partial reprints (0.05–0.26 here — a
per-block measure found them); monthly PDFs of 8405/8503/8506/8507/8407 are
150 ppi, too coarse for commas — the 2400 dpi scans were needed; the
disposition vocabulary has no value for "figure not yet placed" or a dash-
glyph-only difference.

## 006 — the largest-blob colour measurement reads browned paper as ink; "the paper mask r005 already has" does not exist for a4600

From the 006 preparation, confirmed on the contact sheet: SH8603's interior
paper is browned at the head and fore-edge (R>G>B, ~221/211/204 against a
neutral mid-page). r006's recipe (chroma ≥ 18, mean > 25, 3×3 opening, paper
mask) measures that as one full-width blob > 50 mm² on 183 of 184 pages —
literally applied it would ship the whole issue as JPEG and blow the 100 MB
ceiling. The "paper mask (r005 already has one)" is not stored for a4600; the
only one is `page_mask()` in r005_a4_window.py, which removes dark/saturated
bed only. Two fixes agreed exactly here: exclude light warm weak-chroma pixels
(mean > 170, R ≥ G ≥ B, chroma < 45), or drop blobs touching a 4 mm edge band.
The classifier's own false promotion (178) has the same cause — a second
cause besides SH8602's K anchor that the rule should name. Also: the tag must
be zero-padded ("Sonderheft 03/86"); `make_issue_pdf.sh` sets `LANG="deu"`,
which clobbers the locale (harmless warnings); step 2 needs no guetzli
(ENCODER=fast, as SH8602) — say so.
