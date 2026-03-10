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

import glob
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


def collect_listings(issue_dir, start_page, end_page):
    """Collect listing captions from all page block dirs."""
    captions = []
    for p in range(int(start_page), int(end_page) + 1):
        listings_path = os.path.join(issue_dir, 'tmp', f'p{p:03d}_blocks', 'listings.txt')
        if os.path.exists(listings_path):
            with open(listings_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        captions.append(line)
    return captions


def insert_unmatched_images(body, issue_dir, start_page, end_page):
    """Find images P-N.png not yet referenced in body and insert before first body paragraph."""
    # Collect all article images: start_page-*.png through end_page-*.png
    all_images = []
    for p in range(int(start_page), int(end_page) + 1):
        pattern = os.path.join(issue_dir, f'{int(p)}-*.png')
        all_images.extend(sorted(glob.glob(pattern)))

    # Find which are already referenced
    referenced = set(re.findall(r'src="([^"]+\.png)"', body))

    unmatched = []
    for img_path in all_images:
        fname = os.path.basename(img_path)
        if fname not in referenced:
            unmatched.append(fname)

    if not unmatched:
        return body

    # Build figure HTML for unmatched images
    fig_lines = []
    for fname in unmatched:
        fig_lines.append(f'<figure>\n    <img src="{fname}" alt="">\n</figure>')
    fig_html = '\n\n'.join(fig_lines)

    # Insert before the first <p> that is NOT class="intro"
    # i.e., after <h1> and <p class="intro">, before the first regular <p>
    m = re.search(r'(</p>\s*\n\s*)\n(\s*<p[ >])', body)
    # More robust: find first <p> or <p class="noindent"> after any <p class="intro">
    # Strategy: split after last intro paragraph, insert before next element
    intro_end = 0
    for match in re.finditer(r'<p class="intro">.*?</p>', body, re.DOTALL):
        intro_end = match.end()
    if intro_end == 0:
        # No intro — find end of <h1>
        m = re.search(r'</h1>', body)
        if m:
            intro_end = m.end()

    if intro_end > 0:
        body = body[:intro_end] + '\n\n' + fig_html + '\n' + body[intro_end:]
    else:
        body = fig_html + '\n\n' + body

    print(f'images          {len(unmatched)} unmatched image(s) inserted: {", ".join(unmatched)}')
    return body


def assemble(draft_path, issue_dir, start_page, end_page):
    with open(draft_path) as f:
        body = f.read().strip()

    # Strip pipeline markers
    body = re.sub(r'\s*\{\{newblock\}\}\s*', '\n\n', body)
    body = re.sub(r'\s*\{\{newpage:\d+\}\}\s*', '\n\n', body)

    title = extract_title(body)
    author = extract_author(body)
    issue = issue_code(issue_dir)

    # NOTE: Image placement is now handled by the figure agent step.
    # insert_unmatched_images() is no longer called here.

    # Collect listing captions from all pages
    listings = collect_listings(issue_dir, start_page, end_page)
    if listings:
        listing_html = '\n\n'
        for caption in listings:
            listing_html += '        <figure>\n'
            listing_html += '            <pre>TODO</pre>\n'
            listing_html += f'            <figcaption>{caption}</figcaption>\n'
            listing_html += '        </figure>\n'
        # Insert before </address> or at end of body
        # Listings go after author credit (which is the last element)
        body = body + listing_html

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
    <meta name="64er.head1" content="__HEAD1__">
    <meta name="64er.head2" content="__HEAD2__">
    <meta name="64er.toc_title" content="__TOC_TITLE__">
    <meta name="64er.toc_category" content="__TOC_CATEGORY__">
    <!-- <meta name="64er.index_title" content=""> -->
    <!-- <meta name="64er.index_category" content=""> -->
    <meta name="64er.id" content="__ID__">
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
