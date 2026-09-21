# 006 — The issue PDF

**Applies to:** all — every issue gets a PDF, whatever its kind or binding.

**Goal:** one searchable, archive-grade PDF of the whole issue, page N of the
PDF being printed page N, sitting in `issues/<ID>/` under the name the
descriptor's `pdf` key gives it.

**This rule does not carry the recipe.** It lives, measured and reasoned, in
[`tools/img/issue_pdf/README.md`](../../issue_pdf/README.md), beside the
scripts that implement it. Read that; this file says only *when* the step runs
in this chain, *what* it is handed, and *what* is checked afterwards.

---

## Why here — after 005, before the HTML

Its only input is the 600 dpi masters: deskewed, cut to the traced page,
filled and graded. That is step 005's output and nothing later touches it, so
the PDF can be built the moment 005 is done.

It must be built **before** the editorial chain, because several later rules
already treat the PDF's **text layer as a source to consult** — and that layer
is worth having: it is an *independent* OCR of the same pages, run by
`issue_pdf` at **402 dpi**, where this chain's step 010 reads **300 dpi**. The
`issue_pdf` README records the measurement behind that number: at 300 or 150
dpi **tesseract truncates words at the image edges**. Where the corpus shows a
column-edge truncation, the PDF's text layer very often has the word.

**It must be rebuilt whenever the grading changes.** The PDF is pixels, and
re-grading a page — a corrected profile, a second paper class, a re-cut edge —
makes every PDF page built from it stale. That is why this step sits after
005 rather than at the very start of the chain.

## The title page is made BY HAND, always

**Step 005 does not produce the published cover.** After the cover page has
been cut and graded like any other page, the issue owner takes it and makes a
cleaned-up `title.png` **at 150 dpi** — retouching whatever the scan of a
glossy cover leaves behind. That file:

- goes into `issues/<ID>/title.png`, where the site generator reads it, **and**
- **is page 1's image in the PDF.** It is not re-derived from the master; the
  cleaned file IS the 150 dpi master for that page.

Every other page of the PDF is exactly what step 005 produced, reduced by the
`issue_pdf` recipe. The cover is the one page a human touches.

So this step BLOCKS on that hand-off: if `issues/<ID>/title.png` is missing,
or older than the cover master it should have been made from, the PDF is not
ready to build. Ask for it; do not substitute the raw master, because then the
published PDF and the published cover image disagree about what the cover
looks like.

**AND THE COVER MUST BE HANDED TO THE BUILD EXPLICITLY.** `make_issue_pdf.sh`
defaults `TITLE_PNG` to `$IN/title.png` — the **scans** directory — and the
cover lives in the **repo**, `issues/<ID>/title.png`. Those are never the same
place. Always pass it:

```sh
TITLE_PNG=<repo>/issues/<ID>/title.png tools/img/issue_pdf/make_issue_pdf.sh ...
```

MEASURED on SH8601, and this is why both scripts now refuse to build without
one: the default pointed at a file that does not exist, so `[[ -f "$TITLE_PNG" ]]`
was simply false and page 1 fell through to the machine reduction of the cover
master. **A 152-page PDF shipped with the wrong cover and every check passed.**
The loud guard beside that branch (`EXACT SIZE OR STOP`) only fires when the
file IS found, so a missing cover was the one case that said nothing.

Two further traps found with it, both now closed in the scripts:

- the 150 dpi cache is keyed on **existence** (`[[ -s "$CACHE/NNN_150.png" ]] &&
  continue`), so a cover retouched after the last build never reached the PDF.
  Page 1's cache entry is now invalidated by a newer `title.png`.
- **the mixed build does not make the 150 dpi pages at all** — it consumes the
  plain script's cache. It now compares page 1's cached pixels against
  `title.png` (MAE ≤ 1) and refuses to assemble otherwise.

## THE PAGE INPUTS ARE REVIEWED BEFORE THE PDF IS COMPILED — ALWAYS

**Do not compile until the issue owner has looked at the exact files that will
be embedded and said they are good.** Not the masters, not a sample, not a
uniform rendering of them — the embedded images themselves.

**They are not all the same resolution, and the review must show each page as
it will ship.** The mixed build sends each page down one of two paths:

| page | what is embedded | what to show |
|---|---|---|
| carries colour | 150 dpi guetzli raster | the 150 dpi file |
| black ink only | 600 dpi lossless JBIG2 bilevel | the 600 dpi bilevel |

MEASURED on SH8601: 48 of 152 pages are colour-free (098-146 minus 117, one
contiguous block — the listing and reference back half), so nearly a third of
the issue ships at 600 dpi bilevel. Reviewing those at 150 dpi greyscale shows
the owner something the reader will never see, and hides exactly the defects
bilevel conversion introduces — a thin rule dropped, halftone gone to noise,
type thinned at the threshold.

This is not a formality and it is not conditional on how the run went:

- the compile is expensive (hours, with a quality binary search over the whole
  issue) and every defect found afterwards costs the whole build again;
- a grading or cutting mistake is obvious at 150 dpi and invisible in a log;
- the cover is hand-made and must be checked in the same pass, since it is
  page 1's image rather than a re-derivation.

**How to present them:** the prepared 150 dpi pages, in page order, as files the
owner can open — plus a contact sheet for the sweep. Say where they are on
disk. Then WAIT. A build started without that review is to be stopped, not
finished; SH8601's first two builds were.

## The PDF's metadata is a house standard — and it is NOT set by the scripts

The 38 published issue PDFs in `issues/*/` agree on four things, across three
different producing toolchains and eighteen years of files. That agreement is
the standard; it was never written down, so this is where it lives now.

### The four fields the corpus fixes

| field | value | evidence |
|---|---|---|
| `/Title` (DocInfo) **and** `dc:title` (XMP) | monthly `64'er MM/YY`; **Sonderheft `64'er Sonderheft NN/YY`** | 30/30 monthlies, 8/8 Sonderhefte |
| `/Author` (DocInfo) | `Markt & Technik` | 38/38 |
| `/Subject`, `/Keywords` | **absent — never written** | 0/38 carry either |
| `/CreationDate` = `/ModDate` | the build's own timestamp | 37/38 (`8609` is the only file without them) |

**The title names the Sonderheft's number within its year, zero-padded, over a
two-digit year — and nothing else.** `64'er Sonderheft 01/85` … `08/85`, one
per Sonderheft of 1985, in the same shape as the monthly's `64'er 08/85`. It
does **not** carry the theme, the long year, or the repo's `SH` prefix. That is
also how the archive's own index names them: `Gesamtinhaltsverzeichnis
Sonderhefte.csv` cites a Sonderheft article as `1/86`. So `SH8601` is
`64'er Sonderheft 01/86`.

The reason the shape matters: `64'er ` + issue tag is the only string a reader,
a library catalogue or a file manager ever sees for the document, and it is the
one place a monthly and a Sonderheft of the same month are told apart. `64'er
01/86` and `64'er Sonderheft 01/86` are two different 1986 issues; `64'er SH
1/86` sorts and reads as neither.

**Subject and Keywords are deliberately empty.** Not one file in the corpus
sets them — not the 2008 ABBYY 9 file, not the 2025 ABBYY runs, not our own
builds. Do not start now: a keyword list nobody maintains ages into a lie, and
the article-level metadata that would populate it already lives in the HTML.

### The fields the corpus leaves to the tool — do not standardise them

`/Creator`, `/Producer`, `dc:format`, `pdfaid:*`, `xmpMM:DocumentID` and
`/Lang` are whatever the producing tool wrote, and they disagree across the
corpus precisely because the tools do:

| producer | `/Creator` | `/Producer` | `pdfaid` |
|---|---|---|---|
| ABBYY FineReader PDF (most of the corpus) | `ABBYY FineReader PDF` | — | part 3 / conformance A |
| `8404` (2008) | — | `ABBYY FineReader 9.0 Professional Edition` | part 1 / A |
| `SH8507` (pdftk re-assembly) | `pdftk-java 3.3.3` | `itext-paulo-155 …` | — |
| `8608` (our gs build) | `tesseract 5 + guetzli + Ghostscript` | `GPL Ghostscript 10.07.1` | part 3 / **B** |
| `8609`, `SH8601` (our mixed build) | `tesseract 5 + guetzli + jbig2enc + pikepdf` | same | — |

`/Creator` names the toolchain **honestly** — that is the rule the scripts
already follow (`CREATOR="tesseract 5 + guetzli + Ghostscript"  # honest`), and
it is why the mixed build's string differs from the plain build's. Leave it
alone. Likewise `pdfaid`: its absence on a mixed build is correct and already
argued for above — the file is not PDF/A and must not claim to be.

`/Lang` is an ABBYY artefact and is not even self-consistent there (`de-DE` on
`SH8502`/`SH8508`, `en-US` on `SH8501`/`SH8503`–`SH8506` — for German
magazines). Our builds set none. Nothing to copy.

### What the build scripts actually set

**The Sonderheft-vs-monthly distinction is not in the scripts at all.** Both
build scripts hold

```sh
TITLE="64'er $TAG"        # $TAG is argv[3], typed by the operator
AUTHOR="Markt & Technik"
```

and neither reads `issue.json`, so nothing knows an `SH…` issue is a
Sonderheft. **The tag you type IS the standard being applied or broken.** For a
Sonderheft it must be `"Sonderheft 01/86"`, not `"SH 1/86"`.

| field | `make_issue_pdf.sh` (gs, PDF/A) | `make_issue_pdf_mixed.sh` → `assemble_pdf.py` (pikepdf) |
|---|---|---|
| DocInfo `/Title` | pdfmark `/DOCINFO`, then **re-set with `exiftool`** — gs's PDF/A pass silently drops it | `out.docinfo[/Title]` |
| DocInfo `/Author` | pdfmark `/DOCINFO` | `out.docinfo[/Author]` |
| DocInfo `/Creator` | pdfmark `/DOCINFO` | `out.docinfo[/Creator]` |
| DocInfo `/CreationDate`, `/ModDate` | pdfmark `/DOCINFO`, `$NOW` | **NOT SET** |
| XMP `dc:title` | `exiftool -XMP-dc:Title` | `meta["dc:title"]` |
| XMP `dc:creator` | gs, from `/Author` | `meta["dc:creator"] = [author]` |
| XMP `pdf:Producer`, `xmp:CreatorTool` | gs | set explicitly |
| XMP `xmp:CreateDate`/`ModifyDate`/`MetadataDate` | gs | **NOT SET** |
| XMP `dc:format`, `pdfaid`, `xmpMM:*` | gs's PDF/A machinery | **NOT SET** |
| `/Subject`, `/Keywords` | never | never |

So: **`Title` and `Author` are automatic and correct only if the tag is
correct; the dates are automatic on the plain build and simply missing on the
mixed build.** Nothing else is set by hand today, and nothing validates any of
it — which is how `SH8601` shipped as `64'er SH 1/86`.

**The mixed build's missing dates are a real gap, not a choice.** Every other
published file in the archive says when it was made; `8609` and `SH8601` are
the two that do not, and both came out of `assemble_pdf.py`. Until the script
writes them, set them by hand with the file's own mtime.

### Verification

```sh
pdfinfo "$PDF" | grep -E '^(Title|Author|Subject|Keywords|CreationDate|ModDate):'
```

- `Title` is `64'er Sonderheft NN/YY` (Sonderheft) or `64'er MM/YY` (monthly),
  and `pdfinfo -meta` shows the same string in `dc:title`
- `Author` is `Markt & Technik`
- no `Subject`, no `Keywords`
- `CreationDate` and `ModDate` present and equal

### Fixing a shipped file without re-encoding it

`exiftool` writes a PDF as an **incremental update** — it appends a new trailer
and leaves every existing object, including all 152 page images, byte-for-byte
alone. It is the same tool `make_issue_pdf.sh` already uses for the title, so
this is not a foreign edit. Measured on `SH8601`'s delivery: 98,568,266 →
98,572,396 bytes, +4,130 bytes, and `Author`/`Creator`/`Producer`/
`xmp:CreatorTool` all survived untouched.

```sh
T="64'er Sonderheft 01/86"
D="2026:08:23 07:29:50+02:00"        # the file's own mtime
exiftool -overwrite_original \
  -Title="$T" -XMP-dc:Title="$T" \
  -PDF:CreateDate="$D" -PDF:ModifyDate="$D" \
  -XMP-xmp:CreateDate="$D" -XMP-xmp:ModifyDate="$D" "$PDF"
```

Never re-run the build for a metadata fix: the guetzli quality search is hours,
and a rebuild changes the pixels for nothing.

## RE-CUTTING A PAGE MEANS RE-OCR'ING IT — the OCR layer carries the geometry

**The PDF's page box comes from `.ocrcache/NNN.pdf`, not from the PNG.** So a
page that is re-cut to a different size and rebuilt WITHOUT re-running its OCR
keeps its OLD box, and the build reports success.

MEASURED on SH8601: after step 005b unified the four Zahlkarte pages to one
size, two consecutive rebuilds emitted a PDF whose insert pages were still
407.5 / 408.5 / 409.3 / 409.6 pt wide — the byte count did not change at all,
which is the only visible sign that nothing happened.

Three caches sit behind a page, and **all of them are keyed on existence**, so
a re-cut invalidates none of them by itself:

| cache | what it holds | when it must be dropped |
|---|---|---|
| `.ocrcache/NNN.pdf` | the OCR text layer **and the page box** | the page was re-cut, at all |
| `.ocrcache/NNN_150.png` | the 150 dpi raster | the page's pixels changed |
| `.ocrcache/<enc>-q<N>/NNN.jpg`, `NNN_g.pdf`, `merged.pdf`, `out.pdf` | the encoded page and the assembly | either of the above changed |

Re-OCR exactly the affected pages with the recipe's own parameters — they are
one line in `make_issue_pdf.sh`: `-resize 67%`, `-l deu --psm 3 --oem 3 --dpi
402`.

**And check for hardlinks first.** A comparison tree built by copying the cache
may share inodes with the delivery's (`stat -f%l` reports the link count):
writing into one then silently rewrites the other. Unlink before regenerating —
`rm` the entry and make a new file, never edit in place.

## Inputs

- `<tmp>/masters600/NNN.png` — every page of the issue, 600 dpi
- `issues/<ID>/title.png` — **required**, and hand-made: page 1's image, see above
- `issues/<ID>/issue.json` — `pages` for the page count, `pdf` for the output name

## Run

```sh
tools/img/issue_pdf/make_issue_pdf.sh <masters600 dir> <out.pdf> "<issue tag>"
```

**`make_issue_pdf_mixed.sh` with `MODE=allbw` IS THE DEFAULT BUILD**, decided
on 8609 (2026-08-15) and re-confirmed on 8610. It ships every colour-free page
as 600 dpi lossless JBIG2 -- halftone or not -- and the rest as 150 dpi
guetzli. `MODE=nohalftone` converts only the colour-free pages with no
halftone; reach for it when an issue's photographs matter more than its type.

The plain `make_issue_pdf.sh` is **not** the way an issue ships. It has one job
here: it builds the OCR cache and the 150 dpi rasters the mixed build consumes
(procedure step 2 below). Shipping from it does not fit a full issue and the
arithmetic says so twice:

| | pure guetzli at its q84 floor | mixed, `allbw` |
|---|---|---|
| 8609, 176 pages | **103.31 MB -- did not fit** | 96.15 MB at q95 |
| 8610, 200 pages | **103.64 MB -- did not fit** | see this issue's LOG |

The 100 MB ceiling is a hard limit and is not negotiable, and guetzli below
q84 smears the halftone, so on a long issue there is nothing left to give: the
bytes have to come from the bilevel pages instead. 8610 measured **118 of its
200 pages colour-free**, 57.3 MB of the 99.1 MB JPEG payload -- which is the
prize the mixed build collects.

### The whole procedure, in order

Written out because SH8601 was rebuilt SIX times before it was right, and every
wrong build looked like a success. `<tmp>` is the issue's tmp dir, `<A4>` the
delivered A4 pages (`<tmp>/a4600`), `<repo>` this repository.

**1. The pages must be the ones the owner reviewed** — see the review rule
above. The A4 cut comes from step 005b, and re-cutting anything means going
through step 3 below for those pages.

**2. Build the OCR cache and the 150 dpi rasters — WITH THE COVER.** The
default `TITLE_PNG` points into the scans dir, where the cover does not live;
pass it explicitly or the build now refuses:

```sh
TITLE_PNG=<repo>/issues/<ID>/title.png \
  tools/img/issue_pdf/make_issue_pdf.sh <A4> <tmp>/scratch.pdf "<tag>"
```

This populates `<A4>/.ocrcache/`, which is what the mixed build consumes. Its
own output PDF is a by-product here.

**3. If any page was re-cut after that, refresh ITS THREE CACHES** — the OCR
layer carries the page box, so skipping it silently keeps the old geometry (see
the section above). For each affected page `NNN`:

```sh
magick <A4>/NNN.png -resize 25% +repage -strip <A4>/.ocrcache/NNN_150.png
rm -f <A4>/.ocrcache/NNN.pdf                 # unlink: it may be a hardlink
magick <A4>/NNN.png -resize 67% +repage -strip <A4>/.ocrcache/NNN_o.png
tesseract <A4>/.ocrcache/NNN_o.png <A4>/.ocrcache/NNN \
          -l deu --psm 3 --oem 3 --dpi 402 pdf
rm -f <A4>/.ocrcache/NNN_o.png \
      <A4>/.ocrcache/guetzli-q<N>/NNN.jpg <A4>/.ocrcache/guetzli-q<N>/NNN_g.pdf \
      <A4>/.ocrcache/guetzli-q<N>/merged.pdf <A4>/.ocrcache/guetzli-q<N>/out.pdf
```

**4. Assemble.** `QMIN=QMAX=<q>` pins the quality to one encode instead of the
multi-hour binary search — use it for a rebuild whose q is already known, and
let the search run for a first build or after a grading change:

```sh
TITLE_PNG=<repo>/issues/<ID>/title.png QMIN=95 QMAX=95 \
  tools/img/issue_pdf/make_issue_pdf_mixed.sh <A4> <tmp>/<name>.pdf "Sonderheft NN/YY"
```

Watch for `[cover] page 001 carries .../title.png (N grey levels)` in the log.
Its absence means the build died — check the log, not the exit status of a
pipeline.

**5. Stamp the metadata.** The scripts write no dates and take the title from
argv, so the house standard is applied afterwards (exiftool writes an
incremental update — no re-encode, ~4 KB):

```sh
D=$(date -r <tmp>/<name>.pdf "+%Y:%m:%d %H:%M:%S%z" | sed 's/\(..\)$/:\1/')
T="64'er Sonderheft NN/YY"          # or "64'er MM/YY" for a monthly
exiftool -overwrite_original -Title="$T" -XMP-dc:Title="$T" \
  -Author="Markt & Technik" \
  -PDF:CreateDate="$D" -PDF:ModifyDate="$D" \
  -XMP-xmp:CreateDate="$D" -XMP-xmp:ModifyDate="$D" <tmp>/<name>.pdf
```

**6. Run the Verification below**, then copy it into the repo under the name
`issue.json`'s `pdf` key gives — that name and no other, because `generate.py`
looks it up there:

```sh
cp <tmp>/<name>.pdf <repo>/issues/<ID>/$(python3 -c \
   "import json;print(json.load(open('<repo>/issues/<ID>/issue.json'))['pdf'])")
```

**Never `git add -A` an issue directory to commit it.** That is how SH8601's
first, worst build entered history: a 99.8 MB PDF with the wrong cover and the
wrong insert geometry, swept in by a wildcard add. Add the path explicitly, and
look at `git status` first.

## Verification

1. **Page count** — the PDF has exactly `issue.json`'s `pages` pages, and page
   N carries printed page N. `generate.py` slices each article's PDF out of
   this file using its `64er.pages` range, so an off-by-one here silently
   gives every article the wrong pages.
2. **The text layer is real** — extract text from a handful of pages spread
   across the issue and confirm each is non-empty and is that page's text, not
   the previous one's.

   **REAL AND PAGE-CORRECT IS THE WHOLE TEST. It is NOT expected to be clean,
   and its errors are NOT a defect to fix.** This layer is raw tesseract over
   the page image — nothing edits it, and it never sees the corrected
   transcription the editorial chain produces. On SH8601's p016 it reads
   `er C128 im professionellen` and `Spitznamenhaterauchschon` where the
   published article correctly reads `Der C 128 im professionellen` and
   `Einen Spitznamen hat er auch schon` — a lost drop cap and lost word spaces
   that were repaired in the HTML and, by design, not in the PDF.

   r000's cross-cutting rule *the PDF's text layer is a CANDIDATE SOURCE, not
   authority* is the reason: it exists to generate candidates for damaged
   words, and **is never quoted as what the print says.** So do not read a
   mangled sentence in it as a finding, do not "fix" it, and do not propose
   deriving it from the finished HTML as if the mismatch were a bug — the two
   artefacts are produced differently on purpose. The HTML is the transcription;
   the PDF is the paper, with a search aid attached.

   **2a. PAGE 1 IS THE HAND-MADE COVER — COMPARE PIXELS, NOT SHAPE.** Extract
   page 1's image and diff it against `issues/<ID>/title.png`:

   ```sh
   pdfimages -f 1 -l 1 -png "$PDF" /tmp/cover && \
     magick compare -metric MAE /tmp/cover-000.png issues/<ID>/title.png null:
   ```

   A few grey levels is JPEG error and passes; anything more is a different
   image. **"1240x1754 /DCTDecode" is NOT this check** — the machine-derived
   page has exactly that size and codec, which is precisely how SH8601's wrong
   cover passed review. Measured there: the shipped page 1 differed from the
   hand-made cover by MAE 4676 while matching the derived cache file to 2.49.
3. **Size** — under the 100 MB ceiling the build targets.

   **The shipped PDF is NOT PDF/A, and that is expected.** The mixed build
   ships the issue's colour-free pages as 600 dpi lossless JBIG2, and `gs`
   passes through only JPEG, so PDF/A conformance and JBIG2 cannot both hold.
   Image quality wins: MEASURED on SH8601, 48 of 152 pages carry no colour,
   and shipping those as JBIG2 costs 264 KB a page against ~620 KB for guetzli
   at a QUARTER the resolution — which buys nine quality steps on the other
   104 pages, q95 against q86. Do not "fix" this by switching to the plain
   build; a plain PDF/A build exists and is the worse artefact.
4. **THE DELIVERED PDF IS EXACT A4 — 210 x 297 mm, every page OF THE ISSUE.**

   **A bound-in insert that is physically smaller keeps its own size**, as an
   image and as a PDF page. SH8601's Zahlkarte (149-152) measures ~144 x 205
   mm: padding it onto A4 would fabricate 53% of the page and tell the reader
   the card is A4-sized, which it is not.

   **AND EVERY PAGE OF THAT INSERT IS THE SAME SIZE AS THE OTHERS** — check it
   in the delivered PDF, not only in the masters. SH8601's first delivery shipped
   its four Zahlkarte pages at 407.5, 408.5, 409.3 and 409.6 pt wide by 579.4,
   580.1, 581.6 and 576.9 tall: one card, four sizes, because each side was
   traced independently. Step 005b now unifies a contiguous insert run to the
   max of its own pages; a PDF whose insert pages differ from one another means
   that pass did not run. The issue's own leaves are A4; an
   insert is what it is, and its measured size is recorded in the stamp.

   ```
   600 dpi   4961 x 7016 px
   150 dpi   1240 x 1754 px      <- the size every issue's title.png already is
   ```


   That is the archive's geometry and it does not vary by issue or by sheet.
   Step 005 measures what each sheet physically is — this issue's interior
   sheets run 209.2-212.1 x 296.0-298.6 mm, the cover leaf is 223 mm wide
   with its fold flap, the Zahlkarte is 144 x 205 mm — and that measurement
   stays in the master, which is the record of the paper. **Delivery is
   uniform:** crop to the page box, then fit exact A4 — pad a sheet that
   measures short, trim the cover leaf's flap at the trimmed-page edge,
   centre an insert smaller than A4.

   Everything downstream assumes it: `issue_pdf`'s own self-check asserts
   "page still A4", `generate.py` slices article PDFs by page range, and the
   hand-made cover is 1240 x 1754 exactly because that is A4 at 150 dpi.

5. **Build from the PAGE BOX, not the canvas.** Step 005
   writes each master on a uniform canvas with the traced page anchored
   top-left and the rest fabricated paper white. That padding must NOT reach
   the PDF: crop every page to its own `page-px` box, which its stamp records.

   Two things go wrong otherwise, both MEASURED on SH8601's first build:
   every one of the 152 pages carried a fabricated white band down the right
   and along the foot; and page 1 came out 1364×1795 at 25% where the
   hand-made `title.png` is 1240×1754, so the script refused the cover
   rather than distort it and the issue shipped with the raw master as its
   cover. Cropped to the page box, page 1 reduces to 1240×1747 — the
   convention every issue's cover already uses.
6. **Freshness** — no page of the PDF predates the master it was built from.
   The masters carry their grade in a `pNNN.stamp.txt` and a PNG `tEXt`
   chunk; if a master has been re-graded since the PDF was built, the PDF is
   stale and must be rebuilt.

## Recorded in LOG.md

Which script was used, the guetzli quality the size search landed on, the
final size, and — if any page was excluded or substituted — which and why.
