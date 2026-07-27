#!/usr/bin/env python3
"""Draw candidate spine detectors over the inner-edge band and save an overlay
for vision verification. Works in BAND coordinates (x grows OUTWARD from page
interior toward spine/neighbor), then maps back to full-image x for drawing.

Detectors:
  SHADOW (red)   : gutter-shadow luma trough, per band, robustly line-fit.
  NEIGHBOR(green): outward edge of clean-paper margin = where neighbor ink/colour
                   starts (cleanliness drops), per band, line-fit.
  SPECKS (blue)  : vertical fold-speck line (dark dust/perforations in gutter).
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

DPI=600
INNER_W=1100
DARK_T=90
NB=24                    # horizontal bands for line fitting
PAPER_LUMA=150           # clean paper is brighter than this
SAT_PAPER=0.14           # clean paper saturation below this
SPECK_LO,SPECK_HI=12,120

def load(p): return np.asarray(Image.open(p).convert('RGB'))
def is_even(s): return int(s)%2==0

def get_band(rgb,even):
    h,w,_=rgb.shape
    if even:
        band=rgb[:,w-INNER_W:w,:][:,::-1,:]; x0=w-INNER_W; flipped=True
    else:
        band=rgb[:,0:INNER_W,:]; x0=0; flipped=False
    return band,x0,flipped,w

def band_to_real(xb,x0,flipped,w):
    # band x -> full-image x
    if flipped:  # band x=0 -> real x=w-1
        return (w-1)-xb
    return x0+xb

def channels(band):
    rgb=band.astype(np.float32)
    luma=0.299*rgb[...,0]+0.587*rgb[...,1]+0.114*rgb[...,2]
    mx=rgb.max(-1);mn=rgb.min(-1)
    sat=np.where(mx>1,(mx-mn)/np.maximum(mx,1),0)
    return luma,sat

def smooth(a,k):
    return np.convolve(a,np.ones(k)/k,mode='same')

def detect_shadow(luma):
    h,w=luma.shape; pts=[]
    for b in range(NB):
        y0=b*h//NB;y1=(b+1)*h//NB
        col=smooth(luma[y0:y1].mean(0),25)
        s=int(w*0.10);e=int(w*0.92)
        xi=s+int(np.argmin(col[s:e]))
        depth=np.median(col)-col[xi]
        pts.append(((y0+y1)//2,xi,depth))
    return pts

def detect_neighbor(luma,sat):
    """Per band: cleanliness(x)=paper if luma>PAPER_LUMA & sat<SAT_PAPER.
    Find outward end of the contiguous clean run that starts from interior.
    We scan from interior (x=0) outward; allow small gaps; stop where a
    sustained non-clean run (neighbor ink/colour/shadow) begins."""
    h,w=luma.shape; pts=[]
    for b in range(NB):
        y0=b*h//NB;y1=(b+1)*h//NB
        lu=smooth(luma[y0:y1].mean(0),15)
        st=smooth(sat[y0:y1].mean(0),15)
        clean=(lu>PAPER_LUMA)&(st<SAT_PAPER)
        # from interior outward, find first index where next 60px are <50% clean
        win=60; boundary=None
        for x in range(int(w*0.05),w-win):
            if clean[x:x+win].mean()<0.5:
                boundary=x;break
        if boundary is None: boundary=w-1
        pts.append(((y0+y1)//2,boundary,1.0))
    return pts

def detect_specks(band,luma):
    h,w=luma.shape
    spk=(luma>SPECK_LO)&(luma<SPECK_HI)
    # only count isolated-ish dark: within margin zone use column histogram
    colcount=spk.sum(0).astype(float)
    colcount=smooth(colcount,9)
    # speck line = peak within middle margin zone
    s=int(w*0.15);e=int(w*0.85)
    xi=s+int(np.argmax(colcount[s:e]))
    return xi,colcount

def theil_sen(pts):
    ys=np.array([p[0] for p in pts],float);xs=np.array([p[1] for p in pts],float)
    sl=[]
    for i in range(len(ys)):
        for j in range(i+1,len(ys)):
            if ys[j]!=ys[i]: sl.append((xs[j]-xs[i])/(ys[j]-ys[i]))
    a=np.median(sl);b=np.median(xs-a*ys);return a,b

def ransac_line(pts,thr=40,iters=3):
    """Iterative Theil-Sen with residual rejection."""
    P=list(pts)
    for _ in range(iters):
        if len(P)<4: break
        a,b=theil_sen([(y,x) for y,x,_ in P])
        keep=[(y,x,d) for (y,x,d) in P if abs(x-(a*y+b))<thr]
        if len(keep)==len(P): break
        if len(keep)<4: break
        P=keep
    a,b=theil_sen([(y,x) for y,x,_ in P])
    resid=np.std([x-(a*y+b) for y,x,_ in P])
    return a,b,len(P),resid

def main():
    stem=sys.argv[1]
    src=f'/Users/mist/DNB/8609/thumbs_600/{stem}.png'
    rgb=load(src); even=is_even(stem)
    band,x0,flipped,w=get_band(rgb,even)
    luma,sat=channels(band)
    h=luma.shape[0]

    sh=detect_shadow(luma)
    # gate shadow pts by depth
    sh_good=[(y,x,d) for (y,x,d) in sh if d>8]
    nb=detect_neighbor(luma,sat)
    sx,colcount=detect_specks(band,luma)

    res={'stem':stem,'even':even}
    lines={}
    if len(sh_good)>=5:
        a,b,n,r=ransac_line(sh_good)
        lines['shadow']=(a,b);res['shadow']={'tilt_deg':round(np.degrees(np.arctan2(a*h,h)),3),'n':n,'resid':round(r,1),'b':round(b,1)}
    a,b,n,r=ransac_line(nb)
    lines['neighbor']=(a,b);res['neighbor']={'tilt_deg':round(np.degrees(np.arctan2(a*h,h)),3),'n':n,'resid':round(r,1),'b':round(b,1)}
    lines['specks']=(0.0,float(sx));res['specks_x']=int(sx)

    # draw
    im=Image.fromarray(rgb).convert('RGB'); dr=ImageDraw.Draw(im)
    colors={'shadow':(255,0,0),'neighbor':(0,200,0),'specks':(0,80,255)}
    for name,(a,b) in lines.items():
        pts=[]
        for y in range(0,h,20):
            xb=a*y+b
            xr=band_to_real(xb,x0,flipped,w)
            pts.append((xr,y))
        dr.line(pts,fill=colors[name],width=6)
    # crop to inner region for inspection (real coords)
    if even: cx0,cx1=w-900,w
    else: cx0,cx1=0,900
    crop=im.crop((cx0,0,cx1,h))
    crop=crop.resize((crop.width//2,crop.height//4))
    crop.save(f'/Users/mist/DNB/8609/tmp/spine_{stem}.png')
    print(json.dumps(res,indent=1))

if __name__=='__main__':
    main()
