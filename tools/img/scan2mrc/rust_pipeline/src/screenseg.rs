//! Segmentation by SCREENING, not by classifying photo-vs-type. See SEGMENTATION_PLAN.md.
//!
//!   screened      -> contone (the background)
//!   not screened  -> bilevel (the K / ink stencils)
//!
//! Halftone means the original was continuous tone; the press screened it. No halftone means solid
//! ink: type, rules, line art. That is a property of the paper, not a threshold fitted to a sample.
//!
//! WHAT THIS REPLACES. Step 7 votes IMAGE vs TEXT on CMYK statistics, and it cannot work: p092
//! carries two grey photographs whose `objfK` reads 0.44 and 0.03; a "PROFIS" wordmark and a
//! circuit-board photo both read bodyK ~50 / objfK 0.28 with opposite correct answers. Seven
//! features have been tried. The fallback also points at the destructive layer -- a photo sent to
//! bilevel loses tone irreversibly, type sent to contone is merely soft.
//!
//! THREE THINGS MEASURED BEFORE WRITING THIS, each of which shapes the code:
//!
//! 1. Geometry must be PER BLOCK. p092 has page-level angle_consistency 0.97 and still carries
//!    photographs screened at 81 and 102 lpi. 91 of 163 pages show pitch_std 4x the trusted ones --
//!    the signature of more than one screen on the sheet. A page-level angle would aim the test at
//!    the wrong screen and report "not screened" for a photograph.
//! 2. Type's periodic energy is ON-AXIS. p092's body text peaks at 0 deg: that is line rhythm, not
//!    halftone. The axis cut is what separates type from screen.
//! 3. HALFTONE ONLY EXISTS IN MID-TONES. A solid highlight or solid shadow has no dots at all (0%
//!    or 100% ink), so a photograph's flat areas correctly measure "not screened". Blocks must
//!    therefore be grouped and holes filled, or every photo would be shot through with bilevel
//!    patches. This is why `close` + `fill_holes` below are load-bearing, not cosmetic.

use crate::fftutil;
use crate::ndimage;
use num_complex::Complex32;
use rayon::prelude::*;

pub const WIN: usize = 128; // ~22-28 screen cells at 100-135 lpi: enough to fit a screen
pub const STEP: usize = 60; // ~10 cells: fine enough to split a tint from the type on it
const LO_LPI: f32 = 50.0;
const HI_LPI: f32 = 200.0;
const AXIS_DEG: f32 = 12.0;

pub struct BlockMap {
    pub ny: usize,
    pub nx: usize,
    pub s: Vec<f32>,   // peak prominence in the screen band = "is there a screen here"
    pub lpi: Vec<f32>, // that block's own ruling
    pub ang: Vec<f32>, // and angle
}

fn band_and_window(dpi: f32) -> (Vec<bool>, Vec<f32>, Vec<f32>, Vec<f32>) {
    let f = fftutil::fftfreq(WIN);
    let sh = fftutil::fftshift_indices(WIN);
    let fs: Vec<f32> = sh.iter().map(|&i| f[i] as f32).collect();
    let mut band = vec![false; WIN * WIN];
    let mut fr = vec![0.0f32; WIN * WIN];
    let mut ang = vec![0.0f32; WIN * WIN];
    for iy in 0..WIN {
        for ix in 0..WIN {
            let (fy, fx) = (fs[iy], fs[ix]);
            let r = (fy * fy + fx * fx).sqrt();
            let a = fy.atan2(fx).to_degrees().rem_euclid(180.0);
            let on_axis = a.min(180.0 - a) < AXIS_DEG || (a - 90.0).abs() < AXIS_DEG;
            let i = iy * WIN + ix;
            fr[i] = r;
            ang[i] = a;
            band[i] = r > LO_LPI / dpi && r < HI_LPI / dpi && !on_axis;
        }
    }
    let hann: Vec<f32> = (0..WIN)
        .map(|i| 0.5 - 0.5 * (2.0 * std::f32::consts::PI * i as f32 / (WIN - 1) as f32).cos())
        .collect();
    let mut w2 = vec![0.0f32; WIN * WIN];
    for y in 0..WIN {
        for x in 0..WIN {
            w2[y * WIN + x] = hann[y] * hann[x];
        }
    }
    (band, w2, fr, ang)
}

/// Per-block spectrum: strongest off-axis peak in the screen band, and its prominence over the
/// band median. `plane` is a screened channel at `dpi` (K-ish luma works; the screen is in it).
pub fn block_map(plane: &[f32], w: usize, h: usize, dpi: f32) -> BlockMap {
    let (band, win2, fr, ang) = band_and_window(dpi);
    let band_idx: Vec<usize> = (0..WIN * WIN).filter(|&i| band[i]).collect();
    let ny = if h >= WIN { (h - WIN) / STEP + 1 } else { 0 };
    let nx = if w >= WIN { (w - WIN) / STEP + 1 } else { 0 };
    let mut s = vec![0.0f32; ny * nx];
    let mut lpi = vec![0.0f32; ny * nx];
    let mut angm = vec![0.0f32; ny * nx];
    if ny == 0 || nx == 0 || band_idx.is_empty() {
        return BlockMap { ny, nx, s, lpi, ang: angm };
    }
    let out: Vec<(f32, f32, f32)> = (0..ny * nx)
        .into_par_iter()
        .map(|bi| {
            let (by, bx) = (bi / nx, bi % nx);
            let (y0, x0) = (by * STEP, bx * STEP);
            let mut tile = vec![0.0f32; WIN * WIN];
            let mut mean = 0.0f32;
            for y in 0..WIN {
                for x in 0..WIN {
                    let v = plane[(y0 + y) * w + (x0 + x)];
                    tile[y * WIN + x] = v;
                    mean += v;
                }
            }
            mean /= (WIN * WIN) as f32;
            for i in 0..WIN * WIN {
                tile[i] = (tile[i] - mean) * win2[i];
            }
            let spec = fftutil::fft2_real(&tile, WIN, WIN);
            let mag = fftutil::fftshift2(&spec, WIN, WIN);
            let mut vals: Vec<f32> = Vec::with_capacity(band_idx.len());
            let mut best = (0.0f32, 0usize);
            for &i in &band_idx {
                let m = (mag[i] as Complex32).norm();
                vals.push(m);
                if m > best.0 {
                    best = (m, i);
                }
            }
            vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let med = vals[vals.len() / 2].max(1e-6);
            (best.0 / med, dpi * fr[best.1], ang[best.1])
        })
        .collect();
    for (i, (a, b, c)) in out.into_iter().enumerate() {
        s[i] = a;
        lpi[i] = b;
        angm[i] = c;
    }
    BlockMap { ny, nx, s, lpi, ang: angm }
}

/// Blocks -> a screened AREA mask at block resolution.
///
/// `close` bridges the dot-free gaps a halftone leaves in its own highlights and shadows;
/// `fill_holes` recovers a photograph's solid highlight enclosed by screen; the size filter drops
/// isolated blocks that fired on type. Without these a photo comes out shot through with bilevel
/// patches -- see the module note, this is the measured behaviour, not a precaution.
pub fn areas(bm: &BlockMap, thr: f32, min_blocks: usize) -> Vec<bool> {
    let (ny, nx) = (bm.ny, bm.nx);
    let mut m: Vec<bool> = bm.s.iter().map(|&v| v > thr).collect();
    m = ndimage::binary_dilation(&m, nx, ny, 2);
    m = ndimage::binary_erosion(&m, nx, ny, 2);
    m = ndimage::binary_fill_holes(&m, nx, ny);
    let (lb, n) = ndimage::label(&m, nx, ny);
    if n > 0 {
        let sz = ndimage::component_sizes(&lb, n);
        m = lb
            .iter()
            .map(|&l| l != 0 && sz[l as usize - 1] >= min_blocks as u64)
            .collect();
    }
    m
}

/// Block mask -> full-resolution mask. Each block covers WIN px but is anchored every STEP px, so
/// paint the centred STEP x STEP cell: adjacent blocks then tile without overlap.
pub fn expand(mask: &[bool], ny: usize, nx: usize, w: usize, h: usize) -> Vec<bool> {
    let mut out = vec![false; w * h];
    let off = (WIN - STEP) / 2;
    for by in 0..ny {
        for bx in 0..nx {
            if !mask[by * nx + bx] {
                continue;
            }
            let y0 = by * STEP + off;
            let x0 = bx * STEP + off;
            for y in y0..(y0 + STEP).min(h) {
                for x in x0..(x0 + STEP).min(w) {
                    out[y * w + x] = true;
                }
            }
        }
    }
    out
}
