#!/usr/bin/env python3
"""
Inject the mechanically generated body into the HTML shell.
Replaces the placeholder comment with body content from 142_body.html.
"""

HTML = "142 Kennen Sie Ihren C 64_ (Teil 2).html"
BODY = "_work/142_body.html"
PLACEHOLDER = "        <!-- BODY WILL BE MECHANICALLY IMPORTED -->"
CLOSING = "    </article>"
ADDRESS = '\n        <address class="author">(Logo/aw)</address>'

with open(HTML, "r") as f:
    shell = f.read()

with open(BODY, "r") as f:
    body = f.read().rstrip("\n")

if PLACEHOLDER not in shell:
    raise RuntimeError("Placeholder not found in shell")

result = shell.replace(PLACEHOLDER, body + ADDRESS)

with open(HTML, "w") as f:
    f.write(result)

print(f"Injected body ({body.count(chr(10))+1} lines) into {HTML}")
