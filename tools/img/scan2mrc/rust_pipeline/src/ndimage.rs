//! scipy.ndimage equivalents, matching scipy's semantics where it matters.
//! All work on row-major bool / f32 buffers of shape (h, w).
//!
//! Connectivity: scipy's DEFAULT structuring element for label/binary_* is the
//! cross (4-connectivity in 2D). We implement the cross structure for those.
//! Border handling: binary morphology treats out-of-bounds as 0 (border_value=0)
//! which is scipy's default for binary_dilation/erosion.

use rayon::prelude::*;

/// 4-connected labelling (scipy.ndimage.label default cross structure).
/// Returns (labels, n) where labels[px] in 0..=n (0 = background).
pub fn label(mask: &[bool], w: usize, h: usize) -> (Vec<u32>, usize) {
    let mut labels = vec![0u32; w * h];
    let mut next: u32 = 0;
    let mut stack: Vec<usize> = Vec::new();
    for start in 0..(w * h) {
        if !mask[start] || labels[start] != 0 {
            continue;
        }
        next += 1;
        labels[start] = next;
        stack.push(start);
        while let Some(p) = stack.pop() {
            let x = p % w;
            let y = p / w;
            // 4-neighbours
            if x > 0 {
                let q = p - 1;
                if mask[q] && labels[q] == 0 {
                    labels[q] = next;
                    stack.push(q);
                }
            }
            if x + 1 < w {
                let q = p + 1;
                if mask[q] && labels[q] == 0 {
                    labels[q] = next;
                    stack.push(q);
                }
            }
            if y > 0 {
                let q = p - w;
                if mask[q] && labels[q] == 0 {
                    labels[q] = next;
                    stack.push(q);
                }
            }
            if y + 1 < h {
                let q = p + w;
                if mask[q] && labels[q] == 0 {
                    labels[q] = next;
                    stack.push(q);
                }
            }
        }
    }
    (labels, next as usize)
}

/// Component sizes (pixel counts) for labels 1..=n.
pub fn component_sizes(labels: &[u32], n: usize) -> Vec<u64> {
    let mut sz = vec![0u64; n + 1];
    for &l in labels {
        if l != 0 {
            sz[l as usize] += 1;
        }
    }
    sz[1..].to_vec()
}

/// Bounding boxes (find_objects). Returns Vec of Option<(y0,y1,x0,x1)> inclusive
/// bounds for labels 1..=n (y1/x1 are the max index, i.e. slice stop = +1).
pub fn find_objects(labels: &[u32], n: usize, w: usize, h: usize) -> Vec<Option<(usize, usize, usize, usize)>> {
    let mut boxes: Vec<Option<(usize, usize, usize, usize)>> = vec![None; n];
    for y in 0..h {
        for x in 0..w {
            let l = labels[y * w + x];
            if l == 0 {
                continue;
            }
            let i = (l - 1) as usize;
            match &mut boxes[i] {
                None => boxes[i] = Some((y, y, x, x)),
                Some((y0, y1, x0, x1)) => {
                    if y < *y0 {
                        *y0 = y;
                    }
                    if y > *y1 {
                        *y1 = y;
                    }
                    if x < *x0 {
                        *x0 = x;
                    }
                    if x > *x1 {
                        *x1 = x;
                    }
                }
            }
        }
    }
    boxes
}

/// binary_propagation: morphological reconstruction of `seed` under `mask` with the
/// default cross (4-conn) structure. Result = pixels in mask reachable from a seed
/// pixel through mask, 4-connected. (scipy.ndimage.binary_propagation default.)
pub fn binary_propagation(seed: &[bool], mask: &[bool], w: usize, h: usize) -> Vec<bool> {
    // scipy semantics: every seed pixel is ON in the output (even if outside the mask);
    // propagation then grows through `mask` from seed pixels that lie in the mask.
    let mut out = vec![false; w * h];
    let mut stack: Vec<usize> = Vec::new();
    for p in 0..(w * h) {
        if seed[p] {
            out[p] = true;
            stack.push(p);
        }
    }
    while let Some(p) = stack.pop() {
        let x = p % w;
        let y = p / w;
        macro_rules! visit {
            ($q:expr) => {{
                let q = $q;
                if mask[q] && !out[q] {
                    out[q] = true;
                    stack.push(q);
                }
            }};
        }
        if x > 0 {
            visit!(p - 1);
        }
        if x + 1 < w {
            visit!(p + 1);
        }
        if y > 0 {
            visit!(p - w);
        }
        if y + 1 < h {
            visit!(p + w);
        }
    }
    out
}

/// binary_fill_holes (default cross structure). Holes = background not connected to
/// the border. Implemented by flood-filling background from the border (4-conn),
/// then everything not reached and not foreground is a hole -> fill.
pub fn binary_fill_holes(mask: &[bool], w: usize, h: usize) -> Vec<bool> {
    let mut outside = vec![false; w * h];
    let mut stack: Vec<usize> = Vec::new();
    let push = |p: usize, outside: &mut Vec<bool>, stack: &mut Vec<usize>| {
        if !mask[p] && !outside[p] {
            outside[p] = true;
            stack.push(p);
        }
    };
    for x in 0..w {
        push(x, &mut outside, &mut stack);
        push((h - 1) * w + x, &mut outside, &mut stack);
    }
    for y in 0..h {
        push(y * w, &mut outside, &mut stack);
        push(y * w + (w - 1), &mut outside, &mut stack);
    }
    while let Some(p) = stack.pop() {
        let x = p % w;
        let y = p / w;
        macro_rules! visit {
            ($q:expr) => {{
                let q = $q;
                if !mask[q] && !outside[q] {
                    outside[q] = true;
                    stack.push(q);
                }
            }};
        }
        if x > 0 {
            visit!(p - 1);
        }
        if x + 1 < w {
            visit!(p + 1);
        }
        if y > 0 {
            visit!(p - w);
        }
        if y + 1 < h {
            visit!(p + w);
        }
    }
    let mut out = vec![false; w * h];
    for p in 0..(w * h) {
        out[p] = mask[p] || !outside[p];
    }
    out
}

/// One iteration of binary dilation with the cross structure, border_value=0.
fn dilate_once(m: &[bool], w: usize, h: usize) -> Vec<bool> {
    let mut out = vec![false; w * h];
    for y in 0..h {
        for x in 0..w {
            let p = y * w + x;
            let v = m[p]
                || (x > 0 && m[p - 1])
                || (x + 1 < w && m[p + 1])
                || (y > 0 && m[p - w])
                || (y + 1 < h && m[p + w]);
            out[p] = v;
        }
    }
    out
}

/// One iteration of binary erosion with the cross structure, border_value=0
/// (out-of-bounds treated as 0 => border pixels needing an OOB neighbour erode away).
fn erode_once(m: &[bool], w: usize, h: usize) -> Vec<bool> {
    let mut out = vec![false; w * h];
    for y in 0..h {
        for x in 0..w {
            let p = y * w + x;
            let v = m[p]
                && (x > 0 && m[p - 1])
                && (x + 1 < w && m[p + 1])
                && (y > 0 && m[p - w])
                && (y + 1 < h && m[p + w]);
            out[p] = v;
        }
    }
    out
}

pub fn binary_dilation(m: &[bool], w: usize, h: usize, iters: usize) -> Vec<bool> {
    let mut cur = m.to_vec();
    for _ in 0..iters {
        cur = dilate_once(&cur, w, h);
    }
    cur
}

pub fn binary_erosion(m: &[bool], w: usize, h: usize, iters: usize) -> Vec<bool> {
    let mut cur = m.to_vec();
    for _ in 0..iters {
        cur = erode_once(&cur, w, h);
    }
    cur
}

pub fn binary_opening(m: &[bool], w: usize, h: usize, iters: usize) -> Vec<bool> {
    let e = binary_erosion(m, w, h, iters);
    binary_dilation(&e, w, h, iters)
}

pub fn binary_closing(m: &[bool], w: usize, h: usize, iters: usize) -> Vec<bool> {
    let d = binary_dilation(m, w, h, iters);
    binary_erosion(&d, w, h, iters)
}

/// One iteration of dilation/erosion/etc. with a full NxN box structure (np.ones((n,n))).
/// scipy uses this for `binary_opening(..., np.ones((2,2)))` in detect_screened.
fn dilate_once_box(m: &[bool], w: usize, h: usize, sh: i64, sw: i64) -> Vec<bool> {
    // structure np.ones((sh,sw)); origin = center (floor((sh)/2)). For even sizes scipy
    // places origin at floor(size/2). We replicate scipy by using offsets [-o0 .. size-1-o0].
    let o0 = sh / 2;
    let o1 = sw / 2;
    let mut out = vec![false; w * h];
    for y in 0..h as i64 {
        for x in 0..w as i64 {
            let mut v = false;
            'outer: for dy in 0..sh {
                for dx in 0..sw {
                    let ny = y + (dy - o0);
                    let nx = x + (dx - o1);
                    if ny >= 0 && ny < h as i64 && nx >= 0 && nx < w as i64 {
                        if m[(ny as usize) * w + nx as usize] {
                            v = true;
                            break 'outer;
                        }
                    }
                }
            }
            out[(y as usize) * w + x as usize] = v;
        }
    }
    out
}

fn erode_once_box(m: &[bool], w: usize, h: usize, sh: i64, sw: i64) -> Vec<bool> {
    let o0 = sh / 2;
    let o1 = sw / 2;
    let mut out = vec![false; w * h];
    for y in 0..h as i64 {
        for x in 0..w as i64 {
            let mut v = true;
            'outer: for dy in 0..sh {
                for dx in 0..sw {
                    let ny = y + (dy - o0);
                    let nx = x + (dx - o1);
                    let inside = ny >= 0 && ny < h as i64 && nx >= 0 && nx < w as i64;
                    if !inside || !m[(ny as usize) * w + nx as usize] {
                        v = false;
                        break 'outer;
                    }
                }
            }
            out[(y as usize) * w + x as usize] = v;
        }
    }
    out
}

/// Dilation with a `np.ones((sh,sw))` structure -- scipy's default when a square structuring
/// element is passed, which is NOT the same as iterating the 4-neighbour cross: the cross grows a
/// DIAMOND and misses the corners.
pub fn binary_dilation_box(m: &[bool], w: usize, h: usize, sh: i64, sw: i64, iters: usize) -> Vec<bool> {
    let mut cur = m.to_vec();
    for _ in 0..iters {
        cur = dilate_once_box(&cur, w, h, sh, sw);
    }
    cur
}

pub fn binary_opening_box(m: &[bool], w: usize, h: usize, sh: i64, sw: i64, iters: usize) -> Vec<bool> {
    let mut cur = m.to_vec();
    for _ in 0..iters {
        cur = erode_once_box(&cur, w, h, sh, sw);
    }
    for _ in 0..iters {
        cur = dilate_once_box(&cur, w, h, sh, sw);
    }
    cur
}

pub fn binary_closing_box(m: &[bool], w: usize, h: usize, sh: i64, sw: i64, iters: usize) -> Vec<bool> {
    let mut cur = m.to_vec();
    for _ in 0..iters {
        cur = dilate_once_box(&cur, w, h, sh, sw);
    }
    for _ in 0..iters {
        cur = erode_once_box(&cur, w, h, sh, sw);
    }
    cur
}

/// uniform_filter (scipy.ndimage.uniform_filter) with reflect mode ('reflect' is scipy
/// default: (d c b a | a b c d | d c b a)). Square window `size`, separable.
pub fn uniform_filter(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let tmp = uniform_1d_rows(a, w, h, size);
    uniform_1d_cols(&tmp, w, h, size)
}

fn reflect_index(i: i64, n: i64) -> i64 {
    // scipy 'reflect' (a a b c | c b a): index reflection without repeating edge.
    // Actually scipy default mode for uniform_filter is 'reflect' = (d c b a|a b c d|d c b a)
    let mut i = i;
    if n == 1 {
        return 0;
    }
    let period = 2 * n;
    i = ((i % period) + period) % period;
    if i >= n {
        i = period - 1 - i;
    }
    i
}

fn uniform_1d_rows(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let mut out = vec![0.0f32; w * h];
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1; // window covers [lo,hi] relative offsets (size of them)
    let inv = 1.0 / size as f32;
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        let row = &a[y * w..(y + 1) * w];
        for x in 0..w {
            let mut acc = 0.0f32;
            for off in lo..=hi {
                let idx = reflect_index(x as i64 + off, w as i64) as usize;
                acc += row[idx];
            }
            orow[x] = acc * inv;
        }
    });
    out
}

fn uniform_1d_cols(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let mut out = vec![0.0f32; w * h];
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let inv = 1.0 / size as f32;
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        for x in 0..w {
            let mut acc = 0.0f32;
            for off in lo..=hi {
                let idy = reflect_index(y as i64 + off, h as i64) as usize;
                acc += a[idy * w + x];
            }
            orow[x] = acc * inv;
        }
    });
    out
}

/// gaussian_filter (scipy.ndimage.gaussian_filter), truncate=4.0, mode='reflect'.
/// Separable. Kernel radius = int(truncate*sigma + 0.5).
pub fn gaussian_filter(a: &[f32], w: usize, h: usize, sigma: f64) -> Vec<f32> {
    let kernel = gaussian_kernel1d(sigma, 4.0);
    let tmp = correlate1d_rows(a, w, h, &kernel);
    correlate1d_cols(&tmp, w, h, &kernel)
}

fn gaussian_kernel1d(sigma: f64, truncate: f64) -> Vec<f32> {
    let radius = (truncate * sigma + 0.5) as i64;
    let radius = radius.max(0);
    let sigma2 = sigma * sigma;
    let mut phi = Vec::with_capacity((2 * radius + 1) as usize);
    for x in -radius..=radius {
        phi.push((-0.5 / sigma2 * (x as f64) * (x as f64)).exp());
    }
    let sum: f64 = phi.iter().sum();
    phi.iter().map(|&v| (v / sum) as f32).collect()
}

fn correlate1d_rows(a: &[f32], w: usize, h: usize, kernel: &[f32]) -> Vec<f32> {
    let radius = (kernel.len() / 2) as i64;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        let row = &a[y * w..(y + 1) * w];
        for x in 0..w {
            let mut acc = 0.0f32;
            for (k, &kv) in kernel.iter().enumerate() {
                let off = k as i64 - radius;
                let idx = reflect_index(x as i64 + off, w as i64) as usize;
                acc += row[idx] * kv;
            }
            orow[x] = acc;
        }
    });
    out
}

fn correlate1d_cols(a: &[f32], w: usize, h: usize, kernel: &[f32]) -> Vec<f32> {
    let radius = (kernel.len() / 2) as i64;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        for x in 0..w {
            let mut acc = 0.0f32;
            for (k, &kv) in kernel.iter().enumerate() {
                let off = k as i64 - radius;
                let idy = reflect_index(y as i64 + off, h as i64) as usize;
                acc += a[idy * w + x] * kv;
            }
            orow[x] = acc;
        }
    });
    out
}

/// median_filter (scipy.ndimage.median_filter), square `size`, mode='reflect'.
/// Not separable; O(size^2) per pixel.
pub fn median_filter(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    if size <= 1 {
        return a.to_vec();
    }
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let mut out = vec![0.0f32; w * h];
    let win = size * size;
    let mid = win / 2;
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        let mut buf: Vec<f32> = Vec::with_capacity(win);
        for x in 0..w {
            buf.clear();
            for oy in lo..=hi {
                let idy = reflect_index(y as i64 + oy, h as i64) as usize;
                for ox in lo..=hi {
                    let idx = reflect_index(x as i64 + ox, w as i64) as usize;
                    buf.push(a[idy * w + idx]);
                }
            }
            buf.sort_by(|p, q| p.partial_cmp(q).unwrap());
            orow[x] = buf[mid];
        }
    });
    out
}

/// maximum_filter (scipy.ndimage.maximum_filter), square `size`, mode='reflect'.
/// Separable (max is separable). origin = 0.
pub fn maximum_filter(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let tmp = max_1d_rows(a, w, h, size);
    max_1d_cols(&tmp, w, h, size)
}

fn max_1d_rows(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        let row = &a[y * w..(y + 1) * w];
        for x in 0..w {
            let mut m = f32::MIN;
            for off in lo..=hi {
                let idx = reflect_index(x as i64 + off, w as i64) as usize;
                if row[idx] > m {
                    m = row[idx];
                }
            }
            orow[x] = m;
        }
    });
    out
}

fn max_1d_cols(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        for x in 0..w {
            let mut m = f32::MIN;
            for off in lo..=hi {
                let idy = reflect_index(y as i64 + off, h as i64) as usize;
                if a[idy * w + x] > m {
                    m = a[idy * w + x];
                }
            }
            orow[x] = m;
        }
    });
    out
}

pub fn minimum_filter(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let tmp = min_1d_rows(a, w, h, size);
    min_1d_cols(&tmp, w, h, size)
}

fn min_1d_rows(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        let row = &a[y * w..(y + 1) * w];
        for x in 0..w {
            let mut m = f32::MAX;
            for off in lo..=hi {
                let idx = reflect_index(x as i64 + off, w as i64) as usize;
                if row[idx] < m {
                    m = row[idx];
                }
            }
            orow[x] = m;
        }
    });
    out
}

fn min_1d_cols(a: &[f32], w: usize, h: usize, size: usize) -> Vec<f32> {
    let half = (size / 2) as i64;
    let lo = -half;
    let hi = lo + size as i64 - 1;
    let mut out = vec![0.0f32; w * h];
    out.par_chunks_mut(w).enumerate().for_each(|(y, orow)| {
        for x in 0..w {
            let mut m = f32::MAX;
            for off in lo..=hi {
                let idy = reflect_index(y as i64 + off, h as i64) as usize;
                if a[idy * w + x] < m {
                    m = a[idy * w + x];
                }
            }
            orow[x] = m;
        }
    });
    out
}

/// Local std via uniform_filter (matches the `_locstd` helper in the Python).
pub fn local_std(a: &[f32], w: usize, h: usize, win: usize) -> Vec<f32> {
    let m = uniform_filter(a, w, h, win);
    let a2: Vec<f32> = a.iter().map(|&v| v * v).collect();
    let m2 = uniform_filter(&a2, w, h, win);
    m.iter()
        .zip(m2.iter())
        .map(|(&mm, &mm2)| {
            let v = mm2 - mm * mm;
            if v < 0.0 {
                0.0
            } else {
                v.sqrt()
            }
        })
        .collect()
}
