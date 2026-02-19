#!/usr/bin/env python3
"""
Mechanical import script for article 027 "Die Sinne eines Computers".

Reads from _work/027_die_sinne_eines_computers_ocr_raw.txt and places lines
in reading order. All OCR errors are preserved verbatim.

Reading order reconstruction based on multi-column layout analysis of pages 27-29.

Usage:
    python3 _work/027_import.py > _work/027_body.html
"""

import html

RAW = "_work/027_die_sinne_eines_computers_ocr_raw.txt"

with open(RAW, "r") as f:
    lines = f.readlines()

# Strip trailing newlines, keep content
L = [l.rstrip("\n") for l in lines]

def e(text):
    """HTML-escape text."""
    return html.escape(text)

# Build output lines
out = []

def p(cls, *line_nums):
    """Emit a <p> by concatenating raw lines (1-indexed). Merges with space.
    cls=None for plain <p>, or a string like "intro", "noindent"."""
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
    """Emit a blank line (for readability in output)."""
    out.append("")

def raw(text):
    """Emit raw HTML text (for tables, figures, etc.)."""
    out.append(text)

# ============================================================
# ARTICLE-SPECIFIC LINE MAPPING
# Pages 27-29, two-column layout with 13 Bild figures
# ============================================================

# === INTRO (subtitle below title, right column p.27) ===
p("intro", 90, 92, 94, 95)
blank()

# === PAGE 27 BODY ===

# Para 1 (drop cap C): "Computer können hören..."
p(None, 4, 6, 8, 9, 10, 11, 12, 13, 14)
blank()

# Para 2: "Sensoren sind Bauelemente..."
p(None, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33)
blank()

# Para 3: "Die einfachsten Sensoren..."
p(None, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47)
blank()

# === h2: Potentiometer ===
h(2, 49)
blank()

# Para 4: "Auf einer Bahn..." (mentions Bild 1)
p(None, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66)
blank()

# Bild 1 figure
raw("        <figure>")
raw('            <img src="27-1.png" alt="">')
raw("            <figcaption>Bild 1. Ein Schiebepoti hat eine Drahtbahn, auf der ein Schleifer hin- und hergeschoben werden kann.</figcaption>")
raw("        </figure>")
blank()

# Para 5: "Wenn Elektronik Ihr Hobby..."
p(None, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80)
blank()

# Para 6: "Durch Widerstandsänderungen..." (long, spans column break; mentions Bild 2)
p(None, 82, 83, 103, 104, 105, 106, 107, 108, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 121, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141)
blank()

# Bild 2 figure (caption not fully in OCR — from scan)
raw("        <figure>")
raw('            <img src="27-2.png" alt="">')
raw("            <figcaption>Bild 2. Schaltsymbol der temperaturabhängigen Widerstände</figcaption>")
raw("        </figure>")
blank()

# Para 7: "Es gibt zwei verschiedene..."
p(None, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166)
blank()

# Para 8: "daß Temperaturänderungen..."
p(None, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185)
blank()

# === h2: Materialprüfung ===
h(2, 187)
blank()

# Para 9: "In der Materialprüfung..." (long; mentions Bild 3, Bild 4)
# NOTE: OCR gap between lines 197-199 — missing "(DMS)..." text; fix in correction pass
p(None, 189, 190, 191, 192, 193, 194, 195, 196, 197, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 234, 235)
blank()

# Bild 3 figure (caption not in OCR — placeholder from scan)
raw("        <figure>")
raw('            <img src="27-3.png" alt="">')
raw("            <figcaption>Bild 3. Druckschaft und Biegestab: nicht alle Dehnungsmeßstreifen sind gleich</figcaption>")
raw("        </figure>")
blank()

# Bild 4 figure
raw("        <figure>")
raw('            <img src="27-4.png" alt="">')
p_cap = " ".join([e(L[n-1]) for n in [365, 366, 367]])
raw(f"            <figcaption>{p_cap}</figcaption>")
raw("        </figure>")
blank()

# Para 10: "DMS finden sich auch..." (spans page break; mentions Bild 5)
p(None, 237, 238, 240, 241, 245, 246, 247, 248)
blank()

# Bild 5 figure
raw("        <figure>")
raw('            <img src="27-5.png" alt="">')
raw("            <figcaption>Bild 5. Auch in Kraftmeßdosen sind Dehnungsmeßstreifen zu finden</figcaption>")
raw("        </figure>")
blank()

# === PAGE 28 BODY ===

# Para 11: "Es gibt noch eine andere Art..." (mentions Bild 6)
p(None, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273)
blank()

# Bild 6 figure
raw("        <figure>")
raw('            <img src="27-6.png" alt="">')
p_cap6 = " ".join([e(L[n-1]) for n in [426, 427]])
raw(f"            <figcaption>{p_cap6}</figcaption>")
raw("        </figure>")
blank()

# Para 12: "Auch kapazitive Füllhöhenmesser..." (mentions Bild 7)
p(None, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306)
blank()

# Bild 7 figure
raw("        <figure>")
raw('            <img src="27-7.png" alt="">')
p_cap7 = " ".join([e(L[n-1]) for n in [369, 370]])
raw(f"            <figcaption>{p_cap7}</figcaption>")
raw("        </figure>")
blank()

# === h2: Mengenmessung ===
h(2, 308)
blank()

# Para 13: "Hat ihr Wagen eine L-Jetronic..."
p(None, 310, 311, 312, 313, 314, 315, 316, 317, 318)
blank()

# Para 14: "Durch Anblasen mit Luft..." (mentions Bild 8)
p(None, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347)
blank()

# Bild 8 figure
raw("        <figure>")
raw('            <img src="27-8.png" alt="">')
p_cap8 = " ".join([e(L[n-1]) for n in [490, 491, 492, 493, 494]])
raw(f"            <figcaption>{p_cap8}</figcaption>")
raw("        </figure>")
blank()

# Para 15: "Die Hitzdrahtsonde kann..."
p(None, 349, 350, 351, 352, 353)
blank()

# Para 16: "Sehr genau können..." (mentions Bild 9)
p(None, 355, 356, 357, 358, 359, 360, 361, 362, 363, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395)
blank()

# Bild 9 figure
raw("        <figure>")
raw('            <img src="27-9.png" alt="">')
p_cap9 = " ".join([e(L[n-1]) for n in [549, 550]])
raw(f"            <figcaption>{p_cap9}</figcaption>")
raw("        </figure>")
blank()

# === h2: Längenmessung ===
h(2, 397)
blank()

# Para 17: "Passive Sensoren funktionieren..." (mentions Bilder 10 und 11)
p(None, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460)
blank()

# Bild 10 figure
raw("        <figure>")
raw('            <img src="27-10.png" alt="">')
p_cap10 = " ".join([e(L[n-1]) for n in [498, 499, 500, 502, 503, 504, 505]])
raw(f"            <figcaption>{p_cap10}</figcaption>")
raw("        </figure>")
blank()

# Bild 11 figure
raw("        <figure>")
raw('            <img src="27-11.png" alt="">')
p_cap11 = " ".join([e(L[n-1]) for n in [511, 512]])
raw(f"            <figcaption>{p_cap11}</figcaption>")
raw("        </figure>")
blank()

# === h2: Aktive Thermofühler (two-line heading in OCR: lines 462-463) ===
raw("        <h2>Aktive Thermofühler</h2>")
blank()

# Para 18: "Metallthermometer, Heiß-..." (spans page break; mentions Bilder 12, 13)
p(None, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536)
blank()

# Bild 12 figure
raw("        <figure>")
raw('            <img src="27-12.png" alt="">')
p_cap12 = " ".join([e(L[n-1]) for n in [556, 557]])
raw(f"            <figcaption>{p_cap12}</figcaption>")
raw("        </figure>")
blank()

# Bild 13 figure
raw("        <figure>")
raw('            <img src="27-13.png" alt="">')
p_cap13 = " ".join([e(L[n-1]) for n in [564, 565, 566]])
raw(f"            <figcaption>{p_cap13}</figcaption>")
raw("        </figure>")
blank()

# === h2: Strom durch Druck ===
h(2, 538)
blank()

# Para 19: "Kräfte können nicht nur..." (spans across caption block)
p(None, 540, 541, 542, 543, 568, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582)
blank()

# Para 20: "Bestimmt kennen Sie..."
p(None, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604)
blank()

# Para 21: "In Sensoren werden..."
p(None, 606, 607, 608, 609, 610, 611, 612)
blank()

# Para 22: "Mit piezoelektrischen..."
p(None, 614, 615, 616, 617, 618, 619, 620, 621)
blank()

# === h2: Geschwindigkeits- und Drehzahlmessung (three-line heading) ===
raw("        <h2>Geschwindigkeits- und Drehzahlmessung</h2>")
blank()

# Para 23: "Geschwindigkeiten und Drehzahlen..."
p(None, 626, 627, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639)
blank()

# Para 24: "Beschleunigungen können..."
p(None, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652)
blank()

# Para 25: "Was mit einem Heimcomputer..." (light sensors)
p(None, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706)

# ============================================================
# OUTPUT
# ============================================================
body = "\n".join(out)
print(body)
