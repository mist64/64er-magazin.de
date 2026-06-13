# 16 — Fill or remove `<meta name="author">` per article

**Goal:** every article in `issues/<YYMM>/` has either a correctly
filled `<meta name="author" content="…">` (signed by the bylines that
appear in the body), OR the line is removed entirely (for the
unsigned recurring rubrics). No `content="XXX"` placeholder may
survive. Side-effect: a sweep also catches stray mid-body `(byline)`
paragraphs that split.py missed and converts them to
`<address class="author">`.

## Three rules

**Rule 1 — most articles fill from bylines.** For a normal article,
`content` lists the bylines that appear in the body, in the order
they appear. Use editor initials exactly as printed (`bs`, `hm`, `ev`,
etc., or expanded to full names from the previous issue's Impressum:
"Boris Schneider", "Harald Meyer", "Volker Everts"). External
contributors come first if their full name is in the byline; in-house
editor initials trail. Examples:
```html
<meta name="author" content="bs, bs, hm, ev, hm">      <!-- Aktuelles: 5 newsletter items by 4 editors -->
<meta name="author" content="Heimo Ponnath, dm">       <!-- Basic→Assembler: guest author + in-house editor -->
<meta name="author" content="Michael Scharfenberger">  <!-- editorial -->
```
Body byline `(bs/hm)` → meta `bs, hm`.

**Rule 2 — unsigned articles get NO meta tag.** Delete the line
entirely (don't leave empty `content=""`, don't leave `XXX`) for:
- **Leserforum** (per-question authorship — each `<p class="author">`
  inside the Q&A has its own asker)
- **Impressum** (the body IS the masthead — every editor listed there)
- **Vorschau** (unsigned editorial preview of next issue)
- **Fehlerteufelchen** (corrections column, unsigned)
- **»Anwendung des Monats«** call-for-entries (unsigned)
- **»Listing des Monats«** call-for-entries (unsigned)
- Other contest announcements (»Wettbewerb: Bewegte Grafik«, etc.)
- **»Wie schicke ich meine Programme ein?«** (submission rules)
- House ads / Sonderheft promos with no body byline (Eigenanzeigen)

**Rule 3 — editorial gets the chief editor.** The editorial column
is *unsigned-feeling* (no `(initials)` byline at the end), but the
body ends with a chief-editor signature line. The meta lists that
name. Chief-editor mapping: Michael M. Pauly through 8603,
Michael Scharfenberger from 8604 onward.

**Rule 4 — placeholder `XXX` is invalid.** Template ships with
`content="XXX"`. Must be replaced with a real name or the line
removed. Don't leave `XXX` in any article.

## Per-byline expansion vs. tip-column dedupe

Two shapes exist in the wild and the rule used to leave the choice
implicit; pin it explicitly here.

**DEFAULT — per-byline expansion.** One entry in `content="…"` per
`<address class="author">` in the body, **in body order, INCLUDING
repeats**. Example: `<meta name="author" content="bs, bs, hm, ev,
hm">` for Aktuelles with 5 newsletter items by 4 editors (bs writes
two of them, hm writes two).

**EXCEPTION — Tips & Tricks–style multi-byline articles.** In
columns where each sub-section is its own mini-byline (Tips & Tricks
für Profis / Einsteiger / C 16, similar), dedupe the OVERALL meta
across sub-sections: **lead editor first** (the one bylined on the
top-level article header / Foreword), then **unique sub-authors in
first-appearance order**. Example: `79 Tips & Tricks für Profis`
uses `tr, Name1, Name2, …` where `tr` is the column's lead editor
(bylined on the column intro) and each `NameN` is a distinct tip
author appearing in the order their tip is printed.

**How to pick.** Apply the exception only when every / nearly every
`<h2>`-or-`<h3>` sub-section has its own `<address class="author">`
AND the article has a lead editor distinct from the tip authors. A
news-roundup with shared editor initials (Aktuelles, DFÜ-NEWS) is
NOT the exception — it's the default; repeat initials.

**Anti-pattern.** Don't mix the two shapes within one article: don't
dedupe inside an Aktuelles-style roundup, don't expand-with-repeats
inside a Tips & Tricks column.

## Briefing for the sub-agent

The sub-agent must:

1. `grep -l 'name="author" content="XXX"' issues/<YYMM>/*.html` — get
   the placeholder set.
2. `grep -L 'name="author"' issues/<YYMM>/*.html` — get the missing
   set (should match the Rule-2 unsigned-rubric list; flag anything
   else).
3. For each placeholder:
   - **Rule 2** (unsigned rubric: Leserforum, Impressum, Vorschau,
     Fehlerteufelchen, Anwendung-des-Monats, Listing-des-Monats,
     other contest calls, »Wie schicke ich meine Programme ein?«,
     and house-ad / Sonderheft Eigenanzeigen with no byline) →
     **delete the meta line**.
   - **Rule 3** (editorial column by the chief editor) → set
     `content="Michael Scharfenberger"` (from 8604 onward; was
     Michael M. Pauly through 8603).
   - **Rule 1** (normal article) → read the body's bylines
     (`<address class="author">(…)</address>`) and concatenate them
     in the order they appear. Expand initials → full names from
     the previous issue's Impressum (typically
     `issues/<PREV>/<NNN> Impressum.html`).
4. Sweep `grep -E '<p>\(([a-z]+|[A-Z][a-zA-Z]+)' issues/<YYMM>/*.html`
   for surviving `(byline)` paragraphs. If real bylines (not
   formula connectives like `(und)`, `(oder)`), convert to
   `<address class="author">(…)</address>` and update the meta if
   needed.
5. Beautify touched files.
6. **Do not commit.** Return per-file action table: file → action
   (FILLED with content="…", REMOVED, NO CHANGE), plus any
   deviations from the planned action (e.g. "planned FILL but
   article has no body byline → REMOVED instead") with reason.

Critical guardrails:
- No `XXX` may survive. No empty `content=""` either.
- Don't invent author names. Initial → full name comes from the
  previous issue's Impressum, period.
- Don't add a `<meta name="author">` to an unsigned rubric just
  because the file template suggested one.
- House-ads / Sonderheft promos with no body byline are
  Eigenanzeigen — treat as unsigned (remove meta).

## Verification

```bash
dir=issues/<YYMM>

# 1. no XXX left
grep -l 'name="author" content="XXX"' "$dir"/*.html && echo "  FAIL: XXX left"

# 2. no empty content=""
grep -lE 'name="author" content=""' "$dir"/*.html && echo "  FAIL: empty content"

# 3. articles missing meta must match the Rule-2 unsigned list. Cross-
#    check against the same article in the previous issue: if 8606's
#    Leserforum has no meta, 8607's Leserforum should also have none.
python3 -c "$(cat <<'PY'
import os, re, sys
d, prev = sys.argv[1], sys.argv[2]
def has_meta(path):
    return bool(re.search(r'<meta name="author"', open(path).read()))
# build set of recurring rubric titles from prev that lack meta
no_meta_prev = set()
for f in os.listdir(prev):
    if not f.endswith('.html'): continue
    if not has_meta(os.path.join(prev, f)):
        title_key = re.sub(r'^\d+ ', '', f).split('.')[0][:30]
        no_meta_prev.add(title_key)
# now check current issue
for f in os.listdir(d):
    if not f.endswith('.html'): continue
    p = os.path.join(d, f)
    title_key = re.sub(r'^\d+ ', '', f).split('.')[0][:30]
    if has_meta(p):
        # ok if it's not a recurring unsigned rubric
        pass
    else:
        # missing meta — must be in the unsigned list or be a one-off
        # that the orchestrator has approved (e.g. Eigenanzeige)
        if title_key not in no_meta_prev:
            # not in the recurring list; flag for review
            print(f"  no-meta one-off in current issue: {f}")
PY
)" "$dir" "<PREV_DIR>"

# 4. every meta name=author content has at least one comma-separated
#    name made of letters / spaces / dots
grep -hE 'name="author" content=' "$dir"/*.html | \
  grep -vE 'content="[A-Za-zÄÖÜäöüß., ]+"' && echo "  FAIL: malformed content"

# 5. shape consistency: an article whose meta `content` has duplicate
#    entries must have a matching count of body bylines (per-byline
#    expansion shape). If the meta has duplicates but the body has
#    fewer (or no repeated) `<address class="author">` tokens, the
#    article is using the wrong shape — likely the expansion shape
#    applied to a tip-column article, or stale duplicates from an
#    earlier pass.
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    m = re.search(r'<meta name="author" content="([^"]*)"', s)
    if not m: continue
    parts = [p.strip() for p in m.group(1).split(',') if p.strip()]
    if len(parts) == len(set(parts)): continue  # no duplicates
    # has duplicates → expansion shape expected; body byline count
    # should be >= len(parts)
    body_bylines = re.findall(r'<address class="author">', s)
    if len(body_bylines) < len(parts):
        print(f"  {f}: meta has {len(parts)} entries ({len(parts)-len(set(parts))} dup) "
              f"but only {len(body_bylines)} body <address class=\"author\"> — "
              f"shape mismatch (expansion vs dedupe)")
PY
)" "$dir"
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every `<meta name="author">` action the sub-agent
performs must be backed by **runnable verifier evidence pasted
verbatim into the report**:

- For each FILLED meta, paste the body's byline count and the
  `content="…"` entry count, e.g.
  ```
  8 Aktuelles.html → grep -c '<address class="author">' = 5
                     meta content="bs, bs, hm, ev, hm" → 5 entries
  ```
  so the orchestrator can confirm the per-byline-expansion shape (or
  the dedupe-for-tip-columns exception) is consistent.
- For each REMOVED meta, paste the one-line classification
  ("Leserforum: per-question authorship in `<p class="author">`",
  "Sonderheft promo: Eigenanzeige, no body byline").
- For each initial → full name expansion, paste the one-line grep
  result from the previous issue's Impressum showing the source
  mapping, e.g.
  ```
  grep -E '\(bs\)|Boris Schneider' issues/<PREV>/<NN> Impressum.html → "Boris Schneider (bs)"
  ```

**No verifier output, no claimed meta action.** An action reported
without the byline-count evidence (for FILLED) or the rubric
classification (for REMOVED) is treated as un-applied; the
orchestrator will re-dispatch. "Trust me, I matched the bylines"
is never acceptable — author meta is high-leverage editorial
provenance.

## Notes / lessons

- 8607's `16 DER C 64 IN FORSCHUNG UND TECHNIK.html` (first-person
  unsigned essay) and `40 PEEKs und POKEs für C 64 und C 128.html`
  (Sonderheft promo / Eigenanzeige) both ended up REMOVED rather than
  FILLED — verify the article body before defaulting to FILL.
- Don't false-positive math-formula connectives like `<p>und</p>` /
  `<p>oder</p>` as bylines in the mid-body sweep.
- The chief-editor mapping changed in 8604: through 8603 it was
  Michael M. Pauly, from 8604 it's Michael Scharfenberger.
