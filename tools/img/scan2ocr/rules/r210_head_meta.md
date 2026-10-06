# 210 — Fill `64er.head1` / `64er.head2` from page headers

**Applies to:** all — Sonderhefte print running heads too, and the published corpus captures them — `SH8507` has `head1` on 27 of 28 articles (Anwendung, Statistik, Finanzen, …), `SH8506` on 31 of 32. If a given issue's print carries no header band, the rule's own per-page evidence requirement yields no meta; that is a per-page fact, not a kind fact.

**Goal:** every interior-page article gets the running-header text
that's printed at the top of its start page captured into
`<meta name="64er.head1">` (section / column name) and
`<meta name="64er.head2">` (target machine label). The metas live
immediately before the existing `<meta name="64er.toc_category">`.

Editorial / Impressum / Vorschau / Inhalt are explicitly excluded
(rubrics with no running header). Leserforum already gets `head1`
from rule 200 — leave it alone.

## What's on the page

Two short lines at the very top of a typical 64'er interior page:
- left side: `Aktuelles` / `Hardware` / `Kurs: Von Basic zu Assembler`
  / `Tips & Tricks` / `Datenfernübertragung` / `Spiel` / ...
- right side: `C 64` / `C 128` / `C 64/C 128` / `C 64/VC 20` /
  `C 16/C 116/Plus 4`. Sometimes absent.

  **The machine names are SPACED, whatever the band sets.** Owner,
  2026-10-04: *"space. C 64, C 128, C 16, C 116, VC 20."* — see r000's
  CONSISTENCY WITH THE PAGE, where these names are now the one standing
  exception. The examples here were already all spaced; what was missing was
  the statement, so SH8603 set its bands CLOSED to match a body type whose
  thin gap measures neither way, and the issue ended with both forms in it.
  Read the band for the WORDS and the slashes; set the spacing from this rule.

Both come from the OCR / vision read of the top ~250 px of the
rendered page. Anti-memory: never compose either value from the
article's category — the print is the source.

## A LETTERED `b` START PAGE SHARES THE `a` ARTICLE'S BAND

Where r080 has given two articles the same start page as `NNNa` and `NNNb`,
there is **one** printed band on that page, and it sits above the `a` article.
It is still the band for both: the page's running head describes the page.

So read it once and write it to both, unless the `b` article continues onto a
page of its own whose band differs — then the `b` article takes ITS page's
band, because that is the band above its own text. SH8603's `77b` had no
guidance either way and had to be decided by hand.

Record in LOG.md which page each value was read from; with a shared start page
the per-page evidence requirement cannot be satisfied by the page number
alone.

## `&` IN A head1 VALUE: BOTH FORMS ARE IN THE CORPUS

`r210_head_meta_apply.py` writes through `html.escape`, so it emits
`Tips &amp; Tricks`. MEASURED over the published corpus: **159 files carry the
literal `Tips & Tricks` and 52 carry `Tips &amp; Tricks`** (plus one
`Tips&Tricks`). Both parse to the same string, so nothing is broken and
neither is being changed retroactively — but **any grep over `head1` must
accept both forms**, or it silently misses a quarter of the corpus. The
checks below do.

## Briefing for the sub-agent

The sub-agent must:


```bash
# The repo venv, not bare python3: r010_ocr_blocks imports numpy and scipy,
# which the system python does not have, so `python3` makes SRC silently EMPTY
# and every crop below then fails on "/NNN.png". MEASURED on 8611.
PY=${PYTHON:-.venv/bin/python}
SRC=$("$PY" -c 'import sys; sys.path.insert(0, "tools/img/scan2ocr/rules")
import r010_ocr_blocks as OB; print(OB.SRC_DIR)')     # <tmp>/masters600
```

1. The page image is `"$SRC/NNN.png"` from `masters600` — 600 dpi, A4,
   deskewed. For a 300 dpi look, `-resize 50%` of that; never a render of
   the issue PDF, which does not exist until step 006. See r000, *THE PAGE
   IMAGE IS `masters600`*.
2. Build article → start-page map from each file's
   `<meta name="64er.pages" content="N-M">`.
3. Skip the rubrics: `editorial`, `impressum`, `inhalt`, `vorschau`
   (look up by `64er.id`). Also skip the Leserforum (already has
   head1).
4. For each remaining article, dispatch a SUB-SUB-AGENT per unique
   start page:
   - Input: the 300 dpi rendered page PNG and a short prompt.
   - Crop the top ~250 px header strip (`magick … -crop FULLW x250+0+0`).
   - Sub-sub-agent returns `head1=...|head2=...` (head2 may be
     empty when the print shows no machine label).
5. Apply OCR-cleanup substitutions before writing:
   - `C 64IC 128` / `C 64 IC 128` / `C 64_C 128` → `C 64/C 128`
   - `C_64AIVC 20` → `C 64/VC 20`
   - similar slash recovery patterns.
6. Insert `<meta name="64er.head1" content="...">` then
   `<meta name="64er.head2" content="...">` (omit head2 if empty)
   directly before the existing `<meta name="64er.toc_category">`
   line.
7. Beautify (`npx --yes js-beautify --type html --indent-size 4
   --wrap-line-length 0 --replace`).
8. **Do not commit.** Return per-article table.

Critical guardrails:
- Anti-memory. Header text comes from OCR of the rendered page.
- A spread article (16-21) uses only the start page's header.
- The `head1` you write may NOT match the article's
  `<meta name="64er.toc_category">` — the print is the source. The
  8607 issue had `49 Variosystem` printed under "Listing des
  Monats" but categorised under Hardware-Test; the head1 follows
  the print, the toc_category follows our editorial categorisation.

## Verification

```bash
dir=issues/<YYMM>

# 1. how many articles got head1 — and make the target checkable by
#    also printing the total article count and the exclusion list, so
#    N should equal (article count − excluded). Excluded rubrics:
#    editorial, impressum, inhalt, vorschau, leserforum.
n=$(grep -lE '64er\.head1' "$dir"/*.html | wc -l | tr -d ' ')
total=$(ls "$dir"/*.html | wc -l | tr -d ' ')
echo "  head1 in $n of $total article(s)"
# FRONT MATTER MAY OR MAY NOT CARRY A BAND, AND THIS IS NOT A GATE.
#
# The two comments that used to sit here contradicted each other: one said a
# Sonderheft Vorwort "usually DOES carry a section word" (SH8602's p3 prints
# EINLEITUNG), the other that "its page carries the band WITHOUT a section
# word -- so it is a real exclusion".  MEASURED: SH8601's vorwort has no
# head1, SH8602's and SH8603's each have one.  It is a per-page fact, exactly
# as this rule's own per-page evidence requirement says, so the check REPORTS
# the front matter rather than asserting about it.
echo "  front matter (band present or not is a per-page fact, read the crop):"
for f in "$dir"/*.html; do
  id=$(grep -oE '64er\.id" content="[^"]*"' "$f" | sed 's/.*content="//;s/"//')
  case "$id" in
    editorial|vorwort|impressum|inhalt|vorschau)
      h=$(grep -c '64er\.head1' "$f")
      printf '    %-10s head1=%s  %s\n' "$id" "$h" "$(basename "$f")" ;;
  esac
done
# Leserforum, where rule 200 already set head1 by hand -- and NOT every issue
# has one: no Sonderheft does, so a formula that always subtracts it is off by
# one on every Sonderheft.  Count it instead of assuming it.
lf=$(ls "$dir" | grep -ci leserforum || true)
echo "  Leserforum articles: $lf  (0 on every Sonderheft)"
echo "  → n plus the front-matter files WITHOUT a band plus $lf should be $total;"
echo "    any other gap is a missed article, and the crop decides which."

# 2. head1 / head2 placement is immediately before toc_category
python3 -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    if '64er.head1' not in s: continue
    h1 = s.find('64er.head1')
    tc = s.find('64er.toc_category')
    if tc < 0 or h1 > tc:
        print(f"  head1 after toc_category in {f}")
PY
)" "$dir"

# 3. machine label sanity: head2 values look like a C-something
grep -hE '64er\.head2" content=' "$dir"/*.html | \
  sed -E 's/.*content="([^"]*)".*/\1/' | \
  sort -u | head -20
# eyeball — every line should look like a Commodore machine label.
```

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every `head1` / `head2` value the sub-agent writes
must be backed by **runnable verifier evidence pasted verbatim into
the report**:

- For each article, paste a one-line note naming the cropped
  header-strip image the sub-sub-agent inspected and what the
  sub-sub-agent returned, e.g.
  ```
  16 Forschung.html → crop /tmp/64er_<YYMM>_pages_300/p-016.png band
  0,0,FULLW,250 → head1="Hardware" head2="C 64"
  ```
- For empty `head2`, paste a one-line note confirming the print band
  shows no machine label (`head2 absent: section-cover page, no
  machine box on right`).
- For each OCR-cleanup substitution applied (`C 64IC 128` →
  `C 64/C 128`, etc.), paste the verbatim raw OCR output beside the
  cleaned form so the orchestrator can confirm the substitution is
  mechanical, not editorial.

**No verifier output, no claimed head_meta.** A `head1` / `head2`
value reported without the crop-band evidence is treated as a guess;
the orchestrator will re-dispatch. "Trust me, I read the page header"
is never acceptable — head_meta drives the rendered rubric banner
and must come from the print, not from the article's
`toc_category`.

## Notes / lessons

- 44 of 47 article files in 8607 got `head1` (3 skipped:
  Fachredakteur / Impressum / Vorschau). 33 of those also got
  `head2` — the missing ~10 are articles where the print shows
  no machine label (decorative spreads, 64'er Extra pages, contest
  cover pages, CP/M-Ecke, etc.).
- An apply.py script exists at `r210_head_meta_apply.py` (beside this file)
  that reads step 010's block index
  (`<OUT_DIR>/blocks/pNNN.txt`) directly, falling back to the legacy per-issue
  `_work/pNNN/blocks.txt` layout for issues built before the chains were merged.
  Step 010 always writes the index, so there is nothing to build on demand OR skip the script and use the
  vision-only sub-sub-agent crop approach above — vision is faster
  when the header strip is the only thing you need from each page.
- Spread headers for multi-page articles can drift: e.g. an article
  starting on a "section cover" page might have a different
  running header than its body pages. The start page's header is
  authoritative — **unless the start page has no running head at all**, which
  a full-bleed photo opener does not (8612's article 52). Then use the
  article's FIRST HEADED page instead. Without this the helper has nothing to
  read and invents a head from a fragment block.
- `html.escape` writes `&#x27;` for the apostrophe, but the corpus carries a
  literal `'` — in "64'er Extra" above all. Write the literal.
- Check 1's expected-count formula is **off by one**: the Leserforum does
  carry a head1, and the check assumed it does not. It also cannot detect a
  head1 on a rubric that is supposed to be excluded, so a wrong head there
  passes silently.
