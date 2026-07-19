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

### Body "Bild N" references that have NO matching crop file
- **82 Umschaltbares 64'er-DOS**: only 3 photo/layout crops exist
  (82-1 = Bild 1, 82-5 = Bild 5, 82-7a = Bild 7a). The article's
  schematic diagrams **Bild 2, 3, 4, 6, 7b, 8** are printed on the
  scan (pages 87-89) and several are referenced in the body
  (Bild 3 at "…gemäß Bild 3 mit einem Umschalter…", Bild 7b at
  "…Bild 7b zeigt den Bestückungsplan…") but were **not cropped** —
  no PNG exists, so they could not be placed. Not fabricated.
- **154 Attraktiver C 64 sucht Dame**: only one crop exists
  (154-1 = Bild 1, the Ausgangsstellung board, placed). The article
  also prints **Bild 2** (9-board Spielbaum, page 154, referenced at
  "…Stellung 3 in Bild 2…") and **Bild 3** (Alpha-Beta tree, page 155,
  referenced at "Betrachten Sie hierzu Bild 3."). Neither Bild 2 nor
  Bild 3 has a crop file — not placed.

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
