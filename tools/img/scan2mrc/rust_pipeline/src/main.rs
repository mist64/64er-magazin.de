mod detect;
mod fftutil;
mod geometry;
mod grade;
mod imageio;
mod mrc;
mod ndimage;
mod npy;
mod record;
mod resample;
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
    /// CMYK TIFF -> graded (+optional crop +GCR) CMYK TIFF.
    Grade {
        input_tiff: String,
        output_tiff: String,
        #[arg(long, value_enum, default_value = "display")]
        variant: GradeVariant,
        /// Apply GCR after grading.
        #[arg(long)]
        gcr: bool,
        /// A4 crop: provide widths.txt value and page id (parity decides gravity).
        #[arg(long)]
        crop_width: Option<usize>,
        #[arg(long)]
        page_id: Option<u32>,
    },
    /// Full graded+cropped+GCR CMYK from a master scan + widths value (mirrors make_*_cmyk.sh).
    FullCmyk {
        master_png: String,
        output_tiff: String,
        #[arg(long)]
        crop_width: usize,
        #[arg(long)]
        page_id: u32,
        #[arg(long, value_enum, default_value = "detect")]
        variant: GradeVariant,
        #[arg(long, default_value_t = true)]
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
    /// page PNG + score npy -> MRC PDF (mrc_hyst8_perio.py).
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
    /// FAST classify-only: page PNG + score npy -> per-cluster step-7 DIAG lines (stdout).
    /// Skips descreen/jbig2/PDF -- for sweeping classification features across pages.
    Classify {
        page_png: String,
        score_npy: String,
        #[arg(long, default_value_t = 6.0)]
        thr: f64,
    },
    /// Full pipeline: master PNG -> detect CMYK (separate+crop, no grade) -> detect score
    /// -> graded RGB page -> MRC PDF. Mirrors the deploy chain end to end.
    Full {
        master_png: String,
        /// graded RGB page (pages/NNN_2400_cropped.png) used by the MRC render.
        page_png: String,
        out_pdf: String,
        #[arg(long)]
        crop_width: usize,
        #[arg(long)]
        page_id: u32,
        /// working dir for intermediate npy/tiff.
        #[arg(long, default_value = ".")]
        work: String,
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
            crop_width,
            page_id,
        } => {
            let t = std::time::Instant::now();
            let mut cmyk = imageio::read_cmyk_tiff(&input_tiff)?;
            let lv = match variant {
                GradeVariant::Display => grade::GradeLevels::display(),
                GradeVariant::Detect => grade::GradeLevels::detect(),
            };
            grade::grade_in_place(&mut cmyk, lv);
            if let (Some(cw), Some(pid)) = (crop_width, page_id) {
                cmyk = grade::a4_crop(&cmyk, cw, pid);
            }
            if gcr {
                grade::gcr_in_place(&mut cmyk);
            }
            imageio::write_cmyk_tiff(&output_tiff, &cmyk)?;
            eprintln!("grade -> {} ({:.1}s)", output_tiff, t.elapsed().as_secs_f64());
        }
        Cmd::FullCmyk {
            master_png,
            output_tiff,
            crop_width,
            page_id,
            variant,
            gcr,
        } => {
            let t = std::time::Instant::now();
            let rgb = imageio::read_rgb_png(&master_png)?;
            let mut cmyk = separate::separate(&rgb);
            let lv = match variant {
                GradeVariant::Display => grade::GradeLevels::display(),
                GradeVariant::Detect => grade::GradeLevels::detect(),
            };
            grade::grade_in_place(&mut cmyk, lv);
            cmyk = grade::a4_crop(&cmyk, crop_width, page_id);
            if gcr {
                grade::gcr_in_place(&mut cmyk);
            }
            imageio::write_cmyk_tiff(&output_tiff, &cmyk)?;
            eprintln!("full-cmyk -> {} ({:.1}s)", output_tiff, t.elapsed().as_secs_f64());
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
        Cmd::Classify { page_png, score_npy, thr } => {
            let t = std::time::Instant::now();
            mrc::run_classify(&page_png, &score_npy, thr as f32)?;
            eprintln!("classify done ({:.1}s)", t.elapsed().as_secs_f64());
        }
        Cmd::Full {
            master_png,
            page_png,
            out_pdf,
            crop_width,
            page_id,
            work,
            thr,
        } => {
            let t = std::time::Instant::now();
            std::fs::create_dir_all(&work)?;
            // 1) detection-input CMYK = separate + A4 crop (NO grade, matches make_cmyk_crop.sh)
            let rgb = imageio::read_rgb_png(&master_png)?;
            let cmyk = separate::separate(&rgb);
            let cmyk = grade::a4_crop(&cmyk, crop_width, page_id);
            // 2) detect -> score npy (+ _cov)
            let r = detect::detect(&cmyk, 60);
            let base = format!("{}/full_{:03}", work, page_id);
            npy::write_f32(&format!("{}.npy", base), &r.fine, &[r.ny, r.nx])?;
            npy::write_u8(&format!("{}_cov.npy", base), &r.cov, &[4, r.ch4, r.cw])?;
            eprintln!("  [full] detect done ({:.1}s)", t.elapsed().as_secs_f64());
            // 3) MRC PDF from the graded RGB page + score
            mrc::run_mrc(&page_png, &format!("{}.npy", base), &out_pdf, thr as f32, 200.0)?;
            eprintln!("full -> {} ({:.1}s total)", out_pdf, t.elapsed().as_secs_f64());
        }
    }
    Ok(())
}
