# Body Text Extraction Workflow

How to extract the main text flow of every article from a 1980s "64'er" magazine issue as plain HTML (`<h1>`, `<h2>`, `<p class="intro">`, `<p>`). **Body text only** — no figures, tables, listings, page headers, page footers, metadata, or author lines. Those are bolted on by other workflows (`img_workflow.md`, `table_workflow.md`, `prg_workflow.md`, `toc_title_workflow.md`, `index_workflow.md`).

## How to run

Point the agent at this file and provide three parameters:

```
Extract body text for issue YYMM per tools/llm/new/body_workflow.md.
Scans: <path to NNN_600_cropped.png files>
Pages: 1..NNN
Output: issues/YYMM/_work/
```

**Inputs required:**
- **Page scans**: 600 DPI cropped master PNGs, one per magazine page. Filename pattern: `NNN_600_cropped.png` (NNN = zero-padded page number).
- **Page count**: total number of pages in the issue.
- **Output directory**: `issues/YYMM/_work/`. The agent creates it, with `pNNN/` subdirectories per page and `articles/` for stitched output.

**Final deliverable:** one file per article at `_work/articles/article_NNN.html` (NNN = start page). Each file contains `<h1>`, `<h2>`, `<aside>`, `<p>`, `<p class="intro">`, `<p class="source">`, and optional `<p class="noindent">` / inline `<strong>`, `<em>`, `<sub>`, `<sup>`. No `<html>` wrapper, no metadata, no article shell — body text fragment only.

**Forbidden inputs:**
- `issues/YYMM/YYMM.md` or any pre-existing transcription file — never read it.
- Any `_work*/` directories from prior extraction runs — must not influence this run.

**Execution:** proceed without asking for confirmation. Parallelize aggressively — spawn sub-agents for Phase 1 (batches of 10-15 pages) and Phase 3 (one per body page). Phase 2 is tesseract (script). Phases 4-5 are `cat` + `Edit`.

**Expect:** ~50-60% of pages are body pages. ~30-50 articles per issue. Multi-hour job.

**Pay special attention to:**
- The h1 vs h2 distinction (CRITICAL RULE #1 below). A prominent heading on a continuation page is almost always an h2, not a new article. Check whether body text precedes it on the same page.
- Never correcting typos or adding punctuation (CRITICAL RULE #2). The scan wins, your expectations lose.
- Mixed pages (~10% of body pages). After classifying all pages, verify that no article ends mid-sentence without a continuation.

**Report at the end with:**
- Count and list of articles (start page + title).
- Any `[OCR-GAP]` markers.
- Any mixed pages, graphic titles, Texteinschübe, or jump pointers ("Fortsetzung auf Seite N").
- No text excerpts — structural report only.

## CRITICAL RULES (read before anything else)

**1. NEVER promote an h2 section heading to h1 (new article).** An article is a single continuous editorial piece that starts with a title, runs across 1-10 pages, and ends with a byline or clean section break. Within that article, section headings (`<h2>`) divide the text into sub-topics. These h2 headings can be just as large and prominent as article titles — **do not mistake them for article starts.** If body text from the current article appears ABOVE a heading on the same page, that heading is an h2, not an h1. See "Distinguishing h1 from h2" below.

**2. NEVER correct typos or add missing punctuation.** The printed magazine text is historical record. If the OCR says `Benutzeroberfäche` (missing L) and the pixels show the same, emit `Benutzeroberfäche`. If a sentence ends without a period and the pixels show no period, emit no period. Do not let your language model training "fix" what looks wrong. See "OCR fixes CHARACTER-LEVEL ONLY" in Phase 3.

**3. Every character originates in OCR TSV or bounded pixel reads.** No composition, no paraphrasing, no inference from context. See "Anti-memory rule" in every phase section.

## Goal

For every editorial article in the issue, produce a per-article HTML fragment containing only:

```html
<h1>Article title</h1>
<p class="intro">Lead paragraph...</p>
<p>Body paragraph...</p>
<h2>Section heading</h2>
<p>More body paragraph...</p>
```

Article boundaries are **derived** from per-page vision classification. No TOC, no CSV, no running-header clustering. A page is either an article start (has a title), a continuation, an ad, or a rubric page.

## Why a three-engine hybrid

Three tools, each used where it shines:

| Concern | Tool | Why |
|---|---|---|
| **Layout detection + reading order** | **PPStructureV3** (PaddleOCR) | Detects text blocks, images, headers, footers, captions, section titles. Assigns `order_index` for correct column reading order. Solves the #1 Tesseract failure (column jumbling). |
| **Word-level OCR + bboxes** | **Tesseract** | Word-level TSV with `(block, par, line, word)` hierarchy. German `deu` model handles old spelling (daß, muß). hOCR gives font-class info. Phase 3.5 verification needs word-level granularity. |
| **Stylized titles + inline formatting + OCR correction** | **Vision agent** | Graphic titles invisible to both OCR engines. Bold/italic detection. Pixel-level correction of OCR errors. Drop-cap recovery. |

### What PPStructureV3 provides that replaces vision-agent work

PPStructureV3 (`from paddleocr import PPStructureV3`) runs layout detection + OCR per block and returns:

```python
s = PPStructureV3(lang="german")
for result in s.predict(page_image):
    for block in result["parsing_res_list"]:
        block.order_index   # reading order (int, or None for non-text)
        block.label         # "text", "paragraph_title", "image", "figure_title",
                            # "header", "footer", "number"
        block.bbox          # [x1, y1, x2, y2]
        block.content       # OCR text for this block
```

**Calibration on issue 8606 p023** (4-column page with screenshots):
- 14 text blocks with correct column reading order (col1→col2→col3→col4)
- `paragraph_title` label correctly identified "Zwei Programme gratis" (h2)
- Images, captions, headers, footers labeled and separated
- `Benutzeroberfäche` preserved (typo in original)
- `daß`, `muß` handled correctly

This mechanically replaces:
- **Phase 1 page classification** — `header`/`footer`/`image`/`text` labels + presence of `paragraph_title` blocks distinguish article_start from continuation
- **Phase 3 column reconstruction** — `order_index` gives correct reading order
- **Phase 3 h2 detection** — `paragraph_title` label
- **Phase 3 non-body filtering** — `image`/`figure_title`/`header`/`footer`/`number` labels

**PPStructureV3 does NOT replace:**
- **Stylized/graphic title reading** — still needs vision agent for image-rendered titles
- **Word-level OCR** — PPStructureV3 gives block-level text, not word-level bboxes. Tesseract still needed for Phase 3.5 word-diff verification.
- **Inline formatting** (`<strong>`, `<em>`) — still needs vision agent
- **OCR error correction** — still needs vision agent for character-level fixes

### Dependencies

**System (macOS):**
```bash
brew install tesseract tesseract-lang   # Tesseract 5.x with German language pack
brew install imagemagick                # For PNG cropping and resizing
```

**Python (PPStructureV3 / PaddleOCR):**

PaddlePaddle does not yet support Python 3.13+. Use a 3.10-3.12 venv:

```bash
python3.12 -m venv .venv-paddle
source .venv-paddle/bin/activate
pip install paddleocr paddlepaddle
```

Verify installation:
```bash
python3.12 -c "from paddleocr import PPStructureV3; print('OK')"
```

PPStructureV3 downloads ~500MB of models on first run (cached in `~/.paddlex/`). Subsequent runs use cached models. First invocation takes ~30 seconds; subsequent pages ~5-10 seconds each.

**Note on the `predict` API:** PaddleOCR 3.5+ uses `s.predict(path)` not the older `s.ocr(path)`. The old API is deprecated. Also use `PPStructureV3` (not plain `PaddleOCR`) — the plain class does not do layout detection or reading-order assignment.

## Pipeline

```
Phase 0  script (PPStructureV3)  per page  →  layout.json  (blocks + reading order + labels)
Phase 1  agent (vision)          per page  →  page_meta.txt (kind, title bbox, intro bbox)
Phase 2  script (tesseract)      per block →  block_NNN.tsv (word-level OCR within each text block)
Phase 3  agent (vision+text)     per page  →  page_NNN.html (h1 + intro + body)
Phase 3.5 script                            →  verify_flags.txt (TSV word diff)
Phase 4  script                             →  article_NNN.html (cat)
Phase 5  script                             →  cross-page dehyphenation + paragraph merges
```

Phase 0 is new (PPStructureV3 layout detection). Phase 2 now runs Tesseract per PPStructure block (not per page), which avoids the column-jumbling problem entirely. Phases 1, 3, 4, 5 are similar but simpler because layout is already solved.

## Phase 0 — Layout detection (PPStructureV3, script)

For every page:

```python
from paddleocr import PPStructureV3
import json

s = PPStructureV3(lang="german")

for result in s.predict(page_300_path):
    blocks = []
    for b in result["parsing_res_list"]:
        blocks.append({
            "order": b.order_index,
            "label": b.label,
            "bbox": [int(x) for x in b.bbox],
            "content": b.content  # PPStructure's own OCR (backup, not primary)
        })
    with open(layout_json_path, "w") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)
```

Output: `_work/pPPP/layout.json` per page.

### What Phase 0 gives downstream phases

- **Phase 1** reads `layout.json` to classify the page: presence of `paragraph_title` blocks = `article_start`; only `text` blocks = `continuation`; only `image`/`header` = `ad` or `rubric`. Phase 1 vision agent still needed for graphic titles and intro detection, but layout.json handles 80% of classification mechanically.

- **Phase 2** iterates over `layout.json` blocks with `label == "text"` or `label == "paragraph_title"`. For each block, crops the bbox from the 600 DPI source and runs Tesseract with `--psm 6` (single block mode). This eliminates Tesseract's column-jumbling entirely — each block is a single-column region. Output: `_work/pPPP/block_NN.tsv` per text block.

- **Phase 3** uses `order_index` for reading order instead of reconstructing columns from bbox coordinates. Uses `paragraph_title` labels for h2 detection instead of `x_fsize` heuristics. Vision agent focuses on what it's good at: inline formatting, OCR correction, graphic titles.

### PPStructure's OCR vs Tesseract — use both

PPStructureV3 runs its own OCR internally (stored in `block.content`). This is **backup text**, not the primary source. Tesseract remains primary because:
1. Word-level bboxes (Phase 3.5 verification needs them)
2. Better German old-spelling model
3. Deterministic output for diffing

But PPStructure's `block.content` serves as a **second opinion**: if Tesseract and PPStructure agree on a word, high confidence. If they disagree, flag for Phase 3 vision verification. This mechanically catches the `Benutzeroberfäche` dispute — if both engines say `oberfäche`, it's the print; if one says `oberfläche`, flag it.

## Phase 1 — Vision overview (one sub-agent per page)

Input: a 1400px-wide thumbnail of the page (`page_small.png`).

Task: classify the page and describe structure. **Phase 1 does NOT transcribe title or intro text.** It returns only structural metadata plus bbox / block-reference hints. Text extraction happens in Phase 3, always from TSV first, with vision fallback only for blocks where TSV captured nothing (stylized graphic titles, image overlays). This eliminates Phase 1 transcription drift entirely — the agent never types title/intro words, so it can't paraphrase, drop, or mis-read them.

Output: `page_meta.txt` per page.

For `article_start`:

```
kind: article_start
titles:
  - source: ocr          # title text is in TSV — Phase 3 reads from there
    bbox: 213,1222,663,1333   # approximate title region in 300-DPI coords (for Phase 3 to locate the right block)
  - source: graphic      # OR: title is a stylized / image-rendered graphic
    bbox: 0,0,2468,1844       # region for Phase 3 to vision-read
intro:
  present: true
  bbox: 679,2265,1743,2504     # approximate intro region; Phase 3 extracts text from the TSV blocks inside it
```

Or `present: false` if no distinct intro paragraph.

For a page with multiple titles (mixed article boundaries), return the `titles:` list with one entry per title, in top-to-bottom reading order.

Other kinds:

```
kind: continuation
```

```
kind: ad
```

```
kind: rubric
name: Leserforum
```

```
kind: other
note: table of contents
```

```
kind: mixed
# mixed pages MUST still be listed, with all titles + their regions
titles:
  - source: ocr
    bbox: 213,1222,663,1333
  - source: ocr
    bbox: 1306,1623,2305,1703
intro:
  present: false
```

### Distinguishing h1 (article start) from h2 (section heading)

This is the single most common classification mistake. A prominent heading on a continuation page can look like an article title but is actually a section heading within the running article. **Getting this wrong fragments articles and produces wrong output.**

A heading is an **h1 (new article)** when ALL of these are true:
- It is the **first editorial content** on the page (below the running header strip). No body text from any article precedes it in reading order.
- OR: it appears below a clear horizontal rule or visual separator that ended the previous article (including byline, address block, empty space).
- The **running header** (rubric name at top of page) is different from the previous page — indicating a new rubric section.
- It has a **decorative opener**: drop-cap, hero image, bold intro paragraph, or stylized typography.

A heading is an **h2 (section heading)** when ANY of these are true:
- **Body text from the same article appears ABOVE it** on the same page. (This is the strongest signal. Body → heading = the heading is inside the article, not starting a new one.)
- The **running header** is the same as the previous page (same rubric).
- The heading is followed by body text that continues the same topic as the preceding paragraphs.
- There is **no intro paragraph** after it — the next text is ordinary body.
- There is **no byline or address block** between the preceding text and the heading (a byline signals article end; its absence means the article continues).

**Calibration examples from issue 8606:**
- p21 "Kein Gerät für Bastler", "Ganz der Alte", "Das neue Betriebssystem: »Geos«" — all h2s inside Der Neue article. Body text above each, same running header "Hardware-Test / C 64".
- p41 "Vorsicht bei Aspirin und Schweinebraten" — h2 inside Datenbanken article. Body text above it, same running header "Daten verwalten".
- p43 "Geos — ein Meisterwerk" — h2 inside Der Neue article (continuation from p24 via jump). Body text above it, same running header "Hardware-Test / C 64".

**Wrong classification from v2 and v4 runs:** These h2s were promoted to h1 and given their own article files (v2: 49 articles instead of ~42; v4: same). Result: multi-page articles fragmented into 2-3 pieces. The fix: always check whether body text precedes the heading on the same page before classifying as article_start.

### Post-Phase-1 sanity check on article count

After classifying all pages, count the `article_start` pages. A typical 64'er issue has **30-45 articles** (including short news items). If your count exceeds 45, you are almost certainly over-splitting — h2 section headings are being misclassified as article starts.

**Verification procedure:** for every `article_start` page, confirm that:
1. No body text from a prior article appears above the title on that page, OR
2. A byline / address block / horizontal rule clearly ends the prior article before the title.

If neither condition holds, reclassify as `continuation` and demote the heading to h2.

### Why no title/intro transcription in Phase 1

Calibration findings across issue 8606:

- **p70**: Phase 1 said `Software-Anpassung`, TSV + pixels said `Software-Ansteuerung` — Phase 1 misread the thumbnail.
- **p92**: Phase 1 intro had 5 paraphrased words that disagreed with TSV (paraphrased `zur Nachschlagewerk` for `als Nachschlagewerk`, etc).
- **p140**: Phase 1 intro said `Daher haben Sie…`, TSV + pixels said `Bisher haben Sie…`.
- **p161**: Phase 1 intro was garbled beyond character-level fix; Phase 3 agent rebuilt from TSV.

In every case, the title / intro was plain printed text fully present in the tesseract TSV — Phase 1 just transcribed it wrong because thumbnails lose pixel fidelity. The text was always in the OCR. **If Phase 1 never transcribes, it cannot drift.** Phase 3 gets the real text from the TSV block at the bbox Phase 1 pointed to.

For genuinely graphic titles (like `Der Neue` on p19, rendered as stylized type overlaid on a photo), Phase 1 marks `source: graphic` and Phase 3 crops the title region and reads the pixels directly — still a small, bounded vision operation, but zero chance of intro-length paraphrasing drift.

### Mandatory Phase 3 override

Even when Phase 1 says `source: ocr`, Phase 3 MUST re-derive the title and intro from the TSV block(s) in the bbox, not trust any hint text from Phase 1. If Phase 1 accidentally includes a text hint (e.g. a comment describing the title in a report), Phase 3 must ignore it.

The rule: **only two kinds of text ever come from vision transcription:**
1. Graphic titles (bounded: a few words, verified against the picture)
2. Drop caps that tesseract's word-level rows missed (bounded: one letter, verified against the pixels)

Everything else in the output originates in a tesseract TSV row.

### Page kinds

| Kind | What it is | Downstream handling |
|---|---|---|
| `article_start` | Page opens a new article. Has a visible title in the body area. | Phase 2 + Phase 3 run normally. Title + intro bboxes come from Phase 1; actual text derived in Phase 3 from TSV/pixels. |
| `continuation` | Page carries body text of an article that started earlier. No title. | Phase 2 + Phase 3 extract body only. |
| `ad` | Full-page advertisement. Commercial typography, product name, price, no editorial header. | Skip Phase 2 + Phase 3. Emit stub. |
| `rubric` | Editorial rubric with internal structure unlike regular articles (Leserforum, Editorial, Impressum, TOC, Vorschau, Fehlerteufelchen). | Out of scope for this workflow. Skip or handle manually. |
| `other` | Cover, masthead, back cover, unclassifiable. | Skip. |

### Mixed pages

If a page contains end-of-one-article plus start-of-another (~10% of body pages — common, not rare), report `kind: mixed` with `titles:` containing all title bboxes. Phase 3 splits the body blocks spatially at each title position.

Mixed pages can be:
- **Horizontal split**: old article ends at top, horizontal rule, new article below.
- **Vertical split**: old article in left column(s), new article in right column(s).
- **Buried start**: new article starts in a small column below a listing page, easy to miss if only looking for hero-image titles.

### Mixed pages that look like continuation-only

Some mixed pages don't have a prominent new-article title. The new article may start in a small column below a BASIC listing, or the page may carry a "Texteinschub" sidebar alongside the main article. Phase 1 can miss these if it only looks for big titles.

**Verification step:** after Phase 1 is complete for the whole issue, scan for articles that end mid-sentence on one page with no continuation on the next page. If the next page is classified `ad`, `rubric`, or `other`, the article probably jumps (check for "Fortsetzung auf Seite N"). If the next page is `article_start`, check whether the old article's tail exists in a different column/position on that same page (the mixed-page case).

**Pages commonly missed in testing:** p70 (small single-column article below a listing page), p148 (Texteinschübe alongside a multi-page reference article). Both have editorial body text that Phase 1 can miss if it only scans for hero-image titles.

### Intro detection rules

The intro is the lead / teaser paragraph that sits visually distinct from body, typically **bold**, often **wider measure** or spanning multiple body columns. It comes right after (or sometimes above) the title.

- If no distinct lead paragraph exists, emit `intro: present: false`.
- Do not promote the first body paragraph to intro unless it is visually distinguished.
- When uncertain, omit — a false `intro` bbox pulls ordinary body text into a `<p class="intro">` and pollutes the article layout.
- Phase 1 returns ONLY the bbox, not the text. Text comes from Phase 3 reading the TSV blocks inside that bbox.

### Anti-memory rule (Phase 1)

Phase 1 emits no transcribed text for title or intro — only `source: ocr|graphic` and the bbox. This structurally prevents transcription drift. The only text Phase 1 may emit is short structural labels that don't appear in the output HTML:

- `name: Leserforum` (rubric identifier, used only to flag the page as rubric)
- `note: table of contents` (free-form debug note)

Neither of these leaks into article HTML, so even a misread rubric name or note description has zero effect on final output.

## Phase 2 — Tesseract per-block OCR (script)

For every page where Phase 0 produced text blocks in `layout.json`:

```bash
# For each text/paragraph_title block in layout.json:
# 1. Crop the block region from the 600 DPI source (bbox ×2 for 600 DPI coords)
magick <source>/PPP_600_cropped.png +repage -crop WxH+X+Y +repage _work/pPPP/block_NN.png

# 2. Run Tesseract in single-block mode on the crop
tesseract _work/pPPP/block_NN.png _work/pPPP/block_NN -l deu --psm 6 -c hocr_font_info=1 tsv hocr
```

**Key change from the original per-page approach:** Tesseract now runs with `--psm 6` (single uniform block) on each PPStructure block crop, not `--psm 1` (auto page segmentation) on the full page. This eliminates the column-jumbling problem entirely — each crop is a single-column region, so Tesseract can't get the reading order wrong.

Also run Tesseract once on the full page with `--psm 1` to get `page.tsv` as a backup for Phase 3.5 verification:

```bash
magick <source>/PPP_600_cropped.png -resize 50% _work/pPPP/page_300.png
tesseract _work/pPPP/page_300.png _work/pPPP/page -l deu --psm 1 -c hocr_font_info=1 tsv hocr
```

Outputs per page:
- `_work/pPPP/layout.json` — from Phase 0
- `_work/pPPP/block_NN.png` + `block_NN.tsv` + `block_NN.hocr` — per text block
- `_work/pPPP/page_300.png` + `page.tsv` + `page.hocr` — full-page backup

### Why 600 → 300 DPI

Tesseract's LSTM is trained around 300 DPI. Native 600 DPI triggers a Turkish-dotless-`ı` artifact and degrades accuracy. A clean 2:1 `magick -resize 50%` downscales without interpolation artifacts. Never upscale, never sharpen, never threshold — all make results worse.

### Block geometry summary (optional, for Phase 3 debug)

Produce a `blocks.txt` per page with bbox and first 120 chars of each block — useful for phase-3 agents that need a quick index of what's where:

```bash
awk -F'\t' 'NR>1 && $1==5 && $12!="" {
  b=$3;
  if (!(b in minL) || $7<minL[b]) minL[b]=$7;
  if (!(b in minT) || $8<minT[b]) minT[b]=$8;
  if (!(b in maxR) || $7+$9>maxR[b]) maxR[b]=$7+$9;
  if (!(b in maxB) || $8+$10>maxB[b]) maxB[b]=$8+$10;
  text[b]=text[b]" "$12; n[b]++;
}
END {
  for (b in text) printf "block=%02d bbox=%dx%d+%d+%d nw=%d %s\n",
    b, maxR[b]-minL[b], maxB[b]-minT[b], minL[b], minT[b], n[b], substr(text[b],1,120)
}' _work/pPPP/page.tsv | LC_ALL=C sort > _work/pPPP/blocks.txt
```

### Environment notes

- **`LC_ALL=C` on all sort/awk commands.** German text with umlauts causes `Illegal byte sequence` errors on macOS without it. Use `LC_ALL=C sort` and `LC_ALL=C awk` everywhere. Silent data loss otherwise — blocks.txt comes out empty.
- **Scratch location:** all intermediates live in `issues/NNNN/_work/pPPP/` — **not** `/tmp/`. Tesseract sandboxing on macOS can't read `/tmp/` reliably.
- **ImageMagick on macOS Homebrew has no Freetype.** Do not try to draw text labels on overview images with `-font Helvetica` — it silently fails. Use block numbers from blocks.txt instead.

### Quick listing-page detection

~15% of pages are pure hex dumps or BASIC listings with zero body prose. Detect them early to skip Phase 3:

```bash
# After Phase 2, check if >80% of words are hex/numeric/BASIC keywords
total=$(awk -F'\t' '$1==5 && $12!=""' _work/pPPP/page.tsv | wc -l)
hexlike=$(awk -F'\t' '$1==5 && $12!="" && $12 ~ /^[0-9a-fA-F.:;$+\-*\/()]+$/' _work/pPPP/page.tsv | wc -l)
ratio=$((hexlike * 100 / total))
# If ratio > 80, it's a listing page — emit stub and skip Phase 3
```

Also check blocks.txt: if the largest block has >500 words and text preview starts with hex addresses (`a730 : Ze 85 fe`) or BASIC line numbers (`10 REM`, `100 DATA`), it's a listing page.

### News roundup pages (Aktuelles, Neue Produkte)

Some pages contain multiple short news items under a rubric header like "Aktuelles" or "Neue Produkte". Each item has its own bold sub-heading and sometimes its own byline. These are NOT separate articles — they are **one article** (the news roundup) with many `<h2>` sections. Treat the rubric page header as the `<h1>` and each news item heading as `<h2>`.

Exception: if an item spans multiple pages and has its own intro paragraph + decorative opener, it may be a standalone article that happens to sit in the Aktuelles section. Use the h1/h2 distinction rules above.

### Continuation across ad breaks without "Fortsetzung"

Some articles span non-contiguous pages with ads in between but NO explicit "Fortsetzung auf Seite N" marker. Detection:
- Article page N ends without terminal punctuation.
- Page N+1 is an ad.
- Page N+2 has the same running header as page N and starts with a lowercase continuation or `<p class="noindent">`.

In this case, page N+2 is a continuation of the article from page N, not a new article. The ad simply interrupts.

### Orchestration guidance

**Phase 1 batching:** 10-15 pages per sub-agent call. Each reads thumbnails and writes page_meta.txt. ~12 batched calls cover 184 pages. Run them in parallel (up to 8 concurrent to avoid rate limits).

**Phase 2:** run tesseract on all body pages. Use parallel Bash calls (up to 20 per message) or a single background script. ~90 pages × ~5 seconds = ~8 minutes serial, ~1 minute with 10-way parallelism.

**Phase 3:** one sub-agent per body page, up to 8 concurrent. Each takes 2-5 minutes. ~90 pages / 8 = ~12 waves = ~30-60 minutes wall clock. This is the bottleneck.

**Phase 3.5:** script, runs in seconds. No agents needed.

**Phase 4+5:** main thread, ~1 minute per article for cat + Edit. ~40 articles = ~40 minutes.

## Phase 3 — Reconciler agent (one per non-skip page)

Input:
- `page_meta.txt` from Phase 1 (kind + bbox hints for title / intro — NO transcribed text)
- `page.tsv` + `blocks.txt` from Phase 2 (OCR blocks + bboxes)
- `page_small.png` (1400px thumbnail for spatial context)
- Per-block crops if needed (Phase 3 can generate them on demand from bbox data)

Task:

0. **Derive title and intro from TSV** (for `article_start` / `mixed` pages):

   - For each `title` entry in page_meta with `source: ocr`: find the OCR block(s) inside the bbox, concatenate their text, and emit as `<h1>…</h1>`. This text comes from TSV — zero transcription drift possible.
   - For each `title` entry with `source: graphic`: crop the bbox from the full-res page image, spawn a vision sub-agent that reads ONLY the title text (few words, bounded operation), and emit as `<h1>…</h1>`. Log the pixel-read in the report so downstream auditing knows the title was vision-derived.
   - For `intro: present: true`: find the OCR block(s) inside the intro bbox and emit as `<p class="intro">…</p>`. Again, TSV is authoritative.
   - For `intro: present: false`: emit no intro.

   Do NOT trust any hint text that might appear in page_meta — always re-derive from TSV. If Phase 1 accidentally included a title string, ignore it.

1. **Drop non-body blocks** mechanically:
   - Blocks inside the title bbox(es) → already emitted as `<h1>`, drop from body.
   - Blocks inside the intro bbox → already emitted as `<p class="intro">`, drop from body.
   - Block text matches `^Bild [0-9]+[a-z]?\.` or `^Tabelle [0-9]+` or `^Listing [0-9]+` → drop (figure/table/listing caption).
   - Block text matches `^Ausgabe [0-9]+/.*19[0-9]+$` → drop (page footer).
   - Block is in the top ~5% of the page height and has fewer than 5 words → drop (running header).
   - Block has ≥80% empty area (bbox minus text bbox) → drop (image).
   - Block has fewer than 3 words AND sits isolated → drop (decorative rule, page number, stray mark).

2. **Detect section headings (`<h2>`).** Two mechanisms:

   **(a) Standalone heading blocks.** Tesseract's hOCR assigns a font-class index (`x_fsize`) to each word. Body text clusters around one dominant value (e.g. `x_fsize 4`). Blocks where all words share a *different* `x_fsize` AND the block is short (< 10 words) are section headings. Emit as `<h2>`.

   Example from p020: block 10 "Der kleine Bruder des C 128" has `x_fsize 7`, body has `x_fsize 4`. Standalone block, 6 words → `<h2>`.

   **(b) Inline bold headings inside body blocks.** Tesseract sometimes puts a short bold heading in its own `<p>` (paragraph) within a body block, followed by the body paragraph. The heading has the same `x_fsize` as body (tesseract can't see bold weight), but it is visually distinct on the page image: short (1-3 words), no punctuation, bold or heavier weight, separated by whitespace from the body below.

   Example from p020: "Sprachregelung" is `par_1_2` inside block 6, followed by `par_1_3` body text. Same `x_fsize 4` — only detectable by visual inspection. Split it off as `<h2>Sprachregelung</h2>` and emit the following paragraph as `<p>`.

   When uncertain whether a short paragraph is a heading or a fragment, prefer `<p>` (less destructive). Log the ambiguity in `LOG.md`.

3. **Add inline formatting** by comparing the OCR scaffold to the block pixels. The vision agent marks up:
   - `<strong>` — bold runs (heavier weight than surrounding body text)
   - `<em>` — italic runs
   - `<sub>` / `<sup>` — subscript / superscript (rare, mostly in technical articles)

   Do NOT use tesseract's `x_fsize` for this — it's unreliable (font-class buckets split inconsistently). Vision is the authority on inline formatting.

   `<strong>` wraps only phrase-level or word-level bold runs inside body paragraphs. Contiguous bold words = one `<strong>` span, not one per word.

   **Do NOT wrap `<p class="intro">` content in `<strong>`.** The intro class already styles its content as bolder via CSS. Adding a nested `<strong>` is a double-bold. Intro paragraphs get their text plain inside the `<p class="intro">...</p>` tags — no inner formatting tag for the intro-level bold.

   When uncertain whether text is bold or just slightly heavier due to scan quality, omit the tag. False positives are worse than missed formatting.

4. **Correct OCR errors** against the pixels. **Character-level only.** Never change, add, remove, or substitute words. Never "fix" grammar, spelling, punctuation, or style. The only valid OCR fixes are single-character substitutions (`1/l/I`, `O/0`, `rn/m`, `cl/d`, `ı→i`), missing or extra whitespace between words (`dasalle` → `das alle`), missing/mangled accent marks or umlauts (`Anderungen` → `Änderungen`), and drop caps or leading characters the OCR dropped at paragraph starts. Every fix must be verifiable by looking at the exact pixel region for that word.

   **Forbidden "corrections":**
   - Adding a word the OCR missed that you think should grammatically be there (e.g. `behoben sein` → `behoben worden sein`). **Every word in the OCR is treated as correct unless the pixels show something else in its place.** If a sentence looks grammatically odd, that is how it was printed.
   - Re-introducing a noun that appears to have been elided (e.g. `so kann diese jederzeit` → `so kann diese Diskette jederzeit`). If tesseract captured "diese" and the pixels show "diese", leave "diese". Do not infer omitted nouns from context.
   - Modernizing spelling (`daß` → `dass`, `muß` → `muss`, `ß` → `ss`). Old German 1901-1996 spelling is preserved exactly.
   - Fixing grammatical errors or typos in the printed original. The magazine's own mistakes are historical record — preserve them.
   - Replacing "slightly wrong-looking" words with "more correct" ones based on context.
   - Rewording awkward sentences.

   **Rule of thumb:** if the change touches more than one character, or crosses a word boundary beyond whitespace, stop and verify the exact pixels for that word. If you are not sure the pixels show what you want to write, leave the OCR scaffold unchanged. Under-correction is safe; over-correction is a permanent content fabrication that cannot be traced back to the scan.

   **Calibration failures from v2 run (independent extraction of the same issue):**
   - `Benutzeroberfäche` was silently "corrected" to `Benutzeroberfläche` — but the original page actually printed `Benutzeroberfäche` (missing L, confirmed by pixel crop). The v2 agent's language model training auto-corrected what looked like a misspelling. **This is the exact failure mode this rule prevents.** The magazine's typos are historical record.
   - `gefertigt` (no period) was changed to `gefertigt.` — the v2 agent's expectation that sentences end with periods overrode what the OCR actually captured. If the pixel shows no period, emit no period.
   
   Both of these are LLM-training-data bias overriding the scan evidence. When in doubt: **the scan wins, your expectations lose.**

   Recurring **legitimate** OCR fix patterns in 64'er magazines:

   **Single-character substitutions** (the core of OCR correction):
   - `1` ↔ `l` ↔ `I` — the #1 OCR error. Affects: `(Listing ])` → `(Listing 1)`, `(Bild ])` → `(Bild 1)`, `C 64 l` → `C 64 I`, `Fl-Taste` → `F1-Taste`, `S]` → `S1`
   - `O` ↔ `0` — `$FICA` → `$F1CA`, `rO` → `r0`, `(Bild O)` → `(Bild 0)` or vice versa
   - `rn` ↔ `m` — `Cornrnodore` → `Commodore`, `Programrn` → `Programm`
   - `cl` ↔ `d` — `Mecdika-` → `Medika-`
   - `ı` → `i` — Turkish dotless bleed from 600→300 DPI downscale
   - `©` → `C` — tesseract reads the Commodore "C" as copyright symbol on nearly every page. `© 64` → `C 64`, `© 128` → `C 128`. Expect 5-20 of these per page.
   - `»` / `«` mangling — guillemets become `>>`, `<<`, `„`, `"`, `$`, or vanish. Verify each against the pixel crop. If the pixel shows a guillemet, restore it.

   **Drop caps** — the first letter of many article/section openings is a large decorative capital. Tesseract either misses it entirely or places it in a separate block. Symptoms:
   - First word starts lowercase mid-word: `reitag,` (should be `Freitag,`), `ommodore` (should be `Commodore`), `ieht` (should be `Sieht`), `ndlich` (should be `Endlich`)
   - First word is missing its initial: `as` (should be `Das`), `in` (should be `Ein`)
   
   Fix: read the drop cap from the pixel crop of the block. This is a single character — bounded, pixel-verifiable. If the drop cap is in a separate TSV block (level=5 row with just one large character), use that block's text.

   **Compound word spacing** — tesseract frequently merges adjacent words:
   - `dasalle` → `das alle`, `gibtes` → `gibt es`, `aufder` → `auf der`
   - `Computergeschäften` might be a real compound OR `Computer- Geschäften` merged across a line break — check the TSV for a hyphen at line end

   **Screenshot / listing / figure text bleeding into body blocks:**
   - Tesseract captures text from screenshots (menu items like "choose printer", "alarm clock"), BASIC listings (line numbers, DATA statements), and figure labels alongside body text.
   - Filter by **position**: if a block or word cluster sits inside a figure region (large bbox, low word count, high-`x_fsize` mismatch) or has monospaced-looking content (hex addresses, BASIC keywords), drop it.
   - Filter by **content pattern**: lines matching `^[0-9]+ (REM|DATA|PRINT|GOTO|GOSUB|IF|FOR|NEXT|POKE|SYS|READ)` are BASIC listings. Lines matching `^[0-9a-f]{4} :` are hex dumps. Drop both.

   **Column reading order reconstruction:**
   - Tesseract's `--psm 1` auto-segmenter frequently gets column order wrong when images interrupt the column flow. Body text jumps from col 3 back to col 1.
   - Fix: sort body blocks by column assignment (left x-coordinate → column bucket) then by top y-coordinate within each column. Columns read left → right. For a 2-column page at 300 DPI, the midpoint is ~1240px; for 3-column ~830/1660; for 4-column ~620/1240/1860.
   - When a paragraph crosses a column break (last word in col 1, first word in col 2), the TSV will show the words in two different blocks with different x-coordinates but sequential y-coordinates at the column boundary. Join them.

   **Massive single-block spanning multiple columns:**
   - Occasionally tesseract produces one block with 1000+ words that spans the entire page width. The words inside are still position-tagged in the TSV, so you can split them by x-coordinate into columns.
   - Use the same column-bucketing as above, but applied within the block's word list rather than across blocks.

   **Preserve unconditionally:**
   - Old German spelling (`daß`, `muß`, `läßt`, `ß`) — do NOT modernize
   - Original typos (historical record)
   - Printed punctuation exactly as OCR'd (no adding or removing periods, commas, quotes)

5. **Retry tesseract on garbled blocks.** When a body block's OCR is garbled, missing, or clearly wrong (confidence <30, nonsense character sequences, block merged with adjacent column/listing), do NOT transcribe from vision. Instead, re-run tesseract on a tighter crop:

   ```bash
   # Crop the block region from the 600 DPI source (bbox from blocks.txt, coords ×2 for 600 DPI)
   magick <source>/PPP_600_cropped.png -crop WxH+X+Y +repage _work/pPPP/retry_NN.png

   # Re-run tesseract with a simpler page-segmentation mode
   tesseract _work/pPPP/retry_NN.png _work/pPPP/retry_NN -l deu --psm 6 tsv
   ```

   PSM modes to try:
   - `--psm 6` (single uniform block) — best for dense body text that auto-segmenter mangled
   - `--psm 4` (single column) — for narrow columns or text squeezed beside an image
   - `--psm 3` (fully automatic, no OSD) — alternative to the default `--psm 1`

   Use the **600 DPI source** for retry crops, not the 300 DPI downscale — more detail helps on small or dense text. Multiply the 300-DPI bbox coordinates by 2 to get 600-DPI crop coordinates.

   **Persist retry TSV.** Save the retry output as `_work/pPPP/retry_NN.tsv` alongside `page.tsv`. Phase 3.5 verification needs BOTH files — the original `page.tsv` and any `retry_*.tsv` files — to build the complete word list. Without persisted retry TSV, Phase 3.5 flags every retry-recovered word as "novel" and auto-revert destroys legitimate recoveries.

   If the retry still produces garbage, emit `[OCR-GAP]`. Never fall back to vision transcription of body text — that bypasses the entire OCR verification discipline.

   **Calibration:** in v1 testing, the p030 agent successfully recovered a drop-cap paragraph that `--psm 1` missed by re-running with `--psm 6` on a 600×500 crop. The retry text was clean OCR, not vision composition. In 8605 v1, the p158 agent violated this rule and read body from pixels — LOG.md flagged it, but Phase 3.5 could not auto-revert because no retry TSV existed.

6. **Join broken paragraphs.** Tesseract often splits one paragraph into multiple blocks at column breaks. Join when the first character of the next block is lowercase and the previous block ended without terminal punctuation.

6. **Emit the page HTML**:

```html
<!-- page 019 -->
<h1>Der Neue</h1>
<p class="intro">Commodore ist immer wieder für Überraschungen gut: …</p>
<p>Freitag, den 11.4.1986 um 9 Uhr morgens wird eine einmalige Entscheidung getroffen: …</p>
<p>…</p>
```

Rules:
- `<h1>` comes first in the file regardless of physical position on the page (article titles often sit mid-page in 64'er; logical order wins over physical order).
- `<p class="intro">` immediately after `<h1>` if Phase 1 emitted an `intro`.
- `<h2>` section headings inline in the body flow at their natural reading position.
- Body paragraphs follow in reading order.
- Preserve paragraph indentation: default `<p>` for every paragraph. Use `<p class="noindent">` ONLY when the TSV geometry proves the paragraph is flush-left: the first word's `left` coordinate must be within ~5px of the block's left margin (at 300 DPI), AND the rest of the paragraph's first-line wrap confirms that position is the block's natural left edge (not a coincidental indent of a different paragraph). **Do NOT apply `noindent` by position heuristic** (e.g. "first paragraph after every heading"). In 64'er layouts, the first paragraph after an `<h2>` is usually indented the same as any other body paragraph. Real noindent cases are rare and must be verified per-paragraph from TSV data, not guessed. False positives are worse than false negatives — when in doubt, emit plain `<p>`.

- **`<aside>`** — for "Texteinschub" sidebars / text insets: boxed or otherwise visually separated passages that belong to the current article but are set apart from the main text flow. Often titled with a heading like "Texteinschub #1:", "Hinweis", "Zur Erinnerung", or similar. Wrap the entire sidebar content (heading + body + any byline) in a single `<aside>…</aside>` at its natural reading position in the article. Headings inside the aside stay as `<h2>`. Do NOT promote a Texteinschub to its own article (no new `<h1>`); it is part of the parent article and continues the same author/topic.

  Example:
  ```html
  <p>…main body continues…</p>
  <aside>
      <h2>Texteinschub: Dem Computer ins Wort fallen</h2>
      <p>Sidebar body paragraph…</p>
      <p>Another sidebar paragraph…</p>
  </aside>
  <p>…main body resumes…</p>
  ```

  Detect a Texteinschub visually: boxed/ruled border, inset column, distinct background shade, or a heading line starting with "Texteinschub". The content typically diverges from the main body topic (a digression, a related aside, a step-by-step instruction pulled out of the main flow).

- **`<p class="source">`** — for paragraphs printed in smaller font than body. Typically appears at the end of an article or news item and carries vendor address, price, manufacturer info, reference URLs, or similar metadata that isn't part of the article narrative. Examples:
  - `<p class="source">Info: Mannesmann Tally, Postfach 500749, 7000 Stuttgart 50, Tel: 0711/50390</p>`
  - `<p class="source">Informationen über Geos können Sie beim Hersteller Berkeley Softworks erhalten. Die Adresse lautet: Berkeley Softworks, 2150 Shattuck Avenue, Berkeley, California 94704. Der Preis beträgt augenblicklich 59,95 Dollar.</p>`

  Detection: the smaller-font paragraphs have a distinct `x_fsize` bucket in hOCR (typically one size bucket below body dominant), AND/OR are visibly smaller on the page. Usually the last 1–3 paragraphs of an article, or the last 1–2 paragraphs of each item in a news-roundup section.

  Do NOT apply `source` to the article's own narrative body even if it's at the end. `source` is for metadata/reference blocks, not for the author's concluding paragraph. The author byline `(xx)` or `(xx/yy)` is NOT `source` — it's a short standalone `<p>(xx)</p>`.

  A `<p class="source">` replaces what would otherwise be a plain `<p>`. `source` and `noindent` can combine: `<p class="source noindent">` if the source paragraph is also flush-left per TSV.
- For `kind: continuation`: no `<h1>`, no `<p class="intro">`, just body `<p>`s and `<h2>`s.
- For `kind: ad / rubric / other`: emit a single comment `<!-- page NNN: <kind> -->` and stop.

### Anti-memory rule (Phase 3)

- Every paragraph emitted must originate in an OCR block from Phase 2, corrected against the pixel crop.
- If OCR is clearly missing text (gap in reading order, paragraph ends mid-sentence with no continuation visible in any following block), emit a `<p>[OCR-GAP]</p>` marker rather than composing plausible German. A reviewer will fill it in by hand.
- If the agent sees text on the page that no OCR block captured (Tesseract missed a paragraph entirely), log the page to `LOG.md` and emit `[OCR-GAP]`. Do not transcribe from vision — that bypasses the "OCR → file → read → small edit" discipline.

## Phase 3.5 — TSV verification (script, mandatory)

After Phase 3 produces `page_NNN.html` for every body page, run a **mechanical verification** that diffs each page's output against the raw TSV. This catches two failure modes that the workflow rules forbid but agents violate anyway:

1. **Hallucinated text** — words in the HTML that don't exist in the TSV. The agent composed them from context instead of extracting from OCR.
2. **Silently corrected typos** — words in the HTML that differ from the TSV by more than the allowed character-level fixes (whitespace, single-char sub, umlaut, drop cap).

### Procedure

For each `page_NNN.html`:

```bash
# Extract words from the HTML output (strip tags)
sed 's/<[^>]*>//g' _work/pNNN/page_NNN.html | tr -s '[:space:]' '\n' | grep -v '^$' | LC_ALL=C sort -u > /tmp/html_words.txt

# Extract words from ALL TSV sources: per-block TSVs, full-page TSV, retry TSVs
cat _work/pNNN/block_*.tsv _work/pNNN/page.tsv _work/pNNN/retry_*.tsv 2>/dev/null | \
  awk -F'\t' '$1==5 && $12!="" {print $12}' | LC_ALL=C sort -u > /tmp/tsv_words.txt

# Extract words from PPStructure's own OCR (second opinion)
python3.12 -c "import json; blocks=json.load(open('_work/pNNN/layout.json'));
[print(w) for b in blocks if b.get('content') for w in b['content'].split()]" 2>/dev/null | \
  LC_ALL=C sort -u > /tmp/paddle_words.txt

# Words in HTML but not in any TSV — candidates for hallucination or typo correction
comm -23 /tmp/html_words.txt /tmp/tsv_words.txt > /tmp/novel_words.txt

# Cross-check novel words against PPStructure — if PPStructure also has the word, lower concern
comm -12 /tmp/novel_words.txt /tmp/paddle_words.txt > /tmp/novel_confirmed_by_paddle.txt
comm -23 /tmp/novel_words.txt /tmp/paddle_words.txt > /tmp/novel_unconfirmed.txt
# novel_unconfirmed.txt = high-priority flags (neither Tesseract nor PPStructure has the word)
# novel_confirmed_by_paddle.txt = medium-priority (PPStructure agrees but Tesseract doesn't)
```

Three-way verification: Tesseract TSV (primary) + PPStructure content (second opinion) + HTML output. Words in HTML that neither engine captured are almost certainly hallucinated. Words that PPStructure confirms but Tesseract missed may be legitimate (different segmentation caught them).

Most entries in `novel_words.txt` are legitimate: cross-line hyphen rejoins (`Programmser` + `vice` → `Programmservice`), drop-cap restorations (`reitag` → `Freitag`), whitespace-joined compounds (`dasalle` → `das` + `alle` — the joined form was already both words). These are fine.

**Flag for human review** any novel word that:
- Is a complete German word or phrase not derivable from any TSV token by the allowed fixes (e.g. `IBM PC` appearing where TSV has `8-Biter`)
- Differs from a TSV word by more than one character AND the change is not whitespace/umlaut/drop-cap (e.g. TSV has `Benutzeroberfäche`, HTML has `Benutzeroberfläche` — that's an `l` insertion, not a single-char substitution)

Write flagged words to `_work/pNNN/verify_flags.txt`.

### Phase 3.5b — Auto-revert flagged words (mandatory)

For each page with a non-empty `verify_flags.txt`, **automatically revert every flagged word to its TSV form** using the Edit tool. Do NOT skip this step. Do NOT use judgment about whether the "correction" was reasonable.

Procedure per flagged word:
1. Find the word in `page_NNN.html`.
2. Find the corresponding TSV token(s) for that position (grep the TSV for surrounding context words to locate the right row).
3. If the TSV token differs from the HTML word: **replace the HTML word with the TSV token via Edit.** The TSV is authoritative.
4. If the TSV token matches the HTML word (false positive from the diff — e.g. a legitimate hyphen rejoin): leave it.

**Exception:** drop-cap restorations (e.g. `reitag` → `Freitag`) and whitespace joins (e.g. `dasalle` → `das alle`) are legitimate Phase 3 fixes. These appear as novel words because the joined/restored form doesn't exist as a single TSV token. To distinguish: if the novel word is constructible by concatenating adjacent TSV tokens (possibly with a hyphen removed), it's legitimate. If not, revert.

This step is mechanical. The agent does not decide whether the "original" or "corrected" form is "better" — the TSV form wins unconditionally.

### Why this step exists

Four independent extraction runs (v1, v2, v3, v4) on the same issue all produced text that violated the anti-memory and typo-preservation rules despite those rules being prominently documented:
- **v2, v3, and v4** all "corrected" the printed typo `Benutzeroberfäche` → `Benutzeroberfläche`. The TSV has `Benutzeroberfäche`. Phase 3.5 flagged it in v4 — but without 3.5b the agent ignored the flag.
- **v3** fabricated ~50 words in the "Geos — ein Meisterwerk" paragraph: `schneller als ein IBM PC` where the TSV has `schneller, als man es einem 8-Biter zutrauen würde`. A mechanical diff would have flagged every fabricated word; auto-revert would have restored the TSV text.

The rules alone are not sufficient. LLM training-data bias overrides explicit instructions when the "correct" form is strongly expected. Flagging alone is not sufficient either — v4 proved that agents ignore their own flags. Only **mechanical auto-revert** closes the loop.

## Phase 4 — Article stitching (byte-level concatenation)

**Phase 4 MUST be byte-level `cat`, not LLM generation.** Do not regenerate article content via the Write tool — the LLM will silently drift (auto-correct OCR artifacts, fill gaps, smooth punctuation) and that is a direct violation of the anti-memory rule.

Correct procedure:

1. **Build the article→pages map.** Walk pages in order. Each `article_start` opens a new article; following `continuation` pages belong to it until the next `article_start`, `ad`, or `rubric`. For `mixed` pages, split the page's content between the ending article and the starting article.

2. **Handle jumps ("Fortsetzung auf Seite N").** Some articles jump over ads/other content to continue on a later page. Detection:
   - **Grep all per-page HTML for "Fortsetzung auf Seite"** — this is a printed navigation marker. The target page number tells you where to look.
   - **Grep all page_meta.txt for `jump_to:` / `jump_from:`** if Phase 1 captured these.
   - **Check for mid-sentence endings** at article boundaries: if an article's last page ends without terminal punctuation and the next page belongs to a different article, the original article probably jumps somewhere. Search later pages (by running header match or body-text continuity) for the continuation.
   
   When a jump is found, **include the target page(s) in the source article's page list**, not in whatever article the target page was adjacent to by page number. Example: Der Neue (p19-24) jumps to p43 bottom → article_019 includes p19-24 + p43 (bottom half). The Datenbanken article on p43 top gets its own extraction.

   **Drop the "Fortsetzung auf/von Seite N" marker lines** from the HTML output — they are navigation, not body text.

3. Concatenate in reading order with `cat`:
   ```bash
   cat _work/p019/page_019.html \
       _work/p020/page_020.html \
       _work/p021/page_021.html \
       ... \
       _work/p043/page_043.html \
       > _work/article_019.html
   ```
3. The result is byte-identical to the per-page files joined together. Every character is traceable to a Phase 3 output on disk.

Do NOT use the `Write` tool with inlined content for Phase 4. Using `Write` with a multi-KB content string means the LLM regenerates every token from context — the probabilistic generation silently introduces drift even when the source text is fully in context. `cat` is the only safe concatenation operator.

## Phase 5 — Cross-page fixups (targeted Edit, deterministic)

After concatenation, the cat'd file contains `<!-- page NNN -->` markers at every page boundary. Phase 5 applies two classes of surgical fixup to the SAME cat'd file via the `Edit` tool — **not** Write, **not** Bash sed-in-place on large files.

Two classes of edit:

1. **Cross-page hyphenation.** When last word of previous page ends with `-` and first word of next page is lowercase, join them. Example match:

   ```
   Wenn Sie die-</p>
   <!-- page 020 -->
   <p>se Ausgabe
   ```

   Becomes:

   ```
   Wenn Sie diese Ausgabe
   ```

   One `Edit` call, one `old_string` / `new_string` pair. The `old_string` must contain enough surrounding context to be unique in the file (typically 2-4 words on each side of the join).

   Do NOT join compound hyphens like `Ost-West` or `CD-ROM`. Detect compounds by context — if the joined form looks like a new word, join; if it's a real compound, leave the hyphen in place and still merge the paragraphs across the page boundary.

2. **Cross-page paragraph merge.** When last `<p>` of previous page ends without terminal punctuation (`.`, `!`, `?`, `:`, `»`, `«`, `—`) and first `<p>` of next page starts lowercase (a continuation), merge the two into one `<p>` and strip the intervening `<!-- page NNN -->` comment and closing/opening `</p><p>` tags. Example:

   ```
   alle wichtigen Befehle, die sich</p>
   <!-- page 022 -->
   <p class="noindent">mit einem Filezugriff
   ```

   Becomes:

   ```
   alle wichtigen Befehle, die sich mit einem Filezugriff
   ```

   Again: one `Edit` call per boundary. The `Edit` tool is a literal string-replace, which is exactly the anti-memory-safe operation: you can only match what's already in the file, and you write only what you specify verbatim.

3. **Strip remaining page comments.** After all joins are applied, any `<!-- page NNN -->` marker that survived (at clean paragraph breaks) should be removed by one more Edit per marker. Two or three Edits typically suffice for a multi-page article.

4. **Verify: grep for residual unjoined hyphens and missing drop caps.** After all Phase 5 edits, run:
   ```bash
   grep -nE '\-</p>$' article_NNN.html    # trailing hyphen at paragraph end = missed join
   grep -nE '^<p[^>]*>[a-z]' article_NNN.html  # paragraph starting lowercase = missed merge or drop cap
   ```
   Each hit is either:
   - A cross-page hyphen Phase 5 missed → apply the join now.
   - A drop cap the Phase 3 agent missed (e.g. `reitag,` for `Freitag,`) → restore the capital letter from the page image via a sub-agent Read of the block crop. One character, bounded.
   - A legitimate mid-article continuation fragment that Phase 5 already merged but the lowercase is inside the `<p>` (false positive) → ignore.

   Do NOT skip this grep. v4 left `aller-letzter`, `wer-den`, and `reitag,` in final output because Phase 5 only processed cross-page boundaries and missed within-page unjoined hyphens that Phase 3 should have caught.

When both signals conflict at a boundary (hyphen at end but next word is capitalized), log in `LOG.md` and leave alone — a human reviewer decides.

### Why Edit, not Bash sed

`sed -i` on a large file re-writes the whole file atomically and gives no change diff to review. `Edit` shows exactly which surrounding context matched and which new bytes replaced it, so every Phase 5 change is auditable in the harness log. Anti-memory discipline needs that auditability.

### Forbidden tools for Phase 4 and 5

- **Never use `Write` with multi-line article content.** Write is for creating fresh files, not for reproducing existing content. Even if the source file's bytes are in the LLM's context, regenerating them through the Write tool is LLM composition, not file copy.
- **Never hand-type paragraphs into an Edit `new_string`.** Every Edit `new_string` at the page boundary must contain ONLY characters that were already in the file on at least one side of the boundary — the result of the join, not a fresh paragraph. A valid Phase 5 Edit takes a small range from the file and outputs the same characters in a slightly different arrangement (hyphen removed, page comment stripped, paragraph tags collapsed).
- **Never use the main-thread LLM to "clean up" the article text** after cat. Phase 3 was the last legitimate place for content changes. Phases 4 and 5 are byte-level plumbing.

## Delegation

Main thread never Reads a page PNG. All pixel operations go through sub-agents:

- Phase 1: one sub-agent per page (batchable, 10 pages per call is fine).
- Phase 3: one sub-agent per non-skip page (parallelizable).
- Scripts run on the main thread (Phase 2, 4, 5).

Sub-agent prompts must be self-contained: page number, file paths, task, expected output format, anti-memory reminders.

## Reference files that must NOT be used as content sources

The issue directory may contain a pre-existing transcription file like `issues/NNNN/NNNN.md` (e.g. `issues/8606/8606.md`). These are historical reference material, possibly machine-OCR'd years ago, possibly hand-transcribed. **They are NOT the source of truth for this pipeline.**

- **Phase 1 (title/intro vision)**: do not consult `NNNN.md`. Title and intro must come from the page pixels.
- **Phase 3 (body reconciliation)**: do not consult `NNNN.md`. Body text must come from Phase 2 tesseract OCR, corrected against the page pixels.
- **Investigation / boundary chasing only**: a sub-agent may consult `NNNN.md` to *locate* where an article continues (e.g. grep for a known phrase to find the continuation page), but must NOT copy text from it into any output file. Treat it like an index, not a database.
- **Investigation reports must not quote content.** When the investigation agent reports its findings, it must return only page numbers, layout coordinates, and structural facts — NEVER string fragments from `NNNN.md`. Example:
  - ✓ "MT-85 continues on p27, left column; page has a byline and an address paragraph at the bottom of that column."
  - ✗ "MT-85 continues on p27 with h2 'Gemischte Gefühle' and ends with '(aw)' / Info: Mannesmann Tally, Postfach 500749…"
  The second leaks text from `NNNN.md` into the main thread's context, from where it will end up in the next Phase 3 prompt and prime the extraction agent with expected content. That is an anti-memory violation by proxy: the Phase 3 agent's output is no longer a blind extraction, it's a confirmation of preloaded text.

Using `NNNN.md` as a content source bypasses the entire OCR + pixel verification discipline. The anti-memory rule applies: every character in the output must originate in (a) pixels read by a vision agent, or (b) an OCR block verified against pixels. Text copied from `NNNN.md` — or even quoted from `NNNN.md` inside an investigation report — satisfies neither.

## What NOT to do

- Do not parse the TOC or annual index CSV to decide article boundaries.
- Do not use font size as a title detector.
- Do not include figures, tables, listings, or their captions.
- Do not include running headers, page numbers, or issue footers.
- Do NOT include section dingbats or pullquotes.
- Author bylines like `(xx)` or `(xx/yy)` at the end of an article or section ARE kept as short standalone `<p>(xx)</p>` elements — they are part of the body flow. Do NOT drop them. Bylines appearing inline at the end of a paragraph (not on their own line) stay inside that paragraph.
- Do not emit metadata, `<meta>` tags, or article shell HTML. Body extraction stops at `<h1>` + `<p class="intro">` + `<p>`; metadata is a later stamp step.
- Do not use `/tmp/` for scratch files. Use `issues/NNNN/_work/`.
- Do not Read page PNGs from the main thread.
- Do not retype a block's text by hand. Read the file, correct in place.
- Do not promote the first body paragraph to `<p class="intro">` unless it is visually distinct.

## When you can't decide — log, don't delete

If a page is ambiguous (article start or continuation? intro or body? full-page ad or editorial?), pick the less-destructive interpretation (prefer `continuation` over `ad`, prefer `body` over `skip`) and write an entry in `issues/NNNN/LOG.md`:

- page number
- what the page looks like
- why it's ambiguous
- what action a reviewer should take

A dropped page is invisible in git history; a continuation page misclassified as ad can be fixed by re-running Phase 1 after editing the page kind.

## Anti-memory rule (top priority)

Never write article text from memory — not a word. Every character in the output must originate in either the page pixels (Phase 1, for title/intro) or an OCR block corrected against the pixels (Phase 3, for body). If text looks missing, emit `[OCR-GAP]` and log. Never compose plausible German to fill a gap. Same discipline as the root `MEMORY.md`.

## Auditing agent output: verify against TSV, not against reports

Agent self-reports use informal language that can sound like fabrication when it isn't. Example phrasings that look suspicious but are usually benign:

- *"Added missing word 'Diskette'"* — usually means the agent rejoined a word that tesseract captured but placed in a separate TSV row at a line break. The word was in the OCR; the agent's "adding" was just un-splitting it.
- *"Restored missing 'worden'"* — same thing: `beho-\nben worden sein` in TSV became `behoben worden sein` after rejoining across a hyphenated line break.
- *"Pixel-recovered the initial F of 'Freitag'"* — a drop-cap the tesseract word-level rows missed; the letter is genuinely on the page, the agent read it from the image. Legitimate.

Before reverting an apparent violation in an extraction agent's output, **grep the raw TSV for the disputed token**:

```bash
awk -F'\t' '$1==5 && $12!=""' _work/pNNN/page.tsv | awk '{print $12}' | grep -B3 -A3 "disputed_word"
```

If the word is in the TSV, the agent was right — don't revert. If the word is NOT in the TSV but the agent claims to have pixel-recovered it, crop the relevant block from `page_1900.png` and Read that crop via a sub-agent to verify the pixels show it. Only then is revert justified.

**Never revert an agent's output based on the wording of its own report alone.** The agent is summarizing, not specifying. The ground truth is TSV + pixels, not the prose of the report. A revert that removes legitimately-sourced text is itself a content fabrication — you're deleting characters that originated in pixels.

This rule applies recursively: if *this* workflow's main thread revises an agent's output, the same discipline holds — every edit must be a literal `Edit` that removes TSV-derived characters only when those characters actually didn't come from pixels.
