#!/usr/bin/env python3
"""p031's master, repaired: the M&T ad's grey-blue panel, which the bed drop whitened, kept.  Run with ISSUE=SH10.

What failed (ink-lost sweep 2026-11-15, tmp/inksweep/RESULT.txt): r005_masters_sheet traced p031 (paper/bed,
A4 sheet, box 44 1 4980 7033 in sheets600) correctly, but its BED DROP reached in from the torn right edge through
the Markt&Technik book ad's grey-blue halftone panel (x 158-209 mm of the page, full height): every dot dark enough
to read as bed was painted paper white, leaving a dithered half-white and DESTROYING the panel's reversed text
("Fragen Sie Ihren Buchhändler ...").  1359.5 mm2 of shipped print, one region, 30.7 mm deep.

What this does: OVERRIDE.  r005_masters_sheet is imported unchanged and run on page 31 alone.  After locate(),
`keep` is set True in the panel's column band (page x >= BAND_MM, i.e. sheet x >= box x0 + BAND_MM) up to, per row,
the first column of the bed: the bed is the run of lum < BED_LUM that reaches the box's right edge (lum ~35,
B-R 10-13 in sheets600; ~14 px).  Rows within EDGE_ROWS of the box's top and bottom are left to the trace.
Everything else the trace decided stands.

Bed check BEFORE the run (control's standard): `regrade_031.py --check` computes the same pixels on sheets600
and the pre-fix master and prints what would newly be kept, without writing anything.

Pre-fix artefacts kept under <tmp>/recovery/031.prebed/.  Refuses a master that already carries this OVERRIDE.
After it: r005_a4_window.py 31, the ink-lost test, 010 (and 020) for 031, and drop p031's PDF cache.
"""
import sys
from pathlib import Path
import numpy as np

BAND_MM, BED_LUM, EDGE_ROWS, LIT_RUN, MARGIN = 157.0, 70, 24, 5, 2
PX_MM = 600 / 25.4
TAG = "OVERRIDE bed-drop"


def band_mask(lum, box):
    """True where the override keeps: the panel band, short of the bed at each row's right end."""
    x0, y0, x1, y1 = box
    out = np.zeros(lum.shape, bool)
    xa = x0 + int(round(BAND_MM * PX_MM))
    for y in range(y0 + EDGE_ROWS, y1 - EDGE_ROWS + 1):
        row = lum[y, xa:x1 + 1]
        # The paper's end on this row: the last pixel of a run of >= LIT_RUN lit pixels.  A lone pixel >= BED_LUM
        # inside the bed is scanner noise and must not carry the band into it; MARGIN px are left to the trace.
        lit = np.convolve((row >= BED_LUM).astype(np.int32), np.ones(LIT_RUN, np.int32), "valid") == LIT_RUN
        idx = np.nonzero(lit)[0]
        if idx.size == 0:
            continue
        end = idx[-1] + LIT_RUN - MARGIN
        out[y, xa:xa + end] = True
    return out


if "--check" in sys.argv:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    T = Path("/Users/mist/DNB/SH10/tmp")
    s = np.asarray(Image.open(T / "sheets600/031.png").convert("RGB")).astype(int)
    pre = T / "recovery/031.prebed/masters600/031.png"
    m = np.asarray(Image.open(pre if pre.exists() else T / "masters600/031.png").convert("RGB"))
    box = (44, 1, 4980, 7033)
    lum = s.mean(2)
    band = band_mask(lum, box)
    fab = np.zeros(lum.shape, bool)
    x0, y0, x1, y1 = box
    fab[y0:y1, x0:x1] = m[:y1 - y0, :x1 - x0].min(2) >= 254
    new = band & fab
    br = s[..., 2] - s[..., 0]
    mm2 = (25.4 / 600) ** 2
    print(f"newly kept {new.sum()} px = {new.sum() * mm2:.1f} mm2")
    for name, sel in (("new & lum<70", new & (lum < 70)), ("new & 70-200", new & (lum >= 70) & (lum < 200)),
                      ("new & >=200", new & (lum >= 200))):
        if sel.any():
            print(f"  {name:14s} n={sel.sum():8d} lum {lum[sel].mean():.0f} B-R {br[sel].mean():+.1f} "
                  f"frac B-R>=12 {(br[sel] >= 12).mean():.3f}")
    ref = (~fab) & (lum < 200)
    ref[:, :x0 + int(100 * PX_MM)] = False
    ref[:, x0 + int(150 * PX_MM):] = False
    print(f"  reference kept print x 100-150 mm: n={ref.sum()} lum {lum[ref].mean():.0f} "
          f"B-R {br[ref].mean():+.1f} frac B-R>=12 {(br[ref] >= 12).mean():.3f}")
    bed = np.zeros(lum.shape, bool)
    bed[y0:y1, x1 - 40:x1 + 1] = lum[y0:y1, x1 - 40:x1 + 1] < BED_LUM
    print(f"  bed in the last 40 cols: {bed.sum()} px, of which kept by the band: {(bed & band).sum()}")
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R

st = R.OUT_MASTER / "031.stamp.txt"
if TAG in st.read_text(encoding="utf-8"):
    sys.exit("031 already carries the bed-drop OVERRIDE; nothing done")
prefix = Path(R.ISS.tmp) / "recovery" / "031.prebed" / "masters600" / "031.stamp.txt"
if not prefix.exists():
    sys.exit(f"no pre-fix copy at {prefix.parent.parent}; keep the automatic artefacts first")

_locate = R.Traced.locate


def locate(self):
    _locate(self)
    if self.stem != "031":
        return self
    lum = np.asarray(self.arr, dtype=np.float32)
    lum = lum.mean(2) if lum.ndim == 3 else lum
    band = band_mask(lum, self.box)
    before = int((~self.keep).sum())
    self.keep |= band
    self.notes.append(
        f"{TAG}: the bed drop whitened the M&T ad's grey-blue panel (page x >= {BAND_MM:.0f} mm, full height) and "
        f"its reversed text; keep restored there up to each row's bed run ({before - int((~self.keep).sum())} px); "
        f"issues/SH10/reviewed/regrade_031.py")
    return self


R.Traced.locate = locate
R.process(31)
out = st.read_text(encoding="utf-8")
assert TAG in out, "stamp does not say what was done"
print("\n".join(l for l in out.splitlines() if l.split(" ", 1)[0] in
                ("page-class", "page-size", "page-px", "sheet-box", "notes", "edge-finder", "skew")))
