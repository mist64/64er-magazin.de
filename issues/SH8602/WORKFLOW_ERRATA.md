# SH8602 — workflow errata (r340)

Written as the build goes. Newest at the bottom.

## 005 — the scans are MIXED RESOLUTION and step 005 hardcodes 2400 dpi

**What the rules say.** r000, *Where the scans are*: "`/Volumes/S/png/<ID>/NNN.png`
the 2400 dpi masters". r005_masters_sheet.py: `SCAN_DPI = 2400`,
`SCAN_REDUCE = SCAN_DPI // MASTER_DPI  # 4`. r000's thumb recipe: one command,
`magick "$m" -scale 6.25%` for every master.

**What I did.** Ran the thumb recipe verbatim over all 168 masters. 160 of the
thumbs came out ~317 × 449 px — 37.5 dpi, not 150.

**What is true.** SH8602's pages **003–162 are 600 dpi** (`5029 × 7188` px,
`236.22 px/cm`, ~63 MB); only **001, 002, 163–168** are 2400 dpi
(~20300 × 28751, ~850 MB). The raw TIFFs in `/Volumes/S/scan/SH8602/` are the
same (~72 MB interior, ~1 GB cover), so no 2400 dpi copy of the interior
exists. r000 *does* hint at this — `create_thumbnails.sh` "branches by page
range because that issue's scans were *mixed resolution*" — but as a reason to
distrust found thumbs, not as a property the chain must handle. Re-derived the
interior thumbs with `-scale 25%`; all 168 are now 1256–1349 px wide.

**Cost.** ~5 min, 4 commands to notice and re-derive. The real cost is
downstream: step 005 sheet cannot run on 160 of 168 pages as written.

**What would have prevented it.** r000 thumb recipe: "Scale each master by
`150 / its own dpi` (read `%x` from the PNG), never a fixed 6.25 % — SH8602 is
600 dpi on 003–162." And r005: `SCAN_DPI` per page from the PNG header.

## 005 — the sheet variant asks for a "measured colors.txt" and says nowhere how to measure one

**What the rule says.** r005_masters_sheet.md: "`low` — the cheap interior
stock … this issue's **measured** `colors.txt`". The procedure for measuring
`W` lives only in r005_masters_spread.md, *The profile is MEASURED for this
issue's paper*; the sheet rule points at SH8601's existing file.

**What I did.** Found no `colors.txt` beside SH8602's scans (correctly — r005
spread says the profile lives in the repo) and went looking in the sheet rule
for the procedure; it is not there. Took it from the spread rule.

**Cost.** ~3 min, 3 commands.

**What would have prevented it.** One line in the sheet rule's *Two papers*
section: "For a new issue, measure `paper.low` as in r005_masters_spread.md
*The profile is MEASURED* (pool interior thumbs, low percentile) and write it
to `issues/<ID>/colors.txt`."

## 005 — the mixed-resolution fix, as made (moved under the build)

The resolution problem above BLOCKED step 005, so it was fixed at once
(r000: "a defect that BLOCKS the build … is fixed at once … recorded in the
errata as having moved under the build"). The owner, asked at PAUSE 1, chose
this over a rescan.

- `r005_masters_sheet.py`: new `scan_dpi(scan)` reads the PNG pHYs, snaps to
  `SCAN_DPIS = (600, 2400)`, and cross-checks that the frame is 250–350 mm tall
  at that resolution (else `PageFailed`). The reduction is per page:
  `dpi // MASTER_DPI`, so 4 at 2400 (unchanged) and 1 at 600. A 600 dpi page
  has no `masters2400/NNN.png`; its full-resolution render goes to scratch,
  because there it IS `sheets600`. `cmyk2400/NNN.tif` is still written (the
  separation, at the scan's own dpi). Every stamp gains `scan-dpi`.
- **Before/after, measured** on p050 (600 dpi) and p163 (2400 dpi):
  - p050 before: traced **53.2 × 76.0 mm**, published as an uncropped sheet
    (every mm constant read at a quarter scale). After: **209.2 × 296.9 mm**,
    A4 class, own-paper white 255, dark contrast 251.
  - p163 before → after: `masters600`, `sheets600`, `masters2400` and `debug600`
    all **pixel-identical** (`magick compare -metric AE` = 0); the profile
    is byte-identical; the stamp differs by the one added `scan-dpi 2400` line.
- **Consequence for r005's Verification 1** ("every page produced all six
  artefacts"): it now has to expect no `masters2400/NNN.png` for a 600 dpi
  page. Not edited mid-build; harvest it.
- The lane peak (19 GB) is a 2400 dpi number; a 600 dpi lane is ~1/16 of it.
  Sized by the rule anyway (`lanes(19)` → 10).

## 005 — the sheet Verification names an output the code no longer writes

**What the rule says.** r005_masters_sheet.md, Outputs and Verification 1, 4, 6:
`<tmp>/figures600/NNN.png` "the figure master — r145 reads this", read through
`R.OUT_FIGURE`.

**What is true.** `r005_masters_sheet.py` has no `OUT_FIGURE` and writes no
`figures600/`; its outputs are `masters600`, `masters2400`, `sheets600`,
`cmyk2400`, `debug600` (`OUT_DIRS`). Only the module docstring still says
`figures600`. Pasted verbatim, checks 1, 4 and 6 die with `AttributeError`
before checking anything.

**What I did.** Ran them with `figures600` replaced by the directory that
exists. Recorded which in LOG.md, per check.

**Cost.** ~5 min reading code to establish it.

**What would have prevented it.** Outputs/Verification rewritten against
`OUT_DIRS`: `sheets600/NNN.png` is the uncropped graded sheet, and the
figure-render check (6) has to say which of the two existing renders is
uncurved, or be dropped.

## 005 — Verification 4 flags 166 of 168 pages on the printed footer

**What the rule says.** Check 4: "a 6 mm band inside the TRACED PAGE's own
four edges holds no bed and no prop — except where full-bleed art
legitimately reaches the trim." It prints numbers; it does not say what
"holds no bed" means numerically, and its worked table was SH8601's.

**What is true.** SH8602 prints a black `SONDERHEFT` bar, the 64'er logo and
the folio 3–5 mm above the foot on every interior page, so the bottom band
reads 10–28 % "dark" (lum < BED_LUM) on almost every page. Looked at 007 and
009 at the foot: print, no bed. A per-page printout of 168 lines in which
nearly every line is non-zero is not read by anyone.

**Also:** check 6's premise (figures600 is the UNCURVED render) does not hold
for what exists: `sheets600` measures glyph p50 21/24/19/20 on
050/100/120/150, identical to `masters600`. Both carry the curve. The
"fidelity" render the rule promises figure cuts does not exist in the
current code.

**What would have prevented it.** Check 4 should compare against a band
1–2 mm *outside* the trim line (where only bed can be), or exclude rows that
are dark across ≥ 40 % of the width in one run (a printed bar), and state a
threshold. Check 6 should be rewritten against what the code writes.

## 040 — the script does not implement the rule's "length 2 only if paired"

**What the rule says.** "length == 2 → keep only if it pairs within the
paragraph; an unpaired `**` is a literal and is escaped." **What is true.**
`r040_escape_asterisks.sh:39` keeps every length-2 run unconditionally
(`return m.group(0) if n == 2`); the Verification still says the bold count is
"invariant by construction". No effect on SH8602 (no `**` outside fences);
the next issue with an unpaired `**` ships it as a bold delimiter. The script
also calls bare `python3`. And the Notes' "List bullets in this project are
always `-`" is false for this OCR output: SH8602 has 9 `* ` bullet lines,
which become literal `\*`. Found by the 040 sub-agent; ~1 min.

## 120 — "the same root with the SH naming" points at the wrong disk

**What the rule says.** "For Sonderhefte the file lives under the same root
with the SH naming." **What I did.** Looked for `SH86*`, found
`SH8X/SH86A.D64` / `SH86B.D64` — a plausible "SH 86, sides A/B" — and nearly
took it. Its directory (Dateiverwaltung, Haushaltskasse, Floppy, Sound) is not
this issue. **What is true.** Sonderheft disks are numbered by the magazine's
running Sonderheft number, not by year: `SH0X/SH01.D64` is SH 1/86 (SH8601's
prg.txt names it), `SH0X/SH02.D64` is SH 2/86 — header "sonderheft 2/86",
separators matching this issue's pages. **Cost.** ~5 min, 6 commands.
**What would have prevented it.** "Sonderheft N/86 is
`~/tmp/64er-Disketten/SH0X/SH0N.D64`; confirm by the disk header
(`sonderheft N/86`). `SH8X/SH8nA/B` are other Sonderhefte — do not match on
the year."

## 050 — rule and script disagree on `</`+non-letter, and on why it is idempotent

"EXCEPT `</` followed by a non-letter … Escape those too": the script's regex
`<(/?[a-zA-Z][^<>\n]*?)>` needs a letter after `/`, so `</>` passes through,
and the Verification uses the same letter-first regex so it cannot see it
either. The "lookbehinds for `\`" given as the idempotence reason are not in
the script (it is idempotent because entities carry no `<`). Moot on SH8602
(0 occurrences). An unclosed `<`+letter (`31 <A AND`) is not discussed;
Discount happens to escape it. Found by the 050 sub-agent.

## 060 — `<ol>` without `start=` silently renumbers; nothing checks it

**What the rule says.** "`<ol type="a">` in a converted file is a **bug
signature**" — the only list defect it names. **What is true** (060 sub-agent,
SH8602): Discount emits no `start=`, so every printed list not starting at 1
shows from 1 (9 lists here), a list interrupted by prose becomes one-item
`<ol>`s that all say "1." (~20 here), two adjacent lists fuse and continue
numbering, and a BASIC line `1000. PRINT …` loses its line number entirely —
the same silent text loss as `M. Grewe`, by another route. The corpus carries
one `<ol start=` in 130+ `<ol>`, so earlier issues probably shipped this
unseen. Also: the rule's `<p><pre>` example does not reproduce on Discount
3.0.2.0 (post-pass unwrapped 0; its regex also misses `<p> <pre>`); a literal
`\*` inside a raw `<p class="source">` block ships as `\*`; and the "`<br` >
0" spot-check passes on hand-written `<br>` alone.
**What would have prevented it.** A 060 check: every `<ol>` whose source line
begins with N≠1, or a number ≥ 100 (a BASIC line), is listed for 190 with
its source line; and `<ol start="N">` named as the fix.
**Cost.** None yet; found by the 060 sub-agent, fixes owed at 190.

## 070 — the script still has the ordering bug its rule says was fixed

"Order matters: fold the curly quotes FIRST, then `''`. As shipped, `''` →
`"` ran before…" — `r070_html_cleanup.sh` still lists `("''", '"')` before
the curly folding. The rule also says a formula's double prime must be left,
while its table and script convert every `''`. And the rule file's own curly
characters have been flattened to ASCII in places, so table rows read
`"` → `"`. No effect on SH8602 (one `''`, OCR garbage). Found by the 070
sub-agent.

## 080 — Verification 4 rejects the lettered pages the same rule demands

`grep -vE 'content="[0-9,\- ]+"'` flags every `NNNa`/`NNNb`, which "Three
conventions" requires; and nothing says the FILENAME keeps the plain number
(the corpus does: 8507, 8508). The splitter turns ANY `<p>(…)</p>` into a
byline, and its DOTALL regex can span paragraphs — SH8602 got 7 false
bylines and one `<address>` that swallowed two paragraphs and broke the
`<head>`; a post-split check ("every `<address>` matches `(Name/)xx`") would
have caught them. The "escaped HTML text" sentence does not describe the
code (it strips tags, keeps entities). The script calls bare `python3`.
Also: which `64er.issue` form a Sonderheft takes is shown only by the Usage
example (`'Sonderheft 7/86'`), and SH8601 shipped `SH8601` — I briefed from
the outlier first. Found by the 080 sub-agent; correction ~3 min.

## 110 — the Sonderheft case is "all" in the header and monthly in the body

"Applies to: all — the README's release table carries the Sonderheft dates
too". It carries bounds ("**vor** 14. Februar 2026", "ca.", "unbekannt"),
which "Convert `TT. Monat 20JJ`" cannot read; the Vorschau derivation is
monthly-only; the Verification grep `"${YYMM:2:2}/${YYMM:0:2}"` with 8602
digits matches the MONTHLY 02/86 bullet (and breaks on `SH8602`). Nothing
says what to do with a bullet that holds a bound. Wrote a provisional date and
carried it to PAUSE 2. Found by the 110 sub-agent.

## 090 — small inaccuracies

"Find the TOC pages in the issue's PDF (usually pages 6–7…)" — names the PDF
the next block forbids, and assumes two pages (this Sonderheft: one, p5).
"entry is the printed entry text" — title only, or title + subtitle? and
what of entries not printed at all (Eintipphilfen, Impressum)? Check 2 says
"run once all toc_category metas are filled", but from 080 on every file
carries `XXX`, so before 100 it fails rather than being vacuous. "Normalised to
Title Case" is wrong for German ("Listings zum Abtippen"). Found by the 090
sub-agent.

## 120 — Check 2's comment contradicts the rule; shared and repeated separators

Check 2: "each `----------NN` should map to a `NN ….html`" / "matches the
start page of some article" — against the rule's own "`NN` is the PAGE … not
as a start page" (SH8602: 142–151 inside 141; 113, 114). Not said: two
identical separators (`131` twice) map to 131a/131b in disk order; a separator
page shared by two articles (53, 114, 138) is decided by file content. Case 1
claims the right dialect is "byte-identical, never merely closer" — false for
Simons' BASIC with tokens inside REM (`spline 64`: code identical, 6 REM
lines differ). The routing list misses the mirror of "BASIC at a load address
not ending in 01": machine code at an address ending in 01 (`pseudo-irq` at
$9E01) is decoded as BASIC garbage. Found by the 120 sub-agent.

## 100 — the wrapper does not parse under /bin/bash; the helper contradicts the rule

`r100_toc_category.sh` dies under macOS `/bin/bash` 3.2 ("unexpected EOF while
looking for matching `"`" at line 87; backticks in a Python comment inside
`$(cat <<'PY' …)`); it runs under Homebrew bash 5. `r100_toc_title_apply.py`
writes a toc_title for every article (rule: only where it differs; delete the
placeholder otherwise) and writes `&` raw (rule: `&amp;`); the rule never says
whether to use it. The "unclaimed TOC entry" check skips lettered pages
(`a.isdigit()`) and labels every section "Rubriken". Not said: whether a
Sonderheft's printed subtitle line joins toc_title (SH8506/07 yes, SH8601 no).
Found by the 100 sub-agent.

## 130 — placement sentences that contradict each other, and a verifier that flags the rule's own variant

"The figure block must be inserted after the `</p>` of the paragraph
containing that first mention" vs the Placement-style shapes "all listings in a
single block at the very end" — no precedence stated. "Within a tip section,
listing goes AFTER the byline" has no fallback for a byline fused into a `<p>`.
Verifier #2 flags every Hypra-Ass `<pre>` backed by a `.prg`, which the
variant table prescribes. Verifier #6 "at least 3 words" fails on printed
captions such as "Listing 4. »Floppy-Lister«". The Sonderheft norm — disk
has the full program, the print only the changed lines — needs comma-separated
data-range runs, mentioned only in passing; a disk file whose line numbers
differ from the print (renumbered DATA) has no case. Found by the 130 sub-agent
(25 min, 156 tool calls).

## 140 — recurring-slug check is monthly-shaped

Check 4 compares against one `<PREV>` and flags any of its rubric slugs this
issue lacks — on a themed Sonderheft (SH8601 C 128 → SH8602 Tips & Tricks) it
flags `bücher`, `cpm`, so "All four checks should pass" cannot be met. "The
editorial slug should always be `editorial`" — Sonderhefte use `vorwort`
(SH8503–07, SH8601); `checksummer`, `mse`, `impressum` are not listed as
recurring. Check 3 pipes into `head -5` (r000 forbids). Found by the 140
sub-agent.

## 150 — r000's "every unplaced figure is a TODO" has no producer

r000 Gate 1: "every unplaced figure is a `TODO` by design". r150 never inserts
one before images exist, and no other rule does (r130's `<pre>TODO</pre>` is
listings only). r000 counts "r150 (6)" figure-dependent checks; r150 has 5.
Naming is unstated for tables (`-tN` is corpus practice), unnumbered tables,
unnumbered captioned images, uncaptioned non-lead images, and a non-lead
figure of the SECOND article on a shared page. "Always delegate scan reads to
sub-sub-agents" sits beside the pause-2 need to survey every page.
`r150_figure_captions.py` only sees caption blocks starting Bild/Tabelle/
Listing. Found by the 150 sub-agent.

## 160 — evidence demand cannot be met; caption check passes "Bildschirm"

"For each Pass-3 candidate block walked … paste the one line" vs Pass 3
returning 1746 lines on SH8602 and the rule itself calling it "a hint list to
skim". Check #7's `'Bild' not in cap` substring test lets "…auf dem
Bildschirm" pass; anchor `^(Tabelle|Bild) \d`. Not covered: a framed box with
no inner rules; a title printed as a full-width row inside the table; a column
header reprinted at the top of each column half; a caption glued into body
text when the table is left for crop. #5's regex also matches `Bild N`, which
floods it before crops exist. The visual walk found 13 tables the sweeps and
the 150 worklist had missed — the walk is the part that works. Found by the
160 sub-agent (23 min).

## 170 — mutually contradicting method sentences; no glyph convention; no version test

"tesseract-locate the caption's bbox in the rendered page" vs the block-index
recipe; "300 dpi is the right target resolution" vs "Crop from the graded 600
dpi master"; "Dispatch a sub-sub-agent to OCR the crop" beside the measured
GLM-OCR section, with no word on which is authoritative. Check 3 sees only
`<figcaption>Listing N`, so captionless boxes (all 29 Einzeiler) and named
captions are never checked. `r170_score_hex_ocr.py` is hard-wired to 8611's
`3d.code.prg`. No convention for an unnameable reverse/graphic glyph in a
listing without checksums (the agent used `[ILLEGIBLE]`, 39 times), nor for
side-by-side machine variants (VC 20 / C 64). Nothing says to TEST the
Checksummer version — 141 L11 verifies only under V1/V2 in a V3 issue.
Orchestrator error recorded too: my brief said "write only *.html", which
blocked the rule's "recreate as a disk file" — fixed by a second dispatch.
(78 min, 421 tool calls.)

## 180 — "expand initials" vs "keep initials exactly as printed"

Briefing step 3 and the evidence section say expand initials from the
Impressum; the guardrail says keep them as printed and only CHECK them. Case C
maps the Vorwort to the chief editor; a Sonderheft Vorwort is signed by its
writer (SH8602: Georg Klinge). The Impressum vocabulary check assumes `xx =
Name` lines Sonderheft Impressums never print, and misses initials inside
`(Name/xx)` bylines — 10 of the 11 here. Orchestrator note: my brief said
"use it to expand"; the agent followed the rule, correctly.

## 190 — aside heading level stated two ways; dash-list precedent misstated; "never retype" vs "restore from the crop"

"An aside's heading is one level below the article's highest section
heading" vs the next clause "`h2` when the body has `h2` sections" vs the
unconditional "The aside's heading is an `<h2>`". "Dash lists stay `<p>— …</p>`
… 8609-8611 all keep the paragraph form" — those issues carry 128 `<li>`.
"code inside `<pre>` must come from the existing HTML … never retype from
print" vs "restore them from the crop if not" — on SH8602 the OCR had lost
whole code values (20's organ program, 44's 2000–2160 loader) that only the
crop has. The broken-listing sweep's `(?=[A-Z]{2})` misses assignment lines
(`30 A=1`); the Verification uses `$TMPDIR_ISSUE` without defining it. Found
by the 190A sub-agent (50 min).
- 190B adds: "Convert … to `<ul>`/`<ol>` only when the print shows a real
  bullet glyph" contradicts "Dash lists stay `<p>— …</p>`"; the Verification
  has no check for the never-split-author rule it describes; nothing says
  whether the step-020 vision `truth/NNN.txt` transcripts may serve as a
  CANDIDATE source for a page whose OCR is hopeless (58: used, then verified
  against every page — r000's PDF-text-layer rule is the right analogue and
  should be cited here).

## 210 — "vorwort … carries the band WITHOUT a section word" is SH8601-only

Verification check 1 lists `vorwort` as excluded because "its page carries
the band WITHOUT a section word" — SH8602 p3 prints EINLEITUNG, as do
SH8503–07; and step 3 does not skip it. "Crop the top ~250 px" names no
resolution (at 600 dpi the band needs ~500 px). Check 1 only lists files and
compares nothing; check 3 is eyeball-only. Found by the 210 sub-agent.

## 220 — re-classified `all`, but every mechanism is still monthly

The apply script cannot read the Sonderheft CSV layout ("write one", no spec);
the routing check parses the monthly columns, so on a Sonderheft it examines 0
rows and passes silently, drops lettered pages (`lo.isdigit()`), and
`continue`s past unmatched titles (hiding both a mis-filed and an unapplied
row); Verification 1 greps `^<YYMM>,`. "Run it from the issue directory"
contradicts "ONE cwd: the REPO ROOT". Nothing covers a row whose page lands
inside another article and is clearly not it (SH8602's C16 row — nearest-
preceding routing would silently mis-file it onto article 20). "Category values
must match a TOPICS list in generate.py" — no TOPICS entry for the Sonderheft
CSV's top-level categories. Found by the 220 sub-agent.

## 230 — "8607 is the only issue that ships LaTeX" is false

8508/52 and 8602/71 ship MathJax too. Two sentences name 8606 as if it were
the current issue. The evidence example path (`/tmp/64er_<YYMM>_pages_600/`)
and "render at 300 dpi" contradict r000's masters600 rule. Nothing says what
to do with a formula an earlier step faked with a CSS overline. Found by the
230 sub-agent.

## 250 — check 4 accepts a source paragraph before a byline; $PY unset

The rule puts a single-topic source AFTER the `<address>`; check 4 accepts one
followed by `<address>`, so any pre-byline prose wrongly tagged `source`
passes (seen on a plant). Check 4 uses `$PY` which the block never sets (runs
as `-c …`, a silent no-op). Pass 1's label grep (Preis, Vertrieb, Anbieter)
would tag Impressum lines if followed literally. The import's small-type tag
was 13/14 OCR junk on SH8602, not "every one a source note" as measured on
8609. Found by the 250 sub-agent.

## 260 — check 1 FAILs on a correct program-name heading and has no way to be told

"A heading that IS code stays in caps — 8609's `POKE 1,0 ???` is the only hit
in the corpus" — SH8602's `UNNEW` (a program name) is another; the check only
exempts ROM keywords, so the correct tree reports FAIL, and r260 does not read
`adjudicated.txt` the way r310 does. "Applies to: all — the print sets
headings in caps in both kinds" is false for SH8602. "`14mal schneller
laden`, which check 2 flags" — check 2 now skips digit-initial headings. Found
by the 260 sub-agent.

## 280 — the Briefing still carries the rules the body reversed

Briefing step 1: "If the candidate would add or drop letters vs the
German-correct form, it's a print typo. Skip — do not even open the block
index" vs the section "THE CROP DECIDES … This rule used to say the opposite"
(SH8602 `spezieles` is OCR — the print has `spe-zielles`). "Explicitly NOT
touch … `<pre>`" vs "`<pre>` IS in this rule's scope". The "two-engine
cross-check" vs "The block index is a LOCATOR, not a second engine"; the
evidence section still asks for "grep output showing the other engine read the
corrected form", which cannot happen. Verification 1–2 still pipe into `head`.
"Normalise" model names vs r000 "CONSISTENCY WITH THE PAGE". Found by the 280A
sub-agent.

## 290 — still tells the agent to write the adjudication into the page

"Write the adjudication into the file, immediately above the heading, as an
HTML comment opening `So im Heft gedruckt:`" (with an example naming a step and
a checker) — contradicts r000 ("never a gate adjudication — those live in
`adjudicated.txt`") and r310's header. "An aside's heading sits ONE LEVEL BELOW
the article's highest section heading. So `<h2>` when the body has `<h2>`"
contradicts itself (the 290 agent's literal check flagged all 12 correct
asides); "Inside an `<aside>`? … stays [h2]" contradicts the h3 exception. The
Verification block still has no aside-outranks or paragraph-tail check (only
r310 has them). Found by the 290 sub-agent.

## 300 — the "disk has the bug, user not yet asked" state has no word

"Every aside carries a disposition comment" vs "stays unmarked until the
listing is either patched … or the decision is taken to leave it"; none of the
three vocabulary words fits "disk has the bug, decision pending". The same
illegible-digit case gets `Reiner Druckfehler` in the aside but `Disk-Version
bereits korrigiert` in the prg header (step 2 vs appendix step 8). Goal/step 4
"Patch the source listing" vs "Default to recording" and r000's "user first";
even the `;` header the rule demands is a prg edit r000 sends to the user.
"check the r330 verdicts" — r330 runs after r300. Stale inputs (fehlerteufelchen
PDFs, "PDF pages 4-7") when the later issues are imported and greppable.
Found by the 300 sub-agent.

## 320 — the dropped-listings companion crashes on lettered pages and is vacuous on MSE/BASIC issues

`r320_dropped_listings.py` `pages_of()` does `int(b)` on `131b` and dies.
Run on a letter-stripped copy it reports 0 — but it only examines SMON
monitor-dump blocks (`a 1234 xx`), of which SH8602 has none, so a planted
removal of every `<pre>` in the issue still reports 0. The rule should say
which listing formats it covers and that "0" on an issue without dumps is not
evidence.

## 310 — the intro-badge check has no adjudication path

`badge bled into the intro (r280)` matches any intro opening `\d{1,2}\s`
and calls `H()` directly, not via `ADJUDICATED_HERE`, so neither
adjudicated.txt nor a page note can clear a correct intro such as SH8602/159
"20 KByte adressierbarer Speicher …" — the same defect class as the old
printed-period check. Fix: route it through `ADJUDICATED_HERE(..., 'badge-intro')`
and/or skip a number followed by a unit. Not edited mid-build (r000); HARD
stays at 1, adjudicated.

## 330 — nothing says how a new issue gets its reprint leads

r330's trigger is `REPRINTS.md` leads, which SH8601 inherited from a deleted
PDF-OCR file. For a fresh issue no step produces them, and the rule's fallback
("no REPRINTS.md … ran, zero leads") would have recorded zero for an issue
that measurably reprints 8+ articles (Checksummer 0.92, MSE 0.96, Debugging
0.83, Ordnung 0.74 …). I built the leads by 8-word-shingle overlap of every
built article against all of `issues/` (~2 min) and wrote `REPRINTS.md`.
**What would have prevented it:** a "Step 0 — find the leads" in r330 with
that measurement, run after 280, before 325/330.

## 325 — the dump cross-checker is silent on three more dump forms

"Do not take its silence as coverage" names two unread forms; SH8602 has three
more it also skips without a word: SMON `>, C000 A9 C0 LDA #$C0`, the monitor
`.,  081A  A9 CC  LDA #$CC`, and assembler listings with line#/loc/code
columns (95 instruction rows in one half of this issue). It should print how
many rows it parsed so "0 parsed" differs from "0 wrong". The pdftotext
locator it recommends does not exist before 006. "Readers must … report as they
go" — a sub-agent has only its final hand-back. Found by both 325 readers.
