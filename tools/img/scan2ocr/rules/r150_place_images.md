# 150 — Place image figures into article HTML

**Applies to:** all — every issue has figures to place. The Vorschau-teaser section is one rubric's placement convention, inert when the issue has no Vorschau.

**Goal:** turn every loose `<page>-<n><suffix>.png` (and `title.png` if
unhandled elsewhere) in the issue directory into a `<figure>` or
`<img class="inline">` inside the article it belongs to. Captions are
verbatim from the print scan; alt text is a short German visual
description.

## FIRST: capture the printed captions, while the OCR still exists

A caption belonging to a figure nobody has cut yet is in no HTML file. It lives
only in the OCR intermediates, and those go when `<tmp>` is swept — MEASURED
across the corpus, exactly ONE issue still has them, the one being built. 8611
had **74** printed `Bild`/`Tabelle`/`Listing` captions in that position. Lose
them and they must be read off the masters again, one page at a time.

So before anything else here, and before any sweep:

```bash
$PY tools/img/scan2ocr/rules/r150_figure_captions.py issues/<YYMM> --write
```

It writes `issues/<YYMM>/figure_captions.txt` (`page<TAB>status<TAB>caption`)
next to the articles, where it survives the sweep, and r150's later re-run has
the text without touching a master. `status` is `IN_HTML`, `ABSENT` (no figure
yet) or `TRUNCATED`. **`IN_HTML` means "present as a `<figcaption>` in THIS
PAGE'S OWN ARTICLE"** — the match is against figcaptions only, scoped by
`64er.pages`, because matching the whole article text made a caption "present"
when the prose merely mentioned the figure, and matching issue-wide let a bare
`Bild 5.` on p106 find a `Bild 5. …` in any of four other SH8605 articles.

**AND IT IS A LEAD, NOT THE WORKLIST.** The extractor takes its candidates from
the block index, so **a caption the layout analysis folded into a figure or box
region never reaches it at all**. MEASURED on SH8605's hand-over survey (every
editorial page at 20 %, 600 dpi where needed): **39 printed captions are missing
from `figure_captions.txt` altogether** — 6 ×6, 20 ×2, 30 ×2, 40, 69, 77 ×8,
90, 101 ×4, 111, 149 ×10, 164 ×3. They have a shape in common: the caption is
printed INSIDE the frame or on the tinted ground, e.g. 40 p57 *"Bild 3. Ein
Programm-Ablaufplan"* inside a grey flowchart frame, 164 p175 *"Bild 3. Ein
normales Diskettendirectory"* inside the framed screenshot, 30 p37 *"Bild 15"*
inside a shared print-sample frame, and 149's sprite captions set two to a
frame.

**So the worklist comes from LOOKING AT EVERY EDITORIAL PAGE**, with this file
as a cross-check — not the other way round. A build that trusted the file would
have handed the owner a worklist missing about a quarter of the figures.

**AND NO PAGE GOES ON THE WORKLIST WHILE ITS GRADE IS STILL IN QUESTION.** The
owner cuts his crops out of `sheets600/NNN.png`, so a worklist row is an
instruction to cut *those* pixels. If the page is re-graded afterwards, the
crop he already cut came off the old grade and nothing will ever say so — the
PNG looks fine, it is simply made of different paper from the page around it.
MEASURED on SH09: p031 was graded with no paper-yellowing correction at all
(r005 check 7g, HARVEST 40), and worklist row 25 told the owner to cut figure
`30-0b` from `sheets600/031.png`. Cut before the re-grade, that figure carries
a +14.6 DN R−B edge cast the rest of the issue does not. Cut after, it matches.

So before the worklist is handed over, and again before any row is re-issued:
no page on it may have an open re-grade, an unruled `NOT APPLIED` stamp, or a
pending `reviewed/` override. If one does, either settle it first or mark the
row `HOLD — <why>` and tell the owner in the same breath, so he cuts the other
rows and leaves that one. **The cheapest moment to catch this is before he
picks up the knife; the most expensive is after the figure is placed, because
by then it is one PNG among forty and nothing distinguishes it.**

In the other direction the file carries spurious ROWS, which cost a line and
nothing more: a prose mention `(Bild 5)` or a DATA line `BILD 7` opens like a
caption and becomes a candidate. Read the row, not the count.

### AN UNCUT FIGURE HAS EXACTLY TWO ARTEFACTS, AND NEITHER IS IN THE HTML

A figure the owner has not cut yet produces **the worklist row and the
placement plan, and nothing else**: `<tmp>/crop_worklist.txt` and
`<tmp>/r150/placement_plan.txt`. It never produces a placeholder in the HTML --
not an empty `<figure>`, not a comment, not an `<img>` pointing at a file that
does not exist. A placeholder is indistinguishable from a placed figure to
every step after this one, and the one thing it is guaranteed to do is ship.

MEASURED on SH10: r000 says "every unplaced figure is a TODO" and this rule
placed only delivered PNGs, so the step had no stated shape for the gap between
them and stopped to ask. The stop was right and the rule was what cost it; the
answer is one sentence long and it is now above.

### AND THE SERIES RULE IS r160'S, APPLIED AT WORKLIST TIME

r160 says a numbered series is **all typeset or all cropped**. That is a
decision about the worklist, not about the typesetting, so it is made HERE:
**one cropped member puts the whole series on the list.** A series is the print
labelling, not the prose's -- `Teil N` on the page and `Plan N` in the text are
one series, anchored at the first text that names the whole set (84-x1..x4 on
SH10).

MEASURED on SH10: the worklist excluded the typeset members of four series (10,
71, 101, 126). The conflict was invisible until r160 had typeset them, and by
then the owner was already cutting -- a supplement of 8 rows, plus 2 for the
TEDMON dumps, handed over mid-knife. The check costs one pass over the worklist
before it is handed over: for every row, is any other member of its series
missing from the list?

### THE page -> Bild MAP IS DERIVABLE. DO NOT HAND-KEEP IT.

The block index already answers it, per page, in one line:

```bash
grep -ohE '\bBild [0-9]+[a-z]?\.' <OUT_DIR>/blocks/pNNN.txt
```

Run it per page and the map falls out. It misses exactly the captions set
INSIDE a frame — the ones listed above, which the worklist documents as folded
away — so the gaps are known, small and already written down.

**MEASURED on SH8606, which is why this is here.** The pre-150 survey wrote
`73-1..3` on p74 as *Bild 5/6/7* and `73-4..6` on p76 as *Bild 1/2/3*, because
it assumed delivery order equals page order. It does not: the magazine prints
**Bild 5-7 on p74, BEFORE Bild 1-3 on p76**. The delivered PNGs, the printed
pages 074/076/077 and the shipped `<figcaption>`s all agree that file number =
Bild number, so **the HTML was never wrong — only the worklist was**, and the
one-line grep above would have caught it the day it was written.

**AND A WORKLIST CORRECTION REWRITES THE ROW. It never appends a footnote.**
Step 150 DID notice this one (`73-5 earth = Bild 5`) and added a correction
line below the table while leaving the wrong rows standing. Four days later
control built the owner's croplist from that table and walked straight into the
same swap. A note under a table is not a correction; it is a second claim, and
the reader who needs it is the one who did not scroll. Fix the row.

## TWO ARTICLES CAN SHARE A START PAGE — the second one's lead image is `-00`

Figure files are `<article-start-page>-<n>.png`, so two articles beginning on
the same page collide on the prefix. The corpus already answers this: the
SECOND article's lead image takes **`-00`**, and `-0` stays with the first.

MEASURED: 15 `-00.png` files across the corpus. Page 8 carries a trade-show
report beside the editorial in 8503, 8508 and 8603, and in every one the report
owns `8-00.png` while the editorial keeps `8-0.png`. The same pairing gives
`52-00` in 8512, 8601, 8602, 8603, 8605, 8608 and 8611.

Precedent renders it as a lead image, not a captioned figure:
`<img src="8-00.png" alt="">`, no `<figcaption>`. r150's alt-text check already
tolerates the name (`-0[0-9a]*`).

So do not renumber a figure into the neighbouring article's sequence, and do
not read a `9-0.png` as belonging to a page-9 article when no article starts on
page 9 — it is the second page-8 article's lead image and belongs at `8-00`.

### `-00` covers the LEAD IMAGE only; four shapes have no name

Each of these came up on SH8603 and had to be settled by hand:

| shape | name | why |
|---|---|---|
| a second article's **table** | `<page>-00t<n>` | `-t<n>` is the table series, and `-00` marks the second article; compose them in that order |
| an **unnumbered** printed "Tabelle." | `<page>-t0` | `t0` for the table the print does not number, so a later numbered one still starts at `t1`. r160's prose may call it "Tabelle 1"; the FILE follows the print |
| a whole **screen-output** crop | `<page>-s<n>` | not a Bild, not a Tabelle, not a listing — a photograph of the screen standing in for text nobody can set |
| a figure printed on the page **BEFORE** its article starts | `<its own article's start page>-<n>` | SH8603's p76 carries Bild 1 and Bild 2 for the article that starts on 77a. The figure belongs to the ARTICLE, so the prefix is the article's start page, not the page the ink is on |

That last one is the only one that changes an existing convention, and it has
to: a figure named for the page it was printed on would land in the
Checksummer's sequence and be placed in the wrong article.

**Four more from SH8604**, same rule: the name follows the print, and it is
lowercase because Verification 1 matches `[0-9]+-[0-9a-z_]+\.png` and the
corpus has **0** PNG names with a capital in them.

> **ERRATUM, 2026-10-07.** This table first gave the unnumbered-picture case as
> `<page>-p<n>`, taken from SH8604's errata *proposal* and codified without
> checking the corpus. **The corpus has 0 `-p<n>` names and 36 `-x` ones**, and
> `-x` already meant exactly this. The rows below are the measured convention.
> A naming rule is settled by counting the corpus, not by adopting the
> suggestion that surfaced it.
>
> **And then counted twice.** The first count found 27 and reported the two
> forms below it; it missed the 9 `-x<n>` names entirely, because the regexes
> looked for `-x` and `-<n>x` and the third form puts the digit AFTER the x.
> Found by SH8605 when a rule built on the short count told it to invent a
> pairing that its page did not have. **A count that drives a rule is only as
> good as the pattern you counted with** — enumerate what is actually there
> (`ls | grep -E '\-[0-9a-z]*x[0-9a-z]*\.'`) before concluding a form does
> not exist.

| shape | name | why |
|---|---|---|
| an **uncaptioned boxed table** | `<page>-ta`, `-tb`, … | it is a table, so it joins the `t` series, but it has no printed number to take — letters keep it out of the numbered run |
| an **unnumbered figure, standalone** | `<page>-x` | **`-x` means it lacks a printed number** (owner, 2026-10-07), and it is not a lead or author image, which take `-0` / `-00`. 6 in the corpus |
| an **unnumbered figure belonging with Bild n** | `<page>-<n>x` | the same, where the figure sits with a numbered one. 21 in the corpus, and **all 21 have a plain `<page>-<n>` sibling** — that pairing is what the form means |
| **SEVERAL unnumbered standalone figures** in one article | `<page>-x<n>`, numbered in page order | 9 in the corpus — `8511/9-x1 … 9-x6` in *9 Aktuell*, `8510/126-x1 … 126-x3` in *Dem Klang auf der Spur (Teil 9)* — and every one is placed in its article's HTML. Use this, not `-<n>x`, when the figures sit with NO numbered Bild: `-<n>x` would invent a pairing the page does not have |
| a numbered Bild the owner has **already typeset** | no file — listed `typeset` in the worklist | owner-crop-wins in reverse: where the typeset version is the delivered one, there is no PNG, and the worklist says so rather than leaving a gap that reads as a lost image |

**And `-t0` is the rule, not `-t1`.** SH8603's worklist HEADER says an
unnumbered "Tabelle." takes `-t1`; the table above says `-t0`, and the table
is right — `t0` leaves `t1` free for the first table the print does actually
number. A worklist header copied from a previous issue carries the wrong name
with it; write the header from this rule, not from the last issue's file.

### A SECOND PRINTED UNIT OF ONE ARTICLE RESTARTS AT BILD 1 — `<start>-00<n>`

The magazine prints some articles in two units: a review, then its
*Anwendung des Monats* or listing half later in the issue under an `<h2>`
repeating the headline, with **its own Bild numbering starting again at 1**.
One article, one `64er.pages`, two series — and the second one collides with
the first file for file.

It takes the `-00` marker, in front of the printed number:
`52-001`, `52-002`, `52-003a`, `52-003b` for the second unit's Bild 1, 2, 3a
and 3b (8702, *Nie wieder Probleme mit Kurvendiskussionen*, p52 + p64-71).

Three reasons, in order:

- **`-00` already means "the second thing at this prefix"** — the second
  article sharing a start page, SH8605's second cartoon — and the table above
  composes it with a series exactly this way for `-00t<n>`.
- **The prefix must stay the article's start page.** Placement resolves a
  figure by finding the article whose `64er.pages` STARTS with the major
  number, so naming the second unit's figures for the page they are printed
  on (`64-1`) leaves them unplaceable: no article starts on 64.
- **The printed number stays visible.** Continuing the first series instead
  (Bild 1 of the second unit as `52-8`) would make the file disagree with the
  caption the page prints, and the caption is what a reader checks against.

**It does not collide with the zero chain.** `-0`, `-00`, `-000` are all
zeros; a name with a non-zero digit after the zeros is a numbered figure of
the second unit. If a second unit ever reaches Bild 10, write `52-0010` and
record it here — at which point the chain and the number do start to look
alike, and the next rule will have to separate them.

### A FORM PRINTED ACROSS TWO PAGES — offer `-xa`/`-xb`, accept one tall image

An order form, a questionnaire or a coupon that runs over two pages is offered
in the worklist as `<page>-xa` and `<page>-xb`, one region per page, because
that is what the crop tool can cut. **The owner may return a single tall
image** instead — 8701's did — and that is the better artefact where the form
reads as one. It then takes the plain `<page>-x` name and the worklist row is
annotated, because owner-crop-wins: a delivered crop replaces the plan, and
the plan is not re-imposed on it.

### A crop that covers SEVERAL Bild numbers is ONE figure

A single cut frame holding more than one numbered Bild is named for all of
them — `10-6abc.png`, and SH8601's `26-5_9.png` — and it becomes **one
`<figure>`, at the FIRST member's printed position, with each printed caption
on its own line** (`<br>`-separated inside the one `<figcaption>`). Not one
figure per number: there is one image.

**AND IT STAYS ONE FILE EVEN WHEN THE FRAME HAS A RULE DOWN THE MIDDLE.** Owner
on SH8608's `10-1_2.png`, 2026-10-17: *"the two in one will need to stay
combined"* — Bild 1 and Bild 2 of the Basic-Kurs, set in one frame split by a
vertical rule, with the two captions side by side beneath it. This reversed an
earlier ruling the same day for two separate files; the later word governs, and
the earlier one is not evidence of a convention.

**Mind what `_` means elsewhere in the corpus before reading a digit off it.**
There are 3 underscore names in 4001 PNGs. `26-5_9` is this form — and its own
digits do not describe its contents, since it carries Bild 9 and Bild 6. The
other two, `36-4_1` and `36-4_2`, are **the same Bild 4 in SH8501's two
Auflagen** — the whole figure twice, not a part of it — placed as
`old_edition` / `new_edition` inside a single `<figure>`, the same mechanism
that sets *Warum ein Sonderheft?* against *Warum eine zweite Auflage?* in that
issue's editorial. So the separator alone does not tell you which case you have
— read the captions.

> **ERRATUM, 2026-11-06.** This paragraph said those two were *"two halves of
> one numbered figure"*, which made `_` look like the corpus form for a picture
> that arrives in two cuts. It is not. Both files are the complete directory
> listing of Bild 4, at 4497x2684 and 2211x1345 px, one per print run. **Nothing
> in the corpus split a picture until SH09 had to** — the section below is that
> case, and it was written by checking this precedent rather than citing it.

### ONE PICTURE ACROSS THE PAGE TURN IS TWO CUTS, `-a` AND `-b`

A cut comes out of one `sheets600` page, so **a picture that crosses the page
turn cannot be one crop.** Its halves are on two sheets, each with its own trim
and its own skew, and the binding has eaten whatever ran through the gutter;
joining them would be our reconstruction of the picture rather than the plate.
Two cuts, in reading order — `<page>-<n>a` and `<page>-<n>b`, both named for the
page the FIRST half is on — and each is placed as its own `<figure>`, adjacent,
the way `56-0a/b/c` are.

MEASURED on SH09, 2026-11-06: `30-0a` (p30) and `30-0b` (p31) are the halves of
one cut-out colour photograph — a diskette and a red arrow pointing into the
slot of a 1541 whose opened body carries on across the turn. Both bleed to
their trim. It is the lead picture of *In die Geheimnisse der Floppy
eingetaucht*.

**AND THIS DOES NOT REVERSE THE TABLE CASE.** *A table printed across two pages
is ONE crop* still holds, and the difference is checkable rather than a matter
of kind: **ask whether the two halves can be butted without inventing a pixel.**
A table's rows continue and the paper destroyed no part of them, so yes — one
crop. A photograph across the gutter, no — two.

**`-a`/`-b` ALREADY MEANT THIS, AND IT MEANS SOMETHING ELSE TOO.** SH8608's
`56-0a/b/c` are three separate computers in one lead slot; SH09's `6-1a`/`6-1b`
are two photographs under one printed caption. The letter does not mean *half
of*: it means **one of several cuts belonging to one printed unit, in reading
order**, and both shapes are that. So the worklist's last column says WHICH —
SH09's reads *"one picture in two cuts because it is on two sheets"* — because
the letters cannot carry it and the next build reads the row, not this rule.

### PROSE PRINTED INSIDE A CUT FRAME GOES WITH THE CROP

*Owner crop wins* named tables and listings. It covers **any text the crop's
frame contains**: where the owner's PNG includes a line of prose — SH8604's
p33 box line — the HTML does not also carry that line as a paragraph. One
or the other, never both, and the delivered crop is the one.

### A CROP THAT CONTAINS ITS OWN PRINTED CAPTION GOES BACK FOR A RE-CUT

SH8604's `10-2` and `81-1` include the printed "Bild N. …" line inside the
frame, so the page shows the caption twice — once as pixels, once as the
`<figcaption>`. Do not drop the `<figcaption>` to compensate: it is the
accessible and searchable copy. Report it to the owner as a re-cut (SH8603's
`31-3` is the precedent), and leave the figure in place meanwhile.

**THE REMEDY ASSUMES A RE-CUT EXISTS, AND SOMETIMES IT DOES NOT.** This section
and *PROSE PRINTED INSIDE A CUT FRAME GOES WITH THE CROP* were written for the
same shape from opposite sides and met a case neither covers: a caption SET
INSIDE the figure's own frame, as part of its composition. MEASURED on 8702's
`22-4` — "**Bild 4.** Aufbau- und Zugriffsschema einer Index-sequentiellen
Datei" is printed in bold in the lower-left of the yellow panel, inside the
frame rule, with the diagram laid out around it. There is no cut that removes
it and leaves the figure.

**The test is whether the caption can be removed without cutting into the
figure's frame or its artwork:**

- **It can** — it sits below the bottom rule, or beside the frame, and a loose
  cut swept it in. Re-cut at the rule, caption out, `<figcaption>` as usual.
  8702's `83-1` is this case and was cut correctly.
- **It cannot** — it is inside the frame, part of the composition. **The crop
  keeps it, AND the `<figcaption>` is still written.** This section's own
  reason decides it: the figcaption is the accessible and searchable copy, and
  dropping it to avoid showing the words twice trades a real loss for a
  cosmetic one. r130's figure grammar expects one regardless.

So *prose inside a cut frame goes with the crop* governs the PIXELS, and it
does not license dropping the figcaption — that sentence is about prose the
HTML would otherwise carry as a `<p>`, not about the caption.

**AND THE OPPOSITE EDGE MATTERS TOO: A LEAD CROP THAT STOPS JUST ABOVE A BAND
OF DISPLAY TYPE.** A crop cut tight to the artwork's frame excludes whatever
is set beneath it, and what is set beneath an opening illustration is often
part of the headline. Reversed type on a black or tinted band is the case to
watch, because OCR returns no block for it either — so the words are in
neither the image nor the text, and nothing downstream can miss something that
is not there.

MEASURED on SH8608's p94, 2026-10-17: `94-0` ends at the drawing's frame, and
immediately below it the page prints **"Text-Manager"** in white on a grey
band, above the headline *"Briefe schreiben leichtgemacht"*. The article
shipped without the prefix; the owner found it by reading the page.

**So when a lead crop's lower edge sits on a band or a tint, read what is in
that band and check it is in the `<h1>`** — see r080, *THE HEADLINE CAN BE SET
INSIDE THE LEAD PHOTO*, which also gives the separator to join it with.

## NEVER LEAVE AN ORPHAN AT THE END — place it where it fits best

**Owner, 2026-10-06:** *"could not be placed so it's at the end. it's clearly
part of a series … place it somewhere between 2 and 4. same rule should apply
to images. dont have orphans at the very end, place them where they fit
best."*

An element whose print position cannot be determined — a table the OCR never
anchored, a figure whose callout is missing, a listing the text never names —
does **not** go to the bottom of the article. The bottom is not a neutral
place to put something: it reads as the article's conclusion, it lands after
the byline's closing run, and a reader meets it with no context at all.

**Place it where it fits best, and a numbered series tells you exactly where.**
SH8604's *Künstliche Intelligenz* shipped its tables as **1, 2, 4, 5, 6 … 3**,
with Tabelle 3 stranded after Listing 4 at the very end. It belongs between
Tabelle 2 and Tabelle 4. Where there is no series, use the first text that
mentions it; where nothing mentions it, use the printed page's own order.

This applies to **images, tables and listings alike** — r130 and r160 place
the other two and the rule is the same.

### The check: a series whose LAST member is not its highest

Plain ascending order is NOT the test and must not be made one. Magazine
layout floats figures out of numeric sequence as a matter of course:
MEASURED over the corpus, **34 articles** carry an out-of-order series, nearly
all of them correct — 8404's *Commodore Drucker* runs 1-5, 11-14, 6-10
because that is how the pages fall.

The orphan signature is narrower: **the last member of the series in document
order is not the highest-numbered, and nothing but markup follows it.** That
finds 10 articles corpus-wide.

```bash
$PY - issues/<ID> <<'PYEOF'
import glob, io, os, re, sys
sys.path.insert(0, 'tools/img/scan2ocr/rules')
import r000_reviewed as R
items = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.html'))):
    s = io.open(f, encoding='utf-8').read()
    i = s.find('<article')
    b = s[i:s.rfind('</article>')] if i >= 0 else s
    for kind in ('Bild', 'Tabelle', 'Listing'):
        ms = [(m.start(), int(m.group(1))) for m in
              re.finditer(r'<figcaption[^>]*>(?:<[^>]+>)*\s*%s\s*(\d+)' % kind, b)]
        if len(ms) < 3:
            continue
        nums = [n for _, n in ms]
        pos, last = ms[-1]
        tail = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', b[pos:])).strip()
        if last == max(nums) or len(tail) >= 400:
            continue
        # THE WHOLE TRAILING RUN, not just the last member.  Reporting only the
        # last one made this a THREE-ROUND check on SH8604's article 10, whose
        # listings ran 1-15, 17-22, 25, 26, 16, 23, 24: it named 24, and 23 and
        # 16 only became "last" after each fix.  The run is the maximal suffix
        # every member of which is below the highest number seen before it.
        k = len(nums)
        while k > 1 and nums[k - 1] < max(nums[:k - 1]):
            k -= 1
        run = nums[k:]
        items.append('%s: %s %s at the end; the series reaches %d before them'
                     % (os.path.basename(f), kind,
                        ', '.join(str(n) for n in run), max(nums[:k])))
new = R.delta(sys.argv[1], 'orphan-at-end', items)
R.report('series ending on a non-highest member', new, len(items),
         sys.argv[1], 'orphan-at-end')
PYEOF
```

A hit is a LOOK: the print may genuinely end on a lower-numbered figure. Read
the page, place it, and record the ones that are right.

## A 1-BIT CROP THAT IS MOSTLY BLACK IS A THRESHOLDING FAILURE

SH8604 shipped 29 figures whose printed halftone screen had been thresholded
into near-solid noise — *58-4* was **89.8 % black**, three legible boxes on a
black field where the page has a full diagram with `VG$=`, `BE$=`, a NIMM
cascade and `GEFUNDEN!→`. The owner re-cut all 29; the new set's maximum is
12.0 %.

**Nothing in the chain noticed.** r150's set check counts files against
references, r310 checks markup, and no gate asks whether a figure is legible
— so 9 crops above 50 % black and 11 above 40 % passed everything.

```bash
# black fraction of every placed 1-bit crop.  Photos are exempt: a dark lead
# photo is legitimately dark.  MEASURED on SH8604 after the re-cut: the only
# crops above 15 % are the lead photos and 10-5 (21.6 %, CHR$ grids, genuine).
$PY - issues/<ID> <<'PYEOF'
import glob, os, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.png'))):
    im = Image.open(f)
    # MODE 1 AND P ONLY.  A greyscale (L) crop is a PHOTO and was never
    # thresholded, so it is legitimately dark: including L flagged exactly
    # SH8604's six lead photos at 71.6-96.5 % and not one line figure, which
    # is the check inverted.  "Photos are exempt" has to be in the code, not
    # only in the prose.
    if im.mode not in ('1', 'P'):
        continue
    a = np.asarray(im.convert('L')) < 128
    frac = 100.0 * a.mean()
    if frac > 40:
        print('  %-16s %5.1f%% black -- look at it at display size' %
              (os.path.basename(f), frac))
PYEOF
```

**It can only flag, never reject** — a solid-black design element and a
crushed halftone measure the same. State the threshold whenever you quote a
figure: grey converted, cut at 128.

**Bilevel and palette crops only.** A greyscale crop is a photograph and was
never thresholded, so darkness there means nothing: with mode `L` included the
check flagged SH8604's six lead photos at **71.6–96.5 %** and not a single
line figure — precisely inverted. MEASURED after that fix: 40 bilevel/palette
crops, **none above 40 %**, the highest being `10-5` at 21.6 % (the CHR$
grids).

### A figure's page must be inside its article's `64er.pages`, and at 150 it often is not

r150's mapping assumes it is. On SH8603, 080 had left the ranges short for
article 31 (p38), 47 (p48), 58 (p59) and most of the game-listing pages,
because a listing-only page carries no headline for 080 to see.

**r320's page-coverage half is the check that catches this, and it runs at the
END — after 130, 150 and 160 have all depended on the ranges.** Run that half
immediately after 080 instead. It needs nothing but the HTML and the page
count, so there is no reason it has to wait, and fixing a range at 080 costs a
meta edit where fixing it at 320 costs re-placing figures.

**And when you add an article on a page another article already claims, do NOT
reduce that article's `64er.pages`.** Sharing a page is normal; the other
article probably prints there too. Look at the page first. 8611 gained a new
article on p185 and the obvious tidy-up — take 185 off article 184, which
claimed 184-185 — would have orphaned 184's Bild 4, its Bild 5 and its closing
paragraph, all of which are printed on p185 above the new article's box. It
would also have cut that page out of 184's per-article PDF slice.

**A `Bild` caption does NOT always want an image.** The print labels tables and
diagrams "Bild" as freely as photographs, and this corpus typesets them:
**154 figures** in it carry a `Bild` caption on an HTML `<table>` — register
bit-layouts (`Bild 1. Der Aufbau des MCR … $D505`), type overviews, market
comparisons. So a figure with a `Bild` caption and no `<img>` is not evidence of
a missing cut; it may be a table that belongs to r160. Decide from the page, and
keep the printed "Bild N" wording either way.

**The file is RAW OCR, not a transcription.** It preserves what tesseract read,
soft hyphens and all — 8611's has 12 `¬` inside words (`Buch¬stabens`) and
glyph errors like `GC 64` for `C 64`. It exists so the caption's TEXT is not
lost with `<tmp>`; it does not exempt anyone from checking each caption against
its page at placement. Pasting a line from it into a `<figcaption>` unread ships
an OCR error into the article.

**`TRUNCATED` is the second thing it finds.** A caption can be present and
short: 8611 dropped the second sentence of several listing captions ("Beachten
Sie bitte die Eingabehinweise auf Seite 99"), which three readers found
independently and by luck. That is a systematic drop at caption transcription,
not a reading miss, and no coverage check sees it — the caption is there.

Read each `TRUNCATED` hit against the page, in BOTH directions: the OCR is
sometimes the short one. Of 8611's two residual hits, p19's `Tabelle 3` is
complete in the HTML and truncated in the OCR, and p148's `Listing 1` is one
printed caption the OCR split into two blocks. Expect a couple of these.

## Mapping images to articles

Image filenames follow `<startpage>-<figurenum><suffix>.png`, e.g.
`145-9a.png`. The **major number** (before the first `-`) is the
**start page of the article** the image belongs to.

1. Extract major number from filename: `145-9a.png` → `145`.
2. Find the article whose `<meta name="64er.pages" content="…">`
   starts with that page, e.g. `content="145-153"`.
3. Disambiguate collisions: when two articles share a start page,
   Read the relevant pages from `<tmp>/masters600/NNN.png` to see which
   article the figure actually sits on. The image may be on a later
   page of the article, not the start page.
4. Fix wrong filenames with `git mv` when visual verification shows
   an image belongs to a different article. Renumber the minor part
   to fit the target article's existing sequence.

## Placement rules

1. **Title/intro images** — filenames matching `-0*.png`: place
   right after the intro paragraph(s) (`<p class="intro">`), before
   the first body paragraph. These are title photos **without
   captions** — **remove the `<figcaption>` line entirely** when
   pasting.
2. **Numbered Bild images** (`-1.png`, `-2.png`, …) always have
   captions and go inline near their first text reference.
3. **Find the first text reference** to each Bild/Tabelle in the
   article body (e.g. "Bild 1", "Bilder 5 und 6", "Tabelle 4",
   "das Bild 2").
4. **Insert the `<figure>` block AFTER the `</p>`** of the paragraph
   that first mentions it. **Never split a paragraph.** If the
   first reference sits mid-paragraph, the figure still goes after
   the *full* enclosing `</p>`.
   **Except when that paragraph is the item's LAST: then the figure goes after
   the byline**, not between the text and the byline. r190's rule that an
   author is never split from what they wrote outranks this one, and in a
   rubric of short items the first mentioning paragraph is routinely also the
   last — 8611's Aktuelles hit it 9 times in one article, and r310 flagged all
   nine as HARD.
5. **Read the caption from the scan.** Open the corresponding page
   PNG, find the caption printed under the image, type it verbatim
   into `<figcaption>`. If no caption is visible, omit
   `<figcaption>` entirely.
6. **Multiple files for one Bild** (e.g. `133-4a.png`, `133-4b.png`):
   put them in **ONE** `<figure>` with multiple `<img>` tags and one
   `<figcaption>` for the whole group.
7. **Plural references** ("Bilder 8 und 9"): place both figures
   after that paragraph, each as a **separate** `<figure>`.
8. **Don't duplicate** a `<figure>` already in the HTML.
9. **Unreferenced images**: locate the image on the scan FIRST,
   then work backwards to the HTML section. Don't pick a
   plausible-looking HTML section and guess. Read the image to see
   what it depicts; Read each page in the article's `64er.pages`
   range; find the image on the scan by visual content match;
   note which column + section heading it sits next to; only then
   insert into the matching HTML section.
10. **Inline portraits** (author bio photo) get
    `<img class="inline" src="…" alt="…">` without `<figure>`
    wrapper.

## TEXT IS THE PRINT'S. POSITION IS OURS.

Owner, 2026-10-07: *"if two image references are swapped, you can still
position them correctly. dont change any text, but the positioning is yours."*

This is the fidelity boundary for this step, and it cuts cleanly:

- **Every character is the print's.** Captions verbatim, prose verbatim, a
  printed typo kept as a printed typo (r325). Nothing in this section licenses
  touching a word.
- **Where an image sits on OUR page is ours.** The HTML reflows — one column
  instead of three, a different measure, a different page break — so the
  print's physical arrangement is not something we reproduce in the first
  place. Choosing which image goes with which caption is the same kind of
  decision as choosing where in the prose a figure lands, and this rule is
  already full of such choices (first mention, *never leave an orphan at the
  end*, a series placed between its neighbours).

**So when the print pairs a caption with the wrong image, place the image the
caption describes.** The reader gets a correct pairing and an unaltered text.

MEASURED on SH8605's 69, p72: *"Bild 2. Die Bedeutung der ADSR-Hüllkurve"* is
printed under the Hüllkurven-Beispiele TABLE, and *"Bild 3. Einige ADSR-Werte
und die dazugehörigen Hüllkurven"* beside the ADSR BOX — while the article
says *"Beispiel d in Bild 2"* and *"Bild 3 zeigt einige Hüllkurvenbeispiele"*.
The images go with the captions that describe them. No text changes, and no
Futureteufelchen is needed, because nothing the reader sees is wrong.

**THE FILE NAME DOES NOT MOVE WITH THE IMAGE.** The crop keeps the name the
owner delivered it under — that name records which figure on the page it was
cut from, which is a fact and stays true. So after a repositioning the file
name and the caption it now sits under will deliberately DISAGREE: SH8605's
`69-2.png` is the table, delivered as Bild 2 because the page prints it there,
and it is placed under Bild 3's caption because that is what Bild 3 describes.
That mismatch is correct and must not be "fixed" by a later pass. Record the
reason in `LOG.md`; do not put it in an HTML comment, which is reader-facing
German and never a process note.

### A LIST OF DECISIONS IS NOT A LIST OF OUTCOMES — REBUILD IT FROM THE ARTEFACT

The LOG records what was decided at a moment. The HTML records what happened.
**Where the two can diverge, the artefact governs, and the list is rebuilt from
it rather than carried forward.**

MEASURED on 8701. Step 150's LOG named six undelivered rows — *70-1, 12-x3,
49-x, 50-3, 144-00, 156-0*. Rebuilt from the HTML at the end of the build:

- **four of the six were wrong.** 12-x3, 49-x, 50-3 and 144-00 WERE delivered,
  under the owner's own names — `10-5`, `49-0`, `55-3`, `28-4` — and all four
  are placed.
- **two were missing.** 69-0 (the Fehlerteufelchen devil) and 178-0 (the
  Amerika skyline) are genuinely declined and were not on it.
- Two of six were right.

Nothing went wrong when that list was written: it was true of the delivery as
first matched. It went stale the moment a file turned out to be the same figure
under another name, and **nothing announces that.** A renamed delivery looks
exactly like a missing one plus an extra one.

So the true declined list is: every worklist row with no `<img src>` pointing
at it in the final HTML. One query over the artefact, at the end, and it cannot
be stale by construction. The same holds for any list of what we chose NOT to
do — r330's dispositions (which also go stale in MEANING, see its own section),
r220's orphan rows, the marks census's vanishers.

**Write the decision down when you make it, and rebuild the list when you
report it.** The first is the record; the second is the fact.

### A RECURRING ARTICLE'S FIGURE IS NOT A DECISION — CHECK THE CORPUS FIRST

**Before treating an undelivered row as declined, look for the same figure in
the other printings.** A piece that recurs — Checksummer, MSE, the Memory Map,
a Kurs, a Fehlerteufelchen — has been published many times. If every other
printing carries the figure, its absence here is an **OMISSION from the
delivery**, not a choice, and it is cut from the master and placed like the
others. One grep over `issues/*/*.html` answers it, and it outranks any
reasoning about what the figure or its caption is for.

MEASURED on 8701 p72. `70-1` (Checksummer Bild 1) was not delivered, was
recorded as declined, and the section below was written about what to do with
its orphaned caption. **Eight other printings carry that caption in a
`<figcaption>` with the image above it** — 8508/53, 8610/76, SH8503/6,
SH8505/6, SH8506/16, SH8507/6, SH8603/76, SH8608/129 — and 8701 was the only
one in the corpus with the figcaption and no image. The owner saw it on the
page and said so: *"we have the very same in 10+ other magazines, why ask me?
do it consistently!"*

The deliveries are large and the owner is deliberate, but **deliberate is not
the same as exhaustive**: a row can simply be missed, and an undelivered row
reads identically either way. The corpus is what tells them apart.

### A DECLINED FIGURE TAKES ITS LABEL, NOT THE ARTICLE'S PROSE

An undelivered worklist row is an answer and the figure does not ship — but
**what goes with it is the LABEL, not everything printed under the picture.**
Where a caption carries something the reader needs independently of the image —
instructions, data, a formula, a part number — it is article text that happens
to be set as a caption, and it stays.

MEASURED on 8701 p72. `70-1`, the framed PETSCII listing of the Checksummer,
was not delivered and was correctly declined. Its printed caption is **105
words of instructions**: *"Bild 1. In Zeile 10 müssen Sie nach den
Anführungsstrichen die ⟨SHIFT+CLR/HOME⟩-Taste drücken…"* — how to type the
listing in. Declining the crop took that with it, so the article kept its
*"Als Beispiel können Sie sich Bild 1 betrachten"* and lost the part that tells
the reader what to do.

> **ERRATUM, same day.** This section first cited 8610's printing of the same
> Bild as the precedent — *"8610 publishes the same caption AS TEXT"*. **It
> does not.** 8610/76 carries `<img src="76-1.png">` with that caption attached
> to it in the ordinary way; r330's D-001 was classed CROP precisely because
> 8610 has the figure and 8701 does not. The claim was read out of a
> disposition label and never checked against the file. The RULE below stands
> on its own reasoning — a procedure is not a label — but 8610 is not evidence
> for it, and a precedent nobody opened is not a precedent.

**AND THE SURVIVING TEXT IS PROSE, NOT A CAPTION.** Placed as
`<figure><figcaption>…</figcaption></figure>` with nothing inside, it renders
as a caption under an empty space, and the owner read it as *"Bild 1 is missing
the image"* — which is exactly what it looks like. The corpus's 68 image-less
`<figure>`s are not this shape: each holds a list, a table or a paragraph that
the caption describes. **A caption needs something to caption.** When a figure
is declined and its caption carries matter the reader needs, that matter goes
into the text flow as a paragraph, keeping its *"Bild 1."* opening so the
article's own reference still lands.

The test is not the caption's length or where it sits. It is: **if the picture
had never existed, would a reader still need these words?** A label — *"Bild 3.
VCR-Buchse (am Fernsehgerät)"* — answers no and goes with the figure. A
procedure answers yes and stays, at its print position, in the shape the corpus
uses for the same content elsewhere.

The dangling *"siehe Bild 1"* is not a reason to drop the caption too. It is the
ordinary consequence of a declined figure — 39 published articles name a Bild
and carry no image — and losing the instructions as well does not mend it.

**What this does NOT license.** It is about position only. A caption that is
wrong in its WORDS is still r300/r325's business and is recorded, not
rewritten. If you find yourself editing a character to make a pairing work,
you have left this rule.

## What is NOT a figure

**A cartoon is a filler, not part of the article.** Signed or not, a cartoon set
in leftover space belongs to the LAYOUT: never crop one, never place one, never
put one on the worklist. (Owner, 2026-10-04, on SH8602's `58-29`, a signed
cartoon at the end of the Sprites article that the survey had proposed as a
DRAWING. Nothing in this rule said so, and "every figure the pages call for"
invites it.)

**AND A CARTOON ON THE ARTICLE'S OWN SUBJECT IS STILL A CARTOON.** The
paragraph above says "set in leftover space", which reads as a test of
PLACEMENT and lets a topical one through. Owner, 2026-10-07, on SH8605's p8 bit
and byte cartoons and the p22 crocodile box: *"i didn't do any of the cartoons,
as always. usually they are not connected to articles. this time they are, but
they are still not helpful, and not referenced or labeled, so let's omit
them."*

So the test is not where it sits or what it depicts. **A cartoon is omitted
unless the body text REFERENCES it or the print LABELS it** — and if either is
true it is not a cartoon, it is a Bild with a number or a figure the prose
calls for. Being about the subject is not enough.

**APPLY IT TO EVERY UNCAPTIONED DRAWING BEFORE IT GETS A WORKLIST ROW.** The
test fires on the drawing, not on where it sits, so it has to be asked while
the row is being written — SH8605's p8 cartoons reached the worklist with
proposed names because each sits INSIDE its article on the article's own
subject, and a placement test never fired. **Lettering inside the art is not a
label**: a caption is set as a caption, in caption type, outside the drawing.

### EXCEPT IN THE LEAD SLOT: A DRAWING UNDER THE HEADLINE IS A FIGURE

Owner, 2026-10-17, on all four of SH8608's: **a drawing in the LEAD position is
cropped, even when the prose never references it and the print never labels
it.** That is the one place where position decides, against the paragraph above
— and it is a narrow place, so check all of it before claiming it:

- the drawing sits **directly under the article's headline**, before the body
  — and *before the body* is GEOMETRY, not reading order: **nothing of the
  article's text stands above it in its own column.** MEASURED on SH09,
  2026-11-06: `106-0` (a man with an axe over a table of papers) and `139-0`
  (a figure bursting through a door marked 1541) are framed, signed "bo"
  drawings at the top of column 2, inside the band under a full-width
  headline, with the bold intro beside them in column 1. In reading order they
  come after the intro; in their own column nothing comes before them, and
  they are **in the lead slot**. That is exactly what separates them from
  SH8608's p105 and p144 below, which carry body text above them in their own
  column. **This paragraph used to end "and they are lead drawings." The owner
  omitted both — see the next section.** The geometry was right; the
  conclusion drawn from it was not;
- it is the article's **`<page>-0`**, i.e. nothing else occupies the lead slot;
- it is **framed or set as an opening illustration**, not dropped into leftover
  space further down.

**AND `-0` IN THE NAME IS NOT EVIDENCE OF ANY OF THAT.** The suffix is a claim
about where the PRINT puts the picture, and a claim can be wrong — see *THE
SUFFIX FOLLOWS THE PRINT*. **Check the position on the page, not the
filename**, and note the trap: this exception is the one place where `-0`
carries a decision, so a mis-named `-0` is exactly the thing it cannot catch.
A cartoon named `-0` walks through a test that keys on `-0`.

MEASURED on SH8606, 2026-10-17: `108-0.png` was placed a year ago as the lead
image of *IRQ-Basic – eine Erweiterung für Sprite-Fans* and the owner removed
it — *"cropping SH8606/108-0 was a mistake."* It is a cartoon with no printed
caption that the prose never mentions, and **it sits at line 223 of 532**,
between two paragraphs on interrupt handling. The `-0` said lead slot; the page
said leftover space. The position settles it and the name never could.

### AND THE LEAD SLOT PROPOSES — IT DOES NOT DISPOSE

**The position test puts a drawing on the worklist. It does not settle what the
drawing IS.** MEASURED on SH09, 2026-11-14: `106-0` and `139-0` passed every
clause of the lead-slot exception above — framed, signed, directly under a
full-width headline, nothing above them in their own column, each its article's
`-0` — and the owner cut neither. His word: *"the others are comics i decide to
omit."* Both articles ship with no lead picture, and that is not a gap.

So the exception's two halves pull in opposite directions and both are the
owner's: **2026-10-17, a drawing in the lead slot is cropped even when nothing
references or labels it** (SH8608, all four); **2026-11-14, a comic in the lead
slot is omitted anyway** (SH09, both). They are not in conflict — the first is
about *position*, the second about *what the thing is*, and the cartoon test
was never repealed. The lead slot stops a cartoon being dropped for sitting at
the top of a page; it does not turn a cartoon into a figure.

**So a drawing that reaches the worklist through the lead slot ALONE — no
reference in the body, no printed label — is listed and marked as such**, e.g.
`lead slot only; omit if cartoon`, so the owner rules on it with the rest of
the crops instead of discovering it placed. Where he omits one, the closing
report says *omitted by the owner*, never *missing*, and no TODO and no
stand-in goes in its place.

**And the worklist header has to stop contradicting this.** SH09's read
*"Cartoons and ads are left out"* while listing two cartoons, because the
lead-slot clause had already promoted them — so the header made a promise the
rows broke, and the owner delivered 44 of 47 with no way to tell which absences
were his decision and which were oversights. Three had to go back to him. The
header now reads: *"Cartoons and ads are left out, except a drawing in the lead
slot, which is listed for you to rule on."*


MEASURED on SH8608: `10-0` (teacher at a blackboard, with the article's own
headline lettered on the board), `67-0` (a key tagged MONITOR unlocking a door
marked RAM ROM), `92-0` (a computer trailing smoke) and `94-0` (a robot with a
lettered speech bubble). All four are signed "bo", none is referenced by its
text, and the last two were filed as cartoon candidates. All four are crops.

**This does NOT reopen the cartoons already omitted**, and the distinction is
checkable rather than a matter of taste. SH8605's p8 bit and byte cartoons were
named `6-00` and `6-000` precisely BECAUSE the lead slot was taken — `6-0.png`
is a colour photograph of a C 64 mainboard. They sat inside the article, below
the opening, which is the "leftover space" case and is still omitted. So is
SH8602's `58-29`, a signed cartoon at the END of the Sprites article.

**"On the opening PAGE" is not the lead slot either.** MEASURED on SH8608:
p105's Einstein-at-a-monitor and p144's "Turbo" car are both signed "bo", both
on their article's first page, and both sit in the text flow BELOW the bold
intro with body text above them — the headline is followed immediately by the
intro, not by the drawing. Neither is referenced. Both stay off the worklist.
If the opening page alone counted, every filler that happens to land on a first
page would become a figure, which is the omission the owner settled in 2026-10.

The reason the lead slot is different: an opening illustration is part of how
the magazine presents the article, the way the headline and the kicker are. A
filler further down is the layout using up a hole. Both are drawn by the same
hand and neither is labelled, which is why nothing short of position separates
them.

**BUT THIS RULE GOVERNS THE WORKLIST, NOT THE DELIVERY. A CROP THAT ARRIVES IS
PLACED.** Owner, 2026-10-07: *"if they are delivered, they are not dropped. i
am deliberate about what goes into crops."* The owner does not cut cartoons, so
a worklist row for one normally comes back undelivered — and that silence is
the answer, not an omission to chase. But if a crop IS in the delivery, the
decision has already been made and it is not ours to revisit: place it.

**But it governs THIS build's delivery. Crops already in the directory from an
earlier hand are re-judged at 150.** A long-running issue can carry files
placed months or years before, by a pass that worked to different rules, and
step 150 naturally looks only at what just arrived.

MEASURED on SH8606, 2026-10-17: the delivery was 17 files and step 150 placed
them without re-judging the 62 already in the directory. `108-0.png` had been
there since 2025-10-23 and was a cartoon in leftover space; the owner removed
it after the issue was closed and published. The check is cheap — for every
pre-existing `-0`/`-00` file, its placed line number against the article's
length. An old `-0` sitting mid-article is the leftover-space case and goes to
the owner as a candidate for removal, **with its position as the evidence**.

This is the same principle as *owner crop wins* elsewhere in the chain. Judging
a delivered PNG against this section and holding it back inverts who decides.
MEASURED on SH8605: `6-00` and `6-000`, the p8 bit and byte cartoons, were
delivered; they were set aside as cartoons and had to be put back. **The test
in this section tells you what not to ASK for. It never tells you to refuse
what you were given.**

(The NAME of a delivered crop is a different matter and may well be wrong —
see *THE SUFFIX FOLLOWS THE PRINT* below. Rename it and place it; do not drop
it.)

### THE SUFFIX FOLLOWS THE PRINT, EVEN WHEN THE DELIVERED NAME DOES NOT

> **ERRATUM, 2026-10-17.** The parenthesis above used to read *"see renaming is
> authorised above"*. **There was no such section, above or below** — the only
> renaming guidance in this file was step 4 of the procedure, which renames a
> wrong PAGE PREFIX and says nothing about a suffix. A cross-reference to a
> section that was never written is a rule that cannot be followed: the builder
> looks, finds nothing, and either asks or guesses. Found on SH8608's delivery,
> where eight files needed exactly this rename. The section below is what the
> parenthesis was always pointing at.

**The owner decides WHICH crops exist. The print decides what each one is
CALLED.** Those are different authorities and they settle different halves of
the filename:

- **the prefix and the file's existence** are the owner's. A delivered crop is
  placed; an undelivered worklist row is an answer, not an omission.
- **the suffix** — `-0`, `-0a`, `-<n>`, `-x`, `-x<n>`, `-<n>x`, `-t<n>` — is a
  claim ABOUT THE PRINT: it says the page labels this figure "Bild 3", or
  labels it with no number at all. A cropping tool numbers its output files in
  the order they were cut; it has not read the page. So the suffix that arrives
  is frequently a count, not a claim, and the two collide hardest on an
  **unnumbered** figure, which a tool will happily call `-1`.

**AND THE PRINT INCLUDES THE BODY TEXT.** An uncaptioned figure that the PROSE
numbers — *"Ausdrucke wie in den Bildern 1 und 2 möglich"*, *"Bild 2 zeigt"* —
takes that number as its suffix, is placed **at the first prose reference
rather than in the lead slot**, and carries **no `<figcaption>`**, because the
print sets none. `-0` is for a lead picture the text never numbers; naming a
prose-numbered one `-0` leaves the reader's "Bilder 1 und 2" pointing at
nothing.

MEASURED on SH8606, 2026-10-17: `176-1` (prose numbers it Bild 1, the print
captions only Bild 2) and `155-0` (prose numbers it Bild 2, the print captions
only Bild 1) **are the same case and the worklist named them differently** —
one `-1`, one `-0` with the lead slot. The owner delivered `176-1`, which
settled it that way round.

So: **rename to what the print says, then place.** Do not ask about it, do not
hold the file back, and do not place it under a name the page contradicts — a
`-1` on a figure the print labels only "Bild." tells every later step that a
"Bild 1" exists on that page.

MEASURED on SH8608, 2026-10-17: of 44 delivered crops, **eight** carried `-1`
or `-2` on a figure the print leaves unnumbered — `6-1`, `94-1`, `102-1`,
`102-2`, `106-1`, `108-1`, `112-1`, `117-1`, renamed to `6-x`, `94-x`,
`102-x1`, `102-x2`, `106-x`, `108-x`, `112-x`, `117-x`. Every one was an
unnumbered printed "Bild." or a caption with no Bild label at all, and the
worklist row for each already said so.

**RECORD THE MAPPING IN `issues/<ID>/reviewed/`**, not in `LOG.md`, which is
git-ignored and does not survive. The delivered name is a fact about what the
owner handed over and the next build must be able to read it back, which is
the same reason the mark verdicts live in `reviewed/marks.txt`.

**This is NOT the same as *THE FILE NAME DOES NOT MOVE WITH THE IMAGE*.** That
rule governs a correctly-named crop placed under a different caption, where the
mismatch is deliberate and records where the crop came from. Here the suffix
was never true of anything. Renaming it destroys no information; keeping it
asserts something the page denies.

## A listing full of unreadable glyphs is cut WHOLE, not glyph by glyph

When a listing carries reverse or graphic PETSCII that cannot be named from the
scan, do **not** propose one crop per glyph, and never ship `[ILLEGIBLE]`.
**Crop the whole listing as one image**, and owner-crop-wins then replaces the
transcription.

> **ERRATUM, 2026-10-17.** This section said *listing* and was read as *anything
> full of unreadable glyphs*. **Two things that are not listings were put on
> SH8608's worklist as whole-frame crops, and neither was ever going to come.**
> Both had an answer already in the corpus. A worklist row that asks the owner
> for a crop the project does not cut costs a round trip and makes the delivery
> look incomplete when it is not. The two sections below are that erratum.

MEASURED on SH8602: the worklist proposed 39 individual glyph crops; the owner
cut five whole listings instead (article 20's Listings 6-9 and article 39's
Listing 1), covering 32 of them, with the remaining seven in boxed one-liners
cut as their boxes. Five images rather than 32, and the listing reads as
printed. Propose that shape FIRST.

**And a table printed across two pages is ONE crop.** The worklist asked for
`20-t2a` + `20-t2b` because the chart runs from one column onto the next page;
the owner cut it whole and it places once. The unit is the TABLE, not the page.


## APPLY r160'S SERIES RULE WHEN YOU WRITE THE WORKLIST, NOT WHEN 160 RUNS

r160 says **a numbered series is all typeset or all cropped** — decided for the
series, not per caption. That rule lives in r160, so it fires at 160, which is
AFTER the worklist has gone to the owner and he has started cutting.

MEASURED on SH10, 2026-11-15: the 54-row worklist went over at 17:43, and at
160 four Bild series turned out split between cropped and typeset members —
10 (1–2 cropped, 3 typeset), 71 (1–4 and 10–24 cropped, 5–9 typeset), 101 (1–2
cropped, 3–4 typeset), 126 (1 cropped, 2 typeset). Honouring r160 then needed a
**supplement of 11 rows** delivered to an owner already at work, and the
typeset versions stand in the HTML until the crops arrive.

**So at 150, for every figure you put on the list, look at its SERIES.** If one
member is cropped, every member goes on the list in the same delivery. The cost
of asking at 150 is one grep of the caption numbers; the cost of asking at 160
is a second pass for the owner.

**AND A REVERSE-VIDEO COLUMN IS CONTENT, SO IT IS A CROP.** Two of SH10's
supplement rows were not series members at all: the TEDMON dumps at 28-5 and
28-24 print a reverse-field column that the typeset version drops, and on p56
that column holds the REM banner's asterisks and `PROGRAMM
VERSUCHSKANINCHEN` — real characters, printed in reverse field, which a
`<pre>` renders as nothing or as black bars. SH8608's Bild 2 precedent for
typesetting a monitor dump was set before anyone checked what the column held.
**Read the column before you decide the dump is typesettable.**

## BEFORE A LISTING OR A TABLE GOES ON THE CROP WORKLIST, ASK WHETHER THE CHAIN CAN PRODUCE IT

**The owner cuts what only a camera can get. Everything the chain can build,
the chain builds.** A worklist row that asks for a crop of something we can
produce costs a round trip, and it makes a complete delivery look incomplete:
the file never arrives, because it was never the owner's to cut.

Run these three questions against every listing and every table before writing
its row. Each has a one-line check and each has now been got wrong:

| ask | check | MEASURED |
|---|---|---|
| **Is the program on the disk?** | `ls issues/<ID>/prg/` for the name the figure's caption or the neighbouring `binary_download` gives | SH8606's `114-l2`, *Listing 2* of Grafik 2000, went on the worklist as *"whole listing as one image (screen printout with reverse-video PETSCII)"*. `titel.prg` is on the disk. The printed listing differs from it — lines 91-93 and the texts GRAFIK 2000 / SCHRIFT-DEMO against the disk's PRODUCED 1984 / BY / FRANK BRENDEL — and **the article's own HTML comment already said so**, which is r120 check 4's *expected r300 patch* outcome, not a reason to photograph it |
| **Can the glyphs be rendered?** | is it a key/character table with a reverse-PETSCII column? | SH8608's `10-t1` — see the section above; the C 64 character ROM draws them |
| **Has a prior printing already set it?** | `grep -rl "<a distinctive caption phrase>" issues/*/*.html` | SH8608's `129-1` — six printings, every one an `<img>`, and the corpus shares 47 PNGs across issues, so a reprint's existing crop is reusable where the two printings are the same picture |

**WHEN YOU REUSE A REPRINT'S CROP, REUSE THE PICTURE AND NOTHING ELSE.** The
caption is always THIS printing's, read off this issue's own page, and the two
printings may well differ in it.

**AND REUSE NEEDS THE SAME PLATE, NOT THE SAME DRAWING.** The standard is
SH8608/129 against SH8603/76 below — *identical to the pixel*. A reproduction
at another scale, or relettered, or in colour where this one is not, is a
different plate, and shipping it would publish the other issue's printing as
this one's. MEASURED on SH09, 2026-11-06: rows `140-1` … `140-6` are the same
six figures as 8510's `34-1` … `34-6` — four of them the same drawings at
another size, `34-2` and `34-4` the colour versions of ours. **All six rows
stay**, and each names the prior file so the owner can see it is cutting that
art a second time. The corpus is full of these — SH09's worklist alone cites
8411/117, 8501/148, 8505/145, 8506/116 and 8612/21 — and the citation is the
work; the reuse is not. MEASURED on SH8608/129 against SH8603/76,
2026-10-17: the picture is identical to the pixel, and the captions are not —
ours prints *"Taste und <B> erzeugt werden."* where SH8603 prints *"Taste und B
erzeugt werden."*, and ours ends *"(Bild 1) so aus"* with no full stop where
SH8603 has *"so aus."* Both were read on both scans and both are PRINT
differences, left as printed. **Record the provenance** beside the crop in
`issues/<ID>/reviewed/` — which file it was copied from, and what you checked
it against — so a later build does not read a borrowed crop as one cut for this
issue.

**Reverse or graphic PETSCII inside a listing is not by itself a reason to
crop.** It is a rendering question with three established answers — the
`{CLR}` / `{4DOWN,2SPACE}` brace names the magazine itself prints, the
`<u>`/overline convention (8610/80), and a rendered glyph (`40-t1_*`). Reach
for the camera only when the printed thing is a photograph of a screen or a
printout that no source reproduces.

MEASURED, 2026-10-17: **three of the rows the owner did not deliver across two
issues were this same mistake**, and in each case the answer was already in the
repository — on the disk, in the character ROM, or in a prior issue. None of
the three was a judgement call; each was one command.

## A TABLE's reverse-character column is RENDERED FROM THE CHARACTER ROM

A key table whose ZEICHEN column shows the reverse PETSCII character for each
control key is **not** a crop at all, whole or glyph by glyph. **Typeset the
table, and render each reverse character from the C 64 character ROM.** Owner,
2026-10-17: *"previously, you used the C64 charset and created the pixel
characters."*

The corpus precedent is SH8605's Tabelle 1 in *40 Basic-Kurs von Anfang an*:
the table is an ordinary HTML `<table>` with its FUNKTION / TASTE(N) / ZEICHEN
/ ASCII columns, and each row's ZEICHEN cell holds one **32×32 bilevel PNG**
named `<page>-t<n>_<ascii>.png`, alt `reverses Zeichen für CHR$(<ascii>)`.
36 of them, `issues/SH8605/40-t1_5.png … 40-t1_159.png`, and SH8605's build
commit `2c7e1db8` records them as *"40 Tabelle 1 with its reverse characters
rendered from the C 64 character ROM"*.

**Why this is not the glyph-by-glyph crop the section above bans.** That ban is
about cutting 39 fragments out of a SCANNED listing, where each crop is a
different piece of one continuous printed image and the result is a mosaic. A
character rendered from the ROM is not a crop of anything: it is the glyph the
machine draws, generated once per ASCII code, identical in every issue, and it
restores a table the reader can actually read instead of a picture of one.

MEASURED on SH8608: the worklist asked the owner for `10-t1`, the whole p14
table, as one image — *"the ZEICHEN column is reverse PETSCII and cannot be
typeset"*. It can. It is the same table, in the same Basic-Kurs course, one
Sonderheft after the one that already rendered it.

## A RECURRING ARTICLE'S FIGURES FOLLOW ITS OTHER PRINTINGS

The magazine reprints a handful of boilerplate articles almost unchanged —
*Wie unsere Basic-Programme einzugeben sind*, the Checksummer, the disk notes.
**Before putting a figure from one of them on the worklist, look at how the
other printings set it.** They are the same article and they settle the
question without asking anyone.

**This is r330's reprint comparison used at worklist time rather than at the
end.** If the article is a reprint, its figure decisions are already made; the
only question is whether THIS printing differs, and that is a diff, not a
judgement. A worklist row for a recurring article that cites no other printing
has not been checked.

**AND NEITHER HAS A RULING ABOUT ONE.** MEASURED on SH8608's `129-1`,
2026-10-17: this section first said *"the other copies set it as a listing, so
this one is a listing too"* — written from the owner's *"consistent with all
other copies of this article, the one 'image' is a listing"* without counting
the copies. **There are six prior printings of the Checksummer and every one of
them sets Bild 1 as an `<img>` crop:**

| printing | file |
|---|---|
| `8508/53 Checksummer 64 – Neu` | `53-1.png` |
| `SH8503/6`, `SH8505/6`, `SH8507/6 Checksummer 64 … Neu` | `6-1.png` |
| `SH8506/16 Checksummer 64 — Neu` | `16-1.png` |
| `SH8603/76 Checksummer 20 V3` | `76-1.png` |

One command settles it, and it is the command this very section asks for:

```bash
grep -rl "So könnte ein Teil eines Listings" issues/*/*.html
```

Found by the builder, which had been told to type the listing, counted the
corpus instead of complying, and held the article out of its commit. **The
owner's sentence is about the ARTICLE — the one picture in it is a picture of a
listing — not an instruction to typeset it.** A one-sentence ruling relayed
without the count behind it is a guess wearing the owner's voice, and it is the
supervisor's job to do that count before passing the ruling on, not the
builder's to undo it afterwards.
### WHERE THE OTHER PRINTING'S PAGE IMAGE LIVES — AND WHY THE `pdftoppm` BAN DOES NOT REACH IT

A published issue has no `<tmp>`: it was wiped when its build finished. Its page
images are **`/Volumes/S/png/<ID>/NNN.png`**, the scans themselves — 53 issues
including SH09 — which r330
names as *the authority for their side*.

**THEIR RESOLUTION VARIES BY ISSUE, AND SOMETIMES INSIDE ONE — MEASURE, DO NOT
ASSUME.** MEASURED 2026-11-14: the monthlies are 2400 dpi throughout (8603 p055
20496x28751, 8510 p034 20761x28751), while SH8608's inner pages are 600 dpi
(p105 5054x7188) under a 2400 dpi cover (p001 20408x28751). This paragraph said
"inner pages about 5050x7190, covers at 2400 dpi" until SH09's builder measured
a monthly and found otherwise — **I had generalised one issue's shape to 53**,
which is the same error as carrying a count forward without re-measuring it.

Look there, and at the delivered crops
in `issues/<ID>/*.png`, which are durable and in the repo: 89 of them for
SH8608.

**The ban on `pdftoppm` is scoped to the issue being BUILT**, where that PDF
does not exist yet and `masters600` is the better image (r000, *THE PAGE IMAGE
IS `masters600`*). It was never about another issue's published PDF — r330
prescribes exactly that render for 8404, the one issue with no scans at all.

MEASURED on SH09, 2026-11-06: a sub-agent sent to compare SH09's layout against
SH8608 rendered SH8608's pages with `pdftoppm` and reported itself for breaking
its brief. It had nowhere else to go. **This section sends you to another
printing and named no file for it**, and the brief said *"Never `pdftoppm`; the
page image is masters600"* — which for SH8608 names a directory that no longer
exists. A ban with no stated scope is read as global, and then the one case it
was never about has no route at all. Nothing of SH09 was rendered that way, and
the finding the agent brought back stands.

## Two resolution buckets, and which one a figure is in

`tools/convert-scans.sh` states the project's convention for every image file
this chain writes:

| bucket | delivered at | how |
|---|---|---|
| colour / greyscale art (`c/`, `gray/`) | **150 dpi** | `-resize 25%` of the 600 dpi crop |
| bilevel line art (`bw/`, `dots/`) | **600 dpi** | no resize |

A crop cut off `masters600` is at 600 dpi by construction, so the colour bucket
always needs the 25 % step and the line-art bucket never does. 8610's editor
portrait came off the master at 1370×1145 / 3.9 MB and was resized to 343×286 /
209 KB, which is 8609's `8-0.png` (339×279 / 208 KB) — the prior issue's file is
the check that the bucket is right. Its Fehlerteufelchen devil is line art and
stays at 600 dpi: `80-0.png` 1070×1062, as 8609's `61-0.png` 1017×1072.

Shipping a colour figure at 600 dpi is not a visible defect on the page — it is
a 3.9 MB download where 209 KB was intended, and nothing in the chain measures
it. Compare against the analogous figure in the previous issue before
committing the file.

### EVERY DELIVERED CROP IS RAW 600 DPI RGB, AND CLASSIFYING IT IS YOUR JOB

**The owner's standing instruction, 2026-10-24: _"in the future, i'll never
give you processed/bucketed crops, only raw 600 dpi rgb crops!"_** So there is
nothing to detect and no second case to check for. A crop delivery is always
8-bit sRGB straight off the scan, it always arrives unbucketed, and the build
always sorts it into `png/{bw,gray,dots,c}/` and runs
`tools/convert-scans.sh` before placing the output.

### A DELIVERED CROP MAY CARRY AN ALPHA CHANNEL, AND `-alpha off` IS NOT ALWAYS RIGHT

**The owner's instruction, 2026-11-06: a placed image carries no alpha —
"remove the channel with `-alpha off` (keeps RGB), never composite".** That
instruction had lived only in control's own notes until 2026-11-15, so SH10's
builder met an alpha crop with nothing in these files to go on and had to reason
it out. It is here now.

**And `-alpha off` does the wrong thing when the cut-out sits over black.**
MEASURED on SH10's 10-1 and 28-0: both arrived RGBA with a cut-out alpha whose
underlying RGB is BLACK, so `-alpha off` keeps that RGB and ships **black
bars** where the transparency was. The two cases:

| the RGB under the alpha | operation |
|---|---|
| **is the image** (the usual case) | `-alpha off` — drop the channel, keep the pixels |
| **is black, under a cut-out** | **flatten onto white** (`-background white -alpha remove`) |

**Either way, verify against `sheets600`** at the crop's own box: the sheet is
what the page actually looks like there, and it settles which of the two the
file is. SH10 verified before choosing, which is what made it a decision rather
than a guess.

This does **not** loosen *owner crop wins*. What the owner decided is the
FRAMING and the CHOICE — which figure ships as a picture, where it is cut, what
it includes. Never re-cut, re-frame, extend or substitute a delivered crop, and
never set a table typeset that arrived as a crop. The bucket is a separate
question, and it is now always open.

**Why the conversion is not optional.** SH8607's 38 crops were **151 MB** as
delivered and **1.8 MB** converted — 85x over the set, 180x on `66-1`
(20.9 MB → 116 KB), 50x on `124-0` (12.2 MB → 246 KB). Placing a delivery
as-is commits scan masters to the published repository, which is precisely what
`.gitignore`'s `issues/*/*` exists to prevent.

**Classify by what the figure IS, which is not what the page is printed in.** A
worklist note that a page carries colour is not a bucket assignment: say what
the page is, never which bucket the crop must be in. MEASURED on SH8608,
2026-10-17, and ruled by the owner — three crops on strongly coloured grounds
(`10-1_2`, memory maps on blue, 77 % of the box above chroma 25; `10-3`, a
green/orange/blue slab, 93 %; `10-4`, an orange header band, 19 %) went to
`bw/` and lost the colour, and the owner ruled it **on purpose**. Grey-ground
drawings in the same delivery (`10-6`, `44-1`, `47-4`, `47-5`, `47-8`) read
better as clean line art than as screened grey. So:

| the figure is | bucket | why |
|---|---|---|
| line art, listing, table, text screenshot — black on white | `bw/` | 600 dpi bilevel, no resize |
| line art or a screen on a **printed grey ground** | `dots/` | `-lat 41x41` reads the ground as ground; a plain threshold turns it into surviving dot noise |
| a real halftone — a photograph, continuous tone | `gray/` | 150 dpi 8-bit, 25 %; a threshold would destroy it |
| colour that carries MEANING, not just a ground | `c/` | 150 dpi colour; rare — SH8607 used it for nothing |

A coloured or tinted ground going to `bw/` loses the ground, and that IS
visible on the page, unlike the harmless direction above. It is still often
right. **Settle the uncertain ones by rendering both ways and looking, not by
argument** — SH8607's four doubtful files (`110-3`, `164-1`, `6-3`, `6-4`) all
turned out to be `bw/`: what read as a ground was the face's own weight.

**Then show the classification to the owner for a yes before placing
anything**, and record it in `issues/<ID>/reviewed/crop-classification.txt`
with the *reason* for each bucket, not just the file list. The next build's
question is never "which bucket was `66-1` in", it is "why".

**Keep the RGB sources, and NEVER COMMIT THEM.** Owner, 2026-10-24: *"i meant
DO NOT COMMIT THE RAW PNGs, but do commit everything else including converted
pngs. make it a rule to never commit the raw pngs."* The sources stay under
`issues/<ID>/png/<bucket>/` and the converted files go to the issue root. Do
not delete `png/` (*"KEEP the png dir"*).

`.gitignore` does most of this for you: `issues/*/*` hides `png/` entirely,
while `!issues/*/*.png` re-includes the root. **But the gitignore cannot tell a
raw crop from a converted one** — it only knows where the file sits. A raw file
copied or moved to the issue root instead of converted is 150 MB of scan master
that git will take without complaint, and `issues/*/*.png` makes it look
intentional.

**So check before the commit, not after.** The converted file and its source
share a name, so two cheap tests catch it:

```bash
ID=SH8607
# 1. a root PNG byte-identical to its png/<bucket>/ source was never converted.
#    find, not a glob: a renamed crop (118-1 -> 118-x1) has no source of its
#    own name, and under zsh an unmatched glob ABORTS THE WHOLE LOOP.
for f in issues/$ID/*.png; do b=$(basename "$f")
  s=$(find "issues/$ID/png" -maxdepth 2 -name "$b" 2>/dev/null | head -1)
  [ -n "$s" ] && cmp -s "$f" "$s" && echo "RAW AT ROOT (identical to source): $b"
done
# 2. and the shape of a raw crop: 8-bit sRGB at the source's own pixel size.
#    title.png is legitimately 8-bit sRGB (1240x1754, the 150 dpi cover), so
#    exclude it or it is flagged on every issue.
magick identify -format '%f %[depth] %[colorspace] %wx%h\n' issues/$ID/*.png |
  awk '$1!="title.png" && $2==8 && $3=="sRGB"'
```

Test 1 is the reliable one. Test 2 lists candidates, not culprits — a genuine
`c/` figure is also 8-bit sRGB, so compare each hit against its source's
dimensions: equal means raw, a quarter means converted.

A commit that has already taken one is not fixed by deleting the file in a
later commit — the blob stays in history, which is what `.gitignore`'s own
comment records about the `_work.zip` that broke pushing. Catch it before.

### A PRINT DEFECT CAN FLIP POLARITY UNDER BILEVEL

A pale flaw on a tinted ground — a glare band across a photographed printout, a
fold, a light scuff — is brighter than its surround in the master and darker
than its surround after thresholding. It changes from a white streak nobody
notices into a **solid black bar**, which looks exactly like damage the
conversion caused.

MEASURED on SH8608's `131-1`, 2026-10-17: a black band across the directory
listing covers part of the `dos 5.1` row and the row below it. It was reported
as a conversion defect that "eats two rows". **It does not.** The master has a
pale glare band in the same place that already wipes out the same characters —
the magazine photographed a printout with a highlight across it, so the loss is
in the plate and ships either way. Only the colour of the loss changed.

**So before reporting a dark band, bar or blob in a bilevel crop, open the same
box in the master and say what is there.** If the characters are already gone,
it is the plate (r000, *WHAT WE PUBLISH IS THE ORIGINAL PRINTING PLATE*) and
there is nothing to fix. A claim that the conversion destroyed content must
name the content the master still has.

## THE BUILD CUTS THE FIRST VERSION OF EVERY CROP. THE OWNER REVIEWS IT

**Owner, 2026-11-17, after seeing nine agent-cut crops:** *"crops are great,
they will need another pass by me, but will make everything WAY easier. make it
a formal rule, and create all crops with the proper naming, plus the 1cm
versions."*

This inverts OWNER INPUT 2 and it is the biggest change this step has had. The
worklist used to be a list of coordinates the owner opened `sheets600` to cut by
hand, one row at a time, for an issue with ninety-odd figures. **Now the build
cuts all of them and he passes over the result.** Everything downstream is
unchanged: the crops are still raw 600 dpi RGB, still unbucketed, still
classified and run through `convert-scans.sh` by the build before placement.

What the owner's pass is for has not changed either — *owner-crop-wins*: a crop
he re-cuts or delivers replaces ours, and ours was never more than a proposal.
What changed is that his pass starts from ninety-three cut pictures instead of
ninety-three rows of `WxH+X+Y`.

### What the build produces

For **every row of the worklist**, two files in `<tmp>/crops_v1/`:

| file | what it is |
|---|---|
| `<name>.png` | the proposal: the region, cut to the artwork's own boundary |
| `<name>_1cm.png` | the same region grown **1 cm on all four sides**, for judging the boundary without opening the master |
| `<name>_1cm_box.png` | the `_1cm` image with a **1 px black/white DASHED rectangle 1 px OUTSIDE** the proposal's boundary, so the cut is visible against its surroundings |

The third file is where the review actually happens: it shows the proposed edge
in its context without painting over a single pixel of the picture being
judged. Owner, 2026-11-17: *"we need 3 for each crop. in addition: 1cm version
with a 1px yellow line 1 px outside of the crop position."*

**The line goes outside, never on the crop.** In the `_1cm` frame the proposal
occupies `(L, T)` to `(L+w, T+h)`, so the rectangle is the columns `L-1` and
`L+w` and the rows `T-1` and `T+h`. Covering the proposal's own edge pixel
would hide the thing being judged.

**And a marker colour must work on EVERY ground the corpus has**, not on the
one in front of you. Measure the band just outside the drawn line across the
whole set before choosing one; if a single colour can be defeated by any common
ground, use a pattern instead of arguing about the colour.

**Where a side is clamped to 0 there is no outside pixel — leave that side
open** and say so. Do not close the rectangle by drawing inside. An open edge
is also the truth: the crop runs to the sheet edge there. MEASURED on 8702:
`28-0a` and `28-0b`, two halves of one picture printed to the trim.

**THE LINE IS BLACK/WHITE DASHED, DASH LENGTH 20 px, PHASED ON A 20 px CELL
GRID** — `black if ((x // 20) + (y // 20)) % 2 == 0 else white`, x and y in the
`_1cm` frame. Owner, 2026-11-17: first *"1px black/white striped with stripe
len 1"*, then **"from now on: black/white dashed with 20px dash length"**. 20 px
at 600 dpi is 0.85 mm, so it reads as a dash at 100 %.

**Phase it on the grid, not on a walk around the perimeter.** The grid keeps
all four sides in phase with each other, and — the part that matters — it stays
verifiable PER PIXEL. A perimeter walk depends on where you started and cannot
be checked without re-walking it. A dash cut short where a corner falls
mid-cell is correct; leave it.

It began as a plain yellow line, on his instruction, and that was measurably
wrong: **90 of 8702's 92 crops sit on a surround that is over 50 % near-white,
87 of them on pure white**, because what lies just outside a figure is the page
margin — and `#FFFF00` differs from `#FFFFFF` in the blue channel alone. A
stripe needs no lucky ground: the black half carries it on paper, the white
half carries it on a dark photograph. **The parity phase is not decoration** —
it alternates along horizontal and vertical runs alike, so the four corners
join without a doubled or dropped pixel, which a per-side counter would not
manage.

**Verify the third file against the second**: it must differ ONLY on the
rectangle's own pixels, every rectangle pixel must equal the parity rule
exactly, and the crop's own area must be byte-identical. The striped line makes
this check stronger than the solid one was — the old form could only ask "is it
yellow", this one asks "is it the RIGHT pixel", so a line drawn one pixel in or
one pixel out of phase is caught.

### NO CROP MAY BEGIN OR END WITH A LINE OF BARE PAPER

Before the folder is opened, flag every crop whose **outermost row or column is
entirely pure paper** (255/255/255). It is a few lines of numpy and it is the
cheapest true statement about a cut edge there is: a figure's own boundary is
where its ink starts, so a full line of paper at the edge means the cut missed
the picture.

```python
# `a` is the crop as RGB; the PER-CHANNEL MINIMUM is the ink measure.
ink = np.array(img.convert('RGB')).min(axis=2)

def paper_run(lines, frac=0.01, thr=250):   # lines of `ink`, from the edge INWARD
    k = 0
    for l in lines:
        if (l < thr).mean() < frac: k += 1
        else: break
    return k                                 # flag any side with k > 0
```

**SAY WHICH CHANNEL. An unpinned predicate gives two answers.** Written as
`(l < thr)` with no statement of what `l` is, this reads equally as luminance
or as the per-channel minimum, and control and the builder duly measured
8702's `10-x3` right edge as 2 and as 1. MEASURED over all 92 with both: they
disagree on **exactly one crop, at the boundary** — that column has 13 pixels
below the threshold where 1 % of 1426 rows is 14.26.

Use the **per-channel minimum**: a pixel is ink if ANY channel is dark. It is
the right measure for a magazine full of pale tints, where a cyan or yellow
ground can sit above a luminance threshold while being plainly not paper — and
it errs toward calling a line CONTENT, which is the safe direction here, since
a wrong trim costs a figure and a wrong keep costs a look.

**THE OBVIOUS VERSION OF THIS CHECK HAS THE `-trim` BUG IN IT.** The first
version written here was `(pixels == 255).all()` on the OUTERMOST LINE ONLY.
It fails the same two ways:

- **"all 255" is an any-pixel predicate**, so scan noise defeats it — a paper
  line reads 254, not 255.
- **One line is not a run.** A single dark pixel in line 0 hides whatever is
  behind it. MEASURED on 8702's `10-x1`: its top row has min 246, **its second
  row is literally all-255**, and the check reported nothing. That is dust
  holding an edge, in the very check written to catch dust holding an edge.

So: a FRACTION of the line, and count the RUN inward. MEASURED over 8702's 92
crops with the corrected predicate: five carry a leading paper run and **all
five are among the nine that were cut by the broken instrument** — `22-2` B28,
`22-1` R3 B4, `10-x1` T3 B1, `10-x3` L1 R2, `14-0` T1. The 83 cut with the
fraction instrument and reviewed by eye: zero.

**FLAG, NEVER AUTO-TRIM.** A figure that legitimately ends in white with no
frame would be damaged by an automatic trim, and nothing in the measurement can
tell the two apart. Flagging costs a look; trimming costs a figure.

**8702 supplied the case that proves it.** `22-2`'s bottom shows a paper run of
**28 lines** — and those lines are the panel's own bottom frame rule, printed
too pale to cross the threshold. An auto-trim would have eaten the frame it
was meant to find. One measurement, two opposite meanings, and only a look
separates them.

**AND IT IS ONE OF A PAIR, BECAUSE THE TWO TRIM PREDICATES FAIL IN OPPOSITE
DIRECTIONS.** This was written as if it were sufficient. It is not:

| predicate | how it fails | what catches it |
|---|---|---|
| **any pixel** within fuzz of white holds the line (ImageMagick `-trim`) | **under-trims** — one dust speck anywhere in a column holds the whole edge | the pure-paper flag above |
| **a fraction** of the line is darker than a threshold | **over-trims** — a faint edge, a pale ground or a thin frame rule falls under the fraction and is eaten | a band test on the OUTSIDE of each edge |

MEASURED on 8702: the 83 crops of the main pass used the fraction predicate
(>3 % of the line darker than 235) and its eye review grew **56** boxes, which
is the over-trim showing up. The nine used `-trim` at 6 % fuzz and `10-x2` kept
three columns of bare paper, which is the under-trim showing up. **Run both
flags. Neither predicate is safe alone.**

### `-trim` FOLLOWED BY `-shave` IS BROKEN BY CONSTRUCTION — AND IT ATE PLATE

The command that cut 8702's first nine:

```
magick NNN.png -crop WxH+X+Y +repage   -bordercolor white -border 1 -fuzz 6% -trim +repage -shave 1x1 +repage
```

The 1 px border is added so a picture lying flush to the crop edge is not eaten
by the trim. **But `-trim` removes that border itself** — it is background by
construction — so by the time `-shave 1x1` runs there is nothing left of it,
and the shave takes **one line of real image off every side**. MEASURED on
`10-x2`: the shaved lines held 80 ink pixels on the right, 34 at the bottom, 2
at the top. That is plate, thrown away, and no check saw it because a crop one
pixel too TIGHT looks like a crop.

On the left the same command did the opposite: a dust speck 4 px outside the
photograph (two pixels, min 216) held the trim, the shave then removed the
speck's own column, and three columns of pure paper were left standing with
nothing visible to explain them. **One command, both failure directions, on one
edge each.**

**The general defect is not the fuzz value. It is that a cleanup step removed
something it had not checked was still there.** `-shave 1x1` is a blind
positional operation that assumed the state its own earlier step had destroyed.
Where you add a guard and then remove it, remove it by measuring what you
added, or arrange that it cannot be consumed — never by position alone.

So: **do not pair `-trim` with `-shave`.** Trim on a fraction-of-line
predicate, with no shave after it, and let the two flags above police the
result.

MEASURED on 8702, which is also why this is here: of 92 crops exactly **one**
tripped it — `10-x2`, three pure-white columns on the left, so its edge sat
0.13 mm outside a near-black photograph, where a white sliver is as visible as
a defect gets. The owner found it in the `_1cm_box` file, which is precisely
what that file is for. The other 91 measured zero on all four sides, so the
trim was provably a no-op on every one of them — **including the panel crops,
whose frame rule is ink at the outermost line.**

**And the one that tripped it was the one that had skipped the measurement.**
The 83 crops cut in the main pass went through an edge-ink check and an eye
review that recut 56 of them; the first nine were cut before that instrument
existed and were then frozen, on control's instruction, because the owner had
approved them. Eight were tight by luck. **An approval is not a measurement**,
and freezing a set puts it outside every check invented afterwards — so when a
later pass builds an instrument, run it over the frozen set too and report the
result, even when nothing is expected to change.

- `<name>` is the **final r150 name** — `8-0`, `10-x1`, `22-3`, `67-2a` — so an
  accepted crop moves into `issues/<ID>/` unchanged. Never a lettered start
  page: Verification 1 matches `[0-9]+-[0-9a-z_]+\.png`, so page 8a's lead
  image is `8-0.png`.
- **1 cm at 600 dpi is 236 px** (600 / 2.54 = 236.22), so each `_1cm` file is
  exactly **+472 px in each axis** over its tight twin.
- `_1cm` and not `-1cm`: a `-` suffix reads as the figure-numbering grammar.

### Cut from `masters600`, not from `sheets600`

The worklist's rows are in the `sheets600` frame because that is the file the
OWNER opens (see the section below, which still stands for his re-cuts). **Our
own cuts come from `masters600`**, where every other step looks, translated by
each page's `sheet-box`. Find the translation by exact pixel match, not by
arithmetic alone, and say in the README that you did.

### The boundary is the artwork's, never the pen stroke's

A box on a worklist — his or ours — says WHICH artwork. The master says WHERE.
Cut to the photograph's own edge, the diagram's ruled frame, the illustration's
extent; a white sliver along one side means the box was followed instead of the
picture.

**A framed or tinted panel is part of the figure.** MEASURED on 8702's `22-1`,
`22-2`, `22-3`: the magazine sets Bild 1-3 as panels with a thin frame rule,
and 22-1's yellow tint is unarguably the figure's own. Cutting the other two to
the bare drawing would have left three siblings of one article inconsistent
with each other. Keep the panel, keep the frame, and keep the white inside the
panel — on 22-2 that white is the point the diagram is making.

**Captions are never in the crop.** They become `<figcaption>` text and are
re-read from the print at placement.

### Clamp at the sheet, and say so

A `_1cm` box can run off the sheet. Clamp it to the master's own bounds, **pad
with nothing**, and name every crop that could not get its full centimetre,
with how much it got on which side. MEASURED on 8702: the masters are 4961 x
7016 — exactly A4 at 600 dpi — and `22-1_1cm` at 4841 px wide clears the left
edge by 17 px, 0.7 mm. The full-width figures have no room for a second
centimetre. **A wide crop that is quietly not wide is worse than no wide crop**,
because it is read as context that is not there.

### Verification — the pair, not the dimensions

A dimensions line cannot tell you the growth was centred, or that nothing was
resampled on the way. Compare the pixels:

```python
# every pair, before the folder is opened
t = Image.open(f'{d}/{n}.png').convert('RGB')
w = Image.open(f'{d}/{n}_1cm.png').convert('RGB')
assert (w.width - t.width, w.height - t.height) == (472, 472)   # unless clamped
assert w.crop((236, 236, 236 + t.width, 236 + t.height)).tobytes() == t.tobytes()
```

The centre of the wide crop must be **byte-identical** to the tight one. That
proves the two files are provably the same region of the same master, which is
the only thing that makes the comparison worth his time.

### Hand it over

- A `README.txt` in the folder: what the three kinds of file are, which master
  set they came from, that they are raw and unclassified, the clamping and
  open-edge notes, and the readings you want his eye on. Text, and short.
- **NO CONTACT SHEETS AND NO DOWNSCALES.** Owner, 2026-11-17, while a set of
  paired sheets was being built for him: *"dont show me downscales or contact
  sheets, just 3 files per crop that i asked for"*. The folder he opens holds
  the three files per crop and the two text files, nothing else. A reduced
  overview is the build's convenience, not his: he is judging a boundary at
  the pixel, and an overview cannot show him one. It also quietly broke the
  instrument — a 1 px line at 600 dpi is 0.042 mm and does not survive any
  downscale, so a sheet would have had to thicken the very line whose position
  is the thing under review.
- `open` the directory.
- They stay in `crops_v1/`. Nothing enters `issues/<ID>/` until he has passed
  over it, and nothing is classified, converted or placed before then.

### Flag a reading, do not ask a question

Where a boundary is genuinely ambiguous, cut your best reading and name it in
the README. A flagged guess he can correct in the picture beats a question that
stops ninety-three crops while it waits for an answer.

**And apply the survival gate before you flag a MARK.** MEASURED on 8702's
`11-x`: faint purple dashes crossed the cyan corner of a Sonderheft cover at
600 dpi, correctly left untouched and raised. But the crop is a colour figure,
`convert-scans.sh` resizes bucket `c` to 25 %, and at the delivered 150 dpi the
corner is clean — nothing survives that reads as a dash. No census row, no
crop to the owner, nothing repainted. *Surface every mark with a crop* still
stands; what the gate adds is that the arithmetic answers first, and his
attention is spent only on what a reader could see.

## THE WORKLIST'S GEOMETRY IS IN THE `sheets600` FRAME — SAY SO IN ITS HEADER

**You look at `masters600`, the owner cuts from `sheets600`, AND THEY ARE NOT
THE SAME COORDINATE SYSTEM.** Every rule that tells you to look at a page names
`masters600`; r000 hands the owner `sheets600` at the end of 005; until
2026-11-06 nothing said that a box measured on the one lands somewhere else on
the other.

The relation is exact. Step 005 crops the traced page out of the sheet and
anchors it at the canvas's top-left, so

    sheet_x = master_x + sheet-box.x0
    sheet_y = master_y + sheet-box.y0

with `sheet-box` read from `<tmp>/masters600/NNN.stamp.txt`. It is a pure
integer translation — no rotation, no scale, because both images are levelled by
the same measurement. VERIFIED on SH09 pp 030, 119 and 139 by correlating a
400x400 master patch into the sheet: **r = 1.00000 at exactly that offset**,
residual 0 px in both axes.

MEASURED on SH09, 2026-11-06: **162 of 168 pages carry a non-zero offset**, up
to **86 px in x** (p099) and **14 px in y** (p042) — 3.6 mm at 600 dpi, which is
the width of a figure's edge. The canvases differ as well (`masters600`
5457x7181 against `sheets600` 5040x7203-7205, and about 5290 wide on the four
cover pages), but that difference is fabricated margin and moves nothing; only
`sheet-box` does.

So, two lines of the worklist's job:

- **measure its boxes on `sheets600`**, the file the owner actually opens, and
- **say in the header which frame they are in**, the way SH09's does.

A row is a rough `WxH+X+Y` that the owner refines by eye, so the frame has never
been fatal — but it is a systematic shift of up to 86 px on 96 % of pages, and
that is exactly the error that survives by looking like a rough number. SH8608's
worklist quoted the master frame and said nothing; its tmp is gone, so how far
that reached cannot be recovered.

## A BLACK BOX ROUND A FIGURE GOES — BUT FIRST, IS IT A BOX?

Owner, 2026-11-17: *"22-* black box goes. 46-4 stays because its really in a
table shape, i.e. line inside that touch the border. all others black box
goes"*, and *"when losing the box, crop JUST INSIDE the box, dont find the
minimal bounding box of the content"*.

**The cut is a fixed distance from the rule, never a search for content.** Find
the band's peak within 45 lines, then cut at the first line past it whose dark
fraction has fallen 75 % of the way back to the ground INSIDE the box — the
ground measured as the median of the lines 8–28 px past the peak. The inside
white and tint are kept by construction. **Do not apply the edge policy to a
crop you have just cut to its rule**; shrinking to content afterwards is the
thing this forbids.

### FINDING THE RULE: A RELATIVE STEP, NOT "IS THE INSIDE LIGHT?"

The detector's first form demanded that the 10 lines just inside the band be
under 0.25 dark — *"lighter inside"*. **That clause assumes a figure is paler
than its own frame, and a dark one is not.**

MEASURED on 8702's `156-1`, which the owner found by eye after the whole set
had been passed: a textbook rule, coverage **1.00**, 7–8 px thick, 1–2 px in,
on all four sides — rejected, because the hardcopy's dense halftone runs flush
to the rule and reads 0.39–0.45 just inside it. Its LEFT side is worse: the
content is solid dark, the saturated band never ends, and the thickness test
threw it out at 59 px. `83-1` had failed the same way and was hand-cut around
the problem instead of fixing it. **A hand-cut is how a blind spot survives.**

So:

1. **A rule is a band at ≥0.95 coverage, ≤15 px thick, starting within 12 px,
   whose mean coverage exceeds the mean of the 10 lines just inside it by
   ≥0.30.** A relative step, not an absolute level. A dark figure steps 1.00 →
   0.45 and passes; content that merely darkens inward has no step and is
   still rejected.
2. **A side whose saturated band runs past 15 px is `indeterminate`, not
   "no rule".** Say so. The rule may be there and inseparable from the content.
3. **FRAMED IS DECIDED PER FIGURE, NOT PER SIDE.** Two or more sides reading
   `rule` with continuity ≥0.8 make the figure framed, and the indeterminate
   sides are then cut at the inner offset the resolved sides agree on. Same
   lesson as the skew: **the figure is the unit of judgement.**

MEASURED over all 92 with the corrected test, which is the only reason to
trust it: it catches `156-1` (B/R/T rule at continuity 1.00, L indeterminate)
and **changes nothing else**. `39-0` now reads `rule` on four sides and is
still rejected by the continuity test at 0.09–0.17, so the tests compose.
Every dark photograph in the issue — `10-x3`, `30-1`, `27-x1`, `50-0`,
`135-0`, `160-x1/x2`, `162-x2` — produces only indeterminate sides and no
`rule`, so none is falsely framed. **A repair that finds exactly the case that
prompted it and nothing else is the one to ship.**

### TWO TESTS BEFORE YOU CUT, BOTH THE OWNER'S

**1. Is it a continuous line?** *"39-0 isnt a durchgehende linie. not a full
box."* Measure the **longest unbroken dark run along the side, as a share of
the side** — not the dark fraction, which a dashed line passes easily.

**2. Do hard lines inside touch it?** *"46-4 stays because its really in a
table shape"*; *"156-3 … its like a table, because there are clear hard lines
inside that touch the border."* Count lines running ≥80 px inward from just
inside the rule. **Two per side is the baseline — those are the frame's own
corners.** More than two means internal structure meets the border, and cutting
the border would leave those lines hanging in air.

MEASURED on 8702:

| crop | coverage | longest unbroken run | spokes | verdict |
|---|---|---|---|---|
| `39-0` ABENTEUER grid | 0.95–0.96 | **0.09–0.17** | 12–21 | not a box — dashed, and the grid's own edge |
| `156-3` Giga-CAD screen | 0.95–1.00 | 1.00 | **3–5** | a box, but a table: the window's hard lines meet it |
| `46-4` pin table | 0.98–1.00 | 0.24–1.00 | **6** | a table |
| the 18 that were cut | 0.85+ | ~1.00 | 2 | a frame: cut it |

**Coverage alone would have cut the crossword.** `39-0`'s outer line is 96 %
dark and 0.09 continuous — the cell boundaries with gaps where white cells meet
the edge. That is the single sharpest discriminator found here.

**Be honest about the second test's strength.** Continuity separates cleanly
(0.09 against 1.00). Spokes separate `46-4` clearly at 6, but `156-3` only at
3–5 against a baseline of 2 — that one still needs the eye. **Flag, never
auto-cut**, as everywhere else in this step.

## `crops.txt` — WHAT WAS CUT, AND FROM WHERE

Every issue writes `issues/<ID>/crops.txt` at placement, one row per figure.
Owner, 2026-11-17, approving the format: *"cool format. crops.txt: commit it
too at the end"* — so it is **tracked, and it goes into the issue's squash
commit** with the articles.

```
# 8702 — crops.txt: every figure in this issue, as cut. Written at step 150.
#
#   file    the PNG in issues/8702/
#   type    resolution bucket (tools/convert-scans.sh):
#             bw   600 dpi bilevel        dots  600 dpi bilevel, screen removed
#             gray 150 dpi grayscale      c     150 dpi colour
#   origin  page and position of the cut in the 600 dpi master: NNN +X+Y
#   size    the cut, in 600 dpi pixels (c and gray ship at a quarter of this)
#   rot     de-skew WE applied to the page before cutting, degrees, + clockwise
#           a figure printed crooked on the plate keeps its tilt — by design
#
file        type  origin          size       rot
8-0.png     c     008 +736+784    1351x1121  +0.00
10-x1.png   c     010 +1779+1360  1536x1784  +0.00
22-1.png    dots  023 +253+510    4369x533   +0.00
148-5.png   c     148 +391+4875   2135x1529  +0.25
151-1.png   bw    151 +2555+3396  2034x2141  +0.00
```

Columns are space-aligned to the widest cell, with a two-space gap. The three
decisions inside it, each of which is a rule and not a layout preference:

- **`origin` is the page AND the position in the master**, so any crop can be
  re-cut exactly, audited against the plate, or re-derived after a re-level.
  A crop whose origin is not recorded cannot be checked against anything.
- **`rot` records only the skew WE corrected**, never the figure's own tilt.
  That is *we publish the plate* in a column: our scan error is fixed, the
  magazine's crooked paste-up stays crooked. Distinguishing the two is a
  measurement, not a judgement — see *THE FIGURES ARE AN INDEPENDENT WITNESS
  OF PAGE SKEW*.
- **`size` is the cut, not what ships.** `c` and `gray` go out at a quarter.
  Two sizes in one table invites reading the wrong one, so the delivered size
  is derivable from `type` and stated in the header rather than given a column.

**Write it at 150, not at cut time** — `type` is not known until the crop is
classified, and a column that is blank on the first pass is a column nobody
trusts. It lives beside the articles rather than in `<tmp>` for the same reason
`figure_captions.txt` does: `<tmp>` is swept and this is the only durable
record of where each figure came from.

## Alt text — describe only what is visible

- **No identity claims** unless caption explicitly names the
  person.
- **No age / role / job inference.** `Person`, `Mann`, `Frau`, or
  describe what they're doing.
- **No interpretation.** "Person mit Programmlisting in der Hand
  neben einem Drucker" beats "Autor präsentiert sein Werk".

## Briefing for the sub-agent

The sub-agent must:

1. **Do not render the issue PDF.** It does not exist yet -- it is built at
   the END, by step 006 (`r000`, *THE PAGE IMAGE IS `masters600`*). The page
   image is `<tmp>/masters600/NNN.png`, already 600 dpi, deskewed, cut and
   graded by step 005, and it is the same file r010 OCR'd and r145 cut these
   figures from. Read it directly; there is nothing to render up front.
2. Generate `issues/<YYMM>/images.txt` worklist from the loose PNGs:
   ```bash
   find . -maxdepth 1 -name "*.png" -not -name "title.png" \
     -exec basename {} \; | sort -V | \
     awk '{printf "<figure>\n    <img src=\"%s\" alt=\"\">\n    <figcaption>XXXXXXXXX</figcaption>\n</figure>\n", $0}' \
     > images.txt
   ```
   `sort -V` is required (handles `49-9, 49-9a, 49-10`).
3. For every entry: read the relevant scan page from `/tmp`, find the
   article whose `64er.pages` covers the image's major-page number,
   place the `<figure>` after the `</p>` of the paragraph that first
   references it (or — for `-0*` title images — right after the intro,
   `<figcaption>` removed). Captions verbatim from print.
4. Use `git mv` to rename images whose filename's major page doesn't
   match the article they actually belong to (e.g. an image printed
   on page 56 but tied to the article starting at page 49 →
   `git mv 56-1.png 49-3.png`).
5. Beautify every touched HTML file at the end:
   ```bash
   npx --yes js-beautify --type html --indent-size 4 \
     --wrap-line-length 0 --replace issues/<YYMM>/*.html
   ```
6. Delete `images.txt` when it's empty.
7. **Do not commit.** Return a per-article placement table:
   `File | Figures placed | Inline images | Notes` rows. Flag any
   `git mv` performed, any `<figcaption>` omitted (no caption on
   scan), any placement that was a judgment call, any caption hard
   to read at 150 dpi (request a 600 dpi crop if uncertain).

Tell the sub-agent explicitly:
- Image reads belong in further sub-sub-agents (anti-memory + vision
  budget). Main image scanning must not happen in the orchestrator.
- `<figcaption>` is omitted entirely when the print has no caption
  under the image — do not invent.
- `alt` describes only what's visible. No identity / role / age
  guesses.
- Inline portraits (author bio photo) get
  `<img class="inline" src="…" alt="…">` without `<figure>`.

## Verification

```bash
# The repo venv, not bare python3 (CLAUDE.md): the step modules import
# numpy, scipy and PIL, which the system python here does not have, so as
# `python3` this check failed at the import rather than checking anything.
PY=${PYTHON:-.venv/bin/python}
dir=issues/<YYMM>

# 1. every loose PNG (excluding title.png) is referenced by exactly
#    one <img src=…> across the article HTMLs
# `find`, NOT `ls "$dir"/*.png`.  The glob is expanded by the SHELL, and zsh
# -- which is what runs here -- aborts the line with "no matches found" when
# the issue has no PNG yet, so the check died instead of reporting 0 (8702).
# find prints nothing and exits 0 on an empty directory, in every shell.
loose=$(find "$dir" -maxdepth 1 -name '*.png' ! -name 'title.png' | wc -l | tr -d ' ')
# The class needs `_`: a single photo carrying two printed captions is cut as
# one file named for both (SH8601's 26-5_9.png, Bild 9 and Bild 6 of the same
# plug).  Without it the check reported 105 files against 104 references and
# looked like a lost image.
# COMPARE THE SETS, NOT THE COUNTS.  Two counts being equal says nothing: a
# dangling reference plus an unreferenced file cancel out, and so does one
# file referenced twice.  Both pass a count test and both were shown on plants.
comm -3 \
  <(find "$dir" -maxdepth 1 -name '*.png' ! -name 'title.png' \
      -exec basename {} \; | sort -u) \
  <(grep -hoE 'src="[0-9]+-[0-9a-z_]+\.png"' "$dir"/*.html \
      | sed 's/^src="//; s/"$//' | sort -u) \
  | sed 's/^\t/  referenced but no file: /; s/^\([^ ]\)/  file never referenced: \1/'
# and separately: no file referenced twice
grep -hoE 'src="[0-9]+-[0-9a-z_]+\.png"' "$dir"/*.html | sort | uniq -d \
  | sed 's/^/  referenced more than once: /'

# 2. no XXXXXXXXX placeholder left in any figcaption
grep -nE 'XXXXXXXXX' "$dir"/*.html && echo "  FAIL: placeholder caption survived"

# 3. images.txt is gone
[ ! -f "$dir/images.txt" ] && echo "  images.txt removed ✓" || \
  echo "  FAIL: $dir/images.txt still present"

# 4. each <img> has a non-empty alt (with the documented exception:
#    title images may have alt="" by design — they have no caption
#    and the title is the heading itself)
#
#    ESCAPE `<` AND `>` IN ALT TEXT.  An unescaped one passes this check --
#    it only looks for emptiness -- while breaking every downstream
#    `<img [^>]*>` regex, which stops at the wrong `>`.  MEASURED: the corpus
#    has 2, both `alt="Michael Scharfenberger, Chefredakteur<"` (8604/8 and
#    8606/8), so the second clause below exists to find them.
"$PY" -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    for m in re.finditer(r'<img [^>]*src="([^"]+)"[^>]*alt="([^"]*)"', s):
        src, alt = m.groups()
        if not alt:
            # tolerated: -0 / -00 title images
            base = os.path.splitext(os.path.basename(src))[0]
            mm = re.match(r'\d+-0[0-9a]*$', base)
            if not mm:
                print(f"  empty alt: {f}  {src}")
        if '<' in alt or '>' in alt:
            print(f"  UNESCAPED </> in alt: {f}  {src}  {alt!r}")
PY
)" "$dir"

# 5. <figure> nesting clean: every <figure> has a matching </figure>
"$PY" -c "$(cat <<'PY'
import os, re, sys
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.html'): continue
    s = open(os.path.join(d, f)).read()
    o = len(re.findall(r'<figure>', s)); c = len(re.findall(r'</figure>', s))
    if o != c: print(f"  mismatched figure tags in {f}: open={o} close={c}")
PY
)" "$dir"
```

All five checks should pass. The orchestrator should also spot-read
3-5 placed figures to confirm captions look like real print text
(not a placeholder, not paraphrased, not synthesised from body
references).

## Evidence-in-report requirement

A previous sub-agent on a different rule claimed verification it never
ran (the `internsiv` OCR regression). To make that failure mode
impossible here, every image placement and every `git mv` the
sub-agent applies must be backed by **runnable verifier evidence
pasted verbatim into the report**:

- For each `<figure>` placed, paste the body line containing the
  first text reference (`Bild N` / `Bilder N und M`) the placement
  was anchored to, e.g.
  ```
  133 Computer-Simulation.html → "…wie in Bild 4 dargestellt…"
  ```
  so the orchestrator can confirm the figure landed after that
  paragraph's `</p>`.
- For each `<figcaption>`, paste the sub-sub-agent's verbatim caption
  read from the scan (the exact words the vision agent returned), so
  the orchestrator can confirm no caption was paraphrased or invented.
- For each `git mv`, paste a one-line statement of which page the
  image was visually located on (`Read <tmp>/masters600/NNN.png`)
  and which article's column it sat in.
- For each unplaced image, paste the one-line reason logged to
  `LOG.md`.

**No verifier output, no claimed placement.** A figure or rename
reported without the body-anchor line / verbatim caption / page
location evidence is treated as un-applied; the orchestrator will
re-dispatch. "Trust me, I read the scan" is never acceptable.

## Notes / lessons

- The 92-image 8607 placement run renamed exactly two files
  (`56-1/2.png` → `49-3/4.png`); rename-then-place is much cheaper
  than the alternative (placing then realising mid-article you've
  picked the wrong article).
- Body-text "Bild N" references that match no file usually mean the
  print rendered the figure as a typeset text table (e.g. memory
  layouts under "Neues zum Thema Sortieren"), or refer back to a
  previous issue (correction notes). Don't fabricate an image — log
  and skip.
- Multiple files for one Bild (`-3a`, `-3b`, `-3c`) go in **one**
  `<figure>` with a single `<figcaption>`.
- Plural "Bilder 8 und 9" → two separate `<figure>` blocks after the
  same paragraph.
- Always delegate scan reads to sub-sub-agents — the main thread
  should never load page PNGs directly.

## Layout arrows in captions are typesetting pointers, not text

A caption that ends in `▶` / `►` / `◀` / `▲` / `▼` is pointing the reader at
artwork placed somewhere awkward on the page (`Bild 3. Der fünffach vergrößerte
Buchstabe »A« ►`). In the HTML the caption sits with its figure, so the arrow is
meaningless — strip it.

## Vorschau teasers: the image goes at the END of its section

The Vorschau is a run of `<h2>` teasers, some of which carry a picture. The
picture belongs **after that teaser's text**, immediately before the next `<h2>`
— not directly under the heading.

Measured across all 30 Vorschau pages in the corpus: 25 issues place every
figure after the text, 4 place them all under the heading (8409, 8412, 8502,
8607), and none mixes the two. So the convention is settled and the outliers
are old defects, not a variant style.

The failure mode to watch for is subtler than "wrong end": the OCR tends to emit
the figure just BEFORE its heading, which makes it read as the tail of the
*previous* teaser. 8609 had the acoustic-coupler photo trailing "C 64 — die
Musikmaschine" when it belongs to "DFÜ für Sie", and the Beverly Hills (Axel F)
still trailing Vizawrite when it belongs to "Hardcopies in Farbe und ganz
klein". Match each picture to its teaser by subject, then place it at the foot
of that section.
