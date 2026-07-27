#!/usr/bin/env python3
"""Page-skew estimation — Method A (projection-variance), the validated production method.

Estimate the rotation needed to level a scanned magazine page. Detect on a small (150-dpi)
thumbnail; the angle is scale-invariant, so apply the SAME angle to the full-res master.

Method: binarize (text=ink), sweep candidate angles, rotate, project onto rows, and score the
"peakiness" of the row profile (sum of squared row-to-row differences). Horizontal text lines ->
sharp peaks/valleys -> high score. The maximizing angle is the correction.

Convention: returned angle = correction to LEVEL the page, POSITIVE = counter-clockwise ("left"),
as measured with scipy.ndimage.rotate.

!!! SIGN GOTCHA when APPLYING (see NOTES.md): scipy.ndimage.rotate (used here to MEASURE) and
PIL Image.rotate rotate in OPPOSITE visual directions. Verify residual skew ~0 after applying;
do not trust the sign by reasoning alone.

CLI:  deskew.py THUMB.png [THUMB2.png ...]
API:  estimate_skew(path_or_gray_array) -> (angle_deg, confidence)
"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import rotate

Image.MAX_IMAGE_PIXELS = None

# proven config (tools/img/deskew/NOTES.md): two-stage coarse -> fine
COARSE = (-3.0, 3.0, 0.2)
FINE_HALF, FINE_STEP = 0.3, 0.02
# body-text crop (drop masthead bar / footer / side margins so only body text drives it)
MARGIN = dict(top=0.06, bottom=0.05, side=0.04)
BIN_K = 0.4  # ink threshold = mean - BIN_K*std


def _binarize(a):
    return (a < a.mean() - BIN_K * a.std()).astype(np.float32)


def _score(b, ang):
    r = rotate(b, ang, reshape=False, order=0, mode="constant", cval=0.0)
    return float(np.sum(np.diff(r.sum(axis=1)) ** 2))


def estimate_skew(src):
    """src: path to a (thumbnail) image, or a 2-D grayscale float array.
    Returns (angle_deg, confidence). confidence = peak/median of the fine sweep."""
    if isinstance(src, (str, bytes)):
        a = np.asarray(Image.open(src).convert("L"), dtype=np.float32)
    else:
        a = np.asarray(src, dtype=np.float32)
    H, W = a.shape
    a = a[int(MARGIN["top"] * H):int((1 - MARGIN["bottom"]) * H),
          int(MARGIN["side"] * W):int((1 - MARGIN["side"]) * W)]
    b = _binarize(a)
    lo, hi, st = COARSE
    angs = np.arange(lo, hi + 1e-9, st)
    sc = np.array([_score(b, x) for x in angs])
    c = angs[int(sc.argmax())]
    f = np.arange(c - FINE_HALF, c + FINE_HALF + 1e-9, FINE_STEP)
    fs = np.array([_score(b, x) for x in f])
    best = float(f[int(fs.argmax())])
    conf = float(fs.max() / np.median(fs))
    return best, conf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: deskew.py THUMB.png [...]")
    for p in sys.argv[1:]:
        ang, conf = estimate_skew(p)
        d = "left/CCW" if ang > 0 else ("right/CW" if ang < 0 else "none")
        print(f"{p}: {ang:+.3f} deg ({d})  confidence={conf:.1f}")
