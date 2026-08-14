#!/usr/bin/env python3
"""
Gather everything worth eyeballing into out/review/, one flat directory.

Per page:
    pNNN.png   the overlay -- final labels if stage B has run, otherwise the
               stage-A geometric guess
    pNNN.txt   the article text that page contributes to the corpus

The two names sort adjacently, so scrolling the directory shows each page's
picture immediately followed by the text taken off it -- which is the only way to
spot a false positive (text present that should not be) or a false negative (text
missing that should be there).

INDEX.txt is the triage list: pages are ordered MOST SUSPICIOUS FIRST, not by
page number, because with 176 pages the ones worth a human's attention are the
handful where the evidence disagrees with itself.
"""

import json
import os
import shutil

OUT_DIR = "/Users/mist/DNB/8609/tmp/ocr/out"
# Deliberately OUTSIDE OUT_DIR.  OUT_DIR is a working directory -- json, digests,
# per-page tsv leftovers, two kinds of overlay -- and a reviewer should not have
# to pick the three files that matter out of nine hundred.
REVIEW_DIR = "/Users/mist/DNB/8609/tmp/ocr/review"
PAGES = range(1, 177)

# A page earns a flag when its signals contradict each other.  These are triage
# hints for a human, never automatic corrections.
SHORT_ARTICLE_CHARS = 400    # "article" page with less text than a long caption
BIG_AD_CHARS = 200           # page called ad/toc that still yielded text
NOISE_FRAC = 0.35            # this much of the page read as OCR garbage


def flags(rec, chars):
    out = []
    blocks = rec.get("blocks", [])
    kind = rec.get("page_kind", "?")
    labels = [b["label"] for b in blocks]
    n = max(1, len(labels))

    if kind in ("article", "mixed") and chars < SHORT_ARTICLE_CHARS:
        out.append("article-page-but-little-text")
    if kind in ("ad", "toc", "other") and chars > BIG_AD_CHARS:
        out.append("non-article-page-but-text-kept")
    if labels.count("noise") / n > NOISE_FRAC:
        out.append("mostly-noise")
    if not any(l == "header" for l in labels) and kind in ("article", "mixed"):
        # every editorial page carries a running head; its absence on a page
        # called editorial means either the head was missed or the call is wrong
        out.append("no-running-head")
    if any(l == "header" for l in labels) and kind == "ad":
        out.append("running-head-on-an-ad")
    if not blocks:
        out.append("no-blocks-at-all")
    return out


def main():
    if os.path.exists(REVIEW_DIR):
        shutil.rmtree(REVIEW_DIR)
    os.makedirs(REVIEW_DIR)

    rows = []
    for p in PAGES:
        stem = f"{p:03d}"
        final = os.path.join(OUT_DIR, stem + "_final.png")
        boxes = os.path.join(OUT_DIR, stem + "_boxes.png")
        art = os.path.join(OUT_DIR, stem + ".article.txt")
        labels = os.path.join(OUT_DIR, stem + ".labels.json")
        plain = os.path.join(OUT_DIR, stem + ".json")

        src_png = final if os.path.exists(final) else (boxes if os.path.exists(boxes) else None)
        if src_png:
            shutil.copyfile(src_png, os.path.join(REVIEW_DIR, f"p{stem}.png"))

        chars = 0
        if os.path.exists(art):
            shutil.copyfile(art, os.path.join(REVIEW_DIR, f"p{stem}.txt"))
            chars = os.path.getsize(art)

        rec = {}
        for cand in (labels, plain):
            if os.path.exists(cand):
                rec = json.load(open(cand, encoding="utf-8"))
                break
        if not rec:
            continue

        rows.append({
            "page": p,
            "kind": rec.get("page_kind", "-"),
            "blocks": len(rec.get("blocks", [])),
            "chars": chars,
            "staged": "B" if os.path.exists(labels) else "A",
            "flags": flags(rec, chars),
        })

    rows.sort(key=lambda r: (-len(r["flags"]), r["page"]))
    lines = [
        "Review index -- most suspicious first, then page order.",
        "A flagged page is one whose signals disagree; it is a hint, not a verdict.",
        "",
        f"{'page':>4}  {'stage':<5} {'kind':<8} {'blocks':>6} {'chars':>6}  flags",
    ]
    for r in rows:
        lines.append(f"p{r['page']:03d}  {r['staged']:<5} {r['kind']:<8} "
                     f"{r['blocks']:>6} {r['chars']:>6}  {', '.join(r['flags'])}")

    flagged = sum(1 for r in rows if r["flags"])
    total_chars = sum(r["chars"] for r in rows)
    empty = sum(1 for r in rows if r["chars"] == 0)
    lines += ["",
              f"{len(rows)} pages, {flagged} flagged, {empty} with no article text, "
              f"{total_chars} chars of corpus total."]
    open(os.path.join(REVIEW_DIR, "INDEX.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[-1:]))
    print("review dir:", REVIEW_DIR)


if __name__ == "__main__":
    main()
