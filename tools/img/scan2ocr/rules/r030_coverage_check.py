#!/usr/bin/env python3
"""Reconcile the OCR blocks the CLASSIFIER KEPT against the published HTML.

Stage B (r020) decides which blocks on a page are article content and records
them in <page>.labels.json as "order".  Everything it kept must therefore end up
in the article that claims that page.  A kept block whose text appears nowhere
in that article is content dropped between the scan and the published page —
the failure mode that no spell-check or markup grep can see, because what
survives reads perfectly well.

Listing blocks are excluded: the disk .txt is the correct petcat rendering while
the OCR reading of the printed listing is garbled ('mps 891' for 'mps 801'), so
they never match and would drown the signal.
"""
import glob, io, json, re, sys

ISSUE = sys.argv[1] if len(sys.argv) > 1 else '/Users/mist/Documents/git/64er-magazin.de/issues/8609'
OCR   = sys.argv[2] if len(sys.argv) > 2 else '/Users/mist/DNB/8609/tmp/ocr/out'
SHINGLE, MIN_WORDS, THRESH = 4, 12, 0.25

norm = lambda t: re.sub(r'[^a-z0-9]+', ' ', t.lower()).split()

page2art, arttext = {}, {}
for f in sorted(glob.glob(ISSUE + '/*.html')):
    s = io.open(f, encoding='utf-8').read()
    m = re.search(r'64er\.pages" content="([^"]*)"', s)
    if not m: continue
    i = s.find('<article')
    arttext[f] = ' '.join(norm(re.sub(r'<[^>]+>', ' ', s[i:s.rfind('</article>')] if i >= 0 else s)))
    for part in m.group(1).split(','):
        part = part.strip()
        rng = range(int(part.split('-')[0]), int(part.split('-')[1]) + 1) if '-' in part \
              else ([int(part)] if part.isdigit() else [])
        for p in rng: page2art.setdefault(p, []).append(f)

listings = ' '.join(' '.join(norm(io.open(f, encoding='utf-8', errors='replace').read()))
                    for f in glob.glob(ISSUE + '/prg/*.txt'))

missing, kept_total = [], 0
for p, arts in sorted(page2art.items()):
    try:
        lab = json.load(open(f'{OCR}/{p:03d}.labels.json'))
    except FileNotFoundError:
        continue
    keep = {str(i) for i in lab.get('order', [])}
    if not keep: continue
    hay = ' '.join(arttext[a] for a in arts) + ' ' + listings
    for b in lab.get('blocks', []):
        if str(b.get('id')) not in keep: continue
        if str(b.get('label', '')).startswith('listing'): continue
        w = norm(b.get('text', ''))
        if len(w) < MIN_WORDS: continue
        kept_total += 1
        probes = [' '.join(w[i:i+SHINGLE]) for i in range(0, len(w) - SHINGLE, max(1, len(w)//12))]
        hit = sum(1 for pr in probes if pr in hay)
        if probes and hit / len(probes) < THRESH:
            missing.append((p, b.get('label'), round(hit/len(probes), 2), len(w),
                            ' '.join(w[:16]), [a.split('/')[-1][:30] for a in arts]))

print(f'pages {len(page2art)}   kept prose blocks {kept_total}   UNACCOUNTED {len(missing)}'
      f'   ({100*len(missing)/max(1,kept_total):.1f}%)\n')
for p, lab, frac, n, txt, arts in missing:
    print(f'p{p:<4} {lab:<9} match={frac:<5} words={n:<4} {arts}')
    print(f'      "{txt}…"')
