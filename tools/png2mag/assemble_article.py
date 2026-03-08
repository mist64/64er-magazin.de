#!/usr/bin/env python3
"""Wrap article_draft.html in the final article HTML shell with metadata.

Usage:
    python3 tools/png2mag/assemble_article.py <article_draft> <issue_dir> <start_page> <end_page>

Example:
    python3 tools/png2mag/assemble_article.py issues/8604/tmp/article_draft.html issues/8604 053 057

Reads:
- article_draft.html — joined body HTML from step 6
- headers.txt — from the first page's blocks dir (for head1/head2)

Extracts from the body:
- <title> from <h1>
- author from <address class="author">

Derives:
- 64er.issue from issue dir name (YYMM → M/YY)
- 64er.pages from start_page/end_page

Output: issues/NNNN/PPP Title.html (in issue dir, named by start_page + title)
"""

import os
import re
import sys
from html.parser import HTMLParser


def extract_title(body):
    """Extract text content of the first <h1> tag."""
    class H1Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_h1 = False
            self.text = ''
        def handle_starttag(self, tag, attrs):
            if tag == 'h1':
                self.in_h1 = True
        def handle_endtag(self, tag):
            if tag == 'h1':
                self.in_h1 = False
        def handle_data(self, data):
            if self.in_h1:
                self.text += data
    p = H1Parser()
    p.feed(body)
    return p.text.strip()


def extract_author(body):
    """Extract text from <address class="author"> if present."""
    m = re.search(r'<address class="author">\s*(.*?)\s*</address>', body)
    if m:
        # Strip parentheses: "(Name/initials)" -> "Name, initials"
        text = m.group(1)
        text = re.sub(r'^\(|\)$', '', text)
        text = text.replace('/', ', ')
        return text
    return ''


def read_headers(blocks_dir):
    """Read head1 and head2 from headers.txt."""
    path = os.path.join(blocks_dir, 'headers.txt')
    head1 = ''
    head2 = ''
    if os.path.exists(path):
        with open(path) as f:
            line = f.read().strip()
        m = re.search(r'head1=([^|]+)', line)
        if m:
            head1 = m.group(1).strip()
        m = re.search(r'head2=([^|]+)', line)
        if m:
            head2 = m.group(1).strip()
    return head1, head2


def issue_code(issue_dir):
    """Derive issue string from dir name: 8604 -> 4/86."""
    basename = os.path.basename(issue_dir.rstrip('/'))
    m = re.match(r'(\d{2})(\d{2})', basename)
    if m:
        yy, mm = m.group(1), m.group(2)
        return f'{int(mm)}/{yy}'
    return ''


def indent_body(body, spaces=8):
    """Indent each line of the body HTML. Skip lines inside <pre> blocks."""
    prefix = ' ' * spaces
    lines = body.split('\n')
    result = []
    in_pre = False
    for line in lines:
        if '<pre>' in line:
            in_pre = True
        if in_pre:
            # Only indent the first line of a <pre> block (the <pre> tag itself)
            if '<pre>' in line:
                result.append(prefix + line)
            else:
                result.append(line)
        elif line.strip():
            result.append(prefix + line)
        else:
            result.append('')
        if '</pre>' in line:
            in_pre = False
    return '\n'.join(result)


def assemble(draft_path, issue_dir, start_page, end_page):
    with open(draft_path) as f:
        body = f.read().strip()

    title = extract_title(body)
    author = extract_author(body)
    issue = issue_code(issue_dir)

    # Find headers.txt in the start page's blocks dir
    blocks_dir = os.path.join(issue_dir, 'tmp', f'p{start_page}_blocks')
    head1, head2 = read_headers(blocks_dir)

    # Pages string
    if start_page == end_page:
        pages = str(int(start_page))
    else:
        pages = f'{int(start_page)}-{int(end_page)}'

    indented = indent_body(body)

    html = f'''<!DOCTYPE html>
<html lang="de">

<head>
    <title>{title}</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../style.css">
    <meta name="author" content="{author}">
    <meta name="64er.issue" content="{issue}">
    <meta name="64er.pages" content="{pages}">
    <meta name="64er.head1" content="{head1}">
    <meta name="64er.head2" content="{head2}">
    <!-- <meta name="64er.toc_title" content="TODO"> -->
    <!-- <meta name="64er.toc_category" content="TODO"> -->
    <!-- <meta name="64er.index_title" content="TODO"> -->
    <!-- <meta name="64er.index_category" content="TODO"> -->
    <meta name="64er.id" content="TODO">
</head>

<body>
    <article>
{indented}
    </article>
</body>
</html>
'''

    # Output path: issues/NNNN/PPP Title.html
    output_path = os.path.join(issue_dir, f'{int(start_page)} {title}.html')
    with open(output_path, 'w') as f:
        f.write(html)
    print(f'output          {output_path}')
    return output_path


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__.strip())
        sys.exit(1)
    assemble(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
