import numpy as np, json
from PIL import Image, ImageDraw
from skimage import transform, measure, color
img=Image.open('/mnt/user-data/uploads/b28b9a07-image.png').convert('RGB'); a=np.asarray(img).astype(float)/255
# switch-centre holes: white, round, ~100 px area
g=color.rgb2gray(a); lab=measure.label(g>0.85)
blobs=np.array([[r.centroid[1],r.centroid[0]] for r in measure.regionprops(lab) if 80<=r.area<=130 and r.eccentricity<0.6])
kx=[-128.5875,-109.5375,-90.4875,-71.4375,-52.3875,-33.3375]
ky={0:[-7.14375,11.90625,30.95625],1:[-7.14375,11.90625,30.95625],2:[-11.90625,7.14375,26.19375],3:[-14.2875,4.7625,23.8125],4:[-11.90625,7.14375,26.19375],5:[-9.525,9.525,28.575]}
keys=np.array([[kx[c],ky[c][r]] for c in range(6) for r in range(3)])
T0=transform.AffineTransform(np.load('photo/T_front.npy'))          # px -> mm, lower panel, left half
def fit(guess_px):                                            # guess_px: predicted px of each key
    src=[];dst=[]
    for k,p in zip(keys,guess_px):
        d=np.linalg.norm(blobs-p,axis=1); i=d.argmin()
        if d[i]<8: src.append(blobs[i]); dst.append(k)
    T=transform.AffineTransform.from_estimate(np.array(src),np.array(dst))
    e=np.linalg.norm(T(np.array(src))-np.array(dst),axis=1)
    return T,len(src),e.mean()
base=T0.inverse(keys)
d=json.load(open('boardsource_outline.json'))
draw=ImageDraw.Draw(img,'RGBA')
import corne36_case as C
P=C.P
# case inner wall / outer wall as offset curves of the measured outline
from skimage import measure as M
def offset_curve(poly,off,res=0.2):
    o=np.array(poly); gx=np.arange(o[:,0].min()-6,o[:,0].max()+6,res); gy=np.arange(o[:,1].min()-6,o[:,1].max()+6,res)
    X,Y=np.meshgrid(gx,gy,indexing='ij'); s=C.poly_sdf(poly,X,Y)
    c=max(M.find_contours(s,off),key=len); return np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
pcb=np.array(d['outline']); inner=offset_curve(d['outline'],P['clearance']); outer=offset_curve(d['outline'],P['clearance']+P['wall'])
cx=452.5; dy=-495
cases={'lower-left':base,'lower-right':np.c_[2*cx-base[:,0],base[:,1]],
       'upper-left':base+[0,dy],'upper-right':np.c_[2*cx-base[:,0],base[:,1]+dy]}
for name,guess in cases.items():
    T,n,err=fit(guess); print(name,'keys matched',n,'resid mm %.2f'%err)
    Ti=T.inverse
    for poly,col,w in [(outer,(0,200,255,255),2),(inner,(255,230,0,255),2),(pcb,(255,0,200,255),1)]:
        p=Ti(np.vstack([poly,poly[:1]])); draw.line([tuple(q) for q in p],fill=col,width=w)
    for hx,hy in d['holes']:
        q=Ti([[hx,hy]])[0]; r=P['standoff_d']/2/0.411; draw.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],outline=(0,255,0,255),width=2)
    for k,(lab_,pt) in enumerate([('USB',d['usb']),('PWR',d['pwr'])]):
        q=Ti([pt])[0]; draw.rectangle([q[0]-4,q[1]-4,q[0]+4,q[1]+4],outline=(255,60,60,255),width=2)
draw.text((60,40),"cyan = case outside   yellow = case inside wall   magenta = measured PCB edge (your cut board)\ngreen = screw posts   red = USB-C / power switch openings",fill=(0,0,0))
big=img.resize((img.width*2,img.height*2),Image.LANCZOS); big.save('out5/outline_on_product.png')
