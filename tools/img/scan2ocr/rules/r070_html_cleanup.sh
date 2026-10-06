#!/bin/bash
# Cleanup the post-Discount HTML for a 64'er issue:
#   <blockquote><p> -> <p class="intro">
#   </blockquote>   -> (removed)
#   <br/>           -> <br>
#   curly single/double quotes (Unicode + entities) -> straight ASCII
#   ''              -> "
# German guillemets «» are intentionally kept.
# In-place rewrite, idempotent.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
if [ -z "$1" ]; then
  echo "usage: $0 <html-file>" >&2
  exit 1
fi
"$PY" - "$1" <<'PY'
import sys
fp = sys.argv[1]
s = open(fp, encoding='utf-8').read()
REPL = [
    ('<blockquote><p>',  '<p class="intro">'),
    ('</blockquote>',    ''),
    ('<br/>',            '<br>'),
    # Unicode curly quotes -> straight.  THESE RUN FIRST.  With "''" -> '"'
    # ahead of them the script was NOT idempotent, though its rule claims it
    # is: TEDMON'’s folded to TEDMON''s on the first run and would become
    # TEDMON"s on a second.  Folding first makes one run final.
    ('‘', "'"), ('’', "'"),
    ('“', '"'), ('”', '"'), ('„', '"'),
    # ...and only then two straight apostrophes -> one double quote.
    # NOTE a double PRIME in a formula (P'') is legitimate and this eats it;
    # it survived on 8612 only by the ordering accident above.  If an issue
    # sets primes, exclude them before this step runs.
    ("''",               '"'),
    # HTML entities Discount could emit (defensive)
    ('&lsquo;', "'"), ('&rsquo;', "'"),
    ('&ldquo;', '"'), ('&rdquo;', '"'), ('&bdquo;', '"'),
]
for a, b in REPL:
    s = s.replace(a, b)

# ---- A SPACED DASH IN BODY TEXT IS AN EN DASH (owner, 2026-10-04) ----------
# The rule has required this since the SH8602 harvest and THIS SCRIPT NEVER DID
# IT, nor did the Verification check for it, so a run of the script alone passed
# 070 with 0 en dashes.  Both SH8603 and SH8604 had to write the pass by hand in
# a sub-agent (119 and 283 conversions), which also means the self-`git add`
# below staged half a step.
#
# NOT inside <pre> or <code>: a listing is typed in by a reader, and " - " there
# is a minus sign.  Blanked by length so every offset below stays valid.
import re as _re
PRE = _re.compile(r'<(pre|code)\b.*?</\1>', _re.S)
holes = [(m.start(), m.end()) for m in PRE.finditer(s)]
def in_hole(i):
    return any(a <= i < b for a, b in holes)

# WHAT STAYS A HYPHEN IS DECIDED BY THE FLANKS, NOT BY A WORD LIST.  Three
# shapes keep it, and they are measured against a 20-case fixture built from the
# published corpus plus the seven sites where SH8604's hand pass disagreed with
# an earlier version of this test (which scored 11/20; this scores 18/20, and
# the report below surfaces both remaining cases).
#
#   1. A RANGE OR ARITHMETIC: an operand on BOTH sides -- a number, a $ hex
#      address, a closing paren, or a BASIC numeric FUNCTION about to open one.
#      Keeps "$C0D6 - $C115", "(290 - 300)", "$7A00 - 7F20",
#      "(PEEK(45) + 256 * PEEK(46)) - 2)", "($CB00 - 1)", "1111 - 1024 > 80",
#      "POKE I,255 - PEEK(I)".
#      The function list is BASIC's, not a guess at what looks technical: with
#      the old [A-Z]{2,}\s*\( this also kept "C 64 - ACM (e.V.)", because an
#      acronym before a bracket is indistinguishable from PEEK(.
#   2. AN INDEXED ITEM ON BOTH SIDES -- "<Word> <number-or-letter>".  Keeps
#      SH8604's "gleich Satz 1 - Satz 3", "Mitte Satz 3 - Satz 3" and
#      "vom Raum O - MZ 1": record and index ranges whose flanks are words.
#   3. PROGRAM TEXT: an ALL-CAPS token on both sides.  Keeps SH8604's
#      "mit ON - GOTO" (a BASIC keyword pair), "1 REM * INDEX-MAKER - ERSTELLT"
#      (REM text in an unfenced listing) and "»WE WERE DISCUSSING YOU - NOT ME«"
#      (a program's printed output; PETSCII has one hyphen and no en dash).
#
# It converts "C 64 - Programmieren in Maschinensprache", "Vizawrite Classic
# 128 - Gutes noch besser?", "nicht vom ROM - das eventuell benötigt wird",
# "C 64 - ACM (e.V.)" and "S. 77 - View BAM" -- right in both directions.
#
# NOT skipping <p class="source">, which SH8604 proposed: measured, it holds
# bibliography and credits, and one of its 4 spaced hyphens corpus-wide is
# "F. Kassera: C 64 - Programmieren in Maschinensprache", which must convert.
# Shape 3 catches the INDEX-MAKER case that prompted the proposal.
_FN = (r'PEEK|ABS|INT|VAL|LEN|ASC|SIN|COS|TAN|ATN|EXP|LOG|SQR|RND|SGN|USR|'
       r'FRE|POS|TAB|SPC|CHR\$|LEFT\$|RIGHT\$|MID\$|STR\$')
OPERAND_L = _re.compile(r'(?:\$[0-9A-Fa-f]+|\d+|\))\s*$')
OPERAND_R = _re.compile(r'^\s*(?:\$[0-9A-Fa-f]+|\d+'
                        r'|(?:' + _FN + r')\s*\('
                        r'|[A-Z\xc4\xd6\xdc][\w.]*\s+\d)')
INDEXED_L = _re.compile(r'[A-Z\xc4\xd6\xdc][\w.]*\s+[A-Z0-9]+\s*$')
CAPS_L    = _re.compile(r'[A-Z\xc4\xd6\xdc][A-Z\xc4\xd6\xdc0-9$.\-]+\s*$')
CAPS_R    = _re.compile(r'^\s*[A-Z\xc4\xd6\xdc][A-Z\xc4\xd6\xdc0-9$.\-]+')

def keep_hyphen(L, R):
    if OPERAND_L.search(L) and OPERAND_R.match(R):   return True
    if INDEXED_L.search(L) and OPERAND_R.match(R):   return True
    if CAPS_L.search(L) and CAPS_R.match(R):         return True
    return False

# A CONVERSION THE FLANK TEST CANNOT SETTLE IS STILL PRINTED.  Two shapes, both
# measured: a bare number on the right -- which is a minus in
# "Es soll die Zahl - 12" but a prose dash in "25 Zeilen - 121 Farbtöne",
# "zu bleiben - 1000, 1024 oder 997 Durchläufe" and
# "Audio-/Video-Buchse - 6poliger AV-Stecker", so it cannot be decided here --
# and a dash inside a »...« quotation, which catches a program's printed output
# in mixed case (SH8604's "»We were discussing you - not me«").
def is_suspect(L, R):
    return bool(_re.match(r'\s*\d', R)) or ('\xbb' in L[-40:] and '\xab' in R[:40])

out, conv, skipped, suspects = [], 0, [], []
for m in _re.finditer(r' - ', s):
    if in_hole(m.start()):
        continue
    L, R = s[max(0, m.start() - 40):m.start()], s[m.end():m.end() + 40]
    if keep_hyphen(L, R):
        skipped.append((L[-26:] + ' - ' + R[:26]).replace('\n', ' '))
        continue
    if is_suspect(L, R):
        suspects.append((L[-30:] + ' - ' + R[:30]).replace('\n', ' '))
    out.append((m.start(), m.end()))
    conv += 1
for a, b in reversed(out):
    s = s[:a] + ' \u2013 ' + s[b:]

open(fp, 'w', encoding='utf-8').write(s)
# report
import subprocess
counts = {
    '<blockquote':       s.count('<blockquote'),
    'class="intro"':     s.count('class="intro"'),
    '<br/>':             s.count('<br/>'),
    '<br>':              s.count('<br>'),
    'curly remaining':   sum(s.count(c) for c in '‘’“”„'),
    'en dashes written':  conv,
    'hyphens kept':       len(skipped),
}
print(f"{fp}: " + ', '.join(f"{k}={v}" for k,v in counts.items()))
# EVERY KEPT HYPHEN IS PRINTED, because the flank test is a good default and not
# a verdict.  Two residue shapes it gets wrong, both seen in the corpus: a bare
# minus after a word ("Es soll die Zahl - 12"), and an OCR-spaced compound
# ("FOR..NEXT - Schleife"), which wants its hyphen CLOSED, not widened.
for x in skipped:
    print(f"    kept: {x}")
if suspects:
    print(f"  converted but NOT settled by the flank test: {len(suspects)}"
          " -- check each against the page")
    for x in suspects:
        print(f"    suspect: {x}")

# U+201A IS NEVER CORRECT IN THIS CORPUS AND IS NEVER FOLDED SILENTLY.
# U+201E, the German low DOUBLE, is a real quotation mark and folds above; this
# is the low SINGLE, and it is always an OCR error -- but of three different
# kinds, so no single replacement is right.  MEASURED over 1,825 articles: 38
# sites in 14 files, of which a COMMA ("ausnutzen ‚kann", "LOAD \"??Name*\" ‚8",
# "str(‚dv)", and "VOLDEF (n(‚n(‚n(,n))))" where the last comma survived as a real
# one), an OPENING QUOTE ("‚Computer Music'", "die ‚Reihe Taschenbuch"), and pure
# NOISE ("Dollar-‚Zeichen", "Joystick-‚Modus").  Resolve each against the page.
# finditer over the character itself, not a fixed-width pattern: two sites
# within 26 characters of each other overlap, and findall would report one.
low9 = [s[max(0, m.start() - 26):m.end() + 26].replace('\n', ' ')
        for m in _re.finditer('\u201a', s)]
if low9:
    print(f"  U+201A (low-9 single quote): {len(low9)} -- resolve each against the page")
    for x in low9:
        print(f"    {x}")
PY
git add "$1" 2>/dev/null || true
