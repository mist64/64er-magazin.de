# 5 — Split the consolidated `.html` into one file per article

**Goal:** turn the single `issues/8607/8607.html` into one HTML file per
article (e.g. `issues/8607/8 Aktuelles.html`, `issues/8607/19 Der Neue.html`,
…) with the per-article `<head>` template, derived metadata, and authors
collected from `(byline)` paragraphs.

## What the script does

For every `<h1>` block (each `<h1>` text ends with `[page-numbers]`):

- **filename** = `<first-page> <h1-without-page-numbers>.html`
- **`<title>`** = the cleaned `<h1>` text
- **`64er.pages` meta** = the bracketed page numbers
- **`64er.issue` meta** = the issue id passed in (or auto-derived from the
  directory name; e.g. `issues/8607/` → `7/86`)
- **bylines** `<p>(name1/name2)</p>` → `<address class="author">(name1/name2)</address>`
  AND collected into `<meta name="author" content="name1, name2, …">`
- **`64er.id` meta** = a unique placeholder `XXX<N>` per article, where `<N>`
  starts at `0` and increments in the order the `<h1>` sections are walked
  (first article → `XXX0`, second → `XXX1`, …). The sequence resets per
  issue. This guarantees the build doesn't choke on duplicate `64er.id`
  values and gives the meta-fill step a stable per-article handle.
- each per-article file is beautified with **js-beautify** (same engine
  Nova's `nova-beautify` extension uses), 4-space indent, no line wrapping
  — so `<article>` children land at 8 spaces, `<ul>`/`<ol>` children at
  12, `<br>`-continuation lines at +4 from their opener, and inline
  elements (e.g. `<address class="author">(xy)</address>`) stay on a
  single line. Requires Node/npm available on `PATH`; on first run `npx`
  fetches `js-beautify` from the network.
- a small text cleanup pass (idempotent with step 4 because the same
  substitutions are applied):
  - `<blockquote><p>` → `<p class="intro">`
  - `</blockquote>` → *(removed)*
  - `<br/>` → `<br>`
  - `&lsquo;`, `&rsquo;` → `'`; `&ldquo;`, `&rdquo;` → `"`; `''` → `"`
- strips any `id=` attribute that snuck in (Discount doesn't emit them, but
  this is defensive).

The script is adapted from `tools/split.py`. The original still works on
its own; this copy is the canonical version for the rules pipeline.

## Usage

```bash
# auto-derive 64er.issue from the dir name (8607 -> 7/86):
tools/llm/rules/5_split.sh issues/8607/8607.html

# explicit (needed for Sonderhefte / unusual paths):
tools/llm/rules/5_split.sh issues/SH8607/SH8607.html 'Sonderheft 7/86'
```

After the script:
- the consolidated `issues/8607/8607.html` is `git rm`'d
- the per-article `*.html` files are `git add`'d

## Verification

```bash
# 1. how many articles came out
ls issues/8607/*.html | wc -l                          # expect dozens

# 2. each file's <h1> matches its filename (modulo sanitisation)
for f in issues/8607/*.html; do
  base=$(basename "$f" .html | sed -E 's/^[0-9]+ //')
  h1=$(grep -oE '<h1>[^<]+</h1>' "$f" | head -1 | sed -E 's#</?h1>##g')
  [ "$base" = "$h1" ] || echo "MISMATCH: $f  (file:'$base'  h1:'$h1')"
done

# 3. no stray <h1> in the body (each file should have exactly one)
for f in issues/8607/*.html; do
  n=$(grep -c '<h1>' "$f"); [ "$n" -eq 1 ] || echo "n=$n  $f"
done

# 4. every <meta name="64er.pages"> looks like a page spec
grep -h '64er.pages" content=' issues/8607/*.html | grep -vE 'content="[0-9,\- ]+"'

# 5. consolidated file is gone
[ ! -f issues/8607/8607.html ] && echo "consolidated removed ✓"
```

## Notes / lessons

- split.py's text replacements overlap with `4_html_cleanup.sh`. That's
  intentional — running 4 first means the .html is already clean when split
  starts, and split's own replacements become no-ops. Either order is safe.
- Bylines must look like `<p>(Author Name)</p>` or `<p>(Name1/Name2)</p>`
  on their own paragraph. Bylines embedded mid-sentence won't be picked up.
- The `[pages]` spec on `<h1>` is the only way the script learns the
  article's page range — make sure every `<h1>` in the OCR `.md` ends
  with `[N]` or `[N-M]` or `[N,M-O]`.
