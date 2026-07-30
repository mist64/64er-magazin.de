//! The 2400 dpi apply: master scan -> deskewed/cropped A4 page -> graded CMYK.
//!
//! Port of `04-grade/apply_fullres.py`. See `APPLY_PORT.md` for the measured case, the contract
//! change, and -- the part that matters -- the seven places where a naive port silently diverges
//! from the Python. Every one of them is marked SEAM below.
//!
//! ONE affine: the output grid is inverse-mapped straight onto the raw master, so the deskew and
//! the A4 crop cost a single interpolation rather than two.

use crate::imageio::{self, Cmyk, Rgb};
use crate::npy;
use crate::pilio;
use crate::resample::{resample_rgb_channel, Filter};
use anyhow::{Context, Result};
use rayon::prelude::*;
use serde::Deserialize;

// convert.py anchor colours (identical to separate.rs; repeated here because this file must not
// silently inherit a change made for the other caller).
const COLOR_C: [f64; 3] = [38.0, 140.0, 165.0];
const COLOR_CM: [f64; 3] = [36.0, 44.0, 79.0];
const COLOR_CY: [f64; 3] = [42.0, 109.0, 44.0];
const COLOR_M: [f64; 3] = [192.0, 37.0, 66.0];
const COLOR_MY: [f64; 3] = [185.0, 34.0, 31.0];
const COLOR_Y: [f64; 3] = [201.0, 159.0, 61.0];
const COLOR_K: [f64; 3] = [16.0, 17.0, 17.0];
const COLOR_W: [f64; 3] = [201.0, 195.0, 188.0];

/// Tile side for the cached luma statistics. Must stay equal to `mrc.rs::HOP` and to the
/// detector's hop: the cached grid IS the score grid.
const HOP: usize = 60;

/// Grade levels as percentages, per channel. `display` is the canonical deliverable grade
/// (ALL.sh / CLAUDE.md stage 1a); `detect` keeps the shadows (lo=0) because the screening
/// analysis needs tonal range the display grade clips away.
#[derive(Clone, Copy)]
pub struct Levels {
    pub c: (f64, f64),
    pub m: (f64, f64),
    pub y: (f64, f64),
    pub k: (f64, f64),
}
impl Levels {
    pub fn display() -> Self {
        Levels { c: (50.0, 90.0), m: (30.0, 70.0), y: (30.0, 70.0), k: (90.0, 95.0) }
    }
    pub fn detect() -> Self {
        Levels { c: (0.0, 90.0), m: (0.0, 70.0), y: (0.0, 70.0), k: (0.0, 95.0) }
    }
}

#[derive(Deserialize)]
pub struct Geometry {
    pub page: u32,
    pub parity: String,
    pub thumb_size: [f64; 2],
    pub out_size: [usize; 2],
    pub corners_master: [[f64; 2]; 4],
    pub corners_thumb: [[f64; 2]; 4],
}

#[derive(Deserialize)]
struct GeomFile {
    pages: std::collections::HashMap<String, serde_json::Value>,
}

/// The matte/spine/hole parameters, RE-RASTERISED into the output frame rather than upscaled.
pub struct AlphaParams {
    bed_top: Vec<f32>,
    bed_bottom: Vec<f32>,
    bed_left: Vec<f32>,
    bed_right: Vec<f32>,
    spine_inb: Vec<f32>,
    spine_max: f32,
    holes: Vec<u8>, // bit-packed rows, `holes_w` bits per row
    holes_h: usize,
    holes_w: usize,
    holes_stride: usize,
}

impl AlphaParams {
    pub fn load(dir: &str) -> Result<Self> {
        let f = |n: &str| -> Result<Vec<f32>> {
            Ok(npy::read_f32(&format!("{}/{}.npy", dir, n))
                .with_context(|| format!("read {}/{}.npy", dir, n))?
                .0)
        };
        let (holes, hshape) = npy::read_u8(&format!("{}/holes.npy", dir))?;
        // holes_shape is int64 (numpy's default for np.array([H, W])). It must be READ, not
        // inferred: packbits pads the last byte of each row, so the packed width overstates the
        // true column count by up to 7 and every hole lookup would land on the wrong column.
        let (hs, _) = npy::read_i64(&format!("{}/holes_shape.npy", dir))?;
        let holes_h = hs[0] as usize;
        let holes_w = hs[1] as usize;
        let holes_stride = if hshape.len() == 2 { hshape[1] } else { holes.len() / holes_h.max(1) };
        let spine_inb = f("spine_inb")?;
        let spine_max = spine_inb.iter().cloned().fold(f32::MIN, f32::max);
        Ok(AlphaParams {
            bed_top: f("bed_top")?,
            bed_bottom: f("bed_bottom")?,
            bed_left: f("bed_left")?,
            bed_right: f("bed_right")?,
            spine_inb,
            spine_max,
            holes,
            holes_h,
            holes_w,
            holes_stride,
        })
    }

    /// Linear interpolation along a per-scanline profile, clamped at both ends.
    /// SEAM 5b: matches the Python `at()` helper exactly -- clip position, floor, next index
    /// clamped to n-1, weight in f32.
    #[inline]
    fn at(arr: &[f32], pos: f64) -> f32 {
        let n = arr.len();
        if n == 0 {
            return 0.0;
        }
        let i = pos.clamp(0.0, (n - 1) as f64);
        let i0 = i.floor() as usize;
        let i1 = (i0 + 1).min(n - 1);
        let fr = (i - i0 as f64) as f32;
        arr[i0] * (1.0 - fr) + arr[i1] * fr
    }

    #[inline]
    fn hole_at(&self, xt: f64, yt: f64) -> bool {
        if self.holes_h == 0 || self.holes_w == 0 {
            return false;
        }
        // np.clip(np.round(xt), 0, W-1) -- numpy rounds HALF TO EVEN
        let hx = (round_half_even(xt).max(0.0) as usize).min(self.holes_w - 1);
        let hy = (round_half_even(yt).max(0.0) as usize).min(self.holes_h - 1);
        let byte = self.holes[hy * self.holes_stride + hx / 8];
        // numpy packbits is big-endian within the byte
        (byte >> (7 - (hx % 8))) & 1 == 1
    }

    /// UNKNOWN mask for one output pixel, given its position in raw 600 dpi thumb coordinates.
    ///
    /// SEAM 5c: the FAR edges are computed in FLOAT32, not f64. `Ht - 1 - bot` in the Python is a
    /// Python int minus a float32 array, so numpy evaluates the subtraction in float32 and only
    /// the comparison against the float64 `yt` promotes. Doing it in f64 instead moves the
    /// boundary by up to ~2.4e-4 px, which flips exactly the pixels that land inside that window
    /// -- measured on p002 as 14 pixels of the known mask and 9 of the CMYK, all within 13 px of
    /// the right edge. The NEAR edges (`yt < top`, `xt < lef`) are pure comparisons and need no
    /// such care.
    #[inline]
    fn unknown(&self, geo: &Geometry, xt: f64, yt: f64) -> bool {
        let wt1 = (geo.thumb_size[0] as i64 - 1) as f32;
        let ht1 = (geo.thumb_size[1] as i64 - 1) as f32;
        let top = Self::at(&self.bed_top, xt) as f64;
        let bot = Self::at(&self.bed_bottom, xt);
        let lef = Self::at(&self.bed_left, yt) as f64;
        let rig = Self::at(&self.bed_right, yt);
        if yt < top || yt > (ht1 - bot) as f64 || xt < lef || xt > (wt1 - rig) as f64 {
            return true;
        }
        if self.spine_max >= 0.0 {
            let d = Self::at(&self.spine_inb, yt);
            let hit = if geo.parity == "even" { xt > (wt1 - d) as f64 } else { xt < d as f64 };
            if hit {
                return true;
            }
        }
        self.hole_at(xt, yt)
    }
}

/// numpy's `np.round`: half away from zero is WRONG here -- numpy rounds half to even.
#[inline]
fn round_half_even(v: f64) -> f64 {
    let r = v.round();
    if (v - v.trunc()).abs() == 0.5 && (r % 2.0) != 0.0 {
        r - v.signum()
    } else {
        r
    }
}

struct Plane {
    normal: [f64; 3],
    d: f64,
    nnorm: f64,
}
fn plane(p1: [f64; 3], p2: [f64; 3], p3: [f64; 3]) -> Plane {
    let v1 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]];
    let v2 = [p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]];
    let n = [
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    ];
    let d = -(n[0] * p1[0] + n[1] * p1[1] + n[2] * p1[2]);
    let nnorm = (n[0] * n[0] + n[1] * n[1] + n[2] * n[2]).sqrt();
    Plane { normal: n, d, nnorm }
}
#[inline]
fn dist(px: [f64; 3], pl: &Plane) -> f64 {
    (px[0] * pl.normal[0] + px[1] * pl.normal[1] + px[2] * pl.normal[2] + pl.d).abs() / pl.nnorm
}

/// One CMY channel value for a pixel.
/// SEAM 3: the divide is guarded (`max(d1+d2, 1e-12)`) as in the Python; separate.rs has no guard.
/// SEAM 4: `*255.0` is TRUNCATED toward zero (numpy `.astype(uint8)`), not rounded. Do not change.
#[inline]
fn cmy(px: [f64; 3], pa: &Plane, pb: &Plane) -> u8 {
    let d1 = dist(px, pa);
    let d2 = dist(px, pb);
    let g = d1 / (d1 + d2).max(1e-12) * 255.0;
    255u8.wrapping_sub((g as i64).clamp(0, 255) as u8)
}

/// SEAM 2: Python computes `t` in FLOAT32 (`v.astype(np.float32)`), so the port must too --
/// f64 here differs by 1 at boundaries. The rounding rule (`floor(t*255 + 0.5)`) already matched.
/// The SPAN, though, is a Python float: `hi - lo` is evaluated in f64 and only then meets the
/// float32 array, so it is computed in f64 here and narrowed once.
#[inline]
fn level(v: u8, lo: f32, inv_span: f32) -> u8 {
    let t = ((v as f32 - lo) * inv_span).clamp(0.0, 1.0);
    (t * 255.0 + 0.5).floor() as u8
}

/// Output pixel centres -> source coordinates, from the rectangle's four corners.
fn affine(corners: &[[f64; 2]; 4], w_out: usize, h_out: usize) -> ([f64; 2], [f64; 2], [f64; 2]) {
    let tl = corners[0];
    let tr = corners[1];
    let bl = corners[3];
    let ex = [(tr[0] - tl[0]) / w_out as f64, (tr[1] - tl[1]) / w_out as f64];
    let ey = [(bl[0] - tl[0]) / h_out as f64, (bl[1] - tl[1]) / h_out as f64];
    (tl, ex, ey)
}

/// Bilinear sample of the master.
/// SEAM 5: `inside` bounds, the x0/y0 clamp to W-2/H-2, and f32 weights all match the Python.
/// The caller applies `clip(s + 0.5) -> u8` (round-half-up then truncate), also as in the Python.
#[inline]
fn sample(master: &Rgb, xs: f64, ys: f64) -> ([f32; 3], bool) {
    let w = master.w;
    let h = master.h;
    let inside = xs >= 0.0 && xs <= (w - 1) as f64 && ys >= 0.0 && ys <= (h - 1) as f64;
    let x0 = (xs.floor().max(0.0) as usize).min(w - 2);
    let y0 = (ys.floor().max(0.0) as usize).min(h - 2);
    let fx = (xs - x0 as f64) as f32;
    let fy = (ys - y0 as f64) as f32;
    let idx = |x: usize, y: usize| (y * w + x) * 3;
    let (i00, i01, i10, i11) = (idx(x0, y0), idx(x0 + 1, y0), idx(x0, y0 + 1), idx(x0 + 1, y0 + 1));
    let mut out = [0.0f32; 3];
    for c in 0..3 {
        let p00 = master.data[i00 + c] as f32;
        let p01 = master.data[i01 + c] as f32;
        let p10 = master.data[i10 + c] as f32;
        let p11 = master.data[i11 + c] as f32;
        let top = p00 + (p01 - p00) * fx;
        let bot = p10 + (p11 - p10) * fx;
        out[c] = top + (bot - top) * fy;
    }
    (out, inside)
}

pub struct Warped {
    pub rgb: Vec<u8>, // H_out * W_out * 3
    pub unknown: Vec<bool>,
    pub w: usize,
    pub h: usize,
}

/// Step 1: ONE affine -> the deskewed, cropped A4 page plus its unknown mask.
pub fn warp(master: &Rgb, geo: &Geometry, ap: &AlphaParams) -> Warped {
    let (w_out, h_out) = (geo.out_size[0], geo.out_size[1]);
    let (tlm, exm, eym) = affine(&geo.corners_master, w_out, h_out);
    let (tlt, ext, eyt) = affine(&geo.corners_thumb, w_out, h_out);
    let mut rgb = vec![0u8; w_out * h_out * 3];
    let mut unknown = vec![false; w_out * h_out];
    rgb.par_chunks_mut(w_out * 3)
        .zip(unknown.par_chunks_mut(w_out))
        .enumerate()
        .for_each(|(y, (rrow, urow))| {
            let v = y as f64 + 0.5;
            for x in 0..w_out {
                let u = x as f64 + 0.5;
                let xs = tlm[0] + u * exm[0] + v * eym[0];
                let ys = tlm[1] + u * exm[1] + v * eym[1];
                let (s, inside) = sample(master, xs, ys);
                for c in 0..3 {
                    rrow[x * 3 + c] = (s[c] + 0.5).clamp(0.0, 255.0) as u8;
                }
                let xt = tlt[0] + u * ext[0] + v * eyt[0];
                let yt = tlt[1] + u * ext[1] + v * eyt[1];
                urow[x] = !inside || ap.unknown(geo, xt, yt);
            }
        });
    Warped { rgb, unknown, w: w_out, h: h_out }
}

/// SEAM 1: the K normalisation is taken over the KNOWN (non-alpha) pixels, not globally over the
/// image as `separate::separate()` does. Feeding the cropped page to that function would silently
/// produce the `"crop"` candidate instead of `"known"` and shift every K value on the page.
pub fn knorm(rgb: &[u8], unknown: Option<&[bool]>) -> (f64, f64) {
    let n = rgb.len() / 3;
    let (lo, hi) = (0..n)
        .into_par_iter()
        .fold(
            || (f32::MAX, f32::MIN),
            |(lo, hi), i| {
                if let Some(u) = unknown {
                    if u[i] {
                        return (lo, hi);
                    }
                }
                let r = rgb[i * 3] as f32 - COLOR_K[0] as f32;
                let g = rgb[i * 3 + 1] as f32 - COLOR_K[1] as f32;
                let b = rgb[i * 3 + 2] as f32 - COLOR_K[2] as f32;
                let d = (r * r + g * g + b * b).sqrt();
                (lo.min(d), hi.max(d))
            },
        )
        .reduce(|| (f32::MAX, f32::MIN), |a, b| (a.0.min(b.0), a.1.max(b.1)));
    (lo as f64, hi as f64)
}

/// RGB -> graded CMYK, pre-GCR. GCR is applied separately so the caller can keep the un-GCR'd
/// planes for the ICC page without paying for a second separation (they are the same computation
/// up to the GCR block).
pub fn separate_grade(rgb: &[u8], w: usize, h: usize, lv: Levels, dmin: f64, dmax: f64) -> Cmyk {
    let span = (dmax - dmin).max(1e-12);
    let pac = plane(COLOR_C, COLOR_CM, COLOR_CY);
    let pbc = plane(COLOR_M, COLOR_Y, COLOR_W);
    let pam = plane(COLOR_M, COLOR_CM, COLOR_MY);
    let pbm = plane(COLOR_C, COLOR_Y, COLOR_W);
    let pay = plane(COLOR_Y, COLOR_CY, COLOR_MY);
    let pby = plane(COLOR_C, COLOR_M, COLOR_W);
    let lvl = |p: (f64, f64)| -> (f32, f32) {
        let lo = 255.0 * p.0 / 100.0;
        let hi = 255.0 * p.1 / 100.0;
        (lo as f32, (1.0 / (hi - lo)) as f32)
    };
    let (lc, ic) = lvl(lv.c);
    let (lm, im) = lvl(lv.m);
    let (ly, iy) = lvl(lv.y);
    let (lk, ik) = lvl(lv.k);

    let mut out = Cmyk::new(w, h);
    out.c
        .par_chunks_mut(w)
        .zip(out.m.par_chunks_mut(w))
        .zip(out.y.par_chunks_mut(w))
        .zip(out.k.par_chunks_mut(w))
        .zip(rgb.par_chunks(w * 3))
        .for_each(|((((rc, rm), ry), rk), px)| {
            for x in 0..w {
                let p = [px[x * 3] as f64, px[x * 3 + 1] as f64, px[x * 3 + 2] as f64];
                let c = cmy(p, &pac, &pbc);
                let m = cmy(p, &pam, &pbm);
                let y = cmy(p, &pay, &pby);
                // K: distance to COLOR_K, normalised over [dmin,dmax], TRUNCATED, then inverted.
                // SEAM 4: `.astype(np.int64)` truncates toward zero -- matched here by `as i64`.
                let dr = p[0] - COLOR_K[0];
                let dg = p[1] - COLOR_K[1];
                let db = p[2] - COLOR_K[2];
                let d = (dr * dr + dg * dg + db * db).sqrt();
                let kv = (((d - dmin) / span * 255.0) as i64).clamp(0, 255) as u8;
                let k = 255 - kv;
                rc[x] = level(c, lc, ic);
                rm[x] = level(m, lm, im);
                ry[x] = level(y, ly, iy);
                rk[x] = level(k, lk, ik);
            }
        });
    out
}

/// SEAM 6: neutral moved to K and clipped -- same as `grade::gcr_in_place`, repeated here so the
/// apply cannot drift when that one is changed for the standalone `grade` subcommand.
pub fn gcr(img: &mut Cmyk) {
    let Cmyk { c, m, y, k, .. } = img;
    c.par_iter_mut()
        .zip(m.par_iter_mut())
        .zip(y.par_iter_mut())
        .zip(k.par_iter_mut())
        .for_each(|(((cc, mm), yy), kk)| {
            let neu = (*cc).min(*mm).min(*yy);
            *cc -= neu;
            *mm -= neu;
            *yy -= neu;
            *kk = ((*kk as i16 + neu as i16).clamp(0, 255)) as u8;
        });
}

// -------------------------------------------------------------------------------------------
// SEAM 7 -- the fill. `mirror_edges` is the whole inpaint cost; the interior-hole Telea path is
// deliberately NOT ported (see the report / APPLY_PORT.md).
// -------------------------------------------------------------------------------------------

/// Per-row / per-column first and last KNOWN index (or the Python's sentinels when the line has
/// no known pixel at all: first = n, last = -1).
struct Runs {
    rfirst: Vec<i64>,
    rlast: Vec<i64>,
    cfirst: Vec<i64>,
    clast: Vec<i64>,
    rowany: Vec<bool>,
    colany: Vec<bool>,
}

fn runs(known_unknown: &[bool], w: usize, h: usize) -> Runs {
    // `known_unknown[i]` is the UNKNOWN flag; known = !unknown.
    let mut rfirst = vec![w as i64; h];
    let mut rlast = vec![-1i64; h];
    let mut rowany = vec![false; h];
    rfirst
        .par_iter_mut()
        .zip(rlast.par_iter_mut())
        .zip(rowany.par_iter_mut())
        .enumerate()
        .for_each(|(y, ((f, l), a))| {
            let row = &known_unknown[y * w..(y + 1) * w];
            for x in 0..w {
                if !row[x] {
                    *f = x as i64;
                    break;
                }
            }
            for x in (0..w).rev() {
                if !row[x] {
                    *l = x as i64;
                    break;
                }
            }
            *a = *l >= 0;
        });
    let mut cfirst = vec![h as i64; w];
    let mut clast = vec![-1i64; w];
    let mut colany = vec![false; w];
    // column scan: one pass over the page, cheaper than w strided passes
    for y in 0..h {
        let row = &known_unknown[y * w..(y + 1) * w];
        for x in 0..w {
            if !row[x] {
                if cfirst[x] == h as i64 {
                    cfirst[x] = y as i64;
                }
                clast[x] = y as i64;
            }
        }
    }
    for x in 0..w {
        colany[x] = clast[x] >= 0;
    }
    Runs { rfirst, rlast, cfirst, clast, rowany, colany }
}

/// SEAM 7b -- INTERIOR HOLES, by Telea diffusion.
///
/// `mirror_edges` handles the border-reaching unknown runs. What is left are clip-punch holes in
/// the middle of the sheet: 53 components across 18 of 176 pages, each tiny. The Python calls
/// OpenCV's `cv2.inpaint(..., INPAINT_TELEA)` on a small crop around each; here the `inpaint`
/// crate provides Telea (ported from Pyheal).
///
/// This CANNOT be bit-identical to OpenCV -- it is a different implementation of the same
/// algorithm -- and that is accepted deliberately: the pixels being written are INVENTED, so
/// "identical to OpenCV" is a reproducibility property, not a correctness one. The other 158
/// pages remain byte-identical; on these 18 only the hole neighbourhoods differ.
const HOLE_GROW: usize = 3; // px @600: the punch has a torn halo the detected mask misses
const HOLE_PAD: usize = 24; // context around each hole handed to the diffusion
const HOLE_RADIUS: i32 = 4; // Telea's sampling radius, as the Python passes

/// The EDGE BANDS, defined GEOMETRICALLY: the leading/trailing unknown run of every row and
/// column. Deliberately not by connectivity -- a clip hole touching a band is 8-connected to it,
/// so a connectivity test merges the two, the hole then looks like part of the band and is never
/// diffused. That is exactly why p098 and p100 kept visible punch marks.
fn band_mask(unknown: &[bool], w: usize, h: usize) -> Vec<bool> {
    let mut band = vec![false; w * h];
    for y in 0..h {
        let row = &unknown[y * w..(y + 1) * w];
        let first = row.iter().position(|&u| !u);
        let (first, last) = match first {
            Some(f) => (f as i64, (w - 1 - row.iter().rev().position(|&u| !u).unwrap()) as i64),
            None => (w as i64, -1i64),
        };
        for x in 0..w {
            if (x as i64) < first || (x as i64) > last {
                band[y * w + x] = true;
            }
        }
    }
    for x in 0..w {
        let mut cfirst = h as i64;
        let mut clast = -1i64;
        for y in 0..h {
            if !unknown[y * w + x] {
                if cfirst == h as i64 {
                    cfirst = y as i64;
                }
                clast = y as i64;
            }
        }
        for y in 0..h {
            if (y as i64) < cfirst || (y as i64) > clast {
                band[y * w + x] = true;
            }
        }
    }
    for i in 0..w * h {
        band[i] &= unknown[i];
    }
    band
}

/// Diffuse every unknown region that is NOT part of an edge band. Returns the number filled.
pub fn diffuse_holes(rgb: &mut [u8], unknown: &[bool], w: usize, h: usize) -> usize {
    let band = band_mask(unknown, w, h);
    let holes: Vec<bool> = (0..w * h).map(|i| unknown[i] && !band[i]).collect();
    if !holes.iter().any(|&b| b) {
        return 0;
    }
    // grow to catch the torn halo, then clip back to genuinely unknown pixels.
    // The structure is a SQUARE, np.ones((2*grow+1, 2*grow+1)) as the Python passes -- NOT
    // `binary_dilation(.., HOLE_GROW)`, which iterates the 4-neighbour cross and grows a diamond
    // that misses the corners. That difference split one of p130's holes into two components.
    let side = (2 * HOLE_GROW + 1) as i64;
    let grown_raw = crate::ndimage::binary_dilation_box(&holes, w, h, side, side, 1);
    let grown: Vec<bool> = (0..w * h).map(|i| grown_raw[i] && unknown[i]).collect();
    let (lbl, n) = crate::ndimage::label(&grown, w, h);
    if n == 0 {
        return 0;
    }
    let boxes = crate::ndimage::find_objects(&lbl, n, w, h);
    let mut filled = 0usize;
    for k in 1..=n {
        let (y0, y1, x0, x1) = match boxes[k - 1] {
            Some(b) => b,
            None => continue,
        };
        let cy0 = y0.saturating_sub(HOLE_PAD);
        let cy1 = (y1 + HOLE_PAD + 1).min(h);
        let cx0 = x0.saturating_sub(HOLE_PAD);
        let cx1 = (x1 + HOLE_PAD + 1).min(w);
        let (ch, cw) = (cy1 - cy0, cx1 - cx0);
        let mut sub = ndarray::Array3::<u8>::zeros((ch, cw, 3));
        let mut msk = ndarray::Array2::<u8>::zeros((ch, cw));
        for yy in 0..ch {
            for xx in 0..cw {
                let src = (cy0 + yy) * w + (cx0 + xx);
                for c in 0..3 {
                    sub[[yy, xx, c]] = rgb[src * 3 + c];
                }
                // this component only -- neighbouring holes keep their own pass
                if lbl[src] as usize == k {
                    msk[[yy, xx]] = 255;
                }
            }
        }
        if inpaint::telea_inpaint(&mut sub.view_mut(), &msk.view(), HOLE_RADIUS).is_err() {
            continue;
        }
        for yy in 0..ch {
            for xx in 0..cw {
                let dst = (cy0 + yy) * w + (cx0 + xx);
                if lbl[dst] as usize == k {
                    for c in 0..3 {
                        rgb[dst * 3 + c] = sub[[yy, xx, c]];
                    }
                }
            }
        }
        filled += 1;
    }
    filled
}

/// Mirror-fill the border-reaching unknown runs, in place.
///
/// Rows and columns are resolved INDEPENDENTLY from the untouched mask and each unknown pixel
/// takes whichever boundary is nearer -- the Python's `mirror_edges`, minus its three full-page
/// copies (rowf, colf, out): each filled pixel's source index is a closed form of the run, so
/// nothing is materialised.
///
/// Returns the number of DEAD pixels (row and column both entirely unknown) that had to fall
/// back to the nearest-resolved-pixel rule.
pub fn mirror_edges(rgb: &mut Vec<u8>, unknown: &[bool], w: usize, h: usize) -> usize {
    let r = runs(unknown, w, h);
    // trailing-run reflected length per row / column (`m` in _mirror_1d)
    let row_tm: Vec<i64> = (0..h)
        .map(|y| {
            if !r.rowany[y] {
                return 0;
            }
            let k = w as i64 - 1 - r.rlast[y];
            std::cmp::min(k, r.rlast[y] + 1 - r.rfirst[y])
        })
        .collect();
    let col_tm: Vec<i64> = (0..w)
        .map(|x| {
            if !r.colany[x] {
                return 0;
            }
            let k = h as i64 - 1 - r.clast[x];
            std::cmp::min(k, r.clast[x] + 1 - r.cfirst[x])
        })
        .collect();

    let src = rgb.clone(); // ONE copy: every mirrored value must come from the ORIGINAL pixels
    let mut dead: Vec<(usize, usize)> = Vec::new();
    // rows are independent, but the dead list is shared -> collect per row then concatenate
    let deads: Vec<Vec<(usize, usize)>> = rgb
        .par_chunks_mut(w * 3)
        .enumerate()
        .map(|(y, out_row)| {
            let mut dl = Vec::new();
            let (rf, rl) = (r.rfirst[y], r.rlast[y]);
            for x in 0..w {
                if !unknown[y * w + x] {
                    continue;
                }
                let xi = x as i64;
                let drow: i64 = if !r.rowany[y] {
                    1 << 30
                } else if xi < rf {
                    rf - xi
                } else if xi > rl {
                    xi - rl
                } else {
                    0
                };
                let yi = y as i64;
                let (cf, cl) = (r.cfirst[x], r.clast[x]);
                let dcol: i64 = if !r.colany[x] {
                    1 << 30
                } else if yi < cf {
                    cf - yi
                } else if yi > cl {
                    yi - cl
                } else {
                    0
                };
                if r.rowany[y] && drow <= dcol {
                    let sx = if xi < rf {
                        let m = std::cmp::min(rf, rl + 1 - rf);
                        if xi >= rf - m {
                            2 * rf - 1 - xi
                        } else {
                            rf + m - 1
                        }
                    } else if xi > rl {
                        let m = row_tm[y];
                        if xi <= rl + m {
                            2 * rl + 1 - xi
                        } else if m > 0 {
                            rl - m + 1
                        } else {
                            rl
                        }
                    } else {
                        xi
                    };
                    let s = (y * w + sx as usize) * 3;
                    out_row[x * 3] = src[s];
                    out_row[x * 3 + 1] = src[s + 1];
                    out_row[x * 3 + 2] = src[s + 2];
                } else if r.colany[x] && dcol < drow {
                    let sy = if yi < cf {
                        let m = std::cmp::min(cf, cl + 1 - cf);
                        if yi >= cf - m {
                            2 * cf - 1 - yi
                        } else {
                            cf + m - 1
                        }
                    } else if yi > cl {
                        let m = col_tm[x];
                        if yi <= cl + m {
                            2 * cl + 1 - yi
                        } else if m > 0 {
                            cl - m + 1
                        } else {
                            cl
                        }
                    } else {
                        yi
                    };
                    let s = (sy as usize * w + x) * 3;
                    out_row[x * 3] = src[s];
                    out_row[x * 3 + 1] = src[s + 1];
                    out_row[x * 3 + 2] = src[s + 2];
                } else if !r.rowany[y] && !r.colany[x] {
                    dl.push((y, x));
                }
            }
            dl
        })
        .collect();
    for d in deads {
        dead.extend(d);
    }
    if dead.is_empty() {
        return 0;
    }
    // DEAD CORNERS. `dead` is exactly (rows with no known pixel) x (cols with no known pixel), a
    // Cartesian product, so the nearest non-dead pixel is always a pure vertical or pure
    // horizontal exit -- a full EDT is not needed. scipy's tie-break (measured on p006/p062/p017:
    // 13/14/23 tied pixels, all agreeing) is the LEXICOGRAPHICALLY SMALLEST (y, x) feature.
    let bad_row: Vec<bool> = (0..h).map(|y| !r.rowany[y]).collect();
    let bad_col: Vec<bool> = (0..w).map(|x| !r.colany[x]).collect();
    let exit = |mask: &[bool], i: usize| -> (i64, i64) {
        let n = mask.len() as i64;
        let mut j = i as i64;
        while j >= 0 && mask[j as usize] {
            j -= 1;
        }
        let up = if j >= 0 { i as i64 - j } else { i64::MAX / 4 };
        let mut j = i as i64;
        while j < n && mask[j as usize] {
            j += 1;
        }
        let dn = if j < n { j - i as i64 } else { i64::MAX / 4 };
        (up, dn)
    };
    let filled: Vec<(usize, usize, [u8; 3])> = dead
        .par_iter()
        .map(|&(y, x)| {
            let (ru, rd) = exit(&bad_row, y);
            let (cu, cd) = exit(&bad_col, x);
            let dv = ru.min(rd);
            let dh = cu.min(cd);
            // candidates, lexicographically ordered by (y, x)
            let mut best: Option<(i64, i64)> = None;
            let mut consider = |cy: i64, cx: i64, d: i64| {
                if d != dv.min(dh) {
                    return;
                }
                match best {
                    None => best = Some((cy, cx)),
                    Some((by, bx)) => {
                        if (cy, cx) < (by, bx) {
                            best = Some((cy, cx))
                        }
                    }
                }
            };
            consider(y as i64 - ru, x as i64, ru);
            consider(y as i64 + rd, x as i64, rd);
            consider(y as i64, x as i64 - cu, cu);
            consider(y as i64, x as i64 + cd, cd);
            let (fy, fx) = best.unwrap_or((y as i64, x as i64));
            let s = (fy as usize * w + fx as usize) * 3;
            (y, x, [rgb[s], rgb[s + 1], rgb[s + 2]])
        })
        .collect();
    let n_dead = filled.len();
    for (y, x, v) in filled {
        let o = (y * w + x) * 3;
        rgb[o] = v[0];
        rgb[o + 1] = v[1];
        rgb[o + 2] = v[2];
    }
    n_dead
}

// -------------------------------------------------------------------------------------------
// ICC: graded, NOT GCR'd CMYK -> RGB through US Web Coated SWOP -> AdobeRGB1998.
// -------------------------------------------------------------------------------------------

/// The page the MRC renderer draws from, built to ALL.sh's contract. `lcms2` is the library PIL's
/// ImageCms wraps, and the parameters are PIL's defaults: TYPE_CMYK_8 -> TYPE_RGB_8, perceptual
/// intent, no flags.
pub fn icc_page_rgb(cmyk: &Cmyk, profile_dir: &str) -> Result<Vec<u8>> {
    use lcms2::{Intent, PixelFormat, Profile, Transform};
    let inp = Profile::new_file(format!("{}/USWebCoatedSWOP.icc", profile_dir))
        .map_err(|e| anyhow::anyhow!("open SWOP profile: {:?}", e))?;
    let outp = Profile::new_file(format!("{}/AdobeRGB1998.icc", profile_dir))
        .map_err(|e| anyhow::anyhow!("open AdobeRGB profile: {:?}", e))?;
    let t: Transform<[u8; 4], [u8; 3]> = Transform::new(
        &inp,
        PixelFormat::CMYK_8,
        &outp,
        PixelFormat::RGB_8,
        Intent::Perceptual,
    )
    .map_err(|e| anyhow::anyhow!("build ICC transform: {:?}", e))?;
    let n = cmyk.w * cmyk.h;
    let mut out = vec![0u8; n * 3];
    const CHUNK: usize = 1 << 22; // 4 M pixels: 16 MB in, 12 MB out
    let mut src = vec![[0u8; 4]; CHUNK.min(n)];
    let mut dst = vec![[0u8; 3]; CHUNK.min(n)];
    let mut i = 0usize;
    while i < n {
        let m = CHUNK.min(n - i);
        for j in 0..m {
            src[j] = [cmyk.c[i + j], cmyk.m[i + j], cmyk.y[i + j], cmyk.k[i + j]];
        }
        t.transform_pixels(&src[..m], &mut dst[..m]);
        for j in 0..m {
            out[(i + j) * 3] = dst[j][0];
            out[(i + j) * 3 + 1] = dst[j][1];
            out[(i + j) * 3 + 2] = dst[j][2];
        }
        i += m;
    }
    Ok(out)
}

// -------------------------------------------------------------------------------------------
// The option-C cached products: what `mrc` actually eats, instead of a 200 MB page RGB PNG.
// -------------------------------------------------------------------------------------------

/// Per 60x60 tile: mean luma, and the fraction of pixels below 45 / above 235.
///
/// This is the ONLY genuine consumer of 2400 dpi in the renderer, and it does not survive
/// downsampling -- a 4x4 average of halftone dots is mid-grey and crosses neither threshold. It
/// is computed here, at full resolution, exactly as `mrc.rs::luma_tiles` does.
pub fn luma_tiles_2400(rgb: &[u8], w: usize, ny: usize, nx: usize) -> Vec<f32> {
    let mut out = vec![0.0f32; 3 * ny * nx];
    let (tl, rest) = out.split_at_mut(ny * nx);
    let (bk, wh) = rest.split_at_mut(ny * nx);
    tl.par_chunks_mut(nx)
        .zip(bk.par_chunks_mut(nx))
        .zip(wh.par_chunks_mut(nx))
        .enumerate()
        .for_each(|(ty, ((trow, brow), wrow))| {
            for tx in 0..nx {
                let mut sum = 0.0f64;
                let mut blackn = 0u32;
                let mut whiten = 0u32;
                for yy in 0..HOP {
                    let base = ((ty * HOP + yy) * w + tx * HOP) * 3;
                    for xx in 0..HOP {
                        let o = base + xx * 3;
                        // PIL "L": (R*299 + G*587 + B*114) / 1000, integer division
                        let v = (rgb[o] as u32 * 299 + rgb[o + 1] as u32 * 587
                            + rgb[o + 2] as u32 * 114)
                            / 1000;
                        sum += v as f64;
                        if (v as f32) < 45.0 {
                            blackn += 1;
                        }
                        if (v as f32) > 235.0 {
                            whiten += 1;
                        }
                    }
                }
                let cnt = (HOP * HOP) as f64;
                trow[tx] = (sum / cnt) as f32;
                brow[tx] = if (blackn as f64 / cnt) > 0.70 { 1.0 } else { 0.0 };
                wrow[tx] = if (whiten as f64 / cnt) > 0.50 { 1.0 } else { 0.0 };
            }
        });
    out
}

/// 600 dpi RGB from the 2400 dpi page, one channel at a time so the full-res f32 plane
/// (2.2 GB a channel) is never held.
fn rgb600(page: &[u8], w: usize, h: usize, mw: usize, mh: usize, f: Filter) -> Vec<u8> {
    let mut out = vec![0u8; mw * mh * 3];
    for ch in 0..3 {
        let p = resample_rgb_channel(page, ch, w, h, mw, mh, f);
        for i in 0..mw * mh {
            out[i * 3 + ch] = crate::resample::clip8(p[i]);
        }
    }
    out
}

pub struct Opts {
    pub master_dir: String,
    pub geo_json: String,
    pub geo_dir: String,
    pub out_dir: String,
    pub profile_dir: String,
    pub variant_display: bool,
    pub inpaint: bool,
    pub detect_too: bool,
    pub cache: bool,
    pub write: bool,
}

pub fn load_geometry(path: &str, page: u32) -> Result<Geometry> {
    let txt = std::fs::read_to_string(path).with_context(|| format!("read {}", path))?;
    let gf: GeomFile = serde_json::from_str(&txt).context("parse page_geometry.json")?;
    let v = gf
        .pages
        .get(&page.to_string())
        .with_context(|| format!("page {} not in {}", page, path))?;
    let g: Geometry = serde_json::from_value(v.clone()).context("parse page geometry")?;
    Ok(g)
}

/// Read the master scan for a page.
pub fn read_master(dir: &str, page: u32) -> Result<Rgb> {
    imageio::read_rgb_png(&format!("{}/{:03}.png", dir, page))
}

macro_rules! stage {
    ($t:expr, $name:expr, $rep:expr, $body:block) => {{
        let __s = std::time::Instant::now();
        let __r = $body;
        let e = __s.elapsed().as_secs_f64();
        eprintln!("  {:<22} {:6.1}s", $name, e);
        $rep.push(($name.to_string(), (e * 10.0).round() / 10.0));
        let _ = &$t;
        __r
    }};
}

pub fn run(page: u32, o: &Opts) -> Result<serde_json::Value> {
    let t0 = std::time::Instant::now();
    let mut times: Vec<(String, f64)> = Vec::new();
    let geo = load_geometry(&o.geo_json, page)?;
    let ap = AlphaParams::load(&format!("{}/{:03}", o.geo_dir, page))?;
    let (w, h) = (geo.out_size[0], geo.out_size[1]);
    std::fs::create_dir_all(&o.out_dir).ok();

    let master = stage!(t0, "master decode", times, { read_master(&o.master_dir, page)? });
    let mut wp = stage!(t0, "warp + alpha", times, { warp(&master, &geo, &ap) });
    drop(master);
    let (dmin, dmax) = stage!(t0, "knorm", times, { knorm(&wp.rgb, Some(&wp.unknown)) });
    let (cmin, cmax) = knorm(&wp.rgb, None);

    if o.detect_too {
        let mut d = stage!(t0, "separate detect", times, {
            separate_grade(&wp.rgb, w, h, Levels::detect(), dmin, dmax)
        });
        gcr(&mut d);
        if o.write {
            stage!(t0, "write detect tiff", times, {
                pilio::write_cmyk_tiff_raw(
                    &format!("{}/{:03}_cmyk_detect.tif", o.out_dir, page),
                    w,
                    h,
                    [&d.c, &d.m, &d.y, &d.k],
                )?
            });
        }
    }

    let mut n_dead = 0usize;
    let mut n_holes = 0usize;
    if o.inpaint {
        n_dead = stage!(t0, "mirror inpaint", times, {
            mirror_edges(&mut wp.rgb, &wp.unknown, w, h)
        });
        n_holes = stage!(t0, "telea holes", times, {
            diffuse_holes(&mut wp.rgb, &wp.unknown, w, h)
        });
    }

    let lv = if o.variant_display { Levels::display() } else { Levels::detect() };
    let mut cm = stage!(t0, "separate display", times, {
        separate_grade(&wp.rgb, w, h, lv, dmin, dmax)
    });
    drop(wp.rgb);
    let nog = if o.cache { Some(cm.clone_planes()) } else { None };
    stage!(t0, "gcr", times, { gcr(&mut cm) });

    let gcr_ok = cm
        .c
        .par_iter()
        .zip(cm.m.par_iter())
        .zip(cm.y.par_iter())
        .all(|((a, b), c)| (*a).min(*b).min(*c) == 0);
    let means: Vec<f64> = (0..4)
        .map(|i| {
            let ch = cm.channel(i);
            let s: u64 = ch.par_iter().map(|&v| v as u64).sum();
            (s as f64 / ch.len() as f64 * 100.0).round() / 100.0
        })
        .collect();

    if o.write {
        let name = format!(
            "{}/{:03}_cmyk_{}{}.tif",
            o.out_dir,
            page,
            if o.variant_display { "display" } else { "detect" },
            if o.inpaint { "_filled" } else { "" }
        );
        stage!(t0, "write display tiff", times, {
            pilio::write_cmyk_tiff_lzw(&name, w, h, [&cm.c, &cm.m, &cm.y, &cm.k])?
        });
        stage!(t0, "write known png", times, {
            let known: Vec<bool> = wp.unknown.par_iter().map(|&u| !u).collect();
            pilio::write_png_1bit(&format!("{}/{:03}_known.png", o.out_dir, page), w, h, &known)?
        });
    }
    let unknown_pct = {
        let n = wp.unknown.par_iter().filter(|&&u| u).count();
        (100.0 * n as f64 / (w * h) as f64 * 1000.0).round() / 1000.0
    };
    drop(cm);

    if let Some(nog) = nog {
        let pagergb = stage!(t0, "icc transform", times, { icc_page_rgb(&nog, &o.profile_dir)? });
        drop(nog);
        let (ny, nx) = (h / HOP, w / HOP);
        stage!(t0, "tile stats 2400", times, {
            let t = luma_tiles_2400(&pagergb, w, ny, nx);
            npy::write_f32(&format!("{}/{:03}_tiles.npy", o.out_dir, page), &t, &[3, ny, nx])?
        });
        let (mw, mh) = (w / 4, h / 4);
        stage!(t0, "600 lanczos", times, {
            let r = rgb600(&pagergb, w, h, mw, mh, Filter::Lanczos);
            pilio::write_rgb_png_fast(
                &format!("{}/{:03}_rgb600_lanczos.png", o.out_dir, page),
                mw,
                mh,
                &r,
            )?
        });
        stage!(t0, "600 box", times, {
            let r = rgb600(&pagergb, w, h, mw, mh, Filter::Box);
            pilio::write_rgb_png_fast(
                &format!("{}/{:03}_rgb600_box.png", o.out_dir, page),
                mw,
                mh,
                &r,
            )?
        });
        let meta = serde_json::json!({
            "page": page, "w": w, "h": h, "mw": mw, "mh": mh, "ny": ny, "nx": nx, "hop": HOP,
            "lanczos": format!("{:03}_rgb600_lanczos.png", page),
            "box": format!("{:03}_rgb600_box.png", page),
            "tiles": format!("{:03}_tiles.npy", page),
        });
        std::fs::write(
            format!("{}/{:03}_cache.json", o.out_dir, page),
            serde_json::to_string(&meta)?,
        )?;
    }

    Ok(serde_json::json!({
        "page": page,
        "out_size": [w, h],
        "knorm": "known",
        "variant": if o.variant_display { "display" } else { "detect" },
        "k_candidates": {
            "crop": [(cmin * 100.0).round() / 100.0, (cmax * 100.0).round() / 100.0],
            "known": [(dmin * 100.0).round() / 100.0, (dmax * 100.0).round() / 100.0],
        },
        "unknown_pct": unknown_pct,
        "inpaint": o.inpaint,
        "holes_filled": n_holes,
        "dead_px": n_dead,
        "gcr_ok": gcr_ok,
        "mean": {"C": means[0], "M": means[1], "Y": means[2], "K": means[3]},
        "stages": times.iter().map(|(a, b)| serde_json::json!([a, b])).collect::<Vec<_>>(),
        "secs": (t0.elapsed().as_secs_f64() * 10.0).round() / 10.0,
    }))
}
