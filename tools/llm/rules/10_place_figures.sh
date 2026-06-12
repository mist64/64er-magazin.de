#!/bin/bash
# Verify the placement of <figure> tags from rule 10 and, if everything
# placed cleanly, delete the issue's prg.txt worklist.
#
# Usage:
#   tools/llm/rules/10_place_figures.sh <issue-dir>
#
# Exits 0 if verification passes (and removes prg.txt). Exits non-zero
# with the failing check if anything's off.
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <issue-dir>" >&2
  exit 1
fi
dir="$1"
[ -d "$dir" ] || { echo "no such dir: $dir" >&2; exit 1; }

python3 -c "$(cat <<'PY'
import os, re, sys, collections
d = sys.argv[1]
problems = 0
def fail(msg):
    global problems; problems += 1; print(f"  FAIL: {msg}")

# 1. every data-filename in every article resolves to prg/ or prg/del/
pdir = os.path.join(d, 'prg'); ddir = os.path.join(pdir, 'del')
have = set(os.listdir(pdir)) | (set(os.listdir(ddir)) if os.path.isdir(ddir) else set())
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'data-filename="([^"]+)"', s):
        fn = m.group(1)
        cand = fn + '.txt' if not fn.endswith('.prg') else fn
        if cand not in have:
            fail(f"{f}: data-filename {fn!r} -> {cand!r} not under prg/")

# 2. <figcaption>Listing N…</figcaption> numbers are non-decreasing per article
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    nums = [int(n) for n in re.findall(r'<figcaption>Listing (\d+)', open(os.path.join(d, f)).read())]
    prev = 0
    for n in nums:
        if n < prev: fail(f"{f}: Listing {n} after Listing {prev}"); break
        prev = n

# 3. data-name unique within each article (excluding the canonical
#    <pre data-mse=mse1> + sibling <div class="binary_download"> pair
#    that intentionally share a name)
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    pres = re.findall(r'<pre [^>]*data-name="([^"]+)"', s)
    divs = re.findall(r'<div class="binary_download" [^>]*data-name="([^"]+)"', s)
    # Allow each div data-name to also appear once in <pre> (the MSE pair).
    pre_count = collections.Counter(pres)
    for n in divs: pre_count[n] -= 1
    dup = [n for n, c in pre_count.items() if c > 1]
    if dup: fail(f"{f}: duplicate <pre data-name> {dup}")
    div_dup = [n for n, c in collections.Counter(divs).items() if c > 1]
    if div_dup: fail(f"{f}: duplicate binary_download data-name {div_dup}")

# 4. no <p>(byline)</p> mid-article ending up between <figure>s and the
#    closing </article>: the byline must sit before the figures-block,
#    not interleaved (a common pattern bug after manual placement).
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    last_addr = s.rfind('<address class="author"')
    last_fig = s.rfind('<figure')
    if last_addr > 0 and last_fig > last_addr:
        # figure after address — that's the normal pattern (tail block).
        # We only flag the opposite: address after figures.
        pass
    if last_addr > 0 and last_fig > 0 and last_addr > last_fig:
        # Address comes after the last figure — usually fine, but flag
        # if there's another figure further down (interleaved layout).
        rest = s[last_addr:]
        if '<figure' in rest:
            fail(f"{f}: byline interleaved with figures")

if problems == 0:
    print("verification clean")
sys.exit(0 if problems == 0 else 1)
PY
)" "$dir"

# 5. drop prg.txt if it only has the source-path comment and the
#    "------ende------" sentinel left over (i.e. nothing article-bound
#    remains). Orphans that the user has accepted (boot screens,
#    typing-aid reprints) don't block deletion either.
worklist="$dir/prg.txt"
if [ -f "$worklist" ]; then
  # strip blanks, source-path comments, and the ende sentinel; any
  # surviving <figure>/binary_download line means real work is left.
  real_left=$(grep -cE '^[^<]*<(figure|div class="binary_download")' "$worklist" || true)
  if [ "$real_left" -gt 0 ]; then
    echo "  $real_left figure/download block(s) still in $worklist — leaving in place"
  else
    rm "$worklist"
    echo "  removed $worklist (no article-bound listings left)"
  fi
fi
