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
