use image::ImageReader;
use nalgebra::DMatrix;
use rayon::prelude::*;
use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter};
use tiff::encoder::{colortype, TiffEncoder};

const EPS: f32 = 1e-6;

const TARGETS: [[f32; 3]; 7] = [
    [1.0, 0.0, 0.0], // C
    [0.0, 1.0, 0.0], // M
    [0.0, 0.0, 1.0], // Y
    [0.0, 1.0, 1.0], // R = M+Y
    [1.0, 0.0, 1.0], // G = C+Y
    [1.0, 1.0, 0.0], // B = C+M
    [1.0, 1.0, 1.0], // K = C+M+Y
];

const EXAMPLE_CONFIG: &str = r#"# Example CMYK profile
#
# Reference colors (RGB values 0-255)
W 205 194 190
C 39 136 165
M 235 82 117
Y 180 141 50
R 195 37 32
G 63 113 57
B 33 41 77
K 26 27 27

# Level stretch (low% high%, 0-100)
LC 15 85
LM 15 85
LY 15 85
LK 30 50
"#;

struct Config {
    refs: [[f32; 3]; 8],
    levels: [[f32; 2]; 4],
}

fn parse_config(path: &str) -> Result<Config, Box<dyn Error>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);

    let mut refs = [[0.0f32; 3]; 8];
    let mut levels = [[0.0f32; 2]; 4];

    for line in reader.lines() {
        let line = line?;
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }

        match parts[0] {
            "W" => refs[0] = parse_rgb(&parts[1..])?,
            "C" => refs[1] = parse_rgb(&parts[1..])?,
            "M" => refs[2] = parse_rgb(&parts[1..])?,
            "Y" => refs[3] = parse_rgb(&parts[1..])?,
            "R" => refs[4] = parse_rgb(&parts[1..])?,
            "G" => refs[5] = parse_rgb(&parts[1..])?,
            "B" => refs[6] = parse_rgb(&parts[1..])?,
            "K" => refs[7] = parse_rgb(&parts[1..])?,
            "LC" => levels[0] = parse_level(&parts[1..])?,
            "LM" => levels[1] = parse_level(&parts[1..])?,
            "LY" => levels[2] = parse_level(&parts[1..])?,
            "LK" => levels[3] = parse_level(&parts[1..])?,
            _ => {}
        }
    }

    Ok(Config { refs, levels })
}

fn parse_rgb(parts: &[&str]) -> Result<[f32; 3], Box<dyn Error>> {
    if parts.len() < 3 {
        return Err("RGB needs 3 values".into());
    }
    Ok([
        parts[0].parse::<f32>()?,
        parts[1].parse::<f32>()?,
        parts[2].parse::<f32>()?,
    ])
}

fn parse_level(parts: &[&str]) -> Result<[f32; 2], Box<dyn Error>> {
    if parts.len() < 2 {
        return Err("Level needs 2 values".into());
    }
    Ok([
        parts[0].parse::<f32>()? / 100.0,
        parts[1].parse::<f32>()? / 100.0,
    ])
}

#[inline(always)]
fn poly_features(r: f32, g: f32, b: f32, white: &[f32; 3]) -> [f32; 6] {
    let dr = -(r.max(EPS) / white[0]).log10();
    let dg = -(g.max(EPS) / white[1]).log10();
    let db = -(b.max(EPS) / white[2]).log10();
    [dr, dg, db, dr * dg, dr * db, dg * db]
}

fn derive_matrix(refs: &[[f32; 3]; 8]) -> [f32; 18] {
    let white = &refs[0];
    let mut design = Vec::with_capacity(7 * 6);
    for i in 1..=7 {
        let [r, g, b] = refs[i];
        design.extend_from_slice(&poly_features(r, g, b, white));
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

fn print_usage(program: &str) {
    eprintln!("Usage: {} [--colors FILE] <input> <output.tiff>", program);
    eprintln!();
    eprintln!("Options:");
    eprintln!("  --colors FILE   Color profile (default: colors.txt)");
    eprintln!();
    eprintln!("Example colors.txt:");
    eprint!("{}", EXAMPLE_CONFIG);
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();

    let mut config_path = String::from("colors.txt");
    let mut positional: Vec<&str> = Vec::new();

    let mut i = 1;
    while i < args.len() {
        if args[i] == "--colors" {
            if i + 1 >= args.len() {
                print_usage(&args[0]);
                std::process::exit(1);
            }
            config_path = args[i + 1].clone();
            i += 2;
        } else if args[i].starts_with('-') {
            eprintln!("Unknown option: {}", args[i]);
            print_usage(&args[0]);
            std::process::exit(1);
        } else {
            positional.push(&args[i]);
            i += 1;
        }
    }

    if positional.len() < 2 {
        print_usage(&args[0]);
        std::process::exit(1);
    }

    let input = positional[0];
    let output = positional[1];

    let config = parse_config(&config_path)?;
    let white = config.refs[0];

    // Load image
    let mut reader = ImageReader::open(input)?;
    reader.no_limits();
    let img = reader.decode()?.into_rgb8();
    let (width, height) = (img.width() as usize, img.height() as usize);

    // Derive calibration matrix
    let m = derive_matrix(&config.refs);

    // Convert to raw RGB bytes
    let rgb = img.into_raw();

    // Process pixels in parallel
    let mut cmyk = vec![0u8; width * height * 4];

    cmyk.par_chunks_exact_mut(4)
        .zip(rgb.par_chunks_exact(3))
        .for_each(|(out, inp)| {
            let r = inp[0] as f32;
            let g = inp[1] as f32;
            let b = inp[2] as f32;

            let f = poly_features(r, g, b, &white);

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

    // Apply per-channel level stretch
    let levels = config.levels;

    cmyk.par_chunks_exact_mut(4).for_each(|pixel| {
        for (i, [low_pct, high_pct]) in levels.iter().enumerate() {
            let low = low_pct * 255.0;
            let high = high_pct * 255.0;
            let range = high - low;
            let stretched = ((pixel[i] as f32 - low) / range * 255.0).clamp(0.0, 255.0);
            pixel[i] = stretched as u8;
        }
    });

    // Write CMYK TIFF
    let file = File::create(output)?;
    let mut writer = BufWriter::new(file);
    let mut encoder = TiffEncoder::new(&mut writer)?;
    let image = encoder.new_image::<colortype::CMYK8>(width as u32, height as u32)?;
    image.write_data(&cmyk)?;

    Ok(())
}
