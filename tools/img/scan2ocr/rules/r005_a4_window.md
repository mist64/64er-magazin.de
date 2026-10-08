# 005b — The A4 window, anchored on the 64'er logo

**Applies to:** **`binding: "sheet"` only.** Every issue of this magazine is
cut this way, but a SPREAD issue is already cut this way by step 005: the
spread variant anchors on the logo and writes an exact A4 window,
`MASTER_W_PX x MASTER_H_PX` = **4961 x 7016**, so `masters600` IS the A4
delivery. The sheet variant writes a traced-trim canvas of varying size
instead, and that is what this step turns into A4.

Running it on a spread issue produces `a4600`, a second crop computed a
different way from the same `sheets600`, which nothing downstream reads —
step 010 OCRs `masters600`, and for a spread issue so does the PDF. 8611
asked before running it rather than after, which is the only reason this
line is right.

**This rule is copied from the process that already solved it**, `03-crop`, and
is reproduced here so scan2ocr is self-contained. The wording of the principle
and the measured figures are the originals; only the fallback order is new,
because this magazine's Sonderhefte are not clip-bound and have no spine to
fall back to.

---

## Run

```bash
cd tools/img/scan2ocr/rules
PY=${PYTHON:-../../../../.venv/bin/python}   # the repo venv; never bare "$PY"
$PY r005_a4_window.py            # no arguments: every page
```

**No arguments.** The program measures every page in `sheets600`, fits ONE
`(S, B)` offset pair per parity, and cuts every page to `<tmp>/a4600/`, one
`NNN.png` and one `NNN.stamp.txt` each. There is no per-page invocation and no
page list — the whole point of the step is that the window is fitted across the
issue and then applied rigidly, so cutting a subset would fit a different
window.

**Two env knobs, which `r005_masters_sheet` ("No CLI knobs, no env knobs") does
not cover because they are this program's, not that one's:**

| knob | default | what it does |
|---|---|---|
| `FILL` | `paint` | what goes outside the frame. `paint` is what every sheet issue has shipped; `mirror` is the experiment described under *The fill* and is NOT the default. |
| `A4_OUT` | `<tmp>/a4600` | redirects the cut, for a comparison run that must not overwrite the delivery. |

Reading these out of the program was a 4-command detour on SH8605, and the
only other record of which `FILL` a build used was SH8604's git-ignored
`LOG.md` — which the next build does not have.

---

## Why the logo is the anchor — the principle, verbatim

> The "64'er" wordmark is print-registered to the page CONTENT. The sheet edge
> is not: print-to-cut registration varies, so anchoring on the paper edge
> would align the paper and misalign the type.

That is the whole reason the anchor exists. Cutting to the traced paper edge
produces a page whose *sheet* is square and whose *type* wanders by however much
the guillotine varied — 1–3 mm on SH8601. Cutting to the logo produces the
property the rest of the chain depends on:

> Cut every page to exactly **210 × 297 mm** (4961 × 7016 px @600 dpi) so the
> same content lands in the same place on every page, and the later stages need
> no per-page geometry.

## What the anchor is, and how well it is found

The wordmark sits in the **outer bottom corner**, is the same glyph on every
page (not mirrored between parities), and is template-matched
(`template_64er_600.png`). MEASURED on 8609: found on **129 of 176** pages,
confidence p50 **0.95**, parity correct on all 129.

Two cautions carried over from the original, both paid for once already:

- `logo_detect.py` reports coordinates in the **raw** thumb frame although its
  docstring claims the deskewed one. Transform the anchor through the same
  rotation the levelling used, and verify by landing it on the glyph — never by
  trusting a sign convention.
- Running the detector on a **page subset REWRITES** its whole output file with
  only those pages. Back it up first.

## The window is rigid, one offset pair per parity

> The window is RIGID relative to the anchor: one (S, B) pair per parity, not
> per page, because the point of anchoring on the logo is that the same content
> lands in the same place on every page.

`S` = the anchor's distance from the window's left edge, `B` = from its top
edge, fitted to minimise alpha inside the window over the pages that have their
own logo. 8609's fitted values, kept as the shape of the answer rather than as
constants to reuse:

```
even   S= 568  B=6892   mean alpha in window 1.27%
odd    S=4416  B=6900   mean alpha in window 1.90%
```

**S must span the full page width.** On odd pages the anchor is near the RIGHT
edge, and a search range capped at 900 px pinned the optimum to its own
boundary and reported 71 % alpha — a window mostly off the page.

Pages with no detected logo are **excluded from the fit** — an interpolated
anchor would drag the optimum toward its own error — but still receive a
window afterwards, from an anchor interpolated across same-parity neighbours
and marked as interpolated.

## A4 does not fit without alpha, and that is expected

> A4 fits alpha-free on **0 of 129** pages. The page simply is not 210 × 297 mm
> of known pixels once bed, neighbour, clip holes and the deskew wedge are
> removed, so the objective is not "avoid alpha" but "minimise it", and
> inpainting is structural rather than optional. The deficit is small and
> consistent (1–3 mm), i.e. a thin border, not a chunk.

And where the window overhangs the canvas, leave the output **transparent
rather than clamping the window** — clamping silently shifts the content and
destroys the one property the anchor exists to provide.

## The fallback order for this chain

The original falls back to a **spine** anchor where there is no logo. A
glue-bound issue has no spine, so for `binding: sheet` the order is:

1. **the 64'er logo**, where it is found — the anchor proper;
2. **paper-edge**, where a page has no detected logo;
3. **traced-edge**, for pages that carry no logo at all — the cover leaf and a
   bound-in card such as SH8601's Zahlkarte, which are not body pages and have
   no wordmark to register to.

**And an insert smaller than the issue's leaf keeps its measured size** rather
than being centred on an A4 window: SH8601's Zahlkarte is ~144 x 205 mm, and
padding it to A4 would fabricate 53% of the page. A4 is the geometry of the
ISSUE's leaves.

**ONE INSERT IS ONE OBJECT, AND ALL ITS PAGES ARE THE SAME SIZE.** A bound-in
card is a single physical thing, scanned once per side. Tracing it four times
gives four boxes that differ by tracing error, and shipping those verbatim tells
the reader the same card is four different sizes. MEASURED on SH8601's
Zahlkarte (149-152): `3395x4829`, `3404x4834`, `3410x4846`, `3413x4808` px — a
spread of **0.76 x 1.61 mm across the front and back of one card**.

Take the **max per axis**, for the same reason the A4 rule pads a sheet that
measures short: a box that traced short has CUT INTO the card, and content lost
to a short trace cannot be recovered downstream, while padding costs at most the
spread — 0.76 x 1.61 mm of the card's own paper. Pad **symmetrically**, so the
content stays where it sits on the card.

Group by **contiguous run**, never all inserts at once: an issue may bind in two
different cards, and unifying across them invents a size neither one is. The cover leaf is the opposite case and is trimmed, not
padded — its 223 mm width is a fold flap, not a larger page.

Record per page which of the three was used, beside the grade stamp, so a page
whose type sits differently from its neighbours can be explained rather than
re-derived.

## A PAGE WHOSE TRACE FAILS IS CUT BY A SCRIPT — NEVER BY HAND, AND THE SCRIPT IS YOURS TO WRITE

**NAMING, because the numbers collide.** The three above — logo, paper-edge,
traced-edge — are the ANCHOR fallbacks, and they are implemented in
`r005_a4_window.py`. The three below are RECOVERIES for a page whose trace
failed outright, they are a different thing, and **they are not in the code**:
every build so far has re-derived them in a hand-written script (SH8603's
155/163/168, SH8604's 163). Call them recovery A, B and C, not fallback 1, 2
and 3. Implementing them in `r005_a4_window.py` is the open task; until then,
the builder writes the script and records which recovery it used in the stamp.

**Owner, 2026-10-04: "manual cropping is not an option for the PDF."** A hand
crop does not reproduce, is not recorded anywhere a later build can read, and
turns one person into the step. A page whose trace fails gets a BEST-EFFORT
window from the evidence that is there, and the result is published with a note
saying which fallback produced it.

**THE SUMMARY CANNOT SEE THIS FAILURE, SO DO NOT WAIT FOR IT TO SAY SO.** The
program runs the anchor fallbacks only for pages step 005 TRACED. For an
uncropped page it still produces a window — `traced-edge` off the whole frame
— and the two numbers that would normally condemn one both look healthy:
MEASURED on SH8604's p163, **alpha 4.02 %, fabricated 0.00 %**, with ~4 mm of
scanner bed left along the foot. Fabricated is 0 precisely BECAUSE the window
sits inside the frame; alpha is small because the frame is bigger than A4.
Neither can rise for the one defect that is actually present. Check the foot of
every page the 005 stamp calls `uncropped` by eye, and expect to run a
recovery.

The rule above assumes every page of an insert traced, so the run can take the
max per axis. It does not cover a page that failed OUTRIGHT — the trace found
no card at all and the page was published as an uncropped sheet. MEASURED:

| issue | traced | failed |
|---|---|---|
| SH8602 | 165 `143.1 x 208.0`, 166 `145.0 x 208.0`, 167 `143.1 x 208.4` | 168 (`212.7 x 304.2`, uncropped) |
| SH8603 | 181 `144.4 x 207.7` | 182, 183, 184 (`216.4 x 304.2`, uncropped) |

So, in order:

**Recovery A.** **A failed page of an INSERT takes its run's unified size.** The authority is
   **the run's own agreeing traces**, never a corpus constant: a bound-in card
   is whatever that issue bound in. MEASURED: SH8602 and SH8603's Zahlkarte read
   ~144 x 208 mm, SH8601's ~144 x 205 — but **SH8604's reads 149.9 x 206.9**,
   6 mm wider, because its card carries a printed "Wußten Sie schon …" flap.
   All four of its traces agree and its edges are clean, so the card is simply a
   different object. Read as a constant, the rule would have called all four
   failed.

   So the test is **agreement within the run**, not a match against ~144 x 208.
   A member has failed when it disagrees with its agreeing siblings, or when it
   reads at sheet size (216 x 304 mm) — that is the frame, not the card.

   **Anchoring:** on the page's own traced top-left corner where there is one;
   where there is not, on whichever edges ARE measurable (right or bottom
   against the bed), and NOT on the run's offset. MEASURED on SH8603: the run's
   offset put the window's right edge at 3438, past 183's card edge at 3431, so
   28% of 183's right 24 px band was bed. Check the window's edge bands for bed
   before accepting it.
**Recovery B.** **A failed page with surplus paper** (a wrapper back cover, 217 mm of paper
   in an A4 frame) is windowed on its **ink bounding box**, not the paper's.
**Recovery C.** **A failed page whose ground is full-bleed dark**, where a colour test for
   the prop cannot work because the sheet is already graded and separated, is
   cut from **row and column luminance profiles**: the prop shows as a step at
   the foot, the bed as a plateau darker than the page. MEASURED on SH8602/155:
   page lum ~6 -> ~105 -> ~200 at row ~7005; dark-brown ground ~10 against bed
   ~3, a step at x~4948.

Cut from `masters600`, pad outside the frame with paper white, write into
`<tmp>/a4600/`, and keep the automatic window as a backup. Note in the stamp
which fallback was used.

## Verification

```bash
cd tools/img/scan2ocr/rules
PY=${PYTHON:-../../../../.venv/bin/python}   # the repo venv; never bare "$PY"

# 1. every body page is exactly 4961 x 7016, and any page that is NOT says so
#    in its own stamp.  An INSERT is legitimately a different size -- 'ONE
#    INSERT IS ONE OBJECT' unifies the run and records it -- so the question is
#    not "are they all A4" but "is every exception a documented one".
#    MEASURED on SH8605: 196 at 4961x7016 and 197-200 at 3551x4923, the
#    bound-in card, each stamp carrying UNIFIED or OVERRIDE.
$PY - <<'PY'
import collections, re, struct
import r005_a4_window as A
def wh(f):                      # the IHDR, so a 100 MB page costs 24 bytes
    with open(f, 'rb') as fh: return struct.unpack('>II', fh.read(24)[16:24])
want, sizes, bad = (A.A4_W, A.A4_H), collections.Counter(), []
for f in sorted(A.OUT_A4.glob("[0-9][0-9][0-9].png")):
    sz = wh(f); sizes[sz] += 1
    if sz == want: continue
    note = f.with_suffix(".stamp.txt").read_text(encoding="utf-8")
    tag = next((t for t in ("UNIFIED", "OVERRIDE") if t in note), None)
    (print(f"  {f.stem} {sz[0]}x{sz[1]} -- documented {tag}") if tag
     else bad.append((f.stem, sz)))
print("expected", want, "| found", dict(sizes))
assert not bad, f"off-size pages with no UNIFIED/OVERRIDE in the stamp: {bad}"
PY

# 2. The anchor lands on the glyph -- check the overlay on a sample, per
#    parity, rather than trusting the transform.  (By eye: `overlay()` writes
#    them.  Check 3 is the measurement, but it cannot tell a logo from a
#    convincing near-miss, and the overlay can.)

# 3. CONTENT REGISTRATION, which is the property this rule exists for and the
#    only one that proves it worked: the logo must land in the SAME PLACE in
#    every delivered page of a parity.  Detect it in the DELIVERY (not the
#    sheet) and compare.  MEASURED on all 200 pages of SH8605: 181 pages carry
#    a logo, and the modal position is (4600, 6888) even / (360, 6888) odd with
#    spread 0 px in both axes.
#
#    **READ THE OPPOSITE EDGE AS THE CONTROL.**  The anchor is the tight
#    bbox's corner on the wordmark's own side, and that is exactly the edge the
#    tight bbox gets wrong on a page where the match is poor -- so a page can
#    look 16 px out of register while its content is where it belongs.  SH8605
#    p033: bbox x0 376 against a modal 360, width 364 against 379-383, score
#    0.937 against 0.948 -- but x1 740 against 741-742.  The RIGHT edge agrees
#    to a pixel, so the page is registered and what moved is the detection.
#    (p033 had been re-cut by override to its pre-field window, and this is how
#    you tell that the re-cut worked: the errata it came from recorded the same
#    16 px as "0.68 mm out of register in the delivery", which the opposite
#    edge disproves.)
#
#    So the check has to separate two findings that look identical:
#      (a) width WITHIN p5-p95 but the anchor off the mode -> the window was
#          not rigid.  This is the defect the rule is about.
#      (b) width OUTSIDE p5-p95 -> the detector, not the window.  Check the
#          opposite edge before concluding anything, and expect it to agree.
#
#    Two measures that DO NOT work, so they are not re-attempted:
#      - cross-correlating the foot strips of same-parity pages.  The strips
#        differ by CONTENT (different folios, different figures), so the best
#        shift is content, not registration: it reported -4/+4 px on a
#        correctly registered SH8605.
#      - the darkest row of the foot strip, as a stand-in for the foot rule.
#        Not every page has one, and a figure at the foot is darker: spread
#        241 px (odd) and 282 px (even) on the same correct issue.
$PY - <<'PY'
import collections, cv2, numpy as np, statistics as st
from PIL import Image
import r005_a4_window as A
Image.MAX_IMAGE_PIXELS = None
tmpl = cv2.imread(str(A.TEMPLATE), cv2.IMREAD_GRAYSCALE)
res = collections.defaultdict(list)
for f in sorted(A.OUT_A4.glob("[0-9][0-9][0-9].png")):
    pg = int(f.name[:3])
    g = cv2.cvtColor(np.asarray(Image.open(f).convert("RGB")), cv2.COLOR_RGB2GRAY)
    ok, side, sc, _a, bb = A.detect(g, tmpl)
    if ok:
        res[pg % 2].append((pg, side, round(sc, 3), bb[0], bb[2], bb[3]))
for par in (0, 1):
    rows = res[par]
    if not rows: continue
    far = 4 if par == 0 else 3          # the anchor's own edge: x1 even, x0 odd
    near = 3 if par == 0 else 4         # and the opposite one, as the control
    anc = [r[far] for r in rows]; ctl = [r[near] for r in rows]
    w = [r[4] - r[3] for r in rows]; y = [r[5] for r in rows]
    lo, hi = np.percentile(w, 5), np.percentile(w, 95)
    mode_a, mode_y = st.mode(anc), st.mode(y)
    print(("even" if par == 0 else "odd "),
          f"n={len(rows)} anchor ({mode_a}, {mode_y}) spread {max(anc)-min(anc)}/"
          f"{max(y)-min(y)} px | logo width {min(w)}-{max(w)} p5 {lo:.0f} p95 {hi:.0f}")
    rigid, detect_ = [], []
    for r in rows:
        if r[far] == mode_a and r[5] == mode_y: continue
        (detect_ if not (lo <= r[4] - r[3] <= hi) else rigid).append(
            (r[0], r[far], r[5], r[2], r[4] - r[3], r[near]))
    for pg, a_, y_, sc, w_, c_ in detect_:
        print(f"    p{pg:03d} DETECTOR: anchor {a_} (mode {mode_a}), width {w_} "
              f"outside p5-p95, score {sc} -- opposite edge {c_}, "
              f"control says {'REGISTERED' if abs(c_ - st.mode(ctl)) <= 2 else 'MOVED'}")
    assert not rigid, f"the window is not rigid on parity {par}: {rigid}"
    assert all(abs(c_ - st.mode(ctl)) <= 2 for *_, c_ in detect_), \
        "a detector outlier whose opposite edge ALSO moved -- that is registration"

# 4. alpha is a thin border, not a chunk, and the per-page figure is recorded.
#    Read it back out of the stamps rather than trusting the run's summary --
#    the stamp is what a later build can still see.
#
#    ALPHA IS NOT THE NUMBER TO ASSERT ON.  It is measured with the PAPER MASK,
#    which is blind to a full-bleed page, and ~half of an insert's window is
#    bed by construction.  MEASURED on SH8605: the cover reads alpha 83.07%
#    with fabricated 0.11% -- the window sits almost entirely inside the traced
#    page and nothing was invented; the 83% is the mask failing, not a defect,
#    and the delivered cover is right.  Inserts read ~50%.
#    FABRICATED is the number that means something, because it is computed
#    against the TRACED PAGE rather than the mask: it is the fraction of the
#    delivery that is not print.  Report alpha in three populations, assert on
#    fabricated.
#
#    ON AN INSERT, BOTH FIGURES ARE STALE AND DESCRIBE A PAGE THAT WAS NOT
#    DELIVERED.  They are computed for the full A4 window and the UNIFIED step
#    then cuts that window down to the card, so the stamp reports the A4
#    window's numbers against a 3551 x 4923 delivery: SH8605's p199 and p200
#    read fabricated 49.99% and 50.12%, which is the bed around a small card
#    inside a window the size of a page, NOT half an invented delivery (the
#    unification padded 3536 -> 3551 px, +7/+8 px a side, 0.4%).  So no check
#    can catch a genuinely half-invented insert from these numbers.  Recompute
#    alpha and fabricated AFTER the unification cut and overwrite them in the
#    stamp; until that lands, read an insert's two figures as the window's and
#    take the padding from the UNIFIED line.
$PY - <<'PY'
import re, statistics as st
import r005_a4_window as A
body, ins = [], []
for f in sorted(A.OUT_A4.glob("*.stamp.txt")):
    t = f.read_text(encoding="utf-8")
    a = float(re.search(r'alpha\s+([\d.]+)%', t).group(1))
    b = float(re.search(r'fabricated ([\d.]+)%', t).group(1))
    (ins if ("UNIFIED" in t or "OVERRIDE" in t) else body).append((f.name[:3], a, b))
fullbleed = [r for r in body if r[1] > 20.0]      # the mask could not see it
body = [r for r in body if r[1] <= 20.0]
for name, rows in (("body", body), ("full-bleed", fullbleed),
                   ("insert/override", ins)):
    if not rows: continue
    A_ = [r[1] for r in rows]; B_ = [r[2] for r in rows]
    print(f"{name:16s} n={len(rows):3d} alpha p50 {st.median(A_):5.2f}% "
          f"max {max(A_):5.2f}% ({max(rows, key=lambda r: r[1])[0]}) | "
          f"fabricated p50 {st.median(B_):5.2f}% max {max(B_):5.2f}% "
          f"({max(rows, key=lambda r: r[2])[0]})")
bad = [r for r in body + fullbleed if r[2] > 5.0]
assert not bad, f"these pages are more than 5% invented: {bad}"

# 5. AFTER A REGRADE, the window must not have moved.  The field moves no
#    pixels, so a window that moves between runs is a MATCHER artefact, not a
#    better fit.  MEASURED on SH8605: the paper-yellowing field changed p033's
#    logo match to a 364 px bbox (every other page 379-383) at score 0.937
#    against 0.948, and the anchor landed 16 px off -- 0.68 mm out of register
#    in the delivery, the only outlier among 181 logo pages, and found only
#    because the whole parity was re-run.  Keep the previous run (A4_OUT) and:
$PY - <<'PY'
import re, sys, pathlib
import r005_a4_window as A
PREV = pathlib.Path("<the previous run's a4600>")      # A4_OUT of that run
if not PREV.is_dir():
    sys.exit("no previous run to compare -- skip this check on a first build")
def win(d, n):
    m = re.search(r'window\s+(-?\d+) (-?\d+) (\d+) (\d+)\s+in the master',
                  (d / n).read_text(encoding="utf-8"))
    return m.groups() if m else None
moved = [f.name[:3] for f in sorted(A.OUT_A4.glob("*.stamp.txt"))
         if (PREV / f.name).exists() and win(A.OUT_A4, f.name) != win(PREV, f.name)]
print("pages whose window moved across the regrade:", moved or "none")
assert not moved, f"the field moves no pixels, so these are matcher artefacts: {moved}"
PY
```

**And the stamp must name the grade it was cut from.** `a4600/*.stamp.txt` and
the PNG's `r005b` chunk carry the anchor, the window, alpha and fabricated, but
NOT `grade-sha` / `field-sha`, so a stale A4 page cannot be caught by string
comparison the way a stale master can — `masters600/NNN.stamp.txt` carries both.
Copy them through from the master's stamp at cut time, and check they match the
masters the delivery was cut from. Until that lands, check 5 above is the only
guard, and it needs the previous run kept.
