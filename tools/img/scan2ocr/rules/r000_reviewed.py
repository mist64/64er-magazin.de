"""A LIST-GATE REPORTS THE DELTA, NOT THE LIST.

r000: A GATE THAT ALWAYS REPORTS STOPS BEING READ.  Several checks in this
chain are not pass/fail at all -- they hand the operator a list to eyeball,
and a legitimate issue produces a non-empty one every single run.  On SH8603:

  * r160 check 5 printed 8 lines, every one a Bild photo reference or an
    unnumbered printed "Tabelle." that the prose calls "Tabelle 1";
  * r160 check 7 printed 6, every one a named-box caption that r160 ITSELF
    requires ("Variablenliste", "Programmaufbau", "Programmablaufplan:",
    "Variable", "Zusammenfassung der Bedienung des Programms:",
    "Tabellarische Uebersicht");
  * r290 check 2 labelled every non-h2 aside heading a possible erratum box
    although r290's own header prescribes h3 for them.

A list that is correct and non-empty cannot be "fixed", so it gets skimmed,
and the one new line in it gets skimmed too.  The remedy is not to weaken the
check or to enumerate a closed vocabulary it cannot have: it is to record what
was looked at, and report only what is new since.

    <issue>/reviewed/<key>.txt      one item per line, '#' comments allowed

THE FILE MUST BE COMMITTED, or the mechanism is pointless: the next build has
no baseline to compare against and the gate reports its whole list again.
`issues/` is whitelist-governed (`issues/*/*` ignores everything, with
exceptions), and that pattern ignores the DIRECTORY, so git never descends
into it -- `.gitignore` therefore carries `!issues/*/reviewed/`, next to the
`!issues/*/prg/` that does the same job for the disk files.  Found on SH8604,
after the records had been written and silently not committed.

This is the per-INSTANCE companion to r310's per-CLASS adjudicated.txt.  Use
adjudicated.txt when a whole finding class is blessed with a count; use this
when the gate's output is an open list the operator walks item by item.

Usage from a rule's Verification block, run from the repo root:

    import sys; sys.path.insert(0, 'tools/img/scan2ocr/rules')
    import r000_reviewed as R
    new = R.delta('issues/SH8603', 'r160-table-refs', items)
    R.report('r160 check 5', new, len(items))
"""

import os


def _path(issue_dir, key):
    return os.path.join(issue_dir, 'reviewed', key + '.txt')


def recorded(issue_dir, key):
    """The set of items already walked and confirmed for this key."""
    try:
        lines = open(_path(issue_dir, key), encoding='utf-8').read().splitlines()
    except OSError:
        return set()
    return {ln.strip() for ln in lines if ln.strip() and not ln.startswith('#')}


def delta(issue_dir, key, items):
    """`items` minus what is recorded, order preserved, duplicates collapsed."""
    seen, known, out = set(), recorded(issue_dir, key), []
    for it in items:
        it = str(it).strip()
        if it in seen or it in known:
            continue
        seen.add(it)
        out.append(it)
    return out


def record(issue_dir, key, items, why=''):
    """Append items to the baseline.  The operator runs this after walking them."""
    p = _path(issue_dir, key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'a', encoding='utf-8') as f:
        if why:
            f.write('# %s\n' % why)
        for it in items:
            f.write('%s\n' % str(it).strip())
    return p


def report(label, new, total, issue_dir=None, key=None):
    """Print the delta, and say how to record it.  Returns 1 if anything is new.

    THE COUNT OF ALREADY-REVIEWED ITEMS IS PRINTED TOO.  A silent gate is as
    unreadable as a noisy one: if the baseline has quietly swallowed the whole
    list, the operator has to be able to see that from the output.
    """
    old = total - len(new)
    if not new:
        print('  %s: %d item(s), all previously reviewed' % (label, total))
        return 0
    print('  %s: %d NEW of %d (%d previously reviewed)'
          % (label, len(new), total, old))
    for it in new:
        print('    %s' % it)
    if issue_dir and key:
        print('    -- walk each, then record them:')
        print('       $PY -c "import sys; sys.path.insert(0,'
              '\'tools/img/scan2ocr/rules\'); import r000_reviewed as R; '
              'R.record(\'%s\', \'%s\', sys.stdin.read().splitlines(), \'<why>\')"'
              % (issue_dir, key))
    return 1
