#!/bin/bash
# Verification for the renumber (rule 000 requires every change to ship with one).
cd ~/Documents/git/64er-magazin.de || exit 1
D=tools/img/scan2ocr/rules
fail=0
echo "1. file count and naming"
bad=$(ls $D | grep -vE '^[0-9]{3}_[a-z0-9_]+\.(md|sh)$' | tr '\n' ' ')
[ -n "$bad" ] && { echo "   BAD NAMES: $bad"; fail=1; } || echo "   all $(ls $D|wc -l|tr -d ' ') files match NNN_name.{md,sh}"
echo "2. every NNN_name.md/sh reference resolves to a file that exists"
for ref in $(grep -rhoE '\b[0-9]{3}_[a-z0-9_]+\.(md|sh)\b' $D | sort -u); do
  [ -f "$D/$ref" ] || { echo "   DANGLING: $ref"; fail=1; }
done
echo "3. no reference to a removed or old-style rule file"
old=$(grep -rhoE '\b[0-9]{1,2}b?_[a-z0-9_]+\.(md|sh)\b' $D | sort -u | tr '\n' ' ')
[ -n "$old" ] && { echo "   OLD-STYLE REFS: $old"; fail=1; } || echo "   none"
echo "4. every 'step NNN' reference resolves"
for n in $(grep -rhoE '\b[Ss]tep [0-9]{3}\b' $D | grep -oE '[0-9]{3}' | sort -u); do
  ls $D/${n}_* >/dev/null 2>&1 || { echo "   DANGLING step $n"; fail=1; }
done
echo "5. no bare 'rule N' left pointing at the old numbering"
left=$(grep -rhoE '\b[Rr]ule [0-9]{1,2}b?\b' $D | sort -u | tr '\n' ' ')
[ -n "$left" ] && echo "   REVIEW: $left" || echo "   none"
echo "6. history untouched"
git diff --cached --stat -- issues/ tools/img/scan2mrc/ | tail -1 | grep -q . && { echo "   STAGED history/unrelated!"; fail=1; } || echo "   nothing from issues/ or scan2mrc is staged"
exit $fail
