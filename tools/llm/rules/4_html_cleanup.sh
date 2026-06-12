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
if [ -z "$1" ]; then
  echo "usage: $0 <html-file>" >&2
  exit 1
fi
python3 - "$1" <<'PY'
import sys
fp = sys.argv[1]
s = open(fp, encoding='utf-8').read()
REPL = [
    ('<blockquote><p>',  '<p class="intro">'),
    ('</blockquote>',    ''),
    ('<br/>',            '<br>'),
    ("''",               '"'),
    # Unicode curly quotes -> straight
    ('‘', "'"), ('’', "'"),
    ('“', '"'), ('”', '"'), ('„', '"'),
    # HTML entities Discount could emit (defensive)
    ('&lsquo;', "'"), ('&rsquo;', "'"),
    ('&ldquo;', '"'), ('&rdquo;', '"'), ('&bdquo;', '"'),
]
for a, b in REPL:
    s = s.replace(a, b)
open(fp, 'w', encoding='utf-8').write(s)
# report
import subprocess
counts = {
    '<blockquote':       s.count('<blockquote'),
    'class="intro"':     s.count('class="intro"'),
    '<br/>':             s.count('<br/>'),
    '<br>':              s.count('<br>'),
    'curly remaining':   sum(s.count(c) for c in '‘’“”„'),
}
print(f"{fp}: " + ', '.join(f"{k}={v}" for k,v in counts.items()))
PY
git add "$1" 2>/dev/null || true
