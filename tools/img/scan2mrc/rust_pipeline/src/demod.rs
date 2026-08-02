//! STAGE B — from halftone to dot area, per ink, using the geometry stage A measured.
//!
//! Two products, and they are produced by different means for different reasons:
//!
//!   TONE       the dot area the press laid down, per ink, at the screen's own information rate.
//!              This is the contone image. It needs NO demodulation -- see `contone` below.
//!   COHERENCE  how much of the local ink is explained by that block's screen. This is what
//!              separates a line on a tint from the tint, and it is the only thing here that
//!              genuinely requires knowing (ruling, angle).
//!
//! WHY TONE IS JUST A BOX AVERAGE. A halftone encodes tone as dot AREA on a fixed lattice, so the
//! tone is recovered by integrating over exactly one cell. A box average of width `2400/ruling`
//! does that -- and a box of width N has its first spectral null at 1/N, which is precisely the
//! screen fundamental. The averaging window and the screen cell are the same object. This is also
//! why measuring screening at 600 dpi was dangerous (FINDINGS.md 2): the 4x box downsample nulls a
//! 150 lpi screen. Here that null is the entire point.
//!
//! It also means the contone rate is not a free parameter. The halftone discarded everything above
//! ruling/2, so the contone Nyquist IS the ruling: sampling faster than the screen recovers nothing
//! but interpolation, and sampling slower throws away tone the paper still holds. So this stage
//! derives its output dpi from the ruling stage A measured on THIS page, rather than taking 150 as
//! a constant.
//!
//! WHY COHERENCE NEEDS THE VECTOR. A previous prototype compared per-channel inverse halftoning
//! against a blanket low-pass and found them essentially identical in sharpness (FINDINGS.md 3), and
//! that result is not surprising: both are band-limited to ruling/2, which is where the information
//! ends. Demodulation is not a sharpness lever and must not be sold as one. What a low-pass cannot
//! do is say WHICH ink at a given place is part of a periodic grid and which is not -- and that is
//! the question that separates K line-art sitting on a K-screened tint from the tint under it. Two
//! things in the same place at different scales, told apart by coherence, not by a classifier.
//!
//! TWO GRADES, TWO PURPOSES -- do not feed this stage one input.
//!
//!   COHERENCE runs on the UNCLIPPED (detect) grade. Clipping the shadows is what makes a faint
//!             tint's dots fall below the level floor and vanish, and coherence is exactly the
//!             measurement that must still see them.
//!   CONTONE   runs on the DISPLAY grade. The unclipped K is not an ink amount at all -- it is the
//!             raw rich-black distance field, and it reads 80 on WHITE PAPER and 250 across a
//!             perfectly ordinary photograph. Measured on p007, which is how this was found: the
//!             contone came out solid black. `K -level 90%,95%` is what turns that distance field
//!             into ink (page-mean K collapses ~67 -> 7), and dot area is meaningless without it.
//!
//! Same pixels, two gradings, two questions. Feeding either question the other's input produces a
//! confident wrong answer rather than an error.
//!
//! THE STENCIL IS A MASK, NOT A SUBTRACTION. It would be tempting to reconstruct the screen and
//! subtract it, leaving the line art. Don't: a halftone dot is square-ish, so it carries strong
//! harmonics, and reconstructing from the fundamental alone leaves harmonic residue that looks
//! exactly like structure. The stencil is "ink is present here AND coherence is low" -- a decision
//! about each pixel, never an arithmetic difference. FINDINGS.md 2 records the same caution.

use crate::imageio::Cmyk;
use crate::screen::{self, ScreenField};
use num_complex::Complex32;
use rayon::prelude::*;

// ================================================================================================
//  CONSTANTS. As in screen.rs: all here, documented, no env vars and no CLI flags.
// ================================================================================================

/// Resolution the stencil layers are decided and drawn at. 2400/4: fine enough that a 1 px mark at
/// 600 dpi is a real stroke rather than a scanner artifact, coarse enough that a page of bilevel
/// masks stays small. The screen is NOT measured here -- see the module note.
pub const STENCIL_DPI: f64 = 600.0;

/// Fallback contone rate, lines per inch, used only where a page has no trustworthy ruling at all
/// (a page of pure type). 150 is the middle of this issue's measured 133-160 and the value the old
/// renderer shipped; it is a fallback, not the default -- the default is the measured ruling.
pub const CONTONE_FALLBACK_LPI: f64 = 150.0;

/// The contone divisor is `round(2400 / ruling)` clamped to this range: 2400/12 = 200 dpi at the
/// fine end, 2400/20 = 120 dpi at the coarse end. Clamped because a wild ruling estimate must not
/// be able to produce a 40 dpi background, and because an integer divisor makes the box average an
/// exact cell integral rather than a resampling.
pub const DIV_MIN: usize = 12;
pub const DIV_MAX: usize = 20;

/// Gaussian smoothing applied to the demodulated field, in SCREEN PERIODS.
///
/// This is the Gabor uncertainty dial. Small sigma localises well but is noisy; large sigma is
/// confident but smears across the boundary between a tint and the type on it -- which is the exact
/// boundary this measurement exists to find. 1.5 periods is about 1 mm at 150 lpi: a few cells, so
/// the estimate is stable, but under the height of body type so a line's own gap still reads as
/// incoherent.
pub const COH_SIGMA_PERIODS: f64 = 1.5;

/// Ink level below which coherence is not computed at all (the block is bare paper in this ink, and
/// a ratio there is noise divided by noise).
pub const MIN_INK: f32 = 8.0;

// ================================================================================================

pub struct Contone {
    pub w: usize,
    pub h: usize,
    pub dpi: f64,
    /// dot area 0-255 per ink, C M Y K
    pub ink: Vec<Vec<u8>>,
}

pub struct Coherence {
    pub w: usize,
    pub h: usize,
    /// 0..1 per ink at STENCIL_DPI: the share of local ink energy sitting at that block's screen
    pub ink: Vec<Vec<f32>>,
}

/// The contone divisor for this page: derived from the ruling stage A actually measured, not
/// assumed. Uses the median over every block that fired in any ink, so one ink's harmonic lock
/// cannot drag it.
pub fn contone_divisor(f: &ScreenField) -> usize {
    let mut ls: Vec<f32> = Vec::new();
    for ink in &f.ink {
        for i in 0..f.ny * f.nx {
            if screen::fired(ink, i) {
                ls.push(ink.lpi[i]);
            }
        }
    }
    let lpi = if ls.is_empty() {
        CONTONE_FALLBACK_LPI
    } else {
        ls.sort_by(|a, b| a.partial_cmp(b).unwrap());
        ls[ls.len() / 2] as f64
    };
    ((screen::SRC_DPI / lpi).round() as usize).clamp(DIV_MIN, DIV_MAX)
}

/// TONE. Box-average each ink over one screen cell -> dot area at the screen's own rate.
///
/// The divisor is the cell width in source pixels, so this is an exact integral over the cell and
/// the screen fundamental lands on the box's first null. No window, no FFT, no per-block geometry:
/// the ruling sets the width and that is the whole of it.
pub fn contone(cmyk: &Cmyk, div: usize) -> Contone {
    let (w, h) = (cmyk.w / div, cmyk.h / div);
    let n = (div * div) as u32;
    let ink: Vec<Vec<u8>> = (0..4)
        .map(|ci| {
            let src = cmyk.channel(ci);
            let mut out = vec![0u8; w * h];
            out.par_chunks_mut(w).enumerate().for_each(|(y, row)| {
                for x in 0..w {
                    let mut acc: u32 = 0;
                    for sy in 0..div {
                        let base = (y * div + sy) * cmyk.w + x * div;
                        for sx in 0..div {
                            acc += src[base + sx] as u32;
                        }
                    }
                    // round-half-up, so a flat field of value v returns exactly v
                    row[x] = ((acc + n / 2) / n) as u8;
                }
            });
            out
        })
        .collect();
    Contone { w, h, dpi: screen::SRC_DPI / div as f64, ink }
}

/// The screen vector (cycles per source pixel, as (fy, fx)) for the block covering a source pixel,
/// or None where that ink reported no screen there.
///
/// Nearest block, not interpolated: between two blocks with different rulings the interpolated
/// vector belongs to neither screen, and the magnitude we take afterwards is more forgiving of a
/// hard switch than of a wrong frequency.
fn vector_at(f: &ScreenField, ci: usize, sy: usize, sx: usize) -> Option<(f64, f64)> {
    let by = (sy / screen::STEP).min(f.ny.saturating_sub(1));
    let bx = (sx / screen::STEP).min(f.nx.saturating_sub(1));
    let bi = by * f.nx + bx;
    let ink = &f.ink[ci];
    if !screen::fired(ink, bi) {
        return None;
    }
    let lpi = ink.lpi[bi] as f64;
    if lpi <= 0.0 {
        return None;
    }
    let a = (ink.ang[bi] as f64).to_radians();
    let fr = lpi / screen::SRC_DPI; // cycles per source pixel
    Some((fr * a.sin(), fr * a.cos()))
}

/// COHERENCE. Per ink, the share of local AC energy sitting at that block's own screen frequency.
///
/// Demodulate (multiply by exp(-i2*pi*f.x), which slides the screen to DC), then integrate. The
/// integration is done by accumulating straight into the STENCIL_DPI grid: after demodulation the
/// screen IS at DC, so summing a DIV x DIV cell is the matched low-pass and costs nothing extra.
/// A coherent grating survives that sum; type and noise, whose phase wanders, cancel.
///
/// Normalised by the local AC RMS so the answer is a SHARE, not an amplitude -- amplitude is what
/// stage A's depth gate is for, and mixing the two questions is what made stage A's first version
/// fire on crosstalk.
pub fn coherence(cmyk: &Cmyk, f: &ScreenField) -> Coherence {
    let div = (screen::SRC_DPI / STENCIL_DPI).round() as usize; // 4
    let (w, h) = (cmyk.w / div, cmyk.h / div);
    let ink: Vec<Vec<f32>> = (0..4)
        .map(|ci| {
            let src = cmyk.channel(ci);
            // Per output cell we accumulate three things: the demodulated signal, and the first two
            // moments of the raw value. NOT the AC about this cell's own mean -- see below.
            let mut num = vec![Complex32::new(0.0, 0.0); w * h];
            let mut s1 = vec![0.0f32; w * h];
            let mut s2 = vec![0.0f32; w * h];
            num.par_chunks_mut(w)
                .zip(s1.par_chunks_mut(w))
                .zip(s2.par_chunks_mut(w))
                .enumerate()
                .for_each(|(y, ((nrow, arow), brow))| {
                    for x in 0..w {
                        let (sy0, sx0) = (y * div, x * div);
                        let vec_here = vector_at(f, ci, sy0, sx0);
                        let mut acc = Complex32::new(0.0, 0.0);
                        let (mut a, mut b) = (0.0f32, 0.0f32);
                        for sy in 0..div {
                            let base = (sy0 + sy) * cmyk.w + sx0;
                            for sx in 0..div {
                                let v = src[base + sx] as f32;
                                a += v;
                                b += v * v;
                                // DO NOT subtract a per-cell mean here. The cell is div px across
                                // (4 at 600 dpi) and the screen period is ~16 px, so subtracting
                                // the cell's own mean is a high-pass at a QUARTER of the screen
                                // period -- it removes the very signal being measured, and every
                                // tint then reads incoherent. Found by looking: p007's cyan tint
                                // bars came out marked as line art. The carrier's DC lands at -f
                                // after demodulation and is removed by the smoothing below, which
                                // is the correct place for it.
                                if let Some((fy, fx)) = vec_here {
                                    let ph = -2.0
                                        * std::f64::consts::PI
                                        * (fy * (sy0 + sy) as f64 + fx * (sx0 + sx) as f64);
                                    let (si, co) = ph.sin_cos();
                                    acc += Complex32::new(v * co as f32, v * si as f32);
                                }
                            }
                        }
                        nrow[x] = acc;
                        arow[x] = a;
                        brow[x] = b;
                    }
                });
            // Smooth all three over COH_SIGMA_PERIODS, then combine. Smoothing the parts and then
            // dividing is stable; dividing noisy fields and then smoothing is not.
            let cells_per_period = {
                let d = contone_divisor(f) as f64; // source px per screen cell
                (d / div as f64).max(1.0)
            };
            let sigma = COH_SIGMA_PERIODS * cells_per_period;
            let nr: Vec<f32> = num.iter().map(|z| z.re).collect();
            let ni: Vec<f32> = num.iter().map(|z| z.im).collect();
            let nr = crate::ndimage::gaussian_filter(&nr, w, h, sigma);
            let ni = crate::ndimage::gaussian_filter(&ni, w, h, sigma);
            let a = crate::ndimage::gaussian_filter(&s1, w, h, sigma);
            let b = crate::ndimage::gaussian_filter(&s2, w, h, sigma);
            let per_cell = (div * div) as f32;
            (0..w * h)
                .map(|i| {
                    let mean = a[i] / per_cell;
                    if mean < MIN_INK {
                        return 0.0;
                    }
                    // variance of the raw value over the smoothing neighbourhood
                    let var = (b[i] / per_cell - mean * mean).max(0.0);
                    let rms = var.sqrt();
                    if rms < 1e-3 {
                        return 0.0;
                    }
                    // A sinusoid of amplitude A demodulated at its own frequency averages to A/2,
                    // and its AC rms is A/sqrt(2). So sqrt(2)*|R|/rms is 1 for a pure grating and
                    // falls toward 0 as the ink stops being periodic at that vector.
                    let r = (nr[i] * nr[i] + ni[i] * ni[i]).sqrt() / per_cell;
                    (std::f32::consts::SQRT_2 * r / rms).min(1.0)
                })
                .collect()
        })
        .collect();
    Coherence { w, h, ink }
}
