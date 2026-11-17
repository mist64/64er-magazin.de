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
            # r080's lettered pages ('169a') are not ints -- int('131b') dies
            # here and took the whole check with it on SH8602.
            part = re.sub(r'(?<=\d)[a-z]$', '', part)
            if '-' in part:
                a, b = (re.sub(r'[^0-9]', '', x) for x in part.split('-', 1))
                if a and b:
                    out |= set(range(int(a), int(b) + 1))
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
    # A DIRECTORY WITH NO labels.json IS NOT A CLEAN RUN -- it is no run.
    # MEASURED 2026-10-17: SH8608 pointed this at <tmp>/ocr when the build's
    # output is <tmp>/ocr/out. The glob matched nothing, the loop never ran,
    # and this printed "dropped listing blocks: 0 ... 0" and exited 0. The
    # builder reported a clean gate that had looked at nothing, and found out
    # only because the sibling r320_coverage_check.py refused the same path
    # with exit 2. Refuse it here too, and in the same words.
    label_files = sorted(glob.glob(f'{ocr}/*.labels.json'))
    if not label_files:
        print(f'CANNOT RUN: no <page>.labels.json under {ocr}')
        print('  This check reads the OCR intermediates to find listing blocks')
        print('  that classification dropped. Point it at the build\'s OCR out')
        print('  directory (usually <tmp>/ocr/out, NOT <tmp>/ocr), or rebuild')
        print('  them if <tmp> has been swept.')
        return 2

    dropped = checkable = 0        # so "0 findings" can be told from "0 looked at"
    bypage = {}                    # page -> dropped listing blocks, for the weak gate
    for lf in label_files:
        p = int(os.path.basename(lf)[:3])
        lab = json.load(open(lf))
        order = {str(i) for i in lab.get('order', [])}
        for b in lab.get('blocks', []):
            if str(b.get('id')) in order: continue
            if not str(b.get('label', '')).startswith('listing'): continue
            t = str(b.get('text', ''))
            dropped += 1
            bypage[p] = bypage.get(p, 0) + 1
            # ONLY SMON monitor dumps are checkable this way.  An issue whose
            # dropped listings are BASIC or MSE yields nothing here, and the
            # result is then "0 findings" from a check that examined nothing --
            # on SH8602 a planted removal of EVERY <pre> still reported 0.
            if len(DUMP.findall(t)) < 5: continue
            checkable += 1
            arts = p2a.get(p, [])
            html = ' '.join(io.open(a, encoding='utf-8').read() for a in arts)
            pres = ' '.join(re.findall(r'<pre(?![^>]*data-filename)[^>]*>(.*?)</pre>', html, re.S))
            addrs = {norm(a) for a in ADDR.findall(t)}
            have  = {norm(a) for a in ADDR.findall(pres)}
            cov = len(addrs & have) / max(1, len(addrs))
            if cov < 0.5:
                bad.append((p, len(t.split()), round(cov, 2),
                            [os.path.basename(a)[:30] for a in arts], ' '.join(t.split()[:12])))
    # --- THE WEAK GATE, for the blocks the strong one cannot read -----------
    # "0 checkable" is honest but it leaves the whole population unexamined:
    # MEASURED on 8702, 644 dropped listing blocks on 38 pages, not one of them
    # a monitor dump, so the strong test looked at NOTHING and said 0. The
    # weakest true statement that still covers them: a page whose OCR found
    # listing blocks must belong to an article that places at least one listing
    # figure. It cannot see a SINGLE missing listing among several placed ones
    # -- say so rather than let a green here be read as coverage -- but it does
    # catch a whole article's listings going missing, and it is the only thing
    # standing between 644 blocks and no check at all.
    weak = []
    for p, n in sorted(bypage.items()):
        arts = p2a.get(p, [])
        if not arts:
            weak.append((p, n, 'NO ARTICLE CLAIMS THIS PAGE'))
            continue
        html = ' '.join(io.open(a, encoding='utf-8').read() for a in arts)
        if not re.search(r'<pre[^>]*data-filename', html):
            weak.append((p, n, os.path.basename(arts[0])[:40] + ' — no listing figure'))

    print(f'dropped listing blocks: {dropped}   of those checkable as monitor '
          f'dumps: {checkable}   with no home in the article: {len(bad)}')
    print(f'page-level check: {len(bypage)} page(s) with dropped listings, '
          f'{len(weak)} whose article places no listing at all')
    if dropped and not checkable:
        print('  NOTE: none of the dropped listings is a monitor dump, so the '
              'ADDRESS check examined nothing. Only the page-level check below '
              'covers them, and it cannot see one missing listing among several.')
    for p, n, c, a, t in bad:
        print(f'  p{p:<4} words={n:<4} addr-coverage={c}  {a}\n        {t}…')
    for p, n, why in weak:
        print(f'  p{p:<4} {n:>3} dropped listing block(s)  {why}')
    return 1 if (bad or weak) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
