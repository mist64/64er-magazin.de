# 16 — Fill or remove `<meta name="author">` per article

**Goal:** every article in `issues/<YYMM>/` has either a correctly
filled `<meta name="author" content="…">` (signed by the bylines that
appear in the body), OR the line is removed entirely (for the
unsigned recurring rubrics). No `content="XXX"` placeholder may
survive. Side-effect: a sweep also catches stray mid-body `(byline)`
paragraphs that split.py missed and converts them to
`<address class="author">`.

The full policy lives in `tools/llm/new/author_meta_workflow.md` and
is the authoritative reference (Rule 1 = fill from bylines, Rule 2 =
unsigned rubrics get NO meta, Rule 3 = editorial gets the chief
editor's name). This rule file is the dispatch + verification gate.

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
```

## Notes / lessons

- 8607's `16 DER C 64 IN FORSCHUNG UND TECHNIK.html` (first-person
  unsigned essay) and `40 PEEKs und POKEs für C 64 und C 128.html`
  (Sonderheft promo / Eigenanzeige) both ended up REMOVED rather than
  FILLED — verify the article body before defaulting to FILL.
- Don't false-positive math-formula connectives like `<p>und</p>` /
  `<p>oder</p>` as bylines in the mid-body sweep.
- The chief-editor mapping changed in 8604: through 8603 it was
  Michael M. Pauly, from 8604 it's Michael Scharfenberger.
