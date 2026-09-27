#!/bin/bash
# Escape literal '*' in a 64'er OCR markdown file.
# Rule: contiguous runs of length exactly 2 stay (** = bold delimiter);
# all other run lengths get every '*' escaped to '\*'.
# In-place rewrite, idempotent.
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <md-file>" >&2
  exit 1
fi
python3 - "$1" <<'PY'
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

def esc(m):
    n = len(m.group(0))
    return m.group(0) if n == 2 else '\\*' * n
# (?<!\\) keeps idempotent: skip runs already preceded by '\'
s = map_outside_fences(s, lambda line: re.sub(r'(?<!\\)\*+', esc, line))
open(fp, 'w', encoding='utf-8').write(s)
# report
solo = len(re.findall(r'(?<!\\)(?<!\*)\*(?!\*)', s))
runs = len(re.findall(r'\*{3,}', s))
bold = len(re.findall(r'\*\*[^*]+?\*\*', s))
print(f"{fp}: solitary={solo}  3+runs={runs}  **bold** pairs={bold}")
PY
