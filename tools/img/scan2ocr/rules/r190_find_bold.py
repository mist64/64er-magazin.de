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

This REPORTS candidates; it does not edit.  Confirm each on the crop before
wrapping it in <strong> -- a drop cap, a heading that leaked into a body block,
and a word sitting over a rule or a figure edge all read heavy for reasons that
have nothing to do with weight.

usage:  r190_find_bold.py <masters600 dir> <page> [page ...]
"""
import csv, json, subprocess, sys, tempfile, os
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

def listing_boxes(master):
    """Bboxes of every block that does NOT reach the article, at master scale.

    EXCLUDE BY LABEL -- `listing` and `ad` -- NOT by absence from `order`.
    Testing `order` looks more principled ("only text that reaches the article")
    and is wrong: it cost 15 of p077's 25 CONFIRMED-BOLD Multiplan command names,
    which sit in blocks the classifier had labelled `noise` while their text
    still reached the article by another route.  A misclassified block is not a
    reason to go blind to it.

    The two excluded classes are where the false positives actually live:
    advertisements set product names in heavy display type (p095's `PROTEXT`,
    p053's `dBASE II`), the Zahlkarte insert's printed pattern reads 63x, and a
    monospace listing line is mostly digits, which a proportional-face median
    calls bold.

    MONOSPACE LISTING TEXT IS NOT COMPARABLE.  A BASIC line number in a listing
    reads 1.6-2.5x its line median on stroke weight alone, because a monospace
    face sets digits far heavier than the surrounding proportional prose -- and
    a listing line is mostly digits.  MEASURED on SH8601: 194 hits issue-wide
    fell to 30 once listing blocks were excluded, and the ~164 removed were all
    line numbers on pages 43-46, 52, 55-57, 64-66 and 76-77.  Listings are
    <pre> and out of scope for run-in emphasis anyway.
    """
    lab = os.path.join(os.path.dirname(master),
                       '..', 'ocr', 'out',
                       os.path.basename(master).replace('.png', '.labels.json'))
    try:
        d = json.load(open(os.path.normpath(lab)))
    except Exception:
        return []
    out = []
    SKIP = ('listing', 'ad')
    for b in d.get('blocks', []):
        if str(b.get('label', '')).startswith(SKIP):
            x, y, w, h = b.get('bbox', [0, 0, 0, 0])
            out.append((x, y, x + w, y + h))
    return out


def page_bold(master):
    skip = listing_boxes(master)
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
    drop_lines = set()      # any line with a word inside a listing goes ENTIRELY
    first_of_par = set()          # (block,par,line,wordnum) that opens a paragraph
    seen_par = set()
    for r in rows:
        if r.get('level') != '5' or not (r.get('text') or '').strip():
            continue
        l, t, w, h = (int(r[k]) for k in ('left', 'top', 'width', 'height'))
        if w < MIN_PX or h < MIN_PX:
            continue
        cx, cy = l + w // 2, t + h // 2
        if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in skip):
            drop_lines.add((r['block_num'], r['par_num'], r['line_num']))
            continue
        key = (r['block_num'], r['par_num'])
        if key not in seen_par:
            seen_par.add(key)
            first_of_par.add((r['block_num'], r['par_num'], r['line_num'], r['word_num']))
        lines[(r['block_num'], r['par_num'], r['line_num'])].append(
            (r['text'].strip(), float(ink[t:t+h, l:l+w].mean()), (l, t, w, h),
             (r['block_num'], r['par_num'], r['line_num'], r['word_num']) in first_of_par))
    # DROP THE WHOLE LINE, not the individual words.  Removing only the words
    # that fall inside a listing box CHANGES THAT LINE'S MEDIAN, so different
    # borderline words cross the threshold and the noise merely moves.
    # MEASURED on SH8601 p055: per-word exclusion swapped one set of BASIC line
    # numbers (`S888`, `4208`) for another (`4848`, `SO6B`, `5188`) and added a
    # phantom hit on p058.  Per-line exclusion removes the class.
    out = []
    for key, ws in lines.items():
        if key in drop_lines:
            continue
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
