#!/usr/bin/env python3
"""The back cover, page 164 (scanned and first built as 168; renumbered 2026-11-15 when the owner moved the four
Zahlkarte leaves to the end -- the measurements below were taken under the OLD numbers: "a4600/168" is this page,
"167" is today's 163), levelled on its print in masters600 AND a4600.  Run with ISSUE=SH10.

What failed: r005_masters_sheet read `skew +0.00 -> +0.00` on this full-bleed colour ad; its rows skew score peaks at
1.47, i.e. it measured nothing.  The leaf itself is level on the scan (traced edges T +0.05 B +0.07), but the PRINT
sits crooked on it.  Measured on a4600/168 on the ad's light-blue frame rule (B-R > 60, B > 180):
left edge 10.20 -> 8.64 mm and right 198.46 -> 196.51 mm over y 30-270 mm (0.37, 0.47 deg); top 9.36 -> 10.75 mm and
bottom 287.27 -> 288.12 mm over x 30-170 mm (0.57, 0.35 deg) -- all four turn the same way, a rotation, not a keystone.
skew_score on the frame mask, 0.02 deg steps: cols +0.44 (peak 9.1), rows +0.56 (peak 5.2); r005 check 3 rot90 +0.46.
-> +0.44 deg.  The other side of the leaf, 167, is the mirror case (print level, leaf edges T +0.54 B +0.58) and is NOT
touched: one sheet printed or trimmed ~0.5 deg out of square.  Approved by control (levelling is presentation; the chain
levels on the print).  Shape: issues/SH10/reviewed/level_cards.py.

OVERRIDE: one rotation, the page-box centre as pivot in both files (the a4 window is `0 0 4961 7016 in the master`),
reflecting at the box edge.  Originals under <tmp>/recovery/.  Refuses a page already carrying the OVERRIDE.
After it: re-run 010 (and 020) for 164.  A later r005/r005b run over 164 undoes this -- re-run the script.
"""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import r000_issue
Image.MAX_IMAGE_PIXELS = None
P, ANG = 164, +0.44   # was 168 before the 2026-11-15 reorder
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
note = (f"override     OVERRIDE levelled on the print: {ANG:+.2f} deg (the ad's frame rule); 005 read 0.00 at "
        f"peak 1.47; issues/{iss.id}/reviewed/level_164.py")
im = Image.open(M / f"{n}.png")
a = np.array(im.convert("RGB"))
a[:ph, :pw] = rot(np.ascontiguousarray(a[:ph, :pw]), ANG, (pw / 2, ph / 2))
save(M / f"{n}.png", a, im, sm, note, "r005")
im = Image.open(A / f"{n}.png")
a = rot(np.array(im.convert("RGB")), ANG, (pw / 2 - x0, ph / 2 - y0))
save(A / f"{n}.png", a, im, sa, "  " + note, "r005b")
print(n, f"{ANG:+.2f}", "pivot a4", (pw / 2 - x0, ph / 2 - y0))
