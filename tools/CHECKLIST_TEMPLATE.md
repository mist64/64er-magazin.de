# Article Conversion Checklist Template

Use one checklist file per article conversion run.
Status rule: if any checkbox is unchecked, the article status is `partial`.

## Article

- `issue`: `8604`
- `start_page`:
- `toc_title`:
- `real_title`:
- `output_html`:
- `run_id`:
- `open_issues_count`: ``
- `residual_defects`: ``

## Unresolved Ledger

- List every unresolved issue with:
  - file line
  - short reason
  - planned resolution
- If none, write `none`.

## Phase Checklist

- [ ] 1. Identify boundaries
  - Evidence:
  - `pages_included`:
  - `ad_pages_excluded`:

- [ ] 2. Run Tesseract OCR (per-page → concatenate)
  - Evidence:
  - `pages_ocrd`:
  - `raw_file`:
  - `ocr_command`:

- [ ] 3. Create initial HTML shell
  - Evidence:
  - Metadata present:
  - `index_title` commented+empty:

- [ ] 4. Mechanical import pass (from extracted text only)
  - Evidence:
  - Import method:
  - Memory-written prose used: `no`

- [ ] 5. Structure pass
  - Evidence:
  - `heading_inventory` (scan page, visual treatment, assigned level for EVERY heading):
  - `intro`:
  - `noindent/strong`:
  - `pre/table/figure/address`:

- [ ] 6. OCR correction pass (`prose_pass`, paragraph-by-paragraph vs scan)
  - Evidence:
  - Pages checked:
  - Notes:

- [ ] 7. Technical fidelity pass (`technical_pass`)
  - Evidence:
  - Listings:
  - Tables:
  - Symbols/notation:
  - Listing quality ledger (`start/end/opcode-sequence/unknown_tokens`):

- [ ] 8. Bild/Tabelle positioning pass
  - Evidence:
  - Placement map (`reference -> figure`):
  - Reference proof (`OCR/scan line -> HTML line -> asset`):

- [ ] 9. Asset validation
  - Evidence:
  - All referenced files exist:
  - Orphan article assets handled:

- [ ] 10. Coverage validation
  - Evidence:
  - Page coverage confirmed:
  - Continuation pages confirmed:

- [ ] 11. Final QA gate
  - Evidence:
  - HTML sanity:
  - Author normalization:
  - Unresolved issues:
  - `open_issues_count = 0`:
  - `residual_defects = none`:
  - Synthetic prose additions (count):

- [ ] 11b. Objective lint checks
  - Evidence:
  - OCR-noise grep (for example `1 da|Ida|Kl I|I\\^`):
  - Variable confusion grep (for example `\\bZl\\b|\\bSl\\b`):
  - Asset existence/orphan check:
  - Result: `pass/fail`

- [ ] 12. Completion report prepared
  - Evidence:
  - Pages OCR'd and raw file:
  - Output path:
  - Placement list:
  - Remaining uncertainty:

## Completion Lock

- [ ] All checkboxes above are checked.
- [ ] Lock integrity verified (`phase 11 checked`, `phase 11b pass`, `open_issues_count = 0`).

Only when this box is checked may the article be reported as `done`.
