#!/bin/bash
# Escape <...> patterns in a 64'er OCR .md when they're NOT real HTML tags
# (e.g. <RETURN>, <SHIFT-RUN/STOP>, <F3>). Real tags (<br>, <sub>, <img …>,
# etc.) are kept. In-place rewrite, idempotent (skips already-escaped \<...\>).
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <md-file>" >&2
  exit 1
fi
python3 - "$1" <<'PY'
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
def map_outside_fences(s, fn):
    out, infence = [], False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            out.append(line)
            continue
        out.append(line if infence else fn(line))
    return ''.join(out)

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
open(fp, 'w', encoding='utf-8').write(s)
# report
left_bad = 0
for m in re.finditer(r'<(/?[a-zA-Z][^<>\n]*?)>', s):
    name = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', m.group(1)).group(1)
    if name not in HTML_TAGS: left_bad += 1
escaped = s.count('&lt;')
print(f"{fp}: unescaped non-HTML <…> remaining = {left_bad};  &lt; sequences = {escaped}")
PY
