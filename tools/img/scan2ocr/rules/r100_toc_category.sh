#!/bin/bash
# Fill the 64er.toc_category meta in every article HTML for an issue,
# driven by a {filename -> category} mapping read from stdin.
#
# Usage:
#   tools/img/scan2ocr/rules/r100_toc_category.sh <issue-dir> < mapping.tsv
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
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_BIN="${PYTHON:-$DIR/../../../../.venv/bin/python}"
issue_dir="$1"

# THE BODY GOES TO A FILE, NOT THROUGH $( ... ).  It used to be
# python3 -c "$(cat <<'PY' ... PY)" -- the command substitution so that the
# inline source would not eat our stdin, which carries the mapping TSV.
# macOS /bin/bash is 3.2 and it SCANS INSIDE $( ... ) even when the heredoc
# there is quoted, so a backtick or an apostrophe in a PYTHON COMMENT broke
# the whole script: bash -n failed with "unexpected EOF while looking for
# matching quote" and it ran only under Homebrew bash 5.  Both SH8603 and
# SH8604 hit it, and patching out the offending characters one by one leaves
# the next comment to re-break it.  A heredoc written to a file is not
# scanned, keeps stdin free, and ends the class.
body=$(mktemp -t r100_body)
trap 'rm -f "$body"' EXIT
cat > "$body" <<'PY'

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
        # Name what we touched, so step 4 can stage exactly that.
        # "git add -u <dir>" stages EVERY tracked modification in the dir --
        # on 8612 it swept WORKFLOW_ERRATA.md into this step's commit.
        open(os.path.join(issue_dir, '.r100_staged'), 'a', encoding='utf-8').write(fp + "\n")
print(f"updated {changed} of {len(mapping)} file(s) in {issue_dir}")
PY
"$PY_BIN" "$body" "$issue_dir"

# 4. stage ONLY the files this step rewrote (never "git add -u <dir>": r000's
#    rule on self-staging scripts and a shared index)
if [ -s "$issue_dir/.r100_staged" ]; then
  tr '\n' '\0' < "$issue_dir/.r100_staged" | xargs -0 git add --
  rm -f "$issue_dir/.r100_staged"
else
  echo "  nothing rewritten -- nothing staged"
fi
