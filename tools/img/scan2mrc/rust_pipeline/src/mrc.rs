//! Stages 3-5: mrc_hyst8_perio.py port.
//! Cluster mask (steps 1-6), per-cluster image/text classification (step 7),
//! K + accent-ink JBIG2 layers, descreened colour bg, solid-rect fills, PDF assembly.

use crate::imageio::{self, Rgb};
use crate::ndimage;
use crate::npy;
use crate::record::Recorder;
use crate::resample::{nearest_plane_u8, resample_plane_f32, Filter};
use crate::fftutil;
use anyhow::{Context, Result};
use num_complex::Complex32;
use std::io::Write;
use std::process::Command;

const HOP: usize = 60;

// Canonical sRGB per ink.
fn canon(nm: &str) -> [u8; 3] {
    match nm {
        "K" => [39, 36, 37],
        "C" => [0, 172, 236],
        "M" => [202, 0, 136],
        "Y" => [255, 242, 45],
        "MY" => [204, 34, 41],
        "MC" => [50, 52, 142],
        "CY" => [51, 164, 87],
        _ => [0, 0, 0],
    }
}
fn ink_hue(nm: &str) -> f64 {
    match nm {
        "MY" => 0.0,
        "Y" => 60.0,
        "CY" => 120.0,
        "C" => 180.0,
        "MC" => 240.0,
        "M" => 300.0,
        _ => 0.0,
    }
}
const INK_NAMES: [&str; 6] = ["MY", "Y", "CY", "C", "MC", "M"];

const SAT_BLACK: f32 = 60.0;
const LUMA_BLACK: f32 = 100.0;
// K-mask thresholds (text-on-tint fixes; no-op on white paper by construction):
const MARK_LUMA: f32 = 165.0;     // mark ceiling (was 185): drops light-gray edge ramp over tints
const MARK_CONTRAST: f32 = 60.0;  // mark must be this much darker than local-max bg (was 45)
const SHARP_SUPPORT: f32 = 140.0; // `sharp` needs a dark 3x3 neighbour -> rejects lone screen dots
const INK_SAT: f32 = 80.0;
const MIN_CC: usize = 15;
const MIN_K: usize = 6;
const GROW: f32 = 4.0;
const TONE: f32 = 150.0;

// === DARK-FILL (REVERSED graphics) -> IMAGE  (issue G1). A reversed box = white text/content on a
// SOLID dark neutral fill. Such fills are NOT screened, so they miss the screened cluster mask M and
// go straight to the bilevel K layer -> the fill becomes a SOLID BLACK BLOB and the white lettering
// is lost (p104 "AGS-Farbbaender", p78/p107 reversed headers). Fix: detect these regions at 600dpi
// (mw x mh, where luma/sat live) and force them into IMAGE so they render via the descreened contone
// bg instead of K. A connected dark-neutral component (luma<DARK & sat<SAT) is a reversed FILL (not
// bold text / a table outline / a solid photo) iff, over its bbox:
//   dark_frac   = comp_px / bbox_area   > DARKFILL_FRAC   (dark INK fills the bbox -> rejects loose
//                 bold TEXT, whose strokes leave most of the bbox white, AND thin frame/table
//                 OUTLINES, whose interior is one big enclosed hole, not ink)
//   filled_frac = fill_holes(comp)_px / bbox_area > DARKFILL_FILLED (solid/rectangular once interior
//                 holes are filled -> rejects spread-out text runs)
//   hole_frac   = (filled_px - comp_px) / bbox_area in (HOLES_LO, HOLES_HI) -> enclosed bright
//                 content inside (reversed white lettering): LO rejects a solid blob/rule with no
//                 text; HI rejects a thin frame whose interior is mostly empty white (table/ad border).
// Env-overridable. See env_f reads in run_mrc step 7.
const DARKFILL_DARK: f32 = 90.0;      // luma ceiling: dark neutral ink (the fill)
const DARKFILL_SAT: f32 = 60.0;       // sat ceiling: NEUTRAL (kills coloured red/blue boxes)
const DARKFILL_MINPX: usize = 20000;  // min component px @600 (~0.06% page; > step-7's 8000 = a genuine FILL)
const DARKFILL_FRAC: f64 = 0.45;      // dark_frac floor: dark ink fills the bbox
// filled_frac floor: the hole-filled shape must essentially BE its bbox, i.e. a box. 0.70 also
// admitted bold headline type -- a glyph with counters ("8", "O", "D", "a") reads as a dark shape
// with enclosed bright content, so it was promoted to IMAGE, left the K stencil, and came back
// soft from the 150 dpi background (p062 "zum C 128" lost its 8: dark 0.743, filled 0.812,
// holes 0.069 -- inside every old gate). Measured over 34 promotions on 23 pages of 8609 the two
// populations do not touch: headline glyphs 0.804-0.886, real reversed boxes 0.965-0.997
// ("298.00", "WIMBLEDON/Kassette 25.-", "NEU", "ariolasoft"). 0.93 sits in that gap. Dark PHOTOS
// (0.737-0.930) also stop being promoted, which costs nothing: they are screened, so step 7 puts
// them in IMAGE anyway -- this promoter exists only for UNSCREENED solid fills.
const DARKFILL_FILLED: f64 = 0.93;
const DARKFILL_HOLES_LO: f64 = 0.05;  // enclosed-bright floor: reversed text present
const DARKFILL_HOLES_HI: f64 = 0.55;  // enclosed-bright ceiling: not a hollow frame

pub struct ClusterOut {
    pub w: usize, // NX
    pub h: usize, // NY
    pub mask: Vec<bool>,
}

/// Round to 4 decimals for the record. Full f64 precision would make every row noisy to diff for
/// digits that carry no decision; 4 is finer than any gate in this file.
fn r2(v: f64) -> f64 {
    (v * 10000.0).round() / 10000.0
}

fn env_f(name: &str, def: f32) -> f32 {
    std::env::var(name).ok().and_then(|s| s.parse().ok()).unwrap_or(def)
}
fn env_i(name: &str, def: i64) -> i64 {
    std::env::var(name).ok().and_then(|s| s.parse().ok()).unwrap_or(def)
}

/// Steps 1-6 -> tile-grid cluster mask M (NY x NX).
fn build_cluster(
    src_luma_tiles: &LumaTiles,
    score: &[f32],
    ny: usize,
    nx: usize,
    thr: f32,
) -> Vec<bool> {
    let extend = env_i("EXTEND", 0) as usize;
    // +1 registration roll: np.pad(score,((1,0),(1,0)),'edge')[:NY,:NX]
    let mut sc = vec![0.0f32; ny * nx];
    for y in 0..ny {
        for x in 0..nx {
            let sy = if y == 0 { 0 } else { y - 1 };
            let sx = if x == 0 { 0 } else { x - 1 };
            sc[y * nx + x] = score[sy * nx + sx];
        }
    }
    let tluma = &src_luma_tiles.tluma;
    let black_t = &src_luma_tiles.black_t;
    // s1 = binary_propagation(score>THR, mask=(score>GROW)&(tluma<TONE))
    let seed: Vec<bool> = sc.iter().map(|&v| v > thr).collect();
    let mask1: Vec<bool> = (0..ny * nx)
        .map(|i| sc[i] > GROW && tluma[i] < TONE)
        .collect();
    let s1 = ndimage::binary_propagation(&seed, &mask1, nx, ny);
    if std::env::var("MRCDBG").is_ok() {
        let frac = |m: &[bool]| m.iter().filter(|&&b| b).count() as f64 / (nx * ny) as f64 * 100.0;
        eprintln!(
            "DBG seed{:.2} mask1{:.2} s1{:.2}",
            frac(&seed),
            frac(&mask1),
            frac(&s1)
        );
    }
    // label, discard-small
    let (lbl, n) = ndimage::label(&s1, nx, ny);
    let sz = ndimage::component_sizes(&lbl, n);
    let boxes = ndimage::find_objects(&lbl, n, nx, ny);
    let area_thr = 0.012 * ny as f64 * nx as f64;
    // OPTIONAL (env-gated, default OFF -> byte-identical): density-based keep. A real small photo is
    // DENSELY screened (high seed fraction); bloom is sparse. Keep small clusters whose seed density
    // >= DISCARD_DENSITY and area >= DISCARD_MINPX, regardless of size -> rescues small ad photos that
    // the size filter drops to bilevel-K, without keeping sparse bloom. See QA_FINDINGS.md synthesis.
    let dens_keep = env_f("DISCARD_DENSITY", 0.0) as f64; // 0.0 = disabled
    let dens_minpx = env_i("DISCARD_MINPX", 6) as f64;
    let mut seedcnt = vec![0u32; n + 1];
    if dens_keep > 0.0 {
        for i in 0..ny * nx {
            if seed[i] && lbl[i] != 0 {
                seedcnt[lbl[i] as usize] += 1;
            }
        }
    }
    let mut keep = vec![false; n + 1];
    for k in 1..=n {
        if let Some((y0, y1, x0, x1)) = boxes[k - 1] {
            let h = y1 - y0 + 1;
            let w = x1 - x0 + 1;
            let area = sz[k - 1] as f64;
            let dense = dens_keep > 0.0
                && area >= dens_minpx
                && (seedcnt[k] as f64 / area) >= dens_keep;
            if area >= area_thr || (w.max(h) >= 30 && area / (w * h) as f64 >= 0.6) || dense {
                keep[k] = true;
            }
        }
    }
    let s2: Vec<bool> = lbl.iter().map(|&l| l != 0 && keep[l as usize]).collect();
    // s3 = grow the screened mask across connected near-black tiles (bridge dark gaps in a photo).
    // Default = unlimited geodesic propagation (original). OPTIONAL (env BLACKBRIDGE>0): bound the
    // bridge to N cells from the seed so it patches small dark gaps but can't flood a whole dark/
    // text-dense block (fixes p117 SICOS over-grow). Default 0 = byte-identical.
    let mask3: Vec<bool> = (0..ny * nx).map(|i| s2[i] || black_t[i]).collect();
    let bridge = env_i("BLACKBRIDGE", 0);
    let s3 = if bridge <= 0 {
        ndimage::binary_propagation(&s2, &mask3, nx, ny)
    } else {
        let mut cur = s2.clone();
        for _ in 0..bridge {
            let d = ndimage::binary_dilation(&cur, nx, ny, 1);
            cur = (0..ny * nx).map(|i| d[i] && mask3[i]).collect();
        }
        cur
    };
    let s4 = ndimage::binary_fill_holes(&s3, nx, ny);
    // rect-snap
    let mut s5 = s4.clone();
    let (lbl2, n2) = ndimage::label(&s4, nx, ny);
    let boxes2 = ndimage::find_objects(&lbl2, n2, nx, ny);
    let sz2 = ndimage::component_sizes(&lbl2, n2);
    for k in 1..=n2 {
        if let Some((y0, y1, x0, x1)) = boxes2[k - 1] {
            let barea = ((x1 - x0 + 1) * (y1 - y0 + 1)) as f64;
            if sz2[k - 1] as f64 / barea >= 0.85 {
                for y in y0..=y1 {
                    for x in x0..=x1 {
                        s5[y * nx + x] = true;
                    }
                }
            }
        }
    }
    let mut mm = if extend > 0 {
        ndimage::binary_dilation(&s5, nx, ny, extend)
    } else {
        s5.clone()
    };
    // white-barrier
    let white = &src_luma_tiles.white;
    let cut: Vec<bool> = (0..ny * nx).map(|i| mm[i] && !white[i]).collect();
    let (lblc, _nc) = ndimage::label(&cut, nx, ny);
    let mut seeded = std::collections::HashSet::new();
    for i in 0..ny * nx {
        if sc[i] > thr && cut[i] {
            seeded.insert(lblc[i]);
        }
    }
    seeded.remove(&0);
    for i in 0..ny * nx {
        if lblc[i] > 0 && !seeded.contains(&lblc[i]) {
            mm[i] = false;
        }
    }
    let mm = ndimage::binary_fill_holes(&mm, nx, ny);
    if std::env::var("MRCDBG").is_ok() {
        let frac = |m: &[bool]| m.iter().filter(|&&b| b).count() as f64 / (nx * ny) as f64 * 100.0;
        eprintln!(
            "DBG s2{:.2} s3{:.2} s4{:.2} s5{:.2} M{:.2}",
            frac(&s2),
            frac(&s3),
            frac(&s4),
            frac(&s5),
            frac(&mm)
        );
    }
    mm
}

struct LumaTiles {
    tluma: Vec<f32>,
    black_t: Vec<bool>,
    white: Vec<bool>,
}

/// Tile the page luma into NY x NX HOP x HOP blocks -> per-tile mean, black fraction,
/// white fraction (mirrors mrc_hyst8_perio.py L26-27,49).
fn luma_tiles(luma_full: &[f32], w: usize, ny: usize, nx: usize) -> LumaTiles {
    let mut tluma = vec![0.0f32; ny * nx];
    let mut black_t = vec![false; ny * nx];
    let mut white = vec![false; ny * nx];
    for ty in 0..ny {
        for tx in 0..nx {
            let mut sum = 0.0f64;
            let mut blackn = 0u32;
            let mut whiten = 0u32;
            for yy in 0..HOP {
                let row = (ty * HOP + yy) * w + tx * HOP;
                for xx in 0..HOP {
                    let v = luma_full[row + xx];
                    sum += v as f64;
                    if v < 45.0 {
                        blackn += 1;
                    }
                    if v > 235.0 {
                        whiten += 1;
                    }
                }
            }
            let cnt = (HOP * HOP) as f64;
            tluma[ty * nx + tx] = (sum / cnt) as f32;
            black_t[ty * nx + tx] = (blackn as f64 / cnt) > 0.70;
            white[ty * nx + tx] = (whiten as f64 / cnt) > 0.50;
        }
    }
    LumaTiles { tluma, black_t, white }
}

/// Convert RGB page to grayscale (PIL "L" = 0.299R+0.587G+0.114B, rounded).
fn rgb_to_luma_full(rgb: &Rgb) -> Vec<f32> {
    let n = rgb.w * rgb.h;
    let mut out = vec![0.0f32; n];
    for i in 0..n {
        let r = rgb.data[i * 3] as f32;
        let g = rgb.data[i * 3 + 1] as f32;
        let b = rgb.data[i * 3 + 2] as f32;
        // PIL L uses integer rounding: (R*299 + G*587 + B*114)/1000 truncated
        out[i] = ((r as u32 * 299 + g as u32 * 587 + b as u32 * 114) / 1000) as f32;
    }
    out
}

pub fn run_cluster(page_png: &str, score_npy: &str, thr: f32) -> Result<ClusterOut> {
    let src = imageio::read_rgb_png(page_png)?;
    let (score, shape) = npy::read_f32(score_npy)?;
    let ny = shape[0];
    let nx = shape[1];
    let luma = rgb_to_luma_full(&src);
    let lt = luma_tiles(&luma, src.w, ny, nx);
    let mask = build_cluster(&lt, &score, ny, nx, thr);
    Ok(ClusterOut { w: nx, h: ny, mask })
}

// ----- HSV-ish hue/sat/luma helpers on a downsampled RGB (600dpi) -----
struct Rgb600 {
    w: usize,
    h: usize,
    r: Vec<f32>,
    g: Vec<f32>,
    b: Vec<f32>,
}

/// rgb @600 from LANCZOS resize, as int16 in Python (rounded). We resample then clip8.
fn rgb600_lanczos(src: &Rgb, mw: usize, mh: usize) -> Rgb600 {
    let mut rch = vec![0.0f32; src.w * src.h];
    let mut gch = vec![0.0f32; src.w * src.h];
    let mut bch = vec![0.0f32; src.w * src.h];
    for i in 0..src.w * src.h {
        rch[i] = src.data[i * 3] as f32;
        gch[i] = src.data[i * 3 + 1] as f32;
        bch[i] = src.data[i * 3 + 2] as f32;
    }
    let rr = resample_plane_f32(&rch, src.w, src.h, mw, mh, Filter::Lanczos);
    let gg = resample_plane_f32(&gch, src.w, src.h, mw, mh, Filter::Lanczos);
    let bb = resample_plane_f32(&bch, src.w, src.h, mw, mh, Filter::Lanczos);
    // PIL Lanczos resize of an 8-bit image clips to u8; np.int16 keeps the value.
    let clip = |v: &Vec<f32>| -> Vec<f32> {
        v.iter().map(|&x| crate::resample::clip8(x) as f32).collect()
    };
    Rgb600 {
        w: mw,
        h: mh,
        r: clip(&rr),
        g: clip(&gg),
        b: clip(&bb),
    }
}

fn compute_sat_luma(rgb: &Rgb600) -> (Vec<f32>, Vec<f32>) {
    let n = rgb.w * rgb.h;
    let mut sat = vec![0.0f32; n];
    let mut luma = vec![0.0f32; n];
    for i in 0..n {
        let mx = rgb.r[i].max(rgb.g[i]).max(rgb.b[i]);
        let mn = rgb.r[i].min(rgb.g[i]).min(rgb.b[i]);
        sat[i] = mx - mn;
        luma[i] = 0.299 * rgb.r[i] + 0.587 * rgb.g[i] + 0.114 * rgb.b[i];
    }
    (sat, luma)
}

/// hue in degrees 0..360 from RGB (matches the Python's max-channel branch logic).
fn compute_hue(r: &[f32], g: &[f32], b: &[f32]) -> Vec<f32> {
    let n = r.len();
    let mut hue = vec![0.0f32; n];
    for i in 0..n {
        let mx = r[i].max(g[i]).max(b[i]);
        let mn = r[i].min(g[i]).min(b[i]);
        let d = (mx - mn).max(1.0);
        let h = if mx == r[i] {
            ((g[i] - b[i]) / d).rem_euclid(6.0)
        } else if mx == g[i] {
            (b[i] - r[i]) / d + 2.0
        } else {
            (r[i] - g[i]) / d + 4.0
        };
        hue[i] = (h * 60.0).rem_euclid(360.0);
    }
    hue
}

fn jbig2(work: &str, name: &str, mask: &[bool], w: usize, h: usize) -> Result<Vec<u8>> {
    let png = format!("{}/{}.png", work, name);
    imageio::write_bilevel_as_gray_png(&png, w, h, mask)?;
    let out = Command::new("jbig2")
        .args(["-p", &png])
        .output()
        .context("run jbig2")?;
    if !out.status.success() {
        anyhow::bail!("jbig2 failed: {}", String::from_utf8_lossy(&out.stderr));
    }
    Ok(out.stdout)
}

/// FFT low-pass tap helper (smoothstep guard band) on a (mw x mh) field, shifted layout.
fn tap(mw: usize, mh: usize, r0: f64, r1: f64) -> Vec<f32> {
    let cy = mh / 2;
    let cx = mw / 2;
    let mut w = vec![0.0f32; mw * mh];
    for iy in 0..mh {
        for ix in 0..mw {
            let dy = iy as f64 - cy as f64;
            let dx = ix as f64 - cx as f64;
            let cyc = (dy * dy + dx * dx).sqrt() / mh as f64 * 600.0;
            let mut wf = ((r1 - cyc) / (r1 - r0)).clamp(0.0, 1.0);
            wf = 0.5 - 0.5 * (std::f64::consts::PI * wf).cos();
            if cyc <= r0 {
                wf = 1.0;
            }
            if cyc >= r1 {
                wf = 0.0;
            }
            w[iy * mw + ix] = wf as f32;
        }
    }
    w
}

fn lp_field(ch: &[f32], mw: usize, mh: usize, tap_shifted: &[f32]) -> Vec<f32> {
    let mut data = fftutil::fft2_real(ch, mw, mh);
    let shifted = fftutil::fftshift2(&data, mw, mh);
    let mut weighted = vec![Complex32::new(0.0, 0.0); mw * mh];
    for i in 0..mw * mh {
        weighted[i] = shifted[i] * tap_shifted[i];
    }
    let rx = fftutil::ifftshift_indices(mw);
    let ry = fftutil::ifftshift_indices(mh);
    for y in 0..mh {
        for x in 0..mw {
            data[y * mw + x] = weighted[ry[y] * mw + rx[x]];
        }
    }
    fftutil::fft2_inplace(&mut data, mw, mh, true);
    data.iter().map(|c| c.re).collect()
}


/// Everything the MRC pipeline DECIDES about a page, and the fields the render needs to act on it.
///
/// The split is deliberate: `analyze` decides, `run_mrc` renders. Both `mrc` and `classify` call
/// `analyze`, so the cheap sweep and the shipping path make the same decisions BY CONSTRUCTION --
/// they are not two implementations kept in sync. (They were, until this refactor: step 7 existed
/// twice in this file, verbatim down to the format string, and darkfill existed only in the render
/// path, which is why probing it needed a third copy in Python.)
pub struct Analysis {
    pub mw: usize,
    pub mh: usize,
    pub rgb600: Rgb600,
    pub sat: Vec<f32>,
    pub luma: Vec<f32>,
    pub hue: Vec<f32>,
    pub lumaf: Vec<f32>,
    pub satf: Vec<f32>,
    pub m600: Vec<bool>,
    pub image: Vec<bool>,
    pub tintmask: Vec<bool>,
    pub black: Vec<bool>,
    pub inkpix: Vec<bool>,
    pub present: Vec<&'static str>,
}

/// Decide everything: cluster mask (steps 1-6), chromatic tint, step 7 image-vs-text, the darkfill
/// reversed-box promotion, the K mask and its despeckle, and which accent inks are present.
///
/// Deliberately excludes the expensive render-only work -- the descreen FFT, the jbig2 encodes and
/// the PDF assembly -- which is what makes a full-issue decision sweep affordable.
pub fn analyze(
    src: &Rgb,
    score: &[f32],
    ny: usize,
    nx: usize,
    thr: f32,
    score_npy: &str,
    page: &str,
    rec: &mut Recorder,
) -> Result<Analysis> {
    let w = src.w;
    let h = src.h;
    let kmed = env_i("KMED", 5).max(1) as usize;
    let kopen = env_i("KOPEN", 0) as usize;
    let _ = page;

    // ---- cluster mask M (steps 1-6) ----
    let luma_full = rgb_to_luma_full(src);
    let lt = luma_tiles(&luma_full, w, ny, nx);
    let m_tile = build_cluster(&lt, &score, ny, nx, thr);

    // ---- M600: NEAREST resize of (M*255) to mw x mh, >128 ----
    let mw = w / 4;
    let mh = h / 4;
    let m_u8: Vec<u8> = m_tile.iter().map(|&b| if b { 255 } else { 0 }).collect();
    // M is at tile resolution (NX x NY); the Python builds M as a full-res bool? No:
    // M is NY x NX (tile grid). M600 = resize of (M*255) image (NX x NY) to (mw x mh).
    let m600_u8 = nearest_plane_u8(&m_u8, nx, ny, mw, mh);
    let mut m600: Vec<bool> = m600_u8.iter().map(|&v| v > 128).collect();

    // ---- rgb @600 (LANCZOS) + sat/luma/hue ----
    let rgb600 = rgb600_lanczos(src, mw, mh);
    let (sat, luma) = compute_sat_luma(&rgb600);
    let hue = compute_hue(&rgb600.r, &rgb600.g, &rgb600.b);
    let lumaf = ndimage::median_filter(&luma, mw, mh, kmed);
    let satf = ndimage::median_filter(&sat, mw, mh, kmed);

    // ---- chromatic-tint detection (blurred copy) ----
    let rb = ndimage::gaussian_filter(&rgb600.r, mw, mh, 8.0);
    let gb = ndimage::gaussian_filter(&rgb600.g, mw, mh, 8.0);
    let bb = ndimage::gaussian_filter(&rgb600.b, mw, mh, 8.0);
    let (satb, lumab) = {
        let n = mw * mh;
        let mut s = vec![0.0f32; n];
        let mut l = vec![0.0f32; n];
        for i in 0..n {
            let mx = rb[i].max(gb[i]).max(bb[i]);
            let mn = rb[i].min(gb[i]).min(bb[i]);
            s[i] = mx - mn;
            l[i] = 0.299 * rb[i] + 0.587 * gb[i] + 0.114 * bb[i];
        }
        (s, l)
    };
    let hueb = compute_hue(&rb, &gb, &bb);
    let cc: Vec<f32> = (0..mw * mh)
        .map(|i| (gb[i].min(bb[i]) - rb[i]).clamp(0.0, 255.0))
        .collect();
    let mc: Vec<f32> = (0..mw * mh)
        .map(|i| (rb[i].min(bb[i]) - gb[i]).clamp(0.0, 255.0))
        .collect();
    let yc: Vec<f32> = (0..mw * mh)
        .map(|i| (rb[i].min(gb[i]) - bb[i]).clamp(0.0, 255.0))
        .collect();

    let mut tintmask = vec![false; mw * mh];
    let (lblm, nmc) = ndimage::label(&m600, mw, mh);
    {
        // per-component stats
        let mut comps: Vec<Vec<usize>> = vec![Vec::new(); nmc + 1];
        for i in 0..mw * mh {
            if lblm[i] != 0 {
                comps[lblm[i] as usize].push(i);
            }
        }
        for k in 1..=nmc {
            let idx = &comps[k];
            if idx.len() < 3000 {
                continue;
            }
            // colp = satb>15 ; colp.mean()
            let colp: Vec<bool> = idx.iter().map(|&i| satb[i] > 15.0).collect();
            let colp_mean = colp.iter().filter(|&&b| b).count() as f64 / idx.len() as f64;
            if colp_mean <= 0.05 {
                continue;
            }
            // mean lumab over colp; skip if dark colour (mean<140 = content image)
            let mut lsum = 0.0;
            let mut ln = 0usize;
            for (j, &i) in idx.iter().enumerate() {
                if colp[j] {
                    lsum += lumab[i] as f64;
                    ln += 1;
                }
            }
            if ln == 0 || (lsum / ln as f64) < 140.0 {
                continue;
            }
            // hue circular dispersion over colp
            let mut cs = 0.0;
            let mut sn = 0.0;
            for (j, &i) in idx.iter().enumerate() {
                if colp[j] {
                    let a = (hueb[i] as f64).to_radians();
                    cs += a.cos();
                    sn += a.sin();
                }
            }
            cs /= ln as f64;
            sn /= ln as f64;
            let rv = (cs * cs + sn * sn).sqrt();
            let disp = (((-2.0 * rv.max(1e-9).ln()).max(0.0)).sqrt()).to_degrees();
            if disp >= 25.0 {
                continue;
            }
            // all CMY present check
            let mean_over = |arr: &[f32]| -> f64 {
                idx.iter().map(|&i| arr[i] as f64).sum::<f64>() / idx.len() as f64
            };
            let present = (mean_over(&cc) > 5.0) as i32
                + (mean_over(&mc) > 5.0) as i32
                + (mean_over(&yc) > 5.0) as i32;
            if present >= 3 {
                continue;
            }
            // mostly neutral mid-tone gate
            let neutral_frac = idx
                .iter()
                .filter(|&&i| satb[i] < 30.0 && lumab[i] > 70.0 && lumab[i] < 200.0)
                .count() as f64
                / idx.len() as f64;
            if neutral_frac > 0.45 {
                continue;
            }
            for &i in idx {
                tintmask[i] = true;
            }
        }
    }

    // ---- step 7: image vs text-on-bg (per-cluster, pure CMYK) ----
    let tcv = env_f("TCV", 30.0);
    let ts = env_f("TS", 22.0);
    let tt = env_f("TT", 14.0);
    let vote = env_f("VOTE", 0.40);
    // load _cov.npy from <npy>_cov.npy
    let cov_path = {
        let p = score_npy.strip_suffix(".npy").unwrap_or(score_npy);
        format!("{}_cov.npy", p)
    };
    let mut image = vec![false; mw * mh];
    if let Ok((cov, cshape)) = npy::read_u8(&cov_path) {
        let cmw = cshape[2];
        let cmh = cshape[1];
        let plane = cmw * cmh;
        // cov channels are at mw x mh already (W/4 x H/4); assume equal.
        let cf = |ci: usize| -> Vec<f32> {
            cov[ci * plane..(ci + 1) * plane]
                .iter()
                .map(|&v| v as f32)
                .collect()
        };
        let (c_, m_, y_, k_) = (cf(0), cf(1), cf(2), cf(3));
        let neu: Vec<f32> = (0..plane).map(|i| c_[i].min(m_[i]).min(y_[i])).collect();
        let ccx: Vec<f32> = (0..plane).map(|i| c_[i] - neu[i]).collect();
        let mcx: Vec<f32> = (0..plane).map(|i| m_[i] - neu[i]).collect();
        let ycx: Vec<f32> = (0..plane).map(|i| y_[i] - neu[i]).collect();
        let lc = ndimage::local_std(&ccx, cmw, cmh, 37);
        let lm = ndimage::local_std(&mcx, cmw, cmh, 37);
        let lyc = ndimage::local_std(&ycx, cmw, cmh, 37);
        let colorvar: Vec<f32> = (0..plane).map(|i| lc[i].max(lm[i]).max(lyc[i])).collect();
        let maxcmy: Vec<f32> = (0..plane).map(|i| ccx[i].max(mcx[i]).max(ycx[i])).collect();
        let satmean = ndimage::uniform_filter(&maxcmy, cmw, cmh, 37);
        let kmedf = ndimage::median_filter(&k_, cmw, cmh, 25);
        let tonevar = ndimage::local_std(&kmedf, cmw, cmh, 37);
        // candidate (sized at cmw x cmh; m600 is mw x mh; assume equal dims)
        let cand: Vec<bool> = (0..plane)
            .map(|i| {
                (colorvar[i] > tcv || (satmean[i] > ts && tonevar[i] > tt)) && m600.get(i).copied().unwrap_or(false)
            })
            .collect();
        // B6 continuous-tone OBJECT trigger (rescues faint/grayscale photos the vote misses):
        // erode 4px to remove thin text strokes, then measure internal variation of the surviving
        // body. bodyK=std(K) over eroded mid-tone region cleanly separates photos (>=~36) from
        // flat boxes/tables/headlines (<=~24); objfK gate drops dark-scan-margin artifacts.
        let bk = env_f("BK", 32.0) as f64;
        let objf = env_f("OBJF", 0.30) as f64;
        let bc = env_f("BC", 34.0) as f64;
        let midk: Vec<bool> = (0..plane)
            .map(|i| k_[i] > 20.0 && k_[i] < 238.0 && m600.get(i).copied().unwrap_or(false))
            .collect();
        let midc: Vec<bool> = (0..plane)
            .map(|i| maxcmy[i] > 12.0 && m600.get(i).copied().unwrap_or(false))
            .collect();
        let erk = ndimage::binary_erosion(&midk, cmw, cmh, 4);
        let erc = ndimage::binary_erosion(&midc, cmw, cmh, 4);
        // std of `vals` over the subset of `idx` where `mask` is true
        let stdv = |idx: &[usize], vals: &[f32], mask: &[bool]| -> (f64, usize) {
            let (mut s, mut s2, mut n) = (0.0f64, 0.0f64, 0usize);
            for &i in idx {
                if mask.get(i).copied().unwrap_or(false) {
                    let v = vals[i] as f64;
                    s += v;
                    s2 += v * v;
                    n += 1;
                }
            }
            if n == 0 {
                return (0.0, 0);
            }
            let m = s / n as f64;
            ((s2 / n as f64 - m * m).max(0.0).sqrt(), n)
        };
        let diag = std::env::var("MRC_DIAG").is_ok();
        // per-cluster vote over M600
        let mut comps: Vec<Vec<usize>> = vec![Vec::new(); nmc + 1];
        for i in 0..mw * mh {
            if lblm[i] != 0 {
                comps[lblm[i] as usize].push(i);
            }
        }
        let mut nb6 = 0;
        for k in 1..=nmc {
            let idx = &comps[k];
            if idx.len() < 8000 {
                continue;
            }
            let frac = idx.iter().filter(|&&i| cand.get(i).copied().unwrap_or(false)).count() as f64
                / idx.len() as f64;
            let mut is_img = frac >= vote as f64;
            let (sdk, nk) = stdv(idx, &k_, &erk);
            let objfk = nk as f64 / idx.len() as f64;
            let (sdc, _nc) = stdv(idx, &maxcmy, &erc);
            if !is_img {
                if nk > 200 && sdk >= bk && objfk >= objf {
                    is_img = true;
                    nb6 += 1;
                } else if stdv(idx, &maxcmy, &erc).1 > 200 && sdc >= bc {
                    is_img = true;
                    nb6 += 1;
                }
            }
            if is_img {
                for &i in idx {
                    image[i] = true;
                }
            }
            // bbox + feature means: needed by the record ALWAYS (the differ cannot recover a gate
            // value once the binary has changed), and by the DIAG print when it is on.
            let (mut x0, mut y0, mut x1, mut y1) = (mw, mh, 0usize, 0usize);
            for &i in idx {
                let (x, y) = (i % mw, i / mw);
                x0 = x0.min(x);
                y0 = y0.min(y);
                x1 = x1.max(x);
                y1 = y1.max(y);
            }
            let n = idx.len() as f64;
            let cvm = idx.iter().map(|&i| colorvar[i] as f64).sum::<f64>() / n;
            let sm = idx.iter().map(|&i| satmean[i] as f64).sum::<f64>() / n;
            let tvm = idx.iter().map(|&i| tonevar[i] as f64).sum::<f64>() / n;
            rec.push(serde_json::json!({
                "kind": "cluster", "page": page, "cid": k, "area": idx.len(),
                "bbox": [x0, y0, x1, y1],
                "layer": if is_img { "bg" } else { "k" },
                "verdict": if is_img { "IMAGE" } else { "TEXT" },
                "rescue": is_img && frac < vote as f64,
                "vote": r2(frac), "cv": r2(cvm), "s": r2(sm), "tv": r2(tvm),
                "bodyK": r2(sdk), "objfK": r2(objfk), "bodyC": r2(sdc),
            }));
            if diag {
                // bbox normalized to [0,1] in (mw,mh) = the page frame, for cluster cropping
                eprintln!(
                    "DIAG cid={} area={} bbox={:.4},{:.4},{:.4},{:.4} cx={:.3} cy={:.3} vote={:.2} cv={:.1} s={:.1} tv={:.1} bodyK={:.1} objfK={:.2} bodyC={:.1} verdict={}",
                    k, idx.len(),
                    x0 as f64 / mw as f64, y0 as f64 / mh as f64, x1 as f64 / mw as f64, y1 as f64 / mh as f64,
                    (x0 + x1) as f64 / 2.0 / mw as f64, (y0 + y1) as f64 / 2.0 / mh as f64,
                    frac, cvm, sm, tvm, sdk, objfk, sdc, if is_img { "IMAGE" } else { "TEXT" }
                );
            }
        }
        eprintln!("  step7: {} clusters, +{} via bodyK (BK={} OBJF={} BC={})", nmc, nb6, bk, objf, bc);
    } else {
        eprintln!("WARNING: no cov cache ({}) -> step 7 disabled", cov_path);
    }

    // === DARK-FILL (reversed graphics) -> IMAGE (issue G1). See constant block at top. Runs on the
    // 600dpi luma/sat (raw, not median-filtered) regardless of step 7; promotes solid dark-fill
    // reversed boxes into IMAGE so they descreen instead of becoming a solid-black K blob with the
    // white text lost. ===
    {
        let darkfrac_env = env_f("DARKFILL_FRAC", DARKFILL_FRAC as f32) as f64;
        let filled_env = env_f("DARKFILL_FILLED", DARKFILL_FILLED as f32) as f64;
        let holes_lo = env_f("DARKFILL_HOLES", DARKFILL_HOLES_LO as f32) as f64;
        let holes_hi = env_f("DARKFILL_HOLES_HI", DARKFILL_HOLES_HI as f32) as f64;
        let dark_t = env_f("DARKFILL_DARK", DARKFILL_DARK);
        let sat_t = env_f("DARKFILL_SAT", DARKFILL_SAT);
        let minpx = env_i("DARKFILL_MINPX", DARKFILL_MINPX as i64) as usize;
        let dfill: Vec<bool> = (0..mw * mh).map(|i| luma[i] < dark_t && sat[i] < sat_t).collect();
        let (dlbl, dn) = ndimage::label(&dfill, mw, mh);
        let dsz = ndimage::component_sizes(&dlbl, dn);
        let dboxes = ndimage::find_objects(&dlbl, dn, mw, mh);
        let mut promoted = 0usize;
        for k in 1..=dn {
            let cpx = dsz[k - 1] as usize;
            if cpx < minpx {
                continue;
            }
            let (y0, y1, x0, x1) = match dboxes[k - 1] {
                Some(b) => b,
                None => continue,
            };
            let bw_ = x1 - x0 + 1;
            let bh_ = y1 - y0 + 1;
            let ba = (bw_ * bh_) as f64;
            let dark_frac = cpx as f64 / ba;
            if dark_frac <= darkfrac_env {
                // recorded without filled/hole: the hole-fill is the expensive part and this
                // candidate never reaches it, so those stay null rather than being invented.
                rec.push(serde_json::json!({
                    "kind": "darkfill", "page": page, "cid": k, "px": cpx,
                    "bbox": [x0, y0, x1, y1], "layer": "k", "promoted": false,
                    "dark_frac": r2(dark_frac),
                    "filled_frac": serde_json::Value::Null, "hole_frac": serde_json::Value::Null,
                }));
                continue; // loose text / hollow frame -> skip
            }
            // build sub-mask of this component over its bbox, fill holes, count
            let mut sub = vec![false; bw_ * bh_];
            for y in y0..=y1 {
                for x in x0..=x1 {
                    if dlbl[y * mw + x] as usize == k {
                        sub[(y - y0) * bw_ + (x - x0)] = true;
                    }
                }
            }
            let filled = ndimage::binary_fill_holes(&sub, bw_, bh_);
            let fp = filled.iter().filter(|&&b| b).count();
            let filled_frac = fp as f64 / ba;
            let hole_frac = (fp - cpx) as f64 / ba;
            let promote = filled_frac > filled_env && hole_frac > holes_lo && hole_frac < holes_hi;
            // EVERY candidate is recorded, not just the promoted ones: the near-misses are how a
            // gate change is judged, and the p062 "8" sat 0.12 inside a boundary nobody had looked at.
            rec.push(serde_json::json!({
                "kind": "darkfill", "page": page, "cid": k, "px": cpx,
                "bbox": [x0, y0, x1, y1],
                "layer": if promote { "bg" } else { "k" },
                "promoted": promote,
                "dark_frac": r2(dark_frac), "filled_frac": r2(filled_frac), "hole_frac": r2(hole_frac),
            }));
            if promote {
                // Force the FILL's bbox into BOTH image (-> no K blob) AND m600 (-> the descreened
                // contone bg is actually PAINTED here; otherwise the bg whiteout `bg[~m150]=255`
                // would leave the box blank, since reversed fills sit OUTSIDE the screened mask M).
                // Use the filled bbox SHAPE (not just the thin ink) so the reversed white lettering
                // inside the box is covered too.
                for yy in 0..bh_ {
                    for xx in 0..bw_ {
                        if filled[yy * bw_ + xx] {
                            let i = (y0 + yy) * mw + (x0 + xx);
                            image[i] = true;
                            m600[i] = true;
                        }
                    }
                }
                promoted += 1;
            }
        }
        eprintln!(
            "  darkfill(G1): {}/{} dark comps promoted to IMAGE (DARK={} SAT={} FRAC={:.2} FILLED={:.2} HOLES={:.2}-{:.2})",
            promoted, dn, dark_t, sat_t, darkfrac_env, filled_env, holes_lo, holes_hi
        );
    }

    // ---- K (black) layer ----
    let bgl = ndimage::maximum_filter(&luma, mw, mh, 9);
    let bgd = ndimage::minimum_filter(&luma, mw, mh, 3);   // darkest 3x3 neighbour (lone-dot support test)
    let mark: Vec<bool> = (0..mw * mh)
        .map(|i| satf[i] < SAT_BLACK && lumaf[i] < MARK_LUMA && lumaf[i] < bgl[i] - MARK_CONTRAST)
        .collect();
    let sharp: Vec<bool> = (0..mw * mh)
        .map(|i| sat[i] < SAT_BLACK && luma[i] < LUMA_BLACK && bgd[i] < SHARP_SUPPORT)
        .collect();
    let mut black: Vec<bool> = (0..mw * mh)
        .map(|i| (mark[i] || sharp[i]) && !image[i])
        .collect();
    if kopen > 0 {
        black = ndimage::binary_opening(&black, mw, mh, kopen);
    }
    // despeckle: drop components < MIN_K
    {
        let (lbk, nk) = ndimage::label(&black, mw, mh);
        if nk > 0 {
            let szk = ndimage::component_sizes(&lbk, nk);
            // RECORD what the despeckle throws away. Most of it is single-pixel scan noise and
            // recording each one would bury the file, so: an aggregate row always, plus an
            // individual row per dropped component at or above KDROP_REC (default 4 px @600) --
            // the size range where a drop could still be a real mark (a thin serif, a period)
            // rather than a speck. Same gate that has already cost us one shipped bug at the
            // cluster level, so it is worth being able to see it.
            let recmin = env_i("KDROP_REC", 4) as u64;
            let mut dropped = 0usize;
            let mut cx = vec![0u64; nk + 1];
            let mut cy = vec![0u64; nk + 1];
            if rec.enabled() {
                for (i, &l) in lbk.iter().enumerate() {
                    if l != 0 && szk[l as usize - 1] < MIN_K as u64 {
                        cx[l as usize] += (i % mw) as u64;
                        cy[l as usize] += (i / mw) as u64;
                    }
                }
            }
            for k in 1..=nk {
                let s = szk[k - 1];
                if s >= MIN_K as u64 {
                    continue;
                }
                dropped += 1;
                if rec.enabled() && s >= recmin {
                    rec.push(serde_json::json!({
                        "kind": "kdrop", "page": page, "cid": k, "px": s,
                        "centroid": [cx[k] / s, cy[k] / s],
                        "layer": "dropped",
                    }));
                }
            }
            rec.push(serde_json::json!({
                "kind": "kdrop_total", "page": page, "components": nk, "dropped": dropped,
                "min_k": MIN_K, "recorded_above": recmin,
            }));
            black = lbk
                .iter()
                .map(|&l| l != 0 && szk[l as usize - 1] >= MIN_K as u64)
                .collect();
        }
    }
    let crisp: Vec<bool> = m600.iter().map(|&v| !v).collect();
    let inkpix: Vec<bool> = (0..mw * mh)
        .map(|i| crisp[i] && !black[i] && sat[i] >= INK_SAT)
        .collect();

    // present accent inks
    let mut present: Vec<&str> = Vec::new();
    for nm in INK_NAMES {
        let h0 = ink_hue(nm);
        let mut cnt = 0usize;
        let mut tot = 0usize;
        for i in 0..mw * mh {
            if inkpix[i] {
                tot += 1;
                let dd = (((hue[i] as f64 - h0 + 540.0).rem_euclid(360.0)) - 180.0).abs();
                if dd < 25.0 {
                    cnt += 1;
                }
            }
        }
        if tot > 0 && (cnt as f64 / tot as f64) > 0.05 {
            present.push(nm);
        }
    }
    eprintln!("present accent inks: {:?}", present);
    rec.push(serde_json::json!({
        "kind": "page", "page": page, "mw": mw, "mh": mh, "inks": present,
        "image_frac": r2(image.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64),
        "screen_frac": r2(m600.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64),
        "tint_frac": r2(tintmask.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64),
        "k_frac": r2(black.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64),
    }));


    Ok(Analysis { mw, mh, rgb600, sat, luma, hue, lumaf, satf, m600, image, tintmask, black, inkpix,
                  present })
}


/// FAST classify-only path: runs `analyze` -- the identical decisions the render makes -- and
/// writes the record, skipping the descreen FFT, the jbig2 ink layers and the PDF assembly. For
/// sweeping decisions across the whole issue cheaply (~22s a page against ~47s for a full render).
pub fn run_classify(page_png: &str, score_npy: &str, thr: f32) -> Result<()> {
    let src = imageio::read_rgb_png(page_png)?;
    let (score, shape) = npy::read_f32(score_npy)?;
    let (ny, nx) = (shape[0], shape[1]);
    let page = page_stem(page_png);
    let mut rec = Recorder::new(record_path(score_npy, ".npy", "_classify.jsonl"));
    let _a = analyze(&src, &score, ny, nx, thr, score_npy, &page, &mut rec)?;
    rec.flush()?;
    Ok(())
}

/// The page identity carried in every record row: the file stem with any of our suffixes stripped,
/// so `154_page_rgb.png` and `154.png` record as the same page and their runs can be differed.
fn page_stem(path: &str) -> String {
    let s = std::path::Path::new(path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    for suf in ["_page_rgb", "_rgb", "_page"] {
        if let Some(t) = s.strip_suffix(suf) {
            return t.to_string();
        }
    }
    s
}

/// Where the record goes: MRC_RECORD if set, else derived from the output the run already names,
/// so a baseline exists without anyone having to remember to ask for one.
fn record_path(base: &str, strip: &str, add: &str) -> Option<String> {
    if let Ok(p) = std::env::var("MRC_RECORD") {
        return if p.is_empty() { None } else { Some(p) };
    }
    Some(format!("{}{}", base.strip_suffix(strip).unwrap_or(base), add))
}


pub fn run_mrc(page_png: &str, score_npy: &str, out_pdf: &str, thr: f32, bg_dpi: f32) -> Result<()> {
    let src = imageio::read_rgb_png(page_png)?;
    let w = src.w;
    let h = src.h;
    let (score, shape) = npy::read_f32(score_npy)?;
    let ny = shape[0];
    let nx = shape[1];

    // work dir
    let out_dir = std::path::Path::new(out_pdf)
        .parent()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_default();
    let stem = std::path::Path::new(out_pdf)
        .file_stem()
        .unwrap()
        .to_string_lossy()
        .to_string();
    let work = if out_dir.is_empty() {
        format!(".mrctmp_{}", stem)
    } else {
        format!("{}/.mrctmp_{}", out_dir, stem)
    };
    std::fs::create_dir_all(&work)?;


    // ---- DECIDE (shared with `classify`: one implementation, no sync to maintain) ----
    let page = page_stem(page_png);
    let mut rec = Recorder::new(record_path(out_pdf, ".pdf", ".jsonl"));
    let Analysis { mw, mh, rgb600: _rgb600, sat, luma, hue, lumaf, satf, m600, image, tintmask,
                   black, inkpix, present } =
        analyze(&src, &score, ny, nx, thr, score_npy, &page, &mut rec)?;
    let _ = (&sat, &luma, &lumaf, &satf);

    // ---- DESCREEN ONCE: BOX 2400->600 then guard-band Hann low-pass ----
    let mut rch = vec![0.0f32; w * h];
    let mut gch = vec![0.0f32; w * h];
    let mut bch = vec![0.0f32; w * h];
    for i in 0..w * h {
        rch[i] = src.data[i * 3] as f32;
        gch[i] = src.data[i * 3 + 1] as f32;
        bch[i] = src.data[i * 3 + 2] as f32;
    }
    let ir = resample_plane_f32(&rch, w, h, mw, mh, Filter::Box);
    let ig = resample_plane_f32(&gch, w, h, mw, mh, Filter::Box);
    let ib = resample_plane_f32(&bch, w, h, mw, mh, Filter::Box);
    let t_y = tap(mw, mh, 80.0, 100.0);
    let t_c = tap(mw, mh, 30.0, 50.0);
    let yi: Vec<f32> = (0..mw * mh)
        .map(|i| 0.299 * ir[i] + 0.587 * ig[i] + 0.114 * ib[i])
        .collect();
    let cbi: Vec<f32> = (0..mw * mh).map(|i| ib[i] - yi[i]).collect();
    let cri: Vec<f32> = (0..mw * mh).map(|i| ir[i] - yi[i]).collect();
    let dy = lp_field(&yi, mw, mh, &t_y);
    let dcb = lp_field(&cbi, mw, mh, &t_c);
    let dcr = lp_field(&cri, mw, mh, &t_c);
    let drf: Vec<f32> = (0..mw * mh).map(|i| dy[i] + dcr[i]).collect();
    let dbf: Vec<f32> = (0..mw * mh).map(|i| dy[i] + dcb[i]).collect();
    let dgf: Vec<f32> = (0..mw * mh)
        .map(|i| (dy[i] - 0.299 * drf[i] - 0.114 * dbf[i]) / 0.587)
        .collect();

    let scrf: Vec<bool> = (0..mw * mh).map(|i| m600[i] && !image[i]).collect();

    // build ink layers
    struct Layer {
        col: [u8; 3],
        data: Vec<u8>,
    }
    let mut layers: Vec<Layer> = Vec::new();
    for nm in &present {
        let h0 = ink_hue(nm);
        let dd: Vec<f64> = (0..mw * mh)
            .map(|i| (((hue[i] as f64 - h0 + 540.0).rem_euclid(360.0)) - 180.0).abs())
            .collect();
        let mut near = vec![true; mw * mh];
        for o in &present {
            if o != nm {
                let h_o = ink_hue(o);
                for i in 0..mw * mh {
                    let ddo = (((hue[i] as f64 - h_o + 540.0).rem_euclid(360.0)) - 180.0).abs();
                    near[i] = near[i] && dd[i] <= ddo;
                }
            }
        }
        let mut sel: Vec<bool> = (0..mw * mh)
            .map(|i| inkpix[i] && near[i] && dd[i] < 30.0)
            .collect();
        // CC area gate
        let (lblc, nc) = ndimage::label(&sel, mw, mh);
        if nc > 0 {
            let szc = ndimage::component_sizes(&lblc, nc);
            sel = lblc
                .iter()
                .map(|&l| l != 0 && szc[l as usize - 1] >= MIN_CC as u64)
                .collect();
        }
        if sel.iter().any(|&b| b) {
            let data = jbig2(&work, &format!("ink_{}", nm), &sel, mw, mh)?;
            layers.push(Layer {
                col: canon(nm),
                data,
            });
        }
    }
    let kdata = jbig2(&work, "k", &black, mw, mh)?;

    // ---- colour background, at bg_dpi ----
    // The source page is 2400 dpi, so the divisor is 2400/bg_dpi (12 -> 200 dpi, 16 -> 150).
    // The contone limit is set by the halftone, not by us: the screen discarded everything above
    // ~ruling/2, so ~150-160 dpi carries all the information the paper still holds. Anything
    // above that is empty interpolation that costs bytes -- and the background is ~94% of the
    // file, so this is the only size knob that matters.
    let div = (2400.0 / bg_dpi).round().max(1.0) as usize;
    let bw = w / div;
    let bh = h / div;
    let bg_r = resample_plane_f32(&clip_field(&drf), mw, mh, bw, bh, Filter::Box);
    let bg_g = resample_plane_f32(&clip_field(&dgf), mw, mh, bw, bh, Filter::Box);
    let bg_b = resample_plane_f32(&clip_field(&dbf), mw, mh, bw, bh, Filter::Box);
    let mut bg = vec![0u8; bw * bh * 3];
    for i in 0..bw * bh {
        bg[i * 3] = crate::resample::clip8(bg_r[i]);
        bg[i * 3 + 1] = crate::resample::clip8(bg_g[i]);
        bg[i * 3 + 2] = crate::resample::clip8(bg_b[i]);
    }
    // M150 white-out
    let m600_u8b: Vec<u8> = m600.iter().map(|&b| if b { 255 } else { 0 }).collect();
    let m150_u8 = nearest_plane_u8(&m600_u8b, mw, mh, bw, bh);
    let m150: Vec<bool> = m150_u8.iter().map(|&v| v > 128).collect();
    for i in 0..bw * bh {
        if !m150[i] {
            bg[i * 3] = 255;
            bg[i * 3 + 1] = 255;
            bg[i * 3 + 2] = 255;
        }
    }
    // text inpaint (normalized convolution)
    let black_u8: Vec<u8> = black.iter().map(|&b| if b { 255 } else { 0 }).collect();
    let tk_u8 = nearest_plane_u8(&black_u8, mw, mh, bw, bh);
    let tk0: Vec<bool> = tk_u8.iter().map(|&v| v > 128).collect();
    let tk = ndimage::binary_dilation(&tk0, bw, bh, 2);
    let wmask: Vec<f32> = tk.iter().map(|&b| if b { 0.0 } else { 1.0 }).collect();
    let den = ndimage::gaussian_filter(&wmask, bw, bh, 5.0);
    for c in 0..3 {
        let chan: Vec<f32> = (0..bw * bh).map(|i| bg[i * 3 + c] as f32 * wmask[i]).collect();
        let num = ndimage::gaussian_filter(&chan, bw, bh, 5.0);
        for i in 0..bw * bh {
            if tk[i] {
                let v = num[i] / den[i].max(1e-6);
                bg[i * 3 + c] = crate::resample::clip8(v);
            }
        }
    }

    eprintln!(
        "image {:.1}%  screened {:.1}%  tint regions {}",
        image.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64 * 100.0,
        m600.iter().filter(|&&b| b).count() as f64 / (mw * mh) as f64 * 100.0,
        ndimage::label(&tintmask, mw, mh).1,
    );
    // ---- solid-rectangle fills ----
    let rect = env_i("RECT", 1);
    if rect != 0 {
        let nr = solid_rects(&mut bg, bw, bh, &tintmask, &scrf, mw, mh);
        eprintln!("solid rectangles: {}", nr);
    }

    // ---- PDF assembly ----
    let bgdata = {
        use flate2::write::ZlibEncoder;
        use flate2::Compression;
        let mut e = ZlibEncoder::new(Vec::new(), Compression::new(9));
        e.write_all(&bg)?;
        e.finish()?
    };
    write_pdf(out_pdf, w, h, bw, bh, &bgdata, mw, mh, &kdata, &layers.iter().map(|l| (l.col, l.data.clone())).collect::<Vec<_>>())?;
    eprintln!(
        "saved {} inks {:?} total {}K",
        out_pdf,
        present,
        std::fs::metadata(out_pdf)?.len() / 1024
    );
    // Output sizes are a decision outcome too -- a fix that quietly doubles the K layer should be
    // visible in the diff, not only in a directory listing.
    rec.push(serde_json::json!({
        "kind": "output", "page": page, "bg_dpi": bg_dpi,
        "bytes": {"bg": bgdata.len(), "k": kdata.len(),
                  "ink": layers.iter().map(|l| l.data.len()).sum::<usize>(),
                  "pdf": std::fs::metadata(out_pdf)?.len()},
    }));
    rec.flush()?;
    Ok(())
}

fn clip_field(f: &[f32]) -> Vec<f32> {
    f.iter().map(|&v| v.clamp(0.0, 255.0)).collect()
}

/// Solid-rectangle fills (chromatic tints + neutral grey). Mirrors L196-264.
fn solid_rects(
    bg: &mut [u8],
    bw: usize,
    bh: usize,
    tintmask: &[bool],
    scrf: &[bool],
    mw: usize,
    mh: usize,
) -> usize {
    let mut nrect = 0usize;
    let n = bw * bh;
    let bf_r: Vec<f32> = (0..n).map(|i| bg[i * 3] as f32).collect();
    let bf_g: Vec<f32> = (0..n).map(|i| bg[i * 3 + 1] as f32).collect();
    let bf_b: Vec<f32> = (0..n).map(|i| bg[i * 3 + 2] as f32).collect();
    let bs: Vec<f32> = (0..n)
        .map(|i| {
            let mx = bf_r[i].max(bf_g[i]).max(bf_b[i]);
            let mn = bf_r[i].min(bf_g[i]).min(bf_b[i]);
            mx - mn
        })
        .collect();
    let bhh = compute_hue(&bf_r, &bf_g, &bf_b);
    let lu: Vec<f32> = (0..n)
        .map(|i| 0.299 * bf_r[i] + 0.587 * bf_g[i] + 0.114 * bf_b[i])
        .collect();
    // tint200 = NEAREST resize of tintmask to bw x bh
    let tm_u8: Vec<u8> = tintmask.iter().map(|&b| if b { 255 } else { 0 }).collect();
    let tint200_u8 = nearest_plane_u8(&tm_u8, mw, mh, bw, bh);
    let tint200: Vec<bool> = tint200_u8.iter().map(|&v| v > 128).collect();

    let near_hue = |h: f32, h0: f32, t: f32| -> bool {
        ((h - h0).abs()).min(360.0 - (h - h0).abs()) < t
    };
    let edge = |p: &[f32], f: f32| -> (usize, usize) {
        let mx = p.iter().cloned().fold(f32::MIN, f32::max);
        let thr = mx * f;
        let idx: Vec<usize> = (0..p.len()).filter(|&i| p[i] > thr).collect();
        if idx.is_empty() {
            (0, p.len() - 1)
        } else {
            (idx[0], idx[idx.len() - 1])
        }
    };
    let median_of = |vals: &mut Vec<f32>| -> f32 {
        if vals.is_empty() {
            return 0.0;
        }
        vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let m = vals.len();
        if m % 2 == 1 {
            vals[m / 2]
        } else {
            (vals[m / 2 - 1] + vals[m / 2]) / 2.0
        }
    };

    // chromatic tint rects
    let (lblt, nt) = ndimage::label(&tint200, bw, bh);
    {
        let mut comps: Vec<Vec<usize>> = vec![Vec::new(); nt + 1];
        for i in 0..n {
            if lblt[i] != 0 {
                comps[lblt[i] as usize].push(i);
            }
        }
        for k in 1..=nt {
            let idx = &comps[k];
            if idx.len() < 300 {
                continue;
            }
            let (mut y0, mut y1, mut x0, mut x1) = (bh, 0usize, bw, 0usize);
            for &i in idx {
                let y = i / bw;
                let x = i % bw;
                y0 = y0.min(y);
                y1 = y1.max(y);
                x0 = x0.min(x);
                x1 = x1.max(x);
            }
            let selc: Vec<usize> = idx.iter().cloned().filter(|&i| bs[i] > 10.0).collect();
            if selc.len() < 100 {
                continue;
            }
            // mean hue (circular)
            let (mut cs, mut sn) = (0.0f64, 0.0f64);
            for &i in &selc {
                let a = (bhh[i] as f64).to_radians();
                cs += a.cos();
                sn += a.sin();
            }
            let h0 = (sn.atan2(cs).to_degrees().rem_euclid(360.0)) as f32;
            let mut fsat_v: Vec<f32> = selc.iter().map(|&i| bs[i]).collect();
            let fsat = median_of(&mut fsat_v);
            let mut flum_v: Vec<f32> = selc.iter().map(|&i| lu[i]).collect();
            let flum = median_of(&mut flum_v);
            // colmask
            let colmask: Vec<bool> = (0..n)
                .map(|i| {
                    near_hue(bhh[i], h0, 22.0)
                        && bs[i] >= (8.0f32).max(0.45 * fsat)
                        && (lu[i] - flum).abs() <= 45.0
                })
                .collect();
            let pad = 4usize;
            let sy0 = y0.saturating_sub(pad);
            let sy1 = (y1 + pad).min(bh - 1) + 1;
            let sx0 = x0.saturating_sub(pad);
            let sx1 = (x1 + pad).min(bw - 1) + 1;
            let sh = sy1 - sy0;
            let sw = sx1 - sx0;
            // row means / col means of colmask over the sub-window
            let mut rowm = vec![0.0f32; sh];
            let mut colm = vec![0.0f32; sw];
            for yy in 0..sh {
                let mut s = 0.0;
                for xx in 0..sw {
                    if colmask[(sy0 + yy) * bw + (sx0 + xx)] {
                        s += 1.0;
                        colm[xx] += 1.0;
                    }
                }
                rowm[yy] = s / sw as f32;
            }
            for xx in 0..sw {
                colm[xx] /= sh as f32;
            }
            let (t_, bm_) = edge(&rowm, 0.5);
            let (l_, r_) = edge(&colm, 0.5);
            let py0 = sy0 + t_;
            let py1 = sy0 + bm_ + 1;
            let px0 = sx0 + l_;
            let px1 = sx0 + r_ + 1;
            // rfill
            let mut fillc = 0usize;
            let mut tot = 0usize;
            let mut lu_vals = Vec::new();
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    tot += 1;
                    if colmask[i] {
                        fillc += 1;
                    }
                    lu_vals.push(lu[i]);
                }
            }
            let rfill = fillc as f64 / tot.max(1) as f64;
            if rfill < 0.70 || (px1 - px0) < 8 || (py1 - py0) < 8 {
                continue;
            }
            // luma std over rect
            let mean = lu_vals.iter().sum::<f32>() / lu_vals.len() as f32;
            let var = lu_vals.iter().map(|&v| (v - mean) * (v - mean)).sum::<f32>()
                / lu_vals.len() as f32;
            if var.sqrt() > 14.0 {
                continue;
            }
            // colour = median of bg over incol
            let mut col = [0u8; 3];
            for c in 0..3 {
                let mut vals: Vec<f32> = Vec::new();
                for yy in py0..py1 {
                    for xx in px0..px1 {
                        let i = yy * bw + xx;
                        if colmask[i] {
                            vals.push(bg[i * 3 + c] as f32);
                        }
                    }
                }
                col[c] = median_of(&mut vals) as u8;
            }
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    bg[i * 3] = col[0];
                    bg[i * 3 + 1] = col[1];
                    bg[i * 3 + 2] = col[2];
                }
            }
            nrect += 1;
        }
    }

    // neutral grey rects
    let scr_u8: Vec<u8> = scrf.iter().map(|&b| if b { 255 } else { 0 }).collect();
    let screen_u8 = nearest_plane_u8(&scr_u8, mw, mh, bw, bh);
    let screen: Vec<bool> = screen_u8.iter().map(|&v| v > 128).collect();
    let mut graym: Vec<bool> = (0..n)
        .map(|i| screen[i] && bs[i] < 25.0 && lu[i] > 200.0 && lu[i] < 252.0)
        .collect();
    graym = ndimage::binary_closing(&graym, bw, bh, 2);
    let (lblg, ng) = ndimage::label(&graym, bw, bh);
    {
        let mut comps: Vec<Vec<usize>> = vec![Vec::new(); ng + 1];
        for i in 0..n {
            if lblg[i] != 0 {
                comps[lblg[i] as usize].push(i);
            }
        }
        for k in 1..=ng {
            let idx = &comps[k];
            if idx.len() < 6000 {
                continue;
            }
            let mut lu_comp: Vec<f32> = idx.iter().map(|&i| lu[i]).collect();
            let gmed = median_of(&mut lu_comp);
            let (mut y0, mut y1, mut x0, mut x1) = (bh, 0usize, bw, 0usize);
            for &i in idx {
                let y = i / bw;
                let x = i % bw;
                y0 = y0.min(y);
                y1 = y1.max(y);
                x0 = x0.min(x);
                x1 = x1.max(x);
            }
            let colmask: Vec<bool> = (0..n).map(|i| bs[i] < 25.0 && lu[i] < gmed + 10.0).collect();
            // comp filled
            let mut compmask = vec![false; n];
            for &i in idx {
                compmask[i] = true;
            }
            let compfill = ndimage::binary_fill_holes(&compmask, bw, bh);
            let pad = 4usize;
            let sy0 = y0.saturating_sub(pad);
            let sy1 = (y1 + pad).min(bh - 1) + 1;
            let sx0 = x0.saturating_sub(pad);
            let sx1 = (x1 + pad).min(bw - 1) + 1;
            let sh = sy1 - sy0;
            let sw = sx1 - sx0;
            let mut rowm = vec![0.0f32; sh];
            let mut colm = vec![0.0f32; sw];
            for yy in 0..sh {
                let mut s = 0.0;
                for xx in 0..sw {
                    if compfill[(sy0 + yy) * bw + (sx0 + xx)] {
                        s += 1.0;
                        colm[xx] += 1.0;
                    }
                }
                rowm[yy] = s / sw as f32;
            }
            for xx in 0..sw {
                colm[xx] /= sh as f32;
            }
            let (t_, bm_) = edge(&rowm, 0.5);
            let (l_, r_) = edge(&colm, 0.5);
            let py0 = sy0 + t_;
            let py1 = sy0 + bm_ + 1;
            let px0 = sx0 + l_;
            let px1 = sx0 + r_ + 1;
            if (px1 - px0) < 8 || (py1 - py0) < 8 {
                continue;
            }
            // incol count
            let mut incol_cnt = 0usize;
            for yy in py0..py1 {
                for xx in px0..px1 {
                    if colmask[yy * bw + xx] {
                        incol_cnt += 1;
                    }
                }
            }
            if incol_cnt < 100 {
                continue;
            }
            // colour median over incol
            let mut col = [0u8; 3];
            for c in 0..3 {
                let mut vals = Vec::new();
                for yy in py0..py1 {
                    for xx in px0..px1 {
                        let i = yy * bw + xx;
                        if colmask[i] {
                            vals.push(bg[i * 3 + c] as f32);
                        }
                    }
                }
                col[c] = median_of(&mut vals) as u8;
            }
            if (col.iter().cloned().max().unwrap() as i32 - col.iter().cloned().min().unwrap() as i32) > 14 {
                continue;
            }
            // tone flatness
            let mut tone: Vec<f32> = Vec::new();
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    if colmask[i] {
                        tone.push(0.299 * bg[i * 3] as f32 + 0.587 * bg[i * 3 + 1] as f32 + 0.114 * bg[i * 3 + 2] as f32);
                    }
                }
            }
            let mut tone_sorted = tone.clone();
            let gm = median_of(&mut tone_sorted);
            let flat_frac = tone.iter().filter(|&&v| (v - gm).abs() < 15.0).count() as f64 / tone.len() as f64;
            if flat_frac < 0.80 {
                continue;
            }
            // coloured-content gate
            let mut satgt = 0usize;
            let mut tot = 0usize;
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    tot += 1;
                    if bs[i] > 40.0 {
                        satgt += 1;
                    }
                }
            }
            if satgt as f64 / tot as f64 > 0.10 {
                continue;
            }
            // graycov
            let mut graycov = 0usize;
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    let rl = 0.299 * bg[i * 3] as f32 + 0.587 * bg[i * 3 + 1] as f32 + 0.114 * bg[i * 3 + 2] as f32;
                    if rl >= 205.0 && rl <= 250.0 {
                        graycov += 1;
                    }
                }
            }
            if (graycov as f64 / tot as f64) < 0.45 {
                continue;
            }
            for yy in py0..py1 {
                for xx in px0..px1 {
                    let i = yy * bw + xx;
                    bg[i * 3] = col[0];
                    bg[i * 3 + 1] = col[1];
                    bg[i * 3 + 2] = col[2];
                }
            }
            nrect += 1;
        }
    }
    nrect
}

/// Write the MRC PDF (matches L266-279). bg = FlateDecode RGB; K + inks = JBIG2 image masks.
fn write_pdf(
    path: &str,
    w: usize,
    h: usize,
    bw: usize,
    bh: usize,
    bgdata: &[u8],
    mw: usize,
    mh: usize,
    kdata: &[u8],
    layers: &[([u8; 3], Vec<u8>)],
) -> Result<()> {
    let pw = w as f64 / 2400.0 * 72.0;
    let ph = h as f64 / 2400.0 * 72.0;
    // Build PDF objects manually.
    let mut objs: Vec<Vec<u8>> = Vec::new();
    // We'll assign object numbers as we go: 1=catalog,2=pages,3=page,4=bg,5..=inks,then K,then content.
    // Build content stream first (string), object numbers known after counting.
    // Object plan:
    //   1 Catalog
    //   2 Pages
    //   3 Page
    //   4 Bg image
    //   5..(5+L-1) ink images
    //   (5+L) K image
    //   (6+L) Content stream
    let l = layers.len();
    let bg_obj = 4;
    let ink_start = 5;
    let k_obj = ink_start + l;
    let content_obj = k_obj + 1;

    // content stream
    let mut content = format!("q {} 0 0 {} 0 0 cm /Bg Do Q\n", pw, ph);
    for (i, (col, _)) in layers.iter().enumerate() {
        content += &format!(
            "q {:.3} {:.3} {:.3} rg {} 0 0 {} 0 0 cm /S{} Do Q\n",
            col[0] as f64 / 255.0,
            col[1] as f64 / 255.0,
            col[2] as f64 / 255.0,
            pw,
            ph,
            i
        );
    }
    content += &format!("q 0 0 0 rg {} 0 0 {} 0 0 cm /K Do Q\n", pw, ph);

    // resources dict
    let mut xobj = format!("/Bg {} 0 R", bg_obj);
    for i in 0..l {
        xobj += &format!(" /S{} {} 0 R", i, ink_start + i);
    }
    xobj += &format!(" /K {} 0 R", k_obj);

    // 1 Catalog
    objs.push(b"<< /Type /Catalog /Pages 2 0 R >>".to_vec());
    // 2 Pages
    objs.push(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>".to_vec());
    // 3 Page
    objs.push(
        format!(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {} {}] /Resources << /XObject << {} >> >> /Contents {} 0 R >>",
            pw, ph, xobj, content_obj
        )
        .into_bytes(),
    );
    // 4 Bg image (FlateDecode RGB)
    let mut bgobj = format!(
        "<< /Type /XObject /Subtype /Image /Width {} /Height {} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {} >>\nstream\n",
        bw, bh, bgdata.len()
    )
    .into_bytes();
    bgobj.extend_from_slice(bgdata);
    bgobj.extend_from_slice(b"\nendstream");
    objs.push(bgobj);
    // ink images
    for (_, data) in layers {
        let mut o = format!(
            "<< /Type /XObject /Subtype /Image /Width {} /Height {} /ImageMask true /Decode [0 1] /Filter /JBIG2Decode /Length {} >>\nstream\n",
            mw, mh, data.len()
        )
        .into_bytes();
        o.extend_from_slice(data);
        o.extend_from_slice(b"\nendstream");
        objs.push(o);
    }
    // K image
    {
        let mut o = format!(
            "<< /Type /XObject /Subtype /Image /Width {} /Height {} /ImageMask true /Decode [0 1] /Filter /JBIG2Decode /Length {} >>\nstream\n",
            mw, mh, kdata.len()
        )
        .into_bytes();
        o.extend_from_slice(kdata);
        o.extend_from_slice(b"\nendstream");
        objs.push(o);
    }
    // content stream
    {
        let cb = content.into_bytes();
        let mut o = format!("<< /Length {} >>\nstream\n", cb.len()).into_bytes();
        o.extend_from_slice(&cb);
        o.extend_from_slice(b"\nendstream");
        objs.push(o);
    }

    // serialize
    let mut out: Vec<u8> = Vec::new();
    out.extend_from_slice(b"%PDF-1.7\n%\xE2\xE3\xCF\xD3\n");
    let mut offsets = vec![0usize; objs.len() + 1];
    for (i, obj) in objs.iter().enumerate() {
        offsets[i + 1] = out.len();
        out.extend_from_slice(format!("{} 0 obj\n", i + 1).as_bytes());
        out.extend_from_slice(obj);
        out.extend_from_slice(b"\nendobj\n");
    }
    let xref_off = out.len();
    out.extend_from_slice(format!("xref\n0 {}\n", objs.len() + 1).as_bytes());
    out.extend_from_slice(b"0000000000 65535 f \n");
    for i in 1..=objs.len() {
        out.extend_from_slice(format!("{:010} 00000 n \n", offsets[i]).as_bytes());
    }
    out.extend_from_slice(
        format!(
            "trailer\n<< /Size {} /Root 1 0 R >>\nstartxref\n{}\n%%EOF\n",
            objs.len() + 1,
            xref_off
        )
        .as_bytes(),
    );
    std::fs::write(path, out).with_context(|| format!("write pdf {}", path))?;
    Ok(())
}
