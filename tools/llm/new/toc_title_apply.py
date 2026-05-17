#!/usr/bin/env python3
"""
Fill `64er.toc_title` meta tags by matching article HTMLs against the printed
table of contents (parsed into _tmp/toc_entries.json under each issue).

TOC entries are records of the form
    {"page": <int>, "section": <str>, "prefix": <str or null>, "title": <str>}
where `page` is the page number listed in the TOC, `section` is the SECTION
banner header (AKTUELLES, HARDWARE-TEST, KURSE, …), `prefix` is the optional
bold sub-heading printed above the entry (e.g. "Tips & Tricks zum C 64 für
Profis" or "Anwendung des Monats"), and `title` is the entry text itself.

The script:
  1. Loads `<issue_dir>/_tmp/toc_entries.json`.
  2. For each article HTML in `issues/<issue>/`, reads its `64er.pages` set
     and `64er.toc_category`.
  3. Matches the article to one or more TOC entries using a combination of
     start-page, page-set membership, and title similarity.
  4. Builds a single `toc_title` string per article (combining multiple
     sub-entries that share a prefix into a single category line; multiple
     distinct entries get joined with " / ").
  5. Replaces the existing `<!-- <meta name="64er.toc_title" content="XXX"> -->`
     placeholder line with an active meta tag.

Usage:
  python3 tools/llm/new/toc_title_apply.py 8606            # dry-run / report
  python3 tools/llm/new/toc_title_apply.py 8606 --apply    # actually edit
  python3 tools/llm/new/toc_title_apply.py 8606 --verify   # verify only

Run from repo root.
"""

import argparse
import glob
import html as H
import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def expand_pages(pages_attr):
    """Expand '10-12,15' -> (set, ordered list)."""
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
    id_m = re.search(r'<meta name="64er\.id"\s+content="([^"]*)"', text)
    pages_attr = pages_m.group(1) if pages_m else ""
    pages_set, pages_list = expand_pages(pages_attr)
    start = pages_list[0] if pages_list else None

    # Detect active toc_title (NOT the commented placeholder).
    has_active_toc_title = False
    for m in re.finditer(r'<meta name="64er\.toc_title"\s+content="[^"]*">', text):
        # Check if this match is inside an HTML comment.
        snippet_start = max(0, m.start() - 40)
        ctx = text[snippet_start: m.end() + 4]
        # Look for an unclosed "<!--" immediately preceding.
        before = text[:m.start()]
        last_open = before.rfind("<!--")
        last_close = before.rfind("-->")
        if last_open > last_close:
            continue  # inside a comment
        has_active_toc_title = True
        break

    has_placeholder = bool(re.search(
        r"^    <!-- <meta name=\"64er\.toc_title\" content=\"XXX\"> -->\s*$",
        text, re.MULTILINE))

    return {
        "path": path,
        "text": text,
        "title": (title_m.group(1).strip() if title_m else ""),
        "toc_category": (toc_cat_m.group(1) if toc_cat_m else ""),
        "id": (id_m.group(1) if id_m else ""),
        "pages_attr": pages_attr,
        "pages_set": pages_set,
        "start": start,
        "has_active_toc_title": has_active_toc_title,
        "has_placeholder": has_placeholder,
    }


def normalize_for_compare(s):
    s = s.lower()
    s = H.unescape(s)
    s = re.sub(r"[^\wäöüß ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title_similarity(a, b):
    aw = set(normalize_for_compare(a).split())
    bw = set(normalize_for_compare(b).split())
    if not aw or not bw:
        return 0.0
    overlap = len(aw & bw)
    return overlap / min(len(aw), len(bw))


SECTION_TO_TOC_CATEGORY = {
    # Normalized section -> set of toc_category labels it can match.
    "AKTUELLES":                {"Aktuelles"},
    "HARDWARE-TEST":            {"Hardware-Test"},
    "COMPUTERZUBEHÖR":          {"Computerzubehör"},
    "DATEIVERWALTUNG":          {"Dateiverwaltung"},
    "WETTBEWERBE":              {"Wettbewerbe", "Wettbewerbe|Anwendung des Monats"},
    "LISTINGS ZUM ABTIPPEN":    {"Listings zum Abtippen"},
    "SOFTWARE-HILFE":           {"Software-Hilfe"},
    "64'er Extra":              {"64'er Extra"},
    "KURSE":                    {"Kurse"},
    "SOFTWARE-TEST":            {"Software-Test"},
    "SPIELE-TEST":              {"Spiele-Test"},
    "RUBRIKEN":                 {"Rubriken"},
}


def section_matches_article(section, toc_cat):
    """Loose match: TOC section matches article's toc_category (or its
    first '|'-separated part)."""
    if not toc_cat:
        # Editorial-style articles with empty toc_category — only match RUBRIKEN.
        return section == "RUBRIKEN"
    parts = toc_cat.split("|")
    candidates = SECTION_TO_TOC_CATEGORY.get(section, set())
    if any(p in candidates for p in parts):
        return True
    if toc_cat in candidates:
        return True
    # Fallback: case-insensitive substring.
    cat_norm = parts[0].lower()
    return cat_norm == section.lower() or cat_norm in section.lower() or section.lower() in cat_norm


def entry_match_score(entry, article):
    """Return a numeric match score (higher = better)."""
    score = 0.0

    # Manual override: when the entry has a `hint_id` field, only the
    # article with that exact `64er.id` is allowed to match.
    hint = entry.get("hint_id")
    if hint:
        if article.get("id") == hint:
            score += 100.0
        else:
            return -1.0, 0.0

    if entry["page"] == article["start"]:
        score += 10.0
    elif entry["page"] in article["pages_set"]:
        score += 3.0
    elif article["start"] is not None and abs(entry["page"] - article["start"]) == 1:
        score += 1.5  # off-by-one (continuation from previous page)

    # Section / category match.
    if section_matches_article(entry["section"], article["toc_category"]):
        score += 2.0

    # Title similarity (between article <title> and entry text).
    entry_text = entry["title"]
    if entry["prefix"]:
        entry_text = entry["prefix"] + " " + entry["title"]
    sim_title = title_similarity(article["title"], entry["title"])
    sim_full = title_similarity(article["title"], entry_text)
    sim = max(sim_title, sim_full)
    score += 3.0 * sim

    # Extra boost when the article title nearly EQUALS the entry's main
    # title (not just substring) — this distinguishes "ProDisc — eine
    # professionelle Diskettenverwaltung" (article == entry) from
    # "Wir suchen die Anwendung des Monats" (article merely contains some
    # words of the entry's prefix). When the match is exact (1.0) we
    # award an even larger bonus so the entry's main-title-is-the-article-
    # title relationship dominates over any prefix-keyword boost on
    # another article.
    if sim_title >= 0.9:
        score += 15.0

    # When the entry's prefix is a category label (e.g. "Tips & Tricks
    # zum C 64 für Einsteiger") and the article title matches that prefix
    # (e.g. "Tips & Tricks für Einsteiger"), boost. Multi-word prefixes
    # only — single-word prefixes like "Grafik" or "Anwendung" are too
    # generic to disambiguate.
    if entry["prefix"]:
        prefix_words = set(normalize_for_compare(entry["prefix"]).split())
        prefix_sim = title_similarity(article["title"], entry["prefix"])
        if len(prefix_words) >= 3 and prefix_sim >= 0.5:
            if prefix_sim >= 0.99:
                score += 10.0  # exact prefix match dominates
            else:
                score += 3.0 * prefix_sim

    return score, sim


def assign_entries_to_articles(toc_entries, articles):
    """Return (article_path -> [entry, ...]) plus list of orphan entries."""
    assignments = defaultdict(list)
    orphan_entries = []

    for entry in toc_entries:
        scored = []
        for a in articles:
            score, sim = entry_match_score(entry, a)
            scored.append((score, sim, a))

        scored.sort(key=lambda t: (-t[0], -t[1]))
        if not scored:
            orphan_entries.append(entry)
            continue
        best_score, best_sim, best_art = scored[0]
        # Threshold: a real match requires either start-page+section,
        # high page-set membership, or strong title similarity.
        if best_score < 4.0:
            orphan_entries.append(entry)
            continue
        # Also reject if the best article isn't even on the entry's page.
        if entry["page"] not in best_art["pages_set"] and best_sim < 0.5:
            orphan_entries.append(entry)
            continue
        # Reject when section mismatches AND title similarity is weak AND
        # the entry's page is not the article's start page (i.e. the
        # article merely has the page in its range, but covers a totally
        # different topic). This catches TOC entries whose corresponding
        # article is missing from the issue, while keeping start-page
        # matches that cover multiple TOC items (e.g. one article being
        # both the music-contest winner and its own listing).
        if (
            not section_matches_article(entry["section"], best_art["toc_category"])
            and best_sim < 0.5
            and entry["page"] != best_art["start"]
        ):
            orphan_entries.append(entry)
            continue
        assignments[best_art["path"]].append(entry)

    return assignments, orphan_entries


def render_toc_title(entries):
    """Render a list of TOC entries assigned to one article into a single
    toc_title attribute string.

    Strategy:
      - Deduplicate by (prefix, title).
      - If only one unique entry: return "prefix: title" if prefix exists,
        else title.
      - If multiple entries share the same non-null prefix, return just the
        prefix (this is the Tips & Tricks case — many sub-entries under one
        bold category header).
      - Otherwise join entries with " / ".
    """
    if not entries:
        return None

    # Dedup by (prefix, title) — handles cross-references in TOC.
    seen = set()
    unique = []
    for e in entries:
        key = (e.get("prefix") or "", e["title"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)

    if len(unique) == 1:
        e = unique[0]
        if e["prefix"]:
            return f"{e['prefix']}: {e['title']}"
        return e["title"]

    # Multiple entries: check if all share the same prefix.
    prefixes = {e["prefix"] for e in unique}
    if len(prefixes) == 1 and None not in prefixes:
        return unique[0]["prefix"]

    # Otherwise join.
    parts = []
    for e in unique:
        if e["prefix"]:
            parts.append(f"{e['prefix']}: {e['title']}")
        else:
            parts.append(e["title"])
    return " / ".join(parts)


PLACEHOLDER_RE = re.compile(
    r'^(    )<!-- <meta name="64er\.toc_title" content="XXX"> -->\s*$',
    re.MULTILINE,
)


def replace_placeholder(text, toc_title):
    """Replace the placeholder line with an active meta tag. Returns
    new_text or None if placeholder wasn't found."""
    # Escape only " and & — leave existing HTML markup (<b>, <br>) intact.
    safe = toc_title.replace("&", "&amp;").replace('"', "&quot;")
    # But if the user already used HTML entities like &amp; in the JSON,
    # don't double-escape. We'll do a smarter pass: only escape raw "&"
    # not followed by a known entity.
    # Simpler: do not escape; the JSON-supplied value should be ready-to-go.
    # Just escape '"' since we wrap in double quotes.
    safe = toc_title.replace('"', "&quot;")
    replacement = f'\\1<meta name="64er.toc_title" content="{safe}">'
    new_text, n = PLACEHOLDER_RE.subn(replacement, text, count=1)
    if n == 0:
        return None
    return new_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--apply", action="store_true",
                    help="Actually modify files (default: dry-run)")
    ap.add_argument("--verify", action="store_true",
                    help="Verify each article has the meta tag or report")
    ap.add_argument("--toc-json", default=None,
                    help="Path to toc_entries.json (default: <issue>/_tmp/toc_entries.json)")
    args = ap.parse_args()

    issue_dir = os.path.join(REPO_ROOT, "issues", args.issue)
    if not os.path.isdir(issue_dir):
        print(f"ERROR: issue dir not found: {issue_dir}", file=sys.stderr)
        sys.exit(1)

    toc_json = args.toc_json or os.path.join(issue_dir, "_tmp", "toc_entries.json")
    if not os.path.isfile(toc_json):
        print(f"ERROR: toc entries not found: {toc_json}", file=sys.stderr)
        sys.exit(1)

    with open(toc_json) as f:
        toc_entries = json.load(f)

    html_paths = sorted(glob.glob(os.path.join(issue_dir, "*.html")))
    articles = [read_article_meta(p) for p in html_paths]

    print(f"Issue:           {args.issue}")
    print(f"HTML files:      {len(articles)}")
    print(f"TOC entries:     {len(toc_entries)}")
    print()

    assignments, orphans = assign_entries_to_articles(toc_entries, articles)

    # Build per-article toc_title.
    print("=== Article -> TOC entries -> toc_title ===")
    planned = []  # list of (path, new_text, toc_title, entries)
    no_match = []   # articles with no TOC match (will keep placeholder)
    already_set = []  # articles with non-placeholder toc_title already
    no_placeholder = []  # articles where title==toc_title (no placeholder)
    matched = []
    for a in articles:
        entries = assignments.get(a["path"], [])
        fn = os.path.basename(a["path"])
        if a["has_active_toc_title"]:
            already_set.append(a)
            print(f"  SKIP (already set)   {fn}")
            continue
        if not entries:
            no_match.append(a)
            print(f"  NO MATCH             {fn}  (pages={a['pages_attr']})")
            continue
        toc_title = render_toc_title(entries)
        matched.append((a, entries, toc_title))
        if not a["has_placeholder"]:
            # No placeholder to replace. This is the convention for
            # articles whose <title> already equals the TOC title — the
            # generator falls back to <title>. Nothing to do.
            no_placeholder.append((a, toc_title))
            print(f"  NO PLACEHOLDER       {fn}  (toc_title would be: {toc_title!r})")
            continue
        new_text = replace_placeholder(a["text"], toc_title)
        if new_text is None:
            print(f"  ERROR: no placeholder line in {fn}")
            continue
        planned.append((a["path"], new_text, toc_title, entries))
        entry_repr = " | ".join(
            (e["prefix"] + ": " + e["title"]) if e["prefix"] else e["title"]
            for e in entries
        )
        print(f"  MATCH                {fn}")
        print(f"      entries: {entry_repr}")
        print(f"      title:   {toc_title!r}")

    print()
    print("=== Orphan TOC entries (no article match) ===")
    for e in orphans:
        prefix = (e["prefix"] + ": ") if e["prefix"] else ""
        print(f"  p{e['page']:>3}  [{e['section']}]  {prefix}{e['title']}")

    print()
    print("=== Articles with placeholder kept (no TOC match) ===")
    for a in no_match:
        print(f"  {os.path.basename(a['path'])}  pages={a['pages_attr']}")

    print()
    print("=== Articles with no placeholder (title likely == toc_title) ===")
    for a, toc_title in no_placeholder:
        print(f"  {os.path.basename(a['path'])}  would-be: {toc_title!r}")

    print()
    print("=== Articles already-set ===")
    for a in already_set:
        print(f"  {os.path.basename(a['path'])}")

    if args.verify:
        print()
        print("=== VERIFY ===")
        missing = [a for a in articles
                   if not a["has_active_toc_title"] and a["has_placeholder"]
                   and a["path"] in assignments]
        if not missing:
            print("All matched articles have active toc_title.")
        else:
            for a in missing:
                print(f"  MISSING: {os.path.basename(a['path'])}")
        return

    print()
    print(f"Summary: toc_entries={len(toc_entries)}  "
          f"orphans={len(orphans)}  matched_articles={len(matched)}  "
          f"no_match_articles={len(no_match)}  already_set={len(already_set)}  "
          f"to_modify={len(planned)}")

    if not args.apply:
        print()
        print(f"DRY-RUN: would modify {len(planned)} files. Re-run with --apply to write.")
        return

    modified = 0
    for path, new_text, toc_title, entries in planned:
        with open(path, "w") as f:
            f.write(new_text)
        modified += 1
    print(f"Wrote {modified} files.")


if __name__ == "__main__":
    main()
