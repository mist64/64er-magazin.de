# 320 — Omission checks (terminal, needs the OCR intermediates)

**Applies to:** all — omission is the defect class that reads as correct in any issue. Its page-coverage companion leans on the Jahresinhaltsverzeichnis, which has no Sonderheft rows — for a Sonderheft use the printed TOC's page numbers instead; the omission gate itself is unaffected.

**Run order — LAST, with r310.** r310 answers "does the finished issue satisfy
its structural invariants" and needs only `issues/<YYMM>/`. This one answers
"is anything MISSING", and needs the scan intermediates as well.

That input difference is why they are separate rules:

| | r310 | r320 |
|---|---|---|
| inputs | `issues/<YYMM>/` only | plus `tmp/ocr/out/*.json`, `*.labels.json` |
| lifetime | forever — the issue is in git | a window — the intermediates are multi-GB, not in git, and get deleted |
| inputs missing | something is badly wrong | normal for an old issue — must report **cannot run**, never "passed" |

That last row is the whole point. A check that reports green because it never
ran is worse than no check; 8609 shipped with `WORST.txt` at 0 bytes and nobody
noticed the r020 triage had produced nothing.

## Why this is not part of r030

r030 is the *assemble* step. A check filed under 030 reads as "run when you run
030" — but content can be lost at any later step: a figure dropped at r130, a
paragraph at r190, a table flattened at r160. The check has to run at the end.
r030 also already claims a paragraph-accounting check in its own Verification
block (the model-backed one that was never run), so a second check under the
same number is ambiguous.

## The gate

```bash
tools/img/scan2ocr/rules/r320_coverage_check.py issues/<YYMM> <ocr-out-dir>
```

Stage B records which blocks it selected as article content in
`<page>.labels.json` as `order`. The invariant:

> **every block the classifier kept must appear in the article claiming its page.**

Investigate every `UNACCOUNTED` hit and record the disposition. On 8609 after
the full review pass it reports 3 of 613 (0.5%), all explainable: a block
starting where a drop cap was restored (`as tun` vs `Was tun`), a listing
fragment deliberately deleted as a duplicate, and a table whose cells now split
the 4-word probes.

Known false-positive sources, excluded or expected:

- **listing blocks** are skipped — the disk `.txt` is the correct petcat
  rendering while the OCR reading of the printed listing is garbled (`mps 891`
  for `mps 801`)
- **ads and non-article matter** are excluded by using `order` rather than every
  block on the page; before that filter p140's job ad produced six spurious hits
- **our own OCR corrections** move the HTML away from the OCR, hence a probe
  fraction rather than an exact match

## Companions to run at the same time

- **THE PAGE-JUMP SPLICE — check both ends of every `Fortsetzung`.** Where an
  article jumps pages, the text at the END of the last column before the jump
  can be missing outright, and the two halves are then welded into one sentence
  that still reads as German. Nothing else in the chain sees it: the paragraph
  is well-formed, the byline is in place, r310 is clean, and r320's own block
  accounting passes because the classifier's block for that column was never
  kept in the first place.

  MEASURED on 8610, `41 Nach uns die Sintflut` (pages `41, 48`): the corpus read
  *"…des Gesamtsystems **beitragen. Druckern ist nun einmal sehr komplex**…"*
  while p41's last column ends with a NEW paragraph, *"Das Thema Computer mit
  verschiedenen Programmen, Interfaces und"*, and p48's continuation block reads
  *"Druckern ist nun einmal sehr…"*. Twelve words and a paragraph break, gone,
  and a human reading for sense found it — no check did.

  So: for every article whose `64er.pages` carries a comma, crop the end of the
  last column before each jump and the start of the continuation block, and
  compare them against the text at that join. Restore what is missing from the
  crop, word for word, keeping the paragraph break where the print starts one.
  Check the reverse too — a continuation's first words duplicated, or the
  `Fortsetzung auf Seite N` marker itself leaking into the prose.

  ```bash
  grep -l '64er.pages" content="[^"]*,' issues/<ID>/*.html
  ```

  Every hit is a whole column of type. This is the cheapest check in the file
  per byte recovered, and the only one that finds this class at all.
- **page coverage** — every page is claimed by an article or is knowingly an
  ad/classifieds page. The annual `Jahresinhaltsverzeichnis` gives the
  authoritative range per article; it caught two understated ones in 8609
  (71-74, 82-84).
- **dangling cross-references — TRIED AND REJECTED.** Text citing `Bild 3` with
  no such caption sounds like a good proxy for "the figure and its caption were
  dropped together". It is not, in a serialised magazine. Implemented and run
  over five issues it produced five candidates and **every one checked against
  the PDF was a cross-issue reference**, i.e. correct as printed:

  | case | what the print says |
  |---|---|
  | 8607/150 Listing 2 | "Listing 2 **(Ausgabe 5/86)** wird zuerst …" |
  | 8608/154 Bild 5 | "… zeigt Bild 5 **in der ersten Folge … in der Mai-Ausgabe**" |
  | 8607/79 Listing 3 | the print itself skips it — already noted in the file |
  | 8607/168 Bild 2 | opens "zwei Druckfehlerteufelchen **aus Ausgabe 3/86** berichtigen:" three paragraphs earlier |

  The qualifier that identifies a foreign reference is often several paragraphs
  upstream, so no local rule finds it; successive attempts either missed the
  qualifier or grew broad enough to hide real gaps. **And the check is
  redundant**: a dropped caption is a `caption` block, which this coverage gate
  already reconciles. Use the gate; do not rebuild the reference check.

## The loss this gate CANNOT see: a line or two dropped inside a claimed page

Every check here asks whether a page, an article or a file is accounted for.
A page can be fully claimed, its blocks all present and its word count
unremarkable, and still be missing a line or two of text the OCR never
emitted. 8611 had four: an intro's opening sentence, four lines mid-column,
two phrases beside a figure, and a fragment before a subhead. Nothing in this
gate fired on any of them, and nothing could have.

Three instruments were tried against those four cases and **all three failed**
— do not rebuild them:

- **Unclaimed vertical whitespace in a text column.** A dropped line leaves no
  hole: the following block simply starts where it starts. The gaps this finds
  are the running header's, on every page, and it missed the clearest case.
- **A block starting mid-word or lowercase.** Real, but it is the dropped
  drop-cap signal r280 already sweeps, and column flow makes a lowercase start
  legitimate.
- **Blocks abutting an illustration as a crop worklist.** Too broad to be a
  worklist (658 blocks over 127 pages in one issue) and it still misses cases
  that are nowhere near a figure.

So there is no mechanical check, and this section exists to say so rather than
to leave the next agent looking for one. The instrument is **r325, reading the
page** — and **r290**, which catches lost HEADINGS as a side effect of holding
the crop up for the level question. What this class contributes is where to
look hardest: the FIRST
LINE of a column, and any paragraph that runs beside a figure or an ornamental
initial. Both are places the OCR's line segmentation has least context.

## Why omission needs its own gate at all

It is the one defect class that reads as correct. An article missing a
paragraph, a table, a heading or its last line passes spell-checks, markup
greps, beautify, tag balance and the build. 8609 shipped with all four before a
page-by-page read found them, and reading every page by hand does not scale.
