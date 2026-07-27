#!/usr/bin/env python3
"""02b spine detector v2. Works in ABSOLUTE image x (no flip confusion).

Layout on the binding side:
  even page: [ page content | clean margin | NEIGHBOR block | (border) ]   (neighbor near RIGHT border)
  odd  page: [ (border) | NEIGHBOR block | clean margin | page content ]   (neighbor near LEFT border)

Primary signal = NEIGHBOR-CONTENT BOUNDARY: find, per horizontal band, the
neighbor ink/colour block nearest the binding border; the spine cut = that
block's edge facing the page interior. Gutter shadow is weak in these scans so
it is used only as a secondary confirm.

Per-band boundary points -> RANSAC line fit (allows tilt). Confidence gated on
#evidence-bands and residual. Overlay drawn for vision verification.
"""
import sys,json,numpy as np
from PIL import Image,ImageDraw

INNER_W=1200          # search band width on binding side (px @600dpi)
NB=28                 # horizontal bands
DARK_T=95             # luma<this => dark/ink pixel
CONTENT_DARK=0.05     # dark_frac above this => "content" column
CONTENT_SAT=0.17      # sat_mean above this => "content" column (colour)
CLEANRUN=70           # px of sustained clean to declare margin start
BLOCKMIN=20           # neighbor block must be at least this wide (px) to count
BORDER_NEAR=240       # neighbor block must START within this many px of the binding
                      # border (else it is the page's OWN text/content -> reject band)
RANSAC_THR=45         # px residual for inlier

def is_even(s): return int(s)%2==0
def load(p): return np.asarray(Image.open(p).convert('RGB'))
def sm(a,k):  return np.convolve(a,np.ones(k)/k,mode='same')

def col_signals(sub):
    """sub: HxWx3 slice. Returns per-column dark_frac, sat_mean over full height."""
    rgb=sub.astype(np.float32)
    luma=0.299*rgb[...,0]+0.587*rgb[...,1]+0.114*rgb[...,2]
    mx=rgb.max(-1);mn=rgb.min(-1);sat=np.where(mx>1,(mx-mn)/np.maximum(mx,1),0)
    return (luma<DARK_T).mean(0), sat.mean(0)

def band_boundary(content, even):
    """content: bool array over the INNER_W search columns, index 0 = interior-most
    of the search band, index -1 = binding border. Return spine x (in search-band
    coords) = page-facing edge of the neighbor block nearest the border, or None."""
    n=len(content)
    if even:
        # neighbor near border = HIGH index. scan from border (n-1) inward (dec).
        # find outer content block; its inner edge = spine.
        i=n-1
        # skip any clean gap right at border (white gutter gap)
        # find first content from border
        while i>=0 and not content[i]: i-=1
        if i<0: return None
        if (n-1)-i > BORDER_NEAR: return None   # content too far from border = page text
        outer_end=i
        # walk inward while (mostly) content, allowing small gaps
        clean=0; edge=i
        while i>=0:
            if content[i]:
                clean=0; edge=i
            else:
                clean+=1
                if clean>=CLEANRUN: break
            i-=1
        if outer_end-edge < BLOCKMIN: return None
        if edge <= 10: return None   # block reached interior limit = no clean gap (full-bleed/merged)
        return edge  # inner edge of neighbor block
    else:
        # neighbor near border = LOW index. scan from border (0) inward (inc).
        i=0
        while i<n and not content[i]: i+=1
        if i>=n: return None
        if i > BORDER_NEAR: return None          # content too far from border = page text
        outer_end=i
        clean=0; edge=i
        while i<n:
            if content[i]:
                clean=0; edge=i
            else:
                clean+=1
                if clean>=CLEANRUN: break
            i+=1
        if edge-outer_end < BLOCKMIN: return None
        if edge >= n-10: return None   # block reached interior limit = no clean gap (full-bleed/merged)
        return edge

def theil_sen(pts):
    ys=np.array([p[0] for p in pts],float);xs=np.array([p[1] for p in pts],float)
    sl=[]
    for i in range(len(ys)):
        for j in range(i+1,len(ys)):
            if ys[j]!=ys[i]: sl.append((xs[j]-xs[i])/(ys[j]-ys[i]))
    if not sl: return 0.0,float(np.median(xs))
    a=np.median(sl);b=np.median(xs-a*ys);return a,b

def ransac(pts,thr=RANSAC_THR,iters=4):
    P=list(pts)
    for _ in range(iters):
        if len(P)<4: break
        a,b=theil_sen([(y,x) for y,x in P])
        keep=[(y,x) for (y,x) in P if abs(x-(a*y+b))<thr]
        if len(keep)==len(P) or len(keep)<4: P=keep if len(keep)>=4 else P; break
        P=keep
    a,b=theil_sen([(y,x) for y,x in P])
    resid=float(np.std([x-(a*y+b) for y,x in P])) if len(P)>=2 else 999
    return a,b,len(P),resid

def detect(stem, draw=True):
    rgb=load(f'/Users/mist/DNB/8609/thumbs_600/{stem}.png')
    h,w,_=rgb.shape; even=is_even(stem)
    if even: x_off=w-INNER_W; sub=rgb[:,x_off:w,:]
    else:    x_off=0;         sub=rgb[:,0:INNER_W,:]
    pts=[]           # (y_center, abs_x)
    raw=[]
    for b in range(NB):
        y0=b*h//NB;y1=(b+1)*h//NB
        df,st=col_signals(sub[y0:y1])
        df=sm(df,11); st=sm(st,11)
        content=(df>CONTENT_DARK)|(st>CONTENT_SAT)
        bx=band_boundary(content,even)
        yc=(y0+y1)//2
        if bx is not None:
            pts.append((yc, x_off+bx))
            raw.append((yc,x_off+bx))
    res={'stem':stem,'even':even,'n_evidence':len(pts),'NB':NB}
    line=None
    if len(pts)>=6:
        a,b,n,r=ransac(pts)
        tilt=float(np.degrees(np.arctan2(a*h,h)))
        res['fit']={'tilt_deg':round(tilt,3),'x_at_ytop':round(b,1),'x_at_ybot':round(a*h+b,1),
                    'inliers':n,'resid_px':round(r,1)}
        res['confident']= (n>=6 and r<RANSAC_THR)
        line=(a,b)
    else:
        res['confident']=False
    if draw:
        im=Image.fromarray(rgb).convert('RGB');dr=ImageDraw.Draw(im)
        for (yc,xx) in raw:
            dr.ellipse([xx-7,yc-7,xx+7,yc+7],outline=(255,0,255),width=4)
        if line:
            a,b=line
            dr.line([(a*y+b,y) for y in range(0,h,20)],fill=(0,220,0),width=6)
        if even: cx0,cx1=w-1000,w
        else: cx0,cx1=0,1000
        crop=im.crop((cx0,0,cx1,h)); crop=crop.resize((crop.width//2,crop.height//4))
        crop.save(f'/Users/mist/DNB/8609/tmp/spine_{stem}.png')
    print(json.dumps(res))
    return res

if __name__=='__main__':
    for s in sys.argv[1:]: detect(s)
