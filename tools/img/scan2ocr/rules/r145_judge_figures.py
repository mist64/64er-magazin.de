"""Decide which of the measured rectangles are article figures.

Geometry proposes; this disposes.  FINDINGS is explicit that "is this a picture
or is it type" is not answerable from any low-level statistic -- half the
figures in this magazine ARE pictures of text (screenshots, hardcopies,
character sets, flowcharts), and every statistic that rejects a data table
rejects those with it.  So the rectangles arrive here with their measurements
attached and something that can READ THE PAGE makes the call.

One model call per page that has candidates.  The model sees the overlay with
every candidate numbered, plus the page's own caption lines, which is what tells
it a region is "Bild 3" rather than a table.
"""
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import r000_llm as llm
import r010_ocr_blocks as OB

OUT = os.path.join(OB.OUT_DIR, "figures")
LANES = 4
CAPTION_RE = re.compile(r"^\s*(Bild|Tabelle|Abb\.?)\s*(\d+)", re.I)

PROMPT = """You are extracting the FIGURES from one page of the German home-computer
magazine "64'er", issue 9/September 1986, so they can be cropped out as images.

A geometric pass has already measured candidate rectangles. It cannot tell a
picture from typesetting -- half this magazine's figures ARE pictures of text
(screen photographs, printer hardcopies, character-set samples, flowcharts with
labelled nodes), so no measurement separates them from a data table. You can see
the page, so you decide.

The overlay image shows the page with every candidate outlined in RED and
numbered. Judge each one.

A candidate IS a figure when it is:
  - a photograph (product shot, portrait, press photo)
  - a screen photograph or a printer hardcopy, even though it shows text
  - a diagram, schematic, flowchart, chart or graph
  - line art, a drawing or a cartoon
A candidate is NOT a figure when it is:
  - body text, a headline, a standfirst, a caption
  - a DATA TABLE of typeset text (rows of specifications, prices, functions),
    even when it is set on a grey or yellow tint. These get transcribed as HTML
    tables elsewhere, not cropped.
  - a BASIC program listing printed for the reader to type in
  - PAGE FURNITURE: a rubric badge or section logo ("64'er Test", "BUECHER",
    "LESERFORUM", "Aktuelles"), a headline or headline banner, a running head, a
    page number, a footer, a rule, or blank paper. These are printed once per
    article by the magazine's layout, not placed as an illustration. They look
    like line art and they are cropped cleanly, which is exactly why they keep
    being kept -- judge them by their ROLE on the page, not their appearance.
  - anything belonging to an advertisement

For each candidate that IS a figure, also give:
  - "number": the figure's number as printed in its caption. "3" for "Bild 3".
    When a candidate says ANCHORED ON CAPTION, that caption is printed directly
    beneath it and its number is the answer -- do not second-guess it.
    Use "t3" for "Tabelle 3" if a table is so complex it must stay an image.
    Use "0" when the figure has NO caption (an opening or title photograph).
  - "convert": how it must be converted, which depends on what it physically is:
      "c"     full colour
      "gray"  continuous-tone greyscale, no colour
      "bw"    black on white -- line art, a hardcopy, a screenshot of text
      "dots"  black on a screened grey grid (a halftone pattern is visible)
  - "caption": the caption line's text if the page prints one, else null.

Also report, in "missing", any figure you can SEE on the page that has no red box
at all -- describe where it is and what it is. Do not invent a bounding box.

Return ONLY a JSON object, no prose, no code fence:
{{"figures": {{"<index>": {{"figure": true, "number": "3", "convert": "bw",
                          "caption": "Bild 3. ..."}}, ...}},
  "missing": ["..."]}}
Every candidate index must appear in "figures"; give `{{"figure": false}}` with a
one-word "why" for the ones that are not figures.

PAGE {page}. CANDIDATES:
{cands}

CAPTION LINES PRINTED ON THIS PAGE:
{caps}
"""


def judge(page):
    cand_path = f"{OUT}/p{page:03d}.json"
    if not os.path.exists(cand_path):
        return None
    cands = json.load(open(cand_path))
    if not cands:
        return None
    dest = f"{OUT}/p{page:03d}.judged.json"
    rec = json.load(open(os.path.join(OB.OUT_DIR, f"{page:03d}.labels.json"), encoding="utf-8"))
    caps = []
    for b in rec["blocks"]:
        for line in b["text"].split("\n"):
            if CAPTION_RE.match(line):
                caps.append(" ".join(line.split())[:150])
    lines = []
    for i, c in enumerate(cands):
        x0, y0, x1, y1 = c["bbox"]
        anchor = (f"  ANCHORED ON CAPTION: {c['caption']!r}" if c.get("caption")
                  else "  no caption -- an opening photo or a cover")
        lines.append(f"[{i}] {c['w']}x{c['h']} px at x={x0} y={y0}  "
                     f"measured_type={c['type']}{anchor}")
    prompt = PROMPT.format(page=page, cands="\n".join(lines),
                           caps="\n".join(caps) or "(none)")

    # THE CACHE KEY IS THE PROMPT ITSELF.  Keyed on nothing, a verdict survived
    # a re-run of the extractor and was applied to a different candidate list --
    # indices no longer lined up and 168 candidates produced 22 figures with
    # three buckets empty.  Keyed on the boxes, rewriting the instructions
    # changed nothing.  Keyed on boxes plus the instructions, changing the
    # EVIDENCE in the prompt changed nothing: every page returned its cached
    # verdict after the measured types were corrected.  Three variants of one
    # bug, so the key is now everything the model is actually shown.
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    if os.path.exists(dest):
        old = json.load(open(dest))
        if old.get("key") == key:
            return old
        print(f"p{page:03d}: prompt changed, re-asking", flush=True)
    # Name the overlay BARE and run from its directory: the CLI transport is a
    # nested `claude -p`, and it refuses to read a path outside its working
    # directory -- it comes back with "permission not granted, session
    # non-interactive" rather than an answer.  Same lesson as r020_evaluate's
    # truth pass, which carries the same comment.
    reply = llm.call(prompt, "", image_path=f"p{page:03d}.png",
                     cwd=f"{OUT}/overlay")
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        print(f"p{page:03d}: no JSON in reply", flush=True)
        return None
    got = json.loads(m.group(0))
    got["key"] = key
    json.dump(got, open(dest, "w"), ensure_ascii=False, indent=1)
    keep = sum(1 for v in got.get("figures", {}).values() if v.get("figure"))
    print(f"p{page:03d}: {keep}/{len(cands)} are figures"
          f"{'  MISSING: ' + str(len(got.get('missing', []))) if got.get('missing') else ''}",
          flush=True)
    return got


if __name__ == "__main__":
    pages = [int(a) for a in sys.argv[1:]] or range(1, 177)
    with ThreadPoolExecutor(max_workers=LANES) as ex:
        list(ex.map(judge, pages))
