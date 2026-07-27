#!/usr/bin/env python3
"""
03 A4 CROP -- global-fit stage (the front-end's final step before grading)
==========================================================================

Positions a FIXED A4 output rectangle on every page so that the rigid "64'er"
LOGO lands at the SAME output position on all pages. This is NOT a per-page
nudge: we solve GLOBAL constants once (over all 176 pages) and every page's A4
window is those constants + that page's own logo anchor.

WHY LOGO-ANCHOR (not edge-anchor)
---------------------------------
The logo detector (logo_detect.py) shows the wordmark wanders ~9-11 mm
horizontally relative to the scanned sheet edges (even anchor_x spans
1944..2784 master px = 8.7 mm; odd 17944..19064 = 11.9 mm). Anchoring the A4
window to the *edge* would inherit that wander; anchoring to the *logo* removes
it -- the printed content sits at a fixed offset from the logo (it was on the
same physical plate), so a logo-locked window lands on the same content every
page. That is exactly the north-star "reconstruct the prepress sheet" intent.

THE RULE (locked with the user)
-------------------------------
* VERTICAL: two GLOBAL constants A (px below the logo baseline) and B (px above
  it) with A + B = A4_H. The logo baseline sits at a fixed vertical output
  position (B from the window top). A,B chosen to MAXIMISE captured real
  (non-alpha) page content across all pages == minimise bed/yellow alpha inside
  the window. Convex 1-D fit (objective below).
* HORIZONTAL: also logo-anchored & mirror-symmetric.
    even page -> logo bottom-LEFT , spine on the RIGHT (inner = right edge)
    odd  page -> logo bottom-RIGHT, spine on the LEFT  (inner = left  edge)
  The inner (spine-side) crop edge = a GLOBAL AVERAGE of where the spine sits
  relative to the logo (per parity). We do NOT crop at each page's own spine
  (they differ slightly); we crop at the parity-average spine-vs-logo offset.
  A4 width is fixed, so fixing the inner edge fixes the outer trim too (the
  logo's offset from the outer trim is therefore also a fixed constant).
* NO-LOGO pages (47 ad/cover pages): the logo anchor is reconstructed by
  INTERPOLATION -- the logo's offset relative to that page's own content box is
  near-constant per parity, so we place the anchor at (this page's content box)
  + (per-parity median logo-vs-content offset). Flagged confidence="interp".

This stage only COMPUTES the per-page A4 window (x0,y0,x1,y1 in MASTER px) plus
the global constants -> tmp/crop_windows.json. It does NOT resample; full-res
apply is later Rust. Pixels inside the window that fall in alpha (bed/neighbor,
or beyond the sheet) stay unknown -- we never fabricate.

INPUTS
------
* tmp/logo_positions.json  (logo_detect.py)  -- per-page logo anchor (master px)
* tmp/matte_cache.json     (build_matte_cache.py) -- per-page bed_matte pass-2
      edge cut_px/decision + spine_matte spine line (600-dpi thumb coords).
  bed_matte/spine_matte are the source detectors; the cache just avoids re-
  running them (~8 min) on every fit. Delete the cache to force a rebuild.
"""
import os, sys, json
import numpy as np

# --------------------------------------------------------------------------- #
#  CONSTANTS  (spatial values in MASTER 2400-dpi px unless suffixed _600)      #
# --------------------------------------------------------------------------- #
MASTER_DPI   = 2400
THUMB_DPI    = 600
SCALE        = MASTER_DPI // THUMB_DPI            # 600-thumb px -> master px (=4)

# A4 in master px:  297mm & 210mm at 2400 dpi.
MM_PER_IN    = 25.4
A4_H = round(297.0 / MM_PER_IN * MASTER_DPI)      # 28063
A4_W = round(210.0 / MM_PER_IN * MASTER_DPI)      # 19843

# Vertical fit search grid for B (px above logo baseline). Baseline ~27600,
# sheet top at 0, so B up to ~ anchor_y; step fine enough for sub-mm.
B_MIN, B_MAX, B_STEP = 26000, 28063, 5

# A bed/spine edge counts as a real content boundary only if the detector
# actually applied the cut (HIGH-confidence or PRIOR-accepted). LOW/NONE/REJECT
# -> treat that edge as flush / full-bleed content (boundary at the sheet edge).
APPLIED = ("HIGH", "PRIOR")

# Only trust a page's spine for the global spine-vs-logo average when the spine
# detector is HIGH confidence (a real neighbor boundary was locked).
SPINE_OK = ("HIGH",)

PATHS = dict(
    logo   = "/Users/mist/DNB/8609/tmp/logo_positions.json",
    matte  = "/Users/mist/DNB/8609/tmp/matte_cache.json",
    out    = "/Users/mist/DNB/8609/tmp/crop_windows.json",
)


# --------------------------------------------------------------------------- #
def _content_box(m):
    """Content rectangle of a page in MASTER px, from its bed_matte edges.
    top/bottom always meaningful; left/right only when the bed cut was applied
    (else the content runs to the sheet edge). Returns (top,bottom,left,right,
    Wm,Hm)."""
    Wm, Hm = m["w600"] * SCALE, m["h600"] * SCALE
    bed = m["bed"]
    def cut(edge):
        e = bed[edge]
        return e["cut_px"] * SCALE if e["decision"] in APPLIED else 0.0
    top    = cut("top")
    bottom = Hm - cut("bottom")
    left   = cut("left")
    right  = Wm - cut("right")
    return top, bottom, left, right, Wm, Hm


def _spine_master(m):
    """Spine x at the vertical centre of the page, in MASTER px, or None."""
    sp = m["spine"]
    if sp.get("conf") not in SPINE_OK or sp.get("x_top") is None:
        return None
    return 0.5 * (sp["x_top"] + sp["x_bot"]) * SCALE


# --------------------------------------------------------------------------- #
def main():
    logo  = {p["page"]: p for p in json.load(open(PATHS["logo"]))}
    if not os.path.exists(PATHS["matte"]):
        sys.exit(f"missing {PATHS['matte']} -- run build_matte_cache.py first")
    matte = json.load(open(PATHS["matte"]))
    pages = sorted(logo)

    # ---- gather per-page geometry ---------------------------------------- #
    P = {}
    for n in pages:
        lo = logo[n]; m = matte[str(n)]
        top, bot, left, right, Wm, Hm = _content_box(m)
        P[n] = dict(
            parity   = "even" if n % 2 == 0 else "odd",
            found    = lo["found"],
            anchor_x = lo["anchor_x"], anchor_y = lo["anchor_y"],
            ctop=top, cbot=bot, cleft=left, cright=right, Wm=Wm, Hm=Hm,
            spine    = _spine_master(m),
        )

    found = [n for n in pages if P[n]["found"]]

    # ===================================================================== #
    #  VERTICAL GLOBAL FIT  (choose B; A = A4_H - B)                         #
    #  minimise  sum_p [ max(0, B - t_p) + max(0, A - s_p) ]                 #
    #     t_p = anchor_y - content_top   (baseline->content top)            #
    #     s_p = content_bottom - anchor_y(baseline->content bottom)         #
    #  top_overhang = alpha above real content; bottom_overhang = alpha      #
    #  below it. Convex in B -> grid search over found pages.                #
    # ===================================================================== #
    t = np.array([P[n]["anchor_y"] - P[n]["ctop"] for n in found])
    s = np.array([P[n]["cbot"] - P[n]["anchor_y"] for n in found])
    Bs = np.arange(B_MIN, B_MAX + 1, B_STEP)
    cost = np.array([
        np.clip(B - t, 0, None).sum() + np.clip((A4_H - B) - s, 0, None).sum()
        for B in Bs])
    B = int(Bs[cost.argmin()])
    A = A4_H - B

    # ===================================================================== #
    #  HORIZONTAL GLOBAL FIT  (per-parity averaged spine-vs-logo offset)     #
    #     even: inner=right = anchor_x + S_even ;  x0 = x1 - A4_W            #
    #     odd : inner=left  = anchor_x + S_odd  ;  x1 = x0 + A4_W            #
    # ===================================================================== #
    S, spine_stat = {}, {}
    for par in ("even", "odd"):
        offs = [P[n]["spine"] - P[n]["anchor_x"] for n in found
                if P[n]["parity"] == par and P[n]["spine"] is not None]
        S[par] = float(np.mean(offs))
        spine_stat[par] = dict(n=len(offs), mean=float(np.mean(offs)),
                               std=float(np.std(offs)),
                               min=float(np.min(offs)), max=float(np.max(offs)))
    # implied fixed logo-vs-outer-trim offset (constant, per parity)
    outer_off = {"even": A4_W - S["even"],   # even: outer=left; anchor_x - x0
                 "odd":  A4_W + S["odd"]}     # odd : outer=right; x1 - anchor_x

    # ===================================================================== #
    #  NO-LOGO ANCHOR RECONSTRUCTION (interpolation)                        #
    #  logo offset vs the page's own content box is near-constant per parity #
    #     rel_bot   = content_bottom - anchor_y                             #
    #     rel_outer = anchor_x - content_left   (even) |                    #
    #                 content_right - anchor_x  (odd)                       #
    #  reconstruct: anchor_y = content_bottom - median(rel_bot);            #
    #               anchor_x = content_left/right +/- median(rel_outer).    #
    #  We also report the model's residual on FOUND pages = the honest       #
    #  interpolation error.                                                  #
    # ===================================================================== #
    rel = {"even": dict(bot=[], out=[]), "odd": dict(bot=[], out=[])}
    for n in found:
        p = P[n]; par = p["parity"]
        rel[par]["bot"].append(p["cbot"] - p["anchor_y"])
        rel[par]["out"].append(p["anchor_x"] - p["cleft"] if par == "even"
                               else p["cright"] - p["anchor_x"])
    med = {par: dict(bot=float(np.median(rel[par]["bot"])),
                     out=float(np.median(rel[par]["out"]))) for par in rel}
    # interpolation error = residual of the median model on found pages
    interp_err = {}
    for par in rel:
        rb = np.array(rel[par]["bot"]); ro = np.array(rel[par]["out"])
        interp_err[par] = dict(
            y_resid_std=float(np.std(rb - med[par]["bot"])),
            x_resid_std=float(np.std(ro - med[par]["out"])),
            y_resid_max=float(np.max(np.abs(rb - med[par]["bot"]))),
            x_resid_max=float(np.max(np.abs(ro - med[par]["out"]))))

    for n in pages:
        p = P[n]
        if p["found"]:
            continue
        par = p["parity"]
        p["anchor_y"] = int(round(p["cbot"] - med[par]["bot"]))
        p["anchor_x"] = int(round((p["cleft"] + med[par]["out"]) if par == "even"
                                  else (p["cright"] - med[par]["out"])))
        p["interp"] = True

    # ===================================================================== #
    #  EMIT PER-PAGE WINDOWS + measure alpha inside                          #
    # ===================================================================== #
    out_pages = []
    alpha_fracs, alpha_found, alpha_interp = [], [], []
    for n in pages:
        p = P[n]; par = p["parity"]; ax, ay = p["anchor_x"], p["anchor_y"]
        y0, y1 = ay - B, ay + A
        if par == "even":                       # logo left, spine right
            x1 = ax + S["even"]; x0 = x1 - A4_W
        else:                                    # logo right, spine left
            x0 = ax + S["odd"];  x1 = x0 + A4_W
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))

        # alpha estimate = window area minus overlap with the content rectangle.
        # inner content edge = this page's own spine when known, else sheet edge.
        sp = p["spine"]
        if par == "even":
            cr = sp if sp is not None else p["cright"]; cl = p["cleft"]
        else:
            cl = sp if sp is not None else p["cleft"];  cr = p["cright"]
        ix = max(0, min(x1, cr) - max(x0, cl))
        iy = max(0, min(y1, p["cbot"]) - max(y0, p["ctop"]))
        win_area = (x1 - x0) * (y1 - y0)
        alpha = 1.0 - (ix * iy) / win_area
        alpha_fracs.append(alpha)
        (alpha_interp if p.get("interp") else alpha_found).append((alpha, n))

        out_pages.append(dict(
            page=n, parity=par, window=[x0, y0, x1, y1],
            anchor_x=int(ax), anchor_y=int(ay),
            confidence=("interp" if p.get("interp") else "logo"),
            alpha_frac=round(alpha, 4)))

    result = dict(
        note="A4 crop windows in MASTER 2400-dpi px. window=[x0,y0,x1,y1].",
        A4_H=A4_H, A4_W=A4_W,
        vertical=dict(A_below_baseline=A, B_above_baseline=B, sum=A + B,
                      baseline_output_y=B),
        horizontal=dict(spine_vs_logo_offset=S, outer_trim_offset=outer_off,
                        spine_stats=spine_stat),
        interp=dict(median_rel=med, residual=interp_err),
        pages=out_pages)
    json.dump(result, open(PATHS["out"], "w"), indent=1)

    # ---- report ---------------------------------------------------------- #
    af = np.array([a for a, _ in alpha_found]); ai = np.array([a for a, _ in alpha_interp])
    print(f"A4 master px: H={A4_H} W={A4_W}")
    print(f"VERTICAL  A(below)={A}  B(above)={B}  (A+B={A+B})  baseline@y={B} in window")
    tot = cost.min()
    print(f"  vertical fit cost (sum overhang px over {len(found)} found) = {tot:.0f}"
          f"  ~{tot/len(found):.0f} px/page")
    for par in ("even", "odd"):
        st = spine_stat[par]
        print(f"HORIZONTAL {par}: spine_vs_logo S={S[par]:+.0f}  (n={st['n']} "
              f"std={st['std']:.0f} range[{st['min']:+.0f},{st['max']:+.0f}])  "
              f"outer_trim_off={outer_off[par]:.0f}")
    print(f"INTERP residual (found-page model error): "
          + "  ".join(f"{par}: dy~{interp_err[par]['y_resid_std']:.0f}"
                      f"(max{interp_err[par]['y_resid_max']:.0f}) "
                      f"dx~{interp_err[par]['x_resid_std']:.0f}"
                      f"(max{interp_err[par]['x_resid_max']:.0f})" for par in ("even", "odd")))
    print(f"COVERAGE alpha-in-window: all mean={np.mean(alpha_fracs)*100:.1f}% "
          f"worst={max(alpha_fracs)*100:.1f}%")
    print(f"  logo pages  mean={af.mean()*100:.1f}% worst={af.max()*100:.1f}% "
          f"(p{alpha_found[int(af.argmax())][1]})")
    print(f"  interp pages mean={ai.mean()*100:.1f}% worst={ai.max()*100:.1f}% "
          f"(p{alpha_interp[int(ai.argmax())][1]})")
    print(f"wrote {PATHS['out']}  ({len(out_pages)} pages)")


if __name__ == "__main__":
    main()
