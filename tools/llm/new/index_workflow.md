# Index Category/Title Workflow

How to fill `64er.index_category` and `64er.index_title` for each article HTML from the Jahresinhaltsverzeichnis (annual index) CSV.

## Source

The annual index CSVs are at the repo root:

- `Jahresinhaltsverzeichnis 1984-85.csv`
- `Jahresinhaltsverzeichnis 1985.csv`
- `Jahresinhaltsverzeichnis 1986.csv`

### CSV format

```
YYMM,pages,category,subcategory,title
```

Example:
```
8605,18—24,Software-Grundlagen und Kurse,Grafik,Grafik und Computer-Animation
8605,24—27,Hardware-Test,Drucker,Die Regenbogendrucker (Farbdruckerübersicht)
8605,107,Buchbesprechungen,C 128,C 128 — Das große Grafik-Buch
```

- **Pages** use em-dash `—` as range separator
- **Category** and **subcategory** become `64er.index_category` joined with `|`: `Software-Grundlagen und Kurse|Grafik`
- **Title** becomes `64er.index_title` (if different from `<title>`)

## What the meta tags do

- `64er.index_category` — determines where the article appears in the generated "Artikel" (articles-by-topic) page. Format: `Category|Subcategory`. The category values must match the `TOPICS` list in `generate.py`.
- `64er.index_title` — the title as it appears in the annual index, often with parenthetical clarifications like `(Farbdruckerübersicht)` or `(Teil 1)` that aren't in the article headline.

## Rules

1. **Omit `index_title` when it equals `<title>`.** The generator falls back to `toc_title`, then `<title>`.

2. **Multiple entries per article.** Some articles have multiple CSV rows (e.g. Bücher with one row per book review, Tips & Tricks with one row per tip). Add **all** entries as consecutive `index_title`/`index_category` pairs:
   ```html
   <meta name="64er.index_title" content="C 128 — Das große Grafik-Buch">
   <meta name="64er.index_category" content="Buchbesprechungen|C 128">
   <meta name="64er.index_title" content="C 64: Wunderland der Grafik">
   <meta name="64er.index_category" content="Buchbesprechungen|Grafik">
   ```

3. **Articles without CSV entries stay empty.** Do not invent index entries. If an article has no row in the CSV, it gets no `index_category`/`index_title`. This is normal for rubrics (Editorial, Leserforum, Fehlerteufelchen, Impressum, Vorschau) and sometimes for content articles that were omitted from the annual index.

4. **CSV typos.** The CSV may have errors (e.g. "Basic Basic-Programme" with a stutter). Fix obvious typos when applying — or remove the `index_title` if the corrected version matches `<title>`.

5. **Placement in HTML.** The index meta tags go between `toc_title`/`toc_category` and `64er.id`:
   ```html
   <meta name="64er.toc_category" content="Grafik">
   <meta name="64er.toc_title" content="Hilfreiche Grundlagen: Grafik für Profis">
   <meta name="64er.index_title" content="Grafik für Profis (Teil 1)">
   <meta name="64er.index_category" content="Software-Grundlagen und Kurse|Grafik für Profis">
   <meta name="64er.id" content="profi-grafik">
   ```

## Procedure

1. Run the extraction script (`index_workflow_apply.py`, in the same directory as this file):
   ```bash
   cd issues/YYMM
   python3 ../../tools/llm/new/index_workflow_apply.py YYMM "../../Jahresinhaltsverzeichnis YYYY.csv"
   ```
   The script:
   - Reads the CSV for the target issue
   - Matches each row to an HTML file by start page
   - Inserts `index_category` and (if different from `<title>`) `index_title` meta tags
2. Review the output for:
   - "NO FILE" — CSV entries that couldn't be matched to any HTML
   - Ambiguous matches — verify the right file was chosen
   - Multiple-entry articles — verify all entries are present
3. Check which articles have no `index_category` — decide if they're rubrics (skip) or missing from the CSV (add manually)
4. Fix any CSV typos in the applied `index_title` values

## Verification

```bash
# Count articles with index entries
grep -c 'index_category' *.html | grep -v ":0$" | wc -l

# List articles WITHOUT index entries (rubrics or missing)
for f in *.html; do
  grep -q 'index_category' "$f" || echo "$f"
done

# Check for duplicated/malformed entries
grep -n 'index_' *.html | sort
```
