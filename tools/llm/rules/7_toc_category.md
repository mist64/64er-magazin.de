# 7 — Fill `64er.toc_category` in every article from a mapping

**Goal:** replace the placeholder line
`<!-- <meta name="64er.toc_category" content="XXX"> -->`
in each per-article HTML with a real
`<meta name="64er.toc_category" content="...">`, driven by an explicit
mapping you write by hand from the printed Table of Contents.

The script is reusable across issues. The mapping itself is one-shot per
issue — you build it from the printed TOC (see the previous step for the
`toc.txt` it must agree with) and feed it to this script.

## Sibling meta: `64er.toc_title` (also filled from the printed TOC here)

Rule 5 (split) leaves a commented placeholder
`<!-- <meta name="64er.toc_title" content="XXX"> -->` in every article.
This meta carries **the article's wording as printed in the
Inhaltsverzeichnis (TOC)** — which is often richer than the article's
own `<h1>`/`<title>` (e.g. TOC `Die besten Spiele unter 15 Mark` vs
article `Billiges Vergnügen?`; TOC `Neue Serie: C 64 selbst repariert`
vs `Die Axt im Haus… (1)`). The site's issue page renders `toc_title`
when present, falling back to `toc_category` then `<title>`.

Because you are already reading the printed TOC page here to build the
`toc_category` mapping, capture the TOC wording in the same pass:

- For each article, set
  `<meta name="64er.toc_title" content="<verbatim TOC wording>">`,
  placed immediately **after** the `toc_category` line, **only when the
  TOC wording differs from the article's `<title>`**. If they are the
  same, DELETE the placeholder comment (don't ship a redundant
  toc_title, and don't leave the `XXX` comment — same rule as
  `index_title` in rule 20).
- Recurring rubrics whose TOC line is just the rubric name
  (Leserforum, Bücher, Vorschau, Fehlerteufelchen, Impressum, Editorial)
  get no `toc_title` — delete the placeholder.
- Verbatim from the TOC print (anti-memory): the TOC often abbreviates
  or expands differently than the headline; type what the TOC page
  shows, Title/natural-cased as the TOC prints it.

**Escaping & join conventions (keep consistent within an issue):**
- `toc_title` is an HTML attribute value — write `&` as `&amp;`
  (`Tips &amp; Tricks zu Superbase`), matching how `<title>`/filenames
  escape it. Don't ship a raw `&` in some files and `&amp;` in others.
- **Multi-line TOC entries** (the TOC wraps one entry across two printed
  lines, e.g. `Gesucht: Ihr Wunschdrucker / Tolle Preise zu gewinnen`,
  or `20 Drucker für Schulen zu gewinnen`) are **joined into one
  `toc_title`** — don't drop the second line.
- **Kicker + title** (print sets a bold kicker line above the title,
  e.g. `Anwendung des Monats:` over `Digi-Controller`): join into one
  `toc_title`. Two acceptable forms — a **colon join**
  (`Anwendung des Monats: Digi-Controller`) or 8607's **`<b>` markup**
  (`<b>Anwendung des Monats:</b> Digi-Controller`). Pick ONE and use it
  for every kicker entry in the issue; don't mix within an issue.

Verification: no `<!-- <meta name="64er.toc_title" content="XXX"> -->`
comment survives in any article, and every `toc_title` value is
non-empty and not equal to that file's `<title>`.
```bash
grep -l 'toc_title" content="XXX"' issues/<YYMM>/*.html   # expect: none
```
(8608 shipped 44 stale `toc_title` placeholders because no rule owned
this — that is the hole this section closes.)

## The mapping format

A TSV stream on stdin: one row per article file, two tab-separated
columns:

```
<filename>\t<category>
```

- `<filename>` — basename relative to the issue dir (e.g.
  `8 Aktuelles.html`, `9 DFÜ-NEWS_ DATEX-P-PARAMETER.html`).
- `<category>` — must exactly equal a non-comment, non-empty line in
  `<issue-dir>/toc.txt`, *or* be the empty string (the editorial uses
  `""`; the site generator sorts empty-category articles first).
- Sub-categories are pipe-separated (`Parent|Sub`).
- Blank lines and lines beginning with `#` in the mapping are ignored,
  so you can group/document the mapping inline.

## What the script does

1. Reads the mapping from stdin into a `{filename: category}` dict.
2. **Validates**:
   - every `*.html` in `<issue-dir>` is in the mapping (no orphans),
   - every filename in the mapping exists on disk,
   - every non-empty category appears as a line in
     `<issue-dir>/toc.txt`.
3. For each article file, replaces the **placeholder** comment
   `    <!-- <meta name="64er.toc_category" content="XXX"> -->`
   (or an existing `<meta name="64er.toc_category" content="…">` line,
   so re-runs are safe) with
   `    <meta name="64er.toc_category" content="<category>">`.
4. `git add`s each rewritten file.

If any validation fails, the script exits non-zero **before touching any
file**, so the issue dir stays in a consistent state.

## Usage

```bash
tools/llm/rules/7_toc_category.sh issues/8607 <<'TSV'
# editorial gets ""
8 Fachredakteur_ Hobby und Beruf&hellip;.html	

# Aktuelles
8 Aktuelles.html	Aktuelles
9 DFÜ-NEWS_ DATEX-P-PARAMETER.html	Aktuelles

# Forschung und Technik
16 DER C 64 IN FORSCHUNG UND TECHNIK.html	Forschung und Technik
…
TSV
```

(Comments and blanks are ignored; tabs separate filename from category.)

For an alternative invocation pattern, write the mapping to
`issues/<YYMM>/toc_category_mapping.tsv` and run:

```bash
tools/llm/rules/7_toc_category.sh issues/<YYMM> < issues/<YYMM>/toc_category_mapping.tsv
```

## Verification

After running, every article should have exactly one `64er.toc_category`
line and no remaining placeholder comment:

```bash
# placeholder gone
grep -lE '<!-- <meta name="64er\.toc_category" content="XXX"> -->' issues/<YYMM>/*.html
# expect: no output

# every file has exactly one toc_category line
for f in issues/<YYMM>/*.html; do
  n=$(grep -c '<meta name="64er\.toc_category"' "$f")
  [ "$n" -eq 1 ] || echo "$f: $n"
done

# every category value appears in toc.txt
python3 - <<'PY'
import glob, re
issue = '<YYMM>'
toc = {ln.strip() for ln in open(f'issues/{issue}/toc.txt') if ln.strip()}
for f in glob.glob(f'issues/{issue}/*.html'):
    m = re.search(r'<meta name="64er\.toc_category" content="([^"]*)"', open(f).read())
    if not m: continue
    cat = m.group(1)
    if cat and cat not in toc:
        print(f"{f}: category {cat!r} not in toc.txt")
PY
```

## Lessons / things to watch

- The mapping is **the** editorial step — the script just applies it.
  Build the mapping from the printed TOC, walking each `(filename →
  page → TOC entry → category)` chain by hand.
- Editorial = `""`. The generator treats an empty value as "category
  index −1" and sorts it before everything else, which is what the
  magazine's editorial slot expects.
- Articles **listed twice** in the printed TOC (e.g. an "Anwendung des
  Monats" announcement under Wettbewerbe + the actual listing under
  Listings zum Abtippen) get **one** category. Pick the one whose
  pages match the article's `<meta name="64er.pages">` content.
- Articles **not in the printed TOC** (small fillers, walkthroughs)
  get the closest topical category that's already in `toc.txt`. Don't
  invent new categories — extend `toc.txt` first if you really need one.
- Once this step is done, prune any line in `toc.txt` that no article
  ended up using — the generator doesn't care about unused lines, but
  the file is documentation; keep it tight.
