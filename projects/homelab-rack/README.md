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

- `rackmounts/network_switch.py`: 100 x 100 x 26 mm network switch.
- `rackmounts/intel_nuc.py`: NUC7i3BNK, regenerated as a check against the reference STL.
- `rackmounts/pi_hd_nuc.py`: 2U, three bays: Raspberry Pi 4B in its case, a portable USB drive
  standing on edge in a slot, Intel NUC T9.
