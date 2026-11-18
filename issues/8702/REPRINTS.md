# 8702 — reprint leads (step 330, Step 0)

Step 140 ran no overlap pass on this monthly, so this step ran it first and
also wrote `reprints.txt` (r140, *Check 4 CANNOT see a reprint*). **Neither
file was page-confirmed when written** (step 1 has since confirmed every
row -- see *Step 1* at the end). Every row below, and every line of
`reprints.txt`, is the overlap pass's result and a **hypothesis** for step 1
to confirm or refute against both printed pages. Step 1 runs on all of them;
r330's *a lead already in `reprints.txt` has been confirmed* does not hold for
this file.

## How the leads were found

Measured 2026-11-17, after step 300 and before 325, over all 52 articles of
8702 against every other `issues/*/*.html` (2222 files; the working tree,
including step 300's uncommitted outbound asides in 8611, 8612, 8701).
Script and full output: `<TMPDIR_ISSUE>/r330s0/step0.py` / `step0.txt`
(scratch). Text taken with `r330_reprint_compare.py`'s own extractor, so
`<pre>`/`<code>`, `futureteufelchen` and `nachdruck` are excluded and
line-end hyphens joined as the diff will join them; words lower-cased.

- **whole article**: 8-word shingles. `ours` = shared / our shingles,
  `theirs` = shared / its shingles, `min` = shared / the smaller set.
  Whole-article threshold ~0.5.
- **per block**: a block of ours matches when ≥ 50 % of its shingles occur in
  the candidate; `run` = longest run of matching blocks / the shorter
  article's block count, read above ~0.4; `strong` = blocks at ≥ 80 %.
  Every block match was read.
- **table cells**: identical `<td>`/`<th>` texts (≥ 6 chars, not bare
  numbers). **listing lines**: identical `<pre>` lines ≥ 20 chars (none
  found).
- **Leserforum source lines**: every quoted reader question in `14
  Leserforum` carries its printed source line (»Ausgabe 12/86« etc.). All
  ten were followed to their issue by hand, because a reader question is
  one short block and the shingle pass cannot always score it: the 9/86 LCD
  question is re-worded (0.47) and the 12/86 Koalapainter question has 8
  shingles of which one word differs (0.13). Both are below 0.5 and are
  leads all the same.

Separation: no whole-article reprint in this issue. Everything that is not
house furniture is at or below 0.09 whole-article. The two reuses are a
standing Checksummer/MSE box inside 52 (0.72 `theirs` against the box
printed alone as 8611/99) and ten reader questions in the Leserforum.

Direction: 8702 (2/87) is the youngest issue in the corpus with text; every
claimed original is a 1986 monthly or 8701, all older by cover date, so no
`REVERSED` candidate. Origin = the earliest MONTHLY carrying the text
(r140).

## Leads

| 8702 article | claimed original | overlap (min / ours / theirs; blocks; run) | status |
|---|---|---|---|
| 66 Checksummer MSE (measured inside 52 Nie wieder Probleme mit Kurvendiskussionen) | 8609/46 | 0.04 / 0.03 / 0.04; 4 blocks (1.00, 0.84, 0.70, 0.63), run 4 | **new lead (hypothesis)**, PARTIAL shape: only the »Checksummer MSE« `<aside>` on our p66 (4 paragraphs + `(tr)`) is shared, the article is not. The box is standing house text: its first three paragraphs are identical in 8609/46 (inside »Vollgas für die Floppy«, `fsd`), 8611/99 (printed alone, `checksummer`) and 8612/74 (inside »Tips & Tricks für Profis«); only the last paragraph's pointer changes with each printing (8609: »3/86 … 55, MSE 2/86 … 57«; 8611: »10/86 … 76, MSE 2/86 … 57«; 8612: »10/86 … 76«; ours: »1/87 auf Seite 70«, i.e. 8701/70). 8609/46 is the earliest monthly carrying it, so the origin. Standing reprint by content: compare, no credit (owner 2026-10-06) — but our `64er.id` is `kurvendiskussion`, not `checksummer`, so step 7's check (a) will expect a credit unless the body declares it under »Recorded, not credited«. |
| 66 Checksummer MSE (measured inside 52 Nie wieder Probleme mit Kurvendiskussionen) | 8611/99 + 8612/74 | 8611/99: 0.72 / 0.03 / 0.72, run 0.67 (4/6 of the box's blocks); 8612/74: 0.07 / 0.03 / 0.07, 4 blocks | **new lead (hypothesis)**: the second and third printings of the same box, closer to ours in their last paragraph than 8609 is. Step 1 decides whether they are diffed (as 8701 did with 8609/15) or only noted. **8611/99 is AMBIGUOUS** — `resolve` gives 3 candidates (`94 Tips & Tricks zum C 16, C 116, Plus_4`, `99 Checksummer und MSE`, `99 Fehlerteufelchen`); `--against` scores the box 99 % of words, the others 46 % / 45 %. A row on it needs two `REJECTED` lines. |
| 14 Leserforum | 8607/13 + 8609/15 + 8610/14 + 8611/16 + 8612/16 + 8701/14 | 8612/16: 0.09 / 0.09 / 0.09, 5 blocks (0.87, 1.00, 1.00, 1.00, 0.73); 8611/16: 2 blocks (0.79, 1.00); 8701/14: 1 block 0.83; 8609/15: 1 block 1.00 (+ LCD 0.47); 8607/13: 1 block 1.00; 8610/14: 1 block 1.00 | **new lead (hypothesis)**, PARTIAL shape: only the quoted reader questions are reprinted, each under its printed source line; the answers are new. Per original: **8607/13** »Wer kennt Olympia Carrera?« (7/86; the same question is reprinted again in 8609/15 and 8611/16, both also leads here); **8609/15** »LCD-Displays am C 64?« (9/86; re-worded and shortened, the Handheld sentence cut); **8610/14** »Computerversicherungen« (10/86); **8611/16** »C 64 auch für Blinde?« (11/86; ours lacks »Welche Software- und Hardwarelösungen gibt es?«); **8612/16** »Fastload und Wiesemann-Interface?«, »Seltsame Null«, »C 64 stürzt ab?«, »Nachladen?«, »Koalapainter und C 128?« (12/86); **8701/14** »Zeichensätze vom Character-Editor« (1/87). One diff per original, with `--partial`. Single-item reuse, so presumably no credit (8701 precedent, owner 2026-10-07), declared by the body. |

### Word differences in the shared text (for 325 and the body; nothing decided)

Read off a token diff of the shared blocks only. Each is a question for the
printed pages, not a finding.

- **52 box, our side:** »Listings. .« (stray full stop); »([CLR)})« where
  all three earlier printings have »({CLR})«; »zım Beispiel« (dotless ı) for
  »zum«; »Einsendung .eines« (stray full stop). Also, against all three:
  »SHIFT-Taste« / »Commodore-Taste« where they have »<SHIFT>-Taste« /
  »<C=>-Taste«; »Auch erzeugt er« where they have »Auch er erzeugt«;
  »Der Checksummer und MSE wurde« (8612: »… und der MSE wurden«).
- **14 Leserforum:** »Koalapainter-Bilder im C 128-Modus« (ours) vs
  »C 128-Modul« (8612/16); »Create Character-Programm« (ours) vs
  »Program« (8701/14); the »Nachladen?« question has one more `"` on our
  side, and 8612 adds »Es wird dann ständig nachgeladen.«; »Fastload«
  (ours) vs »Fast-Load« (8612); one comma in »Olympia Carrera« against
  8611/16 (8607/13 and 8609/15 match ours).

## Not leads

- `179 Impressum` — 0.97 to 8701/187, 0.89–0.92 to 8609–8612, 0.78–0.82 to
  earlier monthlies and SH8602–SH8604: the shared masthead.
- `176 Wir suchen die Anwendung des Monats` and `176 Einmal im Monat gibt es
  2000 Mark für das Listing des Monats` — 1.00 / 0.93 to the same house ad in
  every monthly from 8512/180 to 8701/174 (`anwendung_des_monats` /
  `listing_des_monats`). Recurring house furniture, kept out of the table on
  the 8701 precedent.
- `93 Fehlerteufelchen` ← 8611/52 (0.28), 8701/83 (0.25), 8612/52 (0.25),
  8611/44 (0.14), 8607/36 (0.08), 8612/22, 8612/40: each one block, the
  erratum text itself inside our own `fehlerteufelchen` asides in those
  issues — step 300's outbound copies (uncommitted for 8611, 8612, 8701;
  8607/36's from the earlier back-propagation 5b090f0a). Not a reprint.
- `148 Die Axt im Haus... (Teil 7)` ← 8608/48, 8609/130, 8610/49, 8611/156,
  8612/48, 8701/144: one block each, the series' standing disclaimer
  (»Alle in dieser Serie gemachten Anleitungen …«).
- `36 Es muß nicht immer Schule sein` ← 8608/33 (0.02): two `<li>` of the
  »Ali« section — the address line and one bullet (»Noch ein Pluspunkt
  verdient Beachtung …«) verbatim from 8608/33's Ali table, in a section
  that says it updates the 8/86 review; ← 8611/12 (0.01): one sentence
  re-worded. Single sentences, not a reprint. A second witness for 325:
  8608 sets »Wastl-Witt-Straße«, ours »Wastl Witt-Straße«.
- `19 Was Hänschen nicht lernt ...` ← 8608/33 (0.01): one checklist item;
  the same author (R. Werner) re-wrote his 8/86 criteria list, every item
  re-worded.
- `136 Von Basic zu Assembler (Teil 11)` ← SH8607/66, 8502/134: one
  bibliography line (»Quelle: Schineis, Braun, Grellner …«) and 8 stray
  shingles.
- `31 Preisgünstiger Schönschreiber`, `33 MPS 1000 — Neue Referenz` ← the
  1986 printer tests (13–30 cells, one `<td>` font list): the standard
  data-box labels. `160`, `162`, `44` ← every game review (7–8 cells): the
  rating-box labels. `42` ← SH09/79 (7 cells).
- `76 Tips & Tricks zum C 16 und Plus/4` ← 8610/93, 8701/79: the `<h1>`
  rubric title only. `18 Computerlexikon zum Sammeln` ← 8610/26, 8612/28:
  7 shingles, the rubric's standing intro phrase. `156 Giga-CAD Plus` ←
  12 articles at exactly 5 shingles each: stock phrases.
- `10`, `11`, `135`, `143`, `151`, `158`, `163`, `164`, `171`, `174`
  (both), `180`, `20`, `22`, `26`, `27`, `28`, `30`, `34`, `39`, `40`,
  `46`, `48`, `49`, `50`, `72`, `79`, `8` (both), `83`, `86`, `88`, `91` —
  no candidate sharing ≥ 5 shingles, no block, no table or listing match:
  original to this issue by this measure.

## Step 1 (330 body, 2026-11-17)

Every lead above was confirmed on both printed pages (ours masters600 p14, p15, p66; theirs the published PDFs, folios checked): all nine lead × original pairs are **PARTIAL** — 52 shares only the Checksummer/MSE box (with 8609/46 as origin and 8611/99, 8612/74 as further printings), 14 shares only the ten quoted reader questions. Per-pair records: `reviewed/r330-*.txt`; the verdicts and evidence are in LOG.md's `## Step 330 (reprint_compare)`. Neither article gets a credit: 52's box is the standing Checksummer/MSE text (owner 2026-10-06) and single-item reuse; 14's reuse is single questions (owner 2026-10-07).

Recorded, not credited: `14 Leserforum.html`, `66 Checksummer MSE.html`


2026-11-18: the Checksummer/MSE box was split out of `52 Nie wieder Probleme mit Kurvendiskussionen.html` into its own article `66 Checksummer MSE.html` (`64er.id` `checksummer`, as 8611/99; owner ruling on the Inhalt line »Eingabehinweise« p66). The measurements above were taken while the box was inside 52; the shared text and the PARTIAL verdicts are unchanged. Records renamed `reviewed/r330-52-*` → `reviewed/r330-66-*`.
