#!/usr/bin/env python3
"""SH09: re-apply pdf-postfix.txt items 1 and 2 to a fresh r006 build.  Run with the repo venv.

  pdf_postfix.py <build output> <out.pdf> [<previous shipped pdf>]

1. Page order ...162, 167, 168, 163-166: the four blue order/payment leaves (scan 163-166) go after the covers.
   Pages are moved, never re-encoded; the image streams are asserted to be the build's, in the new order.
2. /Title and XMP dc:title "64'er Sonderheft 9" (exiftool), because build.sh passes "Sonderheft 09/86".
With a previous shipped file it lists the pages whose image streams differ from it.
Drop item 1 once png/ carries the corrected order, see pdf-postfix.txt.
"""
import hashlib, subprocess, sys
import pikepdf
src, out = sys.argv[1:3]


def streams(pdf):
    return [[hashlib.sha1(o.read_raw_bytes()).hexdigest() for _, o in p.images.items()] for p in pdf.pages]


with pikepdf.open(src) as pdf:
    assert len(pdf.pages) == 168, len(pdf.pages)
    pre = streams(pdf)
    for _ in range(4):
        pdf.pages.append(pdf.pages[162])
        del pdf.pages[162]
    assert streams(pdf) == pre[:162] + pre[166:168] + pre[162:166]
    pdf.save(out)
subprocess.run(["exiftool", "-q", "-overwrite_original", "-Title=64'er Sonderheft 9",
                "-XMP-dc:Title=64'er Sonderheft 9", out], check=True)
if len(sys.argv) > 3:
    with pikepdf.open(out) as a, pikepdf.open(sys.argv[3]) as b:
        sa, sb = streams(a), streams(b)
        print("pages whose image streams differ from", sys.argv[3], [i + 1 for i in range(168) if sa[i] != sb[i]])
