# 21 — Render printed math formulas via MathJax (LaTeX) — when needed

**Goal:** every typeset math formula in the article HTML — every
`<p>TODO FORMULA</p>` / `TODO FORMULAS` placeholder and every
naturally-occurring inline formula — is rendered legibly. MathJax
(LaTeX) is the right tool for **complex** formulas; **simple ones can
stay as plain Unicode + `<sub>` / `<sup>`** when that already
reproduces the print correctly.

## When Unicode is enough vs when MathJax is needed

**Unicode + `<sub>` / `<sup>` is fine for:**
- Plain inline expressions that already render correctly with
  Unicode chars and the standard sub/sup tags: `V<sub>0</sub>`,
  `X<sup>2</sup>+Y<sup>2</sup>`, `2π`, `α·β`, `ω<sub>0</sub>²`,
  `dV/dt`, `≈`, `∑`, `√(a²+b²)` (rendered as `√(a<sup>2</sup>+b<sup>2</sup>)`).
- Anything that 8606 already ships verbatim (`<sup>2</sup>` for
  squared, etc.).

**MathJax (LaTeX) is needed for:**
- Stacked fractions printed with a real horizontal vinculum (not a
  slash) — `\frac{\mathrm{d}V}{\mathrm{d}t}`.
- Square roots with a vinculum spanning multiple terms.
- Summation / integral with limits below and above the symbol.
- Multi-line aligned equations or anything else where layout
  matters beyond "baseline glyph + superscript".

The boundary is what the print **shows**. If the print typeset a
fraction as a stacked numerator-over-denominator with a horizontal
bar, that's MathJax. If the print just wrote `dV/dt` inline on one
line, plain Unicode is enough — don't gold-plate it.

The generator preloads MathJax globally
(`generate.py` line ~1399 ships
`mathjax/es5/tex-mml-chtml.js` to every page). The standard
MathJax delimiters are:

- **Inline**: `\(…\)`  → `\(V = V_0 \cdot \cos(\omega t)\)`
- **Display**: `\[…\]` → `\[\frac{\mathrm{d}V}{\mathrm{d}t} = -\omega^2 X\]`

Use display when the formula is its own paragraph (the print
typically centres these), inline when it sits inside running prose.

## Why MathJax and not Unicode + `<sup>`

- 64'er's typeset formulas use real math notation (fractions,
  square roots, summation, vector arrows, Greek letters with
  diacritics). HTML's `<sup>`/`<sub>` can only fake the easy
  cases; everything else looks broken (`a/b` as a flat slash
  instead of a fraction, square roots without the vinculum).
- MathJax renders the same LaTeX source identically across the
  browsers we care about and degrades to readable plain text in
  RSS or print views.
- Existing 8606 prose still has the legacy `<sup>` patterns (e.g.
  `<sup>2</sup>` for squared); leave those alone — only **new**
  formulas inserted by this pipeline use MathJax.

## Briefing for the sub-agent

When resolving `<p>TODO FORMULA</p>` / `<p>TODO FORMULAS</p>` /
inline `TODO FORMULA` tokens:

1. Render the relevant scan page at 300 dpi for context and 600 dpi
   for the formula itself. Small superscripts and subscripts need
   the 600 dpi pixel budget.
2. Crop the formula region and dispatch a sub-sub-agent for the
   OCR/vision read. Sub-sub-agent returns:
   - For a complex formula → the LaTeX source.
   - For a simple formula that Unicode can reproduce → the Unicode +
     `<sub>` / `<sup>` HTML version.
3. **Make the per-formula Unicode-vs-MathJax decision** based on the
   print:
   - One-line expressions, no stacked fractions, no spanning roots
     → emit Unicode HTML (`V<sub>0</sub>`, `X<sup>2</sup>+Y<sup>2</sup>`,
     `dV/dt`, `2π`, `α·β`, `ω<sub>0</sub>²`, etc.).
   - Stacked fractions, multi-term square roots, summations / integrals
     with limits, multi-line aligned equations → emit LaTeX inside
     MathJax delimiters.
4. Wrap the returned content:
   - **MathJax** standalone formula → `<p>\[…\]</p>` (display).
   - **MathJax** inline token → `\(…\)` substituted into the existing
     `<p>`.
   - **Unicode** standalone → `<p>` containing the Unicode HTML.
   - **Unicode** inline token → the Unicode HTML inserted into the
     existing `<p>` directly.
5. For LaTeX: use standard macros (`\frac`, `\sqrt`, `\sum`, `\cdot`,
   `\omega`, `\mathrm` for upright differentials, `_{}` / `^{}` for
   subscripts/superscripts). Don't escape backslashes — raw LaTeX in
   HTML works once MathJax sees the delimiters.

Anti-memory: the LaTeX source comes from reading the scan, not
from physics knowledge or context. If the print shows a specific
notation (e.g. `V₀` vs `V_0`), match the print.

## Verification

```bash
dir=issues/<YYMM>

# 1. no TODO FORMULA / FORMULAS markers survive
grep -nE 'TODO FORMULA' "$dir"/*.html && echo "  FAIL: TODO FORMULA left"

# 2. any LaTeX outside MathJax delimiters is a bug — Unicode-only
#    formulas should not contain LaTeX macros at all.
#    (heuristic: any \frac / \sqrt / \cdot / \omega outside \( \) or
#    \[ \] is suspicious)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for keyword in (r'\frac', r'\sqrt', r'\cdot', r'\omega', r'\mathrm'):
        for m in re.finditer(re.escape(keyword), s):
            # check it's inside \( \) or \[ \]
            i = m.start()
            window = s[max(0, i-100):i]
            opens = window.count(r'\(') + window.count(r'\[')
            closes = window.count(r'\)') + window.count(r'\]')
            if opens <= closes:
                snippet = s[max(0, i-20):i+30]
                print(f"  bare LaTeX in {f}: {snippet!r}")
PY
)" "$dir"

# 3. balanced \( \) and \[ \] pairs per file
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o_inline = s.count(r'\(');  c_inline = s.count(r'\)')
    o_disp   = s.count(r'\[');  c_disp   = s.count(r'\]')
    if o_inline != c_inline:
        print(f"  inline math mismatch in {f}: \\(={o_inline} \\)={c_inline}")
    if o_disp != c_disp:
        print(f"  display math mismatch in {f}: \\[={o_disp} \\]={c_disp}")
PY
)" "$dir"
```

## Notes / lessons

- A single article often has both display and inline formulas (a
  derivation centres each step then references variables inline).
  Pick the delimiter per occurrence, not per article.
- 64'er reuses physics notation that maps cleanly to LaTeX:
  - `V₀` → `V_0`
  - `dV/dt` → `\frac{\mathrm{d}V}{\mathrm{d}t}`
  - `ω` → `\omega`
  - `2π` → `2\pi`
  - `√(x²+y²)` → `\sqrt{x^2 + y^2}`
- The existing `<sup>2</sup>` patterns in prior issues are
  acceptable for the simple inline-squared case and don't need
  to be retroactively migrated — only NEW formulas use MathJax.
- `[ILLEGIBLE]` is still the answer when the scan is too blurry,
  even at 600 dpi. Don't guess at LaTeX.
