//! Minimal .npy writer/reader for the array shapes the pipeline uses, matching the
//! numpy format the Python produces (C-order, little-endian).

use anyhow::{bail, Result};
use std::fs::File;
use std::io::{Read, Write};

fn header(descr: &str, shape: &[usize]) -> Vec<u8> {
    let shape_str = if shape.len() == 1 {
        format!("({},)", shape[0])
    } else {
        let inner: Vec<String> = shape.iter().map(|s| s.to_string()).collect();
        format!("({})", inner.join(", "))
    };
    let dict = format!(
        "{{'descr': '{}', 'fortran_order': False, 'shape': {}, }}",
        descr, shape_str
    );
    // total header must be aligned to 64 bytes including magic(6)+ver(2)+len(2)
    let mut hdr = dict.into_bytes();
    let prelude = 10;
    let total = prelude + hdr.len() + 1; // +1 for newline
    let pad = (64 - (total % 64)) % 64;
    for _ in 0..pad {
        hdr.push(b' ');
    }
    hdr.push(b'\n');
    let mut out = Vec::new();
    out.extend_from_slice(&[0x93]);
    out.extend_from_slice(b"NUMPY");
    out.push(1);
    out.push(0);
    let len = hdr.len() as u16;
    out.extend_from_slice(&len.to_le_bytes());
    out.extend_from_slice(&hdr);
    out
}

pub fn write_f32(path: &str, data: &[f32], shape: &[usize]) -> Result<()> {
    let mut f = File::create(path)?;
    f.write_all(&header("<f4", shape))?;
    let mut bytes = Vec::with_capacity(data.len() * 4);
    for &v in data {
        bytes.extend_from_slice(&v.to_le_bytes());
    }
    f.write_all(&bytes)?;
    Ok(())
}

pub fn write_u8(path: &str, data: &[u8], shape: &[usize]) -> Result<()> {
    let mut f = File::create(path)?;
    f.write_all(&header("|u1", shape))?;
    f.write_all(data)?;
    Ok(())
}

/// Parse a .npy header and return (descr, shape, data_offset).
fn parse_header(buf: &[u8]) -> Result<(String, Vec<usize>, usize)> {
    if &buf[0..6] != &[0x93, b'N', b'U', b'M', b'P', b'Y'] {
        bail!("not a npy file");
    }
    let hlen = u16::from_le_bytes([buf[8], buf[9]]) as usize;
    let header = std::str::from_utf8(&buf[10..10 + hlen])?;
    // crude parse
    let descr = {
        let k = header.find("'descr'").unwrap();
        let s = header[k..].find('\'').unwrap() + k;
        let rest = &header[s + 1..];
        let q1 = rest.find('\'').unwrap();
        let after = &rest[q1 + 1..];
        let q2 = after.find('\'').unwrap();
        let q3 = after[q2 + 1..].find('\'').unwrap();
        after[q2 + 1..q2 + 1 + q3].to_string()
    };
    let shape = {
        let k = header.find("'shape'").unwrap();
        let open = header[k..].find('(').unwrap() + k;
        let close = header[open..].find(')').unwrap() + open;
        let inner = &header[open + 1..close];
        inner
            .split(',')
            .filter_map(|s| s.trim().parse::<usize>().ok())
            .collect::<Vec<_>>()
    };
    Ok((descr, shape, 10 + hlen))
}

pub fn read_f32(path: &str) -> Result<(Vec<f32>, Vec<usize>)> {
    let mut buf = Vec::new();
    File::open(path)?.read_to_end(&mut buf)?;
    let (descr, shape, off) = parse_header(&buf)?;
    if !descr.contains("f4") {
        bail!("expected f4, got {}", descr);
    }
    let data: Vec<f32> = buf[off..]
        .chunks_exact(4)
        .map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    Ok((data, shape))
}

/// int64 arrays. `holes_shape.npy` is one: numpy's `np.array([H, W])` defaults to int64, and
/// reading it as f32 (or deriving the width from the packed byte count) is wrong -- `packbits`
/// pads the last byte, so `bytes*8` overstates the width by up to 7 columns and every hole
/// lookup lands on the wrong column.
pub fn read_i64(path: &str) -> Result<(Vec<i64>, Vec<usize>)> {
    let mut buf = Vec::new();
    File::open(path)?.read_to_end(&mut buf)?;
    let (descr, shape, off) = parse_header(&buf)?;
    if !descr.contains("i8") {
        bail!("expected i8 (int64), got {}", descr);
    }
    let data: Vec<i64> = buf[off..]
        .chunks_exact(8)
        .map(|c| i64::from_le_bytes([c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]]))
        .collect();
    Ok((data, shape))
}

pub fn read_u8(path: &str) -> Result<(Vec<u8>, Vec<usize>)> {
    let mut buf = Vec::new();
    File::open(path)?.read_to_end(&mut buf)?;
    let (_descr, shape, off) = parse_header(&buf)?;
    Ok((buf[off..].to_vec(), shape))
}
