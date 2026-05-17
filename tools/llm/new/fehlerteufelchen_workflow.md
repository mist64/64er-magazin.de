# Fehlerteufelchen Cross-Issue Workflow

How to find every Fehlerteufelchen rubric in a range of issues, index them in `Fehlerteufelchen.md`, and apply the corrections to both the source articles and their `.txt` listings.

## What Fehlerteufelchen is

The "Fehlerteufelchen" rubric was 64'er-Magazin's errata column. Each monthly issue (1986–1987 consistently, sporadic afterwards) had a 1-page rubric listing corrections for past articles. After ~1988 the rubric was discontinued or folded into other rubrics (Basic Corner, Tips & Tricks, Reparaturecke). A column header graphic appears at the page top — usually a small cartoon devil — and is often invisible to OCR.

## Pipeline

### 1. Find the Fehlerteufelchen page in each candidate issue

Source PDFs live in `~/DNB/64er_OCR/OCR-YYYY_MM_64er[_HIRES].pdf` (Year > 1985 has them; later years drop the rubric).

Heuristics, in priority order:

1. **TOC reference**: PDF pages 4-7 list Fehlerteufelchen entries like `Fehlerteufelchen ... 73`. The CSV has format `<title> <page>`. Apply per-issue offset (PDF page = magazine page − 2 typically; varies). When multiple page numbers, take the **largest** (rubric page, not inline-mention pages).
2. **First-5-lines header**: scan all pages for `Fehlerteufelchen` in the first 5 lines (top-of-page article header).
3. **Score-based fallback**: count `Zeile`, `Ausgabe N/MM`, `Seite N`, `korrigiert`, `muß` on each page. Page with highest score in mid-magazine is a candidate.

All three approaches need visual verification — OCR misses graphic banners. **Render each candidate to image and Read multimodally** to confirm.

### 2. Extract single-page PDFs

```bash
qpdf <source.pdf> --pages . <N> -- fehlerteufelchen_pages/<issue>.pdf
```

Save to `fehlerteufelchen_pages/<issue>.pdf` (untracked — do not commit; per user instruction).

### 3. Verify with three OCR layers

For 99%+ confidence:

1. **Tesseract** (`tesseract <img> - -l deu --psm 6`) — fast text layer.
2. **PaddleOCR PP-OCRv5** (`PaddleOCR(lang='german').predict(<img>)`) — better with stylized banners.
3. **Vision Read** on the rendered PNG — catches banners both OCR engines miss.

Keep only pages where at least one method finds the rubric. Remove false positives.

### 4. Assemble `Fehlerteufelchen.md`

One section per issue, ordered chronologically:

```markdown
## Ausgabe N/YY

Seite NNN

- **Article Name** (Ausgabe N/YY, Seite NNN)
- **Another Article** (Sonderheft N/YY, Seite NNN)
```

- Use **printed magazine page**, not PDF page, for "Seite NNN".
- Preserve German typography: `&`, `daß`, `muß`, »...«.
- Each item: article title + `Ausgabe X/YY` or `Sonderheft X/YY` + `Seite NNN` (preserve `ff` suffix).

### 5. Cross-check articles in repo

For each item in `Fehlerteufelchen.md`, find the source article. The pattern:
- `Ausgabe N/YY` → `issues/YYNN/<page> <title>.html` (where pages are determined by `<meta name="64er.pages">`)
- `Sonderheft N/YY` → `issues/SH<YY><NN>/<page> <title>.html`

Match by start-page + title overlap. Multi-page articles cover ranges; use `pages` meta from HTML, not filename.

Many references will be to articles not yet imported (in older or out-of-range issues / Sonderhefte). Note those, skip.

### 6. Add erratum aside to source article

If the article has no `<aside class="fehlerteufelchen">`, extract the erratum text from the FT source HTML (e.g. `issues/<FT-issue>/<FT-page> Fehlerteufelchen.html`) and insert at end of article:

```html
        <aside class="fehlerteufelchen" id="fehlerteufelchen">
            <h2>Fehlerteufelchen</h2>

            <p>... erratum paragraph(s) ...</p>

            <!-- Korrektur im Programm angewendet -->
            <!-- 64'er M/YYYY -->
        </aside>
    </article>
```

Trailing comments:
- `<!-- 64'er M/YYYY -->` — always; names the issue where the erratum appeared
- One of the following status comments, ABOVE the `<!-- 64'er ... -->` line, when the erratum involves a code listing:
  - `<!-- Korrektur im Programm angewendet -->` — the source `.txt` listing in `prg/` has been patched (Style A or B)
  - `<!-- Disk-Version bereits korrigiert -->` — the print typo never propagated to the `.D64` disk; the `.txt`/`.prg` already match the corrected version (`.txt` may carry the same note `(...; Disk-Version bereits korrigiert)` in its header)
- **Omit** the status comment when the erratum is not listing-related (hardware/figcaption/price corrections, reprints without the affected element, etc.) — i.e. when there's no `prg/<name>.txt` to apply the fix to.

If a `<!-- Fehlerteufelchen ... -->` placeholder comment already exists in the article (old convention), **remove** it after adding the aside (don't keep both).

### 7. Wrap the affected element with a link

Look in the article body for the element the erratum addresses. Wrap it in:

```html
<a href="#fehlerteufelchen" class="fehlerteufelchen_link">...</a>
```

Common wrap targets (per existing convention):

- **Bild N figcaption** — when the erratum corrects a figure or its caption
- **Specific code line** inside a `<pre>` listing — when the line is inline in HTML
- **Table cell** `<td>` — when correcting a tabular value
- **Inline price / value** — when correcting a number in prose
- **Listing N figcaption** — fallback when the listing is auto-generated from `data-filename` (cannot wrap individual lines)

**Don't wrap content inside the aside itself** — that creates a self-referencing link.

If the article is a **reprint** without the affected element (e.g. a Sonderheft reprint that omitted some figures), **omit the wrap**. The aside alone still provides the correction.

### 8. Update the source listing `.txt` (if applicable)

If the erratum corrects code in a numbered Basic listing, find the source `.txt` in `issues/<source-issue>/prg/<name>.txt`.

**Style — three patterns observed:**

**Header** (always, right after `;<file>.prg ==XXXX==` line):
```
;inkl. Fehlerteufelchen N/YYYY
```
Optional parenthetical: `(Zeile X)`, `(Zeilen X, Y, Z)`, `(...; Disk-Version bereits korrigiert)`.

**Style A — single inline marker per fixed line:**
```
;Zeile 336 neu entspr. Fehlerteufelchen 4/1986
  336 goto 375
```
Place the marker comment right above the corrected line. Best for one or two changed lines.

**Style B — show old before new:**
```
;vor Fehlerteufelchen N/YYYY
;   1 poke650,128:ifpeek(1022)=0then5000
    1 clr:poke650,128:ifpeek(1022)=0then5000
```
Comment out the original line(s) with `;`, then put the corrected version below. Use when preserving the history aids the reader.

**Disk-already-correct case:** When the print typo never reached the disk version (e.g. an unreadable number that's clear in the binary), use header only:
```
;inkl. Fehlerteufelchen N/YYYY (Zeile NNN; Disk-Version bereits korrigiert)
```
No per-line markers — the .txt as extracted is already correct.

### 9. Asymmetry to watch for

Past contributor work (e.g. thierer's per-issue PRs) sometimes applied the fix to **only one side** — `.txt` was patched but the article aside was missing, or vice versa. When auditing, check **both** sides for every item.

### 10. Do not commit `fehlerteufelchen_pages/`

The single-page extract PDFs are working reference material, not part of the published site. Add to `.gitignore` or just don't `git add` them. Don't mention them in commit messages either.

## Verification checklist

For each erratum:
- [ ] Source article exists in repo (find via `64er.pages` meta + title)
- [ ] Aside present at end of article with `class="fehlerteufelchen" id="fehlerteufelchen"`
- [ ] Aside text matches print (preserve original typos, German spelling)
- [ ] `<a href="#fehlerteufelchen" class="fehlerteufelchen_link">` wraps the right body element (or absent if article is a reprint missing that element)
- [ ] Comment trailer `<!-- 64'er M/YYYY -->` names the FT issue
- [ ] If listing-related: status comment `<!-- Korrektur im Programm angewendet -->` or `<!-- Disk-Version bereits korrigiert -->` above the issue trailer
- [ ] If listing in `prg/<name>.txt`: header annotation + per-line markers in Style A or B (or disk-already-correct note)
- [ ] No duplicate erratum (e.g. both a placeholder comment AND an aside)

## Anti-memory rule

When extracting text from the print scan:
1. Render PDF page → PNG
2. OCR (tesseract + paddle)
3. Visually verify with Read multimodal
4. Write to `_tmp/<issue>_ft.txt`
5. Read that file, then edit articles

Don't compose erratum text from memory or training knowledge — every word must trace to the print.

## Related

- Errata items index: `/Fehlerteufelchen.md`
- Standard PRG workflow: `tools/llm/new/prg_workflow.md`
- Anti-memory enforcement: `tools/png2mag/WORKFLOW.md`
