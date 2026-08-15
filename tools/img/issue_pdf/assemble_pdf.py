#!/usr/bin/env python3
"""Assemble per-page OCR PDFs into one issue PDF, replacing each page's image.

    assemble_pdf.py <manifest.tsv> <out.pdf> <title> <author> <creator> <icc>

WHY THIS EXISTS, when make_issue_pdf.sh already merges with Ghostscript: gs TRANSCODES any image
it does not pass through, and it passes through only JPEG. The moment one page is JBIG2, gs turns
it back into something else -- which is what stopped the 8608 MRC prototype. So a mixed document
(JBIG2 for the bilevel pages, JPEG for the rest) has to be assembled without gs, hence pikepdf.

The text layer is never touched: each input is a one-page tesseract PDF, and only its image
XObject is swapped. See swap_image.py, which does the same for the single-page JPEG case.

MANIFEST, one page per line, tab separated:

    <ocr_page.pdf>  jpeg    <image.jpg>   <width>  <height>
    <ocr_page.pdf>  jbig2   <image.jb2>   <width>  <height>

`jbig2` files must be PDF-embeddable generic-region streams -- `jbig2 -p page.pbm > page.jb2`,
WITHOUT -s. Symbol mode is a false economy here: it substitutes visually-similar symbols across
the page, which is the failure that turned 6s into 8s in scanned Xerox documents. An archival
master gets lossless generic coding even though it costs ~4x the bytes.
"""

import sys

import pikepdf
from pikepdf import Array, Dictionary, Name, String


def image_stream(pdf: pikepdf.Pdf, kind: str, path: str, w: int, h: int) -> pikepdf.Stream:
    with open(path, "rb") as fh:
        data = fh.read()
    st = pikepdf.Stream(pdf, data)
    st.Type = Name("/XObject")
    st.Subtype = Name("/Image")
    st.Width = w
    st.Height = h
    if kind == "jpeg":
        st.ColorSpace = Name("/DeviceRGB")
        st.BitsPerComponent = 8
        st.Filter = Name("/DCTDecode")
    elif kind == "jbig2":
        # NO /Decode. The spec says JBIG2Decode emits 1 = black, which reads as though DeviceGray
        # needs [1 0] to reconcile it -- but the filter already hands back 0 for the black pixels,
        # and adding the array renders every bilevel page as a photographic negative. Measured:
        # with [1 0] the proof page came back mean 0.13 (mostly black), without it 0.93.
        st.ColorSpace = Name("/DeviceGray")
        st.BitsPerComponent = 1
        st.Filter = Name("/JBIG2Decode")
    else:
        raise SystemExit(f"unknown image kind {kind!r}")
    return st


def main() -> None:
    if len(sys.argv) != 7:
        raise SystemExit(__doc__)
    manifest, out_pdf, title, author, creator, icc = sys.argv[1:]

    out = pikepdf.Pdf.new()
    n_jbig2 = n_jpeg = 0

    with open(manifest) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            src, kind, img, w, h = line.split("\t")
            page_pdf = pikepdf.open(src)
            if len(page_pdf.pages) != 1:
                raise SystemExit(f"{manifest}:{lineno}: {src} has {len(page_pdf.pages)} pages")
            page = page_pdf.pages[0]
            names = list(page.images.keys())
            if len(names) != 1:
                raise SystemExit(f"{manifest}:{lineno}: {src} has {len(names)} images")
            page.Resources.XObject[names[0]] = image_stream(
                page_pdf, kind, img, int(w), int(h)
            )
            # copy_foreign happens implicitly on append; the source stays open until then
            out.pages.append(page)
            n_jbig2 += kind == "jbig2"
            n_jpeg += kind == "jpeg"

    with open(icc, "rb") as fh:
        icc_data = fh.read()
    profile = pikepdf.Stream(out, icc_data)
    profile.N = 3
    out.Root.OutputIntents = Array(
        [
            Dictionary(
                Type=Name("/OutputIntent"),
                S=Name("/GTS_PDFA1"),
                OutputConditionIdentifier=String("sRGB"),
                Info=String("sRGB"),
                DestOutputProfile=profile,
            )
        ]
    )

    with out.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:title"] = title
        meta["dc:creator"] = [author]
        meta["pdf:Producer"] = creator
        meta["xmp:CreatorTool"] = creator
    out.docinfo[Name("/Title")] = String(title)
    out.docinfo[Name("/Author")] = String(author)
    out.docinfo[Name("/Creator")] = String(creator)

    out.save(out_pdf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    print(f"{out_pdf}: {len(out.pages)} pages, {n_jbig2} jbig2, {n_jpeg} jpeg")


if __name__ == "__main__":
    main()
