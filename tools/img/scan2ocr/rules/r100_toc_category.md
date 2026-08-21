# 100 — Fill `64er.toc_category` in every article from a mapping

**Applies to:** all — every article in every issue needs a `toc_category` from that issue's own `toc.txt`.

**Goal:** replace the placeholder line
`<!-- <meta name="64er.toc_category" content="XXX"> -->`
in each per-article HTML with a real
`<meta name="64er.toc_category" content="...">`, driven by an explicit
mapping you write by hand from the printed Table of Contents.

The script is reusable across issues. The mapping itself is one-shot per
issue — you build it from the printed TOC (see the previous step for the
`toc.txt` it must agree with) and feed it to this script.

## Where the categories come from: THIS issue, and nothing else

The closed set of legal values is `issues/<ID>/toc.txt`, which step 090
transcribed from **this issue's own printed Inhaltsverzeichnis**. It is not a
house list, it does not carry over, and it differs completely between the two
kinds of issue:

| issue | `toc.txt` |
|---|---|
| `8609` (monthly) | Aktuelles, Hardware-Test, Hardware, Drucker, Spiele-Test, Wettbewerbe, `Listings zum Abtippen\|…`, 64'er-Extra, Grundlagen, Kurse, Software-Test, Software-Hilfen, Software, Rubriken |
| `SH8507` (sonderheft) | Vorwort, Eintipphilfen, Anwendung, Datenfernübertragung (DFÜ), Dateiverwaltung, Finanzen, Naturwissenschaft, Statistik, Rubriken |

A Sonderheft is one theme end to end, so its categories are the sections of that
theme — they will not resemble the monthlies' at all. **Read this issue's
`toc.txt` before writing a single mapping line**, and never reach for a category
because the last issue had it. The script enforces that (it rejects any value
not in `toc.txt`), but the enforcement only catches a wrong *value*; a mapping
built from memory of another issue is wrong in a way that still validates.

The `<ID>` throughout this rule is the issue directory name — `8609` for a
monthly, `SH8601` for a Sonderheft. Every path and glob below takes it verbatim.

## Sibling meta: `64er.toc_title` (also filled from the printed TOC here)

Rule 080 (split) leaves a commented placeholder
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
  `index_title` in rule 220).
- An article **whose printed TOC line is nothing but its own name** gets no
  `toc_title` — delete the placeholder. That is the test, not a list of rubric
  names: it catches the monthly rubrics (Leserforum, Bücher, Vorschau,
  Fehlerteufelchen, Impressum, Editorial) and equally a Sonderheft's Impressum
  or a section whose TOC line repeats its headline. Apply the test to this
  issue's TOC page; do not carry a rubric list over from another issue.
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
- **Kicker + title** (print sets a bold kicker line above the title —
  in a monthly typically `Anwendung des Monats:` over `Digi-Controller`,
  in a Sonderheft the section or part name over the piece's own headline):
  join into one
  `toc_title`. Two acceptable forms — a **colon join**
  (`Anwendung des Monats: Digi-Controller`) or 8607's **`<b>` markup**
  (`<b>Anwendung des Monats:</b> Digi-Controller`). Pick ONE and use it
  for every kicker entry in the issue; don't mix within an issue.

Verification: no `<!-- <meta name="64er.toc_title" content="XXX"> -->`
comment survives in any article, and every `toc_title` value is
non-empty and not equal to that file's `<title>`.
```bash
grep -l 'toc_title" content="XXX"' issues/<ID>/*.html   # expect: none
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
tools/img/scan2ocr/rules/r100_toc_category.sh issues/8607 <<'TSV'
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

(Comments and blanks are ignored; tabs separate filename from category. The
example above is a monthly; for a Sonderheft the issue dir is `issues/SH8601`
and the categories are that issue's own — see *Where the categories come from*.)

For an alternative invocation pattern, write the mapping to
`issues/<ID>/toc_category_mapping.tsv` and run:

```bash
tools/img/scan2ocr/rules/r100_toc_category.sh issues/<ID> < issues/<ID>/toc_category_mapping.tsv
```

## Verification

After running, every article should have exactly one `64er.toc_category`
line and no remaining placeholder comment:

```bash
# placeholder gone
grep -lE '<!-- <meta name="64er\.toc_category" content="XXX"> -->' issues/<ID>/*.html
# expect: no output

# every file has exactly one toc_category line
for f in issues/<ID>/*.html; do
  n=$(grep -c '<meta name="64er\.toc_category"' "$f")
  [ "$n" -eq 1 ] || echo "$f: $n"
done

# every category value appears in toc.txt
python3 - <<'PY'
import glob, re
issue = '<ID>'
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
- **The empty category `""` is for the opening slot the printed TOC does not
  file under any category.** The generator treats an empty value as "category
  index −1" and sorts it before everything else. In a monthly that is the
  editorial. **It is not automatic, and it is not kind-independent** — decide it
  from this issue's TOC page. `SH8507` prints its opening piece under a real
  category and the published corpus follows the print:
  `3 Anwendungen für jedermann.html` → `Vorwort`, and `164 Impressum.html` →
  `Rubriken`. Not one article in that issue carries `""`. If this issue's TOC
  files its opening piece under a heading, that heading is its category.
- Articles **listed twice** in the printed TOC get **one** category. Pick the
  one whose pages match the article's `<meta name="64er.pages">` content. (The
  commonest monthly instance: an "Anwendung des Monats" announcement filed under
  Wettbewerbe and the actual listing filed under Listings zum Abtippen.)
- Articles **not in the printed TOC** (small fillers, walkthroughs)
  get the closest topical category that's already in `toc.txt`. Don't
  invent new categories — extend `toc.txt` first if you really need one.
- Once this step is done, prune any line in `toc.txt` that no article
  ended up using — the generator doesn't care about unused lines, but
  the file is documentation; keep it tight.
