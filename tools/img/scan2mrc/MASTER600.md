# The 600 dpi viewable master — end to end

**What this produces:** one 600 dpi RGB page per scan — deskewed, matted, neighbour page and
scanner bed removed, cropped to A4, colour-graded — as a PNG that declares its own resolution.
Not an MRC PDF, not the renderer's input: the thing you open and look at.

**What it is a reproduction of:** `tools/img/ALL.sh`, the original recipe that made the 600 dpi
masters before any of this pipeline existed. Its chain was

    convert.py (RGB -> CMYK)  ->  magick -level per channel  ->  -resize 25%
                              ->  SWOP -> AdobeRGB  ->  -density 600

and that is the chain reproduced here, in Rust, on top of the measured front end (deskew, matte,
spine, A4 window) that ALL.sh did not have. Three of its properties are deliberate and are **not**
improvements waiting to happen:

* **No GCR.** ALL.sh has none. GCR (move `min(C,M,Y)` into K) is the MRC renderer's reconstruction
  choice — it makes CMY pure colour and K all neutral, which is what the *renderer* needs. The
  viewable master keeps the separation as graded.
* **Reduce before the ICC transform**, which is ALL.sh's order. The transform is a nonlinear
  per-pixel map, so running it after the reduce is a different image, not a cheaper route to the
  same one. It is also 16× less work: 35 MP instead of 557.
* **Grade at 2400, then scale.** The other order is much worse and not a matter of taste: the K
  level clips at 90–95%, so downsampling first turns thin black type into mid-grey and the clip
  then erases it. Grading at full res, where the ink either is or is not on the paper, and
  averaging afterwards, is what antialiases the type instead of deleting it.

---

## Running it

```sh
./pipeline.sh --only master                 # all 176 pages, 3 lanes
./pipeline.sh --only master --pages 7 92    # a subset
./pipeline.sh --only master --force         # re-render pages that already have output
```

`master` is a stage in `pipeline.sh` like any other, so it goes through the same driver and the
same page list. It depends on `geom` and on nothing after it: **`cache` is not a prerequisite** —
the master run reads the cut profiles `geom` wrote and returns before the renderer's 1 GB CMYK
TIFF is ever built.

From a cold `tmp/`, the whole thing is:

```sh
./pipeline.sh --only skew,holes,spine,stack,logo,clear,window,geom
./pipeline.sh --only master
```

**Cost:** ~19 s and ~70 MB a page (three candidate grades, see below), ~20 min and ~12 GB for the
issue at 3 lanes. One grade alone is ~23 MB a page.

**Output:** `tmp/master600/NNN_master600_<grade>.png`, 4960×7015, 8-bit RGB (AdobeRGB), pHYs
tagged 600 dpi. Plus `NNN_known.png`, the 1-bit unknown mask at 2400, and one JSON line per page
appended to `tmp/master_reports.jsonl`.

---

## The stages, in order

Everything before `master` is measurement on the 150/600 dpi thumbnails and writes metadata only —
no pixel of the master scan is touched until the last stage.

| stage | script | writes |
|---|---|---|
| `skew` | `01-deskew/deskew.py` | `skew_all.txt` — one angle per page, MEASURED, not applied |
| `holes` | `02b-opposite-page/clip_holes.py` | `clip_holes.json` — the six binder-clip punches |
| `spine` | `02b-opposite-page/spine.py` | `spine_all.json` — the neighbour-page boundary |
| `stack` | `stack_render.py` | `stack600/NNN.png` — deskew+matte+spine composed, RGBA |
| `logo` | `03-crop/logo_detect.py` | `logo_positions.json` — the 64'er wordmark anchor |
| `clear` | `03-crop/logo_clearance.py` | `logo_clearance.json` — page around the anchor |
| `window` | `03-crop/fit_window.py` | `crop_windows_v2.json` — the A4 window per page |
| `geom` | `03-crop/emit_geometry.py` | `page_geometry.json` + `page_geometry/NNN/` — CUT PROFILES |
| `master` | `mrcpipe apply --variant master` | `master600/NNN_master600_*.png` |

**The trap, restated because it has cost a 7-hour run:** the last stage reads the CUT PROFILES from
`geom`, not the matte code. Changing `bed_matte.py` and re-running `master` applies nothing. Any
matte, spine or window change must re-run from `stack`.

## Inside the last stage

Per page, in `rust_pipeline/src/apply.rs`:

1. **ONE affine.** The output grid is inverse-mapped straight onto `master_2400/NNN.png`, so
   deskew + matte + A4 crop cost a single interpolation rather than three. Alongside it, the
   unknown mask is rasterised *analytically into the output frame* — bed, neighbour page, clip
   punches — never upscaled from a thumbnail.
2. **Inpaint** (`--inpaint`): edge bands mirror-filled from the page itself, beyond mirror range
   the page's own measured paper colour; interior clip punches Telea-inpainted.
3. **Separate** to CMYK — the `convert.py` separation, same eight anchor colours: C/M/Y from the
   ratio of distances to two anchor planes, K from distance to solid black normalised over the
   page.
4. **Grade** — per-channel level stretch. Which levels is the open question; see below.
5. **Reduce 4:1**, lanczos, per ink plane.
6. **ICC** SWOP → AdobeRGB, on the 600 dpi CMYK.
7. **Write** PNG with a pHYs chunk declaring 600 dpi.

**Lanczos, not box.** Measured on p007: type is visibly crisper, photo and C64 screenshot are
indistinguishable, and there is no ringing halo on the black-on-cyan headings — which is where
ringing would show first on this issue. It also matches what ImageMagick's `-resize` did.

**4:1 exactly.** 19843/4 = 4960.75, so the page is 4960×7015 rather than A4-at-600's 4961×7016 —
0.03 mm short, and worth less than resampling on a non-integer ratio.

---

## The grade — decided 2026-08-14: `c30`

Rendered all three ways on p007 and chosen: **`c30`**, the neutral-calibrated separation with
C 30,70. `apply.rs` now renders that alone; the other two sit commented one line above it, because
reinstating them is how the decision gets re-examined rather than re-argued. `pipeline.sh`'s
`FINAL_GRADE` publishes it. Everything below is the evidence.

### The three candidates

ALL.sh graded `C 50%,90%` and `M`/`Y` `30%,70%`, `K 90%,95%`. The M, Y and K values transfer
unchanged. **C does not**, and the reason is worth keeping:

`convert.py` applies no neutral correction of any kind — verified by reading it: the plane-ratio
separation, distance-to-black for K, and nothing else (`stretch_levels` and `remove_black` are
defined but commented out at the call site). That separation reads cyan far too high on a neutral —
a grey at 45% density comes out C 128 / M 78 / Y 62 — and `C -level 50%,90%` clips exactly that
excess back off. It is a hand-compensation for a known defect of the separation, not a colour
decision.

This code separates through `neutral_luts`, which removes the same imbalance *at source*, derived
from the anchors rather than fitted. So ALL.sh's C value applied here corrects the same error
twice. All three variants are rendered so the difference is looked at rather than argued about:

| tag | separation | C level | what it is |
|---|---|---|---|
| `allsh` | raw, no neutral LUT | 50,90 | ALL.sh end to end — reproduces the original master |
| `c50` | neutral-calibrated | 50,90 | corrects C twice; rendered to show the cost, not a candidate |
| `c30` | neutral-calibrated | 30,70 | ALL.sh's intent, corrected once — **chosen** |

Measured on p007. `allsh` lands *between* the other two and closer to `c50`, which is the finding
that matters: the original masters were warm because C 50,90 only **partly** cancels the
separation's cyan excess. That warmth is an artefact of an uncorrected separation, not a colour
decision anyone made — so reproducing it would be reproducing a defect.

| patch | allsh (R,G,B) | c50 (R,G,B) | c30 (R,G,B) |
|---|---|---|---|
| whole page | 205.7, 201.3, 202.8 (**+4.4 R**) | 207.5, 200.1, 200.8 (**+7.5**) | 200.3, 199.5, 201.1 (**+0.8**) |
| black "9/86" | 71.7, 71.1, 71.3 | 72.0, 70.8, 70.7 | 70.9, 70.6, 70.7 |
| photo crop | 54.7, 25.0, 23.9 | 59.8, 22.4, 22.7 | 40.0, 24.6, 25.0 |
| paper margin | 255, 255, 255 | 255, 255, 255 | 255, 255, 255 |

Visibly, `c50` turns the letterpress photo lurid red and the C64 screenshot's grey UI panel
warm-pink with magenta sprites; `allsh` does the same, less far; `c30` keeps the panel grey and the
sprites blue.

**Known non-reproduction.** ALL.sh ran `convert.py` on the *uncropped* master, so its K
normalisation span came from the whole scan — bed, neighbour page and all. This code normalises
over the known page area. On p007 the two spans are `known [0, 363.17]` against `crop [0, 412.81]`,
14% apart, which shifts every K value on the page. Not currently reproduced; if the blacks read
wrong against the old masters, this is the first place to look.

Once a grade is chosen, drop the other two from the loop in `apply.rs` (`--variant master`) and the
per-page cost falls to ~8 s and ~23 MB.
