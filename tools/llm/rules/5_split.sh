#!/bin/bash
# Split a converted 64'er issue HTML into per-article files.
# Wraps tools/split.py with: path-derived 64er.issue, output into the input
# directory, and post-split git management.
#
# Usage:
#   tools/llm/rules/5_split.sh <html-file> [64er.issue]
#
# If [64er.issue] is omitted, derive it from the directory name (e.g.
# `issues/8607/` -> "7/86"). For Sonderhefte and other naming schemes the
# 2nd arg must be passed explicitly.
set -e
if [ -z "$1" ]; then
  echo "usage: $0 <html-file> [64er.issue]" >&2
  exit 1
fi
src="$1"
dir=$(cd "$(dirname "$src")" && pwd)
base=$(basename "$src")
# Derive 64er.issue from path if not given.
if [ -n "$2" ]; then
  issue="$2"
else
  d=$(basename "$dir")
  if [[ "$d" =~ ^([0-9]{2})([0-9]{2})$ ]]; then
    yy="${BASH_REMATCH[1]}"
    mo=$((10#${BASH_REMATCH[2]}))
    issue="${mo}/${yy}"
  else
    echo "could not derive 64er.issue from '$d', pass it as 2nd arg (e.g. '7/86' or 'Sonderheft 5/86')" >&2
    exit 1
  fi
fi
echo "splitting $src as 64er.issue=$issue"

# Run split logic in input dir so the per-article files land beside the source.
( cd "$dir" && python3 - "$base" "$issue" <<'PY'
# Adapted from tools/split.py: split one consolidated HTML into per-article
# files. Each <h1> ends with [page-numbers]; extracted into 64er.pages.
# (p)(author)(/p) becomes <address class="author"> and feeds <meta name="author">.
import sys, re

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*+]', '_', name)

def remove_id_attributes(html):
    return re.sub(r'\s+id=["\'][^"\']*["\']', '', html)

def apply_text_replacements(html):
    html = html.replace('<blockquote><p>', '<p class="intro">')
    html = html.replace('</blockquote>', '')
    html = html.replace('<br/>', '<br>')
    html = html.replace('&rsquo;', "'")
    html = html.replace('&lsquo;', "'")
    html = html.replace('&rdquo;', '"')
    html = html.replace('&ldquo;', '"')
    html = html.replace("''", '"')
    return html

def split_html(input_file, issue):
    content = open(input_file, encoding='utf-8').read()
    sections = re.split(r'(<h1[^>]*>.*?</h1>)', content, flags=re.DOTALL)
    if len(sections) < 3:
        print("No <h1> tags found or content is improperly formatted.")
        return
    tpl_start = ('<!DOCTYPE html>\n<html lang="de">\n\n<head>\n'
                 '    <title>XXX</title>\n'
                 '    <meta charset="UTF-8">\n'
                 '    <link rel="stylesheet" href="../style.css">\n'
                 '    <meta name="author" content="XXX">\n'
                 '    <meta name="64er.issue" content="{issue}">\n'
                 '    <meta name="64er.pages" content="XXX">\n'
                 '    <!-- <meta name="64er.toc_category" content="XXX"> -->\n'
                 '    <!-- <meta name="64er.toc_title" content="XXX"> -->\n'
                 '    <meta name="64er.id" content="XXX">\n'
                 '</head>\n\n<body>\n    <article>\n')
    tpl_end = '\n    </article>\n</body>\n</html>\n'
    written = []
    idx = 0
    for i in range(1, len(sections), 2):
        h1 = sections[i]
        body = sections[i+1] if i+1 < len(sections) else ''
        h1_text = re.search(r'<h1[^>]*>(.*?)</h1>', h1, re.DOTALL).group(1).strip()
        page_match = re.search(r'\[(.*?)\]$', h1_text)
        if not page_match:
            print(f"Warning: no page spec in <h1>: {h1_text}")
            continue
        pages = page_match.group(1)
        h1_clean = re.sub(r'\s*\[.*?\]$', '', h1_text)
        first_page = pages.split(',')[0].split('-')[0].strip()
        # plain-text version of the heading for the filename and <title>
        h1_plain = re.sub(r'<[^>]+>', '', h1_clean).strip()
        out_name = sanitize_filename(f"{first_page} {h1_plain}.html")
        body = apply_text_replacements(body)
        # Collect (author) bylines into <address class="author"> + <meta name=author>
        authors = set()
        for a in re.findall(r'<p>\(([^)]*?)\)</p>', body, re.DOTALL):
            authors.add(a.strip().replace('/', ', '))
            body = body.replace(f'<p>({a})</p>', f'<address class="author">({a})</address>', 1)
        out = tpl_start.format(issue=issue)
        out += f"        <h1>{h1_clean}</h1>\n"
        out += remove_id_attributes(body.strip()) if body.strip() else "        <p>No additional content.</p>\n"
        out += tpl_end
        out = re.sub(r'<title>XXX</title>', f'<title>{h1_plain}</title>', out)
        out = re.sub(r'<meta name="64er.pages" content="XXX">',
                     f'<meta name="64er.pages" content="{pages}">', out)
        out = re.sub(r'<meta name="64er.id" content="XXX">',
                     f'<meta name="64er.id" content="XXX{idx}">', out)
        idx += 1
        if authors:
            out = re.sub(r'<meta name="author" content="XXX">',
                         f'<meta name="author" content="{", ".join(sorted(authors))}">', out)
        open(out_name, 'w', encoding='utf-8').write(out)
        written.append(out_name)
    print(f"wrote {len(written)} files")
    # emit the list so the shell wrapper can git-add them
    with open('.split_outputs', 'w') as f:
        for n in written: f.write(n + '\n')

split_html(sys.argv[1], sys.argv[2])
PY
)

# Beautify each per-article file in place using js-beautify
# (same engine as Nova's nova-beautify extension). 4-space indent, no line
# wrapping so OCR'd line breaks are preserved; inline elements stay on
# their line.
files=()
while IFS= read -r name; do files+=("$dir/$name"); done < "$dir/.split_outputs"
npx --yes js-beautify \
  --type html \
  --indent-size 4 \
  --wrap-line-length 0 \
  --replace "${files[@]}" >/dev/null
echo "beautified ${#files[@]} file(s) via js-beautify"

# git: drop the consolidated .html, stage the per-article files.
if git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
  git rm -f --quiet "$src"
else
  rm -f "$src"
fi
for f in "${files[@]}"; do git add "$f"; done
rm -f "$dir/.split_outputs"
echo "git: removed $src, staged the per-article files"
