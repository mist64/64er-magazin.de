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

A `.prg` or `.txt` file from the disk can be assignable to an article (because the section separator on the D64 says so) but have no corresponding printed listing in the magazine — it's bonus content the reader can download but not type in. Place it in that article, but hide it.

**The pattern depends on the file's CLASSIFICATION by `prg_links.sh`, not its on-disk extension:**

- **Binary file** (moved to `prg/*.prg` only — no `.txt` companion): use `<div class="binary_download">`. The CSS hides the div body and only shows the download link.

  ```html
  <div class="binary_download" data-filename="duennschrift.prg" data-name="Dünnschrift"></div>
  ```

- **BASIC file** (classified as BASIC: `.txt` exists in `prg/`, the `.prg` was moved to `prg/del/`): use a hidden `<pre>` wrapping pattern with the basename-only `data-filename` (no `.prg` suffix). The generator reads the petcat text and makes a binary download link from it via `petcat2prg`.

  ```html
  <div style="display: none;">
      <pre data-filename="greatprint-demo" data-name="Greatprint Demo"></pre>
  </div>
  ```

  **Do NOT** use `<div class="binary_download" data-filename="greatprint-demo.prg">` for a BASIC-classified file. Two problems with that:
  1. `prg/greatprint-demo.prg` doesn't exist (it's in `del/`), so the generator throws `BinaryDownloadError: Binary file not found`.
  2. Even if you move the `.prg` back, the `.prg` suffix forces MSE/hex rendering mode, which is wrong for BASIC content — you'd get a hex dump where a petcat text listing belongs.

  The hidden `<pre>` pattern solves both: the text renders via the `.txt` + `petcat2prg` pipeline, and nothing displays in the article body because the wrapper div is `display: none`.

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
| `data-assembler` | `"hypra-ass"` for Hypra-Ass source listings (master file is `prg/<name>.txt`), or `"top-ass"` for Top-Ass source listings (master file is `prg/<name>.prg`) |

## Rules

- **Captions must be verbatim** from the magazine scan — read from `png/*_600_cropped.png` files (scale with `magick -resize 25%` if 600dpi). When `pdftotext` and the scan disagree on a program name (typical OCR confusion in captions: `»RND«` vs `»FIND«`, `R` vs `F` in old print), **trust the article body's spelling** — the body prose mentions the name multiple times in unambiguous contexts.
- **Listings with no `Listing N.` caption.** Some short programs are referenced from the article body simply as "(Listing)" or "(Assembler-Listing)" with no number. Use a verbatim caption from the scan that matches that style (`Listing: Caption text`, `Assembler-Listing: Caption text`) — don't invent a Listing-N number that doesn't exist in the print.
- **Disk variants of the same listing** are common for multi-target programs (e.g. `block 1300_c 128.prg` and `block c000_c 64.prg` for the same BLOCK routine assembled at two load addresses). Place the main Hypra-Ass / BASIC version as the captioned `<figure>` and emit each target-address variant as a sibling `<div class="binary_download" data-filename="…" data-name="…">` immediately below. They share the article's listing slot but each gets its own download link.
- **Listings printed in the magazine but not on disk.** Some listings are printed in the magazine yet do NOT ship as a file on the disk — either because they're a one-shot pre-step that produces something else (e.g. "Listing 1. Change MSE" in Master-Text), or because the disk omitted them for space, or because the print is an assembler disassembly of an in-ROM routine. Even so, **emit a `<figure>` block with the verbatim caption and `<pre>TODO</pre>` as the body** so the gap is visible in the rendered HTML:
  ```html
  <figure>
      <pre>TODO</pre>
      <figcaption>Listing N. Caption from scan</figcaption>
  </figure>
  ```
  This signals "the printed magazine had this listing, but it's not yet transcribed". A future pass can OCR the printed listing into the `<pre>` body. Do NOT skip the figure entirely — that would silently lose the printed Listing N from the article.

- **The listings at the end of an article must be in printed Listing-number order.** When `prg_links.sh` emits `<figure>` blocks in the order it found them on the disk's directory, that order rarely matches the printed Listing N numbering. After placement, walk the article's tail-of-article listing block and reorder so the captions read `Listing 1`, `Listing 2`, `Listing 3`, … in sequence. Common case: `Listing 11` (Lader) and `Listing 12` (Install) often come off the disk reversed because the disk stores `install` before `lader` alphabetically.
- **`data-name` must be unique** within an article; two listings can't share the same `data-name`
- **`data-filename` base name max 16 chars** (C64 filename limit)
- **`.txt` header line**: must be `;filename.prg ==ADDR==` matching the base name
- **Credit external contributors**: add `;Eingetippt von Name` as first line in `.txt` files, or `<!-- Eingetippt von Name -->` comment in HTML for inline listings
- **Compiled/binary-only versions**: use only `binary_download` div, no `<pre>` display
- **Placement**: in Tips & Tricks articles, place each listing at the end of its own section, not at the end of the entire article. For other articles, all listings go at the end before `</article>`.
- **Files from external contributors** (e.g. `prg2/`): copy to `prg/`, fix header line to match filename, add credit line. For inline-only listings (Z80 asm, Pascal), embed directly in HTML.

## Cropping listing regions from the page scan (for TODO transcription)

When you need to fill a `<pre>TODO</pre>` placeholder by OCRing the printed listing, **don't guess the crop coordinates by trial-and-error.** Use the caption's bounding box from a layout-detected block file to crop the listing region in one shot.

If `_work/p<NNN>/blocks.txt` already exists (produced by the body workflow's PaddleOCR PPStructureV3 pass), grep it:

```bash
grep -i "listing" _work/p072/blocks.txt
# → block=22 bbox=825x84+195+1955 nw=12  Listing 1. Komprimierte Version ...
# → block=45 bbox=840x39+1321+3256 nw=8   Listing 2. Hier die entwirrte ...
```

The bbox `WxH+X+Y` gives you the caption's column (`X`, width `W`) and top-edge (`Y`). The listing code sits **above** the caption in the same column. To find its bbox, walk preceding blocks in `blocks.txt` and pick those whose x-range overlaps with the caption's x-range — these are blocks in the same column. The topmost code-block above the caption is your crop's top edge.

If `_work/` doesn't exist, regenerate it. The body workflow's Phase 0 PaddleOCR script produces `_work/p<NNN>/blocks.txt`, `page.tsv`, `page.hocr`, and rendered PNG scaffolds. A simpler standalone alternative for just this purpose (caption-bbox lookup) is plain tesseract:

```bash
tesseract <page>.png - -l deu tsv > /tmp/p.tsv
awk -F'\t' '$1==5 && $12 ~ /^Listing$/ {
  # word "Listing" found at column $7, row $8, in block $3
  print "block="$3" left="$7" top="$8
}' /tmp/p.tsv
```

Then group words by `block_num` to get the caption's full bbox, find adjacent code blocks above it, and crop. Tesseract's block segmentation is coarser than PaddleOCR's but suffices for caption-anchored cropping.

**One-shot crop command:**

```bash
# For listing whose code starts at (CX, CY) with size CWxCH:
magick _work/p<NNN>/page_300.png -crop <CW>x<CH>+<CX>+<CY> +repage /tmp/listing.png
# Read with vision, transcribe.
```

Add ~50 px padding on each side to be safe; tesseract block-segmentation tends to undercount whitespace at the top of code blocks.

**Why this matters:** iterative trial-and-error cropping (eyeballing `+Y` and `+H` until the image is right) costs 3–5 vision-read iterations per listing. The bbox-first approach makes the first crop right ~90% of the time, paying back the cost of one tesseract pass.

## Known `prg_links.sh` quirks

- The script's per-file moves quote filenames properly, so individual files with spaces or unusual characters survive. However if the disk's section-separator filenames begin with `-` (e.g. `--------------NN`), some shells expand the bulk-move glob into arguments `mv` interprets as options. The script has been patched to use `mv ./*` instead of `mv *` to avoid this — but if you see "Processing files with petcat..." print zero lines for a disk and the resulting `prg/` is empty, this is the symptom. Try running each `.D64` separately as a workaround.
- The `del/` subdirectory under `prg/` holds files the script decided NOT to publish as their own listing (typically: the `.prg` of a BASIC program that's been petcat-decoded to `.txt`). Don't delete `del/`; the generator may still resolve binary downloads from those files.

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

## Final report — present a summary table

After all placements, produce a summary table for the user listing what you did and what they may want to spot-check:

| Article | Listings placed | Binary companions | Notes |
|---|---|---|---|
| `55 Master-Text` | 11 (Listings 2–12) | 16 | Listing 1 (Change MSE) emitted as `<pre>TODO</pre>` — not on disk |
| `134 Von Basic zu Assembler` | 5 (Listings 1, 3–6) | 8 (BLOCK/SWAP variants) | Listing 2 (BLTUC disasm) emitted as `<pre>TODO</pre>` — disassembly of in-ROM routine, not on disk |
| `82 Tips C 128` | 5 (Listings 1–5) | — | Listing 6 (sprinv source) emitted as `<pre>TODO</pre>` — not on disk; Listing 3 was »FIND« not »RND« (OCR confusion in pdftotext) |
| … | | | |

Also flag explicitly in the report:
- Every `<pre>TODO</pre>` placeholder, with the reason (printed-but-not-on-disk, transient pre-step, in-ROM disassembly, etc.) so a future pass knows what to OCR.
- Every `(Listing N)` body reference for which you did NOT add a figure, and why (e.g. Fehlerteufelchen-column references to listings from previous issues).
- The end-of-article listing order verification (`grep -A1 '<figure>' article.html | grep figcaption | grep -oE 'Listing [0-9]+'` should print Listing-N in ascending order).
- Unplaced blocks in `prg.txt` and orphan files in `prg/` not referenced from any HTML (e.g. boot splash screens like `leser-info!`).

The user will scan this table to decide where to spot-check. Without it they'd have to grep every article.

## Generator Integration (`generate.py`)

- `prg/*.txt` → read into `listings[basename]` (text) and `listings_bin[basename]` (binary via petcat2prg)
- `prg/*.prg` → read into `listings_bin[filename]` (raw binary)
- `data-filename` without `.prg` suffix → BASIC listing path (petcat text, optional checksummer)
- `data-filename` with `.prg` suffix → MSE or binary path
- Normal BASIC rendering strips `;` comment lines, empty lines, and leading spaces
- `data-assembler="hypra-ass"` → reads `prg/<filename>.txt` (petcat-text master), re-tokenizes with `petcat2prg`, then runs `tools/assembler_decode.py` `decode_bytes(..., topass=False)` to render the assembler listing
- `data-assembler="top-ass"` → reads `prg/<filename>.prg` directly and runs `decode_bytes(..., topass=True)` (Top-Ass uses native BASIC tokenization for mnemonics)

### Hypra-Ass / Top-Ass HTML pattern

```html
<figure>
    <pre data-filename="taktzyklen.src" data-name="Taktzyklen (Quellcode)" data-assembler="hypra-ass"></pre>
    <figcaption>Caption text</figcaption>
</figure>
```

The `<pre>` body stays empty — the generator auto-decodes from `prg/<filename>.txt` (Hypra-Ass) or `prg/<filename>.prg` (Top-Ass). For Hypra-Ass also place a binary download alongside the source listing if the assembled `.prg` is also published.

### Decoder note: shifted PETSCII vs BASIC tokens

`tools/assembler_decode.py` decodes the petcat-tokenized PRG byte stream. Two byte ranges share the same numeric values but have different meanings:

- **$80–$C0**: legitimate BASIC V2 tokens (SYS, `*`, `=`, FOR, etc.). These can appear in the magazine-style BASIC starter line of the source (e.g. `100 SYS9*4096`) and must be detokenized.
- **$C1–$DA**: shifted-PETSCII uppercase letters `A`..`Z` (these are typed uppercase letters in the C64 source). They collide with the BASIC tokens `LEFT$` ($C8), `RIGHT$` ($C9), `MID$` ($CA), `GO` ($CB). In `topass=False` (Hypra-Ass) mode the decoder treats this range as PETSCII text, not tokens — otherwise `HYPRA-ASS` would decode as `LEFT$YPRA-ASS`.

If you touch this decoder, keep this split in mind: any Hypra-Ass listing with uppercase letters will hit $C1–$DA. Top-Ass mode uses a different mnemonic table ($81–$B8) and a `.` + token disambiguator for directives, so the rule does not apply there.
