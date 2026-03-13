#!/usr/bin/env python3
"""Stamp TOC metadata into an article HTML file from a JSON file.

Usage:
    python3 tools/png2mag/stamp_toc.py <article_html> <toc_json>

The JSON file should contain:
{
    "toc_category": "Grafik",
    "toc_title": ""           // empty string = use <h1> title (no override)
}

This updates the HTML file in place, replacing the TODO placeholders.
"""

import json
import re
import sys


def stamp_toc(html_path, json_path):
    with open(json_path) as f:
        data = json.load(f)

    with open(html_path) as f:
        html = f.read()

    toc_category = data.get('toc_category', '')
    toc_title = data.get('toc_title', '')

    # Replace commented-out TOC placeholders with actual values
    if toc_category:
        html = re.sub(
            r'<!-- <meta name="64er\.toc_category" content="TODO"> -->',
            f'<meta name="64er.toc_category" content="{toc_category}">',
            html,
        )
    if toc_title:
        html = re.sub(
            r'<!-- <meta name="64er\.toc_title" content="TODO"> -->',
            f'<meta name="64er.toc_title" content="{toc_title}">',
            html,
        )
    else:
        # Empty toc_title = same as h1, remove the placeholder entirely
        html = re.sub(
            r'\s*<!-- <meta name="64er\.toc_title" content="TODO"> -->\n',
            '\n',
            html,
        )

    with open(html_path, 'w') as f:
        f.write(html)

    print(f'toc_category    {toc_category}')
    print(f'toc_title       {toc_title or "(same as h1)"}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__.strip())
        sys.exit(1)
    stamp_toc(sys.argv[1], sys.argv[2])
