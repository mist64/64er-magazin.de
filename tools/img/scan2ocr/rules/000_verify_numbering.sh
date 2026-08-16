#!/bin/bash
# Verification for the numbering itself -- rule 000 requires every change to
# ship with one, and a renumber is exactly the kind of change whose damage is
# invisible until someone follows a dead reference months later.
cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." || exit 1
D=tools/img/scan2ocr/rules
fail=0

echo "1. file naming"
# _step.py and llm.py are deliberately unnumbered: a loader and a transport,
# shared by several steps and belonging to none of them.
bad=$(ls $D | grep -v '^__pycache__$' | grep -vE '^([0-9]{3}_[a-z0-9_]+\.(md|sh|py)|_step\.py|llm\.py)$' | tr '\n' ' ')
if [ -n "$bad" ]; then echo "   BAD NAMES: $bad"; fail=1
else echo "   all $(ls $D | grep -v '^__pycache__$' | wc -l | tr -d ' ') files match NNN_name.{md,sh,py} (+ _step.py, llm.py)"; fi

echo "2. every NNN_name.{md,sh,py} reference resolves"
n=0
for ref in $(grep -rhoI --exclude-dir=__pycache__ -E '\b[0-9]{3}_[a-z0-9_]+\.(md|sh|py)\b' $D tools/img/scan2ocr/README.md 2>/dev/null | sort -u); do
  if [ ! -f "$D/$ref" ]; then echo "   DANGLING: $ref"; fail=1; else n=$((n+1)); fi
done
echo "   $n distinct references resolve"

echo "3. no old-style or removed-rule file reference"
old=$(grep -rhoI --exclude-dir=__pycache__ -E '\b[0-9]{1,2}b?_[a-z0-9_]+\.(md|sh)\b' $D | sort -u | tr '\n' ' ')
if [ -n "$old" ]; then echo "   OLD-STYLE REFS: $old"; fail=1; else echo "   none"; fi

echo "4. every 'step NNN' reference resolves"
for num in $(grep -rhoI --exclude-dir=__pycache__ -E '\b[Ss]tep [0-9]{3}\b' $D | grep -oE '[0-9]{3}' | sort -u); do
  ls $D/${num}_* >/dev/null 2>&1 || { echo "   DANGLING step $num"; fail=1; }
done
echo "   ok"

echo "5. no bare 'rule N' left in the old numbering"
left=$(grep -rhoI --exclude-dir=__pycache__ -E '\b[Rr]ule [0-9]{1,2}b?\b' $D | sort -u | tr '\n' ' ')
if [ -n "$left" ]; then echo "   REVIEW: $left"; else echo "   none"; fi

echo "6. nothing from issues/ or scan2mrc is staged"
if git diff --cached --stat -- issues/ tools/img/scan2mrc/ | tail -1 | grep -q .; then
  echo "   STAGED history/unrelated!"; fail=1
else echo "   clean"; fi

echo "7. every step .py parses"
python3 - "$D" <<'PY' || fail=1
import ast, glob, os, sys
d = sys.argv[1]
files = sorted(glob.glob(os.path.join(d, "*.py")))
bad = []
for f in files:
    try:
        ast.parse(open(f, encoding="utf-8").read())
    except SyntaxError as e:
        bad.append(f"{os.path.basename(f)}: {e}")
print("   " + ("; ".join(bad) if bad else f"{len(files)} .py files parse"))
sys.exit(1 if bad else 0)
PY

exit $fail
