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
