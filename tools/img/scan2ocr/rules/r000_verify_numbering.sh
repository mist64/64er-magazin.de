#!/bin/bash
# Verification for the numbering itself -- rule 000 requires every change to
# ship with one, and a renumber is exactly the kind of change whose damage is
# invisible until someone follows a dead reference months later.
cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." || exit 1
# THE REPO VENV, NOT BARE python3 (CLAUDE.md, r000).  This wrapper used to
# invoke `python3` by name, so it ran on whichever python was first on PATH --
# it worked only because its body happens to be stdlib-only, and r000's sweep
# had fixed the Verification FENCES and never the wrapper BODIES (SH8608).
R000_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$R000_DIR/../../../../.venv/bin/python}"

D=tools/img/scan2ocr/rules
fail=0

echo "1. file naming"
# Every file in here is rNNN_name.{md,sh,py}, with no exceptions.  000 is the
# number for things that are not a step but apply to every step: the
# orchestration spec, this check, and the model transport.  The r prefix exists
# so that a step file is also a legal Python module name -- 010_ocr_blocks is
# not importable by name, r010_ocr_blocks is.
# "NO EXCEPTIONS" WAS NOT TRUE, AND THIS CHECK WAS PERMANENTLY RED BECAUSE OF
# IT.  The comment above already names three files that are not steps -- the
# harvest record, this check's own directory furniture, and the model transport
# -- and the grep exempted none of them, so check 1 reported
# `BAD NAMES: HARVEST.md ISSUE.txt LOCAL_MODELS.md template_64er_600.png`,
# set fail=1, and made this whole verifier exit non-zero on a correct tree.
# An exit code that is always 1 tells you nothing, and it hides every other
# finding below it (r000, A GATE THAT ALWAYS REPORTS STOPS BEING READ).
# So the exceptions are a LIST, here, and anything not on it is still a defect.
NOT_STEPS='^(HARVEST\.md|ISSUE\.txt|LOCAL_MODELS\.md|template_64er_600\.png)$'
bad=$(ls $D | grep -v '^__pycache__$' | grep -vE "$NOT_STEPS" \
        | grep -vE '^r[0-9]{3}_[a-z0-9_]+\.(md|sh|py)$' | tr '\n' ' ')
if [ -n "$bad" ]; then echo "   BAD NAMES: $bad"; fail=1
else echo "   all $(ls $D | grep -v '^__pycache__$' | grep -vE "$NOT_STEPS" | wc -l | tr -d ' ') step files match rNNN_name.{md,sh,py}, plus 4 known non-step files"; fi

echo "2. every rNNN_name.{md,sh,py} reference resolves"
n=0
for ref in $(grep -rhoI --exclude-dir=__pycache__ -E '[/ "(]r?[0-9]{3}_[a-z0-9_]+\.(md|sh|py)\b' $D tools/img/scan2ocr/README.md 2>/dev/null | sort -u); do
  ref=${ref##*[/ \"(]}; if [ ! -f "$D/$ref" ]; then echo "   DANGLING: $ref"; fail=1; else n=$((n+1)); fi
done
echo "   $n distinct references resolve"

echo "3. no old-style or removed-rule file reference"
old=$(grep -rhoI --exclude-dir=__pycache__ -E '\b[0-9]{1,2}b?_[a-z0-9_]+\.(md|sh)\b' $D | sort -u | tr '\n' ' ')
if [ -n "$old" ]; then echo "   OLD-STYLE REFS: $old"; fail=1; else echo "   none"; fi

echo "4. every 'step NNN' reference resolves"
for num in $(grep -rhoI --exclude-dir=__pycache__ -E '\b[Ss]tep [0-9]{3}\b' $D | grep -oE '[0-9]{3}' | sort -u); do
  ls $D/r${num}_* >/dev/null 2>&1 || { echo "   DANGLING step $num"; fail=1; }
done
echo "   ok"

echo "5. no old-numbering reference in any spelling"
# The first renumber missed rule-9, rules 10/12, (27) and rules 0-28 because the
# regex demanded "rule" + a space + one noun.  Every form the audit found is
# covered here; a form that is not covered is a form that will silently rot.
left=$(grep -rhoI --exclude-dir=__pycache__ --exclude="$(basename "${BASH_SOURCE[0]}")" -E \
  "[Rr]ules?[- ][0-9]{1,2}([/,–-][0-9]{1,2})*\b" $D \
  | grep -vE "[Rr]ules?[- ](0[0-9][0-9]|[0-9]{3})" | sort -u | tr '\n' ' ')
if [ -n "$left" ]; then echo "   REVIEW: $left"; fail=1; else echo "   none"; fi

echo "8. every H1 number matches its filename"
"$PY" - "$D" <<'PY2' || fail=1
import glob, os, re, sys
d = sys.argv[1]; bad = []
for f in sorted(glob.glob(os.path.join(d, "r[0-9][0-9][0-9]_*.md"))):
    num = os.path.basename(f)[1:4]
    first = open(f, encoding="utf-8").readline()
    m = re.match(r"^# (\d+b?) ", first)
    # A LETTERED STEP'S H1 CARRIES THE LETTER, and the filename cannot.
    # r005_a4_window.md is step 005b and says so in its H1; comparing against
    # the bare three digits flagged it on every run, so this check was red on
    # a correct tree too.
    if not m or m.group(1) not in (num, num + "b"):
        bad.append(f"{os.path.basename(f)} -> {first.strip()[:40]!r}")
print("   " + ("; ".join(bad) if bad else "all H1 numbers match"))
sys.exit(1 if bad else 0)
PY2

echo "9. every repo path a rule names exists"
"$PY" - "$D" <<'PY3' || fail=1
import glob, os, re, sys
d = sys.argv[1]; root = os.path.abspath(os.path.join(d, "..", "..", "..", ".."))
bad = set()
pat = re.compile(r"`(tools/[A-Za-z0-9_./-]+)`")
for f in sorted(glob.glob(os.path.join(d, "r*.md"))):
    body = open(f, encoding="utf-8").read()
    for p in pat.findall(body):
        p = p.rstrip(".")
        if not os.path.exists(os.path.join(root, p)):
            bad.add(f"{os.path.basename(f)}: {p}")
print("   " + ("; ".join(sorted(bad)) if bad else "all named tools/ paths exist"))
sys.exit(1 if bad else 0)
PY3

echo "10. the three program steps' verification blocks import cleanly"
(cd "$D" && "$PY" -c "
import r010_ocr_blocks, r020_classify, r030_assemble, r010_blocks_index
print('   4 step modules import')" ) || fail=1

echo "6. nothing from issues/ is staged"
if git diff --cached --stat -- issues/ | tail -1 | grep -q .; then
  echo "   STAGED history/unrelated!"; fail=1
else echo "   clean"; fi

echo "7. every step .py parses"
"$PY" - "$D" <<'PY' || fail=1
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
