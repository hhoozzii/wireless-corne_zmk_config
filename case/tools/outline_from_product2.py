import numpy as np, json
from PIL import Image
from skimage import transform, measure, color, morphology
from scipy import ndimage as ndi
import corne36_case as C
img=np.asarray(Image.open('/mnt/user-data/uploads/b28b9a07-image.png').convert('RGB')).astype(float)/255
g=color.rgb2gray(img)
lab=measure.label(g>0.85)
blobs=np.array([[r.centroid[1],r.centroid[0]] for r in measure.regionprops(lab) if 80<=r.area<=130 and r.eccentricity<0.6])
kx=[-128.5875,-109.5375,-90.4875,-71.4375,-52.3875,-33.3375]
ky={0:[-7.14375,11.90625,30.95625],1:[-7.14375,11.90625,30.95625],2:[-11.90625,7.14375,26.19375],3:[-14.2875,4.7625,23.8125],4:[-11.90625,7.14375,26.19375],5:[-9.525,9.525,28.575]}
keys=np.array([[kx[c],ky[c][r]] for c in range(6) for r in range(3)])
T0=transform.AffineTransform(np.load('photo/T_front.npy')); base=T0.inverse(keys)
def fit(guess):
    src=[];dst=[]
    for k,p in zip(keys,guess):
        d=np.linalg.norm(blobs-p,axis=1); i=d.argmin()
        if d[i]<8: src.append(blobs[i]); dst.append(k)
    return transform.AffineTransform.from_estimate(np.array(src),np.array(dst))
cx=452.5
m=g<0.85
m[:627]=False; m[856:]=False                       # lower panel only: top bar and bottom bar
m[786:,100:254]=False; m[786:,2*int(cx)-254:2*int(cx)-100+1]=False   # wrist pads
band=m[627:655]; m[627:655]=morphology.opening(band,np.ones((1,15),bool))   # snap-tab stubs
mx=np.arange(-122,6,0.1); my=np.arange(-28,72,0.1); MX,MY=np.meshgrid(mx,my,indexing='ij')
acc=[]
for name,guess in {'left':base,'right':np.c_[2*cx-base[:,0],base[:,1]]}.items():
    T=fit(guess)
    P=T.inverse(np.c_[MX.ravel(),MY.ravel()])
    v=ndi.map_coordinates(m.astype(float),[P[:,1],P[:,0]],order=1,mode='constant').reshape(MX.shape)
    v[MX<-119.05]=0                                # breakaway column slot (mouse-bite line at col0/col1)
    b=v>0.5
    lb=measure.label(b); keep=lb==np.bincount(lb.ravel()[lb.ravel()>0]).argmax()
    keep=ndi.binary_fill_holes(keep)
    acc.append(keep.astype(float))
avg=np.mean(acc,0); diff=np.abs(acc[0]-acc[1]).sum()*0.01
print('left/right disagreement area mm2: %.1f'%diff)
c=max(measure.find_contours(ndi.gaussian_filter(avg,1.0),0.5),key=len)
poly=np.c_[np.interp(c[:,0],np.arange(len(mx)),mx),np.interp(c[:,1],np.arange(len(my)),my)]
poly=measure.approximate_polygon(poly,0.1)
print('vertices',len(poly),'bbox',poly.min(0).round(2),poly.max(0).round(2))
old=json.load(open('boardsource_outline.json'))
ov=np.array(old['outline'])
dd=C.poly_sdf(poly.tolist(),ov[:,0][:,None],ov[:,1][:,None]).ravel()
print('my hand trace vs product edge (mm, +=outside):',np.round(dd,1))
hp=np.array(old['holes']); print('holes inside product outline by',np.round(C.poly_sdf(poly.tolist(),hp[:,0][:,None],hp[:,1][:,None]).ravel(),1))
json.dump(poly[:-1].round(3).tolist(),open('photo/product_outline_mm.json','w'))
np.save('photo/product_mask_mm.npy',avg)
