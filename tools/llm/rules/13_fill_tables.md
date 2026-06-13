# 13 — Extract and place data tables

**Goal:** turn every `<p>TODO TABLE</p>` placeholder, and every prose
`Tabelle N` reference whose table is missing from the HTML, into a
proper `<table>` block. Captioned tables get wrapped in `<figure>` with
`<figcaption>`; uncaptioned tables stay bare.

## Extraction pipeline (per table)

1. **Build the page block index** per rule 0's recipe → `/tmp/64er_<YYMM>_p<NNN>_blocks.txt`.
2. **Identify target block** by either grepping the blocks file for a known cell value (e.g. a row header from the article's prose), or visual cross-check via a low-res page thumbnail.
3. **Crop just that block** with `magick … -crop WxH+X+Y` using the bbox from blocks.txt. If the crop exceeds 2000 px on any axis, also produce a resized copy for vision Read.
4. **Second-pass OCR on the crop** with PSM hint: `--psm 6` for compact tables, `--psm 4` for narrow tables with variable row heights.
5. **Vision-corrected HTML assembly** — Read the cropped image + the second-pass OCR text in parallel. Walk through OCR row by row; fix substitutions (`1`↔`l`↔`I`, `O`↔`0`, `rn`↔`m`, `cl`↔`d`); preserve old German spelling (`daß`, `muß`); preserve printed typos (`TPYE`, `SHURE`). If a cell is illegible, write `[ILLEGIBLE]`.
6. **Emit HTML** per the shape rules below.

## HTML shape per print type

- **Bordered data table with headers** → plain `<table>` with `<th>` header row.
- **Borderless glossary / key list** → `<table class="plain">` with no header row.
- **Table with a real caption** → wrap the whole `<table>` in `<figure>` with `<figcaption>`. A "real caption" is text printed on the scan in one of: `Tabelle: …`, `Tabelle N: …`/`Tabelle N. …`, `Bild N: …`/`Bild N. …` (for numbered figure-tables), or `STECKBRIEF: …` (yellow callout). **Do NOT promote section headings or bold titles above a table to `<figcaption>`** — a bold "Erklärung der einzelnen Bearbeitungsroutinen" above a table is a heading, not a caption.
- **The `<figcaption>` ALWAYS goes BELOW the table** inside the `<figure>`, even if the print places it above. Project convention.
- **Table with a heading or no caption marker** → bare `<table>`, no `<figure>`.

## "Bild N" can be a table — or pseudo-code

`Bild N.` on a scan doesn't always point at an image — 64'er routinely labels data tables AND structured pseudo-code boxes as `Bild N`. Sweep for these too, **but only if not already placed as an image**. For each `Bild` caption:
- If a PNG file `<page>-<n>.png` already exists AND the article HTML references it via `<img>` → leave alone (image is ground truth).
- If not → open the surrounding block. Decide visually:
  - **Rectangular grid of cells (data table)** → `<table>` inside `<figure>`.
  - **Indented pseudo-code or structured listing in a box** → `<pre>` inside `<figure>`. Preserve indentation as printed.
  - **Photo, diagram, schematic** → fall back to image workflow (rule 12).

## Multi-level headers

If the print has a spanning header (e.g. "Adresse" above sub-headers "Dez"/"Hex"), reproduce with `colspan`/`rowspan`. Don't flatten.

## Multi-page tables

Tables spanning two or more pages need a join check: entries in continuous order; last row of page N and first row of page N+1 are not duplicates; sub-section headers emit `<tr><th colspan="N">SectionName</th></tr>` rows; skip the yellow page-banner ("64'er Extra", "Daten verwalten") at the top of each continuation page.

## Sweeping captions across a whole issue

A pure `Tabelle …` grep is **not enough**. Use a layered sweep:

**Pass 1 — explicit captions:**
```bash
pdftotext -layout issues/<YYMM>/64er_19XX-XX.pdf /tmp/64er_<YYMM>_full.txt
grep -iE "Tabelle[ :.][^.]" /tmp/64er_<YYMM>_full.txt | \
  grep -vE "Farbtabelle|Steuersequenztabelle|[Ww]ertetabelle|Preistabelle|Linktabelle"
```
Also sweep for `Bild N\.`, `STECKBRIEF`, and `^\s*Listing [0-9]+\.`.

**Pass 2 — explicit placeholders:**
```bash
grep -l "TODO TABLE" issues/<YYMM>/*.html
```
Every `TODO TABLE` MUST be replaced. **Garbage adjacent to `TODO TABLE`** — the OCR pipeline sometimes drops a flattened prose representation in a `<p>…<br>…</p>` block right before or after. Delete that garbage when replacing.

**Pass 3 — UNCAPTIONED tables.** Many tables have NO `Tabelle N.` caption and won't appear in Pass 1. Patterns observed in 8607 alone that Pass 1 missed: `Verwendete Variable` callout (variable-reference list), `Monitor-/Fernseher-Eingangsnormen` + per-Stecker Pin/Signal tables, `Leistungen des Breitband-ISDN`, `Datenblatt des Seikosha MP-1300AI`, `Kurz belichtet — Melchers CPA-80X` test datasheet, `Funktionen der Sekundäradressen`. Other common shapes: bottom-half marketplace/comparison tables, yellow / tinted callout boxes, multi-page reference tables, fontspec/ASCII-code lookups, aside-style boxes.

**This pass is MANDATORY. "Visually scan every page" is not enough — make it mechanical** using rule 23's blocks index:

```bash
# 1. Walk each page's blocks index for known callout heading words
grep -hiE "Verwendete |Leistungen |Steckernormen|Belegung |Datenblatt|Kurz belichtet|Pin\s+Signal|Funktion: |Funktionen |Eingang|Kennummer" \
  issues/<YYMM>/_tmp/blocks/p*.txt

# 2. Walk for narrow-column multi-line blocks (sidebar callout shape):
#    blocks whose width < 350 px AND text contains 4+ short newline-
#    separated lines = strong candidate for tabular reference data.
for f in issues/<YYMM>/_tmp/blocks/p*.txt; do
  awk -F'[ =x+]' '/^block=/ { w=$5; if (w<350) print FILENAME": "$0 }' "$f"
done | head -50
```

For each candidate block:
1. Crop and view the page region (use rule 23's bbox).
2. Decide if it's a `<table>` / `<aside>` / `<pre>` per the HTML shape rules.
3. Confirm the article HTML doesn't already have it (no `<table>`, no `<img>` for it, no `TODO TABLE`).
4. Extract verbatim.

**Pass 3 must be REPORTED as done in the sub-agent's structured report**, including: pages walked, candidate blocks found, candidates extracted, candidates explicitly skipped (with reason). A sub-agent report that doesn't list Pass 3 explicitly = Pass 3 was skipped.

`TODO LISTING` is **NOT** a table — those are code listings (rule 14).

## Briefing for the sub-agent

The sub-agent must:

1. Render the issue PDF to `/tmp/64er_<YYMM>_pages/p-NNN.png` at `-r 150`
   (once, up front).
2. Run `pdftotext -layout` on the PDF to `/tmp/64er_<YYMM>_full.txt` for
   caption-sweep grep.
3. Find work to do via the documented three passes:
   - Pass 1: `Tabelle [N]?[.:]`, `STECKBRIEF`, `Bild N` (the last for
     pseudo-code / Bild-labelled tables).
   - Pass 2: `grep -l 'TODO TABLE' issues/<YYMM>/*.html` — every hit
     MUST be replaced.
   - Pass 3: visually scan the page thumbnails for uncaptioned
     marketplace / comparison / yellow-callout tables the prose
     introduces with "in der folgenden Übersicht", "wir haben
     zusammengefaßt", etc.
4. For each target, run the tesseract block-summary → crop → second
   tesseract pass pipeline described above. Use sub-sub-agents for
   image / vision reads.
5. Emit:
   - bare `<table>` when the print has no caption marker;
   - `<figure><table>…</table><figcaption>…</figcaption></figure>` when
     the print has `Tabelle N.` / `STECKBRIEF:` / `Bild N.` — figcaption
     **below** the table inside the `<figure>`, regardless of where
     the print prints it.
6. Place after the `</p>` of the first paragraph that references the
   table (never split a paragraph). If never referenced, append at
   the article tail, just before the closing `</article>` (or before
   the trailing `<address class="author">`).
7. **Skip tables already placed as images** (`<img>` inside `<figure>`)
   — image is the ground truth; converting loses fidelity.
8. **Delete adjacent OCR-garbage paragraphs** next to a `TODO TABLE`
   placeholder (the OCR pipeline sometimes drops a flattened
   `<p>…<br>…</p>` next to the placeholder).
9. Beautify all touched HTML at the end via
   `npx --yes js-beautify --type html --indent-size 4 --wrap-line-length 0 --replace`.
10. **Do not commit.** Return a per-article placement table, plus any
    `[ILLEGIBLE]` cells, any `TODO TABLE` you couldn't replace, any
    tables intentionally skipped, and any LOG.md entries written.

Critical preservation rules:
- Old German spelling stays (`daß`, `muß`, `läßt`, `ß`).
- Print typos stay (TPYE, unbalanced quotes, missing commas in
  decimals, mixed-case opcode bytes).
- Substitute OCR-confused glyphs (`0/O`, `1/l/I`, `rn/m`, `cl/d`),
  **never** add or drop characters.
- `TODO LISTING` is NOT a table — leave those to the listings rule.

## Verification

```bash
dir=issues/<YYMM>

# 1. no TODO TABLE survives
grep -l 'TODO TABLE' "$dir"/*.html && echo "  FAIL: TODO TABLE left"

# 2. every <table> has a matching </table>
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
bad = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<table[\s>]', s)); c = len(re.findall(r'</table>', s))
    if o != c: print(f"  mismatch {f}: <table>={o} </table>={c}"); bad += 1
sys.exit(1 if bad else 0)
PY
)" "$dir"

# 3. no [ILLEGIBLE] cells survive (they should be resolved before commit)
grep -l '\[ILLEGIBLE\]' "$dir"/*.html && echo "  WARN: [ILLEGIBLE] cells present"

# 4. every <figcaption> for a Tabelle N. caption lives BELOW the table
#    inside the same <figure>. Grep for misplaced ones (figcaption
#    before table within a figure).
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<figure[^>]*>(.*?)</figure>', s, re.DOTALL):
        body = m.group(1)
        # if a figure has both a figcaption and a table, figcaption must come AFTER table
        if '<figcaption' in body and '<table' in body:
            if body.index('<figcaption') < body.index('<table'):
                print(f"  figcaption-before-table in {f}")
PY
)" "$dir"

# 5. every Tabelle N reference in body has either: a) a matching
#    <figcaption>Tabelle N. …</figcaption> in the same file, b) an
#    <img> for Tabelle N (-tN.png), or c) an explicit LOG.md note.
#    Soft check — flag for human review:
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    refs = set()
    for m in re.finditer(r'\bTabelle (\d+)\b', s):
        refs.add(m.group(1))
    placed = set(re.findall(r'<figcaption>Tabelle (\d+)', s)) | \
             set(re.findall(r'-t(\d+)\.png', s))
    miss = refs - placed
    if miss:
        print(f"  {f}: Tabelle {sorted(miss)} referenced but not placed")
PY
)" "$dir"
```

All five checks should pass. Soft check (#5) may flag false positives
(prose mentioning "Tabelle N" of a previous issue, or a "Tabelle"
that turns out to be a bullet list); the orchestrator should walk
the flagged ones and decide.

## Notes / lessons

- The 9-TODO-TABLE 8607 sweep also caught 6 captioned tables that
  prose referenced but the import had missed (`36 Modem`, `50 R.C.S.`,
  `139 Basic-zu-Assembler`, `153 RP-System`, `174 Knobeleien Tab. 2`).
  Run all three passes — the TODO grep alone misses uncaptioned and
  STECKBRIEF tables.
- The yellow-callout-with-bullet-list pattern (e.g. 153 `Tabelle 1.
  Das kann das RP-System`) should be emitted as `<ul>` inside the
  `<figure>` rather than forcing a single-column `<table>`. Choose
  the shape that matches the print's visual structure.
- STECKBRIEF callouts deserve a dedicated follow-up sweep — they are
  often tracked in their own column ("der SUPERBASE-Steckbrief zu
  FIND, ENTER, SELECT, …") and may not all be flagged as Tabelle N.
  If extraction is too large for the table pass, log to `LOG.md`.
- Tables already placed as images (e.g. `174-t1.png`) are out of
  scope — never replace them with HTML tables.
