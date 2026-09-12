"""1U open-top 10-inch rackmount for a Raspberry Pi 4B in its case, a portable USB hard drive
and an Intel NUC T9 mini PC, side by side.

Seen from the front, left to right: the Pi bay, a slot the drive stands in on its long edge,
the NUC bay. The Pi and the NUC face the front, each bay as deep as its device with hooks at
the back. The walls stop at the panel's top edge: the Pi fits under it, the NUC stands 8 mm
above it through a notch in the panel, and the drive 19 mm above the slot walls so it can be
lifted out. The unit above must be free at the front.

The drive sits behind solid panel; its slot has a 20 mm end wall instead of hooks, open above
it for the USB plug. Insert it with its port towards the back and the port edge up.

The Pi goes in with its USB and Ethernet ports facing the front, which puts the power and
HDMI sockets against the left wall at the back: the cables pass through that wall's window.
"""

from _tray import Bay, multi_tray
from build123d import Part

PI = Bay(width=66, depth=96, height=34)
HD = Bay(width=9, depth=110, height=58, front=False, rear_wall=20)  # 9 mm thick, on edge
NUC = Bay(width=88, depth=88, height=47)


def build() -> Part:
    return multi_tray([PI, HD, NUC], open_top=True)
