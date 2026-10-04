#!/usr/bin/env python3
"""r310 — whole-issue invariants.  Needs ONLY issues/<YYMM>/.

Per-rule Verification blocks answer "did this step do its job", and they run
when that step runs — so they cannot see an invariant a LATER step breaks.
This one runs at the end, over the finished issue, and re-checks everything
regardless of which rule last touched a file.

HARD failures must be zero and exit non-zero.  SOFT findings are a triage list:
each has a known false-positive population documented beside it, because the
recurring mistake is "fixing" a product name, a German compound or a print typo.

usage:  r310_issue_invariants.py [issues/<ID>] [--soft]
        With no path it uses r000_issue's selected issue (rules/ISSUE.txt).
"""
import glob, io, os, re, sys
from html.parser import HTMLParser


# THE ADJUDICATION MARKER IS GERMAN, because the comment it lives in is.
# Every HTML comment in this corpus is written in German and addressed to a
# reader of this edition -- the owner's rule, and the hand-built issues' practice
# long before anyone wrote it down.  The marker used to be the English word
# PRINTED, which forced an English comment around it: a rule that says "put this
# English token in a comment" is a rule that says "write the comment in English",
# and three chain-built issues learned exactly that (8611 22 of 22 English,
# SH8601 14 of 16, 8612 26 of 26 before the rewrite), several with crop
# coordinates and step numbers in them.
#
# "So im Heft gedruckt" is what the corpus already says for this -- it reads as a
# note to a reader rather than a token for a checker -- and "Abweichung vom
# Druck" for the case where this edition knowingly differs.  PRINTED stays
# recognised so the six comments already carrying it (8610, 8611, SH8601) keep
# passing.  It is legacy, not a second option to pick from.
ADJUDICATED = (r'<!--(?:(?!-->).)*'
               r'(?:\bPRINTED\b|So im Heft gedruckt|Abweichung vom Druck)'
               r'(?:(?!-->).)*-->\s*$')

# A MECHANICAL ADJUDICATION IS NOT AN EDITORIAL NOTE, AND DOES NOT BELONG IN THE
# PAGE.  Two different things were using one mechanism.  An editorial note --
# "the printed table gives Busy on pin 16, the schematic has it right on 11" --
# is written for whoever reads the source and belongs in the file.  A mechanical
# adjudication -- "yes, this heading really does end with a full stop" -- says
# only that the gate already asked and the answer was yes, and it ended up in
# the file because a comment was the only channel this gate had.
#
# MEASURED on 8612: 26 comments, of which 14 were mechanical and TEN of those
# were the identical sentence in one article, one per heading the gate flagged.
# They ship: the live page for 8610 serves its comment as written.
#
# So the mechanical ones move to <issue>/adjudicated.txt, one line per CLASS
# rather than per instance, and the file carries the reason a person would want:
#
#     # finding-key        n   reason
#     heading-ends-period  10  alle zehn Zwischenüberschriften so gedruckt
#     byline-split          1  Einzeiler vor der Autorenzeile, so gedruckt
#
# A `#` comment line and blank lines are ignored.  `n` is the count the build
# adjudicated; it is recorded so a later run that finds MORE of them says so
# instead of silently inheriting an old blessing.
ADJ_FILE = 'adjudicated.txt'


def adjudications(issue_dir):
    """{finding-key: (count, reason)} from <issue>/adjudicated.txt, or {}."""
    path = os.path.join(issue_dir, ADJ_FILE)
    out = {}
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except OSError:
        return out
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        parts = ln.split(None, 2)
        if len(parts) < 2:
            continue
        key, n = parts[0], parts[1]
        out[key] = (int(n) if n.isdigit() else 0, parts[2] if len(parts) > 2 else '')
    return out


def ADJUDICATED_HERE(body, pos, adj, key, seen):
    """An adjudication, from adjudicated.txt OR from a comment in the page.

    The file is the normal channel; a comment still counts so the editorial
    notes that legitimately live in a page (a print error with the right value
    beside it) keep working, and so 8610/8611/SH8601 keep passing unchanged.
    Returns the reason, or '' when there is none.
    """
    if key in adj:
        seen[key] = seen.get(key, 0) + 1
        return adj[key][1] or 'so gedruckt'
    if re.search(ADJUDICATED, body[max(0, pos - 400):pos], re.S):
        return 'im Text vermerkt'
    return ''

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
    # Mechanical adjudications live beside the issue, not in its pages.
    ADJ = adjudications(d)
    adj_seen = {}
    hard, soft = [], []
    H = lambda k, f, x='': hard.append((k, os.path.basename(f), x))
    S = lambda k, f, x='': soft.append((k, os.path.basename(f), x))
    ids, arts = {}, list(articles(d))
    # The issue's kind, for the checks that only apply to one. A directory with
    # no descriptor (an issue imported before this chain) is treated as unknown
    # and those checks are skipped rather than guessed at.
    ISS_KIND = 'unknown'
    try:
        import json
        ISS_KIND = json.load(open(os.path.join(d, 'issue.json')))['kind']
    except Exception:
        pass
    if not arts: print('FAIL: no articles found — wrong directory?'); return 2

    for f, s, body in arts:
        prose = re.sub(r'<pre.*?</pre>', '', body, flags=re.S)

        # --- HARD: markup shape ---------------------------------------------
        if st := unbalanced(s): H('unbalanced tags', f, str(st[:3]))
        for _ in re.finditer(r'<ol[^>]*type=', body):  H('<ol type=> (Discount alpha-list bug, r060)', f)
        for _ in re.finditer(r'<p>\s*<pre', body):     H('<p><pre> (Discount fenced-code bug, r060)', f)
        for _ in re.finditer(r'<li>\s*<p>', body):     H('<li> wraps <p>', f)
        # NEVER SPLIT THE AUTHOR AWAY FROM THE TEXT THEY WROTE -- not by a
        # listing, a table, an image or an aside.  The byline belongs directly
        # after the article's last paragraph; anything the layout floats in
        # between belongs before that paragraph or after the byline.
        # r190 had this for images and tables only, which is why five cases
        # survived here -- <pre> and <aside> were not covered.
        # MEASURED on SH8601: 5, separated by <pre>, <figure>, <table> and
        # combinations of them.
        # ...EXCEPT where the print itself sets it that way, which happens in
        # the tip rubrics: a tip ends with the two monitor lines or the four
        # program lines it is about, and THEN the byline.  Moving that block
        # below the byline to satisfy this check inverts the page.  MEASURED on
        # 8610 p94, `Tip zu INPUT`: the print reads "...ist die verbesserte
        # INPUT-Anweisung aktiviert." / ">0419 34 39 2b 28" / ">0545 00 04" /
        # "(Daniel Neukomm/tr)".  So the same PRINTED marker that adjudicates a
        # heading's trailing period adjudicates this: an HTML comment carrying
        # the word PRINTED, within the 400 characters before the block, saying
        # what was read off the page.  It downgrades to soft -- still listed,
        # never silent.
        for mm in re.finditer(r'<address class="author">', body):
            pre_ = body[:mm.start()]
            lastp = pre_.rfind('</p>')
            if lastp < 0: continue
            tail = pre_[lastp + 4:]
            broke = re.findall(r'<(figure|table|pre|aside)\b', tail, re.I)
            if broke:
                start = lastp + 4 + tail.lower().index('<' + broke[0].lower())
                adj = ADJUDICATED_HERE(body, start, ADJ, 'byline-split', adj_seen)
                if adj:
                    S('<%s> before the byline — adjudicated: %s (r190)'
                      % (broke[0], adj), f)
                else:
                    H('<%s> splits the byline from its text (r190)' % broke[0], f)
        # A NUMBERED LIST TORN IN HALF.  The OCR hands r030 a numbered list as
        # one prose blob; Discount then promotes whichever item happens to fall
        # at a line start into an <ol> and leaves the rest inline in the <p>.
        # Which item that is depends on arbitrary wrapping, so the reader sees
        # "1. 2. 1.".  MEASURED on SH8601: four in `139 Tips und Tricks`, one in
        # `6 Rundgang`.  A one-item <ol> is the tell -- the magazine does not
        # print numbered lists of one.
        #
        # THE GATE SAYS THERE IS A TEAR; IT DOES NOT SAY WHICH REPAIR.  Two
        # different printed shapes produce the same one-item <ol>:
        #   * a CONTIGUOUS list -- items back to back after an intro ending in a
        #     colon.  Repair: one <ol>, printed markers stripped.
        #   * numbered RUN-IN HEADINGS -- each item is a flush-left line ending
        #     in a colon whose own explanation (paragraphs, a listing, even an
        #     <h2>) follows before the next item.  Repair: plain <p> keeping the
        #     printed numeral, as article 125 already sets them.  Merging these
        #     into one <ol> would drag item 2 up over its own explanation and
        #     silently REORDER the article.
        # MEASURED on SH8601: five tears, two contiguous and three run-in.  READ
        # THE PAGE before choosing.
        #
        # Verified across the corpus: all 16 hits are real tears -- each has a
        # preceding <p> ending in a colon, or is a numbered step.  8606/86 is
        # the extreme case, SIX consecutive one-item <ol> rendering as "1." six
        # times.
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

        # The bare \d{1,2} matches any intro opening with a number, and a
        # correct one often does -- SH8602/159 "20 KByte adressierbarer
        # Speicher ...".  It called H() DIRECTLY, so neither adjudicated.txt
        # nor a note in the page could clear it: the same defect class as the
        # old printed-period check.  Now it skips a number followed by a unit,
        # and anything left goes through the adjudication path.
        UNIT = re.compile(r'^\d{1,2}\s+(?:[KMG]?Byte|KB|MB|Bit|Zeichen|Spalten|'
                          r'Zeilen|Sekunden|Minuten|Jahre|Mark|DM|Prozent|%)\b')
        for mm in re.finditer(r'<p class="intro">((?:Gier|Test|64\'er|\d{1,2}|-F\])\s[^<]{0,60})', body):
            if UNIT.match(mm.group(1)):
                continue
            if ADJUDICATED_HERE(body, mm.start(), ADJ, 'badge-intro', adj_seen):
                continue
            H('badge bled into the intro (r280)', f, mm.group(1)[:34])
        # An adjudicated exception is expressed IN THE FILE, next to the thing
        # it excuses.  A heading whose trailing period was READ off the master
        # carries an HTML comment saying so within the 400 characters before it;
        # without this, a verified-printed period can never be cleared and the
        # gate can never honestly reach zero, which is how a gate stops being
        # read.  The word PRINTED (upper case, in a comment) is the marker, and
        # it must state what was verified and how -- see r290.
        printed_ok = lambda pos: bool(
            ADJUDICATED_HERE(body, pos, ADJ, 'heading-ends-period', adj_seen))
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
        # r250 tags a source footer from the MEASURED type size, which is
        # blind to a footer set in ordinary body type -- and to one a later
        # step moved. 8610 p173 ends on a bare <p> naming the distributor and
        # its Postfach, printed in the small type, untagged. The shape is
        # narrow enough to check: the LAST block of the article, short, and
        # it names a company form or a Postfach. FP population: an article
        # that genuinely ends on a sentence about a company.
        tail_p = re.findall(r'<p(?![^>]*class=)[^>]*>((?:(?!</p>).){0,220})</p>\s*'
                            r'(?:<address[^>]*>[^<]*</address>\s*)?$', body, re.S)
        for t in tail_p:
            if re.search(r'\b(GmbH|AG|KG|OHG|Verlag|Postfach|Ltd|Inc)\b', t):
                S('article ends on an untagged contact footer (r250)', f, t[:34])

        # --- German addresses, pre-1993 ------------------------------------
        # A West German address of the period is "<4-digit PLZ> <Stadt>" and,
        # for a city with several Zustellpostaemter, a district NUMBER after
        # the city: "8013 Haar bei Muenchen", but "4000 Duesseldorf 30",
        # "2000 Hamburg 76", "4300 Essen 1".  That number is bare digits and
        # nothing else, which makes it a perfect OCR trap: it stands alone at
        # the end of a line, so no word context can correct it, and the
        # confusions are the classic ones -- 3/S, 5/S, 0/O, 1/l/|, 8/B.
        # MEASURED on 8610: 2 of 7 were wrong ("Duesseldorf SO", "Essen |"),
        # both invisible to every spelling check.
        #
        # Both checks look ONLY at text that already names a street, a
        # Postfach or a Verlag/GmbH, within the 120 characters before the
        # PLZ.  Without that gate a bare "\d{4} <Word> <token>" matches BASIC
        # line numbers, prices and print specs -- MEASURED over 8604-8609:
        # 60 findings, 12 of them addresses; with the gate, 9 findings, 9
        # addresses.
        ADDR_CTX = (r'(?:[\wäöüß.\-]*(?:stra(?:ss|ß)e|str\.|weg|platz|gasse|allee|ring)'
                    r'|Postfach|Verlag|GmbH|KG|AG)')
        for mm in re.finditer(ADDR_CTX + r'[^<]{0,120}?'
                              r'\b\d{4}\s+[A-ZÄÖÜ][\wäöüß.\-]+'
                              r'(?:\s+(?:a\.|b\.|am|an|bei|im)\s+[A-ZÄÖÜ][\wäöüß.\-]+)*'
                              r'\s+([^\s<.,;:)]{1,2})(?=[\s.,;:)<]|$)', prose):
            if not mm.group(1).isdigit():
                S('district code after the city is not a number (r280)', f, mm.group(0)[-30:])
        # A postal address is SET AS A BLOCK, one element per line.  OCR joins
        # the lines into one paragraph and nothing downstream can tell the
        # result from prose -- it is grammatical-looking German.  The tell is
        # a street with a house number running straight into a PLZ, no comma
        # between them.  MEASURED on 8610: 1 hit, p150, a real defect; the
        # comma-separated run-in form the magazine also uses does not match.
        for mm in re.finditer(r'(?i)\b[\wäöüß.\-]*(?:stra(?:ss|ß)e|str\.|weg|platz|gasse|allee|ring)'
                              r'\s*\d+[a-z]?\s+\d{4}\s+[A-ZÄÖÜ]', prose):
            S('street runs into the PLZ — address block flattened into prose?', f, mm.group(0)[:36])

        if 'name="author"' not in s and '<address class="author">' not in body:
            S('no author at all — read the last page, a dropped final line takes the byline (r180)', f)

    # --- a monthly has an Editorial ---------------------------------------
    # Same shape as the Impressum and harder to see: on 8611 the Editorial was
    # not dropped, it was ABSORBED. Step 020 read p8 as one text under "# Start"
    # (OCR took only the first word of "Start frei ..."), 030 and 080 then glued
    # it to the front of the Messebericht, and the Chefredakteur's sign-off ran
    # into the next article mid-paragraph. No coverage check can see that: the
    # page is claimed, every word is present, nothing is missing -- there is
    # simply one article where there were two.
    # MEASURED over the corpus: 33 monthlies carry exactly one id="editorial",
    # none carries two, and every Sonderheft carries none. It is always p8.
    if ISS_KIND == 'monthly':
        ed = [f for f, s_, b in arts
              if re.search(r'name="64er\.id"\s+content="editorial"', s_)]
        if len(ed) != 1:
            H('monthly has %d Editorial articles, expected exactly 1 (r080)'
              % len(ed), os.path.basename(d),
              ', '.join(os.path.basename(x) for x in ed[:3]))

    # --- the magazine's own name ----------------------------------------
    # 64'er and 128'er take an APOSTROPHE. OCR reads it as a double quote and
    # r070 then straightens that to ", giving 64"er -- grammatical-looking,
    # invisible in a proof-read, and the highest-frequency proper noun in the
    # corpus. MEASURED over every published issue: exactly TWO occurrences,
    # 8610 p9 (shipped) and 8611 mid-build. 0 false positives, so HARD.
    # Both spellings of the apostrophe are accepted: the corpus uses ASCII '
    # and U+2019 about equally and neither is wrong.
    for mm in re.finditer(r'\b(?:64|128)["\u201c\u201d\u201e\u00ab\u00bb]er', prose):
        H("the magazine's name takes an apostrophe, not a quote (r070/r280)",
          f, mm.group(0))

    # --- the issue has an Impressum -------------------------------------
    # A masthead reads like a list, so step 020's prompt grouped it with the
    # table of contents and the corpus dropped it -- silently, because ~90
    # kept-nothing pages is normal in an issue half full of ads, so a missing
    # Impressum hides inside a legitimate population. It was rebuilt BY HAND on
    # 8610 and SH8601 and lost outright on 8611 before anyone noticed a pattern.
    # The prompt is fixed; this is the check that says so next time.
    # MEASURED over the corpus: 41 of 41 published issues carry exactly one,
    # and no issue carries two. 0 false positives.
    imp = [f for f, s_, b in arts
           if re.search(r'name="64er\.id"\s+content="impressum"', s_)]
    if len(imp) != 1:
        H('issue has %d Impressum pages, expected exactly 1 (r020)' % len(imp),
          os.path.basename(d), ', '.join(os.path.basename(x) for x in imp[:3]))

    # --- the Impressum is BUILT, not just transcribed --------------------
    # The masthead prints as a list of labelled entries with rules between
    # groups, and the whole text can be present while none of that structure is:
    # 8611 shipped the complete text as NINE run-together paragraphs, 105 words
    # in the first, no <em> labels and no <hr>. Every other check passed -- the
    # words are all there, so coverage, spelling and markup see nothing.
    # MEASURED over 41 Impressum pages: paragraphs median 36, and the lowest
    # besides 8611's 9 is 16. Label marking is <em> in the monthlies and
    # <strong> in the Sonderhefte, median 32; only 8611 and SH8504 have none.
    for f, s_, b in arts:
        if not re.search(r'name="64er\.id"\s+content="impressum"', s_):
            continue
        body = s_[s_.find('<article'):]
        paras = len(re.findall(r'<p[ >]', body))
        labels = len(re.findall(r'<em[ >]', body)) + len(re.findall(r'<strong[ >]', body))
        if paras < 12:
            H('Impressum has %d paragraphs; the masthead is one per printed entry'
              % paras, f, 'structure never built')
        elif labels < 10:
            S('Impressum marks %d labels; the print sets them bold' % labels, f, '')

    # --- every <img> target exists --------------------------------------
    # generate.py skips a missing image SILENTLY (os.path.exists guard before
    # the avif/jpg conversion), so a <figure> written against a file that was
    # never cut passes the build gate and ships a broken image. Nothing else in
    # the chain looks at this. MEASURED over the whole corpus: exactly ONE,
    # 8605/87's 87-0.png, shipped. 0 false positives, so HARD.
    for f, s_, b in arts:
        for mm in re.finditer(r'<img[^>]+src="([^"]+)"', s_):
            src = mm.group(1)
            if src.startswith(('/', 'http', 'data:')):
                continue
            if not os.path.exists(os.path.join(d, src)):
                H('<img> target does not exist (the build skips it silently)',
                  f, src)

    # ------------------------------------------------------------------
    # Four checks added from 8612's review. Every one of these defects was
    # found by the OWNER READING, and nothing in the chain could see them.
    # ------------------------------------------------------------------

    # 1. An ASIDE HEADING MUST NOT OUTRANK ITS ARTICLE (r190/r290).
    #    h2 is correct when the body has h2 sections of its own; it is wrong
    #    when the aside would hold the file's only h2, or would outrank a body
    #    built from h3. 8612: article 8's §202a box, article 91's bio box.
    for f, s_, b in arts:
        asides = re.findall(r'<aside\b.*?</aside>', b, re.S)
        if not asides:
            continue
        outside = b
        for a in asides:
            outside = outside.replace(a, ' ')
        body_levels = {int(x) for x in re.findall(r'<h([23])\b', outside)}
        for a in asides:
            # Rule 300's erratum box is a STANDARD element, not the article's
            # own aside, and the corpus sets it h2 in 20 of 20 cases. Not this
            # check's business. (r290 claims it uses h3; the corpus disagrees.)
            if re.search(r'class="[^"]*(?:future|fehler)teufelchen', a):
                continue
            for lv in {int(x) for x in re.findall(r'<h([23])\b', a)}:
                if lv == 2 and 2 not in body_levels:
                    H('aside heading outranks its article (h2, body has no h2)',
                      f, re.sub(r'<[^>]+>', '', (re.search(r'<h2[^>]*>(.*?)</h2>', a, re.S)
                                                 or re.match('', '')).group(1)
                                if re.search(r'<h2[^>]*>(.*?)</h2>', a, re.S) else '')[:40])

    # 1b. 64er.issue must be M/YY (monthly) or "Sonderheft N/YY".
    #     SH8601 shipped its directory name as the key for all 29 articles,
    #     because r080 showed the Sonderheft form only in a usage example.
    #     The key is generate.py's dictionary key and code parses its shape.
    ISSUE_KEY = re.compile(r'^(\d{1,2}/\d{2}|Sonderheft \d{1,2}/\d{2})$')
    for f, s_, b in arts:
        mm = re.search(r'64er\.issue" content="([^"]*)"', s_)
        if mm and not ISSUE_KEY.match(mm.group(1)):
            H('64er.issue is not M/YY or "Sonderheft N/YY"', f, mm.group(1)[:30])

    # 2. A <p> THAT IS ONLY A PAGE POINTER is the layout speaking, not the
    #    author, and is never transcribed (r080). 8612 kept "Anleitung auf
    #    Seite 58"; 8611/50 kept "Listing auf Seite 54". A sweep of 8612 found
    #    16 "auf Seite N" and exactly ONE was a pointer, so this must match the
    #    WHOLE paragraph, never a substring.
    PTR = re.compile(r'^\s*(?:\w+\s+)?(?:auf|von)\s+Seite\s+\d+\s*\.?\s*$', re.I)
    for f, s_, b in arts:
        for mm in re.finditer(r'<p[^>]*>(.*?)</p>', b, re.S):
            txt = re.sub(r'<[^>]+>', '', mm.group(1)).replace('&nbsp;', ' ')
            if PTR.match(txt):
                H('<p> is only a page pointer (layout, not text)', f, txt.strip()[:40])

    # 3. TWO ARTICLES MUST NOT SHARE A BARE START PAGE (r080). They get
    #    lettered pages NNNa / NNNb in printed order. 8611 was lettered on
    #    instruction and it never became a rule, so 8612 repeated it twice
    #    (169 and 193) and the owner caught both.
    starts = {}
    for f, s_, b in arts:
        mm = re.search(r'64er\.pages" content="([^"]+)"', s_)
        if not mm:
            continue
        first = mm.group(1).split(',')[0].strip().split('-')[0].strip()
        if re.match(r'^\d+$', first):
            starts.setdefault(first, []).append(f)
    for pg, fs in sorted(starts.items()):
        if len(fs) > 1:
            for f in fs:
                H('two articles share bare start page (needs NNNa/NNNb)', f, 'p' + pg)

    # 4. A <br> INSIDE A <td> is usually the printed COLUMN's wrap, not the
    #    author's line break, and is not reproduced (r160/r190). SOFT: an
    #    author's break in a cell is legitimate, so this is a list to read,
    #    not a failure. 8612 shipped 283 of these before the owner's review.
    for f, s_, b in arts:
        n = sum(len(re.findall(r'<br\s*/?>', c))
                for c in re.findall(r'<td\b[^>]*>(.*?)</td>', b, re.S))
        if n:
            S('<br> inside a <td> (column wrap, or the author\'s?)', f, '%d' % n)

    for k, f, x in hard: print(f'HARD  {k:<52} {f[:40]} {x}')
    if '--soft' in sys.argv:
        for k, f, x in soft: print(f'soft  {k:<52} {f[:40]} {x}')
    # A blessing that no longer matches what is on the page is not a blessing.
    # If adjudicated.txt says ten and the pages now hold twelve, two were never
    # looked at -- say so rather than let the file silently cover them.
    for key, (n, why) in sorted(ADJ.items()):
        got = adj_seen.get(key, 0)
        if n and got != n:
            print(f'ADJ   {key:<24} declared {n}, found {got}'
                  f'{"  -- MORE than adjudicated" if got > n else ""}')
    if ADJ:
        print(f'adjudicated.txt: {len(ADJ)} class(es), '
              f'{sum(adj_seen.values())} instance(s) matched')

    print(f'\narticles {len(arts)}   HARD {len(hard)}   soft {len(soft)}'
          f'{"" if "--soft" in sys.argv else "  (--soft to list)"}')
    return 1 if hard else 0

if __name__ == '__main__':
    # DEFAULT TO THE SELECTED ISSUE. This used to fall back to a hard-coded
    # 'issues/8609', so a bare `r310_issue_invariants.py` audited 8609 and
    # reported ITS findings -- on 8612 that was "articles 55 HARD 4", four
    # r190 byline splits in articles that do not exist in 8612. Every other
    # rule in the chain takes the issue from r000_issue; now so does this.
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        target = sys.argv[1]
    else:
        import r000_issue
        # rules/ -> scan2ocr/ -> img/ -> tools/ -> repo root
        _repo = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
        target = os.path.join(_repo, 'issues', r000_issue.ISSUE)
    sys.exit(main(target))
