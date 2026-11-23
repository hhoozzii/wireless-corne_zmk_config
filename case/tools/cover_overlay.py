import numpy as np, sys
from PIL import Image, ImageDraw
from skimage import transform, measure
OUT=sys.argv[1] if len(sys.argv)>1 else 'out'
g=np.load(f'{OUT}/_cover2d.npz'); gx,gy,S=g['gx'],g['gy'],g['shape']; m=S<0; r=gx[1]-gx[0]
im=Image.open('/mnt/user-data/uploads/5166f9d3-image.jpg').convert('RGBA'); W,H=im.size
M=np.load('photo/hires2_T_top-L.npy'); T=transform.AffineTransform(M); Ti=T.inverse
yy,xx=np.mgrid[0:H,0:W]; q=T(np.c_[xx.ravel(),yy.ravel()])
ix=np.round((q[:,0]-gx[0])/r).astype(int); iy=np.round((q[:,1]-gy[0])/r).astype(int)
ok=(ix>=0)&(ix<len(gx))&(iy>=0)&(iy<len(gy)); inside=np.zeros(len(q),bool); inside[ok]=m[ix[ok],iy[ok]]
fill=np.zeros((H*W,4),np.uint8); fill[inside]=(0,200,255,95)
out=Image.alpha_composite(im,Image.fromarray(fill.reshape(H,W,4)))
dr=ImageDraw.Draw(out)
for c in measure.find_contours(m.astype(float),0.5):
    mm=np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
    p=Ti(mm); dr.line([tuple(v) for v in p],fill=(0,255,255,255),width=2)
a=Ti([[-125,-28],[3,72]]); out=out.convert('RGB').crop((int(a[0,0]),int(a[0,1]),int(a[1,0]),int(a[1,1])))
out.save(f'{OUT}/cover_on_top_photo.png')
