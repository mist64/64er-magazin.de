# 300 — Apply cross-issue Fehlerteufelchen errata to this issue's articles

**Goal:** the "Fehlerteufelchen" was 64'er's errata column. Corrections
for **this** issue's articles were printed in the Fehlerteufelchen rubric
of **later** issues. This rule harvests every such correction and applies
it to the affected article here: an `<aside class="fehlerteufelchen">` at
the end of the article, an in-text link to it, and — for code errata — a
matching fix in the `prg/*.txt` listing.

This is why prior issues carry 2–7 of these asides each (8601–8607) while a
freshly-built issue has **zero**: the errata live in issues that are
imported later, so this step is a **cross-issue enrichment**, not a
single-issue transform.

## Run order — LAST (after rules 000–290)

This rule must run **after** every single-issue rule is done, because it:
- wraps a **figure caption / listing caption / table cell / inline value**
  in a link — so figures (rules 130/150), listings (rules 130/170) and tables
  (rule 160) must already be placed, and
- edits `prg/<name>.txt` — so the PRG extraction (rule 120) must be done, and
- must not be disturbed by later text passes — so heading case (260),
  autolink (270), OCR cleanup (280) and hierarchy (290) must already have run
  (they would otherwise re-touch the wrapped element).

It is also **re-run over old issues** whenever a new issue is imported, in
case the new issue's Fehlerteufelchen corrects an already-published article
(see step "Asymmetry" below). For issue `YYNN`, scan the Fehlerteufelchen
of **every issue after `YYNN`**.

## Full procedure

The exhaustive procedure — finding the rubric page in each candidate issue,
three-OCR-layer verification, building the `Fehlerteufelchen.md` index, the
`prg/*.txt` Style A/B patterns — is the **appendix at the foot of this file**.
Read it before running this rule. The essentials are distilled below.

## Inputs

- `Fehlerteufelchen.md` (repo root) — the cross-issue errata index. Each
  item: `**Article** (Ausgabe M/YY, Seite NNN)`. Build/extend it per the
  workflow doc from the later issues' Fehlerteufelchen rubrics.
- `fehlerteufelchen_pages/<issue>.pdf` — single-page rubric extracts,
  **untracked; never `git add` them, never name them in a commit message**
  (appendix step 10).
- The already-imported FT-source article HTML where available
  (`issues/<FT-issue>/<page> Fehlerteufelchen.html`) — the erratum text is
  transcribed from there / the scan, never composed from memory.

## For each erratum targeting an article in THIS issue

1. **Find the source article** by `<meta name="64er.pages">` start-page +
   title overlap (not filename). `Ausgabe N/YY → issues/YYNN/`,
   `Sonderheft N/YY → issues/SH<YY><NN>/`. If the article isn't imported
   yet, note and skip.

2. **Add the aside** at the very end of the article, immediately before
   `</article>` (and after the byline / any trailing listings — rule 130
   already reserves this as the last block):

   ```html
           <aside class="fehlerteufelchen" id="fehlerteufelchen">
               <h2>Fehlerteufelchen</h2>

               <p>… erratum paragraph(s), transcribed verbatim …</p>

               <!-- Korrektur im Programm angewendet -->
               <!-- 64'er M/YYYY -->
           </aside>
       </article>
   ```
   - `<h2>Fehlerteufelchen</h2>` is the heading (matches 8606; some early
     issues used `<h3>` — use **h2** going forward).
   - `<!-- 64'er M/YYYY -->` — **always**, names the issue the erratum
     appeared in.
   - **Status comment** (only when the erratum concerns a code listing),
     placed **above** the `64'er` line — exactly one of:
     - `<!-- Korrektur im Programm angewendet -->` — real code bug, fixed
       in the `prg/*.txt` (step 4).
     - `<!-- Disk-Version bereits korrigiert -->` — the `.D64` was patched
       after the print run; the printed listing was wrong but the disk
       works; `.txt` unchanged.
     - `<!-- Reiner Druckfehler -->` — print-only artifact (unreadable
       digit, hardware-schematic typo); disk was never wrong.
   - **Omit** the status comment entirely for non-code errata (figure
     caption, prices, addresses, reprints).
   - If an old `<!-- Fehlerteufelchen … -->` placeholder comment exists,
     **delete it** — never ship both placeholder and aside.
   - **Multiple corrections to the SAME article → ONE aside.** An
     article corrected in more than one later issue (e.g. 8608's
     `17 Leserforum`: a Lichtorgel Watt fix *and* an SX vendor-name fix,
     both from 10/86) gets a single `<aside … id="fehlerteufelchen">`
     with one `<p>` per correction — `id` must stay unique on the page,
     and every in-text link (step 3) points at that one anchor. If the
     corrections came from different issues, list each `<!-- 64'er
     M/YYYY -->` trailer (one per correction, in issue order).

3. **Wrap the affected element** with the link (do NOT wrap anything inside
   the aside — that self-references):

   ```html
   <a href="#fehlerteufelchen" class="fehlerteufelchen_link">…</a>
   ```
   Wrap the most specific element the erratum addresses, per convention:
   Bild-N figcaption · a specific `<pre>` code line (when inline) · a
   table `<td>` · an inline price/value in prose · else the Listing-N
   figcaption (fallback when the listing is auto-generated from
   `data-filename` and individual lines can't be wrapped). If the article
   is a **reprint** missing that element, omit the wrap — the aside alone
   still carries the correction.

4. **Patch the source listing** `issues/<source-issue>/prg/<name>.txt` when
   the erratum fixes numbered Basic code (appendix step 8): header
   `;inkl. Fehlerteufelchen N/YYYY` after the `;<file>.prg ==XXXX==` line,
   then Style A (single inline `;Zeile X neu entspr. …` marker above the
   fixed line) or Style B (comment the old line with `;`, corrected line
   below). Disk-already-correct → header note only, no per-line markers.

## Anti-memory (mandatory)

Every erratum word must trace to the print: render the FT PDF page → OCR
(tesseract + paddle) → **Read the PNG multimodally** → write to
`_tmp/<issue>_ft.txt` → Read that file → edit the article. Never compose
erratum text from memory. Preserve original typos and German spelling
(`daß`, `muß`, »…«). See
the anti-memory rule in `r000_orchestration.md`.

## Asymmetry to watch (both sides!)

Past work sometimes patched only one side — the `.txt` was fixed but the
article aside was missing, or vice versa. For **every** item verify BOTH
the article aside AND the `prg/*.txt` fix exist.

## Verification

```bash
dir=issues/<YYMM>
# every aside is well-formed and anchored
grep -rl 'aside class="fehlerteufelchen" id="fehlerteufelchen"' "$dir"/*.html
# every aside names its source issue
for f in $(grep -rl 'class="fehlerteufelchen"' "$dir"/*.html); do
  grep -q "<!-- 64'er " "$f" || echo "  $f: aside missing <!-- 64'er M/YYYY --> trailer"
done
# no orphan links (link present but no aside in same file)
for f in "$dir"/*.html; do
  grep -q 'href="#fehlerteufelchen"' "$f" && \
    ! grep -q 'id="fehlerteufelchen"' "$f" && echo "  $f: link with no aside"
done
# no leftover placeholder comments alongside an aside
grep -rl '<!-- Fehlerteufelchen' "$dir"/*.html
```

Cross-check against the full checklist in
the "Verification checklist" below.

## Notes

- Reference errata index: `/Fehlerteufelchen.md`.
- The rubric ran monthly 1986–1987, sporadically after; ~post-1988 it was
  folded into Basic-Corner / Tips & Tricks / Reparaturecke — so for a 1986
  issue, later 1986–1987 issues are the primary hunting ground.
- A cartoon-devil banner heads the rubric and is usually invisible to OCR —
  always confirm the rubric page visually (appendix step 1).

---

# Appendix — the procedure in full

Folded in from what used to be the separate fehlerteufelchen workflow doc,
which lived outside the rules directory.
A rule must be self-contained: r000 briefs a sub-agent with the rule file as its
primary instruction source, so a rule that points outward for its actual
procedure hands the sub-agent an incomplete spec.

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
  - `<!-- Korrektur im Programm angewendet -->` — Case 1: real code bug, fixed in the source `.txt` listing in `prg/` (Style A or B)
  - `<!-- Disk-Version bereits korrigiert -->` — Case 2: the `.D64` disk was patched after the print run, so the disk works even though the printed listing has the bug. The `.txt` may carry the same note `(...; Disk-Version bereits korrigiert)` in its header.
  - `<!-- Reiner Druckfehler -->` — Case 3: print-only artifact (unreadable digit, mis-printed line that users were instructed to type differently, hardware schematic typo). The disk was never wrong; no `.txt` change applicable.
- **Omit** the status comment entirely when the erratum is not about a code listing (hardware figure caption, prices, addresses, reprints without the affected element, etc.).

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
- Standard PRG workflow: rule `r120_prg_from_d64.md`
- Anti-memory enforcement: `r000_orchestration.md`, "OCR cleanup granularity"

## When an erratum corrects a listing, check the disk file FIRST

The Programm-Service disk usually carries the **already-corrected** program, so
an erratum that fixes a listing line often describes a defect that exists only
in print. 8609's Bar-Codes erratum (11/86) says line 85 has two digits
transposed; `prg/ean-codes.txt` line 85 already reads
`85 data"0111011","0010001","1000100"` — exactly the corrected form.

So: add the aside (it records what the printed listing got wrong), and **do not
touch the `.txt`**. Only when the disk file also carries the error is there a
listing to repair, and that is a separate decision.

## Record the errata state in the listing's own `;` header

The `.txt` listings carry a `;` comment block after the `;name.prg ==addr==`
header, and the corpus already has a settled vocabulary for errata state. Use
it — do not invent wording, and do not leave the state unrecorded:

```
;vor Fehlerteufelchen 1/1987
;inkl. Fehlerteufelchen 8/1986 (Zeile 20; Disk-Version bereits korrigiert)
;inkl. Fehlerteufelchen 9/1986 (Zeile 230; Zeile 190 in der Disk-Version bereits korrigiert)
;Zeile 391 neu entspr. Fehlerteufelchen 4/1986
;Fehlerteufelchen 2/1985 (Zeile 3040) wurde darauf angewandt
```

So the two branches both have a home:

- **the disk already carries the fix** → `;inkl. Fehlerteufelchen N/YYYY (Zeile
  X; Disk-Version bereits korrigiert)`, and the `.txt` is left untouched
- **the disk is the pre-correction version** → `;vor Fehlerteufelchen N/YYYY`,
  and the `.txt` is left as the disk shipped; or, if the correction is applied,
  `;Zeile X neu entspr. Fehlerteufelchen N/YYYY` naming each changed line

Default to recording rather than patching: readers typed these programs from the
disk, so the disk state is the historical fact and the aside on the article
already documents what the print got wrong. Patch only deliberately, and then
say which lines changed.

Placement is after the `==addr==` header, before the first program line
(`8607/prg/farbenspiel.txt` is the model).

The other `;` forms in use, worth preserving when they exist: `;Quelle: <disk or
URL>`, `;Eingetippt von <name>`, `;version=simons`, `;*** Machine language part
skipped. ***`.

## Binary listings: check the bytes, record in LOG.md

An MSE/machine-code listing is stored as a `.prg`, which cannot carry a `;`
header. Two consequences:

1. **Check the bytes directly** rather than guessing. The printed erratum gives
   the corrected rows with their addresses; read the `.prg`'s load address from
   its first two bytes and compare each row. 8609's `viza.key.prg` matched the
   10/86 erratum at all five addresses, so the disk had shipped corrected and
   there was nothing to patch — settled in one command, no judgement needed.
2. **Record the finding in the issue's `LOG.md`**, since the file itself cannot
   hold the note. The `<aside class="fehlerteufelchen">` on the article still
   carries what the print got wrong; the LOG entry carries what the disk state
   is.

## Every aside carries a disposition comment

An erratum aside says what the print got wrong. It must ALSO say what happened
to the program, as an HTML comment immediately before the `<!-- 64'er N/YYYY -->`
source marker. The corpus vocabulary — use it verbatim, do not invent wording:

| comment | meaning |
|---|---|
| `<!-- Reiner Druckfehler -->` | the error exists only in the print; no program is affected (a wrong figure number, a garbled sentence) |
| `<!-- Disk-Version bereits korrigiert -->` | a program IS affected, but the Programm-Service disk already shipped the corrected version — nothing was patched |
| `<!-- Korrektur im Programm angewendet -->` | the correction was applied to the listing in `prg/` |

```html
        <!-- Disk-Version bereits korrigiert -->
        <!-- 64'er 10/1986 -->
    </aside>
```

The three are mutually exclusive and the choice is a **finding, not a guess**:

- for a `.txt` listing, diff the erratum's corrected lines against the file
- for a `.prg`, read the load address from the first two bytes and compare the
  erratum's rows byte for byte at their printed addresses

8609: `viza.key.prg` matched the 10/86 erratum at all five addresses and
`ean-codes.txt` already had the corrected line 85 — both
`Disk-Version bereits korrigiert`. `xref 7.0.txt` differs on all seven lines of
the 1/87 erratum, so it is NOT one of those two, and stays unmarked until the
listing is either patched (`Korrektur im Programm angewendet`) or the decision
is taken to leave it.

Getting this wrong is not cosmetic: `Reiner Druckfehler` on an erratum that
does affect a program tells a future reader no listing needs checking.
