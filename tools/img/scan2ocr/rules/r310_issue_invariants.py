#!/usr/bin/env python3
"""r310 — whole-issue invariants.  Needs ONLY issues/<YYMM>/.

Per-rule Verification blocks answer "did this step do its job", and they run
when that step runs — so they cannot see an invariant a LATER step breaks.
This one runs at the end, over the finished issue, and re-checks everything
regardless of which rule last touched a file.

HARD failures must be zero and exit non-zero.  SOFT findings are a triage list:
each has a known false-positive population documented beside it, because the
recurring mistake is "fixing" a product name, a German compound or a print typo.

usage:  r310_issue_invariants.py issues/8609 [--soft]
"""
import glob, io, os, re, sys
from html.parser import HTMLParser

VOID = {'img', 'br', 'meta', 'link', 'hr', 'input'}
# SOFT allow-lists — verified legitimate, do NOT "fix" these
OK_JAM = {'HiRes', 'TurboAss', 'StarTexter', 'StarDatei', 'SpeedDos', 'KoalaPrinter',
          'GeoWrite', 'HesWare', 'LowRes', 'VizaWrite', 'ComPrint', 'LSname'}

def articles(d):
    for f in sorted(glob.glob(os.path.join(d, '*.html'))):
        s = io.open(f, encoding='utf-8').read()
        i = s.find('<article')
        yield f, s, (s[i:s.rfind('</article>')] if i >= 0 else s)

def unbalanced(html):
    class P(HTMLParser):
        def __init__(self): super().__init__(); self.st = []
        def handle_starttag(self, t, a):
            if t not in VOID: self.st.append(t)
        def handle_endtag(self, t):
            if self.st and self.st[-1] == t: self.st.pop()
            elif t in self.st: self.st.remove(t)
    p = P(); p.feed(html); return p.st

def main(d):
    hard, soft = [], []
    H = lambda k, f, x='': hard.append((k, os.path.basename(f), x))
    S = lambda k, f, x='': soft.append((k, os.path.basename(f), x))
    ids, arts = {}, list(articles(d))
    if not arts: print('FAIL: no articles found — wrong directory?'); return 2

    for f, s, body in arts:
        prose = re.sub(r'<pre.*?</pre>', '', body, flags=re.S)

        # --- HARD: markup shape ---------------------------------------------
        if st := unbalanced(s): H('unbalanced tags', f, str(st[:3]))
        for _ in re.finditer(r'<ol[^>]*type=', body):  H('<ol type=> (Discount alpha-list bug, r060)', f)
        for _ in re.finditer(r'<p>\s*<pre', body):     H('<p><pre> (Discount fenced-code bug, r060)', f)
        for _ in re.finditer(r'<li>\s*<p>', body):     H('<li> wraps <p>', f)
        n1 = len(re.findall(r'<h1>', body))
        if n1 != 1 and 'Leserforum' not in f:          H(f'h1 count = {n1}', f)
        m = re.search(r'64er\.id" content="([^"]*)"', s)
        if not m: H('no 64er.id', f)
        elif m.group(1) in ids: H(f'duplicate 64er.id "{m.group(1)}"', f, ids[m.group(1)])
        else: ids[m.group(1)] = os.path.basename(f)

        # --- HARD: the closing run is a unit --------------------------------
        blocks = [(mm.start(), mm.group(1)) for mm in
                  re.finditer(r'<(figure|table|p class="source"|address class="author")\b', body)]
        for i, (_, k) in enumerate(blocks):
            if k in ('p class="source"', 'address class="author"') and i and blocks[i-1][1] in ('figure', 'table'):
                H(f'<{blocks[i-1][1]}> splits the closing run', f)

        # --- HARD: OCR classes with no legitimate population -----------------
        for mm in re.finditer(r'\b(?:Bild|Tabelle|Listing)\s+\]', prose): H('"] " for digit 1 (r280)', f)
        for mm in re.finditer(r'®', prose):                                H('® for ? (r280)', f)

        for mm in re.finditer(r'<p class="intro">(?:Gier|Test|64\'er|\d{1,2}|-F\])\s', body):
            H('badge bled into the intro (r280)', f)
        for mm in re.finditer(r'<h([2-6])>([^<]*)</h\1>', body):
            t = mm.group(2).rstrip()
            # an ellipsis is legitimate and the magazine sets it both ways:
            # "Die LED brennt, aber..." and "Farbausfall, Bildausfall . . ."
            if t.endswith('.') and not re.search(r'\.\s?\.\s?\.$', t):
                H('heading is a paragraph tail (r290)', f, t[:40])

        # --- SOFT: triage, each with a documented FP population -------------
        for mm in re.finditer(r'<p(?: class="intro")?>([a-zäöüß][a-zäöüß]*)\b', body):
            S('paragraph starts lowercase — eaten drop cap? (FP: keyword lists)', f, mm.group(1))
        for mm in re.finditer(r'\b[A-Za-zÄÖÜäöüß]{3,}[a-zß](?=[A-ZÄÖÜ])[A-ZÄÖÜ][a-zäöüß]{3,}', prose):
            if mm.group(0) not in OK_JAM: S('lost space? (FP: product names)', f, mm.group(0))
        # OCR over-segmentation of one initial glyph: DDer, WWichtig, BBrillant.
        # SOFT, not HARD — a legitimate population exists (command mnemonics with
        # a placeholder tail, e.g. 8606's "Rechten Rand setzen RRxxx").
        for mm in re.finditer(r'\b([A-ZÄÖÜ])\1[a-zäöüß]{2,}', prose):
            S('doubled initial capital — OCR split one glyph? (FP: RRxxx mnemonics)', f, mm.group(0)[:24])
        for mm in re.finditer(r'\bC(?:64|128|16|116)\b', prose):
            S('model name without space (FP: print really omits it)', f, mm.group(0))
        for mm in re.finditer(r'<p class="source">(?:(?!</p>).)*?<br(?:(?!</p>).)*?</p>', body, re.S):
            if mm.group(0).count('<br') < 2: S('<br> in a running Info: footer — column wrap?', f)
        for mm in re.finditer(r'[^<>]{15,}\((?:[a-z]{2,3}|[A-ZÄÖÜ][^()<>]{2,28}/[a-z]{2,3})\)</p>', body):
            S('byline glued to a paragraph (FP: Impressum masthead)', f, mm.group(0)[-34:])
        # dangling cross-reference: text cites "Bild 3"/"Tabelle 2"/"Listing 4"
        # with no such caption. A reference with no target usually means the
        # figure and its caption were dropped together.
        # EXEMPT: an article with exactly ONE such caption, left unnumbered by
        # the print, satisfies a reference to "<kind> 1" — 8609's 95 cites
        # "(Listing 1)" (confirmed on p95) while its sole caption reads
        # "Listing »Hardcopy« …". That mismatch is the magazine's own.
        caps = ' '.join(re.findall(r'<figcaption>(.*?)</figcaption>', body, re.S))
        nocap = re.sub(r'<figcaption>.*?</figcaption>', '', body, flags=re.S)
        # an erratum aside cites the CORRECTING issue's listings, not this
        # article's ("Folgende Zeilen (Listing 2) …" in a 1/87 erratum)
        nocap = re.sub(r'<aside class="fehlerteufelchen".*?</aside>', '', nocap, flags=re.S)
        for kind in ('Bild', 'Tabelle', 'Listing'):
            refs = {m.group(1) for m in re.finditer(kind + r'\s+(\d{1,2})\b', nocap)}
            have = {m.group(1) for m in re.finditer(kind + r'\s+(\d{1,2})\b', caps)}
            n_caps = len(re.findall(kind + r'\b', caps))
            if refs and not have and n_caps == 1 and refs == {'1'}:
                continue                      # the sole unnumbered caption IS "1"
            for miss in sorted(refs - have):
                if have:                      # only meaningful once some are numbered
                    S(f'refers to {kind} {miss} but no such caption', f)

        if 'name="author"' not in s and '<address class="author">' not in body:
            S('no author at all — read the last page, a dropped final line takes the byline (r180)', f)

    for k, f, x in hard: print(f'HARD  {k:<52} {f[:40]} {x}')
    if '--soft' in sys.argv:
        for k, f, x in soft: print(f'soft  {k:<52} {f[:40]} {x}')
    print(f'\narticles {len(arts)}   HARD {len(hard)}   soft {len(soft)}'
          f'{"" if "--soft" in sys.argv else "  (--soft to list)"}')
    return 1 if hard else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'issues/8609'))
