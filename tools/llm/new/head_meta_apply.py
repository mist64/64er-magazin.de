#!/usr/bin/env python3
"""
Fill 64er.head1 / 64er.head2 meta tags by extracting page headers from OCR.

For each article HTML the script:
  1. Reads <meta name="64er.pages">. Takes the first page in the range.
  2. Looks up the OCR `blocks.txt` for that page in
       issues/<ISSUE>/_work/p<NNN>/blocks.txt,
     falling back to _work_v2, _work_v3, _work_v4, _work_v5.
  3. Applies a heuristic to find the two top-of-page labels:
        head1 = section / column name (e.g. "Tips & Tricks")
        head2 = target-machine label  (e.g. "C 64", "C 64/C 128")
  4. Cleans up common OCR substitutions inside head2
     ("C 64IC 128" -> "C 64/C 128", "C_64AIVC 20" -> "C 64/VC 20", …).
  5. Inserts two <meta> lines (head1 first, then head2) immediately BEFORE
     the existing 64er.toc_category line.  Skip if either meta is already
     present.

Usage:
  python3 tools/llm/new/head_meta_apply.py 8606            # dry-run / report
  python3 tools/llm/new/head_meta_apply.py 8606 --apply    # actually edit
  python3 tools/llm/new/head_meta_apply.py 8606 --verify   # verify only

Run from repo root.
"""

import argparse
import glob
import html as H
import os
import re
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

WORK_DIRS = ["_work", "_work_v2", "_work_v3", "_work_v4", "_work_v5"]

# Vertical band where the running headers live (300-DPI page is ~3500px tall).
HEADER_Y_MAX = 260

# Sane height range for header text.
HEADER_H_MIN = 25
HEADER_H_MAX = 100

# Sane width range for header text (excludes full-width rule lines etc).
HEADER_W_MIN = 100
HEADER_W_MAX = 800

# Articles that should never get head1/head2 (by 64er.id).
SKIP_IDS = {
    "editorial",
    "impressum",
    "inhalt",
    "vorschau",
}

# Page numbers that should never get head1/head2 (front-matter / classifieds / ads).
# Front matter / TOC area / classifieds area in 8606.
SKIP_PAGES = set(range(1, 8))  # 1-7
SKIP_PAGES.update(range(105, 134))  # classifieds + ads block (verified by OCR scan)
SKIP_PAGES.update(range(180, 188))  # back matter / ads


# ---------- block parsing ----------

BLOCK_RE = re.compile(
    r"^block=(\d+)\s+bbox=(\d+)x(\d+)\+(\d+)\+(\d+)\s+nw=(\d+)\s*(.*)$"
)


def parse_blocks(path):
    """Yield dicts {bn, w, h, x, y, nw, text} for each block in a blocks.txt."""
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = BLOCK_RE.match(line)
            if not m:
                continue
            bn, w, h, x, y, nw, text = m.groups()
            out.append({
                "bn": int(bn),
                "w": int(w),
                "h": int(h),
                "x": int(x),
                "y": int(y),
                "nw": int(nw),
                "text": text.strip(),
            })
    return out


def find_blocks_file(issue_dir, page):
    """Return first existing blocks.txt for `page` (int), trying _work, _work_v2, …."""
    for wd in WORK_DIRS:
        cand = os.path.join(issue_dir, wd, f"p{page:03d}", "blocks.txt")
        if os.path.isfile(cand):
            return cand, wd
    return None, None


# ---------- machine label detection / cleanup ----------

# Tokens that suggest this block is a machine label.
MACHINE_TOKENS = ("64", "128", "16", "20", "VC", "CP/M", "CP", "M", "Amiga", "PC")

# Recognised machine names after cleanup.
MACHINE_NAMES = {"C 64", "C 128", "C 16", "VC 20", "CP/M", "Amiga", "PC"}


def looks_like_machine_label(text):
    """Heuristic: does this text look like a printed machine-name header?"""
    if not text:
        return False
    t = text.strip()
    # Strip trailing punctuation.
    t = re.sub(r"[\s\.;,:!?“”„]+$", "", t)
    # OCR often turns "C" into "Cc" and "CP/M" into "CP/IM" or "CPIM".
    # Use a lenient check: length is short and most characters are digits, /, space
    # or known letters from machine names.
    if len(t) > 25:
        return False
    if len(t) < 2:
        return False
    upper = t.upper()
    # Must contain at least one digit OR a /-separator OR "AMIGA"/"CP" string
    has_digit = any(c.isdigit() for c in upper)
    has_amiga = "AMIGA" in upper
    has_cp = "CP" in upper and ("M" in upper or "/" in upper or "I" in upper)
    if not (has_digit or has_amiga or has_cp):
        return False
    # Reject obvious section-name words.
    bad_words = (
        "TIPS", "TRICKS", "EFFEKTIVES", "GRUNDLAGEN", "SPEICHER", "SPIELE",
        "SOFTWARE", "HARDWARE", "LISTING", "ANWENDUNG", "DATEN", "BÜCHER",
        "BUCHER", "AKTUELLES", "VORSCHAU", "IMPRESSUM", "LESERFORUM",
        "EXTRA", "MONAT", "ASSEMBLER", "BASIC", "WANDERVORSCHL",
        "KNOBELEIEN", "FEHLERTEUFELCHEN", "HILFE", "TEST",
    )
    for w in bad_words:
        if w in upper:
            return False
    return True


def clean_machine_label(text):
    """Fix common OCR substitutions inside a machine-label string."""
    if not text:
        return text
    t = text.strip()
    # Strip leading/trailing punctuation.
    t = re.sub(r"^[\s\W_]+|[\s\W_]+$", "", t, flags=re.UNICODE)

    # Common OCR errors at the start, e.g. "Cc 128" -> "C 128".
    t = re.sub(r"^Cc\b", "C", t)
    # "CPIM" -> "CP/M", "CP/IM" -> "CP/M"
    t = re.sub(r"\bCP[/]?IM\b", "CP/M", t)
    t = re.sub(r"\bCPM\b", "CP/M", t)

    # "6A4" -> "64" anywhere (OCR mis-recognises the "/" between digits as "A")
    t = re.sub(r"6A4", "64", t)
    # Stray "A" inside machine name: "64A" -> "64" when followed by separator char
    t = re.sub(r"(?<=64)A(?=[ICN/])", "", t)

    # "C_64" -> "C 64", "C_128" -> "C 128"  (handle optional space around underscore)
    t = re.sub(r"\bC[_\s]+(?=\d)", "C ", t)
    t = re.sub(r"\bVC[_\s]+(?=\d)", "VC ", t)

    # Mid-word "I" or "1" between machines should be "/":
    #   "C 64IC 128" -> "C 64/C 128"
    #   "C 641 VC 20" -> "C 64/VC 20"
    # Lookahead accepts "C ..", "VC ..", "CP/M" or "Amiga".
    for _ in range(4):
        new = re.sub(
            r"(\d)\s*[AI1]+\s*(?=(?:C|VC|CP|Amiga)\b)",
            r"\1/",
            t,
        )
        if new == t:
            break
        t = new

    # "INC 20" / "...INC 20"  -> "VC 20"  (OCR sees the "/V" as "IN")
    t = re.sub(r"INC\s*20\b", "/VC 20", t)
    # "NC 20" -> "/VC 20"
    t = re.sub(r"(?<![A-Z/])NC\s*20\b", "/VC 20", t)

    # Insert missing slash between adjacent machine names:
    #   "C 64VC 20"  -> "C 64/VC 20"
    #   "C 64C 128"  -> "C 64/C 128"   (defensive)
    for _ in range(3):
        new = re.sub(
            r"(\d)\s+(?=(?:VC|C)\s*\d)",
            r"\1/",
            t,
        )
        if new == t:
            break
        t = new

    # Normalise spaces around '/'
    t = re.sub(r"\s*/\s*", "/", t)
    # Tidy whitespace.
    t = re.sub(r"\s+", " ", t).strip()
    return t


def clean_section_header(text):
    """Tidy up an OCR'd section header (head1)."""
    if not text:
        return text
    t = text.strip()
    # Collapse weird whitespace.
    t = re.sub(r"\s+", " ", t)
    # Drop a leading lone glyph if OCR added something weird.
    t = re.sub(r"^[^\w\(\[]+", "", t, flags=re.UNICODE)
    # Drop trailing punctuation noise.
    t = re.sub(r"[\s\.;,:!?]+$", "", t)
    # Fix "Tips &Tricks" / "Tips&Tricks" / "Tips& Tricks" / "ips& Tricks"
    # -> "Tips & Tricks"
    t = re.sub(r"\b[Tt]?ips\s*&\s*Tricks?\b", "Tips & Tricks", t)
    return t


def is_header_block(b):
    """True if a block sits in the top header band with sane dimensions."""
    if b["y"] >= HEADER_Y_MAX:
        return False
    if b["h"] < HEADER_H_MIN or b["h"] > HEADER_H_MAX:
        return False
    if b["w"] < HEADER_W_MIN or b["w"] > HEADER_W_MAX:
        return False
    if not b["text"]:
        return False
    # OCR sometimes leaves a stray "block=NN nwords=... text=" prefix in text;
    # skip blocks whose text starts with 'block='.
    if b["text"].startswith("block="):
        return False
    # Reject blocks that look like body text (lots of words spilling into header band).
    if b["nw"] > 10:
        return False
    return True


def extract_head1_head2(blocks):
    """Return (head1_raw, head2_raw, confidence) — strings or None."""
    cands = [b for b in blocks if is_header_block(b)]
    if not cands:
        return None, None, "no-match"

    # Identify machine-label candidates among the headers.
    machine = [b for b in cands if looks_like_machine_label(b["text"])]
    section = [b for b in cands if b not in machine]

    # Sort by X to know what's at outer edge vs inner.
    cands_sorted = sorted(cands, key=lambda b: b["x"])

    head2_block = None
    head1_block = None

    if machine:
        # If multiple machine candidates, prefer the one nearest a page edge.
        machine_sorted = sorted(
            machine,
            key=lambda b: min(b["x"], 2480 - (b["x"] + b["w"])),
        )
        head2_block = machine_sorted[0]
    # head1: the non-machine block furthest from head2 (or just the largest non-machine).
    if section:
        if head2_block is not None:
            # Prefer the section block on the opposite side of the page.
            head2_centre_left = (head2_block["x"] < 1240)
            opposite = [b for b in section if (b["x"] >= 1240) != head2_centre_left]
            if not opposite:
                opposite = section
            # Pick the widest opposite block.
            head1_block = max(opposite, key=lambda b: b["w"])
        else:
            head1_block = max(section, key=lambda b: b["w"])

    if not head1_block and not head2_block:
        return None, None, "no-match"

    head1 = head1_block["text"] if head1_block else None
    head2 = head2_block["text"] if head2_block else None

    conf = "clear-match" if (head1_block and head2_block) else "heuristic-guess"
    return head1, head2, conf


# ---------- HTML helpers ----------

PAGES_RE = re.compile(r'<meta name="64er\.pages"\s+content="([^"]*)"')
TOC_CAT_RE = re.compile(r'<meta name="64er\.toc_category"\s+content="([^"]*)"')
ID_RE = re.compile(r'<meta name="64er\.id"\s+content="([^"]*)"')
HEAD1_RE = re.compile(r'<meta name="64er\.head1"')
HEAD2_RE = re.compile(r'<meta name="64er\.head2"')

# Match the toc_category meta line including the leading indent and trailing newline.
TOC_CAT_LINE_RE = re.compile(
    r'^([ \t]*)<meta name="64er\.toc_category"\s+content="[^"]*">\s*\n',
    re.MULTILINE,
)


def expand_pages(pages_attr):
    out = []
    for seg in pages_attr.split(","):
        seg = seg.strip()
        if not seg:
            continue
        if "-" in seg:
            lo, hi = seg.split("-", 1)
            try:
                out.extend(range(int(lo), int(hi) + 1))
            except ValueError:
                pass
        else:
            try:
                out.append(int(seg))
            except ValueError:
                pass
    return out


def read_article_meta(path):
    text = open(path, encoding="utf-8").read()
    pages_m = PAGES_RE.search(text)
    toc_m = TOC_CAT_RE.search(text)
    id_m = ID_RE.search(text)
    pages = expand_pages(pages_m.group(1)) if pages_m else []
    return {
        "path": path,
        "text": text,
        "pages_attr": pages_m.group(1) if pages_m else "",
        "pages": pages,
        "start": pages[0] if pages else None,
        "toc_category": toc_m.group(1) if toc_m else "",
        "id": id_m.group(1) if id_m else "",
        "has_head1": bool(HEAD1_RE.search(text)),
        "has_head2": bool(HEAD2_RE.search(text)),
    }


def should_skip(art):
    """Return (skip_bool, reason)."""
    if art["id"] in SKIP_IDS:
        return True, f"id={art['id']}"
    if art["start"] is None:
        return True, "no-pages"
    if art["start"] in SKIP_PAGES:
        return True, f"page-{art['start']}-in-skip-range"
    return False, ""


def build_meta_block(indent, head1, head2):
    lines = []
    if head1:
        lines.append(f'{indent}<meta name="64er.head1" content="{H.escape(head1)}">\n')
    if head2:
        lines.append(f'{indent}<meta name="64er.head2" content="{H.escape(head2)}">\n')
    return "".join(lines)


def insert_meta(text, meta_block):
    """Insert meta_block immediately BEFORE the 64er.toc_category line."""
    m = TOC_CAT_LINE_RE.search(text)
    if not m:
        raise RuntimeError("could not locate 64er.toc_category line")
    return text[: m.start()] + meta_block + text[m.start():]


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    issue_dir = os.path.join(REPO_ROOT, "issues", args.issue)
    if not os.path.isdir(issue_dir):
        print(f"ERROR: issue dir not found: {issue_dir}", file=sys.stderr)
        sys.exit(1)

    html_paths = sorted(glob.glob(os.path.join(issue_dir, "*.html")))
    articles = [read_article_meta(p) for p in html_paths]

    print(f"Issue:           {args.issue}")
    print(f"HTML files:      {len(articles)}")
    print()

    plans = []
    skipped = []
    flagged = []
    head1_counter = Counter()
    head2_counter = Counter()

    print("=== Per-article extraction ===")
    for art in articles:
        fn = os.path.basename(art["path"])
        skip, reason = should_skip(art)
        if skip:
            skipped.append((fn, reason))
            print(f"  SKIP {fn:<70}  ({reason})")
            continue

        page = art["start"]
        blocks_path, work_src = find_blocks_file(issue_dir, page)
        if blocks_path is None:
            flagged.append((fn, page, "no-blocks-file", "", ""))
            print(f"  ??   p{page:>3}  {fn:<70}  no blocks.txt")
            continue

        blocks = parse_blocks(blocks_path)
        head1_raw, head2_raw, conf = extract_head1_head2(blocks)

        head1 = clean_section_header(head1_raw) if head1_raw else None
        head2 = clean_machine_label(head2_raw) if head2_raw else None

        if art["has_head1"] or art["has_head2"]:
            skipped.append((fn, "already-has-head"))
            print(f"  HAVE {fn:<70}  (head1/head2 already present)")
            continue

        if not head1 and not head2:
            flagged.append((fn, page, "no-headers-found", "", ""))
            print(f"  ??   p{page:>3}  {fn:<70}  no headers found ({work_src})")
            continue

        # Decide confidence.
        flag = ""
        if not head1 or not head2:
            flag = "partial"
        elif head2 not in MACHINE_NAMES and not all(
            m in head2 for m in head2.split("/")[:0]
        ):
            # head2 looks weird if it doesn't match a known machine name and
            # isn't an obvious composite like "C 64/C 128"
            ok = True
            parts = head2.split("/")
            for p in parts:
                if p.strip() not in MACHINE_NAMES:
                    ok = False
                    break
            if not ok:
                flag = "head2-unusual"

        if head1:
            head1_counter[head1] += 1
        if head2:
            head2_counter[head2] += 1

        print(f"  OK   p{page:>3}  {fn:<70}  src={work_src} conf={conf}"
              + (f" FLAG={flag}" if flag else ""))
        print(f"           head1={head1!r}  head2={head2!r}")
        if head1_raw and head1 != head1_raw:
            print(f"           (raw head1={head1_raw!r})")
        if head2_raw and head2 != head2_raw:
            print(f"           (raw head2={head2_raw!r})")

        plans.append({
            "art": art,
            "page": page,
            "work_src": work_src,
            "head1": head1,
            "head2": head2,
            "conf": conf,
            "flag": flag,
        })
        if flag:
            flagged.append((fn, page, flag, head1 or "", head2 or ""))

    print()
    print("=== Distinct head1 values ===")
    for v, c in head1_counter.most_common():
        print(f"  {c:>3}  {v!r}")
    print()
    print("=== Distinct head2 values ===")
    for v, c in head2_counter.most_common():
        print(f"  {c:>3}  {v!r}")

    print()
    print("=== Skipped ===")
    for fn, reason in skipped:
        print(f"  {fn:<70}  {reason}")

    print()
    print("=== Flagged for review ===")
    for fn, page, reason, h1, h2 in flagged:
        print(f"  p{page:>3}  {fn:<70}  {reason}  head1={h1!r} head2={h2!r}")

    print()
    print(f"Summary: total={len(articles)}  "
          f"to_fill={len(plans)}  skipped={len(skipped)}  "
          f"flagged={len(flagged)}")

    if args.verify:
        return

    if not args.apply:
        print()
        print(f"DRY-RUN: would modify {len(plans)} files. Re-run with --apply.")
        return

    modified = 0
    for p in plans:
        art = p["art"]
        # Find indent from the existing toc_category line.
        m = TOC_CAT_LINE_RE.search(art["text"])
        if not m:
            print(f"  ERROR {os.path.basename(art['path'])}: no toc_category line")
            continue
        indent = m.group(1)
        block = build_meta_block(indent, p["head1"], p["head2"])
        try:
            new_text = insert_meta(art["text"], block)
        except RuntimeError as e:
            print(f"  ERROR {os.path.basename(art['path'])}: {e}")
            continue
        if new_text != art["text"]:
            with open(art["path"], "w", encoding="utf-8") as f:
                f.write(new_text)
            modified += 1
    print(f"\nWrote {modified} files.")


if __name__ == "__main__":
    main()
