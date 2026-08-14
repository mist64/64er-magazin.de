# issue_pdf — scans to a searchable, archive-grade issue PDF

Takes a folder of 600 dpi page scans and produces one searchable PDF/A-3B per issue, sized to land
just under 100 MB. Built and measured on issue 8608 (168 pages, landed q85 = 98.99 MB); moved into
the repo 2026-08-14 so it stops living in a working directory.

```sh
./make_issue_pdf.sh <input_dir> <output.pdf> <issue_tag>
./make_issue_pdf.sh ~/DNB/8609/tmp/master600/final 64er_1986-09.pdf "09/86"
```

`input_dir` holds `001…NNN` as `.tiff` or `.png` at 600 dpi A4, plus an optional `title.png` used
as page 1's image (a cleaned cover). Everything is cached under `<input_dir>/.ocrcache`, so
re-running to re-tune quality only redoes the guetzli encode.

## The two resolutions

They look like an inconsistency and are not — this is the one design decision in the whole script:

* **OCR reads 402 dpi** (the 600 dpi page at 67%), tagged `--dpi 402`. Measured on 8608: at 300 or
  150 dpi tesseract **truncates words at the image edges**. The higher render costs only time.
* **The delivered image is 150 dpi** (25%), guetzli-encoded — perceptual JPEG, far better per byte
  than `-quality`.

`swap_image.py` puts the 150 dpi JPEG into the 402 dpi page PDF, replacing only the image XObject
stream. The text layer, its word boxes and the page geometry are untouched, because PDF draws an
image into a unit square scaled by the CTM — a different pixel count lands on the same page area.

## Stages

1. **OCR** — `magick -resize 67%` → `tesseract -l deu --psm 3 --oem 3 --dpi 402 … pdf`, one
   searchable single-page PDF per page, cached.
2. **Rasters** — `magick -resize 25%` → 150 dpi PNG per page, cached. Page 1 takes `title.png`
   instead, resized to page-1 dimensions.
3. **Size search** — binary search over guetzli quality 84…97 for the largest that keeps the final
   PDF/A under 100 MB. Each probe encodes, swaps, merges and PDF/A-converts; all of it is cached
   per quality, so a probe that was already run is free.
4. **Merge and convert** — `gs -sDEVICE=pdfwrite -dAutoRotatePages=/None -dPassThroughJPEGImages=true`,
   then a second `gs` pass with `-dPDFA=3` and an sRGB OutputIntent.
5. **Title** — set with exiftool afterwards; see below.

## Things that were learned the expensive way

* **Never rotate.** `-dAutoRotatePages=/None` on every `gs` invocation. Some pages (e.g. 8609 p003,
  the tear-out reply card) are printed sideways *in the magazine* — that is content, not a scan
  defect, and OCR returning gibberish for them is correct behaviour, not a bug to "fix" by rotating.
* **gs PDF/A silently drops the DOCINFO `/Title`.** Author, Creator and the dates survive; Title
  does not. It is set afterwards with exiftool, which keeps the file PDF/A-3B and is the same tool
  the archive's own files use for XMP.
* **PDF/A-3B, not 3A.** Ghostscript cannot produce tagged/3A output. The archive's ABBYY files are
  3A; ours are not, and claiming otherwise in metadata would be false.
* **JBIG2 and JPEG 2000 are not viable through this pipeline.** `gs` transcodes any non-JPEG image
  — there is no JPX or JBIG2 passthrough — so an MRC-style build needs a hand-rolled pikepdf
  assembler instead of `gs`. See `scan2mrc/` for that line of work.
* **`gs`'s JPEGQ flag is ignored** (it re-encodes as FLATE). Use the distiller QFactor param, or do
  what this script does and control size with guetzli before `gs` ever sees the image.
* **Do not log through `>(tee …)`.** A tee child makes a bare `wait` deadlock, which is why the
  script redirects straight to a file.
* **guetzli is slow** — minutes per megapixel. The per-quality cache is what makes the binary
  search bearable; do not clear it casually.

## Dependencies

`tesseract` (with `deu`), `guetzli`, `ghostscript`, `imagemagick`, `exiftool`, `poppler`
(`pdfinfo`/`pdftotext`), and a Python with `pikepdf` + `Pillow` — the script finds the ocrmypdf
formula's interpreter (`/opt/homebrew/Cellar/ocrmypdf/*/libexec/bin/python`), newest first.

`swap_image.py` was **reconstructed** on 2026-08-14: the original was lost with its working
directory, and this is written back from the contract the builder calls it with. It verified
correct on 8609 p003 — 8.2 MB → 288 KB, image replaced as `1240x1754 /DCTDecode /DeviceRGB`, text
layer byte-identical, page still A4. It has a self-check:

```sh
"$PYBIN" swap_image.py verify out.pdf     # image dims/filter/colourspace + content stream size
```
