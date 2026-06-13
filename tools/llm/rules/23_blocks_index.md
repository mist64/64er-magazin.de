# 23 — Build the per-page blocks index (once per issue)

**Goal:** generate a lightweight per-page layout-block index for the
issue, saved to `issues/<YYMM>/_tmp/blocks/p<NNN>.txt`. The index
lists each layout block on each page with its bbox (`WxH+X+Y`) and a
short text preview. Several later rules (13 fill_tables, 14
transcribe_listings, 19 head_meta, 22 rubric_banners) use this index
to locate captions, code blocks, header strips, and banner
illustrations without re-running tesseract every time.

**Run this early.** After the PDF is in `issues/<YYMM>/` and before
rules 10/12/13/14/19/22 dispatch. The whole pass is fast
(~1-2 seconds per page on tesseract, no model loading).

## What this is NOT

It's NOT the rich PaddleOCR PPStructureV3 output produced by the
body-text-extraction workflow (`tools/llm/new/body_workflow.md`).
That output goes to `_work/p<NNN>/` and carries reading-order,
column boundaries, and per-block hOCR — useful for body-text
reconstruction but expensive (~50 s/page). Rule 23 is the cheap
shorthand needed when you only want bbox + a few words of text per
block.

If an issue HAS the rich `_work/p<NNN>/blocks.txt` (because
body_workflow.md ran), rules that need bboxes prefer that. If not,
they read this rule's `_tmp/blocks/p<NNN>.txt`. Same shape, both
work.

## Briefing for the sub-agent

```bash
issue=<YYMM>
dir="issues/$issue"
tmp="/tmp/64er_${issue}"        # all /tmp scratch lives under this prefix
mkdir -p "$dir/_tmp/blocks"
mkdir -p "${tmp}_pages_300"

# 1. render every page to PNG at 300 dpi (once)
pdftoppm -r 300 "$dir/64er_19XX-XX.pdf" "${tmp}_pages_300/p" -png

# 2. tesseract TSV + awk block-grouper per page
for png in ${tmp}_pages_300/p-*.png; do
  page=$(basename "$png" .png | sed 's/^p-//')
  tsv="${tmp}_p${page}_ocr.tsv"
  out="$dir/_tmp/blocks/p${page}.txt"
  tesseract "$png" "${tsv%.tsv}" -l deu tsv 2>/dev/null
  awk -F'\t' 'NR>1 && $1==5 && $12!="" {
    b=$3;
    if (!(b in minL) || $7<minL[b]) minL[b]=$7;
    if (!(b in minT) || $8<minT[b]) minT[b]=$8;
    if (!(b in maxR) || $7+$9>maxR[b]) maxR[b]=$7+$9;
    if (!(b in maxB) || $8+$10>maxB[b]) maxB[b]=$8+$10;
    text[b]=text[b]" "$12;
  }
  END {
    for (b in text) {
      printf "block=%s bbox=%dx%d+%d+%d text=%s\n",
        b, maxR[b]-minL[b], maxB[b]-minT[b], minL[b], minT[b],
        substr(text[b],1,200);
    }
  }' "$tsv" | sort > "$out"
done
```

Each output file looks like:
```
block=1 bbox=1980x44+260+200 text= Aktuelles C 64
block=22 bbox=825x84+195+1955 text= Listing 1. Komprimierte Version ...
block=45 bbox=840x39+1321+3256 text= Tabelle 2. Hier die entwirrte ...
```

`<page>` is the zero-padded PDF page number (matching
`/tmp/64er_<YYMM>_pages_300/p-<page>.png`). PDF page may differ from
magazine page — body pages typically use magazine page + an offset.

Output location: `issues/<YYMM>/_tmp/blocks/`. The `_tmp/` directory
is **untracked** (per `.gitignore` rule `**/_tmp/`); never commit it.

## How later rules use it

| Rule | What they grep for |
|---|---|
| 13 fill_tables | `Tabelle [0-9]+`, `STECKBRIEF`, `Bild [0-9]+` |
| 14 transcribe_todo_listings | `Listing [0-9]+` |
| 19 head_meta | First block (`block=1`) — running header at top of page |
| 22 rubric_banners | The rubric name (`Bücher`, `Fehlerteufelchen`, `Editorial`, `Leserforum`) |

Each rule has its own use-the-bbox-to-crop recipe; this rule just
guarantees the index exists.

## Verification

```bash
dir=issues/<YYMM>

# 1. one blocks file per rendered page
n_pages=$(ls /tmp/64er_<YYMM>_pages_300/p-*.png 2>/dev/null | wc -l | tr -d ' ')
n_blocks=$(ls "$dir/_tmp/blocks/"p*.txt 2>/dev/null | wc -l | tr -d ' ')
[ "$n_pages" = "$n_blocks" ] || \
  echo "  WARN: $n_pages pages rendered, $n_blocks block files"

# 2. every blocks file is non-empty (a body page has many blocks)
for f in "$dir/_tmp/blocks/"p*.txt; do
  [ -s "$f" ] || echo "  empty: $f"
done

# 3. spot-check format: every line should be 'block=N bbox=WxH+X+Y text= ...'
head -1 "$dir/_tmp/blocks/"p050.txt 2>/dev/null
```

## Notes / lessons

- 300 dpi is the right resolution for this pass. Lower (150 dpi)
  loses bbox precision; higher (600 dpi) just slows tesseract
  without adding useful detail at the block granularity.
- The PDF page numbering rarely matches the magazine's printed page
  number (front matter, TOC pages 6-7, etc. shift the offset).
  Rules that work in terms of magazine pages need to apply the
  per-issue offset before looking up `p<NNN>.txt`. The offset
  becomes obvious from the running header on the first body page.
- This rule's `.txt` files are not the same as the `prg/*.txt`
  petcat listing files — different content, different directory.
- The body_workflow.md PPStructureV3 outputs (in `_work/p<NNN>/`)
  carry additional fields (column boundaries, reading-order
  `order_index`, layout class) that rule 23 doesn't reproduce.
  Issues that already have those `_work/` outputs don't need rule
  23 — but having both is fine; later rules prefer `_work/` when
  present and fall back to `_tmp/blocks/`.
