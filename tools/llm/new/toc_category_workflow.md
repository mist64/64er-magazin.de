# TOC Category Workflow

How to derive `issues/YYMM/toc.txt` (the per-issue list of valid categories, in sort order) and fill `<meta name="64er.toc_category">` in every article HTML.

Companion to `toc_title_workflow.md`, which covers the article title as it appears in the TOC.

## How to run

```
Set up toc.txt and fill 64er.toc_category in all HTMLs for issue YYMM
per tools/llm/new/toc_category_workflow.md.
```

**Input:**
- `issues/YYMM/64er_*.pdf` — full issue PDF.
- `issues/YYMM/_work/p006/page_300.png`, `_work/p007/page_300.png` — 300dpi rendered pages of the TOC (usually pages 6–7; occasionally 4–5 for older issues — check by skimming the PDF).
- `issues/YYMM/*.html` — article files with placeholder `<!-- <meta name="64er.toc_category" content="XXX"> -->` lines.

**Output:**
- `issues/YYMM/toc.txt` — one category per line, in sort order.
- All HTMLs updated: placeholder comments replaced with `<meta name="64er.toc_category" content="…">`.

## What `toc.txt` is

The source of truth for **which category values are valid** and **in what order** they sort. The site generator (`generate.py:565`) reads this file and rejects any article whose `toc_category` is not listed:

```
ERROR: category not in toc.txt: 'Whatever' (Article Title)
```

**Format:** one category per line. Use `|` to express a sub-category under a parent. The order in the file defines the rendering/sort order on the issue page.

Example (`issues/8606/toc.txt`):
```
Aktuelles
Hardware-Test
Computerzubehör
Dateiverwaltung
Wettbewerbe|Anwendung des Monats
Wettbewerbe
Listings zum Abtippen|Anwendung des Monats
Listings zum Abtippen|Listings des Monats
Listings zum Abtippen|Anwendung
Listings zum Abtippen|Grafik
Listings zum Abtippen|Tips & Tricks zum C 64 für Einsteiger
Listings zum Abtippen|Tips & Tricks zum C 64 für Profis
…
Listings zum Abtippen
Software-Hilfe
64'er Extra
Kurse
Software-Test
Spiele-Test
Rubriken
```

Note the parent category (`Wettbewerbe`, `Listings zum Abtippen`) is listed AFTER its `|sub` lines — that's the sort position used for articles tagged with the bare parent (no sub-cat). Pick whichever ordering matches the printed magazine's flow.

## What `64er.toc_category` is

A per-article meta tag in each HTML `<head>`. Its content must exactly match a line in `toc.txt`, except for the editorial (see Rule 1).

```html
<meta name="64er.toc_category" content="Listings zum Abtippen|Tips & Tricks zum C 128">
```

The generator (`generate.py:561`) reads this to sort the article into the right section on the issue index page.

## Rules

1. **Editorial = empty.** The issue's editorial (usually on page 8, no category banner in the TOC but listed under `RUBRIKEN`) gets `content=""`. The generator sorts empty-category articles first (`category_index = -1`).

2. **Match the magazine's printed section banners.** The bold ALL-CAPS banners on the TOC pages (`AKTUELLES`, `HARDWARE-TEST`, `LISTINGS ZUM ABTIPPEN`, etc.) are the categories. Use the magazine's exact spelling and casing — convert ALL-CAPS to title case (`Aktuelles`, `Hardware-Test`) only because that's the project convention; see other issues' `toc.txt` for style.

3. **Sub-categories** are the smaller bold sub-headers under a parent banner (e.g. under `LISTINGS ZUM ABTIPPEN`: `Anwendung des Monats`, `Tips & Tricks zum C 128`). Encode as `Parent|Sub`. If a parent has no sub-headers in this issue, just use the parent.

4. **Articles spanning multiple sections.** Some articles are listed in two places in the TOC (e.g. an announcement under `Wettbewerbe` + the actual listing under `Listings zum Abtippen`). Assign **one** category, based on where the article's main content sits. The article's `64er.pages` meta hints — if pages match the listing section, use that.

5. **Articles not in the printed TOC.** Occasional small articles (game walkthroughs, fillers) are not in the TOC. Pick the closest topical category that *is* in `toc.txt`. Don't invent new categories. Don't leave `content=""` for non-editorials.

6. **Don't add a category to `toc.txt` that no article uses.** Lean: 12–22 lines is typical for an issue.

## Procedure

### 1. Read the TOC pages using three engines

Triangulate vision + pdftotext + tesseract — each gets some details wrong, three together get the structure right.

```bash
mkdir -p _toc
pdftotext -layout -f 6 -l 7 64er_*.pdf _toc/toc_pdftotext.txt
tesseract _work/p006/page_300.png _toc/toc_p6_tess -l deu 2>/dev/null
tesseract _work/p007/page_300.png _toc/toc_p7_tess -l deu 2>/dev/null
```

Then `Read` `_work/p006/page_300.png` and `_work/p007/page_300.png` directly (vision). For dense columns, `magick … -crop` a sub-rectangle and re-read.

The TOC is laid out in three or four columns per page. Identify:
- Each ALL-CAPS section banner (category)
- Each bold sub-header under a banner (sub-category)
- Each article entry (title + page number) — and which (sub-)category it sits under

### 2. Write `toc.txt`

List the categories in the order they appear when reading the TOC top-to-bottom, left-to-right across both pages. For each parent with sub-categories, list the `Parent|Sub` lines, then the bare `Parent` for any articles tagged with the parent alone.

### 3. Build the per-article mapping

For every `*.html` in the issue dir, decide which `toc.txt` line it maps to. The article filename starts with its page number, which matches the page numbers in the TOC. Cross-reference:

- TOC entry `Druckermöbel … 30` + file `30 Druckermöbel.html` → `Computerzubehör`
- TOC entry `Master-Text — Textverarbeitung hoch drei … 55` under `LISTINGS ZUM ABTIPPEN / Listings des Monats:` + file `55 Master-Text — Textverarbeitung hoch drei.html` → `Listings zum Abtippen|Listings des Monats`
- File `87 Die Lösung zu »The Institute«.html` — not in TOC, topically a game → `Spiele-Test`

### 4. Apply with a script, then delete the script

Write a one-shot Python script with an explicit `MAPPING = {filename: category}` dict. Include sanity checks:

- Every HTML in the dir is in `MAPPING` (no orphans).
- Every category value (except `""`) is a line in `toc.txt` (no typos that would crash `generate.py`).

```python
MAPPING = {
    "8 Aktuelles.html":              "Aktuelles",
    "8 Im neuen Gehäuse&hellip;.html": "",  # editorial
    "9 COMMODORE SCHLÄGT ZU.html":   "Aktuelles",
    # …
}

# sanity checks
files_on_disk = {f for f in os.listdir(".") if f.endswith(".html")}
assert files_on_disk == set(MAPPING), \
    f"missing={files_on_disk - set(MAPPING)} extra={set(MAPPING) - files_on_disk}"
with open("toc.txt", encoding="utf-8") as f:
    toc = {ln.strip() for ln in f if ln.strip()}
for v in set(MAPPING.values()) - {""}:
    assert v in toc, f"category not in toc.txt: {v!r}"

# replace placeholder
placeholder = re.compile(
    r'    <!-- <meta name="64er\.toc_category" content="XXX"> -->'
)
existing = re.compile(
    r'    <meta name="64er\.toc_category" content="[^"]*">'
)
for fn, cat in MAPPING.items():
    text = open(fn, encoding="utf-8").read()
    new_meta = f'    <meta name="64er.toc_category" content="{cat}">'
    if placeholder.search(text):
        text = placeholder.sub(new_meta, text, count=1)
    elif existing.search(text):
        text = existing.sub(new_meta, text, count=1)
    open(fn, "w", encoding="utf-8").write(text)
```

After it runs cleanly, delete the script — it's one-shot per issue.

### 5. Verify

```bash
# Every HTML has exactly one toc_category line
grep -c "toc_category" *.html | grep -v ":1$"   # should be empty

# Optional: run the generator against the issue to confirm no "category not in toc.txt" errors
python3 ../../generate.py --issues YYMM local
```

## Placement in HTML

The `toc_category` meta tag goes in `<head>`, immediately above `toc_title`:

```html
<meta name="64er.pages" content="55-60,62-66,68-69">
<meta name="64er.toc_category" content="Listings zum Abtippen|Listings des Monats">
<meta name="64er.toc_title" content="Listings des Monats: Professionelle Textverarbeitung">
<meta name="64er.id" content="master-text">
```

## What NOT to do

- Don't invent categories. Only use what appears in the printed TOC.
- Don't add `Parent|Sub` entries to `toc.txt` if no article maps to them.
- Don't leave the `<!-- … XXX -->` placeholder comment in any HTML.
- Don't set `content=""` for any article except the editorial.
- Don't reorder `toc.txt` after the fact without re-checking that the resulting issue index page still reads naturally.

Related: [`toc_title_workflow.md`](toc_title_workflow.md) for the `64er.toc_title` meta tag.
