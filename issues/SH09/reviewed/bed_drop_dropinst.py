#!/usr/bin/env python3
# INSTRUMENT, read-only, writes nothing: measures what r005_masters_sheet's bed drop (level_and_trace, last block)
# removes INSIDE the line-traced page.  Run from the repo root: ISSUE=<id> .venv/bin/python issues/SH09/reviewed/bed_drop_dropinst.py <pages>
# Built for SH09 p030 (2026-11-15).  Run on all 168 SH09 pages; NOT run on the eleven other r005 issues
# (8610 8611 8612 8701 SH8602-SH8608): owner 2026-11-14, "just do this issue."  See WORKFLOW_ERRATA.md, r005 bed drop.
"""Instrument r005's bed drop: which pixels inside the line-traced page it removes.  Read-only.
argv: pages.  ISSUE from env.  Writes nothing."""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path("tools/img/scan2ocr/rules").resolve()))
import r005_masters_sheet as R
import scipy.ndimage as ND
MM=R.MM
orig=R.ND.label
for p in map(int,sys.argv[1:]):
    t=R.level_and_trace(p)
    arr=t.arr; h,w=t.h,t.w
    ys,xs=np.arange(h),np.arange(w)
    line=((xs[None,:]>=t.xl[:,None])&(xs[None,:]<=t.xr[:,None])&(ys[:,None]>=t.yt[None,:])&(ys[:,None]<=t.yb[None,:]))
    removed=line&~t.keep
    lum=arr.mean(2)
    lab,k=ND.label(removed); sz=np.bincount(lab.ravel())[1:] if k else np.array([0])
    print(f"p{p:03d} finder {t.finder} dropped comps {t.dropped}  removed inside line-box {removed.sum()/MM/MM:8.1f} mm2 "
          f"({removed.sum()/line.sum()*100:.3f}% of page)  largest {sz.max()/MM/MM:.1f} mm2  mean lum {lum[removed].mean() if removed.any() else 0:.1f}  "
          f"prop-mask share {(R.prop_mask(arr)[removed]).mean() if removed.any() else 0:.2f}", flush=True)
