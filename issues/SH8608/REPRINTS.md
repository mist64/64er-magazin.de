# SH8608 — reprint leads (step 330, Step 0)

`reprints.txt` (step 140, confirmed against the page there) lists seven:
44 → SH8601/sprites, 129 → SH8603/checksummer, 130 → 8505/checksummer,
139 → SH8505/hypra-copy, 146 → 8512/smon, 150 → 8508/diskmon,
157 → 8604/tips_c16. This file **extends** it with the leads Step 0's own pass
adds; those seven do not go back through step 1. Every other row is a
**hypothesis** for step 1 to confirm or refute against both printed pages.

## How the leads were found

Measured 2026-10-10, after step 320, over every article in `issues/` except
SH8608 itself (script and full output: `<tmp>/_scratch330/step0b.py` / `step0b.txt`; per-block and per-table attribution `step0b_blocks.py`, `step0b_cells.py`):

- **whole article**: 8-word shingles of the normalised text (`<pre>`/`<code>`,
  comments, `futureteufelchen` and `nachdruck` excluded; lower-cased, soft
  hyphens at line ends joined). Three figures per pair: `ours` = shared /
  our shingles (how much of OUR article is that original), `theirs` = shared /
  its shingles (how much of the ORIGINAL is in ours — the merged-reprint
  signal), `min` = shared / the smaller set. Whole-article threshold ~0.5.
- **per block** (*Step 0's ~0.5 overlap threshold misses a MERGED reprint*):
  a block of ours matches when ≥ 50 % of its shingles occur in the candidate;
  the longest run of matching blocks is scored against the SHORTER article
  (`run`), read above ~0.4; `strong` counts blocks at ≥ 80 %.
- **table cells**: identical `<td>`/`<th>` texts (≥ 6 chars, not bare
  numbers) — the shingle passes cannot see a table.

Separation: whole-article reprints sit at 0.55–0.85 (`ours`); merged 157 has
`ours` 0.09–0.24 per original but `theirs` 0.51–0.77. 57's reprint is two
tables (cells only; prose run 0.01). The highest pair that is none of these
and not the masthead is 0.08 (`120` ← 8610/80, `108` ← 8611/99: the
Fehlerteufelchen that correct THIS issue — see *Not leads*).

Direction: every claimed original is older by cover date (latest 8606 = 6/86
against 8/86), so no `REVERSED` candidate. The two monthlies that share text
with us the other way round, 8610/80 and 8611/99, print SH8608's errata and
are therefore younger.

## Leads

| SH8608 article | claimed original | overlap (min / ours / theirs; run; cells) | status |
|---|---|---|---|
| 44 Shapes auf dem C 16 | SH8601/32 | 0.57 / 0.57 / 0.08; run 0.33, 24/33 blocks, strong 12 | confirmed-by-140 (`SH8601/sprites`). PARTIAL shape: the SSHAPE/GSHAPE half of the C 128 article, re-told for the C 16 |
| 129 Checksummer 20 V3 | SH8603/76 | 0.79 / 0.79 / 0.29; run 1.00, 9/9 blocks | confirmed-by-140 (`SH8603/checksummer`). **Standing reprint** — compare, no credit (owner 2026-10-06). Same house text in SH8507/6 0.66, SH8504/6 0.64 and the other Checksummer pages |
| 130 Wie unsere Basic-Programme einzugeben sind | 8505/54 | 0.48 / 0.41 / 0.48; run 0.30; cells 39/44 in every Checksummer page | confirmed-by-140 (`8505/checksummer`). **Standing reprint** (`abtippen`) — compare, no credit. Note: the Sonderheft copies score higher (SH8603/76 0.60, SH8507/6 0.60, 8508/53 0.53 with theirs 0.45); 140's lead stands, step 1 does not re-open it |
| 139 Schnell kopiert mit Hypra-Copy VC 20 | SH8505/69 | 0.84 / 0.84 / 0.82; run 0.88, 15/17 blocks | confirmed-by-140 (`SH8505/hypra-copy`). SH8605/138 (0.76) is a later reprint of the same, not a separate lead |
| 146 SMON für den VC 20 | 8512/100 | 0.55 / 0.55 / 0.12; run 0.50, 19/28 blocks, strong 12; cells 22/33 | confirmed-by-140 (`8512/smon`). The SMON command summary + VC 20 disk-monitor commands of 8512's long article |
| 146 SMON für den VC 20 | 8502/72 | 0.27 / 0.27 / 0.05; run 0.14, 9/28 blocks | **new lead (hypothesis)**: block 9 (»Alle Eingaben erfolgen in der hexadezimalen Schreibweise …«) matches 8502/72 at 1.00 and 8512/100 not at all; its other 8 blocks are also in 8512/100. Likely 8512/100's own source; step 1 decides PARTIAL or NOT-A-REPRINT |
| 150 Disketten-Monitor VC 20 | 8508/83 | 0.85 / 0.82 / 0.85; run 0.70, 20/23 blocks, strong 15; cells 54/56 | confirmed-by-140 (`8508/diskmon`) |
| 157 Tips & Tricks zum C 16/C 116 | 8604/83 + 8605/91 + 8606/86 + SH8605/164 | 8604/83: 0.77 / 0.17 / **0.77**, 11 blocks, cells 35; 8605/91: 0.51 / 0.09 / **0.51**, run 0.82; 8606/86: 0.69 / 0.24 / **0.69**, 20 blocks, strong 15, cells 26; SH8605/164: 0.27 / 0.27 / 0.15, 23 blocks, strong 20 | **MERGED.** 8604/83 confirmed-by-140 (`8604/tips_c16`); **8605/91, 8606/86, SH8605/164 new leads (hypothesis)**. Our blocks fall in order: 8604 (blocks 4–82), 8605 (123–167), 8606 (171–269), SH8605/164's number-systems course (272–338) |
| 157 Tips & Tricks zum C 16/C 116 | 8603/79 | 0.25 / 0.07 / 0.25; run 0.08, 7/73 blocks | **new lead (hypothesis)**: the earlier, partly re-worded form of the hex course that SH8605/164 carries in full (every 8603/79 block of ours is also in SH8605/164 — 8603/79 at 0.40–1.00, SH8605/164 at 1.00 for all but two). Step 1: which printing is the source |
| 57 C 128-Programme auf dem C 16? | SH8603/31 | 0.22 / 0.19 / 0.22; prose run 0.01 (1/78 blocks); **cells: Tabelle 2 »Die Zeropage beim C 16« 144/145, Tabelle 4 »Die restlichen Systemadressen beim C 16« 154/159** | **new lead (hypothesis)**: the two C 16 address tables, from SH8603's »Den C 16 und VC 20 durchschaut«; the C 128 Tabellen 3/5 share only 69/35 cells (same descriptions, different machine), Tabelle 1 is a keyword list (see *Not leads*). No monthly carries these tables (next best 8408/102, 13 cells). Table-only reuse — cf. SH8605's 77/90/20 |
| 10 Basic-Kurs für C 16-Einsteiger | 8512/146 | 0.05 / 0.01 / 0.05; 6/620 blocks, strong 2 | **new lead (hypothesis)**: one passage (blocks 1011–1034, low/high byte of a 16-bit number, »Jedes der beiden Bytes kann für sich allein …«) shared word for word with Memory Map Teil 13 — same author (Dr. Helmuth Hauck). 8411/133 shares 2 of those blocks. Single-passage reuse |

## Not leads

- `162 Impressum` — 0.86 to SH8604/162, 0.87 SH8606/178, 0.85 SH8605/194,
  0.6–0.77 to the older Sonderhefte: the shared masthead.
- `129`/`130` against the other Checksummer/abtippen pages (SH8503/6 …
  SH8507/6, 8502/65, 8508/53, 8603/55, SH8602/6, SH8604/93, SH8606/6): the
  standing house text; the credited-by-140 originals are the ones compared.
- `108` ← 8611/99 and `120` ← 8610/80 (one block each, 1.00): the
  Fehlerteufelchen that correct THIS issue's Grafik-16 (line 280) and Panik
  listings — rule 300's input (done), and younger than us.
- `57` Tabelle 1 »Befehlsvorrat des C 16 und C 128« ← SH8601/96 (112 cells),
  8506/16 (108), 8608/84 (40): Basic keyword names, which every such table
  prints; no shared wording (prose 0.03).
- `10` ← SH8601/96, 8608/84, 8506/16 (38–39 cells): the same keyword lists.
- `8 Fragen und Antworten zum C 16` ← 8607/98: one 17-word sentence
  (»Der C 16 simuliert den Save- und Verify-Vorgang …«), noise-level.
- `94` ← 8603/70, 8602/14, 8512/185: the publisher's address block.
- `92` ← 8604/92 (one block at 0.42, 8 cells), `79` ← SH8505/103 (0.07 of
  theirs, no block, 9 cells), `87` ← SH8603/14 (6 cells), `138` ← 8505/145
  (0.02): stock phrases and register/address cells, no shared wording.
- `3`, `6`, `47`, `56`, `67`, `90`, `96`, `100`, `102`, `105`, `106`, `110`,
  `112`, `115`, `117`, `123`, `131`, `132`, `135`, `144`, `154` — no
  candidate sharing ≥ 5 shingles, no block, no table above noise: original to
  this issue by this measure.

## Step 1 outcome (2026-10-10)

Every lead confirmed from both printed pages (LOG.md, `## Step 330 (reprint_compare)`): CONFIRMED 129, 139, 150; PARTIAL 10, 44, 57, 130, 146 ×2, 157 ×5. None refuted, none unresolved, none reversed. 157's hex course follows SH8605/164's wording, which re-edits and extends 8603/79.

Credited (step 7): 44, 139, 150, 157. Standing reprints, never credited: 129, 130. Table-only or single-passage reuse (owner 2026-10-07), recorded and not credited:

Recorded, not credited: `10 Basic-Kurs für C 16-Einsteiger.html`, `57 C 128-Programme auf dem C 16_.html`, `146 SMON für den VC 20.html`
