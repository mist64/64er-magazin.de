# Figure Placement Workflow

How to place `<figure>` blocks for PNG images into article HTML for a 1980s German computer magazine ("64'er") issue.

## Inputs

1. Article HTML draft — the article body after text import
2. `images.txt` — generated figure stubs for every PNG in the issue directory, e.g.:
   ```
   find . -maxdepth 1 -name "*.png" -not -name "title.png" -exec basename {} \; | sort -V | \
     awk '{printf "<figure>\n    <img src=\"%s\" alt=\"\">\n    <figcaption>XXXXXXXXX</figcaption>\n</figure>\n", $0}' \
     > images.txt
   ```
   `sort -V` (version sort) handles the `<page>-<num><suffix>.png` pattern correctly: `145-1, 145-2, …, 145-9, 145-9a, 145-9b, …, 145-11`. Plain `sort -n` gets the minor number wrong (`145-1, 145-11, 145-2`).
3. Page scans — extract **all pages** from the issue PDF **once, up front** into `/tmp/<issue>_pages/` so you can Read any page without repeatedly invoking `pdftoppm`:
   ```bash
   mkdir -p /tmp/8605_pages
   pdftoppm -r 150 64er_1986-05.pdf /tmp/8605_pages/p -png
   ```
   This yields `/tmp/8605_pages/p-001.png`, `p-002.png`, … Always use `/tmp` for these scratch files, never a subdirectory of the repo.

   **Resolution matters.** The PDF embeds 150 dpi images. Extract at `-r 150` — that matches the native resolution. Lower (`-r 100`) loses detail; higher (`-r 300`) just upscales pixels and wastes vision-token budget with no legibility gain.

   **If a caption is unreadable at 150 dpi: STOP and ask.** Do not guess, do not compose from context, do not upscale. The user has 600 dpi masters (separate files, not in the PDF) and will hand over a crop of the region on request. Reach for them explicitly rather than working around illegibility.

There is **no captions manifest**. Captions must be read directly from the scan.

## Mapping images to articles

Image filenames follow `<startpage>-<figurenum><suffix>.png`, e.g. `145-9a.png`. The **major number** (before the first `-`) is the **start page of the article** the image belongs to.

1. **Extract the major number** from the filename: `145-9a.png` → `145`.
2. **Find the article HTML** whose `<meta name="64er.pages" content="...">` starts with that page, e.g. `content="145-153"`.
3. **Disambiguate collisions.** Two articles can share a start page (e.g. `12 Das Klangspektakel.html` and `12 Schnelle Floppy für wenig Geld.html`). When that happens, Read the relevant pages from `/tmp/<issue>_pages/` (already extracted up front) to see which article the figure actually sits on. The image may be on a later page of the article, not the start page — check all pages in the article's `64er.pages` range. `pdftotext -layout -f N -l N file.pdf -` is useful to grep for which article title appears on a page.
4. **Fix wrong filenames with `git mv`.** Image filenames may contain errors (wrong major number). If visual verification shows an image actually belongs to a different article, rename it:
   ```bash
   git mv 145-9a.png 142-3.png
   ```
   Renumber the minor part to fit the target article's existing sequence. Do not just copy — use `git mv` so history is preserved.

## Procedure

Work through `images.txt` top to bottom. For each `<figure>` block:

1. Move it to the correct location in the article HTML (see placement rules below).
2. Replace the `XXXXXXXXX` placeholder with the caption from the scan, or remove `<figcaption>` entirely if the image has no caption (see rule 1).
3. **Fill the `alt` attribute.** Since you are looking at the image anyway to verify placement, write a short German description of what the image shows (e.g. `alt="Buchcover »C 64: Wunderland der Grafik«"`, `alt="Schaltplan des EPROM-Brenners"`, `alt="Screenshot des Hauptmenüs"`). Keep it concise — a phrase, not a sentence. Do not duplicate the figcaption text.
4. Delete the block from `images.txt` **using the Edit tool, not a script**. Read `images.txt` (or the relevant slice) first, then remove exactly the 4-line `<figure>…</figure>` block for that image.

Continue until `images.txt` is empty.

### Tool discipline

- **Use the Edit tool for all file modifications**, including removing blocks from `images.txt`. Do not use `sed`/`awk`/Python scripts to rewrite files.
- **Scratch files go in `/tmp`**, never in a subdirectory of the repo.
- **Edit is a literal string-replace, not a semantic operation.** When inserting a `<figure>` between paragraphs, the `old_string` must contain tokens on *both sides* of the insertion point (e.g. `</p>\n\n<p>Next para start`) and the `new_string` must reproduce both sides verbatim with the figure between them. Never put text in `new_string` that wasn't in `old_string` — that re-introduces a copy while the original stays in place, producing silent duplication.
- **After any non-trivial edit, Read the touched lines** to verify the result. Especially after a revert: do not stack a fuzzy edit on top of a mistake. Read the current bytes, then do one minimal precise edit.

## Placement rules

1. **Title/intro images** — filenames matching `-0*.png` (e.g. `-0.png`, `-00.png`, `-01.png`): place right after the intro paragraph(s) (`<p class="intro">`), before the first body paragraph. These are title photos **without captions** — **remove the `<figcaption>` line entirely** when pasting:
   ```html
   <figure>
       <img src="FILENAME" alt="">
   </figure>
   ```

2. **Numbered Bild images** (`-1.png`, `-2.png`, …) always have captions and go inline near their first text reference.

3. **Find the first text reference** to each Bild/Tabelle in the article body (e.g. "Bild 1", "Bilder 5 und 6", "Tabelle 4", "das Bild 2").

4. **Insert the `<figure>` block AFTER the `</p>`** of the paragraph that first mentions it. **Never split a paragraph.** If the first "Bild N" reference sits mid-paragraph, the figure still goes after the *full* enclosing `</p>` — not after the sentence containing the reference. Paragraphs are atomic; text content must not be moved, broken, or duplicated.

5. **Read the caption from the scan.** Open the corresponding page PNG, find the caption printed under the image, and type it verbatim into `<figcaption>`. Do not invent or paraphrase. If no caption is visible on the scan, omit `<figcaption>` entirely.

6. **Multiple files for one Bild** (e.g. `133-4a.png`, `133-4b.png`): put them in **ONE `<figure>`** with multiple `<img>` tags, one `<figcaption>` for the whole group.

7. **Plural references** ("Bilder 8 und 9"): place both figures after that paragraph, each as a **separate `<figure>`**.

8. **Do not duplicate** a `<figure>` already in the HTML (e.g. from an earlier pipeline step) — just verify its position and delete the stub from `images.txt`.

9. **Unreferenced images** (never named in the text): **locate the image on the scan first, then work backwards to the HTML section.** Do not pick a plausible-looking HTML section and guess — that produces miscategorizations when an article has multiple similar sections (e.g. two Centronics-interface product announcements in the same roundup article).
   1. Read the image file to see what it depicts.
   2. Read each page in the article's `64er.pages` range (not just the start page — product photos for late sections live on late pages).
   3. Find the image on the scan by visual content match.
   4. Note which **column and section heading** the image sits next to on the scan. That scan context determines the HTML section the image belongs to.
   5. Only then insert the `<figure>` in the matching HTML section.

10. **Fallback**: if you truly cannot determine placement, place after the intro.

11. **Missing numbers in a Bild sequence — STOP AND ASK.** If the Bild files for an article are numbered with gaps (e.g. files `145-1, 145-2, 145-4, 145-5, …, 145-11, 145-13, …` with no `145-3`, `145-10`, `145-12`), do **not** silently skip the gaps and carry on placing the rest. A missing file usually means one of: the file is misnamed, the file was lost during extraction, or the article's Bild numbering doesn't map 1:1 to the filenames and everything is off by one. All three need human judgment. Stop, list the missing numbers, and ask the user before placing any figure from that article.

    This rule applies **only to the numbered Bild sequence** (`-1`, `-2`, `-3`, …). It does **not** apply to tables, which are a separate sequence with a `t` prefix (`-t1`, `-t2`, …). A single `-t2` with no `-t1` is fine — not every table sequence in the scan has survived into files, and tables are tracked independently from Bilder.

## Delegate image reads to subagents

The main conversation must **never Read scan PNGs directly**. Page scans are large enough to trip the 2000px per-image limit, and even when they don't, they burn vision-token budget and pollute context with pixels you only need once.

Instead, for every image operation (caption extraction, visual description for `alt`, visual placement lookup for unreferenced images), spawn a subagent with a self-contained prompt:

- **Input to the subagent:** the exact PNG path(s), the question (e.g. "what is the verbatim caption under Bild 5?" or "describe in 10 German words what this schematic shows"), and any context it needs (article title, page range).
- **Output from the subagent:** text only — the caption string, the alt-text phrase, or "image is in column 2 next to heading 'Foo'". No images come back into main context.

The main thread keeps doing the judgment work: locating the right `</p>` anchor, writing the Edit call, removing the stub from `images.txt`. Subagents only touch pixels.

This makes the 2000px limit structurally unreachable and keeps main context focused on HTML editing.

**Subagent tool discipline for images:** subagents view image content via the `Read` tool — that is how Claude actually sees a PNG. For any image *manipulation* (cropping, resizing, format conversion) use `magick` (ImageMagick) via `Bash`. **Do not use Python / PIL / Pillow / any scripting language for image work** — `magick` is sufficient and is the only tool the main workflow assumes. Spell this out explicitly in the subagent prompt so it doesn't reach for Python by habit.

## Anti-memory rule

When reading captions from the scan, type what you see — do not compose from memory or context. If a caption is unclear, OCR the caption region or ask rather than guessing.

## Alt text: describe only what is visible

The `alt` attribute must describe only what is actually visible in the image. Do not infer identity, role, age, or any other attribute that is not directly observable.

- **No identity claims.** Do not write `alt="Porträt des Autors X"` unless a caption on the scan explicitly names the person. An unlabeled person next to an article by X is not proof it *is* X.
- **No age guesses.** Do not write `alt="Kind"` / `alt="Jugendlicher"` / `alt="älterer Herr"` from a photo. Use neutral terms like `Person`, `Mann`, `Frau`, or describe what they are doing.
- **No inferred roles.** `alt="Programmierer bei der Arbeit"` is a guess; `alt="Person am Computer"` is description.
- **Describe, don't interpret.** "Person mit Programmlisting in der Hand neben einem Drucker" is better than "Autor präsentiert sein Werk".

When in doubt, strip the claim and keep only the visual facts.

## What NOT to do

- Do not invent captions that aren't visible on the scan
- Do not move or modify any text content
- Do not change existing HTML structure beyond inserting `<figure>` blocks
- Do not remove any existing content
- Do not leave `XXXXXXXXX` placeholders in the final HTML
