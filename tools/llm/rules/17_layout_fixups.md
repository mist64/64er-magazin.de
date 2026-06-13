# 17 — Fix line breaks, lists, indentation, inline callouts

**Goal:** resolve the mechanical formatting TODO markers the OCR/import
pipeline leaves behind: `<p>TODO PRE</p>`, `<p>TODO INDENTATION</p>`,
`<p>TODO INDENTED</p>`, `<p>TODO ASIDE</p>` (non-bio), `<p>TODO
BOX</p>`, plus general line-break / empty-paragraph / list-marker
cleanup.

This rule explicitly **excludes** content-reconstruction TODO markers:
`TODO FORMULA` (math markup is editorial), `TODO ALL BOXES LIKE
BELOW` (needs fresh OCR of box content), and content placeholders
like `<p>TODO two boxes with text</p>`. Those belong to a separate
editorial pass.

It also excludes the author-bio `<aside>` work — that is rule 15.
This rule only handles non-bio asides: methodology, contest, feature
list, warning callouts.

## Briefing for the sub-agent

The sub-agent must:

1. Render scans at 300 dpi if not already done: `pdftoppm -r 300
   issues/<YYMM>/64er_19XX-XX.pdf /tmp/64er_<YYMM>_pages_300/p -png`.
2. Walk every `<p>TODO …</p>` marker in `issues/<YYMM>/*.html`:

   | Marker | Action |
   |---|---|
   | `TODO PRE` | Look at the following `<p>…<br>…</p>` block. If the print shows monospace code, fold into `<pre>…</pre>`. If the print shows a real numbered/bulleted list, convert to `<ol>`/`<ul>` instead (and delete the marker). |
   | `TODO INDENTATION` / `TODO INDENTED` | Look at the print indentation. If code → `<pre>`. If prose with visual indent for nested enumeration → `&nbsp;`-prefixed `<br>` inside `<p>`. If real nested list → nested `<ul>`/`<ol>`. |
   | `TODO ASIDE` (non-bio) | Wrap the following heading + paragraphs + closing `<address>` in `<aside>`. Delete the marker. Verify the section is NOT an author bio (that's rule 15). |
   | `TODO BOX` | Same as TODO ASIDE if the print shows a boxed callout. If the print shows indented monospace code with no box border, use `<pre>` instead. |
   | `TODO FORMULA` / `TODO FORMULAS` | **SKIP** — editorial (math markup decision). Report unfilled. |
   | `TODO ALL BOXES LIKE BELOW` | **SKIP** content reconstruction — fresh OCR of multiple boxes is out of scope. |
   | `TODO two boxes with text` (or similar content stubs) | **SKIP** content reconstruction. |

3. Light general formatting sweep:
   - Delete `<p>` paragraphs containing only `&nbsp;` or only
     whitespace.
   - Drop a trailing `<br>` immediately before `</p>`.
   - Convert prose-looking enumeration to `<ul>` / `<ol>` **only**
     when the print shows a real bullet glyph or number prefix on
     each item; if the print is just numbered prose ("1. ein,
     2. zwei, 3. drei" running text), leave it as `<p>`/`<br>`.
4. Beautify touched files (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`). **Verify
   `<pre>` blocks survived** (js-beautify preserves them by default
   but sanity-check after each run).
5. **Do not commit.** Return per-marker action table + general-sweep
   summary + list of explicitly-skipped FORMULA / content markers.

Critical guardrails:
- Anti-memory: code inside `<pre>` must come from the existing HTML
  (the OCR import has the bytes); never retype from print.
- "Only convert to lists when print shows a marker glyph" — applies
  here exactly as it does in the markdown→HTML conversion rules.
  Enumeration-looking prose without a real bullet stays `<p>`/`<br>`.
- Non-bio `<aside>` callouts (methodology, contest, feature list,
  warning) are this rule's territory; author bios are rule 15's.

## Verification

```bash
dir=issues/<YYMM>

# 1. no in-scope TODO marker survives
grep -hoE 'TODO (PRE|INDENTATION|INDENTED|ASIDE|BOX)' "$dir"/*.html \
  | sort -u && echo "  FAIL: in-scope TODO survived"

# 2. expected-skip TODO markers may still exist
grep -lE 'TODO FORMULA|TODO ALL BOXES|TODO two boxes' "$dir"/*.html \
  > /tmp/skipped_files.txt
echo "  expected skipped markers in $(wc -l < /tmp/skipped_files.txt | tr -d ' ') file(s):"
cat /tmp/skipped_files.txt

# 3. <pre> well-formed
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<pre\b', s)); c = len(re.findall(r'</pre>', s))
    if o != c: print(f"  pre mismatch in {f}: open={o} close={c}")
PY
)" "$dir"

# 4. <aside> well-formed
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<aside\b', s)); c = len(re.findall(r'</aside>', s))
    if o != c: print(f"  aside mismatch in {f}: open={o} close={c}")
PY
)" "$dir"
```

## Notes / lessons

- 8607 had 4 TODO PRE markers in `76 Tips & Tricks für Einsteiger`
  alone — when one article has several, eyeball the print first to
  see whether they're code, list, or numbered prose; they need not
  all be the same shape.
- `157 Maintext 64` had a 40-item Funktionsübersicht where the
  print showed real dash bullets — that's a `<ul>`, not a
  `&nbsp;`-flattened paragraph.
- `36 Modem mit Wählautomatik`'s monitor-patch stanzas read as
  TODO BOX but were really indented monospace — `<pre>` was the
  right shape, not `<aside>`.
- The `49 Variosystem` C.A.E. "TODO two boxes with text" and the
  10 `TODO FORMULA` placeholders are explicitly out of scope and
  must be left for an editorial pass — flagging them in the report
  is enough.
