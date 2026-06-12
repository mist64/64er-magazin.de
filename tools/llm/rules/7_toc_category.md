# 7 — Fill `64er.toc_category` in every article from a mapping

**Goal:** replace the placeholder line
`<!-- <meta name="64er.toc_category" content="XXX"> -->`
in each per-article HTML with a real
`<meta name="64er.toc_category" content="...">`, driven by an explicit
mapping you write by hand from the printed Table of Contents.

The script is reusable across issues. The mapping itself is one-shot per
issue — you build it from the printed TOC (see the previous step for the
`toc.txt` it must agree with) and feed it to this script.

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
