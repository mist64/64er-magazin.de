# 050 — Escape angle-bracket text that isn't a real HTML tag

**Applies to:** all — a character-class transform on the `.md`; no issue-specific input.

**Goal:** prevent the browser (and the markdown converter) from swallowing
text like `<RETURN>`, `<SHIFT-RUN/STOP>`, `<F3>`, `<CBM>`, … by escaping
them so they render as literal text. Keep real HTML tags (`<br>`, `<sub>`,
`</sup>`, `<aside>`, `<img …>`, etc.) untouched.

## Rule

For every `<…>` pattern in the `.md`:
- Extract the first identifier (the would-be tag name; for `</X>` strip the leading `/`, for `<X/>` ignore the trailing `/`).
- If the **lowercased** identifier is in the HTML whitelist (`br, p, h1-h6, a, strong, em, sub, sup, table, tr, td, th, thead, tbody, ul, ol, li, dl, dt, dd, hr, img, code, pre, blockquote, aside, figure, figcaption, address, div, span, section, article, small, big, b, i, u, kbd, mark, samp, …`) → **keep**.
- Else → **replace** the surrounding `<` and `>` with the entities `&lt;` and
  `&gt;` directly. Not with `\<` … `\>`: this file used to say that, and the
  script's own comment says why it stopped — Discount **preserves `\<`
  literally** when what follows looks like a tag, so `text \<F1\>` ships
  backslashes and all. MEASURED on Discount 3.0.2 with r060's flags.
- **Fenced code is left alone.** The escape is for Discount's inline parser,
  which does not run inside a fence, so an entity written there is re-escaped
  by 070 and ships as the visible text `&lt;F1&gt;`. Discount escapes `<…>`
  inside a fence by itself, correctly. Same for r040's `\*`, which would ship
  as a stray backslash in a listing.

Patterns that already start with a non-letter (e.g. `< CBM >` with leading space, `<10`, `<\*>`) won't be matched and stay as-is — they're already browser-safe because HTML requires a letter immediately after `<` for a tag.

## Usage

```bash
tools/img/scan2ocr/rules/r050_escape_tags.sh issues/8607/8607.md
```

Idempotent: lookbehinds for `\` (i.e., `(?<!\\)<` and `(?<!\\)>`) mean re-runs are no-ops.

## Verification

```bash
# nothing left unescaped that isn't a real tag:
python3 - "$file" <<'PY'
import re, sys
WHITE = {'a','abbr','address','article','aside','b','blockquote','body','br','caption','code','col','colgroup','dd','del','details','dfn','div','dl','dt','em','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','head','header','hr','html','i','iframe','img','ins','kbd','label','li','link','main','map','mark','meta','nav','ol','p','param','pre','q','rp','rt','ruby','s','samp','script','section','small','source','span','strong','style','sub','sup','table','tbody','td','tfoot','th','thead','title','tr','u','ul','var','wbr'}
s = open(sys.argv[1]).read()
bad = []
for m in re.finditer(r'(?<!\\)<(/?[a-zA-Z][^<>]*?)(?<!\\)>', s):
    name = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', m.group(1)).group(1).lower()
    if name not in WHITE: bad.append(m.group(0))
print(f"unescaped non-HTML <…>: {len(bad)}")
for b in bad[:5]: print(f"  e.g. {b}")
PY
```

Expected: zero unescaped non-HTML tags.

## Notes / lessons

- Discount has no built-in way to whitelist HTML tags: `-html` flag escapes
  everything (including real `<br>`), default/strict mode preserves
  everything. So this fix lives in the `.md` pre-pass.
- Marked 2 doesn't fully solve this either: it leaves `<RETURN>`, `<CRSR LEFT/RIGHT>`, etc. unescaped — those would get swallowed by browsers as unknown elements. Our pass is stricter.
- Browser behavior for `<RETURN>foo`: the browser parses `<RETURN>` as an
  unknown empty element, then displays `foo`. The text inside the angle
  brackets disappears. This script prevents that.
