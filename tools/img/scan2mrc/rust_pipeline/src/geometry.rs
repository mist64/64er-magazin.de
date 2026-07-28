//! Stage 2 (geometry variant): measure_screen_geometry.py.
//! Per channel: scan N=512 non-overlapping patches, Hann-windowed FFT, strongest
//! off-axis peak in screen band (pitch 8..30 px), strength = peak/median(band).
//! A patch counts if mean in (25,225) and strength >= 40. >=3 hits => screen, with
//! pitch=median, angle folded mod 90 via circular mean of 4*angle, consistency = |R|.

use crate::fftutil;
use crate::imageio::Cmyk;
use num_complex::Complex32;
use rayon::prelude::*;
use serde::Serialize;

const N: usize = 512;
const PITCH_MIN: f64 = 8.0;
const PITCH_MAX: f64 = 30.0;
const INK_LO: f64 = 25.0;
const INK_HI: f64 = 225.0;
const STR_THR: f64 = 40.0;
const MIN_PATCHES: usize = 3;
const AXIS_EXCL: f64 = 8.0;

#[derive(Serialize)]
#[serde(untagged)]
pub enum ChannelGeom {
    Screen {
        screen: bool,
        pitch_px: f64,
        lpi: f64,
        angle_deg: f64,
        angle_consistency: f64,
        patches: usize,
        median_strength: f64,
        pitch_std: f64,
    },
    NoScreen {
        screen: bool,
        strong_patches: usize,
    },
}

#[derive(Serialize)]
pub struct GeomResult {
    pub file: String,
    pub dpi: f64,
    pub channels: serde_json::Map<String, serde_json::Value>,
}

fn hann(n: usize) -> Vec<f64> {
    (0..n)
        .map(|i| 0.5 - 0.5 * (2.0 * std::f64::consts::PI * i as f64 / (n as f64 - 1.0)).cos())
        .collect()
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}
fn round1(v: f64) -> f64 {
    (v * 10.0).round() / 10.0
}

struct Masks {
    band: Vec<bool>,
    offaxis: Vec<bool>,
    cc: f64,
}

fn build_masks() -> Masks {
    let cc = (N / 2) as f64;
    let mut band = vec![false; N * N];
    let mut offaxis = vec![false; N * N];
    for y in 0..N {
        for x in 0..N {
            let dy = y as f64 - cc;
            let dx = x as f64 - cc;
            let rr = (dy * dy + dx * dx).sqrt();
            let ang = (dy.atan2(dx).to_degrees()).rem_euclid(180.0);
            let in_band = rr >= N as f64 / PITCH_MAX && rr <= N as f64 / PITCH_MIN;
            let near0 = (ang - 0.0).abs().min(180.0 - (ang - 0.0).abs()) < AXIS_EXCL;
            let near90 = (ang - 90.0).abs().min(180.0 - (ang - 90.0).abs()) < AXIS_EXCL;
            band[y * N + x] = in_band;
            offaxis[y * N + x] = in_band && !(near0 || near90);
        }
    }
    Masks { band, offaxis, cc }
}

fn median(mut v: Vec<f64>) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let n = v.len();
    if n == 0 {
        return 0.0;
    }
    if n % 2 == 1 {
        v[n / 2]
    } else {
        (v[n / 2 - 1] + v[n / 2]) / 2.0
    }
}

fn std_dev(v: &[f64]) -> f64 {
    let n = v.len() as f64;
    if n == 0.0 {
        return 0.0;
    }
    let mean = v.iter().sum::<f64>() / n;
    (v.iter().map(|&x| (x - mean) * (x - mean)).sum::<f64>() / n).sqrt()
}

pub fn measure(img: &Cmyk, dpi: f64, file: String) -> GeomResult {
    let masks = build_masks();
    let band_idx: Vec<usize> = (0..N * N).filter(|&i| masks.band[i]).collect();
    let win = hann(N);
    let h = img.h;
    let w = img.w;
    let mut channels = serde_json::Map::new();
    let names = ["C", "M", "Y", "K"];
    for ci in 0..4 {
        let chan = img.channel(ci);
        // patch grid (non-overlapping stride N)
        let mut starts = Vec::new();
        let mut y0 = 0;
        while y0 + N <= h {
            let mut x0 = 0;
            while x0 + N <= w {
                starts.push((y0, x0));
                x0 += N;
            }
            y0 += N;
        }
        let hits: Vec<(f64, f64, f64)> = starts
            .par_iter()
            .filter_map(|&(y0, x0)| {
                // patch mean
                let mut sum = 0.0f64;
                for yy in 0..N {
                    let srow = (y0 + yy) * w + x0;
                    for xx in 0..N {
                        sum += chan[srow + xx] as f64;
                    }
                }
                let m = sum / (N * N) as f64;
                if m < INK_LO || m > INK_HI {
                    return None;
                }
                let mut tile = vec![0.0f32; N * N];
                for yy in 0..N {
                    let srow = (y0 + yy) * w + x0;
                    for xx in 0..N {
                        tile[yy * N + xx] = ((chan[srow + xx] as f64 - m) * win[yy] * win[xx]) as f32;
                    }
                }
                let mut data: Vec<Complex32> =
                    tile.iter().map(|&v| Complex32::new(v, 0.0)).collect();
                fftutil::fft2_inplace(&mut data, N, N, false);
                let shifted = fftutil::fftshift2(&data, N, N);
                // band magnitudes (for median), and offaxis peak
                let mut band_mags: Vec<f64> = Vec::with_capacity(band_idx.len());
                for &bi in &band_idx {
                    band_mags.push(shifted[bi].norm() as f64);
                }
                if band_mags.is_empty() {
                    return None;
                }
                // peak over offaxis
                let mut peak = f64::MIN;
                let mut peak_idx = 0usize;
                for i in 0..N * N {
                    if masks.offaxis[i] {
                        let mag = shifted[i].norm() as f64;
                        if mag > peak {
                            peak = mag;
                            peak_idx = i;
                        }
                    }
                }
                let med = median(band_mags);
                let strength = peak / (med + 1e-6);
                if strength >= STR_THR {
                    let iy = peak_idx / N;
                    let ix = peak_idx % N;
                    let dy = iy as f64 - masks.cc;
                    let dx = ix as f64 - masks.cc;
                    let r = (dy * dy + dx * dx).sqrt();
                    if r > 0.0 {
                        let pitch = N as f64 / r;
                        let angle = dy.atan2(dx).to_degrees().rem_euclid(180.0);
                        return Some((strength, pitch, angle));
                    }
                }
                None
            })
            .collect();

        if hits.len() >= MIN_PATCHES {
            let pit: Vec<f64> = hits.iter().map(|h| h.1).collect();
            let angs: Vec<f64> = hits.iter().map(|h| h.2).collect();
            let strs: Vec<f64> = hits.iter().map(|h| h.0).collect();
            // angle folded mod 90, circular mean of 4*angle
            let mut s = 0.0;
            let mut c = 0.0;
            for &a in &angs {
                let a4 = (a.rem_euclid(90.0) * 4.0).to_radians();
                s += a4.sin();
                c += a4.cos();
            }
            s /= angs.len() as f64;
            c /= angs.len() as f64;
            let mang = (s.atan2(c).to_degrees() / 4.0).rem_euclid(90.0);
            let consist = (s * s + c * c).sqrt();
            let mpitch = median(pit.clone());
            channels.insert(
                names[ci].to_string(),
                serde_json::to_value(ChannelGeom::Screen {
                    screen: true,
                    pitch_px: round2(mpitch),
                    lpi: round1(dpi / mpitch),
                    angle_deg: round1(mang),
                    angle_consistency: round2(consist),
                    patches: hits.len(),
                    median_strength: round1(median(strs)),
                    pitch_std: round2(std_dev(&pit)),
                })
                .unwrap(),
            );
        } else {
            channels.insert(
                names[ci].to_string(),
                serde_json::to_value(ChannelGeom::NoScreen {
                    screen: false,
                    strong_patches: hits.len(),
                })
                .unwrap(),
            );
        }
    }
    GeomResult {
        file,
        dpi,
        channels,
    }
}
