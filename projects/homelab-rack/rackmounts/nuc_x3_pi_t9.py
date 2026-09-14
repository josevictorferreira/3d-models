"""3U 10-inch rackmount for every machine in one row: three NUC7i3BNK, a Raspberry Pi 4B and
an Intel NUC T9, all standing on edge.

`nuc_x3_pi.py` with a fifth bay. Left to right seen from the front: the Pi, the three NUCs,
the T9. Five bays and their six walls come to 217.1 mm of the 254 mm panel, which is as wide
as this tray gets: the outer walls end 3.2 mm short of the rack ear slots.

That width costs two of the tray's usual features, and both are deliberate:

- No gussets. The brace run would be 1.2 mm, under the 10 mm the tray needs, so `multi_tray`
  omits them. The wide Haiz switch tray already in the rack has none either.
- A 2.2 mm wall-to-panel fillet instead of the usual 8 mm, clamped so it stops 1 mm clear of
  the ear slots and the panel still meets the rail flat.

So the front is braced by the panel and the plate alone. It is stiff enough bolted at four
points, but do not hang the loaded tray by the panel while fitting it.

Every wall is honeycombed: with five bays on edge, all but the outermost faces of the end bays
have a device breathing against them. Exhaust leaves through the open rear between the hooks.

The rear is stepped three ways, deepest to shallowest: NUC 111, Pi 96, T9 88. Tip each NUC
whichever way puts its rear sockets where the cables run, and tip the Pi so its power and HDMI
edge faces up, away from the plate.
"""

from _tray import Bay, multi_tray
from build123d import Part

# Each device lying on its side: width across the rack, depth, height.
NUC = Bay(width=35, depth=111, height=115)  # NUC7i3BNK, 115 x 111 x 35 upright
PI = Bay(width=34, depth=96, height=66)  # Pi 4B in its case, 66 x 96 x 34 upright
T9 = Bay(width=47, depth=88, height=88)  # NUC T9, 88 x 88 x 47 upright

UNITS = 3


def build() -> Part:
    return multi_tray([PI, NUC, NUC, NUC, T9], units=UNITS, wall_vents=True)
