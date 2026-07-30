//! Resampling matching PIL's ImagingResample semantics (BOX, NEAREST, LANCZOS).
//!
//! PIL resamples separably: horizontal pass then vertical pass, each via
//! precomputed filter coefficients over a support window, using the standard
//! `filterscale = max(1, in/out)` and `support * filterscale` window, with the
//! filter sampled at `(x - center + 0.5) / filterscale`. Coefficients are
//! normalized to sum to 1. Output is rounded (round half up via +0.5 floor on
//! the clipped accumulator, matching PIL's `clip8`).
//!
//! Implemented for f32 single-channel planes (the pipeline downsamples channels).
//! NEAREST is implemented separately for masks (must not interpolate).

#[derive(Clone, Copy)]
pub enum Filter {
    Box,
    Nearest,
    Lanczos,
}

fn box_filter(x: f64) -> f64 {
    // PIL BOX: support 0.5, value 1 for |x| < 0.5 else 0 (with x<=-0.5 -> 0, x<0.5 ->1)
    if x > -0.5 && x <= 0.5 {
        1.0
    } else {
        0.0
    }
}
fn box_support() -> f64 {
    0.5
}

fn sinc(x: f64) -> f64 {
    if x == 0.0 {
        1.0
    } else {
        let px = std::f64::consts::PI * x;
        px.sin() / px
    }
}
fn lanczos_filter(x: f64) -> f64 {
    // a = 3
    if -3.0 <= x && x < 3.0 {
        sinc(x) * sinc(x / 3.0)
    } else {
        0.0
    }
}
fn lanczos_support() -> f64 {
    3.0
}

/// Precompute the per-output-pixel coefficient bounds and weights for one axis.
/// Returns (bounds: Vec<(start, n)>, weights: flattened Vec<f64>, ksize).
fn precompute_coeffs(
    in_size: usize,
    out_size: usize,
    filterf: fn(f64) -> f64,
    support0: f64,
) -> (Vec<(usize, usize)>, Vec<f64>, usize) {
    let scale = in_size as f64 / out_size as f64;
    let filterscale = if scale < 1.0 { 1.0 } else { scale };
    let support = support0 * filterscale;
    let ksize = (support.ceil() as usize) * 2 + 1;
    let mut bounds = Vec::with_capacity(out_size);
    let mut weights = vec![0.0f64; out_size * ksize];
    for xx in 0..out_size {
        let center = (xx as f64 + 0.5) * scale;
        let mut ww = 0.0;
        let ss = 1.0 / filterscale;
        // window [center - support, center + support]
        let mut xmin = (center - support + 0.5).floor() as i64;
        if xmin < 0 {
            xmin = 0;
        }
        let mut xmax = (center + support + 0.5).floor() as i64;
        if xmax > in_size as i64 {
            xmax = in_size as i64;
        }
        let xmin = xmin as usize;
        let xmax = xmax as usize;
        let n = xmax - xmin;
        let base = xx * ksize;
        for x in 0..n {
            let w = filterf((x as f64 + xmin as f64 - center + 0.5) * ss);
            weights[base + x] = w;
            ww += w;
        }
        if ww != 0.0 {
            for x in 0..n {
                weights[base + x] /= ww;
            }
        }
        bounds.push((xmin, n));
    }
    (bounds, weights, ksize)
}

/// Resample an f32 plane (in_w x in_h) to (out_w x out_h) with the given PIL filter.
/// Returns f32 values (NOT clipped to 0..255 — caller clips if producing u8).
pub fn resample_plane_f32(
    src: &[f32],
    in_w: usize,
    in_h: usize,
    out_w: usize,
    out_h: usize,
    filter: Filter,
) -> Vec<f32> {
    if let Filter::Nearest = filter {
        return nearest_plane_f32(src, in_w, in_h, out_w, out_h);
    }
    let (ff, sup): (fn(f64) -> f64, f64) = match filter {
        Filter::Box => (box_filter, box_support()),
        Filter::Lanczos => (lanczos_filter, lanczos_support()),
        Filter::Nearest => unreachable!(),
    };
    // Horizontal pass: in_w x in_h -> out_w x in_h
    let (hb, hw, hk) = precompute_coeffs(in_w, out_w, ff, sup);
    let mut tmp = vec![0.0f32; out_w * in_h];
    for yy in 0..in_h {
        let row = &src[yy * in_w..(yy + 1) * in_w];
        for xx in 0..out_w {
            let (xmin, n) = hb[xx];
            let base = xx * hk;
            let mut acc = 0.0f64;
            for x in 0..n {
                acc += row[xmin + x] as f64 * hw[base + x];
            }
            tmp[yy * out_w + xx] = acc as f32;
        }
    }
    // Vertical pass: out_w x in_h -> out_w x out_h
    let (vb, vw, vk) = precompute_coeffs(in_h, out_h, ff, sup);
    let mut out = vec![0.0f32; out_w * out_h];
    for yy in 0..out_h {
        let (ymin, n) = vb[yy];
        let base = yy * vk;
        for xx in 0..out_w {
            let mut acc = 0.0f64;
            for y in 0..n {
                acc += tmp[(ymin + y) * out_w + xx] as f64 * vw[base + y];
            }
            out[yy * out_w + xx] = acc as f32;
        }
    }
    out
}

/// Resample ONE channel of an interleaved 8-bit RGB image without materialising the full-res
/// f32 plane first. Bit-for-bit the same as `resample_plane_f32` over that plane -- the
/// accumulator is f64 either way and `u8 as f32 as f64 == u8 as f64` -- but a 2400 dpi page
/// plane is 2.2 GB and the apply needs six of them.
pub fn resample_rgb_channel(
    src: &[u8],
    ch: usize,
    in_w: usize,
    in_h: usize,
    out_w: usize,
    out_h: usize,
    filter: Filter,
) -> Vec<f32> {
    use rayon::prelude::*;
    let (ff, sup): (fn(f64) -> f64, f64) = match filter {
        Filter::Box => (box_filter, box_support()),
        Filter::Lanczos => (lanczos_filter, lanczos_support()),
        Filter::Nearest => panic!("NEAREST has no coefficient path"),
    };
    let (hb, hw, hk) = precompute_coeffs(in_w, out_w, ff, sup);
    let mut tmp = vec![0.0f32; out_w * in_h];
    tmp.par_chunks_mut(out_w).enumerate().for_each(|(yy, orow)| {
        let row = &src[yy * in_w * 3..(yy + 1) * in_w * 3];
        for xx in 0..out_w {
            let (xmin, n) = hb[xx];
            let base = xx * hk;
            let mut acc = 0.0f64;
            for x in 0..n {
                acc += row[(xmin + x) * 3 + ch] as f64 * hw[base + x];
            }
            orow[xx] = acc as f32;
        }
    });
    let (vb, vw, vk) = precompute_coeffs(in_h, out_h, ff, sup);
    let mut out = vec![0.0f32; out_w * out_h];
    out.par_chunks_mut(out_w).enumerate().for_each(|(yy, orow)| {
        let (ymin, n) = vb[yy];
        let base = yy * vk;
        for xx in 0..out_w {
            let mut acc = 0.0f64;
            for y in 0..n {
                acc += tmp[(ymin + y) * out_w + xx] as f64 * vw[base + y];
            }
            orow[xx] = acc as f32;
        }
    });
    out
}

fn nearest_plane_f32(
    src: &[f32],
    in_w: usize,
    in_h: usize,
    out_w: usize,
    out_h: usize,
) -> Vec<f32> {
    // PIL NEAREST maps output (x,y) -> input floor((x+0.5)*scale)
    let sx = in_w as f64 / out_w as f64;
    let sy = in_h as f64 / out_h as f64;
    let mut out = vec![0.0f32; out_w * out_h];
    for yy in 0..out_h {
        let iy = (((yy as f64 + 0.5) * sy).floor() as usize).min(in_h - 1);
        for xx in 0..out_w {
            let ix = (((xx as f64 + 0.5) * sx).floor() as usize).min(in_w - 1);
            out[yy * out_w + xx] = src[iy * in_w + ix];
        }
    }
    out
}

/// Nearest-neighbour resample of a u8 plane (for masks). Matches PIL NEAREST.
pub fn nearest_plane_u8(
    src: &[u8],
    in_w: usize,
    in_h: usize,
    out_w: usize,
    out_h: usize,
) -> Vec<u8> {
    let sx = in_w as f64 / out_w as f64;
    let sy = in_h as f64 / out_h as f64;
    let mut out = vec![0u8; out_w * out_h];
    for yy in 0..out_h {
        let iy = (((yy as f64 + 0.5) * sy).floor() as usize).min(in_h - 1);
        for xx in 0..out_w {
            let ix = (((xx as f64 + 0.5) * sx).floor() as usize).min(in_w - 1);
            out[yy * out_w + xx] = src[iy * in_w + ix];
        }
    }
    out
}

/// Clip an f32 accumulator to a u8 the way PIL's clip8 does: round to nearest,
/// clamp 0..255. PIL adds 0.5 and truncates after a fixed-point shift; for our
/// float path round-half-up is the closest match.
pub fn clip8(v: f32) -> u8 {
    let r = (v + 0.5).floor();
    if r < 0.0 {
        0
    } else if r > 255.0 {
        255
    } else {
        r as u8
    }
}
