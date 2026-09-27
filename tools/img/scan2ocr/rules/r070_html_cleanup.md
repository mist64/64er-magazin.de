# 070 — HTML cleanup: blockquote → intro, curly quotes → straight, `<br/>` → `<br>`

**Applies to:** all — house-style substitutions on the converted HTML; no issue-specific input.

**Goal:** turn the Discount output into the project's house style:
- the leading "intro" paragraph in each article comes through as
  `<blockquote><p>…</p></blockquote>`; convert to `<p class="intro">…</p>`
- curly typographic quotes from the OCR become straight ASCII
- `<br/>` (XHTML) becomes `<br>` (HTML5)

German guillemets `«» / »«` are kept — they're the magazine's authentic
quotation marks and stay verbatim.

## Inside `<pre>` these substitutions are CORRECT — do not make this step fence-aware

Steps 040, 050 and 060 all had to be taught to leave fenced code alone, and it
would be easy to conclude that any whole-file pass is wrong inside `<pre>`.
This one is not, and the difference is the whole point:

| the pass | inside `<pre>` | why |
|---|---|---|
| 040 `\*`, 050 `&lt;` | **wrong** | the escape is for Discount's inline parser, which does not run in a fence, so it ships literally |
| 060 `-G` padding | **wrong** | the renderer added it; it was never in the source |
| **070 curly → straight** | **RIGHT** | it restores what the source actually was |

**Ask what the source characters were, not whether it is a code block.** The
C64 character set has exactly ONE quote, `"` at 0x22 — there is no curly quote
in PETSCII — so a `"` or `"` inside a listing is an OCR misreading of a plain
quote and straightening it is a repair, not a corruption. `CHR$(27);"*"` is
what the magazine printed and what a reader must type; `CHR$(27);"*"` would not
run.

MEASURED over the published corpus, inside `<pre>`: **8610 has 0 curly quotes
and 102 straight; 8608 has 0 and 26.** 8609 has 8 curly that survived, and
those are a defect, not a precedent.

## Substitutions

| from | to |
|---|---|
| `<blockquote><p>` | `<p class="intro">` |
| `</blockquote>` | *(removed)* |
| `<br/>` | `<br>` |
| `'` (U+2019 right single) | `'` |
| `'` (U+2018 left single) | `'` |
| `"` (U+201D right double) | `"` |
| `"` (U+201C left double) | `"` |
| `„` (U+201E German low double) | `"` |
| `&rsquo;`, `&lsquo;` | `'` |
| `&rdquo;`, `&ldquo;`, `&bdquo;` | `"` |
| `''` (two ASCII apostrophes) | `"` |

## Usage

```bash
tools/img/scan2ocr/rules/r070_html_cleanup.sh issues/8607/8607.html
```

In-place rewrite, idempotent (re-running on a cleaned file is a no-op).

## Verification

After running:

```bash
grep -c '<blockquote'        issues/8607/8607.html   # expect 0
grep -c 'class="intro"'      issues/8607/8607.html   # ≥1
grep -c '<br/>'              issues/8607/8607.html   # 0
grep -c '<br>'               issues/8607/8607.html   # >0
python3 -c "
import sys
s = open(sys.argv[1]).read()
for c in '‘’“”„':
    n = s.count(c)
    if n: print(f'  remaining {c!r}: {n}')
" issues/8607/8607.html                              # nothing reported
```

## Notes

- `r080_split.sh`'s embedded splitter already performs the same `&lsquo;`/`&rsquo;`/`&ldquo;`/`&rdquo;`/`''` replacements
  as part of its per-article cleanup. Doing it here too is harmless (step 080
  becomes a no-op for these) and keeps the pre-split HTML uniform if you ever
  want to look at it directly.
- German guillemets `«` `»` `‹` `›` are NOT touched — they're the magazine's
  real quotation marks.
