#!/usr/bin/env python3
"""r280 — find words OCR welded together, using a German dictionary.

r310's jam check needs a CAPITAL at the seam ("derComputer"), because that
is the only seam a pure-pattern rule can see.  The seam that has no capital
is invisible to it and just as common: "warenalle", "darfnicht", "ganz-
rechts", "Tagzum".  Grammatical-looking German, valid HTML, no tell.

So this check asks a dictionary instead:

    a word the German dictionary does not know,
    which splits into two words it DOES know,
    is a jam.

Neither half alone is evidence -- German glues nouns together all day, and
"Diskettenbefehle" splits just as cleanly as "darfnicht".  What separates
them is the FIRST half's word class: a noun or a verb stem legitimately
compounds, a function word (nicht, doch, ganz, waren, eines, und, ...)
never does.  The tool cannot decide that, so it does not try -- it prints
the candidates and a human reads the list.  MEASURED on 8610: 245 unknown
lowercase words, 94 split candidates, 17 real jams; 1328 unknown
capitalised words, 135 candidates, 8 real jams.  A list that size is read
in two minutes, and it found every jam in the issue.

Needs aspell with the German dictionary (`brew install aspell`); the
dictionary is `de-alt`, the pre-1996 orthography, which is the magazine's
("daß", "muß") -- `de` reports every one of those as a misspelling.

usage:  r280_word_jams.py issues/8610
"""
import glob, io, os, re, subprocess, sys

DICT = 'de-alt'
# The word must stand alone: without these guards "Fachbegriff" yields the
# fragment "achbegriff", which splits into "ach"+"begriff" and looks like a
# jam.  MEASURED on 8610: the guards drop 2383 phantom words of 2628.
LOWER = re.compile(r'(?<![A-Za-zÄÖÜäöüß])[a-zäöüß]{9,}(?![A-Za-zÄÖÜäöüß])')
UPPER = re.compile(r'(?<![A-Za-zÄÖÜäöüß])[A-ZÄÖÜ][a-zäöüß]{8,}(?![A-Za-zÄÖÜäöüß])')


def prose(html):
    """Article text with listings, tables and markup removed."""
    i = html.find('<article')
    body = html[i:html.rfind('</article>')] if i >= 0 else html
    body = re.sub(r'<(pre|table|script|style)\b.*?</\1>', '', body, flags=re.S | re.I)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    return re.sub(r'<[^>]+>', ' ', body)


def unknown(words):
    """The subset aspell does not know. One call, not one per word."""
    if not words:
        return set()
    p = subprocess.run(['aspell', '-d', DICT, '--encoding=utf-8', 'list'],
                       input='\n'.join(words), capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit('aspell failed (brew install aspell): ' + p.stderr.strip())
    return set(p.stdout.split())


def jams(words):
    """(word, left, right) for every unknown word that splits into two known
    words.  The right half must start lower case: a capital there is r310's
    case, already reported, and "Tag"+"Zum" is not a word boundary anyway."""
    unk = sorted(unknown(words))
    cands = [(w, w[:i], w[i:]) for w in unk for i in range(3, len(w) - 2)]
    bad = unknown(sorted({p for _, a, b in cands for p in (a, b)}))
    out, seen = [], set()
    for w, a, b in cands:
        if w not in seen and a not in bad and b not in bad and b[0].islower():
            seen.add(w)
            out.append((w, a, b))
    return out


def main(d):
    lower, upper = {}, {}
    files = sorted(glob.glob(os.path.join(d, '*.html')))
    if not files:
        print('FAIL: no articles found — wrong directory?')
        return 2
    for f in files:
        t = prose(io.open(f, encoding='utf-8').read())
        for rx, bag in ((LOWER, lower), (UPPER, upper)):
            for w in rx.findall(t):
                bag.setdefault(w, set()).add(os.path.basename(f))
    n = 0
    for label, bag in (('lower case', lower), ('capitalised', upper)):
        found = jams(list(bag))
        print(f'\n--- {label}: {len(bag)} words, {len(found)} split candidates '
              f'--- read them; a function word on the left is a jam')
        for w, a, b in found:
            n += 1
            print('  %-28s -> %-14s %-14s  %s'
                  % (w, a, b, ', '.join(sorted(bag[w]))[:64]))
    print(f'\n{n} candidates to read.  This check never fails a build: every '
          f'finding needs a human, and the dictionary is the incomplete party.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'issues/8609'))
