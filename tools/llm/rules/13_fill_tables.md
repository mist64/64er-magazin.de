# 13 — Extract and place data tables

**Goal:** turn every `<p>TODO TABLE</p>` placeholder, and every prose
`Tabelle N` reference whose table is missing from the HTML, into a
proper `<table>` block. Captioned tables get wrapped in `<figure>` with
`<figcaption>`; uncaptioned tables stay bare.

The full procedural spec lives in `tools/llm/new/table_workflow.md`
and is the authoritative reference. This rule file is the dispatch +
verification gate around that workflow.

## Briefing for the sub-agent

The sub-agent must:

1. Render the issue PDF to `/tmp/<YYMM>_pages/p-NNN.png` at `-r 150`
   (once, up front).
2. Run `pdftotext -layout` on the PDF to `/tmp/<YYMM>_full.txt` for
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
4. For each target, run the `tesseract` block-summary → crop → second
   tesseract pass pipeline (`table_workflow.md` Steps 1–6). Use sub-
   sub-agents for image / vision reads.
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
