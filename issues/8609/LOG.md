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

## Rule 130 — printed listings with no separate disk file (`<pre>TODO</pre>`)

- `66 Tips & Tricks für Profis.html`, section *Hypra-Platos verbessert*:
  the print carries **Listing 1** (patch at $0E40) and **Listing 2** (patch at
  $345C), both shown under the name `hyplatos 2`. The disk holds only the
  **already-patched** program `hyplatos 2.prg` (0801–3591, 11666 bytes), which
  is offered as a `binary_download`. The two printed patch fragments are not
  separate files, so both figures carry `<pre>TODO</pre>` pending an OCR pass.

## Rule 130 — classification note for a later pass

- `hires-colossal` (article `82 HiRes Colossal.html`) is a **machine-language**
  program (load address $CC01) and is printed as an **MSE hex listing**
  ("Name : hires-colossal cc01 cd27"). The extraction step classified it as a
  BASIC listing, so the master lives in `prg/hires-colossal.txt` and the
  petcat rendering is meaningless. Fix: move `prg/del/hires-colossal.prg` to
  `prg/` and switch the figure to
  `<pre data-filename="hires-colossal.prg" data-mse=mse1>` + a
  `binary_download` sibling.
- `shades control` (article `66 Tips & Tricks für Profis.html`) is likewise
  printed as an MSE hex listing, but it *is* a BASIC program, so the petcat
  rendering is correct and readable — only the presentation differs from print.

## Rule 160 — notes from the table pass

- `34 Marktübersicht Drucker.html` — the market table actually runs over
  **pages 35–39**, and page 39 carries a **second** table
  (*Matrix-Tintenstrahldrucker*). Both are now placed. The `<head>` meta
  `64er.pages` still says `34` and needs widening to `34-39` — not touched
  here because the head-meta pass owns that file region.
- `54 Bar-Codes selbst gemacht.html` — the two-column block *Verwendete Codes
  zur Druckeransteuerung* (p55) is already placed, but as a `<pre><code>`
  with OCR damage (`%ıs Zoll`, `chr$()`). Left as-is by the table pass; it is
  a transcription fix (rule 170/280), not a missing table.
- `155 Tips und Tricks zum Startexter (Teil 1).html` — the body still reads
  `(siehe Tabelle ])` (OCR of `Tabelle 1`). The box it points at is printed
  with the caption *Übersicht über die Druckerfunktionen beim StarTexter*, so
  there is no `Tabelle 1.` figcaption to match it. Word-level fix belongs to
  rule 280.
- `148 Wettstreit der Assembler.html` — the *Kleines Assembler-Lexikon* box on
  p150 has **five** entries in print (Block, Bedingte Assemblierung,
  **Interaktive Assemblierung**, Assemblerschleifen, Variable); the HTML has
  only four. The *Interaktive Assemblierung* paragraph was dropped by the OCR
  import and still needs to be transcribed.
