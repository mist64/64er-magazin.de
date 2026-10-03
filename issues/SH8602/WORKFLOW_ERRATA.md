# SH8602 — workflow errata (r340)

Written as the build goes. Newest at the bottom.

## 005 — the scans are MIXED RESOLUTION and step 005 hardcodes 2400 dpi

**What the rules say.** r000, *Where the scans are*: "`/Volumes/S/png/<ID>/NNN.png`
the 2400 dpi masters". r005_masters_sheet.py: `SCAN_DPI = 2400`,
`SCAN_REDUCE = SCAN_DPI // MASTER_DPI  # 4`. r000's thumb recipe: one command,
`magick "$m" -scale 6.25%` for every master.

**What I did.** Ran the thumb recipe verbatim over all 168 masters. 160 of the
thumbs came out ~317 × 449 px — 37.5 dpi, not 150.

**What is true.** SH8602's pages **003–162 are 600 dpi** (`5029 × 7188` px,
`236.22 px/cm`, ~63 MB); only **001, 002, 163–168** are 2400 dpi
(~20300 × 28751, ~850 MB). The raw TIFFs in `/Volumes/S/scan/SH8602/` are the
same (~72 MB interior, ~1 GB cover), so no 2400 dpi copy of the interior
exists. r000 *does* hint at this — `create_thumbnails.sh` "branches by page
range because that issue's scans were *mixed resolution*" — but as a reason to
distrust found thumbs, not as a property the chain must handle. Re-derived the
interior thumbs with `-scale 25%`; all 168 are now 1256–1349 px wide.

**Cost.** ~5 min, 4 commands to notice and re-derive. The real cost is
downstream: step 005 sheet cannot run on 160 of 168 pages as written.

**What would have prevented it.** r000 thumb recipe: "Scale each master by
`150 / its own dpi` (read `%x` from the PNG), never a fixed 6.25 % — SH8602 is
600 dpi on 003–162." And r005: `SCAN_DPI` per page from the PNG header.

## 005 — the sheet variant asks for a "measured colors.txt" and says nowhere how to measure one

**What the rule says.** r005_masters_sheet.md: "`low` — the cheap interior
stock … this issue's **measured** `colors.txt`". The procedure for measuring
`W` lives only in r005_masters_spread.md, *The profile is MEASURED for this
issue's paper*; the sheet rule points at SH8601's existing file.

**What I did.** Found no `colors.txt` beside SH8602's scans (correctly — r005
spread says the profile lives in the repo) and went looking in the sheet rule
for the procedure; it is not there. Took it from the spread rule.

**Cost.** ~3 min, 3 commands.

**What would have prevented it.** One line in the sheet rule's *Two papers*
section: "For a new issue, measure `paper.low` as in r005_masters_spread.md
*The profile is MEASURED* (pool interior thumbs, low percentile) and write it
to `issues/<ID>/colors.txt`."

## 005 — the mixed-resolution fix, as made (moved under the build)

The resolution problem above BLOCKED step 005, so it was fixed at once
(r000: "a defect that BLOCKS the build … is fixed at once … recorded in the
errata as having moved under the build"). The owner, asked at PAUSE 1, chose
this over a rescan.

- `r005_masters_sheet.py`: new `scan_dpi(scan)` reads the PNG pHYs, snaps to
  `SCAN_DPIS = (600, 2400)`, and cross-checks that the frame is 250–350 mm tall
  at that resolution (else `PageFailed`). The reduction is per page:
  `dpi // MASTER_DPI`, so 4 at 2400 (unchanged) and 1 at 600. A 600 dpi page
  has no `masters2400/NNN.png`; its full-resolution render goes to scratch,
  because there it IS `sheets600`. `cmyk2400/NNN.tif` is still written (the
  separation, at the scan's own dpi). Every stamp gains `scan-dpi`.
- **Before/after, measured** on p050 (600 dpi) and p163 (2400 dpi):
  - p050 before: traced **53.2 × 76.0 mm**, published as an uncropped sheet
    (every mm constant read at a quarter scale). After: **209.2 × 296.9 mm**,
    A4 class, own-paper white 255, dark contrast 251.
  - p163 before → after: `masters600`, `sheets600`, `masters2400` and `debug600`
    all **pixel-identical** (`magick compare -metric AE` = 0); the profile
    is byte-identical; the stamp differs by the one added `scan-dpi 2400` line.
- **Consequence for r005's Verification 1** ("every page produced all six
  artefacts"): it now has to expect no `masters2400/NNN.png` for a 600 dpi
  page. Not edited mid-build; harvest it.
- The lane peak (19 GB) is a 2400 dpi number; a 600 dpi lane is ~1/16 of it.
  Sized by the rule anyway (`lanes(19)` → 10).
