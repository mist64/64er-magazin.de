#!/usr/bin/env python3
"""p030 and p167: the bed drop took printed photo with it.  Re-derive their masters with the drop's reach bounded.
Run with ISSUE=SH09 and the repo venv.  r005 is frozen for SH09: imported unchanged, two functions wrapped, p030/p167 only.

What failed: level_and_trace()'s last block drops every frame-touching component of `lum < BED_LUM | prop` whose
share outside the line-traced page exceeds BED_OUTSIDE_FRAC (0.5), WHOLESALE.  A dark photo that runs off the trim
joins the bed beyond it, the bed outweighs it, and the photo goes too: masters600 = sheets600 with ~keep painted 255.
  p030  1716.5 mm2 inside the page, one component reaching 48.68 mm deep (the 1541 chassis, page turn)
  p167   186.2 mm2, reaching 23.66 mm (olive ground under the sleeve, foot of the back cover)
Nothing said so: no note, no stamp line.  sheets600 and the owner's crops never had it (they are taken before keep).

THE PREDICATE (measured on all 168 pages of SH09, 49 dropped components that reach inside the line box):
  a doomed component is NOT dropped if the part of it inside the line-traced page reaches more than
  DEPTH_MAX_MM = 10 mm from the line box's edge (Euclidean distance transform of the line box, 600 dpi).
  Legitimate removals (bed at the trim, looked at): deepest 4.45 mm (p017, bed notch), then p092 1.82, p001 1.48,
  p132 1.48, p130 1.27, p125 0.51; largest 13.8 mm2.  Defects: shallowest 23.66 mm (p167).  10 mm sits in the
  4.45 .. 23.66 gap, a factor of ~2.2 from either side.  Area was not used: 13.8 mm2 legit against 15.3 mm2 for
  p168's prop bite leaves no margin, while depth separates the dark branch by a factor of 5.
  The predicate is per COMPONENT, not per pixel: a per-pixel depth cap would still eat the outer 10 mm of a
  photo that bleeds off the trim (p167's median depth is 5.3 mm).
p168 (prop branch, 15.3 mm2, 3.64 mm deep) is NOT repaired here: depth cannot separate it from bed, and its bite
lies at sheet x 5160-5246 while the delivered window ends at x 4961 -- it is outside the published page.

THE GRADE IS PINNED.  process() measures the paper-yellowing field's own anchors (page_anchors: Pc, the centre
paper, and K, the ink floor) over `keep`.  Restoring the photo to keep could move K and so re-grade the whole page,
sheets600 included, which the owner's crops were cut from.  page_anchors() is therefore called with the ORIGINAL
keep, and the run asserts sheets600 comes out byte-identical to the pre-fix copy.  Only masters600 changes, and only
where keep changed.

Writes masters600, sheets600, masters2400, cmyk2400, debug600 for the two pages, as r005 would.  Pre-fix copies:
<tmp>/recovery/predrop/.  It refuses a page whose master already carries this OVERRIDE.

AFTERWARDS: RECUT_OVERRIDE=1 r005_a4_window.py 30 167 (sheets600 is unchanged, so the cached fit stands and the
window must not move -- check 5); the PDF, see reviewed/pdf-postfix.txt.
"""
import sys
from pathlib import Path
import numpy as np
import scipy.ndimage as ND
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r005_masters_sheet as R

PAGES = (30, 167)
DEPTH_MAX_MM = 10.0
TAG = "OVERRIDE bed-drop"
PRE = Path(R.ISS.tmp) / "recovery" / "predrop"

_level_and_trace = R.level_and_trace
_page_anchors = R.page_anchors
ORIG_KEEP = {}
REPORT = {}


def bounded_drop(t):
    """r005's drop, with the predicate above.  Recomputed from the line box, so it replaces t.keep exactly."""
    arr, h, w = t.arr, t.h, t.w
    ys, xs = np.arange(h), np.arange(w)
    line = ((xs[None, :] >= t.xl[:, None]) & (xs[None, :] <= t.xr[:, None]) &
            (ys[:, None] >= t.yt[None, :]) & (ys[:, None] <= t.yb[None, :]))
    lum = arr.mean(2, dtype=np.float32)
    bedlike = (lum < R.BED_LUM) | R.prop_mask(arr)
    lab, _ = ND.label(bedlike)
    touching = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    touching.discard(0)
    keep = line.copy()
    spared = []
    if touching:
        labels = np.array(sorted(touching))
        total = ND.sum(np.ones_like(lab, bool), lab, labels)
        outside = ND.sum(~line, lab, labels)
        doomed = labels[(outside / np.maximum(total, 1)) > R.BED_OUTSIDE_FRAC]
        depth = ND.distance_transform_edt(line) / R.MM
        reach = ND.maximum(depth, lab, doomed) if len(doomed) else []
        inside = ND.sum(line, lab, doomed) if len(doomed) else []
        go = []
        for l, d, a in zip(doomed, reach, inside):
            if d > DEPTH_MAX_MM:
                spared.append((float(a) / R.MM / R.MM, float(d)))
            else:
                go.append(l)
        if go:
            keep &= ~np.isin(lab, go)
    return keep, spared


def level_and_trace(page):
    t = _level_and_trace(page)
    if page not in PAGES:
        return t
    ORIG_KEEP[page] = t.keep.copy()
    keep, spared = bounded_drop(t)
    REPORT[page] = (int((keep & ~t.keep).sum()), int((~keep & t.keep).sum()), spared)
    t.keep = keep
    desc = ", ".join(f"{a:.1f} mm2 reaching {d:.1f} mm" for a, d in spared)
    t.notes.append(f"{TAG}: r005's bed drop removed print inside the page ({desc}); the drop is bounded to "
                   f"components reaching <= {DEPTH_MAX_MM:g} mm into the line-traced page, the field anchors "
                   f"pinned to r005's own keep; issues/SH09/reviewed/rebed_030_167.py")
    return t


def page_anchors(arr, keep, box, field=None):
    for p, k in ORIG_KEEP.items():
        if k.shape == keep.shape and p == CURRENT[0]:
            return _page_anchors(arr, k, box, field)
    return _page_anchors(arr, keep, box, field)


def pixels(p):
    """The decoded pixels: the PNG also carries the stamp in a tEXt chunk, and the stamp now has the OVERRIDE line,
    so the file's bytes change even when not one pixel does."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    return np.asarray(Image.open(p).convert("RGB"))


CURRENT = [None]
R.level_and_trace = level_and_trace
R.page_anchors = page_anchors
for page in [int(a) for a in sys.argv[1:]] or PAGES:
    assert page in PAGES, page
    stem = f"{page:03d}"
    st = R.OUT_MASTER / f"{stem}.stamp.txt"
    if TAG in st.read_text(encoding="utf-8"):
        sys.exit(f"{stem} already carries the bed-drop OVERRIDE; nothing done")
    if not (PRE / "sheets600" / f"{stem}.png").exists():
        sys.exit(f"no pre-fix copy under {PRE}; keep the automatic artefacts first")
    CURRENT[0] = page
    R.process(page)
    out = st.read_text(encoding="utf-8")
    assert TAG in out, "stamp does not say what was done"
    restored, removed, spared = REPORT[page]
    a, b = pixels(PRE / "sheets600" / f"{stem}.png"), pixels(R.OUT_SHEET600 / f"{stem}.png")
    same = a.shape == b.shape and not (a != b).any()
    print(f"p{stem}: keep +{restored} px (+{restored / R.MM / R.MM:.1f} mm2), -{removed} px; spared {spared}; "
          f"sheets600 pixels identical to the pre-fix copy: {same}")
    assert same, f"p{stem}: sheets600 changed -- the grade moved; the owner's crops no longer match"
