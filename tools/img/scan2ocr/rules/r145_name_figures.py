"""Write the figures the judge kept, named and sorted for conversion.

Naming follows what the repo already uses, verified against issue 8608: the
major number is the ARTICLE's START PAGE, never the page the picture sits on, so
a photo on p42 belonging to the article that starts on p41 is `41-2.png`.  Step
150 maps images to articles by exactly that number.

  <start>-<n>.png     n is the printed caption number: "Bild 3" -> 3
  <start>-0.png       an opening/title photograph, which has no caption
  <start>-00.png      ...and the next one, when -0 is taken
  <start>-t<n>.png    a table so complex it has to stay an image

Files land in png/<type>/ so tools/convert-scans.sh can do the rest: colour and
greyscale get scaled to 150 dpi, black-on-white is thresholded at 600, and a
screened halftone is descreened before thresholding.
"""
import json
import os
import shutil
import sys

import r010_ocr_blocks as OB

OUT = os.path.join(OB.OUT_DIR, "figures")
DEST = os.path.join(OB.OUT_DIR, "figures", "png")
ARTICLES = os.path.join(os.path.dirname(OB.OUT_DIR), "articles.json")
TYPES = ("c", "gray", "bw", "dots")


def article_start(page, arts):
    """The start page of the article this page belongs to."""
    best = None
    for a in arts:
        if page in a["pages"]:
            s = min(a["pages"])
            if best is None or s > best:
                best = s           # the latest article that covers it
    return best if best is not None else page


def main():
    arts = json.load(open(ARTICLES, encoding="utf-8"))
    for t in TYPES:
        os.makedirs(f"{DEST}/{t}", exist_ok=True)
    used, rows = {}, []
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".judged.json"):
            continue
        page = int(f[1:4])
        judged = json.load(open(f"{OUT}/{f}"))
        cands = json.load(open(f"{OUT}/p{page:03d}.json"))
        start = article_start(page, arts)
        for idx, v in sorted(judged.get("figures", {}).items(), key=lambda kv: int(kv[0])):
            if not v.get("figure"):
                continue
            i = int(idx)
            if i >= len(cands):
                continue
            num = str(v.get("number", "0"))
            if num in ("0", "", "None"):
                # -0, then -00, then -000: the convention for uncaptioned opener
                n = used.get((start, "0"), 0)
                used[(start, "0")] = n + 1
                num = "0" * (n + 1)
            typ = v.get("convert") or cands[i]["type"]
            if typ not in TYPES:
                typ = cands[i]["type"]
            # Two figures can claim the same number -- two pages of one article
            # each printing a "Bild 1", or an OCR misread.  The repo already has
            # a form for this (`145-9a.png`), so disambiguate with a letter
            # rather than silently overwriting one of them.
            base = f"{start}-{num}"
            if base in used:
                used[base] += 1
                base = f"{base}{chr(ord('a') + used[base] - 1)}"
            else:
                used[base] = 1
            name = f"{base}.png"
            src = f"{OUT}/crops/p{page:03d}-{i}-{cands[i]['type']}.png"
            if not os.path.exists(src):
                continue
            shutil.copy(src, f"{DEST}/{typ}/{name}")
            rows.append({"page": page, "start": start, "name": name, "type": typ,
                         "bbox": cands[i]["bbox"], "caption": v.get("caption")})
    json.dump(rows, open(f"{DEST}/figures.json", "w"), ensure_ascii=False, indent=1)
    per = {t: len(os.listdir(f"{DEST}/{t}")) for t in TYPES}
    print(f"{len(rows)} figures -> {DEST}/  {per}")
    dupes = [r["name"] for r in rows]
    clash = {n for n in dupes if dupes.count(n) > 1}
    if clash:
        print(f"  NAME CLASHES ({len(clash)}): {sorted(clash)[:10]}")


if __name__ == "__main__":
    sys.exit(main())
