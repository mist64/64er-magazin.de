#!/usr/bin/env python3
"""Fill the UNKNOWN pixels. Two problems, two methods, because they are not the same problem.

  EDGE BANDS   the window overhangs the scan, or the bed/neighbour was cut away. These are runs
               of unknown at the START or END of a row or column, they are mostly page MARGIN,
               and they reach the image border. Filled by MIRRORING the known pixels back across
               the boundary.
  CLIP HOLES   punched through real content, interior, ~6 per page and small. Filled by
               DIFFUSION (cv2.inpaint), which is what diffusion is good at -- a smooth patch
               across a small gap surrounded on all sides by known content.

WHY NOT REPLICATE THE LAST PIXEL for the edges. That is what the sampler was accidentally doing
already, and it is why p007's outer 6.4mm came out as coloured streaks: the "last pixel" was the
last pixel of the SCAN -- scanner edge noise, std 113 per channel -- smeared across 604 px.
Replicating the last KNOWN pixel would fix that, but it still stretches whatever single line of
pixels happens to sit at the boundary. Mirroring continues the page's own texture instead, at the
same cost, and a margin reflected into a margin is indistinguishable from the real thing.

WHY NOT DIFFUSION FOR THE EDGES. A diffused band has no halftone screen, and Stage 3 classifies
regions BY screen energy -- a smooth 6mm band would read as "not screened" and could flip a
cluster's classification. Mirrored pixels carry the real screen, at the real angle.

NOTHING HERE IS SILENT: the sidecar (NNN_known.png) still marks every filled pixel as unknown,
so what was invented stays knowable and any later stage can still exclude it.
"""
import numpy as np


def _mirror_1d(line, known, max_reflect=None):
    """Fill the unknown run(s) at the ENDS of a 1-D line by reflecting the known part.

    line   (N, C) values;  known (N,) bool.  Returns filled copy. Interior gaps are left alone --
    they are holes, and holes are the diffusion path's job.
    """
    n = known.shape[0]
    if known.all() or not known.any():
        return line
    first = int(np.argmax(known))
    last = n - 1 - int(np.argmax(known[::-1]))
    out = line
    if first > 0:
        k = first
        src = np.arange(first, min(first + k, last + 1))          # mirror outward from `first`
        if src.size:
            ref = line[src][::-1]
            take = min(first, ref.shape[0])
            out[first - take:first] = ref[-take:] if take < ref.shape[0] else ref
            if take < first:                                       # region deeper than we can
                out[:first - take] = ref[0]                        # mirror: hold the far value
    if last < n - 1:
        k = n - 1 - last
        src = np.arange(max(last - k + 1, first), last + 1)
        if src.size:
            ref = line[src][::-1]
            take = min(k, ref.shape[0])
            out[last + 1:last + 1 + take] = ref[:take]
            if last + 1 + take < n:
                out[last + 1 + take:] = ref[take - 1] if take else line[last]
    return out


def _replicate_1d(line, known):
    """Edge-clamp: hold the last KNOWN value outward. The comparison method for the mirror."""
    n = known.shape[0]
    if known.all() or not known.any():
        return line
    first = int(np.argmax(known))
    last = n - 1 - int(np.argmax(known[::-1]))
    if first > 0:
        line[:first] = line[first]
    if last < n - 1:
        line[last + 1:] = line[last]
    return line


def mirror_edges(rgb, known, method="mirror"):
    """Fill the border-reaching unknown runs by reflecting about the ORIGINAL boundary.

    Rows and columns are computed INDEPENDENTLY from the untouched mask, and each unknown pixel
    takes whichever of the two is nearer to its own boundary. The previous version ran the row
    pass, marked its own output as known, and then let the column pass reflect about that moved
    axis using already-invented pixels as source -- so the result was not a reflection at all.
    Checked directly on p083: |fill[first-1-k] - src[first+k]| should be 0 for a true mirror and
    was 94, 89, 128, 72 ... Reflecting about the real boundary is what makes the fill continue
    the page instead of smearing it.
    """
    fn = _mirror_1d if method == "mirror" else _replicate_1d
    H, W = known.shape

    rowf = rgb.copy()
    for y in np.flatnonzero(~known.all(1) & known.any(1)):
        kn = known[y]
        if not (kn[0] and kn[-1]):
            rowf[y] = fn(rowf[y], kn)

    colf = rgb.copy()
    for x in np.flatnonzero(~known.all(0) & known.any(0)):
        kn = known[:, x]
        if not (kn[0] and kn[-1]):
            colf[:, x] = fn(colf[:, x], kn)

    # distance from each unknown pixel to its own row / column boundary; nearer one wins
    ys, xs = np.arange(H)[:, None], np.arange(W)[None, :]
    rowany, colany = known.any(1), known.any(0)
    rfirst = np.where(rowany, np.argmax(known, 1), W)[:, None]
    rlast = np.where(rowany, W - 1 - np.argmax(known[:, ::-1], 1), -1)[:, None]
    cfirst = np.where(colany, np.argmax(known, 0), H)[None, :]
    clast = np.where(colany, H - 1 - np.argmax(known[::-1], 0), -1)[None, :]
    drow = np.where(xs < rfirst, rfirst - xs, np.where(xs > rlast, xs - rlast, 0))
    dcol = np.where(ys < cfirst, cfirst - ys, np.where(ys > clast, ys - clast, 0))
    drow = np.where(rowany[:, None], drow, 1 << 30)
    dcol = np.where(colany[None, :], dcol, 1 << 30)

    unk = ~known
    out = rgb.copy()
    take_row = unk & (drow <= dcol)
    take_col = unk & (dcol < drow)
    out[take_row] = rowf[take_row]
    out[take_col] = colf[take_col]
    return out


def diffuse_holes(rgb, known, radius=4, pad=24, max_area=None):
    """cv2.inpaint each INTERIOR unknown component, on a small crop around it.

    Interior = does not touch the image border; that is what separates a clip hole from an edge
    band. Cropping matters: cv2.inpaint on a 557 MP page would be absurd, and the holes are a few
    hundred px across.
    """
    import cv2
    from scipy import ndimage as ndi
    unk = ~known
    if not unk.any():
        return rgb, 0
    lab, n = ndi.label(unk)
    if n == 0:
        return rgb, 0
    H, W = known.shape
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    out = rgb
    filled = 0
    for sl, i in zip(ndi.find_objects(lab), range(1, n + 1)):
        if sl is None or i in border:
            continue
        area = int((lab[sl] == i).sum())
        if max_area is not None and area > max_area:
            continue
        y0 = max(sl[0].start - pad, 0); y1 = min(sl[0].stop + pad, H)
        x0 = max(sl[1].start - pad, 0); x1 = min(sl[1].stop + pad, W)
        sub = np.ascontiguousarray(out[y0:y1, x0:x1])
        m = np.ascontiguousarray((lab[y0:y1, x0:x1] == i).astype(np.uint8))
        out[y0:y1, x0:x1] = cv2.inpaint(sub, m, radius, cv2.INPAINT_TELEA)
        filled += 1
    return out, filled


def fill(rgb, known, holes=True, method="mirror"):
    """Edge bands by `method`, interior holes by diffusion. Returns (filled_rgb, n_holes)."""
    out = mirror_edges(rgb, known, method)
    nh = 0
    if holes:
        out, nh = diffuse_holes(out, known)
    return out, nh
