# 10-inch rackmount tray

Reference for `projects/homelab-rack/rackmounts/_tray.py` and for the object it was copied
from. All dimensions in mm.

## Contents

1. Adding a device
2. What scales with the device, what does not
3. Limits and how the tray degrades
4. The reference: Intel NUC7i3BNK 10-inch rackmount (measured)
5. Axes and print orientation
6. Several devices in one tray

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
wall window length (cavity depth minus 14 each end) and height (15, or less on a short cavity;
its lower edge always 4 above the plate, so side-mounted plugs pass through it), gusset run
(44.6, shortened so it clears the ear slots, dropped below 10). For `units=2` the ears get
two slots per U, each pair at +-15.875 from that U's centreline.

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
| width > ~199.5 | gusset run under 10; gussets omitted |
| width > ~207.5 | root fillet clamped so it stops `EAR_CLEARANCE` (1) short of the ear slots |
| width > ~221.5 | clamp leaves no fillet at all; the walls meet the panel square |
| width > ~223.5 | walls themselves reach the ear slots; not supported, use a plain panel |
| cavity height < 12 | wall windows omitted |
| depth < ~50 | fewer or no honeycomb rows |
| vent zone < ~30 wide | most cells clipped away; a 36 mm bay keeps 4 plate hexes |

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
- Wall-to-panel fillet R8 on the outer side, full height. Its widest point is at the panel back
  (Z=4) and it tapers inward from there, so what has to clear the ear slots is `tray_width / 2 +
  the radius`. `multi_tray` shrinks the radius to keep that 1 mm short of the slots; without the
  clamp a tray over ~207.5 wide stands proud of the panel back where the rail bolts on and will
  not sit flat. (`network_switch_haiz.py` builds its own body at 209.7 wide and keeps the full
  R8: it protrudes 0.076 mm over a 1.1 mm band, under one layer, so it mounts fine.)
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

## 6. Several devices in one tray

`multi_tray([Bay(width, depth, height), ...], units)` lays the bays out from -X to +X (left to
right seen from the front), each with its own depth and rear hooks, sharing a 4.35 wall with its
neighbour. The rear is stepped: an exposed rear corner (tray side, or against a shallower
neighbour) gets the R10.25 curl; against a deeper neighbour the wall carries on past the hook.
Wall height comes from the tallest `front=True` bay. Vents, panel opening and rebate are per
bay; windows are cut only in the two outer walls. Options per bay:

- `front=False`: no panel opening or rebate, the device sits against the panel back at Z = 4.
- `open_top=True` (a `multi_tray`/`tray` argument, not per bay): walls run to the panel's top
  edge, no rim band and only the plate-band gussets; a front bay taller than the unit gets a
  notch through the panel's top edge instead of an error. Use it when a 47 mm device must live
  on a 1U panel and the unit above is free. Preferred over 2U for short walls: on a 2U panel
  the rim-band gussets float mid-panel and read as a second floor.
- `wall_vents=True` (also a `multi_tray`/`tray` argument): every wall, inner ones included, is
  cut with the plate's honeycomb instead of the single elongated-hexagon cable window. Same
  lattice as the plate (14.42 flat-to-flat, 4 webs) stood up in the Y-Z plane, so the two
  patterns line up along the rack's depth; margins are the window's (4 from the plate and the
  cavity bottom, 14 from the panel back). Each wall is cut only as deep as its *shallower*
  neighbour, so it never reaches into that bay's rear corner and hook. Use it when the device
  vents through a face that ends up against a wall, which is what standing one on edge does.
- `rear_wall=h`: no hooks; a plain end wall `h` tall from the plate closes the bay, and the bay
  is open at the rear above it so a plug can reach the device. The end wall's outer corners are
  R4.35 so it stays one wall thick round its square inside. A device in such a bay may stand
  taller than the walls (it does not set the wall height), which is how it gets lifted out.

Design notes learned on the first multi-bay tray:

- A rear stop at a bay's own depth is the same R10.25 curl the tray end has, just attached to a
  wall that continues past it; against a deeper neighbour skip the outer rounding, or a
  1.9 mm sliver is left where the arc meets the continuing wall. This is why each bay can be
  its own depth with a stepped rear instead of a second set of hooks.
- A closed end wall with square inside corners thins to 1.9 mm at the corners if given the
  R10.25 outer radius; radius = wall thickness keeps it uniform.
- A drive on edge is retained by a 10 mm slot and an end wall about a third of its height; the
  rest of the rear stays open for the plug, and the drive should stand a few mm above the
  walls or it cannot be gripped. The bay's `height` is the drive's real height, and only
  `front=True` bays set the wall height.
- Wall height is one number for the whole tray; a shorter front device just gets a taller lip
  above its opening. Panel openings are per device height, rebates likewise.
- `fillet` on a sketch vertex list: after filleting one corner, re-select vertices before the
  next; `group_by(Axis.Y)[-1].sort_by(Axis.X)[:1]` picks the left rear corner, `[-1:]` the right.

A cell that the zone clips to less than `MIN_VENT_CELL` (2) is dropped rather than left as a
sliver. Without this a narrow zone produced unprintable slots: 0.79 mm in a 24 mm bay zone,
0.4 mm in the Haiz switch's 189 mm one (four of them, 54.76 mm3 - the only geometry change the
fix made to an existing part).

`projects/homelab-rack/rackmounts/pi_hd_nuc.py` is the worked example: Pi bay 67 wide x 97 deep,
a 10 x 111 slot for a 9 mm drive on edge with a 20 mm end wall, NUC bay 89 x 89; tray 183.4
wide, 119.35 deep, 1U open-top (the NUC stands 8 mm above the panel, the drive 19 mm above the
slot walls). `pytest` and the `tray()` wrapper guard the single-bay geometry: the
refactor to bays reproduced the NUC and switch trays to within 1e-5 mm3.
