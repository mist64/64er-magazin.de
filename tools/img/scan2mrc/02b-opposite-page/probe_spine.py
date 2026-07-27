#!/usr/bin/env python3
"""02b spine-probe: measure candidate signals column-by-column near the inner
(binding) edge of a split magazine scan, to locate the spine/gutter line.

EVEN page -> neighbor overlap on RIGHT edge (inner=right)
ODD  page -> neighbor overlap on LEFT  edge (inner=left)

Signals measured per column x in the inner search band:
  luma_mean   : mean brightness  (gutter shadow = trough)
  dark_frac   : fraction of very-dark pixels (neighbor ink + speck line)
  sat_mean    : mean HSV saturation (neighbor colored content; paper~low)
  spec_count  : count of small dark specks (fold dust / staple perforations)

Outputs a diagnostic profile plot + numbers; a separate overlay tool draws lines.
"""
import sys, os, json
import numpy as np
from PIL import Image

DPI = 600
INNER_W = 1100          # width of inner search band (px @600dpi ~1.8in)
DARK_T  = 90            # luma < this = "ink/dark"
SPECK_LO, SPECK_HI = 15, 110   # speck luma window (dark but not pure black frame)

def load(path):
    im = Image.open(path).convert('RGB')
    return np.asarray(im)

def is_even(stem):
    return int(stem) % 2 == 0

def inner_band(rgb, even):
    """Return (band_rgb, x0) where x0 is the x-offset of the band in full image.
    For even (inner=right) we FLIP horizontally so that in band-coords x
    increases going OUTWARD (page-interior -> spine -> neighbor). We record a
    flag so overlay can map back."""
    h, w, _ = rgb.shape
    if even:
        band = rgb[:, w-INNER_W:w, :]
        x0 = w-INNER_W
        band = band[:, ::-1, :]   # flip: band x=0 is page interior, x grows outward
        flipped = True
    else:
        band = rgb[:, 0:INNER_W, :]
        x0 = 0
        flipped = False
    return band, x0, flipped

def col_profiles(band):
    rgb = band.astype(np.float32)
    luma = (0.299*rgb[...,0]+0.587*rgb[...,1]+0.114*rgb[...,2])
    mx = rgb.max(-1); mn = rgb.min(-1)
    sat = np.where(mx>1, (mx-mn)/np.maximum(mx,1), 0.0)
    luma_mean = luma.mean(0)
    dark = (luma < DARK_T)
    dark_frac = dark.mean(0)
    sat_mean = sat.mean(0)
    return luma, luma_mean, dark_frac, sat_mean

def band_analysis(luma, nb=16):
    """Per horizontal band: find the gutter-shadow trough x (min of smoothed
    column-luma within band). Returns list of (y_center, trough_x, depth)."""
    h, w = luma.shape
    out=[]
    for b in range(nb):
        y0=b*h//nb; y1=(b+1)*h//nb
        col = luma[y0:y1].mean(0)
        # smooth
        k=25
        ker=np.ones(k)/k
        cs=np.convolve(col, ker, mode='same')
        # search only outer half of band (spine is outward of interior text)
        # but keep full; report global min in a mid zone
        s= int(w*0.15); e=int(w*0.95)
        xi = s+int(np.argmin(cs[s:e]))
        depth = np.median(cs) - cs[xi]
        out.append((( y0+y1)//2, xi, float(depth), float(cs[xi])))
    return out

def theil_sen(pts):
    """pts: list of (y,x). Fit x = a*y + b robustly. Return a,b."""
    ys=np.array([p[0] for p in pts],float); xs=np.array([p[1] for p in pts],float)
    slopes=[]
    n=len(ys)
    for i in range(n):
        for j in range(i+1,n):
            if ys[j]!=ys[i]:
                slopes.append((xs[j]-xs[i])/(ys[j]-ys[i]))
    a=np.median(slopes)
    b=np.median(xs-a*ys)
    return a,b

def main():
    stem=sys.argv[1]
    src=f'/Users/mist/DNB/8609/thumbs_600/{stem}.png'
    rgb=load(src)
    even=is_even(stem)
    band,x0,flipped=inner_band(rgb,even)
    luma,lm,df,sm=col_profiles(band)
    bands=band_analysis(luma)
    # robust line from trough points, weighted: drop low-depth (unreliable) bands
    good=[(y,x,d) for (y,x,d,v) in bands if d>3]
    res={'stem':stem,'even':even,'flipped':flipped,'x0':x0,'INNER_W':INNER_W,
         'band_troughs':[(int(y),int(x),round(d,1),round(v,1)) for (y,x,d,v) in bands]}
    if len(good)>=6:
        a,b=theil_sen([(y,x) for (y,x,d) in good])
        # tilt angle: dx over full height
        h=luma.shape[0]
        dx=a*h
        ang=np.degrees(np.arctan2(dx,h))
        res['fit']={'a':a,'b':b,'tilt_deg':round(float(ang),3),'dx_fullheight':round(float(dx),1)}
    # profile summary: locations of key features
    res['luma_min_x']=int(np.argmin(np.convolve(lm,np.ones(25)/25,mode='same')))
    print(json.dumps(res,indent=1))
    # save profiles for plotting
    np.savez(f'/Users/mist/DNB/8609/tmp/prof_{stem}.npz',
             lm=lm,df=df,sm=sm,bands=np.array(bands))

if __name__=='__main__':
    main()
