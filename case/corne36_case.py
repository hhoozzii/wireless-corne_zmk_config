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
    cut_extra=-0.2,     # broken-off edge: the board stops at the mouse-bite line, so 0.7-0.2 = 0.5 mm gap there
    wall=1.8,           # wall thickness (4 perimeters at 0.45)
    floor=2.0,          # floor thickness (bottom='floor')
    # --- bottom: 'acrylic' = no printed floor; a sheet fits inside the wall from below, M3 standoffs
    #     from the sheet to the PCB hold everything together. 'floor' = the earlier printed tray.
    bottom='floor',
    acrylic_t=3.0,      # sheet thickness
    acrylic_fit=0.2,    # sheet is this much smaller than the opening it fits into
    standoff_h=5.0,     # M3 F-F standoff length = gap between sheet and PCB. 5 mm so the M3x5 from below (2 mm in)
                        # and the M3x4 from above (2.4 mm in) don't meet at the two clamp holes
    standoff_d=5.0,     # round M3 standoff diameter (keepout drawn in the previews)
    acrylic_hole_d=3.2, # M3 screw holes in the sheet at the standoffs
    stop_h=1.0,         # strip round the inside of the wall just above the sheet: the sheet stops against it
    under_pcb=3.5,      # space under PCB for hotswap sockets, switch posts, nRF module
    pcb=1.6,
    lip=1.2,            # wall height above PCB top (hides the cut; keycaps clear it)
    ledge=1.0,          # support ledge reaching under the PCB edge
    cut_ledge=-3.0,     # broken-off (outer) edge: no ledge at all (its hotswap sockets reach the board edge);
                        # the ledge band starts this far from the cut line, so -3 clears the whole gap
    # mounting holes are ~4.2-4.8 mm (no grommets): a pin locates the board in each hole, a shoulder under the
    # PCB supports it; M2 screw + washer only where the switches leave room for the washer ('screw_holes')
    pin_d=3.6,          # pin through the PCB hole (smallest hole measured 4.24 mm)
    pin_below_top=0.3,  # pin stops this far below the PCB top surface so the washer clamps the board
    pin_chamfer=0.5,    # lead-in chamfer at the pin top
    shoulder_d=5.4,     # support ring under the PCB (socket tabs sit ~3 mm from some hole centres)
    screw_d=1.7,        # M2 self-tapping pilot in the screw posts (M2 x 8 + 5 mm washer)
    # --- top cover: thin plate lying on the PCB inside the wall, cut out around each switch
    cover_t=1.0,        # thickness (wall rises 1.2 mm above the PCB, so it sits 0.2 mm below the wall top)
    cover_gap=0.3,      # gap between cover edge and case wall
    key_cut=15.6,       # square cutout per switch (Choc v2 housing passes a 15.5 mm opening)
    cover_screw_d=2.4,  # clearance for the screws that clamp cover + PCB (M2; 3.4 for the M3 acrylic build)
    min_web=1.2,        # remove cover features narrower than this
    # raised wall round the controller strip (top + inner edge) to guard the nice!view
    display_wall=7.0,   # wall top this far above the PCB top there (keys get the normal 1.2 mm lip)
    display_zone=(-23.0, -40.0, 10.0, 32.0),   # x0, y0, x1, y1 of the raised part (KiCad y-down); 45 deg ramps at its ends
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
    acrylic = p.get('bottom') == 'acrylic'
    z_base = p['acrylic_t'] if acrylic else p['floor']               # top of the floor / sheet
    z_pb = z_base + (p['standoff_h'] if acrylic else p['under_pcb'])
    z_pt = z_pb + p['pcb']; z_top = z_pt + p['lip']
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
                                  box_sdf(X, Y, -40, 0, 50, 90),
                                  box_sdf(X, Y, xcut + p['cut_ledge'], xcut + 6,
                                          min(cy0, cy1) - 3, max(cy0, cy1) + 3)])
    ledge = np.maximum(band, -no_ledge)

    holes = d['holes']
    shoulder = np.min([circ_sdf(X, Y, hx, hy, p['shoulder_d'] / 2) for hx, hy in holes], 0)
    pin_r = np.min([circ_sdf(X, Y, hx, hy, 0) for hx, hy in holes], 0)          # distance to nearest hole centre
    screw = np.min([circ_sdf(X, Y, hx, hy, p['screw_d'] / 2) for hx, hy in d.get('screw_holes', holes)], 0)
    feet = np.min([circ_sdf(X, Y, fx, fy, p['foot_d'] / 2) for fx, fy in p['feet']], 0)

    z_max = z_top + (0 if acrylic else p['display_wall'] - p['lip'])
    gz = np.arange(-1.0, z_max + 1.0, p['res_z']) + p['res_z'] * 0.43
    Z = gz[None, None, :]
    E = lambda s2, z0, z1: np.maximum(s2[..., None], np.maximum(z0 - Z, Z - z1))

    solid = E(outer, 0, z_top)
    if acrylic:
        # open frame: the sheet slides in from below under the lip and the stop strip
        solid = np.maximum(solid, -E(cavity, -5, z_top + 5))
        solid = np.minimum(solid, E(np.maximum(ledge, outer), z_base, z_pb))          # lip the PCB rests on
        gap = np.maximum(cavity, -s_pcb)                                             # outside the PCB footprint
        solid = np.minimum(solid, E(np.maximum(gap, outer), z_base, z_base + p['stop_h']))
        solid = np.maximum(solid, -E(usb, z_pb - 2.5, z_top + 5))
        solid = np.maximum(solid, -E(pwr, z_pb - 1.0, z_top + 5))
        v, f = to_mesh(solid, gx, gy, gz, r, p['res_z'])
        return v, f, dict(z_base=z_base, z_pcb_bot=z_pb, z_pcb_top=z_pt, z_top=round(z_top, 2)), (gx, gy, gz, solid)
    # raised wall by the display: same wall ring, taller inside display_zone, 45 deg ramp down at its ends
    zx0, zy0, zx1, zy1 = p['display_zone']
    inside = -box_sdf(X, Y, zx0, zx1, zy0, zy1)                       # >0 inside the zone
    rise = np.clip(inside, 0, None)
    z_wall = z_top + np.minimum(rise, p['display_wall'] - p['lip'])
    ring = np.maximum(outer, -cavity)
    solid = np.maximum(solid, -E(cavity, p['floor'], z_top + 5))
    solid = np.minimum(solid, np.maximum(ring[..., None], np.maximum(z_top - 0.5 - Z, Z - z_wall[..., None])))
    solid = np.minimum(solid, E(np.maximum(ledge, outer), 0, z_pb))
    solid = np.minimum(solid, E(shoulder, 0, z_pb))
    z_pin = z_pt - p['pin_below_top']
    rz = p['pin_d'] / 2 - np.clip(Z - (z_pin - p['pin_chamfer']), 0, None)        # chamfered pin radius
    solid = np.minimum(solid, np.maximum(pin_r[..., None] - rz, np.maximum(0 - Z, Z - z_pin)))
    solid = np.maximum(solid, -E(usb, p['usb_floor'], z_max + 5))
    solid = np.maximum(solid, -E(pwr, z_pb - 1.0, z_max + 5))
    solid = np.maximum(solid, -E(screw, -5, z_max + 5))
    solid = np.maximum(solid, -E(feet, -5, p['foot_depth']))
    v, f = to_mesh(solid, gx, gy, gz, r, p['res_z'])
    return v, f, dict(z_pcb_bot=z_pb, z_pcb_top=z_pt, z_top=round(z_top, 2), z_display_wall=round(z_max, 2)), (gx, gy, gz, solid)


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


def rbox_sdf(X, Y, cx, cy, w, h, deg):
    t = np.radians(deg); dx, dy = X - cx, Y - cy
    u, v = dx * np.cos(t) + dy * np.sin(t), -dx * np.sin(t) + dy * np.cos(t)
    return box_sdf(u, v, -w / 2, w / 2, -h / 2, h / 2)


def build_cover(d, p=P):
    """Thin top cover: lies on the PCB inside the case wall, square cutouts around every switch,
    open over the controller strip (USB-C, display/battery window, power switch, reset), a channel
    for the battery wires, and clearance holes where the two M2 screws clamp cover + PCB."""
    r = 0.1617
    gx, gy, X, Y = grid_for(d['outline'], p['cut_extra'] + 3, r)
    s_pcb = poly_sdf(d['outline'], X, Y)
    (cx0, cy0), (cx1, cy1) = d['cut']; xcut = min(cx0, cx1)
    cutzone = box_sdf(X, Y, xcut - p['cut_extra'], xcut + 4, min(cy0, cy1) + 1.0, max(cy0, cy1) - 1.0)
    plate = np.minimum(s_pcb, cutzone) - (p['clearance'] - p['cover_gap'])
    holes = [rbox_sdf(X, Y, kx, ky, p['key_cut'], p['key_cut'], a) for kx, ky, a in d['keys']]
    (ox0, oy0), (ox1, oy1) = d['controller_opening']; holes.append(box_sdf(X, Y, ox0, ox1, oy0, oy1))
    (bx0, by0), (bx1, by1) = d['battery_wire_channel']; holes.append(box_sdf(X, Y, bx0, bx1, by0, by1))
    holes += [circ_sdf(X, Y, hx, hy, p['cover_screw_d'] / 2) for hx, hy in d['screw_holes']]
    shape = np.maximum(plate, -np.min(holes, 0))
    # drop anything narrower than min_web (wedges where an opening meets a cutout at an angle)
    from scipy import ndimage as ndi
    from skimage.morphology import opening, disk
    m = opening(shape < 0, disk(int(round(p['min_web'] / 2 / r))))
    shape = 0.0371 + (ndi.distance_transform_edt(~m) - ndi.distance_transform_edt(m)) * r
    t = p['cover_t']
    gz = np.arange(-0.4, t + 0.4, 0.1) + 0.0437
    Z = gz[None, None, :]
    solid = np.maximum(shape[..., None], np.maximum(-Z, Z - t))
    return to_mesh(solid, gx, gy, gz, r, 0.1), (gx, gy, shape)


# ---------------------------------------------------------------- acrylic sheet (2D, laser cut)
def build_sheet(d, p=P, r=0.1):
    """Sheet outline = board (+ rough-cut allowance) grown by clearance - acrylic_fit, so it drops inside the
    frame wall with acrylic_fit all round; M3 holes at every mounting hole. Returns (outline, holes) in
    y-up mm, same x/y as the STL. The shape is flat, so one cut file serves both halves: flip one over."""
    from skimage.measure import find_contours
    gx, gy, X, Y = grid_for(d['outline'], 3, r)
    s_pcb = poly_sdf(d['outline'], X, Y)
    (cx0, cy0), (cx1, cy1) = d['cut']; xcut = min(cx0, cx1)
    cutzone = box_sdf(X, Y, xcut - p['cut_extra'], xcut + 4, min(cy0, cy1) + 1.0, max(cy0, cy1) - 1.0)
    sheet = np.minimum(s_pcb, cutzone) - (p['clearance'] - p['acrylic_fit'])
    cs = find_contours(sheet, 0.0)
    c = max(cs, key=len)
    pts = np.column_stack([gx[0] + c[:, 0] * r, gy[0] + c[:, 1] * r])      # array axes are (x, y)
    pts = dp_simplify(pts, 0.01)
    pts[:, 1] *= -1
    holes = [(hx, -hy, p['acrylic_hole_d'] / 2) for hx, hy in d['holes']]
    return pts, holes


def dp_simplify(pts, tol):
    if np.allclose(pts[0], pts[-1]):                     # closed ring: split at the point farthest from the start
        pts = pts[:-1]; k = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
        a, b = dp_simplify(pts[:k + 1], tol), dp_simplify(np.vstack([pts[k:], pts[:1]]), tol)
        return np.vstack([a[:-1], b])                    # b ends at pts[0] -> ring closed again
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1: continue
        a, b = pts[i], pts[j]; ab = b - a; L = np.hypot(*ab) + 1e-12
        dd = np.abs(ab[0] * (pts[i + 1:j, 1] - a[1]) - ab[1] * (pts[i + 1:j, 0] - a[0])) / L
        k = int(np.argmax(dd))
        if dd[k] > tol:
            keep[i + 1 + k] = True; stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return pts[keep]


def write_dxf(path, outline, holes):
    """Plain R12 DXF, millimetres: one closed POLYLINE + CIRCLEs on layer CUT."""
    L = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '9', '$INSUNITS', '70', '4', '0', 'ENDSEC',
         '0', 'SECTION', '2', 'ENTITIES',
         '0', 'POLYLINE', '8', 'CUT', '66', '1', '70', '1', '10', '0', '20', '0', '30', '0']
    for x, y in outline[:-1] if np.allclose(outline[0], outline[-1]) else outline:
        L += ['0', 'VERTEX', '8', 'CUT', '10', f'{x:.4f}', '20', f'{y:.4f}', '30', '0']
    L += ['0', 'SEQEND', '8', 'CUT']
    for x, y, rr in holes:
        L += ['0', 'CIRCLE', '8', 'CUT', '10', f'{x:.4f}', '20', f'{y:.4f}', '30', '0', '40', f'{rr:.4f}']
    L += ['0', 'ENDSEC', '0', 'EOF']
    open(path, 'w').write('\n'.join(L) + '\n')


def write_svg(path, outline, holes, margin=2.0):
    x0, y0 = outline.min(0) - margin; x1, y1 = outline.max(0) + margin
    w, h = x1 - x0, y1 - y0
    tx = lambda x, y: (x - x0, y1 - y)                                       # SVG y points down
    d = 'M ' + ' L '.join('%.4f,%.4f' % tx(x, y) for x, y in outline) + ' Z'
    circ = ''.join('<circle cx="%.4f" cy="%.4f" r="%.4f"/>' % (*tx(x, y), rr) for x, y, rr in holes)
    open(path, 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" viewBox="0 0 {w:.3f} {h:.3f}">'
        f'<g fill="none" stroke="#ff0000" stroke-width="0.1"><path d="{d}"/>{circ}</g></svg>\n')


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
    (cv, cf), cgrid = build_cover(d)
    np.savez_compressed(os.path.join(outdir, '_cover2d.npz'), gx=cgrid[0], gy=cgrid[1], shape=cgrid[2])
    write_stl(os.path.join(outdir, 'corne36_cover_half.stl'), cv, cf, 'corne36 top cover half')
    write_3mf(os.path.join(outdir, 'corne36_cover_half.3mf'), [('corne36 top cover half', cv, cf)])
    if P.get('bottom') == 'acrylic':
        so, sh = build_sheet(d)
        tag = 'corne36_acrylic_%gmm' % P['acrylic_t']
        write_dxf(os.path.join(outdir, tag + '.dxf'), so, sh)
        write_svg(os.path.join(outdir, tag + '.svg'), so, sh)
        meta['sheet_bbox'] = [so.min(0).round(2).tolist(), so.max(0).round(2).tolist()]
        meta['sheet_vertices'] = len(so)
    info = dict(meta=meta, tris=len(f), bbox=[v.min(0).round(2).tolist(), v.max(0).round(2).tolist()], fit_tris=len(tf), cover_tris=len(cf))
    json.dump(dict(info, params=P), open(os.path.join(outdir, 'build_info.json'), 'w'), indent=1)
    print(json.dumps(info))
