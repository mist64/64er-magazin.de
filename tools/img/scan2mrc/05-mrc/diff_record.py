#!/usr/bin/env python3
"""Diff two MRC decision records: what changed, and in what way.

  diff_record.py <baseline.jsonl> <new.jsonl> [--tol 0.02] [--json out.json]

Accepts a file or a directory of per-page records on either side.

Three buckets, most useful first:

  1. VERDICT FLIPS      -- a region changed destination layer (TEXT->IMAGE, promoted, dropped).
                           Both sides' gate values are printed inline, so a flip can be explained
                           without re-running anything -- which matters because the baseline's
                           binary no longer exists.
  2. GATE CROSSINGS     -- same verdict, but a feature moved by more than --tol. Fragile: the next
                           issue may flip it.
  3. STABLE             -- collapsed to counts.

Rows are joined on a SPATIAL key, not on component id: ids are assignment order and shift whenever
the mask moves, which would report every row as changed. Unmatched rows are reported as added or
removed rather than silently dropped.
"""
import argparse
import collections
import glob
import json
import os
import sys

# feature fields compared per kind (the gates -- everything a decision actually turned on)
FEATURES = {
    "cluster": ["vote", "cv", "s", "tv", "bodyK", "objfK", "bodyC"],
    "darkfill": ["dark_frac", "filled_frac", "hole_frac"],
    "kdrop": ["px"],
    "page": ["image_frac", "screen_frac", "tint_frac", "k_frac"],
    "output": [],
}
# the field whose change means "this region went somewhere else"
VERDICT = {"cluster": "verdict", "darkfill": "promoted", "kdrop": "layer", "page": "inks"}
QUANT = 8       # spatial key quantisation, px @600. Survives a small change in extent, still
                # separates neighbouring regions.


def load(path):
    files = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.jsonl")))
    else:
        files = [path]
    rows = []
    for f in files:
        with open(f) as fh:
            for l in fh:
                if l.strip():
                    rows.append(json.loads(l))
    return rows


def key(r):
    if "bbox" in r:
        x0, y0, x1, y1 = r["bbox"]
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    elif "centroid" in r:
        cx, cy = r["centroid"]
    else:
        return (r["kind"], r.get("page"), 0, 0)
    return (r["kind"], r.get("page"), cx // QUANT, cy // QUANT)


def fmt(r, fields):
    return " ".join("%s=%s" % (f, r.get(f)) for f in fields if f in r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("new")
    ap.add_argument("--tol", type=float, default=0.02,
                    help="relative move that counts as a gate crossing (default 2%%)")
    ap.add_argument("--json", default=None)
    A = ap.parse_args()

    old = {key(r): r for r in load(A.baseline)}
    new = {key(r): r for r in load(A.new)}

    flips, moves, added, removed = [], [], [], []
    for k, r in new.items():
        o = old.get(k)
        if o is None:
            added.append(r)
            continue
        kind = r["kind"]
        vf = VERDICT.get(kind)
        if vf and o.get(vf) != r.get(vf):
            flips.append((o, r))
            continue
        for f in FEATURES.get(kind, []):
            a, b = o.get(f), r.get(f)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(b - a) > A.tol * max(abs(a), 1e-9):
                    moves.append((f, o, r))
                    break
    for k, r in old.items():
        if k not in new:
            removed.append(r)

    pages = sorted({r.get("page") for r in
                    [x[1] for x in flips] + [x[2] for x in moves] + added + removed
                    if r.get("page")})

    print("baseline %d rows   new %d rows" % (len(old), len(new)))
    print("VERDICT FLIPS %d   gate moves %d   added %d   removed %d   pages touched %d"
          % (len(flips), len(moves), len(added), len(removed), len(pages)))
    if pages:
        print("pages: %s" % " ".join(pages))

    if flips:
        print("\n=== VERDICT FLIPS (every one of these must be accounted for) ===")
        for o, r in sorted(flips, key=lambda t: (t[1].get("page", ""), -t[1].get("area", t[1].get("px", 0)))):
            kind = r["kind"]
            vf = VERDICT[kind]
            print("p%s %-9s %s  %s -> %s   area=%s" % (
                r.get("page"), kind, r.get("bbox") or r.get("centroid"),
                o.get(vf), r.get(vf), r.get("area", r.get("px"))))
            print("      was: %s" % fmt(o, FEATURES.get(kind, [])))
            print("      now: %s" % fmt(r, FEATURES.get(kind, [])))
    if added or removed:
        print("\n=== REGIONS APPEARED / VANISHED ===")
        for r in added[:40]:
            print("  + p%s %-9s %s area=%s" % (r.get("page"), r["kind"],
                                               r.get("bbox") or r.get("centroid"),
                                               r.get("area", r.get("px"))))
        for r in removed[:40]:
            print("  - p%s %-9s %s area=%s" % (r.get("page"), r["kind"],
                                               r.get("bbox") or r.get("centroid"),
                                               r.get("area", r.get("px"))))
        if len(added) > 40 or len(removed) > 40:
            print("  ... (%d added, %d removed total)" % (len(added), len(removed)))
    if moves:
        print("\n=== GATE MOVES (same verdict, feature moved > %.0f%%) ===" % (100 * A.tol))
        byf = collections.Counter(f for f, _, _ in moves)
        for f, c in byf.most_common():
            print("  %-10s %d regions" % (f, c))

    if A.json:
        json.dump({"flips": [{"old": o, "new": n} for o, n in flips],
                   "added": added, "removed": removed,
                   "moves": [{"field": f, "old": o, "new": n} for f, o, n in moves],
                   "pages": pages},
                  open(A.json, "w"), indent=1)
        print("\nwrote %s" % A.json)
    return 1 if flips else 0


if __name__ == "__main__":
    sys.exit(main())
