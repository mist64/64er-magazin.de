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

# -G PADS EVERY LINE INSIDE A FENCE WITH TWO SPACES.  It is Discount's
# GitHub hard-break marker, and inside <pre><code> it is not a line break,
# it is trailing whitespace in a LISTING -- the one thing in this corpus
# that has to come out byte-identical to the fence it came from, because a
# reader types it in.  Reproduced on a two-line scratch file: with -G the
# lines end "A  ", without it "A".  -G stays: it is what preserves the
# OCR'd line breaks in prose.  js-beautify at 080 does NOT strip these
# (tested), and nothing else in the chain does either.
# MEASURED on 8611: 85 lines across all 35 blocks.
def strip_pre(m):
    body = "\n".join(l.rstrip() for l in m.group(1).split("\n"))
    return "<pre><code>" + body + "</code></pre>"

s, t = re.subn(r"<pre><code>(.*?)</code></pre>", strip_pre, s, flags=re.S)
io.open(p, "w", encoding="utf-8").write(s)
print(f"  unwrapped {n} <p><pre> nestings (Discount fenced-code bug)")
print(f"  de-padded {t} <pre> blocks (Discount -G trailing spaces)")
UNWRAP
echo "wrote $out  ($(wc -l < "$out") lines)"
# KEEP A COPY OF THE EXACT INPUT BEFORE DROPPING IT.  This step deletes the
# .md, and several checks downstream need the text that was actually converted:
# r060's own start-number survey, r040's heading count, r320's dropped-listing
# gate.  The rule used to point them at <tmp>/ocr/<ID>.md, which is the 030
# handover -- pre-040, pre-050, and so not the file Discount saw.  The copy goes
# beside the handover, named so the difference is visible.
if [ -z "$TMPDIR_ISSUE" ]; then
  echo "r060: \$TMPDIR_ISSUE is not set -- see r000 'the working directory must" >&2
  echo "      be DURABLE'.  Without it this step would delete the only copy of" >&2
  echo "      the text that was converted." >&2
  exit 1
fi
mkdir -p "$TMPDIR_ISSUE/ocr"
keep="$TMPDIR_ISSUE/ocr/$(basename "${md%.md}").pre060.md"
cp "$md" "$keep" && echo "kept the converted source at $keep"

# Replace the .md with the .html in git: drop the source, stage the result.
# Tolerant on first run (md may not be tracked yet).
if git ls-files --error-unmatch "$md" >/dev/null 2>&1; then
  git rm -f --quiet "$md"   # -f so staged edits from earlier steps don't block removal
else
  rm -f "$md"
fi
git add "$out"
echo "git: removed $md, staged $out"
