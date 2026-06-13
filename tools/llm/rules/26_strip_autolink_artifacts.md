# 26 — Strip Discount's `+autolink` false-positive `<a>` wrappers

**Goal:** the article text in this project comes from 1986 magazine
print. It does NOT contain real URLs. Any `<a href="…">…</a>` wrapper
the markdown→HTML pass emits is a Discount `+autolink` false positive
that needs to be stripped, and `+autolink` should be dropped from
rule 3 to prevent the issue at source.

## What goes wrong

Discount with `+autolink` recognises a small set of URI schemes
(`http:`, `https:`, `ftp:`, `mailto:`, `news:`, `telnet:`, …). When
markdown source contains `…NEWS: DATEX-P-PARAMETER…`, Discount sees
the `news:` scheme prefix and wraps the token as a link to itself:

```html
DFÜ-<a href="NEWS:">NEWS:</a> DATEX-P-PARAMETER
```

The same misfire affects other "scheme-prefix"-like words: `TEL:`,
`FAX:`, `MAILTO:`, `FTP:`, anything followed by a `:`.

## Fix at source: rule 3

Rule 3 (`3_md_to_html.sh`) currently passes `+autolink` unconditionally.
Drop it. 1986 article text never has a real URL, so we lose nothing.

After the change, the discount flags become
`+html,+github-listitem,+strikethrough,+tables,+fencedcode` —
without `+autolink`.

## Fix existing damage in the issue

For every article HTML in `issues/<YYMM>/*.html` produced before
rule 3's update:

```bash
grep -lE '<a href="[A-Z]+:">' issues/<YYMM>/*.html
```

For each match: replace `<a href="X:">Y</a>` with just `Y` (the
visible text). Don't touch genuine `mailto:` or `http://` autolinks
if they exist (none should in practice — verify by reading the
match in context).

## Briefing for the sub-agent

1. Update `tools/llm/rules/3_md_to_html.sh`: drop `+autolink` from
   the Discount flags.
2. Sweep every article in `issues/<YYMM>/*.html`:
   ```bash
   grep -nE '<a href="[^"]+">[^<]*</a>' issues/<YYMM>/*.html
   ```
3. For each hit, replace the `<a href="…">TEXT</a>` with just
   `TEXT`. Anti-memory: don't paraphrase TEXT; literally just unwrap
   the anchor.
4. Beautify touched files.
5. **Do not commit.** Return per-article table: file, count of
   wrappers stripped, sample of stripped TEXT.

Critical: this is **structural unwrapping only** — the visible text
between the open and close tags stays verbatim.

## Verification

```bash
dir=issues/<YYMM>

# 1. no <a href> wrappers survive
grep -nE '<a href=' "$dir"/*.html && echo "  FAIL: <a href> left"

# 2. rule 3 no longer emits +autolink
grep -E '\+autolink' tools/llm/rules/3_md_to_html.sh && \
  echo "  FAIL: rule 3 still passes +autolink"
```

## Notes / lessons

- The visible-text TEXT is the same as the heading word, by Discount's
  autolink design (`[scheme]:` wraps as `<a href="scheme:">scheme:</a>`).
  So the unwrapping is mechanical.
- The original 8607 instance was in `9 DFÜ-NEWS_ DATEX-P-PARAMETER.html`
  on the `<h1>`: `DFÜ-<a href="NEWS:">NEWS:</a> DATEX-P-PARAMETER`
  → `DFÜ-NEWS: DATEX-P-PARAMETER`. Rule 25 then converts the
  heading to natural case.
- If a future issue genuinely cites a URL (very unlikely for 1986
  content), let the editor wrap it in `<a>` manually rather than
  reinstating `+autolink`.
