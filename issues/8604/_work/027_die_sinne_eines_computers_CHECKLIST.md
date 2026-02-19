# Article Conversion Checklist

## Article

- `issue`: `8604`
- `start_page`: `27`
- `toc_title`: `Die Sinne eines Computers`
- `real_title`: `Die Sinne eines Computers`
- `output_html`: `27 Die Sinne eines Computers.html`
- `run_id`: `027_session2`
- `open_issues_count`: `0`
- `residual_defects`: `none`

## Unresolved Ledger

`none`

## Phase Checklist

- [x] 1. Identify boundaries
  - Evidence: TOC entry "Die Sinne eines Computers" pages 27-29, MSR section
  - `pages_included`: `27, 28, 29`
  - `ad_pages_excluded`: `none`

- [x] 2. Run Tesseract OCR (per-page → concatenate)
  - Evidence: 600 DPI masters downscaled to 300 DPI, Tesseract with `-l deu --psm 1`
  - `pages_ocrd`: `27, 28, 29`
  - `raw_file`: `_work/027_die_sinne_eines_computers_ocr_raw.txt` (708 lines)
  - `ocr_command`: `for p in 027 028 029; do tesseract _work/${p}_300.png stdout -l deu --psm 1; done`

- [x] 3. Create initial HTML shell
  - Evidence: Shell with all metadata fields populated
  - Metadata present: `yes` (issue, pages, head1, toc_title, toc_category, index_category, id)
  - `index_title` commented+empty: `yes`

- [x] 4. Mechanical import pass (from extracted text only)
  - Evidence: `_work/027_import.py` with line-number mappings for 25 paragraphs + 13 figures
  - Import method: `027_import.py → inject.py`
  - Memory-written prose used: `no`

- [x] 5. Structure pass
  - Evidence:
  - `heading_inventory` (scan page, visual treatment, assigned level for EVERY heading):
    - "Potentiometer" — p.27, rule above+below → h2
    - "Materialprüfung" — p.27, rule above+below → h2
    - "Mengenmessung" — p.28, rule above+below → h2
    - "Längenmessung" — p.28, rule above+below → h2
    - "Aktive Thermofühler" — p.28, rule above+below → h2
    - "Strom durch Druck" — p.29, rule above+below → h2
    - "Geschwindigkeits- und Drehzahlmessung" — p.29, rule above+below → h2
  - `intro`: `yes` (subtitle block with class="intro")
  - `noindent/strong`: `none needed`
  - `pre/table/figure/address`: `13 figures (Bild 1–13), no tables, no listings, no addresses`

- [x] 6. OCR correction pass (`prose_pass`, paragraph-by-paragraph vs scan)
  - Evidence:
  - Pages checked: `27, 28, 29`
  - Notes: Fixed ~100 hyphenation breaks across all paragraphs. Key corrections:
    - "Bild ]" → "Bild 1" (OCR misread)
    - "gibtesin" → "gibt es in" (merged words)
    - "Termperaturkoeffizieten" → "Temperaturkoeffizienten" (double-m, missing n)
    - "rungist. Beiden" → "rung ist. Bei den" (split merged words)
    - OCR gap at Materialprüfung para: inserted missing "(DMS). Die Wirkungsweise schnell er-"
    - "0,1]" → "0,01" (OCR misread)
    - "gemesssen" → "gemessen" (triple-s)
    - "MeBlei-tung" → "Meßleitung" (OCR garble)
    - "und Il" → "und 11" (OCR misread)
    - Missing line 412 "werden schon anhand des" restored in Längenmessung para
    - "Induktivitätt" → "Induktivität" (double-t)
    - "Referenzspulle" → "Referenzspule" (double-l)
    - "miteiner Referenz-undeiner" → "mit einer Referenz- und einer"
    - "vVerbindungsstelle" → "Verbindungsstelle" (doubled V)
    - "Thermselemmente" → "Thermoelemente" (garbled caption)
    - "dereineum" → "der eine um" (three merged words)
    - "piezoelektisch" → "piezoelektrisch" (missing r)
    - "chneller" → "schneller" (missing s)
    - "Legtman anei-nen" → "Legt man an einen"
    - "istneben" → "ist neben"
    - Added missing periods after "leiten sie", "verstimmt", "Verbindungsstelle", "Durchflußgeschwindigkeit", "Luftmengen-Messung"
    - Removed OCR noise: trailing apostrophe, "°" after Druckdose, double dot ". ."

- [x] 7. Technical fidelity pass (`technical_pass`)
  - Evidence:
  - Listings: `none`
  - Tables: `none`
  - Symbols/notation: `°C` preserved correctly; `»«` guillemets correct
  - Listing quality ledger: `N/A`

- [x] 8. Bild/Tabelle positioning pass
  - Evidence:
  - Placement map:
    - Bild 1 ref line 33 → figure line 35
    - Bild 2 ref line 42 → figure line 44
    - Bild 3 ref line 55 → figure line 57
    - Bild 4 ref line 55 → figure line 62
    - Bild 5 ref line 67 → figure line 69
    - Bild 6 ref line 74 → figure line 76
    - Bild 7 ref line 81 → figure line 83
    - Bild 8 ref line 92 → figure line 94
    - Bild 9 ref line 101 → figure line 103
    - Bild 10 ref line 110 → figure line 112
    - Bild 11 ref line 110 → figure line 117
    - Bild 12 ref line 124 → figure line 126
    - Bild 13 ref line 124 → figure line 131
  - Reference proof: All 13 figures placed immediately after the paragraph containing their first reference

- [x] 9. Asset validation
  - Evidence:
  - All referenced files exist: `yes` (27-1.png through 27-13.png all present)
  - Orphan article assets handled: `no orphans`

- [x] 10. Coverage validation
  - Evidence:
  - Page coverage confirmed: `yes` (pages 27-29 fully covered)
  - Continuation pages confirmed: `N/A` (article is self-contained)

- [x] 11. Final QA gate
  - Evidence:
  - HTML sanity: `valid` (proper nesting, no unclosed tags)
  - Author normalization: `no author credited in article`
  - Unresolved issues: `none`
  - `open_issues_count = 0`: `yes`
  - `residual_defects = none`: `yes`
  - Synthetic prose additions (count): `0`

- [x] 11b. Objective lint checks
  - Evidence:
  - OCR-noise grep (`Il\b|Sl\b|1da`): `0 matches`
  - Residual hyphenation grep (`[A-Z][a-z]- [a-z]`): `0 matches`
  - Double-space in text: `0 matches` (all matches are HTML indentation)
  - Stray punctuation (`\. \.` or `&#x27;`): `0 matches`
  - Asset existence/orphan check: `pass` (13/13 files present)
  - Result: `pass`

- [x] 12. Completion report prepared
  - Evidence:
  - Pages OCR'd and raw file: `27-29`, `_work/027_die_sinne_eines_computers_ocr_raw.txt`
  - Output path: `27 Die Sinne eines Computers.html`
  - Placement list: 13 figures (Bild 1–13), 7 h2 headings, 0 h3, 0 listings, 0 tables
  - Remaining uncertainty: `none`

## Completion Lock

- [x] All checkboxes above are checked.
- [x] Lock integrity verified (`phase 11 checked`, `phase 11b pass`, `open_issues_count = 0`).

Article status: `done`
