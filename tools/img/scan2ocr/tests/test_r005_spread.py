import numpy as np

import r005_masters_spread as S
from r005_masters import MM, PAPER_RGB

PAPER = tuple(int(v) for v in PAPER_RGB)     # the built-in W
BED = (135, 128, 124)                          # 8610's grey bed strip
PROP = (250, 218, 113)                         # the yellow prop


def synthetic_frame(par="even", w=5500, h=7300, top_bed_mm=1.0, prop_mm=7.0,
                    fold_from_edge_mm=20.0, neighbour_rgb=(90, 120, 200)):
    """A levelled 600 dpi spread frame: bed on top, prop below, paper to the
    outer frame edge, a neighbour strip beyond the fold on the inner side."""
    a = np.empty((h, w, 3), np.uint8)
    a[:] = PAPER
    a[:int(top_bed_mm * MM)] = BED
    a[h - int(prop_mm * MM):] = PROP
    fold = int(fold_from_edge_mm * MM)
    if par == "even":
        a[:, w - fold:] = neighbour_rgb
    else:
        a[:, :fold] = neighbour_rgb
    return a


def test_outer_edges_even():
    a = synthetic_frame("even")
    e = S.outer_edges(a, "even")
    h, w = a.shape[:2]
    assert abs(np.polyval(e["top"], w / 2) - 1.0 * MM) < 2 * MM * 0.1 + 3
    assert abs(np.polyval(e["bot"], w / 2) - (h - 7.0 * MM)) < 3
    assert abs(np.polyval(e["outer"], h / 2) - 0) < 3          # paper to the frame
    assert abs(S.tilt(e["top"])) < 0.05
    assert e["source"] == "paper" and e["body"] > S.FULLBLEED_BODY_FRAC


def test_outer_edges_odd_is_mirrored():
    a = synthetic_frame("odd")
    e = S.outer_edges(a, "odd")
    h, w = a.shape[:2]
    assert abs(np.polyval(e["outer"], h / 2) - (w - 1)) < 3
    assert e["source"] == "paper"


def test_outer_edges_fullbleed_uses_frame_and_prop():
    # a cover: dark art to the trim, so the paper mask sees nothing but the bed
    # strip's neighbours -- top and outer are the frame, the bottom is the prop
    a = synthetic_frame("odd")
    h, w = a.shape[:2]
    a[int(1.0 * MM):h - int(7.0 * MM)] = (50, 50, 36)      # p200's median colour
    # p001's orange banner: prop-coloured art inside the foot, above the prop,
    # on the left third -- the bottom line is the prop's, not the banner's
    a[h - int(12.0 * MM):h - int(9.0 * MM), :w // 3] = PROP
    e = S.outer_edges(a, "odd")
    assert e["source"] == "fullbleed" and e["body"] < S.FULLBLEED_BODY_FRAC
    assert list(e["top"]) == [0.0, 0.0]
    assert abs(np.polyval(e["outer"], h / 2) - (w - 1)) < 1e-9
    assert abs(np.polyval(e["bot"], w / 2) - (h - 7.0 * MM)) < 3
    assert abs(S.tilt(e["bot"])) < 0.05
    assert list(S.outer_edges(a, "even")["outer"]) == [0.0, 0.0]


def with_holes(a, par, fold_from_edge_mm=10.0, ys_mm=(30, 43, 130, 143, 230, 243),
               d_mm=0.7, x_jitter_mm=0.1):
    """Six 0.7 mm holes on a line fold_from_edge_mm in from the inner frame
    edge -- 10 mm, where 8610's sheets600 have them (MEASURED 8.3-12.2 on
    p100/p101), inside S.HOLE_BAND_MM."""
    h, w = a.shape[:2]
    x = (w - fold_from_edge_mm * MM) if par == "even" else fold_from_edge_mm * MM
    r = d_mm * MM / 2
    yy, xx = np.mgrid[:h, :w]
    for i, y_mm in enumerate(ys_mm):
        cx = x + (x_jitter_mm * MM if i % 2 else -x_jitter_mm * MM)
        disc = (yy - y_mm * MM) ** 2 + (xx - cx) ** 2 <= r * r
        a[disc] = (20, 18, 18)
    return a, x


def test_find_holes_finds_six():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    gray = a.mean(2).astype(np.uint8)
    holes = S.find_holes(gray, "even")
    assert len(holes) == 6
    assert all(abs(cx - x) < 0.3 * MM for cx, cy, d in holes)
    assert all(0.5 < d < 1.0 for _, _, d in holes)


def test_find_holes_ignores_type_and_rules():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    h, w = a.shape[:2]
    a[int(100 * MM):int(100 * MM) + 4, w - int(14 * MM):w - int(6 * MM)] = 0    # a rule
    a[int(150 * MM):int(153 * MM), w - int(11 * MM):w - int(9 * MM)] = 0      # a 3 mm blob
    gray = a.mean(2).astype(np.uint8)
    assert len(S.find_holes(gray, "even")) == 6


def test_fit_fold_line():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even")
    h = a.shape[0]
    fold = S.fit_fold(S.find_holes(a.mean(2).astype(np.uint8), "even"), h)
    assert fold is not None and fold["n"] == 6
    assert abs(np.polyval(fold["poly"], h / 2) - x) < 0.2 * MM
    assert abs(S.tilt(fold["poly"])) < 0.1


def test_fit_fold_refuses_three_holes():
    a, x = with_holes(synthetic_frame("even", neighbour_rgb=PAPER), "even",
                      ys_mm=(30, 43, 130))
    assert S.fit_fold(S.find_holes(a.mean(2).astype(np.uint8), "even"),
                      a.shape[0]) is None


def test_neighbour_boundary_finds_colour_step():
    a = synthetic_frame("even", fold_from_edge_mm=18.0, neighbour_rgb=(90, 120, 200))
    h, w = a.shape[:2]
    nb = S.neighbour_boundary(a, "even")
    assert nb is not None
    assert abs(np.polyval(nb["poly"], h / 2) - (w - 18.0 * MM)) < 2


def test_neighbour_boundary_finds_colour_step_odd():
    # mirrors the even-parity test above: same fold depth, opposite side.  The
    # even path indexes its strip border-first (`inward = cols[::-1]`) and
    # maps back with `to_x(strip_w - edge)`; the odd path uses the strip
    # order directly and `to_x(edge)`.  A mirror bug in either mapping would
    # only show up on the parity it belongs to, so both are exercised here.
    a = synthetic_frame("odd", fold_from_edge_mm=18.0, neighbour_rgb=(90, 120, 200))
    h, w = a.shape[:2]
    nb = S.neighbour_boundary(a, "odd")
    assert nb is not None
    assert abs(np.polyval(nb["poly"], h / 2) - 18.0 * MM) < 2


def test_neighbour_boundary_none_on_blank_margin():
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    assert S.neighbour_boundary(a, "even") is None


def test_neighbour_boundary_rejects_far_from_prior():
    a = synthetic_frame("even", fold_from_edge_mm=18.0, neighbour_rgb=(90, 120, 200))
    h, w = a.shape[:2]
    assert S.neighbour_boundary(a, "even", prior_x=w - 40.0 * MM) is None


def test_ncc_peaks_at_the_paste():
    rng = np.random.default_rng(0)
    tmpl = S.load_template()
    th, tw = tmpl.shape
    region = 200 + 10 * rng.standard_normal((th + 400, tw + 600)).astype(np.float32)
    region[150:150 + th, 300:300 + tw] = tmpl
    m = S.ncc(region, tmpl)
    y, x = np.unravel_index(m.argmax(), m.shape)
    assert (y, x) == (150, 300) and m.max() > 0.95


def test_find_logo_even_page_bottom_left():
    tmpl = S.load_template()
    th, tw = tmpl.shape
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    g = a.mean(2).astype(np.uint8)
    h, w = g.shape
    y0, x0 = h - int(16 * MM) - th, int(24 * MM)
    g[y0:y0 + th, x0:x0 + tw] = tmpl.astype(np.uint8)
    r = S.find_logo(g, "even", tmpl)
    assert r is not None and r["score"] > 0.9
    assert (r["x"], r["y"]) == (x0, y0 + th)          # outer-bottom corner: bottom-LEFT


def test_find_logo_odd_page_bottom_right():
    tmpl = S.load_template()
    th, tw = tmpl.shape
    a = synthetic_frame("odd", neighbour_rgb=PAPER)
    g = a.mean(2).astype(np.uint8)
    h, w = g.shape
    y0, x0 = h - int(16 * MM) - th, w - int(24 * MM) - tw
    g[y0:y0 + th, x0:x0 + tw] = tmpl.astype(np.uint8)
    r = S.find_logo(g, "odd", tmpl)
    assert r is not None and (r["x"], r["y"]) == (x0 + tw, y0 + th)


def test_find_logo_none_on_blank():
    a = synthetic_frame("even", neighbour_rgb=PAPER)
    assert S.find_logo(a.mean(2).astype(np.uint8), "even", S.load_template()) is None


# --- cut: the window ---------------------------------------------------------

def synthetic_geom(page, w=5500, h=7300, fold_from_edge_mm=20.0, logo=True,
                   anchor_dx_mm=24.0, anchor_dy_mm=16.0):
    par = "even" if page % 2 == 0 else "odd"
    fold_x = w - fold_from_edge_mm * MM if par == "even" else fold_from_edge_mm * MM
    ax = anchor_dx_mm * MM if par == "even" else w - anchor_dx_mm * MM
    return {"page": page, "parity": par, "sheet_px": [w, h],
            "skew": {"angle": 0.0, "residual": 0.0},
            "edges": {"top": [0.0, 1.0 * MM], "bot": [0.0, h - 7.0 * MM],
                      "outer": [0.0, 0.0 if par == "even" else w - 1.0],
                      "source": "paper", "body": 0.9},
            "fold": {"source": "holes", "poly": [0.0, fold_x], "n": 6,
                     "residual_mm": 0.1, "tilt_deg": 0.0},
            "holes": [[fold_x, 40 * MM, 0.7]],
            "anchor": ({"source": "logo", "x": int(ax), "y": int(h - anchor_dy_mm * MM),
                        "score": 0.9, "bbox": [0, 0, 0, 0]} if logo else None),
            "notes": []}


def test_unknown_mask_marks_bed_prop_neighbour_and_hole():
    g = synthetic_geom(100)
    u = S.unknown_mask(g)
    w, h = g["sheet_px"]
    assert u[2, w // 2] and not u[int(2 * MM), w // 2]          # bed strip / paper
    assert u[h - 3, w // 2]                                        # prop
    assert u[h // 2, w - 5] and not u[h // 2, w - int(25 * MM)]  # beyond fold / inside
    assert u[int(40 * MM), int(w - 20 * MM)]                      # the hole disc


def test_fit_window_recovers_the_layout():
    # The synthetic frame is 233 x 309 mm with 1 mm bed, 7 mm prop and the fold
    # 20 mm in from the inner edge, so the KNOWN region (212.7 x 300.7 mm) holds
    # a 210 x 297 window with a little slack: the objective is flat over that
    # slack and argmin takes the first minimum, i.e. the smallest S and B --
    # the window at its LARGEST x0 and y0: against the foot, and against
    # whichever side edge is on the RIGHT -- the fold on an even page, the
    # outer edge on an odd one.  The expected offsets follow from that, to
    # within the 0.3 mm inset, the 0.75 mm the filled hole on the fold pushes
    # the even window off it, and one grid step.
    geoms = [synthetic_geom(p) for p in range(10, 30)]
    fit = S.fit_window(geoms)
    assert fit["stats"]["even"]["pages"] == fit["stats"]["odd"]["pages"] == 10
    tol = 1.0 * MM
    for par, page in (("even", 10), ("odd", 11)):
        g = synthetic_geom(page)
        w, h = g["sheet_px"]
        fold_x = g["fold"]["poly"][1]
        outer_x = g["edges"]["outer"][1]
        bot_y = g["edges"]["bot"][1]
        ax, ay = g["anchor"]["x"], g["anchor"]["y"]
        x0 = (fold_x if par == "even" else outer_x) - S.MASTER_W_PX
        y0 = bot_y - S.MASTER_H_PX
        S_, B_ = fit[par]
        assert abs(S_ - (ax - x0)) < tol, (par, S_, ax - x0)
        assert abs(B_ - (ay - y0)) < tol, (par, B_, ay - y0)


def test_anchor_of_without_logo_places_window_on_fold_and_foot():
    g = synthetic_geom(100, logo=False)
    source, x0, y0 = S.anchor_of(g)
    assert source == "edges"
    assert abs(x0 - (g["fold"]["poly"][1] - S.MASTER_W_PX)) < 1
    assert abs(y0 - (g["edges"]["bot"][1] - S.MASTER_H_PX)) < 1
    g = synthetic_geom(101, logo=False)
    source, x0, y0 = S.anchor_of(g)
    assert abs(x0 - g["fold"]["poly"][1]) < 1


def test_cut_page_is_a4_and_white_where_unknown():
    # The fit puts the window's foot on the bottom inset; this page's wordmark
    # sits 6 mm LOWER than the fitted pages', so its window runs 6 mm into the
    # prop, and that band must come out white.
    g = synthetic_geom(100, anchor_dy_mm=10.0)
    fit = S.fit_window([synthetic_geom(p) for p in range(10, 30)])
    sheet = synthetic_frame("even")
    master, unknown_frac, notes = S.cut_page(g, fit, sheet)
    assert master.shape == (S.MASTER_H_PX, S.MASTER_W_PX, 3)
    assert (master[-5:] == 255).all()             # the prop band is white
    assert (master[-int(6 * MM):] == 255).all()
    assert tuple(master[S.MASTER_H_PX // 2, S.MASTER_W_PX // 2]) == PAPER
    assert 0.015 < unknown_frac < 0.05
    assert notes == []
