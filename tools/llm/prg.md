# Adding Listings (PRG) to Article HTMLs

## Workflow

1. Run `tools/prg_links.sh` on the `.D64` disk image → produces `prg.txt` with HTML snippets and extracts files to `prg/`
2. Fill in placeholder values (`XXXXXXXXXXXX`, `YYYYYYYYYYYYY`) with correct `data-name` and captions
3. Insert listing snippets into the correct HTML articles
4. For listings not on disk (manually typed), files may come separately (e.g. `prg2/` directory)

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

## Generator Integration (`generate.py`)

- `prg/*.txt` → read into `listings[basename]` (text) and `listings_bin[basename]` (binary via petcat2prg)
- `prg/*.prg` → read into `listings_bin[filename]` (raw binary)
- `data-filename` without `.prg` suffix → BASIC listing path (petcat text, optional checksummer)
- `data-filename` with `.prg` suffix → MSE or binary path
- Normal BASIC rendering strips `;` comment lines, empty lines, and leading spaces
- `data-hypraass` → preserves assembler formatting (implementation in progress via `tools/hypra_ass_decode.py`)
