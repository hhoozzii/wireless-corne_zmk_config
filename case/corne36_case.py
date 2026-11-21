#!/usr/bin/env python3
"""
Low-profile tray case for a Boardsource Wireless Corne SMT with the outer
(pinky) column cut off -> 36 keys. Kailh Choc v2 switches, MX keycaps.

Geometry source: foostan/crkbd 3x6 bottom-plate outline (standard Corne/CRKBD
outline, which the Boardsource PCB is compatible with). The outline is clipped
at the column-0 / column-1 boundary where the board was cut.

Usage:  python3 corne36_case.py [outline.json] [outdir]
Needs:  numpy, scikit-image, matplotlib (for point-in-polygon)

All dimensions in mm. Coordinates below are crkbd/KiCad coordinates of the
LEFT half seen from the top (x to the right, y DOWN, as in KiCad).
"""
import json, math, os, struct, sys, zipfile
import numpy as np
from matplotlib.path import Path
from skimage.measure import marching_cubes

# ---------------------------------------------------------------- parameters
P = dict(
    # --- where the PCB was cut (KiCad x). Column 0/1 boundary = -119.06.
    cut_x=-119.06,
    cut_extra=2.0,      # room for a rough cut: PCB may stick out up to this far past the boundary
    clearance=0.5,      # gap between PCB edge and wall on the other sides
    wall=2.4,           # wall thickness (6 perimeters at 0.4)
    floor=2.0,          # floor thickness
    under_pcb=3.5,      # clearance under PCB for hotswap sockets / bottom parts
    pcb=1.6,            # PCB thickness
    lip=1.2,            # wall height above PCB top (hides the cut edge; keep low for choc)
    ledge=1.0,          # how far the support ledge reaches under the PCB edge
    standoff_d=4.4,     # standoff diameter at the 2 remaining M2 holes
    screw_d=1.7,        # pilot hole for M2 self-tapping screw (2.0 = loose / 3.2 = heat insert M2)
    # --- openings on the inner edge (KiCad coords)
    usb_x=-13.3, usb_w=14.0,          # USB-C slot on the top edge of the controller area
    pwr_y=34.6, pwr_w=14.0,           # power switch slot on the inner edge (TRRS spot on wired Cornes)
    slot_floor=1.0,                   # slots go down to (PCB bottom - this)
    # --- battery pocket in the floor, under the controller area
    batt=dict(x0=-22.8, x1=-4.9, y0=-14.0, y1=19.0, depth=1.2),
    # --- rubber feet recesses (diameter, depth) at KiCad coords
    feet=[(-110.0, -12.0), (-110.0, 35.0), (-68.0, 47.0), (-33.0, 55.0), (-32.0, -14.0)],
    foot_d=10.0, foot_depth=0.8,
    # --- mesh resolution
    res_xy=0.25, res_z=0.25,
)
HOLES_KEPT = [(-43.278346, 38.498363), (-43.271782, -0.794121)]   # the two cut-off holes at x=-119.46 are gone


# ---------------------------------------------------------------- 2D helpers
def clip_halfplane_x(poly, xmin):
    """Sutherland-Hodgman clip of a closed polygon to x >= xmin."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[0] >= xmin, b[0] >= xmin
        if ina:
            out.append(a)
        if ina != inb:
            t = (xmin - a[0]) / (b[0] - a[0])
            out.append((xmin, a[1] + t * (b[1] - a[1])))
    return out


def poly_sdf(poly, X, Y):
    """Exact signed distance to a closed polygon (negative inside)."""
    pts = np.stack([X.ravel(), Y.ravel()], 1)
    A = np.array(poly)
    B = np.roll(A, -1, 0)
    d2 = np.full(len(pts), np.inf)
    for s in range(0, len(A), 64):
        a, b = A[s:s + 64], B[s:s + 64]
        ab = b - a
        L = (ab ** 2).sum(1)
        L[L == 0] = 1e-12
        ap = pts[:, None, :] - a[None]
        t = np.clip((ap * ab[None]).sum(2) / L[None], 0, 1)
        q = a[None] + t[..., None] * ab[None]
        d2 = np.minimum(d2, ((pts[:, None, :] - q) ** 2).sum(2).min(1))
    inside = Path(A).contains_points(pts)
    d = np.sqrt(d2)
    d[inside] *= -1
    return d.reshape(X.shape)


def box_sdf(X, Y, x0, x1, y0, y1):
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0) / 2, abs(y1 - y0) / 2
    qx, qy = np.abs(X - cx) - hx, np.abs(Y - cy) - hy
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)


def circ_sdf(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


# ---------------------------------------------------------------- build
def build(outline, p=P):
    z_pcb_bot = p['floor'] + p['under_pcb']
    z_pcb_top = z_pcb_bot + p['pcb']
    z_top = z_pcb_top + p['lip']

    cav_poly = clip_halfplane_x(outline, p['cut_x'] - p['cut_extra'])   # PCB incl. rough edge
    pcb_poly = clip_halfplane_x(outline, p['cut_x'])                   # nominal PCB

    off = p['clearance'] + p['wall'] + 2.0
    xs = np.array([q[0] for q in cav_poly]); ys = np.array([q[1] for q in cav_poly])
    r = p['res_xy']
    gx = np.arange(xs.min() - off, xs.max() + off, r) + r * 0.37   # off-grid so flat faces never sit on samples
    gy = np.arange(ys.min() - off, ys.max() + off, r) + r * 0.29
    X, Y = np.meshgrid(gx, gy, indexing='ij')

    s_cav = poly_sdf(cav_poly, X, Y)
    s_pcb = poly_sdf(pcb_poly, X, Y)

    cavity = s_cav - p['clearance']                       # <0 inside the pocket the PCB drops into
    outer = s_cav - p['clearance'] - p['wall']            # <0 inside the case footprint
    inner_edge_x = xs.max()                               # x of the straight inner edge (-4.26)
    top_y = -17.17                                        # top edge of controller area

    # openings (2D, KiCad coords)
    usb = box_sdf(X, Y, p['usb_x'] - p['usb_w'] / 2, p['usb_x'] + p['usb_w'] / 2, top_y - 10, top_y + 3)
    pwr = box_sdf(X, Y, inner_edge_x - 3, inner_edge_x + 10, p['pwr_y'] - p['pwr_w'] / 2, p['pwr_y'] + p['pwr_w'] / 2)
    slots = np.minimum(usb, pwr)

    # ledge region: in the pocket but outside the PCB shrunk by `ledge`, not in slots
    ledge = np.maximum(np.maximum(cavity, -(s_pcb + p['ledge'])), -slots)

    stand = np.min([circ_sdf(X, Y, hx, hy, p['standoff_d'] / 2) for hx, hy in HOLES_KEPT], 0)
    screw = np.min([circ_sdf(X, Y, hx, hy, p['screw_d'] / 2) for hx, hy in HOLES_KEPT], 0)
    b = p['batt']
    batt = box_sdf(X, Y, b['x0'], b['x1'], b['y0'], b['y1']) - 0.0
    feet = np.min([circ_sdf(X, Y, fx, fy, p['foot_d'] / 2) for fx, fy in p['feet']], 0)

    gz = np.arange(-1.0, z_top + 1.0, p['res_z']) + p['res_z'] * 0.43
    Z = gz[None, None, :]
    E = lambda s2, z0, z1: np.maximum(s2[..., None], np.maximum(z0 - Z, Z - z1))   # extrusion

    solid = E(outer, 0, z_top)
    solid = np.maximum(solid, -E(cavity, p['floor'], z_top + 5))                    # pocket
    solid = np.minimum(solid, E(np.maximum(ledge, outer), 0, z_pcb_bot))            # support ledge
    solid = np.minimum(solid, E(stand, 0, z_pcb_bot))                               # standoffs
    solid = np.maximum(solid, -E(slots, z_pcb_bot - p['slot_floor'], z_top + 5))    # USB / power slots
    solid = np.maximum(solid, -E(screw, -5, z_top + 5))                              # screw pilot holes
    solid = np.maximum(solid, -E(batt, p['floor'] - b['depth'], z_top + 5))        # battery pocket
    solid = np.maximum(solid, -E(feet, -5, p['foot_depth']))                        # feet recesses

    verts, faces, _, _ = marching_cubes(solid.astype(np.float32), 0.0, spacing=(r, r, p['res_z']))
    verts += np.array([gx[0], gy[0], gz[0]])
    verts[:, 1] *= -1                       # KiCad y-down -> y-up (keeps it a LEFT half)
    faces = faces[:, ::-1]                  # flipping one axis reverses winding; restore outward normals
    # marching_cubes on a "solid<0" field gives normals pointing toward +field (outward) already;
    # we checked orientation via signed volume below.
    vol = signed_volume(verts, faces)
    if vol < 0:
        faces = faces[:, ::-1]
    meta = dict(z_pcb_bot=z_pcb_bot, z_pcb_top=z_pcb_top, z_top=z_top)
    return verts, faces, meta, (gx, gy, gz, solid)


def signed_volume(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0


def mirror_x(v, f):
    v = v.copy(); v[:, 0] *= -1
    return v, f[:, ::-1].copy()


def write_stl(path, v, f, name):
    tri = v[f].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(f), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'] = n; rec['v'] = tri
    with open(path, 'wb') as fh:
        fh.write(name.encode()[:80].ljust(80, b' '))
        fh.write(struct.pack('<I', len(f)))
        fh.write(rec.tobytes())


def write_3mf(path, parts):
    """parts: list of (name, verts, faces). Each placed side by side as its own object."""
    objs, items = [], []
    for i, (name, v, f) in enumerate(parts, 1):
        vs = '\n'.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
        ts = '\n'.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        objs.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>\n{vs}\n</vertices>'
                    f'<triangles>\n{ts}\n</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'crkbd_outline.json')
    outdir = sys.argv[2] if len(sys.argv) > 2 else 'out'
    os.makedirs(outdir, exist_ok=True)
    outline = [tuple(q) for q in json.load(open(src))['loops'][0]]
    if math.dist(outline[0], outline[-1]) < 1e-6:
        outline = outline[:-1]
    v, f, meta, grid = build(outline)
    np.savez_compressed(os.path.join(outdir, '_grid.npz'), gx=grid[0], gy=grid[1], gz=grid[2], solid=grid[3])
    # place the bottom at z=0 and centre each half for printing
    v[:, 2] -= v[:, 2].min()
    vl = v.copy()
    vr, fr = mirror_x(v, f)
    write_stl(os.path.join(outdir, 'corne36_case_left.stl'), vl, f, 'corne36 case left')
    write_stl(os.path.join(outdir, 'corne36_case_right.stl'), vr, fr, 'corne36 case right')
    # 3MF with both halves side by side
    w = vl[:, 0].max() - vl[:, 0].min()
    vl2 = vl - [vl[:, 0].max() + 5, 0, 0]
    vr2 = vr - [vr[:, 0].min() - 5, 0, 0]
    write_3mf(os.path.join(outdir, 'corne36_case_pair.3mf'), [('left', vl2, f), ('right', vr2, fr)])
    json.dump(dict(meta=meta, params=P, tris=len(f), bbox=[v.min(0).tolist(), v.max(0).tolist()]),
              open(os.path.join(outdir, 'build_info.json'), 'w'), indent=1)
    print(json.dumps(dict(meta=meta, tris=len(f), bbox=[v.min(0).round(2).tolist(), v.max(0).round(2).tolist()])))
