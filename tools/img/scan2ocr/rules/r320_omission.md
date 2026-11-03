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

## The gate — BOTH scripts, and the directory is `<tmp>/ocr/out`

```bash
OCR=<tmp>/ocr/out        # NOT <tmp>/ocr -- see below
tools/img/scan2ocr/rules/r320_coverage_check.py    issues/<YYMM> "$OCR"
tools/img/scan2ocr/rules/r320_dropped_listings.py  issues/<YYMM> "$OCR"
```

**Step 320 is both of these, and this block used to invoke only the first.**
A builder running "the gate" ran half of it and had to find the other script
elsewhere and invent its argument. MEASURED on SH8608, 2026-10-17: the
dropped-listings half was pointed at `<tmp>/ocr`, which holds no
`labels.json` at all. It printed `dropped listing blocks: 0 … 0` and exited 0,
and a hollow pass was reported as a clean gate. Found only because the coverage
half refused the same path with exit 2.

`r320_dropped_listings.py` now refuses it the same way. **Both scripts exit 2
on a directory with no `labels.json`: 2 means the check did not run, and it is
not a pass.**

Stage B records which blocks it selected as article content in
`<page>.labels.json` as `order`. The invariant:

> **every block the classifier kept must appear in the article claiming its page.**

Investigate every `UNACCOUNTED` hit and record the disposition. On 8609 after
the full review pass it reports 3 of 613 (0.5%), all explainable: a block
starting where a drop cap was restored (`as tun` vs `Was tun`), a listing
fragment deliberately deleted as a duplicate, and a table whose cells now split
the 4-word probes.

**The gate cannot see text the classifier never kept.** All three of 8612's
real losses were outside its reach: a `noise`-labelled block (p19), a line
absent from `labels.json` altogether (p23), and merged column tops (p163).
Earlier steps had found them by eye. So run the companion sweep over the
`noise` and `other` blocks and screen what comes back — on 8612 that gave 71
candidates, all of them figure text, which is the expected population. A
page whose `noise` block holds prose is the finding.

Known false-positive sources, excluded or expected:

- **listing blocks** are skipped **only when the article references a disk
  file for that listing** — there the disk `.txt` is the correct petcat
  rendering while the OCR reading of the printed listing is garbled (`mps 891`
  for `mps 801`). A **hand-typed** listing has no disk file to be right, and is
  checked like prose.

  MEASURED on 8612: article 74's NMI routine is hand-typed, **21 printed lines
  from p76 were missing**, and this gate reported nothing. It was found by
  diffing the HTML against the PDF text layer and cropping the suspects. Of
  8612's 38 listings, 36 are disk-backed and 2 are not; skipping all of them
  is what hid this.
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

## RUN THE RECONCILIATION BEFORE `<tmp>` IS SWEPT — you cannot go back

The kept-block reconciliation needs `<page>.labels.json`, which lives in the
issue's `<tmp>`. Once that is swept the check can never be run on that issue
again: MEASURED today, of every issue in the corpus exactly ONE still has its
OCR intermediates — the one being built. So this half is a one-shot gate, and
running it late means not running it.

It used to fail silently in exactly that situation: with the directory gone,
every page raised `FileNotFoundError`, the loop skipped them all, and the
summary printed `kept prose blocks 0   UNACCOUNTED 0   (0.0%)` — a pass, from a
check that had not looked at anything. It now prints `CANNOT RUN` and says
what is missing. The unclaimed-pages half needs no OCR and still runs.

## A PASSAGE PRESENT TWICE IS AN OMISSION DEFECT TOO

This gate looks for text that went missing. The mirror defect is text added
back that was never gone: SH8603's 190A "restored" a section that 030 had
glued onto the end of a neighbouring paragraph, and the issue shipped it
twice — noticed only because a stray `©` survived in the raw copy. r190 now
pre-checks before restoring anything; this gate is the backstop, because by
here every restoration and every heading split has happened.

Same sweep r190 runs, over the finished issue:

```bash
# A DUPLICATED PASSAGE, which is what a wrong "restoration" leaves behind.
# PROSE ONLY: a <table> repeats cell patterns by nature ("a) 1, 2, 3 b) 1, 2
# min. 10; max. 25,4" across printer columns), a <pre> repeats listing lines,
# and a pin-name legend repeats its own vocabulary -- swept with those in, all
# four of SH8603's first hits and all of 8612's were tables, i.e. correct
# output reported as a defect.  MEASURED with them out: 1 to 4 hits per issue.
# A hit is a LOOK: read both occurrences and decide which (if either) belongs.
$PY - issues/<ID> <<'PYEOF'
import glob, io, os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
W = 12
STRIP = re.compile(r'<(pre|code|table)\b.*?</\1>', re.S)
items = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    s = io.open(f, encoding='utf-8').read()
    i = s.find('<article'); b = s[i:s.rfind('</article>')] if i >= 0 else s
    b = STRIP.sub(' ', b)
    words = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', b)).split()
    seen, last = {}, -99
    for n in range(len(words) - W + 1):
        k = ' '.join(words[n:n + W]).lower()
        if k in seen and n - seen[k] >= W:
            if n - last > W:
                items.append('%s: w%d and w%d  "%s"'
                             % (os.path.basename(f), seen[k], n, k[:62]))
            last = n
        seen.setdefault(k, n)
new = R.delta(sys.argv[1], 'dup-passages', items)
R.report('duplicated prose passages', new, len(items), sys.argv[1], 'dup-passages')
PYEOF
```

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

## A LISTING BLOCK CAN HIDE PROSE, AND UNACCOUNTED EXCLUDES IT (SH8607)

The UNACCOUNTED half skips `listing-*` blocks, which is right for listings and
wrong for a block that only *starts* as one. SH8607 p151's "Wichtiger Hinweis
zum Abtippen" box was OCR'd into the head of a `listing-standalone` block and
was therefore invisible to 020, 130, 190 and this step alike — the one defect
class this rule exists to catch, hidden by its own exclusion.

**List any `listing-*` block whose leading lines are prose** (no line number,
no hex address, sentence punctuation) as `PROSE INSIDE A LISTING BLOCK`, even
though the block itself is excluded from the count. See r020.

## A PARAGRAPH THAT ENDS ON A LINE-BREAK HYPHEN IS TEXT LOST AT A COLUMN BREAK

The print hyphenates at the end of every column. When the join fails, the
hyphen survives into the HTML and whatever followed it is gone — and the page
still reads as prose right up to the break, so nothing else in the chain sees
it. Two readers reported one of these on 8610 p44 in October 2026; the scan of
the corpus that followed found four more.

```bash
grep -rnE '[a-zäöüß]-</p>' issues/<ID>/*.html        # must print nothing
```

**MEASURED over the whole published corpus: five hits, all five real.** No
false positive — a paragraph legitimately ending in a hyphen does not occur.
Run it per issue at the end, and over `issues/*` after any step that joins or
splits paragraphs.

Three shapes, all of them seen:

1. **The continuation is the very next `<p>`.** One paragraph split in two
   (SH8505 p28: `gesteuert wer-` / `den.`). Join them.
2. **The continuation follows a HEADING.** The print puts a heading at the foot
   of a column and runs the paragraph straight through it — SH8601 p14
   (`die Auflö-` + h2 + `sung von 320 Punkten …`) and 8506 p41 (`bei vielen
   Ter-` + h2 + `minalprogrammen zurück …`). Join the paragraph and put the
   **heading after it**: the text before the heading belongs to the section
   above, so leaving the h2 in the middle puts half a sentence under the wrong
   one.
3. **The continuation is not in the file.** Read the master. 8610 p44 had lost
   the standfirst's last line (`sten.`) at the column break. **Do not complete
   the word from grammar** — SH8601 p78's `angege-` has exactly one plausible
   completion and it is still open for that reason.

### The companion check that does NOT work — do not re-invent it

The obvious partner is "a `<p>` that starts lowercase after a `<p>` that ends
without terminal punctuation", to catch the orphaned second half. **MEASURED:
118 files, 291 pairs, and nearly all are correct** — it fires on the house
pattern where a command line sits in its own `<p>` between two halves of a
sentence (*"Das Maschinenprogramm kann nun mit"* / `SYS 49152` / *"gestartet
werden"*). A plain `<p>` starting with a lowercase word is worse still: 172
files, mostly glossary and listing entries. Neither is usable; the hyphen is
the only precise signal.


## A GATE WHOSE MATCHER CAN'T READ THE FIX IT ASKED FOR (8701, p33)

The noise sweep's whole purpose is to ask *is this text anywhere in the HTML?*
It asked it with 3-word shingles — and a shingle cannot read a table.

8701 p33 printed three pin assignments inside yellow panels. Step 020 labelled
them `noise`, nothing carried them, and this gate is what found them. They were
then typeset, as `<table>`, because that is what the print shows. **The sweep
re-ran and still called all three LOST.** Every word was in the file. The cell
stream normalises to `1 luminanz 2 masse 3 audio out`, the block's shingle
`luminanz masse audio` occurs nowhere in it, and the row numbers between the
words are the reason. Five more blocks failed identically — p35, p48, p61,
p162, p170 — all of them tables.

So the gate written to catch the p33 loss could not see the p33 **fix**, and it
reported the correct outcome as the defect. Short, number-interleaved text is
the one population this sweep exists for, and a prose-order matcher is blind to
all of it.

**The sweep now reports three outcomes, not two:**

| outcome | test | what it means |
|---|---|---|
| published | ≥ 50 % of its 3-word shingles are in the HTML | silent |
| **vocabulary only** | ≥ 90 % of its 4+ letter words are on the page, in any order | **its own short list — eyeball every one** |
| needs a disposition | neither | the ranked list, `real × (1 − found)` |

**The middle row is the point, and it is a downgrade, not a dismissal.** A
vocabulary match is much weaker evidence than a phrase match. TESTED while
writing it: a paragraph that is genuinely gone, whose words happen to scatter
through its own article in another order, scores 0.92. Folding that into
"published" would have bought six table false positives at the price of a new
way to lose a paragraph in silence — the exact failure this gate exists to
prevent. A typeset table lands in that list and is correct; a reordered lost
paragraph lands there and is not; the list is short enough that the difference
is visible at a glance, and both counts are in the verdict line.

**The general rule, and it is the second time this build has paid for it** (see
r005's fold gate, which compared the window edge to the fold it was set from):
**a gate must be able to represent the correct answer.** Before trusting one,
construct the passing case by hand and check that the check actually passes it.
A green gate that could not have gone red is not evidence.

## THE AD MATTER IS NOT AN OMISSION — the Inserentenverzeichnis precedent

The back-matter page carries the Impressum in one column and the
**Inserentenverzeichnis** — the alphabetical list of advertisers, with page
numbers — in the other. **No issue in the corpus transcribes it**, and that is
a decision, not an oversight: it indexes the ads, which we do not publish, so
every page number in it points at nothing.

The noise sweep finds its text every time, because it is real German words that
occur in no article. 8701 p187 raised `Bitte beachten Sie unsere
Österreich-Beilage …`, a notice printed in that same column. **Disposition:
omitted, no comment, no aside** — like the list it belongs to.

Already settled on 8610 (p195), 8611 (**p187, the same page**) and 8612 (p195),
each time in that issue's `LOG.md` and nowhere else, which is why 8701 asked
again — and `LOG.md` is git-ignored, so those three rulings exist on one
machine and in no clone. **If a sweep will raise the same block every time, the
answer belongs here**, in the rule the next builder reads before running it.

Not to be confused with 8610's `75 Österreich-Beilage.html` — an editorial
article announcing the supplement, which is published. The notice beside the ad
index is not that article.
