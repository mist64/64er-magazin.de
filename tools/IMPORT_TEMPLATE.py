#!/usr/bin/env python3
"""
Mechanical import script for article NNN "TITLE".

Reads from _work/NNN_slug_ocr_raw.txt and places lines
in reading order. All OCR errors are preserved verbatim.

Reading order reconstruction based on multi-column layout analysis of pages X-Y.

Usage:
    python3 _work/NNN_import.py > _work/NNN_body.html
"""

import html

RAW = "_work/NNN_slug_ocr_raw.txt"

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

def basic_listing(start, end):
    """Emit a BASIC listing as a table with class 'plain right0'.
    Lines are tab-separated: line_number<TAB>code."""
    raw('        <table class="plain right0">')
    for i in range(start, end + 1):
        line = L[i - 1]
        parts = line.split("\t", 1)
        if len(parts) == 2:
            raw(f"            <tr><td>{e(parts[0])}</td><td>{e(parts[1])}</td></tr>")
        else:
            raw(f'            <tr><td colspan="2">{e(line)}</td></tr>')
    raw("        </table>")

def tsv_table(header_line, data_start, data_end, css_class="plain pre"):
    """Emit a tab-separated table (e.g. assembler listing).
    header_line: 1-indexed line with tab-separated headers.
    data_start..data_end: 1-indexed range of data rows."""
    cols_h = L[header_line - 1].split("\t")
    ncols = len(cols_h)
    raw(f'        <table class="{css_class}">')
    raw("            <tr>")
    for c in cols_h:
        raw(f"                <th>{e(c)}</th>")
    raw("            </tr>")
    for i in range(data_start, data_end + 1):
        cols = L[i - 1].split("\t")
        while len(cols) < ncols:
            cols.append("")
        raw("            <tr>")
        for c in cols:
            raw(f"                <td>{e(c)}</td>")
        raw("            </tr>")
    raw("        </table>")

# ============================================================
# ARTICLE-SPECIFIC LINE MAPPING BELOW
# Replace NNN/TITLE/slug above and fill in the mapping.
# ============================================================

# === TITLE AND INTRO ===
# h(1, LINE_NUM)          # title line
# p("intro", LINE_NUM)    # intro/lead line
# blank()

# === PAGE NNN BODY ===
# p(None, LINE_NUM)                  # single-line paragraph
# p(None, LINE_A, LINE_B)            # multi-line merge (reading order)
# h(2, LINE_NUM)                     # subheading
# blank()

# === FIGURES ===
# raw("        <figure>")
# raw('            <img src="NNN-1.png" alt="">')
# raw("            <figcaption>Bild 1. CAPTION</figcaption>")
# raw("        </figure>")
# blank()

# === LISTINGS ===
# raw("        <figure>")
# tsv_table(HEADER_LINE, DATA_START, DATA_END)  # assembler
# basic_listing(START, END)                       # BASIC
# raw(f"            <figcaption>{e(L[CAPTION_LINE - 1])}</figcaption>")
# raw("        </figure>")
# blank()

# ============================================================
# OUTPUT
# ============================================================
body = "\n".join(out)
print(body)
