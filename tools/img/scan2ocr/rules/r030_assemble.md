# 030 — Put the pages back together into articles

**Applies to:** all — article boundaries exist in every issue. The department / column vocabulary it feeds the model is read off THIS issue's running heads and TOC, not compiled in — see *Where the issue-specific facts come from*.

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
3. **Where an interrupted article resumes.** `Fortsetzung auf Seite 146`.
   However many the issue prints (8609 printed five; a Sonderheft that runs its
   listings inline may print none), each one is confirmed in **both**
   directions before joining — the foot of the interrupted page must name the
   page that resumes it, and that page's head must name the page it came from.
   A one-sided marker is not a jump; it is an OCR miss or a print error, and it
   is reported, not acted on.
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

This taxonomy is general. **Which runs in THIS issue fall into which shape is
not** — it is read off this issue's own running heads and printed TOC, never
carried over from the last one.

| | title comes from | how to recognise it in this issue |
|---|---|---|
| **department** | the **running head** — the magazine prints no headline for the run | a run of consecutive pages under one standing running head for which the TOC and the pages themselves offer **no headline naming the run**. The head becomes the title; each item headline inside becomes a `##`. |
| **column** | the **printed headline** | a run under a standing running head that **does** print its own headline. That headline is the title; the item headlines inside become `##`. |
| **article** | its own headline | everything else — including any headline that names a specific product, program, machine or event |

Two invariants that hold in every issue:

- **A shared running head never merges by itself.** In 8609 `Tips & Tricks` runs
  over pages 62–96, most of which carry full articles. The head is evidence
  about the section, not about the unit.
- **A standing name recurs and names no subject of its own**; a headline that
  names a subject is an article even when it shares a page with others. When a
  headline names a subject and you are unsure, it is an article.

**Kind changes what you should expect to find**, and the classifier must not
invent what the print does not set:

| `kind` | what this shape usually looks like |
|---|---|
| `monthly` | several departments and standing columns — the news run, the reader-mail rubric, the tips columns — plus feature articles |
| `sonderheft` | one theme end to end. Typically **no departments and no standing columns**: the running head names the section of the book (`Anwendung`, `Statistik`, `Finanzen` in `SH8507`) and every piece under it prints its own headline, so every piece is an **article**. A `sonderheft` that shows a department is possible; it just needs the same evidence as any other — no headline for the run — and not a memory of how the monthlies look. |

## A TINTED BOX ACROSS THE COLUMNS SCRAMBLES THE READING ORDER

**Twice proven on SH8601, and it is this chain's most dangerous failure**,
because the damage reads as ordinary German.

When a band of tinted boxes or tables cuts across the text columns, tesseract's
`--psm 3` treats each half-column as an independent block and emits them in the
wrong order. Step 030 then joins them in that order, welding the head of one
column onto the tail of another. MEASURED:

- **p090** — a tinted box interleaved with the surrounding body columns; the
  reading order was scrambled and a truncation there would have been traded for
  an unknown reordering (recorded in r000).
- **p124** — three columns, each cut in half by a band of four tinted tables
  (Tabellen 1-4). The six half-columns came out in the wrong order, so the
  published article read:

  > Für die RS232-Routine nach einem Moment wieder »vernünftigen« Text liefern.
  > …kann die Basicsen, für die der Speicher des C 64 zu klein war.

  Two sentences, each half from one column and half from another. **Both are
  grammatical enough to survive every gate in this chain** — r310's invariants,
  r320's coverage count, a green build — and both are meaningless. They were
  found by a human reading the article (r325).

**So: whenever a page has a tinted box or table band interrupting its columns,
verify the reading order against the page BEFORE trusting the assembled text.**
The block index gives the geometry; column x-positions and band y-ranges are
enough to establish the true order:

```
p124: columns at x ≈ 330 / 1815 / 3305, bands at y ≈ 520-2020 / 4880-6650
      order = col1-upper, col1-lower, col2-upper, col2-lower, col3-upper, col3-lower
```

Confirm every join by reading the two fragments as ONE SENTENCE on the 600 dpi
master. A join that does not read as a sentence is the wrong join.

**Coverage counting cannot see this.** r320 asks whether every block survived,
and every block does survive — in the wrong place. The only detector is meaning.

## Where the issue-specific facts come from

Nothing in this step is allowed to be true only of one issue. Each fact has a
named source, and the source is the issue, not the rule:

| fact | source |
|---|---|
| page count, working paths, `kind` | `issues/<ID>/issue.json` via `r000_issue.py` (see the descriptor section of `r000_orchestration.md`) |
| **which pages hold the table of contents** | discovered from step 020's own labels: the pages carrying the most `toc`-labelled text, cover excluded. It was `(6, 7)` in 8609; it is 4–5 in some older issues and neither in a Sonderheft. Never a compiled-in page pair. |
| the running head on each page | step 020's `header` blocks for that page |
| the candidate department / column names | this issue's running heads plus this issue's printed TOC — the same two sources the model is shown, so it can see for itself which runs print a headline and which do not |
| the issue's article titles and start pages | this issue's printed TOC, used to **correct** titles and start pages, never assumed complete (it omits short items) |

The model call is briefed with those, and with nothing else. If a run in this
issue looks like a department, the evidence for that is on this issue's pages.

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

`ISSUE_MD` is **derived** from the descriptor, not typed: the chain carries one
constant, `ISSUE = "<ID>"` in `r000_issue.py`, which `r030_assemble.py` imports,
and every path under it comes from `r000_issue.load(ISSUE)`. It points into the issue's working directory, not into
the repo -- ask the module for it rather than assuming a path.

Two more checks that the issue-specific facts really did come from the issue:

```bash
cd tools/img/scan2ocr/rules
python3 -c "import r030_assemble as A; print(A.ISSUE, A.ISS.kind, A.PAGES, A.OUT_DIR)"
```

- the id, kind and page range must be **this** issue's, straight out of
  `issues/<ID>/issue.json`;
- the run prints `contents page(s): N, M` — the pages it FOUND. Confirm they are
  this issue's printed Inhaltsverzeichnis (8609: 6, 7). A `WARNING: no contents
  page found` line means the boundary call ran on running heads and headlines
  alone; that is a legitimate but degraded run and belongs in `LOG.md`.

## The coverage gate moved to r320

The omission check that used to be documented here is now **r320**, because
it must run at the END of an issue (content can be lost at any later step)
and because it needs the OCR intermediates, which r310 does not. See
`r320_omission.md`.
