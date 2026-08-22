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

## Inputs

- `<tmp>/masters600/NNN.png` — every page of the issue, 600 dpi
- `issues/<ID>/title.png` — **required**, and hand-made: page 1's image, see above
- `issues/<ID>/issue.json` — `pages` for the page count, `pdf` for the output name

## Run

```sh
tools/img/issue_pdf/make_issue_pdf.sh <masters600 dir> <out.pdf> "<issue tag>"
```

Use `make_issue_pdf_mixed.sh` where the issue has a substantial number of
pages carrying only black ink: it ships those as 600 dpi lossless JBIG2 and
the rest as 150 dpi guetzli. The plain script ships every page at 150 dpi
guetzli, quality binary-searched to land under 100 MB.

## Verification

1. **Page count** — the PDF has exactly `issue.json`'s `pages` pages, and page
   N carries printed page N. `generate.py` slices each article's PDF out of
   this file using its `64er.pages` range, so an off-by-one here silently
   gives every article the wrong pages.
2. **The text layer is real** — extract text from a handful of pages spread
   across the issue and confirm each is non-empty and is that page's text, not
   the previous one's.
3. **Size** — under the 100 MB ceiling the build targets.

   **The shipped PDF is NOT PDF/A, and that is expected.** The mixed build
   ships the issue's colour-free pages as 600 dpi lossless JBIG2, and `gs`
   passes through only JPEG, so PDF/A conformance and JBIG2 cannot both hold.
   Image quality wins: MEASURED on SH8601, 48 of 152 pages carry no colour,
   and shipping those as JBIG2 costs 264 KB a page against ~620 KB for guetzli
   at a QUARTER the resolution — which buys nine quality steps on the other
   104 pages, q95 against q86. Do not "fix" this by switching to the plain
   build; a plain PDF/A build exists and is the worse artefact.
4. **THE DELIVERED PDF IS EXACT A4 — 210 x 297 mm, every page.**

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
