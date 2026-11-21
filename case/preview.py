import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import corne36_case as C
g=np.load('out/_grid.npz'); gx,gy,gz,S=g['gx'],g['gy'],g['gz'],g['solid']
occ=S<0
top=np.where(occ.any(2), gz[len(gz)-1-np.argmax(occ[:,:,::-1],2)], np.nan)
H=top.T  # rows = kicad y ascending -> plotted y = -kicad y descending from top
fig,ax=plt.subplots(1,2,figsize=(16,7.2),gridspec_kw=dict(width_ratios=[1.35,1]))
ls=LightSource(315,45)
ext=[gx[0],gx[-1],-gy[-1],-gy[0]]
Hm=np.nan_to_num(H,nan=-1)
rgb=ls.shade(Hm,cmap=plt.cm.Greys_r,vert_exag=3,blend_mode='soft',vmin=-1,vmax=9)
rgb[Hm<0]=[1,1,1,1]
ax[0].imshow(rgb,extent=ext)
# keys (36) from crkbd v4 coords: col1..5 + thumbs
cols={-109.5375:[-7.14375,11.90625,30.95625],-90.4875:[-11.90625,7.14375,26.19375],-71.4375:[-14.2875,4.7625,23.8125],-52.3875:[-11.90625,7.14375,26.19375],-33.3375:[-9.525,9.525,28.575]}
import matplotlib.patches as mp, matplotlib.transforms as mt
def key(x,y,rot=0,w=1):
    r=mp.Rectangle((-w*9.525,-9.525),w*19.05,19.05,fill=False,ec='tab:blue',lw=.8)
    r.set_transform(mt.Affine2D().rotate_deg(rot).translate(x,-y)+ax[0].transData); ax[0].add_patch(r)
for x,ys in cols.items():
    for y in ys: key(x,y)
key(-61.9125,47.625); key(-41.097974,49.801677,-(168.06-180)); key(-19.256135,51.882713,-(-113.88+180)+0,1.5)
o=json.load(open('crkbd_outline.json'))['loops'][0]; o=np.array(o)
ax[0].plot(o[:,0],-o[:,1],'--',c='0.6',lw=.7,label='original 6-col PCB outline')
ax[0].axvline(C.P['cut_x'],c='tab:red',lw=.8,ls=':'); ax[0].text(C.P['cut_x']+0.5,30,'cut line',color='tab:red',fontsize=8)
for hx,hy in C.HOLES_KEPT: ax[0].plot(hx,-hy,'o',ms=3,c='tab:orange')
ax[0].annotate('USB-C slot',(C.P['usb_x'],19),(C.P['usb_x']-30,26),fontsize=8,arrowprops=dict(arrowstyle='->'))
ax[0].annotate('power switch slot',(-2,-C.P['pwr_y']),(8,-55),fontsize=8,arrowprops=dict(arrowstyle='->'))
ax[0].annotate('battery pocket',(-14,-3),(5,8),fontsize=8,arrowprops=dict(arrowstyle='->'))
ax[0].annotate('M2 standoffs',(-43.3,0.8),(-75,22),fontsize=8,arrowprops=dict(arrowstyle='->'))
ax[0].set_xlim(gx[0]-15,gx[-1]+28); ax[0].set_aspect('equal'); ax[0].set_title('Left half, top view (keys = blue, mm)'); ax[0].legend(loc='lower left',fontsize=8)
# cross-section through middle row y=7.14 (kicad)
j=np.argmin(abs(gy-9.0)); sec=occ[:,j,:].T
ax[1].imshow(sec,origin='lower',extent=[gx[0],gx[-1],gz[0],gz[-1]],cmap='Greys',aspect=4)
m=C.P; zb=m['floor']+m['under_pcb']
ax[1].add_patch(mp.Rectangle((m['cut_x']-1.2,zb),-4.26-(m['cut_x']-1.2),m['pcb'],color='tab:green',alpha=.6,label='PCB (with 1.2 mm rough edge)'))
ax[1].set_title('Section through home row (z exaggerated 4x)'); ax[1].set_xlabel('x mm'); ax[1].set_ylabel('z mm'); ax[1].legend(fontsize=8,loc='upper center')
plt.tight_layout(); plt.savefig('out/preview_top_section.png',dpi=130)
