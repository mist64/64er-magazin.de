mod apply;
mod fftutil;
mod grade;
mod imageio;
mod ndimage;
mod npy;
mod pilio;
mod record;
mod resample;
mod separate;

use anyhow::Result;
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
    /// (01-deskew -> 02-matte -> 03-crop, applied by `apply` as one affine).
    Grade {
        input_tiff: String,
        output_tiff: String,
        #[arg(long, value_enum, default_value = "display")]
        variant: GradeVariant,
        /// Apply GCR after grading.
        #[arg(long)]
        gcr: bool,
    },
    /// master scan -> deskewed, matted, A4-cropped, graded CMYK.
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
    }
    Ok(())
}
