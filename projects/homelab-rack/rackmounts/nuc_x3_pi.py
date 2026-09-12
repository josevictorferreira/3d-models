"""3U 10-inch rackmount for three Intel NUC7i3BNK and a Raspberry Pi 4B, all standing on edge.

The same idea as `intel_nuc_x3.py` with a fourth bay added: every device is tipped 90 degrees
onto its long side, so the face it normally shows the rack front stays forward but is now tall
and narrow. Seen from the front, left to right: the Pi, then the three NUCs. Four bays take
164.75 mm of the 254 mm panel; the 3U height is still set by the NUC's 115 mm width.

The Pi bay is 15 mm shallower than the NUC bays, so the tray's rear is stepped: the Pi's hooks
sit forward of the NUCs'. The wall they share is vented only as deep as the Pi bay, so nothing
cuts into its rear corner.

Every wall is honeycombed. A NUC breathes through its bottom panel, which on its side faces a
wall, and each of the middle two NUCs faces a wall on both sides; the Pi's case vents land the
same way. Exhaust leaves through the open rear between the hooks.

Tip each NUC whichever way puts its rear power and HDMI sockets where the cables run. Tip the
Pi so its power and HDMI edge faces up, away from the plate: the bay is cut to the full 116 mm
cavity, so a 66 mm Pi leaves 50 mm of open slot above it for those cables, and the panel closes
that gap off at the front.
"""

from _tray import Bay, multi_tray
from build123d import Part

# Each device lying on its side: width across the rack, depth, height.
NUC = Bay(width=35, depth=111, height=115)  # NUC7i3BNK, 115 x 111 x 35 upright
PI = Bay(width=34, depth=96, height=66)  # Pi 4B in its case, 66 x 96 x 34 upright

UNITS = 3


def build() -> Part:
    return multi_tray([PI, NUC, NUC, NUC], units=UNITS, wall_vents=True)
