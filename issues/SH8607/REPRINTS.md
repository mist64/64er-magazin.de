# Reprint leads — SH8607 (step 330, Step 0)

`reprints.txt` (step 140, confirmed against the page there) lists: 119 Checksummer → 8603/checksummer, 120 MSE → 8602/mse, and 6 Memory Map mit Wandervorschlägen → the eighteen `memory_map` parts 8411 … 8606 (a MERGED reprint of the whole course). Those twenty rows do not go back through step 1. This file **extends** that list with the leads Step 0's own pass adds; every row marked *new lead* is a **hypothesis** for step 1 to confirm or refute against both printed pages.

Measured 2026-10-23 after step 290, over every article in `issues/` except SH8607 itself (scratch: `/Users/mist/DNB/SH8607/tmp/agent330s0/` — `step0.py`/`step0.txt` whole-article + per-block + table cells, `mm_blocks.py`/`mm_blocks.txt`/`sections.txt`/`perpart.txt` the Memory Map per-block map, `mm_runs.py`/`mm_runs.txt` the per-part run measure):

- **whole article**: 8-word shingles of the normalised text (`<pre>`/`<code>`, comments, `futureteufelchen` and `nachdruck` excluded; lower-cased, line-end hyphens joined). `min` = shared / the smaller shingle set, `ours` = shared / ours, `theirs` = shared / the original's. Whole-article threshold ~0.5; partials ≥ 0.4 listed.
- **per block** (*Step 0's ~0.5 overlap threshold misses a MERGED reprint*): blocks extracted with `r330_reprint_compare.extract`; a block of ours matches a candidate when ≥ 50 % of its shingles occur there; `run` = the longest run of consecutive matching blocks, scored against the SHORTER article; read above ~0.4.
- **table cells**: identical `<td>`/`<th>` texts (≥ 6 chars, not bare numbers) — the shingle passes cannot see a table.

Direction: every claimed original below is older by cover date than Sonderheft 7/86 (latest: 8606 = 6/86), so no `REVERSED` candidate. SH8608/162 (Impressum, 8/86) is the only younger file that scores, and it is not a lead.

## Leads

| this issue | claimed original | score | note |
|---|---|---|---|
| `119 Checksummer 64 V3.html` | 8603/55 | 0.92 | confirmed-by-140 (`8603/checksummer`). **Standing house text** — compare, no credit (owner 2026-10-06). The Sonderheft copies score higher (SH8606/6 1.00, SH8604/93 0.99, SH8605/135 0.98, SH8602/6 0.95); 8603/55 is the MONTHLY original. 8508/53 »Checksummer 64 – Neu« (0.66) is the older, different version |
| `120 MSE – Abtippen sicher und leicht gemacht.html` | 8602/57 | 0.89 | confirmed-by-140 (`8602/mse`). **Standing house text** — compare, no credit. SH8606/7 0.99, SH8602/7 / SH8604/94 0.95; the older monthly 8505/55 scores the same (0.89; ours 0.82 vs 8602/57's 0.87) — 140's lead stands, step 1 does not re-open it |
| `6 Memory Map mit Wandervorschlägen.html` | 8411/133 | 0.81 | confirmed-by-140, MERGED — Teil 1; score for every part row = `theirs` over prose (`mm_runs.txt`); see *The Memory Map* below |
| `6 Memory Map mit Wandervorschlägen.html` | 8412/132 | 0.80 | confirmed-by-140, MERGED — Teil 2 |
| `6 Memory Map mit Wandervorschlägen.html` | 8501/126 | 0.85 | confirmed-by-140, MERGED — Teil 3 |
| `6 Memory Map mit Wandervorschlägen.html` | 8502/150 | 0.74 | confirmed-by-140, MERGED — Teil 4 |
| `6 Memory Map mit Wandervorschlägen.html` | 8503/144 | 0.65 | confirmed-by-140, MERGED — Teil 5 |
| `6 Memory Map mit Wandervorschlägen.html` | 8504/144 | 0.70 | confirmed-by-140, MERGED — Teil 6 |
| `6 Memory Map mit Wandervorschlägen.html` | 8506/120 | 0.77 | confirmed-by-140, MERGED — Teil 7 |
| `6 Memory Map mit Wandervorschlägen.html` | 8507/140 | 0.88 | confirmed-by-140, MERGED — Teil 8 |
| `6 Memory Map mit Wandervorschlägen.html` | 8508/129 | 0.82 | confirmed-by-140, MERGED — Teil 9 |
| `6 Memory Map mit Wandervorschlägen.html` | 8509/112 | 0.87 | confirmed-by-140, MERGED — Teil 10 |
| `6 Memory Map mit Wandervorschlägen.html` | 8510/133 | 0.86 | confirmed-by-140, MERGED — Teil 11 |
| `6 Memory Map mit Wandervorschlägen.html` | 8511/145 | 0.87 | confirmed-by-140, MERGED — Teil 12 |
| `6 Memory Map mit Wandervorschlägen.html` | 8512/146 | 0.89 | confirmed-by-140, MERGED — Teil 13 |
| `6 Memory Map mit Wandervorschlägen.html` | 8601/128 | 0.85 | confirmed-by-140, MERGED — Teil 14 |
| `6 Memory Map mit Wandervorschlägen.html` | 8602/145 | 0.89 | confirmed-by-140, MERGED — Teil 15 |
| `6 Memory Map mit Wandervorschlägen.html` | 8603/122 | 0.87 | confirmed-by-140, MERGED — Teil 16 |
| `6 Memory Map mit Wandervorschlägen.html` | 8605/154 | 0.90 | confirmed-by-140, MERGED — Teil 17 |
| `6 Memory Map mit Wandervorschlägen.html` | 8606/145 | 0.83 | confirmed-by-140, MERGED — Teil 18 (Schluß) |
| `6 Memory Map mit Wandervorschlägen.html` | 8606/92 | prose 0.00; cells 209/240 | **new lead (hypothesis)**: the closing address table »Die Bedeutung der Speicherzellen 0 bis 1023, nach Funktionen geordnet« (SH pp 63-65, 106) against 8606's »64'er Extra: Speicherzellen 0 bis 1023 nach Funktionen geordnet« (`extra`, pp 92-93): 327 vs 326 `<tr>`, 209 of our 240 distinct cells identical. Table-only reuse; not part of the course series. Step 160's LOG already used it as a candidate reading only (»the page wins in ~40 places«) |
| `159 Tips und Tricks für Basic-Programmierer.html` | SH8605/90 | 0.15; cells 147/201 | **new lead (hypothesis)**: Tabelle 2 »Alle Register des Video-Chips auf einen Blick« (13 register-description cells at 1.00); no shared prose. SH8605 recorded its own 90 as table-only PARTIAL ← 8404/119 |
| `159 Tips und Tricks für Basic-Programmierer.html` | 8404/119 | 0.04; cells 113/201 | **new lead (hypothesis)**: the same VIC-II register table in its earliest MONTHLY printing; SH8605/90 shares more cells (147 vs 113). Step 1: which printing the table follows. Table-only reuse either way |

`178 Impressum.html` scores 0.95 to SH8608/162, 0.89 SH8606/178, 0.84 SH8604/162, 0.83 SH8605/194 and 0.60-0.75 to the older Sonderhefte: the shared masthead, boilerplate, not an article reprint — not a lead, no row (kept out of the table so `verify` does not read it as one).

## The Memory Map — a merged reprint of all eighteen parts

**Parts 6 and 15 are in the corpus under `memory_map`, and the brief's premise was wrong.** No Memory Map ran in 8505 or 8604 (neither directory has a Memory Map article; `grep -il 'wandervorschl'` finds nothing in them). The numbering is printed in the files: 8504/144 is »Teil 6« (`64er.index_title` »Memory Map mit Wandervorschlägen (Teil 6)«), 8506/120 »(Teil 7)«, 8601/128 »(Teil 14)« (`toc_title`), 8602/145 »(Teil 15)«. So the eighteen lines of `reprints.txt` are exactly Teil 1-18, and our standfirst says the same: »eine zusammenhängende Wiedergabe einer Serie von Aufsätzen, die im 64'er, Ausgabe 11, November 1984 angefangen hat und sich in 18 Folgen bis Ausgabe 6, Juni 1986, hinzog.« The course skipped 5/85 and 4/86.

Whole-article score is meaningless here by construction (`ours` 0.03-0.07 per part); `theirs` is the signal (0.65-0.90 above). Per part, against our 1452 prose blocks of ≥ 8 words:

| part | original | our prose blocks matched | longest run (/shorter) | its blocks found in ours | SH8607 sections it supplies |
|---|---|---|---|---|---|
| 1 | 8411/133 | 80 | 16 (0.18) | 73/88 | Vorspann, Adresse 0-2 (VC 20 and C 64), RAM-ROM-Umschaltung, Kassettenrecorder; Texteinschub 1, 3 |
| 2 | 8412/132 | 61 | 25 (0.34) | 50/73 | Adresse 3-17; Texteinschub 4, 5 (8412's Tabelle 1 and 2 — corrected at the body run, 330B) |
| 3 | 8501/126 | 89 | 26 (0.25) | 87/102 | Adresse 18-44 (incl. »Das billigste editierfähige Textverarbeitungssystem«); Texteinschub 6, 7 |
| 4 | 8502/150 | 38 | 9 (0.22) | 30/41 | Adresse 45/46; Texteinschub 8, 9 |
| 5 | 8503/144 | 70 | 16 (0.16) | 68/98 | Adresse 47-56; Texteinschub 10, 11 |
| 6 | 8504/144 | 58 | 18 (0.25) | 57/73 | Adresse 57-79; Texteinschub 12 |
| 9 | 8508/129 | 69 | 44 (0.53) | 70/83 | Adresse 80-143; Texteinschub 13 |
| 7 | 8506/120 | 68 | 25 (0.32) | 64/79 | Adresse 144-152; Texteinschub 14 (ST-atus) |
| 8 | 8507/140 | 61 | 17 (0.26) | 58/65 | Adresse 153-157; Texteinschub 15 (Dynamische Tastenabfrage) |
| 10 | 8509/112 | 96 | 27 (0.25) | 90/108 | Adresse 158-182; Texteinschub 16, 17, 18 |
| 11 | 8510/133 | 97 | 23 (0.22) | 96/106 | Adresse 183-198; Texteinschub 19, 20 |
| 12 | 8511/145 | 50 | 27 (0.44) | 52/61 | Adresse 199-207; Texteinschub 21 |
| 13 | 8512/146 | 80 | 28 (0.33) | 77/86 | Adresse 208-255; Texteinschub 22, 23 — **and Texteinschub 2 (Low-/High-Byte), moved forward into part 1's territory** (corrected at the body run: Texteinschub Nr. 4 »Zeiger, Vektoren und Flaggen« is 8412's Tabelle 1 and Nr. 5 is 8412's Tabelle 2, 330B — not Teil 13) |
| 14 | 8601/128 | 68 | 24 (0.30) | 70/80 | Adresse 256-645; Texteinschub 24, 25 |
| 15 | 8602/145 | 87 | 26 (0.26) | 88/100 | Adresse 646-658; Texteinschub 26, 27 |
| 16 | 8603/122 | 79 | 21 (0.28) | 65/76 | Die RS232-Schnittstelle, Adresse 659-673; Texteinschub 28, 29, 30 |
| 17 | 8605/154 | 85 | 24 (0.24) | 96/101 | Adresse 674-787, Speicher für die Register des Mikroprozessors; Texteinschub 31, 32, 33 |
| 18 | 8606/145 | 97 | 25 (0.24) | 95/106 | Adresse 788-1023; Texteinschub 34, 35, 36 |

The run measure stays below 0.4 for 16 of the 18 parts because the reprint interleaves: re-worded address headings (`Adresse 80 — 82 ($50 - $52)` → `Adresse 80 bis 82 ($50 bis $52)`), Texteinschübe renumbered 1-36 across the course (each monthly part numbered its own from 1), table cells between prose blocks. The `its blocks found in ours` column (0.68-0.95) is the merged-reprint signal; every part is far above anything a non-reprint reaches.

**Three leads sit on a shared page** (`resolve` exits 2), so the body run's LOG needs a `REJECTED` line for the other candidate: 8501/126 (also the last page of `8501/122 Müllabfuhr im Computer- Die Garbage Collection.html`, 122-126), 8504/144 (last page of `8504/138 Assembler ist keine Alchimie — Teil 8.html`), 8507/140 (last page of `8507/132 Dem Klang auf der Spur (Teil 7).html`). The other fifteen part leads and 8603/55, 8602/57, 8606/92, SH8605/90, 8404/119 resolve to one article.

**Order differs from the monthlies.** In print the course jumped: Teil 7 (8506) treated 144-152, Teil 8 (8507) 153-157, and Teil 9 (8508) went back for 80-143 (8508 says so: »Ab dieser Speicherzelle wurde der Kurs irrtümlicherweise … im 64'er, Ausgabe 6/85, weitergeführt«). SH8607 runs strictly by address, so 8508's block sits before 8506's. Texteinschub 2 comes from Teil 13; Texteinschub 4 and 5 are 8412's Tabelle 1 and 2 (body run, 330B — Step 0 had put Nr. 4 under Teil 13).

**Coverage.** 56,395 words in 3,882 blocks; prose 51,834 words, of which **89.1 %** sit in blocks matched ≥ 0.5 to one monthly part. Of the rest, 1,974 words are re-edited blocks (0.2-0.5 matched) and 1,085 words are unmatched (< 0.2). Table cells (4,561 words) are matched only 20 % by shingles — tables are re-set and the cell pass is the measure for them.

**New to this printing** (no source in the corpus):

- the Vorspann's second to sixth paragraphs (»Dieser Kurs ist eine zusammenhängende Wiedergabe …«, the thanks to readers, the note on the lists);
- the section »Inhaltsverzeichnis der Texteinschübe und Tabellen« (379 words, 2 % matched);
- bridging and cross-reference sentences re-pointed to the new Texteinschub/Bild/Tabelle numbers (e.g. »Der Effekt … wird im Texteinschub Nr. 7 …«, »Bild 11 zeigt …«, »In Listing 2 (Seite 63) …«);
- table footnotes and captions in the RS232 part (»Tabelle 11. Die Bedeutung der einzelnen Bits im RS232-Steuerregister«, »Tabelle 13. Realisierbarkeit der Schnittstellen …«);
- the closing paragraphs at Adresse 828-1023 (»Die Kenntnis der Inhalte der Speicherzellen des Kassettenpuffers …«, »Detaillierte »Wandervorschläge« müßte ich erst zusammenstellen …«);
- the address table 0-1023 is not from the course parts but matches 8606/92 (new lead above).

**Dropped from the monthlies** (3,889 words of their prose under 0.2 in ours): each part's standfirst, temporal framing (»Das nächste Mal …«, »In der letzten Folge …«), reader-letter remarks, the 8503 »in eigener Sache« note, 8601's Literatur list, 8606's farewell. The monthly corrections (8504's Dr. Beyer improvements, 8506's »Korrektur zu Adressen 65 bis 66«, 8606's Tape-Header Nachtrag) are not present as such — whether SH8607's text carries them worked in is a step 1 / r300 question (*a reprint missing its original's erratum*), not settled here.

## Not leads

- `178 Impressum` — masthead, above.
- `147` ← 8502/134 (15 cells: Kernal routine names `ramtas`, `setlfs` …), `66` ← SH8608/57 (6 cells: register-display labels; SH8608 is younger), `86` ← SH8601/125 (8 cells: ROM routine labels), `139 Programmierhilfe` ← SH8606/73, 8607/50 (0.01), `144` ← 8609/124 (0.01), `164` ← 8602/59 (0.00): stock names and phrases, no shared wording.
- `3`, `73`, `84`, `107`, `110`, `118`, `122`, `124`, `125`, `126`, `128`, `130`, `139 Garbage 64`, `142`, `146` — no candidate sharing ≥ 5 shingles, no block, no table above noise: original to this issue by this measure.

## Claimed original content
Everything in SH8607 other than the rows of *Leads* is, by this measure, original to the issue.

## Credits (step 7) — decided at the body run, not here

- **Standing reprints 119 (`checksummer`), 120 (`mse`)**: compared, recorded CONFIRMED/PARTIAL in LOG.md, **never credited** (*A REGULARLY REPRINTED ARTICLE GETS NO CREDIT BOX*, owner 2026-10-06).
- **6 Memory Map**: the rule says a `CONFIRMED` or `PARTIAL` reprint links to its original(s); a multi-part series merged into one reprint is `PARTIAL`, »one row and one diff **per original**«, and the credit opens `Teilweiser Nachdruck aus`, names **every** original the LOG gives a row for with the part re-set after each, and says what the rest is. Credit applies only »where the BODY TEXT is substantially reprinted« (owner 2026-10-07); table-only or single-item reuse is recorded, not credited. By this measure the body text is substantially reprinted (89 % of the prose). Whether 8606/92 (table only) is named in that credit, and the exact wording, is the body run's decision from the verdicts.
- **159**: if step 1 finds PARTIAL, it is table-only reuse → by the rule recorded, not credited, declared on a `Recorded, not credited:` line (written at the body run, not here).

Recorded, not credited: `159 Tips und Tricks für Basic-Programmierer.html`
