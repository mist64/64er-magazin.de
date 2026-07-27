# scan2mrc — full raw-scan → MRC pipeline (ordered stages)

Each stage is an index-prefixed subdir, run in order. Detection stages work on the 150/600-dpi
thumbnails (fast, angle/position are scale-invariant); the heavy full-res apply happens once, in Rust/
libvips, reading the per-page metadata the detection stages write.

Stages:
  01-deskew/  measure text skew (projection-variance, Method A). Text is the orientation ground truth.
  02-matte/   find the paper boundary; mark everything outside (bed wedges, yellow, neighbor strip,
              clip holes) as unknown/alpha. Keep every genuine page pixel; no A4 trim yet.
  03-crop/    (todo) final A4 crop, aligned on the text; trim outer excess.
  04-grade/   (todo) per-channel CMYK grade (levels detected per-issue).
  05-detect/  (todo) screen-periodicity score.
  06-mrc/     (todo) MRC render (existing rust_pipeline).

Metadata (small, git-able, per issue) is the contract between detection and apply:
skew_deg, crop box, unknown mask spec, grade levels — never bake decisions into the pixels early.
Conventions: measurements are resolution-relative (1px@600dpi == 4px@2400dpi, same mm); fabricate
nothing until an explicit fill step.
