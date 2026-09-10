"""1U 10-inch rackmount for the Intel NUC7i3BNK (115 x 111 x 35 mm).

Regenerates the tray the shared `_tray` design was copied from, minus its wall vent slots and
keystone variant. Useful as a check that the base still matches the reference STL.
"""

from _tray import tray
from build123d import Part

NUC_WIDTH = 115
NUC_DEPTH = 111
NUC_HEIGHT = 35


def build() -> Part:
    return tray(NUC_WIDTH, NUC_DEPTH, NUC_HEIGHT)
