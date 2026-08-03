//! STAGE D — the MRC PDF. Two layers, both in the press's own colour space.
//!
//!   BACKGROUND   everything screened, as CMYK contone at the rate the screen itself sets
//!                (derived per page, 120-200 dpi). Photographs are drawn from their recovered dot
//!                area; a flat area's interior is SNAPPED to its one measured ink percentage, so a
//!                20% cyan bar really is 20% cyan and carries no residual screen at all.
//!   STENCILS     everything not screened, as a 1-bit mask per ink at 600 dpi, JBIG2-encoded and
//!                painted in that ink. Type and line art, at four times the background's resolution.
//!
//! WHY CMYK AND NOT RGB. The measurement produces per-ink dot area, so writing it as CMYK is the
//! identity -- no conversion, nothing invented. It is also the only way a flat fill can say "50%
//! cyan" instead of "this shade of blue", and the only way a neutral photograph stays neutral
//! instead of picking up the paper's yellow cast. The archival master is CMYK; a delivery tier that
//! wants RGB converts once, here, at the point of writing.
//!
//! OVERPRINT IS REQUIRED TO VIEW THIS FILE CORRECTLY, and that is a real constraint, not a detail.
//! Each stencil is a /Separation colourant painted with /OP /op true, so the layers add on the plate
//! the way ink does instead of the later one replacing the earlier. Without it, red type -- M and Y
//! together -- renders as pure yellow, measured on p007 at RGB (252, 201, 24) against (238, 35, 52)
//! with overprint honoured.
//!
//! Ghostscript needs `-dOverprint=/simulate` (it ignores overprint by default on RGB devices);
//! Acrobat needs Overprint Preview; a press RIP does it natively. For the ARCHIVAL master this is
//! the correct and honest representation -- it is what the press physically did. A DELIVERY tier
//! that must look right in any viewer should be flattened to composite CMYK or RGB at that point,
//! which is exactly the two-tier split CLAUDE.md already specifies. Do not "fix" this by going back
//! to opaque layers: that silently discards one of two overlapping inks.
//!
//! WHAT THIS DOES NOT DO YET, deliberately. A flat area is snapped inside the background raster
//! rather than emitted as a vector fill, and type is JBIG2 rather than vector glyphs. Both are exact
//! in VALUE at the stated resolution, which is what was asked for; both are resolution-independence
//! increments for later, and neither changes this file's interface.

use crate::demod::{Contone, STENCIL_DPI};
use crate::route::{Class, Routing};
use crate::screen;
use crate::{ndimage, pilio};
use anyhow::{Context, Result};
use std::io::Write;
use std::process::Command;

// ================================================================================================
//  CONSTANTS
// ================================================================================================

/// Flate compression level for the background. 9: the background is the only large raster in the
/// file and it is written once, so the slowest setting is free in practice.
const FLATE_LEVEL: u32 = 9;

/// Paper: no ink at all -- not "white sampled from the scan". Storing the scan's idea of white is
/// how a page acquires a grey cast and pays bytes for it.
const PAPER: [u8; 4] = [0, 0, 0, 0];

/// Total ink (C+M+Y+K, 0-1020) at or above which a contone pixel outside every area is still drawn.
///
/// NOTHING MAY FALL BETWEEN THE TWO LAYERS. A pixel outside an area is normally paper, because the
/// stencil draws whatever is there. But the stencil needs one ink to OWN the mark (half the
/// strongest), and in a photograph's brown mid-tone all four inks sit at similar levels so none
/// qualifies -- while the block, being solid rather than screened, joined no area either. The result
/// was a white staircase on the block grid straight through p007's Spindizzy photograph: ink on the
/// paper, drawn by neither layer. So the background covers everything the stencil does not.
const ORPHAN_INK: u32 = 24;

/// How far a contone pixel may sit from its area's measured flat percentage and still be snapped to
/// it. Twice the spread that defined the area as flat in the first place, so the interior snaps
/// while a genuine edge -- which departs by far more -- does not.
const SNAP_TOL: f32 = 2.0 * crate::route::UNIFORM_STD;

/// Ink colours for the stencil layers, in DeviceCMYK. Exact, not approximated through RGB.
const INK_CMYK: [[f64; 4]; 4] = [
    [1.0, 0.0, 0.0, 0.0], // C
    [0.0, 1.0, 0.0, 0.0], // M
    [0.0, 0.0, 1.0, 0.0], // Y
    [0.0, 0.0, 0.0, 1.0], // K
];
const INK_NAME: [&str; 4] = ["C", "M", "Y", "K"];
/// Standard PDF separation colourant names, so a RIP recognises these as the process inks.
const INK_SEP: [&str; 4] = ["Cyan", "Magenta", "Yellow", "Black"];

// ================================================================================================

/// Build the background: contone where an area is screened and varying, the measured flat colour
/// where it is uniform, paper everywhere else.
fn background(tone: &Contone, r: &Routing) -> Vec<u8> {
    // stencil coverage sampled onto the contone grid: true where the 1-bit layers already draw
    let sdiv_y = (r.sh as f64 / tone.h as f64).max(1.0);
    let sdiv_x = (r.sw as f64 / tone.w as f64).max(1.0);
    let (w, h) = (tone.w, tone.h);
    let mut bg = vec![0u8; w * h * 4];
    // block index for a contone pixel
    let ty_per = (screen::SRC_DPI / tone.dpi).round() as usize;
    for y in 0..h {
        for x in 0..w {
            let (sy, sx) = (y * ty_per, x * ty_per);
            let by = sy.saturating_sub(screen::WIN / 2) / screen::STEP;
            let bx = sx.saturating_sub(screen::WIN / 2) / screen::STEP;
            let bi = by.min(r.ny - 1) * r.nx + bx.min(r.nx - 1);
            // membership at PIXEL scale, not block scale: a region's boundary is placed by coherence
            // at 600 dpi rather than quantised to the 1.35 mm block grid
            let l = {
                let cy = ((y as f64 * sdiv_y) as usize).min(r.sh - 1);
                let cx = ((x as f64 * sdiv_x) as usize).min(r.sw - 1);
                if r.pix[cy * r.sw + cx] { r.label[bi] } else { 0 }
            };
            let px = &mut bg[(y * w + x) * 4..(y * w + x) * 4 + 4];
            // does the stencil already draw here?
            let covered = {
                let cy0 = (y as f64 * sdiv_y) as usize;
                let cx0 = (x as f64 * sdiv_x) as usize;
                let cy1 = (((y + 1) as f64 * sdiv_y) as usize).min(r.sh).max(cy0 + 1);
                let cx1 = (((x + 1) as f64 * sdiv_x) as usize).min(r.sw).max(cx0 + 1);
                let mut hit = false;
                'cov: for cy in cy0..cy1.min(r.sh) {
                    for cx in cx0..cx1.min(r.sw) {
                        if (0..4).any(|ci| r.stencil[ci][cy * r.sw + cx]) {
                            hit = true;
                            break 'cov;
                        }
                    }
                }
                hit
            };
            if l == 0 {
                // Outside every area: paper, UNLESS there is ink here that no stencil draws AND
                // this block actually carries a screen.
                //
                // The fired test is the important half. Without it the orphan path fires on ordinary
                // text on bare paper wherever the stencil's footprint test disagrees with it by a
                // pixel, and the background then paints a faint ghost of those glyphs under the
                // crisp stencil copy -- p007 showed "r. Das er" in outline, and nothing else on the
                // line. On bare paper the stencil is the only layer and the background has no
                // business drawing anything; the orphan case is ink in a SCREENED block that no
                // stencil claimed, which is what this was written for.
                let total: u32 = (0..4).map(|ci| tone.ink[ci][y * w + x] as u32).sum();
                if total < ORPHAN_INK || covered || !r.fired[bi] {
                    px.copy_from_slice(&PAPER);
                } else {
                    for ci in 0..4 {
                        px[ci] = tone.ink[ci][y * w + x];
                    }
                }
                continue;
            }
            let a = &r.areas[(l - 1) as usize];
            // A FLAT AREA IS SNAPPED PER PIXEL, NOT PAINTED PER REGION.
            //
            // The obvious implementation -- fill the whole area with its measured colour -- puts a
            // staircase along every tint-bar edge, because areas are quantised to the 128 px block
            // grid and that is 1.35 mm on paper. So instead: where the contone already agrees with
            // the measured percentage, replace it with exactly that percentage; where it does not,
            // this is an edge or something drawn on top, and the contone is left alone. The interior
            // becomes exact (no residual screen ripple at all) and the boundary keeps its true shape
            // at the contone's own resolution.
            // ...and UNDER a glyph on a tint, the background is the TINT, not a blurred copy of the
            // glyph. The contone is a box average over a screen cell, so it includes whatever is
            // printed on top; leaving it there draws every letter twice -- once soft at 160 dpi and
            // once crisp at 600 -- and the soft copy shows as a halo around the sharp one. The old
            // renderer met the same problem and answered it with a text inpaint that painted
            // unsupported background BLACK and welded letter counters shut on 166 of 176 pages
            // (FINDINGS.md 4). For a flat area the answer needs no invention at all: the value under
            // the glyph is the measured tint percentage.
            let flat = a.class == Class::Flat;
            for ci in 0..4 {
                let v = tone.ink[ci][y * w + x];
                px[ci] = if flat && (covered || (v as f32 - a.mean[ci]).abs() <= SNAP_TOL) {
                    a.mean[ci].round().clamp(0.0, 255.0) as u8
                } else {
                    v
                };
            }
        }
    }
    bg
}

/// Shell out to jbig2enc for one stencil. Generic (`-p`), not symbol-mode: symbol mode is a text
/// optimisation and these masks include rules and line art.
fn jbig2(work: &str, name: &str, mask: &[bool], w: usize, h: usize) -> Result<Vec<u8>> {
    let png = format!("{}/{}.png", work, name);
    // POLARITY. `write_png_1bit` sets bit 1 where the slice is true, and in a 1-bit greyscale PNG
    // 1 is WHITE. jbig2enc takes black as the foreground, and a PDF ImageMask with Decode [0 1]
    // paints where the sample is 0. So the mask must be inverted on the way out: ink -> 0 -> black
    // -> foreground -> painted. Passing it straight through inverts the entire page, painting the
    // paper and knocking the type out of it.
    let ink_is_black: Vec<bool> = mask.iter().map(|&b| !b).collect();
    pilio::write_png_1bit(&png, w, h, &ink_is_black)?;
    let out = Command::new("jbig2")
        .args(["-p", &png])
        .output()
        .context("run jbig2 (is jbig2enc installed?)")?;
    if !out.status.success() {
        anyhow::bail!("jbig2 failed: {}", String::from_utf8_lossy(&out.stderr));
    }
    let _ = std::fs::remove_file(&png);
    Ok(out.stdout)
}

fn deflate(data: &[u8]) -> Result<Vec<u8>> {
    use flate2::write::ZlibEncoder;
    use flate2::Compression;
    let mut e = ZlibEncoder::new(Vec::new(), Compression::new(FLATE_LEVEL));
    e.write_all(data)?;
    Ok(e.finish()?)
}

pub struct Sizes {
    pub bg: usize,
    pub ink: [usize; 4],
    pub total: usize,
}

/// Render one page to an MRC PDF.
///
/// `src_w`/`src_h` are the 2400 dpi page dimensions, which set the physical page size -- the layers
/// are at different resolutions and each is scaled to the same sheet.
pub fn write_pdf(
    path: &str,
    src_w: usize,
    src_h: usize,
    tone: &Contone,
    r: &Routing,
    work: &str,
) -> Result<Sizes> {
    std::fs::create_dir_all(work)?;
    let pw = src_w as f64 / screen::SRC_DPI * 72.0;
    let ph = src_h as f64 / screen::SRC_DPI * 72.0;

    let raw_bg = background(tone, r);
    // THE BACKGROUND, AS A PICTURE. Written beside the PDF because when something is wrong in the
    // output the first question is always "which layer drew this", and answering it by reasoning
    // about the content stream has cost several rounds. Cheap: one PNG of an already-computed
    // buffer.
    {
        let mut px = vec![0u8; tone.w * tone.h * 3];
        for i in 0..tone.w * tone.h {
            let (c, m, y, k) = (
                raw_bg[i * 4] as f32,
                raw_bg[i * 4 + 1] as f32,
                raw_bg[i * 4 + 2] as f32,
                raw_bg[i * 4 + 3] as f32,
            );
            let f = |v: f32| ((1.0 - v / 255.0) * (1.0 - k / 255.0) * 255.0).clamp(0.0, 255.0) as u8;
            px[i * 3] = f(c);
            px[i * 3 + 1] = f(m);
            px[i * 3 + 2] = f(y);
        }
        let p = path.strip_suffix(".pdf").unwrap_or(path);
        pilio::write_rgb_png_fast(&format!("{}_bg.png", p), tone.w, tone.h, &px)?;
    }
    // AND THE STENCIL, as a picture, for the same reason. Between them these two files answer
    // "which layer drew this" directly, which is the question every render defect starts with and
    // the one that has cost the most rounds of guessing.
    {
        let mut px = vec![255u8; r.sw * r.sh * 3];
        for i in 0..r.sw * r.sh {
            for ci in 0..4 {
                if r.stencil[ci][i] {
                    let c = INK_CMYK[ci];
                    px[i * 3] = ((1.0 - c[0]) * (1.0 - c[3]) * 255.0) as u8;
                    px[i * 3 + 1] = ((1.0 - c[1]) * (1.0 - c[3]) * 255.0) as u8;
                    px[i * 3 + 2] = ((1.0 - c[2]) * (1.0 - c[3]) * 255.0) as u8;
                }
            }
        }
        let p = path.strip_suffix(".pdf").unwrap_or(path);
        pilio::write_rgb_png_fast(&format!("{}_stencil.png", p), r.sw, r.sh, &px)?;
    }
    let bg = deflate(&raw_bg)?;

    // Stencils, in draw order: the chromatic inks first, K last, so black type lands on top of any
    // colour it overlaps rather than under it.
    let mut layers: Vec<(usize, Vec<u8>)> = Vec::new();
    for ci in [0usize, 1, 2, 3] {
        let mut m = r.stencil[ci].clone();
        if m.iter().all(|&b| !b) {
            continue;
        }
        // ISOLATED PIXELS ONLY. A pixel with no set 8-neighbour cannot be part of any stroke -- it
        // is a lone 42 micron speck, which no press could lay down. This is provably incapable of
        // deleting a connected mark, which is the property the old MIN_K/MIN_CC despeckles lacked
        // when they removed periods and umlaut dots by AREA (FINDINGS.md 4).
        //
        // It is worth doing because JBIG2 pays dearly for isolated pixels: without it the C and M
        // stencils on p007 are 162K and 165K against 18K and 36K, i.e. a quarter of a megabyte per
        // page of scanner grit.
        {
            let src = m.clone();
            for y in 0..r.sh {
                for x in 0..r.sw {
                    let i = y * r.sw + x;
                    if !src[i] {
                        continue;
                    }
                    let mut n = 0;
                    for dy in -1i64..=1 {
                        for dx in -1i64..=1 {
                            if dy == 0 && dx == 0 {
                                continue;
                            }
                            let (yy, xx) = (y as i64 + dy, x as i64 + dx);
                            if yy < 0 || xx < 0 || yy >= r.sh as i64 || xx >= r.sw as i64 {
                                continue;
                            }
                            if src[yy as usize * r.sw + xx as usize] {
                                n += 1;
                            }
                        }
                    }
                    if n == 0 {
                        m[i] = false;
                    }
                }
            }
        }

        // NO MORPHOLOGICAL OPENING. One was tried here and removed: `ndimage`'s structuring element is
        // the 4-neighbour CROSS, so a pixel survives only if a plus fits inside the mask -- and no
        // plus fits inside a 1 or 2 px line at any orientation. It therefore erases hairline rules,
        // thin serifs and the tail of a comma ENTIRELY rather than thinning them, which is exactly
        // the content loss FINDINGS.md 4 records for the old MIN_K/MIN_CC despeckles. If scanner
        // noise ever needs removing it must be done by a filter that cannot delete a connected
        // stroke, and it must be measured against the text before it ships.
        layers.push((ci, jbig2(work, INK_NAME[ci], &m, r.sw, r.sh)?));
    }

    // ---- assemble ----------------------------------------------------------------------------
    // object plan: 1 catalog, 2 pages, 3 page, 4 background, 5.. stencils, then content
    let bg_obj = 4;
    let ink_start = 5;
    let content_obj = ink_start + layers.len();

    // EACH LAYER IS SCALED TO ITS OWN TRUE EXTENT. The background covers tone.w*div source pixels
    // and the stencils sw*4, and neither is exactly the page: 1322*15 = 19830 against 4960*4 = 19840
    // for a 19843 px page. Stretching both to the full sheet drifts them ~10 source px apart at the
    // right edge, which is a registration error between the contone and the type sitting on it.
    let bg_div = (screen::SRC_DPI / tone.dpi).round() as usize;
    let bgw = pw * (tone.w * bg_div) as f64 / src_w as f64;
    let bgh = ph * (tone.h * bg_div) as f64 / src_h as f64;
    let st_div = (screen::SRC_DPI / STENCIL_DPI).round() as usize;
    let stw = pw * (r.sw * st_div) as f64 / src_w as f64;
    let sth = ph * (r.sh * st_div) as f64 / src_h as f64;
    let mut content = format!(
        "q {:.4} 0 0 {:.4} 0 {:.4} cm /Bg Do Q\n",
        bgw, bgh, ph - bgh
    );
    // OVERPRINT, because that is what the press did. Each stencil paints one ink opaquely, so where
    // two of them overlap the later one REPLACES the earlier rather than adding to it -- and red
    // type is M and Y together. Measured on p007: source ink M 234 / Y 198, rendered RGB
    // (252, 201, 24), i.e. pure yellow, because Y is drawn after M. /Separation colourants plus an
    // overprint ExtGState make each layer affect only its own plate, which is the physical truth
    // being reconstructed and not a compositing trick.
    content += "/GSop gs\n";
    for (n, _) in layers.iter().enumerate() {
        content += &format!(
            "q /Ink{} cs 1 scn {:.4} 0 0 {:.4} 0 {:.4} cm /S{} Do Q\n",
            n, stw, sth, ph - sth, n
        );
    }

    let mut xobj = format!("/Bg {} 0 R", bg_obj);
    for (n, _) in layers.iter().enumerate() {
        xobj += &format!(" /S{} {} 0 R", n, ink_start + n);
    }
    // one Separation colourant per layer: tint 1 of that ink, everything else untouched
    let mut csdict = String::new();
    for (n, (ci, _)) in layers.iter().enumerate() {
        let c = INK_CMYK[*ci];
        csdict += &format!(
            " /Ink{} [/Separation /{} /DeviceCMYK \
             << /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [{} {} {} {}] /N 1 >>]",
            n, INK_SEP[*ci], c[0], c[1], c[2], c[3]
        );
    }

    let mut objs: Vec<Vec<u8>> = Vec::new();
    objs.push(b"<< /Type /Catalog /Pages 2 0 R >>".to_vec());
    objs.push(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>".to_vec());
    objs.push(
        format!(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {:.3} {:.3}] \
             /Resources << /XObject << {} >> /ColorSpace <<{} >> \
             /ExtGState << /GSop << /Type /ExtGState /OP true /op true /OPM 1 >> >> >> \
             /Contents {} 0 R >>",
            pw, ph, xobj, csdict, content_obj
        )
        .into_bytes(),
    );
    let mut o = format!(
        "<< /Type /XObject /Subtype /Image /Width {} /Height {} /ColorSpace /DeviceCMYK \
         /BitsPerComponent 8 /Filter /FlateDecode /Length {} >>\nstream\n",
        tone.w,
        tone.h,
        bg.len()
    )
    .into_bytes();
    o.extend_from_slice(&bg);
    o.extend_from_slice(b"\nendstream");
    objs.push(o);
    for (_, data) in &layers {
        let mut o = format!(
            "<< /Type /XObject /Subtype /Image /Width {} /Height {} /ImageMask true /Decode [0 1] \
             /Filter /JBIG2Decode /Length {} >>\nstream\n",
            r.sw,
            r.sh,
            data.len()
        )
        .into_bytes();
        o.extend_from_slice(data);
        o.extend_from_slice(b"\nendstream");
        objs.push(o);
    }
    let cs = deflate(content.as_bytes())?;
    let mut o = format!(
        "<< /Length {} /Filter /FlateDecode >>\nstream\n",
        cs.len()
    )
    .into_bytes();
    o.extend_from_slice(&cs);
    o.extend_from_slice(b"\nendstream");
    objs.push(o);

    let mut out: Vec<u8> = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n".to_vec();
    let mut offsets = Vec::with_capacity(objs.len());
    for (i, ob) in objs.iter().enumerate() {
        offsets.push(out.len());
        out.extend_from_slice(format!("{} 0 obj\n", i + 1).as_bytes());
        out.extend_from_slice(ob);
        out.extend_from_slice(b"\nendobj\n");
    }
    let xref = out.len();
    out.extend_from_slice(format!("xref\n0 {}\n0000000000 65535 f \n", objs.len() + 1).as_bytes());
    for off in &offsets {
        out.extend_from_slice(format!("{:010} 00000 n \n", off).as_bytes());
    }
    out.extend_from_slice(
        format!(
            "trailer\n<< /Size {} /Root 1 0 R >>\nstartxref\n{}\n%%EOF\n",
            objs.len() + 1,
            xref
        )
        .as_bytes(),
    );
    std::fs::write(path, &out).with_context(|| format!("write {}", path))?;

    let mut ink = [0usize; 4];
    for (ci, d) in &layers {
        ink[*ci] = d.len();
    }
    Ok(Sizes { bg: bg.len(), ink, total: out.len() })
}

pub fn summarise(page: &str, s: &Sizes, tone: &Contone) -> String {
    let inks: Vec<String> = (0..4)
        .filter(|&ci| s.ink[ci] > 0)
        .map(|ci| format!("{} {}K", INK_NAME[ci], s.ink[ci] / 1024))
        .collect();
    format!(
        "p{} pdf {}K = bg {}K @{:.0}dpi + stencils {} @{:.0}dpi",
        page,
        s.total / 1024,
        s.bg / 1024,
        tone.dpi,
        if inks.is_empty() { "none".into() } else { inks.join(" ") },
        STENCIL_DPI
    )
}
