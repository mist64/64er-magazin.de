# 030 — Put the pages back together into articles

**Goal:** one consolidated `<YYMM>.md` for the issue — every article in reading
order, with its page range in the title — from the per-page corpus of step 020.
This is the file step 040 onward operate on.

This is a **program step** that makes exactly one model call for the whole issue.

## What only exists once the pages are back together

1. **Where an article begins and ends.** A page routinely holds the end of one
   article and the start of the next, so the unit is the **paragraph**, not the
   page. Grouping whole pages cannot express the issue.
2. **A paragraph running over a page break is one paragraph.** Same test as a
   column break — the continuation is not indented, or the paragraph before it
   ends on a German function word — because it is the same physical fact.
   Until this step existed every page boundary was a false paragraph break.
3. **Where an interrupted article resumes.** `Fortsetzung auf Seite 146`. Five
   such jumps in 8609, each confirmed in **both** directions before joining.
4. **The line-break hyphens**, resolved over the distinct broken words.

Only (1) needs judgement, and it gets the one model call: the running heads, the
table of contents and the headline fragments are all evidence about the same
question and only make sense together. Everything else here is deterministic.

## Run

```bash
tools/img/scan2ocr/rules/r030_assemble.sh
```

## Outputs

```
<YYMM>.md         every article, in issue order   <- the handover to step 040
articles.json     the structure, machine-readable
hyphens.json      resolved line-break hyphens (cache)
```

## The three shapes an article can take

| | title comes from | example |
|---|---|---|
| **department** | the **running head** — the magazine prints no headline for the run | `Aktuelles [8-12]` with 22 news items as `##` |
| **column** | the **printed headline** | `Tips & Tricks für Einsteiger [64-65]`, 8 tips as `##` |
| **article** | its own headline | everything else |

A shared running head never merges by itself: `Tips & Tricks` runs over pages
62–96, most of which carry full articles.

## Conventions this step must produce, because step 080 (split) reads them

- `# Title [12-14, 17]` — the page range in the h1, comma-separated ranges. A
  page carrying two articles appears in **both**: lossy for the page, correct
  for both articles.
- a byline is **always its own paragraph**, kept verbatim — `(bs)` or
  `(Knut Smoczyk/tr)`.

## Verification

```bash
cd tools/img/scan2ocr/rules
python3 - <<'PY'
import r030_assemble as A
stream, pi = A.page_stream()
c = A.candidates(stream); v = A.ask_boundaries(stream, c, pi)
segs = A.split_articles(stream, c, v); arts = A.merge_continuations(segs)
acts = {i: v.get(n, {}) for n, (i, _) in enumerate(c)}
drop  = {i for i, a in acts.items() if a.get("action") == "drop"}
title = {i for i, a in acts.items() if a.get("action") == "start"
         and stream[i]["role"] == "title" and not a.get("keep_heading")}
mark  = {i for i, p in enumerate(stream) if A.FORTSETZUNG.search(p["text"])}
kept  = sum(len(a["paras"]) for a in arts)
tot = kept + len(title - mark - drop) + len(drop - mark) + len(mark)
print(f"paragraphs {len(stream)}  accounted {tot}  UNEXPLAINED LOSS {len(stream) - tot}")
PY
```

**Every paragraph must be accounted for**: in an article, used as a title,
dropped as a headline fragment, or a cross-reference. Unexplained loss must be
**0** — this is the check that catches a boundary rule quietly eating text.

Also confirm: no `¬` survives, and every `#` line carries a page range.

```bash
md=$(python3 -c "import sys; sys.path.insert(0,'tools/img/scan2ocr/rules'); import r030_assemble as A; print(A.ISSUE_MD)")
grep -c '¬'            "$md"    # expect 0
grep -c '^# .*\[[0-9]' "$md"    # expect = article count
```

`ISSUE_MD` is a constant at the top of `r030_assemble.py` and points into the
issue's working directory, not into the repo -- ask the module for it rather
than assuming a path.

## The coverage gate — catching content that was DROPPED

The defect this step cannot see by inspection is **omission**: if a block never
made it out of the OCR, the article still reads perfectly, and no spell-check,
markup grep or beautifier will ever flag it. Issue 8609 shipped with two whole
ratings boxes, a function table, four `<h2>`s and two truncated article endings
missing before anyone noticed — all found by reading pages against the HTML,
which does not scale.

`r030_coverage_check.py` makes it mechanical. Stage B records the blocks it
selected as article content in `<page>.labels.json` as `order`. The invariant:

> **every block the classifier kept must appear in the article that claims its
> page.**

```bash
tools/img/scan2ocr/rules/r030_coverage_check.py issues/<YYMM> <ocr-out-dir>
```

It prints `pages N   kept prose blocks N   UNACCOUNTED n (x%)` and then each
unaccounted block with its page, label, match fraction and opening words.

Run it after step 030 and again at the end of the issue. **Investigate every
hit.** On 8609 after the full review pass it reports 3 of 613 (0.5%), and all
three are explainable false positives:

- a block whose text begins where a drop-cap was eaten (`as tun` vs the restored
  `Was tun`) — our own correction moving the text away from the OCR
- a listing fragment deliberately deleted as a duplicate of the placed listing
- a table whose cells now split the text, so the 4-word probes straddle cells

Known false-positive sources, all excluded or expected:
- **listing blocks** are skipped — the disk `.txt` is the correct petcat
  rendering while the OCR reading of the printed listing is garbled (`mps 891`
  for `mps 801`), so they never match
- **ads and non-article matter** are already excluded by using `order` rather
  than every block on the page; before that filter, p140's Markt&Technik job ad
  produced six spurious hits
- **our own OCR corrections** move HTML text away from the OCR, which is why the
  threshold is a low fraction of probes rather than an exact match
