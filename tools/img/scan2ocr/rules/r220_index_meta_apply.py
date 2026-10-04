#!/usr/bin/env python3
r"""
Apply index_category and index_title from Jahresinhaltsverzeichnis CSV to article HTMLs.

Usage:
    cd issues/YYMM
    python3 ../../tools/img/scan2ocr/rules/r220_index_meta_apply.py YYMM ../../Jahresinhaltsverzeichnis\ YYYY.csv

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


def sonderheft_key(issue_code):
    """SH8602 -> '2/86'.  The Sonderheft CSV keys on the magazine's running
    Sonderheft number and the year, not on the directory name."""
    m = re.match(r'^SH(\d{2})(\d{2})$', issue_code)
    return f"{int(m.group(2))}/{m.group(1)}" if m else None


def parse_sonderheft_csv(csv_path, issue_code):
    """Gesamtinhaltsverzeichnis Sonderhefte.csv -- a DIFFERENT layout.

    No header row, and the columns are not the monthly ones:

        0 category   1 subcategory   2 title   3 issue as N/YY   4 page

    So the issue key is in column 3, not column 0, and the page is a single
    page rather than a range.  SH8601 shipped with NO index metadata at all
    because r220 was classified `monthly` on the evidence that no Sonderheft
    appears in the ANNUAL csvs -- true, and the wrong file.
    """
    key = sonderheft_key(issue_code)
    if not key:
        return []
    entries = []
    with open(csv_path, encoding="utf-8") as f:
        for parts in csv.reader(f):
            if len(parts) >= 5 and parts[3].strip() == key:
                page = re.sub(r'[^0-9]', '', parts[4])
                if not page:
                    continue
                entries.append({
                    'start': page,
                    'category': parts[0].strip(),
                    'subcategory': parts[1].strip(),
                    'title': parts[2].strip(),
                })
    return entries


def parse_csv(csv_path, issue_code):
    """Parse CSV and return entries for the given issue."""
    if issue_code.startswith("SH"):
        return parse_sonderheft_csv(csv_path, issue_code)
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


def page_coverage(html_files):
    """{filename: set of pages it covers}, from 64er.pages -- not the filename.

    The filename only carries the START page, so routing by it alone sends a
    row to whichever article happens to start on that page even when the row
    belongs to a rubric running across it. On 8612 the "320 KByte" item, which
    sits inside "11 Aktuell" (pages 11-14), went to "14 Scorpio" because
    Scorpio starts on 14 -- and the check then flagged the correct route as
    the wrong one.
    """
    cov = {}
    for fn in html_files:
        m = re.search(r'64er\.pages" content="([^"]+)"',
                      open(fn, encoding="utf-8").read())
        if not m:
            continue
        pages = set()
        for seg in m.group(1).split(","):
            seg = seg.strip()
            mm = re.match(r'^(\d+)[a-z]?(?:\s*[-\u2013\u2014]\s*(\d+)[a-z]?)?$', seg)
            if not mm:
                continue
            lo = int(mm.group(1))
            hi = int(mm.group(2)) if mm.group(2) else lo
            pages.update(range(lo, hi + 1))
        cov[fn] = pages
    return cov


def find_file_for_entry(entry, by_page, all_files, cov=None):
    """Find the HTML file that an index entry belongs to."""
    start = entry['start']
    candidates = by_page.get(start, [])

    # A MULTI-PAGE RUBRIC that covers this page and carries a matching <h2>
    # outranks an article that merely starts here.
    if cov and start.isdigit():
        pg = int(start)
        t = re.sub(r'<[^>]+>', '', entry['title']).strip().lower()[:24]
        for fn, pages in cov.items():
            if fn in candidates or pg not in pages or len(pages) < 2:
                continue
            body = open(fn, encoding="utf-8").read()
            for h in re.findall(r'<h[23][^>]*>(.*?)</h[23]>', body, re.DOTALL):
                h = re.sub(r'<[^>]+>', '', h).strip().lower()
                if t and (t in h or h[:24] in t):
                    return fn

    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        # Try title match
        for c in candidates:
            c_base = c.split('.html')[0].split(' ', 1)[-1].lower() if ' ' in c else ''
            if c_base[:10] in entry['title'].lower() or entry['title'].lower()[:10] in c_base:
                return c
        return candidates[0]  # fallback

    # No file STARTS on this page, so the row belongs to the article that is
    # running across it -- the one whose start page is the NEAREST PRECEDING
    # one. This used to return the first filename in LEXICAL order whose range
    # contained the page, which is not the same thing and is wrong whenever two
    # articles overlap: on 8611 the p13 Aktuell rows went to "11 Epson"
    # (11-13 sorts before "12 Aktuell") and the p69 ProDisc row went to
    # "52 Das Ende aller Tippfehler" (65-73). 4 of 49 rows misrouted, and no
    # check saw it -- a count of rows applied cannot.
    best, best_start = None, -1
    for fn in all_files:
        text = open(fn, encoding='utf-8').read()
        m = re.search(r'64er\.pages" content="([^"]*)"', text)
        if not m:
            continue
        for segment in m.group(1).split(','):
            segment = segment.strip()
            lo, _, hi = segment.partition('-')
            try:
                lo_i, hi_i = int(lo), int(hi or lo)
            except ValueError:
                continue
            if lo_i <= int(start) <= hi_i and lo_i > best_start:
                best, best_start = fn, lo_i
    return best


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
    cov = page_coverage(html_files)

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
        fn = find_file_for_entry(entry, by_page, html_files, cov)
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

            # get_title() returns the ESCAPED <title>; the CSV title is raw.
            # Comparing them directly meant every title containing &差 differed
            # from itself, and 4 rows on 8611 got a redundant index_title.
            if idx_title != H.unescape(article_title or ''):
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
