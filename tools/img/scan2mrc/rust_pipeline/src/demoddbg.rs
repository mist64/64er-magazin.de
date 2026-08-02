//! The debug picture for STAGE B. One PNG per page, two panels.
//!
//!   LEFT   THE CONTONE, as it will be drawn: the recovered dot area per ink, converted to RGB for
//!          viewing only. If a photograph looks posterised or a tint looks blotchy here, the
//!          screen cell integral is wrong and nothing downstream can repair it.
//!   RIGHT  THE SPLIT, which is the question this stage exists to answer. Every pixel carrying ink
//!          is coloured by whether that ink is part of a periodic grid:
//!              BLUE   coherent -> halftone. Goes to the contone background.
//!              RED    incoherent ink -> a mark. Goes to the bilevel stencil.
//!          The case to look at is type ON a tint. The bar should be solid blue with the letters
//!          drawn in red ON it. If the letters are blue, the stencil will lose them into the
//!          background; if the whole bar is red, a flat tint is about to be redrawn as line art.
//!
//! This picture is the only honest way to judge stage B, because both failure directions are
//! invisible in the contone alone.

use crate::demod::{Coherence, Contone};
use crate::imageio::Cmyk;
use crate::pilio;
use anyhow::Result;

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Coherence at or above this counts as "explained by the screen". Provisional, and deliberately
/// only used by this drawer and by stage C -- the field itself is continuous, so it can be
/// re-judged without re-measuring.
pub const COHERENT: f32 = 0.30;

/// Ink level (0-255) below which a pixel is treated as bare paper and left uncoloured. Well above
/// scanner noise, well below any real mark.
pub const INK_PRESENT: f32 = 24.0;

/// Both panels are drawn at this divisor from the stencil grid, to keep the PNG a readable A4.
const SHRINK: usize = 4; // 600 dpi / 4 = 150 dpi

const GUTTER: usize = 24;
const WASH: f32 = 0.62;
const LIFT: f32 = 0.40;

// ================================================================================================

/// Naive CMYK -> sRGB, for VIEWING ONLY. Deliberately not the ICC transform: this panel must show
/// what the measurement produced, not what a colour engine makes of it.
fn cmyk_rgb(c: f32, m: f32, y: f32, k: f32) -> [f32; 3] {
    let f = |v: f32, kk: f32| ((1.0 - v / 255.0) * (1.0 - kk / 255.0)).clamp(0.0, 1.0);
    [f(c, k), f(m, k), f(y, k)]
}

pub fn write_png(path: &str, cmyk: &Cmyk, tone: &Contone, coh: &Coherence) -> Result<()> {
    // The two panels share a grid: the coherence grid (600 dpi) reduced by SHRINK.
    let (pw, ph) = (coh.w / SHRINK, coh.h / SHRINK);
    let ow = pw * 2 + GUTTER;
    let mut px = vec![255u8; ow * ph * 3];
    let put = |px: &mut Vec<u8>, panel: usize, x: usize, y: usize, rgb: [f32; 3]| {
        let i = ((y * ow) + panel * (pw + GUTTER) + x) * 3;
        px[i] = (rgb[0] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 1] = (rgb[1] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 2] = (rgb[2] * 255.0).clamp(0.0, 255.0) as u8;
    };

    // ---- LEFT: the contone, sampled onto the shared grid -------------------------------------
    for y in 0..ph {
        for x in 0..pw {
            // map this pixel to the contone grid (different rate: contone dpi is derived per page)
            let ty = (y * tone.h) / ph;
            let tx = (x * tone.w) / pw;
            let ti = (ty.min(tone.h - 1)) * tone.w + tx.min(tone.w - 1);
            let rgb = cmyk_rgb(
                tone.ink[0][ti] as f32,
                tone.ink[1][ti] as f32,
                tone.ink[2][ti] as f32,
                tone.ink[3][ti] as f32,
            );
            put(&mut px, 0, x, y, rgb);
        }
    }

    // ---- RIGHT: the split ---------------------------------------------------------------------
    // Backdrop: the page in grey, lifted, so red and blue read against it.
    let sdiv = (cmyk.w / coh.w).max(1); // source px per coherence px
    for y in 0..ph {
        for x in 0..pw {
            // total ink at this spot, from the source, averaged over the shrink cell
            let (cy, cx) = (y * SHRINK, x * SHRINK);
            let mut ink = [0.0f32; 4];
            let mut n = 0.0f32;
            for dy in 0..SHRINK {
                for dx in 0..SHRINK {
                    let (yy, xx) = (cy + dy, cx + dx);
                    if yy >= coh.h || xx >= coh.w {
                        continue;
                    }
                    let sy = yy * sdiv;
                    let sx = xx * sdiv;
                    let si = sy * cmyk.w + sx;
                    ink[0] += cmyk.c[si] as f32;
                    ink[1] += cmyk.m[si] as f32;
                    ink[2] += cmyk.y[si] as f32;
                    ink[3] += cmyk.k[si] as f32;
                    n += 1.0;
                }
            }
            if n == 0.0 {
                continue;
            }
            for v in ink.iter_mut() {
                *v /= n;
            }
            let total = ink[0] + ink[1] + ink[2] + ink[3] * 1.5;
            let g = (1.0 - (total / 380.0).min(1.0)).clamp(0.0, 1.0);
            let g = g + (1.0 - g) * LIFT;
            let mut col = [g, g, g];

            // Which inks are present here, and are they coherent? Take the ink with the most
            // presence: on this paper a mark is essentially never two inks disagreeing about
            // whether it is a screen.
            let mut best = (0.0f32, 0usize);
            for ci in 0..4 {
                if ink[ci] > best.0 {
                    best = (ink[ci], ci);
                }
            }
            if best.0 >= INK_PRESENT {
                // coherence at the full stencil grid, max over the shrink cell: a thin stroke must
                // not be averaged away by its own neighbourhood
                let mut cmax = 0.0f32;
                for dy in 0..SHRINK {
                    for dx in 0..SHRINK {
                        let (yy, xx) = (cy + dy, cx + dx);
                        if yy < coh.h && xx < coh.w {
                            cmax = cmax.max(coh.ink[best.1][yy * coh.w + xx]);
                        }
                    }
                }
                let tint = if cmax >= COHERENT {
                    [0.10, 0.45, 0.95] // blue: halftone -> contone
                } else {
                    [0.90, 0.15, 0.15] // red: a mark -> stencil
                };
                for k in 0..3 {
                    col[k] = col[k] + (tint[k] - col[k]) * WASH;
                }
            }
            put(&mut px, 1, x, y, col);
        }
    }
    pilio::write_rgb_png_fast(path, ow, ph, &px)
}

/// One line for the terminal, printed as the page finishes.
pub fn summarise(page: &str, tone: &Contone, coh: &Coherence) -> String {
    let n = (coh.w * coh.h) as f64;
    let mut parts = Vec::new();
    for (ci, nm) in ["C", "M", "Y", "K"].iter().enumerate() {
        let c = &coh.ink[ci];
        let hi = c.iter().filter(|&&v| v >= COHERENT).count();
        if hi == 0 {
            continue;
        }
        parts.push(format!("{} coh {:.1}%", nm, 100.0 * hi as f64 / n));
    }
    if parts.is_empty() {
        parts.push("no coherent ink".into());
    }
    format!(
        "p{} contone {}x{} @{:.0}dpi | {}",
        page, tone.w, tone.h, tone.dpi, parts.join("  ")
    )
}
