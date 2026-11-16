#!/usr/bin/env python3
"""p023's delivered page, its edges repaired: the scanner bed and the torn fringe mirrored out.  Run with ISSUE=SH10.

What is wrong, and why it is ours: regrade_023.py graded p023 on a hand-traced box (x 7..4975 in sheets600) and keeps
EVERYTHING inside it, by design -- a dark bleed joined to the bed at the gutter is not whitened, which is what saved
the ad's gutter-bleed photo.  So on the rows the photo does not reach, the bed and the torn paper fringe lie inside the
box, and r005_a4_window cut them into a4600 as they were.  The marks census measured it on the trial PDF: a dark
neutral run from the gutter edge on 59 % of lines, median 0.51 mm (reviewed/a4600-overrides.txt, the `pending` line).
The same box also leaves a bed wedge along the lower fore edge (to 15 px) and the left part of the foot (to 9 px).

What this does: OVERRIDE, in a4600 only (masters600 and sheets600 are not touched).  Nothing moves; the window stands.
  gutter  per row, the strip is the run from x 0 of bed (dark) and fringe (the torn paper: light and blue-cast,
          B-R >= 12, which holds for 85 % of the strip's mid-tones and <= 6 % of the halftone's), bridged over gaps of
          <= 2 px and ended at its rightmost FRINGE pixel: dark beyond the fringe is print (the bleed photo and the
          black headline are as dark and as neutral as the bed; the fringe is what separates them).  The bed seen
          through the tear behind the fringe joins the strip: up to the last very dark pixel (L <= 15, darker than
          99.9 % of the photo's dark pixels) within 10 px of the fringe, then on through L < 30.  Where clean paper
          (L >= 240, B-R <= 4) or the red ink at full strength (B-R <= -90) begins within 25 px beyond that -- 4 px
          in a row and 80 % of the next 12, which a halftone never is -- the strip runs to it: beside the red and the
          paper the fringe is too neutral for the blue-cast test, and the page itself says where it starts.  Outliers are clamped to the
          running median (41 rows) + 8 px (a loose fibre lying on the photo at y ~3000 is not the edge), then the
          strip is widened by 1 px and 2 rows.
  foot    per column, the run of dark pixels (L < 100) up from the last row, at most 20 px, taken only where paper
  fore    (L > 235) follows within 4 px, the grey transition and the cut's shadow included; per row the same from the
          right edge.  Both edges are clean cuts on white paper here.
Every strip pixel is replaced by its mirror image across the strip's inner edge (SH09 recover_031.py's method),
folded back every 10 px so that the fill is taken from the page's first 10 px only, so the printed bleed continues
into the strip and no pixel inside the page changes.

r005_a4_window.py rewrites a4600/023.png and its stamp on every run that names page 23; check_a4600_overrides.py (in
issues/SH09/reviewed/, run with ISSUE=SH10) then reads RED; re-run this script.  It refuses a page that already carries
the OVERRIDE, and keeps the cut it replaces under <tmp>/recovery/023.edge/.  After it runs, page 23's PDF caches are
stale (r006 "RE-CUTTING A PAGE MEANS RE-OCR'ING IT").
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
if iss.id != "SH10":
    sys.exit(f"this script is SH10's p023 only, not {iss.id}")
A = Path(iss.tmp) / "a4600"
R = Path(iss.tmp) / "recovery" / "023.edge"
TAG = "OVERRIDE edge"
st = (A / "023.stamp.txt").read_text()
if "OVERRIDE" in st:
    sys.exit("023 already carries the OVERRIDE; nothing done")

XMAX, CAP, K = 48, 20, 10


def fold(d):
    """distance d into the strip -> distance into the page: mirrored, and mirrored again every K px, so the fill
    comes from the page's first K px only (a plain mirror of a 40 px strip reaches 40 px in and drags the far side of a
    letter's counter into the strip)"""
    d = d % (2 * K)
    return np.where(d < K, d, 2 * K - 1 - d)


def gutter(a):
    """per row: width of the bed + fringe strip at x 0"""
    s = a[:, :XMAX + 16].astype(int)
    L, BR = s.mean(2), s[..., 2] - s[..., 0]
    fringe = (BR >= 12) & (L >= 60) & (L <= 245)
    edgey = (L < 90) | fringe
    vdark = L <= 15
    page = ((L >= 240) & (BR <= 4)) | (BR <= -90)      # clean paper, or the red ink at full strength
    e = np.zeros(len(s), int)
    for y in range(len(s)):
        last, gap = -1, 0
        for x in range(XMAX):
            if edgey[y, x]:
                last, gap = x, 0
            else:
                gap += 1
                if gap > 2:
                    break
        if last < 0 and page[y, 0]:
            continue                 # the page starts at x 0
        fr = np.nonzero(fringe[y, :last + 1])[0]
        if last < 0:
            pass                     # a pale fringe at x 0: only the page rule below can end it
        elif fr.size:
            x = fr[-1] + 1
            vd = np.nonzero(vdark[y, x:min(x + 10, XMAX)])[0]
            if vd.size:
                x += vd[-1] + 1
                while x < XMAX and L[y, x] < 30:
                    x += 1
            e[y] = x
        elif last + 1 < XMAX:
            e[y] = last + 1          # bed alone, ended on the page
        # where the page beside the strip is paper or the red headline, the page says where it starts
        for x in range(e[y] + 1, min(e[y] + 26, XMAX)):
            if page[y, x:x + 4].all() and page[y, x:x + 12].mean() >= 0.8:
                e[y] = x
                break
    e = np.minimum(e, ND.median_filter(e, 41, mode="nearest") + 8)
    e = np.where(e > 0, e + 1, 0)
    return np.minimum(ND.maximum_filter1d(e, 5), XMAX)


def border_run(L):
    """per line (rows of L, run from the LAST column): dark run (L < 100), <= CAP, taken only where paper (L > 235)
    follows within 4 px; the grey transition up to that paper pixel joins the run"""
    v = L[:, ::-1][:, :CAP + 5]
    d = v[:, :CAP + 1] < 100
    run = np.argmin(d, axis=1)
    run[d.all(1)] = 0
    out = np.zeros(len(L), int)
    for i in np.nonzero(run)[0]:
        p = np.nonzero(v[i, run[i]:run[i] + 5] > 235)[0]
        if p.size:
            out[i] = run[i] + p[0]
    return out


im = Image.open(A / "023.png")
info = im.info
a = np.array(im.convert("RGB"))
h, w, _ = a.shape
src = a.copy()
mask = np.zeros((h, w), bool)
e = gutter(src)
for y in np.nonzero(e)[0]:
    x = np.arange(e[y])
    a[y, x] = src[y, e[y] + fold(e[y] - 1 - x)]
    mask[y, x] = True
b = border_run(a.mean(2).T)               # per column, up from the foot
for x in np.nonzero(b)[0]:
    y = np.arange(h - b[x], h)
    a[y, x] = a[h - b[x] - 1 - fold(y - (h - b[x])), x]
    mask[y, x] = True
r = border_run(a.mean(2))                 # per row, in from the fore edge
for y in np.nonzero(r)[0]:
    x = np.arange(w - r[y], w)
    a[y, x] = a[y, w - r[y] - 1 - fold(x - (w - r[y]))]
    mask[y, x] = True

R.mkdir(parents=True, exist_ok=True)
shutil.copy2(A / "023.png", R / "023.auto.png")
shutil.copy2(A / "023.stamp.txt", R / "023.auto.stamp.txt")
np.savez_compressed(R / "023.strips.npz", gutter=e, foot=b, fore=r)
frac = 100 * mask.sum() / (h * w)
note = (f"  {TAG}: bed and torn fringe mirrored out at the page edges, {frac:.3f}% of the page -- gutter "
        f"{int((e > 0).sum())} of {h} rows (median {int(np.median(e[e > 0]))} px, max {e.max()}), foot "
        f"{int((b > 0).sum())} columns (max {b.max()}), fore edge {int((r > 0).sum())} rows (max {r.max()}); "
        f"regrade_023.py's hand box keeps the bed by design; issues/{iss.id}/reviewed/repair_edge_023.py\n")
meta = PngImagePlugin.PngInfo()
for k, v in info.items():
    if isinstance(v, str):
        meta.add_text(k, v.rstrip("\n") + ("\n" + note if k == "r005b" else ""))
Image.fromarray(a).save(A / "023.png", dpi=info.get("dpi", (600, 600)), pnginfo=meta)
(A / "023.stamp.txt").write_text(st.rstrip("\n") + "\n" + note)
print(note.strip())
