#!/usr/bin/env python3
"""
Auto-detect per-page crop widths for book-bound Sonderheft issues
(single A4 pages ripped from a thick perfect-bound magazine),
as opposed to the Klammer-bound issues whose source is A3 sheets folded in two.

Assumptions about the scans:
  - page is always west-aligned in the scan
  - black scanner bg is always on the east, variable width per page
  - ODD pages: fizz/riffle on the WEST (binding/inner). Cut FIZZ_CONST from west.
  - EVEN pages: fizz/riffle on the EAST (binding/inner, adjacent to black bg).
                Cut FIZZ_CONST from the page's east edge.

`widths.txt` value = page width AFTER cutting the inner edge,
                      with the outer edge left alone (in thumb px).

Per-page variable: `east_edge` (col where scanner black bg starts).
Global constant:   FIZZ_CONST.

Run from the issue directory (must contain ./thumbs/NNN.png).
  detect_widths.py                # all pages in cwd
  detect_widths.py 5 6            # only listed pages (appends/updates)
"""
import sys, os, glob, subprocess
from PIL import Image, ImageDraw
import numpy as np

Image.MAX_IMAGE_PIXELS = None  # source PNGs can be 20k×28k


def image_width(path):
    """Read width via `magick identify` (header only, fast on huge PNGs)."""
    out = subprocess.check_output(["magick", "identify", "-format", "%w", path])
    return int(out.strip())

# tunables on the 150-dpi A4-fit thumb (~1230 wide)
EDGE_SKIP        = 2
PAPER_MEAN_MIN   = 90
PAPER_RUN        = 12
TOP_BOTTOM_TRIM  = 0.08
FIZZ_CONST       = 12

# widths.txt unit: pixels of the 150-dpi-resize of the source PNG
# (= src_w / 4 for 600-dpi sources, src_w / 16 for 2400-dpi sources).
# This matches the ALL*.sh family so the cropping step uses it directly.
DPI_RESIZE_THRESH = 10000  # src_w > this → 2400-dpi source (resize 6.25%)


def analyze(thumb_path):
    arr = np.array(Image.open(thumb_path).convert("L"))
    h, w = arr.shape
    band = arr[int(h * TOP_BOTTOM_TRIM): int(h * (1 - TOP_BOTTOM_TRIM))]
    return band.mean(axis=0), w


def find_east_edge(col_mean, w):
    """Walk east → west; return the eastmost col of the first PAPER_RUN-long
       run of paper-bright cols."""
    run = 0
    for i in range(w - 1 - EDGE_SKIP, -1, -1):
        if col_mean[i] >= PAPER_MEAN_MIN:
            run += 1
            if run >= PAPER_RUN:
                return i + (PAPER_RUN - 1)
        else:
            run = 0
    return w - 1


def detect(thumb_path, odd, src_w):
    col_mean, w = analyze(thumb_path)
    east = find_east_edge(col_mean, w)
    if odd:
        x0, x1 = FIZZ_CONST, east
    else:
        x0, x1 = 0, east - FIZZ_CONST
    width_thumb = max(0, x1 - x0 + 1)
    resize_150_w = src_w / (16 if src_w > DPI_RESIZE_THRESH else 4)
    width_150 = round(width_thumb * resize_150_w / w)
    return {"east_edge": east, "x0": x0, "x1": x1,
            "width_thumb": width_thumb, "width_150": width_150,
            "thumb_w": w, "src_w": src_w}


def draw_preview(thumb_path, info, out_path):
    img = Image.open(thumb_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.line([(info["east_edge"], 0), (info["east_edge"], h)], fill=(0, 120, 255), width=2)
    draw.line([(info["x0"], 0), (info["x0"], h)], fill=(255, 0, 0), width=3)
    draw.line([(info["x1"], 0), (info["x1"], h)], fill=(255, 0, 0), width=3)
    img.save(out_path)


def save_cropped_thumb(thumb_path, info, out_path):
    img = Image.open(thumb_path)
    img.crop((info["x0"], 0, info["x1"] + 1, img.size[1])).save(out_path)


def main():
    page_args = [a.zfill(3) for a in sys.argv[1:]]
    issue = os.getcwd()
    thumbs = os.path.join(issue, "thumbs")
    if not os.path.isdir(thumbs):
        sys.exit(f"missing {thumbs} (run from issue dir)")

    preview_dir = os.path.join(issue, "widths_preview")
    os.makedirs(preview_dir, exist_ok=True)
    widths_path = os.path.join(issue, "widths.txt")
    debug_path  = os.path.join(issue, "widths_debug.txt")

    # load existing widths so per-page updates merge
    existing = {}
    if page_args and os.path.isfile(widths_path):
        with open(widths_path) as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    pid, val = line.split(":", 1)
                    existing[pid.strip()] = val.strip()

    targets = sorted(page_args) if page_args else sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(thumbs, "[0-9][0-9][0-9].png"))
    )

    debug_lines = [f"# FIZZ_CONST={FIZZ_CONST} thumb px",
                   "# widths.txt unit: 150-dpi-resize px (src_w/4 for 600 dpi src, src_w/16 for 2400 dpi src)",
                   "# id parity east_edge x0 x1 width_thumb width_150 thumb_w src_w"]
    for pid in targets:
        thumb = os.path.join(thumbs, f"{pid}.png")
        src   = os.path.join(issue, f"{pid}.png")
        if not os.path.isfile(thumb):
            print(f"WARN: missing {thumb}")
            continue
        if not os.path.isfile(src):
            print(f"WARN: missing {src}")
            continue
        odd = (int(pid) % 2) == 1
        src_w = image_width(src)
        info = detect(thumb, odd, src_w)
        existing[pid] = str(info["width_150"])
        debug_lines.append(f"{pid} {'odd' if odd else 'even'} "
                           f"{info['east_edge']} {info['x0']} {info['x1']} "
                           f"{info['width_thumb']} {info['width_150']} "
                           f"{info['thumb_w']} {info['src_w']}")

        draw_preview(thumb, info, os.path.join(preview_dir, f"{pid}.png"))
        save_cropped_thumb(thumb, info, os.path.join(preview_dir, f"{pid}_cropped.png"))
        print(f"{pid} {'odd ' if odd else 'even'}  "
              f"east={info['east_edge']:4d}  cut[{info['x0']:4d}..{info['x1']:4d}]  "
              f"w_thumb={info['width_thumb']:4d}  w_150={info['width_150']:4d}  "
              f"src_w={info['src_w']:5d}")

    with open(widths_path, "w") as f:
        for pid in sorted(existing):
            f.write(f"{pid}: {existing[pid]}\n")
    with open(debug_path, "w") as f:
        f.write("\n".join(debug_lines) + "\n")

    print(f"\nwidths  → {widths_path}  ({len(existing)} pages)")
    print(f"debug   → {debug_path}")
    print(f"preview → {preview_dir}/")


if __name__ == "__main__":
    main()
