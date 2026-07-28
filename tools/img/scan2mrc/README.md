# scan2mrc — full raw-scan → MRC pipeline (ordered stages)

Each stage is an index-prefixed subdir, run in order. Detection stages work on the 150/600-dpi
thumbnails (fast, angle/position are scale-invariant); the heavy full-res apply happens once, in Rust/
libvips, reading the per-page metadata the detection stages write.

Stages:
  01-deskew/  measure text skew (projection-variance, Method A). Text is the orientation ground truth.
  02-matte/   find the paper boundary; mark everything outside (bed, insert, sheet-edge shadow)
              as unknown/alpha. Nothing about the backing is hardcoded — it is calibrated per
              issue. DONE at thumb level: top 176/176, bottom 176/176, sides 120/116 clean.
  02b-opposite-page/  the neighbour page and the binder-clip holes: colour-boundary spine where
              one exists (41/176), clip-hole line as the fallback. DONE at thumb level.
  03-crop/    A4 window anchored on the 64'er wordmark; per-parity offsets fitted to minimise
              alpha inside the window. DONE at thumb level.
  04-grade/   (todo) per-channel CMYK grade (levels detected per-issue).
  05-detect/  (todo) screen-periodicity score.
  06-mrc/     (todo) MRC render (existing rust_pipeline).

Metadata (small, git-able, per issue) is the contract between detection and apply:
skew_deg, crop box, unknown mask spec, grade levels — never bake decisions into the pixels early.
Conventions: measurements are resolution-relative (1px@600dpi == 4px@2400dpi, same mm); fabricate
nothing until an explicit fill step.

## Composing and reviewing the stack

    stack_render.py            01+02+02b composed -> tmp/stack600/NNN.png  (RGBA, deskewed)
    stack_render.py --review   the same, but cuts marked with MAGENTA HAIRLINES and nothing
                               removed -> tmp/review/. A tint wash states the verdict but hides
                               the evidence under itself: the pixels that decide whether a cut is
                               right are the few either side of the line, and a wash recolours
                               exactly those.
    verify_alpha.py            checks EVERY rendered page: RGBA, alpha strictly {0,255} (a partial
                               value would be a soft fringe, and alpha means UNKNOWN), coverage in
                               band, every canvas border marked. 176/176, 0 failures.

RGB is rotated bicubic and ALPHA nearest, then recombined — rotating RGBA together interpolates
the alpha into a fringe and bleeds the black transparent-fill into the page border underneath it.

## Shared core

    linefit.py   Both boundary problems are the same problem: find a line so all of one material
                 is on one side and as little of the other as possible. 02-matte and 02b differ
                 only in how CANDIDATES are produced and in the fire test; the fit lives here once.
                 It is a MODE, not a regression, so no outlier fence / coverage percentile /
                 smoothing is needed — every one of those was tried and each broke something else.
