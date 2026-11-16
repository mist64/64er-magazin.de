#!/usr/bin/env python3
"""The bound-in Zahlkarte, pages 166 and 168 (measured and first built as 164 and 166; the owner moved the four
card leaves to the end on 2026-11-15, old 163-166 -> 165-168, so every page number in the measurements below is the
OLD one: old 164 = today's 166, old 166 = today's 168), levelled on its print in masters600 AND a4600.  Run with ISSUE=SH10.

What failed: r005_masters_sheet levels on the skew of the type with a dark-ink mask.  These cards are printed in
CYAN ONLY, so lum < 90/130 sees 0.0 % ink and the step measured nothing: it left all four cards at -0.02 deg.
Measured on the CARD BOX in masters600, on the RED channel (R < 120, where cyan ink is dark), 5 mm inside the box,
skew_score swept -1..+1 deg in 0.04 deg steps, both orientations (tmp/card_sweep.out):
    163  rows +0.00  cols +0.08 (peak 11.9)   -> within 0.1, NOT touched
    164  rows +0.32 (peak 6.7)  cols +0.28    -> +0.30
    165  rows +0.00  cols +0.00 (peak 23.7)   -> NOT touched
    166  rows +0.20 (peak 5.3)  cols +0.20    -> +0.20
Check 3 of r005 read the same: 164 +0.32, 166 +0.18.  Override approved by control for 164 and 166 only.
Shape follows issues/SH09/reviewed/level_cards.py (cv2's positive angle equals measure_skew's reading).

What this does: OVERRIDE.  One rotation per page, one angle, reflecting at the box edge.  Pivot: the card-box
centre in masters600, the image centre in a4600 (the unified card window, padded 0-16 px, so the two pivots differ by
under 0.1 px of rotation offset at these angles).  sheets600 and cmyk2400 are not touched.  Originals kept under
<tmp>/recovery/.  Refuses a page that already carries the OVERRIDE.  After it: re-run 010 (and 020) for 166, 168;
re-run r005 check 3 on them.  A later r005 or r005b run over these pages undoes this -- re-run the script.
"""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/img/scan2ocr/rules"))
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import r000_issue
Image.MAX_IMAGE_PIXELS = None
ANGLES = {166: (+0.30, "horizontal, red channel"), 168: (+0.20, "horizontal, red channel")}   # were 164, 166 before the 2026-11-15 reorder
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
    note = (f"override     OVERRIDE levelled on the print: {ang:+.2f} deg ({orient}); 005 measured nothing on "
            f"this cyan-only card; issues/{iss.id}/reviewed/level_cards.py")
    im = Image.open(M / f"{n}.png")
    a = np.array(im.convert("RGB"))
    a[:ph, :pw] = rot(np.ascontiguousarray(a[:ph, :pw]), ang, (pw / 2, ph / 2))
    save(M / f"{n}.png", a, im, sm, note, "r005")
    im = Image.open(A / f"{n}.png")
    a = np.array(im.convert("RGB"))
    a = rot(a, ang, (a.shape[1] / 2, a.shape[0] / 2))
    save(A / f"{n}.png", a, im, sa, "  " + note, "r005b")
    print(n, f"{ang:+.2f} {orient}")
