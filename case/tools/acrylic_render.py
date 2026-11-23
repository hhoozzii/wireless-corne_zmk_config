"""Render: printed frame (PCB rests on the lip, enters from the top) + acrylic sheet inside the frame from below
+ M3 standoffs between sheet and PCB."""
import json, os, sys, numpy as np, matplotlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image, ImageDraw, ImageFont
from skimage.measure import marching_cubes
import corne36_case as C, zrender

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'boardsource_outline.json')); P = dict(C.P); P['res_xy'] = 0.35; P['res_z'] = 0.25
fv, ff, meta, _ = C.build(d, P)
zb, zpb, zpt = meta['z_base'], meta['z_pcb_bot'], meta['z_pcb_top']
r = 0.35
gx, gy, X, Y = C.grid_for(d['outline'], 8, r)
s_pcb = C.poly_sdf(d['outline'], X, Y)
(cx0, cy0), (cx1, cy1) = d['cut']; xcut = min(cx0, cx1)
board = np.minimum(s_pcb, C.box_sdf(X, Y, xcut - P['cut_extra'], xcut + 4, min(cy0, cy1) + 1.0, max(cy0, cy1) - 1.0))
holes = d['holes']


def mesh(s2, z0, z1, rz=0.2):
    gz = np.arange(z0 - 1, z1 + 1, rz) + 0.07; Z = gz[None, None, :]
    s = np.maximum(s2[..., None], np.maximum(z0 - Z, Z - z1)).astype(np.float32); s[np.abs(s) < 2e-3] = 2e-3
    v, f, _, _ = marching_cubes(s, 0.0, spacing=(r, r, rz)); v += [gx[0], gy[0], gz[0]]; v[:, 1] *= -1
    return v, f


sheet2 = np.maximum(board - (P['clearance'] - P['acrylic_fit']),
                    -np.min([C.circ_sdf(X, Y, x, y, P['acrylic_hole_d'] / 2) for x, y in holes], 0))
sheet = mesh(sheet2, 0, zb)
standoffs = mesh(np.min([C.circ_sdf(X, Y, x, y, P['standoff_d'] / 2) for x, y in holes], 0), zb, zpb)
nx = np.array(d['notch'])
win = C.box_sdf(X, Y, nx[:, 0].min(), nx[:, 0].max(), nx[:, 1].min() + 4, nx[:, 1].max())
pcb2 = np.maximum(s_pcb, -np.minimum(win, np.min([C.circ_sdf(X, Y, x, y, 2.25) for x, y in holes], 0)))
pcb = mesh(pcb2, zpb, zpt)
PARTS = [('sheet', sheet, (0.55, 0.75, 0.95), 0.45), ('standoffs', standoffs, (0.80, 0.62, 0.24), 1.0),
         ('pcb', pcb, (0.15, 0.16, 0.16), 1.0), ('frame', (fv, ff), (0.93, 0.93, 0.92), 1.0)]


def view(offsets, elev, azim, width, hide=()):
    parts = [(v + [0, 0, offsets.get(n, 0)], f, c, a) for n, (v, f), c, a in PARTS if n not in hide]
    return zrender.render(parts, elev=elev, azim=azim, width=width)


shots = [('Assembled, from above', view({}, 38, -60, 900)),
         ('From below: sheet sits inside the wall', view({}, -40, -60, 900)),
         ('Exploded', view({'sheet': -16, 'standoffs': -8, 'pcb': 14}, 24, -60, 900))]
F = ImageFont.truetype(os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data/fonts/ttf/DejaVuSans-Bold.ttf'), 20)
W = sum(im.width for _, im in shots) + 40 * (len(shots) - 1); H = max(im.height for _, im in shots) + 46
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); x = 0
for t, im in shots:
    out.paste(im, (x, 46)); dr.text((x + 12, 10), t, font=F, fill=(30, 30, 30)); x += im.width + 40
out.save('acrylic_render.png')
print(meta, 'total height', meta['z_top'])
