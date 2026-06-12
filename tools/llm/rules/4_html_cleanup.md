# 4 — HTML cleanup: blockquote → intro, curly quotes → straight, `<br/>` → `<br>`

**Goal:** turn the Discount output into the project's house style:
- the leading "intro" paragraph in each article comes through as
  `<blockquote><p>…</p></blockquote>`; convert to `<p class="intro">…</p>`
- curly typographic quotes from the OCR become straight ASCII
- `<br/>` (XHTML) becomes `<br>` (HTML5)

German guillemets `«» / »«` are kept — they're the magazine's authentic
quotation marks and stay verbatim.

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
tools/llm/rules/4_html_cleanup.sh issues/8607/8607.html
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

- `split.py` already performs the same `&lsquo;`/`&rsquo;`/`&ldquo;`/`&rdquo;`/`''` replacements
  as part of its per-article cleanup. Doing it here too is harmless (split.py
  becomes a no-op for these) and keeps the pre-split HTML uniform if you ever
  want to look at it directly.
- German guillemets `«` `»` `‹` `›` are NOT touched — they're the magazine's
  real quotation marks.
