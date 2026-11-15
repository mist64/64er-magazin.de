#!/usr/bin/env python3
"""p031's grade, repaired: the paper-yellowing field applied on a hand-traced page box.  Run with ISSUE=SH09.

What failed: r005_masters_sheet traced 149.0 x 297.4 mm.  The opened 1541 photo bleeds off the gutter to about
61 mm, and paper/bed read that dark photo as bed, so the traced left edge was the photo's outer boundary.  The
page class was 'uncropped sheet', FIELD_PAGE_MM rejected the box (213.3 x 305.0 mm), and the field was NOT
APPLIED: the delivered page kept the yellowed fore and top edges (99-100 % of the paper tinted in the outer
6 mm, R-B up to +16; the class median is 0-1 %).  See reviewed/colour-030-031.txt.

What this does: OVERRIDE.  r005_masters_sheet is imported unchanged (r005 is frozen for SH09) and run on page 31
alone.  The only change is the traced box, which is the paper edge measured by hand on sheets600/031.png:
the median per edge of paper against bed, on rows and columns that no print reaches.  The fore, top and bottom
edges are clean.  At the gutter, where the photo bleeds, the edge is read on the rows below the photo; it is
torn, 0-9 px from the sheet.  Box x 2..4968, y 4..7038 = 210.2 x 297.8 mm, page class A4 sheet, inside
FIELD_PAGE_MM.  The existing field_low.txt is applied on that box; no refit.  p031 was rejected from the fit, which
is a class shape that 159 pages carry.

WARNING -- p031'S PHOTO IS WHOLE BY ACCIDENT, AND THIS SCRIPT IS THE ACCIDENT (measured 2026-11-15).  r005's bed drop
(level_and_trace, last block) removes 2947.7 mm2 inside p031's automatic line box, 2552 mm2 of it in one component:
the other half of the p030/p031 lead photo, dark, joined to the bed at the gutter -- the same defect that whitened
p030 (reviewed/rebed_030_167.py).  It never reached a pixel because locate() below REPLACES `keep` with the hand box
AFTER level_and_trace has dropped it, discarding the drop's result; before this script, the failed trace published
the whole sheet (NOT CROPPED, keep = all) and discarded it the same way.  So: do not "tidy" this override into
`self.keep &= box`, and do not let a later r005 run trace p031 successfully without the bounded drop of
rebed_030_167.py (components reaching > 10 mm into the page are not dropped) -- either way p031 loses half its photo.

The stamp says so: `field` names field_low.txt and its digest (fitted), `sheet-box` is the box it was anchored on,
and `notes` carries the OVERRIDE line naming this script.

Writes masters600, sheets600, masters2400, cmyk2400 and debug600 for 031, as r005 would.  The pre-fix artefacts
are kept under <tmp>/recovery/031.prefield/.  It refuses a master that already carries this OVERRIDE.

AFTERWARDS, IN THIS ORDER (done 2026-11-14):
1. r005_a4_window.py's cache still holds the old sheet_box (0 0 5039 7204) in a4win/measured.json, and cut() translates
   the window into the master frame with it: a re-cut on the stale cache shifted a4600 by 2/4 px.  So move
   a4win/031.npz away and let `RECUT_OVERRIDE=1 r005_a4_window.py 31` re-measure p031.
2. THE WINDOW IS PINNED (r005_a4_window check 5: after a regrade the window must not move; the field moves no pixels).
   The re-measure moved the logo match 1 px (anchor y 6925 -> 6924, score 0.923 -> 0.918).  That is a matcher
   artefact of the colour change, as on SH8605 p033.  So measured.json p031 keeps the PRE-FIX logo fields
   (found side score angle bbox anchor) and the newly measured sheet_box 2 4 4968 7038 and page_class `A4 sheet`.
   Then re-cut again.  Window 7 5 4961 7016 in the sheet, as before; a4600 against the pre-fix cut: shift 0,0.
   The a4600 stamp carries a PINNED line saying so.  A later refresh of that cache must keep the pin.
3. recover_031.py (0.439 %), then check_a4600_overrides.py (green).
4. The PDF: page 31's one image stream swapped, see reviewed/pdf-postfix.txt item 3.
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R

BOX = (2, 4, 4968, 7038)       # sheets600/031.png frame (the levelled sheet, 600 dpi)
TAG = "OVERRIDE field"

st = R.OUT_MASTER / "031.stamp.txt"
if TAG in st.read_text(encoding="utf-8"):
    sys.exit("031 already carries the field OVERRIDE; nothing done")
pre = Path(R.ISS.tmp) / "recovery" / "031.prefield" / "masters600" / "031.stamp.txt"
if not pre.exists():
    sys.exit(f"no pre-fix copy at {pre.parent.parent}; keep the automatic artefacts first")

_locate = R.Traced.locate


def locate(self):
    _locate(self)
    if self.stem != "031":
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
        f"{TAG}: trace gave 149.0 x 297.4 mm (gutter-bleed photo read as bed); page box traced by hand on "
        f"sheets600, {x0} {y0} {x1} {y1} = {self.page_w_mm:.1f} x {self.page_h_mm:.1f} mm, and the class field "
        f"applied on it; issues/SH09/reviewed/regrade_031.py")
    return self


R.Traced.locate = locate
R.process(31)
out = st.read_text(encoding="utf-8")
assert TAG in out and "NOT APPLIED" not in out, "stamp does not say what was done"
print("\n".join(l for l in out.splitlines() if l.split(" ", 1)[0] in
                ("field", "field-sha", "page-class", "page-size", "sheet-box", "notes", "field-anchors",
                 "field-page-gain")))
