mod apply;
mod detect;
mod fftutil;
mod geometry;
mod grade;
mod imageio;
mod mrc;
mod ndimage;
mod npy;
mod pilio;
mod record;
mod resample;
mod screenseg;
mod separate;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand, ValueEnum};

#[derive(Parser)]
#[command(name = "mrcpipe", about = "MRC screening / PDF pipeline (Rust port of the 8608-600 Python)")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Clone, Copy, ValueEnum)]
enum GradeVariant {
    Display,
    Detect,
}

#[derive(Subcommand)]
enum Cmd {
    /// RGB scan PNG -> CMYK TIFF (convert.py separation).
    Separate {
        input_png: String,
        output_tiff: String,
    },
    /// CMYK TIFF -> graded (+optional GCR) CMYK TIFF. Cropping is the FRONT END's job
    /// (01-deskew -> 02-matte -> 03-crop, applied by 04-grade/apply_fullres.py as one affine).
    Grade {
        input_tiff: String,
        output_tiff: String,
        #[arg(long, value_enum, default_value = "display")]
        variant: GradeVariant,
        /// Apply GCR after grading.
        #[arg(long)]
        gcr: bool,
    },
    /// CMYK TIFF -> screen score npy (+ _chan, _cov). detect_screened.py.
    Detect {
        cmyk_tiff: String,
        /// Output base path; writes <out>.npy, <out>_chan.npy, <out>_cov.npy.
        out_base: String,
        #[arg(long, default_value_t = 60)]
        hop: usize,
    },
    /// CMYK TIFF -> per-channel screen geometry JSON. measure_screen_geometry.py.
    Geometry {
        cmyk_tiff: String,
        out_json: String,
        #[arg(long, default_value_t = 2400.0)]
        dpi: f64,
    },
    /// page PNG + score npy -> screened cluster mask PNG (steps 1-6).
    Cluster {
        page_png: String,
        score_npy: String,
        out_mask_png: String,
        #[arg(long, default_value_t = 6.0)]
        thr: f64,
    },
    /// page PNG + score npy -> MRC PDF.
    Mrc {
        page_png: String,
        score_npy: String,
        out_pdf: String,
        #[arg(long, default_value_t = 6.0)]
        thr: f64,
        /// background raster dpi (source assumed 2400 dpi). 200 was the old fixed value; the
        /// measured screen ruling for this issue is 136-159 lpi, which is the real limit.
        #[arg(long, default_value_t = 200.0)]
        bg_dpi: f64,
    },
    /// master scan -> deskewed, matted, A4-cropped, graded CMYK (04-grade/apply_fullres.py).
    ///
    /// With --cache it ALSO writes what `mrc` consumes -- 2400 dpi tile statistics, 600 dpi
    /// Lanczos RGB and 600 dpi Box RGB -- instead of a 200 MB page RGB PNG. See APPLY_PORT.md.
    Apply {
        pages: Vec<u32>,
        #[arg(long, default_value = "/Users/mist/DNB/8609/master_2400")]
        master: String,
        #[arg(long, default_value = "/Users/mist/DNB/8609/tmp/page_geometry.json")]
        geo: String,
        #[arg(long, default_value = "/Users/mist/DNB/8609/tmp/page_geometry")]
        geo_dir: String,
        #[arg(long, default_value = "/Users/mist/DNB/8609/tmp/render/deliver")]
        out: String,
        #[arg(long, default_value = "/Users/mist/Documents/git/64er-magazin.de/tools/img")]
        profiles: String,
        #[arg(long, value_enum, default_value = "display")]
        variant: GradeVariant,
        /// mirror-fill the edge bands (the interior-hole Telea path is NOT ported)
        #[arg(long)]
        inpaint: bool,
        /// also write the UNFILLED detect-graded CMYK the screening analysis reads
        #[arg(long)]
        detect_too: bool,
        /// also write the cached MRC inputs (tile stats + 600 dpi Lanczos/Box RGB)
        #[arg(long)]
        cache: bool,
        /// also write the 2400 dpi page RGB PNG the current `mrc` reads (drop-in for the Python)
        #[arg(long)]
        page_rgb: bool,
        #[arg(long)]
        no_write: bool,
    },
    /// The SAME decisions `mrc` makes (cluster mask, tint, step 7, darkfill, K despeckle, ink
    /// presence) plus the JSONL record, without the descreen FFT / jbig2 / PDF. ~22s a page
    /// against ~47s -- for sweeping decisions across the whole issue.
    Classify {
        page_png: String,
        score_npy: String,
        #[arg(long, default_value_t = 6.0)]
        thr: f64,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Separate { input_png, output_tiff } => {
            let t = std::time::Instant::now();
            let rgb = imageio::read_rgb_png(&input_png)?;
            let cmyk = separate::separate(&rgb);
            imageio::write_cmyk_tiff(&output_tiff, &cmyk)?;
            eprintln!("separate {}x{} -> {} ({:.1}s)", rgb.w, rgb.h, output_tiff, t.elapsed().as_secs_f64());
        }
        Cmd::Grade {
            input_tiff,
            output_tiff,
            variant,
            gcr,
        } => {
            let t = std::time::Instant::now();
            let mut cmyk = imageio::read_cmyk_tiff(&input_tiff)?;
            let lv = match variant {
                GradeVariant::Display => grade::GradeLevels::display(),
                GradeVariant::Detect => grade::GradeLevels::detect(),
            };
            grade::grade_in_place(&mut cmyk, lv);
            if gcr {
                grade::gcr_in_place(&mut cmyk);
            }
            imageio::write_cmyk_tiff(&output_tiff, &cmyk)?;
            eprintln!("grade -> {} ({:.1}s)", output_tiff, t.elapsed().as_secs_f64());
        }
        Cmd::Detect { cmyk_tiff, out_base, hop } => {
            let t = std::time::Instant::now();
            let cmyk = imageio::read_cmyk_tiff(&cmyk_tiff)?;
            let r = detect::detect(&cmyk, hop);
            npy::write_f32(&format!("{}.npy", out_base), &r.fine, &[r.ny, r.nx])?;
            npy::write_f32(&format!("{}_chan.npy", out_base), &r.finec, &[4, r.ny, r.nx])?;
            npy::write_u8(&format!("{}_cov.npy", out_base), &r.cov, &[4, r.ch4, r.cw])?;
            eprintln!(
                "detect map {}x{} -> {}.npy ({:.1}s)",
                r.ny, r.nx, out_base, t.elapsed().as_secs_f64()
            );
        }
        Cmd::Geometry { cmyk_tiff, out_json, dpi } => {
            let t = std::time::Instant::now();
            let cmyk = imageio::read_cmyk_tiff(&cmyk_tiff)?;
            let g = geometry::measure(&cmyk, dpi, cmyk_tiff.clone());
            let val = serde_json::json!({
                "file": g.file,
                "dpi": g.dpi,
                "channels": g.channels,
            });
            std::fs::write(&out_json, serde_json::to_string_pretty(&val)?)
                .with_context(|| format!("write {}", out_json))?;
            eprintln!("geometry -> {} ({:.1}s)", out_json, t.elapsed().as_secs_f64());
        }
        Cmd::Cluster { page_png, score_npy, out_mask_png, thr } => {
            let t = std::time::Instant::now();
            let m = mrc::run_cluster(&page_png, &score_npy, thr as f32)?;
            imageio::write_bilevel_as_gray_png(&out_mask_png, m.w, m.h, &m.mask)?;
            eprintln!("cluster -> {} ({:.1}s)", out_mask_png, t.elapsed().as_secs_f64());
        }
        Cmd::Mrc { page_png, score_npy, out_pdf, thr, bg_dpi } => {
            let t = std::time::Instant::now();
            mrc::run_mrc(&page_png, &score_npy, &out_pdf, thr as f32, bg_dpi as f32)?;
            eprintln!("mrc -> {} ({:.1}s)", out_pdf, t.elapsed().as_secs_f64());
        }
        Cmd::Apply {
            pages,
            master,
            geo,
            geo_dir,
            out,
            profiles,
            variant,
            inpaint,
            detect_too,
            cache,
            page_rgb,
            no_write,
        } => {
            let o = apply::Opts {
                master_dir: master,
                geo_json: geo,
                geo_dir,
                out_dir: out,
                profile_dir: profiles,
                variant_display: matches!(variant, GradeVariant::Display),
                inpaint,
                detect_too,
                cache,
                page_rgb,
                write: !no_write,
            };
            for p in pages {
                let r = apply::run(p, &o)?;
                println!("{}", serde_json::to_string(&r)?);
            }
        }
        Cmd::Classify { page_png, score_npy, thr } => {
            let t = std::time::Instant::now();
            mrc::run_classify(&page_png, &score_npy, thr as f32)?;
            eprintln!("classify done ({:.1}s)", t.elapsed().as_secs_f64());
        }
    }
    Ok(())
}
