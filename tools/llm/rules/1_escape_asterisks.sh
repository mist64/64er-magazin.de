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
def esc(m):
    n = len(m.group(0))
    return m.group(0) if n == 2 else '\\*' * n
s = re.sub(r'\*+', esc, s)
open(fp, 'w', encoding='utf-8').write(s)
# report
solo = len(re.findall(r'(?<!\\)(?<!\*)\*(?!\*)', s))
runs = len(re.findall(r'\*{3,}', s))
bold = len(re.findall(r'\*\*[^*]+?\*\*', s))
print(f"{fp}: solitary={solo}  3+runs={runs}  **bold** pairs={bold}")
PY
