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
