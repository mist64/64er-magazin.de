#!/usr/bin/env python3
"""
Generic body injector for article HTML shells.

Usage:
    python3 _work/inject.py <html_file> <body_file> [<address_text>]

Examples:
    python3 _work/inject.py "142 Kennen Sie Ihren C 64_ (Teil 2).html" _work/142_body.html "(Logo/aw)"
    python3 _work/inject.py "63 Grafik Druckprogramm zu Database.html" _work/63_body.html "(Marcus Plewa/kn)"

The HTML shell must contain the placeholder line:
    <!-- BODY WILL BE MECHANICALLY IMPORTED -->

If <address_text> is given, an <address class="author"> tag is appended after the body.
"""

import sys

PLACEHOLDER = "        <!-- BODY WILL BE MECHANICALLY IMPORTED -->"

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    html_file = sys.argv[1]
    body_file = sys.argv[2]
    address_text = sys.argv[3] if len(sys.argv) > 3 else None

    with open(html_file, "r") as f:
        shell = f.read()

    with open(body_file, "r") as f:
        body = f.read().rstrip("\n")

    if PLACEHOLDER not in shell:
        print(f"ERROR: Placeholder not found in {html_file}", file=sys.stderr)
        print(f"Expected: {PLACEHOLDER!r}", file=sys.stderr)
        sys.exit(1)

    replacement = body
    if address_text:
        replacement += f'\n        <address class="author">{address_text}</address>'

    result = shell.replace(PLACEHOLDER, replacement)

    with open(html_file, "w") as f:
        f.write(result)

    line_count = body.count("\n") + 1
    print(f"Injected body ({line_count} lines) into {html_file}")

if __name__ == "__main__":
    main()
