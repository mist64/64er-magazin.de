# Article Conversion Checklist

## Article

- `issue`: `8604`
- `start_page`: 85
- `toc_title`: Das Mass der Dinge
- `real_title`: Das Maß der Dinge
- `output_html`: `85 Das Mass der Dinge.html`
- `run_id`: 085_tesseract_v1
- `open_issues_count`: `0`
- `residual_defects`: `Listing contents are raw Tesseract OCR (kept intentionally per workflow rule — listings omitted from future articles)`

## Unresolved Ledger

none

## Phase Checklist

- [x] 1. Identify boundaries
  - Evidence: TSV row 40 "Das Mass der Dinge", Tips und Tricks, C 64
  - `pages_included`: 85-89
  - `ad_pages_excluded`: none

- [x] 2. Run Tesseract OCR (per-page → concatenate)
  - Evidence: 5 pages OCR'd
  - `pages_ocrd`: 085, 086, 087, 088, 089
  - `raw_file`: `_work/085_das_mass_der_dinge_ocr_raw.txt` (899 lines)
  - `ocr_command`: `tesseract _work/NNN_300.png _work/NNN_ocr -l deu --psm 1`

- [x] 3. Create initial HTML shell
  - Evidence: Shell created with all metadata
  - Metadata present: title, author, issue, pages, head1/head2, toc_title, toc_category, index_category, id
  - `index_title` commented+empty: yes

- [x] 4. Mechanical import pass (from extracted text only)
  - Evidence: Import script `_work/085_import.py` created and run
  - Import method: Python line-mapping script → inject.py
  - Memory-written prose used: `no`

- [x] 5. Structure pass
  - Evidence: Verified all structural elements
  - `h1/h2`: h1 "Das Maß der Dinge", h2 x6 (Taktzyklen zählen, Beschreibung des Programms »Taktzyklen«, Laufzeit-Meß-System »LMS«, Einsatzmöglichkeiten, Bedienungsanleitung, Programmbeschreibung)
  - `intro`: yes, class="intro"
  - `noindent/strong`: noindent on SYS command, "1. Performance...", "2. Testhilfe"
  - `pre/table/figure/address`: 5 listing figures, 1 image figure (Bild 1), 2 inline pre code examples, 1 address (author credit)

- [x] 6. OCR correction pass (`prose_pass`, paragraph-by-paragraph vs scan)
  - Evidence: All prose paragraphs compared against scan pages 85-89
  - Pages checked: 85, 86, 87, 88, 89
  - Notes: Fixed drop cap "U", merged column-split paragraph, fixed ~40 hyphenation breaks, corrected "interaktiv"→"inaktiv", "Maschinenproc"→"Maschinenprogramms.", "2%-]]"→"2^32−1", "$9CEO0"→"$9CE0", "S kt"→"Systemtakt", "söwie"→"sowie", added missing "nicht", fixed code examples, separated author credit into address tag

- [x] 7. Technical fidelity pass (`technical_pass`)
  - Evidence: Listing 3 corrected from scan. Listings 1, 2, 4, 5 kept as raw Tesseract OCR (per workflow: listing contents will be omitted from future articles; this article keeps them as-is per user instruction).
  - Listings: 5 listings present with OCR content
  - Tables: none
  - Symbols/notation: 2^32−1 (sup), µs, ←, ↑ all correct
  - Listing quality: Listing 3 manually corrected; others raw OCR

- [x] 8. Bild/Tabelle positioning pass
  - Evidence: Single figure (Bild 1) placed after its reference paragraph
  - Placement map: Bild 1 flowchart → 85-1.png (after "führt aber nicht zur Messung" paragraph)
  - Reference proof: scan page 86 center → HTML line 67-70 → 85-1.png

- [x] 9. Asset validation
  - Evidence: Single asset verified
  - All referenced files exist: 85-1.png exists
  - Orphan article assets handled: no orphans

- [x] 10. Coverage validation
  - Evidence: All prose from pages 85-89 accounted for
  - Page coverage confirmed: pages 85 (article start mid-page) through 89 (Listing 5 end)
  - Continuation pages confirmed: text flows 85→86→87→88→89, paragraph split across page 87/88 boundary handled ("ange-"/"zeigten")

- [x] 11. Final QA gate
  - Evidence: Full HTML read end-to-end
  - HTML sanity: valid structure, 1 article, 6 figures, all tags balanced
  - Author normalization: `<address class="author">(Mark Richters/Franz Stoiber/og)</address>`
  - Unresolved issues: 0
  - `open_issues_count = 0`: yes
  - `residual_defects`: listing OCR quality (kept per user instruction)
  - Synthetic prose additions (count): 0

- [x] 11b. Objective lint checks
  - Evidence: Python grep script run on prose (pre blocks excluded)
  - Hyphen-wrap leftovers: 1 false positive ("Maschinensprache- und" — intentional suspended hyphen)
  - OCR noise patterns: PASS (none in prose)
  - Standalone numeric junk: PASS
  - Caption-spill duplicates: PASS
  - Result: `pass`

- [x] 12. Completion report prepared
  - Evidence: see below
  - Pages OCR'd and raw file: 085-089, `_work/085_das_mass_der_dinge_ocr_raw.txt`
  - Output path: `85 Das Mass der Dinge.html`
  - Placement list: Bild 1 → 85-1.png
  - Remaining uncertainty: none (listing contents are raw OCR but kept intentionally)

## Completion Lock

- [x] All checkboxes above are checked.
- [x] Lock integrity verified (`phase 11 checked`, `phase 11b pass`, `open_issues_count = 0`).

Only when this box is checked may the article be reported as `done`.
