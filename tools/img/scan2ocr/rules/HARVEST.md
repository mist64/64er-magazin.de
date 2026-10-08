# Harvest of 8612's WORKFLOW_ERRATA.md

Working tracker. Each row: an errata entry, the owner's ruling, and where the
change lands. Closed rows stay, so the next harvest can see what was decided
and why. Source: `issues/8612/WORKFLOW_ERRATA.md` (~50 entries, 3 already
resolved mid-build).

Status: `decided` = ruled, not yet applied. `done` = applied and verified.

## Round 1 — the top of the errata's own cost ranking

### 1. r006 FORCE_CONTONE measures total chroma area  — decided
Owner: fix both defects, exact threshold.
- Threshold the LARGEST CONNECTED COMPONENT, not the sum of opened pixels.
- Exclude chroma lying outside the traced paper (the scanner bed).
- Replace "~50 mm2" with an exact 50.0; drop "there is no judgement here"
  being asserted before the measure is right.
- Expected on 8612: 022 024 114 125 152 172 180; 186 (27.9) and 042 (15.4)
  fall out as display-type fringe, 004 as bed.
- Lands in: r006 method snippet + the FORCE_CONTONE usage line.

### 2. r320 skips every listing block  — decided
Owner: narrow the skip and cover hand-typed listings.
- "Skip a listing block only when its article references a disk file for it;
  a hand-typed listing is checked like prose."
- NOT adopting the pdftotext -raw diff as a standard generator.
- Lands in: r320 (skip condition + gate), r325 (line-structure scope).

### 3. Five Verification checks that cannot fail  — decided
Owner: fix all five, plus the meta-rule.
- r260: heredoc terminator alone on its line; test output non-empty, not exit
  status; exempt a heading opening with a symbol.
- r220: parse the first integer before an em dash so range rows are checked.
- r280: drop `head`; checks 1-2 fail on hits.
- r240: anchor the editorial grep like the others; escape the dot.
- r320: exit non-zero on findings AND on CANNOT RUN.
- r000 (new): a Verification check ships only once it has been seen to fail
  against a deliberately planted fault.

### 4. Three helpers that no longer match the chain  — decided
Owner: fix all three.
- r210_head_meta_apply.py: page-relative fractions instead of 2480 / x<1240.
- r100_toc_title_apply.py: read toc_entries.txt (TSV); add Einsteiger-Teil,
  Hardware, Software-Hilfen to SECTION_TO_TOC_CATEGORY.
- r220 apply: route by 64er.pages coverage plus an h2 match inside a
  multi-page rubric, not by exact start page.

## Round 2 — conventions from the owner's review that live in no rule

### 5. HTML comments: German, reader-facing, harm test  — decided
Owner: codify, with a German machine marker.
- r000 (new): every HTML comment is German, names a print error a reader would
  otherwise act on, and says what is correct. Nothing else -- not absences,
  not provenance, not dates, not step numbers, not crop geometry, not
  adjudications (those live in adjudicated.txt).
- r000 Deliberate deviations: replace the English example with a German one.
- r290/r310: marker regex accepts `Druckfehler` and `So im Heft gedruckt`
  (8610's `Reiner Druckfehler` shape), not only `\bPRINTED\b`.
- Out of scope, recorded: 8611 (22/22 English) and SH8601 (14/16) have the
  same defect. SH8601 matters for the Sonderheft batch.

### 6. Column-wrap <br> (283 in table cells on 8612)  — decided
Owner: rule + code-join rule + SOFT check.
- r160/r190: a <br> marks the AUTHOR's line break only (new list item,
  address line, code line, deliberately set display line). A break where the
  printed column simply ended is not reproduced; join with a space, rejoining
  a word split at a hyphen.
- Beside it, the code-join rule: a wrap after `: , * = + - ( /` or before
  `+ - * / = ) " ;` hides no space; one space only between two alphanumeric
  tokens. An HTML entity ends in `;` and is NOT an operator.
- r310 SOFT: list every <br> in a <td>.
- The BASIC discriminator ("no line number after the break -> wrap") stays
  ADVISORY: it is wrong for unnumbered code (146 Tabelle 1).

### 7. Aside heading level, and standalone page pointers  — decided
Owner: codify both, check both.
- r190/r290: an aside heading is one level below the article's highest section
  heading (h2 if the body has h2 sections, else h3).
- r310 HARD: aside heading must not outrank its article.
- r080: a standalone "Fortsetzung / Anleitung / Listing auf Seite N" paragraph
  is never transcribed -- it is the layout speaking, not the author.
- r310 HARD: a <p> whose entire text matches ^(\w+ )?(auf|von) Seite \d+\.?$
- Note: 16 "auf Seite N" in 8612, only ONE was a pointer. The test is author
  versus layout, not the words.

### 8. Two articles sharing a start page  — decided
Owner: codify in r080 + r310 check.
- r080: two articles starting on the same page get 64er.pages NNNa / NNNb in
  printed order; the one starting higher on the page is `a`.
- r310 HARD: no two articles share a bare start page.
- The a/b ordering itself is read off the crop; the check cannot do it.

## Round 3

### 9. r006 cover/PDF cluster  — decided
Owner: fix all, including the export-elsewhere process change.
- Pre-build: every masters600/NNN.png matches the stamp's master-px.
  (8612: 001 was a 1240x1754 Affinity export saved over the 4961x7016 master;
  r006's freshness check passes in that case. Repaired by re-running `cut`.)
- title.png retouch check: compare with a 25% Lanczos reduction of
  masters600/001.png and COUNT pixels moved >30 levels (max over channels).
  MAE does not discriminate (2.93 unretouched vs 5.54 retouched); the counts
  were 27,049 vs 81,409. A count near the unretouched level -> stop and ask.
- make_issue_pdf_mixed.sh: invalidate guetzli-q*/$n.jpg when ${n}_150.png is
  newer. (8612: the rebuilt PDF had page 1 byte-identical and the same total
  size to the byte, 96,313,586.)
- make_issue_pdf_mixed.sh: end with the exiftool stamp (Title, dc:title,
  CreationDate, ModDate = file mtime).
- MAGICK_THREAD_LIMIT=1; add .ocrcache/pageclass.tsv and jbig2/*.jb2 to the
  cache-key list; fix the README resize claim; define w, h in the chroma snippet.
- r006 tells the owner: export title.png to a NEW path, never over the master.

### 10. r280 letter-count heuristic and two-engine check  — decided
Owner: demote the heuristic; the crop decides.
- The crop is the decision. Letter-count becomes "a hint that it MAY be a
  print typo". (As written it would have KEPT verliert, Textbildschirms,
  einem, Pawrn, zusaetzlicher, COME!I -- all proven OCR damage.)
- Block index becomes a LOCATOR, read via labels.json (full text), not the
  ~300-char truncated .txt.
- Drop the two-engine branch: the index is the HTML's own ancestor, so
  "engines disagree -> apply" never fired once.

### 11. r190 rewritten around the work that happens  — decided
Owner: rewrite.
- Steps become: restore lost drop caps from the crop; split headings that
  swallowed body text; rejoin paragraphs split mid-sentence; clear p.source
  debris. (Both 190 sub-agents found ZERO TODO markers.)
- Verification gains a never-split check and an empty-<p> check.
- The Impressum gets an owning rule.
- Resolved conflicts: interview labels are roman (the page won); dash lists
  stay <p>-- (the corpus won); skipped_files moves out of /tmp.

### 12. r180 author initials  — decided
Owner: keep initials as printed; the rule changes, not the corpus.
- r180: "Initialen bleiben wie gedruckt." (The rule contradicted its own
  examples and 8609-8611.)
- check 4: fix the invalid BSD character range `[...\- ]`.
- check 5: split each <address> on `/` ((Name/xx) yields two entries; 6 files
  in published 8611 were flagged wrongly).

## Round 4

### 13. The 24 mechanical corrections  — decided
Owner: apply all 24 as the errata states; review the diff per step afterwards.
Steps touched: r000, r005 (x3), r030 (x3), r040, r050, r070, r080, r100,
r110, r130 (x2), r145, r160, r210, r220, r240, r250, r310, r320.

### 14. Art-tilted ads  — decided
Owner: diagnostic only, no per-page override.
- r005 Verification: any page with |skew.angle| > 1.0 deg is LOOK AT.
- The re-level pass NOTEs a total angle outside SKEW_COARSE.
- 8612 would have listed 183 (-6.60), 140 (+2.02), 117 (-1.72).

### 15. "Auf einen Blick" boxes  — decided
Owner: figcaption wins; name the exception.
- r160 keeps the general prohibition on promoting headings, EXCEPT a named box
  whose title is part of the box ("Auf einen Blick:", "Stueckliste").
- 8612's instance is brought into line with 8609/22 and 8610/176.

### 16. r120's five gaps  — decided
Owner: codify all five plus the page-mapping rule.
- A separator NN is the PAGE the listings sit on; map through 64er.pages
  (false for 54/57/78 on 8612 -- inside articles 51, 52, 74).
- BASIC at a load address not ending in 01: relink to $1C01.
- Stub test: a bare SYS anywhere, not only as the last statement.
- A line-linked plain-ASCII assembler source has a path.
- Strip `;del/<n>.prg` and leading blank lines on re-decode.

## Round 5

### 17. r320 blind spot + r325 scope  — decided
Owner: both.
- r320 companion: sweep noise/other blocks for screenable text.
- r325: line structure IS in scope for hand-typed <pre>; monospace spacing is
  checked by glyph column; repeated runs are counted mechanically.

### 18. r280 hex exception and <pre> scope  — decided
Owner: fix both.
- A token that is not valid hex (O, l, I) is OCR damage: fix from the crop.
- <pre> IS in r280's scope (the briefing forbade it while every worklist
  contained <pre> items).

### 19. Five codify-only items  — decided
Owner: codify all five.
- r130 data-range: compare each disk listing's first/last line with the print;
  add data-range where they differ. The download stays the full file.
- r160/r150: keep a printed table's drawing+legend pairing; do not regroup.
- r190: the print wins over the never-split rule when the box is physically
  above the source (48's liability box; p50 prints it above).
- r160 names three shapes: a label printed INSIDE the box (Stueckliste); a Bild
  holding tables AND drawings (p61 Bild 7); market tables referenced generically.

### 20. Adjacent-issue defects  — decided
Owner: SH8601 now; 8611 and the prgs later.
- NOW: SH8601's 14 English HTML comments -> German, harm test applied. It is
  the template the next six Sonderheft builds will be compared against.
- RECORDED, not now: 8611 (22/22 English comments); 8510 timer-test and
  SH8505 dump c000 ship prgs one byte longer than the printed range.

## Found while applying — r260's checks had never run, so their gaps were invisible

Once the heredoc terminator was repaired, both r260 checks ran for the first
time and produced five false positives on published issues. Three shapes, all
now exempt:

- a BASIC KEYWORD heading is code and correctly uppercase: 8609/66 "POKE 1,0
  ???", SH8505/103 "ON ERROR GOTO";
- a heading opening with the MAGAZINE'S OWN NAME: 20 in the corpus ("64'er
  Extra: …", "64'er Disk-Ecke");
- a heading opening with a NUMBER of any length, or an ellipsis: 8609 "19 neue
  Befehle", 8611 "14mal schneller laden", 8610 "... oder aber Informationen",
  8611 ". . .und Interpreter-Routinen". The model-number rule wanted three or
  four digits and so missed the two-digit cases.

VERIFIED: 0 findings on every chain-built issue (8609, 8610, 8611, 8612,
SH8601), and the check still fires on a planted ALL CAPS heading.

**Recorded for the owner, out of scope:** 25 findings remain across ten
hand-built pre-chain issues (8408 4, 8501 5, 8408/8412/8504/8505/8507/8601/
8602/8603/SH8506 the rest). They predate the chain.

## DECIDED — the shared-start-page check stays HARD; old issues are not fixed

The new r310 HARD check ("two articles must not share a bare start page")
works, but the corpus shows the lettering convention has only ever been
applied to the pairs the owner happened to notice. Current state:

| issue | lettered | NOT lettered (fires HARD) |
|---|---|---|
| 8609 | — | p8 (editorial + Commodore Deutschland), p167 (Anwendung + Listing) |
| 8610 | — | p8, p16, p193 |
| 8611 | 182a/182b | p8, p99 (Checksummer + Fehlerteufelchen) |
| 8612 | 169a/b, 193a/b | p8, p170, p195 |

**The editorial shares page 8 with the first feature in EVERY issue.** That is
structural, not an oversight, which is why a HARD check on it fails
everywhere. Three ways out, for the owner:

- (a) letter all eleven pairs across 8609-8612 (ordering read off each crop);
- (b) make the check SOFT -- a list to read, not a gate;
- (c) exempt a named class (the editorial, and r300's Fehlerteufelchen box
  which shares p99 with the Checksummer in 8611), keeping it HARD for the
  rest.

**Owner's ruling (2026-10-03): HARD. Do not fix old issues.**

So the check stays HARD, none of the eleven pairs is lettered retroactively,
and the findings stand as a known state of the published corpus: 8609 2 pairs,
8610 3, 8611 2, 8612 3 (p8, p170, p195). Option (a) is rejected, (b) and (c)
are not taken.

What this means for a NEW build: the check will fire on the editorial/feature
pair on page 8 of every issue. Letter the pairs that matter on the page, as
r080 now says, and expect the p8 pair to show up in r310's HARD list without
being a defect. It is a list to read, not a gate to reach zero -- r000's
warning about a check that stops being read applies, and this is the one
place in the chain where a HARD finding is expected to persist.

## Also found while applying

- `generate.py` exits **1 on every run**, on a clean tree, because it calls
  `./filter_rss.py` and `./filter_index.py` with `#!/usr/bin/env python3`
  shebangs and no `check=True`; under system Python both die on missing
  `pytz` / `bs4`. So r000's end-of-issue build gate cannot be read by exit
  code. Pre-existing, out of this harvest's scope, owner's call.
- 8609 carries 4 HARD r190 byline-split findings (articles 64, 66, 68) --
  these are the ones that used to surface when r310 defaulted to issues/8609.
  Out of scope, recorded.

# ============================================================
# SH8602 — harvested 2026-10-04
# ============================================================

49 entries from `issues/SH8602/WORKFLOW_ERRATA.md`, applied in five commits and
the errata file then deleted per the owner's instruction. Read as one
implementer's notes and cross-checked, not transcribed — two claims turned out
to understate the problem (see below) and none was found wrong.

Decision procedure used, agreed with the owner beforehand:
the printed page wins on content; the corpus wins where the print does not
decide; measurement beats assertion; the owner rules what is editorial. For a
rule-versus-code disagreement the PROSE follows the CODE, because changing
prose costs nothing and changing code rewrites published output — unless the
code is demonstrably producing wrong output, and then the blast radius is
measured first.

| commit | what |
|---|---|
| `ba4605c2` | a master is 2400 dpi OR 600 dpi: shared `scan_dpi()`, per-page thumb recipe, per-page disk budget |
| `3305da8f` | r330 reprint leads + THEIRS blind reading; r060 list numbering; four checks that could not do their job |
| `f23a2394` | the owner rulings (figures, glyphs, placement, dash, prg errata, TOC naming, K anchor) |
| `7e799733` | monthly-shaped rules re-shaped; r070/r040/r220 script bugs |
| `61aa8a79` | SH8601's issue key normalised, with the r080 rule and an r310 check |

**Two entries understated their own finding:**

- r320's dropped-listings companion was described as "vacuous on MSE/BASIC
  issues". Making it report its denominator showed worse: **SH8602 has 1,933
  dropped listing blocks of which 0 were checkable, and 8612 has 647 of which
  0.** The gate has returned a clean "0" on both issues while examining
  nothing; only SH8601, which had SMON dumps, ever exercised it.
- r070's ordering bug was recorded as "the script still has the bug its rule
  says was fixed". It is worse than cosmetic: the script was **not
  idempotent**, which is the one property its rule guarantees.

**Corrected while harvesting:** the "banner-only article name" entry. The build
retitled SH8602's article 3 to "Einleitung" after the running-head banner, on
my relay; the owner's final ruling is that the **printed Inhalt** names an
article. The rule in r080 is the TOC, not the banner.


# Harvest of SH8604's WORKFLOW_ERRATA.md

54 proposal entries at finalisation: 15 already harvested during the build, 1
superseded, 9 partly, 29 outstanding. All of them are applied now, in chain
order, one commit per group:

| `92fea5f8` | the 190 cluster, and 005 read cold by SH8605 |
| `e9600042` | 005b, 080, 090, 120 |
| `d7c4cc72` | 130, and two checks seen to fail |
| `65f6b80f` | the two 140 entries, and r330 Step 0 |
| `1dde4e4c` | 150: four names, grouped crops, alt escaping |
| `5f6c0b6e` | the 160 cluster, and an unverified claim in r000 |
| `e259e471` | 170 and 180 |
| `e439d8d9` | 210 and 220 |
| `d1b6059c` | 250, 280, 290, 300, and r000's direct-mode test |
| `fc1e404f` | 006, 070, 325, 330, 340, generate.py |
| `c5438ce7` | the four PARTLY 005 entries |

**Two entries came out differently from what they proposed, and the difference
is the point:**

- **005, the paper pre-fill.** The entry asked for the pre-fill to be GATED on
  the own-white measurement. Measured, no threshold works: against SH8604's
  interior own-white p50 of 208 179 166, the cover is genuinely card at
  distance 40 and the tinted interior sits at 30. The gate was written and
  **not shipped**; the distance is printed beside each pre-filled page instead.
- **005, the parity gate.** The entry diagnosed SH8604's 93 firings as the
  600 dpi frame clipping the torn fringe. It is not: every Sonderheft is
  near-flush on the left (SH8601 0.34 mm, SH8604 0.17 mm) and SH8601's gate
  agrees on 149 of 150, so the margin is not the variable; and SH8604's left
  jitter is 0.35 px against SH8601's 0.06, so that edge is not clipped, it is
  **torn**. SH8604's sheets present the opposite side, consistently. Two
  suppressions were written and reverted. **This is an open owner question for
  PAUSE 1**, recorded in r005 with the numbers.

**Checks changed in this harvest, every one seen to fail before it shipped:**
r130 check 4 (split at the byline) and check 7 (duplicates, corrected once
when it called "Listing 14" and "14b" a duplicate); r140 check 4 (same machine,
bound variables); r150 check 4 (unescaped `<`/`>` in alt); r160 check 5 (a
compound is not a reference; a damage token is a look); r210 check 3 (fails on
a closed machine name); r220's routing check (a row matching no article; a
forward misroute); r250's whole block (exits 1; the wrapped label, minus the
Impressum and minus digit labels); r280 check 4 (Pass 3 finds the lowercase
jam the greps cannot); r290 check 2 (an aside below an h2 body); r330 check 3
(reads the whole entry); r005 Verification 6 (rewritten: it compared a file to
itself).

**Two checks were written and deliberately NOT shipped**, because they fired on
correct data: r210's "does this look like a machine label" (flagged 8612's
`C 16, Plus/4` on 2 of 3 issues) and the r005 own-white gate above. Both are
recorded where they would have gone.

**Found in old issues while verifying, reported and NOT fixed** (owner's call):
8609 x2 and SH8601 x10 asides levelled below an h2 body; 8408/151's duplicate
Listing 1/2, which is CORRECT (C 64 and VC 20 variants share a number) and is
recorded in r130's check as a reviewed/ case; SH8506/116's Listing 1/2, which
looks like a genuine double emission; `alt="Michael Scharfenberger,
Chefredakteur<"` in 8604/8 and 8606/8; and one row of
`Gesamtinhaltsverzeichnis Sonderhefte.csv` keyed `4/86` that belongs to SH8504
(4/85) — `Sprite+Grafik-Basic`, page 42, which matches SH8504's article
exactly.


# ============================================================
# Harvest of SH8605's WORKFLOW_ERRATA.md -- 2026-10-08
# ============================================================

**47 entries** at finalisation, against SH8604's 63. Eight landed during the
build (the rules moved under it, r340's blocking-defect exception), five needed
no rule change, and the rest are applied here in chain order, one commit per
group:

| `350fb7b0` | r000 -- the human's note in the scan dir, the previous reader's PEN, no two model-calling steps at once, the wrapper-header recipe, `port busy` as a PASS |
| `dee19473` | r005 and 005b -- the dpi witness, the pre-fill warning, `$PY`, 005b's Run section and a Verification that runs |
| `67ac89b9` | the PLATE principle: notes and markings are not print, and one that survives into the PDF goes to the owner |
| `62303323` | r006 -- line-art colour, FORCE_CONTONE, the count check, and JOBS in the two PDF scripts |
| `01d07774` | r020, r040, r060, r070, r080, r120, r140 |
| `544f58fc` | r080, r190, r200, r220, r250, and r000's header-vs-body rule |
| `6b7a503d` | the owner's four defaults, r310's two checks, r150's captions |

## What this harvest says about the rules

**The dominant class, by a long way: a check that cannot see the defect it is
named for.** Nine of the 47, and every one of them had been passing quietly for
issues:

- r310's "the closing run is a unit" could never fire at all -- `\b` after a
  quote has no word boundary -- so it had been silent on every page ever built.
- r005's Verification could not RUN: `$PY` was defined in none of the four
  fences that use it. When it was made to run it was already red, on two pages.
- r120 check 3's orphan count only sees files before the FIRST separator.
- r040's bold-pair count cannot span the escaped `\*` between two literals.
- r080 check 4's character class accepted the spaced separator its own rule
  forbids.
- r140 check 3 piped its findings into `head -5`.
- r220's routing check compared the CSV title unstripped.
- r330's `verify` read any four-cell table as a lead row, and skipped a pair
  whose LEAD was already in a problem.
- r150's `figure_captions.txt` matched the whole article text, issue-wide.

**The second class: a check that fails on a CORRECT issue** -- r060's
`<br/> > 0`, r200's three hard-coded Leserforum metas, r250's missing `table`
continuation, r005's uniform-master-size assert, r330's step 7 credit set. Each
one invites the builder to "fix" the transform.

**The third: a rule whose header and body disagree** (r200), which is now a
principle in r000, and **an `Applies to:` whose evidence is an absence the rule
itself caused**, which is void.

**The fourth, and the one the owner named: no default, so everything became a
question.** Futureteufelchen candidates, print/disk divergences, heading levels
and line-end hyphens -- four rules that were clear about HOW to decide and
silent about what the answer usually is. 66 + 14 + 1 + 1 owner questions that
the rules should have settled.

**Four entries record a rule that SAVED the build**: r005's one-sided-pre-fill
warning (caught p198), r006's colour cross-check (caught p007), generate.py's
busy-port fix, and 005b's "the summary cannot see this failure".

**Three entries are my own half-landed changes** -- a vocabulary changed without
its tool (r330's dispositions), a corpus count taken from a proposal without
counting (r150's `-x` names), and this harvest's own failure mode. The harvest
process is now itself a source of defects, which is worth watching.

## Measured while harvesting, not taken from the errata

- r006's two bed guards are NOT interchangeable, which the rule said they were:
  p007's largest blob is 8.5 mm2 with the paper mask and 56.0 mm2 with the 4 mm
  edge band -- missed by one, caught by the other.
- r005's field prose said skipping `r005_field.py` "is not an error" while its
  check 7a asserts a field file for every paper class. The yellowing correction
  could have been skipped with the rule's apparent blessing.
- r020's proposed strengthening does NOT work: all 8 masthead labels are in both
  the block index and the kept text of the very issue whose Impressum was wrong.
  Recorded as a dead end so it is not re-attempted.
- SH8605's p033 is correctly registered: its bbox RIGHT edge is 740 against
  741-742: the errata recorded the 16 px as 0.68 mm out of register in the
  delivery, and the opposite edge disproves it.
- r330's suspended-hyphen set was missing EIGHT words, not one. Counts over all
  41 published issues are in the code.
- r330's `verify` final line COUNTED ROWS, not pairs it had checked, so
  SH8605's `OK: 59 pair(s) verified` was four short and nothing said which four.
  Found by the fix for the shared-lead skip, not by the errata.
- The bare-`python3` entry was reported for r005 and "r010 too". It is
  **64 invocations in 23 rule files**, 14 of them in fences with no `PY=` at
  all -- the same unrunnable-check defect at twenty-three times the reported
  scale. Every harvest entry is a sample, not a census: COUNT IT.


# ============================================================
# A FAILURE MODE OF THIS PROCESS: THE OVER-GENERALISED CLAIM
# 2026-10-08, from the SH8605 harvest and the two builds that followed
# ============================================================

The SH8605 round recorded that *"three entries are my own half-landed changes…
the harvest process is now itself a source of defects, which is worth
watching."* Watching it produced a sharper and more common failure, and it is
worth naming separately because the REMEDY IS DIFFERENT. A half-landed change
needs finishing. An over-generalised one needs the claim CUT BACK to what was
actually measured — finishing it makes it worse.

**The shape: a number or a conclusion carried past the set it was true of.**
Seven instances in one day, five of them mine, and every one looked like
evidence at the time:

| the claim | the set it was true of | what it was applied to |
|---|---|---|
| "a 2400 dpi page may be a hand MARKING" | SH8605, where the markings happened to be at 2400 | the dpi witness in general — SH8608's marking is at **600** |
| "NEVER RUN TWO MODEL-CALLING STEPS AT ONCE" | one SH8605 collision | a standing constraint, which was never the owner's to pay for |
| r080's "Eingabehinweise beside the Checksummer" open question | SH8603's ENTANGLED geometry | every later issue sharing the SUBJECT |
| "fifteen or more precedents for splitting" | Checksummer + **MSE** | Checksummer + **Eingabehinweise**, a different pair |
| "the master is clean, 255 neutral" | the canvas PADDING around the page | the printed page, which is `page-px` inside `canvas-px` |
| "front-of-book residual +1.88 DN" | a band that included the COLOUR WRAPPER | the interior stock; interior-only it is **+0.17** |
| "the re-sweep rewrites sheets600, so the owner's title is stale" | the `low` class the fix touched | the cover, which is `high` and never read that file |

**Why it is hard to see from the inside.** Each claim was *true*, measured, and
written down honestly. What was wrong was the quantifier, and a quantifier is
invisible in the sentence that carries it: "the dpi witness can be a marking"
and "SH8605's markings were at 2400 dpi" read identically when you are the one
who just measured the second.

**The habit that catches it, and it is one line of work:**

> **Name the set, then check the thing you are worried about is IN it.**

Every artefact in this chain already carries its own set membership and will
answer in one grep — a master's stamp says `paper-class`, a field file says its
class, a page says its `64er.pages`, a measurement says which pages it pooled.
The cover/`high` error took one `grep paper-class` to settle after an hour of
measuring the wrong thing. The padding error took one look at
`page-px 4989 7034` inside `canvas-px 5457 7181`.

**And the corollary, which is the SH8605 round's lesson in a second form:** a
tally of the wrong set reads exactly like evidence, and is more persuasive than
no evidence at all. Both r080 corrections are this — the first replaced an
over-scoped question with an over-scoped count, and only a builder checking its
supervisor's citation against the corpus caught it.

**Where it was caught mattered more than that it was caught.** Six of the seven
were caught by MEASUREMENT or by a builder, after the claim had already been
written into a rule and acted on. The cheapest was the only one caught before it
shipped: SH8608 re-checking a ruling it had been given, at a step where it
happened to have the tooling, and coming back rather than building on it.

