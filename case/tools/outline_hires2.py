"""Board outline, mounting holes, USB-C / power switch / reset from Boardsource's two high-res product photos
(bottom side and top side). All four halves are mapped into the LEFT-half top-view frame and averaged."""
import numpy as np, json
from PIL import Image
from skimage import transform, measure, color, morphology
from scipy import ndimage as ndi
import corne36_case as C
kx=[-128.5875,-109.5375,-90.4875,-71.4375,-52.3875,-33.3375]
ky={0:[-7.14375,11.90625,30.95625],1:[-7.14375,11.90625,30.95625],2:[-11.90625,7.14375,26.19375],3:[-14.2875,4.7625,23.8125],4:[-11.90625,7.14375,26.19375],5:[-9.525,9.525,28.575]}
KEYS=np.array([[kx[c],ky[c][r]] for c in range(6) for r in range(3)])
IMGS={'bottom':dict(cols=[288,437,584,733,880,1028],mid=1286.5,path='/mnt/user-data/uploads/a0aaf1d9-image.jpg',bar=362,tab_band=(362,405),pad=(200,640,872),pad_band=(850,880),floor=1100),
      'top':   dict(cols=[320,463,606.5,750,893,1035],mid=1285.5,path='/mnt/user-data/uploads/5166f9d3-image.jpg',bar=373,tab_band=(373,420),pad=(240,668,866),pad_band=(845,875),floor=1088)}
MID=1286.0
masks=[];holes=[];Ts={}
mx=np.arange(-122,6,0.05); my=np.arange(-28,72,0.05); MX,MY=np.meshgrid(mx,my,indexing='ij')
for iname,cfg in IMGS.items():
    g=color.rgb2gray(np.asarray(Image.open(cfg['path']).convert('RGB')).astype(float)/255)
    regs=[r for r in measure.regionprops(measure.label(g>0.85)) if 300<r.area<5000]
    bl=np.array([[r.centroid[1],r.centroid[0],r.area,r.eccentricity] for r in regs])
    sw=bl[(bl[:,2]>1000)&(bl[:,2]<1350)&(bl[:,3]<0.35)&(bl[:,1]<850)]
    m=g<0.85
    m[:cfg['bar']]=False; m[cfg['floor']:]=False
    a,b=cfg['tab_band']; m[a:b]=morphology.opening(m[a:b],np.ones((1,45),bool))
    x0,x1,y0=cfg['pad']
    for xa,xb in [(x0,x1),(int(2*MID)-x1,int(2*MID)-x0)]:
        m[y0:,xa:xb]=False; a,b=cfg['pad_band']; m[a:b,xa:xb]=morphology.opening(m[a:b,xa:xb],np.ones((1,45),bool))
    for side in ['L','R']:
        if iname=='top' and side=='R': continue   # key fit unreliable on this half (stray holes)
        s=sw[sw[:,0]<MID] if side=='L' else sw[sw[:,0]>MID]
        cols=cfg['cols'] if side=='L' else [2*cfg['mid']-x for x in cfg['cols']]
        src=[];dst=[]
        for c,xc in enumerate(cols):
            col=s[np.abs(s[:,0]-xc)<18]; col=col[np.argsort(col[:,1])][:3]
            for r,q in enumerate(col): src.append(q[:2]); dst.append([kx[c],ky[c][r]])
        T=transform.AffineTransform.from_estimate(np.array(src),np.array(dst)); e=np.linalg.norm(T(np.array(src))-np.array(dst),axis=1)
        sc=np.sqrt(abs(np.linalg.det(T.params[:2,:2])))
        print(f'{iname}-{side}: keys {len(src)} resid mean {e.mean():.3f} max {e.max():.3f} mm, {1/sc:.2f} px/mm')
        Ts[f'{iname}-{side}']=(T,g)
        # mounting holes: round, not a switch hole
        cand=bl[((bl[:,0]<MID) if side=='L' else (bl[:,0]>MID))&(bl[:,3]<0.35)&(bl[:,2]>600)]
        for q,(x,y) in zip(cand,T(cand[:,:2])):
            if np.min(np.hypot(KEYS[:,0]-x,KEYS[:,1]-y))<2: continue
            if min(np.hypot(x-tx,y-ty) for tx,ty in [(-61.9,45.85),(-40.9,48.57),(-18.65,52.34)])<1.5: continue  # thumb switch centres
            holes.append((x,y,2*np.sqrt(q[2]/np.pi)*sc)); print('   hole',iname,side,round(x,2),round(y,2),'d',round(2*np.sqrt(q[2]/np.pi)*sc,2))
        P=T.inverse(np.c_[MX.ravel(),MY.ravel()])
        v=ndi.map_coordinates(m.astype(float),[P[:,1],P[:,0]],order=1,mode='constant').reshape(MX.shape)
        v[MX<-119.05]=0
        bb=v>0.5; lb=measure.label(bb); bb=lb==np.bincount(lb.ravel()[lb.ravel()>0]).argmax()
        masks.append(ndi.binary_fill_holes(bb))
stack=np.array(masks,float); avg=stack.mean(0)
for i,k in enumerate(Ts): print(k,'disagreement vs mean mm2: %.1f'%(np.abs(stack[i]-(avg>0.5)).sum()*0.0025))
b=avg>0.5; np.save('photo/hires2_mask.npy',b); np.save('photo/hires2_grid.npy',np.array([mx[0],my[0],0.05]))
hull=morphology.convex_hull_image(b); box=(MX>-27)&(MX<1)&(MY>-19)&(MY<26); b2=b|(hull&box)
wl=measure.label((b2&~b)&box); wr=max(measure.regionprops(wl),key=lambda r:r.area)
window=[[float(mx[wr.bbox[0]]),float(my[wr.bbox[1]])],[float(mx[wr.bbox[2]-1]),float(my[wr.bbox[3]-1])]]
print('display/battery window bbox mm',np.round(window,2),'area mm2 %.0f'%(wr.area*0.0025))
c=max(measure.find_contours(ndi.gaussian_filter(b2.astype(float),1.5),0.5),key=len)
poly=np.c_[np.interp(c[:,0],np.arange(len(mx)),mx),np.interp(c[:,1],np.arange(len(my)),my)]
poly=measure.approximate_polygon(poly,0.05)[:-1]
# cluster holes
H=np.array(holes); groups=[]
for h in H:
    for gp in groups:
        if np.hypot(*(np.mean(gp,0)[:2]-h[:2]))<2: gp.append(h); break
    else: groups.append([h])
hol=[np.mean(gp,0).round(2).tolist()+[len(gp)] for gp in groups]
print('holes seen in >=2 of 3 halves (x, y, dia, n):'); [print('  ',h) for h in sorted(hol) if h[3]>=2]
json.dump(dict(window=window,outline=poly.round(3).tolist(),holes=[h[:3] for h in hol if h[3]>=2]),open('photo/hires2.json','w'))
[np.save(f'photo/hires2_T_{k}.npy',v[0].params) for k,v in Ts.items()]
prev=np.array(json.load(open('boardsource_outline.json'))['outline'])
dd=C.poly_sdf(poly.tolist(),prev[:,0][:,None],prev[:,1][:,None]).ravel()
print('vertices',len(poly),'bbox',poly.min(0).round(2),poly.max(0).round(2),' prev outline vs new: mean %.2f max %.2f'%(np.abs(dd).mean(),np.abs(dd).max()))
