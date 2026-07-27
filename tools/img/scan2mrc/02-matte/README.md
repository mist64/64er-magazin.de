# matte — page isolation (alpha matting)

Find each page's **paper boundary** and mark everything outside it as **unknown (alpha 0)**:
the top/bottom **bed wedges** (page not flush to the bed), the **yellow cardboard** (bottom backing),
the **neighbor-page strip** (spine-side overlap), and the **clip/staple holes**.

Principle: keep every genuine page pixel (incl. outer excess); fabricate nothing. Unknown pixels stay
translucent until an explicit later fill step. Runs after `deskew` (or builds the matte on the raw scan,
then rotates the RGBA with a transparent fill so pre-existing + rotation-added wedges are both alpha 0).

CONSTRAINT (why "dark = bed" is not enough): full-bleed dark pages (e.g. p047 Star NG-10 ad) have real
black ink to every edge — the detector must locate the true PAPER EDGE, not just border-connected dark.

Conventions: margins/measurements are resolution-relative (1px @600dpi == 4px @2400dpi, same mm).
For the top wedge: any alpha pixel forces every pixel above it (smaller Y) in that column to alpha too.
