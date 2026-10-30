<!--
COPIED INTO reviewed/ 2026-10-30 SO IT SURVIVES THE BUILD.

The working copy at issues/SH8607/WORKFLOW_ERRATA.md is git-ignored
(.gitignore: issues/*/*), so it lives on one disk and dies with it. The
sign-off that survives is reviewed/r340-signoff.txt, which COUNTS these
entries but does not carry them -- and 19 of the 26 have not reached their
rule, so the content still matters.

WHAT THE 005b ENTRY COST, as the reason this copy exists: the build found
the cover-leaf Bund defect on p001, fixed it per page with a recovery script
and an OVERRIDE stamp, and did not change the rule. Ten days later the owner
found the same defect on p002, p179 and p180 in the finished PDF. An
erratum that stays in this file is a defect waiting for the next issue.

HARVESTED SO FAR (rule changed): 005 x2, 006 x2, 160, 330, 005b.
STILL OPEN: 050, 070, 080, 100, 120, 130, 140, 180, 210, 250/270, 260,
280 x2, 290 x2, 020/190/320, 325, End gate, 190/marks.
-->

# SH8607 — WORKFLOW_ERRATA

Opened 2026-10-23 at the start of the build. This build runs without questions
(control's brief): every point the rules did not settle is decided here, with
the reasoning, and harvested at the end.

## 005 / PAUSE 1 — "ask when the witnesses disagree" has no answer on a no-question build; the leaf-partner rule already settles it

**What the rules say.** r000 *PAPER: ASK ONLY WHEN THE THREE WITNESSES
DISAGREE*: "Ask when they disagree, or when one of them is blind". r005_sheet
witness 1: "settle any page still in doubt against its leaf partner (n/n+1):
one sheet of paper cannot be two stocks."

**What happened.** SH8607's witnesses disagree on p180 only: 2400 dpi, but the
edge finder does not offer it (frac >= 0.10) and its own white sits inside the
interior band (full-bleed printed back cover, as SH8608's p163). Control's
brief forbids asking. The leaf-partner sentence settles it in one line: 180 is
the back of 179 (own white 93 off the interior), so high. Same for p001 (own
white 19, full-bleed art) via p002 (117). Cost: none beyond reading; ~3 min.

**Suggested.** In r000's paper section replace "Ask when they disagree" with:
"When they disagree, settle each disputed page against its LEAF PARTNER
(r005_sheet witness 1) and record the leaf in LOG.md. Only a disagreement the
leaf cannot settle -- both sides of one sheet in doubt -- goes to the owner."

**Also observed.** On an issue whose interior browns progressively toward the
back (SH8607: R-B 38 at p003 rising smoothly to 68 at p178), ask_text's "the 8
furthest" list is filled entirely by the last interior pages at 76-87
city-block -- the same distance as the bound-in cards (97-107). Read without a
per-page plot it looks like a second stock. Suggested, in r005_sheet witness 1:
"Plot own white against page number before reading the furthest-8 list: a
second stock is a STEP; a smooth ramp to the back is browning of one stock."

## 005 Verification 7f — HARD_BAND 0.25 is red on genuine browning at the back of the book

**What the rule says.** Check 7f: "HARD_BAND is the outer bound of anything
paper can do. SH8608's own worst page needs 1.21 in R (+44 DN), and that is
already a mismeasured page and not a browned one", `HARD_BAND = 0.25`.

**What happened.** SH8607's low field gives pages 170-176 a B gain of
1.252-1.303 (R 1.04-1.06, G 1.19-1.23) and the check asserts. Measured that
it IS browning: median gain by page band 3-40 B 0.992, 41-80 0.98, 81-120
1.001, 121-150 1.075, 151-178 1.217 -- monotone toward the back cover;
chromatic (B moves ~5x R); corr(page, log gB/gR) +0.79; the thumbs' own white
reads R-B 38 at p003 rising smoothly to 68 at p178. Check 7e on the published
masters is clean (mean |d(R-B)| 0.90 DN, worst band 4.39 against 6.0), so the
gain did its job. Decision: accept; run the remaining checks with the band at
0.35. Cost: ~10 min and a re-run of the whole block (it is one fence, so the
assert also killed the stamp-agreement half of 7f).

**Suggested.** In 7f: "HARD_BAND bounds a LEVEL error, not browning. Before
treating a page beyond it as mismeasured, test whether the over-band pages are
the issue's outermost interior leaves and the gain is chromatic and monotone
in page number (SH8607: 170-176, B 1.30 / R 1.05, corr 0.79). That is the back
of the book browning; accept it if 7e is clean." And split 7f's assert from
its stamp-agreement half, so one cannot hide the other.

**Also: never `| tail` a long Verification block.** My first run piped it into
`tail -120` and lost checks 1-6's output; the rule's own "never pipe a check's
findings into head" applies to tail too. Write the whole output to a file.

## 050 — the exact-case whitelist keeps lowercase parameter placeholders that collide with real tags (`<p>`, `<s>`)

**What the rule says.** r050: a `<…>` whose name matches the HTML whitelist
exactly is kept as a tag. **What happened** (reported by the 040-070
sub-agent, confirmed by me): XMENU in Tips & Tricks prints the syntax
`MENU <x>, <y>, <l>, <p>, <t>, <m>, <s>, <ar>` and later explains `<p>` twice.
`<x>` `<t>` … were escaped; `<p>` and `<s>` survived as live tags -- a stray
paragraph open and a STRIKE-THROUGH opener in the published HTML. No
Verification check can see it (the output is "valid" markup). I escaped the
four sites by hand after 070 (2 min). **Suggested.** In r050: "A whitelisted
name inside a comma-separated run of escaped placeholders (`&lt;x&gt;, <p>,
&lt;t&gt;`) is a placeholder too: escape it. Verification: grep for a bare
`<p>`/`<s>`/`<b>`/`<i>` adjacent to `&lt;…&gt;` on the same line."

## 070 — U+201A must be resolved "against the page" inside a script step the chain treats as mechanical

r070: "Resolve each against the page… This step, not later." r000 classifies
040-070 as editorial-but-scripted, and a dispatch briefed as "mechanical, no
word fixes" (mine) correctly stopped at 54 open sites. The rule never says
who resolves them or that 070 is not closed until `grep -c '‚'` is 0.
**Suggested.** In r070 Verification: "`‚` count must be 0 before 080; the
sites are resolved by a crop-reading pass (one sub-agent, evidence per site),
not by the script." Also (sub-agent): the dash pass is NOT idempotent on runs
like ` - - - ` (non-overlapping matches skip the middle); and r050's planted
test writes to `/tmp/t50.md`, against r000's scope rule.

## 080 — "joined at the jump" assumes the host prints "Fortsetzung auf Seite M"; SH8607's p65 does not

r080: "When 030 hands over a `[Fortsetzung von Seite N]` section, splice its
text where the host's `Fortsetzung auf Seite M` line was". SH8607's Memory Map
table ends on p65 with NO forward pointer; only p106 prints "Fortsetzung von
S. 65" as a headline over the rest of the table. 030 saw no marker pair (it
requires both directions), so it glued p106's table to the end of the
PREVIOUS article on the page sequence, Rechnen in Maschinensprache, after its
byline. The 080 sub-agent caught it on the page and moved ~45 paragraphs to
Memory Map's end; my own pre-flight page list had it wrong (I assigned 106 to
Rechnen by sequence). Cost: one wrong pre-flight entry, caught. **Suggested.**
r080: "A page whose headline is 'Fortsetzung von S. N' is a continuation even
when page N prints no forward pointer: splice it at the END of the article
that holds page N, and add the page to that article's 64er.pages." And r030:
report a one-sided 'Fortsetzung von' headline as a WARNING line naming both
pages, instead of silently attaching the text to the page-order predecessor.

## 100 Verification — the TOC-coverage check cannot parse lettered pages, so it reports both p139 articles missing

r100's coverage check splits a spec with `part.partition('-')` and keeps it
only `if a.isdigit()`. r080 REQUIRES lettered pages for two starts on one
page (`139a`, `139b-141`), so the check prints "NO ARTICLE for … Garbage 64
Version 2 p139" and "… Programmierhilfe … p139" on a correct issue -- red on
correct output (r000 *A CHECK THAT CANNOT PASS*). **Suggested.** Strip a
trailing `[a-z]` before `isdigit()` (r080 check 4 already admits the letter).
Also (sub-agent): r100 refers to "glyph normalisation" for the toc_title
comparison only via r090; it should say whether `&` vs "und" (164 "Tips &
Tricks kunterbunt" vs TOC "Tips und Tricks kunterbunt") is wording (yes, we
set a toc_title) -- and that edits made after the script has self-staged are
left unstaged (MM), so the commit must stage by pathspec.

## 120 — five small gaps met extracting SH07A/B (reported by the sub-agent, decisions mine)

1. **Check 3b drops whole sections.** Comment: "A SECTION'S PAGE IS ITS LAST
   *NUMBERED* SEPARATOR; AN ALL-DASH BAR IS A FRAME"; code: `if sep and not
   re.search(r"-+\d+", sep): continue`, which SKIPS the files under a text
   label (`---- windows ---`, `---- nur mit ---`, `---eingabehilfen`) instead
   of re-keying them to the previous numbered separator -- so the check that
   exists to show a missing section omitted 110's ten listings, 124 and the
   Eingabehilfen. Suggested: carry the last numbered page forward.
2. **3b strips the lettered suffix**, so 139a/139b both map to whichever
   article sorts last. Suggested: report "AMBIGUOUS: 139a/139b" and require a
   prg.txt note naming the article.
3. **The raw-byte rule covers only >= $80 after REM.** label-demo 1-4 carry a
   raw $12 (RVS ON) in a REM banner; petcat writes `{rvon}`, which outside a
   string re-tokenises as 5 literal bytes, so the download is 5 bytes off. The
   table says "a REM-only difference | nothing at all"; a raw control byte in
   the .txt would put an invisible control char into the published text view.
   Left as is. Suggested: name the < $20 control-byte case explicitly and its
   disposition (leave, REM-only), so the next build does not spend a test on it.
4. **"Pass the dialect explicitly for anything that is not a C64 BASIC 7.0
   program"** reads as if a C64 program were 7.0; it means "not C64 V2".
5. **Same filename on two disk sides** (dia-show on A = notice, on B = the
   program): the extractor keeps whichever came last, silently. Suggested: a
   collision line in the extractor's output.

## 006 / r000 — "the PDF waits only for title.png" has no recipe for doing the rest early

r000 *BUT THE PDF DOES NOT WAIT FOR THE FIGURES* and control's brief make the
cover the only thing the PDF may wait on, but r006 step 2 (OCR cache, 150 dpi
rasters) refuses to run without `TITLE_PNG`, and nothing says the hours of
OCR/guetzli/classification may run before the owner's file exists. I ran them
with the untouched `title_source_150.png` as a stand-in in `<tmp>` only, so the
real cover costs page 1's caches and one pinned-q assembly. **Suggested.** In
r006 *Run*: "Before the owner's cover exists, run steps 2-4 and the
Verification with `TITLE_PNG=<tmp>/title_source_150.png` into `<tmp>/trial/`
(never into issues/), and record q. When title.png arrives, step 3 for page 001
plus a QMIN=QMAX=q assembly is all that remains."

## 130 — the display table's Hypra-Ass and Top-Ass rows do not match the generator

r130 table: Hypra-Ass `<pre data-filename="<name>.src" data-assembler="hypra-ass">`,
Top-Ass `<pre data-filename="<name>.prg" data-assembler="top-ass">`. The
generator appends `.prg` itself (`listings_bin[name+'.prg']`), so `.src` and
`<name>.prg` both miss; the precedent issues use the BASE name. With the base
name, r130's check 2 and the wrapper's check 1 FAIL on correct output (they
look for `<name>.txt`), which is how SH8607's 86 produced 10 FAILs. Reported by
the 130 sub-agent; I did not re-derive the generator side. Also unclear:
"insert after the </p> of the paragraph containing the first mention" when
that paragraph ends in a colon introducing an example (86 L10, 110 L2) -- the
agent placed after the example. **Suggested.** Fix both table rows to the base
name, teach checks 1/2 that `data-assembler` resolves to `prg/<name>.prg`, and
add the colon case.

## 140 — duplicate ids within an issue: the rule and its check disagree; and my brief dropped reprints.txt

r140 says SH8604's course "runs over 7 articles … all 7 take `kurs`" and
"Uniqueness is **within the issue** … only where the generator needs it", while
its Verification check 2 flags ANY duplicate id (and SH8604 now has one
`kurs`). The sub-agent kept all ids unique (122 `checksummer-c128`, 159
`tips_basic`). **Suggested.** State one answer and make the check match it.
And, MINE (rule fine, I was not): r140 says "If that step is delegated, the
brief must SAY to write the file [reprints.txt]". My 140 brief did not; the
agent ran the overlap pass, reported the results and correctly did not write
outside its scope. I wrote the file from its numbers (5 min). The warning sits
mid-section; **Suggested**: put "the brief must ask for issues/<ID>/reprints.txt"
in r140's *Goal* line, where a briefer reads.

## 006 — make_issue_pdf.sh sets no thread limits; a JOBS-sized run took the box down and the watchdog killed another user's model server [BLOCKER-CLASS]

**What the rules say.** r000 *PARALLELISE TO HALF THE FREE RAM*: "`OMP_NUM_THREADS=1`
stays. It is what makes a lane exactly one core: numpy and ImageMagick both
thread by default"; and records that 32 concurrent magick processes once drove
the load to ~975 and the inference watchdog killed the server. r006 step 2/4:
`JOBS=28 tools/img/issue_pdf/make_issue_pdf.sh …` -- no thread limits named.
**What happened** (006-prep sub-agent, 2026-10-23 ~14:00): `JOBS=22` without
`OMP_THREAD_LIMIT` (what tesseract obeys -- OMP_NUM_THREADS alone is not it)
or `MAGICK_THREAD_LIMIT`: load ~390, /Users/mist/DNB/llm/mem-watchdog.sh
emergency-killed the omlx server (~231 GB) and its restarts until 14:12. The
agent stopped the run, removed 6 half-written OCR pages, re-ran with
`OMP_THREAD_LIMIT=1 OMP_NUM_THREADS=1 MAGICK_THREAD_LIMIT=1 JOBS=24`: load
< 15, 7 min 27 s. The server stayed down; reported to control for a human.
`make_issue_pdf_mixed.sh` sets only MAGICK_THREAD_LIMIT. **Suggested.** Set
all three limits INSIDE both scripts (export at the top, so no caller can
forget), and in r006 *Run* say: "JOBS lanes are only safe because each job is
single-threaded; never run the PDF scripts without OMP_THREAD_LIMIT=1
OMP_NUM_THREADS=1 MAGICK_THREAD_LIMIT=1." Also: the mixed script's own
exiftool stamp writes `-CreateDate="$NOW"` without a zone (pdfinfo shows +2 h);
r006 step 5 restamps it, but the script comment calls its stamp final.

## 160 — four shapes the rule does not name (sub-agents' findings; decisions as taken)

1. A box's own LABEL line when the box also has a printed caption
   ("Erklärung der benutzten Speicherstellen" in p128's box, "CIA (6526)"):
   neither "text above its table is a <p> inside the <figure>" nor "section
   labels stay spanning <th> rows" fits. Used a `<th colspan>` first row.
2. A captionless named box: SH860x precedent is `<aside><h2>…</h2><table>`
   (MSE-Befehle); r160 never names `<aside>`.
3. "Place after the first paragraph that references the table" vs a table that
   floats to a page foot under a running program (p100) or into another
   section (p149): placed at the nearest point that splits neither a program
   nor a numbered sequence. And OCR that glued post-table text into the anchor
   paragraph (p12, p49): split at the print position. Neither is covered.
4. `tr.separator` is styled for `table.plain` only, so a ruled table's printed
   row groups (p100's six) run on with no gap.
**Suggested.** One short subsection "Box anatomy" with these four cases.

## 180 — the closed-vocabulary one-liner greps only the `xx = Name` key form

r180 says the Impressum key comes in two forms and to grep for both, but its
SILENT/UNDEFINED script matches only `xx = Name`. SH8607's Impressum (like
SH8606's) prints `Name (xx)`, so as written the check reports every initial as
UNDEFINED. The sub-agent rewrote it to grep `\(([a-z]{2})\)` too. Also: a
Koordination name printed WITHOUT initials (Georg Klinge, signing `gk`) is
always UNDEFINED. **Suggested.** Match both forms in the script, and allow a
one-line `adjudicated` key for a known unprinted initial (gk = Georg Klinge).

## 210 — two clauses disagree when a shared unlettered start page's only band belongs to the PREVIOUS article

r210: for a shared unlettered page "the band describes the page, so the
starting article takes it" -- and, for an article whose pages carry another
band, it "takes ITS page's band, because that is the band above its own text".
SH8607's p73 has one band (C 128 / GRUNDLAGEN) over 66 Zeropage's tail; 73
Spielen mit Musik und Grafik starts below it and is a C 64 piece whose own p74
reads GRUNDLAGEN / C64. Decided: C 64 (the band above the article's own text).
**Suggested.** "When the shared page's only band sits over the previous
article's text, the starting article takes the band of its first page that is
wholly its own." Also: r220 applied 41/41; the CSV's double space in "Garbage 64
Version  2" was normalised and recorded in reviewed/r220-orphan-rows.txt.

## 250 / 270 — two Verification blocks against r000's own check discipline

r250 check 2 is `grep … | head -20` (r000: "never pipe a check's findings
into head"); harmless here as an eyeball sample. r270's block ends on
`grep … && echo FAIL`, so a CLEAN run exits 1 -- red on correct output for
any exit-status reader (r000: test output non-empty). **Suggested.** Drop the
`head`; give r270 the `rc=…; exit $rc` shape r250 already uses.

## 260 — the Verification block uses `$PY` without defining it

Run as written under bash it dies with `-: command not found` at check 1's
`caps=$($PY - <<'PYEOF'` and check 2's `$PY -c`, and still exits 0 -- r000's
"`$PY` used in three fences with no definition" defect, here again. Fixed for
the run by exporting PY. **Suggested.** First line of the block:
`PY=${PYTHON:-.venv/bin/python}`. (Also, MINE: I pre-scanned h1-h4 and wrote
a heading-all-caps adjudication for five h3 routine names the check never
looks at; the check correctly failed on the over-declaration and I removed it.)

## 280 — two internal contradictions met by every sub-agent

1. Briefing: "`<pre>` IS in scope" and "Do NOT touch … `<code>`"; the
   Verification strips `<code>…</code>`, which removes every `<pre><code>`
   listing -- and nearly all of SH8607's listings are `<pre><code>`. Read as:
   `<pre>` (with or without inner `<code>`) in scope, inline `<code>` out.
2. *Evidence-in-report* still asks for "block-index output showing the other
   engine read the **corrected** form", which the rule's own section
   "EVIDENCE IS THE CROP, PLUS THE INDEX LINE AS A LOCATOR" says is impossible.
   Agents followed crop-plus-locator.
**Suggested.** Say "<pre> and its inner <code> are in scope; inline <code> in
prose is not", make the Verification strip only inline <code>, and rewrite the
evidence requirement to the crop-plus-locator form.

## 280 Pass 1 — "Hard-und → Hard- und" reads as unconditional; SH8607 prints "X-und", "HiRes-und" without the space

The Pass 1 example assumes the OCR lost the space after a compound hyphen.
On SH8607 p79/p77 the PRINT sets "Die X-und Y-Register" and "im HiRes-und im
Multicolor-Modus" closed (crops agent280B/crops/p79_Xund_0.png,
p077_HiResund_0.png). Kept as printed. **Suggested.** "…→ `Hard- und`
only where the crop shows the space." And (MINE): my 280 brief told the three
agents to record baselines under letter-suffixed keys; the Verification reads
`r280-hyphen` / `r280-lost-space`, so the suffixes had to be merged afterwards.

## 290 Verification check 2 — red on correct output: it levels EVERY heading inside an aside, not the aside's own title

r290: "An aside's heading sits AT the level of the article's top section
headings". Check 2 runs `for lvl in re.findall(r'<h([1-6])\b', m.group(1))`
over the whole aside body, so the 44 body-size bold subheads (h3) under the
37 Texteinschub boxes' own h2 titles in SH8607's Memory Map all fail ("44
wrongly levelled") although the print sets them below the box title (crops in
<tmp>/agent290A/). Promoting them to h2 would contradict the print. The same
branch fires on published 8606 (6 in 3 files) and 8609 (2 in 2). Left as is;
check 2 reads no adjudication, so it cannot pass on this issue. **Suggested.**
Test only the FIRST heading of each aside (or skip headings that follow an h2
inside the same aside).

## 020/190/320 — a ruled prose box OCR'd INTO a listing block is invisible to every text step

SH8607 p151: the box "Wichtiger Hinweis zum Abtippen – Bitte beachten Sie den
neuen Checksummer 128 …" was OCR'd as the HEAD of block 7, label
`listing-standalone` (byline + box + the kernel 128 dump). 020 drops listing
blocks from the text by design, 130 replaced the dump with the disk embed, 190
walked the page but the box never appeared in the HTML to be repaired, and
r320's UNACCOUNTED half excludes listing blocks. Found at 290 by an agent
comparing bold heads on the page. Restored from the crop. **Suggested.** In
r020/r320: a `listing-standalone` block whose leading lines are prose (no line
number, no hex address, sentence punctuation) is split -- or at least listed
by r320 as "prose inside a listing block".

## 290 — Sonderheft precedent (SH8602-SH8606 MSE/Checksummer at h2) vs the owner's "looks like h3 → h3"

Decided for the owner's 2026-10-08 ruling: 9 body-size bold own-line heads
h2 → h3 (86 ×2, 120 ×3, 122 ×3, 125 ×1), as SH8608 did, against SH8606's r290
which kept h2 by DEFAULT. **Suggested.** r290's DEFAULT section should say the
owner's print-weight ruling overrides earlier printings' levels.

## 325 — four gaps met by nine readers

1. **Verification 4 (`generate.py --issues <ID> --future --join` exits 0)
   cannot pass before the owner's title.png exists** -- generate.py stops on
   FileNotFoundError at l.2270. Every reader reported it. Suggested: "before
   title.png exists, run it on a scratch copy with title_source_150.png as a
   stand-in (never copied into issues/)".
2. **The locator advice names `pdftotext -bbox <issue pdf>`**, which does not
   exist during the build (r000 THE PAGE IMAGE IS masters600). Readers used
   labels.json bbox_frac. Suggested: name that.
3. **"Monospace spacing, by glyph column" assumes a fixed pitch**; this issue's
   typewriter-like faces drift 36-44 px, so `""` vs `" "` became undecidable at
   several sites (kept as is). Suggested: say the fallback (keep the
   transcription; record as undecidable) explicitly.
4. **Image loads fail silently for a sub-agent ("media removed" / request
   limit)** -- two readers first believed they had checked pages they had
   never seen; one stated it honestly (pp21-28) and a second reader re-did them
   with vision. Suggested in the 325 brief: "for every crop you rely on, confirm
   the image actually loaded; report the pages you could not see".
Also seen: a line-break after "Low/" or "-/" was joined WITH a space by 010
(14 sites in the Memory Map: "Low-/ High", "VC 20/ C 64"); r280's Pass 3 does
not look for it. Suggested: a Pass 3 item "a space after `/` before a capital
is a line-break join -- the print sets `x/Y` closed mid-line".

## End gate — "the issue must BUILD" before the owner's title.png exists needs a scratch-copy recipe

r000's end gate and r325's Verification 4 run `generate.py` on the real tree,
which stops on FileNotFoundError: issues/<ID>/title.png until the owner
delivers it -- and the stand-in must never enter issues/. What worked here:
copy the repo without .git and without the other issue dirs, copy
issues/<ID> plus the SHARED dirs issues/fav and issues/fonts (the generator
copies issues/fav/apple-touch-icon-dev.png and dies without it), put
<tmp>/title_source_150.png in as title.png, `git init` + an EMPTY COMMIT
(generate.py runs `git rev-parse --abbrev-ref HEAD` and dies on a repo without
HEAD), then run it. Three attempts to find those two traps. **Suggested.** Put
this recipe in r000's end-gate section, verbatim.

## 330 — a merged reprint of 18 parts makes the per-D record 74,621 lines, positional, and kept only in a git-ignored LOG

r330 requires one `- D-NNN` line per difference per lead × original, and
`verify` parses LOG.md. SH8607's Memory Map is merged from 18 monthly parts;
each diff of the whole article against one part is ~3,900 differences (the
other 17 parts' material all reads "block only in SH"), so the section is 23
pairs / 74,621 lines / ~19 MB. Three consequences the rule does not foresee:
(1) the lines are positional, so EVERY edit to the article (an OURS fix, the
credit, step 150's figures) renumbers all 18 pairs -- the record had to be
regenerated by content after the fixes, and it will have to be again after the
owner's crops are placed; (2) LOG.md is git-ignored (r000), so this record --
the evidence that 74,621 differences were looked at -- does not survive a
clone; (3) the dispositions came from three agents with three different
tools (330A carried lines, 330B per-part spans + mklog.py, 330C a component
matcher keyed to its own ids), and a fourth agent mapped them onto r330's
numbering with heuristics of its own (MOVED at 3-gram coverage >= 0.6, etc.).
Cost: ~2 h of agent time for the record alone.
**Suggested.** (a) For a merged reprint, diff each part against the SECTION
of ours it supplies (r330 `diff --range`), so "block only in SH" stops being
97 % of the record; (b) key dispositions by content hash, not position, so a
fix does not renumber them; (c) keep the disposition record in
issues/<ID>/reviewed/r330-<pair>.txt (durable), with LOG.md holding only the
summary table. Vocabulary gaps closed explicitly here, as the rule asks:
figure-not-yet-placed = CROP; dash-glyph-only = PRINT with a sentence.

## 005b — on a full-bleed cover the wider-than-A4 branch keeps the spine and clips the cover

p001's traced box is 5180 px (219.3 mm: front cover + spine strip), so 005b's
`place()` took the "wider than A4" branch, which trims the side with MORE BLANK
COLUMNS (`col > BLANK_COL_INK`). A full-bleed cover has no blank side: the
spine's ink starts at column 0, and the 4 px of white between the right trim
(x=5176) and the traced box edge (5180) made the right count as "more blank".
So the window sat at x=0: it kept the whole spine strip and cut 215 px (9 mm) off
the cover's right -- the price read `DM 14`, the banner `Diskette erhältli…`,
the right cyan border was gone. Nothing flagged it: `fabricated` was 0.36 %
(the window is inside the traced box, which includes the spine) and `alpha` is
documented as meaningless on a full-bleed page. It propagated into
`title_source_150.png` (a straight reduction of a4600/001) and the PDF's page 1;
control caught it by comparing against SH8604's `title.png`. I had also
mis-framed it at hand-over as "spine strip left -- trim or keep at the owner's
discretion": a window that excludes printed ink is a defect, not a preference.
Fixed by `<tmp>/scripts/recover_005b_p001.py` (recovery D): edges read off the
master's cyan profile (fold crease x=251, right trim x=5176, cover 4925 px),
window centred on the cover at x0=233, y0=-12 unchanged; OVERRIDE in the stamp.
**Suggested.** (a) On the cover leaf, locate the fold (the crease / the
spine-strip boundary) and take the window from the fold outward -- never from a
blank-column vote, which a full-bleed page cannot answer; (b) a gate for every
traced-edge page: the window must contain all of the traced page's ink on the
side AWAY from the binding (any ink column cut on the outer side is RED); (c)
r005b's hand-over of the title source checks the four edges against the
master (price box, border all round) before it goes to the owner, judged
against the previous issue's published `title.png`.

## 190/marks — a glyph under a hand mark was read as part of the mark (p54 "PRINT#.")

A pen tail ran through the "#" in "CMD und PRINT#." on p54. I took the "#" for part of
the reader's addition (slanted, heavier-looking) and set the HTML as "PRINT.", recording the
whole thing as mark 054h. The owner repainted only the tail; control then measured the plate:
the full stop sits AFTER the "#" (a hand insertion would have had to displace it), the T-to-#
gap is 14 px against the line's 27 px word space (letter spacing), and this grotesque draws
"#" with oblique stems. 8603's original (Teil 16) prints "PRINT#." as well. The HTML was
corrected after the owner's pass (62957b8b); the published page and the HTML had briefly
disagreed.
**Suggested.** When a mark crosses or touches a glyph, decide the glyph SEPARATELY before
attributing it to the hand: compare it with the same character set elsewhere in the issue,
check the spacing it occupies against the line's letter and word space, and, for a reprint,
read the original's page. Record the mark as only the strokes that fail those tests.
