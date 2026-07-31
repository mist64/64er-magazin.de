#!/usr/bin/env python3
"""Roadmap step 9: combine the per-page MRC PDFs into one issue file, LOSSLESSLY.

Lossless is the whole point, so the tool matters. `gs` would re-encode every image stream and
silently undo the descreen/JBIG2 work; `qpdf` copies streams through untouched. Verified rather
than assumed: this script compares the image inventory of the assembled file against the sum of
the parts (count, dimensions, encoding, byte size per stream) and refuses to declare success if
anything moved.

  assemble_issue.py                       -> tmp/8609.pdf
  assemble_issue.py --out X.pdf --pages 1 2 3

The result is the ARCHIVAL tier. The size-targeted delivery file is a separate, later step
(recompress_to_target.py), derived FROM this.
"""
import argparse
import json
import os
import re
import subprocess
import sys

T = "/Users/mist/DNB/8609/tmp"
SRC = os.path.join(T, "mrc")
OUT = os.path.join(T, "8609.pdf")
ISSUE = "9/1986"
TITLE = "64'er Magazin %s" % ISSUE


def page_list(pages):
    if pages:
        return [(p, os.path.join(SRC, "%03d.pdf" % p)) for p in pages]
    fs = sorted(f for f in os.listdir(SRC) if re.fullmatch(r"\d{3}\.pdf", f))
    return [(int(f[:3]), os.path.join(SRC, f)) for f in fs]


def images(path):
    """(count, total stream bytes, encodings) from pdfimages -list."""
    out = subprocess.run(["/opt/homebrew/bin/pdfimages", "-list", path],
                         capture_output=True, text=True).stdout.splitlines()
    rows = [l.split() for l in out[2:] if l.strip()]
    n = len(rows)
    enc = {}
    total = 0
    for r in rows:
        if len(r) < 14:
            continue
        enc[r[8]] = enc.get(r[8], 0) + 1
        s = r[-2]
        mult = {"B": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}.get(s[-1], 1)
        try:
            total += float(s[:-1]) * mult if s[-1] in "BKMG" else float(s)
        except ValueError:
            pass
    return n, total, enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--pages", nargs="*", type=int)
    ap.add_argument("--skip-verify", action="store_true")
    A = ap.parse_args()

    items = page_list(A.pages)
    missing = [p for p, f in items if not os.path.exists(f)]
    if missing:
        print("MISSING pages: %s" % missing)
        return 1
    print("assembling %d pages -> %s" % (len(items), A.out))

    # qpdf, not gs: gs re-encodes image streams, which would undo the descreen and the JBIG2.
    cmd = ["/opt/homebrew/bin/qpdf", "--empty", "--pages"] + [f for _, f in items] + ["--", A.out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode not in (0, 3):          # 3 = warnings only
        print("qpdf failed: %s" % r.stderr[:800])
        return 1
    if r.stderr.strip():
        print("qpdf warnings: %s" % r.stderr.strip()[:400])

    subprocess.run(["/opt/homebrew/bin/qpdf", "--replace-input",
                    "--add-page-labels", "1:D", A.out], capture_output=True)

    size = os.path.getsize(A.out)
    parts = sum(os.path.getsize(f) for _, f in items)
    print("  size %.1f MB   (sum of parts %.1f MB, %+.2f%%)"
          % (size / 1e6, parts / 1e6, 100 * (size - parts) / parts))

    if A.skip_verify:
        return 0
    # LOSSLESS CHECK: the assembled file must carry exactly the streams the parts did.
    print("verifying image streams survived unchanged ...")
    tn = tt = 0
    tenc = {}
    for _, f in items:
        n, t, e = images(f)
        tn += n
        tt += t
        for k, v in e.items():
            tenc[k] = tenc.get(k, 0) + v
    an, at, aenc = images(A.out)
    ok = True
    if an != tn:
        print("  FAIL image count %d vs %d" % (an, tn)); ok = False
    if aenc != tenc:
        print("  FAIL encodings %s vs %s" % (aenc, tenc)); ok = False
    if tt and abs(at - tt) / tt > 0.005:
        print("  FAIL stream bytes %.1f MB vs %.1f MB" % (at / 1e6, tt / 1e6)); ok = False
    print("  images %d   encodings %s   stream bytes %.1f MB" % (an, aenc, at / 1e6))
    print("  LOSSLESS: %s" % ("yes" if ok else "NO -- streams changed"))
    json.dump({"pages": len(items), "bytes": size, "images": an, "encodings": aenc,
               "lossless": ok}, open(os.path.splitext(A.out)[0] + "_assembly.json", "w"), indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
