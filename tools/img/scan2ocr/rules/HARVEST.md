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

**Six more, from the SH8606 and SH8608 round (2026-10-10 to 10-16):**

| the claim | the set it was true of | what it was applied to |
|---|---|---|
| r006's chroma census finds a hand marking | SH8606 p003, a GREEN mark on a LIGHT ground | every marking — SH8608's p104 black dot is chroma **9**, exactly print ink's, and all three of its marks shipped in the PDF |
| "0 failing" from the fence census | the **142** fences at column 0 | all **162**; the 20 indented inside a list were invisible, and two of them were broken |
| r180's "0 of 12 Sonderhefte carry the editor key" | the `xx = Name` spelling | the key as such — SH8608's and SH8606's both carry it as `Name (xx)` |
| r120 check 4's "round-trip failures" | listings that HAVE a disk file and were not patched | all 85 listings, counting print-only ones and r300 patches: 3 and 12 "failures" that were 0 and 0 |
| r000 check 1's "no exceptions" | the step files | the whole directory, so its own four non-step files made the verifier exit 1 on a clean tree |
| my own tile-ground draft | nothing yet | 1529 "findings" on SH8606 at the shipping threshold, because it scoped neither to bilevel pages nor away from halftones |

That last one is the instructive one: it was written **to enforce this rule**,
during the harvest **of this rule**, and still skipped both scoping steps. So
did r006's fence census. Knowing the failure mode is not protection against it;
printing the denominator is.

**And two more the day after, both mine, both caught by a builder reading what
I had written rather than doing what I had said:**

| the claim | what was missing | how it surfaced |
|---|---|---|
| "record the verdict in the issue's `LOG.md`, where the next build will read it" | `issues/*/*` ignores it and nothing un-ignores it — **zero** issues here have a tracked LOG.md | SH8608 mentioned in passing that LOG.md is git-ignored, having recorded the verdict there as told |
| "p104 is 1.6 x 2.0 mm" | the cutoff it was measured at — the file mixed a chroma locator for two marks with `lum < 25` for the third | SH8608 re-measured at 60 %, got 1.65 x 2.16, and offered it as measuring tolerance; it was two different measures |

Neither was a count. Both are the same shape one level up: **a statement whose
qualifier is missing cannot be checked, and reads as fact.** The durability
claim was about a file, not a set; the size claim was about a threshold. The
remedy is the same as the denominator — say the thing that would let a reader
disagree with you, and a second measurement becomes possible instead of
redundant.

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



# ============================================================
# Harvest of SH8606's and SH8608's WORKFLOW_ERRATA.md -- 2026-10-16
# ============================================================

**SH8608: 44 entries. SH8606: 16.** Two issues built in parallel in one working
tree, both held at PAUSE 2 while this ran, so no rule moved under a live build
(r000 forbids it; the harvest waited six days for the second builder to pause).

Three entries were duplicates across the two logs and SH8606's wording won each
time; four of SH8608's carry no proposal by design — two "a rule that saved me"
records and two records of the rules moving mid-build, which r340 asks for.
SH8606's 000 entry needed no change: r000's *TWO ISSUES AT ONCE* already goes
further than it proposed.

| `dcad8f51` | r000's fence census read 142 of 162 fences; the two it could not see were broken |
| `c6cab0a9` | r000's chain table had no 310/320/330 row at all; r325 and r330 contradicted each other on run order; r330 `verify` reads the LAST heading |
| `627e8b3e` | **nine checks that could never pass**, and one that could never fail -- r090, r130 x2, r200, r210, r220, r280, r005, r005b, r300 |
| `acd14a53` | r006: a colour census cannot see a dark hand mark; the PDF copy is not durable; r000's `D`-line commit guard; r150's derivable page->Bild map |
| `22d32641` | r006: 35 % is an asymmetry argument, not an optimum; r000 gains *A CLAIM ABOUT A SET* and the session-limit case |
| `2862c500` | SH8606's errata: the Verification blocks are bash; three checks that read a different artefact from the step they check; r120 check 4 |
| `39f5c9ad` | four wrappers called bare `python3`; r000's own numbering verifier exited 1 on a clean tree |
| `08124538` | SH8608's remaining: six rules that contradicted themselves, r120's 3b and fifth routing case, r040, r325, the emulator write test |

## What this harvest says about the rules

**The dominant class is the MIRROR of SH8605's.** That round's lesson was *a
check that cannot see the defect it is named for*; this round's is **a check
that can never pass**. Nine of them, all found by SH8608 in one build:
r005 check 4 (the printed footer bar sits inside the band it measures), r005b
check 1 (a tag the program only wrote when it padded), r090 check 2 (r080's own
commented-out placeholder), r130 check 6 (a bare printed caption) and check 5 (a
`<YYMM>` that bash reads as a redirect), r200 check 2 (a banner not every page
prints), r210 check 1 (Leserforum counted by filename), r220's orphan rows (the
typos step 4 tells you to fix), r280 checks 1-2 (markup counted as text).

The two faces are one defect — **the check does not know what correct looks
like** — and r000 now requires both halves: plant the fault and watch it fire,
THEN run it against an issue you believe is correct and require silence. All
nine had the first half done. Two more of the same kind turned up in r000's own
numbering verifier when it was finally run.

**A rule that says two things in two places is a tax on every later build.**
Six in SH8608's log alone: r190's aside heading (absolute in one place,
relative in another), r190's dash lists (the ruling sat 250 lines below the
instruction that contradicted it, with a stale example further down still),
r290 (bans an audit pass, then briefs one), r325/r330 (each claimed the other
had already run), r190's closing-run check against a printed text that ends in
a table, r280's evidence form against its own locator paragraph. None was
expensive alone; together they cost three agents' time on one issue, and the
325/330 circle cost a whole partial run that had to be thrown away.

**Two things only a build can tell you.** The Verification blocks are bash and
this machine's shell is zsh, so `for slug in $SLUGS` ran once over the whole
string and r140's check 4 printed nothing — a silent pass in the safe
direction. And a program that writes a file needs true drive emulation: VICE's
default traps let SH8608's VC 20 format loader print `DATAS OK` while writing
four wrong bytes. Neither is visible from reading the rules.

**What the builders did well, and it is worth naming.** Both logs quantify: a
cost in minutes, the measurement that settled it, and a concrete replacement
sentence. SH8608 corrected its own earlier entry twice when a later step
disproved it (the 005b UNIFIED note, the pre-PAUSE-1 census that was "wrong in
both directions"), and corrected one of MY measurements — the 120 dump's
next-row-address pattern is exact for five rows and displaced in two, so its
German comment is worded to be true of all eight. SH8606 caught its
supervisor's claim that a re-sweep had staled the owner's title crop: the
defect was a `low`-class profile and the cover is `high`, which one
`grep paper-class` settles. That is the habit this chain depends on.

## Harvest of SH8608's crop delivery -- 2026-10-17

The owner cut 44 of the 49 crops SH8608's worklist asked for, I checked the
delivery against the worklist and the masters before handing it to the builder,
and four of r150's defects fell out of that one check. None was found by a
build: they were found by someone reading the delivery against the rule that
was supposed to govern it.

| what was wrong in r150 | how it surfaced | the fix |
|---|---|---|
| `(see *renaming is authorised* above)` pointed at a section **that was never written** — the only rename guidance was step 4, which covers a wrong page PREFIX and is silent on the suffix | eight delivered files needed exactly that rename and the rule I went to cite did not exist | new *THE SUFFIX FOLLOWS THE PRINT*: the owner owns which crops exist, the print owns what each is called; rename and place, record the mapping in `reviewed/` |
| the two-bucket table warned only that a colour figure at 600 dpi is "not a visible defect, just a 3.9 MB download" | three crops of colour figures came back bilevel with the ground gone -- the visible direction the table never mentions | added the other face, plus the owner's ruling that the bucket is theirs and a worklist note that a page is colour is **not** a bucket assignment |
| nothing said what a dark bar in a bilevel crop means | I reported `131-1`'s black band as a conversion defect that "eats two rows". The master has a pale glare band in the same place that already wipes out the same characters -- the loss is in the plate, only its colour changed | new *A PRINT DEFECT CAN FLIP POLARITY UNDER BILEVEL*: open the same box in the master and name the content it still has before calling the conversion guilty |
| *A crop that covers SEVERAL Bild numbers is ONE figure* did not say the rule survives a frame with a rule down its middle, and gave `26-5_9` as a form without noting that `_` means *a part of* in the corpus's other two instances | owner reversed an earlier same-day ruling: the combined `10-1_2` stays combined | folded into the existing section -- see below, this one is why the entry is worth reading twice |

**I wrote a duplicate section before checking whether the rule already said it.**
*ONE CROP MAY CARRY TWO PRINTED BILDER* went in as a new `###` -- and r150 had
carried *A crop that covers SEVERAL Bild numbers is ONE figure* since SH8601,
saying the same thing and more precisely (it fixes the figure's position at the
FIRST member's, which my version omitted). I caught it only on the `grep '^### '`
I ran afterwards to check my own headings. **A new section is a claim that the
file does not already cover the case, and that claim is a one-line `grep` away
from being checked.** It belongs with *A CLAIM ABOUT A SET MUST STATE WHICH
MEMBERS IT COUNTED* in r000: I had counted the corpus for the naming form and
not counted the rule file for the rule. The three genuinely new facts were
folded into the section that already existed.

**And the delivery itself was clean where the rules had been sharpened.** Every
crop whose worklist row warned of a caption printed inside the frame -- `6-x`,
`47-1`, `47-3`, `47-5`, `10-6`, `131-1` -- came back with the caption cut away,
and `44-1` was re-cut to drop the printer's repro note on one sentence of
report. The worklist carrying each bbox, the frame's hazard and the caption's
position is what made that possible, and it is the half of PAUSE 2 that is
working.

### The same delivery, second pass: two worklist rows that were never crops

The owner answered the four undelivered rows by delivering two of them (`10-0`,
`129-2`) and telling me what the other two actually are. Both answers were
already in the corpus, and the worklist had asked for them anyway:

| row | the worklist asked for | what it is | where the answer was |
|---|---|---|---|
| `10-t1` | the whole p14 key table as one crop, *"the ZEICHEN column is reverse PETSCII and cannot be typeset"* | a typeset `<table>` whose ZEICHEN cells hold 32x32 glyphs **rendered from the C 64 character ROM** | `issues/SH8605/40-t1_*.png`, 36 files, the SAME table one Sonderheft earlier in the SAME course, and SH8605's build commit 2c7e1db8 says so in its message |
| `129-1` | a framed crop, because the sample lines carry overlined graphic characters | a listing | *"consistent with all other copies of this article, the one 'image' is a listing"* -- the article is boilerplate the magazine reprints |

r150's *A listing full of unreadable glyphs is cut WHOLE* was being read as
covering anything full of unreadable glyphs. It says **listing**, and both of
these are something else. Two new sections now say so, and the erratum on the
old one says why it was mis-read.

**The cost is not the crop, it is the round trip.** A worklist row asking for
something the project does not cut makes a complete delivery look incomplete:
I reported four files "never came" and chased two of them that were never
coming. The check that would have caught both is cheap and is the same check in
each case -- *has this been set before?* For `10-t1`, one `ls issues/*/40-t1_*`.
For `129-1`, r330's reprint comparison, run at worklist time instead of at the
end of the build.

**And I did the builder's work while doing it.** Owner, 2026-10-17:
*"stop doing your siblings' homework."* Checking a delivery file by file --
dimensions, colour modes, bbox montages, caption inclusion, master comparisons
-- is the placing step's own job, and r150's Verification already requires the
builder to produce exactly that evidence. What supervision owed here was the
two rulings and the two rule fixes, which is a fraction of the work and the
only part the builder could not do. The tell was that none of my measuring
changed a decision: the owner settled the bucket question in four words and the
two missing rows in two sentences.

**What the builder did right, and it is the rule working.** SH8608 held `10-0`
and `129-2` rather than placing crops my message had called undelivered, and
asked -- correct, because my message and the directory disagreed and only one
of them could be current. It also separated the two defects in `131-1` exactly
as the new rule asks: the black band is the plate (the master's glare already
wipes those characters), while the reverse-video header fields -- Name
`test/demo 1/85`, ID `84`, Format `2a` -- ARE legible in the master and are
dither in the bilevel crop. That second one is a real conversion loss and went
to the owner. *A claim that the conversion destroyed content must name the
content the master still has* -- it named it.

### And the rule caught its own author, one commit later

4286396c's *A RECURRING ARTICLE'S FIGURES FOLLOW ITS OTHER PRINTINGS* told the
builder to check how the other printings set a figure. I wrote it from the
owner's one-sentence ruling on `129-1` and **did not run the check the section
demands.** SH8608 ran it, found **six prior printings of the Checksummer and an
`<img>` crop for Bild 1 in every one**, and held the article out of its commit
rather than ship what I had told it to do.

| printing | Bild 1 |
|---|---|
| 8508/53, SH8503/6, SH8505/6, SH8506/16, SH8507/6 *Checksummer 64 … Neu* | `<img>` |
| SH8603/76 *Checksummer 20 V3* (the same VC 20 pair) | `<img src="76-1.png">` |
| SH8608/129 | `<pre>` -- mine, and the only one |

The command is one line, and it is the one the section itself asks for:
`grep -rl "So koennte ein Teil eines Listings" issues/*/*.html`.

**The failure is a relay, not a reading.** The owner's *"consistent with all
other copies of this article, the one 'image' is a listing"* is a statement
ABOUT the article -- its one picture is a picture of a listing -- and I turned
it into an instruction to typeset one. Then I wrote the inversion into a rule,
where it would have outlived the issue. **A one-sentence ruling relayed without
the count behind it is a guess wearing the owner's voice.** Doing that count
before passing a ruling on is exactly the supervision work that survived
*stop doing your siblings' homework*: not measuring the delivery, which the
builder owns, but checking the claim I am about to make permanent.

**This is the second time in one day that a builder corrected its supervisor by
counting**, after SH8608 separated the two defects in `131-1`. Both times the
builder had an explicit instruction from me and checked it anyway. That habit
is the only thing standing between a mis-relayed sentence and a published
mistake, and it is worth more than compliance.

### Three worklist rows, two issues, one mistake: asking the owner for what the chain can build

By the end of 2026-10-17 the owner had declined to cut three figures across
SH8606 and SH8608, and every one of them was the same error -- a crop worklist
asking for something the repository could already produce. None was a judgement
call; each was one command:

| row | the worklist said | what it actually was | the command |
|---|---|---|---|
| SH8608 `10-t1` | "the ZEICHEN column is reverse PETSCII and cannot be typeset" | 41 glyphs rendered from the C 64 character ROM, as SH8605 did for the same table | `ls issues/*/40-t1_*` |
| SH8608 `129-1` | a framed crop, the sample lines carry overlined graphic characters | an `<img>` in all six prior printings, and the corpus shares 47 PNGs across issues | `grep -rl "So koennte ein Teil eines Listings" issues/*/*.html` |
| SH8606 `114-l2` | "whole listing as one image (screen printout with reverse-video PETSCII glyphs)" | `titel.prg`, on the disk. It differs from the print in lines 91-93 and two texts -- which **the article's own HTML comment already recorded** -- i.e. r120 check 4's *expected r300 patch* | `ls issues/SH8606/prg/` |

Owner, on the last of them: *"why 114-l2? it's a listing, isnt it on the disk?
cant youtype?"*

**The common thread is that reverse or graphic PETSCII was treated as a reason
to photograph.** It is not. It is a rendering question with three settled
answers in this corpus -- the magazine's own `{CLR}` brace names, the
`<u>`/overline convention from 8610/80, and a rendered glyph. The camera is for
a photograph of a screen or a printout that no source reproduces.

r150 now opens the listing/table part of the worklist with those three
questions, each with its one-line check, before the *cut it WHOLE* section that
was being over-read.

**Why it kept happening is worth naming.** Each row was written with a real
reason attached -- the glyphs genuinely cannot be typed as plain characters,
the lines genuinely are overlined, the disk fassung genuinely differs from the
print. The reason was true and the conclusion was wrong, because the worklist
asked *can I transcribe this as text?* when the question is *can anything in
the repository produce this?* A true premise makes a row read as checked when
nobody checked the thing that mattered.

**And the cost landed on the owner, not on us.** Three round trips, and a
delivery that looked incomplete twice when it was complete both times.

### The harvest that switched off the instrument it harvests from

The 2026-10-16 harvest took 60 entries out of SH8606's and SH8608's
`WORKFLOW_ERRATA.md` **while both builds were still running**, and deleted both
files. r340 says the harvest happens *"once the issue is COMPLETE -- never
earlier"*, so the rule had no instruction for what I had just done, and I
supplied one by hand: *"open a fresh one if you start another build."*

SH8608 read "another build" as **another issue** -- a fair reading -- and so
**step 150 ran with no errata file open**: 47 crops placed, a table typeset
from the character ROM, and two findings that only surfaced because I asked the
builder what its file contained on 2026-10-17. They are now in a reopened file
(eb5de625):

- **340 has no instruction for reopening after a mid-build harvest.** This one.
- **r330 has no remap tool.** "Re-diff and remap by content" cost roughly 25
  commands and a hand-written difflib script across pairs 10, 44 and 129, and a
  plain index shift would have been WRONG on pair 10: 17 old 8512 table-cell
  differences now pair with our new Tabelle 1 instead. A `remap` subcommand is
  proposed. **Recorded, not built** -- a tool is not a mid-build change.

**The defect is the shape of the thing, not the wording.** Deleting a build's
log of where the rules failed, mid-build, removes the only instrument that
records what happens next -- and the removal is invisible from inside the
build, because a builder has no reason to look for an artefact it did not
delete. r340 and r000 now say the file is reopened empty in the same commit as
the harvest, and that **reopening is the harvester's job**.

**It also cost a second thing.** The same harvest means this session's two
issues now have TWO errata files each to harvest at completion, and the first
of each is already in the rules. HARVEST.md's SH8606/SH8608 section of
2026-10-16 is the boundary: anything in a reopened file starts after it.

### A gate that ran against an empty directory and called it a pass

SH8608 corrected one of its own reported passes on 2026-10-17: the
"r320 dropped listings 0" in its step-150 report was hollow. It had run
`r320_dropped_listings.py` against `<tmp>/ocr`, while this build's OCR output
is `<tmp>/ocr/out`. The glob matched nothing, the loop never executed, and the
script printed `dropped listing blocks: 0 … 0` and **exited 0**.

This is r000's *A CHECK SHIPS ONLY ONCE IT HAS BEEN SEEN TO FAIL* wearing its
other face, in a script that already had the right instinct everywhere else: it
separates `dropped` from `checkable` precisely so "0 findings" can be told from
"0 looked at", and prints a NOTE saying `"0" here is not evidence of coverage`
-- but only when `dropped and not checkable`. With no input at all, both are
zero, no NOTE fires, and the hollow case is the one case it does not catch.

**Three fixes, and the third is the one that mattered:**

1. `r320_dropped_listings.py` now exits 2 with `CANNOT RUN` on a directory with
   no `labels.json`, in the same words its sibling `r320_coverage_check.py`
   already used. Seen to fail before shipping.
2. r340's Verification check 2 took `tail -1` -- the OLDEST add of
   `WORKFLOW_ERRATA.md`. After the mid-build reopen that reaches past the live
   file to the deleted one, so the check passes on a file that no longer
   exists. Now `head -1`. **I added the reopen rule this morning and left the
   check that reads the file's history stale in the same file.**
3. **r320's gate block invoked only ONE of its two scripts.** Step 320 is
   `r320_coverage_check.py` AND `r320_dropped_listings.py`; the block headed
   *The gate* ran the first. A builder following it ran half the step, then had
   to find the other script by itself and invent its argument -- which is
   exactly how the wrong directory got passed. The block now runs both, with
   `OCR=<tmp>/ocr/out` spelled out and `NOT <tmp>/ocr` beside it.

**The script was not the hole; the instruction was.** A gate documented as one
command when it is two will be run as one command, and the half left out has no
advocate. Fix 1 makes the mistake loud, fix 3 makes it unlikely.

**And it was caught by the builder re-reading its own report, not by any gate.**
SH8608 volunteered the correction with nothing prompting it, after the step was
reported, committed and signed off -- the third time in one day it has
contradicted something already in writing. The sibling's refusal
(`exit 2 CANNOT RUN`) was the clue, which is an argument for every check in the
pair refusing identically: a check that is loud makes its quiet neighbour
visible.

## Harvest of SH8606's and SH8608's SECOND errata files -- 2026-10-17

Both issues completed today, so this harvest is the one r340 actually
describes: *once the issue is COMPLETE*. Six entries, three of which were
already applied during the day as they surfaced in the builders' messages:

| entry | disposition |
|---|---|
| SH8608 340 — nothing says the build reopens its errata file after a mid-build harvest | applied 759eecac (the reopen is the HARVESTER's job) + a983da1d (check 2 is stated, not claimed, after a reopen) |
| SH8608 320 — `r320_dropped_listings.py` reports 0 on a directory with no OCR output | applied 935d1c97, all three parts: the script exits 2, the gate block runs BOTH scripts, and it names `<tmp>/ocr/out` |
| SH8606 330 — a THEIRS applied outside the issue renumbers the pair and the vocabulary cannot say so | applied aa63000c (`APPLIED`, and the obligation to tell builds in flight), completed here: `verify`'s failure text now names the cause |
| SH8606 150 — the worklist asked for a crop of a listing that was on the disk | r150 applied e392223f; completed here — **r170 now carries the cross-reference**, because r170's sentence is what sends a listing to the worklist and r150's new questions were invisible from there |
| SH8606 150 — an uncaptioned figure the PROSE numbers was listed as `-0` | applied here: *the print includes the body text*. A prose-numbered figure takes that number, goes at the first prose reference, and carries no `<figcaption>` |
| SH8608 330 — "re-diff and remap by content" has no tool | **recorded, not built.** See below |

**The r330 remap tool is the one thing deliberately left undone.** SH8608's
entry is specific — the subcommand's inputs, what it must rewrite, what it must
print — and the cost is measured: ~25 commands and a hand-written difflib
script across three pairs, with a matcher that lost the last D block of each
diff to a regex edge case all three times. It is also not a one-issue problem:
**step 150 runs after 330's body whenever crops arrive after PAUSE 2, which is
the normal order**, so every figure-carrying reprint pair needs this remap, and
SH8605 hit it too. A tool written against three pairs of one issue would be
fitted to them. It should be written when the next issue gives it a second
body of evidence.

**What this harvest confirms about the fix made this morning.** The reopened
files were worth reopening: four of the six entries are from AFTER the
mid-build harvest, and two of them -- the hollow 320 gate and the 330 vocabulary
gap -- are defects in the rules' own instruments. Had the files stayed closed,
those would have reached SH8607 intact.

**And the two builders' entries differ in a way worth noting.** SH8606's say
what the rule says, what it did, what was actually true and what it cost, then
propose replacement wording specific enough to paste. SH8608's do the same and
add the operator detail that makes a tooling gap actionable -- the exact
commands, the edge case its own matcher hit, and why a cheaper fix would have
been wrong. Both are harvestable without a conversation, which is the standard.

Per r340's lifecycle both files are now deleted. SH8606's second file is
recoverable at 3ddc87e2's parent, SH8608's at c86e5b54's parent; the first
files remain recoverable at 0433909e and 888d8d3d.

### The lead-slot exception keys on the one thing that can lie

Owner, 2026-10-17, hours after the exception was added: *"cropping
SH8606/108-0 was a mistake, remove file and dont img src it."*

`108-0.png` is a cartoon -- a boy with his arms spread before a computer,
*"Deine Manieren lassen ganz schön zu wünschen übrig!"*, the machine answering
*"Rüülps!"* -- with no printed caption, never referred to by the prose. It was
placed a year ago (f39d844e) as the article's lead image. **It sits at line 223
of 532**, between two paragraphs on interrupt handling.

So the owner's removal CONFIRMS *EXCEPT IN THE LEAD SLOT*, which already says a
filler "dropped into leftover space further down" stays omitted. What it
exposes is how the cartoon got past that test: **the exception keys on the
`<page>-0` suffix, and the suffix is a claim that can be wrong.** A cartoon
named `-0` walks straight through a test that asks whether it is named `-0`.

This is *THE SUFFIX FOLLOWS THE PRINT* meeting the lead-slot rule, and the two
had not been read against each other. Every other use of a suffix in this file
is descriptive -- it records what the print says. This one is **load-bearing**:
it is the single place where the filename decides whether a picture is
published at all. The section now says to check the position on the page and
names the trap explicitly.

**The age of the error is the point.** It survived a full build, a placement
run, r150's five verifications and an owner review of the issue, because every
one of them read the name. It took the owner looking at the published page.

> **ERRATUM on this file's own commits, 2026-10-17.** `f6954f8b` is titled
> *"Harvest SH8606's and SH8608's second errata files, and delete them"* and
> its message lists three rule changes. **It contains only the two deletions.**
> I ran `git rm` / `git add` for the errata files and then a bare
> `git commit -m`, which commits what is STAGED -- so the three modified rule
> files, which were unstaged, were silently left out while the message went on
> describing them. The r150 half was then swept into `8f17fb87`, a commit about
> something else, and r170 and `r330_reprint_compare.py` stayed uncommitted
> until 64er_SH8606 noticed them in the tree and said so.
>
> So the real landing places are: r150's *the print includes the BODY TEXT* in
> `8f17fb87`; r170's cross-reference and r330's `verify` text in the commit
> below. `f6954f8b`'s message overstates it and is left standing, because a
> rewrite would break the hashes two builders have already quoted back.
>
> **The rule this breaks is already in r000** -- *commit by pathspec while a
> sibling builds* -- and I broke it in the safe-looking direction. Pathspec
> protects against sweeping a sibling's work IN; the same discipline is what
> keeps your own work from being left OUT, because `git commit -m` with
> nothing named commits the index, not your intent. **Name the paths every
> time, including when you think nothing else is staged.** Caught by a builder
> reading the tree, which is the fourth correction a builder has made to this
> supervisor today.

## Harvest of the THIRD errata files -- 2026-10-17, after both issues were published

Both issues were reopened once each after closure, for an owner correction the
chain had no way to catch, and each builder opened a third errata file with one
LIVE entry. Both are harvested here and deleted.

| issue | entry | applied |
|---|---|---|
| SH8606 | a delivered `-0` is not evidence of the lead slot, and the lead-slot exception keys on that suffix | r150, two places: *-0 IN THE NAME IS NOT EVIDENCE* (8f17fb87) and, here, *A CROP THAT ARRIVES IS PLACED* gains the re-judging of crops already in the directory |
| SH8608 | a headline prefix set as reversed type on a tint band is lost at OCR, and nothing downstream looks for it | r080, the unconditional lead-image look (cf729c59, d8b540a5) and, here, how a recovered prefix JOINS the headline |

**Each entry had a second half I had not applied when I patched the rules from
the builders' messages.** I harvested what the message in front of me said and
stopped there; the written entries went further, and the further half was the
better half in both cases:

- SH8606's: step 150 placed the 17 new crops **without re-judging the 62
  already in the directory**, which is exactly how a 2025 cartoon survived into
  a 2026 publication. I had fixed how a `-0` is READ and not when the old ones
  are LOOKED AT. The check is one line per pre-existing `-0` file: its placed
  line number against the article's length.
- SH8608's: having found a lost prefix, the chain still had to be told how to
  JOIN it — the print makes the distinction with a typeface and HTML cannot.
  The corpus answers it: colon for a standing rubric (91 titles), dash for a
  program or product name (221), and en-or-em from the ISSUE's own titles
  rather than the corpus average, which is near even.

**So a message is not an errata entry.** The entry is written against the rule,
quotes what it says, and names what it cost; a message to the supervisor is
written to settle the thing in hand. Harvesting from messages as they arrive
felt efficient all day and dropped half of two findings. **Read the file, even
when you think you already know what is in it.**

**Both reopenings were worth it on their own terms.** Each cost one commit and
each produced a rule change that applies to every future issue -- which is the
argument for r340's reopen rule, written this morning after a mid-build harvest
left SH8608 with nowhere to write.
