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

/// Closing radius in BLOCKS. ZERO -- the grouping never bridges a gap, and should not.
///
/// An ENCLOSED gap is part of the object: a photograph's specular highlight carries no dots, cannot
/// fire, and is surrounded by the picture. That is the per-object fill, and it is principled.
///
/// A gap that is NOT enclosed is a real separation -- the page put white between two things. Welding
/// across it can only merge what the layout kept apart, and that is what it did: at radius 2 (which
/// bridges 4 blocks = 5.4 mm) p022's data-sheet table, whose tinted rows are separated by exactly 4
/// blocks of white, arrived as one region instead of ten.
///
/// Measured over 22 pages, sweeping the radius:
///
///     radius        0      1      2
///     regions     147    112     83       <- lower means more things merged
///     p022 bands   10     10      7
///     p001 cover  99.4%  99.5%  99.9%     <- coverage barely moves
///
/// Coverage is essentially unchanged while the region count almost halves: the closing was never
/// filling gaps, the fill already does that. Verified at radius 0 that nothing fragments that should
/// not -- p001's cover keeps 33,414 of its 33,526 blocks in one region and still covers 100%.
pub const CLOSE_BLOCKS: usize = 0;

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
/// THIS IS NOT A STANDARD DEVIATION but the half-width of the densest MODE_FRAC of the block's
/// values -- see shortest_u8. A tint bar is ~30 contone pixels tall, so its two transition rows are
/// ~7% of its area, and a standard deviation weights that minority by the square of its distance,
/// which put a perfectly flat bar at std 21 against a threshold of 9. An interquartile range was the
/// next attempt and is also wrong, for the reason shortest_u8 gives: a block carrying type holds two
/// populations, and any range statistic straddles both, so it reports how much type the block has.
/// Measured on p022's spec table, a three-line row of dense type read 10.0 against this threshold of
/// 9 while its neighbours -- the identical tint, less text -- read 3.0.
///
/// A per-block variance was considered instead and rejected: a smooth gradient (a sky, a soft
/// backdrop) is flat WITHIN any one block and would be flattened into a single colour. The spread
/// must be measured across the whole area.
///
/// PROVISIONAL: the one constant in this file not yet derived from the issue. It wants the same
/// treatment the screen-field thresholds got -- the distribution over all 176 pages, valley located
/// rather than assumed.
pub const UNIFORM_STD: f32 = 9.0;

/// The same spread, measured ACROSS an area rather than within a block: the densest MODE_FRAC of the
/// per-block medians. A tint is the same colour from end to end; a photograph that is locally smooth
/// still travels. Slightly looser than the within-block figure because a legitimate tint can carry a
/// little press variation across a wide bar.
///
/// The number did not move when the estimator was fixed, which is the point -- it was never the
/// threshold that was wrong. Measured, max over inks, per region:
///
///                        tints (p022 x10, p001 x2)   photographs (p001, p002, p073 x2)
///     half-interdecile         2.5 .. 34.0                  28.0 .. 124.5
///     densest 70%              1.5 ..  7.0                  17.0 ..  61.0
///
/// The two populations overlapped under the old estimator -- a tint at 34 against a photograph at 28
/// -- so no threshold could have separated them.
pub const UNIFORM_ACROSS: f32 = 12.0;

/// An area counts as carrying colour when a chromatic ink's mean dot area reaches this, in levels.
/// Below it the area is neutral and renders as class 2 even if C/M/Y technically fired -- which they
/// do on any neutral image, because before GCR a grey halftone puts near-equal ink in all four
/// channels (FINDINGS.md 1).
pub const COLOUR_INK: f32 = 12.0;

/// SOLIDITY. Ink level at or above which a pixel counts as solid ink and may be drawn by the 1-bit
/// stencil. 128 = more ink than paper, which is where a bilevel mask's boundary belongs.
///
/// This is a solidity test, not a presence test, and the distinction is the whole point of the
/// layer: a stencil can only draw ink at FULL strength, so it must claim only what the press laid at
/// full strength. A 50% grey is ink too, but drawing it solid would be a lie -- it belongs to the
/// contone.
///
/// The old value of 24 was calibrated against the display-graded planes, where the level stretch had
/// already done the solidity test by clipping everything below 30% to zero. With the contone reading
/// LINEAR planes that stretch is gone, so the test has to be stated here explicitly rather than
/// hidden in a grade.
///
/// Well conditioned, unlike most thresholds in this project. Measured on p007's body text, the
/// linear K histogram is sharply bimodal -- 11.2M pixels in 0-15 (paper), 1.57M in 240-255 (solid
/// ink), and a flat ~15k per bin in between (glyph edges). Any value from 16 to 239 gives within
/// half a percent of the same answer; 128 is the midpoint of that valley.
///
/// Solidity alone is not sufficient and is not asked to be: a tint's halftone dots are solid too
/// (11.4% of p007's cyan bar reads >=200 in C). Coherence is what separates those -- the dots are
/// periodic, the letters are not.
pub const INK_PRESENT: f32 = 128.0;

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

/// How far absorption may travel from a screened block, in blocks. ZERO -- the step is disabled,
/// by measurement.
///
/// Absorption existed because a photograph's solid shadow carries no dots and so could never fire.
/// That was true of the old detector. It is no longer true: with `conc` and `agree` the shadow is
/// detected directly, and the step now costs far more than it buys. Measured on p073, coverage of
/// each region against the reach:
///
///     reach   photo   shadow   C64    RED BANNER (must be 0)
///       0      1.00    0.98    0.73        0.03
///       4      1.00    0.98    0.76        0.27
///       8      1.00    0.98    0.78        0.48
///
/// Five points on the C64 against forty-five points of false coverage on a solid graphic that is
/// not a picture at all -- and a graphic swallowed into a photo region loses its stencil, which is
/// how p073's banner went from M 25.5% to 1.5%.
///
/// Left in place at 0 rather than deleted: it is one constant, and if detection ever regresses on
/// solid passages this is the right repair. Raise it only with the table above re-measured, never
/// because a picture looks short.
pub const ABSORB_BLOCKS: usize = 0;

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

/// Fraction of the sample the "densest interval" estimator must cover. See shortest_u8.
/// 0.7 and not 0.5: a region may not be called uniform because half of it happens to be, so a
/// clear majority of the blocks must agree. Measured, the 70% gap between a tint and a
/// photograph is 7.0 vs 20.0 -- wide enough that the existing threshold needs no refitting.
pub const MODE_FRAC: f32 = 0.7;

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
    /// spread of the per-block medians ACROSS the region, and how many blocks that was measured
    /// over. Both are in the debug line: a class decision that cannot be read off the numbers
    /// printed beside it is not auditable.
    pub across: f32,
    pub n_meas: usize,
    /// median ruling of whatever fired inside
    pub lpi: f32,
}

pub struct Routing {
    pub ny: usize,
    pub nx: usize,
    /// the four grouping stages, per block, each recording only what IT added. The debug drawer
    /// shows them in four colours so a wrong shape can be attributed to the step that made it.
    pub st_screen: Vec<bool>,
    pub st_absorb: Vec<bool>,
    pub st_fill: Vec<bool>,
    pub st_rim: Vec<bool>,
    /// per block: is this block's dot area locally flat. Kept for inspection and for any future
    /// split of a mixed region -- a photograph abutting a tint is one connected screened area, and
    /// this is the only signal that says where one ends and the other begins.
    pub uniform: Vec<bool>,
    pub measured_blk: Vec<bool>,
    /// per-block median dot area per ink, and how many contone pixels that median came from.
    /// Dumped as data so a class verdict can be audited against the blocks that produced it.
    pub bmean: Vec<[f32; 4]>,
    pub nvals: Vec<u32>,
    /// PER PIXEL at the stencil grid: is this pixel inside its block's region.
    ///
    /// The block grid is 1.35 mm and a region's boundary quantised to it is both a staircase and a
    /// tile too wide. Blocks find the screen -- that needs the big window for frequency resolution --
    /// but once the vector is known, COHERENCE answers "is this pixel part of that lattice" at 600
    /// dpi with no window at all. So the boundary is placed at pixel scale by coherence, and only
    /// the interior is taken wholesale.
    pub pix: Vec<bool>,
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
    pixmask: &[bool],
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
            // the refined per-pixel membership, not the block's
            let l = if pixmask[i] { label[bi] } else { 0 };
            // INSIDE A PICTURE, EVERYTHING IS CONTONE -- and this is a KNOWN, MEASURED COMPROMISE,
            // not a rule that is simply right. It costs every mark printed ON a picture: the cover
            // renders with K stencil 0.0%, so its headlines come from the 150 dpi background, and
            // about a quarter of the issue has a region covering more than half the page.
            //
            // Removing it was tried and is worse. Without it the cover's stencil fills with the
            // photograph's own high-contrast detail -- the mandrill's eyes, nose ridges and fur
            // arrive as hard black speckle drawn at 600 dpi over a soft contone image.
            //
            // The separators one would reach for do not work, measured on p001:
            //   * ink level -- the photograph's shadows read K 236-250, exactly as solid as type
            //   * coherence alone -- a photograph's solid passages carry no dots either, so they are
            //     as incoherent as a glyph
            // What is actually needed is "solid ink that IS the picture" vs "solid ink printed ON
            // it", which is a thin-structure question, and FINDINGS.md 3 is the record of what
            // happens when that is answered with low-level statistics. Left as it is until there is
            // a measurement that separates them. A photograph is drawn entirely by the
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

/// Half-width of the SHORTEST interval containing `frac` of the sample -- the spread of the
/// densest part of the distribution rather than of its extremes.
///
/// This is the estimator the class test needs, and the reason is physical, not statistical. A tint
/// exists to carry type; every tint in the magazine has words on it. Type is a SECOND population in
/// the same pixels: it adds ink (dark type on a light tint) or removes it (knockout type on a dark
/// bar), so the values are bimodal and the contamination is one-sided -- but which side flips with
/// the polarity of the type. An interdecile or interquartile range straddles both modes and so
/// measures how much type the block carries; measured on p022, corr(block median, solid-ink
/// coverage) = +0.62..+0.88 in all ten bands of one table, and identical tint rows read 4.5 to 34.
/// The densest interval sits on whichever mode is the bulk, which for a tint is the tint.
///
/// A photograph has no dense mode to sit on -- its tone travels, so even the densest 70% is wide.
/// Measured, per region, max over inks:
///
///     estimator      p022 (10 tint rows)   p001/p073 (3 photographs)
///     p90-p10             4.5 .. 34.0           75.5 .. 124.0
///     shortest 70%        2.5 ..  7.0           20.0 ..  59.5
///
/// The threshold did not move; only the estimator was wrong.
fn shortest_u8(v: &[u8], frac: f32) -> f32 {
    let n = v.len();
    if n < 4 {
        return 0.0;
    }
    let w = ((n as f32 * frac) as usize).max(2);
    let mut best = f32::MAX;
    for i in 0..=(n - w) {
        best = best.min((v[i + w - 1] as f32) - (v[i] as f32));
    }
    best / 2.0
}

fn shortest_f32(v: &[f32], frac: f32) -> f32 {
    let n = v.len();
    if n < 4 {
        return f32::MAX;
    }
    let w = ((n as f32 * frac) as usize).max(2);
    let mut best = f32::MAX;
    for i in 0..=(n - w) {
        best = best.min(v[i + w - 1] - v[i]);
    }
    best / 2.0
}

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
    let nvals: Vec<u32> = (0..ny * nx).map(|bi| block_vals[bi][0].len() as u32).collect();
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
            bspread[bi][ci] = shortest_u8(v, MODE_FRAC);
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

    // ---- 3. GROUP BY SCREENING, AND ONLY BY SCREENING -----------------------------------------
    //
    // Screening is a property of a TILE: the block either carries a halftone or it does not. Whether
    // a region is a flat fill or a photograph is a property of the WHOLE CONTIGUOUS CHUNK, and
    // cannot be asked before the chunk exists. Deciding it per block and SEGMENTING on that verdict
    // shattered a photograph into hundreds of one-block areas -- and destroyed the very test that
    // separates a smooth photograph from a tint, since a one-block area has no "across itself".
    // Same error as the deleted renderer's per-cluster vote at a different scale (FINDINGS.md 3).
    //
    // Four steps, in this order, each recorded separately so the debug drawer can attribute a wrong
    // shape to the step that made it:
    //
    //   1  screening        the tiles that measured a halftone
    //   2  absorb solid     near-solid ink reachable from those tiles -- a picture's own shadow
    //   3  fill             everything enclosed by the result -- a picture's own highlight
    //   4  extend one tile  the rim, where the window straddles the picture's edge
    let st_screen = fired_mask.clone();
    let mut m = fired_mask.clone();

    // 2 -- ABSORB. A halftone has no dots in a solid shadow, so those blocks never fire, and being
    // connected to the page edge rather than enclosed the fill cannot reach them either. Propagate
    // GEODESICALLY from the screened tiles through near-solid ink: a shadow is followed however far
    // it runs, and paper stops it dead. Mean ink, not a coverage fraction -- a solid passage inks
    // the whole block and means ~250, a block of body type is 30% covered and means ~76.
    let st_absorb;
    {
        let mut inked = vec![false; ny * nx];
        let mut sum = vec![0.0f32; ny * nx];
        let mut cnt = vec![0u32; ny * nx];
        for ty in 0..tone.h {
            for tx in 0..tone.w {
                let bi = block_of_source(f, ty * ty_per, tx * tx_per);
                let strongest = (0..4).map(|ci| tone.ink[ci][ty * tone.w + tx]).max().unwrap_or(0);
                sum[bi] += strongest as f32;
                cnt[bi] += 1;
            }
        }
        for bi in 0..ny * nx {
            inked[bi] = cnt[bi] > 0 && sum[bi] / cnt[bi] as f32 >= ABSORB_MEAN;
        }
        // BOUNDED, not unlimited. Absorption exists to pick up a picture's OWN solid passages -- a
        // shadow, a dark panel -- which lie within a centimetre or so of the screen that proves the
        // picture is there. An unbounded geodesic walks through any chain of near-solid ink, and on
        // p073 it crossed from the photograph into the solid red banner: the banner joined a photo
        // region, and inside a non-flat region the stencil is suppressed, so the banner's own type
        // stopped being drawn crisply (stencil M 25.5% -> 1.5%).
        //
        // ABSORB_BLOCKS is the leash. 8 blocks is 10.8 mm at 2400 dpi -- wider than any shadow on
        // this paper, far short of the gap between two separate graphics.
        let mask: Vec<bool> = (0..ny * nx).map(|i| inked[i] || m[i]).collect();
        let mut reach = m.clone();
        for _ in 0..ABSORB_BLOCKS {
            let d = ndimage::binary_dilation(&reach, nx, ny, 1);
            let next: Vec<bool> = (0..ny * nx).map(|i| d[i] && mask[i]).collect();
            if next == reach {
                break;
            }
            reach = next;
        }
        st_absorb = (0..ny * nx).map(|i| reach[i] && !m[i]).collect::<Vec<bool>>();
        m = reach;
    }

    // 3 -- FILL, PER OBJECT. Close the halftone's own gaps, then take everything each object
    // encloses BY ITSELF.
    //
    // Filling the union is wrong, and wrong in a way that only shows once detection is good: three
    // separate pictures near each other -- p073 has a computer, a printer and a printout -- jointly
    // ring the paper between them, so a global fill claims that paper and merges all three into one
    // 16,000-block region spanning the whole photographic zone. "Fill all inner blocks" means inner
    // to an OBJECT. A photograph's specular highlight is enclosed by that photograph; the gap
    // between two photographs is enclosed by neither of them alone.
    let st_fill;
    {
        let before = m.clone();
        let seed = m.clone();
        if CLOSE_BLOCKS > 0 {
            m = ndimage::binary_dilation(&m, nx, ny, CLOSE_BLOCKS);
            m = ndimage::binary_erosion(&m, nx, ny, CLOSE_BLOCKS);
        }
        // a closing is EXTENSIVE: it may only add. binary_erosion treats outside-the-array as empty,
        // so without this the blocks within CLOSE_BLOCKS of the grid edge erode away and never
        // return -- 4 mm off every full-bleed picture.
        for i in 0..ny * nx {
            if seed[i] {
                m[i] = true;
            }
        }
        let (cl, cn) = ndimage::label(&m, nx, ny);
        let mut filled = m.clone();
        for c in 1..=cn {
            let only: Vec<bool> = cl.iter().map(|&l| l == c as u32).collect();
            let f = ndimage::binary_fill_holes(&only, nx, ny);
            for i in 0..ny * nx {
                if f[i] {
                    filled[i] = true;
                }
            }
        }
        m = filled;
        st_fill = (0..ny * nx).map(|i| m[i] && !before[i]).collect::<Vec<bool>>();
    }

    let (lb, nreg) = ndimage::label(&m, nx, ny);
    let sz = ndimage::component_sizes(&lb, nreg);
    let mut label: Vec<u32> = vec![0; ny * nx];
    let mut region_of: Vec<u32> = vec![0; nreg + 1];
    let mut nkept = 0u32;
    for c in 1..=nreg {
        if sz[c - 1] >= MIN_AREA_BLOCKS as u64 {
            nkept += 1;
            region_of[c] = nkept;
        }
    }
    for i in 0..ny * nx {
        if lb[i] != 0 {
            label[i] = region_of[lb[i] as usize];
        }
    }

    // 4 -- EXTEND one tile, recorded separately from the interior. A block straddling a picture's
    // edge holds part picture and part surround, so its screen signal is diluted and it often does
    // not fire; enclosure cannot help it, being by definition not enclosed. The rim buys CONTONE
    // COVERAGE and spends no marks: "inside a picture everything is contone" keeps halftone dots out
    // of the bilevel layer, and that rule must not reach out over whatever the picture abuts -- a
    // caption 1.35 mm away would lose its stencil.
    let interior = label.clone();
    let st_rim;
    {
        let snap = label.clone();
        for by in 0..ny {
            for bx in 0..nx {
                let i = by * nx + bx;
                if snap[i] != 0 {
                    continue;
                }
                // EIGHT neighbours, not four. A picture whose edge runs at an angle to the block
                // grid -- which is most of them; p073's C64 sits at about 30 degrees -- has a
                // STAIRCASE boundary, and a 4-neighbour extension covers the flat of every step
                // while leaving the outer CORNER of it bare. The result is a row of one-tile holes
                // along every sloped edge, which is what "the C64 is missing a corner" looks like.
                let mut found = 0u32;
                'nb: for dy in -1i64..=1 {
                    for dx in -1i64..=1 {
                        if dy == 0 && dx == 0 {
                            continue;
                        }
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            continue;
                        }
                        let j = y2 as usize * nx + x2 as usize;
                        if snap[j] != 0 {
                            found = snap[j];
                            break 'nb;
                        }
                    }
                }
                if found != 0 {
                    label[i] = found;
                }
            }
        }
        st_rim = (0..ny * nx).map(|i| label[i] != 0 && snap[i] == 0).collect::<Vec<bool>>();
    }

    // ---- 4. NOW ask each complete chunk what it is ---------------------------------------------
    //
    // Two scales, both over the whole region, and a region must pass both to be called flat:
    //   WITHIN  the median of its blocks' own dot-area spreads -- is it flat everywhere locally
    //   ACROSS  the spread of its blocks' median dot areas     -- and is it the same colour throughout
    // A tint bar is flat on both. A photograph is often flat WITHIN (a soft passage is smooth inside
    // 1.35 mm) and never flat ACROSS, which is exactly what distinguishes them.
    let mut areas: Vec<Area> = Vec::new();
    for id in 1..=nkept {
        let blocks: Vec<usize> = (0..ny * nx).filter(|&i| label[i] == id).collect();
        if blocks.is_empty() {
            continue;
        }
        let meas: Vec<usize> = blocks.iter().cloned().filter(|&i| measured[i]).collect();
        let (mut y0, mut x0, mut y1, mut x1) = (ny, nx, 0usize, 0usize);
        for &i in &blocks {
            let (by, bx) = (i / nx, i % nx);
            y0 = y0.min(by);
            x0 = x0.min(bx);
            y1 = y1.max(by);
            x1 = x1.max(bx);
        }
        let mut mean = [0.0f32; 4];
        let mut within = [0.0f32; 4];
        let mut across = 0.0f32;
        for ci in 0..4 {
            if meas.is_empty() {
                continue;
            }
            let mut mv: Vec<f32> = meas.iter().map(|&i| bmean[i][ci]).collect();
            let mut sv: Vec<f32> = meas.iter().map(|&i| bspread[i][ci]).collect();
            mv.sort_by(|a, b| a.partial_cmp(b).unwrap());
            sv.sort_by(|a, b| a.partial_cmp(b).unwrap());
            mean[ci] = mv[mv.len() / 2];
            within[ci] = sv[sv.len() / 2];
            // shortest_f32 returns f32::MAX below four blocks: too few to know whether the tone
            // travels, and a flat fill replaces a whole region with one colour, so "cannot tell"
            // must fall to the contone side.
            across = across.max(shortest_f32(&mv, MODE_FRAC));
        }
        let mut lpis: Vec<f32> = Vec::new();
        for &i in &blocks {
            for ci in 0..4 {
                if screen::fired(f, ci, i) {
                    lpis.push(f.ink[ci].lpi[i]);
                }
            }
        }
        lpis.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let flat = !meas.is_empty()
            && (0..4).all(|ci| within[ci] <= UNIFORM_STD)
            && across <= UNIFORM_ACROSS;
        let colour = (0..3).any(|ci| mean[ci] >= COLOUR_INK);
        areas.push(Area {
            id: (id - 1) as usize,
            class: if flat {
                Class::Flat
            } else if colour {
                Class::ColourPhoto
            } else {
                Class::GreyPhoto
            },
            bbox: (y0, x0, y1, x1),
            blocks: blocks.len(),
            mean,
            std: within,
            across,
            n_meas: meas.len(),
            lpi: if lpis.is_empty() { 0.0 } else { lpis[lpis.len() / 2] },
        });
    }

    // ---- 4d. place the boundary at PIXEL scale ------------------------------------------------
    //
    // A block on the edge of a region has its whole 1.35 mm cell claimed, including whatever part of
    // it lies past where the screen actually stops -- and the one-tile rim claims another 1.35 mm on
    // top. Both are the same quantisation error, seen from either side of the edge.
    //
    // Coherence already measures, per pixel at 600 dpi, whether the ink there belongs to the lattice
    // this block measured. So: interior blocks are taken whole (they are solidly inside, and asking
    // per pixel there would only punch holes wherever a glyph sits on a tint), and EDGE blocks are
    // resolved per pixel. The boundary then follows the screen instead of the grid.
    //
    // It cannot localise finer than coherence's own smoothing, ~1.5 screen periods or about 1 mm --
    // but that is a soft, true edge instead of a hard, wrong one.
    let pix = {
        let mut edge = vec![false; ny * nx];
        for by in 0..ny {
            for bx in 0..nx {
                let i = by * nx + bx;
                if label[i] == 0 {
                    continue;
                }
                let mut touches_out = false;
                'e: for dy in -1i64..=1 {
                    for dx in -1i64..=1 {
                        let (y2, x2) = (by as i64 + dy, bx as i64 + dx);
                        if y2 < 0 || x2 < 0 || y2 >= ny as i64 || x2 >= nx as i64 {
                            touches_out = true;
                            break 'e;
                        }
                        if label[y2 as usize * nx + x2 as usize] == 0 {
                            touches_out = true;
                            break 'e;
                        }
                    }
                }
                edge[i] = touches_out;
            }
        }
        let mut m = vec![false; sw * sh];
        for cy in 0..sh {
            for cx in 0..sw {
                let bi = block_of_source(f, cy * sdiv, cx * sdiv);
                if label[bi] == 0 {
                    continue;
                }
                m[cy * sw + cx] = if edge[bi] {
                    (0..4).any(|ci| coh.ink[ci][cy * sw + cx] >= COHERENT)
                } else {
                    true
                };
            }
        }
        m
    };

    // ---- 5. stencils, now that the areas are known -------------------------------------------
    let (sw2, sh2, stencil) = stencils(disp, coh, f, &interior, &pix, &areas, &fired_mask, tone);
    debug_assert_eq!((sw, sh), (sw2, sh2));

    let n_fired = fired_mask.iter().filter(|&&b| b).count();
    let n_measured = measured.iter().filter(|&&b| b).count();
    Routing {
        ny, nx, n_fired, n_measured,
        st_screen, st_absorb, st_fill, st_rim,
        fired: fired_mask, label, pix, uniform, measured_blk: measured, bmean, nvals, areas, stencil, sw, sh,
    }
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
    // Per-step block counts, because "the region is too big" is not actionable but "the rim added
    // 9000 blocks" is.
    let n = (r.ny * r.nx) as f64;
    let pc = |v: usize| 100.0 * v as f64 / n;
    let (sc, ab, fi, ri) = (
        r.st_screen.iter().filter(|&&b| b).count(),
        r.st_absorb.iter().filter(|&&b| b).count(),
        r.st_fill.iter().filter(|&&b| b).count(),
        r.st_rim.iter().filter(|&&b| b).count(),
    );
    let cov = r.label.iter().filter(|&&l| l != 0).count();
    format!(
        "p{} blocks {} fired / {} measured | steps screen {} ({:.0}%) +absorb {} +fill {} +rim {} \
         = covered {} ({:.0}%) | areas: {} colour-photo, {} grey-photo, {} flat | stencil {}",
        page,
        r.n_fired,
        r.n_measured,
        sc, pc(sc), ab, fi, ri, cov, pc(cov),
        c1,
        c2,
        c3,
        if sp.is_empty() { "none".into() } else { sp.join(" ") }
    )
}
