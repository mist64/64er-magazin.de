//! The decision record: one JSONL row per decision the MRC analysis makes.
//!
//! Written by the code that MAKES each decision, at the moment it makes it -- so it cannot drift
//! from what shipped. Two readers consume it and neither re-implements anything:
//!
//!   * the overlay drawer  -- needs `bbox`/`centroid` + `layer` + `kind`
//!   * the run differ      -- needs the gate values, which are the one thing that CANNOT be
//!                            recovered afterwards (once the binary changes, the baseline's
//!                            `filled_frac = 0.812` is gone for good)
//!
//! Volume is small enough to always be on: ~400 cluster rows on a busy page, a few floats each.

use anyhow::{Context, Result};
use std::io::Write;

pub struct Recorder {
    path: Option<String>,
    rows: Vec<String>,
}

impl Recorder {
    /// `path` = None disables recording entirely (rows are dropped, no file written).
    pub fn new(path: Option<String>) -> Self {
        Recorder { path, rows: Vec::new() }
    }

    pub fn enabled(&self) -> bool {
        self.path.is_some()
    }

    pub fn push(&mut self, v: serde_json::Value) {
        if self.path.is_some() {
            self.rows.push(v.to_string());
        }
    }

    pub fn len(&self) -> usize {
        self.rows.len()
    }

    /// Write the whole record at once. Not appended row-by-row: a run that dies half way should
    /// leave no file rather than a truncated one that the differ would silently treat as complete.
    pub fn flush(&mut self) -> Result<()> {
        let path = match &self.path {
            Some(p) => p.clone(),
            None => return Ok(()),
        };
        if let Some(dir) = std::path::Path::new(&path).parent() {
            if !dir.as_os_str().is_empty() {
                std::fs::create_dir_all(dir).ok();
            }
        }
        let mut f = std::fs::File::create(&path).with_context(|| format!("create {}", path))?;
        for r in &self.rows {
            writeln!(f, "{}", r)?;
        }
        eprintln!("  record: {} rows -> {}", self.rows.len(), path);
        Ok(())
    }
}
