#!/usr/bin/env python3
"""Printed figure captions, from the OCR, checked against the HTML.

WHY THIS EXISTS. A caption for a figure nobody has cut yet lives ONLY in the OCR
intermediates, and those are swept with <tmp>: measured across the corpus,
exactly one issue still has them -- the one being built. 8611 had 76 printed
Bild/Tabelle/Listing captions in the OCR and in no HTML file. Once <tmp> goes
they must be read off the masters again, one page at a time.

So run this BEFORE the sweep and commit its output next to the article HTML.

It also answers a second question with the same comparison: a caption can be
PRESENT but TRUNCATED. 8611 dropped the second sentence of seven listing
captions ("Beachten Sie bitte die Eingabehinweise auf Seite 99"); three readers
found it independently and a sweep found the last one. A tail that is in the
print and not in the HTML is the same defect as a caption that is missing
outright, and neither is visible to a coverage check.

usage: r150_figure_captions.py <issue-dir> [ocr-dir] [--write]
"""
import glob, html, json, os, re, sys

# THE NUMBER IS OPTIONAL.  `\s*\d` required a digit, so an UNNUMBERED caption
# never matched: SH8603 prints a bare "Tabelle." whose prose calls it "Tabelle
# 1", and "Bild. 1." puts the period before the number.  Both are captions, and
# both were invisible -- which matters most because an unnumbered one is exactly
# the caption r150's naming scheme has no slot for either.
# (?![a-zäöüß]) because the number is now optional: without it, "Bild" matches
# as a PREFIX and "Bildschirm Grafik Basic-Erweiterung" is read as a caption.
# The old `\s*\d` was safe from that only by accident -- 's' is not a digit.
CAPTION = re.compile(r'^(Bild|Tabelle|Listing)(?![a-zäöüß])'
                     r'\s*\.?\s*\d*[a-z]?\s*[.:»]?', re.I)
# JOIN THE LINE-BREAK HYPHEN FIRST (r280 Pass 1's defect, seen from here).
# The OCR keeps the print's hyphenation as '¬' or '-', so "Buch¬stabens"
# normalises to two words where the HTML has one, and the caption reads as
# truncated when it is verbatim. Measured: this alone was 4 of 5 TRUNCATED.
norm = lambda t: re.sub(r'[^a-z0-9]+', ' ',
                        html.unescape(re.sub(r'[¬\u00ad-]\s*', '', t)).lower()).split()

def main(issue_dir, ocr_dir, write):
    hay = set()
    for f in glob.glob(os.path.join(issue_dir, '*.html')):
        w = norm(re.sub(r'<[^>]+>', ' ', open(f, encoding='utf-8', errors='replace').read()))
        for i in range(len(w)):
            hay.add(' '.join(w[i:i+4]))          # 4-word shingles, as r320 uses
    def seen(words):
        # A SHORT CAPTION IS NOT AUTOMATICALLY PRESENT.  `return True` for
        # anything under four words reported SH8603's p146 and p148 tables as
        # IN_HTML while they were absent -- the shortcut exists because the
        # haystack is 4-word shingles, so it was answering "I cannot tell" with
        # "yes".  Fall back to the longest shingle the caption can form.
        if not words:
            return True
        if len(words) < 4:
            return ' '.join(words) in ' '.join(sorted(hay)) or any(
                ' '.join(words) in h for h in hay)
        return ' '.join(words[:4]) in hay
    rows = []
    for jf in sorted(glob.glob(os.path.join(ocr_dir, '[0-9][0-9][0-9].json'))):
        page = int(os.path.basename(jf)[:3])
        for b in json.load(open(jf)).get('blocks', []):
            # NOT ONLY label == 'caption'.  020 labels a caption that sits
            # inside a listing block `listing-inline`, and SH8603's p23 Bild 2
            # was labelled exactly that and so never examined.  Take any block
            # whose TEXT opens like a caption; the CAPTION match below is the
            # real filter, and a false one costs a line in the report.
            if b.get('label') not in ('caption', 'listing-inline', 'body', None):
                continue
            t = ' '.join((b.get('text') or '').split())
            if not CAPTION.match(t): continue
            w = norm(t)
            head, tail = seen(w), seen(w[-6:] if len(w) > 10 else w)
            rows.append((page, 'IN_HTML' if head and tail else
                               'TRUNCATED' if head else 'ABSENT', t))
    rows.sort()
    for st in ('ABSENT', 'TRUNCATED'):
        n = [r for r in rows if r[1] == st]
        print(f'{st}: {len(n)}')
        for p, _, t in n[:8]: print(f'   p{p:<4} {t[:66]}')
        if len(n) > 8: print(f'   … and {len(n)-8} more')
    print(f'IN_HTML: {sum(1 for r in rows if r[1] == "IN_HTML")}   total {len(rows)}')
    if write:
        out = os.path.join(issue_dir, 'figure_captions.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            for p, st, t in rows: fh.write(f'{p}\t{st}\t{t}\n')
        print(f'\nwrote {out} ({len(rows)} lines)')

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import r000_issue
    from r000_issue import ISSUE
    iss = r000_issue.load(ISSUE)
    main(a[0] if a else iss.issue_dir,
         a[1] if len(a) > 1 else iss.out_dir,
         '--write' in sys.argv)
