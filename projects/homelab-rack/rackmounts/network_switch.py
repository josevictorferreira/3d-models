"""1U 10-inch rackmount for the homelab network switch. Measured with calipers."""

from _tray import tray
from build123d import Part

SWITCH_WIDTH = 100
SWITCH_DEPTH = 100
SWITCH_HEIGHT = 26


def build() -> Part:
    return tray(SWITCH_WIDTH, SWITCH_DEPTH, SWITCH_HEIGHT)
