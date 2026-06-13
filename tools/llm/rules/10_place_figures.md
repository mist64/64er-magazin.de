# 10 — Place `<figure>` tags for the extracted listings

**Goal:** turn the worklist `issues/<YYMM>/prg.txt` into real, placed
listing figures inside each per-article HTML, and finish each one with
the actual program name (`data-name`) and verbatim caption
(`<figcaption>`) from the printed magazine.

This step has **no automation**. It's editorial: every `<figure>`
block in `prg.txt` has to be matched to an article, dropped into the
right spot in that article, and have its two placeholders filled.
The verification at the end is automatable; the placement decisions
are not.

## Inputs

- `issues/<YYMM>/prg.txt` — the worklist produced by the previous
  step. Sections are delimited by HTML comments naming the disk's
  per-article separator file (e.g.
  `<!-- 0    "--------------36" del  -->` ⇒ "everything below this,
  until the next separator, belongs to the article whose start page
  is 36").
- `issues/<YYMM>/prg/` — the actual `.txt` / `.prg` files.
- `issues/<YYMM>/64er_*.pdf` — for verbatim captions; one-time
  `pdftotext -layout … /tmp/64er_<YYMM>_full.txt` makes them grep-able.
- `issues/<YYMM>/<page> ….html` — the article files to receive
  figures.
- The page-scan PNGs under `issues/<YYMM>/png/` (when the PDF text
  layer is wrong, fall back to reading the scan visually).

## Procedure

For each `<figure>` block in `prg.txt`, in order:

1. **Find the article.** The section separator above it gives the
   article's start page; the file is the one whose name begins with
   that page number. Section separators of the form
   `----M/YY-NN` point at issue M/YY's article — those listings are
   reprints belonging to that older issue, not the current one
   (place them or report them per the rules below).
2. **Find the body reference.** Inside the target HTML, look for the
   first text mention like `(Listing 1)`, `Listing 1.`, `(Assembler-
   Listing)`, etc. That's where the figure goes. The figure block
   must be inserted **after** the `</p>` of the paragraph containing
   that first mention, never splitting a paragraph.
3. **Fill `data-name`.** Use the user-visible program name from the
   article body, not the raw on-disk filename
   (e.g. `data-name="Vectors"`, not `data-name="vectors.boot"`).
   Must be unique within the article.
4. **Fill `<figcaption>`.** Take the verbatim caption from the
   magazine — typically `Listing N. …` (note the trailing dot after
   `N`). Use `pdftotext` first; if it disagrees with the scan on a
   program name, trust the article body's spelling (the body uses
   the name multiple times; the caption is a single OCR target).
5. **Remove the placed block from `prg.txt`.** That keeps `prg.txt`
   as a running "remaining work" list. Drop the section comment too
   when its block is empty.
6. **Walk the listing tail in printed Listing-N order.** When the
   article has more than one listing, after all are placed, reorder
   them so the captions read `Listing 1`, `Listing 2`, … in
   sequence; disk-directory order is usually not the print order.

## Variants — which HTML shape to use

| File classification | HTML shape | Why |
|---|---|---|
| BASIC source (`prg/<name>.txt` present, `.prg` in `prg/del/`) | `<pre data-filename="<name>"></pre>` (no `.prg` suffix) | Generator renders petcat text; binary download materialised via `petcat2prg`. |
| MSE binary (`prg/<name>.prg`) | `<pre data-filename="<name>.prg" data-name="…" data-mse=mse1></pre>` + sibling `<div class="binary_download" data-filename="<name>.prg" data-name="…">` | MSE hex dump + download. |
| Hypra-Ass source | `<pre data-filename="<name>.src" data-assembler="hypra-ass"></pre>` | Auto-decoded by generator. Master file is `prg/<name>.prg` or `prg/<name>.txt`. |
| Top-Ass source | `<pre data-filename="<name>.prg" data-assembler="top-ass"></pre>` | Auto-decoded. |
| Compiled / binary-only download | `<div class="binary_download" data-filename="<name>.prg" data-name="…">` alone | No printed listing to display. |
| Hidden BASIC companion (no printed listing, but section separator assigns it to this article) | wrap a `<pre data-filename="<name>">` (no `.prg`) inside `<div style="display: none;">` | Materialises a download link without rendering content. |
| Hidden binary companion | `<div class="binary_download" data-filename="<name>.prg" data-name="…">` | Same intent; CSS hides body and shows only the download link. |
| Printed listing not on the disk (e.g. one-shot pre-step, in-ROM disassembly) | `<figure><pre>TODO</pre><figcaption>Listing N. …</figcaption></figure>` | Records that the print has it; future pass OCRs the printed bytes into the `<pre>`. |

For inline-typed listings (e.g. Z80 asm, Pascal source typed by a
contributor and arriving outside `prg/`), **never re-type a non-trivial
listing from memory**. Splice the source file's bytes into the article
via shell I/O (`cat source.txt`), then read back the result to verify.

## Rules / things to watch

- **Captions are verbatim.** Trailing dot after `Listing N`, German
  typography (`»…«`), exact punctuation. Read from the PDF text layer
  first; fall back to scan-visual only when the layer is broken.
- **`data-name` is unique per article.** Two figures in one HTML
  can't share it.
- **`data-filename` base name max 16 characters** (the C 64 file
  system's hard limit).
- **`.txt` header line** must be `;<filename>.prg ==ADDR==` with
  `<filename>` matching the file's base name and `ADDR` matching the
  decoded load address.
- **Credit external contributors** — `;Eingetippt von Name` as the
  first line of contributor-typed `.txt`, or `<!-- Eingetippt von Name
  -->` for HTML-inline listings.
- **Placement style.** Three article shapes, three placements:

  1. **One big program** — article describes a single program with
     multiple `<h2>` sub-sections covering its modules / facets
     (e.g. `67 Die ideale Ergänzung` Master-Text-Drucker driver
     suite, `50 Das Rhythm Construction Set (R.C.S.)`,
     `73 Vectors`, `49 Variosystem`): **all listings in a single
     block at the very end, after the byline, before
     `</article>`** (or before a Fehlerteufelchen aside if
     present).

  2. **Sub-articles of small tools** — column of independent small
     programs with their own bylines per sub-section (Tips &
     Tricks Einsteiger / Profis / C 16, Aktuelles, CP/M-Ecke,
     Hypra-Basic, Newsroom): **listing AFTER the tip's byline at
     the very end of that tip section**. Pattern: tip body prose →
     `<address class="author">(byline)</address>` → `<figure>`
     listing + `<div class="binary_download">` companions → next
     section's `<h2>`.

  3. **Tutorial** — article teaches a concept or technique with
     short illustrative snippets (Kurs / Hilfreiche Grundlagen /
     Reise durch …): **small listings inline**, placed mid-prose
     where the tutorial introduces them. The print typeset is the
     ground truth: tutorial code snippets are usually 3-10 lines
     and tightly interleaved with explanatory text. Don't move
     them to the article tail — that breaks the pedagogical flow.
     Examples: 133 Computer-Simulation, 136 Pascal-Kurs,
     139 Basic zu Assembler, 150 Grafik für Profis, 85 Reise
     durch den C 128.

  **How to pick:**
  - One author, one program → shape 1.
  - Multiple `<h2>` sub-sections each with its own author/byline →
    shape 2.
  - "Kurs", "Teil N", "Grundlagen", "Reise durch …", inline body
    code snippets that teach a concept → shape 3.
  - **Test:** are the article's `<h2>` sub-sections describing the
    SAME program's facets? Then end-of-article. Are they unrelated
    sub-programs with their own author / their own caption? Then
    per-section. In 8607 `67 Die ideale Ergänzung` (Master-Text-
    Drucker) has sub-sections `Text via RS232 senden`,
    `Der Zeichensatz-Editor`, `Editor`, `Hauptmenü` — all parts of
    ONE driver suite → all 6 listings belong at end.
  - **Within a tip section, listing goes AFTER the byline at the
    very end of that section**, never between body paragraphs.
    Pattern: tip body prose → `<address class="author">(byline)</address>`
    → `<figure>` listing + `<div class="binary_download">` companions
    → next sub-section's `<h2>`. Don't break the body prose by
    sticking the listing inline near the first `(Listing N)`
    reference, even when the body refers to it inline — keep the
    body block intact and append the listing after the byline.
  - **At article scope, byline ends the prose, listings follow.**
    Same shape: body → byline → listings → (Fehlerteufelchen aside
    if present) → `</article>`.
- **Disk variants of the same program** (e.g. two load-address builds
  of the same BLOCK routine): the printable source goes in the
  `<figure>`; each variant's binary download goes as a sibling
  `<div class="binary_download">` right below.
- **Listings present in `prg/` but not in any article.** Boot screens,
  utility reprints from previous issues, leftover demos: don't shove
  them into Impressum or a random article. Report them at the end of
  the session, and if no decision is given, append an entry to
  `issues/<YYMM>/LOG.md`. Better an unplaced file than a wrong
  placement.
- **References without a file.** If the article body mentions
  `(Listing N)` and there's nothing in `prg/` for it, emit
  `<figure><pre>TODO</pre><figcaption>Listing N. …</figcaption></figure>`
  with the verbatim caption, so the gap is visible in the build.
  Never silently drop a printed Listing N.

## Verification

```bash
# 1. prg.txt is empty (every listing placed) — or only contains
#    listings explicitly marked "no home in this issue" with a note.
wc -l issues/8607/prg.txt

# 2. Every <figure>'s data-filename resolves to a file in prg/ or prg/del/:
python3 - issues/8607 <<'PY'
import os, re, sys
d = sys.argv[1]; pdir = os.path.join(d, 'prg'); ddir = os.path.join(pdir, 'del')
have = set(os.listdir(pdir)) | (set(os.listdir(ddir)) if os.path.isdir(ddir) else set())
missing = set()
for f in os.listdir(d):
    if not f.endswith('.html'): continue
    for m in re.finditer(r'data-filename="([^"]+)"', open(os.path.join(d,f)).read()):
        fn = m.group(1)
        # BASIC variant: data-filename has no .prg suffix; expect <fn>.txt
        cand = fn + '.txt' if not fn.endswith('.prg') else fn
        if cand not in have: missing.add(f"{f}: {fn} -> {cand}")
for x in sorted(missing): print(x)
PY

# 3. Every <figure data-name> within an article is unique:
python3 - issues/8607 <<'PY'
import os, re, sys, collections
for f in os.listdir(sys.argv[1]):
    if not f.endswith('.html'): continue
    names = re.findall(r'data-name="([^"]+)"', open(os.path.join(sys.argv[1],f)).read())
    dup = [n for n,c in collections.Counter(names).items() if c > 1]
    if dup: print(f"{f}: duplicate data-name {dup}")
PY

# 4. Listing-N captions in each article are in print order:
for f in issues/8607/*.html; do
  ns=$(grep -oE 'Listing [0-9]+' "$f" | awk '{print $2}' )
  prev=0; for n in $ns; do
    [ "$n" -lt "$prev" ] && { echo "$f: Listing $n after $prev (out of order)"; break; }
    prev=$n
  done
done

# 5. Build the issue and confirm no listing-related errors:
.venv/bin/python generate.py --issues 8607 --future local 2>&1 | grep -iE 'listing|prg|figure|binary_download' | head
```

## End-of-session summary

When the placement pass is done, surface a table for spot-checking:

| Article | Listings placed | Binary companions | Notes / `TODO`s |
|---|---|---|---|

…with one row per article that received a figure, and an explicit
list of:
- every `<pre>TODO</pre>` placeholder (with the reason: pre-step
  not on disk, in-ROM disassembly, OCR pending, …),
- every body-text `Listing N` reference for which **no** figure was
  added, and why (e.g. errata referencing an earlier issue),
- every `prg/` file that ended up in no article, and why.

Without this table the user can't pinpoint where to spot-check.
