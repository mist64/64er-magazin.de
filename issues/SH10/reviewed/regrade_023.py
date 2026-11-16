#!/usr/bin/env python3
"""p023's grade, repaired: the paper-yellowing field applied on a hand-traced page box.  Run with ISSUE=SH10.

What failed: r005_masters_sheet traced 174.5 x 297.9 mm.  p023 is the right half of a two-page Markt&Technik
book ad whose photo and red headline bleed off the GUTTER (left) edge, and paper/bed read that bleed as bed, so the
traced left line sat ~36 mm inside the leaf (debug600/023.png).  The page class was 'uncropped sheet', the whole
levelled sheet was published (213.3 x 305.0 mm), FIELD_PAGE_MM rejected the box and the field was NOT APPLIED.
Same failure, same numbers, as SH09 p031 (issues/SH09/reviewed/regrade_031.py, the precedent this follows).

What this does: OVERRIDE.  r005_masters_sheet is imported unchanged and run on page 23 alone.  The only change is
the traced box, measured by hand on sheets600/023.png: per edge, the median first non-bed pixel (lum >= BED_LUM 70)
on every 4th row/column whose next 3 mm inward are >98 % paper (lum > 170), i.e. where no print reaches the trim.
right n=1721, top n=1068, bottom n=1152; the gutter (left) n=297, read on the rows the bleed does not reach.
Box x 7..4975, y 1..7034 = 210.3 x 297.7 mm, page class A4 sheet, inside FIELD_PAGE_MM.  The issue's
field_low.txt is applied on that box; no refit (p023 was rejected from the fit; 159 pages carry the class shape).

THE BED DROP (SH09 p031's warning holds here too): locate() below REPLACES `keep` with the hand box after
level_and_trace has run its bed drop, so a dark bleed joined to the bed at the gutter is NOT whitened.  Do not
"tidy" this into `self.keep &= box`.

Proof: reviewed/tint_023.py, before and after, in reviewed/field-not-applied.txt and LOG.md.
Pre-fix artefacts kept under <tmp>/recovery/023.prefield/.  Refuses a master that already carries this OVERRIDE.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R

BOX = (7, 1, 4975, 7034)       # sheets600/023.png frame (the levelled sheet, 600 dpi)
TAG = "OVERRIDE field"

st = R.OUT_MASTER / "023.stamp.txt"
if TAG in st.read_text(encoding="utf-8"):
    sys.exit("023 already carries the field OVERRIDE; nothing done")
pre = Path(R.ISS.tmp) / "recovery" / "023.prefield" / "masters600" / "023.stamp.txt"
if not pre.exists():
    sys.exit(f"no pre-fix copy at {pre.parent.parent}; keep the automatic artefacts first")

_locate = R.Traced.locate


def locate(self):
    _locate(self)
    if self.stem != "023":
        return self
    x0, y0, x1, y1 = BOX
    ys, xs = np.arange(self.h)[:, None], np.arange(self.w)[None, :]
    self.keep = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)
    self.box = BOX
    self.page_w_mm, self.page_h_mm = (x1 - x0) / R.MM, (y1 - y0) / R.MM
    self.klass = R.page_class(self.page_w_mm, self.page_h_mm)
    if self.klass is None or not R.field_box_ok(self.page_w_mm, self.page_h_mm):
        sys.exit(f"hand box {BOX} is {self.page_w_mm:.1f} x {self.page_h_mm:.1f} mm: not a page the field takes")
    self.notes[:] = [n for n in self.notes if not n.startswith("NOT CROPPED")]
    self.notes.append(
        f"{TAG}: trace gave 174.5 x 297.9 mm (gutter-bleed ad read as bed); page box traced by hand on "
        f"sheets600, {x0} {y0} {x1} {y1} = {self.page_w_mm:.1f} x {self.page_h_mm:.1f} mm, and the class field "
        f"applied on it; issues/SH10/reviewed/regrade_023.py")
    return self


R.Traced.locate = locate
R.process(23)
out = st.read_text(encoding="utf-8")
assert TAG in out and "NOT APPLIED" not in out, "stamp does not say what was done"
print("\n".join(l for l in out.splitlines() if l.split(" ", 1)[0] in
                ("field", "field-sha", "page-class", "page-size", "page-px", "sheet-box", "notes", "field-anchors",
                 "field-page-gain")))
