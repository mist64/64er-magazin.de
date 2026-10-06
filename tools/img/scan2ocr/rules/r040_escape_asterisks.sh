#!/bin/bash
# Escape literal '*' in a 64'er OCR markdown file.
# Rule: contiguous runs of length exactly 2 stay (** = bold delimiter);
# all other run lengths get every '*' escaped to '\*'.
# In-place rewrite, idempotent.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
if [ -z "$1" ]; then
  echo "usage: $0 <md-file>" >&2
  exit 1
fi
"$PY" - "$1" <<'PY'
import re, sys
fp = sys.argv[1]
s = open(fp, encoding='utf-8').read()

# BOTH ESCAPES ARE FOR DISCOUNT'S INLINE PARSER, WHICH DOES NOT RUN INSIDE A
# FENCE.  Applied there anyway, the escape is shipped LITERALLY: `10 A=B\*2`
# renders with the backslash visible, and `&lt;F1&gt;` inside a fence comes out
# as the text "&lt;F1&gt;" because 070 re-escapes the ampersand.  Nothing later
# in the chain strips either.  MEASURED on Discount 3.0.2 with r060's own flags,
# and on 8611: 4 fenced lines would have shipped a stray backslash and 2 would
# have shipped entity text -- inside LISTINGS, which are the one thing in this
# corpus that has to be byte-exact, because a reader types them in.
# Fenced regions are therefore passed through untouched.  ``` only: 030 emits
# no indented code blocks (MEASURED: 0 in 8611), and treating a 4-space indent
# as code would swallow ordinary continuation lines.
def map_outside_fences(s, fn):
    out, infence = [], False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            out.append(line)
            continue
        out.append(line if infence else fn(line))
    return ''.join(out)

def fence_flags(s):
    """(line, inside_a_fence) for every line, fences themselves counted inside."""
    infence = False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            yield line, True
            continue
        yield line, infence

def esc_hash(line):
    # A BODY LINE STARTING WITH '#' BECOMES AN ATX HEADING.  SH8603 p164 prints
    # a bullet wrapping onto "#1281/1282=$0501/0502." (# = decimal, against $);
    # Discount needs no space after the #, so 060 shipped
    # <h1>1281/1282=$0501/0502.</h1>, losing the # and creating a 52nd <h1>
    # that 080 splits articles on.
    #
    # THE TEST IS THE SPACE, nothing else.  A real ATX heading has whitespace
    # after the hashes; the defect is a hash run with none.  An earlier version
    # of this exempted only lines carrying "[digit", on the false belief that
    # 030 emits "# Title [pages]" and nothing else -- 030 also emits ## and ###
    # section headings, and that version escaped all 69 of SH8604's.
    # (?![#\s]) and not (?!\s): a greedy #+ backtracks.  On "## Heading" it
    # matches "##", fails the space lookahead, then backtracks to a single "#"
    # whose next char is "#" -- and escapes the heading after all.  Excluding
    # "#" from the lookahead stops the backtrack.
    return re.sub(r'^(\s*)(#+)(?![#\s])', lambda m: m.group(1) + '\\' + m.group(2), line)

def bullet(line):
    # A LINE-START "* " IS A BULLET, AND ONLY THERE.  r040's Notes used to claim
    # "list bullets in this project are always -, never *"; SH8602 found 9 such
    # lines and SH8603 13 (the printer checklist, pp47-49), escaped as the rule
    # said and left rendering as literal asterisks for 190 to rebuild by hand.
    #
    # Converting at the LINE START is safe; converting mid-line is not.  Measured
    # on SH8603's 030 handover, outside fences: 7 line-start "* " lines, all 7
    # bullets of that checklist -- and 7 lines with a mid-paragraph " * ", which
    # include "POKE 44,30:POKE 30 * 256,0:NEW".  A blanket swap would rewrite
    # BASIC multiplication into a dash that 070 then turns into an en dash.
    # (SH8604: 0 line-start, so this fires only where the shape is really there.)
    #
    # A run-together bullet list -- OCR glues the next item onto the previous
    # line, as on SH8603 p47 -- cannot be separated mechanically for the same
    # reason.  Those asterisks stay escaped and 190 rebuilds the list; see r190.
    return re.sub(r'^(\s*)\*(\s)', r'\1-\2', line)

def esc_gt(line):
    # A LINE-START '>' IS AN INTRO -- 030 marks an article's intro paragraph as
    # a Markdown blockquote, 060 makes it <blockquote><p> and 070 <p
    # class="intro">.  So a '>' there for any other reason silently becomes an
    # intro: SH8603's article 14 reported intros=2 because a C16 monitor prompt
    # did (">1000 1F 10 2B Bytes eingeben, zum Beispiel: D (ANFANG) (ENDE) =").
    #
    # Only the NO-SPACE form is mechanical, exactly as for '#': a blockquote
    # marker needs no space after it, and prose after '>' never omits one.
    # The spaced form cannot be told apart here -- SH8603's "> (ADRESSE)
    # (BYTES) =" is shaped like an intro -- so the summary reports every
    # line-start '>' and r080's intros>1 check is the backstop.
    return re.sub(r'^(\s*)>(?!\s)', r'\1\\>', line)

def esc_line(line):
    line = esc_hash(esc_gt(bullet(line)))
    # LENGTH 2 IS KEPT ONLY IF IT PAIRS ON THIS LINE.  The rule has said so
    # since the 8612 harvest; the code kept every length-2 run regardless, so
    # an unpaired ** shipped as a bold delimiter.  SH8602's Protext article
    # renders space padding as asterisks, giving one literal ** per line, and
    # every fence-aware check read 0 because a pair count cannot see it.
    pairs = len(re.findall(r'(?<!\\)\*{2}(?!\*)', line))
    keep2 = (pairs % 2 == 0)

    def esc(m):
        n = len(m.group(0))
        return m.group(0) if (n == 2 and keep2) else '\\*' * n

    # (?<!\\) keeps idempotent: skip runs already preceded by '\'
    return re.sub(r'(?<!\\)\*+', esc, line)

s = map_outside_fences(s, esc_line)
open(fp, 'w', encoding='utf-8').write(s)
# Report.  THE SUMMARY MUST BE AS FENCE-AWARE AS THE TRANSFORM, which is the
# same failure the rule's Verification docstring warns about: counting the whole
# file, this printed "solitary=2" on SH8603 for two asterisks it had correctly
# left alone inside listings, i.e. it reported correct output as a defect.
t = ''.join('' if f else line for line, f in fence_flags(s))
solo = len(re.findall(r'(?<!\\)(?<!\*)\*(?!\*)', t))
runs = len(re.findall(r'\*{3,}', t))
bold = len(re.findall(r'\*\*[^*]+?\*\*', t))
bull = sum(1 for line in t.splitlines() if re.match(r'^\s*- ', line))
gt = [line.rstrip()[:70] for line in t.splitlines() if re.match(r'^\s*>', line)]
print(f"{fp}: solitary={solo}  3+runs={runs}  **bold** pairs={bold}  bullets={bull}"
      f"  intros={len(gt)}   (outside fences)")
# EVERY LINE-START '>' IS PRINTED.  Each one becomes a <p class="intro">, so
# each has to be an intended intro.  MEASURED on the handovers: SH8603 45,
# SH8604 17; SH8603's set held two monitor lines among the real intros.
for line in gt:
    print(f"    intro?: {line}")
PY
