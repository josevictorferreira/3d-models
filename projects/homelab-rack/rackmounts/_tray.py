"""Shared 10-inch rackmount tray: give it a device's outside measurements, get the part.

Construction copied from the Intel NUC7i3BNK 10-inch rackmount already in the rack: a faceplate
with slotted rack ears, a hex-vented plate the device rests on, two side walls that curl round
at the back into hooks, arched gussets bracing the walls to the faceplate on the top and bottom
bands, and a lip each side of the faceplate opening that stops the device 2 mm behind the front.
The device drops in from the open side, slides forward against the lip, and the hooks keep it
from sliding back out.

Several devices can share one tray: `multi_tray([Bay(...), Bay(...)])` puts them side by side,
each in a bay of its own depth with its own hooks, the bays sharing a wall. A bay can be closed
at the front (the device hides behind solid panel) and can swap its hooks for a low end wall
that a cable passes over.

Axes follow the NUC STL: X across the rack, Y up the rack unit, Z into the rack with the panel
front at Z = 0. Print panel face down, no supports.
"""

from collections.abc import Sequence
from dataclasses import dataclass
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
    RACK_UNIT,
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
MIN_VENT_CELL = 2  # a cell clipped narrower than this is dropped, not left as a sliver

# Wall windows: elongated hexagon with 45 degree tips, low on the wall next to the plate so a
# side-mounted power or HDMI plug can pass through it.
WINDOW_HEIGHT = 15
WINDOW_SIDE_MARGIN = 4  # wall left between the window and the plate, and above it if short
WINDOW_END_MARGIN = 14


@dataclass(frozen=True)
class Bay:
    """One compartment of a tray: the outside measurements of the device it holds, in mm.

    `front` opens the faceplate so the device shows through the bezel; without it the device
    sits behind solid panel. `rear_wall` swaps the rear hooks for a plain end wall that tall
    (measured from the plate), leaving the rear open above it for a cable into the device.
    """

    width: float
    depth: float
    height: float
    front: bool = True
    rear_wall: float | None = None


def slab(sketch: Sketch, y0: float, y1: float) -> Part:
    """Extrude a plan-view sketch (x across the rack, y = Z depth) between two heights."""
    return Pos(0, y0, 0) * extrude(Plane.XZ * sketch, amount=-(y1 - y0))


def plan_rect(
    x0: float, x1: float, z0: float, z1: float, r_left: float = 0, r_right: float = 0
) -> Sketch:
    """Plan rectangle with its rear (max Z) corners rounded by the given radii, 0 for square."""
    rect = Pos((x0 + x1) / 2, (z0 + z1) / 2) * Rectangle(x1 - x0, z1 - z0)
    if r_left > 0:
        rect = fillet(rect.vertices().group_by(Axis.Y)[-1].sort_by(Axis.X)[:1], r_left)
    if r_right > 0:
        rect = fillet(rect.vertices().group_by(Axis.Y)[-1].sort_by(Axis.X)[-1:], r_right)
    return rect


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


def vents(x_mid: float, zone_width: float, z0: float, z1: float) -> Sketch | None:
    """Honeycomb: rows that fit fully between z0 and z1, columns clipped to the zone width."""
    hex_radius = HEX_FLAT / sqrt(3)
    pitch = HEX_FLAT + HEX_WEB
    row_pitch = pitch * sqrt(3) / 2
    rows = int((z1 - z0 - 2 * hex_radius) // row_pitch) + 1
    if rows < 1 or zone_width < HEX_FLAT:
        return None
    z_first = (z0 + z1) / 2 - (rows - 1) * row_pitch / 2
    cells = []
    for row in range(rows):
        x_offset = pitch / 2 if row % 2 else 0
        columns = int((zone_width / 2 + HEX_FLAT / 2 - x_offset) // pitch)
        for col in range(-columns - 1, columns + 1):
            x = x_offset + col * pitch
            if abs(x) - HEX_FLAT / 2 < zone_width / 2 - MIN_VENT_CELL:
                cells.append(
                    Pos(x, z_first + row * row_pitch) * RegularPolygon(hex_radius, 6, rotation=30)
                )
    zone = Pos(0, (z0 + z1) / 2) * Rectangle(zone_width, z1 - z0)
    return Pos(x_mid, 0) * ((Sketch() + cells) & zone)


def wall_window(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Part | None:
    """Cutter through one wall spanning x0..x1: a stretched hexagon in the Y-Z plane."""
    height = min(WINDOW_HEIGHT, y1 - y0 - 2 * WINDOW_SIDE_MARGIN)
    if height < 4 or z1 - z0 <= height:
        return None
    y_mid, half = y1 - WINDOW_SIDE_MARGIN - height / 2, height / 2
    outline = Polygon(
        (y_mid - half, z0 + half),
        (y_mid, z0),
        (y_mid + half, z0 + half),
        (y_mid + half, z1 - half),
        (y_mid, z1),
        (y_mid - half, z1 - half),
        align=None,
    )
    return Pos(x0 - 1, 0, 0) * extrude(Plane.YZ * outline, x1 - x0 + 2)


def wall_honeycomb(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Part | None:
    """Cutter through one wall spanning x0..x1: the plate's honeycomb, stood up in the Y-Z plane.

    Same lattice as `vents`, so the holes in the walls and in the plate read as one pattern and
    line up along the rack's depth. Rows run up the wall, clipped to y0..y1.
    """
    grille = vents((y0 + y1) / 2, y1 - y0, z0, z1)
    if grille is None:
        return None
    return Pos(x0 - 1, 0, 0) * extrude(Plane.YZ * grille, x1 - x0 + 2)


def multi_tray(
    bays: Sequence[Bay], units: int = 1, open_top: bool = False, wall_vents: bool = False
) -> Part:
    """Rackmount with one bay per device, laid side by side from -X to +X.

    The walls are as tall as the tallest front-facing device, with a rim band above. A device
    in a closed-front bay may stand taller and show above the walls, which is how a drive on
    edge gets pulled out.

    `open_top` instead runs the walls to the panel's top edge with no rim band, and any device
    taller than the unit simply stands out of the tray (its panel opening becomes a notch in
    the top edge). Needs the unit above to be free where the devices are.

    `wall_vents` replaces the single cable window with honeycomb through every wall, inner walls
    included, for a device that breathes through the face it presents to a wall.
    """
    panel_height = rack_height(units)
    plate_top = panel_height - PLATE_INSET
    plate_bottom = plate_top - PLATE_THICKNESS
    if open_top:
        cavity_bottom = rim_bottom = 0
    else:
        cavity_height = max(bay.height for bay in bays if bay.front) + 2 * FIT_CLEARANCE
        cavity_bottom = plate_bottom - cavity_height
        if cavity_bottom < MIN_RIM:
            raise ValueError(
                f"{cavity_height} mm cavity does not fit in {units}U; try units={units + 1}"
            )
        rim_bottom = max(0, cavity_bottom - RIM_THICKNESS)
    widths = [bay.width + 2 * FIT_CLEARANCE for bay in bays]
    tray_width = sum(widths) + (len(bays) + 1) * WALL_THICKNESS
    x_walls = (-tray_width / 2, tray_width / 2)
    ear_zone = RACK10_EAR_HOLE_INSET + EAR_SLOT_LENGTH / 2 + 2
    gusset_run = min(GUSSET_RUN, PANEL_WIDTH / 2 - ear_zone - tray_width / 2)

    panel = Box(
        PANEL_WIDTH, panel_height, PANEL_THICKNESS, align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    panel = fillet(panel.edges().filter_by(Axis.Z), PANEL_CORNER_RADIUS)
    ear_slots = [
        Pos(
            sx * (PANEL_WIDTH / 2 - RACK10_EAR_HOLE_INSET),
            panel_height / 2 + (u - (units - 1) / 2) * RACK_UNIT + sy * RACK_EAR_HOLE_OFFSET,
        )
        * SlotOverall(EAR_SLOT_LENGTH, EAR_SLOT_HEIGHT)
        for sx in (-1, 1)
        for u in range(units)
        for sy in (-1, 1)
    ]
    panel -= extrude(Sketch() + ear_slots, PANEL_THICKNESS)

    body = Part() + [slab(wall_root_fill(x), rim_bottom, plate_top) for x in x_walls]
    if gusset_run >= MIN_GUSSET_RUN:
        braces = Sketch() + [gusset(x, gusset_run) for x in x_walls]
        body += slab(braces, plate_bottom, plate_top)
        if cavity_bottom > rim_bottom:  # the rim band, absent on an open-top tray
            body += slab(braces, rim_bottom, cavity_bottom)

    # Bay geometry along Z: device front, inside face of the rear stop, outside of the tray.
    fronts = [BEZEL_THICKNESS if bay.front else PANEL_THICKNESS for bay in bays]
    hook_faces = [z + bay.depth + 2 * FIT_CLEARANCE for z, bay in zip(fronts, bays)]
    ends = [z + WALL_THICKNESS for z in hook_faces]
    rebates = []
    x0 = x_walls[0] + WALL_THICKNESS
    for i, (bay, width) in enumerate(zip(bays, widths)):
        x1 = x0 + width
        x_mid = (x0 + x1) / 2
        z_front, hook_face, end = fronts[i], hook_faces[i], ends[i]
        outer = (x0 - WALL_THICKNESS, x1 + WALL_THICKNESS)
        # Rear corners are rounded where they are exposed: at the tray's sides, and against
        # a shallower neighbour. Against a deeper neighbour the wall simply carries on. An end
        # wall keeps a uniform thickness round its square inside corners, so its radius is one
        # wall.
        radius = WALL_THICKNESS if bay.rear_wall is not None else REAR_CORNER_RADIUS
        r_left = radius if i == 0 or ends[i - 1] < end else 0
        r_right = radius if i == len(bays) - 1 or ends[i + 1] < end else 0
        if bay.rear_wall is None:
            body += slab(
                plan_rect(*outer, PANEL_THICKNESS, end, r_left, r_right), rim_bottom, plate_top
            )
            inner = REAR_CORNER_RADIUS - WALL_THICKNESS
            cavity = plan_rect(x0, x1, z_front, hook_face, inner, inner)
            if width > 2 * inner:  # open at the rear between the hooks
                cavity += plan_rect(x0 + inner, x1 - inner, hook_face - 1, end + 1)
            body -= slab(cavity, rim_bottom - 1, plate_bottom)
        else:
            wall_top = plate_bottom - bay.rear_wall
            body += slab(
                plan_rect(*outer, PANEL_THICKNESS, end, r_left, r_right), wall_top, plate_top
            )
            body += slab(plan_rect(*outer, PANEL_THICKNESS, hook_face), rim_bottom, wall_top)
            body -= slab(plan_rect(x0, x1, z_front, hook_face), rim_bottom - 1, plate_bottom)
        grille = vents(
            x_mid,
            width - 2 * OPENING_LIP,
            PANEL_THICKNESS + VENT_END_MARGIN,
            end - VENT_END_MARGIN,
        )
        if grille is not None:
            body -= slab(grille, plate_bottom - 1, plate_top + 1)
        if bay.front:
            opening_height = bay.height + 2 * FIT_CLEARANCE
            panel -= Pos(x_mid, plate_bottom - opening_height, 0) * Box(
                width - 2 * OPENING_LIP,
                opening_height,
                PANEL_THICKNESS,
                align=(Align.CENTER, Align.MIN, Align.MIN),
            )
            # Rebate behind the lips so the device front reaches the bezel, not the panel back.
            rebates.append(
                Pos(x_mid, plate_bottom - opening_height, BEZEL_THICKNESS)
                * Box(
                    width,
                    opening_height,
                    PANEL_THICKNESS - BEZEL_THICKNESS,
                    align=(Align.CENTER, Align.MIN, Align.MIN),
                )
            )
        x0 = x1 + WALL_THICKNESS

    if wall_vents:
        # Every wall, the shared inner ones too. A wall is cut only as deep as its shallower
        # neighbour, so the cut never reaches into that bay's rear corner and hook.
        x = x_walls[0]
        for j in range(len(bays) + 1):
            reach = min(hook_faces[max(j - 1, 0)], hook_faces[min(j, len(bays) - 1)])
            grille = wall_honeycomb(
                x,
                x + WALL_THICKNESS,
                cavity_bottom,
                plate_bottom,
                PANEL_THICKNESS + WINDOW_END_MARGIN,
                reach - WINDOW_END_MARGIN,
            )
            if grille is not None:
                body -= grille
            if j < len(bays):
                x += WALL_THICKNESS + widths[j]
    else:
        for x_wall, hook_face in ((x_walls[0], hook_faces[0]), (x_walls[1], hook_faces[-1])):
            wall_x = sorted(
                (x_wall, x_wall - WALL_THICKNESS if x_wall > 0 else x_wall + WALL_THICKNESS)
            )
            window = wall_window(
                *wall_x,
                cavity_bottom,
                plate_bottom,
                PANEL_THICKNESS + WINDOW_END_MARGIN,
                hook_face - WINDOW_END_MARGIN,
            )
            if window is not None:
                body -= window

    part = panel + body
    for rebate in rebates:
        part -= rebate
    return part


def tray(
    width: float,
    depth: float,
    height: float,
    units: int = 1,
    open_top: bool = False,
    wall_vents: bool = False,
) -> Part:
    """Rackmount for a device measuring `width` x `depth` x `height` mm (outside, with feet)."""
    return multi_tray([Bay(width, depth, height)], units, open_top, wall_vents)
