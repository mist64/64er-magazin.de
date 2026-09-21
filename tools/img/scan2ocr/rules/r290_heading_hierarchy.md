# 290 — Heading hierarchy (`<h1>` / `<h2>` / `<h3>`)

**Applies to:** all — heading levels follow the print's typographic weight in both kinds.

**Goal:** every article's heading hierarchy matches what the print
typesets. Don't promote / demote on structure alone — judge against
the print's typographic weight.

## DEFAULT: DON'T CHANGE HEADER LEVELS

**The OCR'd / post-step-0 markdown is the source of truth for heading
levels. The default action is to leave heading levels alone. Trust
the input.**

Cross-reference: rule 260 (`heading_case`) carries a parallel
`DEFAULT: don't change heading text` clause. This rule protects
heading *levels*; rule 260 protects heading *text*. Both default to
"trust the input" — keep them in sync.

The "compare print typographic weight" test in the rest of this file
is for **exceptional** cases only — when there's a clear *structural*
reason to suspect the input is wrong (e.g. the hierarchy makes the
article malformed for the generator, or a structural rule like 15
forces a specific level).

Structural overrides that DO apply:

- **An `<h2>` inside an `<aside>` STAYS an `<h2>`.** A set-off box's own
  heading carries the print's banner weight, and it is not demoted for
  sitting in a callout. This section used to say the exact opposite
  ("always demote to `<h3>`") while the bottom of the same file retracted
  it — the evidence that settled it is in *`<h2>` inside `<aside>` is
  CORRECT*, below. There is one aside shape that does use `<h3>`: rule
  300's Fehlerteufelchen erratum box.

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

3. **Inside an `<aside>`?** Then the question does not arise: the
   box's own heading is an `<h2>` and stays one. Do not demote it,
   and do not promote an `<h3>` that rule 300 put in an erratum box.

Never promote on (1) alone. Never demote on (1) alone. (1) without
(2) is a structure-only heuristic and is exactly the trap above.

## Briefing for the sub-agent

For every article in `issues/<YYMM>/*.html`:

1. List heading hierarchy (h1/h2/h3 with line numbers).
2. For each suspicious heading (h3 at top level, h2 → h3
   mid-article, two adjacent h2 with no body between — an `<h2>`
   in an `<aside>` is NOT suspicious), check the **print scan at
   600 dpi**:
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

# 2. aside headings -- an INVENTORY, not a failure.  <h2> in an <aside>
#    is the correct shape; this lists the hits so the report can account
#    for them, and flags the one level that is NOT expected.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
n = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<aside\b[^>]*>(.*?)</aside>', s, re.DOTALL):
        for lvl in re.findall(r'<(h[1-6])\b', m.group(1)):
            n += 1
            mark = '' if lvl == 'h2' else '   <- rule 300 erratum box, or check it'
            print(f"  {f}: <{lvl}> inside <aside>{mark}")
print(f"  {n} aside headings; expected <h2> except rule 300's erratum boxes")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). This rule has its own version
of the same failure mode: bulk-audit passes (`b94e5876b`) re-derived
the "orphan h3 must be promoted" heuristic and silently shipped 14
wrong promotions because no per-heading scan evidence was required.
To make both failure modes impossible here, every heading-level
change the sub-agent applies must be backed by **runnable verifier
evidence pasted verbatim into the report**:

- For each promotion or demotion, paste the page + bbox of the
  scan-band the decision came from, plus a one-line typographic
  comparison against a known-h2 reference in the same issue, e.g.
  ```
  67 Die ideale Ergänzung.html "Editor" → p.68 crop bbox=420x60+580+1180
  weight matches issue's known h2 banners (cf. 50 R.C.S. p.50 h2
  "Anwendung des Monats") → kept h2
  ```
- For each candidate considered but LEFT UNCHANGED, paste the same
  scan-band evidence so the orchestrator can confirm the default-
  to-leave was a real comparison, not a skip-by-omission.
- For each `<h2>` inside an `<aside>` that was LEFT ALONE, nothing has
  to be pasted: it is the expected shape, and check 2's inventory line
  is the whole record. A demotion of one, on the other hand, is a
  heading-level change like any other and needs its scan band.

**No verifier output, no claimed heading change.** A heading-level
change reported without the scan-band evidence is treated as a guess;
the orchestrator will revert it and re-dispatch. The bulk-audit
workflow is banned outright (see anti-pattern above); per-article
changes only, with scan evidence per heading. "Trust me, this looks
like h2 weight" is never acceptable — that's the exact framing that
produced `b94e5876b`.

## Notes / lessons

### History of how this rule reached its current form

The rule started as "compare print weight" and only added "DEFAULT:
don't change" after the third repetition of the same mistake.

- **`b94e5876b`** ("8607: heading hierarchy audit — 20 articles
  fixed"). Walked every 8607 article's hierarchy. 9 of the changes
  were structural (h2-in-aside demotions, kept at the time — the
  convention was later reversed, see below). The other
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

## A "heading" that is really a paragraph tail

The OCR promotes stray text to a heading whenever a line stands alone in the
column. Signatures of the defect, all seen in 8609:

- **ends with a period**: `<h3>89 Mark.</h3>`, `<h3>MHz.</h3>`, `<h3>128.</h3>`,
  `<h3>8000.</h3>` — each is the tail of the preceding sentence, cut at a column
  break. Rejoin it to the previous `<p>` with a space.
- **is a bare number or unit**: same cases as above. A heading consisting only
  of digits, a currency amount or a unit is never a heading.
- **is a mid-sentence fragment**: `<h3>Codes drucken kann, zeigt dieses
  Programm.</h3>` was the end of the article's intro.
- **is half of a two-line heading**: p137 prints *"Wie zählen die
  Zweifingerlinge?"* over two lines; it arrived as
  `<p>Wie zählen die ® .. ®</p>` + `<h3>® Zweifingerlinge?</h3>`. Join the
  halves and drop the grit.

Check: no `<h2>`–`<h6>` may end in `.` (an ellipsis `...` is fine), consist only
of non-letters, or start lowercase.

**But the magazine sometimes really prints the period**, and an exception that
lives only in a log is an exception the gate cannot see. SH8601 p039 sets
`2. Sprites und Windows.` with a printed full stop, measured on the master —
and r310 went on failing it after the finding was adjudicated, so its HARD count
could not honestly reach zero. A gate that always reports two failures stops
being read.

**Write the adjudication into the file, immediately above the heading**, as an
HTML comment containing the word `PRINTED` in upper case, saying what was read
and from where. r310 honours it within the 400 characters before the heading and
demotes the finding to soft:

```html
<!-- The trailing period is PRINTED: verified against the 600 dpi master
     by step 290.  r310 flags a heading ending in "." as a possible
     paragraph tail; here it is the page's own typography. -->
<h3>2. Sprites auf Diskette und Kassette.</h3>
```

The comment is the evidence, not a silencer: it must name the page and how the
glyph was read, exactly as a LOG line would. No marker, no exemption — proved by
stripping the comments from a copy of the issue, which restores the failure.

## `<h2>` inside `<aside>` is CORRECT

A set-off box's heading is an `<h2>`. Do not "fix" it to `<h3>`.

Earlier versions of this rule said the opposite, and for a while said BOTH: the
header section ordered the demotion, this section retracted it, and the
Verification block still tested for the demoted form. That is resolved here, in
this direction, on three pieces of evidence:

- **The published corpus.** 8609 ships **10 `<h2>` inside an `<aside>` across
  7 files** — `9 Aktuelles` ×3, `46 Vollgas für die Floppy 1570/71` ×2,
  `48 Bar-Codes selbst gemacht`, `68 Die CP_M-Ecke (Teil 3)`,
  `148 Wettstreit der Assembler`, `151 GV-Forth V1.0`,
  `160 Der ewige Wettlauf` — and not one demoted `<h3>` among them.
- **Rule 190's practice.** Rule 190 owns every aside in the issue and builds
  them with an `<h2>`; a demote pass here would undo its work on every issue.
- **8610.** 7 instances across 6 files (`32`, `34`, `36`, `46`, `51`, `52`)
  were checked against that precedent and kept, with no demote-then-restore
  round trip.

The one exception is not an exception to the weight rule but a different
shape: rule 300's **Fehlerteufelchen erratum box** carries an `<h3>`, three of
them in 8609 (`48 Bar-Codes selbst gemacht`, `71 Cross-Referenz-Liste C128`,
`156 Tips und Tricks zu Vizawrite (Teil 9)`). Leave those alone too — they are
rule 300's, not this rule's.