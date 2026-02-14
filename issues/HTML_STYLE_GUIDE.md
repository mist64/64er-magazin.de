# HTML Style Guide (64er-magazin.de)

This guide is the reference for writing new HTML files that match the repository style.
It is based on `style.css` and a scan of all current HTML files (`1403` files).

## 1. Required page skeleton

Use this exact baseline unless there is a strong reason not to:

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <title>ARTICLE TITLE</title>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="../style.css">

  <meta name="author" content="INITIALS OR NAME">
  <meta name="64er.issue" content="x/yy or Sonderheft x/yy">
  <meta name="64er.pages" content="start-end">
  <meta name="64er.head1" content="section / rubric">
  <meta name="64er.head2" content="platform / sub-rubric">
  <meta name="64er.toc_title" content="title for toc if needed">
  <meta name="64er.toc_category" content="toc category">
  <meta name="64er.index_title" content="index title if needed">
  <meta name="64er.index_category" content="index categories with | separator">
  <meta name="64er.id" content="stable_article_id">
</head>
<body>
  <article>
    <h1>ARTICLE TITLE</h1>
    <p class="intro">Lead paragraph</p>

    <!-- content -->

    <address class="author">(Author)</address>
    <p class="source">Bezugsquelle: ...</p>
  </article>
</body>
</html>
```

## 2. Head/meta conventions (measured)

Coverage across all 1403 HTML files:

- `<!DOCTYPE html>`: 1403/1403
- `<html lang="de">`: 1403/1403
- `<meta charset="UTF-8">`: 1403/1403
- `<link rel="stylesheet" href="../style.css">`: 1403/1403
- `<article>` in body: 1403/1403
- `<h1>` present: 1372/1403

`<meta name="...">` presence by file:

- `64er.id`: 1403
- `64er.issue`: 1403
- `64er.pages`: 1403
- `64er.toc_category`: 1367
- `author`: 1203
- `64er.head1`: 1195
- `64er.head2`: 942
- `64er.index_category`: 884
- `64er.index_title`: 823
- `64er.toc_title`: 805

Authoring rule:

- Always include: `author`, `64er.issue`, `64er.pages`, `64er.head1`, `64er.toc_category`, `64er.id`.
- Include `64er.head2`, `64er.toc_title`, `64er.index_title`, `64er.index_category` when they are meaningful.

## 3. Article structure conventions

Observed in current corpus:

- First element inside `<article>` is `<h1>` in 1345/1403 files.
- First tag after `</h1>` is:
  - `<p class="intro">` in 1065 files
  - plain `<p>` in 146 files
  - other blocks are much rarer

Authoring rule:

- Start article with `<h1>`.
- Put an intro paragraph immediately after `<h1>`, normally with `class="intro"`.
- Do not assume a `blockquote` convention after `<h1>`; this is not a repository pattern.
- Use `<h2>` as major section heading, `<h3>` for subsections.
- End with `<address class="author">` when author attribution exists.
- Add `<p class="source">` for source/supplier references.

## 4. Typographic conventions

- Normal paragraph text is `<p>`; default CSS already sets indentation and justified text.
- Use `p.noindent` to disable first-line indent.
- Use `p.hanging` for hanging indents.
- Use `p.pregap` to create vertical separation before a paragraph.
- Use `strong`/`b` sparingly; many legacy files overuse visual emphasis.
- Use `<code>` / `<pre>` for code/listings, not plain paragraphs.

## 5. Media, tables, listings

- Wrap images/listings in `<figure>` and captions in `<figcaption>`.
- Use `img.inline` for right-floating inline illustrations.
- Prefer `<table>` for tabular data only.
- For dense data tables, use alignment classes (`center*`, `right*`, `nobreak*`) on the table.
- Use `table.plain` for borderless/plain tabular layout.

## 6. Exhaustive class reference used in HTML files

The following classes are currently used in HTML documents in this repo.

### 6.1 Core text/content classes

- `intro`: lead paragraph style (bold, larger, centered)
- `author`: right-aligned author attribution (`address` or `p`)
- `source`: source/reference block (small text, no indent)
- `noindent`: paragraph without first-line indent
- `hanging`: hanging-indent paragraph
- `pregap`: paragraph with extra top margin
- `inline`: right-floating inline image
- `headline`: centered block image style

### 6.2 Special callout classes

- `fehlerteufelchen`: correction callout box (`aside`)
- `fehlerteufelchen_link`: red wavy-marked correction link
- `futureteufelchen`: future-note callout box (`aside`)
- `futureteufelchen_link`: blue wavy-marked future-note link

### 6.3 Article-type classes

- `impressum`: imprint article variant
- `qa`: Q&A article variant
- `q`: question block (inside `article.qa`)
- `a`: answer block (inside `article.qa`)

### 6.4 Table/list formatting classes

- `plain`: plain table/list style
- `separator`: separator rows/cells in tables
- `strong`, `strong0`: bold table/text variants
- `pre`: monospace/preserved whitespace table variant
- `left`, `center`, `right`: alignment helpers
- `vertical`, `vcenter`, `vbottom`: vertical alignment/orientation helpers
- `indent1`, `indent2`: table cell indentation helpers
- `nobreak`: no-wrap helper
- `small`, `string`: legacy niche table classes

Column-targeting table classes (apply to specific column indexes):

- `center0` `center1` `center2` `center3` `center4` `center5` `center6` `center7` `center8` `center9` `center10` `center11` `center12` `center13` `center14` `center15` `center16`
- `right0` `right1` `right2` `right3` `right4` `right5` `right6` `right7` `right8` `right14`
- `nobreak0` `nobreak1` `nobreak2` `nobreak7` `nobreak8` `nobreak15`

### 6.5 Edition/status marker classes

- `new_edition`
- `old_edition`
- `inverted`

### 6.6 Other used classes

- `binary_download` (used in HTML, no direct rule in `style.css`; treat as structural hook)
- `hsquare` (unordered list bullet variant)

## 7. Exhaustive tag inventory used in current HTML files

Common tags to use for new content:

- Structure: `html`, `head`, `body`, `article`, `section`, `aside`, `div`, `header`
- Headings: `h1`, `h2`, `h3`, `h4`
- Text: `p`, `address`, `strong`, `em`, `b`, `i`, `u`, `sup`, `sub`, `span`, `small`
- Lists: `ul`, `ol`, `li`
- Code/listing: `pre`, `code`
- Media: `figure`, `figcaption`, `img`
- Tables: `table`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td`, `caption`
- Links: `a`
- Separators: `hr`, `br`

Legacy malformed/invalid tags found in historical content (do not use in new files):

- `fbr`, `xwert`, `ywert`, `cx`, `cy`, `xmin`, `xmax`, `ymin`, `ymax`, `dx`, `dy`, `filename`, `return`, `speicher`, `zeilennummer`, `hrift`, `tt`, `font`

## 8. Practical authoring checklist

- Use UTF-8 and German language metadata.
- Keep one `<article>` per file.
- Start with `<h1>`, then `<p class="intro">`.
- Use semantic headings (`h2`/`h3`) instead of bold paragraphs for section structure.
- Use table helper classes only when alignment/wrapping is really needed.
- Keep attribution/source block at article end (`author`, optional `source`).
- Reuse existing classes; do not invent new classes unless you also add CSS in `style.css`.
- Avoid invalid legacy tags from OCR/import artifacts.
