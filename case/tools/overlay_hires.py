import numpy as np, json
from PIL import Image, ImageDraw
from skimage import transform, measure
import corne36_case as C
d=json.load(open('boardsource_outline.json')); P=C.P
def offset_curve(poly,off,res=0.1):
    o=np.array(poly); gx=np.arange(o[:,0].min()-5,o[:,0].max()+5,res); gy=np.arange(o[:,1].min()-5,o[:,1].max()+5,res)
    X,Y=np.meshgrid(gx,gy,indexing='ij'); s=C.poly_sdf(poly,X,Y)
    # cut-side extra room like the case builder
    (cx0,cy0),(cx1,cy1)=d['cut']; s=np.minimum(s,C.box_sdf(X,Y,min(cx0,cx1)-P['cut_extra'],min(cx0,cx1)+4,min(cy0,cy1)+1,max(cy0,cy1)-1))
    c=max(measure.find_contours(s,off),key=len); return np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
pcb=np.array(d['outline']); inner=offset_curve(d['outline'],P['clearance']); outer=offset_curve(d['outline'],P['clearance']+P['wall'])
ux,uy=d['usb']; px_,py_=d['pwr']
usb=np.array([[ux-P['usb_w']/2,uy-3],[ux+P['usb_w']/2,uy-3],[ux+P['usb_w']/2,uy+2],[ux-P['usb_w']/2,uy+2]])
pwr=np.array([[px_-1,py_-P['pwr_w']/2],[px_+4,py_-P['pwr_w']/2],[px_+4,py_+P['pwr_w']/2],[px_-1,py_+P['pwr_w']/2]])
out=[]
for img,path,halves in [('bottom','/mnt/user-data/uploads/a0aaf1d9-image.jpg',['L','R']),('top','/mnt/user-data/uploads/5166f9d3-image.jpg',['L','Rm'])]:
    im=Image.open(path).convert('RGB'); dr=ImageDraw.Draw(im)
    for side in halves:
        if side=='Rm':      # mirror of the top-L fit about the panel centre
            M=np.load('photo/hires2_T_top-L.npy'); F=np.array([[-1,0,2*1285.5],[0,1,0],[0,0,1]]); T=transform.AffineTransform(M@F)
        else: T=transform.AffineTransform(np.load(f'photo/hires2_T_{img}-{side}.npy'))
        Ti=T.inverse
        for poly,col,w in [(outer,(0,190,255),3),(inner,(255,215,0),3),(pcb,(255,0,200),2)]:
            p=Ti(np.vstack([poly,poly[:1]])); dr.line([tuple(q) for q in p],fill=col,width=w)
        for hx,hy in d['holes']:
            q=Ti([[hx,hy]])[0]; r=P['pin_d']/2*7.7; dr.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],outline=(0,230,0),width=3)
            r=P['screw_d']/2*7.7; dr.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],outline=(0,230,0),width=2)
        for box in [usb,pwr]:
            p=Ti(np.vstack([box,box[:1]])); dr.line([tuple(q) for q in p],fill=(255,40,40),width=3)
    im=im.crop((180,280,2400,1160)); out.append(im)
W=out[0].width; canvas=Image.new('RGB',(W,out[0].height+out[1].height+60),'white')
canvas.paste(out[0],(0,0)); canvas.paste(out[1],(0,out[0].height+60))
ImageDraw.Draw(canvas).text((20,out[0].height+15),"top: bottom side   below: top side   |   magenta = board edge   yellow = case inner wall   cyan = case outside   green = screw posts   red = USB-C / power-switch openings",fill=(0,0,0))
canvas.save('out7/case_on_boardsource_photos.png')
canvas.resize((W//2,canvas.height//2),Image.LANCZOS).save('out7/case_on_boardsource_photos_small.png')
