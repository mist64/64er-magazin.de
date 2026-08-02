//! The debug picture for STAGE C: what each part of the page was routed to. One PNG per page.
//!
//! This is the picture the whole pipeline is judged by, because it shows the DESTINATION of every
//! pixel -- which is the thing that goes wrong, and a question a human can answer at a glance
//! without knowing any threshold.
//!
//!   GREEN   class 1, colour photo   -> contone CMYK at the screen's own rate
//!   BLUE    class 2, greyscale photo-> contone, neutral
//!   AMBER   class 3, flat tint/box  -> ONE measured ink percentage, no raster at all
//!   RED     class 4, type/line art  -> per-ink bilevel stencil at 600 dpi
//!   (none)  bare paper
//!
//! Red is drawn ON TOP of the area colours, because that is the truth of the output: lettering on a
//! grey box is class 4 sitting on class 3, and both layers are really there. An amber box with red
//! letters on it is the correct picture for a contents-page tint bar, and the single most
//! informative thing this drawer can show.
//!
//! Areas are also OUTLINED, not only washed. A wash says what a region became; the outline says
//! where the region ends, and region boundaries are where routing errors actually live -- a photo
//! whose edge is one block short leaks its own frame into the stencil.

use crate::imageio::Cmyk;
use crate::pilio;
use crate::route::{Class, Routing};
use crate::screen;
use anyhow::Result;

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Output scale: stencil grid / this. 600/4 = 150 dpi, a readable A4.
const SHRINK: usize = 4;

/// Area wash strength, and the stronger stencil wash drawn over it.
const AREA_WASH: f32 = 0.42;
const STENCIL_WASH: f32 = 0.80;

/// Page grey is lifted toward white by this before washing.
const LIFT: f32 = 0.45;

const COL_COLOUR: [f32; 3] = [0.10, 0.70, 0.30]; // class 1
const COL_GREY: [f32; 3] = [0.15, 0.45, 0.95]; // class 2
const COL_FLAT: [f32; 3] = [0.95, 0.65, 0.10]; // class 3
const COL_STENCIL: [f32; 3] = [0.90, 0.12, 0.12]; // class 4
const COL_EDGE: [f32; 3] = [0.05, 0.05, 0.05]; // area outline

// ================================================================================================

pub fn write_png(path: &str, disp: &Cmyk, r: &Routing) -> Result<()> {
    let (w, h) = (r.sw / SHRINK, r.sh / SHRINK);
    let mut px = vec![255u8; w * h * 3];
    let sdiv = (disp.w / r.sw).max(1);

    let put = |px: &mut Vec<u8>, x: usize, y: usize, c: [f32; 3]| {
        let i = (y * w + x) * 3;
        px[i] = (c[0] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 1] = (c[1] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 2] = (c[2] * 255.0).clamp(0.0, 255.0) as u8;
    };
    let get = |px: &Vec<u8>, x: usize, y: usize| -> [f32; 3] {
        let i = (y * w + x) * 3;
        [
            px[i] as f32 / 255.0,
            px[i + 1] as f32 / 255.0,
            px[i + 2] as f32 / 255.0,
        ]
    };
    let blend = |base: [f32; 3], c: [f32; 3], t: f32| -> [f32; 3] {
        [
            base[0] + (c[0] - base[0]) * t,
            base[1] + (c[1] - base[1]) * t,
            base[2] + (c[2] - base[2]) * t,
        ]
    };

    // ---- the page, lifted -----------------------------------------------------------------
    for y in 0..h {
        for x in 0..w {
            let (sy, sx) = (y * SHRINK * sdiv, x * SHRINK * sdiv);
            let si = sy.min(disp.h - 1) * disp.w + sx.min(disp.w - 1);
            let ink = disp.c[si] as f32 + disp.m[si] as f32 + disp.y[si] as f32
                + disp.k[si] as f32 * 1.5;
            let g = (1.0 - (ink / 420.0).min(1.0)).clamp(0.0, 1.0);
            let g = g + (1.0 - g) * LIFT;
            put(&mut px, x, y, [g, g, g]);
        }
    }

    // ---- area washes, by class ------------------------------------------------------------
    // Each block owns the STEP x STEP cell centred on its window, so adjacent blocks tile exactly.
    let half = screen::STEP / 2;
    for by in 0..r.ny {
        for bx in 0..r.nx {
            let l = r.label[by * r.nx + bx];
            if l == 0 {
                continue;
            }
            let col = match r.areas[(l - 1) as usize].class {
                Class::ColourPhoto => COL_COLOUR,
                Class::GreyPhoto => COL_GREY,
                Class::Flat => COL_FLAT,
            };
            let (cy, cx) = screen::centre_of(by, bx);
            let y0 = cy.saturating_sub(half) / (sdiv * SHRINK);
            let x0 = cx.saturating_sub(half) / (sdiv * SHRINK);
            let y1 = ((cy + half) / (sdiv * SHRINK)).min(h);
            let x1 = ((cx + half) / (sdiv * SHRINK)).min(w);
            for y in y0..y1 {
                for x in x0..x1 {
                    let b = get(&px, x, y);
                    put(&mut px, x, y, blend(b, col, AREA_WASH));
                }
            }
        }
    }

    // ---- area outlines --------------------------------------------------------------------
    for by in 0..r.ny {
        for bx in 0..r.nx {
            let l = r.label[by * r.nx + bx];
            if l == 0 {
                continue;
            }
            let edge = [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)].iter().any(|(dy, dx)| {
                let ny2 = by as i64 + dy;
                let nx2 = bx as i64 + dx;
                ny2 < 0
                    || nx2 < 0
                    || ny2 >= r.ny as i64
                    || nx2 >= r.nx as i64
                    || r.label[ny2 as usize * r.nx + nx2 as usize] != l
            });
            if !edge {
                continue;
            }
            let (cy, cx) = screen::centre_of(by, bx);
            let y0 = cy.saturating_sub(half) / (sdiv * SHRINK);
            let x0 = cx.saturating_sub(half) / (sdiv * SHRINK);
            let y1 = ((cy + half) / (sdiv * SHRINK)).min(h);
            let x1 = ((cx + half) / (sdiv * SHRINK)).min(w);
            for y in y0..y1 {
                for x in x0..x1 {
                    if y == y0 || x == x0 || y + 1 == y1 || x + 1 == x1 {
                        put(&mut px, x, y, COL_EDGE);
                    }
                }
            }
        }
    }

    // ---- the stencil, on top ---------------------------------------------------------------
    // Maximum over the shrink cell, not the mean: a hairline covering one stencil pixel in sixteen
    // must still be visible, or this drawer will report a clean page that is actually losing marks.
    for y in 0..h {
        for x in 0..w {
            let mut hit = false;
            'cell: for dy in 0..SHRINK {
                for dx in 0..SHRINK {
                    let (sy, sx) = (y * SHRINK + dy, x * SHRINK + dx);
                    if sy >= r.sh || sx >= r.sw {
                        continue;
                    }
                    if (0..4).any(|ci| r.stencil[ci][sy * r.sw + sx]) {
                        hit = true;
                        break 'cell;
                    }
                }
            }
            if hit {
                let b = get(&px, x, y);
                put(&mut px, x, y, blend(b, COL_STENCIL, STENCIL_WASH));
            }
        }
    }

    pilio::write_rgb_png_fast(path, w, h, &px)
}

// ================================================================================================
//  THE TYPE-OUTLINE VIEW
// ================================================================================================

/// Output scale for the outline view: stencil grid / this. 1 = the full 600 dpi stencil grid.
///
/// NOT REDUCIBLE. A body-text stroke is ~5 px wide at 600 dpi, so its boundary is 1 px of that and
/// the outline reads as an outline. At 300 dpi the stroke is 2.5 px, its boundary is essentially all
/// of it, and every glyph fills in solid -- which is the wash this view exists to replace. The page
/// is ~10 MB; that is the correct trade for the one picture that shows whether a serif survived.
const OUT_SHRINK: usize = 1;

/// How dark the page is drawn under the outlines. Lighter than the destination view: here the page
/// is the evidence, not the backdrop, and the outlines must not compete with it.
const OUT_LIFT: f32 = 0.30;

/// Outline colour per ink. Saturated, because these are hairlines on a light page.
const OUT_RGB: [[f32; 3]; 4] = [
    [0.00, 0.55, 0.95], // C
    [0.95, 0.00, 0.55], // M
    [0.85, 0.65, 0.00], // Y
    [0.90, 0.10, 0.10], // K
];

/// EVERY MARK THE STENCIL WILL DRAW, OUTLINED RATHER THAN COVERED.
///
/// The destination view washes the stencil red, which answers "how much" but hides the one thing
/// worth checking: WHICH marks. A wash over a paragraph looks identical whether the stencil has the
/// glyphs or a solid rectangle over them. Outlining leaves the type legible inside its own outline,
/// so a lost serif, a filled counter, a glyph that never made it into the layer, and a halftone dot
/// that should not be there are all visible directly.
///
/// Drawn per ink, so a red heading shows a magenta AND a yellow outline where both plates carry it.
/// That is how the p007 red-heading bug would have looked: yellow outlines with no magenta.
pub fn write_outline_png(path: &str, disp: &Cmyk, r: &Routing) -> Result<()> {
    let (w, h) = (r.sw / OUT_SHRINK, r.sh / OUT_SHRINK);
    let mut px = vec![255u8; w * h * 3];
    let sdiv = (disp.w / r.sw).max(1);

    // the page itself, in colour, lifted
    for y in 0..h {
        for x in 0..w {
            let (sy, sx) = (y * OUT_SHRINK * sdiv, x * OUT_SHRINK * sdiv);
            let si = sy.min(disp.h - 1) * disp.w + sx.min(disp.w - 1);
            let (c, m, yv, k) = (
                disp.c[si] as f32,
                disp.m[si] as f32,
                disp.y[si] as f32,
                disp.k[si] as f32,
            );
            let f = |v: f32| {
                let t = (1.0 - v / 255.0) * (1.0 - k / 255.0);
                t + (1.0 - t) * OUT_LIFT
            };
            let i = (y * w + x) * 3;
            px[i] = (f(c) * 255.0) as u8;
            px[i + 1] = (f(m) * 255.0) as u8;
            px[i + 2] = (f(yv) * 255.0) as u8;
        }
    }

    // boundary pixels of each ink's stencil: set, with at least one unset 4-neighbour
    for ci in 0..4 {
        let m = &r.stencil[ci];
        for sy in 0..r.sh {
            for sx in 0..r.sw {
                if !m[sy * r.sw + sx] {
                    continue;
                }
                let edge = [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)].iter().any(|(dy, dx)| {
                    let (y2, x2) = (sy as i64 + dy, sx as i64 + dx);
                    y2 < 0
                        || x2 < 0
                        || y2 >= r.sh as i64
                        || x2 >= r.sw as i64
                        || !m[y2 as usize * r.sw + x2 as usize]
                });
                if !edge {
                    continue;
                }
                let (y, x) = (sy / OUT_SHRINK, sx / OUT_SHRINK);
                if y >= h || x >= w {
                    continue;
                }
                let i = (y * w + x) * 3;
                for k in 0..3 {
                    px[i + k] = (OUT_RGB[ci][k] * 255.0) as u8;
                }
            }
        }
    }
    pilio::write_rgb_png_fast(path, w, h, &px)
}
