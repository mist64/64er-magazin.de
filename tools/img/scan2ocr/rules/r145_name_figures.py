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

# A crop whose size repeats on this many different pages is page furniture.
HASH_N = 12               # side of the average-hash grid used to compare crops
FURNITURE_MIN_PAGES = 3   # the same picture on this many pages is a masthead
HASH_MAX_DIFF = 12        # bits of the 144-bit hash two scans of it may differ by


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
            # THE BUCKET IS MEASURED, NOT JUDGED.  Colour and screening are
            # physical facts about the ink: the extractor measures chroma and
            # the halftone at full resolution, while the model sees a
            # downscaled page overlay in which a small photo is a few hundred
            # pixels.  Every bucket error the sixth census found was the model
            # overriding a correct measurement -- 160-2 (a colour photo),
            # 54-2 and 54-4 (black on a yellow tint) all measured "c" and were
            # judged "bw"; 124-1 measured "gray" and was judged "dots".
            typ = cands[i]["type"]
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
                         "bbox": cands[i]["bbox"],
                         # THE CAPTION IS SOURCED, NEVER GENERATED.  It was
                         # taken from the model's reply, and the model reads the
                         # page image -- so where the OCR had missed a caption
                         # printed inside a tint panel it supplied the real text
                         # (p143's "Blockschaltbild eines Matrixdruckers" is
                         # exactly what is printed), and where it could not read
                         # one it supplied a plausible one instead.  On p133 it
                         # produced "Bild 2. Anschlussbelegung des CIA 6526" for
                         # a chip whose printed caption reads "Bild 3. Die
                         # Pinbelegung des CIA 6526": wrong number, wrong words,
                         # and indistinguishable from the real ones downstream.
                         # 7 of 64 captions matched no OCR block on their page.
                         #
                         # A figure index built on invented text is worse than
                         # one with holes in it, because the holes are visible.
                         # The caption now comes from the extractor's own
                         # caption_lines(), which is OCR of the printed line, and
                         # is null when there is none to read.
                         "caption": cands[i].get("caption")})
    # PAGE FURNITURE REPEATS; A FIGURE DOES NOT.
    #
    # The "64'er Test" and "BÜCHER" rubric badges are cut correctly and are not
    # figures -- they are the section masthead, reprinted on every article of
    # that rubric.  Vision called them junk on four separate pages.  Nothing
    # about one crop says so, but the repetition does: near-identical size on
    # several different pages is a masthead, and a real figure never recurs.
    # Compared by CONTENT, not by size.  Size alone is far too coarse -- it
    # threw away p46's abstract artwork and p8's C-FOX screenshot for sharing a
    # size bucket with the badge.  The masthead repeats because it is literally
    # the same picture, so a coarse perceptual hash separates it from figures
    # that merely happen to be similarly sized.
    from collections import defaultdict
    from PIL import Image as _I
    byhash = defaultdict(list)
    for r in rows:
        p = f"{DEST}/{r['type']}/{r['name']}"
        if not os.path.exists(p):
            continue
        g = _I.open(p).convert("L").resize((HASH_N, HASH_N), _I.BOX)
        px = list(g.getdata())  # noqa: deprecation - stable across Pillow 11-13
        avg = sum(px) / len(px)
        byhash["".join("1" if v > avg else "0" for v in px)].append(r)
    # Grouped by HAMMING DISTANCE, not by an identical string: the same badge
    # scanned on three different sheets differs in a few bits.
    items = [(h, r) for h, group in byhash.items() for r in group]
    used, furniture = set(), set()
    for i, (hi, ri) in enumerate(items):
        if i in used:
            continue
        near = [(i, ri)]
        for j, (hj, rj) in enumerate(items):
            if j <= i or j in used:
                continue
            if sum(a != b for a, b in zip(hi, hj)) <= HASH_MAX_DIFF:
                near.append((j, rj))
        if len({r["page"] for _, r in near}) >= FURNITURE_MIN_PAGES:
            used.update(k for k, _ in near)
            furniture.update(id(r) for _, r in near)
    if furniture:
        dropped = [r["name"] for r in rows if id(r) in furniture]
        print(f"  dropped {len(dropped)} repeated rubric badge(s): {sorted(dropped)[:6]}")
        for r in rows:
            if id(r) in furniture:
                p = f"{DEST}/{r['type']}/{r['name']}"
                if os.path.exists(p):
                    os.remove(p)
        rows = [r for r in rows if id(r) not in furniture]

    json.dump(rows, open(f"{DEST}/figures.json", "w"), ensure_ascii=False, indent=1)
    per = {t: len(os.listdir(f"{DEST}/{t}")) for t in TYPES}
    print(f"{len(rows)} figures -> {DEST}/  {per}")
    dupes = [r["name"] for r in rows]
    clash = {n for n in dupes if dupes.count(n) > 1}
    if clash:
        print(f"  NAME CLASHES ({len(clash)}): {sorted(clash)[:10]}")


if __name__ == "__main__":
    sys.exit(main())
