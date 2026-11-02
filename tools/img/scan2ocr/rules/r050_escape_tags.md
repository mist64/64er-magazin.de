# 050 — Escape angle-bracket text that isn't a real HTML tag

**Applies to:** all — a character-class transform on the `.md`; no issue-specific input.

**Goal:** prevent the browser (and the markdown converter) from swallowing
text like `<RETURN>`, `<SHIFT-RUN/STOP>`, `<F3>`, `<CBM>`, … by escaping
them so they render as literal text. Keep real HTML tags (`<br>`, `<sub>`,
`</sup>`, `<aside>`, `<img …>`, etc.) untouched.

## Rule

For every `<…>` pattern in the `.md`:
- Extract the first identifier (the would-be tag name; for `</X>` strip the leading `/`, for `<X/>` ignore the trailing `/`).
- If the identifier is in the HTML whitelist — **compared exactly, NOT
  lowercased** (`br, p, h1-h6, a, strong, em, sub, sup, table, tr, td, th, thead, tbody, ul, ol, li, dl, dt, dd, hr, img, code, pre, blockquote, aside, figure, figcaption, address, div, span, section, article, small, b, i, u, kbd, mark, samp, …`) → **keep**.
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

**Case matters and this file used to get it wrong.** It said to lowercase the
identifier before the comparison; the script does not, and the script is
right. A 1986 magazine writes its key names in capitals — `<P>`, `<I>`,
`<A>`, `<Q>`, `<B>` — and lowercasing them turns a C64 key into a paragraph,
an italic run, a link or a quotation. `<P>RESS <RETURN>` would open a
paragraph tag and swallow the line. The whitelist is all lowercase precisely
so that an uppercase key name can never match it.

Patterns that already start with a non-letter (e.g. `< CBM >` with leading space, `<10`, `<\*>`) won't be matched and stay as-is — they're already browser-safe because HTML requires a letter immediately after `<` for a tag.

**"A NON-LETTER AFTER `<` IS SAFE" IS WRONG FOR THREE OF THEM.** The HTML5
tokenizer has exactly four paths out of a `<`: a letter (a tag), `/` + a letter
(an end tag), and then **`!`**, **`?`** and **`/` + anything else** — and those
last three all open a *bogus comment*, which eats text up to the next `>` and
renders as nothing at all. So the complete set to escape is:

| after `<` | HTML5 does | in this corpus |
|---|---|---|
| a letter | a tag — whitelist decides | Pass 2 |
| `/` + letter | an end tag — whitelist decides | Pass 2 |
| `!` | bogus comment, text eaten | **8701: `<!>` ×5** |
| `?` | bogus comment, text eaten | not yet seen |
| `/` + non-letter | bogus comment, text eaten | 8612 line 2903 |
| anything else | literal text, safe | left alone |

All three bogus-comment openers are **Pass 3 in the script**, in one pattern.

**Both halves of this were found the same way, an issue apart, and both were
invisible from both ends.** The `</` + non-letter half: the rule had required
it since the 8612 harvest and the script never did it, because Pass 2's pattern
requires a letter after the optional `/` — and the Verification regex had the
same requirement, so neither end could see the gap. 8612 line 2903, "durch
`</>` dargestellt", would have lost the `</>` and swallowed what followed.

The `<!` half, on 8701: the issue prints `<!>` five times (Master-Text, the
"Ausrufungszeichen-Funktion"), every one shipped unescaped, and the `!`
disappeared. **The Verification could not see that either, because it applied
the same "a non-letter after `<` is safe" test as the transform.** A check
derived from the belief it is meant to question can only ever confirm it; this
is the fourth instance in the chain (see HARVEST, 8701). The count the script
prints now covers all three openers for the same reason.

The shape is rare in live text — 0 occurrences in SH8603's and SH8604's 030
handovers, 5 in 8701 — so the planted case in the Verification is what
exercises it.

## Usage

```bash
tools/img/scan2ocr/rules/r050_escape_tags.sh issues/8607/8607.md
```

Idempotent — but **not** by the lookbehinds this line used to claim
(`(?<!\\)<`, `(?<!\\)>`). The script has no such lookbehind. It is idempotent
because its output is entities: `&lt;…&gt;` matches none of the three passes.
Verified by running it twice over its own output.

## Verification

Counted **outside fenced code only**, and **case-sensitively**, so that the
check agrees with the script. Both mattered on 8611: this block reported 2
failures on correct output — one a fenced `<RETURN>`, one its own `[^<>]*?`
running across a newline from `ldx #<fadr` inside a fence to `#>fadr` outside
it — and its `.lower()` would have accepted `<P>` and `<I>` as HTML, which is
exactly the mistake the script refuses to make.

```bash
$PY - issues/<YYMM>/<YYMM>.md <<'PYEOF'
import re, sys
def outside_fences(s):
    """The file's text with every ```-fenced region blanked out.

    A CHECK MUST BE AS FENCE-AWARE AS THE TRANSFORM IT CHECKS. When 040 and 050
    stopped escaping inside fences, these blocks went on counting the whole file
    and began FAILING ON CORRECT OUTPUT -- 040 reported 4 solitary asterisks,
    all 4 correctly left alone inside listings. A check that fails on a good
    result gets "fixed" by undoing the transform, which is how a corrected bug
    comes back.
    """
    out, infence = [], False
    for line in s.splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            infence = not infence
            out.append('\n')
            continue
        out.append('\n' if infence else line)
    return ''.join(out)

WHITE = {'a','abbr','address','article','aside','b','blockquote','body','br','caption','code','col','colgroup','dd','del','details','dfn','div','dl','dt','em','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','head','header','hr','html','i','iframe','img','ins','kbd','label','li','link','main','map','mark','meta','nav','ol','p','param','pre','q','rp','rt','ruby','s','samp','script','section','small','source','span','strong','style','sub','sup','table','tbody','td','tfoot','th','thead','title','tr','u','ul','var','wbr'}
s = outside_fences(open(sys.argv[1], encoding='utf-8').read())
bad = []
# [^<>\n]: a tag does not span lines, and letting it cross one matched from a
# fence into the prose after it.  No .lower(): the script is case-sensitive.
for m in re.finditer(r'(?<!\\)<(/?[a-zA-Z][^<>\n]*?)(?<!\\)>', s):
    name = re.match(r'/?([a-zA-Z][a-zA-Z0-9]*)', m.group(1)).group(1)
    if name not in WHITE: bad.append(m.group(0))
print(f"unescaped non-HTML <...>: {len(bad)}")
for b in bad[:5]: print(f"  e.g. {b}")
# Pass 3's shapes, which this block could not see either: it applied the same
# "a non-letter after '<' is safe" test as the transform, so `</>` (8612) and
# then `<!>` (8701, five times) were unreachable from both ends.  ALL THREE
# bogus-comment openers, or the check confirms the belief it is testing.
bogus = re.findall(r'<(?:![^<>\n]*|\?[^<>\n]*|/(?![a-zA-Z])[^<>\n]*)>', s)
print(f"bogus-comment openers (<!, <?, </ + non-letter): {len(bogus)}")
for b in bogus[:5]: print(f"  e.g. {b}")
PYEOF
```

Expected: zero unescaped non-HTML tags, zero bogus-comment openers.

**And plant Pass 3's case, because live text almost never carries it** (0 in
both SH8603 and SH8604). A check that no issue can exercise is not a check:

```bash
printf 'Zeichen `</>`, `</1>`, die Taste <!> und ein echtes <br> dahinter.\n' > /tmp/t50.md
tools/img/scan2ocr/rules/r050_escape_tags.sh /tmp/t50.md
cat /tmp/t50.md
```

Expected: `&lt;/&gt;`, `&lt;/1&gt;` and `&lt;!&gt;`, with `<br>` untouched. Run
it twice: the output must not change the second time.

## Notes / lessons

- Discount has no built-in way to whitelist HTML tags: `-html` flag escapes
  everything (including real `<br>`), default/strict mode preserves
  everything. So this fix lives in the `.md` pre-pass.
- Marked 2 doesn't fully solve this either: it leaves `<RETURN>`, `<CRSR LEFT/RIGHT>`, etc. unescaped — those would get swallowed by browsers as unknown elements. Our pass is stricter.
- Browser behavior for `<RETURN>foo`: the browser parses `<RETURN>` as an
  unknown empty element, then displays `foo`. The text inside the angle
  brackets disappears. This script prevents that.

## A WHITELISTED NAME IN A RUN OF PLACEHOLDERS IS A PLACEHOLDER (SH8607)

The whitelist is an exact-case name match, so a syntax line full of angle-
bracket parameters escapes most of them and keeps the ones that happen to be
HTML. SH8607's XMENU prints

    MENU <x>, <y>, <l>, <p>, <t>, <m>, <s>, <ar>

`<x>` `<y>` `<l>` `<t>` `<m>` `<ar>` escaped; **`<p>` and `<s>` survived as
live tags** — a stray paragraph open and a strike-through opener in the
published HTML, plus two more sites where the text explains `<p>`. **No
Verification check can see this**, because the output is valid markup either
way; it was caught by eye after 070.

**A whitelisted name sitting in a comma-separated run of escaped placeholders
is a placeholder: escape it.** Judge by the neighbours, not by the name.

```bash
# a bare <p>/<s>/<b>/<i> on a line that also carries an escaped placeholder
grep -nE '&lt;[a-z]+&gt;' issues/<ID>/*.html | grep -E '<(p|s|b|i)>'
```
