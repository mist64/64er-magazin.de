mod apply;
mod demod;
mod demoddbg;
mod fftutil;
mod grade;
mod imageio;
mod ndimage;
mod npy;
mod pilio;
mod record;
mod render;
mod resample;
mod route;
mod routedbg;
mod screen;
mod screendbg;
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
    /// STAGE A: unclipped CMYK TIFF -> the per-ink screen field (npy) + a debug PNG.
    ///
    /// Measures only -- nothing is decided or routed here. Feed it the DETECT-grade (unclipped),
    /// pre-GCR separation: the display grade throws away exactly the faint-screen energy this
    /// stage exists to find. See screen.rs.
    Screen {
        cmyk_tiff: String,
        /// output base: writes <base>.npy and <base>.png
        out_base: String,
    },
    /// STAGE B: unclipped CMYK + the stage-A field -> contone (dot area) + coherence, and the
    /// debug PNG that shows which ink is halftone and which is a mark. See demod.rs.
    Demod {
        /// DISPLAY-graded, GCR'd CMYK. Everything after stage A reads this: only the screen FIELD
        /// needs the unclipped planes, and it is already measured by then.
        display_tiff: String,
        field_npy: String,
        /// output base: writes <base>_tone.npy and <base>.png
        out_base: String,
    },
    /// STAGE C: route every part of the page to its destination and draw it. See route.rs.
    Route {
        /// DISPLAY-graded, GCR'd CMYK
        display_tiff: String,
        field_npy: String,
        /// output base: writes <base>.png
        out_base: String,
    },
    /// STAGE D: the MRC PDF -- CMYK contone background + per-ink JBIG2 stencils. See render.rs.
    Mrc {
        /// DISPLAY-graded, GCR'd CMYK
        display_tiff: String,
        field_npy: String,
        out_pdf: String,
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
        /// also write the display-graded but NOT GCR'd CMYK the screening analysis wants
        #[arg(long)]
        nogcr_too: bool,
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
        Cmd::Screen { cmyk_tiff, out_base } => {
            let t = std::time::Instant::now();
            let cmyk = imageio::read_cmyk_tiff(&cmyk_tiff)?;
            let f = screen::measure(&cmyk);
            screen::write_npy(&format!("{}.npy", out_base), &f)?;
            let png = format!("{}.png", out_base);
            screendbg::write_png(&png, &cmyk, &f)?;
            screendbg::write_prob_png(&format!("{}_prob.png", out_base), &f)?;
            let stem = std::path::Path::new(&cmyk_tiff)
                .file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            println!("{}", screendbg::summarise(&stem, &f));
            eprintln!("screen -> {} ({:.1}s)", png, t.elapsed().as_secs_f64());
        }
        Cmd::Demod { display_tiff, field_npy, out_base } => {
            let t = std::time::Instant::now();
            let disp = imageio::read_cmyk_tiff(&display_tiff)?;
            let f = screen::read_npy(&field_npy)?;
            let div = demod::contone_divisor(&f);
            let geo: Vec<demod::Geometry> = (0..4).map(|ci| demod::filled_geometry(&f, ci)).collect();
            let tone = demod::contone(&disp, div, &f, &geo);
            let coh = demod::coherence(&disp, &f, &geo);
            let cmyk = disp;
            let mut flat = Vec::with_capacity(4 * tone.w * tone.h);
            for pl in &tone.ink {
                flat.extend(pl.iter().copied());
            }
            npy::write_u8(&format!("{}_tone.npy", out_base), &flat, &[4, tone.h, tone.w])?;
            let png = format!("{}.png", out_base);
            demoddbg::write_png(&png, &cmyk, &tone, &coh)?;
            let stem = std::path::Path::new(&display_tiff)
                .file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            println!("{}", demoddbg::summarise(&stem, &tone, &coh));
            eprintln!("demod -> {} (div {}, {:.1}s)", png, div, t.elapsed().as_secs_f64());
        }
        Cmd::Route { display_tiff, field_npy, out_base } => {
            let t = std::time::Instant::now();
            let disp = imageio::read_cmyk_tiff(&display_tiff)?;
            let f = screen::read_npy(&field_npy)?;
            let div = demod::contone_divisor(&f);
            let geo: Vec<demod::Geometry> = (0..4).map(|ci| demod::filled_geometry(&f, ci)).collect();
            let tone = demod::contone(&disp, div, &f, &geo);
            let coh = demod::coherence(&disp, &f, &geo);
            let r = route::route(&f, &tone, &coh, &disp);
            let png = format!("{}.png", out_base);
            routedbg::write_png(&png, &disp, &r)?;
            routedbg::write_outline_png(&format!("{}_type.png", out_base), &disp, &r)?;
            routedbg::write_stages_png(&format!("{}_stages.png", out_base), &disp, &r)?;
            let stem = std::path::Path::new(&display_tiff)
                .file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            println!("{}", route::summarise(&stem, &r));
            for a in &r.areas {
                println!(
                    "   area {:3} {:12} blocks {:5} lpi {:5.0} mean C{:.0} M{:.0} Y{:.0} K{:.0} std {:.1}",
                    a.id, a.class.name(), a.blocks, a.lpi,
                    a.mean[0], a.mean[1], a.mean[2], a.mean[3],
                    a.std.iter().cloned().fold(0.0f32, f32::max)
                );
            }
            eprintln!("route -> {} ({:.1}s)", png, t.elapsed().as_secs_f64());
        }
        Cmd::Mrc { display_tiff, field_npy, out_pdf } => {
            let t = std::time::Instant::now();
            let disp = imageio::read_cmyk_tiff(&display_tiff)?;
            let f = screen::read_npy(&field_npy)?;
            let div = demod::contone_divisor(&f);
            let geo: Vec<demod::Geometry> = (0..4).map(|ci| demod::filled_geometry(&f, ci)).collect();
            let tone = demod::contone(&disp, div, &f, &geo);
            let coh = demod::coherence(&disp, &f, &geo);
            let r = route::route(&f, &tone, &coh, &disp);
            let stem = std::path::Path::new(&out_pdf)
                .file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            let work = format!("{}/.mrctmp_{}",
                std::path::Path::new(&out_pdf).parent()
                    .map(|p| p.to_string_lossy().to_string()).unwrap_or_else(|| ".".into()), stem);
            println!("{}", route::summarise(&stem, &r));
            let sz = render::write_pdf(&out_pdf, disp.w, disp.h, &tone, &r, &work)?;
            let _ = std::fs::remove_dir_all(&work);
            println!("{}", render::summarise(&stem, &sz, &tone));
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
            nogcr_too,
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
                nogcr_too,
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
