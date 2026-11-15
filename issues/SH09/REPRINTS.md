# SH09 — reprint leads (step 330, Step 0)

`reprints.txt` (step 140, confirmed against the page there) lists 30 pairs over 8 articles. This file **extends** it with the leads Step 0's own pass adds; those 30 do not go back through step 1. Every other row is a **hypothesis** for step 1 to confirm or refute against both printed pages.

## How the leads were found

Measured 2026-11-06, after step 300, over every article in `issues/` except SH09 itself (scripts and full output: `<tmp>/scratch_330/step0.py`, `step0.txt`, `step0_low.txt`, `cells.py`).

- **whole article**: 8-word shingles of the normalised text (`<pre>`/`<code>`, comments, `futureteufelchen` and `nachdruck` excluded; lower-cased, hyphens at line ends joined). `ours` = shared / our shingles, `theirs` = shared / its shingles, `min` = shared / the smaller set.
- **table cells**: identical `<td>`/`<th>` texts (at least 6 chars, not bare numbers).
- No per-block pass was run. A merged reprint shows in `theirs` here, as 30 and 94 do.

## Leads

| SH09 article | claimed original | overlap (min / ours / theirs; shared; cells) | status |
|---|---|---|---|
| 30 In die Geheimnisse der Floppy eingetaucht | 8410/153 + 8411/117 + 8412/139 + 8501/148 + 8503/130 + 8505/145 + 8506/116 | 0.68, 0.67, 0.68, 0.75, 0.80, 0.77, 0.56 (theirs); ours 0.06-0.17; cells 8501 193, 8412 30, 8410 16 | confirmed-by-140. MERGED: the whole course |
| 64 Verwalten wie die Profis | SH8608/79 | 0.55 / 0.30 / 0.55; 2765; cells 45 | confirmed-by-140 (`SH8608/dateiverwaltung-ms`) |
| 92 Buchbesprechungen | 8507/88 + 8601/118 + 8604/66 + 8606/97 + 8612/21 | 0.13, 0.16, 0.03, 0.18, 0.14 | confirmed-by-140. MERGED reviews |
| 94 Fragen und Antworten | 8404/14 + 8405/10 + 8406/18 + 8407/10 + 8409/11 + 8410/16 + 8503/16 + 8504/12 + 8505/11 + 8505/13 + 8506/12 + 8507/14 + 8508/18 + 8509/14 | 0.02-0.21 | confirmed-by-140. MERGED letters |
| 97 Checksummer 64 V3 | 8603/55 | 0.87 / 0.84 / 0.87; 457; cells 55+ | confirmed-by-140 (`8603/checksummer`). **Standing reprint**. Same house text in SH8602/6, SH8604/93, SH8605/135, SH8606/6, SH8607/119, 0.87-0.88 |
| 100 MSE – Abtippen sicher und leicht gemacht | 8602/57 | 0.85 / 0.83 / 0.85; 522 | confirmed-by-140 (`8602/mse`). **Standing reprint**. Same house text in SH8604/94, SH8602/7, SH8607/120, SH8606/7, 0.83-0.88 |
| 140 Die Datasette streikt nie wieder | 8510/34 | 0.83 / 0.83 / 0.81; 961 | confirmed-by-140 (`8510/datasette`) |
| 142 64'er-DOS erweitert | 8502/72 | 0.03; 116 | **UNRESOLVED** (step 1, 2026-11-14): the SMON command summary; the same summary is also in 8512/100, and which printing is the original is undetermined |
| 142 64'er-DOS erweitert | 8512/100 | 0.05 / 0.04 / 0.05; 204 | **UNRESOLVED** (step 1, 2026-11-14): the same SMON command summary as 8502/72; which is the original is undetermined. SH8608/146 (0.25, 218) is 8512/100's own reprint, a sibling, not a lead |

## Not leads

- Sibling reprints, found by Step 0 and settled at step 1 (below): `94` ← SH8605/155, `92` ← SH8603/52, `140` ← SH8603/160 (0.93, 1082 shingles), `142` ← SH8608/146. Each is an earlier Sonderheft reprint of a monthly that is already a lead here; a Sonderheft reprint is not the source of a later one (r330), so none is diffed or credited.

- `162 Impressum`: 0.78 to SH8607/178, 0.76 SH8608/162, and down the corpus: the shared masthead.
- `113` ← 8612/72 Fehlerteufelchen (58 shingles, 0.32 of theirs): the erratum that corrects THIS issue's Datev, younger than us; rule 300's input, done.
- `64` ← SH8505/103 ON ERROR GOTO (27 shingles, 0.07; 9 cells), SH8607/6, 8503/124, 8602/151 (9-11 cells): stock register and address cells, no shared wording.
- `79` ← 8608/84 (11 cells), SH8608/10 (7), SH8608/57 (6): Basic keyword and command names.
- `30` ← SH8608/57 (7 cells): address cells.
- `3`, `6`, `13`, `25`, `102`, `103`, `105`, `106`, `107`, `109`, `110`, `111`, `119`, `120`, `136`, `139`, `157`: no candidate at or above 0.02 with 8 shared shingles, no table above 6 cells: original to this issue by this measure.

## Step 1 for the Step 0 leads (2026-11-14)

Per-block attribution, 8-word shingles, a block of ours counted when at least half its shingles occur in the candidate (<tmp>/scratch_330, inline script):

- `94 ← SH8605/155`: 4 blocks of ours match SH8605/155, and all 4 also match the confirmed monthly letters pages. SH8605/155 is an earlier Sonderheft collection of the same monthly letters, so it is a sibling reprint, not an original. No diff. (r330: credit the monthly original; a Sonderheft reprint is not the source of a later one.)
- `92 ← SH8603/52`: 2 blocks, both also in the confirmed monthly Bücher pages. Sibling, no diff.
- `140 ← SH8603/160`: 6 blocks; 5 are also in 8510/34. The sixth, »Zum Schluß soll noch darauf hingewiesen werden, daß selbst bei Commodore-Datasetten …«, is in SH8603/160 and in ours but not in 8510/34's HTML. Sibling reprint of 8510/34, no diff of its own; whether 8510 prints that paragraph is settled on 8510's scan inside the pair `140 ← 8510/34` (PRINT or THEIRS).
- `142 ← SH8608/146, 8512/100, 8502/72`: 10 blocks match SH8608/146; 9 of them also match 8512/100 or 8502/72 at 0.5 or more, and the tenth (the FIND line of the SMON command summary) is in 8502/72 and 8512/100 at a lower share. SH8608/146 is itself 8512/100's reprint, so it is a sibling. **Open**: whether 142's SMON command summary is a PARTIAL reprint of 8502/72 (the SMON series) or of 8512/100, and whether it is reprinted text at all or a command list re-told. That needs both printed pages; held for the orchestrator's ruling on the merged pairs.
