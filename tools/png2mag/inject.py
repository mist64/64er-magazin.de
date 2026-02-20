#!/usr/bin/env python3
"""
Generic body injector for article HTML shells.

Usage:
    python3 tools/inject.py <html_file> <body_file>

Examples:
    python3 tools/inject.py "issues/8604/142 Kennen Sie Ihren C 64_ (Teil 2).html" _work/142_body.html
    python3 tools/inject.py "issues/8604/63 Grafik Druckprogramm zu Database.html" _work/63_body.html

The HTML shell must contain the placeholder line:
    <!-- BODY WILL BE MECHANICALLY IMPORTED -->

The body file should contain all article content including author/source blocks
in the order they appear on the page. The import script is responsible for
placing <address class="author"> and <p class="source"> in the correct order.
"""

import sys

PLACEHOLDER = "        <!-- BODY WILL BE MECHANICALLY IMPORTED -->"

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    html_file = sys.argv[1]
    body_file = sys.argv[2]

    with open(html_file, "r") as f:
        shell = f.read()

    with open(body_file, "r") as f:
        body = f.read().rstrip("\n")

    if PLACEHOLDER not in shell:
        print(f"ERROR: Placeholder not found in {html_file}", file=sys.stderr)
        print(f"Expected: {PLACEHOLDER!r}", file=sys.stderr)
        sys.exit(1)

    result = shell.replace(PLACEHOLDER, body)

    with open(html_file, "w") as f:
        f.write(result)

    line_count = body.count("\n") + 1
    print(f"Injected body ({line_count} lines) into {html_file}")

if __name__ == "__main__":
    main()
