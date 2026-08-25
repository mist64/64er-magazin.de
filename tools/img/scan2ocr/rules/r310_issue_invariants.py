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

def opening_paragraphs(body, n=2):
    """The article's first n prose paragraphs, tags stripped.

    An ornamental initial that OCR never recovered leaves the ARTICLE'S FIRST
    WORDS truncated (`enn beim`, `ur Programmierung`), which is valid HTML and
    grammatical-looking German -- no markup or spelling gate can see it.  The
    window is two paragraphs, not one: the truncated one is usually the first
    body paragraph AFTER a standfirst, and a standfirst is sometimes marked
    `class="intro"` and sometimes a bare <p>, so neither "the first" nor "the
    first non-intro" alone finds them all.  MEASURED on SH8601: two catches all
    17, one catches 1, first-non-intro catches 15.
    """
    out = []
    for mm in re.finditer(r'<p(?: class="intro")?>(.*?)</p>', body, re.S):
        t = re.sub(r'<[^>]+>', '', mm.group(1)).strip()
        if t: out.append(t)
        if len(out) >= n: break
    return out


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
        # A NUMBERED LIST TORN IN HALF.  The OCR hands r030 a numbered list as
        # one prose blob; Discount then promotes whichever item happens to fall
        # at a line start into an <ol> and leaves the rest inline in the <p>.
        # Which item that is depends on arbitrary wrapping, so the reader sees
        # "1. 2. 1.".  MEASURED on SH8601: four in `139 Tips und Tricks`, one in
        # `6 Rundgang`.  A one-item <ol> is the tell -- the magazine does not
        # print numbered lists of one.
        for mm in re.finditer(r'<ol[^>]*>((?:(?!</ol>).)*)</ol>', body, re.S):
            if len(re.findall(r'<li\b', mm.group(1))) == 1:
                H('<ol> with a single <li> — numbered list torn in half? (r060)', f)
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
        # An adjudicated exception is expressed IN THE FILE, next to the thing
        # it excuses.  A heading whose trailing period was READ off the master
        # carries an HTML comment saying so within the 400 characters before it;
        # without this, a verified-printed period can never be cleared and the
        # gate can never honestly reach zero, which is how a gate stops being
        # read.  The word PRINTED (upper case, in a comment) is the marker, and
        # it must state what was verified and how -- see r290.
        printed_ok = lambda pos: bool(
            re.search(r'<!--(?:(?!-->).)*\bPRINTED\b(?:(?!-->).)*-->\s*$',
                      body[max(0, pos - 400):pos], re.S))
        for mm in re.finditer(r'<h([2-6])>([^<]*)</h\1>', body):
            t = mm.group(2).rstrip()
            # an ellipsis is legitimate and the magazine sets it both ways:
            # "Die LED brennt, aber..." and "Farbausfall, Bildausfall . . ."
            # legitimate endings: an ellipsis ("Die LED brennt, aber...",
            # "Farbausfall, Bildausfall . . .") and a trailing abbreviation
            # ("1. SCREEN nr." heads a numbered command list in 8605/29)
            if t.endswith('.') and not re.search(r'\.\s?\.\s?\.$', t) \
                    and not re.search(r'\b[A-Za-zÄÖÜäöü]{1,3}\.$', t):
                if printed_ok(mm.start()):
                    S('heading ends "." — annotated as PRINTED, verified (r290)', f, t[:40])
                else:
                    H('heading is a paragraph tail (r290)', f, t[:40])

        # --- the article's opening: a drop cap the OCR never saw -------------
        # MEASURED on SH8601: 17 of 29 articles opened with a truncated first
        # word.  r010's splice only repairs an initial tesseract DETECTED; where
        # it detected none, the letter is simply absent and everything downstream
        # reads as valid prose.
        for t in opening_paragraphs(body):
            # No legitimate population in 1724 published articles: a stray sigil
            # or a letter+colon standing where the initial belongs.  SH8601 had
            # `$ ie glauben` for `Sie glauben` and `D: große` for `Die große`.
            if re.match(r'[$&%§#@*]\s', t) or re.match(r'[A-ZÄÖÜ][:;]\s', t):
                H('article opens with an initial stub (r010 drop cap)', f, t[:34])
            # Lowercase openings DO have a legitimate population -- the magazine
            # runs a headline into its first sentence (`Warum...` / `sieht die
            # 64'er diesmal`, `3D-Joystick-Grafik` / `ist ein Programm fuer`).
            # 10 in 1724 articles, 7 of them that idiom -- so SOFT, but read
            # every one: the same sweep found `esonders dem` for `Besonders dem`
            # in a published issue.
            elif re.match(r'[a-zäöüß]', t):
                S('article opens lowercase — drop cap never OCR\'d? (FP: headline runs into the text)', f, t[:34])

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
