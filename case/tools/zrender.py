"""Tiny orthographic z-buffer renderer for small-triangle meshes (point-splat per triangle)."""
import numpy as np
from PIL import Image


def view_matrix(elev, azim):
    a, e = np.radians(azim), np.radians(elev)
    # camera looks from direction (cos e cos a, cos e sin a, sin e) towards the origin
    fwd = -np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross(fwd, [0, 0, 1]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.stack([right, up, -fwd])          # rows: screen x, screen y, depth (towards viewer)


def render(parts, elev=35, azim=-58, width=1200, pad=30, bg=(255, 255, 255), n=7, light=(0.3, -0.6, 0.9)):
    """parts: list of (verts, faces, rgb 0..1, alpha). alpha < 1 parts are blended over the opaque ones."""
    R = view_matrix(elev, azim); L = np.array(light) / np.linalg.norm(light)
    allv = np.concatenate([p[0] for p in parts]) @ R.T
    lo, hi = allv.min(0), allv.max(0)
    scale = (width - 2 * pad) / (hi[0] - lo[0])
    height = int((hi[1] - lo[1]) * scale + 2 * pad)
    # barycentric sample pattern
    u, v = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n)); m = (u + v) <= 1
    bu, bv = u[m], v[m]; bw = 1 - bu - bv

    def splat(v3, f, rgb):
        tri = v3[f]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        k = 0.35 + 0.65 * np.abs(nrm @ L)                       # two-sided Lambert
        col = np.clip(np.array(rgb)[None] * k[:, None], 0, 1)
        ts = tri @ R.T
        pts = ts[:, None, 0] * bw[None, :, None] + ts[:, None, 1] * bu[None, :, None] + ts[:, None, 2] * bv[None, :, None]
        px = ((pts[..., 0] - lo[0]) * scale + pad).astype(np.int32).ravel()
        py = ((hi[1] - pts[..., 1]) * scale + pad).astype(np.int32).ravel()
        dz = pts[..., 2].ravel()
        cc = np.repeat(col, len(bu), axis=0)
        ok = (px >= 0) & (px < width) & (py >= 0) & (py < height)
        return px[ok], py[ok], dz[ok], cc[ok]

    def zbuf(chunks):
        px = np.concatenate([c[0] for c in chunks]); py = np.concatenate([c[1] for c in chunks])
        dz = np.concatenate([c[2] for c in chunks]); cc = np.concatenate([c[3] for c in chunks])
        idx = py * width + px
        order = np.lexsort((-dz, idx))                           # nearest (largest dz) first per pixel
        idx, dz, cc = idx[order], dz[order], cc[order]
        first = np.r_[True, idx[1:] != idx[:-1]]
        depth = np.full(width * height, -np.inf); img = np.tile(np.array(bg, float) / 255, (width * height, 1))
        depth[idx[first]] = dz[first]; img[idx[first]] = cc[first]
        return depth, img

    opaque = [splat(p[0], p[1], p[2]) for p in parts if p[3] >= 1]
    depth, img = zbuf(opaque)
    for p in parts:
        if p[3] >= 1:
            continue
        d2, c2 = zbuf([splat(p[0], p[1], p[2])])
        front = d2 > depth
        img[front] = img[front] * (1 - p[3]) + c2[front] * p[3]
    return Image.fromarray((img.reshape(height, width, 3) * 255).astype(np.uint8))
