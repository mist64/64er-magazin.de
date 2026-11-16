"""Exercise r005's BED_REACH_MM cap on a synthetic sheet, both ways.

Run it after changing BED_REACH_MM.  It reads the constant OUT OF THE SOURCE
rather than hardcoding one, because the first version of this test was written
for 5.0 mm and its fixtures silently stopped asserting what they claimed when
the value moved -- a planted "sliver 2 mm inside the line" is a thing the cap is
now SUPPOSED to leave alone.

It also plants its fixtures relative to the cap, so every case stays meaningful
at any D.  The run that matters most is OUTSIDE_IS_RETAINED: it states, out
loud, the price of a small D.
"""
import os, re, sys
import numpy as np
import scipy.ndimage as ND

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "r005_masters_sheet.py")
src = open(SRC, encoding="utf-8").read()
D = float(re.search(r"^BED_REACH_MM\s*=\s*([0-9.]+)", src, re.M).group(1))
FRAC = float(re.search(r"^BED_OUTSIDE_FRAC\s*=\s*([0-9.]+)", src, re.M).group(1))
print(f"read from {os.path.basename(SRC)}: BED_REACH_MM={D}  BED_OUTSIDE_FRAC={FRAC}")

MM = 4.0                                    # px per mm in this toy
h, w = 1400, 1000
ys, xs = np.arange(h), np.arange(w)
xl = np.full(h, 40.0); xr = np.full(h, 700.0)       # 300 px (75 mm) of bed right
yt = np.full(w, 40.0); yb = np.full(w, h - 40.0)
keep0 = ((xs[None, :] >= xl[:, None]) & (xs[None, :] <= xr[:, None]) &
         (ys[:, None] >= yt[None, :]) & (ys[:, None] <= yb[None, :]))

def nearmask(reach_mm):
    r = reach_mm * MM
    n = (xs[None, :] - xl[:, None]) <= r
    n |= (xr[:, None] - xs[None, :]) <= r
    n |= (ys[:, None] - yt[None, :]) <= r
    n |= (yb[None, :] - ys[:, None]) <= r
    return n

def run(bedlike, cap=True):
    lab, _ = ND.label(bedlike)
    touching = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    touching.discard(0)
    if not touching:
        return keep0.copy(), 0
    labels = np.array(sorted(touching))
    total = ND.sum(np.ones_like(lab, bool), lab, labels)
    outside = ND.sum(~keep0, lab, labels)
    doomed = labels[(outside / np.maximum(total, 1)) > FRAC]
    k = keep0.copy()
    if len(doomed):
        k &= ~(np.isin(lab, doomed) & nearmask(D)) if cap else ~np.isin(lab, doomed)
    return k, len(doomed)

fails = []
def check(name, ok, detail, population=None):
    """`population` is the number of pixels the assertion is ABOUT.

    An assertion over an empty set is reported as VACUOUS and counted as a
    failure, never as a pass.  Found the hard way: with the cap disabled this
    test printed "deep interior survives: 0/0 px kept" in green, because at a
    large D the fixture has no deep interior left to survive.  A check that
    asserts nothing must not look like a check that passed.
    """
    if population is not None and population == 0:
        print(f"  VACUOUS  {name}: {detail} -- the set is EMPTY, this asserts nothing")
        fails.append(name + " (vacuous)")
        return
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if not ok:
        fails.append(name)

# The 031 shape: a big bed field beyond the fore edge plus a tint panel that
# bleeds to it.  73 % of the component lies outside, so it IS doomed.
panel_mm = 30.0
B = np.zeros((h, w), bool)
B[:, 700:] = True
B[:, 700 - int(panel_mm * MM):700] = True
frac_out = (B & ~keep0).sum() / B.sum()
check("the fixture is actually doomed", frac_out > FRAC,
      f"{frac_out:.0%} of the component lies outside the line (needs > {FRAC:.0%})")

kNew, nN = run(B, cap=True)
kOld, _ = run(B, cap=False)
near = nearmask(D)
deep = keep0 & B & ~near
band = keep0 & B & near
check("deep interior survives", int((deep & kNew).sum()) == int(deep.sum()),
      f"{int((deep & kNew).sum())}/{int(deep.sum())} px kept past {D} mm",
      population=int(deep.sum()))
check("the band within D is still dropped", int((band & ~kNew).sum()) == int(band.sum()),
      f"{int((band & ~kNew).sum())}/{int(band.sum())} px dropped within {D} mm",
      population=int(band.sum()))
check("the cap is what changed it",
      int((keep0 & ~kOld).sum()) > int((keep0 & ~kNew).sum()),
      f"uncapped loses {int((keep0 & ~kOld).sum())} px, capped loses {int((keep0 & ~kNew).sum())}")

# A sliver of bed poking HALF of D past the line must still go whole.
shallow = D / 2
A = np.zeros((h, w), bool); A[:, :40 + int(shallow * MM)] = True
kA, _ = run(A, cap=True)
got, want = int((keep0 & A & ~kA).sum()), int((keep0 & A).sum())
check(f"bed {shallow} mm inside the line still goes whole", got == want,
      f"{got}/{want} px", population=want)

# ...and bed poking FURTHER than D is deliberately RETAINED.  This is the price
# of a small D and the reason the bed-RETAINED sweep exists: a print-lost sweep
# cannot see this at all.
over = D + 1.0
C = np.zeros((h, w), bool); C[:, :40 + int(over * MM)] = True
kC, _ = run(C, cap=True)
beyond = keep0 & C & ~nearmask(D)
check(f"bed {over} mm inside the line is RETAINED (by design)",
      int((beyond & kC).sum()) == int(beyond.sum()),
      f"{int((beyond & kC).sum())}/{int(beyond.sum())} px kept -- the bed-retained sweep is what catches this in the real world",
      population=int(beyond.sum()))

# A photo wholly inside, touching nothing, is never considered.
P = np.zeros((h, w), bool); P[200:400, 200:300] = True
kP, nP = run(P, cap=True)
check("an interior photo is untouched", int((keep0 & ~kP).sum()) == 0 and nP == 0,
      f"{int((keep0 & ~kP).sum())} px lost, {nP} components doomed")

print(f"\n{len(fails)} failed" if fails else "\nall checks passed")
sys.exit(1 if fails else 0)
