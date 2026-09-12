"""3U 10-inch rackmount for three Intel NUC7i3BNK (115 x 111 x 35 mm) standing on edge.

Three NUCs will not fit side by side lying flat (3 x 115 is wider than the 254 mm panel), so
each one is tipped 90 degrees onto its long side: its 35 mm height becomes the bay width, its
115 mm width becomes the bay height. Three bays then take 125.4 mm across, and the panel has
to be 3U to clear the 115 mm standing height.

Each NUC keeps its front ports facing the rack front and goes in from the open side of the
tray, sliding forward against the bezel lip; the hooks at the back of each bay stop it coming
out. Which way up a NUC lands is free: pick the one that puts its rear power and HDMI sockets
where the cables run.

A NUC draws its cooling air through its bottom panel, which on its side faces a wall, and the
middle NUC faces a wall on both sides. So every wall is honeycombed (`wall_vents`) rather than
carrying the usual single cable window: each NUC's intake breathes straight through the wall
next to it, and the exhaust leaves through the open rear between the hooks.
"""

from _tray import Bay, multi_tray
from build123d import Part

# NUC7i3BNK, lying on its side: width across the rack, depth, height.
NUC_WIDTH = 35
NUC_DEPTH = 111
NUC_HEIGHT = 115

UNITS = 3


def build() -> Part:
    return multi_tray([Bay(NUC_WIDTH, NUC_DEPTH, NUC_HEIGHT)] * 3, units=UNITS, wall_vents=True)
