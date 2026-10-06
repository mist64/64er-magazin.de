# 160 — Extract and place data tables

**Applies to:** all — tables are printed in both kinds.

**Goal:** turn every `<p>TODO TABLE</p>` placeholder, and every prose
`Tabelle N` reference whose table is missing from the HTML, into a
proper `<table>` block. Captioned tables get wrapped in `<figure>` with
`<figcaption>`; uncaptioned tables stay bare.

> **PREREQUISITE — the block index (step 010) must already be built.**
> This rule's mandatory Pass 3 (uncaptioned tables) greps the per-page
> block index at `<OUT_DIR>/blocks/pNNN.txt`, built once per
> issue by [step 010](r010_ocr_blocks.md), which is the FIRST step in the
> chain and therefore always already done by the time this rule runs. If
> `<OUT_DIR>/blocks/` is missing, run step 010 now before
> continuing — do not substitute per-page on-demand OCR for the full
> Pass-3 sweep, which is how Pass 3 gets under-covered.

## Extraction pipeline (per table)

1. **The page block index is already built** — step 010 wrote it to `<OUT_DIR>/blocks/pNNN.txt`.
2. **Identify target block** by either grepping the blocks file for a known cell value (e.g. a row header from the article's prose), or visual cross-check via a low-res page thumbnail.
3. **Crop just that block** with `magick … -crop WxH+X+Y` using the bbox from blocks.txt. If the crop exceeds 2000 px on any axis, also produce a resized copy for vision Read.
4. **Second-pass OCR on the crop** with PSM hint: `--psm 6` for compact tables, `--psm 4` for narrow tables with variable row heights.
5. **Vision-corrected HTML assembly** — Read the cropped image + the second-pass OCR text in parallel. Walk through OCR row by row; fix substitutions (`1`↔`l`↔`I`, `O`↔`0`, `rn`↔`m`, `cl`↔`d`); preserve old German spelling (`daß`, `muß`); preserve printed typos (`TPYE`, `SHURE`). If a cell is illegible, write `[ILLEGIBLE]`.
6. **Emit HTML** per the shape rules below.

## Dense mark-matrices (300 dpi tesseract + 600 dpi vision cross-check)

Some tables are **+/–/x mark grids** (feature-vs-product comparison
matrices — e.g. `29 EDV für Lehrer` Tabelle 1: 73 rows × 12 printers).
tesseract is **useless for the cells** here — the `+`/`–`/`x` glyphs
don't OCR (they come back as `.+++ .++* xer*`) and a single dropped
space shifts every mark into the wrong column. Do NOT try to assemble
these from OCR text. Instead:

1. **tesseract (300 dpi) is only a structural scaffold** — use it to
   read the *row labels* and *section headings* (they're real words),
   never the mark cells. 300 dpi is tesseract's optimal input; never
   feed it 600 dpi.
2. **Read the mark cells from a 600 dpi vision crop**, column-gridded:
   - The page image is **`<tmp>/masters600/NNN.png`** (`031.png` = page 31),
     written by step 005: 600 dpi, A4, deskewed, cut and graded, and the same
     file r010 OCR'd. It is NOT pixel-aligned with tesseract's 300 dpi input --
     locate the table visually, don't reuse 300 dpi coordinates.
     (This rule used to name `~/DNB/<YYMM>/<YYMM>-cmyk/600_cropped/<NNN>.tiff`,
     where an earlier version of the chain put its derived 600 dpi pages. That
     directory does not exist; see `r000`, *THE SCAN IS THE ONLY INPUT*.)
   - Derive the column centres from the printed digit/name header, then
     crop **per section** and, if needed, composite the digit header
     directly above each sparse section so every mark's column is
     unambiguous. Split into strips rather than downscaling — you need
     per-cell legibility.
   - Where the low-res overview and the 600 dpi read disagree on a
     specific cell, the **600 dpi read wins**.
3. **Sanity-anchor** the result: pick a column with a known pattern
   (e.g. the specially-adapted printer that's `+` for almost everything,
   or a daisy-wheel that's `–` for all graphics) and confirm it reads
   that way top-to-bottom. Reproduce genuinely **blank** cells as empty
   (many matrices leave "not applicable" blank, distinct from `–`).
4. The orchestrator must **spot-verify at least one full section**
   cell-by-cell against the 600 dpi scan before accepting a dense
   matrix — a plausible-looking but column-shifted matrix is the
   failure mode.

## HTML shape per print type

- **Bordered data table with headers** → plain `<table>` with `<th>` header row.
- **Borderless glossary / key list** → `<table class="plain">` with no header row.
- **Table with a real caption** → wrap the whole `<table>` in `<figure>` with `<figcaption>`. A "real caption" is text printed on the scan in one of: `Tabelle: …`, `Tabelle N: …`/`Tabelle N. …`, `Bild N: …`/`Bild N. …` (for numbered figure-tables), or `STECKBRIEF: …` (yellow callout). **Do NOT promote section headings or bold titles above a table to `<figcaption>`** — a bold "Erklärung der einzelnen Bearbeitungsroutinen" above a table is a heading, not a caption. **EXCEPT a NAMED BOX whose title belongs to the box rather than to the surrounding section**: "Auf einen Blick: …" and "Stückliste" are captions and DO become `<figcaption>`, as 8609/22 and 8610/176 already have them. The test is whether the title would still make sense with the box removed; a section heading would, a box's own label would not.

Three further shapes this rule never named, all met on 8612:
- a label printed **inside** the box rather than above it (Stückliste) — still the box's caption;
- a `Bild` holding **both** tables and drawings (p61 Bild 7) — one figure, the tables typeset inside it;
- market-overview tables referenced only **generically** ("die Tabelle zeigt"), which no `Tabelle N` sweep will ever find.

**When a printed table interleaves drawings with per-item legends, keep the pairing.** Do not regroup the legends below the images: the legends differ per item (on 8612's EPROM tables the 2516 has CS, the 2532 has none, the 2564 has CS(X)), so a pile of legends under a row of drawings is not untidy, it is **misleading**. One column per item, each drawing above its own legend.
- **The `<figcaption>` ALWAYS goes BELOW the table** inside the `<figure>`, even if the print places it above. Project convention.
- **Table with a heading or no caption marker** → bare `<table>`, no `<figure>`.
- **NEVER fabricate a caption.** A `<figcaption>` is only allowed when its exact text is printed on the page (read it off step 010's block index or a 600 dpi scan crop; the PDF text layer is void, see r000); transcribe it verbatim. Do not compose a plausible-sounding descriptive title of your own — that is a fabrication. When in doubt, emit a bare `<table>` with no caption rather than an invented one. (Conversely, don't delete a real caption as "invented" without checking the scan: 8608/142 `Listing 1. Laufzeit-Testschleife in »C«` IS printed in bold on p145.)

## "Bild N" can be a table, pseudo-code, or a text box

`Bild N.` on a scan doesn't always point at an image — 64'er routinely labels data tables, structured pseudo-code boxes, AND plain boxed-text callouts as `Bild N`. Sweep for these too, **but only if not already placed as an image**. For each `Bild` caption:
- If a PNG file `<page>-<n>.png` already exists AND the article HTML references it via `<img>` → leave alone (image is ground truth).
- If not → open the surrounding block. Decide visually:
  - **Rectangular grid of cells (data table)** → `<table>` inside `<figure>`.
  - **Indented pseudo-code or structured listing in a box** → `<pre>` inside `<figure>`. Preserve indentation as printed.
  - **Boxed text / worked example / annotated ASCII diagram** (prose or a monospace example in a ruled box — e.g. `Bild 1. Beispiel für »wahre« und »falsche« Aussagen`, `Bild 1. Die elementarsten Grundlagen von Prolog`) → this is the common one that isn't a photo and isn't a grid. Emit it inside `<figure>` with `<figcaption>Bild N. …</figcaption>` below: use **`<pre>`** when the box preserves monospace layout / alignment / line breaks (the dominant precedent — 8602/8603/8606/8607 all use `<pre>`), or a plain **`<p>`** when it's flowing prose with no significant whitespace. Never drop it just because it isn't a table.
  - **Photo, diagram, schematic** → fall back to image workflow (rule 150).

A `Bild N` referenced in the body that is NONE of the above *and* has no crop is a gap, not a no-op: log it to `LOG.md` (as with a referenced-but-missing table) rather than silently skipping.

### A NUMBERED SERIES IS ALL TYPESET OR ALL CROPPED — decide for the series

The decision above is per-caption, and that splits a series. SH8604's **Bild
6a-6j** is the case: some members are plain grids (this rule typesets them),
some carry arrows and circled numbers (r150 crops them), so the page ended up
half typeset and half image, in one numbered run, looking like two different
things. **Look at the whole series first. If ANY member has to be cropped,
the whole series goes on r150's crop worklist and this step typesets none of
it.** Consistency within the series beats the per-caption rule.

The same question with the opposite answer: **a small box captioned only
"Tabelle N" that is really a DRAWING** (SH8604's KI Tabelle 1-6 — arrows,
circled numbers) is a crop, whatever the caption calls it. The caption names
the series; the ink decides the medium.

### WHEN A TYPESET BOX AND A CROPPED ONE ARE INTERLEAVED IN THE OCR

"Leave the drawing's garbage in place" is right only while every box on the
page is cropped. SH8604's p10 wove one typeset Bild (6h) and two drawings (6g,
6i) through the same paragraphs, so leaving the garbage left a **duplicate of
the text that was also typeset**. Where a page mixes the two, the OCR run of
the TYPESET box is removed with it; only a cropped box's garbage stays.

### THREE PRINTED SHAPES WITH NO NAME

- **Line-number documentation** — `10-30  Hier wird …`, `40-90  …` — is the
  dominant table shape in a course issue (6× in one SH8604 article alone) and
  was covered only by the generic *Text printed as a table* section. It is a
  **two-column `table.plain`**, line range and description. **Re-read every
  label off the crop**: the OCR systematically drops or misplaces them, and a
  dropped line range looks like prose.
- **A label printed inside the figure box, apart from its caption** ("Die
  komplett sortierte Datei."), and an **intro line printed in the box above a
  series**: both are part of the box, so they go inside the `<figure>` — the
  label as the first line of the box's content, the intro as a `<p>` before
  the first member. Neither is a `<figcaption>`; the caption is the printed
  "Bild N." line.
- **A long unlabelled typewriter-face data box** — SH8604's 176-record
  Texte-Datei, the `A AB ADRESSE` printout — is neither a table nor a Bild:
  it is machine output with no header row and no number. `<pre>`.

### A PAGE POINTER INSIDE A CAPTION IS STILL DROPPED

r170's rule drops a standalone "… auf Seite N" pointer, and r130 already says
r170 wins where both touch a caption. It holds here too: "Die Erklärung finden
Sie auf Seite 34." inside a `Tabelle N.` caption is a typesetting pointer to a
page the reader does not have, so the sentence goes and the rest of the caption
stays verbatim.

## `<code>` ALONE DOES NOT RENDER MONOSPACE — it needs `class="mono"`

`issues/style.css` does not merely leave `<code>` alone — it **sets
`li code, p code, td code { font-family: "RL", serif }`**. Monospace comes only
from `code.mono`, `span.mono`, `table.mono > tbody > tr > td` and `ul.mono > li`,
and `code.mono` (0,1,1) wins over `td code` (0,0,2) on specificity, taking the
font while leaving the `display: block; white-space: pre-line` layout intact.

So a bare `<code>` in a cell is actively rendered in a SERIF face. A column
whose whole purpose is alignment — a bit pattern, a star matrix, a listing line
— comes out proportional, and the markup looks right while the page is wrong.
That is why it survives review: `<code>` reads as "monospace" to anyone
checking the source.

This matters most where the cell carries `&nbsp;` for position: 8611/18's three
`Bild` figures set `   **` against `00011000` and the leading spaces are the
data. In a proportional face they mean nothing.

MEASURED: `<code class="mono">` is the convention, 56 uses across the corpus.
A bare `<code>` inside a `<td>` occurs 27 times in 4 files, and all four are
this defect — 8611/18 (21), plus `8412/86`, `8502/34` and `8506/52`, which are
published with BASIC and assembler lines that do not render monospace.

So: when the print sets a column in typewriter face, write
`<code class="mono">`, and check the rendered page rather than the markup.

## Multi-level headers

If the print has a spanning header (e.g. "Adresse" above sub-headers "Dez"/"Hex"), reproduce with `colspan`/`rowspan`. Don't flatten.

## Multi-page tables

Tables spanning two or more pages need a join check: entries in continuous order; last row of page N and first row of page N+1 are not duplicates; sub-section headers emit `<tr><th colspan="N">SectionName</th></tr>` rows; skip the yellow page-banner ("64'er Extra", "Daten verwalten") at the top of each continuation page.

## Sweeping captions across a whole issue

A pure `Tabelle …` grep is **not enough**. Use a layered sweep:

**Pass 1 — explicit captions:**
```bash
OUT_DIR=$(python3 -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.OUT_DIR)')
cat "$OUT_DIR"/blocks/p*.txt > "$OUT_DIR"/blocks_full.txt
grep -iE "Tabelle[ :.][^.]" "$OUT_DIR"/blocks_full.txt | \
  grep -vE "Farbtabelle|Steuersequenztabelle|[Ww]ertetabelle|Preistabelle|Linktabelle"
```
Also sweep for `Bild N\.`, `STECKBRIEF`, and `^\s*Listing [0-9]+\.`.

**Pass 2 — explicit placeholders:**
```bash
grep -l "TODO TABLE" issues/<YYMM>/*.html
```
Every `TODO TABLE` MUST be replaced. **Garbage adjacent to `TODO TABLE`** — the OCR pipeline sometimes drops a flattened prose representation in a `<p>…<br>…</p>` block right before or after. Delete that garbage when replacing.

**Pass 3 — UNCAPTIONED tables.** Many tables have NO `Tabelle N.` caption and won't appear in Pass 1. Patterns observed in 8607 alone that Pass 1 missed: `Verwendete Variable` callout (variable-reference list), `Monitor-/Fernseher-Eingangsnormen` + per-Stecker Pin/Signal tables, `Leistungen des Breitband-ISDN`, `Datenblatt des Seikosha MP-1300AI`, `Kurz belichtet — Melchers CPA-80X` test datasheet, `Funktionen der Sekundäradressen`. Other common shapes: bottom-half marketplace/comparison tables, yellow / tinted callout boxes, multi-page reference tables, fontspec/ASCII-code lookups, aside-style boxes.

**This pass is MANDATORY — and the VISUAL WALK is the mechanism, not the
sweeps.** This rule used to say the opposite ("visually scan every page is not
enough — make it mechanical"). MEASURED on 8611: **13 of the issue's 39 tables
were found ONLY by the visual walk, with no sweep hit at all**, and the
narrow-column sweep below found none of them. Walk every page. The sweeps
below are a supplement that catches a few shapes an eye skims past; they are
not a substitute and never were.

```bash
# 1. Walk each page's blocks index for known callout heading words
grep -hiE "Verwendete |Leistungen |Steckernormen|Belegung |Datenblatt|Kurz belichtet|Pin\s+Signal|Funktion: |Funktionen |Eingang|Kennummer" \
  <OUT_DIR>/blocks/p*.txt

# 2. Walk for narrow-column multi-line blocks (sidebar callout shape):
#    blocks whose width < 350 px AND text contains 4+ short newline-
#    separated lines = strong candidate for tabular reference data.
for f in <OUT_DIR>/blocks/p*.txt; do
  awk -F'bbox=' '/^block=/ { split($2, b, "x"); if (b[1]+0 < 350)
    print FILENAME": "$0 }' "$f"
done | head -50

# 3. A TINTED box yields NOTHING from the block index: tesseract returns
#    nothing at all on a halftone-screened panel, so such a table is
#    invisible to steps 1 and 2 and to every Tabelle sweep. Re-OCR the
#    suspect region through a tint pre-filter before concluding it is empty.
magick <tmp>/masters600/NNN.png -crop <WxH+X+Y> +repage \
  -colorspace Gray -blur 0x1.5 -threshold 57% png:- \
  | tesseract - - -l deu --psm 6
#    The blur fills the screen dots, the threshold then separates type from
#    tint; 55-60% is the usable band -- EXCEPT WHEN IT IS NOT.  On SH8604's
#    p60 the 55-60% band dropped a whole column and 50% recovered it, so the
#    band is a starting point to sweep, not a setting: try 50, 55, 57, 60 and
#    compare what each returns before concluding a column is not there.
#    On 8612 all six uncaptioned tables came
#    from the visual walk and NONE from a sweep -- the same as 8611.
```

> **This sweep returned 0 on every page of every issue it has ever run on,**
> and nobody noticed for three issues. The old field separator `-F'[ =x+]'`
> also splits `bbox` at its own `x`, so `$5` was the string `"bbo"`, and
> `"bbo" < 350` is a STRING comparison that is never true. A silent no-op
> reporting success is worse than no sweep: "Pass 3 done, 0 candidates" was
> a truthful report of nothing happening, in a pass whose own rule exists
> because 8607's was rubber-stamped.
>
> Fixed, it returns **1249 candidates** on a 192-page issue — mostly noise
> fragments — and still none of the 13 tables the walk found. So it is
> corrected here to stop it lying, not because it earns its place. Treat its
> output as a hint list to skim, and do the walk.

For each candidate block:
1. Crop and view the page region (use step 010's bbox).
2. Decide if it's a `<table>` / `<aside>` / `<pre>` per the HTML shape rules.
3. Confirm the article HTML doesn't already have it (no `<table>`, no `<img>` for it, no `TODO TABLE`).
4. Extract verbatim.

**Pass 3 must be REPORTED as done in the sub-agent's structured report**, including: pages walked, candidate blocks found, candidates extracted, candidates explicitly skipped (with reason). A sub-agent report that doesn't list Pass 3 explicitly = Pass 3 was skipped.

**Mechanical Pass-3 check (don't trust verbal confirmation).** A
sub-agent writing "Pass 3 done: 0 candidates" and moving on is a
known failure mode — 8607's Pass 3 was rubber-stamped, and a
second-look review later extracted 6 missed captioned tables (commit
`8d9b2f7da`). After Pass 3, **always run** the mechanical counters in
the Verification section (checks #6 and #7). If the `<table>` count
in the issue trails the `Tabelle N` figcaption count by 6 or more, or
if there are `<table>` blocks inside `<figure>` whose `<figcaption>`
doesn't mention `Tabelle`, treat Pass 3 as incomplete and re-run.

`TODO LISTING` is **NOT** a table — those are code listings (rule 170).

## Briefing for the sub-agent

The sub-agent must:

1. **Do not render the issue PDF.** It does not exist yet -- step 006 builds
   it at the END (`r000`, *THE PAGE IMAGE IS `masters600`*). Read
   `<tmp>/masters600/NNN.png` directly.
2. Concatenate step 010's block index to `<OUT_DIR>/blocks_full.txt` for
   caption-sweep grep.
3. Find work to do via the documented three passes:
   - Pass 1: `Tabelle [N]?[.:]`, `STECKBRIEF`, `Bild N` (the last for
     pseudo-code / Bild-labelled tables).
   - Pass 2: `grep -l 'TODO TABLE' issues/<YYMM>/*.html` — every hit
     MUST be replaced.
   - Pass 3 (MANDATORY — the VISUAL WALK is the mechanism; the sweeps only
     add to it. See the normative section above):
     sweep step 010's block index for uncaptioned tables, exactly as
     the normative "Sweeping captions across a whole issue → Pass 3"
     section above specifies. Run both blocks-index greps (known
     callout heading words, and narrow-column multi-line blocks),
     crop+decide each candidate, and REPORT the pages walked /
     candidates found / extracted / skipped-with-reason. Then run
     the mechanical Pass-3 counters (Verification #6 and #7). A
     "visually scan the thumbnails" shortcut is NOT sufficient and
     is how Pass 3 gets under-covered.
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

## A GREY GROUND IN A PRINTED TABLE IS MEANING — keep it

Owner, 2026-10-06, on SH8604 p46: *"tabelle 6 has some field with gray bg,
they seem to have a meaning, but we lost the styling."*

A tinted cell, row or block inside a table is not decoration. SH8604's
Tabelle 6 shades **six rows** — the ones the backtracking search discards —
against circled numbers ①②③④⑤ marking the chosen step at each stage. The
shading is the distinction the table exists to draw; typeset away, the reader
is left with two blocks of numbers and nothing to separate them.

**Mark it `class="shaded"`** on each `<td>`/`<th>` that carries the ground, or
on the `<tr>`'s cells where a whole row is shaded. `issues/style.css` defines
`--table-shaded` and the `.shaded` rule.

```html
<tr>
    <td>5</td>
    <td class="shaded">2</td>
    <td class="shaded">2</td>
    <td class="shaded">4</td>
    <td class="shaded">-2</td>
</tr>
```

Put it on the CELLS and not on the `<tr>`: the row's leading label column is
usually NOT shaded in the print (Tabelle 6's RAUM column stays white), and a
`tr` rule would shade it too.

**Nothing in the chain detects this.** The OCR returns characters, not tints,
so a shaded block is invisible to every check here — it is found by looking at
the crop, which is the same reading that r160's Pass 3 already asks for.
Whether other issues have lost table shading is unmeasured; it is not
retroactively corrected, and r000's *THE ISSUE YOU ARE WORKING ON IS THE
SCOPE* applies.

## An element you cannot place does NOT go at the end

**A printed table the prose never references is exactly this case**, not an
exception to it: with no mention to anchor it, there is no "first mention" to
insert after, and SH8604's KI Tabelle 3 went to the article tail, away from
Tabellen 2 and 4 which sit beside it on the page. A numbered series member
goes between its neighbours.

Owner, 2026-10-06. A table, figure or listing whose print position cannot be
determined is placed **where it fits best** — for a numbered series, between
its neighbours — never appended to the bottom of the article, which reads as
the conclusion and lands after the byline's closing run. The rule, the
reasoning and the check are in **r150, *NEVER LEAVE AN ORPHAN AT THE END***,
and they cover all three kinds.

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
    # Strip comments first: `<table[\s>]` matches inside one and `</table>`
    # does not, so a comment MENTIONING a table reported a mismatch on a
    # perfectly balanced file.  A rule that records its reasoning in comments
    # must not be failed by its own prose.
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
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
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
d = sys.argv[1]
items = []
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # TABELLE ONLY.  This matched "Tabelle|Bild" on both sides, so every Bild
    # PHOTO reference had to be satisfied by a placed TABLE -- 8 permanent lines
    # on SH8603, which is a gate that can never reach zero.  A Bild is r150's,
    # and r150's own mapping check is what covers it.  OCR damage still puts
    # ']', 'l' or 'I' where the digit was ("Tabelle ]"), found on 8612.
    # TWO THINGS \b GOT WRONG, both on SH8604's Kuenstliche Intelligenz.
    # (a) A COMPOUND IS NOT A REFERENCE.  `\bTabelle` matches the tail of
    #     "Schluesselwort-Tabelle", and the sentence continues "... Tabelle
    #     I AM und I'M aufgefuehrt werden" -- so the check demanded a placed
    #     "Tabelle I".  Hence the lookbehind: no word character and no hyphen
    #     before it.
    # (b) A DAMAGE TOKEN IS A LOOK, NOT A REFERENCE.  ']', 'l' and 'I' stand
    #     in for a digit the OCR lost, but they are also words, so they
    #     cannot be demanded of a placed table.  Report them to be read off
    #     the crop instead.
    refs = {m.group(1) for m in
            re.finditer(r'(?<![\w-])Tabelle (\d+)\b', s)}
    for m in re.finditer(r'(?<![\w-])Tabelle ([\]lI]+)\b', s):
        items.append('%s: "Tabelle %s" -- digit lost to OCR? read the crop'
                     % (f, m.group(1)))
    placed = set(re.findall(r'<figcaption>(?:Tabelle|Bild) ([\d\]lI]+)', s)) | \
             set(re.findall(r'-t(\d+)\.png', s))
    for n in sorted(refs - placed):
        items.append('%s: Tabelle %s referenced but not placed' % (f, n))
# Reported as a DELTA: an unnumbered printed "Tabelle." that the prose calls
# "Tabelle 1" is a legitimate permanent entry, and so is a reference to a table
# in another issue.  Walk them once, record them, see only what is new after.
new = R.delta(d, 'r160-table-refs', items)
R.report('check 5 (Tabelle N referenced, not placed)', new, len(items),
         d, 'r160-table-refs')
PY
)" "$dir"

# 6. Pass-3 sanity: count <table> elements and <figcaption>Tabelle …
#    figcaptions across the issue. They won't match exactly (bare
#    uncaptioned tables are legitimate), but a delta of 6+ tables found
#    after Pass 3 "completed" signals Pass 3 was rubber-stamped (8607
#    pattern, see commit 8d9b2f7da). Just emit the counts; the
#    orchestrator decides whether to re-run Pass 3.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
tables = 0; tabelle_caps = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    tables += len(re.findall(r'<table\b', s))
    tabelle_caps += len(re.findall(
        r'<figcaption[^>]*>(?:<[^>]+>)*\s*Tabelle\b', s, re.IGNORECASE))
print(f"  <table>={tables}  <figcaption>Tabelle…</figcaption>={tabelle_caps}")
PY
)" "$dir"

# 7. List every <table> inside a <figure> whose <figcaption> doesn't
#    mention "Tabelle". A bare <table> outside <figure> is legitimate
#    (uncaptioned inline data). A <figure>-wrapped table with a
#    non-Tabelle caption is fine too (e.g. STECKBRIEF), but the list
#    is for operator-eyeballing — confirm each one is intentional.
python3 -c "$(cat <<'PY'
import os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
d = sys.argv[1]
nocap, odd = [], []
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<figure\b[^>]*>(.*?)</figure>', s, re.DOTALL):
        body = m.group(1)
        if '<table' not in body: continue
        cap = re.search(r'<figcaption[^>]*>(.*?)</figcaption>',
                        body, re.DOTALL)
        if not cap:
            nocap.append('%s: <figure><table> with no <figcaption>' % f)
            continue
        # A Bild-captioned <figure><table> is the shape this rule REQUIRES
        # for a numbered figure-table, so it is not a finding.
        if 'Tabelle' not in cap.group(1) and 'Bild' not in cap.group(1):
            txt = re.sub(r'<[^>]+>', '', cap.group(1)).strip()[:60]
            odd.append('%s: %s' % (f, txt))
for x in nocap: print('  %s' % x)
# THE NAMED-BOX LIST IS A DELTA.  r160's own "NAMED BOX whose title belongs to
# the box" clause REQUIRES these captions, so this printed 6 permanent lines on
# SH8603 -- "Variablenliste", "Programmaufbau", "Programmablaufplan:",
# "Variable", "Zusammenfassung der Bedienung des Programms:", "Tabellarische
# Uebersicht", all correct.  The vocabulary is open by design, so it cannot be
# listed; what can be recorded is which ones were walked.
new = R.delta(d, 'r160-box-captions', odd)
R.report("check 7 (<figure><table> caption not 'Tabelle …')", new, len(odd),
         d, 'r160-box-captions')
PY
)" "$dir"
```

All seven checks should pass, and **checks 5 and 7 can now reach zero.**

Both are list-gates, not pass/fail checks: a correct issue produces a
non-empty list from each every run, which r000 forbids — *a gate that always
reports stops being read.* On SH8603 check 5 printed 8 lines and check 7
printed 6, and **every one of the 14 was correct.** Check 5's were Bild photo
references and an unnumbered printed "Tabelle." that the prose calls "Tabelle
1"; check 7's were the named-box captions this rule itself requires.

Two changes:

- **Check 5 is about `Tabelle` only.** It matched `Tabelle|Bild` on both sides,
  so every Bild reference had to be satisfied by a placed TABLE. A Bild is
  r150's business and r150's mapping check covers it.
- **Both report a DELTA** against `issues/<ID>/reviewed/<key>.txt`, via
  `r000_reviewed.py`. Walk the list once, record it with the reason, and later
  runs show only what is new. The remaining legitimate entries — an unnumbered
  printed "Tabelle.", a reference to a table in another issue, a named box
  whose vocabulary is open by design — stay visible as a count rather than as
  noise. This is the per-INSTANCE companion to r310's per-CLASS
  `adjudicated.txt`.

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). Pass 3 has its own version of
the same failure mode: the 8607 sub-agent reported "Pass 3 done, 0
candidates" without running the mechanical counters, and a second-look
review later extracted 6 missed tables. To make both failure modes
impossible here, every table the sub-agent emits must be backed by
**runnable verifier evidence pasted verbatim into the report**:

- For each `<table>` placed, paste the pre-fix vs. post-fix counts
  from verifier check #6 (`<table>=N <figcaption>Tabelle…=M`), so
  the orchestrator sees Pass 3 actually advanced the totals.
- For each Pass-3 candidate block walked (not just those extracted),
  paste the one line from `<OUT_DIR>/blocks/p<NNN>.txt` that flagged it
  plus a one-line disposition (`extracted`, `already image`, `already
  placed`, `false positive: bullet list`).
- For each `<figcaption>` typed, paste the verbatim caption text the
  sub-sub-agent returned from the cropped image OCR — so the
  orchestrator can confirm no caption was paraphrased.
- For each `[ILLEGIBLE]` cell, paste the crop path the sub-sub-agent
  used so a 600 dpi re-crop can be attempted by the orchestrator.

**No verifier output, no claimed table.** A table reported without the
pre/post counts + per-candidate disposition is treated as un-applied;
the orchestrator will re-dispatch Pass 3. "Pass 3 done, 0 candidates"
without the per-block enumeration is the canonical failure shape.

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
- **Pass 3 rubber-stamp failure (8607).** 8607's Pass 3 was reported
  as "done, 0 candidates" by the sub-agent. A second-look review
  later extracted 6 missed captioned tables (commit `8d9b2f7da`).
  Verbal "Pass 3 done" confirmation is not enough — always run the
  mechanical counters (Verification #6 and #7) and treat a
  6+-table delta as a re-run signal, not as acceptable variance.

## `class="plain"` is decided by the printed rules, not by the content

- The print sets the table **without ruled separators** → `<table class="plain">`
- The print sets a **ruled grid / boxed table** → `<table>`

This is a look-at-the-page decision. 8609 shipped an unruled bit-layout table in
`62 Tips & Tricks zum C 128` as a plain `<table>`.

## A spanning header row that labels a section is a heading, not a row

Where the print puts a section label above a table (*Matrix-Nadeldrucker*,
*Matrix-Tintenstrahldrucker*), the OCR sometimes lands it inside the table as
`<tr><th colspan="N">…</th></tr>` and sometimes outside as an `<h2>`. Make them
consistent: **the section label becomes an `<h2>` before its table**; only
labels that group *rows within* one table (a manufacturer name spanning the
row, say) stay as a spanning `<th>`.

## Text printed as a table must not stay a run of paragraphs

Recurring in 8609: two- and three-column material arrives as consecutive `<p>`s
(sometimes with the columns interleaved in the wrong reading order). Examples
that had to be rebuilt by hand — printer-command lists, prize lists
(`1. Preis 500 Mark` / `2. Preis 250 Mark` …, printed two-up so the OCR order
was 1,3,2,4), colour assignments (`Rahmen: logische Farbe …`), and
`Eingabe / Abschluß / Bedeutung` command tables.

Signature: a run of short paragraphs that share a common shape (`X: Y`,
`CMD  description`, `N. item`). Check the page — if it is set as a table, build
a table; if it is set as display lines inside a flowing paragraph, use one `<p>`
with `<br>`.

## A `<br>` IS THE AUTHOR'S LINE BREAK, NEVER THE COLUMN'S

**A break where the printed column simply ended is not reproduced.** Join it
with a space, rejoining a word split at a hyphen. A `<br>` marks only a break
the author made: a new list item, an address line, a code line, a deliberately
set display line.

MEASURED on 8612 before the owner's review: **283 `<br>` inside table cells**
(article 40 alone had 181, then 146 with 27, 160 with 23, 74 with 16) and 133
more in ordinary paragraphs. This rule caused them by saying to keep "printed
line breaks" in cells without distinguishing the two kinds. The owner: *"if it
looks like the line breaks are just because of the width of the table, dont
reproduce them in tables."*

**Joining CODE is not the same as joining prose.** A wrap after `: , * = + - ( /`
or before `+ - * / = ) " ;` hides no space — rejoin with none. Use one space
only between two alphanumeric tokens (`DRAW1,X1,Y1 TO`, `SYS 58732`). Joining
with a space everywhere gives `RX* COS(`, `RY= RY*199`, `?PEEK(174) +PEEK(175)
*256`. Two traps: **an HTML entity ends in `;`** (`&lt;&gt;`), so it is not an
operator boundary; and tokenise before joining.

**A discriminator for BASIC cells, advisory only:** if the text after the `<br>`
does not begin a new line number, the break is a wrap artefact. It is **wrong
for unnumbered code** — 146's Tabelle 1 runs statements together with spaces in
the print itself — so decide on the crop, never on this test alone.