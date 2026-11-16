"""The FRONT cover, page 001, levelled on its print in masters600 AND a4600.  Run with ISSUE=SH10.

What failed: r005_masters_sheet read `skew +0.00 -> +0.00` on this full-bleed cover; its skew mask saw ink 3, filled
1.17 % -- it measured nothing (the same blindness as p168, the other half of this A3 wrapper sheet).  The owner, on
the first title source: "title is very much skewed".  Measured on a4600/001 on two printed straights, skew_score
swept in 0.02 deg steps on the straight's own band: the thin rule under "SONDERHEFT 10 ... DM 14,-" +0.58 deg
(peak 19.8, top three 0.56-0.60) and the photo frame's top border +0.54 deg (peak 28.4, top three 0.52-0.56);
whole-page red-channel rows +0.54, cols +0.42.  -> +0.56 deg (the mean of the two straights).  The sheet's trim
(r005 edges L +0.00 R -0.34 T +0.57 B -0.65) disagrees with the print, as on p168: the wrapper sheet is ~0.5 deg out
of square and the chain levels on the PRINT (control).  Shape: issues/SH10/reviewed/level_168.py.

OVERRIDE: one rotation, the page-box centre as pivot in both files (pivot in a4600 = page centre minus the window's
offset in the master), reflecting at the box edge.  Originals under <tmp>/recovery/.  Refuses a page already
carrying the OVERRIDE.  After it: check the four corners of the A4 window for exposed bed; re-make
<tmp>/title_source_150.png from the levelled a4600/001; re-run 010/020 for 001 is not needed (cover, no article).
A later r005/r005b run over 001 undoes this -- re-run the script.
"""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import r000_issue
Image.MAX_IMAGE_PIXELS = None
P, ANG = 1, +0.56
iss = r000_issue.load(r000_issue.ISSUE)
tmp = Path(iss.tmp)
M, A, B = tmp / "masters600", tmp / "a4600", tmp / "recovery"
B.mkdir(exist_ok=True)

def rot(a, ang, pivot):
    return cv2.warpAffine(a, cv2.getRotationMatrix2D(pivot, ang, 1), (a.shape[1], a.shape[0]),
                          flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def save(path, arr, im, stamp_old, note, key):
    txt = stamp_old.rstrip("\n") + "\n" + note + "\n"
    meta = PngImagePlugin.PngInfo()
    meta.add_text(key, txt)
    Image.fromarray(arr).save(path, dpi=im.info.get("dpi", (600, 600)), pnginfo=meta)
    path.with_suffix(".stamp.txt").write_text(txt)

n = f"{P:03d}"
sm, sa = (M / f"{n}.stamp.txt").read_text(), (A / f"{n}.stamp.txt").read_text()
if "OVERRIDE" in sm or "OVERRIDE" in sa:
    sys.exit(f"{n} already carries the OVERRIDE; nothing done")
for d, tag in ((M, "master"), (A, "a4")):
    shutil.copy(d / f"{n}.png", B / f"{n}.{tag}.png")
    shutil.copy(d / f"{n}.stamp.txt", B / f"{n}.{tag}.stamp.txt")
pw, ph = (int(v) for v in re.search(r"^page-px\s+(\d+) (\d+)$", sm, re.M).groups())
x0, y0 = (int(v) for v in re.search(r"^\s+(-?\d+) (-?\d+) \d+ \d+\s+in the master", sa, re.M).groups())
note = (f"override     OVERRIDE levelled on the print: {ANG:+.2f} deg (the top rule and the photo frame); 005 read 0.00, ink 3 "
        f"filled 1.17 %; issues/{iss.id}/reviewed/level_001.py")
im = Image.open(M / f"{n}.png")
a = np.array(im.convert("RGB"))
a[:ph, :pw] = rot(np.ascontiguousarray(a[:ph, :pw]), ANG, (pw / 2, ph / 2))
save(M / f"{n}.png", a, im, sm, note, "r005")
im = Image.open(A / f"{n}.png")
a = rot(np.array(im.convert("RGB")), ANG, (pw / 2 - x0, ph / 2 - y0))
save(A / f"{n}.png", a, im, sa, "  " + note, "r005b")
print(n, f"{ANG:+.2f}", "pivot a4", (pw / 2 - x0, ph / 2 - y0))
