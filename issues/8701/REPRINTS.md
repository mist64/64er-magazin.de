# 8701 — reprint leads (step 330, Step 0)

No `reprints.txt`: step 140 ran no overlap pass on this monthly (its LOG entry
records ids only), so every row below comes from this step's own pass and is
a **hypothesis** for step 1 to confirm or refute against both printed pages.

## How the leads were found

Measured 2026-11-02, after step 300 and before 325, over every article in
`issues/` except 8701 itself (54 articles of ours against the rest of the
corpus; script and full output: `/tmp/64er_8701_r330s0/step0.py` /
`step0.txt`, per-pair detail `detail.py`). Text taken with
`r330_reprint_compare.py`'s own extractor, so `<pre>`/`<code>`, comments,
`futureteufelchen` and `nachdruck` are excluded and line-end hyphens joined
the same way the diff will join them; words lower-cased.

- **whole article**: 8-word shingles. `ours` = shared / our shingles,
  `theirs` = shared / its shingles (the merged-reprint signal), `min` =
  shared / the smaller set. Whole-article threshold ~0.5.
- **per block** (*Step 0's ~0.5 overlap threshold misses a MERGED reprint*):
  a block of ours matches when ≥ 50 % of its shingles occur in the candidate;
  `run` = longest run of matching blocks / the shorter article's block count,
  read above ~0.4; `strong` = blocks at ≥ 80 %. Every block match was read.
- **table cells**: identical `<td>`/`<th>` texts (≥ 6 chars, not bare
  numbers) — the shingle passes cannot see a table.
- **listing lines** (side measure only): identical `<pre>` lines ≥ 20 chars.
  r330 does not compare listings; recorded so nothing is hidden.

Separation: one whole-article reprint (70, 0.94). Everything else that is
not house furniture is below 0.10 whole-article; the Leserforum reprints
the reader QUESTIONS it answers, each a single block, found only by the
per-block pass (14 below).

Direction: 8701 is the youngest issue in the corpus; every claimed original
is a 1986 monthly (latest 8612), so no `REVERSED` candidate. The Leserforum
question blocks are self-dated: each is followed by `Ausgabe 7/86`,
`8/86`, `10/86`, `11/86` (the Amber question, from 12/86, carries no such
line).

## Leads

| 8701 article | claimed original | overlap (min / ours / theirs; run; cells) | status |
|---|---|---|---|
| 70 Checksummer V3 und MSE | 8610/76 | 0.94 / 0.94 / 0.84; run 1.00, 31/37 blocks, strong 28; cells 56/57 | **new lead (hypothesis)**, whole-article shape. **Standing reprint** (`64er.id` `checksummer` on both sides) — compare, no credit (owner 2026-10-06). The Checksummer table cells also occur in every other Checksummer page (SH8605/135 57, SH8607/119, SH8606/6, 8603/55 56, SH8604/93, SH8602/6 55) with no shared prose: those are the older Checksummer-only text, not this MSE-combined one; 8610/76 is the only prose match |
| 14 Leserforum | 8607/13 + 8608/17 + 8610/14 + 8611/16 + 8612/16 | 8607/13: 0.07 / 0.07 / 0.07, 4 blocks (»Fragen zum C 128« 0.70, »SAVE-/LOAD-Anzeige für 1571?« 1.00, »Spiel-Probleme« 0.85, »Technischer Defekt?« 0.86); 8608/17: 1 block 1.00 (»Ärger mit dem C 128«); 8610/14: 1 block 1.00 (»Woher bekommt man ein Copyright?« q1; q2/q3 are under 8 words and cannot score); 8611/16: 1 block 0.86 (»Änderungen im C 64-Kernel«); 8612/16: 1 block 0.85 (»Die neun Prinzen von Amber«) | **new lead (hypothesis)**, PARTIAL shape: only the quoted reader questions are reprinted, answers are new. One diff per original, restricted to those `<div class="q">` blocks. Visibly re-edited already (8607 numbers the questions `(1)…(4)` and runs several letters together; 8612's Amber question is longer, the »THROW STATUE« clause cut), and two differences to read on the page: author »Werner Stehlow« (8701) vs »Werner Strehlow« (8607); »Wie kann man aber nun« vs »nun aber« |
| 14 Leserforum | 8609/15 | 1 block 0.69 (»Spiel-Probleme«) | **new lead (hypothesis)**: 8609/15 already reprinted and answered the same 7/86 Springvogel question (re-worded: »Turbo-Tape«, »dagegen tun«). A third printing, not the original — 8607/13 is. Step 1 decides whether it is diffed or only noted |

## Not leads

- `187 Impressum` — 0.95 to 8611/187 and 8612/195, 0.79–0.93 to every
  earlier monthly's: the shared masthead.
- `174a Wir suchen die Anwendung des Monats` and `174b Einmal im Monat gibt
  es 2000 Mark für das Listing des Monats` — 1.00 to the same house ad in
  8602–8612 (8+ printings each; `64er.id` `anwendung_des_monats` /
  `listing_des_monats`). Recurring house furniture like the masthead, not an
  article reprint. Uncertain: r330 names only `mse`, `checksummer`,
  `abtippen` as standing reprints to compare; these are kept out of the table
  on the Impressum precedent, and at 1.00 word overlap only punctuation could
  differ.
- `69 Fehlerteufelchen` ← 8611/158 (ours 0.35, one block), 8611/50, 8611/24,
  8612/68, 8609/71 (8 listing lines): the errata quote the lines they
  correct — rule 300's input (done), and those articles are older.
- `144a Die Axt im Haus... (Teil 6)` ← 8609/130, 8611/156, 8608/48, 8610/49,
  8612/48: one block each, the series' standing disclaimer (»Alle in dieser
  Serie gemachten Anleitungen …«).
- `36 Marktübersicht Monitore` ← 8601/30 (11 cells: prices, row labels; one
  block »Alle Daten beruhen auf Herstellerangaben …«) and 8512/30: survey
  boilerplate, no shared wording.
- `172 Druck-Daten` ← 8608/158 (one block 0.56, the »Wir danken den Firmen
  …« thanks list naming overlapping printers); `178 Auf nach Amerika!` ←
  8602/162 (the »Mitarbeiter der Markt & Technik Verlag AG …« contest
  exclusion); `32 Der Weg zum richtigen Monitor` ← 8512/16 (0.01): stock
  phrases.
- `94 Noch mehr Tips zu Master-Text` ← 8612/188: 5 of 13 identical hex
  patch lines (`ad60 :`, `ad68 :`, `aea8 :`, `aeb0 :`, `b390 :`), no prose.
  The 1/87 patch repeats rows of the 12/86 one; a listing, outside r330.
- `95 Jahres-Inhaltsverzeichnis '86` ← 8602/85, 8504/84 (15 cells: the
  category names); `45 Aus alt mach neu` ← SH8503/142 (12 cells: game
  titles); `153`, `155` ← the 1986 printer tests (15–21 cells: the
  standard data-box labels); `161`, `162`, `163` ← every game review (7–8
  cells: the rating-box labels).
- `8b`, `8a`, `10`, `12`, `16`, `22`, `24`, `26`, `28`, `30`, `34`, `42`,
  `44`, `49`, `50`, `61`, `64`, `66`, `74`, `79`, `83`, `87`, `90`,
  `144b`, `148`, `149`, `156`, `158`, `166`, `167`, `169`, `170`, `176`,
  `185`, `186` — no candidate sharing ≥ 5 shingles, no block, no table or
  listing above noise: original to this issue by this measure (`149` ←
  8502/134 shares 5 shingles and nothing else).

## Step 1 verdicts (body, 2026-11-02)

Each lead read on both printed pages (8701 masters600; the originals from
their 2400 dpi scans in `/Volumes/S/png/<YYMM>/`, because the monthly PDFs
are 150 ppi). Full record: `LOG.md`, `## Step 330 (reprint_compare)`.

- `70 Checksummer V3 und MSE` ← 8610/76: **CONFIRMED**, the same text
  re-set (p70, 72-73 against 76-78). Standing reprint: compared, no credit.
- `14 Leserforum` ← 8607/13, 8608/17, 8610/14, 8611/16, 8612/16:
  **PARTIAL**. Only the quoted reader questions are reprinted, each under
  its own printed source line (»Ausgabe 7/86« etc.); every answer is new.
  8607/13 supplies four (»Fragen zum C 128« question 4, »SAVE-/LOAD-Anzeige
  für 1571?«, »Spiel-Probleme« question 1, »Technischer Defekt?«); 8608/17 »Ärger mit dem C 128«; 8610/14 »Woher bekommt man ein
  Copyright?«; 8611/16 »Änderungen im C 64-Kernel«; 8612/16 »Die neun
  Prinzen von Amber« (no source line printed).
- `14 Leserforum` ← 8609/15: **PARTIAL**, diffed. 8609 is not the original
  but a second printing of the 7/86 Springvogel question (its own source
  line reads »Ausgabe 7/86«), re-worded; it is a third independent
  transcription of that question, which is what r330 compares for. 8609 p16
  also prints a shortened »Technischer Defekt« with the byline »WERNER
  STREHLOW, Ausgabe 7/86«, re-written, not a reprint of the question text.

The Leserforum reuse is eight short reader questions in a 2570-word
article whose answers are all new, and each question already carries its
printed source line: single-item reuse, so no credit box (owner 2026-10-07,
SH8605 D87).

Recorded, not credited: `14 Leserforum.html`
