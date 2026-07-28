//! Stage 0: geometric RGB->CMYK separation, reimplementing convert.py.
//!
//! convert.py constants (anchor colours, RGB):
//!   color_c =[ 38,140,165]  color_cm=[ 36, 44, 79]  color_cy=[ 42,109, 44]
//!   color_m =[192, 37, 66]  color_my=[185, 34, 31]  color_y =[201,159, 61]
//!   color_k =[ 16, 17, 17]  color_w =[201,195,188]
//!
//! K  = extract_k(img, color_k): per-pixel Euclidean distance to color_k, normalized to
//!      [0,255] over the *global* min/max of distances, then INVERTED (255-x).
//! C  = extract_cmy(points, [c,cm,cy], [m,y,w])  ; M = extract_cmy([m,cm,my],[c,y,w])
//! Y  = extract_cmy([y,cy,my],[c,m,w])
//!   extract_cmy: plane1 through the first triple, plane2 through the second triple;
//!   ratio = dist1/(dist1+dist2); gray = ratio*255 -> uint8 -> INVERT (255-x).
//! Result merged as a CMYK image (C,M,Y,K). (remove_black / stretch_levels are commented
//! out in convert.py, so they are NOT applied.)

use crate::imageio::{Cmyk, Rgb};

const COLOR_C: [f64; 3] = [38.0, 140.0, 165.0];
const COLOR_CM: [f64; 3] = [36.0, 44.0, 79.0];
const COLOR_CY: [f64; 3] = [42.0, 109.0, 44.0];
const COLOR_M: [f64; 3] = [192.0, 37.0, 66.0];
const COLOR_MY: [f64; 3] = [185.0, 34.0, 31.0];
const COLOR_Y: [f64; 3] = [201.0, 159.0, 61.0];
const COLOR_K: [f64; 3] = [16.0, 17.0, 17.0];
const COLOR_W: [f64; 3] = [201.0, 195.0, 188.0];

fn sub(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
}
fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}
fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}
fn norm(a: [f64; 3]) -> f64 {
    dot(a, a).sqrt()
}

struct Plane {
    normal: [f64; 3],
    d: f64,
    nnorm: f64,
}
fn plane(p1: [f64; 3], p2: [f64; 3], p3: [f64; 3]) -> Plane {
    let v1 = sub(p2, p1);
    let v2 = sub(p3, p1);
    let n = cross(v1, v2);
    let d = -dot(n, p1);
    Plane {
        normal: n,
        d,
        nnorm: norm(n),
    }
}
fn dist_to_plane(pt: [f64; 3], pl: &Plane) -> f64 {
    (dot(pt, pl.normal) + pl.d).abs() / pl.nnorm
}

/// Compute one CMY channel value (pre-invert ratio*255 as uint8) for a pixel.
fn cmy_channel_value(px: [f64; 3], pl1: &Plane, pl2: &Plane) -> u8 {
    let d1 = dist_to_plane(px, pl1);
    let d2 = dist_to_plane(px, pl2);
    let ratio = d1 / (d1 + d2);
    // PIL: (ratio*255).astype(uint8) = truncation toward zero (numpy astype), then invert.
    let g = (ratio * 255.0) as i64; // truncate
    let g = g.clamp(0, 255) as u8;
    255 - g
}

/// Full separation: RGB -> CMYK (matching convert.py exactly).
pub fn separate(rgb: &Rgb) -> Cmyk {
    let n = rgb.w * rgb.h;
    // --- K channel: distance to color_k, normalize over global min/max, invert ---
    let mut kdist = vec![0.0f64; n];
    let mut dmin = f64::MAX;
    let mut dmax = f64::MIN;
    for i in 0..n {
        let r = rgb.data[i * 3] as f64;
        let g = rgb.data[i * 3 + 1] as f64;
        let b = rgb.data[i * 3 + 2] as f64;
        let dx = r - COLOR_K[0];
        let dy = g - COLOR_K[1];
        let dz = b - COLOR_K[2];
        let dd = (dx * dx + dy * dy + dz * dz).sqrt();
        kdist[i] = dd;
        if dd < dmin {
            dmin = dd;
        }
        if dd > dmax {
            dmax = dd;
        }
    }
    let span = (dmax - dmin).max(1e-12);

    // CMY planes
    let c1a = plane(COLOR_C, COLOR_CM, COLOR_CY);
    let c1b = plane(COLOR_M, COLOR_Y, COLOR_W);
    let m1a = plane(COLOR_M, COLOR_CM, COLOR_MY);
    let m1b = plane(COLOR_C, COLOR_Y, COLOR_W);
    let y1a = plane(COLOR_Y, COLOR_CY, COLOR_MY);
    let y1b = plane(COLOR_C, COLOR_M, COLOR_W);

    let mut out = Cmyk::new(rgb.w, rgb.h);
    for i in 0..n {
        let r = rgb.data[i * 3] as f64;
        let g = rgb.data[i * 3 + 1] as f64;
        let b = rgb.data[i * 3 + 2] as f64;
        let px = [r, g, b];
        out.c[i] = cmy_channel_value(px, &c1a, &c1b);
        out.m[i] = cmy_channel_value(px, &m1a, &m1b);
        out.y[i] = cmy_channel_value(px, &y1a, &y1b);
        // K: normalized distance -> uint8 (truncate) -> invert
        let normalized = (kdist[i] - dmin) / span * 255.0;
        let kv = (normalized as i64).clamp(0, 255) as u8;
        out.k[i] = 255 - kv;
    }
    out
}
