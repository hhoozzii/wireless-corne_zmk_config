import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from PIL import Image
from skimage import transform, measure
import corne36_case as C
d=json.load(open('boardsource_outline.json'))
g=np.load('out/_grid.npz'); gx,gy,gz,S=g['gx'],g['gy'],g['gz'],g['solid']; occ=S<0
top=np.where(occ.any(2), gz[len(gz)-1-np.argmax(occ[:,:,::-1],2)], np.nan)
fig,ax=plt.subplots(1,3,figsize=(21,7.5),gridspec_kw=dict(width_ratios=[1,1.15,0.9]))
# 1) case footprint over the photo
T=transform.ProjectiveTransform(np.load('photo/T_best.npy')); Ti=transform.ProjectiveTransform(np.linalg.inv(np.load('photo/T_best.npy')))
im=np.asarray(Image.open('/mnt/user-data/uploads/bb6ee6c3-image.jpg'))
ax[0].imshow(im)
outer=C.poly_sdf  # contours of wall in mm -> px
wall_top=np.nan_to_num(top,nan=-1)
for lvl,col,lab in [(0.5,'cyan','case outside'),]:
    for c in measure.find_contours((wall_top>lvl).astype(float),0.5):
        mmxy=np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
        p=Ti(mmxy); ax[0].plot(p[:,0],p[:,1],c=col,lw=1.2)
cav=S[:,:,np.searchsorted(gz,7.6)]<0
for c in measure.find_contours(cav.astype(float),0.5):
    mmxy=np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
    if len(mmxy)>200: p=Ti(mmxy); ax[0].plot(p[:,0],p[:,1],c='yellow',lw=1)
for hx,hy in d['holes']:
    p=Ti([[hx,hy]])[0]; ax[0].add_patch(plt.Circle(p,C.P['standoff_d']/2/0.0753,fill=False,ec='lime',lw=2))
ax[0].set_title('Your board (bottom side) with case wall (yellow = inner, cyan = outer)\nand screw posts (green)',fontsize=10); ax[0].axis('off')
# 2) top view of the case
ls=LightSource(315,45); H=wall_top.T
rgb=ls.shade(H,cmap=plt.cm.Greys_r,vert_exag=3,blend_mode='soft',vmin=-1,vmax=9); rgb[H<0]=[1,1,1,1]
ax[1].imshow(rgb,extent=[gx[0],gx[-1],-gy[-1],-gy[0]])
o=np.array(d['outline']); ax[1].plot(np.r_[o[:,0],o[0,0]],-np.r_[o[:,1],o[0,1]],'--',c='tab:blue',lw=.8,label='measured PCB edge')
ax[1].annotate('USB-C',(d['usb'][0],-d['usb'][1]+1),(d['usb'][0]-30,25),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax[1].annotate('power switch',(d['pwr'][0]+2,-d['pwr'][1]),(5,-52),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax[1].annotate('rough-cut room',(-120,-12),(-118,22),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax[1].set_aspect('equal'); ax[1].set_xlim(gx[0]-2,gx[-1]+22); ax[1].legend(loc='lower left',fontsize=8)
ax[1].set_title('Left case half, top view (mm). Right half is the mirror.',fontsize=10)
# 3) section through battery bay and a key row
j=np.argmin(abs(gy-8.0)); sec=occ[:,j,:].T
ax[2].imshow(sec,origin='lower',extent=[gx[0],gx[-1],gz[0],gz[-1]],cmap='Greys',aspect=3.5)
m=C.P; zb=m['floor']+m['under_pcb']
ax[2].add_patch(plt.Rectangle((-118.5,zb),118.5-23.4,m['pcb'],color='tab:green',alpha=.6,label='PCB'))
ax[2].set_title('Section across home row (z x3.5)',fontsize=10); ax[2].legend(fontsize=8,loc='upper left'); ax[2].set_xlabel('x mm')
plt.tight_layout(); plt.savefig('out/preview.png',dpi=110)
