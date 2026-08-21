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

## Two companions to run at the same time

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

## Why omission needs its own gate at all

It is the one defect class that reads as correct. An article missing a
paragraph, a table, a heading or its last line passes spell-checks, markup
greps, beautify, tag balance and the build. 8609 shipped with all four before a
page-by-page read found them, and reading every page by hand does not scale.
