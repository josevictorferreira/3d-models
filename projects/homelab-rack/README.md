# homelab-rack

Printed parts for a 10-inch homelab rack: trays, ears and adapters under `rackmounts/`.

Rack dimensions (rack unit, rail opening, ear hole size) come from `cadlib/hardware.py`.
Project-wide constants that are not rack standards go in `_common.py` here once the first part needs them.

## Rackmount trays

`rackmounts/_tray.py` is the shared 10-inch tray, copied from the Intel NUC7i3BNK rackmount already
in the rack: hex-vented plate, side walls with rear hooks, gussets, slotted ears, 6 mm front lips.
To mount a new device, measure its outside (width across the rack, depth, height including feet)
and add a file:

```python
from _tray import tray
from build123d import Part


def build() -> Part:
    return tray(width, depth, height)  # mm; add units=2 if it does not fit 1U
```

Then `nix run .#preview <name>`. Print panel face down, no supports. Hardware: 4 x M6 rack screws.

Several devices can share one tray: `multi_tray([Bay(...), Bay(...)], units=2)` gives each its
own bay, depth and hooks, side by side behind one panel. A `Bay(front=False)` hides behind solid
panel; `Bay(rear_wall=20)` replaces its hooks with a 20 mm end wall, open above for a cable.
`open_top=True` (on `tray` too) stops the walls at the panel's top edge with no rim band, so a
device taller than the unit stands out of the tray through a notch in the panel.
`wall_vents=True` swaps the single cable window for honeycomb through every wall, inner walls
included, for a device that breathes through the face it presents to a wall.

- `rackmounts/network_switch.py`: 100 x 100 x 26 mm network switch.
- `rackmounts/network_switch_haiz.py`: 1U open-top, 200 x 121 x 46 mm Haiz network switch.
- `rackmounts/intel_nuc.py`: NUC7i3BNK, regenerated as a check against the reference STL.
- `rackmounts/intel_nuc_x3.py`: 3U, three NUC7i3BNK standing on edge side by side,
  honeycombed walls so each one's bottom-panel intake breathes.
- `rackmounts/nuc_x3_pi.py`: 3U, the same three NUCs on edge plus a Raspberry Pi 4B on edge
  beside them; 164.75 mm wide, stepped rear, honeycombed walls.
- `rackmounts/pi_hd_nuc.py`: 1U open-top, three bays: Raspberry Pi 4B in its case, a portable
  USB drive standing on edge in a slot, Intel NUC T9 (stands 8 mm above the panel).
