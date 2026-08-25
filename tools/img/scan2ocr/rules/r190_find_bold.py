#!/usr/bin/env python3
"""r190b — find BOLD runs on the page, which the OCR throws away.

WHY THIS EXISTS.  The pipeline's OCR output carries geometry, confidence,
`mono`, `digit_frac`, `upper_frac` -- and NO weight attribute.  Tesseract 5
emits none either, in hOCR or TSV.  So a bold run-in term (`**Pal**, HF-
moduliertes FBAS-Signal.`) arrives as plain text and no rule can see it.
MEASURED on SH8601: the magazine's run-in terms were flattened issue-wide,
while the corpus sets them `<p><strong>TERM</strong>, ...` 229 times.

BOLD IS PHYSICALLY MEASURABLE, so this does not need a human reading every
page.  A bold glyph lays down more ink over its box than a roman one of the
same size, so a word's ink fraction against the MEDIAN OF ITS OWN TEXT LINE
separates them.  The line median is the right baseline because it cancels the
things that would otherwise dominate: point size, the scan's exposure, and this
paper's varying grey.

MEASURED on SH8601 p023, where `Pal` opens a bold run-in definition:
    Pal,            0.438 ink   1.76x line median
    every other word on the page          0.78x - 1.30x
A threshold of 1.35 isolates it with nothing else near.

This REPORTS candidates; it does not edit.  Confirm each on the crop before
wrapping it in <strong> -- a drop cap, a heading that leaked into a body block,
and a word sitting over a rule or a figure edge all read heavy for reasons that
have nothing to do with weight.

usage:  r190_find_bold.py <masters600 dir> <page> [page ...]
"""
import csv, subprocess, sys, tempfile, os
from collections import defaultdict
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HEAVY = 1.40          # ink fraction relative to the word's own line median
MIN_CHARS = 3         # short words are noisy: 'man', 'aus', 'zu' hit 1.36-1.49
                      # on stroke-thickening alone.  Raising HEAVY instead lost
                      # a genuine `Composite.` at 1.50, and a false negative is
                      # worse here than a false positive -- the confirming crop
                      # is cheap, a missed bold run is invisible forever.
MIN_PX = 6            # ignore specks
MIN_WORDS_PER_LINE = 3  # a median over one or two words means nothing

def page_bold(master):
    im = Image.open(master).convert('L')
    g = np.asarray(im, np.uint8)
    ink = g < 128
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'p')
        subprocess.run(['tesseract', master, base, '-l', 'deu', '--psm', '3', 'tsv'],
                       capture_output=True)
        rows = list(csv.DictReader(open(base + '.tsv'), delimiter='\t',
                                   quoting=csv.QUOTE_NONE))
    lines = defaultdict(list)
    first_of_par = set()          # (block,par,line,wordnum) that opens a paragraph
    seen_par = set()
    for r in rows:
        if r.get('level') != '5' or not (r.get('text') or '').strip():
            continue
        l, t, w, h = (int(r[k]) for k in ('left', 'top', 'width', 'height'))
        if w < MIN_PX or h < MIN_PX:
            continue
        key = (r['block_num'], r['par_num'])
        if key not in seen_par:
            seen_par.add(key)
            first_of_par.add((r['block_num'], r['par_num'], r['line_num'], r['word_num']))
        lines[(r['block_num'], r['par_num'], r['line_num'])].append(
            (r['text'].strip(), float(ink[t:t+h, l:l+w].mean()), (l, t, w, h),
             (r['block_num'], r['par_num'], r['line_num'], r['word_num']) in first_of_par))
    out = []
    for ws in lines.values():
        if len(ws) < MIN_WORDS_PER_LINE:
            continue
        med = float(np.median([f for _, f, _, _ in ws]))
        if med <= 0:
            continue
        for txt, f, box, opens in ws:
            # POSITION IS THE DISCRIMINATOR.  A run-in term OPENS its paragraph.
            # Mid-sentence words that merely read heavy -- `man`, `aus`, `zur`,
            # short words whose ink fraction is noisy -- are exactly the false
            # positives, and they are never paragraph-initial.  MEASURED on
            # SH8601 p023: 10 candidates -> 4, and all four are the real terms.
            if opens and f / med >= HEAVY and len(txt.strip('.,;:»«()')) >= MIN_CHARS:
                out.append((txt, round(f / med, 2), box))
    return out

def main(dirname, pages):
    for p in pages:
        m = os.path.join(dirname, f'{int(p):03d}.png')
        if not os.path.exists(m):
            print(f'p{p}: no master'); continue
        hits = page_bold(m)
        print(f'p{p}: {len(hits)} heavy word(s)')
        for txt, ratio, (l, t, w, h) in hits:
            print(f'    {ratio:5.2f}x  {txt[:28]:30} at +{l}+{t} ({w}x{h})')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
