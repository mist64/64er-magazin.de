#!/usr/bin/env python3
"""p031's A4 cut, repaired.  Run with ISSUE=SH09.

What failed: r005_masters_sheet traced 149.0 x 297.4 mm (a full-bleed photo at the gutter; the paper mask follows
the photo, no edge found) and published the page as 'uncropped sheet'.  r005_a4_window's logo anchor is right
(score 0.923, window 7 5), but with no trace nothing removed the bed: a hairline on the right and torn-fringe teeth
on the left stayed inside the rigid window, and its summary reads fabricated 0.00 %.

What this does: OVERRIDE.  Right: bed connected to the window border is mirrored out.  Left: on rows where no print
reaches the band, the outer 36 px hold only fringe and paper, so the band is mirrored whole; rows where the photo
bleeds are left alone.  Nothing moves; the window stands.

r005_a4_window.py has no per-page mode and rewrites this page and its stamp on every run.  check_a4600_overrides.py,
beside this file, then reads RED; re-run this script.  It refuses a cut that already carries the OVERRIDE, and it
keeps the automatic cut under <tmp>/recovery/.
"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin
from scipy import ndimage as ND
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import r000_issue
Image.MAX_IMAGE_PIXELS = None
iss = r000_issue.load(r000_issue.ISSUE)
A = Path(iss.tmp) / "a4600"
R = Path(iss.tmp) / "recovery"
st = (A / "031.stamp.txt").read_text()
if "OVERRIDE" in st:
    sys.exit("031 already carries the OVERRIDE; nothing done")
R.mkdir(exist_ok=True)
shutil.copy(A / "031.png", R / "031.auto.png")
shutil.copy(A / "031.stamp.txt", R / "031.auto.stamp.txt")
im = Image.open(A / "031.png")
info = im.info
a = np.array(im.convert("RGB"))
l = a.mean(2)
h, w = l.shape
B, DARK, LB = 24, 110, 36
m = np.zeros_like(l, bool)
m[:, -B:] = l[:, -B:] < DARK
lab, _ = ND.label(m, structure=np.ones((3, 3)))
t = set(lab[:, -1])
t.discard(0)
keep = ND.binary_dilation(np.isin(lab, list(t)), iterations=2)
keep[:, :w - B - 2] = False
ys, xs = np.nonzero(keep)
a[ys, xs] = a[ys, 2 * (w - 1 - (B + 3)) - xs]
right = int(keep.sum())
bleed = ND.binary_dilation((l[:, LB:LB + 30] < 200).mean(1) > .15, iterations=40)
rows = np.nonzero(~bleed)[0]
a[np.ix_(rows, np.arange(LB))] = a[np.ix_(rows, 2 * LB - np.arange(LB))]
left = len(rows) * LB
frac = 100 * (left + right) / (h * w)
note = (f"  OVERRIDE recovery: bed at the window border mirrored out, {frac:.3f}% of the page "
        f"(005 trace failed: uncropped sheet); issues/{iss.id}/reviewed/recover_031.py\n")
meta = PngImagePlugin.PngInfo()
for k, v in info.items():
    if isinstance(v, str):
        meta.add_text(k, v + ("\n" + note if k == "r005b" else ""))
Image.fromarray(a).save(A / "031.png", dpi=info.get("dpi", (600, 600)), pnginfo=meta)
(A / "031.stamp.txt").write_text(st.rstrip("\n") + "\n" + note)
print(f"mirrored {frac:.3f}%: left band {left} px on {len(rows)} rows, right {right} px")
