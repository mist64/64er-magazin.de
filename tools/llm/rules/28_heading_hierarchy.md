# 28 — Heading hierarchy (`<h1>` / `<h2>` / `<h3>`)

**Goal:** every article's heading hierarchy matches what the print
typesets. Don't promote / demote on structure alone — judge against
the print's typographic weight.

## What the print actually shows

64'er print uses (roughly) three heading weights inside an article:

1. **Article title** (h1) — huge banner, usually styled with a
   coloured tint, sometimes spanning columns.
2. **Major section** (h2) — large bold heading. Often appears as
   a banner across one or more columns, with clear whitespace
   above. Articles like `133 Computer-Simulation` (`Die Eulersche
   Methode`) or `49 Variosystem` (`Bedienungsanleitung`,
   `Eingabehinweise`) use this weight.
3. **Sub-heading inside a section** (h3) — smaller bold, often
   inline with the column flow. The print may use h3 throughout
   an article without ever using h2 — and that's fine; it's the
   article's own design choice, not a structural defect.

## The promotion trap (don't do this)

❌ **"This article has no `<h2>`, so the top-level `<h3>` blocks
must be wrong — promote to `<h2>`."**

This heuristic looks tempting because "orphan h3 with no h2 parent"
appears structurally odd. But many 8607 articles intentionally use
only h3 subheadings:

- `174 Computer-Knobeleien (3)`: `Remis-Positionen` / `Kegeln mit
  dem Computer` / `Tac Tix mit Taktik` are sub-sections of equal
  weight — print sets them all in h3-sized bold, never h2-banner
  size. They stay h3.
- `166 Tips und Tricks zu Superbase (Teil 4)`: `Die Centronics-
  Schnittstelle` / `Plotter VC 1520` are inline sub-sections
  within the larger Tips & Tricks column. h3.
- `168 Tips und Tricks zu Vizawrite (Teil 7)`: `Griechisch für
  Vizawrite mit dem SG-10` — same.

The audit in commit `b94e5876b` promoted these to h2 on the
"orphan h3" heuristic, and the user manually reverted them in
`70e6a5905`. The promotion was wrong because the print never used
h2-banner sizing for them.

## The correct test

To decide if an `<h3>` should be `<h2>` (or vice versa), ask:

1. **Is the print's font weight identical to other h2s in the
   issue?** Render the relevant page at 600 dpi and compare to a
   known-h2 heading from a nearby article. If the heading uses
   the same size, weight, leading, whitespace allowance, then
   `<h2>`. If it's smaller / inline / lighter, then `<h3>`.

2. **Does the article structure invite a banner weight?** Some
   articles are short single-topic columns (Tips & Tricks tips,
   Aktuelles items, CP/M-Ecke entries). Those rarely need h2
   banners — print uses inline-flow h3.

3. **Inside an `<aside>`?** Rule 15 says: the first heading inside
   `<aside>` is always `<h3>`, regardless of what it would be at
   article scope. The aside is a callout, so its internal
   hierarchy starts at h3.

Never promote on (1) alone. Never demote on (1) alone. (1) without
(2) is a structure-only heuristic and is exactly the trap above.

## Briefing for the sub-agent

For every article in `issues/<YYMM>/*.html`:

1. List heading hierarchy (h1/h2/h3 with line numbers).
2. For each suspicious heading (h3 at top level, h2 inside an
   aside, h2 → h3 mid-article, two adjacent h2 with no body
   between), check the **print scan at 600 dpi**:
   - Crop the heading region.
   - Compare typographic weight against a known-h2 in the same
     issue.
   - Decide promote / demote / leave by the print's weight, NOT
     by structural orphan-ness.
3. Apply only the changes where the print scan supports them.
4. **Default to leave** if uncertain. The "tax" of a slightly
   unconventional hierarchy is much smaller than the tax of
   getting hundreds of headings wrong by over-promoting.

Anti-memory: every decision comes from the scan crop. No "this h3
should be h2 because in modern web design we want section
banners".

## Verification

```bash
dir=issues/<YYMM>

# 1. each article has exactly one h1
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    n = len(re.findall(r'<h1\b', s))
    if n != 1: print(f"  {f}: {n} <h1> (expected 1)")
PY
)" "$dir"

# 2. no h2 inside <aside> (rule 15 violation)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<aside\b[^>]*>(.*?)</aside>', s, re.DOTALL):
        if re.search(r'<h2\b', m.group(1)):
            print(f"  {f}: <h2> inside <aside>")
PY
)" "$dir"
```

## Notes / lessons

- 8607's audit promoted 3 h3→h2 incorrectly (174 Knobeleien × 3,
  166 Superbase × 2) — the user manually reverted. Pattern: the
  audit picked top-level h3s with no h2 in scope and promoted
  them, but the print never used h2-banner weight in those
  articles. Fixed by adding the "compare print weight" test.
- Don't run a heading audit as a single batch action across the
  whole issue. Per-article decisions, scan crops, judgment.
  Bulk-applying any heading-promotion heuristic is risky.
- The reviewer-then-second-reviewer pattern (used in 8607 for the
  Grafik-Modi table) is overkill for headings — but for a hierarchy
  decision in a clearly-tricky article (multi-h2 article like
  Aktuelles or a tutorial with internal sub-sub-sections), a
  second opinion is worth the time.
