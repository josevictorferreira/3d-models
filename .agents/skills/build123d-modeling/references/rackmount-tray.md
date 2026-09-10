# 10-inch rackmount tray

Reference for `projects/homelab-rack/rackmounts/_tray.py` and for the object it was copied
from. All dimensions in mm.

## Contents

1. Adding a device
2. What scales with the device, what does not
3. Limits and how the tray degrades
4. The reference: Intel NUC7i3BNK 10-inch rackmount (measured)
5. Axes and print orientation

## 1. Adding a device

Measure the outside of the device: width across the rack, depth front to back, height
including rubber feet. Then:

```python
"""1U 10-inch rackmount for <device> (<w> x <d> x <h> mm, calipers)."""

from _tray import tray
from build123d import Part

WIDTH, DEPTH, HEIGHT = 100, 100, 26


def build() -> Part:
    return tray(WIDTH, DEPTH, HEIGHT)  # units=2 for a device taller than ~34 mm
```

`tray()` adds `FIT_CLEARANCE` (0.5) on every side. The device's front face ends up 2 mm behind
the panel front, sitting on the vented plate, with the panel opening exactly the cavity size
minus 6 mm lips on each side. It drops in from the open side and slides forward.

## 2. What scales with the device, what does not

Scales: cavity (device + clearance), tray width, tray depth, panel opening, honeycomb zone
(cavity inset 6 each side, 16 from panel back and rear edge; rows only where a full hex fits),
wall window length (cavity depth minus 14 each end) and height (13, or less on a short cavity),
gusset run (44.6, shortened so it clears the ear slots, dropped below 10).

Fixed style: panel 254 x rack_height(units) x 4 with R5 corners, ear slots 13 x 6.5 centred
8.75 in from the edge and +-15.875 from mid-height, 4.35 walls, 4 plate set 0.5 below the
panel edge, 4 rim band at the open side (shrinks to a minimum of 2 for a tall device),
R10.25 rear corners that the walls follow round into hooks, R8 wall-to-panel fillet, gusset
rise 33.9 with a 3.3 sagitta arc, hexes 14.42 flat-to-flat with 4 webs, 2 mm bezel with a
rebate behind it.

## 3. Limits and how the tray degrades

| Situation | Result |
|---|---|
| height > ~34 (1U) | `ValueError`; pass `units=2` |
| width > ~123 | gussets shortened; below a 10 run they are omitted |
| width > ~215 | tray wider than the ear slots allow; not supported, use a plain panel |
| cavity height < 12 | wall windows omitted |
| depth < ~50 | fewer or no honeycomb rows |

The NUC original had 1 mm vent slots low on the walls and a keystone variant. Neither is in
`_tray.py`; a 27 mm cavity has no room for the slots next to the window.

## 4. The reference: Intel NUC7i3BNK 10-inch rackmount (measured)

Files: `~/Homelab/3d-models/projeto-homelab-rack/rackmount-intel-nuc/` (`.stl`, and a
`2x keystone` variant). Measured with `scripts/stl_inspect.py` on 2026-09-10. Coordinates
relative to the mesh minimum corner, X width, Y height, Z depth, panel front at Z=0.

- Overall 254 x 44.5 x 117.04, 102.7 cm3, 3704 triangles.
- Panel Z 0..4. Ear slots: X 1.44..14.44 (13 long), Y 3.15..9.65 and 34.85..41.35 (6.5 tall),
  centres 31.7 apart. Panel corners R5.
- Opening Z 0..2: X 75.38..178.62, Y 4.55..39.95. Behind it Z 2..4 the opening is the full
  cavity X 69.48..184.52, Y 4..39.95 (the rebate; step face area 469 at Z=2).
- Walls X 65.13..69.48 and 184.52..188.87 (4.35), Y 0..43.95. Cavity 115.04 wide for a 115 mm
  device: the original had zero width clearance.
- Plate Y 39.95..43.95 over X 65.13..188.87, Z 4..117.04; panel top at 44.5 so the plate is
  0.55 inside the U edge. Rim band Y 0..4 is walls + gussets only, open over the cavity.
- Rear corners: outer arc R10.25 centred (75.38, 106.79); inner R5.9 concentric; hook end face
  at X 75.38, Z 112.69..117.04. Rear plate edge Z 117.04 between the hooks only.
- Wall-to-panel fillet R8 on the outer side, full height.
- Gussets on Y 0..4 and 39.95..43.95: from (20.5, 4) on the panel back to (65.13, 37.9) on the
  wall, free edge an arc of R121 (centre (-28.58, 114.84)), sagitta 3.3 towards the corner.
- Honeycomb: hexes 14.42 flat-to-flat, flats parallel to Z, webs 4 (centre pitch 18.42, row
  pitch 15.95). 5 rows, Z centres 28.55 + 15.95 i. Odd rows offset 9.21 and clipped at
  X 75.38 and 178.62 (the opening width), leaving partial hexes at the ends.
- Wall window: elongated hexagon Y 20.95..35.95, flats Z 25.4..91.4, tips at Z 17.9 and 98.9
  (45 degrees), centred on the cavity depth.
- Wall vent slots: 45 slots 1 wide x 10 tall (Y 5..15), Z 16.05..105.05 on a 2 mm pitch.

How each was found: `planes` gave the thicknesses and the 469 mm2 step that revealed the
rebate; `verts` in a box around each corner gave the radii and the gusset arc; `probe` along
Y at plan points settled which layers exist where (e.g. the rim band is open over the cavity,
the plate runs the full wall-to-wall width). A slice image had suggested a slot in the plate
beside each wall; probes showed it was a rendering artifact.

## 5. Axes and print orientation

The NUC STL is stored in print orientation: panel flat, tray growing in +Z. `_tray.py` uses
the same frame with the panel front at Z=0, so the slicer needs no rotation beyond "place on
face". Print panel face down; the hooks are at the top and nothing overhangs.
