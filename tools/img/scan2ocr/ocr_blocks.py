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
from PIL import Image, ImageDraw, ImageFilter, ImageOps

# ---------------------------------------------------------------------------
# CONSTANTS  (no CLI knobs, no env knobs -- see CLAUDE.md)
# ---------------------------------------------------------------------------

# The DESKEWED, MATTED, A4-CROPPED, GRADED 600 dpi master -- not the raw thumbs.
# Three reasons, in order of weight:
#   * figure crops and text then share ONE coordinate system.  The raw thumbs are
#     uncropped and each page has its own width (5245 / 5127 / 5197 px against a
#     uniform 4960 here), so a block's page-fraction means something different on
#     every page and any crop taken elsewhere needs a per-page remap.
#   * an A4-cropped page HAS no facing page, which deletes the sliver problem
#     rather than detecting around it.
#   * MEASURED, the grade also reads better: unknown-word rate against a German
#     dictionary over p8/p55/p58 fell 19.85% -> 19.08% and mean word confidence
#     rose 88.1 -> 88.7.
SRC_DIR = "/Users/mist/DNB/8609/tmp/master600/final"
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
# Rescued crops are BINARISED (Otsu on the crop's own histogram), not merely
# contrast-stretched.  A screened tint stays mid-grey under a stretch and
# tesseract's global binarizer then eats into the type: MEASURED on p51, the
# panel heading read "Chedksummer und MSE" stretched and "Checksummer und MSE"
# binarised.  psm 6 is kept over psm 3 even though psm 3 recovers one extra short
# line here, because psm 3 returns the panel out of reading order -- it put
# "schweifte Klammern / was innerhalb der Klammern steht" near the top -- and
# mangles more words.  Order and accuracy beat one line.
# NOTE: binarising the WHOLE PAGE was tried and rejected. It does not make the
# main pass find the panel (psm 1 still misses it) and it costs accuracy overall:
# unknown-word rate over p8/p51/p55/p58 went 18.28% grey -> 18.69% Otsu -> 19.05%
# Sauvola. The rescue pass is genuinely necessary; binarisation belongs only here.
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
# A region the main pass read BADLY must be redone, not merely topped up.  Its
# ink is "covered", so the rescue used to skip it entirely.  MEASURED on p9's
# boxed panel: the main pass returned garbled fragments at conf 56-71 ("36 des
# oimmodore Amiga m", "nellen Beispielen ir Kunst"), the rescue then found only
# the scraps between them and produced one block spanning BOTH panel columns with
# their lines interleaved, which scored conf 56.5, was labelled noise, and took
# the panel's whole opening paragraph out of the corpus with it.
# So only CONFIDENT blocks mask the ink map.  Anything below this is treated as
# uncovered, the region is re-OCR'd whole, and the original fragments are then
# dropped in favour of the clean re-read.
RESCUE_KEEP_CONF = 78.0
# ...and a re-read supersedes any original block it substantially covers, however
# confident that block was: p9's block 21 scored 96.7 while being a fragment of
# the same paragraph, and keeping it would duplicate text.
RESCUE_SUPERSEDE_FRAC = 0.6
# When a re-read and an original overlap, the more trustworthy one wins, and
# trust is confidence.  MEASURED on p10: the main pass read "Ab sofort können auch
# die Besitzer von C 128-Computern ver-" at conf 94.3, a rescue crop overlapped it
# and produced a horizontally CLIPPED version missing the left half of every line,
# and the original was deleted in favour of it.  Skipping such components outright
# was tried first and was far worse -- it cost p51 its whole rescued sidebar
# (recall 1.00 -> 0.60) and p9 its panel -- because a component's cells can be
# genuinely uncovered while its bounding box still grazes a confident block.
# So both readings are kept until the end, and then the loser is dropped.

# A one-line HEADING is only one or two cells tall, so its interior cells have
# just two text-like neighbours and a threshold of 3 erased them -- p9's panel
# heading "Computerzeit für Grafikfreunde" vanished before the flood fill ever
# saw it, though the cut and the OCR both handled it perfectly.  2 keeps thin
# bands of type.  Solid rules are not a danger here anyway: a rule is uniformly
# dark inside a cell, so it already fails the variance test that defines "texty".
# Text on a SCREENED TINT must be re-read even where the main pass was confident,
# because there tesseract is confidently WRONG.  MEASURED on p11's bottom-right
# panel, it returned "die unterschied. der Organisation und de Ai Inhaltsverzei
# nisses." at conf 91.0, which no confidence gate can catch.  What does separate
# the cases is the background itself: the fraction of pixels that are pure white.
# MEASURED -- tint panels 0.004 / 0.006 / 0.009 (p51, p9, p11), plain columns
# 0.668 / 0.719.  Two orders of magnitude, so the threshold sits anywhere between.
SCREEN_WHITE_FRAC = 0.10

RESCUE_MIN_NEIGHBOURS = 2
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
# A strip smaller than this is discarded as a leftover sliver.  It must stay
# BELOW one line of type: at 300 dpi a text line is ~50 px tall, and a 120 px
# floor silently threw away the heading band of every rescued panel -- p9's
# "Computerzeit für Grafikfreunde" among them.  40 px is under a single line and
# still well above the grit the cut leaves behind.
RESCUE_STRIP_MIN_PX = 40
RESCUE_CUT_DEPTH = 6        # recursion limit for the XY-cut
# The XY-cut lands exactly on the ink, leaving a strip with no white margin, and
# tesseract reads such a strip badly or not at all.  MEASURED on p9: the heading
# band came out 42 px tall in the pipeline against 57 px when cropped by hand, and
# psm 6 returned NOTHING from the tight version while reading "Computerzeit für
# Grafikfreunde" perfectly from the padded one.  Each cut rectangle is therefore
# grown before OCR, clamped to the crop.
RESCUE_RECT_PAD = 8
# Panels are printed over a SCREENED TINT, and at 300 dpi its dots survive as a
# fine texture that fills every gutter.  MEASURED on p9's boxed panel: the longest
# white run was 4 px across the columns and 2 px down the rows, so no cut was
# possible and both columns were OCR'd as one interleaved block.  A 3x3 median
# clears isolated dots and restores the gutters to 34 px and 41 px.  It is applied
# ONLY to the geometry used for cutting and to the rescued crop -- the screen does
# not hurt legibility (word accuracy was measured identical with and without it,
# only confidence rose), so nothing else needs descreening.
DESCREEN_MEDIAN = 3

# A word below this confidence is the binarizer hallucinating letters out of a
# halftone photo or a screened tint.  Blocks made mostly of such words are kept
# but labelled "noise" -- deleting them would make a photo look like blank paper,
# and stage B benefits from knowing a photo is there.
MIN_BLOCK_CONF = 55.0

# Blocks smaller than this are OCR grit, not content.
MIN_BLOCK_WORDS = 2
MIN_BLOCK_AREA_FRAC = 0.00015

# --- neighbour-page sliver: NOT DETECTED, BY DESIGN --------------------------
# The raw thumbs were uncropped and carried a strip of the FACING page at one
# edge (p5 left, p58/p61 right, landing at x >= 0.99 with conf 3.8-40), which had
# to be found geometrically because sliver text is real text that confidence
# will not reject.  SRC_DIR is now the A4-cropped master, so no facing page is
# present and the rule has nothing true left to find -- it could only misfire, on
# genuine narrow content near a trim edge such as the vertical set price line in
# p61's ad.  Dropping real text is the one error this pipeline must not make, so
# the rule is gone rather than merely loosened.  The "sliver" LABEL is kept in the
# vocabulary: stage B may still apply it if a page turns out to be uncropped.

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
# Sitting low on the page is NOT enough to be a folio.  MEASURED on p146, the
# closing "Info: Heinz Haarmann, Kosterstraße 92, 4630 Bochum 1" line of a review
# starts at y=0.94 and was labelled footer on position alone, then dropped -- and
# because stage B is told to trust geometry unless the image contradicts it, the
# LLM kept that label.  A folio also has to LOOK like one: it names the issue, or
# it is a couple of words carrying the page number.  Anything else down there is
# the last line of a column.
FOOTER_MAX_WORDS = 4
FOOTER_MIN_DIGITS = 0.2

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
# A drop cap also wrecks tesseract's BLOCK segmentation: the two or three lines
# set beside the cap are indented away from the column edge, so they are emitted
# as separate blocks from the rest of the paragraph.  MEASURED on p58, where the
# opening paragraph came back as three blocks -- "it »Shrinksprite« ... Programm"
# alone in one, "nennt, lassen sich ... ver-" swallowed by the standfirst above,
# and "kleinern oder aber ..." in a third that the cap was then spliced onto,
# giving "Mkleinern".  Words whose vertical centre lies within the cap's own span
# and which sit to its right in the same column are therefore reassigned to the
# cap's block before any features are measured.  That is a fact about how the
# paragraph was set, not a repair of a threshold.
# The reach must stop at the cap's OWN block, never past it.  A first attempt
# allowed 1.15x the block width and at 0.076 + 1.15*0.43 that lands at 0.57 --
# inside the RIGHT-hand column, which dragged "ler (Bild" and "noch einen" out of
# the facing column and wove them into the paragraph.

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
# A subhead is not indented, so the indent test alone leaves it glued to the end
# of the paragraph above ("...ist überflüssig. Zielblock").  What actually marks
# it on the page is the EXTRA LEADING above it -- the compositor opened up the
# space.  A line whose gap to the previous line exceeds this multiple of the
# block's own median line pitch therefore starts a new paragraph too.  Measuring
# the pitch per block keeps this valid at any type size.
# ...except that MEASURED on p58 the leading above a subhead is not larger at
# all: "Zielblock" sits at 0.81 of the block's line pitch and "Spritenummer" at
# 0.98.  The compositor set them tight, so leading cannot find them.
PARA_GAP_RATIO = 1.45
# What DOES mark a subhead is that it is BOLD, and boldness is directly
# measurable as ink coverage inside the line's own box.  MEASURED on p58:
# subheads 0.401 / 0.427 / 0.522 against 119 body lines whose median is 0.248 and
# whose MAXIMUM is 0.311 -- no overlap whatever.  The test is a ratio to the
# block's own median line, not an absolute, so it holds at any type size or
# printing density: the subheads run 1.6x to 2.1x the median while the body's own
# 90th percentile only reaches 1.15x.
BOLD_INK_RATIO = 1.35
# A line that stops well short of the right margin was ended DELIBERATELY -- it is
# a list item, a line of code, a line of an address -- and the next line starts a
# new paragraph.  In justified body text every line except a paragraph's last
# reaches the margin, so this cannot misfire on ordinary prose, and firing on a
# paragraph's genuine last line is correct anyway.  MEASURED against vision
# transcription, merging these was the largest single source of disagreement:
# p55's printer-code table, p61's errata code lines and p8's numbered list all
# came out as one paragraph where a reader sees several.
SHORT_LINE_FRAC = 0.85

# NOTE -- split_block_columns() below is written but NOT WIRED IN, deliberately.
# Tesseract does sometimes put two neighbouring columns in one block, and then
# every line spans both: MEASURED on p10, a block of vendor addresses read
# "8910 Landsberg 2300 Kiel / DÜM: Dümnler Verlag Hal: Haller Verlag" -- across
# instead of down, which is factually wrong text.  Cutting at a gutter no word
# crosses fixes that, but MEASURED against vision it made the corpus worse
# overall (recall 0.917 -> 0.913, precision 0.910 -> 0.895): once each address
# sits in its own column, the short-line rule splits its three lines into three
# paragraphs where a reader, and vision, see one entry.  Fixing the granularity
# and the interleaving together needs one change, not this half of it, so the
# function stays here unused rather than being deleted and rediscovered.
BLOCK_GUTTER_PX = 30
BLOCK_SPLIT_MIN_LINES = 3
SPLIT_BLOCK_ID = 3000

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

# A block this wide spans the page rather than sitting in a column -- a headline
# or a standfirst.  Column-major ordering alone put p58's headline LAST, because
# its left edge (0.167) formed its own column bucket sorting after the body's
# (0.076).  A full-width block instead ends one band and starts the next, so it
# reads before the columns beneath it, which is the order a person reads.
FULLWIDTH_FRAC = 0.55

# Column membership is decided by how much a block OVERLAPS a column, not by how
# close its left edge is.  A centred subhead is inset from the column edge --
# p58's "Tips für Maschinenprogrammierer" starts at 0.601 against its column's
# 0.527 -- so a left-edge test with any workable tolerance invents a phantom
# column for it, which then sorts after the real one and drops the subhead to the
# bottom of the page.  Overlap has no such failure: the subhead lies entirely
# within its column.
COLUMN_MIN_OVERLAP = 0.5   # fraction of the NARROWER block that must overlap

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


def binarize(img):
    """Otsu on the image's own histogram.  See the RESCUE_* notes for why a
    rescued crop is binarised rather than merely contrast-stretched."""
    a = np.asarray(img)
    h = np.histogram(a, 256, (0, 256))[0].astype(float)
    tot = h.sum()
    w0 = np.cumsum(h)
    w1 = tot - w0
    m = np.cumsum(h * np.arange(256))
    with np.errstate(invalid="ignore", divide="ignore"):
        var = (m[-1] * w0 / tot - m) ** 2 / (w0 * w1)
    return Image.fromarray(((a > int(np.nanargmax(var))) * 255).astype(np.uint8))


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
            # A single span still counts when it is SMALLER than the input: that
            # is a margin being trimmed.  Treating it as "no split" was why p9's
            # panel survived whole -- the row cut separated its heading from its
            # body, left one span, and the recursion stopped before ever looking
            # for the column gutter inside that body band.
            trimmed = len(spans) == 1 and (spans[0][0] > 0 or spans[0][1] < len(prof))
            if len(spans) > 1 or trimmed:
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

    # cells whose background is a screened tint rather than paper
    screened = (cells == 255).mean(axis=(2, 3)) < SCREEN_WHITE_FRAC

    g = RESCUE_COVER_GROW
    for b in blocks:                                   # mask off what we READ WELL
        if b["conf"] < RESCUE_KEEP_CONF:
            continue
        x0, y0, x1, y1 = b["bbox"]
        sl = (slice(max(0, y0 // c - g), (y1 // c) + 1 + g),
              slice(max(0, x0 // c - g), (x1 // c) + 1 + g))
        # a confident block masks its ink only where it sits on PAPER; on a tint
        # its confidence means nothing and the region is re-read regardless
        texty[sl] &= screened[sl]

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
            crop = binarize(im.crop((x0, y0, x1, y1))
                             .filter(ImageFilter.MedianFilter(DESCREEN_MEDIAN)))
            cw, ch = crop.size
            for rx0, ry0, rx1, ry1 in xy_cut(np.asarray(crop, dtype=np.float32)):
                rx0 = max(0, rx0 - RESCUE_RECT_PAD)
                ry0 = max(0, ry0 - RESCUE_RECT_PAD)
                rx1 = min(cw, rx1 + RESCUE_RECT_PAD)
                ry1 = min(ch, ry1 + RESCUE_RECT_PAD)
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


def paragraphs(line_list, line_txt, arr):
    """Split a block's lines into paragraphs on the first-line indent."""
    if not line_list:
        return []
    x0s = [min(w["l"] for w in lw) for lw in line_list]
    base = statistics.median(x0s)
    tops = [statistics.median(w["t"] for w in lw) for lw in line_list]
    rights = [max(w["l"] + w["w"] for w in lw) for lw in line_list]
    right_edge = max(rights) if rights else 0
    inks = []
    for lw in line_list:
        lx0 = min(w["l"] for w in lw)
        lx1 = max(w["l"] + w["w"] for w in lw)
        ly0 = min(w["t"] for w in lw)
        ly1 = max(w["t"] + w["h"] for w in lw)
        cell = arr[ly0:ly1, lx0:lx1]
        inks.append(float((cell < 128).mean()) if cell.size else 0.0)
    ink_med = statistics.median([i for i in inks if i > 0]) if any(inks) else 0.0
    gaps = [tops[i] - tops[i - 1] for i in range(1, len(tops))]
    pitch = statistics.median(gaps) if gaps else 0

    paras, cur = [], []
    for i, txt in enumerate(line_txt):
        indent = x0s[i] - base if i < len(x0s) else 0
        gap = (tops[i] - tops[i - 1]) if i else 0
        new_para = PARA_INDENT_MIN_PX <= indent <= PARA_INDENT_MAX_PX
        if pitch and i and gap > PARA_GAP_RATIO * pitch:
            new_para = True
        if ink_med and inks[i] > BOLD_INK_RATIO * ink_med:   # a bold subhead
            new_para = True
        # ...but a paragraph cannot begin in the middle of a word.  A very short
        # line packs its box tightly enough to pass the bold test on its own --
        # MEASURED, "sig." (the tail of "überflüs-/sig.") did exactly that -- so a
        # break is refused outright when the previous line ends mid-word.
        # a deliberately short PREVIOUS line ends its paragraph here
        if i and right_edge and rights[i - 1] < SHORT_LINE_FRAC * right_edge:
            new_para = True
        if i and line_txt[i - 1].rstrip().endswith("-"):
            new_para = False
        if cur and new_para:
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


def rejoin_dropcap_lines(words):
    """Reattach lines set beside a drop cap to the cap's own block.  See
    DROPCAP_COL_W_FRAC for why tesseract splits them off in the first place."""
    # A line is identified by the block it was recognised in, not by par/line
    # alone: those numbers restart per block, so once words are moved between
    # blocks two unrelated printed lines share a key and get fused into one.
    for w in words:
        w.setdefault("lkey", (w["block"], w["par"], w["line"]))

    by_block = defaultdict(list)
    for w in words:
        by_block[w["block"]].append(w)

    for bid, ws in list(by_block.items()):
        if len(ws) < 2:
            continue
        med_h = statistics.median(w["h"] for w in ws)
        caps = [w for w in ws
                if w["h"] > DROPCAP_H_RATIO * med_h
                and len(w["text"]) <= DROPCAP_MAX_CHARS
                and w["text"][:1].isupper()]
        if not caps:
            continue
        cap = caps[0]
        x_lo, x_hi = cap["l"], max(w["l"] + w["w"] for w in ws)
        y_lo, y_hi = cap["t"], cap["t"] + cap["h"]
        for w in words:
            if w["block"] == bid:
                continue
            cy = w["t"] + w["h"] / 2
            if y_lo <= cy <= y_hi and x_lo <= w["l"] <= x_hi:
                w["block"] = bid
    return words


def split_block_columns(words):
    """Cut a block that holds two side-by-side columns.  See BLOCK_GUTTER_PX."""
    by_block = defaultdict(list)
    for w in words:
        by_block[w["block"]].append(w)

    nid = SPLIT_BLOCK_ID
    for bid, ws in sorted(by_block.items()):
        lines = {w.get("lkey", (w["block"], w["par"], w["line"])) for w in ws}
        if len(lines) < BLOCK_SPLIT_MIN_LINES:
            continue
        x0 = min(w["l"] for w in ws)
        x1 = max(w["l"] + w["w"] for w in ws)
        covered = np.zeros(x1 - x0 + 1, dtype=bool)
        for w in ws:
            covered[w["l"] - x0: w["l"] + w["w"] - x0] = True

        gaps, run = [], 0
        for i, c in enumerate(covered):
            if not c:
                run += 1
            else:
                if run >= BLOCK_GUTTER_PX:
                    gaps.append((i - run + x0, i + x0))
                run = 0
        if not gaps:
            continue
        # cut at every gutter; segments keep their reading order left to right
        bounds = [x0] + [g[0] for g in gaps] + [x1 + 1]
        for k in range(len(bounds) - 1):
            lo, hi = bounds[k], bounds[k + 1]
            seg = [w for w in ws if lo <= w["l"] < hi]
            if not seg:
                continue
            if k == 0:
                continue                      # first segment keeps the block id
            for w in seg:
                w["block"] = nid
            nid += 1
    return words


def block_features(words, W, H, arr):
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
            lines[w.get("lkey", (w["block"], w["par"], w["line"]))].append(w)
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
            "text": "\n".join(t for t in (reflow(p) for p in paragraphs(line_list, line_txt, arr)) if t),
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

    if cy1 < HEADER_BAND:
        return "header"
    if cy0 > 0.90 and (FOOTER_RE.search(b["text"])
                       or (cy0 > FOOTER_BAND and b["n_words"] <= FOOTER_MAX_WORDS
                           and b["digit_frac"] >= FOOTER_MIN_DIGITS)):
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
    # split into bands first: a page-wide block reads before the columns below it
    bands, cur, band = [], [], 0
    for b in sorted(blocks, key=lambda b: b["bbox_frac"][1]):
        if b["w_frac"] >= FULLWIDTH_FRAC:
            if cur:
                bands.append(cur)
            bands.append([b])
            cur = []
        else:
            cur.append(b)
    if cur:
        bands.append(cur)

    out = []
    for items in bands:
        cols = []
        # widest first, so a full column is established before its insets are placed
        for b in sorted(items, key=lambda b: -b["w_frac"]):
            x0, x1 = b["bbox_frac"][0], b["bbox_frac"][2]
            for c in cols:
                ov = min(x1, c["x1"]) - max(x0, c["x0"])
                if ov > 0 and ov >= COLUMN_MIN_OVERLAP * min(x1 - x0, c["x1"] - c["x0"]):
                    c["items"].append(b)
                    c["x0"] = min(c["x0"], x0)
                    c["x1"] = max(c["x1"], x1)
                    break
            else:
                cols.append({"x0": x0, "x1": x1, "items": [b]})
        for c in sorted(cols, key=lambda c: c["x0"]):
            out.extend(sorted(c["items"], key=lambda b: b["bbox_frac"][1]))
    return out


def write_article(page, blocks, dest):
    keep = [b for b in blocks if b["label"] in ARTICLE_LABELS]
    text = "\n".join(b["text"].strip() for b in reading_order(keep) if b["text"].strip())
    open(dest, "w", encoding="utf-8").write(text + ("\n" if text else ""))
    return len(text)


def is_screened(arr, b):
    """Is this block's background a screened tint rather than paper?"""
    x0, y0, x1, y1 = b["bbox"]
    cell = arr[y0:y1, x0:x1]
    return cell.size > 0 and (cell == 255).mean() < SCREEN_WHITE_FRAC


def drop_superseded(blocks, arr):
    """Remove main-pass blocks that a re-read now covers.  See RESCUE_KEEP_CONF."""
    redone = [b for b in blocks if b["id"] >= RESCUE_BLOCK_ID]
    original = [b for b in blocks if b["id"] < RESCUE_BLOCK_ID]
    if not redone:
        return blocks

    def overlap(a, b):
        ax0, ay0, ax1, ay1 = a["bbox"]
        bx0, by0, bx1, by1 = b["bbox"]
        w = min(ax1, bx1) - max(ax0, bx0)
        h = min(ay1, by1) - max(ay0, by0)
        return w * h if w > 0 and h > 0 else 0

    drop = set()
    for o in original:
        ox0, oy0, ox1, oy1 = o["bbox"]
        oarea = max(1, (ox1 - ox0) * (oy1 - oy0))
        for r in redone:
            rx0, ry0, rx1, ry1 = r["bbox"]
            rarea = max(1, (rx1 - rx0) * (ry1 - ry0))
            ov = overlap(o, r)
            if not ov:
                continue
            if ov >= RESCUE_SUPERSEDE_FRAC * oarea or ov >= RESCUE_SUPERSEDE_FRAC * rarea:
                # the confident reading survives; ties go to the re-read, which
                # was made with layout analysis off and the tint removed
                if o["conf"] >= RESCUE_KEEP_CONF and o["conf"] > r["conf"] \
                        and not is_screened(arr, o):
                    drop.add(id(r))
                else:
                    drop.add(id(o))
    return [b for b in blocks if id(b) not in drop]


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
    out = [f"PAGE {page}",
           "id  label            x0    y0    x1    y1   lines  conf  text",
           "(text shown as  START ... END  -- the END matters: a block breaking",
           " mid-sentence is continued by whichever block starts with the rest)"]
    for b in blocks:
        x0, y0, x1, y1 = b["bbox_frac"]
        # Both ends are shown, because reading order is decided by whether one
        # block's last words are finished by another's first ones.
        flat = " ".join(b["text"].split())
        sample = flat if len(flat) <= 240 else f"{flat[:150]} ... {flat[-80:]}"
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

    words = rejoin_dropcap_lines(words)
    blocks = block_features(words, W, H, np.asarray(im))
    # second pass over anything the layout analysis skipped, then rebuild
    extra = rescue_uncovered(im, blocks, stem, W, H)
    if extra:
        arr = np.asarray(im)
        blocks = drop_superseded(
            block_features(rejoin_dropcap_lines(words + extra), W, H, arr), arr)
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
