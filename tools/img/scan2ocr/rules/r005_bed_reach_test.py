import numpy as np, scipy.ndimage as ND
MM = 4.0                                   # px per mm in this toy
BED_REACH_MM, BED_OUTSIDE_FRAC = 5.0, 0.5
h, w = 1400, 1000
ys, xs = np.arange(h), np.arange(w)
xl = np.full(h, 40.0); xr = np.full(h, 700.0)      # 300 px (75 mm) of bed to the right
yt = np.full(w, 40.0); yb = np.full(w, h - 40.0)
keep0 = ((xs[None,:] >= xl[:,None]) & (xs[None,:] <= xr[:,None]) &
         (ys[:,None] >= yt[None,:]) & (ys[:,None] <= yb[None,:]))

def run(bedlike, keep, cap=True):
    lab,_ = ND.label(bedlike)
    touching = set(lab[0,:])|set(lab[-1,:])|set(lab[:,0])|set(lab[:,-1]); touching.discard(0)
    if not touching: return keep.copy(), 0
    labels = np.array(sorted(touching))
    total = ND.sum(np.ones_like(lab,bool), lab, labels)
    outside = ND.sum(~keep, lab, labels)
    doomed = labels[(outside/np.maximum(total,1)) > BED_OUTSIDE_FRAC]
    k = keep.copy()
    if len(doomed):
        if not cap:
            k &= ~np.isin(lab, doomed)
        else:
            reach = BED_REACH_MM*MM
            near =  (xs[None,:] - xl[:,None]) <= reach
            near |= (xr[:,None] - xs[None,:]) <= reach
            near |= (ys[:,None] - yt[None,:]) <= reach
            near |= (yb[None,:] - ys[:,None]) <= reach
            k &= ~(np.isin(lab,doomed) & near)
    return k, len(doomed)

# 031's shape: a big bed field outside the fore edge, plus a NARROW tendril of
# bed-coloured tint running 30 mm into the page over the full height.
B = np.zeros((h,w),bool)
B[:, 700:] = True                                   # bed outside the traced line
B[:, 700-int(30*MM):700] = True                     # the tint panel, 30 mm deep
lab,_ = ND.label(B)
tot = B.sum(); out = (B & ~keep0).sum()
print(f"component: {tot} px, {out} outside ({out/tot:.0%}) -> doomed={out/tot > 0.5}")

kNew,nN = run(B, keep0, cap=True)
kOld,nO = run(B, keep0, cap=False)
R = BED_REACH_MM*MM
nearmask =  (xs[None,:] - xl[:,None]) <= R
nearmask |= (xr[:,None] - xs[None,:]) <= R
nearmask |= (ys[:,None] - yt[None,:]) <= R
nearmask |= (yb[None,:] - ys[:,None]) <= R
deep = keep0 & B & ~nearmask
nearband = keep0 & B & ~deep
print(f"OLD  doomed={nO}  print lost inside page: {int((keep0 & ~kOld).sum())} px")
print(f"NEW  doomed={nN}  print lost inside page: {int((keep0 & ~kNew).sum())} px")
ok_deep = int((deep & kNew).sum()) == int(deep.sum())
ok_near = int((nearband & ~kNew).sum()) == int(nearband.sum())
ok_old  = int((keep0 & ~kOld).sum()) > int((keep0 & ~kNew).sum())
print(f"  deep px survive  {int((deep&kNew).sum())}/{int(deep.sum())}  -> {'PASS' if ok_deep else 'FAIL'}")
print(f"  near-edge dropped {int((nearband&~kNew).sum())}/{int(nearband.sum())} -> {'PASS' if ok_near else 'FAIL'}")
print(f"  cap is what changed it -> {'PASS' if ok_old else 'FAIL'}")

# and the sliver must STILL go whole
A = np.zeros((h,w),bool); A[:, :40+int(2*MM)] = True
kA,nA = run(A, keep0, cap=True)
got=int((keep0&A&~kA).sum()); want=int((keep0&A).sum())
print(f"  bed sliver still fully dropped {got}/{want} -> {'PASS' if got==want else 'FAIL'}")
