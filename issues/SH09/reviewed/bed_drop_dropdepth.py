#!/usr/bin/env python3
# INSTRUMENT, read-only, writes nothing: measures what r005_masters_sheet's bed drop (level_and_trace, last block)
# removes INSIDE the line-traced page.  Run from the repo root: ISSUE=<id> .venv/bin/python issues/SH09/reviewed/bed_drop_dropdepth.py <pages>
# Built for SH09 p030 (2026-11-15).  Run on all 168 SH09 pages; NOT run on the eleven other r005 issues
# (8610 8611 8612 8701 SH8602-SH8608): owner 2026-11-14, "just do this issue."  See WORKFLOW_ERRATA.md, r005 bed drop.
"""Per dropped component: area inside the line box, and how deep it reaches (mm from the line-box edge).  Read-only."""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path("tools/img/scan2ocr/rules").resolve()))
import r005_masters_sheet as R, scipy.ndimage as ND
MM=R.MM
for p in map(int,sys.argv[1:]):
    t=R.level_and_trace(p); arr=t.arr; h,w=t.h,t.w
    ys,xs=np.arange(h),np.arange(w)
    line=((xs[None,:]>=t.xl[:,None])&(xs[None,:]<=t.xr[:,None])&(ys[:,None]>=t.yt[None,:])&(ys[:,None]<=t.yb[None,:]))
    lum=arr.mean(2,dtype=np.float32); prop=R.prop_mask(arr); bedlike=(lum<R.BED_LUM)|prop
    lab,_=ND.label(bedlike)
    touching=set(lab[0,:])|set(lab[-1,:])|set(lab[:,0])|set(lab[:,-1]); touching.discard(0)
    if not touching: continue
    labels=np.array(sorted(touching)); total=ND.sum(np.ones_like(lab,bool),lab,labels); outside=ND.sum(~line,lab,labels)
    doomed=labels[(outside/np.maximum(total,1))>R.BED_OUTSIDE_FRAC]
    depth=ND.distance_transform_edt(line)/MM
    for l in doomed:
        ins=(lab==l)&line
        n=int(ins.sum())
        if n==0: continue
        d=depth[ins]
        print(f"p{p:03d} comp {l} inside {n/MM/MM:9.2f} mm2  maxdepth {d.max():7.2f} mm  p99 {np.percentile(d,99):6.2f}  p50 {np.median(d):5.2f}  prop {prop[ins].mean():.2f}  lum {lum[ins].mean():5.1f}", flush=True)
