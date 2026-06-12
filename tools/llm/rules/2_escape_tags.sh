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
# Pass 1: convert any pre-existing backslash-escaped pair `\<X\>` to entities,
#         since Discount preserves `\<` literal when it looks like a tag.
s = re.sub(r'\\<([^<>\n]*?)\\>', lambda m: '&lt;' + m.group(1) + '&gt;', s)
# Pass 2: escape bare <X> where X is not a recognised HTML tag.
def fix(m):
    inner = m.group(1)
    name_match = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', inner)
    if name_match and name_match.group(1) in HTML_TAGS:   # case-sensitive: only lowercase tags pass
        return m.group(0)
    return '&lt;' + inner + '&gt;'
# Match <…>: starts with letter (so '<10', '< CBM >', '<\*>' don't match).
s = re.sub(r'<(/?[a-zA-Z][^<>\n]*?)>', fix, s)
open(fp, 'w', encoding='utf-8').write(s)
# report
left_bad = 0
for m in re.finditer(r'<(/?[a-zA-Z][^<>\n]*?)>', s):
    name = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', m.group(1)).group(1)
    if name not in HTML_TAGS: left_bad += 1
escaped = s.count('&lt;')
print(f"{fp}: unescaped non-HTML <…> remaining = {left_bad};  &lt; sequences = {escaped}")
PY
