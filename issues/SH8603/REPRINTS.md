# SH8603 — reprint leads

The C 16/VC 20 Sonderheft reprints articles that had already run in the
monthlies (and in an earlier Sonderheft). This list is a set of **leads, not
findings**: each one comes from a measurement, and has to be confirmed against
both printed pages (r330 step 1) before anything is diffed.

## How the leads were found

Not carried over from anything. Measured twice on this issue's own built
articles:

- step 140: 6-word overlap of each article against all 1922 corpus articles
  (`LOG.md`, step 140) — eight leads;
- step 330, 2026-10-04: the share of each SH8603 article's 8-word sequences
  (prose only, `<pre>`/`<code>` removed, lower-cased, machine names closed up
  on both sides so that the owner's spaced `C 16`/`VC 20` does not hide a
  match) that also occur in a published article anywhere in `issues/`; and,
  per block, every corpus article sharing at least half of that block's 8-word
  sequences. That found the step-140 leads again and added 8409/155,
  8603/31, the four book reviews, the two Checksummer pages and 8407/52.

The number is a hint, not a verdict — a heavily re-edited reprint scores low,
a merged series scores low against each part, and a shared masthead scores
high.

## Leads

| SH8603 article | claimed original | evidence (overlap) |
|---|---|---|
| Das ist der C 16 | 8501/16 | 0.89 (`Generationswechsel – Test C 16`); 66 blocks |
| Den C 16 und VC 20 durchschaut | 8409/155 + 8410/157 + 8411/126 | 0.05 / 0.23 / 0.20 — `Der gläserne VC 20`, Teil 1–3, reworked for both machines; 10 / 24 / 23 blocks. Teil 4–6 (8501/130, 8502/141, 8503/155) share nothing |
| Drucker für C 16 | 8505/18 + 8603/31 | 0.47 (`Vergleich: Drucker unter 700 Mark`, same section heads, 12 blocks) / 0.26 (`Der Präsident 6313 C — das preiswerte Schwergewicht`, 12 blocks; p31 is shared with 8603/30) |
| Marktübersicht: Matrixdrucker | 8505/26 | 0.61 |
| Bücher zum C 16 und VC 20 | 8405/96 + 8503/87 + 8506/115 + 8507/88 | 0.15 / 0.16 / 0.05 / 0.17 — single reviews collected from four `Bücher` pages; 6 / 6 / 3 / 5 blocks |
| Checksummer 20 V3 | SH8507/6 | 0.74 — the VC 20 section of `Checksummer 64 V3 - Neu`; no monthly carries that section as text |
| Wie unsere Basic-Programme einzugeben sind | SH8507/6 | 0.92 — the house Eingabehinweise with Tabelle 1. Step 0 first named 8603/55 (0.67, 60 of 82 blocks paired against 3 for SH8507/6); the pages decided otherwise at step 1: every block and table cell of 77a is in SH8507/6 p6-7, while 8603/55 prints an older variant (one `{F1} bis {F8}` row, a `{SHIFT-SPACE}` row, no »Wenn Sie sich erst einmal …«). The block count only reflected that SH8507's HTML stores the table as one `<p>` |
| C 64-Programme für C 16 und VC 20 | 8407/52 | 0.20 (`Der Volkscomputer und der große Bruder: Adressenvergleich VC 20 - C 64`); 1 prose block ≥ 0.5, the address tables pair widely |
| Die Datasette streikt nie wieder | 8510/34 | 0.85 (p34 is shared with 8510/32) |
| Kurvenplotten mit Hardcopy | 8506/68 | 0.95 |
| HELP und TRACE verbessert | 8505/84 | 0.85 |
| »Fenster«-Befehle für den C 16 | 8507/84 | 0.96 |

## Not leads

- `178 Impressum` — 0.85 to SH8602's Impressum (and every other Sonderheft's):
  the shared masthead, not a reprint.
- `11 Fragen und Antworten zum C 16 und VC 20` — 0.03; one question sentence
  ("Kann man Programme für den VC 20 auch auf dem C 16 verwenden?") recurs in
  8504/12 Leserforum. Same topic, not the same text.
- `164 Tips & Tricks zum C 16` — 0.03 to 8604/83 `Tips & Tricks zum C 16`: two
  one-line tips (`WAIT 1,192`, the USR vector) shared. Not compared.
- `127 Eingesperrt!`, `146 Kampf um Rom`, `166 Super-Assembler…`,
  `54 Schnelle Spielegrafik…`, `81 Dateiverwaltung…`, `88 Der VC 20 als Musik
  Maestro` — matches only in later Fehlerteufelchen (8605/87, 8606/73,
  8607/84, 8609/61, 8610/80, 8612/72): errata quoting this issue (rule 300's
  business), not originals.
- `47 Marktübersicht: Matrixdrucker` — also 0.13 to 8609/34 `Punkt für Punkt`,
  a later issue: if anything that one reprints from here.
- `26 Das ist der C 16` — 0.00 to SH8601/96 / 8506/16 (C 128): house phrases.
