# mrcpipe — Rust port of the 8608-600 MRC screening / PDF pipeline

A single Rust binary that runs the full MRC pipeline (or individual stages) for the
64'er magazine digitization project. It reimplements the authoritative Python
(`convert.py`, `apply_gcr.py`, `detect_screened.py`, `measure_screen_geometry.py`,
`mrc_hyst8_perio.py`) — **pure Rust**, shelling out only to `/opt/homebrew/bin/jbig2`
for JBIG2 encoding. Each stage reads/writes the **same file formats** as the Python, so
Rust and Python stages are mix-and-matchable with existing artifacts.

## Build

```
cd rust_pipeline
cargo build --release
# binary: target/release/mrcpipe
```

## Subcommands

| Command | Python equivalent | Description |
|---|---|---|
| `separate <in.png> <out.tiff>` | `convert.py` | geometric RGB→CMYK separation |
| `grade <in.tiff> <out.tiff> [--variant display\|detect] [--gcr] [--crop-width N --page-id P]` | `ALL.sh` levels + `apply_gcr.py` | per-channel `-level` grade, optional A4 crop + GCR |
| `full-cmyk <master.png> <out.tiff> --crop-width N --page-id P [--variant ..] [--gcr]` | `make_graded_cmyk.sh` / `make_detect_cmyk.sh` | separate → grade → crop → GCR in one pass |
| `detect <cmyk.tiff> <out_base> [--hop 60]` | `detect_screened.py` | screen score `.npy` (+ `_chan.npy`, `_cov.npy`) |
| `geometry <cmyk.tiff> <out.json> [--dpi 2400]` | `measure_screen_geometry.py` | per-channel pitch/angle JSON |
| `cluster <page.png> <score.npy> <mask.png> [--thr 6]` | `mrc_hyst8_perio.py` steps 1–6 | screened cluster mask |
| `mrc <page.png> <score.npy> <out.pdf> [--thr 6]` | `mrc_hyst8_perio.py` | full MRC PDF |
| `full <master.png> <page.png> <out.pdf> --crop-width N --page-id P` | the deploy chain | master → detect-CMYK → score → MRC PDF |

`grade --variant detect` uses the no-shadow-clip levels (C/M/Y/K low=0%) from
`make_detect_cmyk.sh`; `display` uses C 50,90 / M,Y 30,70 / K 90,95.

The `mrc` stage honours the same env-var knobs as the Python
(`MINCC`, `EXTEND`, `KMED`, `KOPEN`, `TCV`, `TS`, `TT`, `VOTE`, `RECT`), plus `MRCDBG=1`
to print per-step mask fractions.

### Example (end-to-end, page 016)

```
mrcpipe full 2400_master/016.png pages/016_2400_cropped.png out_016.pdf \
    --crop-width 1246 --page-id 16 --work /tmp/mrc
```

## Completion status

| Stage | Status | Notes |
|---|---|---|
| 0 separation (`convert.py`) | **complete** | exact |
| 1 grade + A4 crop + GCR | **complete** | exact; detect-variant levels selectable |
| 2 detect (`detect_screened.py`) | **complete** | score, `_chan`, `_cov` |
| 2 geometry (`measure_screen_geometry.py`) | **complete** | exact JSON |
| 3–5 MRC (`mrc_hyst8_perio.py`) | **complete** | cluster, step-7 per-cluster vote, K + accent-ink JBIG2 layers, descreened bg, text inpaint, chromatic + neutral-grey solid rects, PDF assembly |
| Newer first-stage variants (no-shadow grade, per-channel geometry) | **available** | `grade --variant detect`, `geometry` |
| Gabor / decoy / smoothed-field screen-probability (`proto_*`) | **not ported** | research prototypes; the deployed baseline does not use them. The geometry stage that feeds them is ported. |

## Validation vs Python (page 016 unless noted)

All comparisons use `.venv/bin/python` only to generate/decode references.

| Stage | Metric | Result |
|---|---|---|
| separation | max-abs per channel vs `convert.py` | **0** (exact) |
| grade + GCR | max-abs vs ImageMagick `-level` + `apply_gcr.py` | **0** (exact) |
| **full-cmyk** (separate+grade+crop+GCR) | max-abs vs production anchor `cmyk_graded/cmyk_016_2400_gcr.tiff` | **0** (exact, all 4 channels, correct A4 crop/gravity) |
| geometry | JSON values vs `screen_geom/{016,007,003}.json` | **identical** (pitch/lpi/angle/consistency/patches/strength/std) |
| detect score | max-abs / corr vs `detect_screened.py` | **5e-5** / **1.0**; threshold masks agree **100.0%** at thr 6 and 10 |
| detect `_cov` | max-abs vs Python | **1** (no pixel differs by >1; FFT/clip rounding) |
| cluster mask | per-tile agreement vs Python steps 1–6 | **100.0%** |
| **MRC PDF** | rasterized @100dpi vs Python | mean abs **0.21**, **99.99%** of px within ±8, **0.008%** > 40, per-channel corr **0.9997** |
| **full pipeline** (all-Rust) | rasterized vs Python ref | mean **0.21**, **99.99%** within ±8, corr **0.9997** |

The MRC residual is sub-perceptual: ~1-LSB FFT-descreen rounding in the colour
background + rasterizer-level antialiasing at JBIG2 mask edges. All discrete decisions
(present inks, image%, screened%, tint regions, solid rectangles) match the Python exactly.

## Speedups measured (page 016, M-series, release build)

| Stage | Python | Rust | Speedup |
|---|---|---|---|
| separation (`convert.py`, slowest Python step) | ~70 s (separate+crop) | ~10 s (separate+grade+crop+GCR) | **~7×** for more work |
| detect | (comparable scipy.fft, workers=-1) | 25.6 s | parity–faster, fully parallel |
| geometry | — | 1.2 s (incl. 2.2 GB tiff read) | fast |
| MRC | (similar) | 31 s | ~same per-op, now rayon-parallel |
| **full page master→PDF** | n/a (multi-script) | **63 s** single binary | — |

The biggest win is the separation+grade+GCR chain (the Python's slowest part, dominated by
`apply_along_axis`-free but interpreted numpy + three ImageMagick passes): one ~10 s Rust
pass replaces a ~70 s+ multi-tool chain, exact to the byte. MRC `ndimage` ops
(`median_filter` size-25, gaussians) are rayon-parallelized (210 s → 31 s after
parallelization).

## Implementation notes (fidelity-critical)

- **Resampling** (`resample.rs`) reimplements PIL's separable BOX / NEAREST / LANCZOS
  (a=3) with PIL's exact coefficient window and `clip8` rounding.
- **ndimage** (`ndimage.rs`) reproduces scipy semantics: 4-connected `label`,
  `binary_fill_holes`, cross-structure morphology (border_value=0), `gaussian_filter`
  (truncate=4, reflect), `uniform_filter`/`median_filter`/`maximum_filter` (reflect).
  - **`binary_propagation` keeps seed pixels even when outside the mask** (verified
    against scipy) — this was the one semantic that, when wrong, collapsed the cluster
    mask from 39% to 6%. Now 100% match.
- **FFT** (`fftutil.rs`) matches numpy `fft2`/`ifft2` (1/N inverse norm) +
  `fftshift`/`ifftshift`/`fftfreq`.
- **CMYK TIFF** (`imageio.rs`) read/write is PIL-compatible (chunky 4×u8, Separated),
  with decoder limits lifted for the ~2.2 GB pages.
- **PDF** (`mrc.rs::write_pdf`) emits the exact content stream of the Python: Flate RGB
  bg XObject, JBIG2 `ImageMask` layers (Decode [0,1]) tinted via `rg`, draw order
  bg → inks → K, page size `W/2400*72` pt.

## Not done / future

- Gabor / k-decoy / smoothed-field screen-probability prototypes (`proto_*.py`) are not
  ported — they are R&D, not in the deployed path. The `geometry` JSON they consume is ported.
- MRC speed: the size-25 `median_filter` and 600 dpi gaussians dominate; a sliding-window
  median and SIMD gaussian would cut the 31 s further (lossless, correctness-preserving).
- Per-page batch driver across all 168 pages (the shell `*_all.sh` scripts can call
  `mrcpipe full` directly).
