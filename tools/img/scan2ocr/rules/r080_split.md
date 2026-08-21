# 080 — Split the consolidated `.html` into one file per article

**Applies to:** all — one file per `<h1>` in any issue. The *Listing/Anwendung des Monats* case is the monthlies' commonest instance of the paired-article rule, not the rule itself — a Sonderheft's multi-part features (`SH8506` HI-EDDI, Hypra-Load/Hypra-Save) are the same shape.

**Goal:** turn the single `issues/8607/8607.html` into one HTML file per
article (e.g. `issues/8607/8 Aktuelles.html`, `issues/8607/19 Der Neue.html`,
…) with the per-article `<head>` template, derived metadata, and authors
collected from `(byline)` paragraphs.

## What the script does

For every `<h1>` block (each `<h1>` text ends with `[page-numbers]`):

- **filename** = `<first-page> <h1-without-page-numbers>.html`. The
  filename derives from the **escaped HTML text** of the `<h1>` (the
  raw markup, not the rendered text), so an entity like `&amp;`
  appears **literally** in the filename (e.g. a file named
  `… Tips &amp; Tricks.html`, not `… Tips & Tricks.html`).
  Filesystem-illegal chars `? / :` are sanitised to `_`.
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
- a small text cleanup pass (idempotent with step 070 because the same
  substitutions are applied):
  - `<blockquote><p>` → `<p class="intro">`
  - `</blockquote>` → *(removed)*
  - `<br/>` → `<br>`
  - `&lsquo;`, `&rsquo;` → `'`; `&ldquo;`, `&rdquo;` → `"`; `''` → `"`
- strips any `id=` attribute that snuck in (Discount doesn't emit them, but
  this is defensive).

The splitter is adapted from `tools/split.py` and **embedded inline in
`r080_split.sh`** -- there is no `split.py` in this directory. The original
still works standalone; the embedded copy is canonical for this chain.

## Usage

```bash
# auto-derive 64er.issue from the dir name (8607 -> 7/86):
tools/img/scan2ocr/rules/r080_split.sh issues/8607/8607.html

# explicit (needed for Sonderhefte / unusual paths):
tools/img/scan2ocr/rules/r080_split.sh issues/SH8607/SH8607.html 'Sonderheft 7/86'
```

After the script:
- the consolidated `issues/8607/8607.html` is `git rm`'d
- the per-article `*.html` files are `git add`'d

## Verification

```bash
# 1. how many articles came out
ls issues/8607/*.html | wc -l                          # expect dozens

# 2. each file's <h1> matches its filename (modulo sanitisation).
#    split sanitises the filesystem-illegal chars `? / :` → `_`, so
#    apply the SAME substitution to the h1 before comparing — else a
#    file `146 Billiges Vergnügen_.html` vs h1 `Billiges Vergnügen?`
#    false-MISMATCHes.
for f in issues/8607/*.html; do
  base=$(basename "$f" .html | sed -E 's/^[0-9]+ //')
  h1=$(grep -oE '<h1>[^<]+</h1>' "$f" | head -1 | sed -E 's#</?h1>##g' | tr '?/:' '_')
  [ "$base" = "$h1" ] || echo "MISMATCH: $f  (file:'$base'  h1:'$h1')"
done

# 3. no stray <h1> in the body (each file should have exactly one).
#    DOCUMENTED EXCEPTION: Leserforum legitimately has ZERO <h1> —
#    rule 200 restructures it with a <header> banner instead of an
#    <h1>. Expect n=0 for the Leserforum file; that's not a failure.
for f in issues/8607/*.html; do
  n=$(grep -c '<h1>' "$f"); [ "$n" -eq 1 ] || echo "n=$n  $f"
done

# 4. every <meta name="64er.pages"> looks like a page spec
grep -h '64er.pages" content=' issues/8607/*.html | grep -vE 'content="[0-9,\- ]+"'

# 5. consolidated file is gone
[ ! -f issues/8607/8607.html ] && echo "consolidated removed ✓"
```

## Paired articles — never split

64'er occasionally runs **two pieces on the same topic in one issue** on
non-adjacent pages — typically a long technical deep-dive and a short
consumer-facing overview / *Anwendung des Monats* blurb. Print gives
each piece its own h1-style banner and its own intro paragraph, so they
*look* like two separate articles. Editorially they are one. Project
policy is to **merge them into a single `.html` file**: one `<article>`,
one `<h1>`, both intros and both bodies preserved in print order.

If the consolidated `.md` already has the two pieces collapsed into one
`<h1>`-rooted section (the only correct upstream state), the splitter
will Do The Right Thing automatically — there's only one `<h1>`, so
only one file comes out. The trap is: **do not "fix" such a section by
re-introducing a second `<h1>` because the printed page has a second
banner.** The visual banner is per-print-piece; the editorial unit is
per-product / per-topic.

### Signals that two banners belong to one article

Any **one** of these is sufficient to treat the pair as a single article:

**»Listing des Monats« and »Anwendung des Monats« are ALWAYS this case.**
The magazine prints the overview blurb and the listing/description apart, on
non-adjacent pages, essentially every issue. **We always combine them into one
article.** Do not treat the split as editorial intent and do not wait for the
other signals to confirm it — if `head1` reads *Listing des Monats* or
*Anwendung des Monats* on two pieces about the same program, they are one
article. The `Jahresinhaltsverzeichnis` agrees: it carries a single row with a
page range spanning both (`8609,48—56` for Bar-Codes, `8609,46—54` for the
1570/71 FSD-System). A tell that the split slipped through: only the first
piece carries `index_category`, and the two ids read like `foo-system` /
`foo-listing`.

When the two banners carry **different** titles, use the
`Jahresinhaltsverzeichnis` title for `<h1>` (e.g. *Vollgas für die Floppy
1570/1571*, not the deep-dive's *Die 1570/71 gibt Gas*) and demote the other
banner to an `<h2>` at the seam, so the file keeps exactly one `<h1>`.

- **Same product/topic name in both banners**, literally or near-literally
  (e.g. *"Variosystem — die gelungene Erweiterung von Vizawrite 64"* on
  p.49 and *"Variosystem druckt für Sie"* on p.56; *"Das Rhythm Construction
  Set (R.C.S.)"* on p.50 and again on p.52).
- **Same author byline** across the two pieces, or one shared author
  appearing in both bylines with different `xx` editor suffixes
  (e.g. `(Georg Brandt/dm)` on both R.C.S. pieces).
- **One piece is a short overview / *Anwendung des Monats* blurb** for
  the same product the other piece deep-dives into, regardless of which
  one prints first.
- **The two pieces are non-adjacent in print** (an unrelated article sits
  between them), and the signals above hold. Adjacent pieces are usually
  legitimately separate; the non-adjacent layout is the editorial
  fingerprint of a deliberate pair.


### Heading SIZE decides article vs. section — measure it, don't guess

Within a rubric like *Aktuelles* the news items carry small headings while a
full article on the same spread carries a **display headline several times
larger**, usually with its own bold stand-first. The OCR flattens both to the
same `<h2>`, so the distinction is invisible in the text and must be read off
the page:

- 8609 p8 sets the editorial and *Commodore Deutschland — auf Erfolg
  ausgerichtet* side by side. The latter is a display-headline interview with a
  bold intro and its own `(aw)` — a separate article — while the Aktuelles items
  that follow on p9 have small headings. It shipped buried inside `8 Aktuelles`.
- Corollary: after splitting, the rubric article's own `64er.pages` and filename
  usually move (Aktuelles became `9 Aktuelles.html`, pages `9-12`).

**The `<h1>` may not be typeset as text at all.** Where the opening spread is a
full-bleed image, the title is set *inside the artwork* and the OCR never sees
it: `34 Marktübersicht Drucker` should be `<h1>Punkt für Punkt</h1>`. When the
h1 looks like a rubric label rather than a title, check
`64er.index_title` — the annual index records the real one (here already
`Punkt für Punkt (Druckerübersicht)`).

### What the merged HTML looks like

- **One `<article>`, one `<h1>`.** Use the longer / more topical title
  (the deep-dive's title, not the short overview's title). For R.C.S.
  this means *"Das Rhythm Construction Set (R.C.S.)"* (which both
  banners happen to share); for Variosystem it's *"Variosystem — die
  gelungene Erweiterung von Vizawrite 64"*, not the shorter
  *"Variosystem druckt für Sie"*.
- **Two `<p class="intro">` paragraphs**, one per piece, each sitting at
  its print-order position inside `<article>`.
- **Two `<address class="author">` bylines** if both pieces are signed.
- **`<meta name="64er.pages">` covers both spans**, comma-joined and in
  print order — e.g. `content="49,56-66"` for Variosystem,
  `content="50,52-56"` for R.C.S.
- The second piece's content (sub-headings, figures, asides, listings,
  *Lebenslauf*-style author box, etc.) sits **inline at its print-order
  position**, never reordered or hoisted.

### Anti-pattern

*"Two h1-style banners on different pages → must be two articles."*
Wrong. The banner is per-print-piece. Check for the signals above
first; if any one holds, it's a paired article and must stay merged.

### Concrete examples (do not touch)

These files are already correct and are the canonical pattern to
match against:

- `issues/8607/49 Variosystem — die gelungene Erweiterung von Vizawrite 64.html`
  — merges the p.49 deep-dive (intro begins *"Varioprint bietet die
  Möglichkeit…"*) and the p.56 consumer overview (intro begins
  *"Variosystem verwandelt Ihren Drucker in eine kleine Druckerei…"*).
- `issues/8607/50 Das Rhythm Construction Set (R.C.S.).html` — merges
  the p.50 *Anwendung des Monats* piece (intro begins *"Rhythmen und
  Rhythmussequenzen, ja sogar ganze Schlagzeug-Begleitungen…"*, with
  byline `(Georg Brandt/dm)` and a *Lebenslauf* aside) and the p.52
  deep-dive (intro begins *"R.C.S. ist ein Programm, das zur
  Erstellung von Rhythmen und Rhythmussequenzen dient…"*).

History: commit `1e661a47b` ("split Variosystem into two articles") was
reverted by `b1ce6c2b6` ("merge Variosystem back to single article")
after user feedback *"i did not want the article to be split. i need it
combined"*. The lesson generalises: **always keep these merged.**

### Verification — list multi-intro / multi-byline files for eyeballing

After split, list every `*.html` whose `<article>` carries more than
one `<p class="intro">` or more than one `<address class="author">`,
together with its `<meta name="64er.pages">`. Each entry in the list
should be a known paired article; if anything else turns up, the
splitter (or a previous edit) mis-handled the section.

```bash
for f in issues/8607/*.html; do
  intros=$(grep -c '<p class="intro">' "$f")
  bylines=$(grep -c '<address class="author">' "$f")
  if [ "$intros" -gt 1 ] || [ "$bylines" -gt 1 ]; then
    pages=$(grep -oE '64er.pages" content="[^"]+"' "$f" | sed -E 's/.*content="([^"]+)"/\1/')
    printf 'intros=%s bylines=%s pages=%-12s %s\n' \
      "$intros" "$bylines" "$pages" "$(basename "$f")"
  fi
done
```

Operator eyeballs the list and confirms every entry is a legitimate
paired article. Anything unexpected is the actionable signal — fix
that file, not the rule.

## Notes / lessons

- the embedded splitter's text replacements overlap with `r070_html_cleanup.sh`. That's
  intentional — running 070 first means the .html is already clean when split
  starts, and split's own replacements become no-ops. Either order is safe.
- Bylines must look like `<p>(Author Name)</p>` or `<p>(Name1/Name2)</p>`
  on their own paragraph. Bylines embedded mid-sentence won't be picked up.
- The `[pages]` spec on `<h1>` is the only way the script learns the
  article's page range — make sure every `<h1>` in the OCR `.md` ends
  with `[N]` or `[N-M]` or `[N,M-O]`.
- **Paired articles never get split.** See the "Paired articles — never
  split" section above. If a consolidated `.md` section contains two
  intros / two bylines / two h1-banner-looking lines for the same
  product, it stays one section (one `<h1>`) so the splitter emits one file.
