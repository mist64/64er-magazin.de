#!/usr/bin/env python3
"""p002's master, repaired: print that the trace painted white as fabricated margin, kept.  Run with ISSUE=SH10.

What failed (owner, from the trial PDF: "p2 is missing a triangle at the top. 'Profi' is almost cut off"):
r005_masters_sheet traced p002 (inside front cover, from an uncut A3 wrapper sheet, 2400 dpi) with the ink/bed
finder (paper frac 0.011), and its TOP line came out at -2.95 deg.  The print runs to the scan's top edge here, so
the quadrilateral's sloped top left a wedge, 0 px deep at the right and ~200 px at the left, OUTSIDE `keep`, and
r005 painted it paper white as fabricated margin.  That wedge is the top of the black triangle and of "Profi".
The left line also sat ~20 px inside the sheet's own edge on the dark rows at the top-left.  r005b's window
(0 9 4961 7016) was fine and cuts 9 px.
Measured before (sheets600 ink, lum < 200, against masters600 pure white, inside the sheet-box 0 0 5278 7034):
top band y < 300 878.3 mm2, left band x < 120 58.0 mm2, right 4.3, bottom 4.8, interior 0.0.

What this does: OVERRIDE.  r005_masters_sheet is imported unchanged and run on page 2 alone.  After locate() the
traced `keep` is OR-ed with the sheet-box's top band (rows 0..TOP_BAND) and left band (columns 0..LEFT_BAND).  The
scan's top and left edges ARE the page's edges here (sheet-box 0 0; no bed above or to the left), so nothing in
those bands is bed.  Right and bottom keep their traces (R -0.01, B -0.09 deg; the right is the Bund, which r005b
trims 317 px off anyway).  The box, page class and stamp geometry are unchanged.

Pre-fix artefacts kept under <tmp>/recovery/002.pretrace/.  Refuses a master that already carries this OVERRIDE.
After it: r005_a4_window.py 2, then re-run the ink-lost test; then 010 (and 020) for 002, and drop p002's PDF cache.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R

TOP_BAND, LEFT_BAND = 400, 150     # px at 600 dpi, sheets600/002 frame
TAG = "OVERRIDE keep"

st = R.OUT_MASTER / "002.stamp.txt"
if TAG in st.read_text(encoding="utf-8"):
    sys.exit("002 already carries the keep OVERRIDE; nothing done")
pre = Path(R.ISS.tmp) / "recovery" / "002.pretrace" / "masters600" / "002.stamp.txt"
if not pre.exists():
    sys.exit(f"no pre-fix copy at {pre.parent.parent}; keep the automatic artefacts first")

_locate = R.Traced.locate


def locate(self):
    _locate(self)
    if self.stem != "002":
        return self
    x0, y0, x1, y1 = self.box
    if (x0, y0) != (0, 0):
        sys.exit(f"box {self.box} does not start at the sheet's corner; the premise of this override is gone")
    before = int((~self.keep[y0:y1, x0:x1]).sum())
    self.keep[0:TOP_BAND, x0:x1 + 1] = True
    self.keep[y0:y1 + 1, 0:LEFT_BAND] = True
    after = int((~self.keep[y0:y1, x0:x1]).sum())
    self.notes.append(
        f"{TAG}: the ink/bed trace's top line (-2.95 deg) and left line cut print that runs to the scan's edge; "
        f"keep extended to the box's top {TOP_BAND} rows and left {LEFT_BAND} columns ({before - after} px restored); "
        f"issues/SH10/reviewed/regrade_002.py")
    return self


R.Traced.locate = locate
R.process(2)
out = st.read_text(encoding="utf-8")
assert TAG in out, "stamp does not say what was done"
print("\n".join(l for l in out.splitlines() if l.split(" ", 1)[0] in
                ("page-class", "page-size", "page-px", "sheet-box", "notes", "edge-finder", "skew")))
