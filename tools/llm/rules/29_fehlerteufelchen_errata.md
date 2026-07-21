# 29 — Apply cross-issue Fehlerteufelchen errata to this issue's articles

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

## Run order — LAST (after rules 0–28)

This rule must run **after** every single-issue rule is done, because it:
- wraps a **figure caption / listing caption / table cell / inline value**
  in a link — so figures (rules 10/12), listings (rules 10/14) and tables
  (rule 13) must already be placed, and
- edits `prg/<name>.txt` — so the PRG extraction (rule 9) must be done, and
- must not be disturbed by later text passes — so heading case (25),
  autolink (26), OCR cleanup (27) and hierarchy (28) must already have run
  (they would otherwise re-touch the wrapped element).

It is also **re-run over old issues** whenever a new issue is imported, in
case the new issue's Fehlerteufelchen corrects an already-published article
(see step "Asymmetry" below). For issue `YYNN`, scan the Fehlerteufelchen
of **every issue after `YYNN`**.

## Full procedure — `tools/llm/new/fehlerteufelchen_workflow.md`

That workflow doc is the authoritative, exhaustive procedure (finding the
rubric page in each candidate issue, three-OCR-layer verification, building
the `Fehlerteufelchen.md` index, the `prg/*.txt` Style A/B patterns). Read
it before running this rule. The essentials are distilled below.

## Inputs

- `Fehlerteufelchen.md` (repo root) — the cross-issue errata index. Each
  item: `**Article** (Ausgabe M/YY, Seite NNN)`. Build/extend it per the
  workflow doc from the later issues' Fehlerteufelchen rubrics.
- `fehlerteufelchen_pages/<issue>.pdf` — single-page rubric extracts,
  **untracked; never `git add` them, never name them in a commit message**
  (workflow doc step 10).
- The already-imported FT-source article HTML where available
  (`issues/<FT-issue>/<page> Fehlerteufelchen.html`) — the erratum text is
  transcribed from there / the scan, never composed from memory.

## For each erratum targeting an article in THIS issue

1. **Find the source article** by `<meta name="64er.pages">` start-page +
   title overlap (not filename). `Ausgabe N/YY → issues/YYNN/`,
   `Sonderheft N/YY → issues/SH<YY><NN>/`. If the article isn't imported
   yet, note and skip.

2. **Add the aside** at the very end of the article, immediately before
   `</article>` (and after the byline / any trailing listings — rule 10
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
   the erratum fixes numbered Basic code (workflow doc step 8): header
   `;inkl. Fehlerteufelchen N/YYYY` after the `;<file>.prg ==XXXX==` line,
   then Style A (single inline `;Zeile X neu entspr. …` marker above the
   fixed line) or Style B (comment the old line with `;`, corrected line
   below). Disk-already-correct → header note only, no per-line markers.

## Anti-memory (mandatory)

Every erratum word must trace to the print: render the FT PDF page → OCR
(tesseract + paddle) → **Read the PNG multimodally** → write to
`_tmp/<issue>_ft.txt` → Read that file → edit the article. Never compose
erratum text from memory. Preserve original typos and German spelling
(`daß`, `muß`, »…«). See [[feedback_print_verbatim]] and
`tools/png2mag/WORKFLOW.md`.

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
`tools/llm/new/fehlerteufelchen_workflow.md` §"Verification checklist".

## Notes

- Reference errata index: `/Fehlerteufelchen.md`.
- The rubric ran monthly 1986–1987, sporadically after; ~post-1988 it was
  folded into Basic-Corner / Tips & Tricks / Reparaturecke — so for a 1986
  issue, later 1986–1987 issues are the primary hunting ground.
- A cartoon-devil banner heads the rubric and is usually invisible to OCR —
  always confirm the rubric page visually (workflow doc step 1).
