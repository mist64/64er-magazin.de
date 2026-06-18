# Scan renumbering & sheet reconstruction

How the cut scans map to magazine pages, how to find missing sides / duplicates,
and how to fix them by moving `Scan*` files. Tools referenced: `renumber.py`,
`make_audit.py`, `rotate_and_preview.sh`, `vision_ocr`.

## Physical model

Issues are **saddle-stitched**: nested bifolios (one folded A3 = one *sheet* = 4 pages).
Each sheet is scanned on **both sides**; every A3-side scan is then **cut into 2 single
A4 pages**. So:

- **1 sheet → 2 sides → 4 cut files.**
- A cut page is ~A4 (≈304×222 mm @ 2400 dpi), stored **landscape** (content lies on its
  side; rotate 90° left / `-rotate 270` to make it upright).
- Files are fed/named in **sheet order, outermost first**: `Scan.tiff` is slot 0, then
  `Scan 1.tiff`, `Scan 2.tiff`, … We call the slot index `src` (so `Scan.tiff` = src 0,
  `Scan N.tiff` = src N).

## The imposition (`renumber.py`)

`renumber.py` requires the file count to be **divisible by 4** and maps each `src` to its
logical page for a *complete* nested booklet of `count` pages. Closed form:

```
sheet j (1 = outermost) occupies scan slots  4(j-1) .. 4j-1
its four pages, in scan order, are:
    [ count+2-2j , 2j-1 , 2j , count+1-2j ]
      └ side A ┘             └ side B ┘
```

- **Side A** (first A3 side scanned) = slots `4(j-1)`, `4(j-1)+1` → pages `count+2-2j` and `2j-1`.
- **Side B** = slots `4(j-1)+2`, `4(j-1)+3` → pages `2j` and `count+1-2j`.
- A page `p` always shares its sheet with its **conjugate** `count+1-p` (1↔count, 2↔count-1, …).
- `sheet(p) = ceil(min(p, count+1-p) / 2)`.

### Example, `count = 8`

| src (Scan) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| page | 8 | 1 | 2 | 7 | 6 | 3 | 4 | 5 |

Sheet 1 = slots 0–3 → pages `[8,1,2,7]`; sheet 2 = slots 4–7 → `[6,3,4,5]`.

### Example, `count = 176` (first slots)

`src`: 0→176, 1→1, 2→2, 3→175, 4→174, 5→3, 6→4, 7→173, 8→172, 9→5, 10→6, 11→171, …
Sheet 4 = slots 12–15 → `[170, 7, 8, 169]` (side A `{170,7}`, side B `{8,169}`).

> Always build the map with the **true** page count (e.g. 176), **not** the current file
> count if files are missing — a short count produces a wrong mapping.

## Reading a folio

Printed page number sits in the **bottom outer corner**: **even page → bottom-left,
odd page → bottom-right** (after making the page upright). To read it:

```
magick "Scan N.tiff" -rotate -90 -gravity South -crop 100%x10%+0+0 +repage -resize 760x out.png
```

OCR (`tesseract`, `vision_ocr`) is unreliable on these dense listing pages — reading the
strip image directly is the accurate method. `make_audit.py` automates this for all pages.

## Audit: find the problems

```
make_audit.py [--src thumbs] [--out audit_sheet.png] [--cols 2] [--height 10] [--pages N]
```

Produces **one image**: every scan's folio strip in **logical page order**, each tagged
(red, on a yellow tab) with the page number it is *assumed* to be. Scan down the sheet:

- **Tag == printed folio** everywhere → order is correct.
- **A run where printed folio = tag + 2** → a **missing side** began just before that run
  (2 pages absent push everything forward by 2).
- **The run reverts to matching** later → a **duplicate** absorbed the shift there
  (2 extra files). A page that appears **twice** is the duplicate.

Confirm a suspected duplicate by content, not eyeballing:

```
magick compare -metric RMSE "thumbs/Scan A.tiff" "thumbs/Scan B.tiff" null:
#  ~0.004  → same scan (duplicate)
#  ~0.26   → genuinely different pages
```

**Bookkeeping identity:** `files = target_pages − missing + duplicates`. A file count that
is divisible by 4 does **not** mean complete — missing sides and duplicates can cancel.

## Fix: move `Scan*` files

Find the `src` slot of any page from the imposition: side A of sheet `j` is at slot
`4(j-1)`; or invert the map (`page → src`). Then:

**Insert a missing side** (2 pages) at slot `k` — shift everything from `k` up by 2,
then drop the two rescans in. Do it **high→low** to avoid clobbering, on **both** the
originals and `thumbs/`:

```
# free slots k, k+1 (here the highest existing index is HI)
for i in $(seq HI -1 k); do mv "Scan $i.tiff" "Scan $((i+2)).tiff"; done
# place rescans (lower page# = first side-A slot)
mv rescan_lowpage.tiff  "Scan k.tiff"
mv rescan_conjugate.tiff "Scan $((k+1)).tiff"
# repeat the same loop inside thumbs/, then thumbnail the two new files
```

**Remove a duplicate** — park it (reversible), then close the gap by shifting the higher
files **down** by 2 (low→high). Equivalently: when inserting a missing side *and* a dup
exists in the same shifted run, deleting the extra pair and inserting the real pair leaves
files above the run **unchanged** (the +2 and −2 cancel).

After every fix, regenerate the audit sheet and re-check. When count == target and ÷4 with
all tags matching, the set is clean and `renumber.py` (or the `page→src` map) yields the
final order.

## Worked example — issue 8609 (Ausgabe 9/1986, 176 pp)

Started with **172** files. `172 = 176 − 6 missing + 2 duplicate`:

| Problem | Pages | Slots (src) | Action |
|---|---|---|---|
| Missing sheet 4, side B | 8, 169 | 14, 15 | inserted rescans |
| Missing sheet 21, side A | 41, 136 | 80, 81 | inserted rescans |
| Missing sheet 27, side A | 53, 124 | 104, 105 | inserted rescans |
| Duplicate (page 58, 119) | 58, 119 | — | moved to `_dupes/` |

Each missing side surfaced in the audit as a `+2` run; the duplicate appeared as page 58
and 119 each showing twice (RMSE ≈ 0.004) and re-syncing the run. Result: clean 176.

## Outputs

- `thumbs/Scan*.tiff` — 150-dpi thumbnails (fast input for audits).
- `thumbs_pageorder/NNN.tiff` — thumbnails copied into reading order.
- Full-res rotated PNGs via `rotate_and_preview.sh` (or `-rotate 270`); can be written
  directly under logical names `NNN.png` by driving the conversion from a `page<TAB>file`
  map generated with the imposition.
