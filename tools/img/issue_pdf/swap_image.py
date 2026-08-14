#!/usr/bin/env python3
"""Swap the page image of a one-page tesseract PDF, keeping its text layer.

    swap_image.py <in.pdf> <image.jpg> <out.pdf>

WHY THIS EXISTS. The OCR text layer and the visible image want different resolutions: tesseract
reads best at ~402 dpi (see README), while 150 dpi is all the delivered picture needs. Re-running
tesseract on the 150 dpi raster to get a smaller file would cost accuracy; re-rendering the PDF
would cost the text layer. So tesseract renders the page at 402 dpi, and this replaces ONLY the
image XObject stream with the guetzli-encoded 150 dpi JPEG. Text layer, word boxes and page
geometry are untouched -- PDF draws an image into a unit square scaled by the CTM, so a different
pixel count lands on exactly the same page area.

RECONSTRUCTED 2026-08-14. The original lived beside the 8608 builder and was lost; this is written
back from the contract the builders call it with. Run it through `verify` below after any change.

Needs pikepdf and Pillow. The ocrmypdf formula ships both:
    /opt/homebrew/Cellar/ocrmypdf/*/libexec/bin/python
"""

import sys

import pikepdf
from PIL import Image

# JPEG colour spaces we can name in the PDF. Anything else (CMYK JPEG, 16-bit) is refused rather
# than guessed at -- a wrong /ColorSpace renders as garbage colour, silently.
PIL_MODE_TO_PDF = {
    "RGB": "/DeviceRGB",
    "L": "/DeviceGray",
}


def swap(in_pdf: str, jpeg_path: str, out_pdf: str) -> None:
    with Image.open(jpeg_path) as im:
        if im.format != "JPEG":
            raise SystemExit(f"{jpeg_path}: expected a JPEG, got {im.format}")
        width, height = im.size
        try:
            colorspace = PIL_MODE_TO_PDF[im.mode]
        except KeyError:
            raise SystemExit(f"{jpeg_path}: unsupported JPEG mode {im.mode!r}")

    with open(jpeg_path, "rb") as fh:
        jpeg = fh.read()

    pdf = pikepdf.open(in_pdf)
    if len(pdf.pages) != 1:
        raise SystemExit(f"{in_pdf}: expected 1 page, got {len(pdf.pages)}")
    page = pdf.pages[0]

    # tesseract writes exactly one image per page. More than one means the input is not what this
    # was built for, and picking one of them would be a guess -- so stop.
    names = list(page.images.keys())
    if len(names) != 1:
        raise SystemExit(f"{in_pdf}: expected 1 image XObject, found {len(names)}: {names}")

    stream = pikepdf.Stream(pdf, jpeg)
    stream.Type = pikepdf.Name("/XObject")
    stream.Subtype = pikepdf.Name("/Image")
    stream.Width = width
    stream.Height = height
    stream.ColorSpace = pikepdf.Name(colorspace)
    stream.BitsPerComponent = 8
    # DCTDecode = the JPEG stays JPEG. Re-encoding here would undo the point of guetzli.
    stream.Filter = pikepdf.Name("/DCTDecode")

    page.Resources.XObject[names[0]] = stream
    pdf.save(out_pdf)


def verify(pdf_path: str) -> None:
    """Print what a swapped page ended up with: image size, filter, and whether text survived."""
    pdf = pikepdf.open(pdf_path)
    page = pdf.pages[0]
    for name, img in page.images.items():
        print(f"{name}: {int(img.Width)}x{int(img.Height)} {img.Filter} {img.ColorSpace}")
    text = pdf.pages[0].obj.get("/Contents")
    print(f"contents stream: {len(bytes(text.read_bytes())) if text is not None else 0} bytes")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "verify":
        verify(sys.argv[2])
    elif len(sys.argv) == 4:
        swap(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
