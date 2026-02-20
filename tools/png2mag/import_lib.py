#!/usr/bin/env python3
"""
Shared utilities for mechanical article import scripts.

Provides reusable HTML building, line loading, and output handling
for converting OCR text into article body HTML.

Usage in import scripts:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
    from import_lib import HtmlBuilder, load_raw_text

    L = load_raw_text("_work/NNN_slug_ocr_raw.txt")
    b = HtmlBuilder(L)

    b.h(1, LINE)
    b.p("intro", LINE)
    b.blank()
    b.p(None, LINE_A, LINE_B)
    b.figure("NNN-1.png", "Bild 1. Caption text")

    print(b.build())
"""

import html


def load_raw_text(filepath):
    """Load text file, strip trailing newlines, return list of lines (0-indexed)."""
    with open(filepath, "r") as f:
        lines = f.readlines()
    return [l.rstrip("\n") for l in lines]


def e(text):
    """HTML-escape text."""
    return html.escape(text)


class HtmlBuilder:
    """Accumulates HTML body lines with helpers for common article elements.

    Lines in L are 0-indexed internally but all public methods accept
    1-indexed line numbers to match the annotated OCR output.
    """

    def __init__(self, L=None):
        self.L = L or []
        self.out = []

    def p(self, cls, *line_nums):
        """Emit <p> by merging raw lines (1-indexed) with space.
        cls=None for plain <p>, or a string like "intro", "noindent"."""
        parts = [e(self.L[n - 1]) for n in line_nums]
        text = " ".join(parts)
        if cls:
            self.out.append(f'        <p class="{cls}">{text}</p>')
        else:
            self.out.append(f"        <p>{text}</p>")

    def h(self, level, *line_nums):
        """Emit <hN> from one or more raw lines (1-indexed), merged with space."""
        parts = [e(self.L[n - 1]) for n in line_nums]
        text = " ".join(parts)
        self.out.append(f"        <h{level}>{text}</h{level}>")

    def blank(self):
        """Emit blank line for readability in output."""
        self.out.append("")

    def raw(self, text):
        """Emit raw HTML text (no escaping)."""
        self.out.append(text)

    def figure(self, src, caption=None, alt=""):
        """Emit <figure> with <img> and optional <figcaption>."""
        self.raw("        <figure>")
        self.raw(f'            <img src="{src}" alt="{alt}">')
        if caption:
            self.raw(f"            <figcaption>{e(caption)}</figcaption>")
        self.raw("        </figure>")
        self.blank()

    def author(self, initials):
        """Emit <address class="author">."""
        self.raw(f'        <address class="author">({initials})</address>')

    def source(self, *line_nums):
        """Emit <p class="source"> from raw lines."""
        parts = [e(self.L[n - 1]) for n in line_nums]
        text = " ".join(parts)
        self.raw(f'        <p class="source">{text}</p>')

    def basic_listing(self, start, end):
        """Emit a BASIC listing as a table with class 'plain right0'.
        Lines are tab-separated: line_number<TAB>code."""
        self.raw('        <table class="plain right0">')
        for i in range(start, end + 1):
            line = self.L[i - 1]
            parts = line.split("\t", 1)
            if len(parts) == 2:
                self.raw(f"            <tr><td>{e(parts[0])}</td><td>{e(parts[1])}</td></tr>")
            else:
                self.raw(f'            <tr><td colspan="2">{e(line)}</td></tr>')
        self.raw("        </table>")

    def tsv_table(self, header_line, data_start, data_end, css_class="plain pre"):
        """Emit a tab-separated table with headers and data rows (1-indexed)."""
        cols_h = self.L[header_line - 1].split("\t")
        ncols = len(cols_h)
        self.raw(f'        <table class="{css_class}">')
        self.raw("            <tr>")
        for c in cols_h:
            self.raw(f"                <th>{e(c)}</th>")
        self.raw("            </tr>")
        for i in range(data_start, data_end + 1):
            cols = self.L[i - 1].split("\t")
            while len(cols) < ncols:
                cols.append("")
            self.raw("            <tr>")
            for c in cols:
                self.raw(f"                <td>{e(c)}</td>")
            self.raw("            </tr>")
        self.raw("        </table>")

    def build(self):
        """Return assembled HTML body as a single string."""
        return "\n".join(self.out)
