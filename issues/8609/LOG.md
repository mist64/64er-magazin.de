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

## Deliberate deviations from print

- **`148 Wettstreit der Assembler`** — p150 sets a single heading *"Kleines
  Assembler-Lexikon: TurboAss- und ASSI/M-Besonderheiten"* over the Lexikon
  box. The second half belongs to the two comparison tables, not to the box.
  Split: `<h2>TurboAss- und ASSI/M-Besonderheiten</h2>` now sits above the
  tables and the aside keeps `Kleines Assembler-Lexikon`. Marked in the file at
  both ends. Do not restore the printed form.

## Errata state of the listings

- **`prg/ean-codes.txt`** (Bar-Codes, erratum 11/86 p99) — the disk already
  carries the corrected line 85. Recorded in the file's `;` header as
  `;inkl. Fehlerteufelchen 11/1986 (Zeile 85; Disk-Version bereits korrigiert)`.
- **`prg/viza.key.prg`** (Vizawrite Teil 9, erratum 10/86 p80) — **the disk
  binary is already the corrected version.** All five corrected rows from the
  printed erratum match byte for byte at $033C, $034C, $0354, $035C and $0364
  (load $033C, 150 bytes, end $03D1). Nothing to patch. A `.prg` cannot carry a
  `;` header, so the record is here plus the aside on the article.
- **`prg/xref 7.0.txt`** (XREF 7.0, erratum 1/87) — the disk is the
  **pre-correction** version; all seven corrected lines differ. Marked
  `;vor Fehlerteufelchen 1/1987`.

  **OPEN — needs the user's sign-off.** The user has asked for the erratum to be
  applied, keeping each superseded line as a `;` comment. Not done yet: the
  1/87 errata text must be re-read at high magnification first (one line,
  `zzu%` vs `ZU%`, is already suspect), and the patched listing must be run in
  x128 before it is committed. Until then the aside on `71` carries no
  disposition comment rather than a false one.
