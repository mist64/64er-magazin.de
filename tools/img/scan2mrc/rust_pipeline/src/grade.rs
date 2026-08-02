//! Stage 1: per-channel level grading, A4 crop, and GCR.
//!
//! ImageMagick `-level lo%,hi%` on a channel maps input [lo,hi] (as fractions of the
//! quantum range) linearly to [0,255], clamping outside. With default gamma=1:
//!   out = clamp((in - lo)/(hi - lo), 0, 1) * 255
//! Display grade:   C 50,90  M 30,70  Y 30,70  K 90,95
//! Detection grade: C 0,90   M 0,70   Y 0,70   K 0,95   (no shadow clip)
//!
//! GCR (apply_gcr.py): n=min(C,M,Y); C-=n; M-=n; Y-=n; K=clip(K+n,0,255).
//! (Computed in int16 then back to u8, exactly as the Python.)
//!
//! A4 crop (ALL.sh / make_graded_cmyk.sh): crop width cw16 = widths[id]*16, height
//! a4h16 = 1754*16. Even page id -> gravity east (crop from left x=0), odd -> gravity
//! west (crop from x = W - cw16). Then extent to (1240*16 x 1754*16) padding background
//! white. Since cw16 <= a4w16, padding adds white columns on the gravity-opposite side.

use crate::imageio::Cmyk;

/// One IM -level on a u8 value (gamma=1).
fn level(v: u8, lo_pct: f64, hi_pct: f64) -> u8 {
    let lo = 255.0 * lo_pct / 100.0;
    let hi = 255.0 * hi_pct / 100.0;
    let t = ((v as f64 - lo) / (hi - lo)).clamp(0.0, 1.0);
    // IM rounds to nearest.
    (t * 255.0 + 0.5).floor() as u8
}

#[derive(Clone, Copy)]
pub struct GradeLevels {
    pub c: (f64, f64),
    pub m: (f64, f64),
    pub y: (f64, f64),
    pub k: (f64, f64),
}

impl GradeLevels {
    pub fn display() -> Self {
        GradeLevels {
            // C, M and Y share one level pair, which is what makes the grade neutral-preserving.
            //
            // C used to sit at (50, 90) against M and Y at (30, 70). That was a hand-compensation
            // for the raw separation reading C far too high on neutrals -- computed from the anchor
            // constants, a mid grey separates to C 128 / M 78 / Y 62. The separation is now
            // calibrated against its own neutral response (apply.rs::neutral_luts), so the
            // compensation must go with it: keeping both corrects the same error twice and the page
            // swings from mauve to red. Measured on p073's grey printer casing: with calibration
            // alone and C still at (50,90), C clipped to 0.1 and the casing rendered RGB 192/109/116.
            //
            // K keeps its own levels. It is not a colour channel here -- it is the rich-black
            // distance field, and (90, 95) is what turns it into an ink amount at all.
            c: (30.0, 70.0),
            m: (30.0, 70.0),
            y: (30.0, 70.0),
            k: (90.0, 95.0),
        }
    }
    pub fn detect() -> Self {
        GradeLevels {
            c: (0.0, 70.0),
            m: (0.0, 70.0),
            y: (0.0, 70.0),
            k: (0.0, 95.0),
        }
    }
}

pub fn grade_in_place(img: &mut Cmyk, lv: GradeLevels) {
    for v in img.c.iter_mut() {
        *v = level(*v, lv.c.0, lv.c.1);
    }
    for v in img.m.iter_mut() {
        *v = level(*v, lv.m.0, lv.m.1);
    }
    for v in img.y.iter_mut() {
        *v = level(*v, lv.y.0, lv.y.1);
    }
    for v in img.k.iter_mut() {
        *v = level(*v, lv.k.0, lv.k.1);
    }
}

/// GCR / under-colour removal, in place.
pub fn gcr_in_place(img: &mut Cmyk) {
    let n = img.w * img.h;
    for i in 0..n {
        let c = img.c[i] as i16;
        let m = img.m[i] as i16;
        let y = img.y[i] as i16;
        let k = img.k[i] as i16;
        let neu = c.min(m).min(y);
        img.c[i] = (c - neu) as u8;
        img.m[i] = (m - neu) as u8;
        img.y[i] = (y - neu) as u8;
        img.k[i] = (k + neu).clamp(0, 255) as u8;
    }
}

