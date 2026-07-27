#!/usr/bin/env python3
"""Learn matte priors from PASS-1 (high-confidence) cuts over the whole magazine.

Runs bed_matte's per-edge analysis (PASS-1 measurement) on every page at 600 dpi, collects the
HIGH-confidence cuts, and summarises, per edge and per PARITY, the typical {cut depth, cut angle}.

PARITY model (a bound magazine on a flatbed): the OUTER bed bar falls on the LEFT of an EVEN page
(verso) and on the RIGHT of an ODD page (recto). So the side-bar priors are learned PER PARITY. The
top wedge and the yellow bottom are physical to the scanner/insert, not the page's handedness, so they
are learned PARITY-INDEPENDENT (one distribution each).

Writes priors.json (median + spread + count per edge/parity) and prints a readable summary table.
This is the learning half of the two-pass plan; PASS-2 (applying these priors to accept ambiguous
edges and reject atypically-deep ones) is enabled separately -- NOT run here.
"""
import sys, os, json, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_matte as bm
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

THUMBS = "/Users/mist/DNB/8609/thumbs_600"
OUT    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "priors.json")
DPI    = 600


def parity(page_no):
    return "even" if page_no % 2 == 0 else "odd"


def summarise(samples):
    """samples: list of (depth, angle). Return median+spread(=robust MAD-based std)+count."""
    if not samples:
        return dict(count=0, median_depth=None, median_angle=None,
                    depth_mad=None, angle_mad=None, depth_iqr=None)
    d = np.array([s[0] for s in samples], float); a = np.array([s[1] for s in samples], float)
    med = float(np.median(d))
    return dict(count=len(samples),
                median_depth=med,
                median_angle=float(np.median(a)),
                depth_mad=float(1.4826 * np.median(np.abs(d - med))),   # robust std of depth
                angle_mad=float(1.4826 * np.median(np.abs(a - np.median(a)))),
                depth_iqr=[float(np.percentile(d, 25)), float(np.percentile(d, 75))])


def main():
    paths = sorted(glob.glob(os.path.join(THUMBS, "*.png")))
    # buckets: top/bottom parity-independent; left/right per parity
    buckets = {"top": [], "bottom": [],
               "left": {"even": [], "odd": []}, "right": {"even": [], "odd": []}}
    counts = {"HIGH": 0, "LOW": 0, "NONE": 0}
    per_edge_high = {e: 0 for e in bm.EDGES}
    n_pages = 0

    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            page_no = int(name)
        except ValueError:
            continue
        a = np.asarray(Image.open(p).convert("RGB"))[..., :3].astype(np.float32)
        H, W, _ = a.shape
        lum = a @ np.array([0.299, 0.587, 0.114], np.float32); sat = a.max(2) - a.min(2)
        dtb = int(bm.WIN_TB_FRAC * H); dlr = int(bm.WIN_LR_FRAC * W)
        n_pages += 1
        for edge in bm.EDGES:
            cut_depth, conf, m = bm.analyze_edge(lum, sat, edge, DPI, H, W, dtb, dlr)
            counts[conf] = counts.get(conf, 0) + 1
            if conf != "HIGH":
                continue
            per_edge_high[edge] += 1
            depth = float(np.median(cut_depth)); ang = m["angle_deg"]
            if edge in ("top", "bottom"):
                buckets[edge].append((depth, ang))
            else:
                buckets[edge][parity(page_no)].append((depth, ang))
        print(f"  {name} done", flush=True)

    priors = {"dpi": DPI, "n_pages": n_pages,
              "top": summarise(buckets["top"]),
              "bottom": summarise(buckets["bottom"]),
              "left": {k: summarise(v) for k, v in buckets["left"].items()},
              "right": {k: summarise(v) for k, v in buckets["right"].items()}}
    json.dump(priors, open(OUT, "w"), indent=2)

    # ---- readable summary ----
    tot = counts["HIGH"] + counts["LOW"] + counts["NONE"]
    print("\n================= PASS-1 PRIORS SUMMARY =================")
    print(f"pages={n_pages}  edges={tot}  HIGH={counts['HIGH']}  LOW={counts['LOW']}  NONE={counts['NONE']}")
    print("high-confidence edges by edge:",
          "  ".join(f"{e}={per_edge_high[e]}" for e in bm.EDGES))
    print(f"\n{'edge/parity':16s} {'n':>4s} {'depth_med':>10s} {'depth_MAD':>10s} "
          f"{'depth_IQR':>16s} {'ang_med':>8s} {'ang_MAD':>8s}")

    def row(label, s):
        if not s["count"]:
            print(f"{label:16s} {0:>4d}    (none)"); return
        iqr = f"[{s['depth_iqr'][0]:.0f},{s['depth_iqr'][1]:.0f}]"
        print(f"{label:16s} {s['count']:>4d} {s['median_depth']:>10.1f} {s['depth_mad']:>10.1f} "
              f"{iqr:>16s} {s['median_angle']:>+8.2f} {s['angle_mad']:>8.2f}")

    row("top (wedge)", priors["top"])
    row("bottom (yellow)", priors["bottom"])
    row("left even", priors["left"]["even"]); row("left odd", priors["left"]["odd"])
    row("right even", priors["right"]["even"]); row("right odd", priors["right"]["odd"])
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
