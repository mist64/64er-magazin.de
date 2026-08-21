# 8609 — Placement log

## Rule 130 (place figures) — unplaced `prg/` files

The following files have **no article home in issue 9/86** and are therefore
left listed in `prg.txt` only, following the 8608 precedent:

### Disk infrastructure (before the first per-article separator)
- `leser-info!` — boot / reader-info screen of the Programm-Service disk
  (auto-run banner). Belongs to no article.

### Section separator `-------------165` — Programm-Service bonus programs
Page 165 of the magazine is the **Programm-Service order-form advertisement**,
not an article. Its copy reads: *"Neben vielen Programmen haben wir diesmal
etwas ganz Besonderes für Sie: Soundmonitor: tolle Musik selbstgemacht!"* —
i.e. the Soundmonitor and its sound data are the disk's **bonus programs**, not
listings belonging to any 9/86 article. Not placed:

- `sound-monitor` (Soundmonitor by Chris Hülsbeck)
- `basedrum       s.prg`, `effectsnare    s.prg`, `paradroideffects.prg`,
  `portamento     s.prg`, `spaceblow    s13.prg`, `supersynth     s.prg`,
  `special 1     s3.prg`, `axel f..prg` — Soundmonitor sound/tune files.

## Resolved — the gaps recorded above are all closed

Kept here as the record of what was open and how each was settled.

- **`66 Tips & Tricks für Profis` — two `<pre>TODO</pre>` patch fragments.**
  RESOLVED. Both patches transcribed from the print and verified byte-identical
  against `prg/hyplatos 2.prg` at `$0E40` and `$345C`; the string at `$0E70`
  decodes to `" NUMMER DES MATRIXFILES (0-9/SPC) ? "`.

- **`hires-colossal` classified as BASIC.** RESOLVED. `prg/hires-colossal.prg`
  moved into `prg/`, the `.txt` retired to `prg/del/`, and the figure switched to
  `<pre data-filename="hires-colossal.prg" data-name="HiRes Colossal" data-mse=mse1>`
  with a `binary_download` sibling. Renders as MSE hex with address and checksum
  columns.

- **`34 Marktübersicht Drucker` `64er.pages`.** RESOLVED — now `34-39`.

- **`54 Bar-Codes` ESC-code block.** RESOLVED. Rebuilt from scan p55: the
  fractions read `1/216`, `7/72` and `1/6 Zoll`, `chr$()` is `chr$(1)`, and the
  invalid `<p><pre>` nesting is gone.

- **`155 …StarTexter` `(siehe Tabelle ])`.** RESOLVED — the print reads
  `(siehe Tabelle 1)`; confirmed on the scan. Part of a wider `]`-for-`1` sweep
  (see below).

- **`148 Wettstreit der Assembler` missing lexicon entry.** RESOLVED. The
  *Interaktive Assemblierung* text was present but glued to the end of the
  *Bedingte Assemblierung* paragraph; split into its own `<p>`, so the box now
  carries all five entries.

## Rule 080 — two articles merged, per the Listing/Anwendung-des-Monats convention

The magazine prints the *Listing des Monats* and *Anwendung des Monats* overview
apart from the listing/description, on non-adjacent pages. We combine them into
one article, as the `Jahresinhaltsverzeichnis` does:

- `48 Bar-Codes selbst gemacht.html` — `pages="48,54-55"` (was 48 + 54)
- `46 Vollgas für die Floppy 1570_71.html` — `pages="46,50-52"` (was 46 + 50)

## Rule 280 — the `]`-for-`1` OCR class

The serif `1` in this typeface is read as `]` by the OCR. Swept issue-wide: 27
occurrences fixed (`Bild ]`, `Listing ]`, `Tabelle ]`, `VR]`, `CHR$(n])`,
`($D60])`, `1541/70/7]`, `Monitor 190]`, `33] Seiten`, …). 8608 has none, so
this is specific to how 9/86 was scanned.

## Rule 300 — forward errata

Three later issues correct 9/86 articles; asides added from
`fehlerteufelchen_pages/`:

- 10/86 p80 → `156 Tips und Tricks zu Vizawrite (Teil 9)` (VIZA.KEY MSE listing)
- 11/86 p99 → `48 Bar-Codes selbst gemacht` (DATA line 85)
- 1/87 → `71 Cross-Referenz-Liste C128` (XREF 7.0)

Note: `Fehlerteufelchen.md` records the XREF 7.0 target as *Ausgabe 9/86, Seite
25*; the printed page reads **Seite 71**, which is where XREF 7.0 actually is.
