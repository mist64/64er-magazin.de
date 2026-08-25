#!/usr/bin/env python3
"""r190c — find ITALIC runs on the page, which the OCR throws away like bold.

Companion to r190_find_bold.py.  Same problem: the pipeline's OCR carries no
style attribute at all, so italic emphasis arrives as plain text.  Different
measurement, because italic is SHEAR, not weight.

WHAT DOES NOT WORK, measured first: the ink covariance of a word (how x shifts
with y over its pixels) is dominated by WHICH LETTERS the word contains, not by
slant.  On SH8601 p076 the roman baseline sat at +0.170 while known-italic words
scattered from -0.178 to +0.613 -- no separation at all.

WHAT WORKS: find the shear that best ALIGNS THE VERTICAL STROKES, the same
operation a deskew does, by maximising the energy of the sheared column
projection.  Upright type peaks at 0; italic peaks at its own slant.  Compared
against the median of the word's OWN TEXT LINE, exactly as the bold detector
does, so page-level scan skew cancels.

MEASURED on SH8601 p076, where Multiplan's FORMAT option names are italic and
the surrounding text is not:
    Stnd Norm Links Rechts Zusamm Fest Ganz   +0.15 .. +0.20
    line median                               +0.00
Clean separation, and it is the same shape of answer the bold detector gives.

CALIBRATE BEFORE USING THIS ON A NEW ISSUE.  The MEASUREMENT transfers -- it is
relative to each word's own text line, so point size, scan exposure, paper grey
and page skew all cancel.  THE THRESHOLD DOES NOT.  It depends on how slanted
that issue's italic actually is, and this archive spans a decade in which the
magazine changed typeface more than once.

Evidence: run unchanged on 8610 p162, this detector returns 32 hits of which the
top ones are `nn`, `en`, `w`, `A`, `70` -- short-token noise, which is exactly
what an uncalibrated threshold looks like.  On SH8601 the same code returns the
FORMAT option names and little else.

So, per issue, before trusting a single hit:
  1. find one page whose emphasis you can confirm by eye,
  2. measure it and the roman text around it,
  3. set the threshold from that gap, and record the numbers in the issue's LOG,
  4. re-check that a known-emphasised word still survives -- a threshold that
     silences the noise by also silencing the real hits is the failure this
     chain has already made once (r000, "changing a tool means measuring before
     and after").

The listing/ad exclusion additionally needs `<tmp>/ocr/out/NNN.labels.json`,
which only exists once the issue has been through step 020.

REPORTS ONLY -- confirm each hit on the crop before wrapping it in <em>.

usage:  r190_find_italic.py <masters600 dir> <page> [page ...]
"""
import csv, json, subprocess, sys, tempfile, os
from collections import defaultdict
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

SLANT = 0.10          # shear above the line median that counts as italic
MIN_PX = 20           # a slant measure needs a few strokes to be meaningful
MIN_WORDS_PER_LINE = 3
SHEARS = np.arange(-0.05, 0.55, 0.05)

def skip_boxes(master):
    """Listing and ad blocks -- see r190_find_bold.py for why these two."""
    lab = os.path.join(os.path.dirname(master), '..', 'ocr', 'out',
                       os.path.basename(master).replace('.png', '.labels.json'))
    try:
        d = json.load(open(os.path.normpath(lab)))
    except Exception:
        return []
    out = []
    for b in d.get('blocks', []):
        if str(b.get('label', '')).startswith(('listing', 'ad')):
            x, y, w, h = b.get('bbox', [0, 0, 0, 0])
            out.append((x, y, x + w, y + h))
    return out

def best_shear(sub):
    """The shear that makes this word's vertical strokes line up best."""
    if sub.sum() < 40:
        return None
    H = sub.shape[0]
    best, score = None, -1.0
    for s in SHEARS:
        pad = int(abs(s) * H) + 2
        acc = np.zeros(sub.shape[1] + pad)
        for y in range(H):
            cols = np.nonzero(sub[y])[0] + int(round(s * (y - H / 2))) + pad // 2
            acc[np.clip(cols, 0, len(acc) - 1)] += 1
        v = float((acc ** 2).sum())
        if v > score:
            score, best = v, float(s)
    return best

def page_italic(master):
    skip = skip_boxes(master)
    ink = np.asarray(Image.open(master).convert('L'), np.uint8) < 128
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'p')
        subprocess.run(['tesseract', master, base, '-l', 'deu', '--psm', '3', 'tsv'],
                       capture_output=True)
        rows = list(csv.DictReader(open(base + '.tsv'), delimiter='\t',
                                   quoting=csv.QUOTE_NONE))
    lines, drop = defaultdict(list), set()
    for r in rows:
        if r.get('level') != '5' or not (r.get('text') or '').strip():
            continue
        l, t, w, h = (int(r[k]) for k in ('left', 'top', 'width', 'height'))
        key = (r['block_num'], r['par_num'], r['line_num'])
        if w < MIN_PX or h < MIN_PX:
            continue
        cx, cy = l + w // 2, t + h // 2
        if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in skip):
            drop.add(key)
            continue
        s = best_shear(ink[t:t+h, l:l+w])
        if s is not None:
            lines[key].append((r['text'].strip(), s, (l, t, w, h)))
    out = []
    for key, ws in lines.items():
        if key in drop or len(ws) < MIN_WORDS_PER_LINE:
            continue
        med = float(np.median([s for _, s, _ in ws]))
        for txt, s, box in ws:
            if s - med >= SLANT:
                out.append((txt, round(s - med, 2), box))
    return out

def main(dirname, pages):
    for p in pages:
        m = os.path.join(dirname, f'{int(p):03d}.png')
        if not os.path.exists(m):
            print(f'p{p}: no master'); continue
        hits = page_italic(m)
        print(f'p{p}: {len(hits)} slanted word(s)')
        for txt, d, (l, t, w, h) in hits:
            print(f'    +{d:.2f}  {txt[:28]:30} at +{l}+{t} ({w}x{h})')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
