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
  -f '+html,+github-listitem,+strikethrough,+tables,+fencedcode,+autolink' \
  "$tmp" > "$out"
rm -f "$tmp"
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
