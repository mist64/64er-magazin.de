//! Byte-exact re-implementations of the two files the Python apply ships.
//!
//! The acceptance bar for the Rust apply is `shasum` equality with the Python's output, so these
//! writers reproduce not just the pixels but the CONTAINER: libtiff's LZW code stream and strip
//! layout, and PIL's PNG filter choice and deflate parameters. Both were validated byte-for-byte
//! against real output before being written here (`tmp/dbg/proto_writers.py`), including against
//! strip 0..5 of a real 19843x28063 page.
//!
//! Why not the `tiff` / `image` crates: they encode correctly but differently -- different strip
//! size, different tag order, a different deflate strategy -- so every page would hash differently
//! for reasons that have nothing to do with the arithmetic the port is being judged on.

use anyhow::{Context, Result};
use std::io::{BufWriter, Seek, SeekFrom, Write};

// ---------------------------------------------------------------------------------------------
// libtiff LZW (tif_lzw.c: LZWPreEncode / LZWEncode / LZWPostEncode)
// ---------------------------------------------------------------------------------------------
const BITS_MIN: i32 = 9;
const BITS_MAX: i32 = 12;
const CODE_CLEAR: u32 = 256;
const CODE_EOI: u32 = 257;
const CODE_FIRST: i32 = 258;
const CODE_MAX: i32 = (1 << BITS_MAX) - 1; // 4095
const HSIZE: usize = 9001;
const HSHIFT: i32 = 5;
const CHECK_GAP: i64 = 10000;

/// Scratch buffers for the LZW encoder, reused across strips (one 9001-entry hash table per
/// worker instead of one per row -- there are 28063 rows a page).
pub struct LzwState {
    hash_h: Vec<i64>,
    hash_c: Vec<i32>,
}

impl LzwState {
    pub fn new() -> Self {
        LzwState { hash_h: vec![-1; HSIZE], hash_c: vec![0; HSIZE] }
    }
}

/// Encode one strip exactly as libtiff would. `out` is appended to.
pub fn lzw_encode(st: &mut LzwState, data: &[u8], out: &mut Vec<u8>) {
    if data.is_empty() {
        return;
    }
    for v in st.hash_h.iter_mut() {
        *v = -1;
    }
    let mut nextdata: u64 = 0;
    let mut nextbits: i32 = 0;
    let mut nbits: i32 = BITS_MIN;
    let mut maxcode: i32 = (1 << BITS_MIN) - 1;
    let mut free_ent: i32 = CODE_FIRST;
    let mut incount: i64 = 0;
    let mut outcount: i64 = 0;
    let mut checkpoint: i64 = CHECK_GAP;
    let mut ratio: i64 = 0;

    macro_rules! put {
        ($code:expr) => {{
            nextdata = (nextdata << nbits) | ($code as u64);
            nextbits += nbits;
            out.push(((nextdata >> (nextbits - 8)) & 0xFF) as u8);
            nextbits -= 8;
            if nextbits >= 8 {
                out.push(((nextdata >> (nextbits - 8)) & 0xFF) as u8);
                nextbits -= 8;
            }
            outcount += nbits as i64;
        }};
    }

    put!(CODE_CLEAR);
    let mut ent: i32 = data[0] as i32;
    incount += 1;
    let mut i = 1usize;
    while i < data.len() {
        let c = data[i] as i32;
        i += 1;
        incount += 1;
        let fcode: i64 = ((c as i64) << BITS_MAX) + ent as i64;
        let mut h: i32 = (c << HSHIFT) ^ ent;
        if st.hash_h[h as usize] == fcode {
            ent = st.hash_c[h as usize];
            continue;
        }
        let mut hit = false;
        if st.hash_h[h as usize] >= 0 {
            let disp: i32 = if h == 0 { 1 } else { HSIZE as i32 - h };
            loop {
                h -= disp;
                if h < 0 {
                    h += HSIZE as i32;
                }
                if st.hash_h[h as usize] == fcode {
                    ent = st.hash_c[h as usize];
                    hit = true;
                    break;
                }
                if st.hash_h[h as usize] < 0 {
                    break;
                }
            }
        }
        if hit {
            continue;
        }
        put!(ent as u32);
        ent = c;
        st.hash_c[h as usize] = free_ent;
        st.hash_h[h as usize] = fcode;
        free_ent += 1;
        if free_ent == CODE_MAX - 1 {
            for v in st.hash_h.iter_mut() {
                *v = -1;
            }
            ratio = 0;
            incount = 0;
            outcount = 0;
            free_ent = CODE_FIRST;
            put!(CODE_CLEAR);
            nbits = BITS_MIN;
            maxcode = (1 << BITS_MIN) - 1;
        } else if free_ent > maxcode {
            nbits += 1;
            maxcode = (1 << nbits) - 1;
        } else if incount >= checkpoint {
            checkpoint = incount + CHECK_GAP;
            let rat = if incount > 0x007f_ffff {
                let r = outcount >> 8;
                if r == 0 {
                    0x7fff_ffff
                } else {
                    incount / r
                }
            } else {
                (incount << 8) / outcount
            };
            if rat <= ratio {
                for v in st.hash_h.iter_mut() {
                    *v = -1;
                }
                ratio = 0;
                incount = 0;
                outcount = 0;
                free_ent = CODE_FIRST;
                put!(CODE_CLEAR);
                nbits = BITS_MIN;
                maxcode = (1 << BITS_MIN) - 1;
            } else {
                ratio = rat;
            }
        }
    }
    // LZWPostEncode
    put!(ent as u32);
    free_ent += 1;
    if free_ent == CODE_MAX - 1 {
        // The table filled on the very last symbol: libtiff still emits the CLEAR before the EOI.
        // Rare (about 1 row in 3000) and easy to drop -- it cost 10 of p002's 28063 strips.
        put!(CODE_CLEAR);
        nbits = BITS_MIN;
    } else if free_ent > maxcode {
        nbits += 1;
    }
    put!(CODE_EOI);
    if nextbits > 0 {
        out.push(((nextdata << (8 - nextbits)) & 0xFF) as u8);
    }
    let _ = (ratio, checkpoint, maxcode, outcount, incount);
}

// ---------------------------------------------------------------------------------------------
// CMYK TIFF, in PIL-via-libtiff's exact layout
// ---------------------------------------------------------------------------------------------

/// Directory layout libtiff writes: pixel data first from offset 8, then the IFD, then the
/// out-of-line values in libtiff's own order (BitsPerSample, StripByteCounts, StripOffsets).
/// RowsPerStrip is 1 because PIL aims at a 64 KB strip and one 19843 px CMYK row is 79372 bytes.
fn write_tiff_dir<W: Write + Seek>(
    f: &mut W,
    w: usize,
    h: usize,
    offs: &[u32],
    cnts: &[u32],
    ifd_off: u64,
) -> Result<()> {
    let n_ent: u16 = 10;
    let bits_off = ifd_off + 2 + 12 * n_ent as u64 + 4;
    let sbc_off = bits_off + 8;
    let so_off = sbc_off + 4 * h as u64;
    // (tag, type, count, value)  -- SHORT=3, LONG=4
    let ents: [(u16, u16, u32, u32); 10] = [
        (256, 3, 1, w as u32),
        (257, 3, 1, h as u32),
        (258, 3, 4, bits_off as u32),
        (259, 3, 1, 5), // LZW
        (262, 3, 1, 5), // Separated
        (273, 4, h as u32, so_off as u32),
        (277, 3, 1, 4),
        (278, 3, 1, 1),
        (279, 4, h as u32, sbc_off as u32),
        (284, 3, 1, 1),
    ];
    f.write_all(&n_ent.to_le_bytes())?;
    for (t, ty, cnt, v) in ents {
        f.write_all(&t.to_le_bytes())?;
        f.write_all(&ty.to_le_bytes())?;
        f.write_all(&cnt.to_le_bytes())?;
        if ty == 3 && cnt == 1 {
            f.write_all(&(v as u16).to_le_bytes())?;
            f.write_all(&0u16.to_le_bytes())?;
        } else {
            f.write_all(&v.to_le_bytes())?;
        }
    }
    f.write_all(&0u32.to_le_bytes())?; // next IFD
    for _ in 0..4 {
        f.write_all(&8u16.to_le_bytes())?;
    }
    let mut buf = Vec::with_capacity(4 * h);
    for &c in cnts {
        buf.extend_from_slice(&c.to_le_bytes());
    }
    f.write_all(&buf)?;
    buf.clear();
    for &o in offs {
        buf.extend_from_slice(&o.to_le_bytes());
    }
    f.write_all(&buf)?;
    Ok(())
}

/// LZW CMYK TIFF, byte-identical to `PIL.Image.merge("CMYK",..).save(p, compression="tiff_lzw")`.
/// Streams row by row: the interleaved page is 2.2 GB and must never be materialised.
pub fn write_cmyk_tiff_lzw(path: &str, w: usize, h: usize, planes: [&[u8]; 4]) -> Result<()> {
    let file = std::fs::File::create(path).with_context(|| format!("create {}", path))?;
    let mut f = BufWriter::with_capacity(1 << 20, file);
    f.write_all(b"II*\x00")?;
    f.write_all(&0u32.to_le_bytes())?;
    let mut offs = Vec::with_capacity(h);
    let mut cnts = Vec::with_capacity(h);
    let mut pos: u64 = 8;
    let mut st = LzwState::new();
    let mut row = vec![0u8; w * 4];
    let mut enc = Vec::with_capacity(w * 5);
    for y in 0..h {
        let base = y * w;
        for x in 0..w {
            row[x * 4] = planes[0][base + x];
            row[x * 4 + 1] = planes[1][base + x];
            row[x * 4 + 2] = planes[2][base + x];
            row[x * 4 + 3] = planes[3][base + x];
        }
        enc.clear();
        lzw_encode(&mut st, &row, &mut enc);
        f.write_all(&enc)?;
        offs.push(pos as u32);
        cnts.push(enc.len() as u32);
        pos += enc.len() as u64;
    }
    let ifd_off = pos;
    write_tiff_dir(&mut f, w, h, &offs, &cnts, ifd_off)?;
    f.flush()?;
    let mut file = f.into_inner().context("tiff into_inner")?;
    file.seek(SeekFrom::Start(4))?;
    file.write_all(&(ifd_off as u32).to_le_bytes())?;
    Ok(())
}

/// UNCOMPRESSED CMYK TIFF -- for the detect-graded page only, which `geometry`/`detect` consume
/// and `cache_pages.sh` deletes ~60s later. LZW costs 44.5s a page for a 24% saving on a file
/// with a one-minute life; that is the wrong trade.
pub fn write_cmyk_tiff_raw(path: &str, w: usize, h: usize, planes: [&[u8]; 4]) -> Result<()> {
    let file = std::fs::File::create(path).with_context(|| format!("create {}", path))?;
    let mut f = BufWriter::with_capacity(1 << 22, file);
    f.write_all(b"II*\x00")?;
    f.write_all(&0u32.to_le_bytes())?;
    let stride = w * 4;
    let mut offs = Vec::with_capacity(h);
    let mut cnts = Vec::with_capacity(h);
    let mut pos: u64 = 8;
    let mut row = vec![0u8; stride];
    for y in 0..h {
        let base = y * w;
        for x in 0..w {
            row[x * 4] = planes[0][base + x];
            row[x * 4 + 1] = planes[1][base + x];
            row[x * 4 + 2] = planes[2][base + x];
            row[x * 4 + 3] = planes[3][base + x];
        }
        f.write_all(&row)?;
        offs.push(pos as u32);
        cnts.push(stride as u32);
        pos += stride as u64;
    }
    let ifd_off = pos;
    // same directory, compression tag flipped to 1 (none)
    let n_ent: u16 = 10;
    let bits_off = ifd_off + 2 + 12 * n_ent as u64 + 4;
    let sbc_off = bits_off + 8;
    let so_off = sbc_off + 4 * h as u64;
    let ents: [(u16, u16, u32, u32); 10] = [
        (256, 3, 1, w as u32),
        (257, 3, 1, h as u32),
        (258, 3, 4, bits_off as u32),
        (259, 3, 1, 1),
        (262, 3, 1, 5),
        (273, 4, h as u32, so_off as u32),
        (277, 3, 1, 4),
        (278, 3, 1, 1),
        (279, 4, h as u32, sbc_off as u32),
        (284, 3, 1, 1),
    ];
    f.write_all(&n_ent.to_le_bytes())?;
    for (t, ty, cnt, v) in ents {
        f.write_all(&t.to_le_bytes())?;
        f.write_all(&ty.to_le_bytes())?;
        f.write_all(&cnt.to_le_bytes())?;
        if ty == 3 && cnt == 1 {
            f.write_all(&(v as u16).to_le_bytes())?;
            f.write_all(&0u16.to_le_bytes())?;
        } else {
            f.write_all(&v.to_le_bytes())?;
        }
    }
    f.write_all(&0u32.to_le_bytes())?;
    for _ in 0..4 {
        f.write_all(&8u16.to_le_bytes())?;
    }
    let mut buf = Vec::with_capacity(4 * h);
    for &c in &cnts {
        buf.extend_from_slice(&c.to_le_bytes());
    }
    f.write_all(&buf)?;
    buf.clear();
    for &o in &offs {
        buf.extend_from_slice(&o.to_le_bytes());
    }
    f.write_all(&buf)?;
    f.flush()?;
    let mut file = f.into_inner().context("tiff into_inner")?;
    file.seek(SeekFrom::Start(4))?;
    file.write_all(&(ifd_off as u32).to_le_bytes())?;
    Ok(())
}

// ---------------------------------------------------------------------------------------------
// zlib at PIL's PNG settings (level 9, Z_FILTERED). flate2 cannot express the strategy.
// ---------------------------------------------------------------------------------------------
mod z {
    use libz_sys::*;
    use std::mem;

    pub fn compress_filtered(src: &[u8]) -> Vec<u8> {
        unsafe {
            // zlib's documented initialisation: an all-zero z_stream means "use the default
            // allocator". The binding types zalloc/zfree as non-nullable fn pointers, so plain
            // `mem::zeroed()` trips the invalid-value lint; C only ever tests them against NULL.
            let mut strm: z_stream = mem::MaybeUninit::zeroed().assume_init();
            let ver = zlibVersion();
            // PIL's PNG settings: level 9, windowBits 15, memLevel **9**, Z_FILTERED. memLevel is
            // not cosmetic -- it sets lit_bufsize, i.e. how often deflate closes a block, and 8
            // (zlib's default) compresses this mask 0.9% BETTER and so hashes differently.
            let rc = deflateInit2_(
                &mut strm,
                9,
                Z_DEFLATED,
                15,
                9,
                Z_FILTERED,
                ver,
                mem::size_of::<z_stream>() as i32,
            );
            assert_eq!(rc, Z_OK, "deflateInit2 failed");
            let mut out = vec![0u8; deflateBound(&mut strm, src.len() as uLong) as usize + 64];
            strm.next_in = src.as_ptr() as *mut Bytef;
            strm.avail_in = src.len() as uInt;
            strm.next_out = out.as_mut_ptr();
            strm.avail_out = out.len() as uInt;
            let rc = deflate(&mut strm, Z_FINISH);
            assert_eq!(rc, Z_STREAM_END, "deflate did not finish in one pass");
            let n = strm.total_out as usize;
            deflateEnd(&mut strm);
            out.truncate(n);
            out
        }
    }
}

fn crc32(data: &[u8]) -> u32 {
    unsafe { libz_sys::crc32(0, data.as_ptr(), data.len() as libz_sys::uInt) as u32 }
}

fn png_chunk<W: Write>(f: &mut W, tag: &[u8; 4], data: &[u8]) -> Result<()> {
    f.write_all(&(data.len() as u32).to_be_bytes())?;
    f.write_all(tag)?;
    f.write_all(data)?;
    let mut c = Vec::with_capacity(4 + data.len());
    c.extend_from_slice(tag);
    c.extend_from_slice(data);
    f.write_all(&crc32(&c).to_be_bytes())?;
    Ok(())
}

#[inline]
fn paeth(a: u8, b: u8, c: u8) -> u8 {
    let p = a as i32 + b as i32 - c as i32;
    let pa = (p - a as i32).abs();
    let pb = (p - b as i32).abs();
    let pc = (p - c as i32).abs();
    if pa <= pb && pa <= pc {
        a
    } else if pb <= pc {
        b
    } else {
        c
    }
}

/// 1-bit grayscale PNG, byte-identical to PIL's
/// `Image.fromarray(mask*255).convert("1").save(p, optimize=True)`.
///
/// `bit_set[i]` true => WHITE (the PNG carries `known`, i.e. the inverse of the alpha). Filters
/// are chosen by the PNG spec's minimum-sum-of-absolute-signed-bytes heuristic, which is what
/// PIL's optimize path does; the IDAT is split at max(65536, W*4) because that is PIL's encoder
/// buffer size.
pub fn write_png_1bit(path: &str, w: usize, h: usize, bit_set: &[bool]) -> Result<()> {
    let stride = (w + 7) / 8;
    let mut raw = Vec::with_capacity((stride + 1) * h);
    let mut cur = vec![0u8; stride];
    let mut prev = vec![0u8; stride];
    let mut cand = vec![vec![0u8; stride]; 5];
    for y in 0..h {
        for b in cur.iter_mut() {
            *b = 0;
        }
        let row = &bit_set[y * w..(y + 1) * w];
        for x in 0..w {
            if row[x] {
                cur[x >> 3] |= 0x80 >> (x & 7);
            }
        }
        let mut best = 0usize;
        let mut best_sum = u64::MAX;
        for fl in 0..5usize {
            let mut sum = 0u64;
            for i in 0..stride {
                let a = if i >= 1 { cur[i - 1] } else { 0 };
                let b = prev[i];
                let c = if i >= 1 { prev[i - 1] } else { 0 };
                let v: u8 = match fl {
                    0 => cur[i],
                    1 => cur[i].wrapping_sub(a),
                    2 => cur[i].wrapping_sub(b),
                    3 => cur[i].wrapping_sub((((a as u32) + (b as u32)) / 2) as u8),
                    _ => cur[i].wrapping_sub(paeth(a, b, c)),
                };
                cand[fl][i] = v;
                sum += if v < 128 { v as u64 } else { 256 - v as u64 };
            }
            if sum < best_sum {
                best_sum = sum;
                best = fl;
            }
        }
        raw.push(best as u8);
        raw.extend_from_slice(&cand[best]);
        std::mem::swap(&mut prev, &mut cur);
    }
    let comp = z::compress_filtered(&raw);
    let file = std::fs::File::create(path).with_context(|| format!("create {}", path))?;
    let mut f = BufWriter::with_capacity(1 << 20, file);
    f.write_all(b"\x89PNG\r\n\x1a\n")?;
    let mut ihdr = Vec::with_capacity(13);
    ihdr.extend_from_slice(&(w as u32).to_be_bytes());
    ihdr.extend_from_slice(&(h as u32).to_be_bytes());
    ihdr.extend_from_slice(&[1, 0, 0, 0, 0]); // bit depth 1, greyscale, deflate, adaptive, no interlace
    png_chunk(&mut f, b"IHDR", &ihdr)?;
    let step = std::cmp::max(65536, w * 4);
    let mut i = 0usize;
    while i < comp.len() {
        let j = std::cmp::min(i + step, comp.len());
        png_chunk(&mut f, b"IDAT", &comp[i..j])?;
        i = j;
    }
    png_chunk(&mut f, b"IEND", b"")?;
    f.flush()?;
    Ok(())
}

/// 8-bit RGB PNG for the cached 600 dpi products. Not byte-compared against anything, so the
/// only requirement is that it round-trips exactly; deflate level 6 is the size/time knee here.
pub fn write_rgb_png_fast(path: &str, w: usize, h: usize, data: &[u8]) -> Result<()> {
    let stride = w * 3;
    let mut raw = Vec::with_capacity((stride + 1) * h);
    let mut prev = vec![0u8; stride];
    for y in 0..h {
        let cur = &data[y * stride..(y + 1) * stride];
        // Paeth on every row: cheap, and these are photographic downsamples
        raw.push(4u8);
        for i in 0..stride {
            let a = if i >= 3 { cur[i - 3] } else { 0 };
            let b = prev[i];
            let c = if i >= 3 { prev[i - 3] } else { 0 };
            raw.push(cur[i].wrapping_sub(paeth(a, b, c)));
        }
        prev.copy_from_slice(cur);
    }
    let comp = {
        use flate2::write::ZlibEncoder;
        use flate2::Compression;
        let mut e = ZlibEncoder::new(Vec::new(), Compression::new(6));
        e.write_all(&raw)?;
        e.finish()?
    };
    let file = std::fs::File::create(path).with_context(|| format!("create {}", path))?;
    let mut f = BufWriter::with_capacity(1 << 20, file);
    f.write_all(b"\x89PNG\r\n\x1a\n")?;
    let mut ihdr = Vec::with_capacity(13);
    ihdr.extend_from_slice(&(w as u32).to_be_bytes());
    ihdr.extend_from_slice(&(h as u32).to_be_bytes());
    ihdr.extend_from_slice(&[8, 2, 0, 0, 0]);
    png_chunk(&mut f, b"IHDR", &ihdr)?;
    png_chunk(&mut f, b"IDAT", &comp)?;
    png_chunk(&mut f, b"IEND", b"")?;
    f.flush()?;
    Ok(())
}
