import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from PIL import Image
from skimage import transform, measure
import corne36_case as C
OUT='out'
d=json.load(open('boardsource_outline.json')); P=C.P
g=np.load(f'{OUT}/_grid.npz'); gx,gy,gz,S=g['gx'],g['gy'],g['gz'],g['solid']; occ=S<0
top=np.where(occ.any(2), gz[len(gz)-1-np.argmax(occ[:,:,::-1],2)], np.nan); H=np.nan_to_num(top,nan=-1)
fig,ax=plt.subplots(1,3,figsize=(22,7.2),gridspec_kw=dict(width_ratios=[1.05,1.1,0.85]))
# 1) case outline over Boardsource's top-side photo
im=np.asarray(Image.open('/mnt/user-data/uploads/5166f9d3-image.jpg'))
Ti=transform.AffineTransform(np.load('photo/hires2_T_top-L.npy')).inverse
ax[0].imshow(im)
mm=lambda c:np.c_[np.interp(c[:,0],np.arange(len(gx)),gx),np.interp(c[:,1],np.arange(len(gy)),gy)]
for c in measure.find_contours((H>0.5).astype(float),0.5): p=Ti(mm(c)); ax[0].plot(p[:,0],p[:,1],c='deepskyblue',lw=1.2)
cav=S[:,:,np.searchsorted(gz,7.6)]<0
for c in measure.find_contours(cav.astype(float),0.5):
    if len(c)>400: p=Ti(mm(c)); ax[0].plot(p[:,0],p[:,1],c='gold',lw=1.2)
for hx,hy in d['holes']:
    q=Ti([[hx,hy]])[0]; ax[0].add_patch(plt.Circle(q,P['pin_d']/2*7.5,fill=False,ec='lime',lw=1.8))
for hx,hy in d['screw_holes']:
    q=Ti([[hx,hy]])[0]; ax[0].add_patch(plt.Circle(q,2.5*7.5,fill=False,ec='red',lw=1.2,ls='--'))
a=Ti([[-125,-28],[3,75]]); ax[0].set_xlim(a[0,0],a[1,0]); ax[0].set_ylim(a[1,1],a[0,1]); ax[0].axis('off')
ax[0].set_title("Case over Boardsource's top-side photo\nyellow = inner wall, blue = outside, green = pins, red dashed = M2 washer (2 screws)",fontsize=9.5)
# 2) top view of the case
ls=LightSource(315,45); rgb=ls.shade(H.T,cmap=plt.cm.Greys_r,vert_exag=3,blend_mode='soft',vmin=-1,vmax=9); rgb[H.T<0]=[1,1,1,1]
ax[1].imshow(rgb,extent=[gx[0],gx[-1],-gy[-1],-gy[0]])
o=np.array(d['outline']); ax[1].plot(np.r_[o[:,0],o[0,0]],-np.r_[o[:,1],o[0,1]],'--',c='tab:blue',lw=.8,label='board edge')
ax[1].annotate('USB-C',(d['usb'][0],-d['usb'][1]+1),(d['usb'][0]-30,25),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax[1].annotate('power switch',(d['pwr'][0]+2,-d['pwr'][1]),(4,-48),arrowprops=dict(arrowstyle='->'),fontsize=9)
for hx,hy in d['screw_holes']: ax[1].annotate('M2 screw',(hx,-hy),(hx-14,-hy-14),arrowprops=dict(arrowstyle='->'),fontsize=8)
ax[1].annotate('pin',(d['holes'][1][0],-d['holes'][1][1]),(-112,10),arrowprops=dict(arrowstyle='->'),fontsize=8)
ax[1].set_aspect('equal'); ax[1].set_xlim(gx[0]-2,gx[-1]+20); ax[1].legend(loc='lower left',fontsize=8)
ax[1].set_title('Case half, top view (mm). Mirror it in the slicer for the other side.',fontsize=10)
# 3) section through a screw post and a pin-only post
hx,hy=d['screw_holes'][0]; j=np.argmin(abs(gy-hy)); sec=occ[:,j,:].T
ax[2].imshow(sec,origin='lower',extent=[gx[0],gx[-1],gz[0],gz[-1]],cmap='Greys',aspect=1.6)
zb=P['floor']+P['under_pcb']; ax[2].add_patch(plt.Rectangle((hx-12,zb),24,P['pcb'],color='tab:green',alpha=.45,label='PCB'))
ax[2].add_patch(plt.Rectangle((hx-2.5,zb+P['pcb']),5,0.4,color='tab:red',alpha=.7,label='M2 washer'))
ax[2].set_xlim(hx-14,hx+14); ax[2].set_ylim(-0.5,10)
ax[2].set_title(f'Section through the screw post at ({hx}, {hy})',fontsize=10); ax[2].legend(fontsize=8,loc='upper right'); ax[2].set_xlabel('x mm'); ax[2].set_ylabel('z mm')
plt.tight_layout(); plt.savefig(f'{OUT}/preview.png',dpi=105)
