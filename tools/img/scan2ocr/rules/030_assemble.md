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
cd tools/img/scan2ocr
python assemble.py
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
cd tools/img/scan2ocr
python - <<'PY'
import assemble as A
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
grep -c '¬' <YYMM>.md                      # expect 0
grep -c '^# .*\[[0-9]' <YYMM>.md           # expect = article count
```
