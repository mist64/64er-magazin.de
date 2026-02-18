# 8604 Conversion Workflow (Living Document)

This file is intentionally iterative and will be updated and improved during the conversion.

## Goal

Convert `8604/8604.md` (OCR dump) + scanned issue pages into repository-style HTML files in `8604/`, aligned with existing issue folders (for example `8603/`).

## Agreed Ground Rules

- Primary text source is `8604/8604.md`.
- Scanned page images / PDF pages are mandatory for verification and correction.
- TOC wording can differ from the on-page article title.
- On-page title and on-page start page always win over TOC when they conflict (TOC errors are ignored).
- `index_title` is currently not set from this workflow and must remain commented out in generated HTML until provided from another source.
- Generic anti-memory rule: avoid writing content from memory as much as possible.
- Prefer extraction, copy, and incremental edits over manual retyping.
- No false done rule: if unresolved OCR or structure issues remain, status must be `partial`.

## TOC Workflow

### 1. Reconstruct TOC from issue TOC pages

- Build a clean TOC from TOC pages in the PDF (not from noisy OCR alone).
- Maintain section order exactly as printed.
- Keep canonical artifacts:
  - `8604/8604_toc_reconstructed.md`
  - `8604/8604_toc_reconstructed.tsv`

### 2. Maintain improved TOC manifest

Use `8604/8604_toc_improved.tsv` as the working manifest with these fields:

- `section`
- `subsection`
- `toc_title`
- `start_page`
- `toc_pages`
- `real_title`
- `pages_raw`
- `ad_pages_excluded`
- `pages_included`
- `include_listings`
- `notes`
- `status`

Required per-entry review:

1. Open the start page and extract `real_title` from the actual page header.
2. Determine all pages that belong to the article.
3. Exclude pure ad pages via `ad_pages_excluded`.
4. Include listing pages that belong to the article in `pages_included`.

Current implementation notes:

- `8604/8604_toc_improved.tsv` is populated and in active use.
- `real_title` is currently filled for all rows:
  - verified on-page title where confirmed
  - otherwise temporary fallback to `toc_title` until visual verification
- `pages_included` / `ad_pages_excluded` are currently mixed quality:
  - manually verified for pilot rows and explicit corrections
  - auto-estimated for most other rows
- Status values in `status`:
  - `pilot_verified`
  - `manually_adjusted_needs_manual_review`
  - `auto_estimated_needs_manual_review`
- Any row with `auto_estimated_*` must still be visually checked before finalization.

## toc.txt Workflow

Create/maintain `8604/toc.txt` in the same style as other issues:

- Main sections only.
- Correct section order.
- Correct upper/lower case.

Current target content:

- Aktuelles
- Hardware-Test
- Messen - Steuern - Regeln
- Hardware
- Wettbewerbe
- Listings zum Abtippen
- Tips und Tricks
- 64'er Extra
- Kurse
- Spiele-Test
- Software-Test
- Software-Hilfen
- Rubriken

## HTML Generation Rules

For each TOC entry (one HTML per TOC line):

- File naming follows issue conventions: `<start-page> <title>.html`.
- Metadata mapping:
  - on-page title -> `<title>`, `<h1>`, usually `64er.index_title` (but currently keep index title disabled; see below)
  - TOC wording -> `64er.toc_title`
- `64er.index_title` handling (current rule):
  - Keep commented out and empty:
  - `<!-- <meta name="64er.index_title" content=""> -->`

Use standard metadata fields where available:

- `author`
- `64er.issue` (`4/86`)
- `64er.pages`
- `64er.head1`
- `64er.head2`
- `64er.toc_title`
- `64er.toc_category`
- `64er.index_category`
- `64er.id`

Lead text rule:

- The subtitle/lead directly under `<h1>` should be encoded as `<p class="intro">...</p>`, not `<blockquote>`.

Leserforum format:

- Use `article` with class `qa`.
- Add header image block first:
  - `<header><img src="<startpage>-0.png" alt="Leserforum" title="Leserforum"></header>`
- For cleanly separable items use:
  - `<section><h2>...</h2> ... </section>`
  - question blocks in `<div class="q">...</div>`
  - answer blocks in `<div class="a">...</div>`
  - sender/signature lines as `<p class="author">...</p>`
  - contact/info lines as `<p class="source">...</p>`
- If OCR quality prevents reliable structural splitting, prefer a faithful line-preserving conversion from extracted text over guessed restructuring.

Image/Bild integration rule:

- Include article images from filesystem using the naming scheme based on the article start page and Bild number.
- Pattern: `<startpage>-<bildnummer>.png` (example: for start page `20`, use `20-1.png`, `20-2.png`, ...).
- Add matching `<figure><img ...><figcaption>Bild n. ...</figcaption></figure>` blocks in article order.
- Placement rule (required): always place each image figure immediately after the paragraph that mentions that Bild reference (for example after the paragraph containing `Bild 1`).
- If an image is not explicitly mentioned in text, inspect the PNG file directly (vision) and place it at the most probable editorial position based on content match.
- For unreferenced images, use this order:
  1. map image content to the matching teaser/paragraph heading
  2. place the figure directly after that matched paragraph block
  3. if no reliable match is possible, keep source image order and place near the nearest plausible block, and note uncertainty in TSV `notes`
- If no article PNG assets exist for the start page, do not invent image figures.
- Special case: files matching `*-0*.png` are usually unnumbered and uncaptioned teaser/lead images; place them near the article start, typically directly below the lead/intro block.

Figure placement rule for Tabellen:

- Treat `Tabelle` entries like `Bild` entries at markup level:
  - always wrap them in `<figure>...</figure>` with a `<figcaption>` like `Tabelle n. ...`
  - if the table is transcribed as HTML, keep semantic `<table>` inside the `<figure>`
- Place every `Tabelle` immediately after the first paragraph that references it in running text.
- Do not leave standalone `Tabelle` headings as plain `<p>` blocks when a figure/table is present.
- Do not keep duplicated caption-spill paragraphs like `<p>Bild n. ...</p>` when the same text is already in adjacent `<figcaption>`.

## OCR Cleanup Policy

Conservative normalization only:

- Always start article text from a direct line-range extraction out of `8604/8604.md`.
- Never draft article prose from memory (for example by writing full text directly in a heredoc such as `cat <<EOF ...`).
- Extraction method (required):
  - identify start/end line numbers in `8604/8604.md`
  - extract with `cut` from numbered lines, for example:
  - `nl -ba 8604/8604.md | sed -n '<start>,<end>p' | cut -f2-`
- Build/refresh HTML text from that extracted block before applying any cleanup edits.
- Do not begin from manually retyped prose.
- Fix obvious missing spaces and broken word joins.
- Fix obvious `l/I` and `0/O` OCR confusion when unambiguous.
- Preserve code/listings with minimal alteration.
- Escape HTML-sensitive characters in code/listing blocks (for example `<`, `<=`, `<>`).
- Do not introduce synthetic prose lines that are not in extracted text or scan evidence.
  - Example: do not add standalone `Bild n ...` paragraphs just to force placement.

Post-extraction editing workflow (required):

These steps are mandatory for every article. Do all of them.
All transformations must be edits on top of the `cut` extraction output.
Do not rebuild prose from scratch at any stage.

1. Extract raw block from `8604.md` with `nl|sed|cut` into `8604/_work/*_ocr_raw.txt`.
2. Build an initial HTML draft by importing that extracted text verbatim (line-preserving).
3. Structural pass:
   - convert headings to appropriate tags (`h1`, `h2`, etc.)
   - convert lead to `<p class="intro">` where applicable
   - split Q/A or section blocks into repository pattern (`section`, `div.q`, `div.a`, `author`, `source`, etc.) when clearly supported by scan/OCR
4. Text repair pass:
   - fix OCR joins/splits, obvious character confusions, punctuation spacing
   - merge hyphenated line breaks where the scan confirms a continuous word
5. Asset pass:
   - place images/listings/tables according to image and mention rules
6. Verification pass:
   - compare paragraph-by-paragraph against scans
   - record non-obvious decisions in TSV `notes`
7. Finalization pass:
   - ensure metadata is correct and `index_title` remains commented/empty
   - keep the raw extraction file for provenance
8. Post-build inspection pass (required):
   - read the resulting HTML file itself end-to-end (not only diffs)
   - record every deviation from house style in the checklist unresolved ledger
   - do not mark done before all recorded deviations are either fixed or explicitly kept as unresolved

Mandatory formatting/markup during verification pass:

- For every paragraph, compare OCR text against the page image and correct all confirmed OCR errors.
- Add `<strong>...</strong>` for text that is printed bold in the scan (including bold lead-ins within paragraphs).
- Use `<p class="noindent">...</p>` for paragraphs that are visually flush-left (new paragraph without first-line indent).
- Transcribe inline tabular content as semantic HTML `<table>` (use `table.plain` where appropriate), not as plain paragraph lines.
- For printed overline notation, use explicit markup with `text-decoration:overline` (for example `<span style="text-decoration:overline">...</span>`).
- Convert trailing author credits in article form (for example `(Marcus Plewa/kn)`) to `<address class="author">(...)</address>` following repository style.
- Remove OCR-spill paragraphs that are only detached line-number runs or fragment remnants (for example isolated `30`, `130 140 150`, `ready.`) when they are clearly not running prose.

Implementation constraint:

- Every structural change (`section`, `div.q`, `div.a`, headings, author/source tags), every OCR correction, and every placement decision must be applied as incremental edits to the extracted base text.
- Never type article body text from memory; only move/split/merge/correct text that already exists in the extraction and is confirmed by scans.
- Run an OCR-noise grep after each major edit (for example `Ida|1 da|Zl|Sl|cOOO|Kl I|I\^`) and add findings to the checklist before phase lock.

## Verification Policy

Before finalizing each article:

1. Compare against start and continuation page images.
2. Compare paragraph-by-paragraph against the page image and correct OCR spacing/character errors.
3. Verify title, headings, body text, names, numbers.
4. Verify page coverage against `pages_included`.
5. Confirm ad-page exclusion decisions.

## Pilot Status

Pilot article completed:

- `8604/63 Grafik Druckprogramm zu Database.html`
- Verified rule demonstrated:
  - on-page title `Schwarz auf weiß`
  - TOC title `Grafik Druckprogramm zu Database`

## Batch Execution Plan

- Process in small batches (suggestion: 10 entries at a time).
- For each batch:
  - Fill `real_title`
  - Finalize `pages_included`
  - Generate/clean HTML
  - Verify with page images
  - Update `status` and `notes` in improved TSV

## Best Practices Learned So Far

- Start/end boundaries: determine article boundaries from scanned page layout first, then confirm with `8604.md` line range.
- Provenance: always keep the extracted OCR source block under `8604/_work/*_ocr_raw.txt` for traceability.
- Two-pass text handling:
  1. direct `cut` extraction into working text
  2. paragraph-by-paragraph correction against scan
- OCR normalization: fix only what is visually confirmed on scan; avoid stylistic rewrites.
- Split-line repair: aggressively repair OCR line-break artifacts (for example `Mit-` + `gliedern`, split words around punctuation) only when unambiguous on scan.
- Metadata discipline:
  - on-page title in `<title>` and `<h1>`
  - TOC wording in `64er.toc_title`
  - keep `64er.index_title` commented and empty
- Lead styling: use `<p class="intro">` for lead/subtitle text directly under `<h1>`.
- Image handling:
  - verify each candidate image with vision before placement
  - include only images that match this article's content
  - do not force all same-start-page images into one article
- Multi-item pages: when one magazine page contains multiple TOC entries, assign text/images by visual ownership, not only by page number.
- Listings: include listing continuation pages in `pages_included` when they belong to the article, even if the prose mostly ends earlier.
- Manifest notes: record non-obvious decisions (page range overrides, excluded/unused images, uncertain placements) in TSV `notes`.

## Fidelity Mode (Strict)

Use this mode whenever highest fidelity is required.

1. No summarization or paraphrase:
   - Do not condense, rewrite, or simplify prose.
   - Preserve content and order from extracted text; only fix OCR errors confirmed on scan.

2. Line coverage accounting:
   - Track each extracted line/paragraph as one of: `kept`, `merged`, `split`, `dropped`.
   - Any dropped line needs explicit reason (for example running header/footer noise).

3. Multi-column reading order:
   - Confirm and follow printed reading order before edits.
   - Do not reorder paragraphs for style.

4. Page-noise whitelist:
   - Only remove running heads/footers, page numbers, and issue/date footer lines.
   - Keep everything else unless explicitly identified as foreign/ad content.

5. Table fidelity:
   - Transcribe inline tables fully before normalization.
   - Keep symbols, units, and labels exactly unless scan clearly shows OCR error.

6. Symbol fidelity:
   - Preserve control symbols and notation (`^`, `£`, `*`, `C=`, arrows, etc.).
   - Mark all confirmed overlined signal names with `text-decoration:overline` in running text.

7. Command/listing fidelity:
   - Use `pre`/table structures for command matrices and bit-pattern examples.
   - Do not convert technical blocks into summarized prose.

8. Structural conversion order:
   - First produce faithful text conversion.
   - Then apply structural markup (`strong`, `noindent`, `table`, `figure`) without changing meaning/content.

9. Figure/table placement proof:
   - Place each `Bild`/`Tabelle` right after first textual reference.
   - If unreferenced, mark placement as best guess in TSV `notes`.

10. Author normalization:
   - Trailing author credits like `(Name/xx)` must be `<address class="author">(...)</address>`.

11. Completion gate:
   - No unresolved OCR artifacts in kept text.
   - All references resolved (Bild/Tabelle/Listing).
   - Paragraph-by-paragraph scan check done.

12. Stop on uncertainty:
   - If a block is ambiguous, flag exact line(s) instead of guessing.

13. Unresolved-issue accounting:
   - Keep an explicit unresolved ledger during conversion.
   - Every unresolved item must include file line and reason.
   - Completion is blocked until unresolved count is zero.

## Execution Contract (Required For `do page X` / `do article X`)

This is the mandatory sequence. Do not skip steps. Do not report completion before step 12 is done.

1. Identify boundaries:
   - Resolve start/end from `8604_toc_improved.tsv` and `8604/8604.md`.
   - Confirm real start page and continuation pages from scans.

2. Extract source text:
   - Extract with `nl | sed | cut` into `8604/_work/<article>_ocr_raw.txt`.
   - All article text edits must be applied on top of this extraction.

3. Create initial HTML shell:
   - Add metadata, `h1`, and intro placeholder.
   - Keep `index_title` commented and empty.
   - Body placeholder must be exactly: `        <!-- BODY WILL BE MECHANICALLY IMPORTED -->`

4. Mechanical import pass:
   - Copy the import template: `cp _work/IMPORT_TEMPLATE.py _work/<NNN>_import.py`
   - Edit the copy: set `RAW` path, fill in article-specific line mappings.
   - Available helpers (see template for full API):
     - `p(cls, *line_nums)` — emit `<p>` from raw lines (merges with space)
     - `h(level, line_num)` — emit heading
     - `blank()` — readability separator
     - `raw(text)` — emit raw HTML (figures, tables)
     - `basic_listing(start, end)` — emit BASIC listing table (`plain right0`)
     - `tsv_table(header, start, end)` — emit tab-separated table (`plain pre`)
   - Run: `python3 _work/<NNN>_import.py > _work/<NNN>_body.html`
   - Inject into shell: `python3 _work/inject.py "<HTML_FILE>" "_work/<NNN>_body.html" "<address_text>"`
   - No rewriting from memory at any point.

5. Structure pass:
   - Convert headings, intros, `noindent`, `strong`, `pre`, `table`, `figure`, `address`.
   - Build special structures (for example `div.q`/`div.a`) only when scan supports it.

6. OCR correction pass (`prose_pass`):
   - Paragraph-by-paragraph visual compare against page images.
   - Fix only confirmed OCR errors.

7. Technical fidelity pass (`technical_pass`):
   - Listing/table/formula/symbol verification is mandatory and separate from prose.
   - Ensure all listings/tables are fully transcribed and not collapsed into prose.
   - Keep symbols/control notation exact.
   - For each `Listing n`, record:
   - `start line verified`
   - `end line verified`
   - `opcode/register sanity`
   - `line-number sequence sanity`
   - `unknown tokens count`
   - If `unknown tokens count > 0`, article cannot be `done`.

8. Bild/Tabelle positioning pass (mandatory):
   - For each `Bild` and `Tabelle`, find first textual reference.
   - Place matching `<figure>` immediately after that paragraph.
   - If unreferenced, place by strongest visual/content match and note in TSV `notes`.
   - Record placement proof for each item:
   - source reference line (OCR line or scan evidence)
   - final HTML line
   - asset filename

9. Asset validation:
   - Confirm every referenced image file exists.
   - Confirm there are no orphaned article images left unhandled.

10. Coverage validation:
   - Confirm page coverage including continuation/listing pages.
   - Confirm ad-only pages excluded.

11. Final QA gate:
   - No unresolved placeholders or malformed HTML blocks.
   - Author credit normalized to `<address class="author">...</address>`.
   - All Bild/Tabelle/Listing references resolved.
   - Unresolved issue count must be zero.
   - Synthetic prose additions must be zero unless explicitly justified with evidence.
   - Run objective grep/lint checks for common OCR artifacts and record results.
   - Verify no duplicated caption-spill body paragraphs remain (`<p>Bild n...` / `<p>Tabelle n...` adjacent to same `<figcaption>`).
   - Verify no standalone numeric OCR-junk paragraphs remain unless intentional (`^\d+( \d+)*$`).
   - Verify `residual_defects` is present and equals `none`.

12. Completion report format:
   - When reporting done, always include:
   - extracted line range used
   - output HTML file path
   - list of Bild/Tabelle placements (`reference paragraph -> figure`)
   - unresolved/uncertain items (if any)
   - unresolved issue count
   - grep/lint check summary

## Failure Policy

If any mandatory pass above is not finished, report status as `partial`, not `done`.
If checklist claims conflict with file reality, status must be `partial`.

## Hard Quality Gates

These rules are blocking. If any one fails, status is `partial`.

1. No quality downgrade:
   - Do not replace uncertain OCR with normalized guesses.
   - If uncertain, keep token and log as unresolved; do not silently "improve" it.

2. Cleanup vs normalization:
   - Cleanup fixes (spacing, `l/1`, `0/O`) require scan confirmation.
   - Normalization (notation/style modernization) is forbidden unless explicitly approved.

3. Paragraph ledger:
   - Every paragraph must be marked `verified`, `corrected`, or `uncertain`.
   - Any `uncertain` paragraph blocks `done`.

4. Scan evidence pointers:
   - Every non-trivial correction must record concise scan evidence (`page + region note`) in checklist notes.

5. Residual defects:
   - Checklist must include `residual_defects`.
   - `done` allowed only when `residual_defects: none`.

6. Objective defect scans (fail-on-hit):
   - Hyphen-wrap leftovers in prose: `[A-Za-zÄÖÜäöüß]-[A-Za-zÄÖÜäöüß]`
   - Known listing garbage tokens (project-maintained pattern list)
   - Standalone numeric junk paragraphs (`<p>^\\d+( \\d+)*$</p>`) unless intentional

7. Final reviewer script:
   - Run local lint/reviewer script that aggregates hard checks.
   - Checklist lock may be checked only if script result is `PASS`.

8. Status semantics:
   - `done`: zero unresolved items + all hard gates pass.
   - `partial`: anything else.

## Anti-Memory Enforcement (Mandatory)

The extraction-first workflow exists to prevent hallucinated or paraphrased prose from entering articles. These enforcement rules make the constraint mechanically verifiable, not just advisory.

### Why this matters

LLMs bias toward generating plausible-sounding text from training data. For a faithful OCR transcription project, this is the primary failure mode: the model "knows" what the article probably says and writes it from memory instead of from the actual OCR source. The result looks correct but may silently differ from what was printed.

### Enforcement rules

1. Mandatory extraction artifact:
   - Phase 2 must produce a `_work/*_ocr_raw.txt` file via `nl|sed|cut`.
   - Phase 4 must `Read` this file before any HTML body text is written.
   - If the raw file does not exist, phases 4+ are blocked.

2. Import via script, not Write:
   - Phase 4 (mechanical import) must use the reusable toolchain:
     1. Copy `_work/IMPORT_TEMPLATE.py` → `_work/<NNN>_import.py`
     2. Fill in article-specific line mappings (the only creative step)
     3. Run: `python3 _work/<NNN>_import.py > _work/<NNN>_body.html`
     4. Inject: `python3 _work/inject.py "<HTML>" "_work/<NNN>_body.html" "<address>"`
   - The model does not compose prose during import — the script does mechanical line placement.
   - The Write tool may only be used for the initial HTML shell (metadata + empty body) in phase 3.

3. Edit-only after import (small edits only):
   - After the mechanical import in phase 4, all subsequent text changes must use the Edit tool (old_string/new_string replacements on text already present in the file).
   - The Write tool must not be used on article HTML files after phase 4.
   - CRITICAL: The Edit tool's `new_string` parameter is also a memory vector. An Edit that replaces a placeholder with 200+ lines of body text is functionally identical to a Write from memory — the LLM is composing the content in the `new_string` field.
   - Therefore: Edit calls in phases 5+ must be small, targeted corrections (fix a word, merge a hyphenation, add a tag). Any bulk insertion of body text must go through the import script (phase 4).
   - The phase 4 import must use `_work/inject.py` (generic tool) to read from `_work/*_body.html` (itself generated from `_work/*_import.py` reading `_work/*_ocr_raw.txt`) and inject into the HTML shell. The injection must be done by the script, not by pasting content into an Edit or Write call.

4. Scratchpad citation for corrections:
   - During OCR correction (phase 6), each non-trivial correction should cite the source evidence: scan page + region (for example "p.142 col2 para3: scan shows 'Fehlerbeseitigung' not 'Fohler-beseitigung'").
   - This grounds corrections in visual evidence rather than model knowledge.

5. Verbatim-first, correct-second:
   - The imported text must contain all OCR errors verbatim.
   - Corrections are applied as a separate pass (phase 6+), never during import.
   - This makes it verifiable that the base text came from extraction, not memory.

6. Provenance chain:
   - For any line in the final HTML, it must be possible to trace back:
     `final HTML line` ← `Edit operation` ← `imported OCR line` ← `_ocr_raw.txt line` ← `8604.md line range`
   - If this chain is broken (for example by a Write that replaces the whole file), the article must be re-extracted.

### Detection of violations

A Write-from-memory violation is indicated by any of:
- Use of the Write tool on an article HTML file after phase 4
- An Edit call where `new_string` contains more than ~5 lines of article prose (bulk insertion disguised as an edit)
- Article body text that does not appear in `_ocr_raw.txt` (after accounting for edits)
- Prose that is suspiciously clean (no OCR artifacts) on first import
- Missing `_ocr_raw.txt` file for a completed article

## Reusable Toolchain (`_work/`)

### `_work/inject.py` — Generic body injector

Injects mechanically generated body HTML into an article shell. This is the anti-memory enforcement chokepoint: the body content flows from a file, never from the LLM's output.

```
python3 _work/inject.py <html_file> <body_file> [<address_text>]
```

- `<html_file>`: the article HTML shell (must contain placeholder comment)
- `<body_file>`: the generated body (output of the import script)
- `<address_text>`: optional, e.g. `"(Logo/aw)"` — appended as `<address class="author">`

### `_work/IMPORT_TEMPLATE.py` — Import script template

Copy this for each new article. Provides reusable helpers:

| Helper | Purpose |
|--------|---------|
| `p(cls, *line_nums)` | Emit `<p>` from raw OCR lines (1-indexed), merged with space |
| `h(level, line_num)` | Emit `<h2>`/`<h3>` from a raw line |
| `blank()` | Emit blank line for readability |
| `raw(text)` | Emit raw HTML (figures, custom markup) |
| `basic_listing(start, end)` | Emit BASIC listing as `table.plain.right0` |
| `tsv_table(header, start, end)` | Emit tab-separated table as `table.plain.pre` |

Workflow:
```
cp _work/IMPORT_TEMPLATE.py _work/<NNN>_import.py
# edit: set RAW path, fill article-specific line mappings
python3 _work/<NNN>_import.py > _work/<NNN>_body.html
python3 _work/inject.py "<article>.html" "_work/<NNN>_body.html" "(author/xx)"
```

The only creative work is deciding which raw lines map to which HTML elements. All prose flows mechanically from the OCR extraction file.

## Checklist Policy (Mandatory)

- Use one checklist file per article run in `8604/_work/`.
- Start from template: `8604/_work/CHECKLIST_TEMPLATE.md`.
- Suggested naming:
  - `8604/_work/<startpage>_<slug>_CHECKLIST.md`
- Create checklist instances by copying the template with `cp`, for example:
  - `cp 8604/_work/CHECKLIST_TEMPLATE.md 8604/_work/133_von_basic_zu_assembler_teil3_CHECKLIST.md`
- Phases must be checked in order; do not check a later phase before earlier phase is complete.
- The final lock checkbox:
  - `All checkboxes above are checked`
  - is required before reporting article status `done`.
- Lock integrity rule:
  - The final lock may be checked only when:
  - phase 11 is checked
  - unresolved issue count is `0`
  - objective grep/lint checks are marked `pass`
- If final lock is unchecked, status must be reported as `partial`.
