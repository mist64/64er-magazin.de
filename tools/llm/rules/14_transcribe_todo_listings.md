# 14 — Transcribe `<pre>TODO</pre>` listings from the printed scan

**Goal:** turn every `<pre>TODO</pre>` placeholder (and the lone
`<p>TODO LISTING</p>` if any) into a verbatim transcription of the
printed listing from the magazine scan. These are listings that the
print published but the source D64 did not ship — they're "additional
listings not on disk" (Pascal, Z80 asm, MSE hex blocks, raw 6502
disassembly of in-ROM code, short BASIC snippets).

This rule fires after rule 10 (place_figures) has done its work — that
step's "emit `<pre>TODO</pre>` for unfound listings" behaviour
generates the placeholders.

## What `<pre>TODO</pre>` means

Some listings are printed in the magazine but do NOT ship as a file
on the disk — either because they're a one-shot pre-step that
produces something else, the disk omitted them for space, the print
is an assembler disassembly of an in-ROM routine, or the language is
non-C64 (Pascal, Z80 asm). Even so, rule 10 emits a `<figure>` block
with the verbatim caption and `<pre>TODO</pre>` as the body so the
gap is visible in the rendered HTML. Rule 14's job is to OCR the
printed listing into the `<pre>` body.

## Cropping listing regions from the page scan

Don't guess crop coordinates by trial-and-error. Use rule 0's
"page block index" recipe to build `/tmp/p<NNN>_blocks.txt`, then
grep for the `Listing` caption line:

```bash
grep -i "listing" /tmp/p<NNN>_blocks.txt
# → block=22 bbox=825x84+195+1955 text= Listing 1. Komprimierte Version ...
```

The bbox tells you the caption's column (`X`, width `W`) and
top-edge (`Y`). The listing code sits **above** the caption in the
same column. Walk preceding blocks whose x-range overlaps the
caption's x-range — the topmost is your crop's top edge. Add ~50 px
padding.

One-shot crop:
```bash
magick /tmp/<YYMM>_pages_300/p-NNN.png \
  -crop <W>x<H>+<X>+<Y> +repage /tmp/listing.png
```

## Briefing for the sub-agent

The sub-agent must:

1. Render the issue PDF to `/tmp/<YYMM>_pages_300/p-NNN.png` at **`-r
   300`** (higher resolution than the figure-placement pass — small
   monospace listing text needs every pixel).
2. For every `<pre>TODO</pre>` placeholder in `issues/<YYMM>/*.html`:
   - Read the adjacent `<figcaption>` to identify which listing + page.
   - tesseract-locate the caption's bbox in the rendered page.
   - `magick` crop the listing region above (or beside) the caption
     with ~50px padding.
   - Dispatch a **sub-sub-agent** to OCR the crop and return the text.
     The sub-sub-agent gets: crop path, language (BASIC / Pascal /
     6502 asm / MSE hex), the anti-memory rule, the verbatim-typo
     rule.
   - Splice the OCR text into the `<pre>` via the shell `head + cat +
     tail` pattern (NOT the Edit tool — multi-line code retyped via
     Edit is a memory write, forbidden).
3. Also resolve any `<p>TODO LISTING</p>` (the rule-3 markdown→html
   conversion sometimes emits this as a paragraph placeholder for
   inline declarations) — replace with an unwrapped `<pre>` block if
   the printed text is short and uncaptioned, or with a
   `<figure>`-wrapped one if it has a Listing N caption.
4. Beautify touched files (`npx --yes js-beautify --type html
   --indent-size 4 --wrap-line-length 0 --replace`). **Verify
   beautify did not collapse `<pre>` content** — it shouldn't, but
   double-check.
5. **Do not commit.** Return a per-listing table: file, listing
   number, language, line count, source page, any `[ILLEGIBLE]`
   lines, any unfilled placeholders.

Critical preservation rules (per anti-memory + verbatim-typo
principle):
- Preserve exact whitespace, indentation, column alignment, line
  numbers as printed.
- Preserve old German spelling (`daß`, `muß`, `ß`).
- Preserve printed typos verbatim (`einstellungsjahr` vs
  `einstelljahr` inconsistencies, missing commas in floats, mixed
  case opcode bytes, `>91 AND <64` impossible logical conditions).
- Preserve BASIC checksummer brackets (`<238>`, `<004>`) on Checksummer
  listings.
- Preserve assembler comment columns and semicolons.
- Pascal `:=`, `BEGIN`/`END`, `THEN`/`ELSE`, `ARRAY [n..m] OF`
  exactly.

## Verification

```bash
dir=issues/<YYMM>

# 1. no <pre>TODO</pre> left
grep -l '<pre>TODO</pre>' "$dir"/*.html && echo "  FAIL: <pre>TODO</pre> survived"

# 2. no <p>TODO LISTING</p> left
grep -l '<p>TODO LISTING</p>' "$dir"/*.html && echo "  FAIL: TODO LISTING survived"

# 3. every <figcaption>Listing N…</figcaption> has a non-empty <pre>
#    body before it (filled, not the placeholder)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
bad = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    # for each <figure> with a Listing figcaption, ensure the <pre>
    # body is not empty / not "TODO"
    for m in re.finditer(r'<figure[^>]*>(.*?)</figure>', s, re.DOTALL):
        body = m.group(1)
        if not re.search(r'<figcaption>Listing\s+\d+', body): continue
        pre_m = re.search(r'<pre[^>]*>(.*?)</pre>', body, re.DOTALL)
        if pre_m:
            inner = pre_m.group(1).strip()
            if inner in ('', 'TODO'):
                print(f"  empty Listing pre in {f}"); bad += 1
sys.exit(1 if bad else 0)
PY
)" "$dir"

# 4. spot-check: every transcribed BASIC listing has line numbers at
#    the start of (most) lines. If a "BASIC" file has zero lines that
#    look like a BASIC line-number prefix, the OCR may have eaten
#    them.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<pre[^>]*>(.*?)</pre>', s, re.DOTALL):
        body = m.group(1)
        if not body.strip(): continue
        lines = [l for l in body.splitlines() if l.strip()]
        if len(lines) < 3: continue
        # heuristic: > 60% of lines start with digit → likely BASIC
        digit_starts = sum(1 for l in lines if re.match(r'\s*\d', l))
        if digit_starts == 0 and len(lines) >= 10:
            # 0 digit-prefixed lines in a 10+ line block → probably
            # asm or Pascal; not a flag
            pass
PY
)" "$dir"
```

## Notes / lessons

- The 8607 sweep transcribed 9 placeholders across 4 articles
  (36 Modem, 79 T&T Profis, 85 C128 Reise, 136 Pascal-Kurs). Pascal
  is the most common "not on disk" language in any issue — the disk
  format is C64-specific, so non-C64 source code never ships.
- Watch out for the `<p>TODO LISTING</p>` pattern (single paragraph
  placeholder) vs. the rule-10 `<figure><pre>TODO</pre>` pattern
  (full figure wrapper). They're emitted by different upstream
  steps and resolve to different shapes.
- `js-beautify` is well-behaved with `<pre>` by default but worth
  checking once after the run.
- 300 dpi is the right target resolution for listing OCR. The
  150 dpi figure-placement scans are too coarse for column-aligned
  asm code.
- The "Listing N body references without a `<figure>`" check this
  step's sub-agent can produce is useful follow-up data — sometimes
  the OCR pipeline dropped a whole listing, not just left a TODO
  placeholder.
