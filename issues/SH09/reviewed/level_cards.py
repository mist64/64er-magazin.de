#!/usr/bin/env python3
"""The bound-in card, pages 163-166, levelled on its print in masters600 AND a4600.  Run with ISSUE=SH09.

What failed: r005_masters_sheet levels on the skew of the type, measured on the raw thumb with the bed in the ink
mask (r005_masters_sheet.md, KNOWN DEFECT, OPEN -- THE SKEW MASK MUST EXCLUDE THE BED).  The card fills half the frame,
so the step levelled these four on the bed's outline: 163 and 165 were tilted by the step, 164 and 166 kept the tilt
of their placement on the glass.  Every other page of the issue is levelled on its type.

What this does: OVERRIDE.  One rotation per page, one angle, the same physical pivot in both directories, reflecting
at the box edge.  The card's trim is not parallel to its print on every side (it reads about 0.5 deg out of square);
no rotation fixes both, and the chain's convention levels on the type.

Each angle is where the peak of the skew score is highest on the page box, in the orientation named: the orientation
whose peak clears SKEW_PEAK_MIN 6.0 (163, 165 only rot90), or the stronger one (164, 166).
cv2's positive angle equals measure_skew's reading.  sheets600 and cmyk2400 are not touched.

r005_masters_sheet.py or r005_a4_window.py rewrites a page and its stamp, and check_a4600_overrides.py then reads RED;
re-run this script.  It refuses a page that already carries the OVERRIDE, and keeps the originals under <tmp>/recovery/.
After it, re-run 010 for 163-166 and 020 for them.
"""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import r000_issue
Image.MAX_IMAGE_PIXELS = None
ANGLES = {163: (-0.50, "rot90"), 164: (+0.54, "horizontal"), 165: (-0.56, "rot90"), 166: (+0.32, "horizontal")}
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

for p, (ang, orient) in ANGLES.items():
    n = f"{p:03d}"
    sm, sa = (M / f"{n}.stamp.txt").read_text(), (A / f"{n}.stamp.txt").read_text()
    if "OVERRIDE" in sm or "OVERRIDE" in sa:
        sys.exit(f"{n} already carries the OVERRIDE; nothing done for it or later pages")
    for d, tag in ((M, "master"), (A, "a4")):
        shutil.copy(d / f"{n}.png", B / f"{n}.{tag}.png")
        shutil.copy(d / f"{n}.stamp.txt", B / f"{n}.{tag}.stamp.txt")
    pw, ph = (int(v) for v in re.search(r"^page-px\s+(\d+) (\d+)$", sm, re.M).groups())
    x0, y0 = (int(v) for v in re.search(r"^\s+(-?\d+) (-?\d+) \d+ \d+\s+in the master", sa, re.M).groups())
    note = (f"override     OVERRIDE levelled on the print: {ang:+.2f} deg ({orient}), pivot page-box centre; "
            f"005 levelled this card on the bed; issues/{iss.id}/reviewed/level_cards.py")
    im = Image.open(M / f"{n}.png")
    a = np.array(im.convert("RGB"))
    a[:ph, :pw] = rot(a[:ph, :pw], ang, (pw / 2, ph / 2))
    save(M / f"{n}.png", a, im, sm, note, "r005")
    im = Image.open(A / f"{n}.png")
    a = rot(np.array(im.convert("RGB")), ang, (pw / 2 - x0, ph / 2 - y0))
    save(A / f"{n}.png", a, im, sa, "  " + note, "r005b")
    print(n, f"{ang:+.2f} {orient}", "pivot a4", (pw / 2 - x0, ph / 2 - y0))
