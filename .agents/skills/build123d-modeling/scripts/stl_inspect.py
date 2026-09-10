#!/usr/bin/env python3
"""Measure an STL you want to copy or check. Needs only numpy.

All coordinates are relative to the mesh's minimum corner (printed as `origin`), so the model
sits in the positive octant regardless of how it was exported.

  stl_inspect.py FILE planes                 axis-aligned planar faces: axis, position, normal, area
  stl_inspect.py FILE slice AXIS LEVEL...    PNG cross-section(s) perpendicular to AXIS (0=x 1=y 2=z)
  stl_inspect.py FILE probe AXIS U V [U V]   coordinates where a ray along AXIS enters/leaves solid
  stl_inspect.py FILE verts X0 X1 Y0 Y1 Z0 Z1   unique vertices inside a box, plus a circle fit

Reading `planes`: a face at position p with normal -1 followed by one at q with normal +1 means
solid between p and q (a wall or rib of thickness q-p). Normal +1 then -1 means a gap (slot, hole).
Area tells you how big the feature is: divide by a known thickness to get its length.

Reading `slice` images: white is solid. Pixel edges can flicker where a ray grazes a mesh edge,
so confirm anything that matters with `probe` before trusting it.
"""

import re
import struct
import sys
import zlib
from pathlib import Path

import numpy as np


def load(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        v = np.array(re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data), dtype=float)
        return v.reshape(-1, 3, 3)
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    return np.frombuffer(data[84 : 84 + n * 50], dtype=rec)["v"].reshape(-1, 3, 3).astype(float)


def planes(tris: np.ndarray) -> None:
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    n /= np.linalg.norm(n, axis=1)[:, None]
    centre = tris.mean(1)
    for axis, label in enumerate("xyz"):
        sel = np.abs(n[:, axis]) > 0.999
        totals: dict[tuple[float, int], float] = {}
        for pos, sign, a in zip(centre[sel, axis], np.sign(n[sel, axis]), area[sel]):
            key = (round(float(pos), 2), int(sign))
            totals[key] = totals.get(key, 0.0) + float(a)
        print(f"-- faces normal to {label}: position  normal  area mm2 --")
        for (pos, sign), a in sorted(totals.items()):
            if a > 20:
                print(f"  {pos:8.2f}  {sign:+d}  {a:9.1f}")


def crossings(tris: np.ndarray, axis: int, u: float, v: float) -> list[float]:
    """Positions along `axis` where the ray through (u, v) on the other two axes hits a face."""
    ua, va = [a for a in range(3) if a != axis]
    hits = []
    for t in tris:
        p, a = t[:, [ua, va]], t[:, axis]
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9:
            continue
        l0 = ((p[1, 1] - p[2, 1]) * (u - p[2, 0]) + (p[2, 0] - p[1, 0]) * (v - p[2, 1])) / d
        l1 = ((p[2, 1] - p[0, 1]) * (u - p[2, 0]) + (p[0, 0] - p[2, 0]) * (v - p[2, 1])) / d
        l2 = 1 - l0 - l1
        if min(l0, l1, l2) >= -1e-9:
            hits.append(round(float(l0 * a[0] + l1 * a[1] + l2 * a[2]), 2))
    return sorted(set(hits))


def slice_png(tris: np.ndarray, axis: int, level: float, out: Path, res: float = 0.25) -> None:
    size = tris.reshape(-1, 3).max(0)
    ua, va = [a for a in range(3) if a != axis]
    U = np.arange(0, size[ua] + res, res)
    V = np.arange(0, size[va] + res, res)
    count = np.zeros((len(V), len(U)), int)
    for t in tris:
        p, a = t[:, [ua, va]], t[:, axis]
        iu = np.where((U >= p[:, 0].min()) & (U <= p[:, 0].max()))[0]
        iv = np.where((V >= p[:, 1].min()) & (V <= p[:, 1].max()))[0]
        if not len(iu) or not len(iv):
            continue
        gu, gv = np.meshgrid(U[iu], V[iv])
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9:
            continue
        l0 = ((p[1, 1] - p[2, 1]) * (gu - p[2, 0]) + (p[2, 0] - p[1, 0]) * (gv - p[2, 1])) / d
        l1 = ((p[2, 1] - p[0, 1]) * (gu - p[2, 0]) + (p[0, 0] - p[2, 0]) * (gv - p[2, 1])) / d
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (1 - l0 - l1 >= -1e-6)
        count[np.ix_(iv, iu)] += inside & ((l0 * a[0] + l1 * a[1] + (1 - l0 - l1) * a[2]) < level)
    img = ((count % 2 == 1) * 255).astype(np.uint8)[::-1]  # second axis up
    raw = b"".join(b"\x00" + row.tobytes() for row in img)

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
        )

    header = struct.pack(">IIBBBBB", img.shape[1], img.shape[0], 8, 0, 0, 0, 0)
    out.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    print(
        f"{out}  horizontal={'xyz'[ua]} vertical={'xyz'[va]}  {res} mm/px  solid px {(img > 0).sum()}"
    )


def verts(tris: np.ndarray, box: list[float]) -> None:
    v = np.unique(np.round(tris.reshape(-1, 3), 3), axis=0)
    m = np.ones(len(v), bool)
    for axis in range(3):
        m &= (v[:, axis] >= box[2 * axis]) & (v[:, axis] <= box[2 * axis + 1])
    pts = v[m]
    print(f"{len(pts)} vertices")
    for p in pts:
        print(f"  {p[0]:8.2f} {p[1]:8.2f} {p[2]:8.2f}")
    # Circle fit in the plane the box is thinnest in: reveals fillet and hole radii.
    spans = [box[2 * a + 1] - box[2 * a] for a in range(3)]
    flat = int(np.argmin(spans))
    keep = [a for a in range(3) if a != flat]
    q = np.unique(np.round(pts[:, keep], 2), axis=0)
    if len(q) >= 3:
        A = np.c_[2 * q[:, 0], 2 * q[:, 1], np.ones(len(q))]
        c = np.linalg.lstsq(A, (q**2).sum(1), rcond=None)[0]
        r = np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)
        resid = np.abs(np.hypot(q[:, 0] - c[0], q[:, 1] - c[1]) - r).max()
        print(
            f"circle fit in {'xyz'[keep[0]]}{'xyz'[keep[1]]}: centre ({c[0]:.2f}, {c[1]:.2f})"
            f" radius {r:.2f}  max residual {resid:.3f} (small = it really is an arc)"
        )


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        sys.exit(__doc__)
    tris = load(Path(argv[1]))
    origin = tris.reshape(-1, 3).min(0)
    tris = tris - origin
    size = tris.reshape(-1, 3).max(0)
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    volume = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
    print(
        f"origin {origin.round(2)}  size {size.round(2)}  triangles {len(tris)}  volume {volume / 1000:.1f} cm3"
    )
    cmd, args = argv[2], argv[3:]
    if cmd == "planes":
        planes(tris)
    elif cmd == "slice":
        axis = int(args[0])
        for level in args[1:]:
            slice_png(tris, axis, float(level), Path(f"slice_{'xyz'[axis]}{level}.png"))
    elif cmd == "probe":
        axis = int(args[0])
        for u, v in zip(args[1::2], args[2::2]):
            print(
                f"{'xyz'[axis]} crossings at ({u}, {v}): {crossings(tris, axis, float(u), float(v))}"
            )
    elif cmd == "verts":
        verts(tris, [float(x) for x in args[:6]])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
