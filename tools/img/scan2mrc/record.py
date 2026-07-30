#!/usr/bin/env python3
"""The decision record, Python side -- the same JSONL format `rust_pipeline/src/record.rs` writes.

One format for both languages, so ONE differ (`05-mrc/diff_record.py`) and ONE overlay drawer
(`05-mrc/draw_record.py`) serve the whole pipeline. Before this, verifying a matte change meant
writing a bespoke probe (`pen_probe.py`) that did by hand what the differ already does for the
renderer -- and the ink-eating defect in the penumbra walk was only found because I happened to
think of a structure test to look for it.

Rules, same as the Rust side:
  * written by the code that MAKES the decision, at the moment it makes it -- so it cannot drift
    from what shipped
  * every row carries the geometry the overlay needs AND the gate values the differ needs; the
    gates are the one thing that cannot be recovered afterwards, because once the code changes the
    baseline's measured value is gone
  * always on where cheap, path from an env var so a baseline exists without anyone remembering to
    ask for one

Usage:
    import record
    rec = record.Recorder(record.path_from_env("BM_RECORD", page))
    rec.push(kind="edge", page=page, edge="bottom", decision="CUT", depth=180.9, ...)
    rec.flush()
"""
import json
import os


class Recorder:
    """path=None disables recording entirely (rows dropped, no file written)."""

    def __init__(self, path=None):
        self.path = path
        self.rows = []

    @property
    def enabled(self):
        return self.path is not None

    def push(self, **row):
        if self.path is not None:
            self.rows.append(row)

    def flush(self):
        """Written in one go, not appended row by row: a run that dies half way should leave no
        file rather than a truncated one the differ would treat as complete."""
        if self.path is None:
            return
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(self.path, "w") as f:
            for r in self.rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        return self.path


def path_from_env(var, page=None):
    """A directory in `var` gets one file per page; a plain path is used as given; unset or empty
    disables. Per page is the default because the drivers run pages in parallel shells."""
    v = os.environ.get(var)
    if not v:
        return None
    if v.endswith("/") or os.path.isdir(v):
        return os.path.join(v, "%03d.jsonl" % int(page)) if page is not None else None
    return v


def r4(v):
    """Round for the record: full float precision makes rows noisy to diff over digits that carry
    no decision. 4 places is finer than any gate in this pipeline."""
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return v
