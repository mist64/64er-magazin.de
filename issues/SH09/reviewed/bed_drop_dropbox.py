#!/usr/bin/env python3
# INSTRUMENT, read-only, writes nothing: measures what r005_masters_sheet's bed drop (level_and_trace, last block)
# removes INSIDE the line-traced page.  Run from the repo root: ISSUE=<id> .venv/bin/python issues/SH09/reviewed/bed_drop_dropbox.py <pages>
# Built for SH09 p030 (2026-11-15).  Run on all 168 SH09 pages; NOT run on the eleven other r005 issues
# (8610 8611 8612 8701 SH8602-SH8608): owner 2026-11-14, "just do this issue."  See WORKFLOW_ERRATA.md, r005 bed drop.
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path("tools/img/scan2ocr/rules").resolve()))
import r005_masters_sheet as R, scipy.ndimage as ND
MM=R.MM
for p in map(int,sys.argv[1:]):
    t=R.level_and_trace(p); h,w=t.h,t.w
    ys,xs=np.arange(h),np.arange(w)
    line=((xs[None,:]>=t.xl[:,None])&(xs[None,:]<=t.xr[:,None])&(ys[:,None]>=t.yt[None,:])&(ys[:,None]<=t.yb[None,:]))
    pre=t.keep.copy(); t.locate(); rem=line&~pre; applied=line&~t.keep
    lab,k=ND.label(rem); sz=np.bincount(lab.ravel()); objs=ND.find_objects(lab)
    out=[]
    for i in (np.argsort(sz[1:])[::-1][:3]+1 if k else []):
        sl=objs[i-1]; out.append(f"{sz[i]/MM/MM:.1f}mm2@x{sl[1].start}-{sl[1].stop},y{sl[0].start}-{sl[0].stop}")
    print(f"p{p:03d} removed {rem.sum()/MM/MM:.1f} mm2, still removed after locate {applied.sum()/MM/MM:.1f} mm2, frame {w}x{h}; dist to line-box edge: comps {' '.join(out)}", flush=True)
