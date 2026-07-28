//! Stage 2: screened-region detection (detect_screened.py L22-53).
//!
//! For each channel C,M,Y,K: slide a 240px Hann-windowed FFT over a HOP=60 grid
//! (overlapping by anchoring tiles at offsets 0,60,120,180 within each 240 block),
//! score = max/mean of FFT magnitude in the off-axis screen band
//! fr in (0.058, 0.080), excluding +-12 deg of H/V axes. Per-channel score map
//! is finec (4, NY, NX); fine = max over channels.
//!
//! Also produces _cov.npy: descreened CMYK coverage at 600dpi (BOX 2400->600 then
//! a guard-band Hann low-pass tap(80,100) on each raw channel), 4 x (H/4) x (W/4) u8.

use crate::fftutil;
use crate::imageio::Cmyk;
use crate::ndimage;
use crate::resample::{resample_plane_f32, Filter};
use num_complex::Complex32;
use rayon::prelude::*;

const T: usize = 240;

/// Build the off-axis band mask (shifted, i.e. as used on the fftshift'd magnitude),
/// length T*T, row-major (matching np.fft.fftshift of fftfreq grids).
fn band_mask() -> Vec<bool> {
    let freqs = fftfreq_shifted(T);
    let mut mask = vec![false; T * T];
    for iy in 0..T {
        for ix in 0..T {
            let fy = freqs[iy];
            let fx = freqs[ix];
            let fr = (fy * fy + fx * fx).sqrt();
            let mut ang = fy.atan2(fx).to_degrees().rem_euclid(180.0);
            // near(ang,0,12)|near(ang,90,12)
            let near0 = ((ang - 0.0).abs()).min(180.0 - (ang - 0.0).abs()) < 12.0;
            let near90 = ((ang - 90.0).abs()).min(180.0 - (ang - 90.0).abs()) < 12.0;
            let _ = &mut ang;
            mask[iy * T + ix] = fr > 0.058 && fr < 0.080 && !(near0 || near90);
        }
    }
    mask
}

fn fftfreq_shifted(n: usize) -> Vec<f64> {
    let f = fftutil::fftfreq(n);
    let idx = fftutil::fftshift_indices(n);
    (0..n).map(|i| f[idx[i]]).collect()
}

fn hann(n: usize) -> Vec<f32> {
    // np.hanning(n): 0.5 - 0.5*cos(2*pi*i/(n-1))
    (0..n)
        .map(|i| {
            (0.5 - 0.5 * (2.0 * std::f64::consts::PI * i as f64 / (n as f64 - 1.0)).cos()) as f32
        })
        .collect()
}

pub struct DetectResult {
    pub fine: Vec<f32>,    // NY*NX
    pub finec: Vec<f32>,   // 4*NY*NX
    pub ny: usize,
    pub nx: usize,
    pub cov: Vec<u8>,      // 4 * (H/4)*(W/4)
    pub cw: usize,         // W/4
    pub ch4: usize,        // H/4
}

/// Compute the per-tile score for one channel by emulating the exact loop semantics:
/// for oy in {0,60,120,180}, ox in {0,60,120,180}: tile the array a[oy:.., ox:..] into
/// 240x240 blocks, FFT each, score = max/mean in band, scatter into finec at the
/// strided positions, taking the maximum.
fn channel_scores(
    a: &[f32],
    w: usize,
    h: usize,
    hop: usize,
    ny: usize,
    nx: usize,
    band: &[bool],
    hann_win: &[f32],
) -> Vec<f32> {
    let noff = T / hop; // 4
    let mut finec = vec![0.0f32; ny * nx];
    let band_idx: Vec<usize> = (0..T * T).filter(|&i| band[i]).collect();
    for oy in (0..T).step_by(hop) {
        for ox in (0..T).step_by(hop) {
            let nty = (h - oy) / T;
            let ntx = (w - ox) / T;
            if nty == 0 || ntx == 0 {
                continue;
            }
            // Compute scores for all (ty,tx) tiles in parallel.
            let scores: Vec<f32> = (0..nty * ntx)
                .into_par_iter()
                .map(|ti| {
                    let ty = ti / ntx;
                    let tx = ti % ntx;
                    let y0 = oy + ty * T;
                    let x0 = ox + tx * T;
                    // extract tile, subtract mean, apply hann
                    let mut tile = vec![0.0f32; T * T];
                    let mut sum = 0.0f64;
                    for yy in 0..T {
                        let srow = (y0 + yy) * w + x0;
                        for xx in 0..T {
                            let v = a[srow + xx];
                            tile[yy * T + xx] = v;
                            sum += v as f64;
                        }
                    }
                    let mean = (sum / (T * T) as f64) as f32;
                    for yy in 0..T {
                        for xx in 0..T {
                            tile[yy * T + xx] =
                                (tile[yy * T + xx] - mean) * hann_win[yy] * hann_win[xx];
                        }
                    }
                    // FFT2 + fftshift + magnitude in band
                    let mut data: Vec<Complex32> =
                        tile.iter().map(|&v| Complex32::new(v, 0.0)).collect();
                    fftutil::fft2_inplace(&mut data, T, T, false);
                    let shifted = fftutil::fftshift2(&data, T, T);
                    let mut peak = 0.0f32;
                    let mut bsum = 0.0f64;
                    for &bi in &band_idx {
                        let mag = shifted[bi].norm();
                        if mag > peak {
                            peak = mag;
                        }
                        bsum += mag as f64;
                    }
                    let bmean = (bsum / band_idx.len() as f64) as f32 + 1e-6;
                    peak / bmean
                })
                .collect();
            // scatter into finec[oy/hop::noff, ox/hop::noff] with maximum
            let row0 = oy / hop;
            let col0 = ox / hop;
            // sub-array dims
            let sub_h = (ny - row0 + noff - 1) / noff;
            let sub_w = (nx - col0 + noff - 1) / noff;
            let h2 = sub_h.min(nty);
            let w2 = sub_w.min(ntx);
            for ty in 0..h2 {
                for tx in 0..w2 {
                    let gy = row0 + ty * noff;
                    let gx = col0 + tx * noff;
                    if gy < ny && gx < nx {
                        let s = scores[ty * ntx + tx];
                        let cur = &mut finec[gy * nx + gx];
                        if s > *cur {
                            *cur = s;
                        }
                    }
                }
            }
        }
    }
    finec
}

/// Descreen coverage low-pass weight (guard band Hann tap from r0=80 to r1=100 cyc),
/// applied on the fftshift'd spectrum. Returns weight array (mh x mw), shifted layout.
fn cov_weight(mw: usize, mh: usize) -> Vec<f32> {
    let mut w = vec![0.0f32; mw * mh];
    let cy = mh / 2;
    let cx = mw / 2;
    for iy in 0..mh {
        for ix in 0..mw {
            let dy = iy as f64 - cy as f64;
            let dx = ix as f64 - cx as f64;
            let cyf = (dy * dy + dx * dx).sqrt() / mh as f64 * 600.0;
            let mut wf = ((100.0 - cyf) / 20.0).clamp(0.0, 1.0);
            wf = 0.5 - 0.5 * (std::f64::consts::PI * wf).cos();
            if cyf <= 80.0 {
                wf = 1.0;
            }
            if cyf >= 100.0 {
                wf = 0.0;
            }
            w[iy * mw + ix] = wf as f32;
        }
    }
    w
}

/// Apply the descreen low-pass to one channel (BOX-downsampled to mw x mh).
fn descreen_channel(ch: &[f32], mw: usize, mh: usize, weight_shifted: &[f32]) -> Vec<u8> {
    // fft2 -> fftshift -> *weight -> ifftshift -> ifft2 -> real -> clip 0..255
    let mut data = fftutil::fft2_real(ch, mw, mh);
    let shifted = fftutil::fftshift2(&data, mw, mh);
    let mut weighted = vec![Complex32::new(0.0, 0.0); mw * mh];
    for i in 0..mw * mh {
        weighted[i] = shifted[i] * weight_shifted[i];
    }
    // ifftshift
    let rx = fftutil::ifftshift_indices(mw);
    let ry = fftutil::ifftshift_indices(mh);
    for y in 0..mh {
        for x in 0..mw {
            data[y * mw + x] = weighted[ry[y] * mw + rx[x]];
        }
    }
    fftutil::fft2_inplace(&mut data, mw, mh, true);
    data.iter()
        .map(|c| {
            let v = c.re;
            if v < 0.0 {
                0
            } else if v > 255.0 {
                255
            } else {
                v as u8 // numpy clip then astype('uint8') truncates
            }
        })
        .collect()
}

pub fn detect(img: &Cmyk, hop: usize) -> DetectResult {
    let w = img.w;
    let h = img.h;
    let ny = h / hop;
    let nx = w / hop;
    let band = band_mask();
    let hann_win = hann(T);
    let mut finec = vec![0.0f32; 4 * ny * nx];
    for ci in 0..4 {
        let chan: Vec<f32> = img.channel(ci).iter().map(|&v| v as f32).collect();
        let sc = channel_scores(&chan, w, h, hop, ny, nx, &band, &hann_win);
        finec[ci * ny * nx..(ci + 1) * ny * nx].copy_from_slice(&sc);
    }
    // fine = max over channels
    let mut fine = vec![0.0f32; ny * nx];
    for i in 0..ny * nx {
        let mut m = finec[i];
        for ci in 1..4 {
            let v = finec[ci * ny * nx + i];
            if v > m {
                m = v;
            }
        }
        fine[i] = m;
    }
    // coverage
    let mw = w / 4;
    let mh = h / 4;
    let weight = cov_weight(mw, mh);
    let mut cov = vec![0u8; 4 * mw * mh];
    for ci in 0..4 {
        let chan: Vec<f32> = img.channel(ci).iter().map(|&v| v as f32).collect();
        let small = resample_plane_f32(&chan, w, h, mw, mh, Filter::Box);
        let d = descreen_channel(&small, mw, mh, &weight);
        cov[ci * mw * mh..(ci + 1) * mw * mh].copy_from_slice(&d);
    }
    DetectResult {
        fine,
        finec,
        ny,
        nx,
        cov,
        cw: mw,
        ch4: mh,
    }
}

/// Binary mask (fine > thr) opened with 2x2 then closed iters=2 (for the viz PNG;
/// not used by the MRC stage but matches detect_screened.py L55).
pub fn viz_mask(fine: &[f32], ny: usize, nx: usize, thr: f32) -> Vec<bool> {
    let m: Vec<bool> = fine.iter().map(|&v| v > thr).collect();
    let o = ndimage::binary_opening_box(&m, nx, ny, 2, 2, 1);
    ndimage::binary_closing_box(&o, nx, ny, 2, 2, 2)
}
