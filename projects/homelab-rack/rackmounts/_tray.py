"""Shared 10-inch rackmount tray: give it a device's outside measurements, get the part.

Construction copied from the Intel NUC7i3BNK 10-inch rackmount already in the rack: a faceplate
with slotted rack ears, a hex-vented plate the device rests on, two side walls that curl round
at the back into hooks, arched gussets bracing the walls to the faceplate on the top and bottom
bands, and a lip each side of the faceplate opening that stops the device 2 mm behind the front.
The device drops in from the open side, slides forward against the lip, and the hooks keep it
from sliding back out.

Axes follow the NUC STL: X across the rack, Y up the rack unit, Z into the rack with the panel
front at Z = 0. Print panel face down, no supports.
"""

from math import sqrt

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Line,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RegularPolygon,
    Sketch,
    SlotOverall,
    ThreePointArc,
    Vector,
    extrude,
    fillet,
    make_face,
)

from cadlib.hardware import (
    RACK10_EAR_HOLE_INSET,
    RACK10_PANEL_WIDTH,
    RACK_EAR_HOLE_OFFSET,
    rack_height,
)

FIT_CLEARANCE = 0.5  # per side of the device, so it slides in without force

# Faceplate.
PANEL_WIDTH = RACK10_PANEL_WIDTH
PANEL_THICKNESS = 4
PANEL_CORNER_RADIUS = 5
EAR_SLOT_LENGTH = 13
EAR_SLOT_HEIGHT = 6.5
OPENING_LIP = 6  # panel left standing each side of the opening; the front stop
BEZEL_THICKNESS = 2  # depth of that lip; the device front sits this far behind the panel

# Tray.
WALL_THICKNESS = 4.35
PLATE_THICKNESS = 4
RIM_THICKNESS = 4  # band at the open edge of the walls that carries the gussets
MIN_RIM = 2  # the rim shrinks to fit a tall device, but not below this
PLATE_INSET = 0.5  # plate face set back from the panel edge so it never rubs the next unit
REAR_CORNER_RADIUS = 10.25  # outer radius; the walls follow it round to form the hooks
WALL_ROOT_FILLET = 8  # between the wall outer face and the panel back
GUSSET_RUN = 44.6  # along the panel back, shortened if the ear slots are in the way
GUSSET_RISE = 33.9  # along the wall
GUSSET_SAGITTA = 3.3  # the brace edge bows this far in towards the corner
MIN_GUSSET_RUN = 10

# Plate vents: honeycomb clipped to a zone inset from the plate edges.
HEX_FLAT = 14.42  # flat to flat
HEX_WEB = 4
VENT_END_MARGIN = 16  # from the panel back and from the rear edge

# Wall windows: elongated hexagon with 45 degree tips, centred on the cavity.
WINDOW_HEIGHT = 13
WINDOW_SIDE_MARGIN = 4  # wall left above and below the window on a short cavity
WINDOW_END_MARGIN = 14


def slab(sketch: Sketch, y0: float, y1: float) -> Part:
    """Extrude a plan-view sketch (x across the rack, y = Z depth) between two heights."""
    return Pos(0, y0, 0) * extrude(Plane.XZ * sketch, amount=-(y1 - y0))


def rear_rounded(width: float, z0: float, z1: float, radius: float) -> Sketch:
    """Plan rectangle from z0 to z1 with its two rear corners rounded."""
    rect = Pos(0, (z0 + z1) / 2) * Rectangle(width, z1 - z0)
    return fillet(rect.vertices().group_by(Axis.Y)[-1], radius)


def wall_root_fill(x_wall: float) -> Sketch:
    """Concave fillet material in the corner between a wall's outer face and the panel back."""
    r = WALL_ROOT_FILLET
    side = 1 if x_wall > 0 else -1
    square = Pos(x_wall + side * r / 2, PANEL_THICKNESS + r / 2) * Rectangle(r, r)
    return square - Pos(x_wall + side * r, PANEL_THICKNESS + r) * Circle(r)


def gusset(x_wall: float, run: float) -> Sketch:
    """Brace from the panel back to a wall's outer face, its free edge a shallow arc."""
    side = 1 if x_wall > 0 else -1
    corner = Vector(x_wall, PANEL_THICKNESS)
    foot = Vector(x_wall + side * run, PANEL_THICKNESS)
    top = Vector(x_wall, PANEL_THICKNESS + GUSSET_RISE)
    chord_mid = (foot + top) / 2
    mid = chord_mid + (corner - chord_mid).normalized() * GUSSET_SAGITTA
    return make_face(Line(corner, foot) + ThreePointArc(foot, mid, top) + Line(top, corner))


def vents(zone_width: float, z0: float, z1: float) -> Sketch | None:
    """Honeycomb: rows that fit fully between z0 and z1, columns clipped to the zone width."""
    hex_radius = HEX_FLAT / sqrt(3)
    pitch = HEX_FLAT + HEX_WEB
    row_pitch = pitch * sqrt(3) / 2
    rows = int((z1 - z0 - 2 * hex_radius) // row_pitch) + 1
    if rows < 1:
        return None
    z_first = (z0 + z1) / 2 - (rows - 1) * row_pitch / 2
    cells = []
    for row in range(rows):
        x_offset = pitch / 2 if row % 2 else 0
        columns = int((zone_width / 2 + HEX_FLAT / 2 - x_offset) // pitch)
        for col in range(-columns - 1, columns + 1):
            x = x_offset + col * pitch
            if abs(x) - HEX_FLAT / 2 < zone_width / 2:
                cells.append(
                    Pos(x, z_first + row * row_pitch) * RegularPolygon(hex_radius, 6, rotation=30)
                )
    zone = Pos(0, (z0 + z1) / 2) * Rectangle(zone_width, z1 - z0)
    return (Sketch() + cells) & zone


def wall_windows(tray_width: float, y0: float, y1: float, z0: float, z1: float) -> Part | None:
    """One cutter through both walls: a stretched hexagon in the Y-Z plane."""
    height = min(WINDOW_HEIGHT, y1 - y0 - 2 * WINDOW_SIDE_MARGIN)
    if height < 4 or z1 - z0 <= height:
        return None
    y_mid, half = (y0 + y1) / 2, height / 2
    outline = Polygon(
        (y_mid - half, z0 + half),
        (y_mid, z0),
        (y_mid + half, z0 + half),
        (y_mid + half, z1 - half),
        (y_mid, z1),
        (y_mid - half, z1 - half),
        align=None,
    )
    return Pos(-tray_width / 2 - 1, 0, 0) * extrude(Plane.YZ * outline, tray_width + 2)


def tray(width: float, depth: float, height: float, units: int = 1) -> Part:
    """Rackmount for a device measuring `width` x `depth` x `height` mm (outside, with feet)."""
    cavity_width = width + 2 * FIT_CLEARANCE
    cavity_height = height + 2 * FIT_CLEARANCE
    cavity_depth = depth + 2 * FIT_CLEARANCE
    panel_height = rack_height(units)
    tray_width = cavity_width + 2 * WALL_THICKNESS
    hook_face = BEZEL_THICKNESS + cavity_depth  # Z of the inside of the rear hooks
    tray_end = hook_face + WALL_THICKNESS
    plate_top = panel_height - PLATE_INSET
    plate_bottom = plate_top - PLATE_THICKNESS
    cavity_bottom = plate_bottom - cavity_height
    if cavity_bottom < MIN_RIM:
        raise ValueError(f"{height} mm tall device does not fit in {units}U; try units={units + 1}")
    rim_bottom = max(0, cavity_bottom - RIM_THICKNESS)
    ear_zone = RACK10_EAR_HOLE_INSET + EAR_SLOT_LENGTH / 2 + 2
    gusset_run = min(GUSSET_RUN, PANEL_WIDTH / 2 - ear_zone - tray_width / 2)

    panel = Box(
        PANEL_WIDTH, panel_height, PANEL_THICKNESS, align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    panel = fillet(panel.edges().filter_by(Axis.Z), PANEL_CORNER_RADIUS)
    ear_slots = [
        Pos(
            sx * (PANEL_WIDTH / 2 - RACK10_EAR_HOLE_INSET),
            panel_height / 2 + sy * RACK_EAR_HOLE_OFFSET,
        )
        * SlotOverall(EAR_SLOT_LENGTH, EAR_SLOT_HEIGHT)
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    panel -= extrude(Sketch() + ear_slots, PANEL_THICKNESS)
    panel -= Pos(0, cavity_bottom, 0) * Box(
        cavity_width - 2 * OPENING_LIP,
        cavity_height,
        PANEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    x_walls = (-tray_width / 2, tray_width / 2)
    outline = rear_rounded(tray_width, PANEL_THICKNESS, tray_end, REAR_CORNER_RADIUS)
    body = slab(outline + [wall_root_fill(x) for x in x_walls], rim_bottom, plate_top)
    if gusset_run >= MIN_GUSSET_RUN:
        braces = Sketch() + [gusset(x, gusset_run) for x in x_walls]
        body += slab(braces, rim_bottom, cavity_bottom) + slab(braces, plate_bottom, plate_top)

    # Cavity: everything but the plate, open at the rear between the hooks.
    cavity = rear_rounded(
        cavity_width, PANEL_THICKNESS, hook_face, REAR_CORNER_RADIUS - WALL_THICKNESS
    ) + Pos(0, tray_end) * Rectangle(tray_width - 2 * REAR_CORNER_RADIUS, 2 * WALL_THICKNESS + 2)
    body -= slab(cavity, rim_bottom - 1, plate_bottom)
    grille = vents(
        cavity_width - 2 * OPENING_LIP,
        PANEL_THICKNESS + VENT_END_MARGIN,
        tray_end - VENT_END_MARGIN,
    )
    if grille is not None:
        body -= slab(grille, plate_bottom - 1, plate_top + 1)
    windows = wall_windows(
        tray_width,
        cavity_bottom,
        plate_bottom,
        PANEL_THICKNESS + WINDOW_END_MARGIN,
        hook_face - WINDOW_END_MARGIN,
    )
    if windows is not None:
        body -= windows

    part = panel + body
    # Rebate behind the lips so the device front reaches the bezel, not the panel back.
    part -= Pos(0, cavity_bottom, BEZEL_THICKNESS) * Box(
        cavity_width,
        cavity_height,
        PANEL_THICKNESS - BEZEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    return part
