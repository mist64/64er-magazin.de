#!/usr/bin/env python3
"""
Mechanical import script for article 085 "Das Maß der Dinge".

Reads from _work/085_das_mass_der_dinge_ocr_raw.txt and places lines
in reading order. All OCR errors are preserved verbatim.

Reading order reconstruction based on multi-column layout analysis of pages 85-89.
Column reordering applied on page 85 (left col text deferred by Tesseract).

Usage:
    python3 _work/085_import.py > _work/085_body.html
"""

import html

RAW = "_work/085_das_mass_der_dinge_ocr_raw.txt"

with open(RAW, "r") as f:
    lines = f.readlines()

L = [l.rstrip("\n") for l in lines]

def e(text):
    """HTML-escape text."""
    return html.escape(text)

out = []

def p(cls, *line_nums):
    """Emit a <p> by concatenating raw lines (1-indexed). Merges with space."""
    parts = [e(L[n - 1]) for n in line_nums]
    text = " ".join(parts)
    if cls:
        out.append(f'        <p class="{cls}">{text}</p>')
    else:
        out.append(f"        <p>{text}</p>")

def h(level, line_num):
    """Emit a heading from a raw line (1-indexed)."""
    out.append(f"        <h{level}>{e(L[line_num - 1])}</h{level}>")

def blank():
    out.append("")

def raw(text):
    out.append(text)

def listing_pre(start, end):
    """Emit OCR'd listing lines as <pre> (verbatim, HTML-escaped)."""
    for i in range(start, end + 1):
        raw(e(L[i - 1]))

# ============================================================
# ARTICLE: "Das Maß der Dinge", pages 85-89
# ============================================================

# === TITLE AND INTRO (page 85, line 107+) ===
h(1, 107)
p("intro", 109, 110, 111, 112, 113)
blank()

# === DROP CAP PARAGRAPH (page 85 left col) ===
# L115 "m die" — drop cap "U" lost by Tesseract
p(None, 115, 117, 119, 120, 121, 122, 123, 124, 125, 126)
blank()

# === TAKTZYKLEN ZÄHLEN (page 85) ===
h(2, 128)
blank()
p(None, 130, 131, 132, 133, 134)
p("noindent", 135)
blank()

# Column reorder: L137-138 + L172-177 = left col continuation
# (Tesseract placed L172-177 after right col text)
p(None, 137, 138, 172, 173, 174, 175, 176, 177)
# Right column start
p(None, 140, 141, 142, 143, 144, 145, 146)
blank()

# === BESCHREIBUNG DES PROGRAMMS (page 85 right col) ===
# L148 + L149 form one heading; L149 "»Taktzyklen«"
h(2, 148)
blank()
# Long paragraph: L151-170 + L181 (page footer break at L178-180)
p(None, 151, 152, 154, 156, 157, 158, 159, 160,
  161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 181)
blank()

# === LAUFZEIT-MESS-SYSTEM »LMS« (page 85 bottom → page 86 top) ===
h(2, 183)
blank()
p(None, 185, 186, 192, 193)
blank()

# === EINSATZMÖGLICHKEITEN (page 86) ===
h(2, 195)
blank()
p(None, 197, 198)
p("noindent", 199)
blank()
p(None, 201, 202, 203, 204, 205)
blank()
p(None, 207, 208, 209, 210, 211, 212, 213)
blank()
p("noindent", 215)
blank()
p(None, 217, 218, 219, 220)
blank()
p(None, 222, 223, 224)
blank()

# === BEDIENUNGSANLEITUNG (page 86) ===
h(2, 225)
blank()
p(None, 227, 228, 229, 230)
blank()

# === MESSEN (m) (page 86) ===
h(3, 232)
blank()
p(None, 234, 235, 236, 237, 238, 239)
blank()
# Paragraph interrupted by Bild 1 flowchart OCR (L243-267 = flowchart box text, skip)
p(None, 241, 268, 269, 270)
blank()

# === BILD 1 ===
raw('        <figure>')
raw('            <img src="85-1.png" alt="">')
raw('            <figcaption>Bild 1. Flußdiagramm zum Laufzeit-Meß-System »LMS«. Nach diesem Schema berechnet man die Laufzeit eines Basic-Programms.</figcaption>')
raw('        </figure>')
blank()

# === LISTINGS 1+2 (page 86, side-by-side hex dump + source, merged by Tesseract) ===
raw('        <figure>')
raw('        <pre>')
listing_pre(275, 291)
raw('        </pre>')
raw('            <figcaption>Listing 1. »Taktzyklen« geben Sie bitte mit dem MSE ein.</figcaption>')
raw('        </figure>')
blank()

raw('        <figure>')
raw('        <pre>')
listing_pre(298, 348)
raw('        </pre>')
raw('            <figcaption>Listing 2. Information für Profis. Quell-Code-Listing zu »Taktzyklen«</figcaption>')
raw('        </figure>')
blank()

# === PAGE 87 PROSE (continuation after END) ===
p(None, 360, 361, 362, 363)
blank()

# === ANZEIGE AB NR. (a) ===
h(3, 365)
blank()
p(None, 367, 368)
blank()
p(None, 370, 371, 372, 373, 374)
blank()
p(None, 376, 377)
blank()

# === VORHERGEHENDE SEITE (↑) ===
# L379 has "Vorhergehende Seite (1)" — "1" is OCR for "↑"
h(3, 379)
blank()
p(None, 381, 382)

# === NÄCHSTE SEITE (RETURN) ===
h(3, 383)
blank()
p(None, 385, 386)

# === SUMME (s) ===
# L387 "Summe" — "(s)" garbled across lines, fix in correction pass
h(3, 387)
blank()
p(None, 391, 392)

# === DRUCKEN (d) ===
h(3, 393)
blank()
p(None, 395, 396, 397)

# === HILFE (h) ===
h(3, 398)
p(None, 399)
blank()

# === ENDE (e) ===
h(3, 401)
blank()
p(None, 403, 404)
blank()
p(None, 406, 407, 408)
blank()

# === HINWEISE (page 87 right col) ===
h(3, 410)
blank()
p(None, 412, 413, 414, 415, 416)
blank()
p(None, 418, 419, 420, 421)
blank()

# === LISTING 3 (page 87, BASIC) ===
raw('        <figure>')
raw('        <pre>')
listing_pre(423, 469)
raw('        </pre>')
raw('            <figcaption>Listing 3. Das Ladeprogramm »LMS« geben Sie bitte mit dem Checksummer V 3 (Ausgabe 3/86, Seite 55) ein.</figcaption>')
raw('        </figure>')
blank()

# === LISTING 4 (page 87, hex dump) ===
raw('        <figure>')
raw('        <pre>')
listing_pre(473, 541)
raw('        </pre>')
raw('            <figcaption>Listing 4. Das Maschinenprogramm »LMS.PHA« bitte mit dem MSE eingeben.</figcaption>')
raw('        </figure>')
blank()

# === PAGE 88 PROSE: Hinweise continuation (left col) ===
p(None, 550, 551, 552, 553)
blank()

# Code example
raw('        <pre>')
raw(e(L[555 - 1]))
raw('        </pre>')
blank()
p(None, 557)
blank()
p(None, 559, 561)
blank()

# Code example
raw('        <pre>')
raw(e(L[563 - 1]))
raw(e(L[565 - 1]))
raw('        </pre>')
blank()
p(None, 567)
blank()

p(None, 569, 570, 571, 572, 573, 574)
blank()
p(None, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585)
blank()

# === LMS LIMITATIONS (page 88, split across columns) ===
p(None, 587, 588, 589, 590)
p(None, 592)
# Item 3 + author credit on same line (L637-638), separation needed in correction
p(None, 637, 638)
blank()

# === PROGRAMMBESCHREIBUNG (page 88 right col) ===
h(2, 598)
blank()
p(None, 600, 601, 602, 603, 604, 605, 606, 607, 608)
blank()
p(None, 610, 611, 612, 613, 614, 615, 616, 617, 618)
blank()
p(None, 620, 621, 622, 623)
blank()
p(None, 625, 626, 627, 628)
blank()
p(None, 630, 631, 632)
blank()
p(None, 634, 635)
blank()

# === LISTING 5 (pages 88-89, BASIC, two-column merged by Tesseract) ===
raw('        <figure>')
raw('        <pre>')
# Page 88 portion
listing_pre(639, 683)
# Page 89 portion
listing_pre(691, 890)
raw('        </pre>')
raw('            <figcaption>Listing 5. Das Auswertungsprogramm »LMS.BAS« (Schluß)</figcaption>')
raw('        </figure>')

# ============================================================
# OUTPUT
# ============================================================
body = "\n".join(out)
print(body)
