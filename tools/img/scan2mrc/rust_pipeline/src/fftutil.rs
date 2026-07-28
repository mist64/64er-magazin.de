//! 2D FFT helpers matching numpy fft2/ifft2/fftshift/fftfreq semantics, built on rustfft.

use num_complex::Complex32;
use rustfft::FftPlanner;

/// numpy.fft.fftfreq(n): [0,1,..,(n-1)/2, -(n/2),..,-1]/n  (d=1).
pub fn fftfreq(n: usize) -> Vec<f64> {
    let mut f = vec![0.0f64; n];
    let half = (n - 1) / 2 + 1; // number of non-negative freqs
    for i in 0..half {
        f[i] = i as f64 / n as f64;
    }
    let mut k = -((n / 2) as i64);
    for i in half..n {
        f[i] = k as f64 / n as f64;
        k += 1;
    }
    f
}

/// fftshift indices for length n: move zero-freq to center.
pub fn fftshift_indices(n: usize) -> Vec<usize> {
    let shift = n - n / 2; // np.fftshift shifts by n//2 (so result index = (i + n - n/2) % n source)
    (0..n).map(|i| (i + shift) % n).collect()
}
pub fn ifftshift_indices(n: usize) -> Vec<usize> {
    let shift = n / 2;
    (0..n).map(|i| (i + shift) % n).collect()
}

/// Forward 2D FFT of a real input (h x w), returns complex (h x w) row-major.
pub fn fft2_real(input: &[f32], w: usize, h: usize) -> Vec<Complex32> {
    let mut data: Vec<Complex32> = input.iter().map(|&v| Complex32::new(v, 0.0)).collect();
    fft2_inplace(&mut data, w, h, false);
    data
}

/// Forward/inverse 2D FFT in place on complex data (h x w row-major).
/// inverse=true performs the inverse and divides by (w*h) (matching numpy ifft2 norm).
pub fn fft2_inplace(data: &mut [Complex32], w: usize, h: usize, inverse: bool) {
    let mut planner = FftPlanner::<f32>::new();
    let fft_row = if inverse {
        planner.plan_fft_inverse(w)
    } else {
        planner.plan_fft_forward(w)
    };
    let fft_col = if inverse {
        planner.plan_fft_inverse(h)
    } else {
        planner.plan_fft_forward(h)
    };
    // rows
    for y in 0..h {
        let row = &mut data[y * w..(y + 1) * w];
        fft_row.process(row);
    }
    // cols
    let mut col: Vec<Complex32> = vec![Complex32::new(0.0, 0.0); h];
    for x in 0..w {
        for y in 0..h {
            col[y] = data[y * w + x];
        }
        fft_col.process(&mut col);
        for y in 0..h {
            data[y * w + x] = col[y];
        }
    }
    if inverse {
        let n = (w * h) as f32;
        for v in data.iter_mut() {
            *v /= n;
        }
    }
}

/// 2D fftshift of a complex array (h x w).
pub fn fftshift2(data: &[Complex32], w: usize, h: usize) -> Vec<Complex32> {
    let rx = fftshift_indices(w);
    let ry = fftshift_indices(h);
    let mut out = vec![Complex32::new(0.0, 0.0); w * h];
    for y in 0..h {
        for x in 0..w {
            out[y * w + x] = data[ry[y] * w + rx[x]];
        }
    }
    out
}

/// 2D fftshift applied to an f32 array (e.g. a frequency-domain weight mask).
pub fn fftshift2_f32(data: &[f32], w: usize, h: usize) -> Vec<f32> {
    let rx = fftshift_indices(w);
    let ry = fftshift_indices(h);
    let mut out = vec![0.0f32; w * h];
    for y in 0..h {
        for x in 0..w {
            out[y * w + x] = data[ry[y] * w + rx[x]];
        }
    }
    out
}

/// 2D ifftshift applied to an f32 array.
pub fn ifftshift2_f32(data: &[f32], w: usize, h: usize) -> Vec<f32> {
    let rx = ifftshift_indices(w);
    let ry = ifftshift_indices(h);
    let mut out = vec![0.0f32; w * h];
    for y in 0..h {
        for x in 0..w {
            out[y * w + x] = data[ry[y] * w + rx[x]];
        }
    }
    out
}
