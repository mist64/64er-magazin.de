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
