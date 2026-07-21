#!/usr/bin/env python3
"""Build ONE audit sheet: every scan's bottom folio-strip, in logical page order,
labelled with the ASSUMED page number (from the renumber.py saddle-stitch imposition).
Eyeball it: where the printed folio != the red label, the page order is wrong there.

Usage:
  make_audit.py [--src DIR] [--out FILE] [--cols N] [--pages TOTAL]

  --src    dir of Scan*.tiff (Scan.tiff = first slot). Default: thumbs
  --out    output image. Default: audit_sheet.png
  --cols   montage columns. Default: 4
  --pages  total page count for the imposition. Default: file count (must be %4==0)

Works on the 150-dpi thumbs (fast) or the full scans — folio is legible either way.
"""
import os, sys, re, glob, subprocess, tempfile, argparse

def rmap(count):
    """renumber.py: scan-slot src -> logical page, for a complete nested booklet."""
    src=0; a=count; b=1; mid=a/2; which=0; m={}
    while True:
        if which==0:
            m[src]=a
            if a%2==0: which=1
            a-=1
        else:
            m[src]=b
            if b%2==0: which=0
            b+=1
        if a<mid+1 or b>mid+1: break
        src+=1
    return m

def scan_file(src_dir, idx):
    base = "Scan" if idx==0 else f"Scan {idx}"
    for ext in (".tiff", ".png", ".tif", ".jpg"):
        p = os.path.join(src_dir, base + ext)
        if os.path.exists(p):
            return p
    return os.path.join(src_dir, base + ".tiff")   # default (for the missing-slot message)

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="thumbs")
ap.add_argument("--out", default="audit_sheet.png")
ap.add_argument("--cols", type=int, default=2)
ap.add_argument("--height", type=int, default=10, help="strip height as %% of page (taller = more above the folio)")
ap.add_argument("--rotate", type=int, default=-90,
                help="degrees to rotate each source upright before cropping the bottom strip. "
                     "Use -90 for raw landscape scans (default), 0 for thumbs already rotated upright.")
ap.add_argument("--pages", type=int, default=0)
a = ap.parse_args()

n_files = sum(len(glob.glob(os.path.join(a.src, "Scan*"+e)))
              for e in (".tiff", ".png", ".tif", ".jpg"))
count = a.pages or n_files
if count % 4:
    sys.exit(f"page count {count} not divisible by 4 (files found: {n_files}); pass --pages")

M = rmap(count)                       # src -> page
order = sorted(M.items(), key=lambda kv: kv[1])   # by logical page

tmp = tempfile.mkdtemp(prefix="audit_")
strips = []
print(f"building {len(order)} strips from {a.src} (count={count})...")
for i, (src, page) in enumerate(order):
    # montage tiles left-to-right: even index -> left column, odd -> right column.
    # put labels in the center gutter: left column labelled on the East, right on the West.
    side = "East" if i % a.cols == 0 else "West"
    f = scan_file(a.src, src)
    if not os.path.exists(f):
        # missing scan slot -> red placeholder strip
        sp = os.path.join(tmp, f"{page:03d}.png")
        subprocess.run(f'magick -size 760x34 xc:"#ffdddd" -gravity {side} '
                       f'-pointsize 22 -fill red -annotate +6+0 "{page:03d}  (no scan {src})" '
                       f'-bordercolor gray -border 1 "{sp}"', shell=True)
        strips.append(sp); continue
    sp = os.path.join(tmp, f"{page:03d}.png")
    # rotate upright, bottom folio strip, scale, splice a yellow label box (gutter side) with the assumed page#
    subprocess.run(
        f'magick "{f}" -rotate {a.rotate} -gravity South -crop 100%x{a.height}%+0+0 +repage '
        f'-gravity Center -crop 100%x50%+0+0 +repage -resize 760x '
        f'-gravity {side} -background "#fff3a0" -splice 84x0 '
        f'-pointsize 30 -fill red -annotate +5+0 "{page:03d}" '
        f'-bordercolor gray -border 1 "{sp}"', shell=True)
    strips.append(sp)

print(f"montaging -> {a.out} ({a.cols} cols)")
subprocess.run(["montage", *strips, "-tile", f"{a.cols}x", "-geometry", "+2+2",
                "-background", "white", a.out])
sz = subprocess.run(f'identify -format "%wx%h" "{a.out}"', shell=True, capture_output=True, text=True)
print(f"done: {a.out}  {sz.stdout}")
