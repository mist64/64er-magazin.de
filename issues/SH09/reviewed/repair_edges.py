#!/usr/bin/env python3
"""p130 and p132, the torn fore edge repaired in a4600.  Run with ISSUE=SH09; optional argument: an output directory.

What failed: both pages keep, inside the traced edge, the dark torn fibres and bed shadow of the fore edge.  They lie
in the fringe, not outside the trace, so r005_a4_window's fill never touched them, and they go through the PDF's 35 %
threshold as a line of black specks.  In the raw the spot is the torn edge beside the bed, with no mark on paper.
p130 passes the marks gate at +4903+6727; p132 does not, but carries the same line.

What this does: OVERRIDE.  Inside each named strip, every component darker than lum 153, grown by 2 px, is replaced by
the paper mirrored across the strip's inner edge.  Nothing else is written.  It refuses a strip whose component reaches
the inner edge, and a source pixel darker than 153: either means something other than fringe is there.  Strips are the
residue's own extent from <tmp>/marks_work/edge_residue.txt, with a margin.  The other 13 pages of that table are below
the gate and stay as they are (reviewed/marks.txt).

r005_a4_window.py has no per-page mode and rewrites these pages and their stamps on every run; check_a4600_overrides.py
then reads RED; re-run this script.  It refuses a page that already carries the OVERRIDE, and keeps the automatic cut
under <tmp>/recovery/, or under <output>/recovery/ when an output directory is given.
"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin
from scipy import ndimage as ND
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r000_issue
Image.MAX_IMAGE_PIXELS = None
STRIPS = {130: [(4878, 6550, 4961, 6945)],                            # x0 y0 x1 y1, a4600 px; x0 is the inner edge
          132: [(4878, 231, 4961, 453), (4911, 3516, 4961, 3652)]}
DARK, GROW = 153, 2
iss = r000_issue.load(r000_issue.ISSUE)
A = Path(iss.tmp) / "a4600"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else A
R = OUT / "recovery" if len(sys.argv) > 1 else Path(iss.tmp) / "recovery"
OUT.mkdir(parents=True, exist_ok=True)
R.mkdir(exist_ok=True)
for p in STRIPS:                                                      # all or nothing
    t = OUT / f"{p:03d}.stamp.txt"
    if "OVERRIDE" in (t if t.exists() else A / t.name).read_text():
        sys.exit(f"{p:03d} already carries the OVERRIDE; nothing done")
done = {}
for p, strips in STRIPS.items():                                      # measure every page before writing any
    n = f"{p:03d}"
    im = Image.open(A / f"{n}.png")
    a = np.array(im.convert("RGB"))
    lum = a @ np.array([.2126, .7152, .0722])
    total = 0
    for x0, y0, x1, y1 in strips:
        dark = lum[y0:y1, x0:x1] < DARK
        lab, _ = ND.label(dark, structure=np.ones((3, 3)))
        if lab[:, 0].any():
            sys.exit(f"{n}: a dark component reaches the inner edge of strip x={x0}; nothing written")
        m = ND.binary_dilation(dark, iterations=GROW)
        m[:, 0] = False
        ys, xs = np.nonzero(m)
        ys, xs = ys + y0, xs + x0
        sx = 2 * x0 - xs
        if (lum[ys, sx] < DARK).any():
            sys.exit(f"{n}: the mirror of strip x={x0} lands on something dark; nothing written")
        a[ys, xs] = a[ys, sx]
        total += len(ys)
    done[p] = (a, im.info, total, len(strips))
for p, (a, info, total, k) in done.items():
    n = f"{p:03d}"
    st = (A / f"{n}.stamp.txt").read_text()
    shutil.copy(A / f"{n}.png", R / f"{n}.auto.png")
    shutil.copy(A / f"{n}.stamp.txt", R / f"{n}.auto.stamp.txt")
    note = (f"  OVERRIDE repair: torn-edge fringe mirrored out of {k} strip(s) on the fore edge, {total} px; "
            f"issues/{iss.id}/reviewed/repair_edges.py\n")
    meta = PngImagePlugin.PngInfo()
    for key, v in info.items():
        if isinstance(v, str):
            meta.add_text(key, v + ("\n" + note if key == "r005b" else ""))
    Image.fromarray(a).save(OUT / f"{n}.png", dpi=info.get("dpi", (600, 600)), pnginfo=meta)
    (OUT / f"{n}.stamp.txt").write_text(st.rstrip("\n") + "\n" + note)
    print(f"{n}: {total} px mirrored in {k} strip(s) -> {OUT}")
