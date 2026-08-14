#!/usr/bin/env python3
"""
Stage A of the article-corpus pipeline.

thumbs_600/NNN.png
   -> 300 dpi greyscale
   -> tesseract TSV (+ an inverted pass over the header band, for reversed-out
      section bars that tesseract reads only intermittently)
   -> per-block bbox + cleaned text + deterministic features
   -> out/NNN.json        blocks, features, heuristic label   (the durable artefact)
   -> out/NNN.digest.txt  compact per-page brief for the stage-B LLM pass
   -> out/NNN_boxes.png   overlay, colour = heuristic label

The FINAL deliverable is stage C: out/NNN.article.txt containing article text and
nothing else -- no running heads, no folios, no ads, no Kleinanzeigen, no
standalone type-in listings, no facing-page slivers.  Empty file where the page
carries no article.

Nothing here is a final decision.  This stage produces the *evidence*: geometry,
cleaned text, and cheap deterministic features.  The heuristic label is a first
guess, used for the overlay and to spare the LLM the cases that geometry already
settles.  Stage B may override any block.
"""

import json
import os
import re
import statistics
import subprocess
import sys
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageOps

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

SRC_DIR = "/Users/mist/DNB/8609/thumbs_600"
OUT_DIR = "/Users/mist/DNB/8609/tmp/ocr/out"

# thumbs_600 is ~600 dpi (5197x7188 for an A4-ish uncropped sheet).  Tesseract's
# sweet spot is 300 dpi: below that small ad/Kleinanzeigen type falls apart,
# above it the engine gains nothing and the halftone screen starts aliasing into
# the binarizer.  Exactly 0.5 keeps the resample a clean box filter.
SRC_DPI = 600
OCR_DPI = 300
SCALE = OCR_DPI / SRC_DPI

# Overlay is drawn at thumb resolution so it can be eyeballed next to thumbs_150.
OVERLAY_DPI = 150

TESS_LANG = "deu"
# psm 1 = automatic page segmentation *with* OSD.  The magazine is 2-3 column
# with rules and boxed figures; psm 3 (no OSD) merges columns across rules on
# some pages.  OSD is cheap here because pages are already deskewed.
TESS_PSM = "1"
# psm 7 ("single text line") for the reversed-out section bar: it is exactly one
# short line, and page segmentation on a strip that thin finds nothing.
TESS_PSM_BAND = "7"
# psm 6 ("uniform block of text") for rescued crops: layout analysis is exactly
# what failed on them, so it must not be run again.
TESS_PSM_RESCUE = "6"

# --- reversed-out section bar ------------------------------------------------
# The section name sits in white type on a solid black rule.  Inverting the whole
# header band does not work: it turns the paper dark and tesseract then reads
# nothing (measured -- p8's "Aktuelles" stayed missing).  The bar has to be found
# first and cropped tight, so that after inversion it is black type on white.
BAR_DARK_LEVEL = 100     # 0-255; below this a pixel counts as bar ink
# A bar row is one containing an UNBROKEN dark run this wide -- not one that is
# merely dark on average.  MEASURED: p8's "Aktuelles" bar spans only ~13% of the
# page width, so an average-darkness test at any useful threshold missed it,
# while a run-length test finds it and still rejects rows of body text, which
# have no unbroken dark run wider than a letter.
BAR_MIN_W_FRAC = 0.06
# ...and it must be ONE TEXT LINE tall.  MEASURED at 300 dpi (page H = 3594 px):
# the section bar is ~52 px (0.0145), the sheet-edge shadow along the top trim is
# 11-15 px (0.004), the hairline rule under the header is ~8 px (0.002), and a
# full-bleed ad background fills the rest of the band (>0.030).  Without this
# window the widest dark run wins and that is always the edge shadow.
BAR_MIN_H_FRAC = 0.008
BAR_MAX_H_FRAC = 0.025
# The bar's own white letters break every horizontal dark run, so on the raw mask
# only its top and bottom edges register (MEASURED p8: unbroken runs of 330 px at
# rows 137-145 and 194-214, but only 27-125 px through the lettering between).
# A horizontal closing of this width bridges the letters and makes the bar solid.
# Widest inter-letter gap seen is a word space at ~20 px, so 41 px is ample.
BAR_CLOSE_PX = 41
# Closing also bridges the word spaces of ordinary body text, so a fill test
# separates them: inside its own box a reversed bar is ~55-85% ink, a line of
# body type ~15%.
BAR_FILL_FRAC = 0.45
BAR_PAD = 6              # px of white margin added around the crop before OCR
# Bar-pass words are given block ids from here up, so they never merge into a
# block from the main pass and can be recognised later.
BAR_BLOCK_ID = 1000
# The bar crop is already known to BE a bar from its geometry, so tesseract's
# confidence carries no information here and must not gate the result.  MEASURED:
# p61's bar read "_Fehlerteufelchen" -- the correct section name -- at conf 21.5,
# because psm 7 on a small inverted crop always scores low.  A conf floor of
# either 60 or 40 discarded it and lost the section name on an errata page.  The
# only thing worth rejecting is grit off the crop edge, so the test is lexical.
BAR_MIN_LETTERS = 3

# --- coverage rescue ---------------------------------------------------------
# Tesseract's page layout analysis silently DISCARDS text panels printed on a
# screened tint: it decides the panel is a picture and never OCRs it.  MEASURED
# on p51, whose boxed "Checksummer und MSE" sidebar -- editorial text the corpus
# must contain -- produced 0 characters under psm 3 and psm 4, while psm 6 on the
# very same crop produced 1214.  Nothing downstream can recover from that, because
# the text never enters the pipeline at all.
#
# So after the main pass the page is checked for ink that NO block covers, and
# every such region is re-OCR'd on its own with psm 6 and its contrast stretched.
# A cell counts as text-like by its standard deviation: type has high local
# variance (~25-80), blank paper (~5) and a flat tint (~8) do not.  Photos do
# exceed it and get re-OCR'd for nothing; they come back as low-confidence
# gibberish and are labelled "noise", which is the correct outcome anyway.
RESCUE_CELL = 32          # px at 300 dpi (~2.7 mm) -- about one x-height
RESCUE_STD = 25.0         # per-cell std above which a cell holds type
RESCUE_MIN_CELLS = 12     # ignore specks; a real missed panel is far bigger
RESCUE_PAD = 8            # px of margin around a rescued crop
RESCUE_BLOCK_ID = 2000    # rescued words get block ids from here up
# Uncovered text-like cells are not islands: column rules, box borders, photo
# edges and the gutters just outside each block's bbox link them into one web
# that spans the sheet.  MEASURED on the first attempt: the flood fill returned a
# single component covering x 0.09-0.94, y 0.04-0.91 of p51 and psm 6 over that
# whole crop still missed the sidebar.  Three guards break the web:
#   * a cell must have at least this many text-like neighbours, which deletes
#     one-cell-thick rules and borders (a rule cell has only 2) while leaving the
#     interior of any real text panel untouched;
#   * the covered mask is grown by one cell, so the gutter hugging each block
#     stops acting as a bridge;
#   * a component must FILL its own bounding box, which a compact panel does and
#     a leaked web never does.
RESCUE_MIN_NEIGHBOURS = 3
RESCUE_COVER_GROW = 1     # cells
RESCUE_MIN_DENSITY = 0.40
# psm 6 treats its crop as ONE uniform block, so a rescued region spanning two
# columns comes back with the columns interleaved line by line (MEASURED on p51:
# "schalten. abläufe festgelegt. Ganz nach / Ihren Vorstellungen." -- the sidebar
# and the facing ad caption woven together).  Layout analysis cannot be used to
# separate them, since it is what failed on this region in the first place, so
# the crop is cut at its own whitespace gutters and each strip is OCR'd alone.
RESCUE_GUTTER_MIN_PX = 24   # ~2 mm at 300 dpi; narrower than any column gutter
# MEASURED on p51's rescued region (1840x1360): the gutter between the sidebar and
# the facing ad is not clean.  Scan speckle and the two boxes' drop shadows leave
# ink in it, so its longest run scores 22 px at a 2% tolerance -- just under the
# 24 px minimum -- and 34 px at 5%.  Ink per column in that region runs 0.20-0.87
# wherever there is actually type, so 5% clears the dirt while staying four times
# below the lightest real column.
RESCUE_GUTTER_INK = 0.05    # column ink fraction below which it is white space
RESCUE_STRIP_MIN_PX = 120   # ignore slivers left over by the cut
RESCUE_CUT_DEPTH = 6        # recursion limit for the XY-cut

# A word below this confidence is the binarizer hallucinating letters out of a
# halftone photo or a screened tint.  Blocks made mostly of such words are kept
# but labelled "noise" -- deleting them would make a photo look like blank paper,
# and stage B benefits from knowing a photo is there.
MIN_BLOCK_CONF = 55.0

# Blocks smaller than this are OCR grit, not content.
MIN_BLOCK_WORDS = 2
MIN_BLOCK_AREA_FRAC = 0.00015

# --- neighbour-page sliver ---------------------------------------------------
# thumbs_600 is NOT cropped to the A4 window: most sheets carry a vertical strip
# of the facing page at one edge (p5 left, p58/p61 right).  Its text is real
# text, so confidence alone will not reject it -- geometry must.  A sliver block
# is narrow AND hard against an outer edge.  Both conditions, never one alone: a
# genuine narrow sidebar sits inboard, a genuine wide block touching the edge is
# a bleed image.  MEASURED on p58/p61: slivers land at x >= 0.99, conf 3.8-40.
SLIVER_EDGE_FRAC = 0.055   # within this fraction of page width of either edge
SLIVER_MAX_W_FRAC = 0.075  # and no wider than this fraction of page width

# --- running header / footer -------------------------------------------------
# The single strongest signal in the magazine: every editorial page carries a
# section header at the top ("Anwendung des Monats", "Grafik", "Software", plus a
# machine tag "C 64" / "C 16, Plus/4") and "Ausgabe 9/September 1986" plus the
# folio at the foot.  Ads carry neither -- that is what identifies p45 as a
# full-page ad with no other evidence available.
HEADER_BAND = 0.075   # top fraction of the page
# MEASURED: p58's folio block "58 64'er" starts at y=0.94, so 0.945 let it through
# and it was then mislabelled a listing (its "58 Zar" OCR matches the BASIC line
# pattern).  0.93 is below the last body line on every test page.
FOOTER_BAND = 0.93
FOOTER_RE = re.compile(r"Ausgabe\s*9\s*/\s*September\s*1986|64.er", re.I)

# --- listing detection (geometric + lexical, never semantic) -----------------
# BASIC type-in listings are monospace, unjustified and line-numbered; hex dumps
# are runs of 2-digit hex.  Decided by regex and by digit density, because a
# regex cannot hallucinate and an LLM can.
BASIC_LINE_RE = re.compile(r'^\s*\d{1,5}\s+[A-Z"\'?]')
HEX_LINE_RE = re.compile(r"(\b[0-9A-Fa-f]{2}\b[ ,]+){6,}")
# MEASURED on p58's hex dump: digit_frac 0.50 / 0.63, against 0.00-0.10 for every
# body block on all 7 test pages.  No overlap at all -- digit density is the
# cleanest single separator found, and far more robust than hex_line_frac, which
# only reached 0.36 on the same blocks because OCR mangles some rows.
LISTING_DIGIT_FRAC = 0.30
LISTING_MIN_LINES = 6
# Second route, for screen-dump listings whose OCR is poor (p55: conf 31 and 56):
# monospaced, line-numbered, and low confidence together.
LISTING_LOWCONF = 70.0
LISTING_BASIC_FRAC = 0.18
# ...and the original route for clean line-numbered listings.
LISTING_LINE_FRAC = 0.45
# A listing this tall (fraction of page height) is a standalone type-in and is
# NOT article text; anything shorter is an inline code snippet and IS.
LISTING_STANDALONE_H_FRAC = 0.18
# Adjacent listing blocks are one listing: p58's hex dump came back as three
# column blocks plus a garbage strip.  Merge when the gap is under this fraction
# of page width/height, then re-decide standalone-vs-inline on the merged box.
LISTING_MERGE_GAP_FRAC = 0.03

# --- Kleinanzeigen -----------------------------------------------------------
# Classified ads: many tiny blocks, small x-height, dense with prices, phone
# numbers and postal codes.
KLEIN_RE = re.compile(r"\bTel\.?\b|\bDM\b|\bVB\b|\bZuschr\b|\b\d{4}\s+[A-ZÄÖÜ][a-zäöüß]+", re.I)
KLEIN_HIT_PER_LINE = 0.35
KLEIN_MAX_LINE_H_FRAC = 0.0075  # x-height ceiling, fraction of page height

# --- heading -----------------------------------------------------------------
HEADING_MAX_LINES = 3
HEADING_MIN_H_FRAC = 0.014      # line height well above body text

CAPTION_RE = re.compile(r"^\s*(Bild|Tabelle|Listing)\b", re.I)
# A listing that carries its own "Listing ..." caption is a standalone type-in,
# however few of its lines OCR recovered.  MEASURED on p55: the boxed
# »EAN-Barcodes« listing came back as only 8 readable lines (h_frac 0.09) and the
# height rule alone let it through as an inline snippet.  Caption adjacency
# settles it; genuine inline snippets are never captioned.
LISTING_CAPTION_RE = re.compile(r"^\s*Listing\b", re.I)
LISTING_CAPTION_GAP_FRAC = 0.04   # caption within this fraction of page height

# --- drop cap ----------------------------------------------------------------
# Every feature article opens with a drop cap spanning ~3 lines.  Tesseract emits
# it as its own word, and because it is tall its top sits above the line it was
# grouped with -- which is why sorting lines by MINIMUM word top scrambled p58's
# opening paragraph.  Lines are therefore sorted by MEDIAN word top, and the cap
# is spliced back onto the first word of the first line ("M" + "it" -> "Mit").
DROPCAP_H_RATIO = 2.2   # taller than this multiple of the median line height
# MEASURED on p58: the cap came back as "M--", because the inverted rule beside
# it feeds two dashes into the same word.  A two-character limit rejected it and
# the paragraph kept opening "it »Shrinksprite«" with a stray "M--" on line two.
DROPCAP_MAX_CHARS = 4   # OCR attaches grit from the rule beside the cap

# --- paragraphs --------------------------------------------------------------
# The corpus wants one line per PARAGRAPH, not one line per printed line, so the
# printed line breaks have to be undone.  Tesseract cannot do this: it has no
# de-hyphenation option, and its own paragraph numbering is not trustworthy here
# -- MEASURED, it called p58's 11-line block one paragraph and p55's 26-line
# block one paragraph, though both plainly contain several.
#
# The first-line indent is trustworthy.  MEASURED at 300 dpi against each block's
# median line start: continuation lines sit at 0 +/- 2 px and paragraph openings
# at +31 to +35.  The gap is more than tenfold, so the split is unambiguous.
PARA_INDENT_MIN_PX = 15
# ...but lines running beside a drop cap are pushed right by the cap itself, and
# measured +121 px on p58.  They continue the opening paragraph rather than
# starting new ones, so anything indented past this ceiling is not a new
# paragraph.
PARA_INDENT_MAX_PX = 60

# --- line-break hyphens ------------------------------------------------------
# A hyphen at a line end is MARKED, not resolved -- see reflow() for why no local
# rule can separate a soft hyphen from a compound from a suspended one.  U+00AC
# is the traditional German typesetting marker for exactly this; it is visible,
# so a reviewer and a later LLM pass can both see it, and it occurs nowhere in
# the magazine's own text, so it can never be mistaken for content.  A hyphen
# inside a printed line stays a plain "-", which is what makes the two tellable
# apart at all.
HYPHEN_MARK = "¬"

# Labels whose text belongs in the article corpus.  Stage C writes exactly these.
# Captions are excluded by the user's decision; errata columns count as article.
ARTICLE_LABELS = {"heading", "body", "listing-inline"}

# Column assignment for reading order.  The magazine's columns are ~0.21 of the
# page wide with ~0.02 gutters, so 0.06 groups a column without swallowing its
# neighbour.
COLUMN_TOL = 0.06

# Overlay colours per heuristic label.
COLOURS = {
    "body": (0, 170, 0),
    "heading": (0, 90, 255),
    "caption": (0, 200, 200),
    "listing-inline": (255, 140, 0),
    "listing-standalone": (255, 0, 200),
    "kleinanzeige": (150, 0, 255),
    "header": (255, 220, 0),
    "footer": (255, 220, 0),
    "sliver": (120, 120, 120),
    "noise": (200, 200, 200),
}


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def _tess(img, base, psm, formats):
    img.save(base + "_work.png")
    subprocess.run(
        ["tesseract", base + "_work.png", base, "-l", TESS_LANG, "--psm", psm,
         "--dpi", str(OCR_DPI)] + formats,
        check=True, capture_output=True,
    )
    out = {f: open(base + "." + f, encoding="utf-8").read() for f in formats}
    os.remove(base + "_work.png")
    for f in formats:
        os.remove(base + "." + f)
    return out


def find_bar(im, W, H):
    """Locate the solid black section rule in the header band, if present.
    Returns (x0, y0, x1, y1) in page pixels or None."""
    band_h = int(H * HEADER_BAND)
    a = np.asarray(im.crop((0, 0, W, band_h)))
    dark = (a < BAR_DARK_LEVEL).astype(np.int32)

    def win_sum(m, k):
        cs = np.cumsum(np.pad(m, ((0, 0), (1, 0))), axis=1)
        return cs[:, k:] - cs[:, :-k]

    # horizontal closing: dilate by BAR_CLOSE_PX, then erode by the same, so the
    # gaps between the bar's reversed letters fill in and the bar reads solid
    k = BAR_CLOSE_PX
    dil = np.pad((win_sum(dark, k) > 0).astype(np.int32), ((0, 0), (k - 1, 0)))
    closed = (win_sum(dil, k) == k).astype(np.int32)

    run = int(BAR_MIN_W_FRAC * W)
    # a window of `run` consecutive pixels is all-dark iff its sum equals `run`
    rows = np.where((win_sum(closed, run) == run).any(axis=1))[0]
    if rows.size == 0:
        return None
    # Every sheet carries a grey register/clamp artefact hard against the top
    # edge, and it is dark enough to pass the run test.  Taking min..max of all
    # qualifying rows therefore spanned artefact AND bar, and the column test
    # over that tall range then averaged to nothing (p8, p61 -> no bar at all;
    # p58, p55 -> a crop too tall for psm 7 to read).  Contiguous row runs are
    # grouped and the widest single run wins.
    breaks = np.where(np.diff(rows) > 1)[0]
    best = None
    for grp in np.split(rows, breaks + 1):
        gy0, gy1 = int(grp.min()), int(grp.max()) + 1
        if not (BAR_MIN_H_FRAC * H <= (gy1 - gy0) <= BAR_MAX_H_FRAC * H):
            continue
        cols = np.where(closed[gy0:gy1].mean(axis=0) >= 0.5)[0]
        if cols.size == 0:
            continue
        # Split into contiguous column runs and score each on its own.  The bar
        # and the plain machine tag ("C 64", far right) share a row band, and
        # taking their combined x-extent averaged the white gutter between them
        # into the fill test -- p58's "Grafik" bar measured 0.235 that way and
        # was rejected, where the bar alone is well over the threshold.
        for cg in np.split(cols, np.where(np.diff(cols) > 1)[0] + 1):
            gx0, gx1 = int(cg.min()), int(cg.max()) + 1
            if (gx1 - gx0) < run:
                continue
            if dark[gy0:gy1, gx0:gx1].mean() < BAR_FILL_FRAC:
                continue
            if best is None or (gx1 - gx0) > (best[2] - best[0]):
                best = (gx0, gy0, gx1, gy1)
    return best


def run_tesseract(png, stem):
    """600 dpi png -> 300 dpi greyscale -> full-page TSV + txt, plus a tight
    inverted pass over the reversed-out section bar.
    Returns (tsv, txt, bar_tsv, bar_origin, greyscale_image, W, H)."""
    im = Image.open(png).convert("L")
    im = im.resize((round(im.size[0] * SCALE), round(im.size[1] * SCALE)), Image.BOX)
    W, H = im.size

    base = os.path.join(OUT_DIR, stem + "_tess")
    full = _tess(im, base, TESS_PSM, ["tsv", "txt"])

    # Tesseract read p55's "Anwendung des Monats" straight off the black bar at
    # conf 96 but missed p8's "Aktuelles" entirely, so the bar is OCR'd a second
    # time, cropped tight and inverted, and the two results are unioned.
    bar_tsv, origin = None, (0, 0)
    bar = find_bar(im, W, H)
    if bar:
        bx0, by0, bx1, by1 = bar
        crop = ImageOps.invert(im.crop(bar))
        padded = Image.new("L", (crop.size[0] + 2 * BAR_PAD, crop.size[1] + 2 * BAR_PAD), 255)
        padded.paste(crop, (BAR_PAD, BAR_PAD))
        bar_tsv = _tess(padded, base + "_bar", TESS_PSM_BAND, ["tsv"])["tsv"]
        origin = (bx0 - BAR_PAD, by0 - BAR_PAD)
    return full["tsv"], full["txt"], bar_tsv, origin, im, W, H


def _gaps(profile):
    """Runs of white in a 1-D ink profile, as [(start, end), ...]."""
    out, run = [], 0
    for i, w in enumerate(profile < RESCUE_GUTTER_INK):
        if w:
            run += 1
        else:
            if run >= RESCUE_GUTTER_MIN_PX:
                out.append((i - run, i))
            run = 0
    if run >= RESCUE_GUTTER_MIN_PX:
        out.append((len(profile) - run, len(profile)))
    return out


def _pieces(gaps, n):
    """Invert a gap list into the content spans between the gaps."""
    out, prev = [], 0
    for g0, g1 in gaps:
        if g0 - prev >= RESCUE_STRIP_MIN_PX:
            out.append((prev, g0))
        prev = g1
    if n - prev >= RESCUE_STRIP_MIN_PX:
        out.append((prev, n))
    return out


def xy_cut(a, x0=0, y0=0, depth=0):
    """Recursive XY-cut of a rescued region into single-column rectangles.

    A single vertical cut is not enough: a gutter is usually clean only over PART
    of a region's height.  MEASURED on p51 -- the same gutter that cuts cleanly
    across a 1258 px-tall crop has no gap at all across the 1360 px-tall region
    the flood fill actually produced, because the facing ad's artwork crosses it
    near the bottom.  Cutting on rows first isolates that band, and the gutter
    then appears in the bands above it.  Returns page-space rectangles."""
    ink_thr = np.percentile(a, 90) - 50
    ink = a < ink_thr
    h, w = a.shape

    if depth < RESCUE_CUT_DEPTH:
        for vertical in (True, False):         # column gutters first, then rows
            prof = ink.mean(axis=0) if vertical else ink.mean(axis=1)
            spans = _pieces(_gaps(prof), len(prof))
            if len(spans) > 1:
                out = []
                for s0, s1 in spans:
                    sub = a[:, s0:s1] if vertical else a[s0:s1, :]
                    dx, dy = (s0, 0) if vertical else (0, s0)
                    out += xy_cut(sub, x0 + dx, y0 + dy, depth + 1)
                return out
    return [(x0, y0, x0 + w, y0 + h)]


def rescue_uncovered(im, blocks, stem, W, H):
    """Find text-like ink that no block covers, re-OCR each region on its own,
    and return the extra words.  See RESCUE_* above for why this exists."""
    c = RESCUE_CELL
    gh, gw = H // c, W // c
    a = np.asarray(im, dtype=np.float32)[:gh * c, :gw * c]
    cells = a.reshape(gh, c, gw, c).swapaxes(1, 2)
    texty = cells.std(axis=(2, 3)) > RESCUE_STD

    # thin rules and borders are text-like by variance but have few text-like
    # neighbours; dropping them stops them bridging unrelated regions
    pad = np.pad(texty.astype(np.int32), 1)
    nb = sum(pad[1 + dy:1 + dy + gh, 1 + dx:1 + dx + gw]
             for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    texty &= nb >= RESCUE_MIN_NEIGHBOURS

    g = RESCUE_COVER_GROW
    for b in blocks:                                   # mask off what we have
        x0, y0, x1, y1 = b["bbox"]
        texty[max(0, y0 // c - g):(y1 // c) + 1 + g, max(0, x0 // c - g):(x1 // c) + 1 + g] = False

    seen = np.zeros_like(texty)
    words = []
    nid = RESCUE_BLOCK_ID
    for sy in range(gh):
        for sx in range(gw):
            if not texty[sy, sx] or seen[sy, sx]:
                continue
            stack, comp = [(sy, sx)], []
            seen[sy, sx] = True
            while stack:                               # 8-connected flood fill
                y, x = stack.pop()
                comp.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < gh and 0 <= nx < gw and texty[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            if len(comp) < RESCUE_MIN_CELLS:
                continue
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            box = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
            if len(comp) / box < RESCUE_MIN_DENSITY:
                continue
            x0 = max(0, min(xs) * c - RESCUE_PAD)
            y0 = max(0, min(ys) * c - RESCUE_PAD)
            x1 = min(W, (max(xs) + 1) * c + RESCUE_PAD)
            y1 = min(H, (max(ys) + 1) * c + RESCUE_PAD)
            crop = ImageOps.autocontrast(im.crop((x0, y0, x1, y1)))
            for rx0, ry0, rx1, ry1 in xy_cut(np.asarray(crop, dtype=np.float32)):
                strip = crop.crop((rx0, ry0, rx1, ry1))
                tsv = _tess(strip, os.path.join(OUT_DIR, f"{stem}_resc{nid}"),
                            TESS_PSM_RESCUE, ["tsv"])["tsv"]
                for w in parse_words(tsv, block_offset=nid):
                    w["l"] += x0 + rx0
                    w["t"] += y0 + ry0
                    words.append(w)
                nid += 1
            nid += 10 - (nid % 10)
    return words


def parse_words(tsv, block_offset=0):
    rows = tsv.splitlines()
    hdr = rows[0].split("\t")
    ix = {k: i for i, k in enumerate(hdr)}
    words = []
    for r in rows[1:]:
        f = r.split("\t")
        if len(f) < len(hdr) or f[ix["level"]] != "5":
            continue
        text = f[ix["text"]].strip()
        if not text:
            continue
        words.append({
            "block": int(f[ix["block_num"]]) + block_offset,
            "par": int(f[ix["par_num"]]),
            "line": int(f[ix["line_num"]]),
            "l": int(f[ix["left"]]), "t": int(f[ix["top"]]),
            "w": int(f[ix["width"]]), "h": int(f[ix["height"]]),
            "conf": float(f[ix["conf"]]),
            "text": text,
        })
    return words


# ---------------------------------------------------------------------------
# text cleanup
# ---------------------------------------------------------------------------

def reflow(lines):
    """Undo the printed line breaks of one paragraph, returning a single line.

    A hyphen at a line end is NOT resolved here, only MARKED.  German writes one
    for three different reasons and no local rule separates them:

        Zei-/chensatz        soft hyphen  -> "Zeichensatz"   (drop it)
        Sprite-/Block        compound     -> "Sprite-Block"  (keep it)
        Groß-/und Klein...   suspended    -> "Groß- und ..." (keep it AND a space)

    A case test gets the third wrong -- "und" is lowercase, so treating a break
    before a lowercase letter as a soft hyphen yields "Großund".  So the hyphen
    becomes HYPHEN_MARK and all three readings stay open for a later pass to
    decide.  A hyphen that was in the MIDDLE of a printed line is left as a plain
    "-", so the two are always distinguishable."""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if not out:
            out = ln
        elif out.endswith("-"):
            out = out[:-1] + HYPHEN_MARK + ln
        else:
            out = out + " " + ln
    return out


def paragraphs(line_list, line_txt):
    """Split a block's lines into paragraphs on the first-line indent."""
    if not line_list:
        return []
    x0s = [min(w["l"] for w in lw) for lw in line_list]
    base = statistics.median(x0s)
    paras, cur = [], []
    for i, txt in enumerate(line_txt):
        indent = x0s[i] - base if i < len(x0s) else 0
        if cur and PARA_INDENT_MIN_PX <= indent <= PARA_INDENT_MAX_PX:
            paras.append(cur)
            cur = []
        cur.append(txt)
    if cur:
        paras.append(cur)
    return paras


def splice_dropcap(line_list, line_txt, median_h):
    """Remove a drop cap word and prepend its letter to the first line."""
    cap = None
    for li, lw in enumerate(line_list):
        for w in lw:
            if w["h"] > DROPCAP_H_RATIO * median_h and len(w["text"]) <= DROPCAP_MAX_CHARS \
                    and w["text"][0].isupper():
                cap = (li, w)
                break
        if cap:
            break
    if not cap:
        return line_txt
    li, w = cap
    letter = w["text"][0]
    rest = [x for x in line_list[li] if x is not w]
    line_txt = list(line_txt)
    line_txt[li] = " ".join(x["text"] for x in rest)
    for j, t in enumerate(line_txt):
        if t.strip():
            line_txt[j] = letter + t.lstrip()
            break
    # Emptied lines are left in place rather than filtered out: the paragraph
    # split indexes this list against the line geometry, and dropping an entry
    # here would shift every indent measurement after it onto the wrong line.
    return line_txt


# ---------------------------------------------------------------------------
# features
# ---------------------------------------------------------------------------

def stdev(xs):
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def block_features(words, W, H):
    groups = defaultdict(list)
    for w in words:
        groups[w["block"]].append(w)

    blocks = []
    for bid, ws in sorted(groups.items()):
        x0 = min(w["l"] for w in ws)
        y0 = min(w["t"] for w in ws)
        x1 = max(w["l"] + w["w"] for w in ws)
        y1 = max(w["t"] + w["h"] for w in ws)
        bw, bh = x1 - x0, y1 - y0
        if bw <= 0 or bh <= 0:
            continue
        # The reversed-bar pass gets block ids >= BAR_BLOCK_ID and is exempt from
        # the word-count floor: "Aktuelles", "Grafik" and "Fehlerteufelchen" are
        # each a single word, and the floor silently discarded exactly the
        # section names the whole inverted pass exists to recover.
        if (len(ws) < MIN_BLOCK_WORDS and bid < BAR_BLOCK_ID) \
                or (bw * bh) / (W * H) < MIN_BLOCK_AREA_FRAC:
            continue

        lines = defaultdict(list)
        for w in ws:
            lines[(w["par"], w["line"])].append(w)
        # sort by MEDIAN top, not min: a drop cap's tall bbox otherwise drags its
        # line above the line that visually precedes it (measured on p58).
        line_list = [sorted(lines[k], key=lambda x: x["l"])
                     for k in sorted(lines, key=lambda k: statistics.median(x["t"] for x in lines[k]))]

        line_txt = [" ".join(w["text"] for w in lw) for lw in line_list]
        n_lines = len(line_list)
        line_h = statistics.median([statistics.median([w["h"] for w in lw]) for lw in line_list])
        line_txt = splice_dropcap(line_list, line_txt, line_h)

        rights = [max(w["l"] + w["w"] for w in lw) for lw in line_list]
        ragged_r = stdev(rights) / bw if bw else 0.0

        ratios = [w["w"] / len(w["text"]) for w in ws if len(w["text"]) >= 3]
        mono = (stdev(ratios) / statistics.mean(ratios)) if len(ratios) > 2 and statistics.mean(ratios) else 1.0

        chars = "".join(w["text"] for w in ws)
        n_ch = max(1, len(chars))
        digits = sum(c.isdigit() for c in chars) / n_ch
        upper = sum(c.isupper() for c in chars) / max(1, sum(c.isalpha() for c in chars))

        basic = sum(bool(BASIC_LINE_RE.match(t)) for t in line_txt) / max(1, len(line_txt))
        hexd = sum(bool(HEX_LINE_RE.search(t)) for t in line_txt) / max(1, len(line_txt))
        klein = sum(bool(KLEIN_RE.search(t)) for t in line_txt) / max(1, len(line_txt))

        blocks.append({
            "id": bid,
            "bbox": [x0, y0, x1, y1],
            "bbox_frac": [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)],
            "n_words": len(ws),
            "n_lines": n_lines,
            "conf": round(statistics.mean(w["conf"] for w in ws), 1),
            "w_frac": round(bw / W, 4),
            "h_frac": round(bh / H, 4),
            "line_h_frac": round(line_h / H, 5),
            "ragged_right": round(ragged_r, 4),
            "mono": round(mono, 4),
            "digit_frac": round(digits, 3),
            "upper_frac": round(upper, 3),
            "basic_line_frac": round(basic, 3),
            "hex_line_frac": round(hexd, 3),
            "klein_frac": round(klein, 3),
            # one line per PARAGRAPH, printed line breaks undone
            "text": "\n".join(t for t in (reflow(p) for p in paragraphs(line_list, line_txt)) if t),
        })
    return blocks


# ---------------------------------------------------------------------------
# heuristic labelling
# ---------------------------------------------------------------------------

def is_listing(b):
    if b["digit_frac"] >= LISTING_DIGIT_FRAC and b["n_lines"] >= LISTING_MIN_LINES:
        return True
    if b["basic_line_frac"] >= LISTING_LINE_FRAC or b["hex_line_frac"] >= LISTING_LINE_FRAC:
        return True
    if b["conf"] < LISTING_LOWCONF and b["basic_line_frac"] >= LISTING_BASIC_FRAC:
        return True
    return False


def heuristic_label(b, W, H):
    """First guess.  Deterministic where the evidence is geometric; genuinely
    ambiguous blocks stay 'body' for stage B to arbitrate."""
    x0, y0, x1, y1 = b["bbox"]
    cx0, cx1 = x0 / W, x1 / W
    cy0, cy1 = y0 / H, y1 / H

    if (cx0 < SLIVER_EDGE_FRAC or cx1 > (1.0 - SLIVER_EDGE_FRAC)) and b["w_frac"] <= SLIVER_MAX_W_FRAC:
        return "sliver"
    if cy1 < HEADER_BAND:
        return "header"
    if cy0 > FOOTER_BAND or (cy0 > 0.90 and FOOTER_RE.search(b["text"])):
        return "footer"
    if b["conf"] < MIN_BLOCK_CONF and not is_listing(b):
        return "noise"
    if is_listing(b):
        return "listing-standalone" if b["h_frac"] >= LISTING_STANDALONE_H_FRAC else "listing-inline"
    if b["klein_frac"] >= KLEIN_HIT_PER_LINE and b["line_h_frac"] <= KLEIN_MAX_LINE_H_FRAC:
        return "kleinanzeige"
    if CAPTION_RE.match(b["text"]):
        return "caption"
    if b["n_lines"] <= HEADING_MAX_LINES and b["line_h_frac"] >= HEADING_MIN_H_FRAC:
        return "heading"
    return "body"


def merge_listings(blocks, W, H):
    """Adjacent listing blocks are one listing (p58's hex dump split into three
    columns plus a garbage strip).  Group them, then re-decide standalone-vs-
    inline on the union box -- a tall dump split into short pieces must not be
    let through as a set of inline snippets."""
    idx = [i for i, b in enumerate(blocks) if b["label"].startswith("listing")]
    if not idx:
        return
    gx, gy = LISTING_MERGE_GAP_FRAC * W, LISTING_MERGE_GAP_FRAC * H
    parent = {i: i for i in idx}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a in idx:
        for c in idx:
            if a >= c:
                continue
            ax0, ay0, ax1, ay1 = blocks[a]["bbox"]
            cx0, cy0, cx1, cy1 = blocks[c]["bbox"]
            if (ax0 - gx) <= cx1 and (cx0 - gx) <= ax1 and (ay0 - gy) <= cy1 and (cy0 - gy) <= ay1:
                parent[find(a)] = find(c)

    captions = [b for b in blocks if LISTING_CAPTION_RE.match(b["text"])]
    groups = defaultdict(list)
    for i in idx:
        groups[find(i)].append(i)
    for g, members in groups.items():
        x0 = min(blocks[i]["bbox"][0] for i in members)
        y0 = min(blocks[i]["bbox"][1] for i in members)
        x1 = max(blocks[i]["bbox"][2] for i in members)
        y1 = max(blocks[i]["bbox"][3] for i in members)
        tall = (y1 - y0) / H >= LISTING_STANDALONE_H_FRAC
        gap = LISTING_CAPTION_GAP_FRAC * H
        titled = any(cx0 <= x1 and cx1 >= x0 and (y0 - gap) <= cy1 and cy0 <= (y1 + gap)
                     for cx0, cy0, cx1, cy1 in (c["bbox"] for c in captions))
        label = "listing-standalone" if (tall or titled) else "listing-inline"
        for i in members:
            blocks[i]["label"] = label
            blocks[i]["listing_group"] = g


# ---------------------------------------------------------------------------
# outputs
# ---------------------------------------------------------------------------

def reading_order(blocks):
    """Column-major order.  The magazine sets 2-3 columns, so a plain
    top-to-bottom sort interleaves them into nonsense.  Blocks are grouped by
    left edge, groups run left to right, each group top to bottom."""
    cols = []
    for b in sorted(blocks, key=lambda b: b["bbox_frac"][0]):
        x0 = b["bbox_frac"][0]
        for c in cols:
            if abs(c["x"] - x0) <= COLUMN_TOL:
                c["items"].append(b)
                break
        else:
            cols.append({"x": x0, "items": [b]})
    out = []
    for c in sorted(cols, key=lambda c: c["x"]):
        out.extend(sorted(c["items"], key=lambda b: b["bbox_frac"][1]))
    return out


def write_article(page, blocks, dest):
    keep = [b for b in blocks if b["label"] in ARTICLE_LABELS]
    text = "\n".join(b["text"].strip() for b in reading_order(keep) if b["text"].strip())
    open(dest, "w", encoding="utf-8").write(text + ("\n" if text else ""))
    return len(text)


def draw_overlay(png, blocks, dest):
    im = Image.open(png).convert("RGB")
    sc = OVERLAY_DPI / SRC_DPI
    im = im.resize((round(im.size[0] * sc), round(im.size[1] * sc)), Image.BOX)
    k = OVERLAY_DPI / OCR_DPI
    d = ImageDraw.Draw(im)
    for b in blocks:
        x0, y0, x1, y1 = [v * k for v in b["bbox"]]
        c = COLOURS.get(b["label"], (255, 0, 0))
        d.rectangle([x0, y0, x1, y1], outline=c, width=2)
        d.text((x0 + 3, max(0, y0 - 11)), b["label"], fill=c)
    im.save(dest)


def write_digest(page, blocks, dest):
    """Compact page brief for stage B.  Geometry first, then a text sample --
    the LLM's job is the layout judgement (is this right-hand half an ad?), not
    re-reading the whole page."""
    out = [f"PAGE {page}", "id  label            x0    y0    x1    y1   lines  conf  text"]
    for b in blocks:
        x0, y0, x1, y1 = b["bbox_frac"]
        sample = b["text"].replace("\n", " / ")[:200]
        out.append(f"{b['id']:<3} {b['label']:<16} {x0:<5.2f} {y0:<5.2f} {x1:<5.2f} {y1:<5.2f} "
                   f"{b['n_lines']:<6} {b['conf']:<5.0f} {sample}")
    open(dest, "w", encoding="utf-8").write("\n".join(out) + "\n")


def process(page):
    stem = f"{page:03d}"
    png = os.path.join(SRC_DIR, stem + ".png")
    tsv, txt, bar_tsv, origin, im, W, H = run_tesseract(png, stem)

    words = parse_words(tsv)
    if bar_tsv:
        # bar words get block ids past the end of the main pass so they form
        # their own block rather than merging into a real one, and their
        # coordinates are shifted back into page space
        for w in parse_words(bar_tsv, block_offset=BAR_BLOCK_ID):
            if sum(c.isalpha() for c in w["text"]) < BAR_MIN_LETTERS:
                continue
            w["l"] += origin[0]
            w["t"] += origin[1]
            words.append(w)

    blocks = block_features(words, W, H)
    # second pass over anything the layout analysis skipped, then rebuild
    extra = rescue_uncovered(im, blocks, stem, W, H)
    if extra:
        blocks = block_features(words + extra, W, H)
    for b in blocks:
        b["label"] = heuristic_label(b, W, H)
    merge_listings(blocks, W, H)

    rec = {"page": page, "ocr_size": [W, H], "ocr_dpi": OCR_DPI, "blocks": blocks}
    json.dump(rec, open(os.path.join(OUT_DIR, stem + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(OUT_DIR, stem + ".txt"), "w", encoding="utf-8").write(txt)
    write_digest(page, blocks, os.path.join(OUT_DIR, stem + ".digest.txt"))
    # Provisional corpus text from the geometric labels alone, so the review
    # folder is populated before the LLM pass runs.  Stage B overwrites it.
    write_article(page, blocks, os.path.join(OUT_DIR, stem + ".article.txt"))
    draw_overlay(png, blocks, os.path.join(OUT_DIR, stem + "_boxes.png"))

    tally = defaultdict(int)
    for b in blocks:
        tally[b["label"]] += 1
    print(f"p{stem}: {len(blocks)} blocks  " +
          "  ".join(f"{k}={v}" for k, v in sorted(tally.items())), flush=True)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for a in sys.argv[1:]:
        process(int(a))
