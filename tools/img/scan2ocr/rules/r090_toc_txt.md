# 090 — `toc.txt`: order of TOC categories for the issue

**Applies to:** all — every issue has a printed Inhaltsverzeichnis and its own closed category set. A Sonderheft's set is simply its own (`SH8507`: Vorwort, Eintipphilfen, Anwendung, … Rubriken).

**Goal:** produce `issues/<YYMM>/toc.txt`, the per-issue ordered list of
allowed `64er.toc_category` values. The site generator reads this file
and (a) controls the rendering order of categories on the issue page,
(b) rejects any article whose `<meta name="64er.toc_category" content="…">`
is not present in the list.

This is a one-off transcription step done from the printed Table of
Contents (Inhaltsverzeichnis) of the issue. There is no automated
extraction — the printed TOC is the source of truth and OCR is too
unreliable for this small, high-leverage file.

## File format

- Plain text, one category per line, terminated by `\n`.
- A bare `Category` line declares a top-level category.
- `Parent|Sub` declares a sub-category (pipe-separated). Sub-categories
  can nest: `Parent|Sub|Subsub`.
- Order is the rendering order on the issue page.
- When a parent and its `Parent|Sub` lines both appear, list the
  `Parent|Sub` lines first and put the bare `Parent` *after* them. The
  bare line's position is where articles tagged with just the parent
  (no sub) sort.

Example (real, from `issues/8606/toc.txt`):

```
Aktuelles
Hardware-Test
Computerzubehör
Dateiverwaltung
Wettbewerbe|Anwendung des Monats
Wettbewerbe
Listings zum Abtippen|Anwendung des Monats
Listings zum Abtippen|Listings des Monats
Listings zum Abtippen|Anwendung
Listings zum Abtippen|Grafik
Listings zum Abtippen|Tips & Tricks
Listings zum Abtippen
64'er Extra
Kurse
Software-Test
Spiele-Test
Rubriken
```

## Procedure

1. Find the TOC pages in the issue's PDF (usually pages 6–7; sometimes
   4–5 for older issues). Render them as PNGs so you can read them
   clearly:
   ```bash
   for p in 6 7; do

```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')     # <tmp>/masters600
```

     # masters600 is 600 dpi, so 150 dpi is -resize 25%.  NOT pdftoppm of
     # the issue PDF: that file is assembled at step 006 and does not exist
     # while the issue is being built.  See r000, "THE PAGE IMAGE IS masters600".
     magick "$SRC/$(printf %03d $p).png" -colorspace Gray -resize 25% \
       <scratch>/toc_p$p.png
   done
   ```
2. Walk the printed TOC **column-by-column, top to bottom, left to
   right**. That gives the order to use in the file.
3. Wording: **take the exact spelling from this issue's printed TOC**,
   normalised to Title Case. The print typically uses all-caps for
   section headers (`AKTUELLES`, `64'er-EXTRA`, `LISTINGS ZUM ABTIPPEN`);
   keep the punctuation and hyphenation but Title-Case the letters
   (`Aktuelles`, `64'er-Extra`, `Listings zum Abtippen`). If the print
   has a hyphen, use a hyphen; if it has a space, use a space.
4. Granularity: **match the granularity of the most recent issues** in
   the repo. Concretely:
   - If the printed TOC lists six separate "Tips & Tricks …" subsections
     (one per system/program), still record them as a single
     `Listings zum Abtippen|Tips & Tricks` line — that's what prior
     issues do.
   - Conversely, do not invent sub-categories that the print doesn't
     name; only break a top-level into `Parent|Sub` lines when the
     print itself uses a sub-header.
5. Write `issues/<YYMM>/toc.txt`. Final newline at end of file.

6. **Write `issues/<YYMM>/toc_entries.txt` as well — the ENTRIES, not just
   the sections.** You have just read every one of them off the page; this
   keeps them instead of throwing them away. One line per printed TOC entry,
   tab-separated:

   ```
   page<TAB>section<TAB>entry
   8	Rubriken	Editorial
   16	Rubriken	Leserforum
   50	Wettbewerbe	Blitzschnelle 3D-Animation
   54	Listings zum Abtippen|Listing des Monats	3D-Grafik in Echtzeit
   187	Rubriken	Impressum
   ```

   `section` is the `toc.txt` line the entry sits under, verbatim. `page` is
   the printed page number. `entry` is the printed entry text — and "the
   printed entry text" was too loose to act on, so, MEASURED on SH8604:

   * `entry` is **the bold title as printed, and only that**: not the blurb
     under it, and not a qualifier the TOC adds such as *(nur auf Diskette)*
     or a `Kurs:` prefix.
   * **Normalise the glyphs the way the article FILENAMES do** — `–` for the
     dash, `'` for the apostrophe, `...` for the ellipsis. The two are compared
     downstream, and 100 cannot match an entry whose dash is the other one.
   * **A printed page number that is wrong goes in as printed**, and the
     misprint is named in `LOG.md`. SH8604's TOC puts MSE on 95; the article
     starts on 94. Correcting it silently loses the only record that the page
     and the TOC disagree.
   * The **disk icon** beside an entry (the Programm-Service marker) OCRs as
     `EI`, `Ei`, `BE` or `Bi`. It is not part of the entry text.
   * **A Sonderheft may have NO Rubriken box at all** and still have an
     Impressum — and, in SH8604, an Einleitung the TOC does not list.
     Neither this step nor 100 covers that; record both, and do not go
     looking for a box that is not printed.
   * Step 1's page loop assumes the TOC is on 6-7 or 4-5. SH8604's is **p5
     alone**. Find it, do not count on it.

   **Why this file exists.** Step 100 needs exactly this and used to
   re-read p6/p7 in full to get it — MEASURED on 8611, where three separate
   readings of the same two pages happened in one afternoon. And it makes
   the Rubriken box checkable: 8611's Editorial was absorbed into its
   neighbour and nothing noticed until step 100, because a missing article
   whose text is still on the page is invisible to every coverage check.
   The Rubriken box is the most regular part of the TOC — one line each,
   name and right-aligned page — and reads cleanly at column-crop
   resolution.

   `toc.txt`'s contract is unchanged. Anything reading `toc_entries.txt`
   must tolerate its absence: issues imported before this chain do not have
   one.

## Verification

```bash
# 1. shape: every line is either bare or pipe-separated, no empties:
grep -nE '^$|[[:space:]]$|^[[:space:]]' issues/<YYMM>/toc.txt && echo "BAD"
# (no output = good)

# 2. cross-check that every article's <meta name="64er.toc_category"> value
#    appears in toc.txt (run this once all toc_category metas are filled):
python3 - <<'PY'
import glob, re
issue = '<YYMM>'   # e.g. '8608' — set to the issue being built
toc = set(line.strip() for line in open(f'issues/{issue}/toc.txt') if line.strip())
missing = set()
for f in glob.glob(f'issues/{issue}/*.html'):
    for m in re.finditer(r'<meta name="64er\.toc_category" content="([^"]+)"', open(f).read()):
        if m.group(1) not in toc:
            missing.add(m.group(1))
for m in sorted(missing): print(f"missing from toc.txt: {m!r}")
PY

# 3. build the site for this issue and confirm no
#    "ERROR: category not in toc.txt:" lines appear.
```

## Lessons

- The first three sub-categories under a parent in the printed TOC are
  *not* necessarily what other issues call them. Older issues use
  short labels (`Anwendung`, `Spiel`, `Grafik`, `Listing des Monats`),
  newer issues may print them spelled out. Pick the wording from the
  current issue's TOC, but pick the granularity that matches prior
  issues' habits — that minimises churn in the per-article
  `toc_category` values across the year.
- `64'er-Extra` vs `64'er Extra` and similar punctuation choices: trust
  the current issue's printed TOC, even if a previous issue used a
  different glyph. Each issue's TOC is its own canonical source.
- The TOC categories are a *closed set* for the issue; once `toc.txt`
  is settled, any article must pick one of its lines exactly.
