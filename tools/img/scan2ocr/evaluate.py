#!/usr/bin/env python3
"""
Ground-truth evaluation for the scan2ocr corpus.

A vision model reads the page image and transcribes the article text under the
SAME rules the pipeline follows.  Its transcription is not truth in an absolute
sense -- it misreads characters too -- but it fails in completely different ways
from tesseract-plus-geometry, so where the two disagree is where our bugs are.

    truth/NNN.txt     what vision read off the page
    out/NNN.article.txt   what the pipeline produced
    report.jsonl      per-page scores
    WORST.txt         pages ranked by how badly they disagree

Three numbers, each answering a different question.  They are deliberately NOT
combined into one score, because the fixes they imply are different:

  recall    of the paragraphs vision found, how many did we produce?
            LOW  => we are LOSING article text (a dropped panel, a skipped
                    column, a region tesseract never read).  The worst failure.
  precision of the paragraphs we produced, how many did vision also see?
            LOW  => we are KEEPING text that is not article -- ad copy, OCR
                    gibberish off a photo, a running head.
  order     of the paragraphs both agree on, are they in the same sequence?
            LOW  => the flow is wrong: columns interleaved, a panel woven into
                    the text beside it, a headline stranded at the foot.

Matching is fuzzy at the token level, because the two sides will never agree
character for character -- one says "Zeichensatz" where the other says
"Zeichensotz".  Chasing character identity would just measure tesseract's
error rate, which is not what this harness is for.
"""

import json
import os
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

SRC_DIR = "/Users/mist/DNB/8609/tmp/master600/final"
OUT_DIR = "/Users/mist/DNB/8609/tmp/ocr/out"
TRUTH_DIR = "/Users/mist/DNB/8609/tmp/ocr/truth"
REPORT = "/Users/mist/DNB/8609/tmp/ocr/report.jsonl"
WORST = "/Users/mist/DNB/8609/tmp/ocr/WORST.txt"

CLAUDE = "claude"
CLAUDE_TIMEOUT = 600
LANES = 4

# Two paragraphs are "the same paragraph" above this token-sequence similarity.
# Set from what the two sides actually look like: a genuine match between a
# tesseract reading and a vision reading of the same paragraph lands well above
# it even with a dozen misread words, while unrelated paragraphs sit far below.
MATCH_MIN = 0.55
# Paragraphs shorter than this are ignored on both sides: a stray "(aw)" or a
# folio fragment is noise in the comparison, not evidence about the pipeline.
MIN_TOKENS = 4

TRUTH_PROMPT = """Transcribe the ARTICLE TEXT from the page image at {path}.
Read the image with the Read tool first.

This is a page of the German computer magazine "64'er", issue 9/September 1986.

INCLUDE, in the order a person reads them:
- article headlines, standfirsts and subheads
- article body text
- short code fragments quoted inside the prose

EXCLUDE completely:
- advertising of any kind, including the publisher's own subscription, club or
  order promotions, coupons and small classified ads
- the running head at the top (section name, machine tag like "C 64")
- the folio line at the foot (page number, "Ausgabe 9/September 1986")
- figure and table captions ("Bild 3. ...", "Tabelle 1. ...")
- standalone type-in listings: BASIC listings and hex dumps printed for the
  reader to key in, usually boxed and captioned "Listing 1. ..."

RULES:
- ONE LINE PER PARAGRAPH. Undo the printed line breaks inside a paragraph.
- Where a word is hyphenated across a line break, join it back together.
- A boxed panel or sidebar is its own run of paragraphs; keep it whole and place
  it where a reader would take it, rather than interleaving it with the text
  beside it.
- Transcribe what is printed, including 1986 spelling. Do not correct or
  modernise anything, and do not summarise.
- If the page carries no article text at all -- a full-page advertisement, for
  instance -- output the single line NO_ARTICLE_TEXT and nothing else.

Output ONLY the transcription. No commentary of any kind, no explanation of what
the page contains, no headings of your own, no code fences. Never describe the
page; either transcribe it or output NO_ARTICLE_TEXT.
"""


def norm_tokens(line):
    line = line.replace("¬", "")          # the line-break hyphen marker
    line = re.sub(r"[^\w\s]", " ", line.lower())
    return [t for t in line.split() if t]


def paragraphs(text):
    out = []
    for ln in text.splitlines():
        toks = norm_tokens(ln)
        if len(toks) >= MIN_TOKENS:
            out.append(toks)
    return out


def similarity(a, b):
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def build_truth(page):
    stem = f"{page:03d}"
    dest = os.path.join(TRUTH_DIR, stem + ".txt")
    if os.path.exists(dest):
        return
    # Run FROM the image directory and name the file bare: a nested `claude -p`
    # refuses to read paths outside its working directory, and silently wrote the
    # refusal into the truth file instead of a transcription.
    prompt = TRUTH_PROMPT.format(path=stem + ".png")
    r = subprocess.run([CLAUDE, "-p", prompt, "--output-format", "text"],
                       capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
                       cwd=SRC_DIR)
    open(dest, "w", encoding="utf-8").write(r.stdout.strip() + "\n")


def score(page):
    stem = f"{page:03d}"
    tp = os.path.join(TRUTH_DIR, stem + ".txt")
    pp = os.path.join(OUT_DIR, stem + ".article.txt")
    if not os.path.exists(tp) or not os.path.exists(pp):
        return None
    raw = open(tp, encoding="utf-8").read()
    if "NO_ARTICLE_TEXT" in raw:
        raw = ""
    truth = paragraphs(raw)
    ours = paragraphs(open(pp, encoding="utf-8").read())

    # Greedy best-match each truth paragraph against ours.  Greedy is adequate
    # because a paragraph that matches two candidates well is the same text
    # duplicated, which is itself a defect worth surfacing.
    used, pairs = set(), []
    for ti, t in enumerate(truth):
        best, bi = 0.0, None
        for oi, o in enumerate(ours):
            if oi in used:
                continue
            s = similarity(t, o)
            if s > best:
                best, bi = s, oi
        if bi is not None and best >= MATCH_MIN:
            used.add(bi)
            pairs.append((ti, bi, best))

    recall = len(pairs) / len(truth) if truth else (1.0 if not ours else 0.0)
    precision = len(pairs) / len(ours) if ours else (1.0 if not truth else 0.0)

    # Order: of the matched pairs, how often does our sequence agree with the
    # truth sequence?  Measured as concordant pairs (Kendall tau, rescaled to
    # 0..1) so that a single displaced paragraph costs a little and a wholly
    # scrambled page costs everything.
    order = 1.0
    if len(pairs) > 1:
        con = dis = 0
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                a = pairs[i][1] - pairs[j][1]
                if a < 0:
                    con += 1
                elif a > 0:
                    dis += 1
        order = con / (con + dis) if (con + dis) else 1.0

    return {
        "page": page,
        "truth_paras": len(truth), "our_paras": len(ours), "matched": len(pairs),
        "recall": round(recall, 3), "precision": round(precision, 3),
        "order": round(order, 3),
        "mean_match": round(statistics.mean([p[2] for p in pairs]), 3) if pairs else 0.0,
        "missing": [" ".join(truth[ti][:12]) for ti in range(len(truth))
                    if ti not in {p[0] for p in pairs}][:4],
        "extra": [" ".join(ours[oi][:12]) for oi in range(len(ours))
                  if oi not in used][:4],
    }


def main(pages):
    os.makedirs(TRUTH_DIR, exist_ok=True)
    with ThreadPoolExecutor(max_workers=LANES) as ex:
        list(ex.map(lambda p: _safe(build_truth, p), pages))

    rows = [r for r in (score(p) for p in pages) if r]
    with open(REPORT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if not rows:
        print("no pages scored")
        return
    print(f"{'page':>5}{'recall':>8}{'prec':>7}{'order':>7}{'match':>7}  {'truth/ours':>10}")
    for r in sorted(rows, key=lambda r: (r["recall"], r["order"], r["precision"])):
        print(f"p{r['page']:03d}{r['recall']:>8.2f}{r['precision']:>7.2f}"
              f"{r['order']:>7.2f}{r['mean_match']:>7.2f}  {r['truth_paras']:>4}/{r['our_paras']:<4}")
    print(f"\nMEAN  recall={statistics.mean(r['recall'] for r in rows):.3f}  "
          f"precision={statistics.mean(r['precision'] for r in rows):.3f}  "
          f"order={statistics.mean(r['order'] for r in rows):.3f}   ({len(rows)} pages)")

    with open(WORST, "w", encoding="utf-8") as f:
        for r in sorted(rows, key=lambda r: (r["recall"], r["order"])):
            if r["recall"] >= 0.98 and r["precision"] >= 0.98 and r["order"] >= 0.99:
                continue
            f.write(f"p{r['page']:03d}  recall={r['recall']} precision={r['precision']} "
                    f"order={r['order']}\n")
            for m in r["missing"]:
                f.write(f"    MISSING (vision saw, we did not): {m}\n")
            for e in r["extra"]:
                f.write(f"    EXTRA   (we produced, vision did not): {e}\n")
    print(f"worst pages: {WORST}")


def _safe(fn, p):
    try:
        fn(p)
    except Exception as e:
        print(f"p{p:03d}: {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]])
