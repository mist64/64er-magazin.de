#!/usr/bin/env python3
"""Diagnostic: plot per-column signal profiles in the inner band so we can SEE
where the fold sits. Band coords: x grows OUTWARD (interior -> spine -> neighbor).

Profiles:
  paper60  : 60th-percentile luma per column (paper shade; ink excluded) -> gutter shadow = dip
  dark_frac: fraction luma<DARK_T (text/neighbor ink)
  sat_mean : mean saturation (neighbor colour)
  speck    : dark-speck column count (fold dust/perforations)
"""
import sys,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

INNER_W=1100; DARK_T=90; SPECK_LO,SPECK_HI=12,120
def is_even(s): return int(s)%2==0
def load(p): return np.asarray(Image.open(p).convert('RGB'))

def band(rgb,even):
    h,w,_=rgb.shape
    if even: return rgb[:,w-INNER_W:w,:][:,::-1,:]
    return rgb[:,0:INNER_W,:]

def main():
    stem=sys.argv[1]
    rgb=load(f'/Users/mist/DNB/8609/thumbs_600/{stem}.png')
    even=is_even(stem); bd=band(rgb,even).astype(np.float32)
    luma=0.299*bd[...,0]+0.587*bd[...,1]+0.114*bd[...,2]
    mx=bd.max(-1);mn=bd.min(-1);sat=np.where(mx>1,(mx-mn)/np.maximum(mx,1),0)
    paper60=np.percentile(luma,60,axis=0)
    dark_frac=(luma<DARK_T).mean(0)
    sat_mean=sat.mean(0)
    spk=((luma>SPECK_LO)&(luma<SPECK_HI)).sum(0).astype(float)
    def sm(a,k=15): return np.convolve(a,np.ones(k)/k,mode='same')
    x=np.arange(INNER_W)
    fig,ax=plt.subplots(5,1,figsize=(14,12),sharex=True)
    ax[0].imshow(band(rgb,even)[::8],aspect='auto',extent=[0,INNER_W,0,100]);ax[0].set_ylabel('band(img)')
    ax[1].plot(x,sm(paper60));ax[1].set_ylabel('paper60 luma');ax[1].grid(1)
    ax[2].plot(x,sm(dark_frac),'r');ax[2].set_ylabel('dark_frac');ax[2].grid(1)
    ax[3].plot(x,sm(sat_mean),'g');ax[3].set_ylabel('sat_mean');ax[3].grid(1)
    ax[4].plot(x,sm(spk,9),'b');ax[4].set_ylabel('speck cnt');ax[4].set_xlabel('band x (outward ->)');ax[4].grid(1)
    ax[0].set_title(f'{stem} even={even}  (x grows OUTWARD toward spine/neighbor)')
    plt.tight_layout();plt.savefig(f'/Users/mist/DNB/8609/tmp/diag_{stem}.png',dpi=70)
    # print peak locations
    print(stem,'paper60_min_x',int(np.argmin(sm(paper60)[50:INNER_W-50])+50),
          'speck_peak_x',int(np.argmax(sm(spk,9)[50:INNER_W-50])+50))

if __name__=='__main__': main()
