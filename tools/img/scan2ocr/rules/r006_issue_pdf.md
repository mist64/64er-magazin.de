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

## Inputs

- `<tmp>/masters600/NNN.png` — every page of the issue, 600 dpi
- `issues/<ID>/title.png` — optional, used as page 1's image (a cleaned cover)
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
3. **Size** — under the 100 MB ceiling the build targets, and PDF/A.
4. **Page geometry** — every page the same size. Note that this chain's
   masters sit on a uniform canvas that is slightly larger than A4 (the
   traced page is anchored top-left on it), so the PDF's page size is the
   canvas, not 210×297 mm. That is expected; what matters is that it is
   *uniform*.
5. **Freshness** — no page of the PDF predates the master it was built from.
   The masters carry their grade in a `pNNN.stamp.txt` and a PNG `tEXt`
   chunk; if a master has been re-graded since the PDF was built, the PDF is
   stale and must be rebuilt.

## Recorded in LOG.md

Which script was used, the guetzli quality the size search landed on, the
final size, and — if any page was excluded or substituted — which and why.
