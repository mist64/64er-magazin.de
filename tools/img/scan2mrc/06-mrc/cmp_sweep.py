#!/usr/bin/env python3
"""Compare two sweep runs of the MRC renderer.

Two questions, and they need different evidence, so this does both separately:

  --mode regression   A vs C: the inpaint fix vs the old inpaint, same darkfill.
                      The fix may ONLY change pixels the fallback actually rewrote. Any difference
                      outside a recorded `inpaint_fallback` bbox is a regression, and this reports
                      it as one instead of averaging it away in a mean.

  --mode darkfill     A vs B: darkfill on vs off, same inpaint.
                      Not decidable by a number -- "is the lettering legible" is a judgement -- so
                      this emits side-by-side crops of every promoted region, largest first, and
                      leaves the verdict to a human.

The background layer is pulled straight out of the PDF (one Flate RGB image), so nothing has to be
rasterised for the regression check. That keeps it cheap enough to run over all 176 pages.

  cmp_sweep.py --mode regression --a tmp/sweep/A --b tmp/sweep/C
  cmp_sweep.py --mode darkfill   --a tmp/sweep/A --b tmp/sweep/B --out tmp/sweep/cmp
"""
import argparse
import glob
import json
import os
import re
import zlib

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np                                                    # noqa: E402
from PIL import Image                                                 # noqa: E402

Image.MAX_IMAGE_PIXELS = None

BG_RE = re.compile(
    rb'/Subtype /Image /Width (\d+) /Height (\d+) /ColorSpace /DeviceRGB '
    rb'/BitsPerComponent 8 /Filter /FlateDecode /Length (\d+)\s*>>\s*stream\r?\n', re.S)
SRC_DPI = 600          # the record's bbox frame
DIFF_T = 8             # per-channel value change that counts as a real difference, not rounding
PAD = 3                # bbox slack in bg px when testing containment: the fallback mask is
                       # labelled at bg_dpi and a 1px edge effect is not a regression


def bg_of(pdf):
    d = open(pdf, 'rb').read()
    m = BG_RE.search(d)
    if not m:
        return None
    w, h, L = int(m.group(1)), int(m.group(2)), int(m.group(3))
    raw = zlib.decompress(d[m.end():m.end() + L])
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def rows(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def regression(A, B):
    """Every changed pixel must lie inside a recorded fallback region."""
    pages = sorted(int(os.path.basename(f)[:3]) for f in glob.glob(os.path.join(B, "[0-9][0-9][0-9].pdf")))
    print("pages to check: %d" % len(pages))
    bad = []
    for p in pages:
        fa = os.path.join(A, "%03d.pdf" % p)
        fb = os.path.join(B, "%03d.pdf" % p)
        if not (os.path.exists(fa) and os.path.exists(fb)):
            continue
        ba, bb = bg_of(fa), bg_of(fb)
        if ba is None or bb is None or ba.shape != bb.shape:
            print("  p%03d  SHAPE/DECODE MISMATCH" % p)
            bad.append((p, -1, -1))
            continue
        diff = (np.abs(ba.astype(np.int16) - bb.astype(np.int16)).max(2) > DIFF_T)
        nd = int(diff.sum())
        if nd == 0:
            continue
        # mark every recorded fallback bbox, in bg space
        h, w = diff.shape
        allowed = np.zeros((h, w), bool)
        rr = rows(os.path.join(A, "%03d.jsonl" % p))
        # the record frame comes from the page row, never a hardcoded size: a page whose crop
        # differs would silently shift every bbox and the containment test would pass on the
        # wrong pixels.
        pg = next((x for x in rr if x.get("kind") == "page"), {})
        mw, mh = pg.get("mw"), pg.get("mh")
        if not mw or not mh:
            print("  p%03d  no page row -- cannot place bboxes" % p)
            bad.append((p, nd, nd))
            continue
        sx, sy = w / float(mw), h / float(mh)
        for r in rr:
            if r.get("kind") != "inpaint_fallback":
                continue
            x0, y0, x1, y1 = r["bbox"]
            allowed[max(0, int(y0 * sy) - PAD):int(y1 * sy) + PAD + 1,
                    max(0, int(x0 * sx) - PAD):int(x1 * sx) + PAD + 1] = True
        outside = int((diff & ~allowed).sum())
        tag = "OK " if outside == 0 else "OUTSIDE"
        print("  p%03d  changed %7d px (%.3f%%)  outside fallback: %d  %s"
              % (p, nd, 100.0 * nd / diff.size, outside, tag))
        if outside > 0:
            bad.append((p, nd, outside))
    print("\n%s" % ("=" * 70))
    if bad:
        print("REGRESSIONS: %d page(s) changed outside a recorded fallback region" % len(bad))
        for p, nd, o in bad:
            print("  p%03d  %d px outside" % (p, o))
    else:
        print("CLEAN: every change is confined to a recorded inpaint_fallback region")
    return len(bad)


def darkfill(A, B, out, dpi=600, limit=60):
    """Side-by-side crops of every promoted darkfill region, largest first."""
    os.makedirs(out, exist_ok=True)
    regs = []
    for f in sorted(glob.glob(os.path.join(A, "[0-9][0-9][0-9].jsonl"))):
        p = int(os.path.basename(f)[:3])
        for r in rows(f):
            if r.get("kind") == "darkfill" and r.get("promoted"):
                x0, y0, x1, y1 = r["bbox"]
                regs.append((p, (x1 - x0) * (y1 - y0), r["bbox"]))
    regs.sort(key=lambda t: -t[1])
    print("promoted darkfill regions: %d (rendering top %d)" % (len(regs), min(limit, len(regs))))
    made = []
    for p, area, bb in regs[:limit]:
        ra = os.path.join(out, "r_%03d_A.png" % p)
        rb = os.path.join(out, "r_%03d_B.png" % p)
        for src, dst in ((os.path.join(A, "%03d.pdf" % p), ra), (os.path.join(B, "%03d.pdf" % p), rb)):
            if not os.path.exists(dst):
                os.system('gs -q -dNOPAUSE -dBATCH -dSAFER -dAutoRotatePages=/None '
                          '-sDEVICE=png16m -r%d -sOutputFile=%s %s' % (dpi, dst, src))
        if not (os.path.exists(ra) and os.path.exists(rb)):
            continue
        k = dpi / float(SRC_DPI)
        box = [int(v * k) for v in bb]
        ia, ib = Image.open(ra).crop(box), Image.open(rb).crop(box)
        sc = min(1.0, 1400.0 / max(1, ia.width))
        if sc < 1.0:
            ia = ia.resize((int(ia.width * sc), int(ia.height * sc)), Image.LANCZOS)
            ib = ib.resize((int(ib.width * sc), int(ib.height * sc)), Image.LANCZOS)
        o = Image.new("RGB", (ia.width, ia.height * 2 + 56), (255, 255, 255))
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(o)
        try:
            fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        except Exception:
            fo = None
        d.text((4, 4), "p%03d  A: darkfill ON  (promoted to contone bg)" % p, fill=(0, 0, 0), font=fo)
        o.paste(ia, (0, 26))
        d.text((4, ia.height + 32), "p%03d  B: darkfill OFF (stays 600dpi K)" % p, fill=(0, 0, 0), font=fo)
        o.paste(ib, (0, ia.height + 54))
        f = os.path.join(out, "df_%03d_%d.png" % (p, area))
        o.save(f)
        made.append(f)
        print("  %s" % f)
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("regression", "darkfill"), required=True)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", default="/Users/mist/DNB/8609/tmp/sweep/cmp")
    ap.add_argument("--limit", type=int, default=60)
    A = ap.parse_args()
    if A.mode == "regression":
        raise SystemExit(min(regression(A.a, A.b), 250))
    darkfill(A.a, A.b, A.out, limit=A.limit)
