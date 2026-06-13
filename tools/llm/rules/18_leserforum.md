# 18 — Restructure Leserforum into the Q&A shape + banner image

**Goal:** turn the flat OCR-imported `Leserforum` article into the
project's canonical Q&A HTML shape (`<article class="qa">`, per-topic
`<section>`, `<div class="q">`, `<div class="a">`, `<p class="author">`
for askers + guest repliers, `<p class="source">` for Info footers,
banner image at the top), plus the `64er.head1` meta tag the
generator needs to render the rubric banner.

The full transformation spec is `tools/llm/new/leserforum_workflow.md`.
This rule is the dispatch + verification gate.

## Briefing for the sub-agent

The sub-agent must:

1. Render the Leserforum start page at 600 dpi: `pdftoppm -r 600
   issues/<YYMM>/64er_19XX-XX.pdf /tmp/<YYMM>_pages_600/p -png -f
   <START> -l <START>`.
2. Crop the banner image (`<START>-0.png`) from the page — envelope /
   letter motif at the top of page <START>. Verify by reading the
   crop.
3. Add `<header><img src="<START>-0.png" alt="Leserforum"
   title="Leserforum"></header>` to the article.
4. Change `<article>` to `<article class="qa">`.
5. For every `<h2>` topic heading: ALL CAPS → Title Case; wrap
   topic in `<section>`. Empty-headed page-32-style tail letters
   get a `<section>` with no `<h2>`.
6. Inside each `<section>`:
   - `<div class="q">` with the question `<p>`s. Multi-part
     questions use `(1)/(2)/(3)` plain-text numbering in separate
     `<p>`s, not `<ol>`.
   - `<p class="author">Reader Name</p>` at the end. If a postal
     address is printed, append after a `<br>` in the same
     `<p class="author">`.
   - `<p class="noindent">Ausgabe N/YY</p>` last, when this is a
     follow-up to a prior issue's question.
7. Editor's reply (when printed) → `<div class="a">` with the reply
   `<p>`s. If signed by a guest expert, end with `<p class="author">`.
8. Vendor / product / address footer → `<p class="source">Info: …</p>`
   at the end of the `<section>`.
9. Add `<meta name="64er.head1" content="Leserforum">` if missing.
   Verify `64er.toc_category=Rubriken`, `64er.id=leserforum`, NO
   `<meta name="author">`.
10. Apply the leserforum_workflow's OCR-fix list to headings and
    body (U→ll, lost spaces, `0` vs `O`, multi-hyphen artifacts).
    These are character-level OCR fixes per cleanup_workflow.md,
    not editorial rewrites.
    **Granularity matters.** OCR cleanup is allowed at the
    **word level only**. Reading a passage and replacing a single
    bad token with the obvious correct word (`darsteUen` →
    `darstellen`) is fine — that's a word-by-word OCR substitution
    where the surrounding text confirms the fix. Reading a
    paragraph and re-typing it from memory because it "reads
    better" is forbidden, even if every word change individually
    looks plausible. The boundary is **one word at a time**;
    nothing larger. See `feedback_print_verbatim` memory for the
    full rule.
11. Beautify (`npx --yes js-beautify --type html --indent-size 4
    --wrap-line-length 0 --replace`).
12. **Do not commit.** Return per-section Q&A summary table.

Critical preservation rules:
- 100% content preserved — no answer or reader address dropped.
- Original typos in reader names stay (e.g. `Bernhad Beerlage`).
- Original idiosyncrasies in print (`Im der Ausgabe 5/86`) stay.
- Old German spelling stays (`daß`, `muß`, `Adreß`).
- Don't invent answers. A question with no printed reply gets no
  `<div class="a">`.
- Don't merge two askers into one `<div class="q">` just because
  they share a section topic — separate `<div class="q">` per
  asker.

## Verification

```bash
file="issues/<YYMM>/<START> Leserforum.html"

# 1. article uses qa class
grep -q '<article class="qa">' "$file" || echo "  FAIL: missing class=qa"

# 2. banner image present
grep -q '<header>.*<img src="<START>-0\.png"' "$file" || \
  echo "  FAIL: missing banner"
ls "issues/<YYMM>/<START>-0.png" >/dev/null || echo "  FAIL: banner file missing"

# 3. required metas
grep -q '64er.head1" content="Leserforum"' "$file" || echo "  FAIL: head1 meta"
grep -q '64er.toc_category" content="Rubriken"' "$file" || \
  echo "  FAIL: toc_category"
grep -q '64er.id" content="leserforum"' "$file" || echo "  FAIL: id meta"
grep -lE '<meta name="author"' "$file" && echo "  FAIL: author meta present (must be removed)"

# 4. balanced section / div counts
python3 -c "$(cat <<'PY'
import re, sys
s = open(sys.argv[1]).read()
checks = [
    ('<section>',    '</section>'),
    ('<div class="q">', '</div>'),
    ('<div class="a">', '</div>'),
    ('<header>',     '</header>'),
]
for o, c in checks:
    # crude: count open vs close of just that exact pattern; divs share
    # </div> so the q/a sums need adding.
    n_o = s.count(o)
    print(f"  {o}: {n_o}")
PY
)" "$file"

# 5. spot-check: every <div class="q"> has a <p class="author">
python3 -c "$(cat <<'PY'
import re, sys
s = open(sys.argv[1]).read()
for m in re.finditer(r'<div class="q">(.*?)</div>', s, re.DOTALL):
    if 'class="author"' not in m.group(1):
        snippet = m.group(1)[:80]
        print(f"  q-div without author: {snippet!r}")
PY
)" "$file"
```

## Notes / lessons

- 8607's Leserforum had 27 sections (more than the median, which is
  ~15-20) because page 32 carried a tail of un-headed letters
  (Vissers, Altmann, Meyer, Schramm) — those get `<section>` with
  no `<h2>` per workflow convention.
- The banner crop coordinates need an eyeball check after cropping
  — bbox depends on each issue's print layout.
- Guest replier names are easy to miss. Look for a `(name)`-style
  signature at the end of an editorial answer; if present, wrap as
  `<p class="author">Guest Name</p>` inside the `<div class="a">`.
- The U→ll substitution pattern is endemic in this issue's
  Leserforum text — it's not editorial rewriting, it's restoring
  OCR-mangled lowercase double-L from the print's typography.
