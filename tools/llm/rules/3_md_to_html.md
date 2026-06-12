# 2 — Convert `.md` → `.html` (Discount / GFM)

**Goal:** convert the OCR markdown to HTML using the same engine Marked 2
uses (Discount, GFM mode), producing the `.html` next to the `.md`.

## Marked 2 GUI settings → Discount CLI flags

| Marked 2 setting | CLI |
|---|---|
| Process Markdown with **Discount (GFM)** | `markdown -G` (use the `gfm_in` entry — also gives single-LF→`<br/>`) |
| Retain line breaks in paragraphs | implied by `-G` |
| Process Markdown inside of HTML | `+html` flag |
| Generate IDs on headlines | default for Discount |
| Render GitHub checkboxes | `+github-listitem` |
| Render `~~delete~~` | `+strikethrough` |
| Render `==highlight==` | **not** in Discount; would need post-pass (n/a here) |

## Usage

```bash
tools/llm/rules/2_md_to_html.sh issues/8607/8607.md
# writes issues/8607/8607.html next to the .md
```

## Verification

- A literal `(\*\*\*)` in the .md renders as `(***)` in the HTML.
- A line ending in a single LF inside a paragraph becomes `…<br/>` in the HTML.
- `**bold**` becomes `<strong>bold</strong>`.

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
