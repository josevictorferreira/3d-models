"""20 mm calibration cube. Exists to prove the toolchain works end to end."""

from build123d import Box, Part

SIZE = 20


def build() -> Part:
    return Box(SIZE, SIZE, SIZE)
