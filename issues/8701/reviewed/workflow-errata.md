# 8701 — the build's errata, and where each one went

COPIED INTO reviewed/ 2026-11-03, at r340 sign-off. The working file,
`issues/8701/WORKFLOW_ERRATA.md`, is LEFT IN PLACE for the owner to read: a
previous harvest deleted two such files before the owner had seen them and
they had to be restored (65ac71b9, *"these files come back unchanged so they
can be read first, and will be deleted again when the owner is done"*). Delete
the working copy when the owner is done with it; this record stays.

**ALL ENTRIES HARVESTED.** Every one reached its rule, and the narrative is in
`tools/img/scan2ocr/rules/HARVEST.md` under the 8701 headings — fifteen
numbered findings across four sections. The rule and tool changes are in these
commits:

    cc419767 / ebc5bc5b / e895d31b   r000 three deliverables; r005 backing; K at the fold
    d79af746 (was b0db3c9a)          the 8701 harvest: twelve findings, five dead or lying checks
    aff50cd1 (was 78a810ad)          r240's three, r320's two sweeps, r300's default
    a5f98838 (was 7bdc09ea)          r005 bed-strip floor 2 mm -> 0.5
    5e99aeef (was 127a19ab)          r240 adjudicated banner shape
    3f274f1d (was 408ae936)          r330 --partial, verify after 150
    79e837fb (was cbcdc7c3)          r330 --partial was hiding MOVED blocks

## What this build was actually about

Five checks were found keyed on the belief they were meant to question —
r020's kept count, r030's unexplained-loss count, r005's `unknown` fraction,
r050's escape test, and the skew residual. A sixth, r300's aside check, held a
literal BACKSPACE where `\b` was meant and had therefore **never matched
anything at all**; repaired, it found 4 asides with no trailer. r230, r260 and
r270 printed FAIL and exited 0; r250 and r300 failed on correct output; r120
check 4 asserted on what its own table says to ignore; r240 had three that
could not pass; r320 claimed coverage it never attempted.

Two owner deliverables came back "nothing to do" — every mark ruled the plate,
every Futureteufelchen declined — and that is recorded as the finding it is:
we kept asking *is this really an error?* where the owner asks *is this ours to
say?*

## The three the build found that control did not

- the clip punches: 74 of 192 pages filled fewer than six, not the 18 reported;
- `--partial` hiding a MOVED block, which would have shipped a wrong byline;
- step 150 renumbering 330's D numbers, which the gate then caught.

## The Jahresinhaltsverzeichnis is deliberately absent

Owner, 2026-11-03: *"remove jahresinhaltsverzeichnis. it's not useful, since we
already have a digital index that is actually linked. pretend the article
doesn't exist."*

`95 Jahres-Inhaltsverzeichnis '86.html` is deleted. It held the printed 1986
index as a 580-row table — 557 entries, 22 Rubrik rows — typeset at step 160
and verified at step 280 against the print, and cross-checked by control
against `Jahresinhaltsverzeichnis 1986.csv`, an independent transcription of
the same pages: same entry count, 99.4 % title agreement, and the three
disagreements all resolved IN THE TABLE'S FAVOUR. The work was correct; the
article is simply redundant beside a searchable index that links to the
articles themselves.

**Consequences, recorded so no gate chases them:**

- pages **95-98** are now unclaimed. `adjudicated.txt` carries `omitted-95 4`.
- the printed contents lists `95  64'er-Extra  Jahresinhaltsverzeichnis 1986`,
  so r100's coverage check will report NO ARTICLE for it. That is correct and
  expected: the entry IS printed and we chose not to publish it.
- the PDF is unaffected and must stay so. It is a facsimile of the printed
  issue; the pages are in it because the magazine has them.

**Two published issues carry the same rubric and were NOT touched**, because
the instruction was about 8701: `8504/84 Jahresinhaltsverzeichnis 1984_85` and
`8602/85 Jahresinhaltsverzeichnis`. If the reasoning applies to them it is the
owner's call, not a tidy-up.

## After the sign-off, 2026-11-03: what the owner and the re-checks found

Each entry is a finding, not a narrative; the rule it went into is named.

- **A declined-crop list copied from the LOG was wrong on four of six.** Step 150
  recorded "70-1, 12-x3, 49-x, 50-3, 144-00, 156-0" as declined. Rebuilt from the
  HTML, 12-x3, 49-x, 50-3 and 144-00 were delivered under other names (10-5, 49-0,
  55-3, 28-4) and are placed. The undelivered rows are 34-2 (typeset stand-in),
  69-0, 70-1, 156-0, 178-0. A disposition list made at a moment is rebuilt from the
  artefact, never copied forward.
- **Panel text labelled `noise` was carried by nothing (p33 Bild 3-5).** The owner
  cut the drawings only; the pin tables inside the same panels were figure-noise to
  step 020 and so neither crop nor HTML. r320's noise sweep printed one of the
  three and nobody read it; the other two fell under its 12-word floor. Fixed by
  typesetting; an under-crop sweep over all 111 rows found no other case (r320).
- **A printed contents entry made an article (p44).** The yellow box "99 Spiele
  für Ihre Meinung" was split out because the contents list it; its heading is
  section-size (124 px against a 524 px banner). Merged as an aside (r080).
- **a/b followed the bigger headline, not the reading order (p8, p144).** Both
  shared start pages were lettered banner-first; the left column comes first.
  generate.py sorts on the letter, so the issue sequence was wrong (r080).
- **A declined figure took instructions with it (p72 Bild 1).** The 105-word
  caption is typing instructions; placed as text without the image, as 8610 does
  (r150).
- **A reprint difference changed meaning without changing count (70 ← 8610/76).**
  Placing that caption turned D-001 from CROP into PRINT; verify passed on the stale
  entry until it was re-read (r330).
- **The window fit hides a sheet-level step (pending the owner).** The wordmark-to-
  fold offset is bimodal, split at the centre spread (pages 1-96 vs 97-192, about
  4.4 mm). One fit per parity sits between the modes; 77 of 98 comparable pages are
  ≥ 0.5 mm off the paper. The fit's recorded `unknown` share did not flag any of
  the bad pages. A gate on master gutter vs certified hole fold (≤ 0.5 mm) catches
  all nine the owner and the analysis found; a colour-difference gate does not
  (p030 and p092 read nothing). **Owner, 2026-11-03: 8701 only, x from the
  certified hole fold, y unchanged** — "the fold is the more important signal,
  because cutting wrong there either loses information or lets the other sheet
  show through" (r005, *Where the window is pinned*).
- **The same step is in the published 8611 and 8612, measured, and NOT acted
  on** (owner: old issues are re-done only in a pass the owner starts).
  For that pass, so it need not be rediscovered:
  - source: the cut-time sidecars `/Users/mist/DNB/8612/tmp/geometry/` (200
    pages + `fit.json`, fit even S 544 B 6888, odd S 4416 B 6884) and
    `/Users/mist/DNB/8611/tmp/geometry/` (192 + `fit.json`); both `binding:
    spread`, pairing k <-> 201-k and k <-> 193-k;
  - check: 16 pages (4 per half per issue, both parities, 6-hole folds)
    re-measured from the 2400 dpi scans with r005's `level_page` and
    `measure_geometry`, unchanged, outputs to scratch: 0.00 mm against the
    sidecars;
  - set: hole fold, template >= 5, 6-14 mm from the frame edge, wordmark found;
  - result, logo-placed window past the fold, median mm (sd), front | back:
    8612 even -0.18 (0.88) | +3.38 (0.98), odd -0.45 (1.22) | +3.03 (1.32);
    8611 even -0.37 (1.07) | +2.97 (0.98), odd -0.22 (1.12) | +4.23 (1.25);
    8701 even -0.64 (0.86) | +3.72 (0.69), odd -0.32 (0.96) | +4.30 (1.09).
    Raw wordmark-to-fold: ~187.3 mm front, ~183.5 mm back in all three.
  - 8609 and 8610 were not measured.
  - per-page data and histograms: `/Volumes/S/tmp/trim_study_86xx/`
    (offsets.json, offset_hist_*.png) -- scratch, gone at close; the numbers
    above are the record.
