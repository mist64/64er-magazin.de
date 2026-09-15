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


def test_outer_edges_odd_is_mirrored():
    a = synthetic_frame("odd")
    e = S.outer_edges(a, "odd")
    h, w = a.shape[:2]
    assert abs(np.polyval(e["outer"], h / 2) - (w - 1)) < 3


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
