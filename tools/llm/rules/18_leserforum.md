# 18 — Restructure Leserforum into the Q&A shape + banner image

**Goal:** turn the flat OCR-imported `Leserforum` article into the
project's canonical Q&A HTML shape (`<article class="qa">`, per-topic
`<section>`, `<div class="q">`, `<div class="a">`, `<p class="author">`
for askers + guest repliers, `<p class="source">` for Info footers,
banner image at the top), plus the `64er.head1` meta tag the
generator needs to render the rubric banner.

## Canonical HTML shape

```html
<!DOCTYPE html>
<html lang="de">

<head>
    <title>Leserforum</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../style.css">
    <meta name="64er.issue" content="N/YY">
    <meta name="64er.pages" content="16-17">
    <meta name="64er.head1" content="Leserforum">
    <meta name="64er.toc_category" content="Rubriken">
    <meta name="64er.id" content="leserforum">
</head>

<body>
    <article class="qa">
        <header>
            <img src="16-0.png" alt="Leserforum" title="Leserforum">
        </header>

        <section>
            <h2>Topic title in natural case?</h2>

            <div class="q">
                <p>Question text…</p>
                <p class="author">Reader Name<br>Street 12, 9999 City</p>
                <p class="noindent">Ausgabe N/YY</p>
            </div>

            <div class="a">
                <p>Editor's reply…</p>
                <p class="author">Guest Replier Name</p>
            </div>

            <p class="source">Info: vendor info, address, product details</p>
        </section>

        <!-- repeat <section> per topic -->
    </article>
</body>
</html>
```

Required metas: `64er.head1=Leserforum`, `64er.toc_category=Rubriken`,
`64er.id=leserforum`. **No `<meta name="author">`** — Leserforum has
no overall author; per-question authorship lives inside each
`<p class="author">`.

## Per-section anatomy

Inside each `<section>`:
- `<h2>` — topic heading in **German natural (sentence) case** (OCR
  import usually delivers ALL CAPS; convert per rule 25's natural-case
  rules — NOT English Title Case). Older issues (8601–8605) used Title
  Case; new issues use natural case for both Leserforum and article
  headings. Empty-headed tail letters (page-32 style) get a
  `<section>` with no `<h2>`.
- One or more `<div class="q">` — questions. Multiple `<div class="q">`
  per section when the editor groups two readers asking the same
  thing.
- Optionally one `<div class="a">` — the editor's reply (when
  printed). Some questions are unanswered ("Wer kann helfen?" calls
  for reader replies in the next issue).
- Optionally one `<p class="source">` — Info / vendor address /
  product footer.

Inside `<div class="q">`:
- One or more `<p>` for the question body. Multi-part questions use
  plain-text `(1) / (2) / (3)` numbering as separate `<p>`s — NOT
  `<ol>`.
- `<p class="author">` for the asker. Convert ALL CAPS to Title Case
  (`HANS FUSS` → `Hans Fuss`). If the asker's postal address is
  printed, append it inside the **same** `<p class="author">` after
  a `<br>` — not a separate paragraph.
- `<p class="noindent">Ausgabe N/YY</p>` last, when this is a
  follow-up to a prior issue's question.

Inside `<div class="a">`:
- One or more `<p>` for the reply body. Multi-part answers mirror
  the question's `(1) / (2)` numbering.
- Optionally one `<p class="author">` at the end if the reply is
  signed by a guest expert (not the editorial team). Editorial
  team's own answers are unsigned.

`<p class="source">` goes after `</div>` of the last `<div class="a">`,
inside the same `<section>`. Used for printed `Info:` blocks
(vendor address + price + product details):
```html
<p class="source">Info: Vendor Name, Street 1, 12345 City<br>
    Product Name, 49 Mark</p>
```

## Special cases

**Long reader letters** (fan letter / opinion piece, not a question):
treat like a single-question `<section>` — `<h2>` title,
`<div class="q">` with all prose `<p>`s, `<p class="author">` at end,
no `<div class="a">`.

**Intro `<aside>`** ("Fragen Sie doch" submission rules): reproduce
as a normal `<aside>` between two `<section>` elements.

## Briefing for the sub-agent

The sub-agent must:

1. Render the Leserforum start page at 600 dpi: `pdftoppm -r 600
   issues/<YYMM>/64er_19XX-XX.pdf /tmp/64er_<YYMM>_pages_600/p -png -f
   <START> -l <START>`.
2. Crop the banner image (`<START>-0.png`) from the page — envelope /
   letter motif at the top of page <START>. Verify by reading the
   crop.
3. Add `<header><img src="<START>-0.png" alt="Leserforum"
   title="Leserforum"></header>` to the article.
4. Change `<article>` to `<article class="qa">`.
5. For every `<h2>` topic heading: ALL CAPS → German natural case (rule 25); wrap
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
10. Apply word-level OCR fixes to headings and body:
    `U→ll` (`darsteUen` → `darstellen`), lost spaces
    (`aufjedenfalls` → `auf jedenfalls`), `0` ↔ `O` confusions
    inside letter runs, lost line-break hyphens (`Druk-ker` →
    `Drucker`), multi-hyphen artifacts (only the LAST hyphen is a
    line break unless the final segment starts uppercase). These
    are character-level OCR fixes, not editorial rewrites.
    OCR errors `0`/`O` confusion in heading: `Z80-MAKR0` →
    `Z80-Makro`. Letter-letter: `INTEREACE` → `Interface`,
    `PROIEKTOREN` → `Projektoren`, `DlN-A4` → `DIN-A4`.
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

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every structural transformation the sub-agent applies
to Leserforum must be backed by **runnable verifier evidence pasted
verbatim into the report**:

- For each `<section>` emitted, paste the topic heading (post-Title-
  Case conversion) and the print page it came from.
- For each ALL-CAPS → Title Case conversion (heading, asker name,
  Guest replier), paste the verbatim original and the converted form,
  e.g. `HANS FUSS → Hans Fuss`.
- For each `<p class="source">Info: …</p>`, paste the verbatim
  vendor/address line so the orchestrator can confirm no address was
  modernised.
- For each Pass-10 word-level OCR fix applied, paste the one-line
  `pdftotext` cross-check (rule 27's evidence form) showing the
  print's actual form is the corrected one, e.g.
  ```
  pdftotext -layout -f 16 -l 16 issues/<YYMM>/64er_19XX-XX.pdf - | grep -i Drucker
  ```
- Per-section count: paste the final `<section>` total + the
  `<div class="q">` count, so the orchestrator can confirm no asker
  was silently merged or dropped.

**No verifier output, no claimed transformation.** A Q&A
transformation reported without the per-section evidence is treated
as un-applied; the orchestrator will re-dispatch. "Trust me, I
preserved every asker" is never acceptable — dropped readers turn
into invisible data loss.

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
