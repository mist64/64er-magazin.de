#!/bin/bash
# Escape <...> patterns in a 64'er OCR .md when they're NOT real HTML tags
# (e.g. <RETURN>, <SHIFT-RUN/STOP>, <F3>). Real tags (<br>, <sub>, <img …>,
# etc.) are kept. In-place rewrite, idempotent -- not because it skips an
# already-escaped \<...\> (the header said so; Pass 1 CONVERTS those), but
# because the output is entities, and &lt;...&gt; matches no pattern here.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-$DIR/../../../../.venv/bin/python}"
if [ -z "$1" ]; then
  echo "usage: $0 <md-file>" >&2
  exit 1
fi
"$PY" - "$1" <<'PY'
import re, sys
fp = sys.argv[1]
HTML_TAGS = {
    'a','abbr','address','article','aside','b','blockquote','body','br',
    'caption','code','col','colgroup','dd','del','details','dfn','div','dl',
    'dt','em','figcaption','figure','footer','form','h1','h2','h3','h4','h5',
    'h6','head','header','hr','html','i','iframe','img','ins','kbd','label',
    'li','link','main','map','mark','meta','nav','ol','p','param','pre','q',
    'rp','rt','ruby','s','samp','script','section','small','source','span',
    'strong','style','sub','sup','table','tbody','td','tfoot','th','thead',
    'title','tr','u','ul','var','wbr',
}
s = open(fp, encoding='utf-8').read()

# BOTH ESCAPES ARE FOR DISCOUNT'S INLINE PARSER, WHICH DOES NOT RUN INSIDE A
# FENCE.  Applied there anyway, the escape is shipped LITERALLY: `10 A=B\*2`
# renders with the backslash visible, and `&lt;F1&gt;` inside a fence comes out
# as the text "&lt;F1&gt;" because 070 re-escapes the ampersand.  Nothing later
# in the chain strips either.  MEASURED on Discount 3.0.2 with r060's own flags,
# and on 8611: 4 fenced lines would have shipped a stray backslash and 2 would
# have shipped entity text -- inside LISTINGS, which are the one thing in this
# corpus that has to be byte-exact, because a reader types them in.
# Fenced regions are therefore passed through untouched.  ``` only: 030 emits
# no indented code blocks (MEASURED: 0 in 8611), and treating a 4-space indent
# as code would swallow ordinary continuation lines.
def fence_flags(s):
    """(line, inside_a_fence) per line; the ``` lines count as inside."""
    infence = False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            yield line, True
            continue
        yield line, infence

def map_outside_fences(s, fn):
    return ''.join(line if inf else fn(line) for line, inf in fence_flags(s))

# Pass 1: convert any pre-existing backslash-escaped pair `\<X\>` to entities,
#         since Discount preserves `\<` literal when it looks like a tag.
s = map_outside_fences(s, lambda l: re.sub(r'\\<([^<>\n]*?)\\>',
                                           lambda m: '&lt;' + m.group(1) + '&gt;', l))
# Pass 2: escape bare <X> where X is not a recognised HTML tag.
def fix(m):
    inner = m.group(1)
    name_match = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', inner)
    if name_match and name_match.group(1) in HTML_TAGS:   # case-sensitive: only lowercase tags pass
        return m.group(0)
    return '&lt;' + inner + '&gt;'
# Match <…>: starts with letter (so '<10', '< CBM >', '<\*>' don't match).
s = map_outside_fences(s, lambda l: re.sub(r'<(/?[a-zA-Z][^<>\n]*?)>', fix, l))

# Pass 3: EVERY OPENER HTML5 TURNS INTO A BOGUS COMMENT, which Pass 2's pattern
# cannot reach.  The tokenizer has exactly four "tag open" paths after `<`: a
# letter (a tag), `/` + a letter (an end tag), and then `!`, `?` and `/` +
# anything-else -- the last three all become a BOGUS COMMENT that eats text up
# to the next '>' and renders as nothing.  Pass 2 covers the first two, so this
# pass must cover all three of the others, not just one of them.
#
# The `</` + non-letter half has been required since the 8612 harvest; the
# script never did it, and neither did the Verification regex, so the gap was
# invisible from both ends.  8612 line 2903, "durch `</>` dargestellt", would
# have lost the </> and swallowed what followed.
#
# `<!` was the same gap one character over, found on 8701: the issue prints
# `<!>` five times (Master-Text, the "Ausrufungszeichen-Funktion"), every one
# of them shipped unescaped, and the `!` disappeared.  The Verification could
# not see it either, because it applied the same "a non-letter after `<` is
# safe" test as the transform -- a check derived from the belief it was meant
# to question.  `<?` has not been seen in the corpus; it is here because it is
# the same tokenizer path and costs one character to close.
s = map_outside_fences(s, lambda l: re.sub(
    r'<(![^<>\n]*|\?[^<>\n]*|/(?![a-zA-Z])[^<>\n]*)>',
    lambda m: '&lt;' + m.group(1) + '&gt;', l))

open(fp, 'w', encoding='utf-8').write(s)
# Report.  THE SUMMARY MUST BE AS FENCE-AWARE AS THE TRANSFORM.  Counting the
# whole file, this read every correctly-untouched <...> inside a listing back as
# "remaining" -- the step's own correct output reported as a defect, which is how
# a fixed bug gets re-broken.  Same repair as r040's summary.
t = ''.join(line for line, inf in fence_flags(s) if not inf)
left_bad = 0
for m in re.finditer(r'<(/?[a-zA-Z][^<>\n]*?)>', t):
    name = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', m.group(1)).group(1)
    if name not in HTML_TAGS: left_bad += 1
# THE SUMMARY COUNTS WHAT PASS 3 ESCAPES -- all three bogus-comment openers.
# Counting only `</` is how the `<!` gap stayed invisible for an issue.
bogus = len(re.findall(r'<(?:![^<>\n]*|\?[^<>\n]*|/(?![a-zA-Z])[^<>\n]*)>', t))
escaped = t.count('&lt;')
print(f"{fp}: unescaped non-HTML <…> remaining = {left_bad};  bogus </ = {bogus};"
      f"  &lt; sequences = {escaped}   (outside fences)")
PY
