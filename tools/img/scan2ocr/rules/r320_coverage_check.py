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

That exclusion leaves a hole, and it has been fallen into: a page that carries
NOTHING BUT one article's listing is claimed by no 64er.pages, so it never
enters the reconciliation at all and its absence reads as silence.  8610's
Listing 3 filled p156-157 and the article's meta said "152-153, 155"; coverage
reported 0.0% unaccounted while two whole pages were unclaimed.  So the second
half of this check walks the page NUMBERS, 1..pages, and reports every one no
article claims.  Ads are the legitimate population and they are most of it --
the check prints the list, a human reads it, and a page with a listing on it
cannot hide in the middle of it.
"""
import glob, html, io, json, re, sys

import r000_issue
from r000_issue import ISSUE

# The ONE per-issue knob, imported from r000_issue as everywhere in scan2ocr.
# Both sides of the reconciliation come from it, which is the point: comparing
# one issue's OCR against another issue's HTML reports a coverage figure that
# means nothing, and it cannot happen while there is a single name to get wrong.
ISS = r000_issue.load(ISSUE)

ISSUE_DIR = sys.argv[1] if len(sys.argv) > 1 else ISS.issue_dir
OCR       = sys.argv[2] if len(sys.argv) > 2 else ISS.out_dir
SHINGLE, MIN_WORDS, THRESH = 4, 12, 0.25

norm = lambda t: re.sub(r'[^a-z0-9]+', ' ', t.lower()).split()

page2art, arttext = {}, {}
for f in sorted(glob.glob(ISSUE_DIR + '/*.html')):
    s = io.open(f, encoding='utf-8').read()
    m = re.search(r'64er\.pages" content="([^"]*)"', s)
    if not m: continue
    i = s.find('<article')
    # UNESCAPE AFTER STRIPPING TAGS, never before: &lt;F3&gt; unescaped first
    # becomes <F3> and is then removed as a tag. Without this the entity text
    # normalises to 'lt f3 gt' and never matches the OCR's 'f3', which both
    # invents false positives and hides a real one whose text turns on < > &.
    arttext[f] = ' '.join(norm(html.unescape(
        re.sub(r'<[^>]+>', ' ', s[i:s.rfind('</article>')] if i >= 0 else s))))
    # A LETTERED page ('169a', '193b') is r080's convention for two articles
    # sharing a start page. `part.isdigit()` is False for it, so both articles
    # claimed NO pages and p169's blocks fell to whichever article's range
    # covered 169 -- four spurious UNACCOUNTED findings on 8612. Strip the
    # suffix: the letter orders the two articles, it is not part of the page.
    def _pg(tok):
        mm = re.match(r'^(\d+)[a-z]?$', tok.strip())
        return int(mm.group(1)) if mm else None
    for part in m.group(1).split(','):
        part = part.strip()
        if '-' in part:
            lo, hi = (_pg(x) for x in part.split('-', 1))
            rng = range(lo, hi + 1) if lo is not None and hi is not None else []
        else:
            one = _pg(part)
            rng = [one] if one is not None else []
        for p in rng: page2art.setdefault(p, []).append(f)

listings = ' '.join(' '.join(norm(io.open(f, encoding='utf-8', errors='replace').read()))
                    for f in glob.glob(ISSUE_DIR + '/prg/*.txt'))

missing, kept_total, pages_read = [], 0, 0
for p, arts in sorted(page2art.items()):
    try:
        lab = json.load(open(f'{OCR}/{p:03d}.labels.json'))
    except FileNotFoundError:
        continue
    pages_read += 1
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

# A SWEPT <tmp> LOOKS EXACTLY LIKE A CLEAN ISSUE: every page raises
# FileNotFoundError, kept_total stays 0, and the old summary printed
# "UNACCOUNTED 0 (0.0%)" -- a pass, from a check that never ran. Say so and exit
# non-zero instead; the unclaimed-pages half below needs no OCR and still runs.
if pages_read == 0:
    print(f'CANNOT RUN: no <page>.labels.json under {OCR}')
    print('  The OCR intermediates are gone (swept <tmp>?). This half of the')
    print('  check reconciles kept blocks against the HTML and needs them.')
    print('  Rebuild them, or run this on an issue whose <tmp> still exists.\n')
else:
    print(f'pages {len(page2art)}   kept prose blocks {kept_total}   UNACCOUNTED {len(missing)}'
          f'   ({100*len(missing)/max(1,kept_total):.1f}%)\n')
for p, lab, frac, n, txt, arts in missing:
    print(f'p{p:<4} {lab:<9} match={frac:<5} words={n:<4} {arts}')
    print(f'      "{txt}…"')

# --- pages no article claims ------------------------------------------------
# Needs only the HTML and the descriptor, so it still runs when <tmp> has been
# swept away and the OCR output is gone -- which is when it is most useful.
unclaimed = [p for p in range(1, ISS.pages + 1) if p not in page2art]
print(f'\nUNCLAIMED PAGES {len(unclaimed)} of {ISS.pages} — ads are the legitimate '
      f'population; a listing or a figure here means some 64er.pages is short')
for p in unclaimed:
    what = ''
    try:
        lab = json.load(open(f'{OCR}/{p:03d}.labels.json'))
        keep = {str(i) for i in lab.get('order', [])}
        labels = sorted({str(b.get('label', '?')) for b in lab.get('blocks', [])
                         if str(b.get('id')) in keep})
        what = '  kept: ' + ', '.join(labels) if labels else '  kept: nothing'
    except FileNotFoundError:
        pass
    print(f'  p{p:<4}{what}')

# EXIT STATUS -- the comment above has said "exit non-zero" since it was
# written, and nothing ever did. This script exited 0 with UNACCOUNTED hits,
# exited 0 with a planted deletion, and exited 0 on CANNOT RUN, so every
# exit-code consumer read all three as a pass.
#
# UNCLAIMED PAGES is informational: ads are the legitimate population there,
# so it does not affect the status.
if pages_read == 0:
    sys.exit(2)      # could not run -- not a pass
if missing:
    sys.exit(1)      # real findings
