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
SERVICE_ERRORS = ("session limit", "usage limit", "rate limit",
                  "Please run /login", "Invalid API key")
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
from ocr_blocks import ARTICLE_LABELS, SRC_DIR, reading_order   # noqa: E402

# Every label the prompt offers must appear here.  "caption" was missing -- it is
# offered to the model and excluded from the corpus, but was not listed as valid,
# so every block the model correctly called a caption failed validation and fell
# back to its GEOMETRIC label, which is "body".  Listing instructions, figure
# captions and table titles were reinstated as article text by that silent
# fallback, and no prompt wording could fix it because the model was right and its
# answer was being discarded.
VALID_LABELS = ARTICLE_LABELS | {
    "caption", "listing-standalone", "ad", "kleinanzeige", "toc",
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
                      This label also covers the listing's APPARATUS: its title
                      line, and any instruction attached to it such as "Das
                      Programm bitte mit dem MSE abtippen", "Beachten Sie die
                      Eingabehinweise auf Seite 51", "(Schluß)", or a REM line
                      quoted out of the listing body. OCR often mangles the word
                      "Listing" itself (it may read "Sting" or "Listin"), so
                      judge these from the image and from what the text says,
                      not from the spelling.
  ad                  advertising of any kind: display ads, advertorials, the
                      publisher's own subscription/order/club promotions, coupons
  kleinanzeige        small classified ad -- one placed BY A READER, in the
                      classifieds section, offering or seeking goods
  toc                 table of contents, cover, masthead/Impressum
  header              running head at the top (section name, machine tag)
  footer              folio line at the foot (page number, "Ausgabe 9/September 1986")
  sliver              text belonging to the FACING page, caught at the extreme
                      left or right edge because the scan is not cropped
  noise               OCR garbage read out of a photo or a screened tint, AND
                      text that is part of a FIGURE rather than of the prose --
                      the contents of a screen dump, a character table, a
                      labelled diagram, a boxed illustration. Such text is
                      printed inside the picture, not written as running text,
                      and does not belong in the corpus. A TABLE OF DATA is the
                      same case: a comparison table of models and specifications,
                      with column headings like "Hersteller / Druckgeschwindigkeit
                      / Schnittstellen", is a table a reader consults, not prose
                      a reader reads. Its cells do not belong in the corpus.
  other               apparatus that belongs to no article -- a publisher's
                      notice among the classifieds, for instance. Use this
                      SPARINGLY. Never use it for text an article carries with
                      it, however list-like that text looks: if the page is an
                      article and the text sits inside it, the label is body.

Rules:
- The provisional label is trustworthy ONLY for header, footer and listing-
  standalone -- those come from measurements of the page (position, digit
  density) that are reliable. A provisional "body" or "heading" means merely
  "this is text we could read"; it carries NO evidence that the text is article
  prose. Decide that yourself, from the image. Overriding a provisional body to
  ad, listing-standalone, noise or other is expected and correct whenever the
  page shows it is not article prose.
- A page is often split: article on one side, an ad on the other. The split can be
  vertical OR horizontal. Judge each block by which side of the rule it sits on.
- An ad is identified by its border, product photography, prices, an order coupon,
  a company logo and address, and by NOT being covered by the page's running head.
- Editorial pages carry a running head; full-page ads carry none. This is the
  single most reliable signal on the page and it OUTRANKS how promotional the
  layout looks. If a running head names a section of the magazine -- "Wettbewerb",
  "Software", "Grafik", "Aktuelles", "Anwendung des Monats" -- the page is
  editorial, and its text is body even when it is set in big coloured panels with
  prize money in display type. An advertiser cannot buy the magazine's own
  section head.
- Errata columns, editorials, interviews, reviews and news are editorial: body.
- Do not judge by subject matter. An ad for a disk drive and an article about a
  disk drive read alike; the layout is what separates them.
- An address or contact appendix that BELONGS TO an article is PART OF THAT
  ARTICLE and must be labelled body. This includes an "Info: <company>,
  <street>, <town>" line closing a review, and a long list of manufacturers or
  distributors with their addresses printed at the end of a comparison test --
  even when it runs to dozens of lines and looks like a directory. The magazine
  wrote it as part of the piece and a reader reads it as part of the piece.
  Do NOT label such a list "other" and do NOT label it "kleinanzeige". What makes
  something a classified is that a READER placed it in the classifieds section,
  never that it contains an address.
- A notice the PUBLISHER prints among the classifieds -- warning advertisers
  about pirated software, explaining the terms of placing an ad -- is apparatus
  belonging to the ad section, not an article. Label it other.

READING ORDER matters as much as the labels. The blocks are listed in the digest
in the order tesseract happened to emit them, which is NOT the order a person
reads the page. You decide the order.

Work it out from the page image and from how the text itself runs:
- A block that ends mid-sentence is continued by whichever block begins with the
  rest of that sentence, even when it sits in another column or another panel.
- Columns read top to bottom, then left to right, but a headline or standfirst
  spanning the page reads before the columns underneath it.
- A boxed panel or sidebar is its own self-contained run. Do not interleave it
  with the main text it sits beside; place it whole, where a reader would take
  it, and keep its own blocks together and in order.
- A subhead reads immediately before the paragraph it introduces.

Return ONLY a JSON object, no prose, no code fence:
{{"page_kind": "<article|ad|mixed|toc|other>",
  "labels": {{"<id>": "<label>", ...}},
  "order": [<id>, <id>, ...]}}
Every id in the digest must appear in "labels".
"order" lists ONLY the blocks whose label is body, heading or listing-inline --
the ones whose text goes into the corpus -- in the order they should be read.

DIGEST:
{digest}
"""


def call_llm(page, digest, overlay):
    prompt = PROMPT.format(digest=digest, overlay=overlay)
    r = subprocess.run([CLAUDE, "-p", prompt, "--output-format", "text"],
                       capture_output=True, text=True, timeout=CLAUDE_TIMEOUT)
    out = r.stdout.strip()
    # Distinguish "the model answered badly" from "the service did not answer":
    # only the first is worth retrying or investigating per page.
    for m_ in SERVICE_ERRORS:
        if m_ in out:
            raise RuntimeError(f"SERVICE UNAVAILABLE: {out[:120]}")
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
    # Drawn from the SAME image stage A measured.  thumbs_150 is uncropped, so
    # using it here put every box at the wrong place on the page the moment the
    # source became the A4-cropped master.
    im = Image.open(os.path.join(SRC_DIR, f"{page:03d}.png")).convert("RGB")
    im = im.resize((im.size[0] // 4, im.size[1] // 4), Image.BOX)
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


# A paragraph does not stop at a column break, but a block does.  The last
# paragraph of one block and the first of the next are the same paragraph whenever
# the earlier one stops mid-sentence.  MEASURED against vision transcription:
# this was the single largest source of disagreement -- "...wie Kopierprogram" and
# "me, Directory-Sorter und ähnliches" were being emitted as two paragraphs where
# a reader sees one.
SENTENCE_END = ".!?:»\"'\u201c"


def join_runons(paras):
    out = []
    for p in paras:
        if out:
            prev = out[-1].rstrip()
            head = p.lstrip()
            # continue when the previous paragraph did not finish a sentence and
            # this one does not begin like a new one
            if prev and prev[-1] not in SENTENCE_END and head[:1].islower():
                if prev.endswith("¬"):
                    out[-1] = prev + head          # word split across the break
                else:
                    out[-1] = prev + " " + head
                continue
        out.append(p)
    return out


def process(page):
    stem = f"{page:03d}"
    rec = json.load(open(os.path.join(OUT_DIR, stem + ".json"), encoding="utf-8"))
    digest = open(os.path.join(OUT_DIR, stem + ".digest.txt"), encoding="utf-8").read()
    overlay = os.path.join(OUT_DIR, stem + "_boxes.png")

    # An existing verdict is reused rather than re-asked, so changing what counts
    # as article text (captions in or out, say) is a rebuild and not 176 fresh
    # LLM calls.  Delete NNN.labels.json to force the page to be judged again.
    cached = os.path.join(OUT_DIR, stem + ".labels.json")
    verdict = None
    if os.path.exists(cached):
        old = json.load(open(cached, encoding="utf-8"))
        cand = {"page_kind": old.get("page_kind", "unknown"),
                "order": old.get("order"),
                "labels": {str(b["id"]): b["llm_label"] for b in old["blocks"]
                           if b.get("llm_label")}}
        # A cached verdict is only valid for the blocks it was made about.  If
        # stage A has since renumbered them the cache is silently wrong: it was
        # applied to a rerun whose ids had changed, most blocks fell back to the
        # geometric guess, and the corpus scored 0.822 instead of 0.917 with no
        # error anywhere.  Compare the id sets and re-ask when they differ.
        now_ids = {str(b["id"]) for b in rec["blocks"]}
        if set(cand["labels"]) == now_ids:
            verdict = cand
        else:
            print(f"p{stem}: cached labels are for different blocks, re-asking", flush=True)
    if verdict is None:
        verdict = call_llm(page, digest, overlay)
    labels = {str(k): v for k, v in verdict.get("labels", {}).items()}

    for b in rec["blocks"]:
        new = labels.get(str(b["id"]))
        b["llm_label"] = new
        # An unknown or missing label falls back to the geometric guess rather
        # than silently dropping the block from the corpus.
        b["label"] = new if new in VALID_LABELS else b["label"]
    rec["page_kind"] = verdict.get("page_kind", "unknown")
    rec["order"] = verdict.get("order")

    json.dump(rec, open(os.path.join(OUT_DIR, stem + ".labels.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    redraw(page, rec["blocks"])

    keep = [b for b in rec["blocks"] if b["label"] in ARTICLE_LABELS]
    # The LLM decides the reading order: column flow, sentences continuing across
    # a column break, a boxed panel that must stay whole rather than being woven
    # into the text beside it.  Geometry alone cannot see any of that.  The
    # geometric order remains only as a fallback, and any block the model forgot
    # is appended in geometric order rather than silently dropped.
    ordered, seen = [], set()
    by_id = {b["id"]: b for b in keep}
    for i in (rec.get("order") or []):
        try:
            bid = int(i)
        except (TypeError, ValueError):
            continue
        if bid in by_id and bid not in seen:
            seen.add(bid)
            ordered.append(by_id[bid])
    missing = [b for b in reading_order(keep) if b["id"] not in seen]
    if missing and ordered:
        print(f"p{stem}: {len(missing)} block(s) missing from LLM order, appended", flush=True)
    ordered += missing
    text = "\n".join(join_runons([b["text"].strip() for b in ordered if b["text"].strip()]))
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
