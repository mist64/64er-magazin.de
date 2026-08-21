# 060 — Convert `.md` → `.html` (Discount / GFM) and replace .md with .html in git

**Goal:** convert the OCR markdown to HTML using the same engine Marked 2
uses (Discount, GFM mode), producing the `.html` next to the `.md`. After
conversion, `git rm` the `.md` and `git add` the `.html`, so only the HTML
lives in the repo from here on.

## Marked 2 GUI settings → Discount CLI flags

| Marked 2 setting | CLI |
|---|---|
| Process Markdown with **Discount (GFM)** | `markdown -G` (use the `gfm_in` entry — also gives single-LF→`<br/>`) |
| Retain line breaks in paragraphs | implied by `-G` |
| Process Markdown inside of HTML | `+html` flag |
| Generate IDs on headlines | default for Discount |
| Render GitHub checkboxes | `+github-listitem` |
| Render `~~delete~~` | `+strikethrough` |
| *(not a Marked 2 setting)* | `-alphalist` — **required**, see below |
| Render `==highlight==` | **not** in Discount; would need post-pass (n/a here) |

## Usage

```bash
tools/img/scan2ocr/rules/r060_md_to_html.sh issues/8607/8607.md
# 1. writes issues/8607/8607.html next to the .md
# 2. `git rm`s the .md (or plain `rm` if not yet tracked)
# 3. `git add`s the .html
```

## `-alphalist` is mandatory

Discount treats a letter followed by a period at the start of a line as an
**alphabetic ordered list** (`a.` → `<ol type="a">`). In this corpus that
construct is almost never a list:

- **Abbreviated forenames.** `M. Grewe: »Nein, …«` in an interview became
  `<ol type="a"><li>Grewe: »Nein, …«</li></ol>` — and the `M.` was **eaten as
  the list marker**. That is silent text loss, not merely wrong markup, and it
  survives every structural check because the result is valid HTML.
- **OCR'd numbers.** A printed `1.` read as the letter `l.` produces the same
  `<ol type="a">` with the number swallowed, turning one real numbered list
  into a chain of one-item lists.

So: `<ol type="a">` in a converted file is a **bug signature**, not a style.
Grep for it after conversion and check every hit against the print.

## Discount emits invalid nesting for fenced code — the post-pass is mandatory

This is the root cause of the "prose glued to the end of a listing" defect.
Given well-formed Markdown:

```
Beispiel:

​```
CODE
​```

Nächster Absatz.
```

Discount produces:

```html
<p><pre><code>CODE
</code></pre>

Nächster Absatz.</p>
```

The `<pre>` is put *inside* a `<p>`, and the following paragraph is swallowed
into the same `<p>` — so the paragraph break after every listing is lost, and
the prose arrives glued to the code. Independent of `-G`; **indented** code
blocks are fine, only fenced ones (`+fencedcode`) do this. Issue 8609 had 19
occurrences, which surfaced as `54`'s ESC table, `82`'s SYS line, `58`'s
Shrinksprite parameters, `96`'s POKE line and six in `135`.

`r060_md_to_html.sh` therefore runs a post-pass that rewrites
`<p><pre>…</pre>TAIL</p>` into `<pre>…</pre>` + `<p>TAIL</p>`.

## Verification

- A literal `(\*\*\*)` in the .md renders as `(***)` in the HTML.
- A line ending in a single LF inside a paragraph becomes `…<br/>` in the HTML.
- `**bold**` becomes `<strong>bold</strong>`.
- **No `<p><pre>` anywhere**: `grep -c '<p>\s*<pre>' issues/<YYMM>/*.html` → 0.
  A hit means the fenced-code post-pass did not run.
- **No `<ol type="a">` anywhere**: `grep -c 'ol type="a"' issues/<YYMM>/*.html` → 0.
  A hit means an abbreviated forename or an OCR'd `1.` was parsed as a list marker
  and its first token deleted.

Quick spot-check (paste into shell after running the script):

```bash
grep -n 'Asterisken'    issues/8607/8607.html | head -1   # expect (***)
grep -c '<strong>'      issues/8607/8607.html             # ~90+
grep -c '<br'           issues/8607/8607.html             # >0 (intra-paragraph LFs)
```

## Notes / lessons

- Discount's `markdown` binary has **no `--hardbreaks`** flag; `-G` is the only
  way to get GFM-style single-LF→`<br/>` from this CLI.
- Marked 2 statically links Discount; there's no exposed binary inside the app
  bundle. The brewed `discount` package is the same engine.
- `==highlight==` isn't part of standard GFM and is not in Discount's flag list.
  If it ever appears in a `.md`, this script ignores it; add a post-pass at
  that point.
- `+autolink` is intentionally omitted: 1986 magazine text never has real URLs,
  but Discount's autolinker wraps `news:`, `tel:`, `fax:`, etc. in `<a href="…">`
  as false positives (rule 270).
- `-smarty` (leading minus = disable) suppresses Discount's smartypants
  substitutions: `(C)` → ©, `(R)` → ®, `(TM)` → ™, plus quote curling
  (`"x"` → "x"). In 64'er articles, `(C)` is body text — math formulas like
  `SIN(C)*USR(A)` (8607/139), curve labels like `Dämpfung (C)` and
  `(Kurve A) und größeren (C) Frequenzen` (8607/133), printed messages like
  `DATA ERZEUGER FERTIG! (C) J. MATERNA` (SH8501/32). The Impressum's
  legitimate `© 1986 Markt & Technik` carries the actual UTF-8 `©`
  character, not the typed sequence `(C)`, so it is unaffected.
