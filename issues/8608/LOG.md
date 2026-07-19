# 8608 — Placement log (rule 10: place figures)

## Unplaced disk-infrastructure files (no article home)

The following three files sit on disk 8608A.D64 *before* the first
per-article separator (`--------------53`). They are disk boot / entry
/ checksum / MSE tooling that belongs to no single article. Per the
orchestrator's user-confirmed decision they are **not placed** into any
article HTML and remain listed in `prg.txt`:

- `leser-info!` — disk boot/reader-info screen (auto-run banner of the
  Programm-Service-Diskette), not an article listing.
- `checksummer` — the 64'er Checksummer V3.0 typing-aid utility, used to
  enter the BASIC listings; a general disk utility, not article-bound.
- `mse.prg` — the MSE (Maschinensprache-Editor) hex-entry utility used to
  type in the MSE listings; general disk tooling, not article-bound.

These are left in `issues/8608/prg/` (and `prg/del/`) and referenced in
`issues/8608/prg.txt` only.

## Image placement (rule 12: place_images) — WEIRD THINGS

All 96 loose crops were placed. Findings the user should know:

### Body "Bild N" references — crop gaps (RESOLVED)
- **82 Umschaltbares 64'er-DOS**: on the first pass only 82-1/82-5/82-7a
  existed; the schematic diagrams Bild 2, 3, 4, 6, 7b, 8 (scan pages
  87-89) had no crop. The user then supplied `82-2, 82-3, 82-4, 82-6,
  82-7b, 82-8` and they were placed (incremental pass). The article now
  carries the full Bild 1, 2, 3, 4, 5, 6, 7a, 7b, 8 in ascending order.
- **154 Attraktiver C 64 sucht Dame**: user supplied `154-2` (Bild 2,
  4×4-Dame Spielbaum) and `154-3` (Bild 3, Alpha-Beta tree); both
  placed. The article has exactly **Bild 1, 2, 3**. The body's
  "Bild 5" is NOT a missing figure — it is a cross-reference to the
  **first installment** of the Knobelecke in the May issue (8605):
  "Eine anschauliche Grafik zu diesem Verfahren zeigt Bild 5 in der
  ersten Folge der Knobelecke in der Mai-Ausgabe." No `154-5` exists
  or is needed.

### Judgment calls / oddities (all placed, noted for review)
- **22 So schnell wie der Wind (22-0)**: named like a caption-less
  title image (`-0`) but the print DOES show a caption under it
  ("Der umrandete Teil zeigt die Platine von Professional 1541 Dos").
  Caption was kept (figcaption included), placed after the intro.
- **50 Digi-Controller**: genuine Bild-number collision in the print —
  the page-50 complex circuit is captioned "Bild 1", and the gate
  diagrams on page 60 restart at "Bild 1"…"Bild 5". Captions kept
  verbatim, so two different figures both read "Bild 1".
- **50-0 / 52-00**: author-bio portraits placed inline
  (`<img class="inline">`) in their Lebenslauf sections, not as figures.
- **8-x collision**: crop 8-0 is the editorial ("Ja oder nein")
  lead portrait; crops 8-1…8-13 = Bild 1…13 all belong to the
  "Brandneu aus den USA" feature (continuous numbering, Bild 11/13
  physically printed on pages 11-12 but part of that feature).
- **12 Aktuelles**: the four 12-x crops are the four Aktuelles
  images (BTX-Telefon, The Last V8, Sprite Light, Line-Spy). The
  Micky comic (Bild 11) and Bodylog (Bild 13) also print on page 12
  but belong to Brandneu (crops 8-11/8-13), not Aktuelles.

### Renamed crops (orphan p59 → Digi-Controller p50 sequence)
- 59-1 → 50-2 (Bild 1 ODER), 59-2 → 50-3 (Bild 2 UND),
  59-3 → 50-4 (Bild 3 EXOR), 59-4 → 50-5 (Bild 4 NICHT),
  59-5 → 50-6 (Bild 5 Anwendungsbeispiel). All five gate diagrams are
  printed on page 60, inside "50 Digi-Controller.html" (pages=50,59-65).
  Plain `mv` used (crop PNGs are untracked; only title.png is in git).

## Rule 13 (fill tables) — extraction & decisions

All `TODO TABLE`/`TODO TABELLE` placeholders replaced; Pass-1 captioned,
Pass-3 uncaptioned/Bild/Steckbrief sweeps run. Placed tables and calls:

- **50 Digi-Controller**: 4 placeholders (operations glossary, operands
  glossary, Treppenhaus-Wahrheitstabelle, Weichenstellung Dual→Dezimal)
  + captioned Tabelle 1 (AWL-Ausdruck) / Tabelle 2 (Testprotokoll) as
  `<figure><pre>`. Numeric tables independently re-verified against the
  scan.
- **20 EX-800**: technical-specs sheet placed as bare `<table>` with a
  `<caption>` heading (print heading, not a "Tabelle N." caption);
  nested speed-comparison matrix reproduced inside its cell.
- **74/75/77 Tips&Tricks, 66 HiRes**: bare `<table>` (CHR$-codes,
  Sprite-View line explanations, IRQ-INIT line explanations, on-screen
  prompts). `TODO LISTING` placeholders left untouched.
- **52 Vokabel-Trainer**: Tabelle 1 (Liste der verwendeten Variablen).
- **142 Small C**: Tabelle 1 (Übersetzungszeiten) + Tabelle 2 (Small
  Tools) — re-verified numeric values.
- **82 Umschaltbares DOS**: Tabelle 1 (EPROM-Belegung, memory-map) +
  Flugsimulator byte-patch table. NOTE: the patch table prints label
  "$BC" while the preceding prose says "$8C" — print inconsistency,
  preserved verbatim (confirmed on scan).
- **128 Programmieren strukturiert**: Tabelle 1 (Schleifentypen Basic
  7.0). "TODO TABELLE 2" turned out to be a prose Kasten labelled
  "Tabelle 2. Anmerkungen zum Programm »COMALCHEN«" (p132) — kept as
  `<figure>`+`<figcaption>` with the prose content (not a data grid).
- **33 Lernsoftware im Test**: Testübersicht Tabelle 1–5 as captioned
  figures.
- **36 Die Qual/Markt der Wahl (Übersicht Lernsoftware)**: the whole
  5-page Marktübersicht comparison table (208 product rows, 7 columns,
  11 subject sections) was MISSING and has been transcribed as one bare
  `<table>` (Deutsch section spot-re-verified against scan). ALSO added,
  as faithful print elements the import had dropped: the p36 Anbieter
  key as `<dl class="anbieter-legende">`, the closing "keinen Anspruch
  auf Vollständigkeit" paragraph, and the byline `(Rüdiger Werner/do)`
  (author meta XXX→Rüdiger Werner, corroborated by sister article 33).
  The p37 "Technische Daten … Modell 6313" block is a PRÄSIDENT PRINTER
  advertisement — NOT extracted.
- **69 Reise durch den C128 (Teil 4)**: Bild 1 (VIC-Register), Bild 2
  (Bildschirmspeicher-Startadressen), Bild 3 (16-KByte-Zugriff des VIC /
  NMI-CIA Port A), Bild 4 (Zeichenmusterquellen, Bits 1–3 in 2604),
  Bild 5 (Anordnung der Zeichenmuster im Zeichen-ROM) and Bild 6
  (Wirkung Bit 3 in 2605 auf Bit-Map-Lage) are ALL data tables labelled
  "Bild" — placed as `<figure><table>`. (Correction: an earlier log line
  claimed "Bild 3–6 are schematics/diagrams, left for the image rule" —
  that was UNVERIFIED and wrong; re-checked against the 300-dpi scan
  pages 70–72, all four are grids and were transcribed.) Table B's
  (Bild 2) `$` column prints "$900/$1900/$2900/$3900" where the
  arithmetic implies $C00/$1C00/$2C00/$3C00 — genuine typesetting errors
  (9-for-C), preserved verbatim (confirmed on scan).
- **149 Superbase (Teil 5)**: the "Tabelle 1" (Leistungsübersicht
  »Verbrauch«) box is UNLABELLED in print → placed as `<figure><ul>`
  with no figcaption (prose still references it as "Tabelle 1", so
  verifier check #5 flags it — expected). SUPERBASE-Steckbrief PROG-
  Modus (Fortsetzung) extracted as a `<figure><table class="plain">`.

- **29 EDV für Lehrer**: Tabelle 1 (»Eine Übersicht, was mit welchem
  Drucker ausgegeben werden kann.« / p31–32 continuation »Übersicht: Was
  kann mit einem Drucker ausgegeben werden (Schluß)«) — the dense 2-page
  +/-/x printer-comparison matrix (12 printers × 73 capability rows,
  9 sections) has now been transcribed from the 600-dpi scan and placed
  as one merged `<figure><table>` (column-gridded per-cell vision read,
  cross-checked against the 300-dpi render). Includes the numbered
  printer key and the `(+ möglich, – nicht möglich, x verändert)` legend.
  No cells left `[ILLEGIBLE]`. Blank cells in the print (many special-
  character rows) are reproduced as empty cells verbatim.

### Left un-transcribed / out of scope
- **84 64'er Extra** — the huge 5-language command-comparison table
  (364 rows) was placed, but the article's `<p class="intro">` is
  TRUNCATED mid-sentence in the import ("…Die folgende Übersicht") —
  a pre-existing body-text gap, NOT repaired here (out of table scope).
