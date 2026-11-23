"""Render: printed tray (floor), PCB, and a rough nice!view + battery stack over the controller strip."""
import json, os, sys, numpy as np, matplotlib
from PIL import Image, ImageDraw, ImageFont
from skimage.measure import marching_cubes
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import corne36_case as C, zrender

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'boardsource_outline.json'))
P = dict(C.P); P['res_xy'] = 0.3; P['res_z'] = 0.25
fv, ff, meta, _ = C.build(d, P)
zpb, zpt = meta['z_pcb_bot'], meta['z_pcb_top']
r = 0.3
gx, gy, X, Y = C.grid_for(d['outline'], 8, r)
s_pcb = C.poly_sdf(d['outline'], X, Y)


def mesh(s2, z0, z1, rz=0.2):
    gz = np.arange(z0 - 1, z1 + 1, rz) + 0.07; Z = gz[None, None, :]
    s = np.maximum(s2[..., None], np.maximum(z0 - Z, Z - z1)).astype(np.float32); s[np.abs(s) < 2e-3] = 2e-3
    v, f, _, _ = marching_cubes(s, 0.0, spacing=(r, r, rz)); v += [gx[0], gy[0], gz[0]]; v[:, 1] *= -1
    return v, f


pcb = mesh(np.maximum(s_pcb, -np.min([C.circ_sdf(X, Y, x, y, 2.25) for x, y in d['holes']], 0)), zpb, zpt)
batt = mesh(C.box_sdf(X, Y, -19, -7, -12, 18), zpt + 0.3, zpt + 3.3)
disp = mesh(C.box_sdf(X, Y, -21.5, -5.5, -14.5, 21.5), zpt + 3.4, zpt + 5.6)    # approx. nice!view on top of the battery
sw = mesh(np.min([C.rbox_sdf(X, Y, kx, ky, 15, 15, a) for kx, ky, a in d['keys']], 0), zpt, zpt + 5)
PARTS = [('pcb', pcb, (0.15, 0.16, 0.16), 1.0), ('sw', sw, (0.08, 0.08, 0.08), 1.0),
         ('batt', batt, (0.75, 0.7, 0.3), 1.0), ('disp', disp, (0.35, 0.5, 0.35), 1.0),
         ('case', (fv, ff), (0.93, 0.93, 0.92), 1.0)]
view = lambda elev, azim, w, hide=(): zrender.render([(v, f, c, a) for n, (v, f), c, a in PARTS if n not in hide],
                                                     elev=elev, azim=azim, width=w)
shots = [('From the front-left', view(38, -60, 900)),
         ('Display side', view(30, 40, 900)),
         ('Case only', view(45, -110, 900, hide=('pcb', 'sw', 'batt', 'disp')))]
F = ImageFont.truetype(os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data/fonts/ttf/DejaVuSans-Bold.ttf'), 20)
W = sum(im.width for _, im in shots) + 40 * (len(shots) - 1); H = max(im.height for _, im in shots) + 46
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); x = 0
for t, im in shots:
    out.paste(im, (x, 46)); dr.text((x + 12, 10), t, font=F, fill=(30, 30, 30)); x += im.width + 40
out.save(sys.argv[2] if len(sys.argv) > 2 else 'preview.png')
print(meta)
