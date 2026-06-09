#!/usr/bin/env python3
"""
Verify page order in a cropped CMYK issue by OCRing the page number from
the outer-bottom corner of every page (via macOS Vision through vision_ocr).

Reads <issue>/cropped/NNN_150_cropped.tiff (150-dpi A4 = 1240×1754).
ODD outer = right; EVEN outer = left.

Usage:
  check_page_order.py <issue_cmyk_dir>
"""
import sys, os, glob, re, subprocess, tempfile
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VISION = os.path.join(SCRIPT_DIR, "vision_ocr")

A4_W, A4_H = 1240, 1754
STRIP_TOP  = 1604      # bottom 150 px
STRIP_H    = A4_H - STRIP_TOP

# bbox filters (normalised within the strip; origin bottom-left).
# Outer-corner where the page number sits: y < 0.5 (lower half of strip).
Y_MAX = 0.55
X_INNER_LIMIT = 0.20   # for EVEN: keep x_center < this
X_OUTER_LIMIT = 0.80   # for ODD : keep x_center > this


def ocr_strip(png_path):
    """Run swift vision_ocr; yield (xc, yc, text) for each result."""
    out = subprocess.run([VISION, png_path], capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if "\t" not in line:
            continue
        bb, text = line.split("\t", 1)
        x, y, w, h = map(float, bb.split())
        yield (x + w / 2, y + h / 2, text.strip())


def detect_page_number(strip_path, odd):
    """Return integer page number or None."""
    candidates = []
    for xc, yc, text in ocr_strip(strip_path):
        if yc > Y_MAX:
            continue
        if odd and xc < X_OUTER_LIMIT:
            continue
        if (not odd) and xc > X_INNER_LIMIT:
            continue
        m = re.fullmatch(r"\d+", text)
        if m:
            candidates.append((xc if odd else -xc, int(text)))
    if not candidates:
        return None
    # pick the most outer (largest |x| from center)
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    issue = sys.argv[1].rstrip("/")
    cropped = os.path.join(issue, "cropped")
    paths = sorted(glob.glob(os.path.join(cropped, "[0-9][0-9][0-9]_150_cropped.tiff")))
    if not paths:
        sys.exit(f"no pages under {cropped}")

    tmpdir = tempfile.mkdtemp(prefix="page_check_")
    print(f"strips in {tmpdir}")

    results = []
    for p in paths:
        pid = int(os.path.basename(p)[:3])
        odd = (pid % 2) == 1
        img = Image.open(p)
        strip = img.crop((0, STRIP_TOP, A4_W, A4_H))
        sp = os.path.join(tmpdir, f"{pid:03d}.png")
        strip.save(sp)
        n = detect_page_number(sp, odd)
        results.append((pid, n))
        marker = "" if n is None else f"→ {n}"
        print(f"file {pid:03d} {'odd ' if odd else 'even'} {marker}")

    print("\n=== analysis ===")
    found = [(pid, n) for pid, n in results if n is not None]
    print(f"pages with detected number: {len(found)} / {len(results)}")

    # monotonic check
    breaks = []
    last_pid, last_n = None, None
    for pid, n in results:
        if n is None:
            continue
        if last_n is not None and n <= last_n:
            breaks.append((last_pid, last_n, pid, n))
        last_pid, last_n = pid, n
    if breaks:
        print(f"\nnon-monotonic transitions ({len(breaks)}):")
        for a_pid, a_n, b_pid, b_n in breaks:
            print(f"  file {a_pid:03d}={a_n} → file {b_pid:03d}={b_n}")
    else:
        print("monotonic ✓")

    # gap check among detected numbers
    nums = sorted({n for _, n in found})
    if nums:
        lo, hi = nums[0], nums[-1]
        missing = sorted(set(range(lo, hi + 1)) - set(nums))
        if missing:
            print(f"\nmissing page numbers in range {lo}..{hi} (may be undetected covers/blanks): {missing}")
        else:
            print(f"\nno gaps in {lo}..{hi}")

    # files with no detected number
    undet = [pid for pid, n in results if n is None]
    if undet:
        print(f"\nundetected ({len(undet)}): {undet}")

    # filename vs ocr mismatches
    mismatches = [(pid, n) for pid, n in results if n is not None and n != pid]
    if mismatches:
        print(f"\nfilename≠ocr ({len(mismatches)}):")
        for pid, n in mismatches:
            print(f"  file {pid:03d} → ocr {n}  (delta {n - pid:+d})")
    else:
        print("\nfilename == ocr for every detected page ✓")


if __name__ == "__main__":
    main()
