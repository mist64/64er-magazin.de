# 8604 Conversion Workflow — Tesseract Edition (Living Document)

**NEVER reproduce article text from memory. ALWAYS extract it from the OCR output first. The output HTML is COMPLETELY unusable if text was ever reproduced from memory.**

This file is intentionally iterative and will be updated and improved during the conversion.

## Goal

100% reproduce the original magazine text. This includes preserving the original spelling (even spelling errors in the original), but excludes OCR artifacts. Never change any wording or content. Never add anything that is not in the original (no captions, no summaries, no editorial notes, no bridge text).

Convert scanned 600 DPI master pages via per-page Tesseract OCR into repository-style HTML files in `8604/`, aligned with existing issue folders (for example `8603/`).

## Agreed Ground Rules

- Primary text source is per-page Tesseract TSV output (`/tmp/<NNN>_ocr.tsv`), reconstructed into `/tmp/<NNN>_ocr.txt` by the agent, and concatenated into `/tmp/<NNN>_ocr_raw.txt`.
- 600 DPI master PNGs (one per page) are the authoritative source images.
- Scanned page images are mandatory for verification and correction.
- TOC wording can differ from the on-page article title.
- On-page title and on-page start page always win over TOC when they conflict (TOC errors are ignored).
- `index_title` is currently not set from this workflow and must remain commented out in generated HTML until provided from another source.
- Generic anti-memory rule: avoid writing content from memory as much as possible.
- Prefer extraction, copy, and incremental edits over manual retyping.
- No false done rule: if unresolved OCR or structure issues remain, status must be `partial`.

## Known Hallucination Patterns (from practice)

These are the most common ways agents introduce fabricated content. Be vigilant about all of them.

1. **Figcaptions are the #1 hallucination risk.** Agents invent captions for photos that have no caption in the magazine. Rule: if a figure has no caption text visible on the scan, use `<figure>` with NO `<figcaption>`. Never invent a descriptive caption.

2. **Table/figure captions get silently reworded.** Agents paraphrase or summarize captions instead of reproducing them exactly. Example: OCR says "Zusammenhang zwischen EXROM/GAME" but agent writes "Zusammenstellung EXROM/GAME". Every caption must be extracted from OCR, not described from the image content.

3. **Bridge text across page/column breaks is fabricated.** When a paragraph spans a page or column break and the OCR for the continuation is hard to find, agents fill the gap with plausible-sounding German text. This is the most dangerous pattern because it reads naturally. Example: agent wrote "weil dort das Basic-Interpreter-ROM liegt" when the actual text was "weil dann der Basic-Interpreter abgeschaltet ist und der SYS-Befehl nicht mehr ausgeführt werden kann."

4. **Figure placement defaults to end-of-article.** Agents dump figures at the end of the article instead of placing them where they appear in the magazine layout. Always check the scan for figure position. Main article photos typically go after the intro paragraph, not before the author line.

5. **Multi-session context loss causes re-hallucination.** When a conversation runs out of context and resumes, the agent may re-invent text that was correctly extracted in the previous session. Always re-verify against OCR after a session boundary.

## Known Recurring OCR Errors

These Tesseract errors appear consistently across articles and should be checked:

- `»I«` → `»l«` (uppercase I misread for lowercase L in switch positions)
- `$1` → `S1`, `Sl` → `S1` (switch name S1 misread as dollar-one or S-lowercase-L)
- `S]` → `S1` (bracket misread for digit 1)
- `ı` → `i` (Turkish dotless i appearing in German text)
- Spacing errors in compound words: `abgeschaltetistund` → `abgeschaltet ist und`
- `©` → `C` (copyright symbol misread for letter C, as in "C 64")
- `®` → garbage (registered symbol appearing as OCR noise)

## OCR Pipeline

### Source Files

600 DPI cropped master PNGs, one per magazine page. These are the authoritative originals; the 150 DPI images in the PDF are derived from them.

Expected location: `png/<NNN>_600_cropped.png` (or provided externally in `/tmp/` or similar).

### Optimal Tesseract Parameters

Discovered through systematic testing on pages 134 and 159:

| Parameter | Value | Reason |
|-----------|-------|--------|
| Input DPI | 300 (downscaled from 600) | Tesseract LSTM trained ~300 DPI; native 600 DPI causes Turkish dotless-ı bug |
| Downscale | `magick <src> -resize 50%` | Clean 2:1 integer downscale, no interpolation artifacts |
| Language | `-l deu` | German; handles both old (daß/muß) and new orthography |
| PSM mode | `--psm 1` | Automatic page segmentation with OSD; correctly detects two-column layouts |
| Preprocessing | None | Upscaling, thresholding, sharpening all make results worse |

### Per-Page OCR Command

**Important:** All intermediate files must be stored within the issue's `./tmp/` directory, not in system `/tmp/`. Tesseract and other tools may not have access to `/tmp/` due to sandboxing.

```bash
# Step 1: Downscale 600 DPI master to 300 DPI
magick png/<NNN>_600_cropped.png -resize 50% ./tmp/<NNN>_300.png

# Step 2: Run Tesseract with TSV + hOCR output
tesseract ./tmp/<NNN>_300.png ./tmp/<NNN>_ocr -l deu --psm 1 -c hocr_font_info=1 tsv hocr
# produces ./tmp/<NNN>_ocr.tsv and ./tmp/<NNN>_ocr.hocr
```

After producing the TSV, the agent reconstructs a plain-text file (`/tmp/<NNN>_ocr.txt`) with correct column reading order. See "Column Reconstruction from TSV" below.

The hOCR file is used by `tsv_layout.py` (see below) to extract font size information per block.

### Multi-Page Articles

For articles spanning multiple pages, OCR each page individually, reconstruct each page's text from TSV, then concatenate:

```bash
# OCR each page (TSV + hOCR output)
for p in 134 135 136; do
    magick png/${p}_600_cropped.png -resize 50% /tmp/${p}_300.png
    tesseract /tmp/${p}_300.png /tmp/${p}_ocr -l deu --psm 1 -c hocr_font_info=1 tsv hocr
done

# Agent reconstructs /tmp/<NNN>_ocr.txt for each page from TSV (see below)

# Concatenate into article raw file (with page markers)
for p in 134 135 136; do
    echo "--- PAGE ${p} ---"
    cat /tmp/${p}_ocr.txt
done > /tmp/133_von_basic_zu_assembler_teil3_ocr_raw.txt
```

The `--- PAGE NNN ---` markers help locate content during the import script mapping phase. They are ignored during import (never emitted as HTML).

### Known Limitations

- **Code listings fragment**: Assembly/BASIC listings may split into many small OCR blocks. Manual stitching in the import script is expected.
- **Directory listings and tables**: Structured columnar content (like Commodore directory listings) loses alignment. Manual correction needed during technical fidelity pass.
- **Old German spelling**: Tesseract `deu` handles pre-1997 orthography (daß, muß, Fluß) correctly — no special configuration needed.

### Column Reconstruction from TSV

TSV output is the primary Tesseract format. The agent reconstructs correct reading order from position data. This replaces reliance on Tesseract's built-in column ordering, which frequently fails around figures and diagrams.

#### TSV format

Each row has: `level`, `page_num`, `block_num`, `par_num`, `line_num`, `word_num`, `left`, `top`, `width`, `height`, `conf`, `text`.

- `level=5` rows are individual words (the only rows with text content).
- `level=1..4` rows are structural (page, block, paragraph, line boundaries) — useful for grouping but contain no text.

#### Reconstruction procedure

For each page TSV:

1. **Filter** to `level=5` rows where `text` is non-empty.
2. **Group** words by `(block_num, par_num, line_num)` to form text lines.
3. **Determine column assignment** for each block using its `left` coordinate:
   - Compute page midpoint from the image width (typically ~1275 px at 300 DPI for these magazine pages, so midpoint ~637).
   - Blocks with `left < midpoint` → left column.
   - Blocks with `left >= midpoint` → right column.
4. **Sort** lines: left-column blocks first (sorted by `top`), then right-column blocks (sorted by `top`).
5. **Join** words within each line with spaces.
6. **Emit** as plain text lines, one per reconstructed line.
7. **Save** as `/tmp/<NNN>_ocr.txt`.

#### Handling special cases

- **Full-width blocks** (headings, titles, page-spanning figures): These may have `left` near 0 and `width` spanning the full page. Place them in reading order by `top` coordinate relative to surrounding column text.
- **Figures and captions**: Tesseract often creates separate blocks for figure captions. Their `left`/`top` coordinates indicate which column they belong to.
- **Three-column layouts** (rare): Use three x-coordinate ranges instead of two. Inspect the TSV `left` values to identify natural clusters.

## TOC Workflow

### 1. Reconstruct TOC from issue TOC pages

- Build a clean TOC from TOC pages in the PDF (not from noisy OCR alone).
- Maintain section order exactly as printed.
- Use normal case for section names in the TSV (e.g., "Hardware-Test" not "HARDWARE-TEST"). Match the casing used in `toc.txt`.
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
- `64er.index_category` handling (current rule):
  - Keep commented out and empty:
  - `<!-- <meta name="64er.index_category" content=""> -->`

Use standard metadata fields where available:

- `author`
- `64er.issue` (`4/86`)
- `64er.pages`
- `64er.head1`
- `64er.head2`
- `64er.toc_title`
- `64er.toc_category`
- `64er.id`

`64er.id` format:

- Lowercase, no spaces.
- Underscores separate words (e.g. `memory_map`, `tips_tricks`).
- Hyphens for model numbers or compound technical names (e.g. `hr-5c`, `hypra-text`).
- German umlauts are allowed (e.g. `bücher`, `dfü`).
- Short and descriptive — typically the main topic, software name, or hardware model.
- For recurring column types, reuse the same id across issues (e.g. `leserforum`, `impressum`, `aktuell`).
- For articles about a specific program/product, use that name (e.g. `superbase64`, `mse`, `sid`).
- No strict length limit, but keep concise.

Lead text rule:

- The subtitle/lead directly under `<h1>` should be encoded as `<p class="intro">...</p>`, not `<blockquote>`.

Leserforum format:

- Use `article` with class `qa`.
- Add header image block first:
  - `<header><img src="<startpage>-0.png" alt="Leserforum" title="Leserforum"></header>`
- Each Q/A topic is a `<section>`:
  - `<h2>Topic Title</h2>` — the topic heading (mixed case, even if ALL CAPS in scan)
  - `<div class="q">` — question block containing:
    - `<p>` paragraphs with question text
    - `<p class="author">Author Name</p>` — questioner name (mixed case)
    - Optional issue reference: `<p class="noindent">Ausgabe N/YY</p>` or `<h3>Ausgabe N/YY</h3>` when visually prominent
  - `<div class="a">` — answer block (when present) containing:
    - `<p>` paragraphs with answer text
    - `<p class="author">Answerer Name</p>` — when the answer is from a named reader (not editorial)
  - `<p class="source">Info: ...</p>` — after `div.a`, still inside section
  - `<ul class="source plain">` — for multi-line address/source blocks
- Questions without answers: `<div class="q">` only, no `<div class="a">`
- Items that are tips/answers without a preceding question: use `<div class="a">` directly (no `<div class="q">`)
- Numbered questions/answers: use `<ol>` / `<li>` when the magazine uses numbered format, or prefix with `(N)` when inline
- `<aside>` blocks for recurring features:
  - "Fragen Sie doch" — reader question invitation
  - "Wollen Sie antworten?" — call for reader answers
  - "Leser fragen - Willi Brechtl antwortet" — special column (use `<h1>` for title, `<p class="intro">` for intro)
  - "Ein Wort in eigener Sache" — editorial notes
  - "Lebenslauf" — author biography box in "Anwendung des Monats" articles. Author name at the end (e.g. `(Matthias Gerloff)`) must be a separate `<address class="author">` element, not inline in the paragraph text.
  - These are NOT `<section>` — they are `<aside>` with `<h2>` (or `<h1>` for Willi Brechtl)
- Name normalization: ALL CAPS names from the magazine scan are converted to mixed case in HTML (e.g. `MARCO TRUNZER` → `Marco Trunzer`)
- Heading normalization: ALL CAPS topic headings are converted to mixed case (e.g. `FRAGEN ZUM C 64` → `Fragen zum C 64`)
  - Preserve proper nouns and acronyms: `CP/M`, `C 64`, `C 128`, `MPS 801`, etc.
- When question has inline author name at end of text (common in compact items), split it into separate `<p class="author">` tag
- `<code>` for inline code/commands within answer text
- If OCR quality prevents reliable structural splitting, prefer a faithful line-preserving conversion from extracted text over guessed restructuring.

Example — typical Q/A section:
```html
        <section>
            <h2>Topic Title</h2>

            <div class="q">
                <p>Question text...</p>
                <p class="author">Questioner Name</p>
            </div>

            <div class="a">
                <p>Answer text...</p>
                <p class="author">Answerer Name</p>
            </div>

            <p class="source">Info: Address or reference...</p>
        </section>
```

Example — question only (no answer):
```html
        <section>
            <h2>Topic Title</h2>

            <div class="q">
                <p>Question text...</p>
                <p class="author">Questioner Name</p>
            </div>
        </section>
```

Example — answer/tip without preceding question:
```html
        <section>
            <h2>Topic Title</h2>

            <div class="a">
                <p>Tip/answer text...</p>
                <p class="author">Contributor Name</p>
            </div>
        </section>
```

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

Listing placement and content rules:

- **Listing contents are omitted** for listings in "Checksummer" format (BASIC code with `<123>`-style checksums after every line) or "MSE" format (address, 8 hex bytes, 1 checksum byte per line). These formats are identifiable either by an explicit label ("Checksummer", "MSE") or by their characteristic structure. The `<figure>` wrapper and `<figcaption>` must be present, and the `<pre>` block inside must contain only `TODO` (no OCR content). These listings will be added separately from a verified source.
- **Default placement: end of article.** All listing `<figure>` blocks go at the end of the article, grouped together just before `</article>`. This keeps the prose flow clean.
- **Exception 1 — tutorial-style articles with small captioned Listings:** When a numbered `Listing N` is small and directly embedded in the prose flow as part of a step-by-step tutorial explanation, keep it inline at the point of reference. The `<figure>` with `<figcaption>` stays; it is just placed inline instead of at the end.
- **Exception 2 — "Tips und Tricks" multi-tool collection articles:** In "Tips und Tricks" articles where every `<h2>` describes a separate, independent tool or trick, place each tool's Listings inline (at the end of that tool's section, before the next `<h2>`). This keeps each self-contained tool section complete. If the article is a single continuous narrative that happens to be in the Tips und Tricks section, use the default (Listings at end).
- **Bare code snippets are always inline.** Unlabeled code examples (bare `<pre>` without `<figure>`/`<figcaption>`, no "Listing N" caption) are always part of the prose flow and stay inline. These are not "Listings" — they are just code examples. This is not an exception; it is the normal case.

Example — default (single-narrative article, Listings at end):
```html
        <p>...prose referencing Listing 1...</p>
        <!-- Listings are NOT here -->
        <address class="author">(...)</address>

        <figure>
            <pre>TODO</pre>
            <figcaption>Listing 1. ...</figcaption>
        </figure>

        <figure>
            <pre>TODO</pre>
            <figcaption>Listing 2. ...</figcaption>
        </figure>
    </article>
```

Example — Tips und Tricks multi-tool (Listings inline per tool section):
```html
        <h2>Tool A</h2>
        <p>...description of Tool A...</p>
        <figure>
            <pre>TODO</pre>
            <figcaption>Listing 1. Tool A program.</figcaption>
        </figure>

        <h2>Tool B</h2>
        <p>...description of Tool B...</p>
        <figure>
            <pre>TODO</pre>
            <figcaption>Listing 2. Tool B program.</figcaption>
        </figure>
    </article>
```

Figure placement rule for Tabellen:

- Treat `Tabelle` entries like `Bild` entries at markup level:
  - always wrap them in `<figure>...</figure>` with a `<figcaption>` like `Tabelle n. ...`
  - if the table is transcribed as HTML, keep semantic `<table>` inside the `<figure>`
- Place every `Tabelle` immediately after the first paragraph that references it in running text.
- Do not leave standalone `Tabelle` headings as plain `<p>` blocks when a figure/table is present.
- Do not keep duplicated caption-spill paragraphs like `<p>Bild n. ...</p>` when the same text is already in adjacent `<figcaption>`.

Author/Info adjacency rule:

- **Paragraph + author + Info form an atomic block.** The `<address class="author">` and any "Info" box always stick directly to the preceding paragraph — never insert a `<figure>` (Bild, Listing, or Tabelle) between them.
- **Image placement treats this block as a unit.** The rule "place figure after the paragraph that references it" means: after the atomic block (paragraph + author + info), not between the paragraph and the author. Figures referenced in the last paragraph go after the author/info, not before it.

## Line-Break Hyphen Handling

### Rule: no script dehyphenation

Scripts must **NEVER** dehyphenate. Dehyphenation requires judgment about whether a hyphen is a line-break artifact or a real compound-word hyphen (e.g., `Basic-Editor`, `Multiple-Choice`, `Generator-Programm`). Scripts cannot make this distinction reliably. All dehyphenation decisions are made by the agent in a dedicated pass.

### Soft hyphen marking (mechanical, in import script)

The import script's `p()` helper joins OCR lines as follows:

- If the previous line **ends with `-`**: replace the trailing `-` with a soft hyphen (`\u00AD`) and join **without space**.
- If the previous line does **not** end with `-`: join with a normal space.

This marks every line-break hyphen position without making any judgment call. Mid-line hyphens (like `Sprachen- oder`) are untouched because they don't occur at line boundaries.

Examples (showing `­` for `\u00AD`):

| OCR lines | Joined result |
|-----------|---------------|
| `"Gene-"` + `"rator-Programm"` | `"Gene­rator-Programm"` |
| `"Basic-"` + `"Editor, aber"` | `"Basic­Editor, aber"` |
| `"Sprachen- oder Ma-"` + `"thematikkurs"` | `"Sprachen- oder Ma­thematikkurs"` |
| `"daß man auch"` + `"mit relativ"` | `"daß man auch mit relativ"` |

### Soft hyphen resolution pass (mandatory agent pass)

After mechanical import, the agent must resolve **every** soft hyphen (`\u00AD`) in the article HTML. No soft hyphens may remain in the final output.

For each `\u00AD`, the agent decides:

1. **Remove** (the common case): the two halves form one word without a hyphen.
   - `Gene­rator` → `Generator`
   - `Ma­thematikkurs` → `Mathematikkurs`
   - `er­möglicht` → `ermöglicht`
   - `Beant­wortung` → `Beantwortung`

2. **Replace with real hyphen `-`**: the original text has a compound-word hyphen at this position.
   - `Basic­Editor` → `Basic-Editor`
   - `Multiple­Choice` → `Multiple-Choice`
   - `Generator­Programm` → `Generator-Programm`
   - `Bildschirm­rand` → depends on original: `Bildschirmrand` (one word) or `Bildschirm-Rand` (compound)

Decision process:

- Does removing the soft hyphen produce a valid German word? → **Remove**.
- Does the position separate two independent word parts that form a compound with a hyphen? → **Replace with `-`**.
- When uncertain, check the scan at the corresponding line break position.
- ALL-CAPS words (e.g., `UNTERSTAN­DING` → `UNDERSTANDING`): the uppercase rule doesn't apply; check the scan.

Verification: grep the final HTML for `\u00AD` or `&shy;`. Count must be **zero** before the article can be marked done.

## OCR Cleanup Policy

Conservative normalization only:

- Always start article text from Tesseract OCR output of the article's pages.
- Never draft article prose from memory (for example by writing full text directly in a heredoc such as `cat <<EOF ...`).
- Extraction method (required):
  - OCR each page belonging to the article with the standard pipeline (see OCR Pipeline above)
  - Concatenate per-page OCR results into `/tmp/<NNN>_<slug>_ocr_raw.txt`
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
All transformations must be edits on top of the Tesseract OCR output.
Do not rebuild prose from scratch at any stage.

1. Run Tesseract on each page and concatenate into `/tmp/*_ocr_raw.txt`.
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

- Start/end boundaries: determine article boundaries from scanned page layout first, then confirm from OCR output.
- Provenance: always keep the per-page OCR files and the concatenated `/tmp/*_ocr_raw.txt` for traceability.
- Two-pass text handling:
  1. Tesseract OCR into working text
  2. paragraph-by-paragraph correction against scan
- OCR normalization: fix only what is visually confirmed on scan; avoid stylistic rewrites.
- Split-line repair: aggressively repair OCR line-break artifacts (for example `Mit-` + `gliedern`, split words around punctuation) only when unambiguous on scan.
- Column reordering: TSV output with x-coordinates makes column assignment mechanical. The agent reconstructs reading order from position data during Phase 2, so the `_ocr.txt` files already have correct column order. This eliminates the column-bleeding problem that plain-text Tesseract output had around figures and diagrams.
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
   - Any dropped line needs explicit reason (for example running header/footer noise, page marker line).

3. Multi-column reading order:
   - Confirm and follow printed reading order before edits.
   - Do not reorder paragraphs for style.
   - When Tesseract column ordering is wrong (detected by comparing against scan), fix in the import script line mapping.

4. Page-noise whitelist:
   - Only remove running heads/footers, page numbers, issue/date footer lines, and `--- PAGE NNN ---` markers.
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

This is the mandatory sequence. Do not skip steps. Do not report completion before step 13 is done.

1. Identify boundaries:
   - Resolve start/end pages from `8604_toc_improved.tsv`.
   - Confirm real start page and continuation pages from scans.
   - **Always check the page AFTER the TOC-listed last page** for continuation content (closing paragraphs, author credits like `(hm)`, `Info:` blocks). Articles frequently spill onto the next page. OCR that page and inspect the top portion.
   - List all pages to OCR (article content pages, excluding pure ad pages).

2. Run Tesseract OCR (TSV pipeline):
   - For each page in the article, run the standard pipeline:
     ```bash
     magick png/<NNN>_600_cropped.png -resize 50% ./tmp/<NNN>_300.png
     tesseract ./tmp/<NNN>_300.png ./tmp/<NNN>_ocr -l deu --psm 1 -c hocr_font_info=1 tsv hocr
     python3 ../../tools/png2mag/tsv_reconstruct.py ./tmp/<NNN>_ocr.tsv > ./tmp/<NNN>_ocr.txt
     ```
   - Use `tsv_reconstruct.py --dump-blocks` to inspect layout when column assignment needs manual review.
   - For complex layouts (images, captions, asides interleaved across columns), use `tsv_layout.py` with a sub-agent for block ordering (see "tsv_layout.py" in Reusable Toolchain below).
   - Concatenate per-page results into the article raw file:
     ```bash
     for p in <page_list>; do
         echo "--- PAGE ${p} ---"
         cat ./tmp/${p}_ocr.txt
     done > ./tmp/<NNN>_<slug>_ocr_raw.txt
     ```
   - All article text edits must be applied on top of this extraction.

3. Create initial HTML shell:
   - Add metadata, `h1`, and intro placeholder.
   - Keep `index_title` commented and empty.
   - Keep `author` as placeholder (`content="TODO"`). The author field is filled at the very end (phase 12), not during shell creation. This prevents premature decisions and keeps the shell mechanical.
   - Body placeholder must be exactly: `        <!-- BODY WILL BE MECHANICALLY IMPORTED -->`

4. Mechanical import pass:
   - Copy the import template: `cp IMPORT_TEMPLATE.py /tmp/<NNN>_import.py`
   - Edit the copy: set `RAW` path, fill in article-specific line mappings.
   - Available helpers (see template for full API):
     - `p(cls, *line_nums)` — emit `<p>` from raw lines (1-indexed), joined with soft-hyphen logic (see "Line-Break Hyphen Handling")
     - `h(level, line_num)` — emit heading
     - `blank()` — readability separator
     - `raw(text)` — emit raw HTML (figures, tables)
     - `basic_listing(start, end)` — emit BASIC listing table (`plain right0`)
     - `tsv_table(header, start, end)` — emit tab-separated table (`plain pre`)
   - When mapping lines, skip `--- PAGE NNN ---` marker lines (they are not content).
   - When Tesseract column order is wrong, reorder by specifying correct line numbers in the import script.
   - Run: `python3 /tmp/<NNN>_import.py > /tmp/<NNN>_body.html`
   - Inject into shell: `python3 inject.py "<HTML_FILE>" "/tmp/<NNN>_body.html" "<address_text>"`
   - No rewriting from memory at any point.

5. Structure pass:
   - Convert headings, intros, `noindent`, `strong`, `pre`, `table`, `figure`, `address`.
   - Heading level determination (mandatory before writing `h()` calls in import script):
     1. Scan ALL pages of the article and inventory every heading.
     2. Classify each heading by its visual typographic treatment:
        - **h2**: heading text with a horizontal rule/line above AND below it.
        - **h3**: bold heading text without horizontal rules.
     3. Record the full heading inventory (text, scan page, visual treatment, assigned level) in the checklist `heading_inventory` field before proceeding.
   - **Displaced headings**: Typesetters sometimes moved headings away from their logical position to avoid placing them at the very top or bottom of a column. When a heading appears in the middle of a paragraph in the scan, move it to its logical position — typically right before the paragraph it introduces. The surrounding text should be re-joined into one paragraph above the heading.
   - Build special structures (for example `div.q`/`div.a`) only when scan supports it.
   - **Author credit and Info block** (mandatory check):
     - Look for an author abbreviation in parentheses at the end of the article text, e.g. `(hm)`, `(sc)`, `(gk)`. Render as `<address class="author">(xx)</address>`.
     - Look for an `Info:` block (book/product reference, supplier address). Render as `<p class="source">Info: ...</p>`.
     - These may appear on the page AFTER the main article text (see Phase 1 boundary rule).

6. Soft hyphen resolution pass:
   - Grep the HTML for `\u00AD` (soft hyphen) to find all line-break positions.
   - For each soft hyphen, decide: **remove** (dehyphenate) or **replace with `-`** (real compound hyphen).
   - See "Soft hyphen resolution pass" in the "Line-Break Hyphen Handling" section for decision rules.
   - After this pass, grep again to confirm zero soft hyphens remain.

7. OCR correction pass (`prose_pass`):
   - Paragraph-by-paragraph visual compare against page images.
   - Fix only confirmed OCR errors.

8. Technical fidelity pass (`technical_pass`):
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

9. Bild/Tabelle positioning pass (mandatory):
   - For each `Bild` and `Tabelle`, find first textual reference.
   - Place matching `<figure>` immediately after that paragraph.
   - If unreferenced, place by strongest visual/content match and note in TSV `notes`.
   - Record placement proof for each item:
   - source reference line (OCR line or scan evidence)
   - final HTML line
   - asset filename

10. Asset validation:
    - Confirm every referenced image file exists.
    - Confirm there are no orphaned article images left unhandled.

11. Coverage validation:
    - Confirm page coverage including continuation/listing pages.
    - Confirm ad-only pages excluded.

12. Final QA gate:
    - No unresolved placeholders or malformed HTML blocks.
    - Fill the `<meta name="author">` field now (it was left empty during shell creation in phase 3).
    - Author credit normalized to `<address class="author">...</address>`.
    - All Bild/Tabelle/Listing references resolved.
    - Unresolved issue count must be zero.
    - Synthetic prose additions must be zero unless explicitly justified with evidence.
    - Run objective grep/lint checks for common OCR artifacts and record results.
    - Verify no duplicated caption-spill body paragraphs remain (`<p>Bild n...` / `<p>Tabelle n...` adjacent to same `<figcaption>`).
    - Verify no standalone numeric OCR-junk paragraphs remain unless intentional (`^\d+( \d+)*$`).
    - Verify `residual_defects` is present and equals `none`.
    - Verify zero soft hyphens remain (`\u00AD` / `&shy;` count = 0).

13. Completion report format:
    - When reporting done, always include:
    - pages OCR'd and raw file path
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
   - Phase 2 must produce per-page `/tmp/<NNN>_ocr.tsv` files via Tesseract, per-page `/tmp/<NNN>_ocr.txt` files reconstructed from TSV by the agent, and a concatenated `/tmp/<NNN>_<slug>_ocr_raw.txt`.
   - Phase 4 must `Read` this file before any HTML body text is written.
   - If the raw file does not exist, phases 4+ are blocked.

2. Import via script, not Write:
   - Phase 4 (mechanical import) must use the reusable toolchain:
     1. Copy `IMPORT_TEMPLATE.py` → `/tmp/<NNN>_import.py`
     2. Fill in article-specific line mappings (the only creative step)
     3. Run: `python3 /tmp/<NNN>_import.py > /tmp/<NNN>_body.html`
     4. Inject: `python3 inject.py "<HTML>" "/tmp/<NNN>_body.html" "<address>"`
   - The model does not compose prose during import — the script does mechanical line placement.
   - The Write tool may only be used for the initial HTML shell (metadata + empty body) in phase 3.

3. Edit-only after import (small edits only):
   - After the mechanical import in phase 4, all subsequent text changes must use the Edit tool (old_string/new_string replacements on text already present in the file).
   - The Write tool must not be used on article HTML files after phase 4.
   - CRITICAL: The Edit tool's `new_string` parameter is also a memory vector. An Edit that replaces a placeholder with 200+ lines of body text is functionally identical to a Write from memory — the LLM is composing the content in the `new_string` field.
   - Therefore: Edit calls in phases 5+ must be small, targeted corrections (fix a word, merge a hyphenation, add a tag). Any bulk insertion of body text must go through the import script (phase 4).
   - The phase 4 import must use `inject.py` (generic tool) to read from `/tmp/*_body.html` (itself generated from `/tmp/*_import.py` reading `/tmp/*_ocr_raw.txt`) and inject into the HTML shell. The injection must be done by the script, not by pasting content into an Edit or Write call.

4. Scratchpad citation for corrections:
   - During OCR correction (phase 6), each non-trivial correction should cite the source evidence: scan page + region (for example "p.142 col2 para3: scan shows 'Fehlerbeseitigung' not 'Fohler-beseitigung'").
   - This grounds corrections in visual evidence rather than model knowledge.

5. Verbatim-first, correct-second:
   - The imported text must contain all OCR errors verbatim.
   - Corrections are applied as a separate pass (phase 6+), never during import.
   - This makes it verifiable that the base text came from extraction, not memory.

6. Provenance chain:
   - For any line in the final HTML, it must be possible to trace back:
     `final HTML line` ← `Edit operation` ← `imported OCR line` ← `_ocr_raw.txt line` ← `/tmp/<NNN>_ocr.txt` ← `agent column reconstruction` ← `/tmp/<NNN>_ocr.tsv` ← `tesseract` ← `/tmp/<NNN>_300.png` ← `600 DPI master PNG`
   - If this chain is broken (for example by a Write that replaces the whole file), the article must be re-extracted.

7. Adding text missed during initial import (Option C procedure):
   - When post-import verification reveals text that was missed during Phase 4 (for example: an unprocessed column area, a page boundary paragraph, right-column text buried in TSV noise), the missing text must NEVER be composed from memory.
   - Required procedure:
     1. Identify the missing text's location in the `_ocr_raw.txt` or per-page `_ocr.txt`/`_ocr.tsv` files.
     2. Write a Python script that extracts the relevant blocks/paragraphs from the OCR source, performs mechanical cleanup (line joining, dehyphenation), and outputs `<p>`-tagged HTML to an intermediate file on disk.
     3. Use a second script to replace the affected text in the HTML file, sourcing from the intermediate file.
     4. Fix OCR errors with targeted Edit calls on the HTML (small `old_string` → `new_string` pairs, each verifiable against the scan). Each Edit fixes one specific OCR artifact.
   - The intermediate HTML file (`*_html.txt` or `*_replacement.txt`) is the provenance artifact. The script that produced it is the audit trail.
   - What is NOT allowed: reading OCR data in the LLM context, mentally assembling sentences, and writing them into an Edit `new_string` or a Write call. This is reconstruction-from-memory even if the individual words came from OCR — the LLM is composing the sentence structure, joining, and punctuation from its own knowledge.
   - Rule of thumb: if you cannot point to a script + output file on disk that produced your text, you are writing from memory.

### Detection of violations

A Write-from-memory violation is indicated by any of:
- Use of the Write tool on an article HTML file after phase 4
- An Edit call where `new_string` contains more than ~5 lines of article prose (bulk insertion disguised as an edit)
- Article body text that does not appear in `_ocr_raw.txt` (after accounting for edits)
- Prose that is suspiciously clean (no OCR artifacts) on first import
- Missing `_ocr_raw.txt` file for a completed article
- Missing text added without an intermediate extraction file as provenance
- Figcaptions, bridge text, or any other content not present in the original scan

### Hallucination review pass (mandatory)

After an article is complete, run a review pass to detect hallucinated content. This is NOT optional — it has caught real hallucinations in every article checked so far.

**Procedure:**
1. Write a script that extracts every figcaption, heading, and paragraph from the HTML.
2. For each element, search for distinctive words/phrases in the OCR raw text.
3. Flag elements with low OCR coverage for manual verification against the scan.
4. Verify ALL figcaptions and headings individually against the scan — these are highest risk.
5. Check page/column break boundaries specifically — bridge text is often fabricated.

**Priority areas (from most to least likely to contain hallucinations):**
1. Figcaptions — especially for photos (vs. numbered diagrams/tables)
2. Bridge text at page/column breaks
3. Table captions (often reworded instead of reproduced)
4. Content added after a session boundary
5. Paragraphs that are "too clean" compared to surrounding OCR quality

## Reusable Toolchain

### OCR Pipeline Scripts

The OCR pipeline is two commands per page, plus column reconstruction via `tsv_reconstruct.py`:

```bash
# Per-page OCR (repeat for each page)
magick png/<NNN>_600_cropped.png -resize 50% ./tmp/<NNN>_300.png
tesseract ./tmp/<NNN>_300.png ./tmp/<NNN>_ocr -l deu --psm 1 -c hocr_font_info=1 tsv hocr
# produces ./tmp/<NNN>_ocr.tsv and ./tmp/<NNN>_ocr.hocr

# Reconstruct reading order from TSV
python3 ../../tools/png2mag/tsv_reconstruct.py ./tmp/<NNN>_ocr.tsv > ./tmp/<NNN>_ocr.txt
```

### `tsv_reconstruct.py` — Column reconstruction from TSV

Reconstructs correct reading order from Tesseract TSV output. Assigns words to columns by x-coordinate clustering, then sorts by column and vertical position.

```
python3 tools/png2mag/tsv_reconstruct.py <tsv_file> [--width W] [--boundaries X,X,...] [--annotate] [--dump-blocks]
```

- `--width W`: page width in pixels (default: 2480)
- `--boundaries X,X,X`: explicit column boundary x-coordinates (auto-detected if omitted)
- `--annotate`: prefix each line with block/band/x/y metadata (useful for debugging layout)
- `--dump-blocks`: show block summary with x/y ranges (for layout analysis before import)

Use `--dump-blocks` first to inspect the layout, then use the plain output for the `_ocr.txt` file.

### `tsv_layout.py` — Layout analysis for LLM-driven block ordering

Produces a compact, LLM-friendly page layout summary from Tesseract TSV (and optional hOCR) files. Designed for a sub-agent to determine reading order on complex multi-column layouts with images, captions, and asides.

```
# Single page (TSV only)
python3 ../../tools/png2mag/tsv_layout.py ./tmp/<NNN>_ocr.tsv

# Single page with hOCR for font size
python3 ../../tools/png2mag/tsv_layout.py ./tmp/<NNN>_ocr.tsv --hocr ./tmp/<NNN>_ocr.hocr

# Multi-page article
python3 ../../tools/png2mag/tsv_layout.py ./tmp/020_ocr.tsv ./tmp/021_ocr.tsv ./tmp/022_ocr.tsv \
  --hocr ./tmp/020_ocr.hocr ./tmp/021_ocr.hocr ./tmp/022_ocr.hocr
```

Output format:

- **Page header**: page number and dimensions
- **HRULE/VRULE**: thin blocks (≤ 10px in one dimension) as one-liners
- **IMAGE**: block bounding box only (no words detected)
- **TEXT**: bounding box, line count, median word height (`h=`), modal font size (`f=`, from hOCR), and a text preview (first + last sentence with `…` in between)

Block classification:

- No automatic SKIP filtering — the LLM sub-agent decides what is a running header, page number, or footer based on context and position data.

#### LLM sub-agent workflow for block ordering

This is a workflow pattern, not code. The sub-agent invocation happens in the main agent's conversation.

1. Run `tsv_layout.py` on all pages of an article → capture output
2. Spawn a sub-agent (Task tool, `subagent_type=general-purpose`, `model=sonnet`, fresh context) with ONLY the layout summary as input plus the prompt template below
3. The sub-agent returns a structured block ordering that the main agent uses to drive the import script's line mappings

This replaces the manual block-ordering step for complex layouts. Simple two-column pages can still use `tsv_reconstruct.py` directly.

#### Sub-agent prompt template

Paste the `tsv_layout.py` output into the marked position. Adjust the column count and any magazine-specific notes as needed.

```
You are a layout analysis expert. You will receive a page layout summary
from an OCR'd magazine page. Your job is to determine:

1. **BODY blocks** — the continuous article text flow, listed in correct
   reading order
2. **Non-body blocks** — blocks that are NOT part of the continuous text
   flow, each annotated with its type

The page is from a German computer magazine (multi-column layout). Use
the block positions (x,y coordinates), sizes, font sizes (f=), line
counts, and text previews to make your decisions.

**Guidelines:**

- Body text blocks (small font, many lines) form the main article flow.
- **H3 subheadings** (larger font, 1–3 lines, free-standing between body
  blocks) are part of the body flow. Include them in the BODY list at
  their correct position.
- Reading order within columns is top-to-bottom. Column order is
  generally left-to-right, but VERIFY by checking text continuity at
  block boundaries.
- **CRITICAL — text continuity check:** The text preview shows the first
  and last words/sentences of each block. Use these to verify reading
  order:
  - If Block A's preview ends with a hyphenated word fragment like
    "verschaf-" and Block B starts with "fen.", then B must immediately
    follow A.
  - Always check these continuation patterns to confirm the correct
    sequence, especially across column boundaries.
- Short blocks near images that start with "Bild N." are CAPTION blocks.
- Very short blocks at page top/bottom edges (especially with page
  numbers or magazine names) are HEADER/FOOTER — mark for discard.
- HRULEs and VRULEs are structural separators, not content — ignore them.

**Page layout:**

<PASTE tsv_layout.py OUTPUT HERE>

**Your output:**

First, show your reasoning: list the text continuity checks at block
boundaries so the logic is visible. Then output a JSON block.

The JSON must follow this exact structure:

```json
{
  "pages": [
    {
      "page": "022",
      "body": [
        {"block": 5},
        {"block": 11},
        {"block": 12, "type": "h2"},
        {"block": 13}
      ],
      "non_body": [
        {"block": 1, "type": "header"},
        {"block": 16, "type": "caption"},
        {"block": 7, "type": "image"},
        {"block": 6, "type": "aside", "aside_id": "specs", "heading": true},
        {"block": 7, "type": "aside", "aside_id": "specs"},
        {"block": 26, "type": "aside", "aside_id": "lastminute", "heading": true},
        {"block": 27, "type": "aside", "aside_id": "lastminute"}
      ]
    }
  ]
}
```

Rules:
- `body`: ordered list. Each entry has `"block"` (int). Add `"type"` only
  for non-default types: `"h2"`, `"aside"`. No type = regular body text.
- `non_body`: unordered list. Each entry has `"block"` and `"type"`.
  Types: `"header"`, `"footer"`, `"caption"`, `"image"`, `"discard"`,
  `"aside"` (for boxed/sidebar content like spec tables or info boxes).
- Aside blocks MUST have an `"aside_id"` string that groups blocks
  belonging to the same box/sidebar. Use a short descriptive slug
  (e.g. `"specs"`, `"lastminute"`, `"bio"`). All blocks from the same
  visual box share the same `aside_id`.
- One page object per page, in page order.
```

### `tsv_reading_order.py` — Reconstruct text from JSON block ordering

Takes the JSON output from the sub-agent (saved to a file) plus the same TSV files, and produces concatenated article text in reading order with non-body blocks (captions, asides) collected at the end.

```
# Single page
python3 ../../tools/png2mag/tsv_reading_order.py order.json ./tmp/022_ocr.tsv

# Multi-page article
python3 ../../tools/png2mag/tsv_reading_order.py order.json \
  ./tmp/020_ocr.tsv ./tmp/021_ocr.tsv ./tmp/022_ocr.tsv ...
```

The script maps page numbers from the JSON `"page"` field to TSV files by extracting the page number from the filename (e.g. `022_ocr.tsv` → `"022"`).

Output sections:
- `--- BODY ---` — all body blocks (including H3s) in reading order, with `[page, block, type]` markers
- `--- CAPTION ---` — all caption blocks
- `--- ASIDE ---` — all aside blocks (if any)
- Headers, footers, images, and discard blocks are silently dropped.

#### Full pipeline example

```bash
# 1. OCR all pages (if not already done)
for p in 020 021 022 023 024 025 026 027; do
    magick png/${p}_600_cropped.png -resize 50% ./tmp/${p}_300.png
    tesseract ./tmp/${p}_300.png ./tmp/${p}_ocr -l deu --psm 1 -c hocr_font_info=1 tsv hocr
done

# 2. Generate layout summary
python3 ../../tools/png2mag/tsv_layout.py ./tmp/0{20,21,22,23,24,25,26,27}_ocr.tsv \
  --hocr ./tmp/0{20,21,22,23,24,25,26,27}_ocr.hocr > ./tmp/layout.txt

# 3. Send layout.txt to sub-agent (using prompt template above) → save JSON to order.json

# 4. Reconstruct text
python3 ../../tools/png2mag/tsv_reading_order.py ./tmp/order.json \
  ./tmp/0{20,21,22,23,24,25,26,27}_ocr.tsv > ./tmp/article_body.txt
```

### `inject.py` — Generic body injector

Injects mechanically generated body HTML into an article shell. This is the anti-memory enforcement chokepoint: the body content flows from a file, never from the LLM's output.

```
python3 inject.py <html_file> <body_file> [<address_text>]
```

- `<html_file>`: the article HTML shell (must contain placeholder comment)
- `<body_file>`: the generated body (output of the import script)
- `<address_text>`: optional, e.g. `"(Logo/aw)"` — appended as `<address class="author">`

### `IMPORT_TEMPLATE.py` — Import script template

Copy this for each new article. Provides reusable helpers:

| Helper | Purpose |
|--------|---------|
| `p(cls, *line_nums)` | Emit `<p>` from raw OCR lines (1-indexed), with soft-hyphen line joining |
| `h(level, line_num)` | Emit `<h2>`/`<h3>` from a raw line |
| `blank()` | Emit blank line for readability |
| `raw(text)` | Emit raw HTML (figures, custom markup) |
| `basic_listing(start, end)` | Emit BASIC listing table (`plain right0`) |
| `tsv_table(header, start, end)` | Emit tab-separated table (`plain pre`) |

Workflow:
```
cp IMPORT_TEMPLATE.py /tmp/<NNN>_import.py
# edit: set RAW path, fill article-specific line mappings
python3 /tmp/<NNN>_import.py > /tmp/<NNN>_body.html
python3 inject.py "<article>.html" "/tmp/<NNN>_body.html" "(author/xx)"
```

The only creative work is deciding which raw lines map to which HTML elements. All prose flows mechanically from the OCR extraction file.

**Page markers**: When the `_ocr_raw.txt` contains `--- PAGE NNN ---` separator lines, skip them in line mappings. They exist only for human orientation during the mapping step.

### `soft_hyphen_report.py` — Soft hyphen diagnostic

Lists all soft hyphens (`\u00AD`) in an article HTML file with context, showing both resolution options (remove vs. replace with `-`) for each occurrence. Run after mechanical import to inventory work for the soft hyphen resolution pass, and again after resolution to confirm zero remain.

```
python3 tools/png2mag/soft_hyphen_report.py "<article>.html"
```

- Exits 0 if no soft hyphens found (PASS)
- Exits 1 if soft hyphens remain (agent must resolve them)

## Checklist Policy (Mandatory)

- Use one checklist file per article run in `/tmp/`.
- Start from template: `CHECKLIST_TEMPLATE.md`.
- Suggested naming:
  - `/tmp/<startpage>_<slug>_CHECKLIST.md`
- Create checklist instances by copying the template with `cp`, for example:
  - `cp CHECKLIST_TEMPLATE.md /tmp/133_von_basic_zu_assembler_teil3_CHECKLIST.md`
- Phases must be checked in order; do not check a later phase before earlier phase is complete.
- The final lock checkbox:
  - `All checkboxes above are checked`
  - is required before reporting article status `done`.
- Lock integrity rule:
  - The final lock may be checked only when:
  - phase 12 is checked
  - unresolved issue count is `0`
  - objective grep/lint checks are marked `pass`
- If final lock is unchecked, status must be reported as `partial`.
