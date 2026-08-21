#!/bin/bash
# Convert a 64'er OCR .md to .html via Discount in GFM mode (same engine
# Marked 2 uses). Writes the .html next to the .md.
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <md-file>" >&2
  exit 1
fi
md="$1"
out="${md%.md}.html"
# Strip a leading UTF-8 BOM if present (otherwise Discount emits <p>﻿</p>).
tmp=$(mktemp)
LC_ALL=C sed -e '1s/^\xEF\xBB\xBF//' "$md" > "$tmp"
markdown -G \
  -f '+html,+github-listitem,+strikethrough,+tables,+fencedcode,-smarty,-alphalist' \
  "$tmp" > "$out"
# -alphalist disables Discount's alphabetic ordered lists (`a.` / `A.` →
# <ol type="a">). In 1986 magazine text a capital letter followed by a period
# at the start of a line is an ABBREVIATED FORENAME, not a list marker:
# `M. Grewe: »Nein, …«` became `<ol type="a"><li>Grewe: »Nein, …«` and the
# `M.` was SWALLOWED as the marker — silent text loss, not just wrong markup.
# It also fires when the OCR reads a digit `1.` as a letter `l.`, so a real
# numbered list turns into <ol type="a"> with its first number eaten.
# +autolink is intentionally omitted: 1986 magazine text never has real
# URLs, but Discount's autolinker wraps `news:`, `tel:`, `fax:`, etc.
# in <a href="…"> as false positives (rule 270).
# -smarty disables Discount's smartypants substitutions: `(C)` → ©,
# `(R)` → ®, `(TM)` → ™, plus quote curling. In 64'er text `(C)` is
# body content (math like `SIN(C)*USR(A)`, curve labels like `Kurve (C)`),
# never a copyright sign. Legitimate © (e.g. Impressum) stays via its
# UTF-8 character.
rm -f "$tmp"

# Post-pass: Discount emits INVALID nesting for a fenced code block —
# it opens a <p>, puts the <pre> inside it, and then swallows the whole
# following paragraph into the same <p>:
#
#   <p><pre><code>CODE
#   </code></pre>
#
#   Next paragraph.</p>
#
# The paragraph break after the listing is lost, which is why prose kept
# arriving glued to the end of a code block. Indented code blocks do NOT
# have this problem, only fenced ones (+fencedcode), and it is independent
# of -G. Issue 8609 had 19 occurrences.
python3 - "$out" <<'UNWRAP'
import io, re, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()

def fix(m):
    pre, tail = m.group(1), m.group(2).strip()
    return pre + ("\n\n<p>" + tail + "</p>" if tail else "")

s, n = re.subn(r"<p>(<pre><code>.*?</code></pre>)(.*?)</p>", fix, s, flags=re.S)
io.open(p, "w", encoding="utf-8").write(s)
print(f"  unwrapped {n} <p><pre> nestings (Discount fenced-code bug)")
UNWRAP
echo "wrote $out  ($(wc -l < "$out") lines)"
# Replace the .md with the .html in git: drop the source, stage the result.
# Tolerant on first run (md may not be tracked yet).
if git ls-files --error-unmatch "$md" >/dev/null 2>&1; then
  git rm -f --quiet "$md"   # -f so staged edits from earlier steps don't block removal
else
  rm -f "$md"
fi
git add "$out"
echo "git: removed $md, staged $out"
