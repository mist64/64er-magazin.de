# TOC Title Workflow

How to fill `64er.toc_title` for each article HTML from the magazine's printed table of contents.

## Source

The table of contents is printed on pages 6–7 (sometimes 4–5) of each issue. Extract the text once:

```bash
pdftotext -layout -f 6 -l 7 <issue>.pdf /tmp/toc.txt
```

The PDF text layer is often noisy for the TOC (mixed columns, decorative elements). Supplement with vision: crop each column from the page scan, resize to readable size, and `Read` the crop.

```bash
# Left column of page 6
magick _cache/pages/p-006.png -crop 400x700+55+1050 +repage -resize 200% /tmp/toc6_left.png
# Middle column
magick _cache/pages/p-006.png -crop 400x700+420+1050 +repage -resize 150% /tmp/toc6_mid.png
# Right column
magick _cache/pages/p-006.png -crop 400x700+840+1050 +repage -resize 150% /tmp/toc6_right.png
```

Read each crop to get the exact TOC text. Repeat for page 7.

## What `64er.toc_title` is

The `<meta name="64er.toc_title">` holds the title of the article **as it appears in the printed table of contents**, which often differs from the article's `<title>` (the headline on the article page itself).

Common differences:

- **Prefixes**: The TOC adds descriptive prefixes on a separate line above the main entry. These are printed in bold and are part of the TOC title — do not drop them. Join them to the main title with a colon and space:
  - `Hilfreiche Grundlagen: Grafik für Profis` (article title: `Grafik für Profis`)
  - `Tips und Auswahlhilfen: Die Regenbogendrucker` (article title: `Die Regenbogendrucker`)
  - `Die besten Programme im Vergleich: Profi Painter kontra Hi-Eddi+` (article title: `Zeichenprogramme im Vergleich`)
  - `Software-Test: Vizawrite Classic 128` (article title: `Vizawrite Classic 128 - Gutes noch besser?`)
  - `Marktübersicht: Was gibt's Neues zum Thema Grafik`
  - `Listing des Monats: Disk-Wizard` (article title: `Abrakadabra`)
  - `Aufruf: Listing des Monats` / `Aufruf: Anwendung des Monats`
  - `Grafik: Super Hardcopies für Epson-Drucker und Kompatible`
  - `Spiele-Listing: Steel-Slab` (article title: `Steel Slab`)

- **Shortened or alternate titles**: The TOC may use a different name entirely:
  - `CeBIT — Erste Eindrücke` (article title: `Rund um Computer in Hannover`)
  - `Editorial` (article title: `Mit Zuversicht …`)
  - `Neu: Knobelecke` (article title: `Computer-Knobeleien`)

- **Game/software reviews**: When one article reviews multiple items, the TOC lists each item separately. Combine them with `/`:
  - `Gyroscope / Bounder` (article title: `Geschickter Joystick`)
  - `Yabbadabbadoo / Back to the Future` (article title: `Von der Leinwand zum Computer`)

- **Part numbers**: The TOC may use arabic `(Teil 3)` where the article uses roman `(Teil III)`.

## Rules

1. **Include the full prefix.** The small-print line above the main entry (e.g. "Hilfreiche Grundlagen:", "Tips und Auswahlhilfen:", "Die besten Programme im Vergleich:") is part of the TOC title. Separate it from the main title with a colon and space. Do not drop it.

2. **Omit the meta tag entirely when `toc_title` equals `<title>`.** If the TOC title is identical to the article's `<title>`, do not add `64er.toc_title` — the generator uses `<title>` as the default. This keeps the HTML clean.

3. **Preserve the TOC's exact wording.** Use the TOC's spelling, punctuation, and abbreviations — not the article headline's. If the TOC says `Grafikwelt` (one word) but the article says `Grafik-Welt`, use `Grafikwelt` in `toc_title`.

4. **Section headers are not titles.** The bold section banners (`GRAFIK`, `DRUCKEN IN FARBE`, `LISTINGS ZUM ABTIPPEN`, etc.) are the `64er.toc_category`, not the `toc_title`. They go in the separate `<meta name="64er.toc_category">` tag.

5. **Sub-entries in Tips & Tricks.** Tips & Tricks articles list individual tips as sub-entries in the TOC, but the HTML has one file per article. Use the main category name as toc_title (e.g. `Tips und Tricks für Profis`), not the individual tip names.

## Procedure

1. Read each column crop of the TOC pages.
2. For each entry, note the full title including any prefix line, and the page number.
3. Match each entry to the HTML file by page number (the file is named `<startpage> <title>.html`).
4. If the TOC title differs from `<title>`, add or update `<meta name="64er.toc_title" content="...">`.
5. If they're identical, ensure no `64er.toc_title` tag exists (remove it if present).
6. After all entries are filled, verify with:
   ```bash
   grep -c 'toc_title' *.html | grep -v ":0$"
   ```
   and cross-check the count against the number of articles whose TOC title differs from their `<title>`.

## Placement in HTML

The `toc_title` meta tag goes in `<head>`, between `toc_category` and `64er.id`:

```html
<meta name="64er.toc_category" content="Grafik">
<meta name="64er.toc_title" content="Hilfreiche Grundlagen: Grafik für Profis">
<meta name="64er.id" content="profi-grafik">
```
