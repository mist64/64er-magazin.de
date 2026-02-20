#!/usr/bin/env python3
"""
Mechanical import script for article 050 "Quizmaster — die Hilfe bei Lernproblemen".

Reads from tmp/050_quizmaster_ocr_raw.txt and places lines
in reading order. All OCR errors are preserved verbatim.

Reading order reconstruction based on multi-column layout analysis of page 050.

Block ordering fixes applied:
- Right column article text: blocks 30 → 34 → 35 (features list then continuation)
  OCR had block 35 (top=1714) interleaved before block 34 (top=2178) due to
  similar vertical position of blocks 30 and 35.
- Lebenslauf right column: blocks 40 → 42 → 43 → 44 (similar interleaving issue)

Usage:
    python3 tmp/050_import.py > tmp/050_body.html
"""

import html

RAW = "tmp/050_quizmaster_ocr_raw.txt"

with open(RAW, "r") as f:
    lines = f.readlines()

# Strip trailing newlines, keep content
L = [l.rstrip("\n") for l in lines]

def e(text):
    """HTML-escape text."""
    return html.escape(text)

# Build output lines
out = []

SHY = "\u00AD"  # soft hyphen — marks line-break hyphen positions

def join_ocr_lines(parts):
    """Join OCR line parts. If a part ends with '-', replace it with a soft
    hyphen and join without space. Otherwise join with a normal space."""
    if not parts:
        return ""
    result = parts[0]
    for part in parts[1:]:
        if not part:
            continue
        if result.endswith("-"):
            result = result[:-1] + SHY + part
        else:
            result = result + " " + part
    return result

def p(cls, *line_nums):
    """Emit a <p> by concatenating raw lines (1-indexed).
    Uses soft-hyphen joining (see WORKFLOW.md).
    cls=None for plain <p>, or a string like "intro", "noindent"."""
    parts = [e(L[n - 1]) for n in line_nums]
    text = join_ocr_lines(parts)
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
# ============================================================
# Raw file line numbers (1-indexed):
#   1: --- PAGE 050 ---
#   2: Anwendung des Mona  (header noise)
#   4-5: title
#   7-8: intro
#   10-26: screenshot OCR garbage (SKIP)
#   28: left figure caption
#   30-45: left column para 1 (drop cap Q missing)
#   46-47: left column para 2 start (ends "Ant-")
#   49-58: left column para 2 continuation (block 24)
#   60: left column para 3 start "Der aktuelle Prozentsat"
#   62-68: left column para 3 continuation (block 32)
#   70: "Lebenslauf" heading
#   72-87: Lebenslauf left column text
#   90: --- [right column] ---
#   92: C 64 (header noise)
#   94-100: right screenshot OCR garbage (SKIP)
#   102: right figure caption
#   104-108: right column - features intro + item 1 (block 30)
#   110-126: right column - continuation after "daß man auch" (block 35, misplaced by OCR)
#   128-129: right column - item 2
#   131-133: right column - item 3
#   135,137,139,141: right column - item 4 (with blank lines between)
#   143,145: right column - item 5
#   146,148: right column - "Dieses Listing beweist wie- der einmal, daß man auch"
#   150: author credit
#   152-167: Lebenslauf right column (block 40)
#   169-187: Lebenslauf right column (block 44, misplaced by OCR)
#   189: Lebenslauf continuation (block 42) "schließen zu können. Da-."
#   191-192: Lebenslauf continuation (block 43) "nach strebe ich ein Studium..."
#   194: "Ausgabe 4/April 1986" (page footer, SKIP)

# === INTRO ===
p("intro", 7, 8)
blank()

# === FIGURES (screenshots, placed after intro as in scan layout) ===
raw("        <figure>")
raw('            <img src="50-1.png" alt="">')
raw(f"            <figcaption>{e(L[28 - 1])}</figcaption>")
raw("        </figure>")
blank()
raw("        <figure>")
raw('            <img src="50-2.png" alt="">')
raw(f"            <figcaption>{e(L[102 - 1])}</figcaption>")
raw("        </figure>")
blank()

# === PARAGRAPH 1 (drop cap Q — OCR has "uizmaster" on line 30) ===
# Build manually to prepend drop cap span
para1_lines = [e(L[n - 1]) for n in range(30, 46)]
para1_text = join_ocr_lines(para1_lines)
out.append(f'        <p><span class="drop-cap">Q</span>{para1_text}</p>')
blank()

# === PARAGRAPH 2 ===
# Lines 46-47 (ends "Ant-") + lines 49-58 (starts "worten")
p(None, 46, 47, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58)
blank()

# === PARAGRAPH 3 ===
# Lines 60 + 62-68 (block break between "Prozentsat" and "an richtigen")
p(None, 60, 62, 63, 64, 65, 66, 67, 68)
blank()

# === PARAGRAPH 4 (features intro) ===
# "Die besonderen Möglichkeiten des Programms sind:"
p(None, 104, 105)
blank()

# === Feature items (em-dash list) ===
# Item 1: "— Einbinden von bis zu zwei frei definierbaren Zeichensätzen,"
p("noindent", 106, 107, 108)
blank()
# Item 2: "— zwei Bewegungssequenzen von je 16 Zeichen,"
p("noindent", 128, 129)
blank()
# Item 3: "— für jede der bis zu 99 Fragen gibt es einen eigenen Bildschirm,"
p("noindent", 131, 132, 133)
blank()
# Item 4: "— Editieren eines Bildschirms wie mit dem Basic-Editor, aber mit einigen Extras,"
# Lines 135, 137, 139, 141 (blank lines 136, 138, 140 between them in OCR)
p("noindent", 135, 137, 139, 141)
blank()
# Item 5: "— alle Funktionen werden durch Menüs gesteuert."
p("noindent", 143, 145)
blank()

# === PARAGRAPH 5 ===
# "Dieses Listing beweist..." (lines 146, 148) continues with block 35 (lines 110-126)
# Correct reading order: line 148 ends "daß man auch" → line 110 starts "mit relativ"
p(None, 146, 148, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126)
blank()

# === AUTHOR CREDIT ===
raw(f'        <address class="author">{e(L[150 - 1])}</address>')
blank()

# === LEBENSLAUF (aside box) ===
raw("        <aside>")
h(2, 70)
blank()
raw("        <figure>")
raw('            <img src="50-0.png" alt="">')
raw("        </figure>")
blank()
# One continuous paragraph across left column (72-87) and right column
# Right column reading order: block 40 (152-167) → block 42 (189) → block 43 (191-192) → block 44 (169-187)
p(None,
  72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87,
  152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167,
  189, 191, 192,
  169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187)
raw("        </aside>")

# ============================================================
# OUTPUT
# ============================================================
body = "\n".join(out)
print(body)
