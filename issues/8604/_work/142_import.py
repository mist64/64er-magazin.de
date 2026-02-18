#!/usr/bin/env python3
"""
Mechanical import script for article 142 "Kennen Sie Ihren C 64? (Teil II)".

Reads from _work/142_kennen_sie_ihren_c64_teil2_ocr_raw.txt and places lines
in reading order. All OCR errors are preserved verbatim.

Reading order reconstruction based on multi-column layout analysis of pages 142-144, 177.
"""

import html

RAW = "_work/142_kennen_sie_ihren_c64_teil2_ocr_raw.txt"

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
    """Emit a <p> by concatenating raw lines (1-indexed). Merges with space."""
    parts = []
    for n in line_nums:
        parts.append(e(L[n - 1]))
    text = " ".join(parts)
    if cls:
        out.append(f'        <p class="{cls}">{text}</p>')
    else:
        out.append(f"        <p>{text}</p>")

def raw(text):
    out.append(text)

# === TITLE AND INTRO ===
# Line 35: title (OCR: "Kennen Sie Ihren C 64? peil II)")
# Line 36: intro
raw(f"        <h1>{e(L[35 - 1])}</h1>")
raw(f'        <p class="intro">{e(L[36 - 1])}</p>')
raw("")

# === PAGE 142 BODY ===
# Lines 3+33: first paragraph (split across Bild 1)
p(None, 3, 33)
raw("")

# Lines 34+37+38: second paragraph (spans columns)
p(None, 34, 37, 38)
raw("")

# Line 39: CPU as computer system
p(None, 39)
raw("")

# Line 40: Basic error handling
p(None, 40)
raw("")

# Line 41: Basic commands slow
p(None, 41)
raw("")

# Line 42: h2 heading "Der eigentliche Chef"
raw(f"        <h2>{e(L[42 - 1])}</h2>")
raw("")

# Line 43: IRQ paragraph
p(None, 43)
raw("")

# Lines 44+49: GDP/DMA paragraph (spans page 142→143)
p(None, 44, 49)
raw("")

# === PAGE 143 LEFT COLUMN ===
# Line 50: AEC paragraph
p(None, 50)
raw("")

# Line 51: Adreßmanager
p(None, 51)
raw("")

# Lines 62+52: GDP halt paragraph (left col bottom → right col top)
p(None, 62, 52)
raw("")

# === PAGE 143 RIGHT COLUMN ===
# Line 53: Systemtakt paragraph
p(None, 53)
raw("")

# Line 58: "Um verfolgen zu können..."
p(None, 58)
raw("")

# Lines 59+60: "Nehmen wir einmal an..." (continues across column)
p(None, 59, 60)
raw("")

# Lines 61+79: "Diese Geräte..." (spans page 143→144)
p(None, 61, 79)
raw("")

# === PAGE 144 LEFT COLUMN ===
# Line 80: "Um auf unser Problem..."
p(None, 80)
raw("")

# Line 81: "Aber so unglaublich..."
p(None, 81)
raw("")

# Line 82: "Der Busmonitor..."
p(None, 82)
raw("")

# Lines 83+119: "Natürlich belegen..." + "später mehr."
p(None, 83, 119)
raw("")

# Lines 120+84+85: "Der Monitor läßt sich..." paragraph (ends with author credit)
p(None, 120, 84, 85)
raw("")

# === BILD 2 SECTION (page 144) ===
# Line 86: Bild 2 description text
p(None, 86)
raw("")

# Lines 87-91: numbered DMA timing items
for i in range(87, 92):
    p(None, i)
raw("")

# Line 92: DMA explanation paragraph
p(None, 92)
raw("")

# === ASSEMBLER LISTING (Bild 3 top part) ===
# Line 94: table header
# Lines 95-108: listing rows
raw("        <figure>")
raw('            <table class="plain pre">')
raw("                <tr>")
raw(f"                    <th>{e(L[94 - 1].split(chr(9))[0])}</th>")
raw(f"                    <th>{e(L[94 - 1].split(chr(9))[1])}</th>")
raw(f"                    <th>{e(L[94 - 1].split(chr(9))[2])}</th>")
raw(f"                    <th>{e(L[94 - 1].split(chr(9))[3])}</th>")
raw(f"                    <th>{e(L[94 - 1].split(chr(9))[4])}</th>")
raw("                </tr>")
for i in range(95, 109):
    cols = L[i - 1].split("\t")
    while len(cols) < 5:
        cols.append("")
    raw("                <tr>")
    for c in cols:
        raw(f"                    <td>{e(c)}</td>")
    raw("                </tr>")
raw("            </table>")
raw("")

# === BASIC LISTING (Bild 3 bottom part) ===
raw('            <table class="plain right0">')
for i in range(109, 118):
    line = L[i - 1]
    # Split on first tab to get line number and rest
    parts = line.split("\t", 1)
    if len(parts) == 2:
        raw(f"                <tr><td>{e(parts[0])}</td><td>{e(parts[1])}</td></tr>")
    else:
        raw(f"                <tr><td colspan=\"2\">{e(line)}</td></tr>")
raw("            </table>")

# Line 118: Bild 3 caption
raw(f"            <figcaption>{e(L[118 - 1])}</figcaption>")
raw("        </figure>")
raw("")

# === BEISPIEL IN BASIC (page 144 right column) ===
# Line 121: h2 heading
raw(f"        <h2>{e(L[121 - 1])}</h2>")
raw("")

# Line 122: explanation intro
p(None, 122)
raw("")

# Lines 123-128: Zeile descriptions (each its own paragraph)
for i in range(123, 129):
    p(None, i)
    raw("")

# Line 129: combined paragraph about lines 20-24
p(None, 129)
raw("")

# === BEISPIEL IN ASSEMBLER ===
# Line 130: h2 heading
raw(f"        <h2>{e(L[130 - 1])}</h2>")
raw("")

# Line 131: intro paragraph
p(None, 131)
raw("")

# Lines 132+137: Zeile 01 (spans page 144→177, line 137 starts with noise)
# Line 137 starts with "Fortsetzung von Seite 144 STOP/RESTORE ausgelöst."
# The "STOP/RESTORE ausgelöst." continues from line 132's "die Tasten"
# We include the full line 137 verbatim (noise will be cleaned in phase 6)
p(None, 132, 137)
raw("")

# === PAGE 177 CONTINUATION ===
# Line 138: Zeile 03
p(None, 138)
raw("")

# Line 139: Zeile 03 continued (Adreß-Zähler paragraph)
p(None, 139)
raw("")

# Line 140: Zeile 04
p(None, 140)
raw("")

# Line 141: Zeile 05
p(None, 141)
raw("")

# Line 142: Zeile 06
p(None, 142)
raw("")

# Line 143: Zeile 07
p(None, 143)
raw("")

# Line 144: Zeile 08
p(None, 144)
raw("")

# Lines 145+162: Zeile 09 (split by Markt&Technik ad)
p(None, 145, 162)
raw("")

# Line 163: Zeile 10
p(None, 163)
raw("")

# Line 164: Zeile 11+12 (combined in OCR)
p(None, 164)
raw("")

# Line 178: Zeile 13
p(None, 178)
raw("")

# Line 179: Timing comparison paragraph
p(None, 179)
raw("")

# Line 180: Final sentence
p(None, 180)

# Assemble the full body
body = "\n".join(out)
print(body)
