#!/usr/bin/env python3
"""
Apply index_category and index_title from Jahresinhaltsverzeichnis CSV to article HTMLs.

Usage:
    cd issues/YYMM
    python3 ../../tools/llm/new/index_workflow_apply.py YYMM ../../Jahresinhaltsverzeichnis\ YYYY.csv

The script:
1. Reads all CSV rows for the given issue code (e.g. 8605)
2. Matches each row to an HTML file by start page number
3. Inserts index_category and index_title meta tags before 64er.id
4. Handles multiple CSV entries per article (e.g. Bücher, Tips & Tricks)
5. Skips index_title when it matches <title>
"""

import csv
import glob
import html as H
import re
import sys
from collections import defaultdict


def parse_csv(csv_path, issue_code):
    """Parse CSV and return entries for the given issue."""
    entries = []
    with open(csv_path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith(f"{issue_code},"):
                continue
            reader = csv.reader([line])
            for parts in reader:
                if len(parts) >= 5:
                    pages = parts[1]
                    # Extract start page (before em-dash or regular dash)
                    start = re.split(r'[—\u2014-]', pages)[0].strip()
                    entries.append({
                        'start': start,
                        'category': parts[2],
                        'subcategory': parts[3],
                        'title': parts[4],
                    })
    return entries


def find_html_by_page(html_files):
    """Build page→filename mapping."""
    by_page = defaultdict(list)
    for fn in html_files:
        m = re.match(r'^(\d+)\s', fn)
        if m:
            by_page[m.group(1)].append(fn)
    return by_page


def find_file_for_entry(entry, by_page, all_files):
    """Find the HTML file that an index entry belongs to."""
    start = entry['start']
    candidates = by_page.get(start, [])

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        # Try title match
        for c in candidates:
            c_base = c.split('.html')[0].split(' ', 1)[-1].lower() if ' ' in c else ''
            if c_base[:10] in entry['title'].lower() or entry['title'].lower()[:10] in c_base:
                return c
        return candidates[0]  # fallback

    # No direct match — search by page range
    for fn in all_files:
        text = open(fn).read()
        m = re.search(r'64er\.pages" content="([^"]*)"', text)
        if m:
            for segment in m.group(1).split(','):
                if '-' in segment:
                    lo, hi = segment.split('-')
                    try:
                        if int(lo) <= int(start) <= int(hi):
                            return fn
                    except ValueError:
                        pass
                elif segment.strip() == start:
                    return fn
    return None


def get_title(text):
    """Extract <title> from HTML."""
    m = re.search(r'<title>(.*?)</title>', text)
    return m.group(1) if m else ""


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} YYMM path/to/csv")
        sys.exit(1)

    issue_code = sys.argv[1]
    csv_path = sys.argv[2]

    # Parse CSV
    entries = parse_csv(csv_path, issue_code)
    print(f"Found {len(entries)} CSV entries for {issue_code}\n")

    # Build mappings
    html_files = sorted(glob.glob("*.html"))
    by_page = find_html_by_page(html_files)

    # Remove existing index entries
    for fn in html_files:
        text = open(fn).read()
        text2 = re.sub(r'    <meta name="64er\.index_category" content="[^"]*">\n', '', text)
        text2 = re.sub(r'    <meta name="64er\.index_title" content="[^"]*">\n', '', text2)
        if text2 != text:
            open(fn, 'w').write(text2)

    # Group entries by target file
    file_entries = defaultdict(list)
    for entry in entries:
        fn = find_file_for_entry(entry, by_page, html_files)
        if fn:
            file_entries[fn].append(entry)
        else:
            print(f"NO FILE for p{entry['start']}: '{entry['title']}'")

    # Apply entries
    for fn in sorted(file_entries):
        text = open(fn).read()
        article_title = get_title(text)

        m_id = re.search(r'(    <meta name="64er\.id")', text)
        if not m_id:
            print(f"NO ID: {fn}")
            continue

        insert = ""
        for entry in file_entries[fn]:
            idx_cat = f"{entry['category']}|{entry['subcategory']}"
            idx_title = entry['title']

            if idx_title != article_title:
                insert += f'    <meta name="64er.index_title" content="{H.escape(idx_title)}">\n'
            insert += f'    <meta name="64er.index_category" content="{H.escape(idx_cat)}">\n'

        text = text[:m_id.start()] + insert + text[m_id.start():]
        open(fn, 'w').write(text)

        titles = [e['title'] for e in file_entries[fn]]
        print(f"OK ({len(titles)} entries): {fn}")
        for t in titles:
            print(f"    → {t}")

    # Report unmatched files
    print(f"\n=== Articles without index_category ===")
    for fn in sorted(html_files):
        text = open(fn).read()
        if 'index_category' not in text:
            print(f"  {fn}")


if __name__ == '__main__':
    main()
