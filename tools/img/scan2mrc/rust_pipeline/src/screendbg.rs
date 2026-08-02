//! The debug picture for STAGE A. One PNG per page, written the moment that page's field exists.
//!
//! Two panels side by side, same page, same scale:
//!
//!   LEFT   what fired, coloured by WHICH INK carries the screen. That is the question the four
//!          content classes are a crossing of: C/M/Y present -> colour photo or colour tint, K
//!          alone -> greyscale photo or grey box, nothing -> type and line art.
//!   RIGHT  what ruling was measured, as a colour ramp. A photograph and the tint next to it can
//!          both fire on the left and be screened at 150 and 133 lpi respectively; if this panel is
//!          noise where the left panel is confident, the geometry is not trustworthy and the
//!          matched demodulation downstream has nothing to aim at.
//!
//! WASH, NOT OUTLINE -- deliberately the opposite of the deleted decision-overlay's rule. That
//! drawer outlined regions because the pixels deciding a cut are the few either side of the line
//! and a tint would recolour exactly those. Here the thing being judged IS an area measurement, so
//! it has to be shown as an area. The underlying page stays legible through it (the wash is applied
//! to a lightened grey page, and the page is drawn from the same data the measurement ran on).

use crate::imageio::Cmyk;
use crate::pilio;
use crate::screen::{self, ScreenField};
use anyhow::Result;

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Downsample from the 2400 dpi source to the debug page image. 16 -> 150 dpi, which is a readable
/// A4 page at ~1240x1754 per panel and lines up with the contone rate the renderer will use.
const SHRINK: usize = 16;

/// Gap between the two panels, px.
const GUTTER: usize = 24;

/// How far the wash pushes the page toward the ink colour, 0..1. High enough to read at a glance,
/// low enough that the type under it stays legible -- the commonest error this picture must reveal
/// is a wash sitting on top of body text.
const WASH: f32 = 0.55;

/// Page grey is lifted toward white by this much before washing, so a dark photograph does not
/// swallow the overlay. 0 = untouched, 1 = white.
const LIFT: f32 = 0.45;

/// Ruling ramp endpoints for the right-hand panel, lpi. Chosen to span the measured content
/// (81-160) with headroom, so a block reading outside it is visibly clipped rather than silently
/// folded into the end of the ramp.
const RAMP_LO: f32 = 60.0;
const RAMP_HI: f32 = 220.0;

/// Canonical sRGB per ink, for the left panel. K washes toward a mid grey rather than black so it
/// stays distinguishable from dark page content underneath.
const INK_RGB: [[f32; 3]; 4] = [
    [0.0, 0.68, 0.94],  // C
    [0.93, 0.11, 0.56], // M
    [1.0, 0.85, 0.0],   // Y
    [0.35, 0.35, 0.40], // K
];

// ================================================================================================

/// Page luma at 1/SHRINK scale, from the CMYK the measurement ran on: dark where ink is.
fn page_grey(cmyk: &Cmyk) -> (usize, usize, Vec<f32>) {
    let (w, h) = (cmyk.w / SHRINK, cmyk.h / SHRINK);
    let mut g = vec![0.0f32; w * h];
    for y in 0..h {
        for x in 0..w {
            let mut acc = 0.0f32;
            for sy in 0..SHRINK {
                let row = (y * SHRINK + sy) * cmyk.w + x * SHRINK;
                for sx in 0..SHRINK {
                    let i = row + sx;
                    // total ink coverage, capped -- this is a legibility backdrop, not a proof
                    let ink = cmyk.c[i] as f32 + cmyk.m[i] as f32 + cmyk.y[i] as f32
                        + cmyk.k[i] as f32 * 1.5;
                    acc += (ink / 3.0).min(255.0);
                }
            }
            g[y * w + x] = 255.0 - acc / (SHRINK * SHRINK) as f32;
        }
    }
    (w, h, g)
}

/// A perceptually monotone ramp for the ruling panel: blue (coarse) -> green -> yellow -> red
/// (fine). Deliberately not a hue wheel, which wraps and makes 60 and 220 lpi the same colour.
fn ramp(t: f32) -> [f32; 3] {
    let t = t.clamp(0.0, 1.0);
    let stops = [
        [0.15, 0.25, 0.85],
        [0.10, 0.75, 0.55],
        [0.95, 0.90, 0.15],
        [0.85, 0.15, 0.10],
    ];
    let s = t * 3.0;
    let i = (s.floor() as usize).min(2);
    let f = s - i as f32;
    let (a, b) = (stops[i], stops[i + 1]);
    [
        a[0] + (b[0] - a[0]) * f,
        a[1] + (b[1] - a[1]) * f,
        a[2] + (b[2] - a[2]) * f,
    ]
}

/// Which page pixels a block covers, in debug-image coordinates: the STEP-sized cell centred on the
/// window, so adjacent blocks tile exactly once with no overlap and no gap.
fn cell(by: usize, bx: usize, w: usize, h: usize) -> (usize, usize, usize, usize) {
    let (cy, cx) = screen::centre_of(by, bx);
    let half = screen::STEP / 2;
    let y0 = cy.saturating_sub(half) / SHRINK;
    let x0 = cx.saturating_sub(half) / SHRINK;
    let y1 = ((cy + half) / SHRINK).min(h);
    let x1 = ((cx + half) / SHRINK).min(w);
    (y0, x0, y1, x1)
}

/// Write the two-panel debug PNG for one page.
pub fn write_png(path: &str, cmyk: &Cmyk, f: &ScreenField) -> Result<()> {
    let (pw, ph, grey) = page_grey(cmyk);
    let ow = pw * 2 + GUTTER;
    let oh = ph;
    let mut px = vec![255u8; ow * oh * 3];

    // both panels start as the lifted grey page
    let put = |px: &mut Vec<u8>, panel: usize, x: usize, y: usize, rgb: [f32; 3]| {
        let ox = panel * (pw + GUTTER) + x;
        let i = (y * ow + ox) * 3;
        px[i] = (rgb[0] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 1] = (rgb[1] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 2] = (rgb[2] * 255.0).clamp(0.0, 255.0) as u8;
    };
    for y in 0..ph {
        for x in 0..pw {
            let g = (grey[y * pw + x] / 255.0).clamp(0.0, 1.0);
            let g = g + (1.0 - g) * LIFT;
            for panel in 0..2 {
                put(&mut px, panel, x, y, [g, g, g]);
            }
        }
    }

    for by in 0..f.ny {
        for bx in 0..f.nx {
            let bi = by * f.nx + bx;
            // LEFT: mix the colours of every ink that fired here, weighted by how hard it fired.
            // Two inks screened in one block is the normal case for a colour photo, so the panel
            // has to show a mixture rather than an argmax.
            let mut wsum = 0.0f32;
            let mut mix = [0.0f32; 3];
            let mut best = (0.0f32, 0usize);
            for ci in 0..4 {
                if !screen::fired(f, ci, bi) {
                    continue;
                }
                let p = f.ink[ci].prom[bi];
                // saturate a couple of thresholds above FIRE so one very strong ink does not erase
                // a genuine second one
                let wgt = ((p - screen::FIRE) / screen::FIRE).clamp(0.0, 1.0);
                for k in 0..3 {
                    mix[k] += INK_RGB[ci][k] * wgt;
                }
                wsum += wgt;
                if p > best.0 {
                    best = (p, ci);
                }
            }
            let (y0, x0, y1, x1) = cell(by, bx, pw, ph);
            if wsum > 0.0 {
                let col = [mix[0] / wsum, mix[1] / wsum, mix[2] / wsum];
                for y in y0..y1 {
                    for x in x0..x1 {
                        let i = ((y * ow) + x) * 3;
                        let base = [
                            px[i] as f32 / 255.0,
                            px[i + 1] as f32 / 255.0,
                            px[i + 2] as f32 / 255.0,
                        ];
                        let o = [
                            base[0] + (col[0] - base[0]) * WASH,
                            base[1] + (col[1] - base[1]) * WASH,
                            base[2] + (col[2] - base[2]) * WASH,
                        ];
                        put(&mut px, 0, x, y, o);
                    }
                }
                // RIGHT: the ruling of whichever ink fired hardest here.
                let l = f.ink[best.1].lpi[bi];
                let col = ramp((l - RAMP_LO) / (RAMP_HI - RAMP_LO));
                for y in y0..y1 {
                    for x in x0..x1 {
                        let ox = pw + GUTTER + x;
                        let i = ((y * ow) + ox) * 3;
                        let base = [
                            px[i] as f32 / 255.0,
                            px[i + 1] as f32 / 255.0,
                            px[i + 2] as f32 / 255.0,
                        ];
                        let o = [
                            base[0] + (col[0] - base[0]) * WASH,
                            base[1] + (col[1] - base[1]) * WASH,
                            base[2] + (col[2] - base[2]) * WASH,
                        ];
                        put(&mut px, 1, x, y, o);
                    }
                }
            }
        }
    }
    pilio::write_rgb_png_fast(path, ow, oh, &px)
}

/// One line per page for the terminal: what fired, per ink, and the ruling it settled on. Printed
/// as each page finishes so a run can be stopped on page 3 rather than after 176.
pub fn summarise(page: &str, f: &ScreenField) -> String {
    let n = (f.ny * f.nx).max(1) as f64;
    let mut parts = Vec::new();
    for (ci, nm) in ["C", "M", "Y", "K"].iter().enumerate() {
        let fired: Vec<usize> = (0..f.ny * f.nx)
            .filter(|&i| screen::fired(f, ci, i))
            .collect();
        if fired.is_empty() {
            continue;
        }
        // median ruling over the blocks that fired -- a mean is dragged by the blocks that locked
        // onto a harmonic or onto nothing in particular
        let mut ls: Vec<f32> = fired.iter().map(|&i| f.ink[ci].lpi[i]).collect();
        ls.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let mut as_: Vec<f32> = fired.iter().map(|&i| f.ink[ci].ang[i]).collect();
        as_.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let mut ds: Vec<f32> = fired.iter().map(|&i| f.ink[ci].depth[i]).collect();
        ds.sort_by(|a, b| a.partial_cmp(b).unwrap());
        parts.push(format!(
            "{} {:.0}% {:.0}lpi@{:.0}deg d{:.0}",
            nm,
            100.0 * fired.len() as f64 / n,
            ls[ls.len() / 2],
            as_[as_.len() / 2],
            ds[ds.len() / 2]
        ));
    }
    if parts.is_empty() {
        parts.push("no screen".to_string());
    }
    format!("p{} {}x{} blocks | {}", page, f.ny, f.nx, parts.join("  "))
}
