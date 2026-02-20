#!/usr/bin/env python3
"""
Soft hyphen report — lists all soft hyphens in an HTML file with context.

Usage:
    python3 tools/png2mag/soft_hyphen_report.py <html_file>

For each soft hyphen found, prints:
  - Line number and position
  - Surrounding context (20 chars before/after)
  - The two word halves joined at the soft hyphen

The agent uses this report to decide for each occurrence:
  - REMOVE: the halves form one word (e.g., Gene­rator → Generator)
  - REPLACE with '-': real compound hyphen (e.g., Basic­Editor → Basic-Editor)

After resolving all soft hyphens, run again to confirm count is zero.
"""

import sys
import re

SHY = "\u00AD"

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    html_file = sys.argv[1]

    with open(html_file, "r") as f:
        lines = f.readlines()

    total = 0
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip("\n")
        pos = 0
        while True:
            idx = line.find(SHY, pos)
            if idx == -1:
                break
            total += 1

            # Extract surrounding context
            ctx_before = line[max(0, idx - 20):idx]
            ctx_after = line[idx + 1:idx + 21]

            # Extract the two word halves around the soft hyphen
            # Walk backwards from idx to find start of left half
            left_start = idx
            while left_start > 0 and line[left_start - 1].isalnum():
                left_start -= 1
            left_half = line[left_start:idx]

            # Walk forwards from idx+1 to find end of right half
            right_end = idx + 1
            while right_end < len(line) and line[right_end].isalnum():
                right_end += 1
            right_half = line[idx + 1:right_end]

            joined = left_half + right_half
            with_hyphen = left_half + "-" + right_half

            print(f"  Line {line_num}, col {idx + 1}:")
            print(f"    context: ...{ctx_before}|{ctx_after}...")
            print(f"    remove → {joined}")
            print(f"    hyphen → {with_hyphen}")
            print()

            pos = idx + 1

    if total == 0:
        print(f"PASS: No soft hyphens found in {html_file}")
    else:
        print(f"TOTAL: {total} soft hyphen(s) in {html_file}")

    sys.exit(0 if total == 0 else 1)

if __name__ == "__main__":
    main()
