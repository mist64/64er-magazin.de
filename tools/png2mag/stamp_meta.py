#!/usr/bin/env python3
"""Stamp metadata into an article HTML file from a JSON file.

Usage:
    python3 tools/png2mag/stamp_meta.py <article_html> <meta_json>

The JSON file should contain any of:
{
    "head1": "Grafik",
    "head2": "C 64",
    "toc_category": "Grafik",
    "toc_title": "",              // empty = same as <h1>, line gets commented out
    "id": "hardmaker"
}

Replaces unique placeholder strings __HEAD1__, __HEAD2__, __TOC_TITLE__,
__TOC_CATEGORY__, __ID__ in the HTML file. No HTML parsing needed.
"""

import json
import re
import sys


def stamp_meta(html_path, json_path):
    with open(json_path) as f:
        data = json.load(f)

    with open(html_path) as f:
        html = f.read()

    replacements = {
        '__HEAD1__': data.get('head1', ''),
        '__HEAD2__': data.get('head2', ''),
        '__TOC_CATEGORY__': data.get('toc_category', ''),
        '__ID__': data.get('id', ''),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # toc_title: if empty, comment out the line; otherwise replace
    toc_title = data.get('toc_title', '')
    if toc_title:
        html = html.replace('__TOC_TITLE__', toc_title)
    else:
        # Same as h1 — comment out the meta tag
        html = re.sub(
            r'    <meta name="64er\.toc_title" content="__TOC_TITLE__">\n',
            '',
            html,
        )

    with open(html_path, 'w') as f:
        f.write(html)

    print(f'head1           {replacements["__HEAD1__"]}')
    print(f'head2           {replacements["__HEAD2__"]}')
    print(f'toc_category    {replacements["__TOC_CATEGORY__"]}')
    print(f'toc_title       {toc_title or "(same as h1)"}')
    print(f'id              {replacements["__ID__"]}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__.strip())
        sys.exit(1)
    stamp_meta(sys.argv[1], sys.argv[2])
