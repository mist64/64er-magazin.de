use image::ImageReader;
use nalgebra::DMatrix;
use rayon::prelude::*;
use std::error::Error;
use std::fs::File;
use std::io::BufWriter;
use std::time::Instant;
use tiff::encoder::{colortype, TiffEncoder};

// ============================================================================
// RGB to CMYK conversion constants
// ============================================================================

// *** Early Stammagazin
// const REFS: [[f32; 3]; 8] = [
//     [203.0, 195.0, 191.0], // W - White (paper)
//     [35.0, 140.0, 167.0],  // C - Cyan
//     [194.0, 51.0, 83.0],   // M - Magenta
//     [204.0, 170.0, 72.0],  // Y - Yellow
//     [192.0, 45.0, 42.0],   // R - Red (M+Y)
//     [34.0, 106.0, 51.0],   // G - Green (C+Y)
//     [35.0, 57.0, 94.0],    // B - Blue (C+M)
//     [28.0, 28.0, 26.0],    // K - Black
// ];

// *** SH8601
const REFS: [[f32; 3]; 8] = [
    [214.0, 195.0, 186.0], // W - White (paper)
    [52.0, 127.0, 153.0],  // C - Cyan
    [194.0, 64.0, 87.0],   // M - Magenta
    [220.0, 156.0, 71.0],  // Y - Yellow
    [205.0, 53.0, 46.0],   // R - Red (M+Y)
    [70.0, 105.0, 60.0],   // G - Green (C+Y)
    [43.0, 54.0, 80.0],    // B - Blue (C+M)
    [52.0, 46.0, 45.0],    // K - Black
];

const TARGETS: [[f32; 3]; 7] = [
    [1.0, 0.0, 0.0], // C
    [0.0, 1.0, 0.0], // M
    [0.0, 0.0, 1.0], // Y
    [0.0, 1.0, 1.0], // R = M+Y
    [1.0, 0.0, 1.0], // G = C+Y
    [1.0, 1.0, 0.0], // B = C+M
    [1.0, 1.0, 1.0], // K = C+M+Y
];

// const WHITE: [f32; 3] = [203.0, 195.0, 191.0];
const WHITE: [f32; 3] = REFS[0];
const EPS: f32 = 1e-6;

// Level stretch: [low%, high%] for each CMYK channel
const LEVEL_C: [f32; 2] = [0.15, 0.85];
const LEVEL_M: [f32; 2] = [0.15, 0.85];
const LEVEL_Y: [f32; 2] = [0.15, 0.85];
const LEVEL_K: [f32; 2] = [0.05, 0.80];

// ============================================================================
// RGB to CMYK conversion
// ============================================================================

#[inline(always)]
fn poly_features(r: f32, g: f32, b: f32) -> [f32; 6] {
    let dr = -(r.max(EPS) / WHITE[0]).log10();
    let dg = -(g.max(EPS) / WHITE[1]).log10();
    let db = -(b.max(EPS) / WHITE[2]).log10();
    [dr, dg, db, dr * dg, dr * db, dg * db]
}

fn derive_matrix() -> [f32; 18] {
    let mut design = Vec::with_capacity(7 * 6);
    for i in 1..=7 {
        let [r, g, b] = REFS[i];
        design.extend_from_slice(&poly_features(r, g, b));
    }

    let mut targets = Vec::with_capacity(7 * 3);
    for t in &TARGETS {
        targets.extend_from_slice(t);
    }

    let a = DMatrix::from_row_slice(7, 6, &design);
    let b = DMatrix::from_row_slice(7, 3, &targets);
    let x = a.svd(true, true).solve(&b, 1e-10).expect("SVD solve failed");

    let mut m = [0.0f32; 18];
    for col in 0..3 {
        for row in 0..6 {
            m[col * 6 + row] = x[(row, col)] as f32;
        }
    }
    m
}

// ============================================================================
// Main
// ============================================================================

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <input> <output.tiff>", args[0]);
        std::process::exit(1);
    }

    let input = &args[1];
    let output = &args[2];

    // Load image
    let t0 = Instant::now();
    let mut reader = ImageReader::open(input)?;
    reader.no_limits();
    let img = reader.decode()?.into_rgb8();
    let (width, height) = (img.width() as usize, img.height() as usize);
    eprintln!("Decode: {:?} ({}x{})", t0.elapsed(), width, height);

    // Derive calibration matrix
    let m = derive_matrix();

    // Convert to raw RGB bytes
    let rgb = img.into_raw();

    // Process pixels in parallel
    let t1 = Instant::now();
    let mut cmyk = vec![0u8; width * height * 4];

    cmyk.par_chunks_exact_mut(4)
        .zip(rgb.par_chunks_exact(3))
        .for_each(|(out, inp)| {
            let r = inp[0] as f32;
            let g = inp[1] as f32;
            let b = inp[2] as f32;

            let f = poly_features(r, g, b);

            let c = (f[0] * m[0] + f[1] * m[1] + f[2] * m[2] + f[3] * m[3] + f[4] * m[4] + f[5] * m[5]).clamp(0.0, 1.0);
            let mt = (f[0] * m[6] + f[1] * m[7] + f[2] * m[8] + f[3] * m[9] + f[4] * m[10] + f[5] * m[11]).clamp(0.0, 1.0);
            let y = (f[0] * m[12] + f[1] * m[13] + f[2] * m[14] + f[3] * m[15] + f[4] * m[16] + f[5] * m[17]).clamp(0.0, 1.0);

            let k = c.min(mt).min(y);
            let c_final = c - k;
            let m_final = mt - k;
            let y_final = y - k;

            out[0] = (c_final * 255.0) as u8;
            out[1] = (m_final * 255.0) as u8;
            out[2] = (y_final * 255.0) as u8;
            out[3] = (k * 255.0) as u8;
        });
    eprintln!("Process RGB->CMYK: {:?}", t1.elapsed());

    // Apply per-channel level stretch
    let t_level = Instant::now();
    let levels = [LEVEL_C, LEVEL_M, LEVEL_Y, LEVEL_K];

    cmyk.par_chunks_exact_mut(4).for_each(|pixel| {
        for (i, &[low_pct, high_pct]) in levels.iter().enumerate() {
            let low = low_pct * 255.0;
            let high = high_pct * 255.0;
            let range = high - low;
            let stretched = ((pixel[i] as f32 - low) / range * 255.0).clamp(0.0, 255.0);
            pixel[i] = stretched as u8;
        }
    });
    eprintln!("Level stretch: {:?}", t_level.elapsed());

    // Write CMYK TIFF
    let t2 = Instant::now();
    let file = File::create(output)?;
    let mut writer = BufWriter::new(file);
    let mut encoder = TiffEncoder::new(&mut writer)?;
    let image = encoder.new_image::<colortype::CMYK8>(width as u32, height as u32)?;
    image.write_data(&cmyk)?;
    eprintln!("Write CMYK TIFF: {:?}", t2.elapsed());

    Ok(())
}
