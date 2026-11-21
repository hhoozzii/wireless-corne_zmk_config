#!/usr/bin/env python3
"""
Low-profile tray case for the Boardsource Wireless Corne SMT (v1.01) with the
outer pinky column broken off -> 36 keys. Kailh Choc v2 switches, MX keycaps.

Board geometry (outline, mounting holes, display window, USB-C, power switch) was
extracted from Boardsource's high-res product photos (top and bottom side) and scaled
with the 19.05 mm key grid (boardsource_outline.json, KiCad-style coords: LEFT half
seen from the top, x right, y down). Expected accuracy ~0.2-0.4 mm, so print the
fit-test frame first. Only one half is generated: the board is symmetric, so mirror
the part in the slicer for the other side.

Usage:  python3 corne36_case.py [boardsource_outline.json] [outdir]
Needs:  numpy, scikit-image, matplotlib
"""
import json, os, struct, sys, zipfile
import numpy as np
from matplotlib.path import Path
from skimage.measure import marching_cubes

P = dict(
    clearance=0.7,      # gap PCB edge -> wall
    cut_extra=1.0,      # extra room past the broken-off edge (rough cut)
    wall=2.4,           # wall thickness (6 perimeters at 0.4)
    floor=2.0,          # floor thickness
    under_pcb=3.5,      # space under PCB for hotswap sockets, switch posts, nRF module
    pcb=1.6,
    lip=1.2,            # wall height above PCB top (hides the cut; keycaps clear it)
    ledge=1.0,          # support ledge reaching under the PCB edge
    # mounting holes are ~4.2-4.8 mm (no grommets): a pin locates the board in each hole, a shoulder under the
    # PCB supports it; M2 screw + washer only where the switches leave room for the washer ('screw_holes')
    pin_d=3.6,          # pin through the PCB hole (smallest hole measured 4.24 mm)
    pin_below_top=0.3,  # pin stops this far below the PCB top surface so the washer clamps the board
    pin_chamfer=0.5,    # lead-in chamfer at the pin top
    shoulder_d=5.4,     # support ring under the PCB (socket tabs sit ~3 mm from some hole centres)
    screw_d=1.7,        # M2 self-tapping pilot in the screw posts (M2 x 8 + 5 mm washer)
    usb_w=13.0,         # USB-C plug opening width (typical overmold 12 mm)
    usb_floor=3.0,      # USB opening goes down to this z (plug body ~6.5 mm tall)
    pwr_w=10.0,         # power switch opening width
    # battery (301230, 3x12x30 mm) sits on top of the PCB under the nice!view: nothing needed in the case
    feet=[(-108.0, -8.0), (-105.5, 28.0), (-62.0, 44.0), (-22.0, 45.0), (-40.0, -10.0)],
    foot_d=10.0, foot_depth=0.8,
    res_xy=0.25, res_z=0.25,
)


# ---------------------------------------------------------------- 2D SDF helpers
def poly_sdf(poly, X, Y):
    pts = np.stack([X.ravel(), Y.ravel()], 1)
    A = np.array(poly, float); B = np.roll(A, -1, 0)
    d2 = np.full(len(pts), np.inf)
    for s in range(0, len(A), 32):
        a, b = A[s:s + 32], B[s:s + 32]
        ab = b - a; L = (ab ** 2).sum(1); L[L == 0] = 1e-12
        ap = pts[:, None, :] - a[None]
        t = np.clip((ap * ab[None]).sum(2) / L[None], 0, 1)
        q = a[None] + t[..., None] * ab[None]
        d2 = np.minimum(d2, ((pts[:, None, :] - q) ** 2).sum(2).min(1))
    d = np.sqrt(d2); d[Path(A).contains_points(pts)] *= -1
    return d.reshape(X.shape)


def box_sdf(X, Y, x0, x1, y0, y1):
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0) / 2, abs(y1 - y0) / 2
    qx, qy = np.abs(X - cx) - hx, np.abs(Y - cy) - hy
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)


def circ_sdf(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def grid_for(poly, pad, r):
    a = np.array(poly)
    gx = np.arange(a[:, 0].min() - pad, a[:, 0].max() + pad, r) + r * 0.37   # off-grid: no faces on samples
    gy = np.arange(a[:, 1].min() - pad, a[:, 1].max() + pad, r) + r * 0.29
    X, Y = np.meshgrid(gx, gy, indexing='ij')
    return gx, gy, X, Y


def to_mesh(solid, gx, gy, gz, r, rz):
    s = solid.astype(np.float32)
    s[np.abs(s) < 2e-3] = 2e-3            # no samples exactly on the surface -> no zero-area triangles
    v, f, _, _ = marching_cubes(s, 0.0, spacing=(r, r, rz))
    v += np.array([gx[0], gy[0], gz[0]])
    v[:, 1] *= -1                       # KiCad y-down -> y-up (stays a LEFT half)
    if signed_volume(v, f) < 0:
        f = f[:, ::-1]
    v[:, 2] -= v[:, 2].min()
    return v, f


def signed_volume(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0


# ---------------------------------------------------------------- case
def build(d, p=P):
    pcb = d['outline']; notch = np.array(d['notch'])
    z_pb = p['floor'] + p['under_pcb']; z_pt = z_pb + p['pcb']; z_top = z_pt + p['lip']
    r = p['res_xy']
    gx, gy, X, Y = grid_for(pcb, p['clearance'] + p['wall'] + p['cut_extra'] + 3, r)

    s_pcb = poly_sdf(pcb, X, Y)
    # rough cut edge: allow cut_extra beyond the traced cut line (runs along y at x ~ -117..-119.6)
    (cx0, cy0), (cx1, cy1) = d['cut']
    xcut = min(cx0, cx1)
    cutzone = box_sdf(X, Y, xcut - p['cut_extra'], xcut + 4, min(cy0, cy1) + 1.0, max(cy0, cy1) - 1.0)
    nx0, nx1 = notch[:, 0].min(), notch[:, 0].max() + 3
    ny0, ny1 = notch[:, 1].min(), notch[:, 1].max()
    bay = box_sdf(X, Y, nx0 + 0.6, nx1, ny0 + 0.6, ny1 - 0.6) - 0.6       # display/battery window in the PCB (no ledge there)
    board = np.minimum(s_pcb, cutzone)                                   # board + rough edge
    cavity = board - p['clearance']
    outer = board - p['clearance'] - p['wall']

    # openings
    ux, uy = d['usb']; px_, py_ = d['pwr']
    usb = box_sdf(X, Y, ux - p['usb_w'] / 2, ux + p['usb_w'] / 2, uy - 10, uy + 4)
    pwr = box_sdf(X, Y, px_ - 5, px_ + 10, py_ - p['pwr_w'] / 2, py_ + p['pwr_w'] / 2)

    # ledge band under the PCB edge; not on the inner (controller/module) edge, the window or thumb tip
    band = np.maximum(cavity, -(s_pcb + p['ledge']))
    no_ledge = np.minimum.reduce([box_sdf(X, Y, -12, 20, -40, 80), bay - 0.5, usb, pwr,
                                  box_sdf(X, Y, -40, 0, 50, 90)])
    ledge = np.maximum(band, -no_ledge)

    holes = d['holes']
    shoulder = np.min([circ_sdf(X, Y, hx, hy, p['shoulder_d'] / 2) for hx, hy in holes], 0)
    pin_r = np.min([circ_sdf(X, Y, hx, hy, 0) for hx, hy in holes], 0)          # distance to nearest hole centre
    screw = np.min([circ_sdf(X, Y, hx, hy, p['screw_d'] / 2) for hx, hy in d.get('screw_holes', holes)], 0)
    feet = np.min([circ_sdf(X, Y, fx, fy, p['foot_d'] / 2) for fx, fy in p['feet']], 0)

    gz = np.arange(-1.0, z_top + 1.0, p['res_z']) + p['res_z'] * 0.43
    Z = gz[None, None, :]
    E = lambda s2, z0, z1: np.maximum(s2[..., None], np.maximum(z0 - Z, Z - z1))

    solid = E(outer, 0, z_top)
    solid = np.maximum(solid, -E(cavity, p['floor'], z_top + 5))
    solid = np.minimum(solid, E(np.maximum(ledge, outer), 0, z_pb))
    solid = np.minimum(solid, E(shoulder, 0, z_pb))
    z_pin = z_pt - p['pin_below_top']
    rz = p['pin_d'] / 2 - np.clip(Z - (z_pin - p['pin_chamfer']), 0, None)        # chamfered pin radius
    solid = np.minimum(solid, np.maximum(pin_r[..., None] - rz, np.maximum(0 - Z, Z - z_pin)))
    solid = np.maximum(solid, -E(usb, p['usb_floor'], z_top + 5))
    solid = np.maximum(solid, -E(pwr, z_pb - 1.0, z_top + 5))
    solid = np.maximum(solid, -E(screw, -5, z_top + 5))
    solid = np.maximum(solid, -E(feet, -5, p['foot_depth']))
    v, f = to_mesh(solid, gx, gy, gz, r, p['res_z'])
    return v, f, dict(z_pcb_bot=z_pb, z_pcb_top=z_pt, z_top=round(z_top, 2)), (gx, gy, gz, solid)


def build_fit_test(d, p=P, t=0.8):
    """Flat 0.8 mm frame: a rim following the case wall (PCB outline + clearance) plus rings with the same
    pins as the case at the mounting holes, joined by spokes. Lower the PCB onto it (bottom side down):
    the pins should drop into the holes and the board edge should sit inside the rim."""
    r = 0.2117
    gx, gy, X, Y = grid_for(d['outline'], 5, r)
    s = poly_sdf(d['outline'], X, Y)
    rim = np.maximum(s - p['clearance'] - 1.6, -(s + 2.0))       # from 2 mm inside the edge to the wall line
    rings = [circ_sdf(X, Y, hx, hy, 3.0) for hx, hy in d['holes']]
    spokes = [np.maximum(box_sdf(X, Y, hx - 1.0, hx + 1.0, -90, 90), s - 0.5) for hx, _ in d['holes']]
    shape = np.minimum.reduce([rim] + rings + spokes)
    shape = 0.0371 + shape
    ph = t + 3.0                                                     # pins stand 3 mm above the frame
    gz = np.arange(-0.5, ph + 0.5, 0.1) + 0.0437
    Z = gz[None, None, :]
    solid = np.maximum(shape[..., None], np.maximum(-Z, Z - t))
    pin_r = np.min([circ_sdf(X, Y, hx, hy, 0) for hx, hy in d['holes']], 0)
    rz = p['pin_d'] / 2 - np.clip(Z - (ph - p['pin_chamfer']), 0, None)
    solid = np.minimum(solid, np.maximum(pin_r[..., None] - rz, np.maximum(-Z, Z - ph)))
    return to_mesh(solid, gx, gy, gz, r, 0.1)


# ---------------------------------------------------------------- output
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
        fh.write(name.encode()[:80].ljust(80, b' ')); fh.write(struct.pack('<I', len(f))); fh.write(rec.tobytes())


def write_3mf(path, parts):
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
        z.writestr('[Content_Types].xml', ct); z.writestr('_rels/.rels', rels); z.writestr('3D/3dmodel.model', model)


def side_by_side(vl, fl, gap=6):
    vr, fr = mirror_x(vl, fl)
    a = vl - [vl[:, 0].max() + gap / 2, 0, 0]
    b = vr - [vr[:, 0].min() - gap / 2, 0, 0]
    return [('left', a, fl), ('right', b, fr)]


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'boardsource_outline.json')
    outdir = sys.argv[2] if len(sys.argv) > 2 else 'out'
    os.makedirs(outdir, exist_ok=True)
    d = json.load(open(src))
    v, f, meta, grid = build(d)
    np.savez_compressed(os.path.join(outdir, '_grid.npz'), gx=grid[0], gy=grid[1], gz=grid[2], solid=grid[3])
    # one half (the left one); the board is symmetric, so mirror it in the slicer for the right side
    write_stl(os.path.join(outdir, 'corne36_case_half.stl'), v, f, 'corne36 case half (left, mirror for right)')
    write_3mf(os.path.join(outdir, 'corne36_case_half.3mf'), [('corne36 case half', v, f)])
    tv, tf = build_fit_test(d)
    write_stl(os.path.join(outdir, 'corne36_fit_test_half.stl'), tv, tf, 'corne36 fit test half')
    write_3mf(os.path.join(outdir, 'corne36_fit_test_half.3mf'), [('corne36 fit test half', tv, tf)])
    info = dict(meta=meta, tris=len(f), bbox=[v.min(0).round(2).tolist(), v.max(0).round(2).tolist()], fit_tris=len(tf))
    json.dump(dict(info, params=P), open(os.path.join(outdir, 'build_info.json'), 'w'), indent=1)
    print(json.dumps(info))
