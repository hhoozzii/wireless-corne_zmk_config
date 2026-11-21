"""Clean Corne outline: straight edges and square steps, edge positions measured from the high-res photo mask."""
import numpy as np, json
def isect(p1,p2,p3,p4):
    p1,p2,p3,p4=map(np.array,(p1,p2,p3,p4)); d1=p2-p1; d2=p4-p3
    cr=lambda a,b:a[0]*b[1]-a[1]*b[0]
    t=cr(p3-p1,d2)/cr(d1,d2); return tuple(float(v) for v in (p1+t*d1).round(3))
CUT=-119.05                      # breakaway mouse-bite line (col0/col1 boundary)
TOP={'c1':-16.25,'c2':-21.0,'c3':-23.15,'c4':-20.95,'c5':-18.45,'strip':-16.2}
STEP={'12':-99.6,'23':-80.4,'34':-62.3,'45':-43.0,'5s':-24.3}
INNER=-3.6; BOTTOM=40.25
# thumb-cluster lower edges (straight lines through measured points)
L_bot=((-119,BOTTOM),(-90,BOTTOM)); L2=((-81.90,40.28),(-70.75,54.95)); L3=((-70.75,54.95),(-33.25,59.83))
L4=((-33.25,59.83),(-18.30,68.37)); L5=((-16.80,67.35),(-3.80,44.75)); L_in=((INNER,0),(INNER,10))
poly=[(CUT,TOP['c1']),(STEP['12'],TOP['c1']),(STEP['12'],TOP['c2']),(STEP['23'],TOP['c2']),(STEP['23'],TOP['c3']),
      (STEP['34'],TOP['c3']),(STEP['34'],TOP['c4']),(STEP['45'],TOP['c4']),(STEP['45'],TOP['c5']),(STEP['5s'],TOP['c5']),
      (STEP['5s'],TOP['strip']),(INNER,TOP['strip']),
      isect(*L_in,*L5),isect(*L5,*L4),isect(*L4,*L3),isect(*L3,*L2),isect(*L2,*L_bot),(CUT,BOTTOM)]
if __name__=='__main__':
    from skimage.draw import polygon as rpoly
    b=np.load('photo/hires2_mask.npy'); x0,y0,r=np.load('photo/hires2_grid.npy')
    P=np.array(poly); ii,jj=rpoly((P[:,0]-x0)/r,(P[:,1]-y0)/r,b.shape); c=np.zeros_like(b); c[ii,jj]=True
    print('vertices:'); [print('  ',v) for v in poly]
    print('area clean %.0f mm2, photo mask %.0f mm2; clean-not-photo %.1f mm2, photo-not-clean %.1f mm2'%(c.sum()*r*r,b.sum()*r*r,(c&~b).sum()*r*r,(b&~c).sum()*r*r))
    d=json.load(open('boardsource_outline.json'))
    d['outline']=[list(map(float,v)) for v in poly]
    d['cut']=[[CUT,TOP['c1']-1.0],[CUT,BOTTOM+1.0]]     # cut-edge allowance spans the whole edge (no end steps)
    d['source']=("Clean polygon (straight edges, square steps) with each edge position measured from Boardsource's two high-res "
                 "product photos (~7.7 px/mm, scaled by the 19.05 mm key grid). Cut edge on the breakaway mouse-bite line "
                 "x=-119.05; USB-C shell and power-switch nub are not part of the outline (the case has openings for them). "
                 "KiCad-style coords of the LEFT half seen from the top (x right, y down).")
    json.dump(d,open('boardsource_outline.json','w'),indent=1)
