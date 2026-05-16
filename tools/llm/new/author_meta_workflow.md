# `<meta name="author">` Workflow

How to fill or remove the `<meta name="author">` tag in every article HTML.

Most articles in an issue are signed by one or more named editors/authors (the bylines `(bs)`, `(ev)`, `(hm)` etc. at the end of the body, expanded in the Impressum). The author meta lists them. But several recurring rubrics and announcements have **no single author** by convention — those articles omit the meta tag entirely.

## How to run

```
Fill or remove <meta name="author"> in issues/YYMM/*.html
per tools/llm/new/author_meta_workflow.md.
```

**Input:** article HTMLs with `<meta name="author" content="XXX">` placeholder (or the line may already be filled / already removed in some).

**Output:** every article has either a correctly filled `<meta name="author">` OR the line is removed.

## Rules

### Rule 1 — most articles have a real author meta

For a normal article, the `content` lists the bylines that appear in the body, in the order they appear. Use the editor initials exactly as printed in the article (`bs`, `hm`, `ev`, etc., expanded to "Boris Schneider", "Harald Meyer", "Volker Everts" per the Impressum). External contributors come first if their full name is in the byline; in-house editor initials trail.

Examples (from 8606):
```html
<meta name="author" content="bs, bs, hm, ev, hm">      <!-- 8 Aktuelles: 5 newsletter items by 4 editors -->
<meta name="author" content="Heimo Ponnath, dm">       <!-- 134 Basic→Assembler: guest author + in-house editor -->
<meta name="author" content="Michael Scharfenberger">  <!-- 8 Im neuen Gehäuse... (editorial) -->
```

If the body byline is `(bs/hm)`, the meta is `bs, hm`. If two articles by different authors are merged into one HTML (rare), include every byline in document order.

### Rule 2 — unsigned articles get NO meta tag

Drop the `<meta name="author">` line entirely (don't leave it empty `content=""`, and don't write `XXX`) for these recurring rubrics and announcements:

| Article type | Examples (8606) |
|---|---|
| **Leserforum** | per-question authorship — each `<p class="author">` inside the Q&A has its own asker |
| **Impressum** | the body IS the masthead listing every editor; no overall byline |
| **Vorschau** | unsigned editorial preview of the next issue |
| **Fehlerteufelchen** | corrections column, unsigned |
| **»Anwendung des Monats« announcement** | call for entries, unsigned |
| **»Listing des Monats« announcement** | call for entries, unsigned |
| **Other contest announcements** (e.g. »Wettbewerb: Bewegte Grafik«) | unsigned |
| **»Wie schicke ich meine Programme ein?«** | unsigned info page on submission rules |

Verify against the prior issue: every one of these has had no `<meta name="author">` for at least the last 5 issues (`8601`–`8605`).

### Rule 3 — editorial DOES get a real author meta

The editorial is *unsigned-feeling* (no `(initials)` byline at the end), but the body ends with a chief-editor signature line ("Michael Scharfenberger, Chefredakteur"). The `<meta name="author">` lists that name:

```html
<meta name="author" content="Michael Scharfenberger">
```

Even though the editorial has a per-issue title (`Im neuen Gehäuse…`, `Mit Zuversicht…`, etc.), the author meta is always the chief editor for that issue (was `Michael M. Pauly` through 8603, `Michael Scharfenberger` from 8604 onward).

### Rule 4 — placeholder `XXX` is invalid

The template ships with `<meta name="author" content="XXX">`. `XXX` must be replaced (with a real name) or the entire line removed. **Do not leave any `XXX` in any article.**

## Procedure

1. **Find all the gaps and placeholders:**
   ```bash
   grep -l 'name="author" content="XXX"' *.html
   grep -L 'name="author"' *.html
   ```
2. **Categorize each:**
   - If it's an unsigned-rubric article (Rule 2 list) → remove the meta line.
   - If it's the editorial → set to the chief editor's name.
   - Otherwise → read the body bylines and fill the content with the matching initials/names.
3. **Apply** with `sed`-free edits (use a small Python script with explicit per-file mapping, like the pattern used in `64er_id_workflow.md` and `toc_category_workflow.md`).
4. **Verify:**
   ```bash
   grep -l 'name="author" content="XXX"' *.html     # must be empty
   ```
   And spot-check a handful of articles to confirm the bylines match the body's `(initials)` markers.

## What NOT to do

- Don't set `content=""`. The convention is "either a real name, or omit the line".
- Don't leave `XXX` in any article. The generator doesn't reject it, but it leaks placeholder text to readers.
- Don't expand initials inconsistently. If 8604 used `bs` and 8605 used `Boris Schneider`, match the more recent convention or stay with whatever the issue already uses.
- Don't add an author for unsigned rubrics just because the file has a placeholder — verify the body has no byline first.
- Don't list editors who only appear in the Impressum (the Impressum already lists them; the article meta only lists who actually worked on THIS article).
