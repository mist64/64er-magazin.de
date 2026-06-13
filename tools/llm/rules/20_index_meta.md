# 20 — Fill `64er.index_category` / `64er.index_title` from the annual CSV

**Goal:** every article that appears in the year's
Jahresinhaltsverzeichnis gets its `index_category` (and an
`index_title` when the index title differs from the article's
`<title>`). These metas drive the generated "Artikel by topic" page
on the site.

The full procedural spec is `tools/llm/new/index_workflow.md`. The
apply script `tools/llm/new/index_workflow_apply.py` does the
mechanical work. This rule is the dispatch + verification gate.

## Briefing for the sub-agent

The sub-agent must:

1. Run `python3 tools/llm/new/index_workflow_apply.py <YYMM>
   "Jahresinhaltsverzeichnis <YYYY>.csv"` from the repo root (or
   the equivalent invocation from the issue dir per the workflow).
2. Review the script's output for:
   - `NO FILE` — CSV rows the script couldn't match. For each,
     find the article HTML manually (by start page, then by
     title fuzzy match) and apply via Edit.
   - Multi-entry articles (multiple CSV rows for the same start
     page) — verify each row produced its own `index_title` +
     `index_category` pair.
   - Ambiguous matches (multiple HTML files starting at the same
     page) — pick the right one by title comparison.
3. Per workflow rule 1: if the applied `index_title` equals the
   article's `<title>`, REMOVE the `index_title` line (keep
   `index_category` only).
4. Per workflow rule 4: spot-check the applied values for CSV
   typos. Common patterns: stuttered words ("Hardware Hardware"),
   misspelled program names, missing letters. Fix at the point of
   application.
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
