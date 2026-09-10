"""Reusable physical dimensions, in millimetres.

Values here are what worked on a typical FDM printer; adjust once measured.
"""

# Clearance hole diameters for metric screws (loose fit, printed vertically).
M3_CLEARANCE = 3.4
M4_CLEARANCE = 4.5

# Heat-set insert holes (hole diameter, depth) for the common brass inserts.
M3_INSERT_DIAMETER = 4.0
M3_INSERT_DEPTH = 5.0

# 19-inch rack (EIA-310).
RACK_UNIT = 44.45
RACK_OPENING_WIDTH = 450.85  # between the mounting rails
RACK_MOUNT_HOLE_PITCH = 465.1  # centre to centre, across the rails
RACK_EAR_HOLE_DIAMETER = 6.5
RACK_EAR_HOLE_OFFSET = 15.875  # U centreline to each of the two outer holes

# 10-inch rack: half-width panel, same hole pattern within a U.
RACK10_PANEL_WIDTH = 254
RACK10_EAR_HOLE_INSET = 8.75  # panel edge to hole centre


def rack_height(units: int) -> float:
    """Height of `units` rack units, minus a small gap so adjacent gear does not bind."""
    return units * RACK_UNIT - 0.8
