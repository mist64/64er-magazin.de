# 220 — Fill `64er.index_category` / `64er.index_title` from the annual CSV

**Applies to:** all — RE-CLASSIFIED 2026-10-03. A monthly takes the annual `Jahresinhaltsverzeichnis <YYYY>.csv`; a **Sonderheft takes `Gesamtinhaltsverzeichnis Sonderhefte.csv`**, a separate file at the repo root with a different layout. The old classification was `monthly`, on the true but incomplete evidence that no Sonderheft appears in the ANNUAL CSVs — which ruled out one file, not the input.

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

Every row is keyed by a **monthly** `YYMM`. There is no Sonderheft row in any of
the three:

```bash
cut -d, -f1 Jahresinhaltsverzeichnis*.csv | sort -u | grep -c SH   # → 0
```

That shows only that the ANNUAL CSVs hold no Sonderheft. **A Sonderheft's
index lives in its own file**, and this rule runs for both kinds.

### A Sonderheft's source: `Gesamtinhaltsverzeichnis Sonderhefte.csv`

Different file, different layout, different issue key. There is no header row.

| col | holds | example |
|---|---|---|
| 0 | category | `Software-Grundlagen` |
| 1 | subcategory | `Basic-Optimierung` |
| 2 | title | `So macht man Programme schneller` |
| 3 | **the issue, as `N/YY`** | `2/86` for `SH8602` |
| 4 | page (a single page, not a range) | `44` |
| 5-6 | empty | |

So the key is **`N/YY` in column 3**, not `SH86NN` and not column 0. Map it
from the directory name: `SH8602` → `2/86`. MEASURED: the file covers every
Sonderheft, `1/85`-`8/85` and `1/86`-`8/86` (SH8602 → 36 rows, pages 9-161;
SH8601 → 27 rows).

The category/subcategory pair is written as `category|subcategory`, which is
the form `SH8501` already carries.

**`SH8501` is NOT a mis-route — it is the one Sonderheft done correctly.** Its
27 `index_category` values read `Listings zum Abtippen|Assembler`,
`…|Basic-Erweiterung`, `…|Floppy` and so on, which match this file's `1/85`
rows. The monthly `8501` rows carry entirely different categories
(Abenteuerlösungen, Aktuell, Hardware-Tests), so they cannot be the source.
An earlier note here had it backwards and told the builder to write nothing.

**Consequence, recorded:** `SH8601` shipped with **0** `index_category` across
its 29 articles because this rule was skipped as `not applicable — kind`.
Published; not fixed retroactively (owner, 2026-10-03). Do not repeat it.

**The apply script HAS a Sonderheft reader** — `parse_sonderheft_csv` in
`r220_index_meta_apply.py`, which keys on **column 3**, exactly as stated
above and as the function's own docstring says. (This paragraph said column 4,
which is the PAGE; and it used to say the script "reads only the monthly
layout … write one as part of this step", so SH8603 set out to write a parser
that already existed. **Nothing is to be written here.**) The monthly path is
`line.startswith(f"{code},")` with `parts[1]` pages / `parts[2]` category /
`parts[4]` title.

**Every cell is `.strip()`ed before it is compared or written.** The file has
trailing empty fields and inconsistent spacing around the key, and an
unstripped `" 4/86"` matches nothing while reporting zero rows as a pass.

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
  Category values are **not** constrained by the `TOPICS` list inside
  `generate.py`. This line used to say they "must match" it; `TOPICS` is a
  GROUPING list for the topic index pages, mapping a label to a set of
  `Category|Subcategory|` prefixes, and a value outside every prefix is
  applied normally and simply does not appear under a labelled topic.
  MEASURED, distinct values matching no prefix: **SH8603 19 of 42 metas,
  SH8602 15 of 35, 8612 30 of 55, 8611 32 of 49.** So this was false for the
  monthlies too, not only for the Sonderhefte — a build that believed it
  would have "corrected" two thirds of a correct CSV.
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

A mechanical apply script exists: `r220_index_meta_apply.py` (beside this file).
It matches each CSV row to an HTML file by start page and inserts the
metas. The agent can run it then audit:

Run it from the issue directory, which is what the script's own paths assume —
its CSV argument is relative to that cwd, and so is the Verification block below:

```bash
# ONE cwd for this rule: the REPO ROOT. The apply script globs *.html, so it
# is invoked with the issue directory as cwd via a subshell -- but every path
# in this file, and every Verification snippet, is relative to the repo root.
# The rule used to say "run from the issue directory" while its Verification
# used repo-root paths.
cd /Users/mist/Documents/git/64er-magazin.de
# $PY, not bare python3 (r000).  And from the repo root the CSV is NOT ../../ :
( cd issues/$ISSUE && $PY ../../tools/img/scan2ocr/rules/r220_index_meta_apply.py \
    "$ISSUE" "../../Jahresinhaltsverzeichnis <YYYY>.csv" )
# ...or, for a Sonderheft, the OTHER file:
( cd issues/$ISSUE && $PY ../../tools/img/scan2ocr/rules/r220_index_meta_apply.py \
    "$ISSUE" "../../Gesamtinhaltsverzeichnis Sonderhefte.csv" )
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

   **A mismatch with the article's headline / TOC is NOT a CSV typo.**
   `index_title` is *sourced from this CSV verbatim* and is *expected*
   to differ from the article's `<h1>`/TOC wording — that is the whole
   reason the field exists (the annual index re-titles articles for a
   cumulative context). Do **not** "correct" a CSV value to match the
   in-issue print. Only fix garble that is wrong *inside the CSV itself*
   (a stutter like `Farbbdrucker`, a dropped letter, an OCR artifact in
   the CSV file); a plausible German phrase that simply doesn't match
   the headline is the index's deliberate wording — keep it verbatim.
   Regression this guards against: 8608/142 `Small C: Drei C-Compiler
   für Systemprogrammierer` was "fixed" to `Der C-Compiler` because the
   article headline reads "der C-Compiler" — but the CSV row genuinely
   says `Drei`, and the headline is not evidence the CSV is wrong. When
   unsure, the CSV wins; see r000 "OCR cleanup granularity" for the mirror
   principle on body text.
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

## Check the ROUTING, not only the count

`check 1` compares CSV rows against rows applied. **A misroute passes it** —
the row landed, just in the wrong article. The old apply script picked the
first filename in LEXICAL order whose page range contained the row's page,
which put four of 8611's 49 rows in the wrong article. It now takes the
**nearest preceding start page**, and that same rule is the check:

```bash
# For a Sonderheft, pass the Sonderheft CSV; the script picks the columns from
# the id it is given.  An empty row set is now reported, not passed.
$PY - issues/<ID> "Jahresinhaltsverzeichnis <YYYY>.csv" <ID> <<'PYEOF'
#   ... or, for a Sonderheft:
# $PY - issues/SH8603 "Gesamtinhaltsverzeichnis Sonderhefte.csv" SH8603 <<'PYEOF'
import csv, glob, io, os, re, sys
# THE ROUTING RULE IS THE CHECK. A row (page, title) belongs to the article
# whose start page is the NEAREST PRECEDING one. So for every applied row,
# verify no OTHER article starts strictly between its article's start and the
# row's own page. This needs the CSV, because the page is the row's, not the
# article's -- an article's mere overlap with another is normal (interleaved
# listing runs) and says nothing.
d, csv_path, code = sys.argv[1], sys.argv[2], sys.argv[3]
# A SONDERHEFT KEYS ITS ROWS IN A DIFFERENT COLUMN OF A DIFFERENT FILE, so this
# filter found 0 rows for one and reported "0 of 0 ... past a nearer article"
# as a pass -- vacuous on SH8601, SH8602 and SH8603 alike.
#   monthly    col 0 = "8612", col 1 = page, col 4 = title
#   Sonderheft col 3 = "3/86", col 4 = page, col 2 = title
SH = code.startswith('SH')
if SH:
    key = '%d/%s' % (int(code[4:6]), code[2:4])      # SH8603 -> 3/86, UNPADDED
    PAGE, TITLE, KEYCOL = 4, 2, 3
else:
    key, PAGE, TITLE, KEYCOL = code, 1, 4, 0
rows = []
for line in io.open(csv_path, encoding='utf-8'):
    p = next(csv.reader([line]))
    # PARSE THE FIRST INTEGER BEFORE THE DASH. `p[1].isdigit()` is False for
    # every range row ("172—173"), so this check silently examined 26 of
    # 8612's 55 rows and a planted range-row misroute passed.
    if len(p) > max(PAGE, TITLE, KEYCOL) and p[KEYCOL].strip() == key:
        mm = re.match(r'\s*(\d+)', p[PAGE])
        if mm:
            rows.append((int(mm.group(1)), p[TITLE]))
if not rows:
    print('  NO ROWS for %s in %s -- wrong CSV or wrong key, not a pass'
          % (key, os.path.basename(csv_path)))
starts, spans, titles, LETTERED = {}, {}, {}, {}
for f in sorted(glob.glob(os.path.join(d, '*.html'))):
    s = io.open(f, encoding='utf-8').read()
    m = re.search(r'64er\.pages" content="([^"]+)"', s)
    if not m: continue
    segs = []
    # PARSE THE LEADING INTEGER, here too.  `lo.isdigit()` is False for a
    # LETTERED page ('21a', '77b'), which r080 requires when two articles start
    # on one page -- so such an article produced no segs, fell out through the
    # `continue` below, and was INVISIBLE to this check: a row on p21 could
    # neither be routed to it nor see it as a nearer article.
    lettered = set()
    for seg in m.group(1).split(','):
        lo, _, hi = seg.strip().partition('-')
        ml = re.match(r'\s*(\d+)([a-z]?)', lo)
        mh = re.match(r'\s*(\d+)', hi) if hi else None
        if ml:
            segs.append((int(ml.group(1)),
                         int(mh.group(1)) if mh else int(ml.group(1))))
            if ml.group(2): lettered.add(int(ml.group(1)))
    if not segs: continue
    if lettered: LETTERED.setdefault(min(lettered), []).append(f)
    starts[f] = segs[0][0]
    spans[f] = segs
    for t in re.findall(r'64er\.index_title" content="([^"]*)"', s):
        titles.setdefault(t, []).append(f)
    tm = re.search(r'<title>(.*?)</title>', s)
    if tm: titles.setdefault(tm.group(1), []).append(f)
bad = 0
orphans = []
for page, title in rows:
    fs = titles.get(title) or titles.get(title.replace('&', '&amp;'))
    # A ROW WHOSE TITLE IS IN NO ARTICLE OF THIS ISSUE WAS SKIPPED, AND THAT
    # IS HOW A FOREIGN ROW GETS IN.  The CSV is hand-kept and a row can carry
    # the wrong issue key: "Sprite+Grafik-Basic,4/86,42" is SH8504's article
    # (4/85, also p42), so the apply script's nearest-preceding-start
    # fallback put it into SH8604's 40 Kuenstliche Intelligenz, printed OK,
    # and BOTH gates agreed -- this check said 0 of 17 and the count said
    # 17 = 17.  Only deleting the row by hand made the count disagree.
    if not fs:
        orphans.append((page, title))
        continue
    f = fs[0]
    # A row whose title IS the article's own title was routed by title, not by
    # page, and the title is the stronger evidence. 8610's "Mini-Hardcopy für
    # MPS 801" (row p96, article starts p95) is exactly this.
    own = re.search(r'<title>(.*?)</title>',
                    io.open(f, encoding='utf-8').read())
    if own and own.group(1).replace('&amp;', '&') == title:
        continue
    # and the nearer article must actually COVER the row's page -- a one-page
    # item that merely starts closer cannot own it. 8607's "9 DFÜ-News" looked
    # like a misroute for 8 Aktuelles' p11 rows until this was added.
    # AND A ROW ROUTED FORWARD IS A MISROUTE TOO.  The test below looks for
    # an article starting BETWEEN this one's start and the row's page, which
    # finds nothing at all when the article starts AFTER the page -- a planted
    # forward move was silent.  An article cannot own a page before it begins.
    if starts[f] > page:
        print(f"  MISROUTE  p{page} {title[:34]:<36} -> "
              f"{os.path.basename(f)[:30]}  (which starts at p{starts[f]})")
        bad += 1
        continue
    closer = [g for g, st in starts.items()
              if starts[f] < st <= page and g != f
              and any(lo <= page <= hi for lo, hi in spans[g])]
    if closer:
        best = max(closer, key=lambda g: starts[g])
        print(f"  MISROUTE  p{page} {title[:34]:<36} -> {os.path.basename(f)[:30]}"
              f"  (p{starts[best]} {os.path.basename(best)[:26]} starts closer)")
        bad += 1
print(f"{bad} of {len(rows)} rows routed past a nearer article")
# AS A DELTA.  A row whose title merely READS differently from the article's
# heading is a legitimate permanent entry, so this is an open list the
# operator walks item by item, not a gate.  MEASURED: SH8602 and SH8603 have
# 0, SH8604 has the 1 real foreign row, the monthlies 8609/8610 have 1 each
# and 8612 has 3 -- all title wordings.  (SH8601 has 22 because it shipped
# with no index metadata at all; see the top of this rule.)
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
items = ['p%d %s' % (pg, t) for pg, t in orphans]
new = R.delta(d, 'r220-orphan-rows', items)
if R.report('rows matching no article', new, len(items), d, 'r220-orphan-rows'):
    print('    -- for each: grep -ril <distinctive word> issues/  '
          'A row found in ANOTHER issue carries the wrong issue key and is')
    print('       that issue\'s row; report it, do not apply it here.')
# LETTERED SIBLINGS CANNOT BE SEPARATED BY PAGE, because they share one.  The
# nearest-preceding-start rule is silent between 21a and 21b, so say so and
# name them: those rows are routed by TITLE and have to be read.
for pg, fs in sorted(LETTERED.items()):
    if len(fs) > 1:
        print(f"  BY TITLE  p{pg} has {len(fs)} lettered articles; page routing "
              f"cannot choose between them -- check each row's title:")
        for f in sorted(fs):
            print(f"              {os.path.basename(f)}")
PYEOF
```

A normal run is **silent**. MEASURED over 8604-8611: 0 hits on seven issues,
1 on 8607 — the CP/M-Ecke, where the row title differs from the article's only
by `(Teil 2)`, which is a real routing question. A flood means the check broke,
not the issue.

Do not replace this with a content check: matching index-title words against
the article's headings misses *24-Nadel-Drucker* in *Epson und der
Druckermarkt*, because "drucker" matches "Druckermarkt".

## Verification

```bash
dir=issues/<YYMM>
csv="Jahresinhaltsverzeichnis <YYYY>.csv"    # replaced below for a Sonderheft

# 1. CSV row count vs applied index_category count.
#
# THE SONDERHEFT CSV IS A DIFFERENT SHAPE AND A DIFFERENT FILE.  The monthly
# Jahresinhaltsverzeichnis keys the issue in COLUMN 1 ("8612,..."); the
# Gesamtinhaltsverzeichnis Sonderhefte keys it in COLUMN 4, unpadded and with
# a slash ("Buchbesprechungen,C16/VC20,Bücher zum C16 und VC20,3/86,52").  So
# `grep -c "^SH8603,"` finds 0 rows, 0 == 0 is reported as a PASS, and the
# routing check below filters on the monthly columns and passes too.  Both
# were vacuous on SH8601, SH8602 and SH8603.
if [ "${ISSUE#SH}" != "$ISSUE" ]; then
  csv="Gesamtinhaltsverzeichnis Sonderhefte.csv"
  YY=${ISSUE:2:2}; MM=${ISSUE:4:2}
  key="$((10#$MM))/$YY"                  # SH8603 -> 3/86, UNPADDED
  csv_rows=$($PY - "$csv" "$key" <<'PYEOF'
import csv, io, sys
rows = [r for r in csv.reader(io.open(sys.argv[1], encoding='utf-8'))
         if len(r) > 3 and r[3].strip() == sys.argv[2]]
print(len(rows))
PYEOF
)
else
  csv_rows=$(grep -c "^$ISSUE," "$csv" | tr -d ' ')
fi
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

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every `index_category` / `index_title` the sub-agent
writes must be backed by **runnable verifier evidence pasted verbatim
into the report**:

- For each FILLED meta pair, paste the CSV row it came from, verbatim,
  e.g.
  ```
  8605,18—24,Software-Grundlagen und Kurse,Grafik,Grafik und Computer-Animation
  → file: 18 Grafik und Computer-Animation.html
  → index_category="Software-Grundlagen und Kurse|Grafik"
  → index_title="Grafik und Computer-Animation"
  ```
- For each manually-routed CSV row (apply.py emitted `NO FILE`),
  paste the CSV row + the file the orchestrator picked + a one-line
  reason (`p.96 start but actual article begins p.95`).
- For each REMOVED `index_title` (because it equalled `<title>`),
  paste the `<title>` line so the orchestrator can confirm the
  duplication.
- For each CSV typo fixed at application time, paste the verbatim
  CSV cell and the corrected value, plus one line of justification
  from the article body.

**No verifier output, no claimed meta action.** An index meta reported
without the CSV-row evidence is treated as a guess; the orchestrator
will re-dispatch. "Trust me, I matched the CSV" is never acceptable —
mis-routing is a known failure mode (the 8607 CP/M-Ecke case).

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
