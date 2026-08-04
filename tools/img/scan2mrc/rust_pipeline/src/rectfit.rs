//! RECTANGLE FIT — experiment, drawn in the debug PNG, read by nothing that routes.
//!
//! In 1986 prepress a photograph was a PLACED RECTANGLE and a tint box was a rectangle. So where a
//! detected region really is one, its true boundary is not the one the detector traced: it is the
//! rectangle the layout contained. Snapping to it is not smoothing a measurement, it is recovering
//! the object -- and it replaces a boundary that depends on detector noise at the edges with one
//! that depends on the page.
//!
//! The operation is a FIT, not a growth. Both failures are on this paper and they are opposite:
//!
//!   p051  the Activision logo box and the screenshots come out fragmentary -- the region covers
//!         part of the object and the rest never fired. The rectangle is OUTSIDE the region.
//!   p055  four flat grey boxes, each genuinely a rectangle, arrive with a jagged outline that
//!         bulges past the box in places and falls short in others. The rectangle is BOTH sides.
//!
//! A grow-only rule fixes the first and not the second, so the edges are not derived from the
//! region at all. They are measured from the PAGE: over a window around the region, the fraction of
//! inked pixels per row and per column is a step profile for anything rectangular, and its edges
//! are where that profile crosses. The region only says where to look.
//!
//! WHAT MAKES IT SAFE IS THE RING, NOT THE PROFILE. A rectangle is accepted only when the ring of
//! paper just outside it is clear: nothing crosses that boundary, so the rectangle cannot be
//! cutting through an object or welding two together. p166's wordmark is the case this must refuse
//! -- it is not rectangular, its ring is full of ink, and it is left alone.
//!
//! Deliberately NOT a condition: "every pixel added is paper or screened". It sounds safe and it is
//! wrong, because the objects most worth snapping are composites -- p166's wordmark is a screened
//! gradient plus solid black line art, p051's logo is a tint plus type. Their unfired pixels are
//! solid ink, so that rule vetoes exactly the cases it was meant to serve.

use crate::imageio::Cmyk;
use crate::ndimage;
use crate::screen;

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Mean ink, over one screen cell, above which that place on the page counts as carrying ink.
/// PROVISIONAL -- this is the constant that most wants deriving from the per-issue paper
/// measurement rather than assumed, since it is the whole basis of the ring test.
///
/// ASKED OVER A CELL, NEVER PER PIXEL. At 2400 dpi a tint IS dots: a single pixel inside a 25% grey
/// box is ink or paper depending on where the dot fell, so a per-pixel test returns a draw from the
/// screen rather than a fact about the page. Measured on p055, whose four grey boxes are exactly
/// the case this rule exists for, a per-pixel test put their inked fraction at 0.62-0.65 -- their
/// dot area, not their extent -- and the boxes were refused for not being solid. Over a cell the
/// same box reads as ink everywhere, which is what it is. 20 of 255 is 8% dot area, below the
/// lightest tint on this issue (~12%) and far above paper.
const PAPER_INK: f32 = 20.0;

/// Averaging window for that question, in coherence-grid pixels. One screen cell at the coarsest
/// ruling here (134 lpi at 2400 dpi = 17.9 source px) is ~4.5 grid pixels; 5 covers it.
const CELL_PX: usize = 5;

/// How far outside the region's own bounding box to look for the rectangle's edge, in BLOCKS.
/// A photograph's lightest edge tone routinely fails to fire, so the true placed edge lies outside
/// what was detected; 4 blocks is 5.4 mm at 2400 dpi.
const SEARCH_BLOCKS: usize = 4;

/// Inked fraction of a row or column, within the search window, above which that line counts as
/// part of the object. A rectangle gives a step profile, so the exact value matters little; 0.5
/// puts the edge at the half-height of the step.
const PROFILE_MIN: f32 = 0.5;

/// Fraction of the ring just outside the fitted rectangle that must be paper. NOT 1.0: paper
/// texture, show-through and a neighbouring column's descender all put ink on a ring that is
/// otherwise clear, and one speck must not veto a good rectangle.
const RING_PAPER: f32 = 0.92;

/// Thickness of that ring, in pixels of the coherence grid, and how far outside the rectangle it
/// starts. The GAP is not slack, it is required: ink density is measured over a cell (see
/// PAPER_INK), so every reading within a cell of the object's edge is contaminated by the object
/// itself. Without it the ring is biased down everywhere and boxes that sit in clear paper are
/// refused for their own edge -- p055's four grey boxes read 0.24/0.87/0.90/0.92 against a
/// threshold of 0.92 when the ring began at the boundary.
const RING_PX: usize = 6;
const RING_GAP: usize = CELL_PX;

/// Fraction of the fitted rectangle that must actually be inked. This is what refuses an L-shape,
/// and what refuses a region that merged two objects with white between them -- their common
/// rectangle is mostly paper. It is the guard that keeps this rule from doing what CLOSE_BLOCKS = 0
/// forbids: claiming a gap the layout put there.
const FILL_MIN: f32 = 0.70;

pub struct Rect {
    pub id: usize,
    /// fitted rectangle, in coherence-grid pixels
    pub y0: usize,
    pub x0: usize,
    pub y1: usize,
    pub x1: usize,
    pub fill: f32,
    pub ring: f32,
    pub ok: bool,
    /// blocks the region has now, and the area of the fitted rectangle in the same unit
    pub blocks: usize,
}

/// EXPERIMENT: whether an accepted rectangle actually replaces the region's pixel boundary, or is
/// only drawn. See the header. With this off nothing here reaches the renderer.
pub const RECT_SNAP: bool = true;

/// Fit a rectangle to every region and say whether it may be trusted.
pub fn fit(
    disp: &Cmyk,
    label: &[u32],
    ny: usize,
    nx: usize,
    sw: usize,
    sh: usize,
) -> Vec<Rect> {
    let sdiv = (disp.w / sw).max(1);
    // strongest ink at each grid pixel, then averaged over a cell -- see PAPER_INK
    let mut peak = vec![0.0f32; sw * sh];
    for y in 0..sh {
        for x in 0..sw {
            let (sy, sx) = ((y * sdiv).min(disp.h - 1), (x * sdiv).min(disp.w - 1));
            let i = sy * disp.w + sx;
            peak[y * sw + x] =
                disp.c[i].max(disp.m[i]).max(disp.y[i]).max(disp.k[i]) as f32;
        }
    }
    let dens = ndimage::uniform_filter(&peak, sw, sh, CELL_PX);
    let inked = |y: usize, x: usize| -> bool { dens[y.min(sh - 1) * sw + x.min(sw - 1)] > PAPER_INK };

    // block -> coherence-grid pixel, via the block's own centre so this agrees with the label map
    let blk_px = (screen::STEP / sdiv).max(1);
    let nregions = label.iter().cloned().max().unwrap_or(0) as usize;
    let mut out = Vec::new();

    for id in 1..=nregions {
        let (mut by0, mut bx0, mut by1, mut bx1) = (usize::MAX, usize::MAX, 0usize, 0usize);
        let mut nblk = 0usize;
        for i in 0..ny * nx {
            if label[i] as usize != id {
                continue;
            }
            nblk += 1;
            let (by, bx) = (i / nx, i % nx);
            by0 = by0.min(by);
            bx0 = bx0.min(bx);
            by1 = by1.max(by);
            bx1 = bx1.max(bx);
        }
        if nblk == 0 {
            continue;
        }

        // search window: the region's bbox, in grid pixels, opened by SEARCH_BLOCKS
        let m = SEARCH_BLOCKS * blk_px;
        let (cy0, cx0) = screen::centre_of(by0, bx0);
        let (cy1, cx1) = screen::centre_of(by1, bx1);
        let half = screen::STEP / 2;
        let wy0 = (cy0.saturating_sub(half) / sdiv).saturating_sub(m);
        let wx0 = (cx0.saturating_sub(half) / sdiv).saturating_sub(m);
        let wy1 = (((cy1 + half) / sdiv) + m).min(sh);
        let wx1 = (((cx1 + half) / sdiv) + m).min(sw);
        if wy1 <= wy0 + 2 || wx1 <= wx0 + 2 {
            continue;
        }

        // EDGES FROM THE PAGE, not from the region: the inked fraction per row and per column is a
        // step for anything rectangular, and the edge is where it crosses. Two things about how it
        // is measured decide whether this works at all.
        //
        // MEASURED OVER THE REGION'S OWN EXTENT, not over the search window. A row's inked fraction
        // taken across the whole window is dominated by whatever else shares that band of the page:
        // on p055 the body text beside the grey boxes made every text row read above PROFILE_MIN,
        // the run walked out across the column, and the fitted rectangle covered box and text alike
        // (fill 0.66, ring 0.38 -- refused, but for the wrong reason).
        //
        // AND THE RUN MUST CONTAIN THE REGION, not merely be the longest one in view. The longest
        // run in a window that clips a neighbouring column is the neighbour.
        let (py0, px0) = (cy0.saturating_sub(half) / sdiv, cx0.saturating_sub(half) / sdiv);
        let (py1, px1) = (((cy1 + half) / sdiv).min(sh), ((cx1 + half) / sdiv).min(sw));
        if py1 <= py0 || px1 <= px0 {
            continue;
        }
        let run = |prof: &Vec<f32>, anchor: usize| -> Option<(usize, usize)> {
            if anchor >= prof.len() || prof[anchor] < PROFILE_MIN {
                return None;
            }
            let mut s = anchor;
            while s > 0 && prof[s - 1] >= PROFILE_MIN {
                s -= 1;
            }
            let mut e = anchor;
            while e + 1 < prof.len() && prof[e + 1] >= PROFILE_MIN {
                e += 1;
            }
            Some((s, e))
        };

        let rows: Vec<f32> = (wy0..wy1)
            .map(|y| (px0..px1).filter(|&x| inked(y, x)).count() as f32 / (px1 - px0) as f32)
            .collect();
        let cols: Vec<f32> = (wx0..wx1)
            .map(|x| (py0..py1).filter(|&y| inked(y, x)).count() as f32 / (py1 - py0) as f32)
            .collect();
        let ay = (py0 + py1) / 2 - wy0;
        let ax = (px0 + px1) / 2 - wx0;
        let (ry, rx) = match (run(&rows, ay), run(&cols, ax)) {
            (Some(a), Some(b)) => (a, b),
            _ => continue,
        };
        let (y0, y1) = (wy0 + ry.0, wy0 + ry.1);
        let (x0, x1) = (wx0 + rx.0, wx0 + rx.1);
        if y1 <= y0 || x1 <= x0 {
            continue;
        }

        // fill: is the rectangle actually solid with object, or is it mostly the paper between two
        let mut ink = 0usize;
        for y in y0..=y1 {
            for x in x0..=x1 {
                if inked(y, x) {
                    ink += 1;
                }
            }
        }
        let area = (y1 - y0 + 1) * (x1 - x0 + 1);
        let fill = ink as f32 / area as f32;

        // the ring: nothing may cross the boundary we are about to declare
        let (mut clear, mut total) = (0usize, 0usize);
        let ry0 = y0.saturating_sub(RING_GAP + RING_PX);
        let rx0 = x0.saturating_sub(RING_GAP + RING_PX);
        let ry1 = (y1 + RING_GAP + RING_PX).min(sh - 1);
        let rx1 = (x1 + RING_GAP + RING_PX).min(sw - 1);
        let (gy0, gx0) = (y0.saturating_sub(RING_GAP), x0.saturating_sub(RING_GAP));
        let (gy1, gx1) = ((y1 + RING_GAP).min(sh - 1), (x1 + RING_GAP).min(sw - 1));
        for y in ry0..=ry1 {
            for x in rx0..=rx1 {
                let inside = y >= gy0 && y <= gy1 && x >= gx0 && x <= gx1;
                if inside {
                    continue;
                }
                total += 1;
                if !inked(y, x) {
                    clear += 1;
                }
            }
        }
        let ring = if total == 0 { 0.0 } else { clear as f32 / total as f32 };

        out.push(Rect {
            id: id - 1,
            y0,
            x0,
            y1,
            x1,
            fill,
            ring,
            ok: fill >= FILL_MIN && ring >= RING_PAPER,
            blocks: nblk,
        });
    }
    out
}
