# SH8604 — workflow errata

Kept from the first confusion onward (r340). Harvested at the end, not during.

## Status at finalization (2026-10-06, against rules HEAD 60ec49b9)

**FINAL.** 54 proposal entries, each with a **Suggested.** and a **Harvest:** line under its heading;
the `## 340` sections are records. Status checked entry by entry against the rules and the commits
since the build began (what landed is compared to what was proposed, and differences are named):

| status | count |
|---|---|
| HARVESTED | 15 |
| PARTLY | 9 |
| OUTSTANDING | 29 |
| SUPERSEDED | 1 |

- **⚠ One entry is a different severity:** *120 — PUBLISHED-FILE ERROR*. The Hobbit `.prg` a reader
  downloaded had `CLOSE` where the program has a shifted space. Fixed in eda01925; the rule that
  would have stopped it reaching the owner as a grouped "asymmetry" is outstanding.
- **Harvested differently from the Suggested:** cfd8528e superseded the `<br>` join for a merged
  article's Inhalt line; ac30971c folded the two petcat observations (space-only body, `$A0` after
  REM) into one rule about brace escapes outside a string; 11bfdf5d exempts photos by image mode
  rather than by name.
- **Seven post-sign-off changes** are recorded in the `## 340 — after sign-off` sections (the sixth
  is control's).
- HARVEST.md does not mention SH8604 yet.

## 005 — the paper pre-fill proposes a FALSE positive, not only misses

**Harvest:** PARTLY — 5f4557cc. The rule pre-fills from the UNION of witnesses; r005_masters_sheet.py still pre-fills from the edge finder alone.

**What the rule says.** r005_masters_sheet.md, *What the step offers as evidence*: the
edge-finder signal "is one-sided: it finds pages whose stock the paper mask is *blind*
to ... A good stock the mask happens to see will not show up". That warns of misses only.

**What happened.** Pre-fill was `[1, 60]`. p060 is an interior page printed under a
full-page tint (frac 0.080, own white 200 169 154 — the interior's). The tint, not the
stock, blinds the paper mask. Pasting the pre-fill back would grade an interior page with
the white-stock anchors. (Misses: 002, 163–168, as on SH8603 — that entry is in harvest.)

**Cost.** One montage, ~2 min.

**Suggested.** Say the edge-finder signal can also fire on a full-bleed tinted interior
page, and gate the pre-fill on the own-white measurement (a page whose own white sits at
the interior p50 is not high stock, whatever its paper fraction).

## 005 — r005_masters_sheet.md still names a per-program ISSUE knob and bare python3

**Harvest:** HARVESTED — 6d144ed9.

**What the rule says.** *Run*: "The only per-issue knob is `ISSUE = "SH8601"` at the top of
the program" and `python3 r005_masters_sheet.py`; *Inputs*: "on this box `/usr/bin/python3`
has all three".

**What is true.** The issue comes from `ISSUE.txt` / `$ISSUE` via `r000_issue.py`
(r000, *BEFORE ANYTHING ELSE*); CLAUDE.md says the repo venv. Ran with `.venv/bin/python`.
No cost — r000 was read first — but a reader of r005 alone would edit the program.

**Suggested.** r005_masters_sheet.md *Run*: "The issue comes from ISSUE.txt / $ISSUE (r000); run with `.venv/bin/python r005_masters_sheet.py`." — and drop the `ISSUE = "SH8601"` sentence.

## 005 — the parity gate is described as a FAILURE; the code only NOTES

**Harvest:** PARTLY — 6d144ed9. Rule says NOTED; the code comment at r005_masters_sheet.py:195 still says a confident disagreement "is a failure".

**What the rule says.** r005_masters_sheet.md, *The parity gate*: "only a **confident**
disagreement (`ratio >= TORN_CONFIDENT_RATIO`) fails the page"; the code comment at
`TORN_CONFIDENT_RATIO` says the same ("a CONFIDENT disagreement is a failure").

**What happened.** p101 (sample) read `torn right (5.68)` where parity says left. The
code appended a `NOTE` and published the page (r005_masters_sheet.py:1082). The overlay
is fine — four lines on the trim, 208.3 × 296.6 mm.

**What is true.** Either the code or the rule is wrong; the build follows the code.
Cost: ~5 min to find which behaviour applies.

**Suggested.** Make the rule say NOTE (the overlay and the size gate are the checks
that can say what is wrong), or make the code fail. Not both stories.

## 005 — the parity gate misfires on 93 of 160 interior pages (600 dpi frames)

**Harvest:** PARTLY — 1217a4d2. Rule explains the frame clipping the fringe; the code does not report "torn side not in frame".

**What the rule says.** *The parity gate*: "143 agree with parity, and they agree loudly:
the smallest ratio among them is 2.73"; a confident disagreement (`>= 2.5`) means
"misfiled or mis-rotated".

**What happened.** The sweep printed `TORN SIDE … misfiled or mis-rotated?` on **93**
pages: 75 odd pages read `right` (2.77–8.53), 18 even pages read `left` (2.58–4.05). None
is misfiled. On p041 (odd, recto), the 600 dpi frame cuts THROUGH the torn fringe at
x = 0, so the paper starts at column 0 in every row (no jitter), while the clean right
edge sits against the bed and carries the only measurable jitter. The ratio is measured
off SH8601's 2400 dpi frames, which show the whole fringe with bed beyond it.

**What is true.** The scan frame, not the paper, decides what this measurement sees.
Traced sizes are normal (odd 207.0–211.6 × 296.1–298.0, even 205.4–211.0 × 294.5–297.6),
and the overlays are correct. Cost: ~15 min (overlay + edge crops of 040/041).

**Suggested.** State that the gate needs the torn side to be IN frame. Where the frame
cuts at x = 0 / w−1 on a parity-predicted side, report "torn side not in frame" rather
than a disagreement.

## 005 — the rule's black-point curve and its Verification 6 describe code that no longer exists

**Harvest:** PARTLY — 1217a4d2. The `-level 30%` curve sections, the output table's "with the black-point curve" and Verification 6 remain; check 4's comment still says sheets600.

**What the rule says.** *One separation, two renders* and *The curve is one issue-wide
constant*: masters600 carries `-level 30%,100%`; Verification 6 compares the curve
between the "figure" render and the master. The harvest (5f4557cc) removed figures600 and
says "`sheets600` and `masters600` … both carry the curve".

**What is true.** The code removed the curve (commit 7b9aa90b, comment at
r005_masters_sheet.py:467 "there is no OCR contrast curve, and that is deliberate"; GCR
is undone at the source instead). Every stamp says `render ONE master, uncurved`. So
Verification 6 measures nothing, and the harvest's explanation of SH8603's equal glyph
p50 (both curved) is wrong: both are UNcurved.

**Also Verification 4.** It now slices `sheets600[:ph, :pw]`, but `sheets600` is the
UNCROPPED sheet; the page sits at the stamp's `sheet-box` offset (p041: 40 5), so the
band check reads a frame shifted by that offset. Since masters600 is uncurved, I read the
bands off `masters600[:ph, :pw]` instead.

**Cost.** ~10 min. **Suggested.** Delete the curve sections and Verification 6 (or turn
it into "glyph p50 on masters600"), and point check 4 at masters600.

## 005b — "the Zahlkarte measures ~144 x 208 across every Sonderheft" is not true of SH8604

**Harvest:** HARVESTED — 1a7157cb.

**What the rule says.** r005_a4_window.md, *A PAGE WHOSE TRACE FAILS*: "The Zahlkarte
measures ~144 x 208 mm across every Sonderheft that has one … A member that disagrees
with that by more than a few mm has failed, whatever its trace says."

**What happened.** SH8604's card traced 149.2–149.9 × 206.5–206.9 on all four sides,
6 mm wider. Read literally, the rule says all four failed. They did not: this card
carries a printed flap ("Wußten Sie schon …", continued on the back), and the 2.5 mm edge
bands are clean.

**Suggested.** Say "the card's size is this issue's, measured from its own good traces";
use the cross-issue figure only to flag a member that disagrees with its own run.
Cost: ~5 min (montage).

## 005b — fallback 3 for a failed page is a rule, not code

**Harvest:** OUTSTANDING. 1a7157cb renamed the recoveries A–C and records them as not in the code.

**What the rule says.** "A PAGE WHOSE TRACE FAILS IS STILL CUT AUTOMATICALLY", fallbacks
1–3. The program runs fallbacks only for pages step 005 traced; for p163 (uncropped) it
chose `traced-edge` off the whole frame and left ~4 mm of bed at the foot, reporting
alpha 4.02 % and **fabricated 0.00 %**, so nothing in its summary flags it.

**What I did.** Derived the foot edge from luminance profiles (fallback 3) in a scratch
script, as SH8603 did for 107. Cost: ~15 min. "Automatic" currently means "each build
re-derives it by hand-written script".

**Suggested.** Implement fallbacks 1–3 in r005_a4_window.py for pages whose 005 stamp
says `uncropped`, and print them in the summary.

## 040 — BLOCKER: the new leading-# escape (5f4557cc) escapes every ##/### sub-heading

**Harvest:** HARVESTED — 0b862013. A `(?![#\s])` lookahead, plus per-level heading counts in Verification.

**What the rule says.** r040_escape_asterisks.md says nothing about `#` (Rule and
Verification cover `*` only). The script (5f4557cc, `esc_hash`) says: "030's own headings
are '# Title [pages]'; anything else leading with # is body text and is escaped."

**What happened.** 030 also emits `## Sub` and `### Sub` (r030's department/column shapes;
SH8604's .md has 69). The regex `^(\s*)(#+)(?!\s*\S.*\[\d)` exempts only lines carrying
`[digit`, so all 69 became `\##`/`\###` (e.g. l.57 `\## Viel Speicher für Adventures`,
l.1371 `\### Regel 1`) and would ship as literal text. The fault it was written for
(`#1281/…`) occurs 0 times here. r040's Verification printed all zeros: it has no `#` check.

**Found by** the 040 sub-agent, confirmed by the orchestrator (`grep -c '^\\#'` = 69 =
`grep -c '^##'` in the 030 output). Cost so far ~10 min; build stopped at 040 pending fix.

**Suggested.** Exempt `#{2,}` followed by whitespace (sub-agent's candidate:
`^(\s*)(#+)(?!#)(?!\s*\S.*\[\d)(?!(?<=##)\s)`, tested on `#1281…`, `##nospace`,
indented `#foo`), and add a Verification line: lines starting `\#` must each be a body
line, and `^#{2,3} ` count must be unchanged across 040.

## 050 — the script does not escape `</` + non-letter, which the rule requires

**Harvest:** HARVESTED — 53b89c0d.

The rule: "EXCEPT `</` followed by a non-letter (`</>`, `</1>`) … Escape those too." The
script's regex needs a letter after `</`; the sub-agent's scratch test left
`durch </> dargestellt und </1> hier` unchanged, and the Verification regex cannot see it
either. 0 cases in SH8604 — no effect here.

**Suggested.** r050_escape_tags.sh: also escape `</` followed by a non-letter (`</>`, `</1>`), and add that case to the Verification regex.

## 070 — the en-dash rule has no code

**Harvest:** HARVESTED — 2d9500ed, ab79a492. The headline `—`/`-` point is covered only by "read the `<h1>` lines".

**What the rule says.** r070, *A SPACED DASH IN BODY TEXT IS AN EN DASH*: "` - ` becomes
` – `" at this step, before 080, because the h1 decides the filename.

**What happened.** `r070_html_cleanup.sh` has no dash code at all; the sub-agent found
that the script left all 326 spaced hyphens and did the pass in Python by hand (283
converted, 43 kept by the rule's exceptions). The rule has no Verification line for it,
so a run of the script alone passes. Cost ~10 min, and a judgement pass per build.

**Also.** The OCR reads the same printed headline dash as `—` on some headings and `-` on
others (SH8604: Inka, The Sword as `—`; MSE, Odyssey, Asterix, Spion III as `-`; one glyph
on the page). A pass that converts only ` - ` leaves the headlines inconsistent with each
other and with the page.

**Suggested.** (Done in 2d9500ed.) r070 Verification: "` – ` count > 0, and every kept ` - ` is printed for review."

## 060 — the script deletes the .md, so 040–060 cannot be re-run from it

**Harvest:** HARVESTED — 53b89c0d. Differently: the script saves `<tmp>/ocr/<ID>.pre060.md` and the checks read that.

The rule says 060 `git rm`s the .md. The .md is git-ignored and untracked, so the script
just `rm`s it; only the sub-agent's scratch copy kept the post-050 state. Re-running needs
040 and 050 again from `<tmp>/ocr/<ID>.md`. Worth one line in r060.

**Suggested.** r060: "The script removes the untracked .md; to re-run 040–060, start again from `<tmp>/ocr/<ID>.md` (030's handover)." (53b89c0d now saves `pre060.md`.)

## 080 — the byline matcher takes any `<p>(…)</p>`; listing-only pages are unstated

**Harvest:** PARTLY — ab79a492. Item 1 with a different guard (no `=`/`;`/digit/lone ALL-CAPS token); items 2–4 (listing-only pages and ad spreads, tail-plus-start pages, the pages separator) not in r080.

1. **`<p>(RETURN)</p>` became a byline.** Dateiverwaltung prints `(RETURN)` on its own line
   after direct-mode POKEs; the splitter made it `<address class="author">` and wrote
   `author = "M. Nickles, bs, RETURN"` — which then made the paired-article check report 3
   bylines. The rule's Notes say only that bylines "must look like `<p>(Author Name)</p>`".
   Suggested guard: a `/xx` editor suffix or a lowercase letter. Cost ~5 min (sub-agent).
2. **Listing-only pages.** r080 never says that pages carrying only an article's listing
   belong in its `64er.pages`, nor that an ad spread inside the run (Odyssey 98-99) stays
   out. The SH8603 precedent lived only in my brief; 030 omits those pages by design, so
   every build has to rediscover this.
3. **A page with one article's tail and the next one's start** (49, 126, 133, 161 here)
   is not the lettered case; the rule could say so in one line.
4. **`64er.pages` separator** is unspecified; the corpus is mixed (`a,b` vs `a, b`).

**Suggested.** r080: "A byline is `<p>(…)</p>` whose content carries a `/xx` editor suffix or a
personal name — never a key name such as `(RETURN)`; pages carrying only an article's listing belong
in its `64er.pages`, an ad spread inside the run does not; a page holding one article's tail and the
next one's start is not the lettered case; `64er.pages` is written `a-b,c` without spaces."

## 070 — the new flank-test dash pass (2d9500ed) against SH8604's hand pass: 7 differences, hand right on all 7

**Harvest:** HARVESTED — ab79a492. Range and ALL-CAPS shapes added; skipping `<p class="source">` was explicitly rejected.

Ran the new `r070_html_cleanup.sh` on a scratch copy of SH8604's post-060 HTML and compared
with the hand pass that shipped. Identical except 7 sites the script widens and the hand
pass kept as hyphens:
- `Satz 1 - Satz 3`, `Satz 3 - Satz 3` (record ranges — operand is a WORD + number, so the
  flank test sees "Satz" on the left and calls it prose);
- `Raum O - MZ 1` (range of array indices);
- `»We were discussing you - not me«`, `»WE WERE DISCUSSING YOU - NOT ME«` (Eliza's printed
  program output — PETSCII has one hyphen);
- `INDEX-MAKER - ERSTELLT` (REM text of an un-fenced OCR listing);
- `ON - GOTO` (BASIC keyword pair).
**Suggested.** r070's flank test: treat "Word N - Word M" as a range (keep the hyphen); skip text
inside »…« that is all caps or quoted program output; skip `<p class="source">` and listing-like
paragraphs.

## 090 — what the TOC rule did not say (sub-agent)

**Harvest:** OUTSTANDING.

1. Entry text: bold title vs blurb, and qualifiers like "(nur auf Diskette)" and the
   "Kurs:" prefix — the rule says only "the printed entry text".
2. Glyphs: dash, apostrophe and ellipsis normalisation in toc_entries.txt are unspecified
   (chose `–`, `'`, `...` to match the filenames).
3. A Sonderheft TOC with NO Rubriken box while the issue has an Impressum (and here an
   unlisted Einleitung): neither r090 nor r100 covers it.
4. A printed TOC page number that is wrong (MSE 95, article on 94): no instruction to flag.
5. The disk icon on entries (Programm-Service marker) is OCR'd as "EI/Ei/BE/Bi".
6. The Procedure's page loop assumes 6–7 or 4–5; here it is p5 only.

**Suggested.** r090 step 6: "`entry` is the bold title as printed, without blurb or a qualifier like '(nur auf Diskette)'; dashes/apostrophes as in the article filenames; record a printed page number as printed and flag a misprint in LOG.md."

## 100 — script does not parse under /bin/bash 3.2; checks and helper disagree with the rule (sub-agent)

**Harvest:** HARVESTED — f5d861a4. Heredoc body via mktemp, shebang kept; items 4–5 (no printed entry, qualifiers) not addressed.

1. `r100_toc_category.sh` (`#!/bin/bash`, 3.2 on macOS) dies: "line 87: unexpected EOF while
   looking for matching '"'" — backticks in a Python comment (4dffec82, `` `git add -u <dir>` ``)
   inside `"$(cat <<'PY' …)"`. `bash -n` fails too. Ran under /opt/homebrew/bin/bash.
   Fix: `#!/usr/bin/env bash` or drop the backticks. (r000: "bash -n is not a test" — here
   even bash -n would have caught it.)
2. "exactly one toc_category line" counts the commented placeholder, so an unfilled file passes.
3. `r100_toc_title_apply.py --apply` would write toc_title == <title> on 13 files (the rule
   says delete) and leave XXX on the 2 unlisted ones; the rule never mentions the helper.
4. No toc_title case for an article with no printed entry (deleted the placeholder).
5. Non-title qualifiers in a TOC line ("(nur auf Diskette)") and dash normalisation in the
   "same as title" comparison are unspecified.

**Suggested.** r100_toc_category.sh: `#!/usr/bin/env bash` and no backticks in heredoc comments; the 'exactly one toc_category' check strips comments first; the rule names r100_toc_title_apply.py and says not to use `--apply` until it deletes title-equal toc_titles.

## 120 — disk errors are invisible; checks 2–4 do not fit a multi-disk Sonderheft (sub-agent)

**Harvest:** PARTLY — 2282dcef. Error-block mapping done (r120_d64_errors.py); check 2 still eyeball with the `----+` regex; item 4 later by 6f29cdce, eda01925, ac30971c.

1. The extractor cannot report a read error: `prg_links.sh` sends c1541 to /dev/null, and c1541
   is silent anyway. The only detector is the 683-byte error block mapped onto file chains
   (done by hand for SH04C: bad sectors are free, no file affected).
2. Check 3 is vacuous here: every SH04 disk opens with a bare "----------------" separator,
   which counts as a section, so an unnumbered intro file passes as "placed".
3. Check 2 is eyeball-only and its `--+` regex misses single-dash text separators
   (`-dateiverwaltung`); no word on one section spanning two articles (40 → KI and Eliza).
4. Check 4's three mismatch cases do not name petcat's round-trip asymmetries (single-space
   line body; $A0 in REM decoded as `close`) — SH8603's `{blu}` was the same class.
5. The `.txt` branch emits `${filename}` not the sanitised name: `data-filename="1985/1986"`
   for `1985_1986.txt`.
6. PRG-typed DATA files (101 on disk C) all get an MSE figure proposal.

**Suggested.** r120: "For a D64 with an error block (size 175531), map its bad sectors onto file chains (c1541 reports nothing) and record the result in LOG.md." Check 2 should match single-dash separators and be mechanical.

## 130 — what the placement rule did not cover (sub-agent B, disks B–D)

**Harvest:** PARTLY — d2752aa3. Check 6 done; missing: "nur auf Diskette" data files are a hidden `binary_download`, never an MSE `<pre>`.

1. Check 6's 3-word minimum false-fires on verbatim short captions; the note "Every print
   `Listing N.` caption has a trailing description" is false (SH8604 p143 "Listing 2. »B«",
   "Listing 3. »The Sword«").
2. A caption repeated on every listing page ("Listing. »Odyssey« (Fortsetzung auf Seite 97)"
   … "(Schluß)"): which to take, and whether to keep a print typo like "Listing." — unstated.
3. A disk-only program with 101 data files: no guidance on data-name or on which file the
   reader loads; the prg.txt template wraps every raw file in an MSE `<pre>`.
4. `data-checksummer`: not mentioned in r130 at all; SH8602 uses it (9×), 8611/8612 never.
5. The evidence requirement assumes a "Listing N" mention; 6 of 11 articles never say
   "Listing", and four have no separate byline to place after.

**Suggested.** r130: "A data file of a 'nur auf Diskette' program (room files, texts, charsets) is a hidden `binary_download` named by its C64 filename, never an MSE `<pre>`"; check 6 allows a verbatim short caption recorded in reviewed/.

## 130 — check 4 contradicts the inline/end ruling; first-mention vs print adjacency (sub-agent A1)

**Harvest:** OUTSTANDING.

1. Check 4 ("Listing-N captions in print order") fails on any shape-3 article that puts a
   long listing at the end after a higher-numbered inline one: "Listing 16 after 26" in
   Dateiverwaltung, by construction of the 2026-10-04 ruling. Exempt the after-byline block.
2. 14b is first mentioned after 15's anchor, but printed directly under 14: first-mention
   placement would put it after 15. Followed the print.
3. One listing, two unrelated captions on two pages (Listing 16, p20/p21): unstated.
4. A binary range mismatch (MSE file 2 bytes longer than the printed span) cannot be
   expressed by data-range and has no stated home.
5. data-name for course listings with no name in the body: unstated (used caption short forms).

**Suggested.** r130 check 4: "Compare print order only among inline listings, and separately within the end block after the byline."

## (owner rule mid-build) the uncut pages and the cover source are handed over when they exist

**Harvest:** HARVESTED — cccaefe9, 4408be0e. Leftover: r000's hand-over table (line 226) still calls the cover crop "a reduction of `masters600/001.png`".

Arrived via control 2026-10-05 after step 130 was under way (r000 *An OWNER DELIVERABLE is
handed over the MOMENT it exists*, cccaefe9): `sheets600/` and a 150 dpi cover crop are
`open`ed for the owner as soon as 005 finishes, without stopping. On SH8604 both had existed
since ~3 h earlier and nothing in the rules I had read said to hand them over before PAUSE 2.
Done at 130: `title_source_150.png` cut from masters600/001 to the stamp's page box.

**Suggested.** (Done in cccaefe9.) r005: "When 005 (and on a sheet issue 005b) finishes, open sheets600/ and the cover source for the owner, then continue."

## 006 — the cover source: r000/r005 named the wrong source directory for a sheet binding

**Harvest:** HARVESTED — 18a0358d → 4408be0e. Same leftover at r000 line 226.

r000 *the issue must BUILD* said: crop masters600/001.png to the traced page box in its stamp,
resize to 1240 x 1754 "(what every other issue uses)". I followed it. The PDF actually reads
the directory 006 passes it — `<tmp>/a4600` for `binding: sheet` (005b's A4 cut, 4961 x 7016),
`masters600` for `spread` — and title.png must equal page 1 of THAT directory at 25 %. My
page-box crop happened to land on 1240 x 1754, but framed tighter than every other PDF page and
squeezed 0.8 % to get there.

Then control sent me the wrong way: it read the gate as masters600 at 25 % (1364 x 1795) and I
regenerated to that, checking the script's arithmetic but not which directory `$IN` is. It
would have been refused. Control caught it within the hour (4408be0e supersedes 18a0358d), and
the cover is now a4600/001.png at 25 %, exactly 1240 x 1754. Cost: two regenerations and two
re-`open`s; the owner had a wrong file open twice.

The framing for the rule: **the cover comes from whatever directory the PDF reads**, and its
size is a consequence of that, never a constant. On a sheet issue the cover waits for 005b.

**Suggested.** (Done in 4408be0e.) r000: "title.png = page 1 of the directory 006 passes the PDF builder (a4600 for sheet, masters600 for spread) reduced 25 %; its size is a consequence, never a constant."

## 130 — more from the course placements (sub-agent A2)

**Harvest:** OUTSTANDING. Item 5 (padded MSE) settled separately by caf83e4b.

1. Putting a long EARLY listing at the end forces every later one to the end too, or check 4
   fails (81: Listing 1 is the 372-line Gerüst). Say that print order wins and the shape
   choice applies from the first end-placed listing onward.
2. Listings never named in the body (81 L3), or named only in text the OCR lost (58 L9/L10).
3. Check 5 cannot run mid-chain: the build dies on the missing title.png. A scratch copy with
   a stand-in title.png works.
4. Check 7 misses a renumbering that leaves the set gap-free ({1,2,3} with a duplicate 2);
   it needs a duplicate test.
5. MSE dumps printed with the last row padded past the end address (fenster, Freiheit) —
   a recurring print/disk class with no rule text.

**Suggested.** r130 (owner ruling): "Print order wins: from the first listing placed at the end, every later-numbered listing goes there too." Check 7: also flag duplicate numbers.

## 140 — reprints.txt handoff is one-sided; check 4 and multi-article courses (sub-agent)

**Harvest:** OUTSTANDING. Check 4 says "SAME series" (2282dcef), not the same machine.

1. r140 says r330 reads `reprints.txt`; r330's Step 0 never mentions it and writes REPRINTS.md
   from its own pass.
2. Check 4 compares against SH8603 (C 16/VC 20), which has no `mse`, so a missing MSE here would
   pass. "Previous issue of the same series" needs the same machine/theme.
3. A course split over 7 articles that continues a one-article course (`kurs`, SH8502/7) has
   one slug to give; "keep the series slug stable" assumes one article per part.
4. The verification snippet uses `<YYMM>`/`<ID>`/`<PREV-SAME-SERIES>` and never sets ISSUE/PREV.

**Suggested.** r330 Step 0: "Read `reprints.txt` first if it exists; REPRINTS.md extends it." r140 check 4: "Compare against the previous Sonderheft for the SAME machine."

## 160 — mixed Bild series, interleaved figure OCR, in-box labels, hanging-indent docs (sub-agent A)

**Harvest:** OUTSTANDING.

1. A numbered Bild series where some members are grids and some carry arrows (Bild 6a–6j):
   r160 typesets the grids and r150 crops the drawings, so the page ends up half each. No
   rule on keeping a series consistent.
2. The OCR wove a typeset Bild (6h) and two drawings (6g, 6i) into the same paragraphs; "leave
   the drawing's garbage" then leaves duplicate text of the typeset one. Orchestrator removed it.
3. A print pointer inside a caption ("Die Erklärung finden Sie auf Seite 34.") — the pointer
   rule covers standalone pointers only.
4. A label printed inside the figure box apart from its caption ("Die komplett sortierte
   Datei.") and an intro line printed in the box above a series: no rule.
5. The "line range / description" documentation shape (6× in this article) is covered only
   by the generic "text printed as a table" section; corpus precedent is `table.plain`.

**Suggested.** r160: "A numbered Bild series is all typeset or all cropped; where some members carry arrows, list the whole series on the crop worklist and typeset none."

## 160 — course-issue shapes the rule does not name (sub-agent B)

**Harvest:** OUTSTANDING. Item 7 (reviewed/ git-ignored) fixed by 5a3edb23, not as suggested.

1. Line-number documentation ("10-30 Hier wird …") is the dominant table shape in a course
   issue; the OCR systematically drops or misplaces its labels, which must be re-read from
   the crop. r160 never names the shape.
2. Small boxes captioned only "Tabelle N" that are really drawings (KI Tabelle 1–6, arrows and
   circled numbers): table or crop? unstated.
3. A printed table never referenced in the prose goes to the article tail, away from its
   neighbours on the page (KI Tabelle 3).
4. Long unlabelled typewriter-face data boxes (176-record Texte-Datei; the "A AB ADRESSE"
   printout) — neither table nor Bild; used `<pre>`.
5. Check 5's regex treats "Tabelle I" (I AM, a keyword) as a table number.
6. The tint pre-filter's "55–60 % band" lost a column on p60; 50 % worked.
7. **`issues/<ID>/reviewed/` is git-ignored** (`.gitignore: issues/*/*`), so the r000_reviewed
   delta records written by checks 5/7 do not survive the build — the next run re-reports
   them as NEW. Either track `reviewed/` or move it.

**Suggested.** r160: "Line-number documentation ('10-30 Hier wird …') is `table.plain`, two columns; re-read every label from the crop — the OCR drops them."

## 170 — load address, reusing an earlier issue's proven file, trailing bytes (sub-agent)

**Harvest:** OUTSTANDING.

1. r170's table says `petcat -l <addr>` but not to read the address from the article's own
   POKEs ("POKE 43,1: POKE 44,32 …" → $2001). My brief said 0801; the sub-agent was right.
2. No method for "this print is the same program as another issue's proven file": tokenise the
   precedent, check every printed sum, compare spacing by eye (sums ignore spaces).
3. "DATA bytes equal the known binary" should say the disk binary may carry bytes past the
   loader's end pointer.
4. A listing over two pages with a second "(Schluß)" caption carrying an instruction sentence.

**Suggested.** r170 table: "`-l <addr>` is the address the ARTICLE's own POKEs set (e.g. POKE 44,32 → $2001), not $0801 by default."

## 160 — the sub-agent reported writing reviewed/ records that did not exist

**Harvest:** OUTSTANDING.

Sub-agent B (160) reported "recorded both items with `R.record`, which wrote
`issues/SH8604/reviewed/r160-table-refs.txt` and `r160-box-captions.txt`", and a re-run
showing "all previously reviewed". When control fixed the gitignore and I went to commit
them, neither file existed anywhere (repo, `<tmp>`). Re-recorded by the orchestrator with
reasons. Lesson for the briefing: a file a sub-agent claims to have written is checked with
`ls` before its report is accepted.

**Suggested.** r000 briefing template: "A file the sub-agent says it wrote is `ls`'d by the orchestrator before the report is accepted."

## 180 — unsigned course chapters, a co-signed Vorwort (sub-agent)

**Harvest:** OUTSTANDING.

1. A normal article with no printed byline (KI, Super-Grafik — chapters of a course): r180's
   Case B lists unsigned RUBRICS only; Case D allows "a real name or remove". Removed (SH8505/3,
   SH8506/3, SH8507/6 precedent); check 3 flags them every run.
2. The Vorwort is co-signed "(Georg Klinge/Boris Schneider)"; r180 names Georg Klinge alone.
3. The vocabulary snippet's `<address class="author">([a-z]*)</address>` only captures
   initials-only bylines; on a Sonderheft almost all are "Name/xx".
4. "Beautify touched files" gives no command; `git diff --name-only` quotes non-ASCII names
   (–, ü) and js-beautify rejects them — use `-z`.

**Suggested.** r180 Case B: "…and any article whose page carries no byline at all — read the last page, then remove the meta." A Vorwort co-signer is kept in print order.

## 300 — "record the candidate and leave it" read as "ask the owner"

**Harvest:** HARVESTED — 69d05cb3.

I carried the Vorwort's "Sonderheft 2/85" / "2/86" to control as a Futureteufelchen candidate
for PAUSE 2. r300 already said an internal inconsistency is a typo and gets no aside; I read
"record the candidate" as "raise it". Control has added the owner's framing ("who is helped?")
and that recording means a LOG.md line, not a question (69d05cb3). Cost: one owner-list item.

**Suggested.** (Done in 69d05cb3.) r300: "Recording a candidate means a LOG.md line; only a candidate that passes 'who is helped?' reaches the owner."

## 190 — check 3b runs on the repo root; Impressum precedent statement (sub-agent D)

**Harvest:** OUTSTANDING. 3b still defaults to `.`.

1. Verification 3b is invoked `$PY - <<'NEVERSPLIT'` with no argument, so it reads `sys.argv[1]`
   default "." — the repo root — and passes whatever the issue holds. Pass "$dir".
2. r190 says the Sonderhefte bold the Impressum labels; SH8602 and SH8603 (the latest) use
   `<em>`. 7 of 9 that mark them use `<strong>`.
3. No rule for text the magazine itself printed twice (126); r300's "who is helped" settled it.

**Suggested.** r190 Verification 3b: `$PY - "$dir" <<'NEVERSPLIT'`. r190 precedent section: "Impressum labels: `<strong>` (7 of 9 Sonderhefte)."

## 190 — numbered label + indented description; dash list with a connective line (sub-agent C)

**Harvest:** OUTSTANDING.

1. A numbered label line followed by an indented description (81 p92) — used `<ol>` items
   holding two `<p>`s; no rule.
2. A dash list with a connective "und" line between its items (58) — the `<p>— …</p>`
   precedent does not cover it.
3. My brief misattributed a 060 `<ol>` note (handover lines 2234–2236) to 81; it was 78's.

**Suggested.** r190: "A numbered label line with an indented description is an `<ol>` item holding both; a connective line inside a dash list ('und') stays a `<br>` line."

## 190 — my brief said "match the page" for machine names; a whole printed block was never imported (sub-agent B)

**Harvest:** OUTSTANDING.

1. My shared 190 brief told the agents to space machine names "only where the PAGE spaces them".
   That was r000's OLD guidance; the owner ruled 2026-10-04 "always spaced" and r000 carries it
   as the one exception. Agent B followed the owner rule regardless; A, C, D followed my brief.
   Fixed by an issue-wide pass afterwards (see LOG).
2. The printed Eliza dialog on p49 (62 monospace lines) survived 010–180 missing: no gate
   compares a page's monospace blocks with the HTML. r320's omission check comes at the end.
3. The dup sweep (W=12) cannot see a 10-word OCR duplication whose first word is garbled.
4. In-flow monospace lines that break a sentence (`<p>`/`<pre>`/`<p>`) vs proportional display
   lines (`<br>`): r190 does not say which.
5. r190's dash-list form is `<p>— …</p>` (em dash), but 070 turns printed hyphen-dashes into en
   dashes; this issue's agents used `<p>– `. Name the glyph.

**Suggested.** r000 briefing template: "Machine names: always spaced in prose (owner 2026-10-04) — never 'match the page'." r320: compare each page's monospace blocks against the HTML before 190.

## 190 — bold line labels in documentation blocks; a sentence split by a code line (sub-agent A)

**Harvest:** OUTSTANDING.

1. Bold run-in line labels in a documentation block (Listing 15, 9010/9020): `<p><strong>NNNN</strong>`
   vs `table.plain` (one item runs on into code, which a table cannot hold) — unstated.
2. A sentence split by a display code line leaves `<p>…</p><pre>…</pre><p>einzugeben.</p>`.
3. (Confirms D) Verification 3b reads "." — pass "$dir".

**Suggested.** r190: "Bold run-in line labels in a documentation block are `<p><strong>NNNN</strong> …</p>` when an entry carries code; otherwise `table.plain`."

## 210 — caps bands, check 3 only lists, Nachschau, unlettered shared pages (sub-agent)

**Harvest:** OUTSTANDING.

1. No rule for an all-caps band's capitalisation (every SH8604 band is caps; SH8603 precedent
   title-cases); compounds and plurals unstated.
2. Check 3 prints head2 values for the eye; a closed `C64` passes unless read. Make it fail.
3. Check 1's front-matter list keys on id, so a second front-matter piece (6, id `kurs`) is
   invisible to it.
4. Exclusions list Vorschau but not a Sonderheft "Nachschau".
5. Shared start pages that are NOT lettered (126, 133) are not covered; "the band describes the
   page" applies.

**Suggested.** r210: "Write a caps band in normal German capitalisation; check 3 FAILS on a closed machine name; a Nachschau carrying a band gets head1."

## 220 — a CSV row keyed to the wrong issue is routed silently and passes every check (sub-agent)

**Harvest:** OUTSTANDING.

1. "Sprite+Grafik-Basic, 4/86, 42" belongs to SH8504 (4/85). The apply script's nearest-start
   fallback put it into 40 KI and printed OK; the routing check (0 of 17) and the count (17 =
   17) both confirmed it. Only removing it by hand made the count disagree. Proposed: print
   FALLBACK for every row with no file starting on its page, and require the row title to
   appear in the receiving article (title/toc_title/heading), else search `issues/*/` for it.
2. The routing check misses a row moved FORWARD into a later article (planted, silent).
3. r220's text says `parse_sonderheft_csv` keys column 4 (it is column 3); the paragraph still
   ends "write one as part of this step"; the invocation snippet uses bare python3 from the repo
   root with a monthly CSV path; cell whitespace trimming is unstated.

**Suggested.** r220: "Print FALLBACK for every row routed with no file starting on its page, and require the row title in the receiving article; otherwise search issues/*/ and report a foreign row."

## 250 — the verification never fails; check 1 cannot see `<p><strong>Label:</strong>` (sub-agent)

**Harvest:** OUTSTANDING.

1. Exits 0 with findings (planted faults print WARN only).
2. Check 1's `<p>(Info|…):` misses `<p><strong>Preis:</strong>` and multi-word labels
   ("Vertrieb Handelsauflage:") — the only shapes this issue has.
3. Check 3 bare python3; `<YYMM>` placeholder not read from ISSUE.
4. No sentence for "this issue has no source notes" — a valid no-op on a Sonderheft without
   vendor footers; inline series markers "(SH2/85)" and the Impressum are not in the
   do-not-qualify list.

**Suggested.** r250 Verification: exit 1 on any finding; check 1 matches `<p>(<strong>)?Label[^:<]{0,30}:`; "An issue with no source notes is a valid no-op."

## 280 — the Verification block cannot see a lowercase jam (sub-agent A)

**Harvest:** OUTSTANDING.

A planted `bestehtaus` passes all three Verification greps; only `r280_word_jams.py` (Pass 3)
finds it. Make it part of the Verification. Also: the `sed -n '1,12p;$p'` sample prints the
12th entry twice when there are 13; the evidence command assumes line-split labels.json text.

**Suggested.** r280 Verification: run `r280_word_jams.py` over the issue and report its count.

## 280/190 — the dash-list glyph: my 190 agents wrote en dashes, precedent is em

**Harvest:** OUTSTANDING.

r190's "Three conflicts" says dash lists stay `<p>— …</p>`; 070 had turned the printed list
hyphens into en dashes, three 190 agents kept `<p>– `, one wrote `<p>— `, and a 280 agent then
"harmonised" the odd one out to en. Measured precedent: em 86, en 0 across SH8602/03, 8611/12.
Standardised to em by the orchestrator. The rule should say "em dash, whatever 070 produced".
Also (sub-agent D): r280's Verification has no punctuation check (guillemet balance, dash
convention), and nothing on thousands separators ("10 000" thin gaps; corpus writes closed).

**Suggested.** r190 *Three conflicts*: "Dash lists are `<p>— …</p>` with an EM dash, whatever 070 produced from the printed hyphen."

## 280 — line-end dashes are lost systematically at 010 (sub-agent B)

**Harvest:** HARVESTED — d90c2484. R280 only, as suggested; r010 unchanged.

r010 joins a line-final " –" like a soft hyphen (" ¬"), so the dash disappears ("bringt warum").
Grepping labels.json for `\S+ ¬` found 8 sites on pp. 6–54 that no prose sweep saw. Add it to
r280 Pass 2 (and fix it at 010). Also: hyphen-minus vs en dash glyph fixes are unaddressed.

**Suggested.** (Done in d90c2484.) r280: "Before Pass 1, grep labels.json for `\w+ ¬\s*\w+` — a space before ¬ is a lost dash, not a soft hyphen."

## 150/280 — naming gaps; a wrong fact in my brief (sub-agents)

**Harvest:** OUTSTANDING.

1. r150 has no name for an uncaptioned boxed table (proposed `-ta`), an uncaptioned non-lead
   portrait (proposed `6-1`), nor for a Bild 160 already typeset (listed "typeset"). SH8603's
   worklist header says an unnumbered "Tabelle." takes `-t1`, r150 says `-t0` — a copied header
   carries the wrong name.
2. My 150 brief said p60 sits "under a full-page salmon tint"; the master shows a grey halftone
   behind the table box only. A fact in a brief must come from the page, not my memory of a thumb.
3. (280 C) r280 does not say how to treat a printed digit-zero variable (`01`/`02` vs `O1`/`O2`,
   both printed in one article), nor that `$` printed as `S` is often the PRINT, not OCR.

**Suggested.** r150: "An uncaptioned boxed table is `-tA`, `-tB`…; an uncaptioned non-lead picture `-pN`; a Bild 160 typeset is listed 'typeset' (owner-crop-wins)."

## 290 — check 2 accepts an aside BELOW the body level; heading vs colon label (sub-agent)

**Harvest:** OUTSTANDING. Check 2 still accepts at-or-below.

1. The aside bullet says AT the body's top level; check 2 accepts "at or below", so 94's h3 aside
   under h2 body passed. Flag `lvl > top` when `top == 2`.
2. A standalone bold heading vs a bold colon label introducing a table ("Dokumentation:") are the
   same face in print; no rule separates them.
3. Locating a run-in head on the page: the block index cannot; 190 could record page+bbox for each
   heading it splits out.

**Suggested.** r290 check 2: flag an aside heading BELOW the body's top level when the body has h2.

## 300 — no disposition word for "owner has not ruled yet"; testing an unreached line (sub-agent)

**Harvest:** OUTSTANDING.

1. "Every aside carries a disposition comment" has no word for a pending decision; only xref 7.0
   ("stays unmarked") covers it.
2. r000's autostart test cannot reach a line like 115; a direct-mode recipe (load, set the
   variables, `goto<line>`) did. Add it to r000.
3. Scratch-test traps: `c1541 -write` into a copied D64 fails silently (the D64s are mode r-x —
   `chmod u+w` the copy and read it back); true-drive LOAD of a 100-block file exceeds 60M cycles.

**Suggested.** r300: add the disposition `<!-- Korrektur offen: Entscheidung des Herausgebers -->` (or 'stays unmarked' stated as the rule) for a pending prg decision; r000: document the direct-mode test recipe for an unreached line.

## 140 — I carried step-140 slug choices to the owner list twice

**Harvest:** OUTSTANDING.

Control had already said the shared slug is not a defect; I re-listed `kurs`/`kleiner-hobbit`
as owner items. A judgement the rule assigns to a step is that step's to make. Cost: two list
corrections by control.

**Suggested.** r140: "Slug choices are this step's; 64er.id is unique within an issue only — never an owner question."

## 330 — vocabulary gaps for moved blocks and markup artefacts; check 3 is line-based (sub-agent)

**Harvest:** OUTSTANDING.

1. When the two HTMLs place the same table at different points, the aligner leaves the prose
   between unpaired on both sides ("BLOCK ONLY IN", 8 of 93's 14) — the words are identical,
   so neither PRINT nor OURS/THEIRS fits; nor does text the other side wraps in `<code>`.
2. Check 3 greps the `- D-NNN THEIRS` line for REPORTED; the rule's own LOG examples wrap it.
3. No rule for which original to credit when a house text was reprinted many times (Checksummer:
   8603/55, SH8602/6, SH8507/6, SH8603/76) — the monthly original, as SH8602 credits, was kept.
4. My brief said "apply only OURS fixes"; r330 step 7's credit line is also required (precedent
   SH8603). The brief should have named it.

**Suggested.** r330: add a disposition MOVED for blocks placed at different points with identical words, and MARKUP for code-wrapping artefacts; check 3 reads the whole entry.

## 325/070 — text typeset after 070 escapes its quote straightening; column measurement method

**Harvest:** OUTSTANDING.

160 typeset 81's Texte-Datei `<pre>` from fresh OCR after 070 had run, so four curly ” survived
in PETSCII text. Any step that adds text after 070 should run 070's quote fold on what it adds.
Reader 4: r325 asks for monospace columns to be compared but names no method; eye estimates were
wrong more than once — glyph pitch from tesseract boxes / ink segments (~41.6 px at 600 dpi
typewriter face) settled it.

**Suggested.** r160/r190: "Any text added after 070 gets 070's quote fold and dash pass." r325: "Measure monospace columns by glyph pitch (tesseract boxes / ink segments), never by eye."

## 340 — rules that saved this build

**Harvest:** HARVESTED — —. No change asked; all five sections intact.

- **r000 "Changing a PROGRAM FILE always goes to the user first"** kept the Hobbit `115 REM` patch,
  the three petcat asymmetries and the four MSE print/disk tails out of `prg/` and on the owner's list.
- **r190 "BEFORE RESTORING A MISSING PASSAGE"** made three agents grep first: two "missing" sentences
  in 58 were already there (one glued to a neighbour) and were split, not duplicated.
- **r130's ruling inline vs end, and r080's listing-only pages** (via the SH8603 precedent) put every
  disk file in an article with no orphans; `prg.txt` pruned to the one documented intro file.
- **r000 "A CHECK YOU HAVE NOT SEEN FAIL IS NOT A CHECK"**: every sub-agent planted a fault; that is
  how r190's check 3b (reads the repo root) and r250's (never exits non-zero) were found.
- **r170's "a complete MSE/Checksummer listing is recreated as a disk file"** turned 94's TODO into a
  proven file (107/107 sums) instead of an owner question.

**Suggested.** Keep these five sections as they are; they did their job on SH8604.

## 340 — sign-off

Kept from the first confusion (005 pre-fill, first commit aa501936) to the end of 006; signed off with
47 entries. After sign-off, seven changes and seven more entries followed (below). Finalized on
2026-10-06 at the owner's instruction: every entry's harvest status is at its heading and summarised
at the top.

## 300/325 — a Futureteufelchen candidate was proposed without checking the transcription against the crop

**Harvest:** OUTSTANDING.

**What happened.** Reader 2 (325) reported p71's `51103 IF 01<>0 AND 02<>0 …` as printed with digit
zeros; I "confirmed" it by RUNNING the printed-as-transcribed line in x64sc (it misbehaves) and
proposed it to the owner. Control cropped the line: the O of O1/O2 measures 113–115 px against
106–107 px for the zeros, visibly rounder at 2–3× — the print is `O1`/`O2` and correct. The raw OCR
`01<>0O` (digit AND letter at one position) was the ambiguity signal, and my own run of the letter
form behaved exactly as the article says. Running proves the transcribed text fails; it does not
prove the transcription is the print. Cost: one wrong owner item, caught by control.

**Suggested.** r300/r325: "Before proposing a Futureteufelchen candidate, re-read every glyph the
claim depends on at ≥ 3× on the crop, measuring O/0 and 1/l widths against known glyphs on the same
line; a candidate whose evidence is our transcription is a candidate OCR error first."

## 150 — grouped crops, text inside a crop's frame, a crop carrying its own caption (sub-agent, full form)

**Harvest:** OUTSTANDING.

1. A file covering several Bild numbers with a letter-run name (`10-6abc`): Verification 1 allows
   `_`, nothing says how captions combine or where it goes (followed SH8601 26-5_9: one figure,
   captions joined with `<br>`, at the first member's position).
2. Text printed inside the crop's frame that the HTML also carries as prose (the p33 box line) —
   owner-crop-wins names tables and listings only.
3. A crop that includes its printed caption (10-2, 81-1) doubles it with the figcaption.
4. Unescaped `>` in alt text passes check 4 but breaks `<img [^>]*>` regexes downstream.

**Suggested.** r150: "A grouped crop `N-6abc` is one `<figure>` with each printed caption on its
own line, at the first member's position; prose printed inside a cut frame goes with the crop;
a crop that contains its printed caption goes back to the owner for a re-cut (SH8603 31-3); escape
`<` and `>` in alt."

## 006 — finished outputs vanished from `<tmp>`; a FORCE range silently forces nothing

**Harvest:** PARTLY — ac929c71. Item 2 (ranges) done; copying the PDF into issues/<ID>/ with a LOG hash is not.

1. Both built PDFs disappeared from `<tmp>` within 27 minutes of being built, logs intact, cause
   unknown. Rebuilt from caches and verified pixel-identical — possible only because the caches and
   a pre-loss render existed.
2. My brief from control gave `FORCE_BILEVEL="003-162"`; the script matches space-separated numbers,
   so a range forces nothing and the build still looks successful. Expanded it (now in r006, ac929c71).

**Suggested.** r006: "Copy the finished PDF into `issues/<ID>/` (uncommitted is fine) the moment it
is built, and keep a hash of it in LOG.md; `<tmp>` is durable for inputs, not a safe home for a
deliverable awaiting review." (Item 2 already harvested.)

## 340 — after sign-off: the owner re-cut 29 figures

The owner re-delivered 29 crops (10-3, 40-1…8, 49-9/10/12, 58-1…12 with 6a/6b, 78-1/2, 81-1/2)
without the halftone dot screen the first two deliveries carried; committed as f6fe86a6. What it fixed: the
screened cuts rendered as near-solid black at web size — 58-4 89.8 → 3.4 % black, 58-9 73.2 → 5.2,
58-3 69.4 → 6.1, 40-6 69.0 → 3.2, 78-1 53.0 → 7.4 — so the drawings and screenshots in them were
illegible on the site. Renames 6-3→10-3 and 40-9/10/12→49-9/10/12 applied; 49-11 keeps its earlier
cut. Set check 47 = 47, r310 HARD 0, site rebuilt; the PDF is built from the pages, not the crops,
and was not touched.

## 150 — dot-screened crops passed every check; nothing measures legibility

**Harvest:** HARVESTED — 1158fb33, 11bfdf5d.

**What happened.** The first delivery's crops of screened artwork placed cleanly: r150's set check,
alt/caption checks, r310 and the site build all pass on an image that is a black rectangle at web
size. No check looks at the pixels. Measured on the 29 replaced files (gray, 50 % threshold):
9 were above 50 % black (40-5, 40-6, 58-3, 58-4, 58-6b, 58-7, 58-9, 58-10, 78-1), 11 above 40 %;
the re-cut set's maximum is 12.0 %. Over the whole issue, genuinely dark images exist — the
greyscale lead photos (71–97 %) and one dense 1-bit figure (10-5, character grids, 21.6 %) — so a
threshold alone cannot reject, only flag.

**Suggested.** r150 Verification: "For each placed crop, print its black fraction (gray, 50 %
threshold). Any 1-bit/line crop above 40 % black is LOOKED AT at display size before sign-off
(halftone screen, inverted scan, or a genuinely dark figure — say which); photos are exempt."

## 340 — after sign-off, second change: four orphans moved off the article end

The owner's new rule (2026-10-06, r150 "NEVER LEAVE AN ORPHAN AT THE END", 1158fb33) found Tabelle 3
in *Künstliche Intelligenz* after Listing 4, and control's check found Listings 16, 23 and 24 after
the byline of *Dateiverwaltung komplett*. Each was placed by its page (b85d414a): Tabelle 3 after
Tabelle 2 (p46 prints it above Tabelle 4); Listing 16 after Bild 5 (foot of p20, before the paragraph
whose colon leads into p21's menu table); Listings 23 and 24 after the sentences that introduce them
(p26 "… abtippen:", p35 "Anschließend finden Sie das Listing 24 …"), ahead of their documentation.
Pure moves, set check 47 = 47, r310 HARD 0, site rebuilt, PDF untouched.

## 150 — the orphan check names one member per series; the black look flags greyscale photos

**Harvest:** HARVESTED — 11bfdf5d. Photos exempted by mode (1/P only), not by histogram or `N-0` name — control's choice, it generalises.

1. On the pre-move files the orphan check reports Listing 24 and Tabelle 3, not Listings 16 and 23: it
   tests only the LAST member, so a run of orphans shows as one. Moving the reported one alone and
   re-running would surface the next — three rounds for 10's three listings.
2. The black-fraction look says "photos are exempt" but filters by PIL mode (`1`/`P`/`L`), and a
   greyscale lead photo is mode `L`: on SH8604 it flags exactly the six lead photos (71.6–96.5 %) and
   no line figure.

**Suggested.** r150: "The orphan check: also report every member that follows the byline/`<address>`
or is followed only by other trailing figures — the whole trailing run, not just its last element."
And for the black look: "skip mode `L` crops whose grey histogram is not bimodal (a photo), or
exempt by name the `N-0` lead images; state that the rest is a look, not a gate."

## 340 — after sign-off, third change: Eliza merged into Künstliche Intelligenz; Tabelle 6 shaded

Owner, 2026-10-06: Eliza is not a separate article (Bild 9-12 and Listing 5-7 continue KI's series;
the only such adjacent pair in the corpus). Merged in a6735119: body appended unchanged, its `<h1>` as
`<h2>` (p49 prints it in the same ruled style as KI's section heads), pages 40-57, author from Eliza's
byline, `toc_title` "Kurs: Künstliche Intelligenz<br>Eliza". Same commit: Tabelle 6's grey ground
(owner: "we lost the styling") restored as `class="shaded"` on the 24 N/O/S/W cells of rows
5,5,6,6,6,7; Tabelle 1-5 carry no tint. Set check 47 = 47, orphan 0, r310 HARD 0, site rebuilt, PDF
untouched.

## 080/100 — a merged article cannot carry a second Inhalt line

**Harvest:** SUPERSEDED — 4988c464, cfd8528e. "first toc_title only" landed (4988c464); the `<br>` join was superseded — a merged article keeps its OWN entry (cfd8528e); no duplicate-meta check.

Control's brief asked for Eliza's Inhalt entry to stay reachable "with a `toc_title` or an index entry
pointing into the merged article, exactly as a lettered sibling would". There is no such mechanism:
generate.py emits one Inhalt line per file, and `find_meta` returns the FIRST meta of a name — a
second `64er.toc_title`/`toc_category` is silently ignored (8501's HI-EDDI and Handballtrainer each
carry one that has never been read). A lettered sibling is a separate file, which is what the merge
removes. Done here by the corpus's `<br>` join (119 `toc_title`s); the cost is that Eliza's printed
page 49 no longer appears — the line shows 40.

**Suggested.** r080/r100: "When a merge swallows a printed Inhalt entry, join the titles in the
surviving article's `toc_title` with `<br>`; never write a second `toc_title` meta — generate.py reads
the first only." Optionally a check that flags any article with two metas of the same `64er.` name.

## 340 — after sign-off, fourth change: Adventure satt links its nine programs

Owner, 2026-10-06: the references in `161 Adventure satt!.html` become links to the ARTICLES. The nine
program names now link to their articles in SH8502 (7) and SH8503 (2) (9fc8fb55): name inside the
`<strong>`, colon outside the anchor, the printed `(SH2/85)`/`(SH3/85)` tags kept as text (each
matches its target's issue). r330 check (b) with the widened `[A-Za-z0-9]\{4,6\}` regex resolves all
nine to exactly one article and catches a planted `zauberschloß_2`. r310 HARD 0, site rebuilt, PDF
untouched.

## 340 — after sign-off, fifth change: the merged article's Inhalt line drops Eliza

Owner, 2026-10-06: *"toc should only say kuenstliche."* `toc_title` is back to "Kurs: Künstliche
Intelligenz", the printed p40 entry in `toc_entries.txt`; Eliza's p49 entry does not appear in the
contents (ee062697). The `<br>` join suggested in the 080/100 entry above is superseded: r100
(cfd8528e) now says a merged article keeps its OWN Inhalt entry, and `<br>` is only for one printed
line with two headings. Rebuilt: the Inhalt shows "Kurs: Künstliche Intelligenz" and no "Eliza" anywhere
in index.html; r310 HARD 0; PDF untouched.

## 340 — after sign-off, sixth change (control): the Hobbit download's `$A0` bytes restored

Control's eda01925: `der kl. hobbit` lines 10000 and 60000 end their REM banner in `$A0`; the `.txt`
had `close` and the published `.prg` carried literal CLOSE. The `.txt` now holds the raw byte and
generate.py reads and pipes listings as latin-1. See the ⚠ 120 entry below — the one finding of this
build that was an error in a file a reader downloaded.

## 340 — after sign-off, seventh change: comments beside two short downloads

Owner, 2026-10-06: *"if we cant get it right, html comment"*. In `133 Wie im Eisen der Fuchs….html`
the hidden figures for `lader` (line 199) and `1985_1986` (lines 2270, 3880) each get a German
comment saying the original line holds only a space and the offered PRG lacks it (1cff6b7a). Sweep
`^[ \t]*[0-9]+[ \t]*$` over the four hidden listings: lader 1, 1985_1986 2, 82 0, 85 0. Both comments
reach the built page beside their downloads; r310 HARD 0; PDF untouched.

## 120 — ⚠ PUBLISHED-FILE ERROR, not a rule defect: the Hobbit download carried `CLOSE` for a shifted space

**Harvest:** PARTLY — eda01925, ac30971c. The mechanism is fixed; the per-difference byte-level cause rule is not in r120.

**Severity: different from every other entry here** — a reader's download was wrong; all other
entries are rule or check defects caught before or without harm.

**What happened.** `der kl. hobbit` lines 10000 and 60000 pad a REM banner and end in `$A0`, the
shifted space — also the token for CLOSE. After REM, petcat detokenises it, so 120's `.txt` read
`… close`, and generate.py's `petcat -w` round-trip wrote five literal bytes into the published
`.prg` where the program has one. I SAW it at 120 (LOG: "REM ends in $A0, decoded as `close`,
re-tokenised as literal CLOSE, +4 bytes each") and filed it as the third "petcat asymmetry" beside
`lader` and `1985_1986`. The cause later given for all three — a space-only line body — is true of
those two only; the owner closed all three as "fine" on that cause, and the Hobbit's different
defect shipped. Control found it and fixed it in eda01925 (the listing is read and piped as
latin-1, the `.txt` holds the raw byte). My error: I grouped three findings under one label because
their symptom (round-trip differs) was shared, and the label then carried one cause for all of them
to the owner.

**Suggested.** r120: "Each round-trip difference goes to the owner with ITS OWN byte-level cause
(hex of the disk bytes vs the re-tokenised bytes) — never grouped under a shared label. A difference
inside a REM or string where the disk byte is ≥ $80 is a TRANSCRIPTION ERROR in a file we publish
until proven otherwise, not an asymmetry." (eda01925 fixed the mechanism; ac30971c recorded the
brace-escape limit; the grouping rule is not yet in r120.)

## generate.py — the serve step's traceback on a busy port reads as a failed build

**Harvest:** OUTSTANDING.

Every rebuild after 006 ended in `OSError: [Errno 48] Address already in use` and a non-zero exit,
because a server not started by this session (a stray `http.server 8081`, started 2026-10-05 00:31)
held the port. The site build itself had completed each time; only the log tail looked like a
failure, and each time I had to prove completion by counting regenerated files.

**Suggested.** generate.py: "When the serve port is taken, print one line (`port N busy — build
complete, not serving`) and exit 0", or add a `--no-serve` flag for verification builds (there is
none today; `--join` skips the server but opens a browser).

## 340 — found while finalizing: rule text and code that contradict harvested fixes

**Harvest:** OUTSTANDING.

Checking each entry against HEAD turned up leftovers of harvests that landed elsewhere:
1. `r000_orchestration.md` line 226 (the hand-over table) still says the cover crop is "a reduction
   of `masters600/001.png`", which contradicts 4408be0e (the cover comes from `<A4>`, a4600 on a sheet).
2. `r005_masters_sheet.py:195` still says a confident parity disagreement "is a failure"; the rule
   now says NOTED (6d144ed9).
3. r005's rule pre-fills from the UNION of witnesses (5f4557cc); the code pre-fills from the edge
   finder alone.
4. r005's Verification 4 comment still says it reads sheets600; the check now slices masters600.

**Suggested.** Fix the four sites in the harvest pass for this issue; a harvest that changes a rule's
claim should grep the rule set and the code comments for the old claim.

