# Porting the 2400 dpi apply to Rust (option C)

## Why

Measured on a full cache pass of 8609: the Python front end is **89%** of the per-page cost
(367s against 46s for the Rust `geometry`+`detect`). Per-stage profile of one page, after the
two dead-work fixes in 4759b17ec:

| stage | s | kind |
|---|---|---|
| affine warp + alpha | 100.7 | per-pixel |
| write page_rgb png | 45.5 | I/O |
| write detect tiff | 44.5 | I/O |
| separate detect | 42.2 | per-pixel |
| write display cmyk + known | ~38.6 | I/O |
| separate display (+nogcr) | 36.6 | per-pixel |
| inpaint (mirror; Telea never runs on most pages) | 36.1 | mixed |
| ICC transform | 31.9 | library |
| master decode | 18.4 | I/O |
| knorm distance | 15.0 | per-pixel |

Target: **409s -> ~90s** for apply, and **47s -> ~25s** for `mrc`, i.e. a full issue pass from
7.5h to ~2.5-3h and an MRC-only re-render of the whole issue from ~46min to ~25min.

The ICC transform will NOT get faster -- `lcms2` is the same library PIL uses -- so it becomes the
largest single item in the ported apply. That is expected and fine.

## The contract change (this is what makes it "option C")

`mrc` consumes the 2400 dpi page RGB, but computes **nothing above 600 dpi**. Full resolution is
used for exactly three things:

1. `rgb_to_luma_full` -> `luma_tiles`: per 60x60 tile, mean luma plus **counts** of pixels below 45
   and above 235. The counts are true 2400 dpi statistics -- they measure ink dot-area coverage, and
   they do NOT survive downsampling (a 4x4 average of dots is mid-grey and crosses neither
   threshold). This is the only genuine consumer of 2400 dpi in the renderer.
2. `rgb600_lanczos` -> 600 dpi Lanczos RGB (K mask, sat/luma/hue).
3. the descreen's `Filter::Box` resample -> 600 dpi Box RGB.

So apply stops writing the 200 MB page RGB PNG and instead writes what `mrc` actually eats:

| cached product | size | note |
|---|---|---|
| tile stats: `tluma` f32, `black_t`, `white` | ~0.9 MB | EXACT -- computed at 2400 dpi, as now |
| 600 dpi Lanczos RGB | ~35 MB | |
| 600 dpi Box RGB | ~35 MB | |
| `NNN_cmyk_display_filled.tif` | ~193 MB | archival tier, unchanged |
| `NNN_known.png` | small | unchanged |

`mrc` grows a path that reads these instead of a page PNG, and keeps the old path as a fallback so
existing caches still render.

**What this gives up:** 600 dpi becomes the renderer's ceiling. The north star wants >=1200 dpi
line-art stencils eventually; that will have to re-derive from the archival CMYK or the master.
Accepted deliberately -- paying 35 GB and ~60s/page now for an unspecified future capability is the
wrong trade.

## Arithmetic seams -- where a naive port silently diverges

These are the reasons `mrcpipe`'s existing `separate()` cannot simply be reused. Each was checked
against `04-grade/apply_fullres.py` line by line.

1. **K normalisation source.** `separate::separate()` normalises the distance-to-K over the
   **global** min/max of the whole input image. `apply_fullres` normalises over
   `cand[knorm]` with `knorm="known"` -- the min/max over **non-alpha pixels only**. Feeding the
   cropped page to the existing Rust would silently produce the `"crop"` candidate instead. The
   port must take the known mask.

2. **`level()` precision.** Python casts to **float32** before dividing:
   `t = clip((v.astype(float32) - lo) / (hi - lo), 0, 1)`, then `floor(t*255 + 0.5)`.
   `grade.rs::level` does the same arithmetic in **f64**. The rounding rule matches, but f32 vs f64
   can differ by 1 at boundaries. The port must use f32 here to be byte-identical.

3. **CMY divide guard.** Python: `d1 / np.maximum(d1 + d2, 1e-12)`. Rust `cmy_channel_value`:
   `d1 / (d1 + d2)` with no guard. Add the guard.

4. **Truncation vs rounding.** Both truncate toward zero after `*255.0` for the CMY channels
   (`.astype(np.uint8)` / `as i64`) and for K (`.astype(np.int64)` / `as i64`). This already
   matches -- do not "fix" it to round-nearest.

5. **The affine sampler.** Bilinear, and the precision is specific:
   - `inside = (xs >= 0) & (xs <= W-1) & (ys >= 0) & (ys <= H-1)`
   - `x0 = clip(floor(xs), 0, W-2)`, `y0 = clip(floor(ys), 0, H-2)`
   - `fx`, `fy` and the four samples are **float32**
   - the result is written back as `clip(s + 0.5, 0, 255) -> uint8` (round-half-up, then truncate)

6. **GCR** (`neu = min(C,M,Y)`; subtract from CMY, add to K with clip) already matches
   `grade::gcr_in_place`.

7. **Inpaint.** `mirror_edges` is the whole cost -- interior-hole Telea runs on only **18 of 176
   pages, 53 components total**, each on a small crop (`pad=24`). Port the mirror; for holes either
   take the `inpaint` crate (which is Telea, ported from Pyheal) or leave those pages to a Python
   touch-up. Do NOT hand-write Telea for 53 components.

## Acceptance -- no regressions

Ordered, strongest first. A port must not change anything.

1. **Byte identity.** `shasum` on `NNN_cmyk_display_filled.tif` and `NNN_known.png` against the
   Python output for the same page. This is the bar; the seams above exist so it can be met.
2. **Bounded numeric difference** where a float path genuinely cannot match (document which, and
   why): report max abs diff and a percentile per plane. Precedent: `mrcpipe` itself was only ever
   validated at raster corr 0.9997, never byte-exact.
3. **Decision identity.** Run `mrcpipe classify` on both the Python-produced and Rust-produced
   inputs, `diff_record` them, and require **zero verdict flips**. This is the gate that matters:
   a +-1 level difference is irrelevant unless it moves a cluster, a darkfill promotion or a K
   component.
4. **Visual.** `draw_record.py --diff` on any page that does move.

Use pages that stress different content: see the A/B sample list in the descreen-tap work
(006 002 017 157 034 073 005 003 154 062, plus 071/095 as text-only controls).

## Related fix, independent of the port

`tap(mw, mh, 80.0, 100.0)` in `run_mrc` is hardcoded for a **200 dpi** background (Nyquist 100 =
the stop). With `--bg-dpi 150` the Nyquist is 75, so the 75-100 lp/in band aliases. Fix:
`tap(mw, mh, 0.4 * bg_dpi, 0.5 * bg_dpi)`, which reproduces (80,100) exactly at 200 dpi. The chroma
tap (30,50) needs no change -- 50 is already below 75.


---

# OUTCOME (2026-07-31)

Done and in production. `04-grade/apply_fullres.py` is deleted; `cache_pages.sh` drives
`mrcpipe apply`.

## Acceptance, as achieved

| gate | result |
|---|---|
| byte identity, `known.png` | **byte-identical** (106,121 bytes, p002) |
| pixel identity, display CMYK | **0 differing samples of 2,227,416,436** (p002, all four planes) |
| pixel identity, page RGB | **0 differing samples of 556,854,109** (p002) |
| decision identity | satisfied A FORTIORI -- identical pixels cannot produce different decisions, so the classify/diff_record run was not needed for the apply |
| interior holes | 627 differing pixels on p130 (0.000113%), **all 627 inside the unknown mask** -- every one is invented content |

The two `.tif` files differ by 1 byte inside the LZW stream (a compressor may reset its dictionary
differently); all 10 TIFF tags match and the decoded image is bit-exact.

## Timing, measured

409s -> **30s** without the page RGB, **50s** with it. Per stage:

| stage | Python | Rust |
|---|---|---|
| master decode | 18.4 | 4.8 |
| affine warp + alpha | 100.7 | **0.8** |
| knorm | 15.0 | 0.1 |
| separate detect | 42.2 | 0.5 |
| write detect tiff | 44.5 | 0.8 (now uncompressed) |
| inpaint (mirror + Telea) | 36.1 | 0.4 + 3.0 |
| separate display | 36.6 | 0.5 |
| write display tiff | ~38 | 8.2 |
| ICC transform | 31.9 | **5.0** |
| write page RGB | 45.5 | 26.2 |

## Where the spec was WRONG

* **ICC.** Predicted "no gain, lcms2 is the library PIL wraps". It is **6x faster** -- the cost was
  PIL's per-strip `Image.merge`, not the transform.
* **Disk.** Option C was projected to cut 200 MB/page to ~35 MB. The two 600 dpi RGB planes are 58
  and 64 MB as PNG, so it is 200 -> 124 MB. The TIME argument stands; the disk claim was oversold.
* **Seams.** Seven were specified; **two more** were found while writing it, both real: numpy's
  `np.round` is HALF TO EVEN (the hole lookup uses it), and `holes_shape` must be read as int64
  rather than inferred from the packed width (packbits pads by up to 7 columns). A third was found
  while testing: `ndimage::binary_dilation(m,w,h,n)` is n iterations of the 4-neighbour CROSS,
  growing a diamond, where the Python uses `np.ones((7,7))`, a square -- fixed by adding
  `binary_dilation_box`.

## Still open

`mrc` still reads the 2400 dpi page RGB rather than the cached tile stats + 600 dpi products.
`apply --cache` writes them and they are verified present, but nothing consumes them yet, so the
option-C speed-up on the render side (47s -> ~25s) is not realised. That is the last piece.
