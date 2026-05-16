#!/usr/bin/env python3
"""
Fill 64er.index_category / 64er.index_title meta tags by matching article
HTMLs against the Jahresinhaltsverzeichnis CSV.

CSV columns (no header): issue, pages, index_cat1, index_cat2, title
- `pages` uses em-dash (U+2014) for ranges: e.g. "10—12"
- Article HTML <meta name="64er.pages"> uses hyphen-minus for ranges, comma for
  disjoint segments: e.g. "10-12" or "48,50-54"

Match strategy:
  1. Parse each CSV row's start page (part before em-dash or hyphen).
  2. For each article, expand 64er.pages into a set of integer pages.
  3. A CSV row matches an article iff start_page ∈ article.pages.
     - If multiple articles claim the same page, disambiguate by title similarity.
  4. Multiple CSV rows may map to the same article (e.g. one HTML page with
     several short items).

Edit:
  Insert one (index_title, index_category) pair per CSV row right after the
  existing `<meta name="64er.toc_category" ...>` line. Skip if any
  `64er.index_category` or `64er.index_title` meta is already present in the
  file (preserve hand-set values).

Usage:
  python3 tools/llm/new/index_meta_apply.py 8606            # dry-run / report
  python3 tools/llm/new/index_meta_apply.py 8606 --apply    # actually edit
  python3 tools/llm/new/index_meta_apply.py 8606 --verify   # verify only

Run from repo root.
"""

import argparse
import csv
import glob
import html as H
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CSV_PATH = os.path.join(REPO_ROOT, "Jahresinhaltsverzeichnis 1986.csv")


def parse_csv_rows(csv_path, issue_code):
    """Return list of dicts: {pages_raw, start_page, cat1, cat2, title}."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        for parts in reader:
            if len(parts) < 5 or parts[0] != issue_code:
                continue
            pages_raw = parts[1]
            start = re.split(r"[——\-]", pages_raw, maxsplit=1)[0].strip()
            try:
                start_int = int(start)
            except ValueError:
                continue
            rows.append({
                "pages_raw": pages_raw,
                "start_page": start_int,
                "cat1": parts[2].strip(),
                "cat2": parts[3].strip(),
                "title": parts[4].strip(),
            })
    return rows


def expand_pages(pages_attr):
    """Expand "10-12,15" → set([10,11,12,15]). Returns (set, ordered list)."""
    pages = []
    for seg in pages_attr.split(","):
        seg = seg.strip()
        if not seg:
            continue
        if "-" in seg:
            lo, hi = seg.split("-", 1)
            try:
                pages.extend(range(int(lo), int(hi) + 1))
            except ValueError:
                pass
        else:
            try:
                pages.append(int(seg))
            except ValueError:
                pass
    return set(pages), pages


def read_article_meta(path):
    text = open(path).read()
    pages_m = re.search(r'<meta name="64er\.pages"\s+content="([^"]*)"', text)
    title_m = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    toc_cat_m = re.search(r'<meta name="64er\.toc_category"\s+content="([^"]*)"', text)
    pages_attr = pages_m.group(1) if pages_m else ""
    pages_set, pages_list = expand_pages(pages_attr)
    start = pages_list[0] if pages_list else None
    return {
        "path": path,
        "text": text,
        "title": (title_m.group(1).strip() if title_m else ""),
        "toc_category": (toc_cat_m.group(1) if toc_cat_m else ""),
        "pages_attr": pages_attr,
        "pages_set": pages_set,
        "start": start,
        "has_index": (
            '64er.index_category' in text or '64er.index_title' in text
        ),
    }


def normalize_for_compare(s):
    s = s.lower()
    s = H.unescape(s)
    s = re.sub(r"[^\wäöüß ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title_similarity(a, b):
    """Simple word-overlap score normalized by smaller set."""
    aw = set(normalize_for_compare(a).split())
    bw = set(normalize_for_compare(b).split())
    if not aw or not bw:
        return 0.0
    overlap = len(aw & bw)
    return overlap / min(len(aw), len(bw))


TITLE_OVERRIDE_THRESHOLD = 0.6


def find_target_article(row, articles):
    """Return (path, reason) or (None, reason).

    Strategy (in order):
      1. Strong title-based override: if some article's title has very high
         similarity to the CSV row title (>= TITLE_OVERRIDE_THRESHOLD), prefer
         it — this fixes off-by-one page numbers in the index (where a CSV row
         says page X but the actual article starts on page X+1 because the
         continuation from a previous article ended on page X).
      2. Articles whose start page == row.start_page.
      3. Else, articles whose page-set contains row.start_page.
      4. Disambiguate ties by title-similarity, then innermost start page.
    """
    # 1. Strong title override across the entire issue.
    scored_all = [
        (title_similarity(row["title"], a["title"]), a) for a in articles
    ]
    best_sim, best_art = max(scored_all, key=lambda t: t[0]) if scored_all else (0.0, None)

    starts = [a for a in articles if a["start"] == row["start_page"]]
    contains = [a for a in articles if row["start_page"] in a["pages_set"]]

    if best_sim >= TITLE_OVERRIDE_THRESHOLD and best_art is not None:
        # Only accept the override if the title-match article is either a
        # start-page or contains-page candidate, or if the start-page bucket
        # is "merged" (multiple CSV entries land on one article). We never want
        # a title match that's totally on a different page range.
        if (
            best_art in starts
            or best_art in contains
            or best_art["start"] == row["start_page"]
            or row["start_page"] in best_art["pages_set"]
            or abs((best_art["start"] or 0) - row["start_page"]) <= 1
        ):
            return best_art, "title"

    if starts:
        candidates = starts
        bucket = "start"
    elif contains:
        candidates = contains
        bucket = "contains"
    else:
        return None, "no_article"

    if len(candidates) == 1:
        return candidates[0], bucket

    scored = sorted(
        candidates,
        key=lambda a: (
            -title_similarity(row["title"], a["title"]),
            -(a["start"] or 0),  # innermost = highest start
        ),
    )
    return scored[0], f"{bucket}+title"


META_INSERT_RE = re.compile(
    r'(    <meta name="64er\.toc_category"\s+content="[^"]*">\n'
    r'(?:    <!-- <meta name="64er\.toc_title"[^>]*-->\n)?)'
)


def insert_meta(text, meta_block):
    """Insert meta_block right after the toc_category line (and its commented
    toc_title sibling, if present). Returns new text or raises."""
    m = META_INSERT_RE.search(text)
    if not m:
        raise RuntimeError("could not locate 64er.toc_category insertion point")
    return text[: m.end()] + meta_block + text[m.end():]


def build_meta_block(rows):
    """Build the inserted meta-block string from one or more CSV rows."""
    out = []
    for r in rows:
        idx_cat = f"{r['cat1']}|{r['cat2']}"
        idx_title = r["title"]
        out.append(f'    <meta name="64er.index_title" content="{H.escape(idx_title)}">\n')
        out.append(f'    <meta name="64er.index_category" content="{H.escape(idx_cat)}">\n')
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--apply", action="store_true",
                    help="Actually modify files (default: dry-run)")
    ap.add_argument("--verify", action="store_true",
                    help="Verify each article has the meta tags or report")
    ap.add_argument("--csv", default=CSV_PATH)
    args = ap.parse_args()

    issue_dir = os.path.join(REPO_ROOT, "issues", args.issue)
    if not os.path.isdir(issue_dir):
        print(f"ERROR: issue dir not found: {issue_dir}", file=sys.stderr)
        sys.exit(1)

    html_paths = sorted(glob.glob(os.path.join(issue_dir, "*.html")))
    articles = [read_article_meta(p) for p in html_paths]
    rows = parse_csv_rows(args.csv, args.issue)

    print(f"Issue:           {args.issue}")
    print(f"HTML files:      {len(articles)}")
    print(f"CSV rows:        {len(rows)}")
    print()

    # Match each CSV row to an article.
    matches = []  # list of (row, article_path or None, reason)
    article_to_rows = defaultdict(list)
    for r in rows:
        art, reason = find_target_article(r, articles)
        if art:
            matches.append((r, art["path"], reason))
            article_to_rows[art["path"]].append(r)
        else:
            matches.append((r, None, reason))

    # Report matches.
    print("=== CSV → Article matches ===")
    for r, path, reason in matches:
        fn = os.path.basename(path) if path else "<NO MATCH>"
        print(f"  p{r['start_page']:>3} [{reason:<14}] {fn}")
        print(f"        cat={r['cat1']}|{r['cat2']}  title={r['title']!r}")

    no_match_rows = [m for m in matches if m[1] is None]

    # Articles with no CSV row.
    matched_paths = {p for _, p, _ in matches if p}
    no_csv_articles = [a for a in articles if a["path"] not in matched_paths]

    print()
    print("=== Articles with no CSV row ===")
    for a in no_csv_articles:
        print(f"  {os.path.basename(a['path'])}   pages={a['pages_attr']} title={a['title']!r}")

    print()
    print("=== Articles already having index_* meta ===")
    already = [a for a in articles if a["has_index"]]
    for a in already:
        print(f"  {os.path.basename(a['path'])}")

    # Verify-mode: just check each article.
    if args.verify:
        print()
        print("=== VERIFY ===")
        missing = []
        for a in articles:
            ok = a["has_index"]
            if not ok and a["path"] in article_to_rows:
                missing.append(a)
        if not missing:
            print("All matched articles have index_* meta tags.")
        else:
            for a in missing:
                print(f"  MISSING: {os.path.basename(a['path'])}")
        return

    # Plan and apply edits.
    print()
    print("=== Planned edits ===")
    planned = []
    for path, csv_rows in sorted(article_to_rows.items()):
        art = next(a for a in articles if a["path"] == path)
        if art["has_index"]:
            print(f"  SKIP (already has index_*): {os.path.basename(path)}")
            continue
        block = build_meta_block(csv_rows)
        print(f"  EDIT {os.path.basename(path)}  ({len(csv_rows)} row(s))")
        for line in block.splitlines():
            print(f"      {line}")
        planned.append((path, art["text"], block))

    print()
    if not args.apply:
        print(f"DRY-RUN: would modify {len(planned)} files. Re-run with --apply to write.")
        # Summary
        matched = sum(1 for _, p, _ in matches if p)
        print()
        print(f"Summary: csv_rows={len(rows)}  matched={matched}  "
              f"no_article={len(no_match_rows)}  no_csv_articles={len(no_csv_articles)}  "
              f"already_set={len(already)}  to_modify={len(planned)}")
        return

    modified = 0
    for path, text, block in planned:
        try:
            new_text = insert_meta(text, block)
        except RuntimeError as e:
            print(f"  ERROR ({os.path.basename(path)}): {e}")
            continue
        if new_text != text:
            with open(path, "w") as f:
                f.write(new_text)
            modified += 1
    print(f"Wrote {modified} files.")


if __name__ == "__main__":
    main()
