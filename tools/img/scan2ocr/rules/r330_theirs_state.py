#!/usr/bin/env python3
"""Two checks on a 330 record: findings carry their state, references agree with it.

Run from r330's Verification block over `issues/<ID>/LOG.md` and
`issues/<ID>/reviewed/r330-theirs.txt`.

    $PY tools/img/scan2ocr/rules/r330_theirs_state.py \
        "issues/$ID/LOG.md" "issues/$ID/reviewed/r330-theirs.txt" || fail=1

CHECK A -- every THEIRS FINDING carries its own disposition word.

  A finding is an entry whose DISPOSITION is THEIRS, which in both records is
  written `THEIRS` followed by an optional parenthetical and then an em dash:
  `- D-022 THEIRS — 8506 p18 reads …`, or, for one with no D number of its
  own, `… | side finding inside <code> THEIRS (flag: program lines) — …`.

  Three shapes have each defeated a simpler version of this check:

  1. The state often wraps onto the NEXT line, so grepping the `- D-NNN
     THEIRS` line alone failed a correctly recorded finding.

  2. A SIDE FINDING HAS NO D NUMBER. A difference inside a block the diff
     dispositioned MOVED or MARKUP, or inside `<pre>`/`<code>` which it does
     not compare at all, is written "side finding inside <code> THEIRS", and a
     pattern anchored on `- D-` never sees it. MEASURED on SH8607: of four
     applied side findings, three carried `APPLIED` only in a comment ABOVE
     the group. **A state in a group header is not a state** -- whoever greps
     for a finding reads its own line, not the comment above its neighbours.

  3. AN ENTRY MUST END WHERE THE NEXT BEGINS. Ending it only at a blank line
     made four consecutive one-line findings match as ONE entry, so the last
     one's `APPLIED` satisfied the check for all four -- exit 0 on the very
     file holding the defect it was written for.

  And the counterpart: matching `THEIRS` anywhere flagged 103 entries on
  SH8607's LOG that merely MENTION one -- `(grp6.png; THEIRS applied …)`,
  "not raised as THEIRS", `**THEIRS applied**` table headings, `THEIRS: 0`
  counts. Hence disposition position, not mere presence.

WHAT THIS DOES NOT CHECK, AND WHY IT IS NOT HERE.

  The failure that actually keeps happening is the one next door: the verdict
  changes and THE PROSE BESIDE IT DOES NOT. SH8607 produced three in one day --
  a mark's description still carrying the old reading (d5e98cc3), a head saying
  "NOT yet blind-read, recorded as UNRESOLVED at D-375…D-379" after both the
  reading and the remap, and four MARKUP lines still pointing at "D-280…D-284
  (UNRESOLVED, THEIRS candidate)" after the candidate was closed.

  A draft of this script checked it: every `D-NNN` named inside an entry must
  exist and must carry the disposition the reference claims. **It cannot work,
  because D numbers are PER PAIR and LOG.md holds 23 of them** -- D-280 exists
  in several pairs with different dispositions, so the first match wins and the
  check reports "calls D-280 THEIRS, but its entry is PRINT" about two
  unrelated pairs. On SH8607 it produced four true hits and six cross-pair
  false ones, and a check whose output must be sifted is a check people learn
  to ignore -- which is exactly what the 103 false positives above did.

  Pair-scoping it means parsing LOG.md's section structure, which is not worth
  a script. So it stays a READING step in r330: after any remap, re-read every
  entry that names another D number. See *A REMAP LEAVES REFERENCES STALE* there.
"""
import re
import sys

STATE = re.compile(r'REPORTED|APPLIED|declined|CLOSED|refuted|UNCONFIRMED')
# THEIRS in DISPOSITION position: optional "(...)" then an em/en dash
FINDING = re.compile(r'\bTHEIRS\b(?:\s*\([^)]*\))?\s*[—–]')
START = re.compile(r'^(?:`|- D-\d)')


def entries(text):
    """One record per finding or log item, however it is laid out."""
    cur = []
    for line in text.splitlines():
        if not line.strip() or START.match(line):
            if cur:
                yield '\n'.join(cur)
            cur = [line] if line.strip() else []
        else:
            cur.append(line)
    if cur:
        yield '\n'.join(cur)


def skip(entry):
    head = entry.lstrip()
    return (head.startswith('#')          # a header comment
            or head.startswith('|')       # a summary-table row
            or head.startswith('**'))     # a heading, not a finding


def main(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    bad = 0
    for entry in entries(text):
        if skip(entry):
            continue
        if FINDING.search(entry) and not STATE.search(entry):
            if not bad:
                print(f'  {path}: THEIRS finding with no state word of its own:')
            print('   ', entry.splitlines()[0][:110])
            bad = 1
    return bad


if __name__ == '__main__':
    sys.exit(max(main(p) for p in sys.argv[1:]))
