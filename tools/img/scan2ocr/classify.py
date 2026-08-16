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

import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw

OUT_DIR = "/Users/mist/DNB/8609/tmp/ocr/out"

# `claude -p` rather than the API: this box has no ANTHROPIC_API_KEY, and the CLI
# already carries the user's credentials.
CLAUDE = "claude"
# Replies that mean "the service did not answer", never "the page says this".
# Auth expiry was added after an overnight run lost pages 84-176 to "Failed to
# authenticate: OAuth session expired", which was counted as a per-page error and
# still let the evaluation run and report a number.
SERVICE_ERRORS = ("session limit", "usage limit", "rate limit",
                  "Please run /login", "Invalid API key",
                  "Failed to authenticate", "OAuth session expired",
                  "credit balance", "Overloaded")
# ...of which these SELF-HEAL and are worth waiting out.  Four concurrent
# `claude -p` processes share one credential file, and when the OAuth token comes
# up for refresh they race: the losers get an expired token.  MEASURED once --
# pages 84-176 of a run died that way at 23:17 and a plain test call succeeded
# again by 23:45 with nothing done to fix it.  A usage limit is the opposite case
# and must NOT be retried, since it resets on a clock, not on a wait.
TRANSIENT_ERRORS = ("Failed to authenticate", "OAuth session expired", "Overloaded")
RETRIES = 3
RETRY_WAIT = 45   # seconds
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
import llm                                                       # noqa: E402
from ocr_blocks import (ARTICLE_LABELS, HYPHEN_MARK,             # noqa: E402
                        PARA_INDENT_MIN_PX, SRC_DIR, reading_order)

# Every label the prompt offers must appear here.  "caption" was missing -- it is
# offered to the model and excluded from the corpus, but was not listed as valid,
# so every block the model correctly called a caption failed validation and fell
# back to its GEOMETRIC label, which is "body".  Listing instructions, figure
# captions and table titles were reinstated as article text by that silent
# fallback, and no prompt wording could fix it because the model was right and its
# answer was being discarded.
# NOTE -- do not reintroduce a "this looks like prose, so it cannot be a listing"
# veto.  It was tried and REVERTED after measuring the whole issue.
# The motive was p51, whose standing sidebar "Der Checksummer und der MSE sind
# Eingabehilfen für unsere Listings ..." stage B insists on calling a listing
# because its SUBJECT is listings; no prompt wording, including quoting the
# sidebar verbatim, moved it.  Two vetoes were tried.  Digit density failed
# immediately: a BASIC listing built from string constants carries few digits, so
# it reinstated 37 paragraphs of listing on p56.  German function-word density
# looked perfect on the pages to hand -- p56's listing blocks score 0.000 every
# one, p51's sidebar 0.276-0.333, body text 0.182-0.325, nothing in between -- and
# it fixed p51 while leaving five listing pages clean.
# Across all 176 pages it was a rout: recall 0.938 -> 0.863, precision 0.951 ->
# 0.848, and FOURTEEN pages in the listings section at the back of the magazine
# started emitting listing text again where vision sees none.  A REM-commented
# listing carries plenty of German.  One page gained, fourteen lost.
# The lesson is about method as much as about listings: a rule verified on the
# handful of pages that motivated it is not verified.

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
2. The overlay image of the same page. Every block is outlined there with its
   id printed at the top-left corner.

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
                      line, and any SHORT note physically attached to it such as
                      "Das Programm bitte mit dem MSE abtippen", "Beachten Sie
                      die Eingabehinweise auf Seite 51", "(Schluß)", or a REM
                      line quoted out of the listing body. Apparatus is a line or
                      two sitting against a listing. A boxed sidebar running to
                      several paragraphs is NOT apparatus even when its subject is
                      listings: the standing explainer "Der Checksummer und der
                      MSE sind Eingabehilfen für unsere Listings ..." is prose the
                      magazine wrote for its readers, and it is body. OCR often mangles the word
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

STRUCTURE. For every block you place in "order", also give it a role, so the
corpus can be written as markdown. The digest lists each block's measured line
height as a fraction of the page (`lineh`), which is the printed type size --
use it, together with the image, to tell the levels apart.

  title       the headline of an article starting on this page. Largest type on
              the page, usually spanning columns. A page may carry two articles
              and so two titles, and a continuation page carries none at all.
  intro       the standfirst: the bold or larger paragraph between the headline
              and the body, before the article proper begins.
  section     a standalone heading inside the article: set on its own line in
              display type, introducing a section of the piece.
  subsection  a heading a level below that -- typically a short bold run-in
              subhead opening a paragraph of body text, naming the thing the
              next paragraphs describe.
  code        a short code fragment quoted inside the prose.
  body        ordinary running prose. Use this when in doubt.

A ROLE CANNOT CHANGE IN THE MIDDLE OF A SENTENCE. Tesseract ends a block wherever
the type changes, and the magazine changes type inside a standfirst -- p39 sets
"...Der Name des Freundes:" small and "Print Shop Companion", which finishes that
sentence, large. Two blocks, one standfirst. So before assigning a role, read the
END of the previous block in your reading order: if this block's text completes
the sentence that one left unfinished, it has the SAME role, however differently
it is set. Size and weight say what a block is only when it starts something new.

A block the digest marks "BREAKS AT A GUTTER" holds two things side by side, and
the reflowed text you see for it reads ACROSS both. Sometimes that is right and
sometimes it is nonsense, and only the text can tell:

  across  the line is one statement that happens to be set in two parts -- a
          table row ("ESC chr$(108) chr$(10): setzt linken Rand auf 10",
          "0- 2048: Bildschirmspeicher"), or a listing line with its REM
          comment. Keep this unless it plainly reads wrong. It is the default.
  rows    across is right, but each LINE is a separate record and they must not
          be reflowed into one paragraph -- a table of commands, addresses or
          values.
  down    across is nonsense: two independent columns were woven together
          line by line, and the text must be read down one and then the other
          ("8910 Landsberg 2300 Kiel" is two different addresses).

Compare the "rows =" and "down =" readings printed under the block against the
across-reading on the block's own line, and put your choice in "reads". Only
gutter-marked ids may appear there; omit an id to leave it "across".

Return ONLY a JSON object, no prose, no code fence:
{{"page_kind": "<article|ad|mixed|toc|other>",
  "labels": {{"<id>": "<label>", ...}},
  "order": [<id>, <id>, ...],
  "roles": {{"<id>": "<role>", ...}},
  "reads": {{"<id>": "<across|rows|down>", ...}}}}
Every id in the digest must appear in "labels".
"order" lists ONLY the blocks whose label is body, heading or listing-inline --
the ones whose text goes into the corpus -- in the order they should be read.

"""


# Identifies the question a cached verdict answered.  See process().
PROMPT_KEY = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()[:16]


def call_llm(page, digest, overlay):
    # The instructions are the cache prefix and identical on every page; the
    # digest and the overlay image are the per-page payload.
    try:
        out = llm.call(PROMPT, "DIGEST:\n" + digest, image_path=overlay)
    except llm.ServiceUnavailable as e:
        raise RuntimeError(f"SERVICE UNAVAILABLE: {e}")
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
SENTENCE_END = ".!?:»\"'\u201c\u00ab"

# German function words. A paragraph CANNOT end on one of these -- "...zwischen
# dem zwölften und dreizehnten Bit. Die" is not a paragraph, it is the first half
# of one, whatever the punctuation and whatever case the continuation starts in.
# MEASURED: this is the narrow, trivially-decidable class. Joining on "does not
# end with a full stop" instead is far broader and over-joins -- it cost recall
# 0.934 -> 0.908 across the issue for 0.007 precision -- because a list item, a
# byline or a heading legitimately ends without one.
DANGLING_WORDS = frozenset("""
der die das den dem des ein eine einen einem einer eines und oder aber
mit von zu zum zur im in am an auf aus bei nach vor über unter durch für ohne
ist sind war waren wird werden kann können muss müssen soll sollen hat haben
sich nicht auch noch nur wenn dass daß als wie so es er sie man
dieser diese dieses jeder jede jedes
""".split())


def join_text(prev, nxt):
    """Join two pieces of one paragraph that the printed page broke apart.

    A trailing hyphen at a COLUMN or PAGE break is the same physical fact as one
    at a line break, so it is marked the same way and left for the hyphen pass
    to resolve.  MEASURED: p8's "Jack Tramiel ver-" / "folgte in Amerika" came
    out as "ver- folgte", because reflow() only sees the lines INSIDE a block
    and this break was between two blocks.  145 such joins across the issue --
    most of them genuine suspended hyphens ("Informations- und", "Fach- und")
    that must keep the hyphen, the rest soft ones ("Pro- gramme", "vor- handen")
    that must lose it.  Nothing local tells the two apart; the marker does."""
    prev, nxt = prev.rstrip(), nxt.lstrip()
    if prev.endswith(HYPHEN_MARK):
        return prev + nxt
    if prev.endswith("-"):
        return prev[:-1] + HYPHEN_MARK + nxt
    return prev + " " + nxt


def ends_dangling(text):
    """Does this paragraph end on a word that cannot end a sentence?"""
    text = text.rstrip()
    if not text or text[-1] in SENTENCE_END:
        return False
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", text)
    return bool(words) and words[-1].lower() in DANGLING_WORDS

# How each role is written as markdown.  A standfirst becomes a blockquote: not
# strictly a quotation, but it renders closest to the printed page and can be
# turned into something else later.
ROLE_PREFIX = {"title": "# ", "intro": "> ", "section": "## ", "subsection": "### "}
# "row" is a body paragraph that is one RECORD of a table: it renders exactly
# like body, but join_runons only ever joins body to body, so a table's rows can
# never be reflowed back into one paragraph.
VALID_ROLES = set(ROLE_PREFIX) | {"body", "code", "source", "row"}

# Source notes -- "Info: Broderbund Software, 17 Paul Drive, ...", publisher
# addresses, ISBN and price credits, "Fortsetzung von Seite 32" -- are set in a
# smaller face than the body, usually at the end of an article. Markdown has no
# way to say that, so they are emitted as an HTML block, which markdown passes
# through untouched.
# MEASURED over the issue, against each page's own median body line height:
# every block below 0.85x is one of these (46 of 969), with the "Info:" lines
# clustering at 0.66-0.67; the 0.85-0.95 band is ordinary body, including
# 26- and 28-line body blocks on p145. The ratio is per page because type size
# varies between pages, and taken from the median so one odd block cannot move it.
SOURCE_LINE_RATIO = 0.85
SOURCE_MIN_BODY_BLOCKS = 2      # too few to take a median from
SOURCE_HTML = '<p class="source">%s</p>'
# Consecutive source notes are ONE note the page set as several blocks: p10's
# vendor list arrives as ten lines ("MVG: Moderne Verlagsgesellschaft," /
# "Justus-von-Liebig-Str. 1," / "8910 Landsberg 2300 Kiel" ...), p146's as
# twenty-one.  They become one <p class="source"> with the line breaks kept as
# <br>, because the line breaks are the address's structure, not typesetting.
SOURCE_JOIN = "<br>\n"


def join_runons(paras):
    """paras is a list of (role, text, starts_block, indent).  Only ordinary prose
    is ever joined: a heading must never be absorbed into the paragraph before
    it, however the sentence happens to end.

    Returns the same shape it was given, keeping each surviving paragraph's own
    indent.  Stage D needs it: whether a paragraph continues the one before is
    decided by ITS first-line indent, and after a continuation splice the
    paragraph being joined is not the first one on its page."""
    out = []
    for role, p, starts_block, indent in paras:
        # A paragraph running over the foot of one column into the next is the
        # normal case, and its continuation is NOT indented.  So the first
        # paragraph of a block joins the previous one when it is flush, and
        # stands alone when it is indented -- the page states which it is.
        if (out and starts_block and role == "body" and out[-1][0] == "body"
                and (indent < PARA_INDENT_MIN_PX
                     or ends_dangling(out[-1][1]))):
            out[-1] = (role, join_text(out[-1][1], p), out[-1][2], out[-1][3])
            continue
        # A standfirst is never printed twice in a row, so two consecutive ones
        # are always one that OCR split.  Unconditional, unlike the heading rule
        # below, because a standfirst legitimately ends on a full stop.
        if out and role == "intro" and out[-1][0] == "intro":
            out[-1] = (role, join_text(out[-1][1], p), out[-1][2], out[-1][3])
            continue
        # A headline set over two lines arrives as two blocks, and rendering them
        # separately produces two "# " lines where a reader sees one headline --
        # MEASURED on p76: "# Module" / "# für Hypra-Basic" against vision's
        # "# Module für Hypra-Basic".  Consecutive blocks sharing a heading role
        # are joined when the first does not finish a sentence.  Body is excluded
        # here and handled below, so a heading is still never absorbed into the
        # paragraph before it.
        if out and role in ROLE_PREFIX and out[-1][0] == role:
            prev = out[-1][1].rstrip()
            if prev and prev[-1] not in SENTENCE_END:
                out[-1] = (role, join_text(prev, p), out[-1][2], out[-1][3])
                continue
        if out and role == "body" and out[-1][0] == "body":
            prev = out[-1][1].rstrip()
            head = p.lstrip()
            # Inside a block the splits come from indent, leading and boldness,
            # and those are reliable -- a list item or a run-in subhead legitimately
            # ends without a full stop, so missing punctuation must NOT rejoin them.
            # Applied unconditionally it cost recall 0.934 -> 0.908 across the issue
            # while gaining only 0.007 precision. The unfinished-sentence test now
            # lives at the block boundary above, where the ambiguity actually is.
            if prev and prev[-1] not in SENTENCE_END and head[:1].islower():
                out[-1] = (role, join_text(prev, head),      # word split across the break
                              out[-1][2], out[-1][3])
                continue
        out.append((role, p, starts_block, indent))
    return out


def render(paras):
    """(role, text, ...) tuples -> markdown.  Paragraphs separated by a blank line."""
    chunks, source = [], []

    def flush():
        if source:
            chunks.append(SOURCE_HTML % SOURCE_JOIN.join(source))
            source.clear()

    for para in paras:
        role, text = para[0], para[1]
        text = text.strip()
        if not text:
            continue
        if role == "source":
            source.append(text)
            continue
        flush()
        if role == "code":
            chunks.append("```\n" + text + "\n```")
        else:
            chunks.append(ROLE_PREFIX.get(role, "") + text)
    flush()
    return "\n\n".join(chunks)


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
                "roles": old.get("roles"),
                "reads": old.get("reads"),
                "labels": {str(b["id"]): b["llm_label"] for b in old["blocks"]
                           if b.get("llm_label")}}
        # A cached verdict is only valid for the blocks it was made about.  If
        # stage A has since renumbered them the cache is silently wrong: it was
        # applied to a rerun whose ids had changed, most blocks fell back to the
        # geometric guess, and the corpus scored 0.822 instead of 0.917 with no
        # error anywhere.  Compare the id sets and re-ask when they differ.
        now_ids = {str(b["id"]) for b in rec["blocks"]}
        # A cached verdict is only valid for the blocks it was made about AND
        # for the question it was asked.  Keying on the blocks alone means every
        # prompt improvement is silently discarded -- the answers keep coming
        # from the cache and the sweep looks like the rule did nothing.  Same
        # lesson as the stale block-id cache in FINDINGS; the fix is the same
        # shape as stage D's boundary cache.
        if set(cand["labels"]) != now_ids:
            print(f"p{stem}: cached labels are for different blocks, re-asking", flush=True)
        elif old.get("prompt_key") != PROMPT_KEY:
            print(f"p{stem}: cached verdict answers an older prompt, re-asking", flush=True)
        else:
            verdict = cand
    if verdict is None:
        verdict = call_llm(page, digest, overlay)
    labels = {str(k): v for k, v in verdict.get("labels", {}).items()}

    for b in rec["blocks"]:
        new = labels.get(str(b["id"]))
        b["llm_label"] = new
        # ...and only when stage A's own listing test also says no.  Without that
        # condition the veto reinstated real listing bodies: a BASIC listing full
        # of string constants can fall under the digit threshold, and p56 went
        # from emitting nothing to emitting 37 paragraphs of listing.
        # An unknown or missing label falls back to the geometric guess rather
        # than silently dropping the block from the corpus.
        b["label"] = new if new in VALID_LABELS else b["label"]
    rec["page_kind"] = verdict.get("page_kind", "unknown")
    rec["order"] = verdict.get("order")
    rec["roles"] = verdict.get("roles")
    rec["reads"] = verdict.get("reads")
    rec["prompt_key"] = PROMPT_KEY

    json.dump(rec, open(os.path.join(OUT_DIR, stem + ".labels.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    redraw(page, rec["blocks"])

    paras = page_paragraphs(rec, stem)
    text = render(join_runons(paras))
    art = os.path.join(OUT_DIR, stem + ".article.txt")
    open(art, "w", encoding="utf-8").write(text + ("\n" if text else ""))

    kept = sum(1 for b in rec["blocks"] if b["label"] in ARTICLE_LABELS)
    print(f"p{stem}: kind={rec['page_kind']:<8} kept {kept}/{len(rec['blocks'])} blocks, "
          f"{len(text)} chars", flush=True)


def page_paragraphs(rec, stem=""):
    """One page's classified blocks -> the paragraph list join_runons expects:
    (role, text, starts_block, first_indent_px).

    Stage D reassembles articles out of these across page boundaries, which is
    why the build lives in its own function: defined twice, the per-page corpus
    and the per-article one would eventually disagree."""
    keep = [b for b in rec["blocks"] if b["label"] in ARTICLE_LABELS]
    # The LLM decides the reading order: column flow, sentences continuing across
    # a column break, a boxed panel that must stay whole rather than being woven
    # into the text beside it.  Geometry alone cannot see any of that.  The
    # geometric order remains only as a fallback, and any block the model forgot
    # is appended in geometric order rather than silently dropped.
    # A page's own body type size, to judge the source notes against.
    body_heights = [b["line_h_frac"] for b in rec["blocks"]
                    if b["label"] == "body" and b["n_lines"] >= 3]
    body_median = (statistics.median(body_heights)
                   if len(body_heights) >= SOURCE_MIN_BODY_BLOCKS else 0)

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
    roles = {str(k): v for k, v in (rec.get("roles") or {}).items()}
    reads = {str(k): v for k, v in (rec.get("reads") or {}).items()}
    paras = []
    for b in ordered:
        role = roles.get(str(b["id"]), "body")
        if role not in VALID_ROLES:
            role = "body"
        # A block that breaks at an internal gutter holds two things side by
        # side and stage A offered the alternatives; stage B picked one.  The
        # default is the across-reading already in b["text"], so a block the
        # model says nothing about is untouched.
        alt = b.get("read_alt") or {}
        pick = reads.get(str(b["id"]))
        if alt and pick in ("rows", "down") and alt.get(pick):
            b = dict(b, text=alt[pick], para_subhead=[])
            if pick == "rows" and role == "body":
                role = "row"
        if b["label"] == "listing-inline":
            role = "code"                     # the label already settled this
        indent = b.get("first_indent_px", 0)
        if (role == "body" and body_median
                and b["line_h_frac"] < SOURCE_LINE_RATIO * body_median):
            role = "source"
        if role == "code":
            paras.append((role, b["text"].strip(), True, indent))
        else:
            # a block may hold several paragraphs; the role applies to each,
            # except paragraphs stage A measured as bold subheads -- those are
            # headings inside a body block, which a per-block role cannot express
            subhead = b.get("para_subhead") or []
            for i, para in enumerate(b["text"].split("\n")):
                if not para.strip():
                    continue
                starts_block = (i == 0)
                if role == "body" and i < len(subhead) and subhead[i]:
                    # A bold run-in subhead sits a level BELOW a standalone
                    # section heading: "Tips für Maschinenprogrammierer" is set
                    # on its own line above a section, while "Ursprungsblock" and
                    # "Zielblock" open a paragraph inside one.
                    paras.append(("subsection", para, starts_block, indent))
                else:
                    paras.append((role, para, starts_block, indent))
    return paras


def safe(page):
    try:
        process(page)
    except Exception as e:                      # one bad page must not stop 176
        print(f"p{page:03d}: FAILED {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    pages = [int(a) for a in sys.argv[1:]]
    with ThreadPoolExecutor(max_workers=LANES) as ex:
        list(ex.map(safe, pages))
