#!/usr/bin/env python3
"""
Stage B + C of the article-corpus pipeline.

B: out/NNN.json + out/NNN_boxes.png  -> one LLM call per page -> out/NNN.labels.json
C: out/NNN.labels.json               -> out/NNN.article.txt

The LLM is asked the ONE question geometry cannot answer: is this block editorial
matter the magazine wrote, or is it advertising / apparatus?  Everything geometry
already settles -- running heads, folios, facing-page slivers, hex dumps -- arrives
pre-labelled from stage A and the model is told to keep those labels unless the
page image plainly contradicts them.

It is given the overlay PNG as well as the text digest, because the decisive
evidence for an ad is usually visual (a bordered half-page with a product shot),
and because the block ids are drawn on the overlay so the model can tie the two
together.

out/NNN.article.txt is the deliverable: article text and nothing else.  A page
with no article content yields an empty file, which is a result, not a failure.
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw

OUT_DIR = "/Users/mist/DNB/8609/tmp/ocr/out"

# `claude -p` rather than the API: this box has no ANTHROPIC_API_KEY, and the CLI
# already carries the user's credentials.
CLAUDE = "claude"
CLAUDE_TIMEOUT = 300
# Each page is an independent call.  4 lanes keeps the box responsive; the
# font_experiments agent shares this machine and swap-thrashes if crowded.
LANES = 4

# Which labels make it into the corpus, and the reading order, come from stage A.
# Stage A writes a provisional article.txt with the same rules before the LLM has
# run, so if these were defined twice the two would eventually disagree.
# (Captions are OUT by the user's decision -- apparatus attached to a figure, not
# running text.  They are still LABELLED and kept in the JSON, so reversing that
# is a rebuild, not a re-OCR.  Errata columns ARE article and stay in.)
from ocr_blocks import ARTICLE_LABELS, reading_order   # noqa: E402

VALID_LABELS = ARTICLE_LABELS | {
    "listing-standalone", "ad", "kleinanzeige", "toc",
    "header", "footer", "sliver", "noise", "other",
}

# Column assignment for reading order.  Two blocks are in the same column when
# their left edges agree to within this fraction of page width; the magazine's
# columns are ~0.21 wide and gutters ~0.02, so 0.06 groups a column without
# swallowing its neighbour.
COLUMN_TOL = 0.06

COLOURS = {
    "body": (0, 170, 0), "heading": (0, 90, 255), "caption": (0, 200, 200),
    "listing-inline": (255, 140, 0), "listing-standalone": (255, 0, 200),
    "ad": (255, 0, 0), "kleinanzeige": (150, 0, 255), "toc": (255, 0, 120),
    "header": (255, 220, 0), "footer": (255, 220, 0),
    "sliver": (120, 120, 120), "noise": (200, 200, 200), "other": (90, 90, 90),
}

PROMPT = """You are labelling one page of the German home-computer magazine "64'er",
issue 9/September 1986, so that its ARTICLE TEXT can be extracted into a corpus.

Two inputs describe the same page:
1. The block digest below. Coordinates are fractions of the page (0,0 = top left).
   The `label` column is a provisional guess made from geometry alone.
2. The overlay image at {overlay}. READ THIS IMAGE FIRST with the Read tool.
   Every block is outlined there with its id printed at the top-left corner.

Assign a final label to every block id. Valid labels:

  body                editorial prose written by the magazine
  heading             headline, subhead or standfirst of an editorial article
  caption             figure/table caption of an editorial article ("Bild 3. ...")
  listing-inline      a SHORT code fragment inside article prose (a few lines,
                      quoted mid-argument, no caption of its own)
  listing-standalone  a type-in program: a BASIC listing or hex dump printed for
                      the reader to key in. Usually boxed, usually captioned
                      "Listing 1. ...". NOT article text however long or short.
  ad                  advertising of any kind: display ads, advertorials, the
                      publisher's own subscription/order/club promotions, coupons
  kleinanzeige        small classified ad
  toc                 table of contents, cover, masthead/Impressum
  header              running head at the top (section name, machine tag)
  footer              folio line at the foot (page number, "Ausgabe 9/September 1986")
  sliver              text belonging to the FACING page, caught at the extreme
                      left or right edge because the scan is not cropped
  noise               OCR garbage read out of a photo or a screened tint
  other               anything else

Rules:
- Keep the provisional label unless the image contradicts it. Geometry already
  settled headers, footers, slivers and hex dumps reliably.
- A page is often split: article on one side, an ad on the other. The split can be
  vertical OR horizontal. Judge each block by which side of the rule it sits on.
- An ad is identified by its border, product photography, prices, an order coupon,
  a company logo and address, and by NOT being covered by the page's running head.
- Editorial pages carry a running head; full-page ads carry none.
- Errata columns, editorials, interviews, reviews and news are editorial: body.
- Do not judge by subject matter. An ad for a disk drive and an article about a
  disk drive read alike; the layout is what separates them.

Return ONLY a JSON object, no prose, no code fence:
{{"page_kind": "<article|ad|mixed|toc|other>", "labels": {{"<id>": "<label>", ...}}}}
Every id in the digest must appear in "labels".

DIGEST:
{digest}
"""


def call_llm(page, digest, overlay):
    prompt = PROMPT.format(digest=digest, overlay=overlay)
    r = subprocess.run([CLAUDE, "-p", prompt, "--output-format", "text"],
                       capture_output=True, text=True, timeout=CLAUDE_TIMEOUT)
    out = r.stdout.strip()
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        raise RuntimeError(f"p{page}: no JSON in reply: {out[:300]}")
    return json.loads(m.group(0))


def redraw(page, blocks):
    src = os.path.join(OUT_DIR, f"{page:03d}_boxes.png")
    dst = os.path.join(OUT_DIR, f"{page:03d}_final.png")
    if not os.path.exists(src):
        return
    # The stage-A overlay is redrawn from the source thumb, so start from the
    # original page rather than stacking boxes on boxes.
    im = Image.open(os.path.join("/Users/mist/DNB/8609/thumbs_150", f"{page:03d}.png")).convert("RGB")
    W, H = im.size
    # Everything not going into the corpus is dimmed, so what remains at full
    # contrast IS the deliverable -- the overlay answers "what did we keep?" at a
    # glance instead of asking the eye to decode a dozen box colours.
    veil = Image.new("RGB", (W, H), (255, 255, 255))
    keep = Image.new("L", (W, H), 90)
    kd = ImageDraw.Draw(keep)
    for b in blocks:
        if b["label"] in ARTICLE_LABELS:
            x0, y0, x1, y1 = b["bbox_frac"]
            kd.rectangle([x0 * W - 4, y0 * H - 4, x1 * W + 4, y1 * H + 4], fill=255)
    im = Image.composite(im, veil, keep)

    d = ImageDraw.Draw(im)
    for b in blocks:
        x0, y0, x1, y1 = b["bbox_frac"]
        art = b["label"] in ARTICLE_LABELS
        c = COLOURS.get(b["label"], (255, 255, 0))
        d.rectangle([x0 * W, y0 * H, x1 * W, y1 * H], outline=c, width=3 if art else 1)
        if art:
            d.text((x0 * W + 3, max(0, y0 * H - 11)), f"{b['id']} {b['label']}", fill=c)
    im.save(dst)


def process(page):
    stem = f"{page:03d}"
    rec = json.load(open(os.path.join(OUT_DIR, stem + ".json"), encoding="utf-8"))
    digest = open(os.path.join(OUT_DIR, stem + ".digest.txt"), encoding="utf-8").read()
    overlay = os.path.join(OUT_DIR, stem + "_boxes.png")

    # An existing verdict is reused rather than re-asked, so changing what counts
    # as article text (captions in or out, say) is a rebuild and not 176 fresh
    # LLM calls.  Delete NNN.labels.json to force the page to be judged again.
    cached = os.path.join(OUT_DIR, stem + ".labels.json")
    if os.path.exists(cached):
        old = json.load(open(cached, encoding="utf-8"))
        verdict = {"page_kind": old.get("page_kind", "unknown"),
                   "labels": {str(b["id"]): b["llm_label"] for b in old["blocks"]
                              if b.get("llm_label")}}
    else:
        verdict = call_llm(page, digest, overlay)
    labels = {str(k): v for k, v in verdict.get("labels", {}).items()}

    for b in rec["blocks"]:
        new = labels.get(str(b["id"]))
        b["llm_label"] = new
        # An unknown or missing label falls back to the geometric guess rather
        # than silently dropping the block from the corpus.
        b["label"] = new if new in VALID_LABELS else b["label"]
    rec["page_kind"] = verdict.get("page_kind", "unknown")

    json.dump(rec, open(os.path.join(OUT_DIR, stem + ".labels.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    redraw(page, rec["blocks"])

    keep = [b for b in rec["blocks"] if b["label"] in ARTICLE_LABELS]
    text = "\n".join(b["text"].strip() for b in reading_order(keep) if b["text"].strip())
    art = os.path.join(OUT_DIR, stem + ".article.txt")
    open(art, "w", encoding="utf-8").write(text + ("\n" if text else ""))

    print(f"p{stem}: kind={rec['page_kind']:<8} kept {len(keep)}/{len(rec['blocks'])} blocks, "
          f"{len(text)} chars", flush=True)


def safe(page):
    try:
        process(page)
    except Exception as e:                      # one bad page must not stop 176
        print(f"p{page:03d}: FAILED {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    pages = [int(a) for a in sys.argv[1:]]
    with ThreadPoolExecutor(max_workers=LANES) as ex:
        list(ex.map(safe, pages))
