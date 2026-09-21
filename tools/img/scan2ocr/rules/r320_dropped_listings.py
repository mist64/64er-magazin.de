#!/usr/bin/env python3
"""r320b — a listing block DROPPED at classification must still have a home.

WHY THIS EXISTS.  r020 drops `listing-*` blocks from `order` (the disk supplies
listings), and r320's coverage gate audits only blocks that were KEPT.  So a
listing with no disk file and no transcription falls between the two and NO GATE
CAN SEE IT.  MEASURED on SH8601: p135's INPUT-Routine, 573 words over two
blocks, absent from the article while every gate reported the issue complete.

WHY ADDRESS COVERAGE, not word matching.  Listing OCR is too noisy for shingles
-- `18 rem x## data lader fuer alle sprites ##rr` is the disk's
`10 REM ... DATA-LADER FUER ALLE SPRITES`, and a word-overlap test calls that
missing.  Trying it on SH8601 gave 84 findings of which 82 were false.  Hex
ADDRESSES survive OCR far better (short tokens, and `O`->`0` is the only common
confusion), so a monitor dump is matched by how many of its addresses appear in
the article's own <pre> blocks.  Same run, that gives exactly the 2 real ones.

usage:  r320_dropped_listings.py <issue dir> <ocr out dir>
"""
import json, glob, io, re, os, sys

def pages_of(f):
    m = re.search(r'64er\.pages" content="([^"]*)"', io.open(f, encoding='utf-8').read())
    out = set()
    if m:
        for part in m.group(1).split(','):
            part = part.strip()
            if '-' in part:
                a, b = part.split('-'); out |= set(range(int(a), int(b) + 1))
            elif part.isdigit():
                out.add(int(part))
    return out

ADDR = re.compile(r'\b([0-9a-fO][0-9a-fO]{3,4})\b')
DUMP = re.compile(r'\ba\s*[0-9a-fO]{4,5}\s+[0-9a-fO]{2}\b')
norm = lambda a: a.lower().replace('o', '0')

def main(issue_dir, ocr):
    p2a = {}
    for f in glob.glob(issue_dir + '/*.html'):
        for p in pages_of(f): p2a.setdefault(p, []).append(f)
    bad = []
    for lf in sorted(glob.glob(f'{ocr}/*.labels.json')):
        p = int(os.path.basename(lf)[:3])
        lab = json.load(open(lf))
        order = {str(i) for i in lab.get('order', [])}
        for b in lab.get('blocks', []):
            if str(b.get('id')) in order: continue
            if not str(b.get('label', '')).startswith('listing'): continue
            t = str(b.get('text', ''))
            if len(DUMP.findall(t)) < 5: continue      # only monitor dumps are checkable this way
            arts = p2a.get(p, [])
            html = ' '.join(io.open(a, encoding='utf-8').read() for a in arts)
            pres = ' '.join(re.findall(r'<pre(?![^>]*data-filename)[^>]*>(.*?)</pre>', html, re.S))
            addrs = {norm(a) for a in ADDR.findall(t)}
            have  = {norm(a) for a in ADDR.findall(pres)}
            cov = len(addrs & have) / max(1, len(addrs))
            if cov < 0.5:
                bad.append((p, len(t.split()), round(cov, 2),
                            [os.path.basename(a)[:30] for a in arts], ' '.join(t.split()[:12])))
    print(f'dropped monitor-dump blocks with no home in the article: {len(bad)}')
    for p, n, c, a, t in bad:
        print(f'  p{p:<4} words={n:<4} addr-coverage={c}  {a}\n        {t}…')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
