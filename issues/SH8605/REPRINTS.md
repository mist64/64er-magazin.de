# SH8605 — reprint leads

The Einsteiger-Sonderheft reprints, besides the house input aids, whole
articles and — far more often — single sections, tables and reader letters
from earlier issues. This list is a set of **leads, not findings**: each one
comes from a measurement and was confirmed or refuted against both printed
pages at step 330 (`LOG.md`, step 330).

## How the leads were found

`reprints.txt` (step 140, whole-article 6-word-shingle overlap) is the first
source and stays as it is; this file extends it. Three more measurements at
step 330, all over every article in `issues/`, listings (`<pre>`/`<code>`)
excluded:

- **per block** (`r330` *Step 0's ~0.5 overlap threshold misses a MERGED
  reprint*): a block of ours matches an article when at least half its 8-word
  shingles occur in it; the longest run of consecutive matching blocks is
  scored against the SHORTER of the two articles, and anything above ~0.4 was
  read. This found the merged articles 120 and 30, 155's Leserforum letters,
  164's tips and the two Bücher reviews.
- **strong blocks**: every article sharing at least one block of ours (15+
  words) at 80 % of its 8-word shingles — the Leserforum originals of 155
  whose run score is low because only two or three letters were taken.
- **table cells**: identical `<td>`/`<th>` texts. The shingle passes cannot
  see a table, so this is what found the reprinted tables of 77, 90, 114 and
  20.

Two more were found only by reading the pages at step 1: 111 ← 8409/16 (Herbert
Heise's report, condensed past the reach of an 8-word window) and 164 ←
8410/89 (one tip, 6-word shingles).

Separation: the run score alone does not separate — confirmed originals run
from 0.98 down to 0.05-0.2 for a single reprinted tip or letter, which the
strong-block list then confirms; the tables score 0 and are found by cells. The
Sonderheft copies of a credited monthly
score up to 0.86 (SH8602/7 MSE) and are not separate leads. The highest pair
that is neither a reprint, a copy of one, nor the masthead is 0.07
(`30` ← 8601/21, refuted on the page), then 0.05 (`164` ← 8607/84). The
masthead itself reaches 0.81 (`194 Impressum` ← SH8604/162).

SH8605's pubdate is 2026-10-31 (October 1986), so the monthlies up to 8610 are
**earlier** and can be originals; 8611 (2026-10-17) too.

## Leads

| SH8605 article | claimed original | evidence (overlap) |
|---|---|---|
| 111 Das DOS 5.1 auf der Demo-Diskette | 8405/40 + 8409/16 | step 140: 8405 `dos5.1` 0.37; per-block run 0.18 / total 0.52. 8409/16 found by reading: byline Herbert Heise, listings »DOS verschieben« |
| 135 Checksummer 64 V3 | 8603/55 | step 140 (`8603/checksummer`); 0.91. Same house text in SH8602/6, SH8604/93, SH8507/6, SH8603/76, 8610/76 |
| 136 MSE – Abtippen sicher und leicht gemacht | 8602/57 | step 140 (`8602/mse`); 0.83. Same house text in SH8602/7, SH8604/94 and earlier versions |
| 138 Schnell kopiert mit Hypra-Copy | SH8505/69 | step 140; 0.81. First printing in SH8505 (8511/45 erratum cites »Sonderheft 5, Seite 70«); no monthly carries it |
| 140 Turbo Tape de Luxe | SH8505/40 | step 140; 0.93. First printing in SH8505 (8510/37: »aus dem 64'er-Sonderheft Nummer 5«); no monthly carries it |
| 142 Hypra-Load | 8410/67 + SH8506/10 | step 140 named 8410 `hypra-load` by its id; the text is SH8506's Hypra-Load 2.1 (run 0.98), written for that Sonderheft. 8410/67 refuted at step 1 |
| 144 Hypra-Save | 8508/79 | step 140 (`8508/hyprasave`); run 0.96. Also SH8506/124 (itself a reprint of 8508/79) |
| 120 Das Computerbüro | 8405/46 + 8509/135 + 8602/18 + 8602/20 + 8602/21 + 8604/149 | merged software reviews; per-block runs 0.34 / 0.74 / 0.50 / 0.65 / 0.86 / 0.83 against the shorter article (whole-article only 0.06-0.11) |
| 30 Ohne Drucker geht es nicht – eine Entscheidungshilfe | 8505/18 + 8511/40 + 8602/31 + 8602/33 + 8603/31 + 8604/21 + 8601/21 | merged printer tests; runs 0.84 (8603/31), 0.74 (8602/33), 0.61 (8604/21, 8511/40), 0.60 (8602/31); 8505/18 via the MPS 801 block (also in SH8603/43, itself a reprint); 8601/21 one shared sentence, refuted |
| 155 Fragen & Antworten | 8404/14 + 8405/10 + 8406/18 + 8407/10 + 8408/17 + 8409/11 + 8410/16 + 8412/14 + 8502/12 + 8503/16 + 8505/11 + 8506/12 + 8507/14 + 8508/18 + 8509/149 + 8510/12 + 8511/14 + 8602/16 + 8610/23 + 8611/29 | reader letters collected from 18 Leserforums (strong blocks: 8412/14 26 blocks, 8507/14 17, 8506/12 18, 8408/17 10, …); 8610/23 and 8611/29 share one block each, refuted |
| 164 Tips und Tricks für Einsteiger | 8407/110 + 8410/89 + 8412/84 + 8501/90 + 8504/153 + 8505/77 + 8506/148 + SH8505/26 + 8603/79 | single tips from nine issues (runs 0.54 8412/84, 0.51 SH8505/26, 0.46 8505/77, 0.38 8501/90, 0.26 8407/110, 0.23 8506/148, 0.08 8603/79; 8504/153 one 140-word block; 8410/89 6-word shingles). SH8504/22 and SH8602/133 are later reprints of 8407/110 and 8505/77 |
| 185 Bücher | 8503/87 + 8511/171 | two of six reviews; runs 0.59 (8511/171), 0.24 (8503/87). SH8508/104 and SH8603/52 are later reprints |
| 188 Computer-Lexikon | 8603/140 | strong blocks: 3 blocks, 286 words (KI and Prolog entries) |
| 77 Rezepte für Grafik-Diners | 8404/119 | table cells: 146 shared (Tabelle 1 VIC-II registers, Tabelle 2 Zeichen-ROM) |
| 90 Der leichte Umgang mit Sprites | 8404/119 | table cells: 94 shared (Tabelle 1 VIC-II registers); prose 0.00 |
| 114 Drucken ohne Rätsel | 8606/160 + 8607/92 | table cells: 62 / 96 shared (MPS codes and Sekundäradressen; ESC/P table) — REVERSED: both monthlies are younger (they print SH8605's errata); compared, not credited |
| 20 Die Ports des C 64 | 8510/129 | table cells: 10 of 10 (User-Port pinout, every cell); one paragraph re-edited |

## Not leads

- `194 Impressum` — 0.81 to SH8604's Impressum (0.2-0.8 to every other
  issue's): the shared masthead.
- `135` ← 8610/76 »Checksummer V3 und MSE« (60 table cells) and the older
  Checksummer texts: the standing house text; the credited (and compared)
  original is 8603/55, the earliest monthly of this version.
- `142` ← 8512/109 Fehlerteufelchen: an erratum to SH8506's Hypra-Load 2.1
  listing (rule 300's business), not an original.
- `176 Die PEEK-, POKE- und SYS-Kiste` ← 8405/86, 8410/91, SH8602/136,
  SH8501/94: one 17-word block; the entries state the same POKE/SYS facts in
  other words.
- `164` »Directory ohne Programmverlust« (SH8501/94, 8506/80) and »Negative
  Bytes?« (8503/16): same tip / question, every sentence rewritten.
- `164` ← 8607/84 Fehlerteufelchen: one stock sentence (»Im Listing … ist die
  Zeile 20 wie folgt zu ändern«).
- `155` ← SH8603/11: one 31-word block of house Q&A text, a Sonderheft echo;
  the Leserforums of 8411, 8501, 8504, 8512, 8601, 8603-8609 share no block.
- `90` ← SH8504/112 »Sprites ohne Streß«: 33-47 shared cells, all bare
  numbers and addresses of different tables.
- `77`/`90` ← SH8603/54, 8608/69, 8603/84; `164` ← 8405/109, 8609/137,
  8608/69; `69` ← 8405/33; `114` ← 8508/81, SH8506/14, 8506/116 (8-16 cells
  each): register addresses, powers of two and the 4-bit binary patterns —
  numbers every such table prints, no shared wording.
- `6 Speicherlandschaft` ← 8405/109 (12 cells): the Basic pointer table
  (TXTTAB … MEMSIZ, 43/44, 2049) — the same facts, but re-ordered columns and
  rewritten descriptions (»Basic-Text-Anfang« / »Anfang Basic-Text«).
- `120` ← 8604/166 »Superbase (Teil 1)« (16 cells): the Superbase menu option
  names; the table they sit in is credited to 8602/18.
- `3`, `17`, `24`, `28`, `40`, `69`, `101`, `132`, `134`, `145`, `149`, `178`
  — no block and no table above noise.

## Credit on the page (owner, D87, 2026-10-07)

Credit where the BODY TEXT is substantially reprinted; table-only or single-item reuse is recorded here and in
LOG.md, with no credit on the page.
- **Credited:** 111, 120, 138, 140, 142, 144, 155 (one credit, its 18 originals as 18 links, no question titles),
  164, 30, and 185 (two of its seven reviews reprinted complete — whole body text).
- **Recorded, not credited:** 77 and 90 (the VIC register table of 8404/119), 20 (the User-Port pinout of
  8510/129), 188 (parts of two entries of a lexicon of ~109 — the single-item case).
- Standing reprints 135/136: compared, never credited (owner, 2026-10-06). 114: REVERSED, no credit.
