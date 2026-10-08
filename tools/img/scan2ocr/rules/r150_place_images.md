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
yet — the work list for after the owner cuts them) or `TRUNCATED`.

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

### A crop that covers SEVERAL Bild numbers is ONE figure

A single cut frame holding more than one numbered Bild is named for all of
them — `10-6abc.png`, and SH8601's `26-5_9.png` — and it becomes **one
`<figure>`, at the FIRST member's printed position, with each printed caption
on its own line** (`<br>`-separated inside the one `<figcaption>`). Not one
figure per number: there is one image.

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

**BUT THIS RULE GOVERNS THE WORKLIST, NOT THE DELIVERY. A CROP THAT ARRIVES IS
PLACED.** Owner, 2026-10-07: *"if they are delivered, they are not dropped. i
am deliberate about what goes into crops."* The owner does not cut cartoons, so
a worklist row for one normally comes back undelivered — and that silence is
the answer, not an omission to chase. But if a crop IS in the delivery, the
decision has already been made and it is not ours to revisit: place it.

This is the same principle as *owner crop wins* elsewhere in the chain. Judging
a delivered PNG against this section and holding it back inverts who decides.
MEASURED on SH8605: `6-00` and `6-000`, the p8 bit and byte cartoons, were
delivered; they were set aside as cartoons and had to be put back. **The test
in this section tells you what not to ASK for. It never tells you to refuse
what you were given.**

(The NAME of a delivered crop is a different matter and may well be wrong —
see *renaming is authorised* above. Rename it and place it; do not drop it.)

## A listing full of unreadable glyphs is cut WHOLE, not glyph by glyph

When a listing carries reverse or graphic PETSCII that cannot be named from the
scan, do **not** propose one crop per glyph, and never ship `[ILLEGIBLE]`.
**Crop the whole listing as one image**, and owner-crop-wins then replaces the
transcription.

MEASURED on SH8602: the worklist proposed 39 individual glyph crops; the owner
cut five whole listings instead (article 20's Listings 6-9 and article 39's
Listing 1), covering 32 of them, with the remaining seven in boxed one-liners
cut as their boxes. Five images rather than 32, and the listing reads as
printed. Propose that shape FIRST.

**And a table printed across two pages is ONE crop.** The worklist asked for
`20-t2a` + `20-t2b` because the chart runs from one column onto the next page;
the owner cut it whole and it places once. The unit is the TABLE, not the page.

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
dir=issues/<YYMM>

# 1. every loose PNG (excluding title.png) is referenced by exactly
#    one <img src=…> across the article HTMLs
loose=$(ls "$dir"/*.png | grep -v '/title\.png$' | wc -l | tr -d ' ')
# The class needs `_`: a single photo carrying two printed captions is cut as
# one file named for both (SH8601's 26-5_9.png, Bild 9 and Bild 6 of the same
# plug).  Without it the check reported 105 files against 104 references and
# looked like a lost image.
# COMPARE THE SETS, NOT THE COUNTS.  Two counts being equal says nothing: a
# dangling reference plus an unreferenced file cancel out, and so does one
# file referenced twice.  Both pass a count test and both were shown on plants.
comm -3 \
  <(ls "$dir"/*.png | xargs -n1 basename | grep -v '^title\.png$' | sort -u) \
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
python3 -c "$(cat <<'PY'
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
python3 -c "$(cat <<'PY'
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
