# Adding Listings (PRG) to Article HTMLs

## Workflow

1. Run `tools/prg_links.sh` on the `.D64` disk image → produces `prg.txt` with HTML snippets and extracts files to `prg/`
2. Fill in placeholder values (`XXXXXXXXXXXX`, `YYYYYYYYYYYYY`) with correct `data-name` and captions
3. Insert listing snippets into the correct HTML articles
4. For listings not on disk (manually typed), files may come separately (e.g. `prg2/` directory)

### How `prg.txt` is organized

The 64'er disks contain dummy "section separator" files named `--------------NN` where **NN is the starting page number of the article** the following listings belong to. `prg_links.sh` emits those separators as HTML comments:

```
<!-- 0    "-------------171" del  -->

<figure><pre data-filename="zviza" data-name="XXXXXXXXXXXX"></pre><figcaption>YYYYYYYYYYYYY</figcaption></figure>
```

This means all listings under `"------NN"` belong to the article whose start page is NN. Look up the article in the issue folder by that page (e.g. `171 Tips und Tricks zu Vizawrite 64 (Teil 5).html`). Legacy-issue disks sometimes have `"-----M/YY-NN"` sections — those listings were reprinted from an earlier issue M/YY; place them in the current issue's article that references them, not in the original issue.

### Finding listing captions

The issue PDF usually has an embedded text layer. Extract it once:

```bash
pdftotext -layout <issue>.pdf /tmp/<issue>_full.txt
```

Then grep for the exact `Listing N.` caption:

```bash
grep -nE "Listing [0-9]+\." /tmp/8605_full.txt
```

This gives you the verbatim caption text in seconds — no scan reading needed. Only fall back to visual OCR when the PDF text layer is broken or the caption didn't OCR cleanly.

### Per-listing placement loop

For each listing in `prg.txt`:
1. Note the section separator comment above it → identifies the target article by start page.
2. `grep "Listing N"` in the target article HTML to find the **first textual reference** (e.g. `"Abhilfe schafft das abgedruckte Programm »ZVIZA« (Listing 1)"`).
3. Insert the `<figure>` block **after** the `</p>` of the paragraph that first mentions it, or at the end of that section — not splitting any paragraph. Same rule as figures in `img_workflow.md`.
4. Replace `data-name="XXXXXXXXXXXX"` with a short, user-visible name (typically the program name from the article, e.g. `ZVIZA`, `Greatprint`, `Matrimult` — not the raw filename). Must be **unique within the article**.
5. Replace `<figcaption>YYYYYYYYYYYYY</figcaption>` with the verbatim caption from pdftotext.
6. **Delete the placed block from `prg.txt`** so it doesn't get re-inserted and you have a running "remaining work" list. Remove its preceding section comment too if the section is empty afterwards.

### First listing checklist (sanity check)

Before calling a first listing "done":
- The `data-filename` exactly matches a file in `prg/` (`prg/zviza.txt` for a BASIC listing, `prg/zviza.prg` for an MSE/binary one). Case-sensitive.
- The `.txt` header line reads `;filename.prg ==ADDR==` where ADDR is the load address.
- The caption in `<figcaption>` matches the scan verbatim, including the period after the number.
- The article has no dangling `Listing N` reference — every `(Listing N)` in the body text has a corresponding `<figure>` below it.

## HTML Patterns

### BASIC listing (petcat-decoded, in `prg/*.txt`)
```html
<figure>
    <pre data-filename="quizmaster" data-name="Quizmaster"></pre>
    <figcaption>Listing 1. Caption text here</figcaption>
</figure>
```

### MSE binary listing (in `prg/*.prg`)
```html
<figure>
    <pre data-filename="hardmaker.prg" data-name="Hardmaker" data-mse=mse1></pre>
    <figcaption>Listing caption</figcaption>
</figure>
<div class="binary_download" data-filename="hardmaker.prg" data-name="Hardmaker"></div>
```

### Binary-only download (no listing display, e.g. compiled versions)
```html
<div class="binary_download" data-filename="c_disk-optimizer.prg" data-name="Disk-Optimizer (compiliert)"></div>
```

### Hidden companion files (belong to an article but have no printed listing)

A `.prg` or `.txt` file from the disk can be assignable to an article (because the section separator on the D64 says so) but have no corresponding printed listing in the magazine — it's bonus content the reader can download but not type in. Place it in that article, but hide it:

- **Binary `.prg` files** → `<div class="binary_download" …>` (identical to the binary-only pattern above). The CSS hides the div's body and only the download link is shown.
- **Text `.txt` files** (rare) → `<pre data-filename="…" data-name="…"></pre>` wrapped in `<div style="display: none;">`, so the petcat text is available for the download machinery but nothing renders in the article body.

Example for a Hi-Res font bonus file that belongs to the Super-Print article but has no printed listing:

```html
<div class="binary_download" data-filename="duennschrift.prg" data-name="Dünnschrift"></div>
```

Example for a text companion file with no printed listing:

```html
<div style="display: none;">
    <pre data-filename="helper" data-name="Helper"></pre>
</div>
```

This rule resolves the ambiguity that used to send orphan files to `LOG.md`: if the D64 section separator tells you which article a file belongs to, and the article text doesn't mention it, place it as a hidden companion — don't log or skip.

### Inline listing (not from disk, e.g. Z80 assembler, Pascal)
```html
<!-- Eingetippt von Patrick Georgi -->
<figure>
    <pre>
  $0FFD0         SEI            ;IRQ aus
  ...</pre>
    <figcaption>Listing 1. Caption</figcaption>
</figure>
```

**Anti-memory rule for inline listings:** when embedding an inline listing of any non-trivial length (more than a handful of lines), **never retype it from memory or from context**. The file is on disk — splice it in via shell:

```bash
{
  head -N article.html   # lines before the insertion point
  echo '        <!-- Eingetippt von Name -->'
  echo '        <figure>'
  echo '            <pre>'
  cat /path/to/source.txt
  echo '</pre>'
  echo '            <figcaption>Listing N. Caption from scan</figcaption>'
  echo '        </figure>'
  echo '    </article>'
  echo '</body>'
  echo ''
  echo '</html>'
} > article.html.new && mv article.html.new article.html
```

Then `Read` the result to verify the splice. Do NOT use the Edit tool to insert a multi-line code block by re-typing its contents — that's exactly the pattern the anti-memory rule forbids (reading a file into context then writing it back out = reproduction from memory).

### data-range for line subsets of a BASIC listing
```html
<pre data-filename="dbii" data-name="DBII" data-range="182,215-216,330,3016-3032"></pre>
```
- Comma-separated ranges; single numbers allowed (no need for `182-182`)
- Generator inserts blank lines between non-contiguous ranges
- Works with both petcat and checksummer views

## Attribute Reference

| Attribute | Purpose |
|-----------|---------|
| `data-filename` | Base name matching `prg/*.txt` (without `.prg`) or `prg/*.prg` (with `.prg`) |
| `data-name` | User-visible friendly name; must be unique per article |
| `data-mse` | MSE version (`mse1`); triggers MSE hex dump display |
| `data-range` | Line number filter: `"100-200"`, `"100,200-300,400"` |
| `data-checksummer` | Checksummer version number; enables dual petcat/checksummer view |
| `data-availability` | Set to `"local"` to suppress download link |
| `data-hypraass` | Set to `"1"` for Hypra-Ass/Top-Ass source listings (WIP) |

## Rules

- **Captions must be verbatim** from the magazine scan — read from `png/*_600_cropped.png` files (scale with `magick -resize 25%` if 600dpi)
- **`data-name` must be unique** within an article; two listings can't share the same `data-name`
- **`data-filename` base name max 16 chars** (C64 filename limit)
- **`.txt` header line**: must be `;filename.prg ==ADDR==` matching the base name
- **Credit external contributors**: add `;Eingetippt von Name` as first line in `.txt` files, or `<!-- Eingetippt von Name -->` comment in HTML for inline listings
- **Compiled/binary-only versions**: use only `binary_download` div, no `<pre>` display
- **Placement**: in Tips & Tricks articles, place each listing at the end of its own section, not at the end of the entire article. For other articles, all listings go at the end before `</article>`.
- **Files from external contributors** (e.g. `prg2/`): copy to `prg/`, fix header line to match filename, add credit line. For inline-only listings (Z80 asm, Pascal), embed directly in HTML.

## Report files that belong nowhere — don't dump them in Impressum

Some files on the D64 belong to no article in the current issue:
- Boot/splash screens like `leserinfo!` (a "Dear Reader" screen that runs at disk boot)
- Reprints of earlier-issue utilities (Checksummer, MSE, Speeddos, etc.) that are shipped so readers can type in the current issue's listings, marked on the disk with `"------M/YY-NN"` section separators pointing at the original publication, not the current issue
- Any file whose D64 section separator doesn't match any article in the issue

**Do NOT dump these into the Impressum, a service page, or any random article.** They have no printed counterpart in this issue and no natural reader-facing home. Instead:

1. Leave them out of all articles.
2. Report them to the user in the session (list the filenames + their section separator if any + why they don't fit).
3. If the user doesn't give a placement decision, add a `LOG.md` entry listing the unplaced files so a future reviewer can deal with them.

The user may choose to ignore these files entirely (the disk download itself is sufficient), add them to a dedicated utilities page, or place them in an article I haven't found. That's a human decision — do not pre-commit it by shoving them into the Impressum.

## When you can't decide — log, don't delete

If a listing reference in the HTML looks wrong, an orphan file on the D64 can't be placed, or a `Listing N` reference in the article body has no matching file on the disk, **do not silently delete or skip it**. Write an entry in the issue's `LOG.md` (create it if it doesn't exist) describing:

- the file and location (or missing file)
- the exact content / reference
- what you looked for (pdftotext search, D64 section separator, adjacent articles)
- possibilities you considered
- what action a reviewer should take

Then leave `prg.txt` and the HTML untouched for that entry and move on. A human can decide later — a deleted orphan cannot be retrieved without scanning git history.

**Exception** — the "hidden companion" rule above resolves the common case where a file belongs to an article (per its D64 section separator) but has no printed listing. Use `<div class="binary_download">` or the hidden `<pre>` pattern directly; no LOG.md entry needed for that case.

## Generator Integration (`generate.py`)

- `prg/*.txt` → read into `listings[basename]` (text) and `listings_bin[basename]` (binary via petcat2prg)
- `prg/*.prg` → read into `listings_bin[filename]` (raw binary)
- `data-filename` without `.prg` suffix → BASIC listing path (petcat text, optional checksummer)
- `data-filename` with `.prg` suffix → MSE or binary path
- Normal BASIC rendering strips `;` comment lines, empty lines, and leading spaces
- `data-hypraass` → preserves assembler formatting (implementation in progress via `tools/hypra_ass_decode.py`)
