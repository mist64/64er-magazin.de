# 12 — Place image figures into article HTML

**Goal:** turn every loose `<page>-<n><suffix>.png` (and `title.png` if
unhandled elsewhere) in the issue directory into a `<figure>` or
`<img class="inline">` inside the article it belongs to. Captions are
verbatim from the print scan; alt text is a short German visual
description.

## Mapping images to articles

Image filenames follow `<startpage>-<figurenum><suffix>.png`, e.g.
`145-9a.png`. The **major number** (before the first `-`) is the
**start page of the article** the image belongs to.

1. Extract major number from filename: `145-9a.png` → `145`.
2. Find the article whose `<meta name="64er.pages" content="…">`
   starts with that page, e.g. `content="145-153"`.
3. Disambiguate collisions: when two articles share a start page,
   Read the relevant pages from `/tmp/64er_<YYMM>_pages/` to see which
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

## Alt text — describe only what is visible

- **No identity claims** unless caption explicitly names the
  person.
- **No age / role / job inference.** `Person`, `Mann`, `Frau`, or
  describe what they're doing.
- **No interpretation.** "Person mit Programmlisting in der Hand
  neben einem Drucker" beats "Autor präsentiert sein Werk".

## Briefing for the sub-agent

The sub-agent must:

1. Render the issue PDF to `/tmp/64er_<YYMM>_pages/` at `-r 150` (once, up
   front).
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
refs=$(grep -hoE 'src="[0-9]+-[0-9a-z]+\.png"' "$dir"/*.html | sort -u | wc -l | tr -d ' ')
[ "$loose" = "$refs" ] || echo "  FAIL: $loose loose PNGs vs $refs unique src refs"

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
