# 28 — Heading hierarchy (`<h1>` / `<h2>` / `<h3>`)

**Goal:** every article's heading hierarchy matches what the print
typesets. Don't promote / demote on structure alone — judge against
the print's typographic weight.

## DEFAULT: DON'T CHANGE HEADER LEVELS

**The OCR'd / post-step-0 markdown is the source of truth for heading
levels. The default action is to leave heading levels alone. Trust
the input.**

Cross-reference: rule 25 (`heading_case`) carries a parallel
`DEFAULT: don't change heading text` clause. This rule protects
heading *levels*; rule 25 protects heading *text*. Both default to
"trust the input" — keep them in sync.

The "compare print typographic weight" test in the rest of this file
is for **exceptional** cases only — when there's a clear *structural*
reason to suspect the input is wrong (e.g. the hierarchy makes the
article malformed for the generator, or a structural rule like 15
forces a specific level).

Structural overrides that DO apply:

- **Rule 15 (h2 inside aside → h3).** Always demote a top-level
  heading inside `<aside>` to `<h3>`. This is structural, not a
  typographic-weight judgement.

### Anti-pattern — the heading-audit trap

❌ **"This orphan h3 has no h2 parent — promote it."**
❌ **"This h2 has only inline-bold sub-sections — demote it."**

Both are the same trap. Both ignore the input's signal in favour of
a structural-tidiness heuristic. Both have been re-introduced and
manually reverted multiple times during 8607 work.

❌ **Never run a heading-level audit pass.** "Walk every article and
re-check the heading hierarchy" is banned as a workflow. Every bulk
heading-hierarchy "audit" that was attempted during 8607 work
re-introduced exactly the same wrong promotions and had to be
manually reverted file by file. Per-article heading-level changes
are only allowed when there's a specific structural defect in the
*one* article being edited for an unrelated reason.

If you find yourself wanting to "fix up" the heading hierarchy
because it "looks odd": stop. The input is right. Move on.

## What the print actually shows

64'er print uses (roughly) three heading weights inside an article:

1. **Article title** (h1) — huge banner, usually styled with a
   coloured tint, sometimes spanning columns.
2. **Major section** (h2) — large bold heading. Often appears as
   a banner across one or more columns, with clear whitespace
   above. Articles like `133 Computer-Simulation` (`Die Eulersche
   Methode`) use this weight.
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

### History of how this rule reached its current form

The rule started as "compare print weight" and only added "DEFAULT:
don't change" after the third repetition of the same mistake.

- **`b94e5876b`** ("8607: heading hierarchy audit — 20 articles
  fixed"). Walked every 8607 article's hierarchy. 9 of the changes
  were structural (rule-15 h2-in-aside demotions, kept). The other
  ~14 were judgement-call promotions / demotions across 12 articles
  (22, 49, 67, 73, 84, 85, 92, 136, 139, 150, 166, 174). All wrong.
- **`70e6a5905`** ("8607: heading hierarchy + Grafik-Modi review
  fixes"). User manually reverted 166 Superbase Centronics+Plotter,
  168 Vizawrite Griechisch, 174 Knobeleien × 3, plus 150 body
  promotions.
- **`1e9da5ac8`** ("8607: revert FT h3→h2 promotions"). Reverted
  84 Fehlerteufelchen × 6 sub-corrections. Added "FT rubric is
  always h3" to this rule.
- **This commit.** Reverted the remaining b94e5876b judgement
  changes in 22, 49, 67, 73, 85, 92, 136, 139 (and the leftover
  166 FIND-Suche change that hadn't been caught yet). 8 files.
  Rewrote the top of this rule as "DEFAULT: don't change" and
  banned the heading-audit pass workflow outright.

The lesson is: every time the rule was framed as "compare print
weight to decide", a sub-agent picking up the rule re-derived the
"orphan h3 must be promoted" heuristic. The only way to stop the
oscillation was to make "don't touch" the default, with the print-
weight test reserved for genuinely exceptional cases.

### Concrete examples already-burned-and-reverted

- 174 Computer-Knobeleien: `Remis-Positionen` / `Kegeln mit dem
  Computer` / `Tac Tix mit Taktik` are top-level sub-sections that
  the print sets in h3-sized bold. They stay h3.
- 166 Tips und Tricks zu Superbase: `FIND — gezielte Suche` /
  `Die Centronics-Schnittstelle` / `Plotter VC 1520`. Inline sub-
  sections within a column. h3.
- 168 Tips und Tricks zu Vizawrite: `Griechisch für Vizawrite mit
  dem SG-10`. Same.
- 22 Wachstumspyramide: `Ausgangsdaten` / `Berechnungsmethode` /
  `Bedienungsanleitung` / `Beispiele für die Anwendung`. Article
  was written entirely in h3 sub-sections. h3.
- 67 Die ideale Ergänzung: `Editor` / `Hauptmenü` are top-level
  sections of the editor description. h2 as the input had them —
  the audit demoted them on a "sub-sections of Zeichensatz-Editor"
  heuristic. Wrong.
- 73 Vectors, 85 C 128: top-level h3 sub-sections.
- 84 Fehlerteufelchen: every sub-correction is h3.
- **Fehlerteufelchen rubric — sub-correction headings are always
  `<h3>`.** The Fehlerteufelchen column is a list of corrections to
  previous issues; each sub-correction starts with a heading like
  "Der kleine Hobbit, Sonderheft 4/86, Seite 111 ff". Print sets
  these in inline-bold weight, NOT h2-banner weight — uniformly
  across every sub-correction. So the choice is uniformly `<h3>`.
  This is the same orphan-h3 anti-pattern documented above: a
  future agent will see h3s with no h2 parent and want to promote.
  Don't. 8607's `84 Fehlerteufelchen.html` was toggled to h2 and
  back to h3 during the issue's work — leave at h3.
- Don't run a heading audit as a single batch action across the
  whole issue. Per-article decisions, scan crops, judgment.
  Bulk-applying any heading-promotion heuristic is risky.
- The reviewer-then-second-reviewer pattern (used in 8607 for the
  Grafik-Modi table) is overkill for headings — but for a hierarchy
  decision in a clearly-tricky article (multi-h2 article like
  Aktuelles or a tutorial with internal sub-sub-sections), a
  second opinion is worth the time.
