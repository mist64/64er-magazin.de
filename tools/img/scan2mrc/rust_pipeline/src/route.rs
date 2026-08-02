//! STAGE C — routing. Where the four content classes are finally assigned, out of the two physical
//! questions stages A and B measured. There is no classifier here and no vote; every branch below
//! reads a measurement.
//!
//!     is there a screen?          stage A, per ink, per block
//!     does its dot area vary?     stage B, per ink, over an area
//!
//!     screened + varying + colour inks  -> CLASS 1  colour photo      -> contone, CMYK
//!     screened + varying + neutral only -> CLASS 2  greyscale photo   -> contone, K
//!     screened + uniform                -> CLASS 3  tint / box        -> flat fill at measured ink %
//!     not screened                      -> CLASS 4  type and line art -> per-ink bilevel stencil
//!
//! CLASS 4 IS NOT A REGION. The first three are areas on the page; the fourth is every pixel that
//! carries ink the screen model cannot explain, wherever it is -- including inside a class 3 tint,
//! which is the whole point. Lettering on a grey box is class 4 sitting on class 3, not a boundary
//! dispute between them. So the stencil is computed per pixel and the areas are computed per block,
//! and they deliberately overlap.
//!
//! UNIFORMITY IS JUDGED AT TWO SCALES, AND BOTH ARE NECESSARY.
//!
//!   WITHIN a block   separates a tint bar from the photograph beside it. A connected screened
//!                    region routinely holds both -- on p092 the closing merges a header bar, two
//!                    photographs and a reversed box into ONE component of 6688 blocks, and asking
//!                    that component whether it is uniform is as meaningless as asking a cluster
//!                    whether it was a photo or type (FINDINGS.md 3: the unit was wrong).
//!   ACROSS an area   catches a smooth gradient. Inside 1.35 mm a soft photographic passage IS
//!                    flat, so the block test alone called p007's Spindizzy artwork (M113 Y112
//!                    K141) a flat fill. A real tint is flat locally AND from end to end; a
//!                    photograph is flat locally and varies across itself.
//!
//! Neither test alone is safe, and the failure directions are opposite -- which is why both are
//! applied and an area must pass both to be flattened.
//!
//! WHY AREAS MUST BE CLOSED AND HOLE-FILLED. A halftone only exists in mid-tones: a solid highlight
//! or a solid shadow carries no dots at all, so a photograph's own flat passages correctly measure
//! "not screened" and appear as gaps. Without closing and filling, every photograph comes out shot
//! through with bilevel patches. This is measured behaviour on this issue, not a precaution
//! (FINDINGS.md 1), and it is the reason the block, not the pixel, is the unit for areas.

use crate::demod::{Coherence, Contone, COHERENT};
use crate::imageio::Cmyk;
use crate::ndimage;
use crate::screen::{self, ScreenField};

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Closing radius in BLOCKS, applied before hole filling. Bridges the dot-free gaps a halftone
/// leaves in its own highlights and shadows. 2 blocks is ~2.7 mm at 2400 dpi -- wider than any
/// specular highlight in this issue, narrower than the gap between two genuinely separate pictures.
pub const CLOSE_BLOCKS: usize = 2;

/// An area smaller than this is not a region worth routing anywhere. 12 blocks is ~22 mm^2.
///
/// DELIBERATELY SMALL, and it must stay that way. The old renderer used a size filter of
/// 0.012 * page area (~1849 cells) to suppress detector bloom, and it discarded every product photo
/// under about 1.9 cm -- p104's entire page of small ads went to bilevel because of it. Bloom is the
/// wrong problem to solve with a size gate; this detector does not bloom (it attributes to the
/// window centre and rejects followers), so the gate can be small enough to keep real small photos.
///
/// LOWERED 12 -> 4 after review. Since a block outside every area no longer suppresses the stencil,
/// a dropped component is not merely lost to the contone -- its halftone DOTS are handed to the
/// bilevel layer, which is the discard-small regression of FINDINGS.md 4 all over again (p104's
/// page of small ads, p081's screened logo). 4 blocks is ~7 mm^2.
pub const MIN_AREA_BLOCKS: usize = 4;

/// Dot-area spread, in ink levels, below which an area is UNIFORM and becomes a flat fill rather
/// than a raster. Measured over non-stencil pixels only -- type on a tint is drawn by its own layer
/// and says nothing about whether the tint underneath is flat.
///
/// THIS IS A HALF-INTERQUARTILE RANGE, (p75 - p25) / 2, NOT A STANDARD DEVIATION. A tint bar is ~30
/// contone pixels tall, so its two transition rows are ~7% of its area -- and a standard deviation
/// weights that minority by the square of its distance, which put a perfectly flat bar at std 21
/// against a threshold of 9. Percentiles ignore a small edge minority while still spanning a
/// photograph's whole tonal range, which is the distinction being measured. Quartiles rather than
/// deciles because even after masking, a thin bar's transition rows survive as a minority: deciles
/// put p007's flat bars at 9-15 against this threshold of 9, quartiles put them at 3.0-3.5. The
/// value was calibrated against the quartile form; note that half-IQR is ~0.53x half-interdecile
/// for Gaussian-ish data, so this gate is looser than the same number would be on deciles.
///
/// A per-block variance was considered instead and rejected: a smooth gradient (a sky, a soft
/// backdrop) is flat WITHIN any one block and would be flattened into a single colour. The spread
/// must be measured across the whole area.
///
/// PROVISIONAL: the one constant in this file not yet derived from the issue. It wants the same
/// treatment the screen-field thresholds got -- the distribution over all 176 pages, valley located
/// rather than assumed.
pub const UNIFORM_STD: f32 = 9.0;

/// The same spread, measured ACROSS an area rather than within a block: half the interdecile range
/// of the per-block medians. A tint is the same colour from end to end; a photograph that is locally
/// smooth still travels. Slightly looser than the within-block figure because a legitimate tint can
/// carry a little press variation across a wide bar.
pub const UNIFORM_ACROSS: f32 = 12.0;

/// An area counts as carrying colour when a chromatic ink's mean dot area reaches this, in levels.
/// Below it the area is neutral and renders as class 2 even if C/M/Y technically fired -- which they
/// do on any neutral image, because before GCR a grey halftone puts near-equal ink in all four
/// channels (FINDINGS.md 1).
pub const COLOUR_INK: f32 = 12.0;

/// Ink level (0-255) at or above which a pixel is considered to carry ink at all.
pub const INK_PRESENT: f32 = 24.0;

/// ...and it must be at least this fraction of the STRONGEST ink at that pixel to draw a stencil.
///
/// WHICH INK OWNS THE MARK. GCR moves the neutral component to K, but it only removes min(C,M,Y):
/// a black mark separated as C 30 / M 40 / Y 10 / K 200 still leaves C 20 / M 30 behind. That
/// residue is scan colour-fringing and plate misregistration around black type, not cyan ink, and
/// without this test every black letter also draws a cyan and a magenta stencil. Measured on p092, a
/// black-and-white page: the C stencil claimed 19.4% and the M stencil 22.2% of the sheet, against
/// actual C coverage of 5.4% and M of 10.7% -- and the resulting mask then excluded so much of the
/// page that no area could be measured at all.
///
/// 0.5 keeps a two-ink colour (C 150 + M 140, each above half the max) and rejects a residue beside
/// a dominant K. Black type: K owns it. Cyan type: C owns it. A tint under type: neither, because
/// coherence has already claimed it.
pub const STENCIL_DOMINANCE: f32 = 0.5;

/// How far a pixel may sit from a flat area's measured percentage and still count as the tint
/// itself rather than something printed on it. Matches render.rs's SNAP_TOL, deliberately: the
/// background paints the tint exactly where the stencil declines to draw.
pub const FLAT_TOL: f32 = 2.0 * UNIFORM_STD;

/// UNBOUNDED. An enclosed unscreened region inside a picture IS part of that picture, whatever its
/// size -- a halftone has no dots in a solid highlight or a solid shadow, so those passages simply
/// cannot fire (measured inside p073's photograph: blocks at ink 0-40 fire 15% with a median
/// modulation of 2 levels, blocks at ink 160-255 fire 28% at 16 levels, against 74-79% for the
/// mid-tones). Enclosure is the whole test; there is nothing a size adds.
///
/// This was briefly capped at 64 blocks, on the theory that an unbounded fill was swallowing the
/// enclosed text column on p007. Measurement said otherwise -- the cap changed that symptom not at
/// all, and the cause was the orphan-ink path in render.rs. Meanwhile the cap was silently blocking
/// every large highlight, which is defect D: a photograph's light passages fell out of their own
/// area, got no contone, and landed as white blocks. Kept as a named constant only to record that
/// the bound was tried and was wrong.
pub const MAX_HOLE_BLOCKS: usize = usize::MAX;

/// ABSORPTION: MEAN ink level a block must reach to be absorbed into an adjacent screened area.
///
/// The mean, not "fraction of pixels above a level". Both describe a dark block, but only the mean
/// distinguishes the two kinds of dark: a photograph's solid shadow inks the WHOLE block and means
/// ~250, while a block of body type is 30% covered at full strength with paper between the letters
/// and means ~76. A fraction-above-threshold test scores both at ~0.3-1.0 and cannot tell them
/// apart -- and when it absorbed a text block into a neighbouring area, the stencil was suppressed
/// there and those words were drawn softly from the 160 dpi background. Visible directly: "Das
/// erste" grey and blurred in the middle of a crisp paragraph.
///
/// Measured on the strongest ink, not the sum: after GCR a solid black is K 255 with almost nothing
/// else beside it, so it sums to only ~265 and a sum-based threshold of 380 never fired at all.
pub const ABSORB_MEAN: f32 = 150.0;

/// A contone pixel counts as part of the screen when at least this fraction of its footprint is
/// coherent. Half: the pixel is more screen than not. Bare paper has no coherence and drops out
/// here without needing a separate ink test.
pub const COHERENT_FRAC: f32 = 0.5;

/// A block needs this FRACTION of its own contone pixels to survive the paper and stencil masks
/// before its dot-area spread means anything, with an absolute floor as well.
///
/// It must be a fraction, not a count: the contone rate is derived per page from the measured
/// ruling, so a block's cell is 8.5 x 8.5 contone pixels on a 160 lpi page and only 6.4 x 6.4 on a
/// 102 lpi one. A fixed count of 32 was 44% of the cell on p007 and 78% of it on p092 -- so on p092
/// almost no block could be measured at all, every area fell through to "unmeasurable", and the page
/// reported five grey photographs with no statistics behind them.
///
/// Where a block cannot be measured it is NOT called uniform. A flat fill replaces a region with a
/// single colour and is the most destructive thing the renderer does, so "I could not measure this"
/// must fall to the contone side. The old renderer's equivalent default pointed at the destructive
/// layer, which is how photographs ended up as solid bilevel blobs.
/// How far a measured verdict may be inherited by unmeasurable blocks, in rounds of one block. 3 is
/// ~4 mm: enough to cross a line of display type, short of crossing a whole picture.
pub const UNIFORM_FILL_ROUNDS: usize = 3;

/// Majority-filter passes over the uniform/varying field before it is segmented. See step 2c.
pub const UNIFORM_CLEAN_ROUNDS: usize = 2;

pub const MIN_MEASURE_FRAC: f64 = 0.25;
pub const MIN_MEASURE_FLOOR: usize = 8;

// ================================================================================================

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Class {
    /// 1: screened, dot area varies, chromatic ink present
    ColourPhoto,
    /// 2: screened, dot area varies, neutral
    GreyPhoto,
    /// 3: screened, dot area uniform -- a tint or a box background
    Flat,
}

impl Class {
    pub fn name(self) -> &'static str {
        match self {
            Class::ColourPhoto => "colour-photo",
            Class::GreyPhoto => "grey-photo",
            Class::Flat => "flat",
        }
    }
}

pub struct Area {
    pub id: usize,
    pub class: Class,
    /// bbox in block coordinates: y0, x0, y1, x1 inclusive
    pub bbox: (usize, usize, usize, usize),
    pub blocks: usize,
    /// mean dot area per ink over the area, non-stencil pixels only (0-255)
    pub mean: [f32; 4],
    /// and its dot-area spread, (p75-p25)/2 -- the uniform/varying test. See UNIFORM_STD.
    pub std: [f32; 4],
    /// median ruling of whatever fired inside
    pub lpi: f32,
}

pub struct Routing {
    pub ny: usize,
    pub nx: usize,
    /// per block: did any ink report a screen here. The renderer needs it to tell "ink in a
    /// screened block that no stencil claimed" (which the background must draw) from "ink on bare
    /// paper" (which is the stencil's business alone).
    pub fired: Vec<bool>,
    /// how many blocks fired, and how many of those could actually be measured on the contone.
    /// Reported because "no area could be measured" is otherwise indistinguishable from "no screen
    /// here", and the two want opposite fixes.
    pub n_fired: usize,
    pub n_measured: usize,
    /// area id + 1 per block, 0 = not screened
    pub label: Vec<u32>,
    pub areas: Vec<Area>,
    /// per ink at STENCIL resolution: ink present and NOT explained by a screen
    pub stencil: Vec<Vec<bool>>,
    pub sw: usize,
    pub sh: usize,
}

/// Block covering a source pixel. The field's blocks are anchored every STEP px with the verdict at
/// the window CENTRE, so the inverse of `centre_of` is offset by half a window.
fn block_of_source(f: &ScreenField, sy: usize, sx: usize) -> usize {
    // Block b is centred at b*STEP + WIN/2 and owns [centre - STEP/2, centre + STEP/2). Inverting
    // that needs the half-step, and without it the whole label map is translated STEP/2 = 64 px
    // (0.68 mm) down and to the right -- so every area boundary in the PDF sat two thirds of a
    // millimetre from where it was measured, and from where routedbg.rs draws it. The debug overlay
    // was right and the renderer was wrong.
    let by = (sy + screen::STEP / 2).saturating_sub(screen::WIN / 2) / screen::STEP;
    let bx = (sx + screen::STEP / 2).saturating_sub(screen::WIN / 2) / screen::STEP;
    by.min(f.ny - 1) * f.nx + bx.min(f.nx - 1)
}

/// THE STENCIL. Per pixel, per ink: ink is present here AND it is not part of a periodic grid.
///
/// A mask, never a subtraction. Reconstructing the screen and subtracting it would leave the
/// harmonic residue of a square-ish dot, which looks exactly like structure (FINDINGS.md 2).
pub fn stencils(
    disp: &Cmyk,
    coh: &Coherence,
    f: &ScreenField,
    label: &[u32],
    areas: &[Area],
    fired_mask: &[bool],
    tone: &Contone,
) -> (usize, usize, Vec<Vec<bool>>) {
    let ty_per = (disp.h / tone.h).max(1);
    let tx_per = (disp.w / tone.w).max(1);
    let (w, h) = (coh.w, coh.h);
    let div = (disp.w / w).max(1);
    // Ink per stencil pixel per channel: the MAXIMUM over the source cell, not the mean. A hairline
    // or a serif covers a fraction of a 4x4 cell, and averaging it with its own white surroundings
    // is how thin strokes get lost.
    let peak: Vec<Vec<u8>> = (0..4)
        .map(|ci| {
            let src = disp.channel(ci);
            let mut m = vec![0u8; w * h];
            for y in 0..h {
                for x in 0..w {
                    let mut ink = 0u8;
                    for sy in 0..div {
                        let base = (y * div + sy) * disp.w + x * div;
                        for sx in 0..div {
                            ink = ink.max(src[base + sx]);
                        }
                    }
                    m[y * w + x] = ink;
                }
            }
            m
        })
        .collect();
    // A LOCATION IS SCREEN IF ANY INK IS COHERENT THERE **AND IT LIES IN A SCREENED AREA**.
    //
    // Coherence is a per-pixel measurement and it misfires: a patch of body text that happens to
    // demodulate well suppresses the stencil under it, and those words are then drawn by the 160 dpi
    // background instead of the 600 dpi mask. Rendered, that is exactly what it looks like -- most
    // of a paragraph crisp and a few words ghosted and eroded ("ergewoehnlich", "Das erste", "nser
    // zweiter" on p007). The area map is the regional context that a pixel cannot have on its own:
    // text on bare paper is in no area, so its stencil can never be suppressed, while text ON a tint
    // still works because under a letter no ink is coherent at all.
    //
    // Per-ink was wrong and the picture showed it: inside a colour photograph M can be coherent
    // while C is present and incoherent, so C drew a stencil across the whole picture and p007's
    // two photographs came out almost entirely claimed by the bilevel layer. Physically there is one
    // sheet of paper: where a halftone exists, the ink at that spot IS the halftone. Type on a tint
    // still works -- the letter covers the dots with solid ink, so no ink is coherent under it.
    let sdiv = (disp.w / w).max(1);
    let screened: Vec<bool> = (0..w * h)
        .map(|i| {
            let (sy, sx) = ((i / w) * sdiv, (i % w) * sdiv);
            let bi = block_of_source(f, sy, sx);
            let l = label[bi];
            // INSIDE A PICTURE, EVERYTHING IS CONTONE. A photograph is drawn entirely by the
            // background -- its dots, its solid shadows and its highlights alike -- so nothing in it
            // belongs to the stencil. Without this, every screened passage whose coherence dipped
            // handed its halftone DOTS to the bilevel layer: 288 KB of dots per page on p007, and
            // the pathology FINDINGS.md 4 records for p173.
            if l != 0 {
                let cls = areas[(l - 1) as usize].class;
                if cls != Class::Flat {
                    return true;
                }
            }
            // ON A FLAT TINT, INK AT THE TINT'S OWN LEVEL *IS* THE TINT. Same test the background
            // uses to snap it: within SNAP_TOL of the measured percentage means this is the tint,
            // and only a departure from it can be something printed on top. Without this the tint's
            // own dots leak into the stencil wherever coherence dips, and the flat fill arrives
            // under a faint dotted texture -- visible on p007's contents bars.
            if l != 0 {
                let a = &areas[(l - 1) as usize];
                let (ty, tx) = ((i / w) * sdiv / ty_per, (i % w) * sdiv / tx_per);
                if ty < tone.h && tx < tone.w {
                    let ti = ty * tone.w + tx;
                    if (0..4).all(|ci| {
                        (tone.ink[ci][ti] as f32 - a.mean[ci]).abs() <= FLAT_TOL
                    }) {
                        return true;
                    }
                }
            }
            // Elsewhere the type printed on top must survive, so suppression needs positive evidence
            // that THIS spot is halftone: coherent ink in a block that actually fired. Requiring the
            // block to have fired is what stops a stray coherent patch over body text from erasing
            // the glyphs under it.
            (fired_mask[bi] || l != 0) && (0..4).any(|ci| coh.ink[ci][i] >= COHERENT)
        })
        .collect();
    let out: Vec<Vec<bool>> = (0..4)
        .map(|ci| {
            (0..w * h)
                .map(|i| {
                    let v = peak[ci][i] as f32;
                    if v < INK_PRESENT || screened[i] {
                        return false;
                    }
                    // WHERE THERE IS BLACK INK, THE COLOUR IS FRINGE. A black glyph's edge carries a
                    // chromatic residue -- plate misregistration on the press plus the scanner's own
                    // chromatic aberration -- and GCR does not remove it, because GCR subtracts
                    // min(C,M,Y) and an edge fringe is usually one ink, not all three.
                    //
                    // NO LEVEL THRESHOLD CAN SEPARATE IT. Measured on p007's body text: at K-ramp
                    // pixels the fringe reaches M p90 169, p99 224, while the genuinely red heading
                    // has M p10 176. The populations overlap almost entirely. What separates them is
                    // not how strong the colour is but whether black ink is there at all -- the
                    // fringe exists only at a K edge, and a red glyph carries no K.
                    //
                    // This restores the deleted renderer's `inkpix = crisp && !black && ...` guard.
                    // Losing it put coloured outlines around every black letter, which is a
                    // regression and was reported as one.
                    if ci != 3 && peak[3][i] as f32 >= INK_PRESENT {
                        return false;
                    }
                    let strongest = (0..4).map(|cj| peak[cj][i]).max().unwrap() as f32;
                    v >= STENCIL_DOMINANCE * strongest
                })
                .collect()
        })
        .collect();
    (w, h, out)
}

/// Group blocks into areas, measure each, and assign its class.
pub fn route(f: &ScreenField, tone: &Contone, coh: &Coherence, disp: &Cmyk) -> Routing {
    let (ny, nx) = (f.ny, f.nx);

    // ---- 1. which blocks carry a screen in any ink --------------------------------------------
    let fired_mask: Vec<bool> = (0..ny * nx)
        .map(|i| (0..4).any(|ci| screen::fired(f, ci, i)))
        .collect();

    // ---- 2. per-BLOCK dot-area spread, over the SCREEN's own pixels --------------------------
    //
    // A block's dot area is measured where the ink IS the screen -- that is, where coherence says
    // so. Not "everywhere except the stencil": that was a second, different criterion for the same
    // question, and the two disagreed. Inside a photograph its own fine detail reads as a mark, so
    // excluding by stencil starved the sample (p092: 14 blocks measurable of 8381); falling back to
    // the full sample then let paper and lettering in, and flat regions swallowed photographs. One
    // criterion, applied the same way in both directions: coherent pixels are the screen, and the
    // screen is what has a dot area.
    let (sw, sh) = (coh.w, coh.h);
    let sdiv = (disp.w / sw).max(1);
    let ty_per = (disp.h / tone.h).max(1);
    let tx_per = (disp.w / tone.w).max(1);
    let mut block_vals: Vec<[Vec<u8>; 4]> = (0..ny * nx)
        .map(|_| [Vec::new(), Vec::new(), Vec::new(), Vec::new()])
        .collect();
    for ty in 0..tone.h {
        for tx in 0..tone.w {
            let (sy, sx) = (ty * ty_per, tx * tx_per);
            let bi = block_of_source(f, sy, sx);
            if !fired_mask[bi] {
                continue;
            }
            // fraction of this contone pixel's footprint that is coherent, in the best ink
            let (cy0, cx0) = (sy / sdiv, sx / sdiv);
            let cy1 = ((sy + ty_per) / sdiv).min(sh).max(cy0 + 1);
            let cx1 = ((sx + tx_per) / sdiv).min(sw).max(cx0 + 1);
            let mut best = 0.0f32;
            for ci in 0..4 {
                if !screen::fired(f, ci, bi) {
                    continue;
                }
                let (mut hit, mut tot) = (0u32, 0u32);
                for cy in cy0..cy1.min(sh) {
                    for cx in cx0..cx1.min(sw) {
                        tot += 1;
                        if coh.ink[ci][cy * sw + cx] >= COHERENT {
                            hit += 1;
                        }
                    }
                }
                if tot > 0 {
                    best = best.max(hit as f32 / tot as f32);
                }
            }
            if best < COHERENT_FRAC {
                continue;
            }
            for ci in 0..4 {
                block_vals[bi][ci].push(tone.ink[ci][ty * tone.w + tx]);
            }
        }
    }

    // a block's cell in contone pixels, both axes
    let cell_px = ((screen::STEP / ty_per).max(1) * (screen::STEP / tx_per).max(1)) as f64;
    let min_measure = ((cell_px * MIN_MEASURE_FRAC) as usize).max(MIN_MEASURE_FLOOR);
    let mut uniform = vec![false; ny * nx];
    // measured[bi]: enough of this block is screen for its statistics to mean anything.
    let mut measured = vec![false; ny * nx];
    let mut bmean = vec![[0.0f32; 4]; ny * nx];
    let mut bspread = vec![[0.0f32; 4]; ny * nx];
    for bi in 0..ny * nx {
        let n = block_vals[bi][0].len();
        if n < min_measure {
            continue;
        }
        measured[bi] = true;
        let mut flat = true;
        for ci in 0..4 {
            let v = &mut block_vals[bi][ci];
            v.sort_unstable();
            bmean[bi][ci] = v[n / 2] as f32;
            let p25 = v[n / 4] as f32;
            let p75 = v[(n * 3 / 4).min(n - 1)] as f32;
            bspread[bi][ci] = (p75 - p25) / 2.0;
        }
        let _ = flat;
    }

    // THE UNIFORM TEST IS A LOCAL GRADIENT ON A ROBUST STATISTIC, not a within-block spread.
    //
    // Within-block spread is contaminated by exactly the thing that must not matter: a bold heading
    // on a tint bar covers a different fraction of each block, its edges leak into the sample, and
    // the verdict then flips from block to block. p007's "SOFTWARE-HILFEN" bar came out as a
    // checkerboard of flat and photo squares and the heading was stencilled in some and drawn softly
    // in others -- SOFTW crisp, ARE-HILFEN eroded.
    //
    // The median dot area of a block is robust: whatever the glyphs do, the tint between them still
    // reads ~50% cyan. So the question becomes "does this block's dot area match its neighbours'" --
    // which is flat for a tint bar however the type falls across it, and varying for a photograph,
    // whose whole nature is that neighbouring patches differ. It is also the same question the
    // across-area test asks, now asked locally, so the two scales agree by construction.
    for by in 0..ny {
        for bx in 0..nx {
            let i = by * nx + bx;
            if !measured[i] {
                continue;
            }
            let mut worst = 0.0f32;
            let mut n = 0;
            for dy in -1i64..=1 {
                for dx in -1i64..=1 {
                    let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                    if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                        continue;
                    }
                    let j = y2 as usize * nx + x2 as usize;
                    if !measured[j] || j == i {
                        continue;
                    }
                    n += 1;
                    for ci in 0..4 {
                        worst = worst.max((bmean[i][ci] - bmean[j][ci]).abs());
                    }
                }
            }
            // An isolated measured block has nothing to compare against; leave it non-uniform, the
            // safe side.
            uniform[i] = n > 0 && worst <= UNIFORM_STD;
        }
    }

    // ---- 2b. an unmeasurable block INHERITS its neighbours' verdict ---------------------------
    //
    // A block whose contone is mostly covered by a big glyph has almost no screen pixels left to
    // measure, so it cannot be called uniform -- and "not uniform" meant "photograph", which
    // suppressed the stencil there and drew the heading softly from the background instead. Measured
    // on p007: "SOFTWARE-HILFEN" on its cyan bar came out with SOFTW crisp and ARE-HILFEN eroded,
    // because the blocks under the second half were unmeasurable and pulled that stretch of the bar
    // into a photo area.
    //
    // Uniformity is a property of a REGION, exactly as the screen vector is (see
    // demod::filled_geometry). A block that could not measure itself still sits on whatever its
    // neighbours sit on, so it inherits their verdict. Inheriting requires a measured majority
    // nearby; with none, nothing changes and the block stays non-uniform, which is still the safe
    // direction.
    for _ in 0..UNIFORM_FILL_ROUNDS {
        let snap_u = uniform.clone();
        let snap_m = measured.clone();
        let mut grew = false;
        for by in 0..ny {
            for bx in 0..nx {
                let i = by * nx + bx;
                if snap_m[i] || !fired_mask[i] {
                    continue;
                }
                let (mut yes, mut no) = (0, 0);
                for dy in -1i64..=1 {
                    for dx in -1i64..=1 {
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            continue;
                        }
                        let j = y2 as usize * nx + x2 as usize;
                        if snap_m[j] {
                            if snap_u[j] {
                                yes += 1;
                            } else {
                                no += 1;
                            }
                        }
                    }
                }
                if yes + no == 0 {
                    continue;
                }
                uniform[i] = yes > no;
                measured[i] = true;
                // the inherited region's colour, so a flat fill has a value to use
                let mut cnt = 0.0f32;
                let mut acc = [0.0f32; 4];
                for dy in -1i64..=1 {
                    for dx in -1i64..=1 {
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            continue;
                        }
                        let j = y2 as usize * nx + x2 as usize;
                        if snap_m[j] {
                            for ci in 0..4 {
                                acc[ci] += bmean[j][ci];
                            }
                            cnt += 1.0;
                        }
                    }
                }
                for ci in 0..4 {
                    bmean[i][ci] = acc[ci] / cnt;
                }
                grew = true;
            }
        }
        if !grew {
            break;
        }
    }

    // ---- 2c. clean the verdict field before segmenting on it ---------------------------------
    //
    // One block's uniform/varying verdict is noisy, because how much of a block a heading covers is
    // an accident of where the block grid falls. Grouping directly on that field shatters one
    // physical region into a CHECKERBOARD of one-block areas -- p007's "SOFTWARE-HILFEN" bar came
    // out as alternating flat and photo squares, and since the stencil is suppressed inside a photo,
    // the heading was stencilled in some squares and drawn softly in others: SOFTW crisp,
    // ARE-HILFEN eroded.
    //
    // A majority filter is the right tool and not a fudge: it cannot merge a photograph into a tint
    // (a photograph is many varying blocks in a row and keeps its majority) but it does remove the
    // isolated flips that the block grid manufactures. Two passes, because a single pass leaves
    // 2x2 clumps.
    for _ in 0..UNIFORM_CLEAN_ROUNDS {
        let snap = uniform.clone();
        for by in 0..ny {
            for bx in 0..nx {
                let i = by * nx + bx;
                if !fired_mask[i] {
                    continue;
                }
                let (mut yes, mut no) = (0, 0);
                for dy in -1i64..=1 {
                    for dx in -1i64..=1 {
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            continue;
                        }
                        let j = y2 as usize * nx + x2 as usize;
                        if !fired_mask[j] {
                            continue;
                        }
                        if snap[j] {
                            yes += 1;
                        } else {
                            no += 1;
                        }
                    }
                }
                if yes + no >= 3 {
                    uniform[i] = yes > no;
                }
            }
        }
    }

    // ---- 3. group blocks of like verdict, separately ------------------------------------------
    // Closing bridges the dot-free gaps a halftone leaves in its own highlights and shadows;
    // fill_holes recovers a photograph's solid highlight enclosed by screen.
    let mut areas: Vec<Area> = Vec::new();
    let mut label = vec![0u32; ny * nx];
    for pass in 0..2 {
        let want_uniform = pass == 0;
        let mut m: Vec<bool> = (0..ny * nx)
            .map(|i| fired_mask[i] && uniform[i] == want_uniform && label[i] == 0)
            .collect();
        let seed = m.clone();
        if CLOSE_BLOCKS > 0 {
            m = ndimage::binary_dilation(&m, nx, ny, CLOSE_BLOCKS);
            m = ndimage::binary_erosion(&m, nx, ny, CLOSE_BLOCKS);
        }
        // A CLOSING IS EXTENSIVE: it can only ever ADD. `binary_erosion` treats outside-the-array as
        // empty, so blocks within CLOSE_BLOCKS of the block-grid edge erode away and never come
        // back -- 4 mm of every full-bleed photo and tint, stripped of its area and then, because
        // label==0 turns off stencil suppression, redrawn as raw halftone dots in the bilevel layer.
        // That is the p173 pathology in FINDINGS.md 4. Restoring the seed makes the operation a
        // closing again.
        for i in 0..ny * nx {
            if seed[i] {
                m[i] = true;
            }
        }
        // BOUNDED HOLE FILL. `binary_fill_holes` fills ANY enclosed region, and on a magazine page
        // a column of body text is routinely enclosed by the graphics around it -- a headline above,
        // a photograph beside, a tint below. Filling it labels the text as part of a picture, and
        // then the background paints a soft 160 dpi copy of every glyph underneath the crisp stencil
        // copy. Measured on p007: under "Das erste" the background reaches level 141 where under the
        // neighbouring "Spiel das" it is a clean 255.
        //
        // What the fill is FOR is a photograph's own specular highlight, which carries no dots and
        // is small. So bound it: fill an enclosed hole only if it is smaller than MAX_HOLE_BLOCKS.
        {
            let inv: Vec<bool> = m.iter().map(|&b| !b).collect();
            let (hl, hn) = ndimage::label(&inv, nx, ny);
            if hn > 0 {
                let hs = ndimage::component_sizes(&hl, hn);
                // a hole touching the border is outside, not enclosed
                let mut border = vec![false; hn + 1];
                for x in 0..nx {
                    border[hl[x] as usize] = true;
                    border[hl[(ny - 1) * nx + x] as usize] = true;
                }
                for y in 0..ny {
                    border[hl[y * nx] as usize] = true;
                    border[hl[y * nx + nx - 1] as usize] = true;
                }
                for i in 0..ny * nx {
                    let c = hl[i] as usize;
                    if c != 0 && !border[c] && hs[c - 1] <= MAX_HOLE_BLOCKS as u64 {
                        m[i] = true;
                    }
                }
            }
        }
        // never steal a block already claimed by the previous pass
        for i in 0..ny * nx {
            if label[i] != 0 {
                m[i] = false;
            }
        }
        let (lb, n) = ndimage::label(&m, nx, ny);
        let sz = ndimage::component_sizes(&lb, n);
        let bx = ndimage::find_objects(&lb, n, nx, ny);
        for c in 1..=n {
            if sz[c - 1] < MIN_AREA_BLOCKS as u64 {
                continue;
            }
            let id = areas.len();
            let (y0, y1, x0, x1) = bx[c - 1].unwrap();
            // area statistics: the MEDIAN over its own blocks, which is what a flat fill will use
            let mut mean = [0.0f32; 4];
            let mut spread = [0.0f32; 4];
            let mut lpis: Vec<f32> = Vec::new();
            for ci in 0..4 {
                let mut mv: Vec<f32> = Vec::new();
                let mut sv: Vec<f32> = Vec::new();
                for i in 0..ny * nx {
                    if lb[i] == c as u32 && measured[i] {
                        mv.push(bmean[i][ci]);
                        sv.push(bspread[i][ci]);
                    }
                }
                if !mv.is_empty() {
                    mv.sort_by(|a, b| a.partial_cmp(b).unwrap());
                    sv.sort_by(|a, b| a.partial_cmp(b).unwrap());
                    mean[ci] = mv[mv.len() / 2];
                    spread[ci] = sv[sv.len() / 2];
                }
            }
            for i in 0..ny * nx {
                if lb[i] == c as u32 {
                    label[i] = id as u32 + 1;
                    for ci in 0..4 {
                        if screen::fired(f, ci, i) {
                            lpis.push(f.ink[ci].lpi[i]);
                        }
                    }
                }
            }
            lpis.sort_by(|a, b| a.partial_cmp(b).unwrap());
            // SECOND SCALE: a candidate flat area must also be flat ACROSS itself. Spread of the
            // per-block medians, which is exactly the gradient a locally-flat photograph has and a
            // tint does not.
            // Default is NOT flat: an area with too few measured blocks to compute a spread has no
            // evidence of uniformity, and a flat fill is the most destructive thing the renderer
            // does. Unmeasurable falls to the contone side, as everywhere else in this file.
            let mut across = f32::MAX;
            let mut any_across = false;
            for ci in 0..4 {
                let mut mv: Vec<f32> = (0..ny * nx)
                    .filter(|&i| lb[i] == c as u32 && measured[i])
                    .map(|i| bmean[i][ci])
                    .collect();
                if mv.len() < 4 {
                    continue;
                }
                mv.sort_by(|a, b| a.partial_cmp(b).unwrap());
                let p10 = mv[mv.len() / 10];
                let p90 = mv[(mv.len() * 9 / 10).min(mv.len() - 1)];
                let v = (p90 - p10) / 2.0;
                across = if any_across { across.max(v) } else { v };
                any_across = true;
            }
            let colour = (0..3).any(|ci| mean[ci] >= COLOUR_INK);
            areas.push(Area {
                id,
                class: if want_uniform && across <= UNIFORM_ACROSS {
                    Class::Flat
                } else if colour {
                    Class::ColourPhoto
                } else {
                    Class::GreyPhoto
                },
                bbox: (y0, x0, y1, x1),
                blocks: sz[c - 1] as usize,
                mean,
                std: spread,
                lpi: if lpis.is_empty() { 0.0 } else { lpis[lpis.len() / 2] },
            });
        }
    }

    // ---- 4b. absorb the solid parts of a picture into their area -----------------------------
    //
    // A halftone exists only in mid-tones, so a photograph's own solid shadow carries no dots, never
    // fires, and -- being connected to the page edge rather than enclosed -- is not recovered by
    // `fill_holes` either. It joined no area, which switched OFF stencil suppression there, and the
    // photograph's dark passages were handed to the bilevel layer. In the rendered PDF that is a
    // ragged staircase of bare paper straight through p007's Spindizzy photograph.
    // SEGMENTATION_PLAN.md predicted exactly this ("absorb solid-K regions into an adjacent screened
    // area"); it is the one part of that plan that turned out to be necessary.
    //
    // GEODESIC, not a fixed number of dilations. The shadow is as big as it is, and growing by a
    // bounded radius reaches part of it and leaves the rest -- which is what an earlier six-round
    // version did. Propagating from the areas THROUGH inked blocks reaches all of a connected
    // shadow and stops dead at paper, whatever the distance.
    //
    // COVERAGE is what separates a shadow from type: a solid passage inks essentially the whole
    // block, a line of text inks 10-20% of it. Not darkness -- a block of bold type is dark too.
    {
        let mut inked = vec![false; ny * nx];
        {
            let mut sum = vec![0.0f32; ny * nx];
            let mut cnt = vec![0u32; ny * nx];
            for ty in 0..tone.h {
                for tx in 0..tone.w {
                    let bi = block_of_source(f, ty * ty_per, tx * tx_per);
                    let strongest = (0..4)
                        .map(|ci| tone.ink[ci][ty * tone.w + tx])
                        .max()
                        .unwrap_or(0);
                    sum[bi] += strongest as f32;
                    cnt[bi] += 1;
                }
            }
            for bi in 0..ny * nx {
                inked[bi] = cnt[bi] > 0 && sum[bi] / cnt[bi] as f32 >= ABSORB_MEAN;
            }
        }
        let seed: Vec<bool> = label.iter().map(|&l| l != 0).collect();
        let mask: Vec<bool> = (0..ny * nx).map(|i| inked[i] || seed[i]).collect();
        let reach = ndimage::binary_propagation(&seed, &mask, nx, ny);
        // spread labels into the reached blocks, to convergence
        loop {
            let mut grew = false;
            let snap = label.clone();
            for by in 0..ny {
                for bx in 0..nx {
                    let i = by * nx + bx;
                    if snap[i] != 0 || !reach[i] {
                        continue;
                    }
                    for (dy, dx) in [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)] {
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            continue;
                        }
                        let j = y2 as usize * nx + x2 as usize;
                        if snap[j] != 0 {
                            label[i] = snap[j];
                            grew = true;
                            break;
                        }
                    }
                }
            }
            if !grew {
                break;
            }
        }
    }

    // ---- 4c. extend every area one block outward ---------------------------------------------
    //
    // A block straddling a picture's edge contains part picture and part surround, so its screen
    // signal is diluted and it often does not fire -- and enclosure cannot recover it, because a rim
    // block is by definition not enclosed. Left out, the picture ends one block short of itself and
    // the background paints nothing there: the ragged white staircase along p073's printer.
    //
    // The rim is recorded SEPARATELY from the interior. Inside a picture everything is contone, which
    // is what keeps halftone dots out of the bilevel layer -- but that rule must not reach out over
    // whatever the picture happens to abut. A caption 1.35 mm from a photograph would lose its
    // stencil entirely. So a rim block buys contone coverage and spends no marks: the background
    // paints it, and the stencil goes on deciding per pixel exactly as it does on open paper.
    let interior = label.clone();
    {
        let snap = label.clone();
        for by in 0..ny {
            for bx in 0..nx {
                let i = by * nx + bx;
                if snap[i] != 0 {
                    continue;
                }
                for (dy, dx) in [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)] {
                    let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                    if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                        continue;
                    }
                    let j = y2 as usize * nx + x2 as usize;
                    if snap[j] != 0 {
                        label[i] = snap[j];
                        break;
                    }
                }
            }
        }
    }

    // ---- 5. stencils, now that the areas are known -------------------------------------------
    let (sw2, sh2, stencil) = stencils(disp, coh, f, &interior, &areas, &fired_mask, tone);
    debug_assert_eq!((sw, sh), (sw2, sh2));

    let n_fired = fired_mask.iter().filter(|&&b| b).count();
    let n_measured = measured.iter().filter(|&&b| b).count();
    Routing { ny, nx, n_fired, n_measured, fired: fired_mask, label, areas, stencil, sw, sh }
}

/// One line per page for the terminal, printed as the page finishes.
pub fn summarise(page: &str, r: &Routing) -> String {
    let (mut c1, mut c2, mut c3) = (0, 0, 0);
    for a in &r.areas {
        match a.class {
            Class::ColourPhoto => c1 += 1,
            Class::GreyPhoto => c2 += 1,
            Class::Flat => c3 += 1,
        }
    }
    let sp: Vec<String> = (0..4)
        .filter_map(|ci| {
            let n = r.stencil[ci].iter().filter(|&&b| b).count();
            if n == 0 {
                return None;
            }
            Some(format!(
                "{} {:.1}%",
                ["C", "M", "Y", "K"][ci],
                100.0 * n as f64 / (r.sw * r.sh) as f64
            ))
        })
        .collect();
    format!(
        "p{} blocks {} fired / {} measured | areas: {} colour-photo, {} grey-photo, {} flat | stencil {}",
        page,
        r.n_fired,
        r.n_measured,
        c1,
        c2,
        c3,
        if sp.is_empty() { "none".into() } else { sp.join(" ") }
    )
}
