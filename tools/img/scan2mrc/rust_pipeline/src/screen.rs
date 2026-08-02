//! STAGE A — the screen field. The one measurement the whole renderer rests on.
//!
//! For each ink (C, M, Y, K) and each block of the page: IS THERE A HALFTONE HERE, and if so at
//! what ruling and angle. Nothing is decided here and nothing is routed; this stage only measures.
//!
//! Everything downstream is a crossing of two questions asked of this field:
//!
//!     screened, dot area varies   -> contone      (a photograph)
//!     screened, dot area uniform  -> flat fill    (a tint or a box background)
//!     not screened                -> bilevel      (type, rules, line art)
//!
//! WHY PER INK. The press screened each plate at its own angle -- C 71 / M 19 / K 45 on the process
//! photos -- and the design tints do not follow the plate convention at all: a two-ink tint sits on
//! the {45, 75} pair and which ink takes which angle flips per box. A single luma measurement sees
//! the sum of up to four gratings and can lock onto any of them, or onto their beat.
//!
//! WHY AT 2400 dpi. A 150 lpi screen is 4 px per cycle at 600 dpi -- exactly where a 4x box
//! downsample has its first null. The previous implementation measured at 600 and survived only
//! because these screens sit at 19/45/71 degrees, where the 2D box response is ~0.6 rather than 0.
//! It would have failed silently on an axis-aligned screen. At 2400 dpi a 150 lpi screen is 16 px
//! per cycle and nothing is near Nyquist.
//!
//! WHY ON UNCLIPPED CHANNELS. Measured, page 092: the display grade (C 50-90, K 90-95) compresses
//! 8.9x under zstd, the unclipped detect grade 1.9x. That ratio IS the halftone energy the clip
//! throws away -- a light tint's dots can fall below the level floor and vanish entirely. Render
//! from the graded planes; measure on the unclipped ones.
//!
//! See FINDINGS.md for the measurements behind every constant below.

use crate::imageio::Cmyk;
use crate::{fftutil, npy};
use anyhow::Result;
use num_complex::Complex32;
use rayon::prelude::*;

// ================================================================================================
//  CONSTANTS. All of them, documented, at the top -- no CLI flags and no env vars. Two agents
//  reading the same constant from two places is how the last renderer ended up with two detectors
//  that disagreed, and how a sweep once quoted sizes for a file that was never rendered.
// ================================================================================================

/// Resolution of the CMYK the field is measured on. Everything spatial below is in px at this dpi.
pub const SRC_DPI: f64 = 2400.0;

/// Analysis window, px @2400. A screen must show ~8+ cycles inside the window for its peak to be
/// separable from the noise floor: 256 px is 16 cycles at 150 lpi and still 8.6 at the coarsest
/// ruling in this issue (81 lpi, on p092's pasted-in ads).
///
/// DO NOT SHRINK THIS TO IMPROVE LOCALISATION. It was tried, and measured: dropping the window from
/// 240 to 160 px collapsed real-screen retention from 22196 blocks to 5175, because a 133 lpi tint
/// (18 px pitch) stops being resolvable. Bloom was unchanged. The screen lock dominates -- use STEP
/// for localisation, not WIN.
pub const WIN: usize = 256;

/// Anchor spacing, px @2400 = 1.35 mm. Fine enough to separate a tint bar from the type sitting on
/// it, which is the discrimination this whole design turns on. Blocks overlap (WIN > STEP); each
/// block's verdict is attributed to its CENTRE, see `block_origin`.
pub const STEP: usize = 128;

/// Screen band, lines per inch. Measured content on this issue: process photos 150-159, design
/// tints 133-152, one-ink cyan tints ~133, pasted-in ad artwork ~100-134. Wider than that range --
/// the old detector's 139-192 lpi band was blind to the 133 lpi tints and to the entire ad section,
/// and caught them only through spectral leakage.
///
/// THE LOW EDGE IS DERIVED, not padded. Over 20 pages, the ruling histogram of real content (blocks
/// that are coherent and not a follower, N=102,697) is EMPTY between 55 and 95 lpi: 7 blocks, 0.01%.
/// Below it sat 13,781 firing blocks whose angles were near-uniform across the admissible range,
/// where real screens concentrate hard at 40-50 and 130-140 degrees -- the signature of broadband
/// 1/f energy leaking into the band's low corner, not of a structure. A subharmonic-lock explanation
/// was tested and disproved: only 5.4% of them had a cross-ink peak at 2x/2.5x/3x their own ruling.
/// 75 sits inside that empty gap and removes 81% of the junk at zero cost in real content.
pub const LO_LPI: f64 = 75.0;
pub const HI_LPI: f64 = 220.0;

/// Half-width of the rejected wedge around the horizontal and vertical axes, degrees.
///
/// THIS IS WHAT SEPARATES TYPE FROM SCREEN. Body text is periodic -- it has a line rhythm -- and
/// that rhythm is on-axis at 0 degrees. A halftone at 19/45/71 degrees is not. Measured on p092:
/// the body type's spectral peak sits at 0 degrees and is rejected here, which is why this design
/// needs no "is it a photo or is it type" classifier anywhere.
///
/// A true Y screen may be on-axis (~0/90) and would also be rejected. That is accepted: an
/// axis-aligned screen is indistinguishable from line rhythm by this test, and Y is the ink whose
/// geometry was least trustworthy in the old measurements anyway.
pub const AXIS_DEG: f64 = 12.0;

/// A block reports a screen when peak/median over the band exceeds this. Median, not mean: one
/// strong peak drags a mean upward and shrinks its own prominence.
///
/// Derived over 20 pages: real content's prominence 5th percentile is 17.1 against 13.0 for junk,
/// so the old value of 8 was doing no work at all and nothing between 8 and 15 changes any verdict.
/// 12 costs 2,671 blocks issue-wide. Do not raise it past ~15, where it starts cutting real screens.
pub const FIRE: f32 = 12.0;

/// ...AND the peak must be at least this deep, in ink levels (0-255).
///
/// PROMINENCE ALONE IS NOT ENOUGH, and this is the first thing stage A got wrong. `peak/median` is
/// a RATIO, so it is scale-invariant: a 5-level ripple scores exactly like a 200-level screen.
/// Measured on p092, a page that is essentially black-and-white: C, M and Y each "fired" on ~30% of
/// blocks at 102 lpi @ 45 degrees -- the same ruling and angle as K, because the separation is
/// geometric and a neutral halftone dot leaves a faint echo of the K screen in every channel. GCR
/// does not remove it (30% before, 30% after): GCR subtracts min(C,M,Y), and the per-channel
/// residue that survives still carries the pattern, just at a few levels of amplitude.
///
/// A real halftone swings between paper and near-solid ink; crosstalk residue is single digits.
///
/// BUT DEPTH IS THE WEAKER OF THE TWO DEFENCES, measured over 20 pages and 737,301 blocks. The
/// crosstalk population runs to depth 34.6 and real screens live down at 8, so the two overlap by
/// physics: a 5% tint modulates as little as a K echo does. Raising DEPTH far enough to cover the
/// crosstalk costs more real content than it saves -- the marginal cost per artifact removed goes
/// 0.93 blocks at 18->20, 1.64 at 20->22, then 4.03, 10.9, 38.3. The elbow is at 22, which is where
/// this sits; the rest of the job belongs to the follower rule below, which is a GEOMETRIC test and
/// separates the populations cleanly where amplitude cannot.
pub const DEPTH: f32 = 22.0;

/// FOLLOWER REJECTION -- the real defence against crosstalk, and the one rule here that is derived
/// from the page rather than fixed.
///
/// The RGB->CMYK separation is geometric, so one plate's halftone leaves a faint echo of ITSELF in
/// the other channels: same ruling, same angle, a fraction of the amplitude. An ink whose peak
/// merely follows a stronger ink's peak at the same geometry is not evidence of a second screen.
///
/// Measured over 737,301 blocks: 25.6% are followers, their depths run to 34.6 and stop, and the
/// histogram valley in depth begins at exactly 35-40. Two independent signals agreeing on the same
/// boundary is what makes this a derivation rather than a fitted threshold. Applying it as a
/// rejection keeps 56,540 MORE real blocks than raising DEPTH to 26 does, while leaving fewer
/// artifacts behind.
///
/// It also cannot be fooled by page strength, because it references the page's own strongest
/// co-located peak instead of any absolute level. Per-page DEPTH scaling was tested as an
/// alternative and is actively harmful: it LOWERS the bar on exactly the pages that are weak
/// because they have no screen at all (p086 has 4 coherent blocks at any threshold; scaled DEPTH
/// would admit 1,419).
///
/// KNOWN GAP: it does not catch the p073 case, where C, M and K all report 181 lpi at 24 degrees
/// with depths 21/27/31 -- within 1.8x of each other, so none is a follower of another. Three real
/// plates cannot share an angle (they are set apart precisely to avoid moire), so that is one
/// structure appearing in three channels. Whether 181 is a real ruling or the second harmonic of
/// ~90 cannot be decided from the stored peak alone; `sub2` and `sub5` below exist to answer it.
pub const FOLLOW_RATIO: f32 = 1.8;
pub const FOLLOW_LPI_FRAC: f32 = 0.03;
pub const FOLLOW_ANG_DEG: f32 = 3.0;

// ================================================================================================

/// The measured field for one ink. All three planes are `ny * nx`, block-major.
pub struct InkField {
    /// peak / median magnitude over the band = "is the spectrum's energy concentrated in one line"
    pub prom: Vec<f32>,
    /// amplitude of that peak in ink levels (0-255) = "is it a screen or a rounding artifact"
    pub depth: Vec<f32>,
    /// that block's own ruling, lines per inch (0 where no peak was found)
    pub lpi: Vec<f32>,
    /// and its angle, degrees, folded to 0..180 (the dot grid is symmetric)
    pub ang: Vec<f32>,
    /// band magnitude at HALF the peak frequency, same angle, over the band median. If the peak we
    /// locked onto is really the 2nd harmonic of a coarser screen, the fundamental is sitting here.
    pub sub2: Vec<f32>,
    /// likewise at 2/5 of the peak frequency: the (2,1) lattice point of a screen at ~1/sqrt(5) of
    /// the measured ruling, which is the other way an off-axis lattice can be misread.
    pub sub5: Vec<f32>,
}

pub struct ScreenField {
    pub ny: usize,
    pub nx: usize,
    /// C, M, Y, K
    pub ink: Vec<InkField>,
}

/// Top-left of block (by, bx) in page pixels. Blocks overlap; the verdict belongs to the CENTRE of
/// the window, not to this corner -- see `centre_of`.
fn block_origin(by: usize, bx: usize) -> (usize, usize) {
    (by * STEP, bx * STEP)
}

/// Where a block's verdict actually applies: the centre of its window.
///
/// The old detector wrote each 240 px window's score to the grid cell at its TOP-LEFT corner, which
/// dilated every feature about four cells (2.5 mm) down and to the right into the surrounding white
/// paper. That bloom then had to be suppressed with an aggressive minimum-area filter, which in
/// turn deleted every small photograph on the ad pages. Two bugs, one off-by-a-window-radius.
pub fn centre_of(by: usize, bx: usize) -> (usize, usize) {
    let (y0, x0) = block_origin(by, bx);
    (y0 + WIN / 2, x0 + WIN / 2)
}

/// Precomputed per-bin geometry of the shifted spectrum, shared by every block.
struct Band {
    /// indices into the WIN*WIN shifted spectrum that lie in the band and off-axis
    idx: Vec<usize>,
    /// sum of the Hann window, for turning a peak magnitude back into ink levels
    gain: f64,
    /// lines per inch of each bin
    lpi: Vec<f32>,
    /// angle of each bin, degrees 0..180
    ang: Vec<f32>,
    /// separable Hann window, WIN*WIN
    win: Vec<f32>,
}

fn band() -> Band {
    let f = fftutil::fftfreq(WIN);
    let sh = fftutil::fftshift_indices(WIN);
    let fs: Vec<f64> = sh.iter().map(|&i| f[i]).collect();
    let (lo, hi) = (LO_LPI / SRC_DPI, HI_LPI / SRC_DPI);
    let mut idx = Vec::new();
    let mut lpi = vec![0.0f32; WIN * WIN];
    let mut ang = vec![0.0f32; WIN * WIN];
    for iy in 0..WIN {
        for ix in 0..WIN {
            let (fy, fx) = (fs[iy], fs[ix]);
            let r = (fy * fy + fx * fx).sqrt();
            // Folded to 0..180: a halftone's dot grid has 180-degree symmetry, so an angle and its
            // opposite are the same screen.
            let a = fy.atan2(fx).to_degrees().rem_euclid(180.0);
            let on_axis = a.min(180.0 - a) < AXIS_DEG || (a - 90.0).abs() < AXIS_DEG;
            let i = iy * WIN + ix;
            lpi[i] = (r * SRC_DPI) as f32;
            ang[i] = a as f32;
            if r > lo && r < hi && !on_axis {
                idx.push(i);
            }
        }
    }
    let h1: Vec<f32> = (0..WIN)
        .map(|i| 0.5 - 0.5 * (2.0 * std::f64::consts::PI * i as f64 / (WIN - 1) as f64).cos())
        .map(|v| v as f32)
        .collect();
    let mut win = vec![0.0f32; WIN * WIN];
    for y in 0..WIN {
        for x in 0..WIN {
            win[y * WIN + x] = h1[y] * h1[x];
        }
    }
    let gain: f64 = win.iter().map(|&v| v as f64).sum();
    Band { idx, gain, lpi, ang, win }
}

/// Sub-bin refinement of the peak by parabolic interpolation on log magnitude, separately in the
/// row and column directions.
///
/// NEEDED, not a polish step: at WIN=512 a previous attempt to read the screen angle straight off
/// the argmax locked onto the FFT lattice's own diagonals -- 45, 63.4 (=atan 2), 71.6 (=atan 3)
/// degrees -- rather than the screen fundamental, and the angles it reported were those constants
/// dressed up as measurements. Interpolating between bins removes the lattice quantisation that
/// produced them.
fn refine(mag: &[f32], pk: usize) -> (f64, f64) {
    let (py, px) = (pk / WIN, pk % WIN);
    let lg = |y: usize, x: usize| -> f64 { (mag[y * WIN + x].max(1e-12) as f64).ln() };
    // parabola through three samples; offset is 0 at the centre, +-0.5 at the neighbours
    let off = |m: f64, c: f64, p: f64| -> f64 {
        let d = m - 2.0 * c + p;
        if d.abs() < 1e-12 {
            0.0
        } else {
            (0.5 * (m - p) / d).clamp(-0.5, 0.5)
        }
    };
    let dy = if py > 0 && py + 1 < WIN {
        off(lg(py - 1, px), lg(py, px), lg(py + 1, px))
    } else {
        0.0
    };
    let dx = if px > 0 && px + 1 < WIN {
        off(lg(py, px - 1), lg(py, px), lg(py, px + 1))
    } else {
        0.0
    };
    (py as f64 + dy, px as f64 + dx)
}

/// Bilinear sample of the shifted magnitude at a fractional bin position. Used to probe whether a
/// coarser fundamental exists under the peak we locked onto.
fn sample(mag: &[f32], ry: f64, rx: f64) -> f32 {
    if ry < 0.0 || rx < 0.0 || ry >= (WIN - 1) as f64 || rx >= (WIN - 1) as f64 {
        return 0.0;
    }
    let (y0, x0) = (ry.floor() as usize, rx.floor() as usize);
    let (fy, fx) = ((ry - y0 as f64) as f32, (rx - x0 as f64) as f32);
    let g = |y: usize, x: usize| mag[y * WIN + x];
    let top = g(y0, x0) * (1.0 - fx) + g(y0, x0 + 1) * fx;
    let bot = g(y0 + 1, x0) * (1.0 - fx) + g(y0 + 1, x0 + 1) * fx;
    top * (1.0 - fy) + bot * fy
}

/// Measure one channel over the whole page.
fn channel_field(plane: &[u8], w: usize, h: usize, b: &Band) -> (usize, usize, InkField) {
    let ny = if h >= WIN { (h - WIN) / STEP + 1 } else { 0 };
    let nx = if w >= WIN { (w - WIN) / STEP + 1 } else { 0 };
    if ny == 0 || nx == 0 {
        return (
            0,
            0,
            InkField { prom: vec![], depth: vec![], lpi: vec![], ang: vec![], sub2: vec![], sub5: vec![] },
        );
    }
    // Bin centre in shifted coordinates, so a refined (row, col) can be turned back into a
    // frequency: bin i is (i - WIN/2)/WIN cycles per pixel.
    let c = (WIN / 2) as f64;
    let out: Vec<(f32, f32, f32, f32, f32, f32)> = (0..ny * nx)
        .into_par_iter()
        .map(|bi| {
            let (by, bx) = (bi / nx, bi % nx);
            let (y0, x0) = block_origin(by, bx);
            let mut tile = vec![0.0f32; WIN * WIN];
            let mut sum = 0.0f64;
            for y in 0..WIN {
                let row = (y0 + y) * w + x0;
                for x in 0..WIN {
                    let v = plane[row + x] as f32;
                    tile[y * WIN + x] = v;
                    sum += v as f64;
                }
            }
            // Remove DC before windowing: a bright block and a dark block of the same texture must
            // measure the same, and the Hann window would otherwise smear the mean across the
            // low-frequency bins.
            let mean = (sum / (WIN * WIN) as f64) as f32;
            for i in 0..WIN * WIN {
                tile[i] = (tile[i] - mean) * b.win[i];
            }
            let spec = fftutil::fft2_real(&tile, WIN, WIN);
            let sh = fftutil::fftshift2(&spec, WIN, WIN);
            let mag: Vec<f32> = sh.iter().map(|z| (*z as Complex32).norm()).collect();

            let mut vals: Vec<f32> = Vec::with_capacity(b.idx.len());
            let mut peak = (0.0f32, 0usize);
            for &i in &b.idx {
                let m = mag[i];
                vals.push(m);
                if m > peak.0 {
                    peak = (m, i);
                }
            }
            if vals.is_empty() {
                return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
            }
            vals.sort_by(|p, q| p.partial_cmp(q).unwrap());
            let med = vals[vals.len() / 2].max(1e-6);

            let (ry, rx) = refine(&mag, peak.1);
            let (fy, fx) = ((ry - c) / WIN as f64, (rx - c) / WIN as f64);
            let r = (fy * fy + fx * fx).sqrt();
            let a = fy.atan2(fx).to_degrees().rem_euclid(180.0);
            // A sinusoid of amplitude A, Hann-windowed, puts |X| = A/2 * sum(win) into each of its
            // two conjugate bins -- so this recovers A in ink levels.
            let depth = (2.0 * peak.0 as f64 / b.gain) as f32;
            // Probe for a coarser fundamental beneath this peak, along the SAME direction: at half
            // the frequency (this peak would then be a 2nd harmonic) and at 2/5 of it (this peak
            // would be the (2,1) lattice point of a screen 1/sqrt(5) as fine). Reported relative to
            // the band median, so it is comparable with `prom`.
            let sub2 = sample(&mag, c + (ry - c) * 0.5, c + (rx - c) * 0.5) / med;
            let sub5 = sample(&mag, c + (ry - c) * 0.4, c + (rx - c) * 0.4) / med;
            (peak.0 / med, depth, (r * SRC_DPI) as f32, a as f32, sub2, sub5)
        })
        .collect();

    let mut f = InkField {
        prom: vec![0.0; ny * nx],
        depth: vec![0.0; ny * nx],
        lpi: vec![0.0; ny * nx],
        ang: vec![0.0; ny * nx],
        sub2: vec![0.0; ny * nx],
        sub5: vec![0.0; ny * nx],
    };
    for (i, (p, d, l, a, s2, s5)) in out.into_iter().enumerate() {
        f.prom[i] = p;
        f.depth[i] = d;
        f.lpi[i] = l;
        f.ang[i] = a;
        f.sub2[i] = s2;
        f.sub5[i] = s5;
    }
    (ny, nx, f)
}

/// Measure all four inks. `cmyk` must be the UNCLIPPED (detect-grade), pre-GCR separation -- see
/// the module note.
pub fn measure(cmyk: &Cmyk) -> ScreenField {
    let b = band();
    let mut ink = Vec::with_capacity(4);
    let (mut ny, mut nx) = (0, 0);
    for ci in 0..4 {
        let (y, x, f) = channel_field(cmyk.channel(ci), cmyk.w, cmyk.h, &b);
        ny = y;
        nx = x;
        ink.push(f);
    }
    ScreenField { ny, nx, ink }
}

/// Angular distance in degrees, on the 0..180 fold.
fn angdiff(a: f32, b: f32) -> f32 {
    let d = (a - b).abs() % 180.0;
    d.min(180.0 - d)
}

/// True where this ink's peak in this block merely echoes a stronger ink's peak. See FOLLOW_RATIO.
pub fn is_follower(f: &ScreenField, ci: usize, i: usize) -> bool {
    let a = &f.ink[ci];
    for cj in 0..4 {
        if cj == ci {
            continue;
        }
        let b = &f.ink[cj];
        if b.depth[i] >= FOLLOW_RATIO * a.depth[i]
            && (b.lpi[i] - a.lpi[i]).abs() <= FOLLOW_LPI_FRAC * a.lpi[i]
            && angdiff(b.ang[i], a.ang[i]) <= FOLLOW_ANG_DEG
        {
            return true;
        }
    }
    false
}

/// True where this block carries a real screen in this ink. Three conditions, all required: a
/// concentrated spectral peak (FIRE), enough modulation to be ink rather than arithmetic (DEPTH),
/// and not merely an echo of a stronger ink at the same geometry (is_follower).
pub fn fired(f: &ScreenField, ci: usize, i: usize) -> bool {
    let a = &f.ink[ci];
    a.prom[i] > FIRE && a.depth[i] > DEPTH && !is_follower(f, ci, i)
}

/// Write the field as one `[4][6][ny][nx]` f32 npy: ink-major, then
/// (prominence, depth, lpi, angle, sub2, sub5).
///
/// This is the whole point of the stage. The field is a few hundred KB where the 2400 dpi planes it
/// came from are gigabytes, so it is the artifact worth caching -- routing and rendering iterate
/// against this and never touch full resolution again.
pub fn write_npy(path: &str, f: &ScreenField) -> Result<()> {
    let n = f.ny * f.nx;
    let mut all = Vec::with_capacity(4 * 6 * n);
    for ink in &f.ink {
        all.extend_from_slice(&ink.prom);
        all.extend_from_slice(&ink.depth);
        all.extend_from_slice(&ink.lpi);
        all.extend_from_slice(&ink.ang);
        all.extend_from_slice(&ink.sub2);
        all.extend_from_slice(&ink.sub5);
    }
    npy::write_f32(path, &all, &[4, 6, f.ny, f.nx])
}

/// Read a field back from the npy this stage wrote. The field is the cacheable artifact -- stages
/// B and C consume it and never re-measure -- so this is the normal way in, not a debug path.
pub fn read_npy(path: &str) -> Result<ScreenField> {
    let (data, shape) = npy::read_f32(path)?;
    if shape.len() != 4 || shape[0] != 4 || shape[1] != 6 {
        anyhow::bail!("{}: expected [4][6][ny][nx], got {:?}", path, shape);
    }
    let (ny, nx) = (shape[2], shape[3]);
    let n = ny * nx;
    let mut ink = Vec::with_capacity(4);
    for ci in 0..4 {
        let b = ci * 6 * n;
        ink.push(InkField {
            prom: data[b..b + n].to_vec(),
            depth: data[b + n..b + 2 * n].to_vec(),
            lpi: data[b + 2 * n..b + 3 * n].to_vec(),
            ang: data[b + 3 * n..b + 4 * n].to_vec(),
            sub2: data[b + 4 * n..b + 5 * n].to_vec(),
            sub5: data[b + 5 * n..b + 6 * n].to_vec(),
        });
    }
    Ok(ScreenField { ny, nx, ink })
}
