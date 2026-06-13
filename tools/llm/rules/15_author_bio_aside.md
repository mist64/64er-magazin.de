# 15 — Wrap author bio sidebars in `<aside>`, mark portraits `class="inline"`

**Goal:** for every article that has a boxed-off author biography in
print (Lebenslauf / Vita / Zur Person / Werdegang / Über den Autor /
the C.A.E. "Computer Aided Course of Life" callout pun), wrap the
bio's heading + paragraphs + portrait + signature in a single
`<aside>…</aside>` block. The bio's portrait, if it is currently a
`<figure>` with no real `Bild N` caption in print, becomes
`<img class="inline" src="…" alt="…">` (no figure wrapper).

This is a purely structural transformation. The bio prose text is
already in the HTML (from OCR import); this step only adds the
`<aside>` opening / closing tags and possibly swaps a `<figure>` for
an inline `<img>`.

## Briefing for the sub-agent

The sub-agent must:

1. Render the issue PDF to `/tmp/64er_<YYMM>_pages/p-NNN.png` at `-r 150`
   if not already done.
2. Sweep every article in `issues/<YYMM>/*.html` for headings or
   paragraphs that look like an author bio: heading text in the set
   `{Lebenslauf, Zur Person, Vita, Werdegang, Über den Autor, Wer
   ist …, C.A.E.}`, or biographical prose (`geboren`, `studierte`,
   `arbeitet seit`, `wuchs auf`, …) sitting in a yellow/tinted
   callout next to the author byline.
3. For each candidate: open the scan to confirm the print shows the
   section as a boxed-off callout. Only those qualify.
4. Wrap the heading + bio paragraphs + portrait + closing
   `<address class="author">(name)</address>` in `<aside>…</aside>`.
   Reference shape:

   ```html
   <aside>
       <h3>Lebenslauf</h3>
       <img src="50-0.png" alt="Porträt Georg Brandt" class="inline">
       <p>Bio prose…</p>
       <address class="author">(Author Name)</address>
   </aside>
   ```

5. If the portrait is currently a `<figure>` with no real `Bild N.`
   caption in print, convert it to an `<img class="inline">` (drop
   the `<figure>` + `<figcaption>` wrapper). If the print labels the
   portrait as a numbered `Bild N`, leave the `<figure>` alone —
   only the `<aside>` wrapping changes.
6. Beautify touched files via js-beautify.
7. **Do not commit.** Return per-article table.

Critical guardrails:
- **Do not invent bios.** Many articles have no author bio at all.
  If the print shows no boxed bio sidebar, do nothing.
- **Do not type bio text from memory.** The prose lives in the HTML
  (from OCR import); this step is structural-only.
- **Do not wrap non-bio callouts.** "TODO ASIDE" markers in
  methodology, contest, feature-overview, or warning callouts are
  for the line-breaks/indentation rule (rule 17), not this one.
  Methodology, "Funktionsübersicht", "Achtung!", contest
  announcements, "So funktioniert X" sidebars are NOT author bios.
- **Skip the editorial.** The chief editor's portrait in the
  editorial is `<img class="inline">` but is NOT wrapped in
  `<aside>` — that's covered by the editorial rule (rule 18).
- **TODO body text in bio boxes.** If a bio callout's prose
  hasn't been OCR'd yet (e.g. `<p>TODO two boxes with text</p>`),
  leave it for the OCR-fix pass; do not invent.

## Verification

```bash
dir=issues/<YYMM>

# 1. every <aside> is well-formed (matched closing tag)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
bad = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<aside\b', s)); c = len(re.findall(r'</aside>', s))
    if o != c: print(f"  mismatch in {f}: <aside>={o} </aside>={c}"); bad += 1
sys.exit(1 if bad else 0)
PY
)" "$dir"

# 2. every <aside> contains either a heading (h2/h3) or a portrait
#    or an address (we don't ship empty asides)
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<aside\b[^>]*>(.*?)</aside>', s, re.DOTALL):
        body = m.group(1)
        if not re.search(r'<h[23]|class="inline"|<address|<p\b', body):
            print(f"  empty-looking aside in {f}")
PY
)" "$dir"

# 3. no img.inline outside an <aside>/<editorial>/<header> — i.e. an
#    inline image is always intentional (portraits in editorial,
#    bio sidebars, leserforum). Reading any flagged file will tell
#    you whether it's a real exception.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<img [^>]*class="inline"[^>]*>', s):
        # walk back to enclosing block element
        start = m.start()
        before = s[:start]
        # find the nearest open tag among aside/figure/h1/h2/article
        if '<aside' in before:
            last_aside = before.rfind('<aside')
            last_close = before.rfind('</aside>')
            if last_close < last_aside: continue
        # not inside an aside: print for manual check
        print(f"  inline img outside aside in {f}")
PY
)" "$dir"
```

Check #3 is informational — the editorial portrait, the
Fachredakteur portrait, and the Leserforum image are all valid
`class="inline"` uses outside an `<aside>`. The flag is there so
the orchestrator can verify the listed files match a known pattern.

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every `<aside>` the sub-agent wraps must be backed
by **runnable verifier evidence pasted verbatim into the report**:

- For each `<aside>` added, paste the page number and a one-line
  scan-confirmation note (`p.50 → yellow boxed-off Lebenslauf
  sidebar next to right column of body text`) showing the print
  actually shows a callout box, not just biographical prose.
- For each `<figure>` → `<img class="inline">` conversion, paste a
  one-line note confirming the print has no `Bild N.` caption under
  the portrait.
- For each candidate considered but rejected (biographical-looking
  prose that is NOT a boxed sidebar), paste the page number and a
  one-line reason ("p.142 prose mentions `geboren in 1955` but the
  print typesets it as running body text, no callout box").

**No verifier output, no claimed aside.** An aside reported without
the page-number scan-confirmation is treated as un-applied; the
orchestrator will re-dispatch. "Trust me, I checked the scan" is
never acceptable.

## Notes / lessons

- 8607 had exactly one straight author bio (`50 R.C.S.` Lebenslauf
  for Georg Brandt). Other articles had biographical-looking
  content that turned out NOT to be boxed sidebars — discipline
  matters here, do not over-apply.
- The C.A.E. ("Computer Aided Course of Life") double-yellow box
  pattern in `49 Variosystem` is a Lebenslauf-pun bio sidebar.
  When the OCR import lands the prose, wrap each of the two boxes
  in its own `<aside>` (separate authors, separate boxes).
- Most "TODO ASIDE" placeholders in an issue are NOT author bios.
  Check each one's surrounding context against the scan before
  treating it as bio work.
