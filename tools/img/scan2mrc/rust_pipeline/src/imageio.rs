//! Image I/O matching PIL semantics.
//! - CMYK TIFF (raw/uncompressed, as produced by PIL.save(..,'TIFF')) read/write.
//! - PNG read/write (RGB, grayscale, 1-bit) via the `image` crate.
//! PIL CMYK convention: higher value = more ink (NOT inverted). PIL writes CMYK TIFF
//! as 4 samples/pixel, 8 bits each, PHOTOMETRIC=Separated, planar=chunky.

use anyhow::{bail, Context, Result};
use std::fs::File;
use std::io::BufWriter;
use std::path::Path;

/// A planar CMYK image: four channel buffers, each H*W bytes, value 0..255 (ink amount).
pub struct Cmyk {
    pub w: usize,
    pub h: usize,
    pub c: Vec<u8>,
    pub m: Vec<u8>,
    pub y: Vec<u8>,
    pub k: Vec<u8>,
}

impl Cmyk {
    pub fn new(w: usize, h: usize) -> Self {
        Cmyk {
            w,
            h,
            c: vec![0; w * h],
            m: vec![0; w * h],
            y: vec![0; w * h],
            k: vec![0; w * h],
        }
    }
    /// A copy of all four planes. The apply needs the graded-but-NOT-GCR'd CMYK alongside the
    /// GCR'd one (the MRC page is built from the former, the deliverable from the latter). They
    /// are the same computation up to the GCR block, so it copies rather than separating a
    /// 557 MP page a second time.
    pub fn clone_planes(&self) -> Cmyk {
        Cmyk {
            w: self.w,
            h: self.h,
            c: self.c.clone(),
            m: self.m.clone(),
            y: self.y.clone(),
            k: self.k.clone(),
        }
    }
    pub fn channel(&self, i: usize) -> &[u8] {
        match i {
            0 => &self.c,
            1 => &self.m,
            2 => &self.y,
            _ => &self.k,
        }
    }
}

/// Read a (possibly huge) CMYK TIFF written by PIL. Uses the `tiff` crate; falls back to
/// a manual interleaved read for the common uncompressed 4-channel chunky layout.
pub fn read_cmyk_tiff(path: &str) -> Result<Cmyk> {
    let file = File::open(path).with_context(|| format!("open {}", path))?;
    let mut dec = tiff::decoder::Decoder::new(file)
        .context("tiff decode")?
        .with_limits(tiff::decoder::Limits::unlimited());
    let (w, h) = dec.dimensions().context("tiff dims")?;
    let (w, h) = (w as usize, h as usize);
    let img = dec.read_image().context("tiff read_image")?;
    let mut out = Cmyk::new(w, h);
    match img {
        tiff::decoder::DecodingResult::U8(buf) => {
            // chunky CMYKCMYK...
            if buf.len() != w * h * 4 {
                bail!(
                    "unexpected CMYK tiff buffer len {} != {}",
                    buf.len(),
                    w * h * 4
                );
            }
            for px in 0..(w * h) {
                out.c[px] = buf[px * 4];
                out.m[px] = buf[px * 4 + 1];
                out.y[px] = buf[px * 4 + 2];
                out.k[px] = buf[px * 4 + 3];
            }
        }
        _ => bail!("unsupported CMYK tiff sample type (expected U8)"),
    }
    Ok(out)
}

/// Write a CMYK TIFF readable by PIL (uncompressed, chunky, PHOTOMETRIC=Separated).
pub fn write_cmyk_tiff(path: &str, img: &Cmyk) -> Result<()> {
    let file = File::create(path).with_context(|| format!("create {}", path))?;
    let w = BufWriter::new(file);
    let mut enc = tiff::encoder::TiffEncoder::new(w).context("tiff enc")?;
    let mut buf = vec![0u8; img.w * img.h * 4];
    for px in 0..(img.w * img.h) {
        buf[px * 4] = img.c[px];
        buf[px * 4 + 1] = img.m[px];
        buf[px * 4 + 2] = img.y[px];
        buf[px * 4 + 3] = img.k[px];
    }
    // The `tiff` encoder lacks a 4-channel CMYK colortype preset that PIL recognizes as
    // Separated; emit via image_with_params using a custom CMYK colortype.
    use tiff::encoder::colortype::CMYK8;
    let image = enc
        .new_image::<CMYK8>(img.w as u32, img.h as u32)
        .context("tiff new_image cmyk")?;
    image.write_data(&buf).context("tiff write cmyk data")?;
    Ok(())
}

/// An RGB image (interleaved R,G,B bytes).
pub struct Rgb {
    pub w: usize,
    pub h: usize,
    pub data: Vec<u8>, // len = w*h*3
}

pub fn read_rgb_png(path: &str) -> Result<Rgb> {
    use image::ImageReader;
    let mut reader = ImageReader::open(path)
        .with_context(|| format!("open png {}", path))?
        .with_guessed_format()
        .context("guess format")?;
    // Lift the default decode memory limit (large pages exceed it).
    reader.no_limits();
    let dyn_img = reader.decode().with_context(|| format!("decode png {}", path))?;
    let rgb = dyn_img.to_rgb8();
    let (w, h) = (rgb.width() as usize, rgb.height() as usize);
    Ok(Rgb {
        w,
        h,
        data: rgb.into_raw(),
    })
}

pub fn write_rgb_png(path: &str, img: &Rgb) -> Result<()> {
    let buf =
        image::RgbImage::from_raw(img.w as u32, img.h as u32, img.data.clone()).context("rgb buf")?;
    buf.save(Path::new(path)).context("save rgb png")?;
    Ok(())
}

/// Grayscale image (1 byte/pixel).
pub struct Gray {
    pub w: usize,
    pub h: usize,
    pub data: Vec<u8>,
}

pub fn write_gray_png(path: &str, img: &Gray) -> Result<()> {
    let buf = image::GrayImage::from_raw(img.w as u32, img.h as u32, img.data.clone())
        .context("gray buf")?;
    buf.save(Path::new(path)).context("save gray png")?;
    Ok(())
}

/// Write a 1-bit (bilevel) PNG. `bits[px]` true => black (0), false => white (255).
/// PIL's `Image.fromarray(np.where(mask,0,255)).save(png)` produces an 8-bit gray PNG,
/// but jbig2enc accepts 1bpp and 8bpp; we write 8-bit gray to match the Python exactly.
pub fn write_bilevel_as_gray_png(path: &str, w: usize, h: usize, black: &[bool]) -> Result<()> {
    let data: Vec<u8> = black.iter().map(|&b| if b { 0u8 } else { 255u8 }).collect();
    write_gray_png(path, &Gray { w, h, data })
}
