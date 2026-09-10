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

- `rackmounts/network_switch.py`: 100 x 100 x 26 mm network switch.
- `rackmounts/intel_nuc.py`: NUC7i3BNK, regenerated as a check against the reference STL.
