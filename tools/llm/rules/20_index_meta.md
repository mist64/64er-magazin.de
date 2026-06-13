# 20 — Fill `64er.index_category` / `64er.index_title` from the annual CSV

**Goal:** every article that appears in the year's
Jahresinhaltsverzeichnis (annual index) CSV gets its `index_category`
(and an `index_title` when the index title differs from the article's
`<title>`). These metas drive the generated "Artikel by topic" page
on the site.

## CSV source + format

The annual index CSVs live at the repo root:
- `Jahresinhaltsverzeichnis 1984-85.csv`
- `Jahresinhaltsverzeichnis 1985.csv`
- `Jahresinhaltsverzeichnis 1986.csv`

Each row: `YYMM,pages,category,subcategory,title`. Pages use em-dash
`—` as range separator. Category + subcategory become
`index_category` joined with `|`:

```
8605,18—24,Software-Grundlagen und Kurse,Grafik,Grafik und Computer-Animation
```
→ `<meta name="64er.index_category" content="Software-Grundlagen und Kurse|Grafik">`
+ `<meta name="64er.index_title" content="Grafik und Computer-Animation">`
(if the title differs from `<title>`).

## What the meta tags do

- `index_category` — drives the article's place on the site's
  generated "Artikel by topic" page. Format: `Category|Subcategory`.
  Category values must match a `TOPICS` list inside `generate.py`.
- `index_title` — title as it appears in the annual index, often
  with parenthetical clarifications like `(Teil 1)` or
  `(Farbdruckerübersicht)` not in the headline.

## Placement in HTML

The index metas go between `toc_title`/`toc_category` and `64er.id`:

```html
<meta name="64er.toc_category" content="Grafik">
<meta name="64er.toc_title" content="Hilfreiche Grundlagen: Grafik für Profis">
<meta name="64er.index_title" content="Grafik für Profis (Teil 1)">
<meta name="64er.index_category" content="Software-Grundlagen und Kurse|Grafik für Profis">
<meta name="64er.id" content="profi-grafik">
```

## Multi-entry articles

Some articles have multiple CSV rows (e.g. `Bücher` with one row per
book review, `Aktuelles` with one row per news item). Emit ALL
entries as consecutive `index_title`/`index_category` pairs in the
same article HTML.

## Apply script (optional but useful)

A mechanical apply script exists: `tools/llm/new/index_workflow_apply.py`.
It matches each CSV row to an HTML file by start page and inserts the
metas. The agent can run it then audit:

```bash
python3 tools/llm/new/index_workflow_apply.py <YYMM> \
  "Jahresinhaltsverzeichnis <YYYY>.csv"
```

## Briefing for the sub-agent

The sub-agent must:

1. Run the apply script (or do the matching manually if the script
   isn't available). Either way: each CSV row's `pages` first integer
   maps to an article whose `64er.pages` starts at that integer.
2. Review for:
   - `NO FILE` — CSV rows the script couldn't match. For each,
     find the article HTML manually (by start page, then by
     title fuzzy match) and apply via Edit.
   - Multi-entry articles (multiple CSV rows for the same start
     page) — verify each row produced its own `index_title` +
     `index_category` pair.
   - Ambiguous matches (multiple HTML files starting at the same
     page) — pick the right one by title comparison.
3. **If the applied `index_title` equals the article's `<title>`,
   REMOVE the `index_title` line** (keep `index_category` only).
   The generator falls back to `toc_title` then `<title>` for the
   index page; a duplicated `index_title` is noise.
4. **Spot-check the applied values for CSV typos** (stuttered
   words, misspelled program names, missing letters). Fix at the
   point of application — don't rewrite the source CSV.
5. Articles in the issue with NO CSV row stay unchanged: the
   recurring rubrics (Editorial, Leserforum, Fehlerteufelchen,
   Impressum, Vorschau), contest filler, call-for-entries, and
   any article the CSV legitimately omits.
6. Beautify touched files.
7. **Do not commit.** Return per-article action table + list of
   articles intentionally left empty + any manual fixups applied.

Critical guardrails:
- Don't invent CSV rows. If an article has no row, it gets no
  index meta. Period.
- A CSV row that doesn't match any article is the **CSV**'s
  problem (or a script-routing problem); fix the routing, do not
  invent an article file.
- The 8607 sweep caught a routing bug: CSV's "Die CP/M-Ecke (Teil
  2)" at p.96 went to `96 Neues vom Hypra-Basic.html` (page 96
  start) but the actual CP/M-Ecke article starts at p.95. Manually
  re-route via Edit.

## Verification

```bash
dir=issues/<YYMM>
csv="Jahresinhaltsverzeichnis <YYYY>.csv"

# 1. CSV row count vs applied index_category count
csv_rows=$(grep -c "^<YYMM>," "$csv" | tr -d ' ')
applied=$(grep -c '64er.index_category' "$dir"/*.html | \
          awk -F: '{s+=$2} END {print s}')
echo "  csv rows: $csv_rows  applied: $applied"
[ "$csv_rows" = "$applied" ] || \
  echo "  WARN: mismatch (expected csv_rows = applied unless skips/manual)"

# 2. articles without index_category — must all be recurring
#    rubrics or other legitimate omissions
for f in "$dir"/*.html; do
  grep -q 'index_category' "$f" || basename "$f"
done

# 3. no index_title equals <title> still present (would be
#    redundant — should have been removed)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    title_m = re.search(r'<title>([^<]+)</title>', s)
    if not title_m: continue
    title = title_m.group(1).strip()
    for m in re.finditer(r'<meta name="64er\.index_title" content="([^"]+)"', s):
        if m.group(1).strip() == title:
            print(f"  redundant index_title in {f}: {title!r}")
PY
)" "$dir"

# 4. index_category values look well-formed: "Category|Subcategory"
grep -hE '64er\.index_category" content=' "$dir"/*.html | \
  sed -E 's/.*content="([^"]*)".*/\1/' | grep -v '|' | head
# any line printed above is a bare category (no subcategory) — flag
# for manual check.
```

## Notes / lessons

- 8607 had exactly 38 CSV rows → 38 applied entries → 36 files
  (two files got two entries each: `8 Aktuelles` and `9 DFÜ-NEWS`).
  Multi-entry per article is normal; rubric-style pages aggregate
  several index items.
- The script's start-page heuristic can mis-route when an article
  spans page boundaries and another article starts on a later page
  in its range. Always review the apply.py report for cross-page
  collisions.
- CSV typos are common — fix them on application rather than
  modifying the source CSV (the CSV is shared across multiple
  issues' apply runs, and per-issue fixes are lower-risk than
  rewriting the CSV).
