import re, json, sys, math
import numpy as np
src=open(sys.argv[1]).read()
segs=[]; holes=[]
num=r'(-?[\d.]+)'
for m in re.finditer(r'\(gr_line \(start '+num+' '+num+r'\) \(end '+num+' '+num+r'\)',src):
    a,b,c,d=map(float,m.groups()); segs.append([(a,b),(c,d)])
for m in re.finditer(r'\(gr_arc \(start '+num+' '+num+r'\) \(mid '+num+' '+num+r'\) \(end '+num+' '+num+r'\)',src):
    sx,sy,mx,my,ex,ey=map(float,m.groups())
    # circle through 3 pts
    A=np.array([[sx,sy],[mx,my],[ex,ey]])
    ax,ay=A[0];bx,by=A[1];cx,cy=A[2]
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    r=math.hypot(ax-ux,ay-uy)
    t0=math.atan2(sy-uy,sx-ux);t1=math.atan2(my-uy,mx-ux);t2=math.atan2(ey-uy,ex-ux)
    def nrm(t): return (t-t0)%(2*math.pi)
    sweep=nrm(t2); 
    if nrm(t1)>sweep: sweep=sweep-2*math.pi
    n=max(4,int(abs(sweep)*r/0.3))
    pts=[(ux+r*math.cos(t0+sweep*i/n),uy+r*math.sin(t0+sweep*i/n)) for i in range(n+1)]
    segs.append(pts)
for m in re.finditer(r'\(gr_curve \(pts \(xy '+num+' '+num+r'\) \(xy '+num+' '+num+r'\) \(xy '+num+' '+num+r'\) \(xy '+num+' '+num+r'\)\)',src):
    p=np.array(list(map(float,m.groups()))).reshape(4,2)
    t=np.linspace(0,1,9)[:,None]
    b=((1-t)**3)*p[0]+3*((1-t)**2)*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
    segs.append([tuple(x) for x in b])
for m in re.finditer(r'\(gr_circle \(center '+num+' '+num+r'\) \(end '+num+' '+num+r'\)',src):
    cx,cy,ex,ey=map(float,m.groups()); holes.append((cx,cy,math.hypot(ex-cx,ey-cy)))
print(len(segs),'segs',len(holes),'holes',file=sys.stderr)
# chain
loops=[]
segs=[list(s) for s in segs]
while segs:
    loop=segs.pop(0)
    while True:
        end=loop[-1]; found=False
        for i,s in enumerate(segs):
            if math.dist(s[0],end)<0.05: loop+=s[1:]; segs.pop(i); found=True;break
            if math.dist(s[-1],end)<0.05: loop+=s[::-1][1:]; segs.pop(i); found=True;break
        if not found: break
    loops.append(loop)
for l in loops: print(len(l), 'closed' if math.dist(l[0],l[-1])<0.05 else 'OPEN', file=sys.stderr)
json.dump({'loops':loops,'holes':holes},open(sys.argv[2],'w'))
