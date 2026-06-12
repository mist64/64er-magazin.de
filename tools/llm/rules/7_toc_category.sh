#!/bin/bash
# Fill the 64er.toc_category meta in every article HTML for an issue,
# driven by a {filename -> category} mapping read from stdin.
#
# Usage:
#   tools/llm/rules/7_toc_category.sh <issue-dir> < mapping.tsv
#
# Mapping rows: <filename>\t<category>
# - empty category means "" (used for the editorial)
# - blank lines and lines starting with '#' are ignored
# - <category> must equal a line in <issue-dir>/toc.txt (or be empty)
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <issue-dir> < mapping.tsv" >&2
  exit 1
fi
issue_dir="$1"
# Use python3 -c so the inline source code doesn't consume our stdin
# (which carries the mapping TSV).
python3 -c "$(cat <<'PY'

import os, re, sys
issue_dir = sys.argv[1]
toc_path = os.path.join(issue_dir, 'toc.txt')
if not os.path.exists(toc_path):
    sys.exit(f"missing {toc_path}")
toc = {ln.strip() for ln in open(toc_path, encoding='utf-8') if ln.strip()}

# 1. read mapping
mapping = {}
for ln in sys.stdin:
    ln = ln.rstrip('\n')
    s = ln.strip()
    if not s or s.startswith('#'): continue
    if '\t' not in ln:
        sys.exit(f"mapping row missing TAB: {ln!r}")
    fn, _, cat = ln.partition('\t')
    fn = fn.strip(); cat = cat.strip()
    if fn in mapping:
        sys.exit(f"duplicate filename in mapping: {fn!r}")
    mapping[fn] = cat

# 2. validate
disk = {f for f in os.listdir(issue_dir) if f.endswith('.html')}
orphans = disk - set(mapping)
missing = set(mapping) - disk
if orphans: sys.exit(f"files in {issue_dir} not in mapping: {sorted(orphans)}")
if missing: sys.exit(f"mapping entries not on disk: {sorted(missing)}")
bad = sorted({c for c in mapping.values() if c and c not in toc})
if bad: sys.exit(f"categories not in toc.txt: {bad}")

# 3. apply
placeholder_re = re.compile(
    r'    <!-- <meta name="64er\.toc_category" content="XXX"> -->'
)
existing_re = re.compile(
    r'    <meta name="64er\.toc_category" content="[^"]*">'
)
changed = 0
for fn, cat in mapping.items():
    fp = os.path.join(issue_dir, fn)
    s = open(fp, encoding='utf-8').read()
    new_line = f'    <meta name="64er.toc_category" content="{cat}">'
    if placeholder_re.search(s):
        s2 = placeholder_re.sub(new_line, s, count=1)
    elif existing_re.search(s):
        s2 = existing_re.sub(new_line, s, count=1)
    else:
        sys.exit(f"{fp}: no placeholder or existing toc_category line")
    if s2 != s:
        open(fp, 'w', encoding='utf-8').write(s2)
        changed += 1
print(f"updated {changed} of {len(mapping)} file(s) in {issue_dir}")
PY
)" "$issue_dir"

# 4. stage rewritten files
git add -u "$issue_dir"
