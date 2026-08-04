//! The debug picture for STAGE C: what each part of the page was routed to. One PNG per page.
//!
//! This is the picture the whole pipeline is judged by, because it shows the DESTINATION of every
//! pixel -- which is the thing that goes wrong, and a question a human can answer at a glance
//! without knowing any threshold.
//!
//! EVERYTHING IS AN OUTLINE. A wash states the verdict and hides the evidence: an area filled with
//! green looks identical whether it holds a photograph or a paragraph, and the pixels that decide
//! whether a boundary is right are precisely the ones a wash recolours. So the page stays legible
//! and every decision is a line drawn on it.
//!
//!   thick GREEN   class 1, colour photo    -> contone CMYK at the screen's own rate
//!   thick BLUE    class 2, greyscale photo -> contone, neutral
//!   thick AMBER   class 3, flat tint/box   -> ONE measured ink percentage, no raster
//!   thin per-ink  class 4, type/line art   -> the bilevel stencil, outlined in its own ink
//!   (no line)     bare paper
//!
//! The two kinds overlap on purpose: lettering on a grey box is class 4 sitting on class 3, and both
//! layers really are there. An amber boundary round a bar with red letterforms outlined inside it is
//! the correct picture for a contents-page tint, and the most informative thing this drawer shows.

use crate::imageio::Cmyk;
use crate::ndimage;
use crate::pilio;
use crate::rectfit::Rect;
use crate::route::{self, Class, Routing};
use crate::screen::{self, ScreenField};
use anyhow::Result;

/// Block index covering a pixel on the stencil grid.
fn screen_block(r: &Routing, cy: usize, cx: usize) -> usize {
    let sdiv = 4; // stencil grid is source/4
    let (sy, sx) = (cy * sdiv, cx * sdiv);
    let by = (sy + screen::STEP / 2).saturating_sub(screen::WIN / 2) / screen::STEP;
    let bx = (sx + screen::STEP / 2).saturating_sub(screen::WIN / 2) / screen::STEP;
    by.min(r.ny - 1) * r.nx + bx.min(r.nx - 1)
}

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Output scale: stencil grid / this. 600/2 = 300 dpi -- fine enough that a stencil boundary is a
/// line rather than a smear, coarse enough for a whole page to be looked at at once.
const SHRINK: usize = 2;

/// Thickness of the screening outline, in output pixels. 5 at 300 dpi is ~0.4 mm: heavy enough to
/// read against a photograph without hiding what it encloses.
const OUTLINE_PX: usize = 5;
/// Saturated yellow -- the one hue that is not otherwise on this paper in quantity.
const OUTLINE_RGB: [f32; 3] = [1.0, 0.85, 0.0];

/// The black-extension PREVIEW, in colours that can never be mistaken for what was actually routed.
/// Yellow is the screened region as it will be rendered. These two are the per-object enclosure
/// test's verdict on the solid black beside it -- see route::BLACK_ENCLOSURE -- and are drawn for
/// judgement only.
///
/// Only what the test ACCEPTS is drawn. The refused objects were drawn too for a while, in red,
/// while the criterion was being calibrated -- that is what showed the first version accepting
/// everything, and what showed p123's banner and p057's reversed panels being turned down. Once
/// the threshold was measured they stopped earning their place on the page: they mark black that
/// changes nothing, since refused black goes exactly where it already goes, the K stencil.
/// The measurement they produced is recorded at route::BLACK_ENCLOSURE.
const BLACK_KEEP_RGB: [f32; 3] = [0.10, 1.0, 0.35];

/// Ink level at which a pixel counts as solid for the preview outline. The same 128 the stencil
/// uses for "ink present", from the bimodal histogram of this paper -- the preview must trace the
/// same pixels the renderer would move, so it must ask the same question of them.
const INK_SOLID: u8 = 128;

/// Closing radius, in debug pixels, applied to the preview mask before outlining it. Removes
/// sub-threshold speckle inside solid ink. 2 px at SHRINK=2 is 0.17 mm on the page -- smaller than
/// any feature the preview is meant to show, larger than the noise it is meant to ignore.
const SPECKLE_PX: usize = 2;

/// The fitted rectangle, where one was accepted -- see rectfit.rs. Distinct from the region's own
/// yellow outline because the whole question is how far the two differ, and from the black
/// preview's green because they answer different questions about the same edge.
const RECT_RGB: [f32; 3] = [0.15, 0.45, 1.0];

/// How far the page is lifted toward white before the outlines go on. Enough that a saturated
/// outline reads against a dark photograph, little enough that the page is still the page.
const LIFT: f32 = 0.35;

const COL_COLOUR: [f32; 3] = [0.10, 0.70, 0.30]; // class 1
const COL_GREY: [f32; 3] = [0.15, 0.45, 0.95]; // class 2
const COL_FLAT: [f32; 3] = [0.95, 0.65, 0.10]; // class 3
const COL_STENCIL: [f32; 3] = [0.90, 0.12, 0.12]; // class 4
const COL_EDGE: [f32; 3] = [0.05, 0.05, 0.05]; // area outline

// ================================================================================================

/// ONE LINE ROUND THE SCREENED CONTENT, and nothing else.
///
/// The page as scanned, with a thick yellow outline where the screened regions end. No class
/// colours, no stencil outlines, no washes -- the single question this answers is "did we find the
/// screening, and does the boundary sit where the screening actually stops".
///
/// The boundary is the PIXEL-refined one (see `Routing::pix`), so it follows the true contour at
/// 600 dpi rather than staircasing round the 1.35 mm block grid.
pub fn write_png(path: &str, disp: &Cmyk, r: &Routing, f: &ScreenField, rects: &[Rect]) -> Result<()> {
    let (w, h) = (r.sw / SHRINK, r.sh / SHRINK);
    let mut px = vec![255u8; w * h * 3];
    let sdiv = (disp.w / r.sw).max(1);

    // the page, as it is -- no lift, no wash. It is the evidence.
    for y in 0..h {
        for x in 0..w {
            let (sy, sx) = (y * SHRINK * sdiv, x * SHRINK * sdiv);
            let si = sy.min(disp.h - 1) * disp.w + sx.min(disp.w - 1);
            let (c, m, yv, k) = (
                disp.c[si] as f32,
                disp.m[si] as f32,
                disp.y[si] as f32,
                disp.k[si] as f32,
            );
            let f = |v: f32| ((1.0 - v / 255.0) * (1.0 - k / 255.0) * 255.0).clamp(0.0, 255.0) as u8;
            let i = (y * w + x) * 3;
            px[i] = f(c);
            px[i + 1] = f(m);
            px[i + 2] = f(yv);
        }
    }

    // the boundary of the screened area, thick
    let inside = |cy: usize, cx: usize| -> bool { r.pix[cy * r.sw + cx] };
    let mut edge = vec![false; w * h];
    for y in 0..h {
        for x in 0..w {
            let (cy, cx) = (y * SHRINK, x * SHRINK);
            if cy >= r.sh || cx >= r.sw || !inside(cy, cx) {
                continue;
            }
            let is_edge = [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)].iter().any(|(dy, dx)| {
                let (y2, x2) = (cy as i64 + dy * SHRINK as i64, cx as i64 + dx * SHRINK as i64);
                y2 < 0
                    || x2 < 0
                    || y2 >= r.sh as i64
                    || x2 >= r.sw as i64
                    || !inside(y2 as usize, x2 as usize)
            });
            if is_edge {
                edge[y * w + x] = true;
            }
        }
    }
    for y in 0..h {
        for x in 0..w {
            if !edge[y * w + x] {
                continue;
            }
            // CENTRED on the boundary, not hung off it. Painting the brush at (x+dx, y+dy) for
            // dx,dy in 0..N offsets the whole line N px right and down and never left or up, so it
            // sits OUTSIDE the region on two sides and inside on none -- 0.42 mm of apparent bleed
            // at 300 dpi, which reads exactly like the detector over-reaching.
            let half = (OUTLINE_PX / 2) as i64;
            for dy in -half..=half {
                for dx in -half..=half {
                    let (yy, xx) = (y as i64 + dy, x as i64 + dx);
                    if yy >= 0 && xx >= 0 && (yy as usize) < h && (xx as usize) < w {
                        let (yy, xx) = (yy as usize, xx as usize);
                        let i = (yy * w + xx) * 3;
                        px[i] = (OUTLINE_RGB[0] * 255.0) as u8;
                        px[i + 1] = (OUTLINE_RGB[1] * 255.0) as u8;
                        px[i + 2] = (OUTLINE_RGB[2] * 255.0) as u8;
                    }
                }
            }
        }
    }
    // the black-extension preview, outlined the same way in its own colours. Drawn after the yellow
    // so that where they coincide the preview is what shows -- the question being asked is what the
    // extension adds, and a boundary it shares with the region is not an addition.
    {
        let colour = BLACK_KEEP_RGB;
        // AT PIXEL RESOLUTION, like the yellow beside it. Drawn per BLOCK the two outlines could not
        // meet: yellow follows r.pix, refined pixel by pixel on coherence, while a block is 128 px =
        // 1.35 mm. Solid black has no coherence, so the black inside a boundary block falls outside
        // yellow, and it fell outside a per-block green too because that green drew only blocks the
        // region had NOT yet claimed. On p166 that is 186 of 407 solid-black blocks belonging to
        // neither outline -- a block-wide gap between them, which read as the two disagreeing when
        // they do not. What the extension actually moves is PIXELS, from the stencil to the contone,
        // so the preview is drawn as those pixels: solid ink, in an accepted object, not already
        // screen. It meets the yellow exactly because between them there is nothing else.
        let mut bp = vec![false; w * h];
        for y in 0..h {
            for x in 0..w {
                let (cy, cx) = (y * SHRINK, x * SHRINK);
                if cy >= r.sh || cx >= r.sw || r.pix[cy * r.sw + cx] {
                    continue; // already screen: the yellow speaks for it
                }
                let (sy, sx) = ((cy * sdiv).min(disp.h - 1), (cx * sdiv).min(disp.w - 1));
                if !r.black_obj[route::block_of_source(f, sy, sx)] {
                    continue;
                }
                if disp.k[sy * disp.w + sx] >= INK_SOLID {
                    bp[y * w + x] = true;
                }
            }
        }
        // Solid ink on this paper is not solid at every pixel -- ink variation and scan noise leave
        // scattered pixels under the threshold inside a black field. Each is a one-pixel hole and
        // each would be outlined, speckling the preview with boundaries that mark nothing. A closing
        // of SPECKLE_PX removes holes that small and leaves every real edge where it was.
        let bp = ndimage::binary_closing(&bp, w, h, SPECKLE_PX);
        let half = (OUTLINE_PX / 2) as i64;
        for y in 0..h {
            for x in 0..w {
                if !bp[y * w + x] {
                    continue;
                }
                let is_edge = [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)].iter().any(|(dy, dx)| {
                    let (y2, x2) = (y as i64 + dy, x as i64 + dx);
                    y2 < 0 || x2 < 0 || y2 >= h as i64 || x2 >= w as i64
                        || !bp[y2 as usize * w + x2 as usize]
                });
                if !is_edge {
                    continue;
                }
                for dy in -half..=half {
                    for dx in -half..=half {
                        let (yy, xx) = (y as i64 + dy, x as i64 + dx);
                        if yy >= 0 && xx >= 0 && (yy as usize) < h && (xx as usize) < w {
                            let i = (yy as usize * w + xx as usize) * 3;
                            px[i] = (colour[0] * 255.0) as u8;
                            px[i + 1] = (colour[1] * 255.0) as u8;
                            px[i + 2] = (colour[2] * 255.0) as u8;
                        }
                    }
                }
            }
        }
    }
    // the fitted rectangles, as an outline in their own colour. Only the accepted ones: a refused
    // rectangle is a rectangle that will not be used, and the page already shows what happens
    // instead -- the region's own outline, in yellow, right there.
    for q in rects.iter().filter(|q| q.ok) {
        let (y0, x0) = (q.y0 / SHRINK, q.x0 / SHRINK);
        let (y1, x1) = ((q.y1 / SHRINK).min(h - 1), (q.x1 / SHRINK).min(w - 1));
        let half = (OUTLINE_PX / 2) as i64;
        let mut put = |y: usize, x: usize| {
            for dy in -half..=half {
                for dx in -half..=half {
                    let (yy, xx) = (y as i64 + dy, x as i64 + dx);
                    if yy >= 0 && xx >= 0 && (yy as usize) < h && (xx as usize) < w {
                        let i = (yy as usize * w + xx as usize) * 3;
                        px[i] = (RECT_RGB[0] * 255.0) as u8;
                        px[i + 1] = (RECT_RGB[1] * 255.0) as u8;
                        px[i + 2] = (RECT_RGB[2] * 255.0) as u8;
                    }
                }
            }
        };
        for x in x0..=x1 {
            put(y0, x);
            put(y1, x);
        }
        for y in y0..=y1 {
            put(y, x0);
            put(y, x1);
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

// ================================================================================================
//  THE GROUPING STAGES, ONE PICTURE
// ================================================================================================

/// Colours for the four grouping steps. Chosen to be told apart at a glance and against a grey page.
const ST_SCREEN: [f32; 3] = [0.10, 0.70, 0.25]; // 1 measured a halftone
const ST_ABSORB: [f32; 3] = [0.10, 0.40, 0.95]; // 2 near-solid ink reached from those tiles
const ST_FILL: [f32; 3] = [0.95, 0.60, 0.05];   // 3 enclosed by the result
const ST_RIM: [f32; 3] = [0.85, 0.10, 0.75];    // 4 the one-tile rim

/// How strongly a stage tints its tiles. Light: the page underneath is the evidence.
const ST_WASH: f32 = 0.45;

/// WHAT EACH GROUPING STEP CONTRIBUTED, in four colours on one page.
///
/// The finished region tells you nothing about how it was reached, and each of the four steps fails
/// in its own way -- screening misses a tile, absorption walks into text, the fill swallows an
/// enclosed column, the rim reaches over a caption. Tinting each step's OWN contribution separates
/// them: a wrong shape can be attributed to the step that made it instead of guessed at.
///
/// Tiles are drawn as tiles, deliberately. The block grid is the unit these decisions are made in,
/// and seeing it is the point -- a staircase on the block boundary is a fact about the method, not
/// an artifact of the drawing.
pub fn write_stages_png(path: &str, disp: &Cmyk, r: &Routing) -> Result<()> {
    let (w, h) = (r.sw / SHRINK, r.sh / SHRINK);
    let mut px = vec![255u8; w * h * 3];
    let sdiv = (disp.w / r.sw).max(1);
    let cell = (sdiv * SHRINK).max(1);
    let put = |px: &mut Vec<u8>, x: usize, y: usize, c: [f32; 3]| {
        let i = (y * w + x) * 3;
        px[i] = (c[0] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 1] = (c[1] * 255.0).clamp(0.0, 255.0) as u8;
        px[i + 2] = (c[2] * 255.0).clamp(0.0, 255.0) as u8;
    };
    let get = |px: &Vec<u8>, x: usize, y: usize| -> [f32; 3] {
        let i = (y * w + x) * 3;
        [px[i] as f32 / 255.0, px[i + 1] as f32 / 255.0, px[i + 2] as f32 / 255.0]
    };

    // the page, lifted
    for y in 0..h {
        for x in 0..w {
            let (sy, sx) = (y * SHRINK * sdiv, x * SHRINK * sdiv);
            let si = sy.min(disp.h - 1) * disp.w + sx.min(disp.w - 1);
            let (c, m, yv, k) = (
                disp.c[si] as f32,
                disp.m[si] as f32,
                disp.y[si] as f32,
                disp.k[si] as f32,
            );
            let f = |v: f32| {
                let t = (1.0 - v / 255.0) * (1.0 - k / 255.0);
                t + (1.0 - t) * 0.30
            };
            put(&mut px, x, y, [f(c), f(m), f(yv)]);
        }
    }

    // each stage's own tiles, in order, so a later step draws over an earlier one only where it
    // genuinely added something
    let half = screen::STEP / 2;
    for (mask, col) in [
        (&r.st_screen, ST_SCREEN),
        (&r.st_absorb, ST_ABSORB),
        (&r.st_fill, ST_FILL),
        (&r.st_rim, ST_RIM),
    ] {
        for by in 0..r.ny {
            for bx in 0..r.nx {
                if !mask[by * r.nx + bx] {
                    continue;
                }
                let (cy, cx) = screen::centre_of(by, bx);
                let y0 = cy.saturating_sub(half) / cell;
                let x0 = cx.saturating_sub(half) / cell;
                let y1 = ((cy + half) / cell).min(h);
                let x1 = ((cx + half) / cell).min(w);
                for y in y0..y1 {
                    for x in x0..x1 {
                        let b = get(&px, x, y);
                        // leave a one-pixel gutter so the tile grid stays visible
                        let inner = y > y0 && x > x0 && y + 1 < y1 && x + 1 < x1;
                        let t = if inner { ST_WASH } else { ST_WASH * 0.35 };
                        put(&mut px, x, y, [
                            b[0] + (col[0] - b[0]) * t,
                            b[1] + (col[1] - b[1]) * t,
                            b[2] + (col[2] - b[2]) * t,
                        ]);
                    }
                }
            }
        }
    }
    pilio::write_rgb_png_fast(path, w, h, &px)
}
