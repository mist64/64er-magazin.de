#!/usr/bin/env python3
"""Build ONE audit sheet from already-renumbered NNN.png pages: every page's
bottom folio-strip, in filename order, labelled (yellow box, red text) with the
FILENAME page number. Eyeball it: where the printed folio != the label, the page
numbering/order is wrong there.

Unlike make_audit.py this does NOT do saddle-stitch imposition — it assumes the
files are already in logical page order (NNN.png). Pages are upright portrait,
so no rotation.

Usage:
  make_folio_montage.py [--src DIR] [--out FILE] [--cols N] [--height PCT]

  --src     dir of NNN.png (150-dpi thumbs ideal; folio legible). Default: thumbs
  --out     output image. Default: folio_audit.png
  --cols    montage columns. Default: 2
  --height  strip height as %% of page (taller = more above the folio). Default: 10
"""
import os, sys, glob, subprocess, tempfile, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="thumbs")
ap.add_argument("--out", default="folio_audit.png")
ap.add_argument("--cols", type=int, default=2)
ap.add_argument("--height", type=int, default=10)
a = ap.parse_args()

pages = sorted(glob.glob(os.path.join(a.src, "[0-9][0-9][0-9].png")))
if not pages:
    sys.exit(f"no NNN.png under {a.src}")

tmp = tempfile.mkdtemp(prefix="folio_")
strips = []
print(f"building {len(pages)} strips from {a.src}...")
for i, f in enumerate(pages):
    pid = os.path.splitext(os.path.basename(f))[0]
    sp = os.path.join(tmp, f"{pid}.png")
    # labels in the center gutter: left column (even index) on the East, right on the West
    side = "East" if i % a.cols == 0 else "West"
    # bottom folio strip, scale to common width, splice yellow label box with filename page#
    subprocess.run(
        f'magick "{f}" -gravity South -crop 100%x{a.height}%+0+0 +repage '
        f'-gravity Center -crop 100%x50%+0+0 +repage -resize 760x '
        f'-gravity {side} -background "#fff3a0" -splice 84x0 '
        f'-pointsize 30 -fill red -annotate +5+0 "{pid}" '
        f'-bordercolor gray -border 1 "{sp}"', shell=True)
    strips.append(sp)

print(f"montaging -> {a.out} ({a.cols} cols)")
subprocess.run(["montage", *strips, "-tile", f"{a.cols}x", "-geometry", "+2+2",
                "-background", "white", a.out])
sz = subprocess.run(f'identify -format "%wx%h" "{a.out}"', shell=True,
                    capture_output=True, text=True)
print(f"done: {a.out}  {sz.stdout}")
