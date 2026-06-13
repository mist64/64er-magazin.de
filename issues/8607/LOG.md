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

## STECKBRIEF callouts extracted

`166 Tips und Tricks zu Superbase (Teil 4).html` — all 5 `SUPERBASE-Steckbrief` callouts (FIND, ENTER, SELECT, OUTPUT, PROG) extracted from yellow callout boxes on print pages 166–167. Each emitted as `<figure><table class="plain">…</table><figcaption>SUPERBASE-Steckbrief: X-Menü</figcaption></figure>` and placed between the FIND-Modus discussion and the Centronics-Schnittstelle section. PROG-Menü figure additionally contains two subheading `<p>` markers ("Möglichkeiten der Befehlszeile:" and "Befehle der Datenbanksprache") plus the trailing "Anmerkung:" paragraph that explains the »I«/»II« primary/secondary command marker convention (the Anmerkung appears inside the same yellow box in print, so it stays inside the figure). PDEF x value in the PROG figure preserves the multi-line print layout via `<br>` (six lines for codes 0/1/2/5/6). Row counts: FIND 14, ENTER 10, SELECT 14, OUTPUT 19, PROG 5 (Befehlszeile) + 11 (Datenbanksprache). Print verbatim preserved: row 13 of FIND uses "Umgehung" while row 14 uses "Umgebung" — both kept as printed. Centronics pinout `TODO TABLE` was already replaced in the earlier pass.

## Pass 3 — UNCAPTIONED callouts extracted (rule 13 Pass 3 sweep)

- `22 Die Wachstumspyramide.html` — added `<aside><h3>Verwendete Variable</h3>` with three nested `<table class="plain">` blocks (a) Felder, b) Strings, c) Numerische Variable) from print page 24. Removed adjacent OCR-garbage occurrence of the literal heading "Verwendete Variable" that the prior import had dropped into the body paragraph immediately preceding the callout (was: "Eine stärker besetzte Verwendete Variable Elterngeneration bekommt").
- `33 Selbstbau Das richtige Kabel zum Monitor.html` — added single `<aside>` with eight nested `<table class="plain">` Pin/Signal lookup blocks from print page 34 (Audio-/Video-Stecker, 6poliger AV-Stecker, 9poliger Cannon-Stecker, 6poliger AV-Stecker [second variant for C 128 80-Zeichen-Modus], Audio-/Video-Buchse, SCART-Stecker, "Belegung der 80-Zeichen-Videobuchse", SCART-Stecker [C 128 RGB variant]). Note: the Audio-/Video-Stecker row "Pin 2 = SND" is a print typo for GND, preserved verbatim per rule.
- `28 Die totale Kommunikation.html` — added `<aside><h3>Leistungen des Breitband-ISDN</h3>` with one `<table class="plain">` (14 rows: Hörfunk/Fernsehen … Fernwirken (Temex)) from print page 40, inserted right after the Breitband-ISDN paragraph.
- `42 Seikosha MP-1300 AI - Geschwindigkeit ist Trumpf.html` — added `<figure><table class="plain"> … <figcaption>Tabelle. Das Datenblatt des Seikosha MP-1300AI</figcaption></figure>` from print page 43 (17 data rows, mixed paired-/full-width layout).
- `43 CRA-80X — der vielseitige Drucker.html` — added `<figure><table class="plain"> … <figcaption>Tabelle. Kurz belichtet — Melchers CPA-80X</figcaption></figure>` from print page 44 (17 data rows, same layout as Seikosha).
- `147 Lernen Sie Ihren Drucker kennen!.html` — added captioned `<figure>` for `Tabelle. Übersicht über die möglichen Grafik-Modi bei Epson-, Star- und MPS-Druckern` (print page 149). The figure contains three sub-tables: (1) main grafik-modi grid with columns Modus | Epson | Star »IBM«-Modus | Star »Star«-Modus (8-Nadeln subsection + 9-Nadeln subsection), (2) two-column `<table class="plain">` for "Grafikmodus für MPS 801/803" + "Sonderzeichendefinition des MPS 802", (3) "Zusammenhang zwischen Daten und Matrixpunkt" Wert/Bit lookup table for Epson/Star vs MPS 801/803, plus the two `Beispiel:` lines as a `<p>` inside the same `<figure>`.

## No [ILLEGIBLE] cells

No cells were marked `[ILLEGIBLE]`. All cell values were verified against the print scan or the on-disk OCR pipeline output.

## Print typos preserved verbatim

- `139 Von Basic zu Assembler.html` — Tabelle 1 row "Indirekt | 3 | JMP($,4301)" preserves the printed comma inside the parenthesis (likely a typesetting error in the magazine; kept as-is).
- `89 Newsroom druckt deutsch.html` — Tabelle row "eck. Klammer l." uses lowercase `l` (the print shows lowercase L, not capital I); the previous HTML had `I` which was wrong.
