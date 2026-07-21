# Processing an issue end-to-end (scan → numbered pages → CMYK)

Operational runbook for turning a directory of raw cut scans into the final
per-page output. For the *theory* of how scan slots map to pages and how to find
missing sides / duplicates, see **[RENUMBERING.md](RENUMBERING.md)** — this file is
the "which commands, in what order, and the gotchas that cost hours" companion.

Reference issues: **8608** (CMYK-converted, complete), **8609/8610** (reconstructed
from scrambled saddle-stitch scans), **8611** (in progress).

**Scripts in this dir** (`tools/img/scan-reconstruct/`):
`thumbs.sh` (step 1), `raw_montage.sh` (step 2 true-count), `rotate.sh` (step 3).
**Shared tools in the parent dir** (`tools/img/`): `make_audit.py`, `renumber.py`,
`make_folio_montage.py`, `pipeline.sh`, `convert.py`, `detect_widths.py` — referenced
below as `../<tool>`.

## Directory layout

```
/Volumes/S/scan/<ISSUE>/            raw cut scans:  Scan.tiff (slot 0), Scan 1..N.tiff
/Volumes/S/scan/<ISSUE>/thumbs/     150-dpi thumbnails for audits (Scan*.png)
/Volumes/S/png/<ISSUE>/             FINAL: 001.png .. NNN.png (full res) + thumb/NNN.png
```

Source tiffs are ~2400 dpi, ~28000×20800 px (~600 MP), ~1 GB each, stored **landscape**
(rotate 90° left = `-rotate 270` to make upright). `Scan.tiff` (no number) is slot 0;
`Scan K.tiff` is slot K. File count must be **÷4** (see RENUMBERING.md).

## The pipeline, step by step

### 0. Survey
```
ls /Volumes/S/scan/<ISSUE>/Scan*.tiff | wc -l      # count; must be %4==0
[ -f "/Volumes/S/scan/<ISSUE>/Scan.tiff" ] && echo "slot0 present"
df -g /Volumes/S | tail -1                           # need headroom (see Disk below)
```
`%4==0` does **not** mean complete — missing + duplicate cancel. Always audit (step 2).

### 1. Thumbnails first (cheap) — *before* the expensive full rotate
Generate only 150-dpi thumbs, then verify page order. Never blind-rotate a whole issue
at full res before confirming the set is complete and correctly ordered.

**`thumbs.sh <SRC_DIR> <OUT_DIR>`** — 12-way parallel, resumable (skips existing).
Run detached (see Durability):
```
nohup bash thumbs.sh /Volumes/S/scan/<ISSUE> /Volumes/S/scan/<ISSUE>/thumbs \
      > /Volumes/S/scan/<ISSUE>_thumb.log 2>&1 &
```
Thumbs are tiny in RAM → finish in a few minutes for a whole issue. Note these thumbs
are **already upright** (the script applies `-rotate 270`), so pass `--rotate 0` to
`make_audit.py` / use `raw_montage.sh` as-is (both expect upright input).

### 2. Audit page order (see RENUMBERING.md → "Audit")
```
../make_audit.py --src thumbs --rotate 0 --pages <TRUE_COUNT> --cols 2 --out audit_<ISSUE>.png
```
- Derive **TRUE_COUNT** first if files are missing: build a raw slot-order montage with
  **`raw_montage.sh <OUT.png> <FIRST_SLOT> <LAST_SLOT>`** (run from the scan dir), read two
  folios that share a sheet (same group of 4 slots), and use `count = folio_a + folio_b − 1`
  (RENUMBERING.md → "Deriving the true count"). Do **not** trust the file count. Cross-check
  on a second sheet — both pairs must give the same count. *(8611: file count 188 but two
  sheets both summed to 193 → TRUE_COUNT 192.)*
- `--rotate 0` because `thumbs.sh` output is pre-rotated upright; use `-90` (default) only
  on raw landscape scans. Missing slots render as red placeholders in the audit.
- Read the montage: tag == printed folio everywhere → clean. `+2` run → missing side;
  re-sync later → duplicate absorbed it. Confirm dups by content:
  `magick compare -metric RMSE "thumbs/Scan A.png" "thumbs/Scan B.png" null:` (~0.004 = same).
- Fix by moving `Scan*` files high→low, on **both** originals and `thumbs/` (recipes in
  RENUMBERING.md → "Fix"). Re-audit until clean. Insert rescans of missing sides as they
  arrive; the low page# goes in the first (side-A) slot.

### 3. Full-res rotate (expensive) — only once the set is clean
**`rotate.sh <SRC_DIR> <OUT_DIR>`** — 8-way parallel, resumable, writes full **and** thumb
from a single magick decode per file (`-clone` twice). Launch detached:
```
nohup bash rotate.sh /Volumes/S/scan/<ISSUE> /Volumes/S/scan/<ISSUE>-png \
      > /Volumes/S/scan/<ISSUE>-png/rotate.log 2>&1 &
```
The skip-check needs **both** outputs → a killed job resumes cleanly (an interrupted file,
having only the full PNG, is redone). ~200 files at 8-way ≈ 80–90 min on this box.

### 4. Verify, renumber, move
```
cd /Volumes/S/scan/<ISSUE>-png
# no zero-byte files:
find . -name 'Scan*.png' -size 0
# renumber.py counts argv but renames hardcoded Scan*.png in CWD by imposition.
# Run it in the full dir AND the thumb dir separately:
python3 ../renumber.py Scan*.png
cd thumb && python3 ../renumber.py Scan*.png && cd ..
# verify 001..NNN complete in both, no Scan* left, then move into place:
mv /Volumes/S/scan/<ISSUE>-png /Volumes/S/png/<ISSUE>
```
`renumber.py` needs the count ÷4; it applies the imposition so `Scan*` → `001.png..NNN.png`
in reading order (RENUMBERING.md → "The imposition").

### 5. Widths + CMYK pipeline
- **Klammer-bound (stapled) issues** — 8608/8609/8610/8611: `widths.txt` is created
  **manually** (page content-width to keep). `detect_widths.py` is **Sonderheft-only**;
  do not use it here.
- Then run the unified converter:
  ```
  cd /Volumes/S/png/<ISSUE>
  bash ../pipeline.sh out --layout=standard
  ```
  `pipeline.sh` (successor to `ALL.sh`) does: `convert.py` RGB→CMYK plane separation →
  per-channel `-level` contrast → resize → ICC (USWebCoatedSWOP→AdobeRGB) → crop →
  per-page saturation auto-classify into `lq/` vs `hq/` (bw/spot/color, threshold 175).
  It **skips pages that already have `lq/`**, so it is resumable. Run with `bash` (the
  file is not chmod +x). Optionally build a folio montage (`make_folio_montage.py`,
  default `--cols 2 --src thumbs`) to eyeball order after renumber.

## Performance — what actually matters (measured on this box)

Hardware: **512 GB RAM, 31 threads.** A 600 MP page needs ~6 GB working set → RAM is never
the limit; you can run 8–16 in parallel.

- **The bottleneck is the PNG encode, not the rotate and not the disk.** Measured on one
  ~983 MB page: rotate compute ≈ 42 s; full PNG encode (zlib, **single-threaded**) ≈ 160–175 s.
  A serial run therefore pins ~1 core and idles the other 30.
- **Parallelize.** `xargs -P 8` (full) / `-P 12` (thumbs) gives ~Nx throughput. Set
  `MAGICK_THREAD_LIMIT` low (2–4) so per-process threads don't oversubscribe against the
  fan-out. The old "parallel rotate is slower" belief is **false** on this box — it came
  from an era of contention that doesn't apply here.
- **PNG compression level barely matters, and level 1 is a trap.** level 1 = 158 s / **923 MB**,
  level 6 = 173 s / 797 MB, default = 175 s / 797 MB. Level 1 is 10 % faster but **15 % bigger**;
  levels 6/9/default are all ~equal. Use **level 9** (or default) — same size, and these are
  intermediates `pipeline.sh` re-encodes anyway.
- If a full rotate seems to take >5 min/file, suspect **stale process state** (kill stray
  `magick`, re-check) or a **near-full disk** (below) — not the algorithm. A clean cold run
  is ~200 s/file.

## Disk space

Near-100 %-full APFS **thrashes on allocation** and slows writes to a crawl — this alone
made an early 8610 run look ~2× slower. Keep real headroom.

- Full level-9 PNG ≈ **800 MB** each; source tiff ≈ **1 GB**. A ~200-page issue's full PNGs
  ≈ **160 GB**. Check `df -g /Volumes/S` gives more than that in free space **before** step 3.
- If space is tight mid-run the job dies and leaves a truncated last file (the skip-check
  redoes it, so it self-heals — but only after you free space).

## Durability — don't lose an 85-minute job

Background jobs die on **session teardown / reboot**, and the agent **scratchpad is wiped
between sessions**. So:

- Put the runner script on a **durable path** (`/Volumes/S/scan/rot9.sh`), **not** in the
  scratchpad (`/private/tmp/.../scratchpad/` vanishes).
- Launch with **`nohup … &`** and redirect to a log on `/Volumes/S`
  (`> /Volumes/S/scan/<ISSUE>-png/rot9.log 2>&1`). `run_in_background` Bash tasks are torn
  down with the session; `nohup` survives.
- All the scripts here are **resumable** (skip when output already exists) — just relaunch
  after any interruption; it picks up where it stopped.
- Watch for completion with a Monitor `until grep -q ALLDONE <log>; do sleep 5; done`
  rather than polling by hand.

## Gotchas that cost time

- **Filenames contain a space** (`Scan 12.tiff`). Always quote; use `-print0 | xargs -0`;
  never a bare `for f in Scan*.tiff` word-split. Index-based loops (`for i in $(seq …)`) are
  safer for shifting slots.
- **`renumber.py` ignores argv contents** — it only counts them, then renames the literal
  `Scan.png` / `Scan N.png` in the CWD. Run it *inside* each target dir; run it separately
  for `thumb/`.
- **Skip-check needs both full + thumb.** If you ever generate them in separate passes, a
  half-done page won't be skipped — intended, but know it.
- **zsh `no matches found`** on globs like `Scan*.png` when a dir is empty is an error, not
  a warning — guard with `2>/dev/null` or test existence first.
- **TRUE_COUNT ≠ file count.** Re-run the audit with the *derived* count; a wrong count
  scrambles the whole montage and sends you chasing phantom problems (this happened on 8610
  with 204/196 before landing on 200).
