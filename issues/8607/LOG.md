# 8607 — Table extraction log

## Tables extracted from `TODO TABLE` placeholders (Pass 2)

All 9 `<p>TODO TABLE</p>` markers replaced.

## Captioned tables added (Pass 1 sweep)

- `50 Das Rhythm Construction Set (R.C.S.).html` — added `Tabelle 1. Die Belegung der Instrumente und ihre Einsprungadressen` (R.C.S. instrument table from print page 53).
- `50 Das Rhythm Construction Set (R.C.S.).html` — added Varioprint `Tabelle 1. So werden die Zeichen von Vizawrite 64 von Varioprint umgesetzt` and `Tabelle 2. Technische Daten von Varioprint und die empfohlene Hardware-Konfiguration.` (both from print page 57).
- `36 Modem mit Wählautomatik.html` — added `Tabelle 1. Beschreibung der Signale am Modem-IC (AM 7910)`, `Tabelle 2. Die Bauteileliste für das Modem`, `Tabelle 3. Funktionsbelegung der DIL-Schalter` (print pages 37–39).
- `139 Von Basic zu Assembler (Teil 5).html` — added `Tabelle 1. Hier noch einmal die verschiedenen Arten der Adressierung` (print page 141).
- `153 Das System für alle Fälle_.html` — added `Tabelle 1. Das kann das RP-System: Jeder Punkt entspricht einem SYS-Befehl` (print page 154, yellow callout box, emitted as `<ul>` inside `<figure>` since the table is a single-column bulleted list with no header).
- `174 Computer-Knobeleien (3).html` — added `Tabelle 2. Die Sprague-Grundy-Verknüpfung` (print page 175); `Tabelle 1` is already placed as `174-t1.png` image and was NOT touched per the "skip tables already present as images" rule.

## Tables intentionally NOT touched (already present as image)

- `174 Computer-Knobeleien (3).html` — `Tabelle 1` is `<img src="174-t1.png">` inside `<figure>`. Per `table_workflow.md`'s "Skip tables already present as images" rule, left alone.

## STECKBRIEF callouts not yet extracted

`166 Tips und Tricks zu Superbase (Teil 4).html` references 5 `SUPERBASE-Steckbrief` callouts in its intro (FIND, ENTER, SELECT, OUTPUT, PROG) — all printed as yellow callout boxes on print pages 166–167. None are currently represented in the HTML. They were not extracted in this pass; they need to be added in a follow-up session. The Centronics pinout `TODO TABLE` in this article was replaced.

## No [ILLEGIBLE] cells

No cells were marked `[ILLEGIBLE]`. All cell values were verified against the print scan or the on-disk OCR pipeline output.

## Print typos preserved verbatim

- `139 Von Basic zu Assembler.html` — Tabelle 1 row "Indirekt | 3 | JMP($,4301)" preserves the printed comma inside the parenthesis (likely a typesetting error in the magazine; kept as-is).
- `89 Newsroom druckt deutsch.html` — Tabelle row "eck. Klammer l." uses lowercase `l` (the print shows lowercase L, not capital I); the previous HTML had `I` which was wrong.
