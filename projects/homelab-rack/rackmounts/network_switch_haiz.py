"""10-inch rackmount for Haiz Network Switch (Switch Grande).

Device dimensions: 200 mm wide, 121 mm deep, 46 mm high.
Fits a 1U form factor with an open top across the switch bay so the switch
sits flush with the rack opening without needing a 2U panel.
"""

from _tray import (
    BEZEL_THICKNESS,
    EAR_SLOT_HEIGHT,
    EAR_SLOT_LENGTH,
    FIT_CLEARANCE,
    OPENING_LIP,
    PANEL_CORNER_RADIUS,
    PANEL_THICKNESS,
    PLATE_INSET,
    PLATE_THICKNESS,
    REAR_CORNER_RADIUS,
    VENT_END_MARGIN,
    WALL_THICKNESS,
    WINDOW_END_MARGIN,
    WINDOW_HEIGHT,
    WINDOW_SIDE_MARGIN,
    plan_rect,
    slab,
    vents,
    wall_root_fill,
)
from build123d import (
    Align,
    Axis,
    Box,
    Part,
    Plane,
    Polygon,
    Pos,
    Sketch,
    SlotOverall,
    extrude,
    fillet,
)

from cadlib.hardware import (
    RACK10_EAR_HOLE_INSET,
    RACK10_PANEL_WIDTH,
    RACK_EAR_HOLE_OFFSET,
    rack_height,
)

# Device dimensions (Haiz large switch).
SWITCH_WIDTH = 200.0
SWITCH_DEPTH = 121.0
SWITCH_HEIGHT = 46.0

UNITS = 1


def _wall_window(x0: float, x1: float, y_bottom: float, z0: float, z1: float) -> Part | None:
    """Vent/port window low on the wall next to the tray floor."""
    height = WINDOW_HEIGHT
    if z1 - z0 <= height:
        return None
    y_mid = y_bottom + WINDOW_SIDE_MARGIN + height / 2
    half = height / 2
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


def build() -> Part:
    """Rackmount tray for Haiz switch: 1U panel with open top over switch bay."""
    panel_height = rack_height(UNITS)

    # 1. Front panel frame with 1U ear slots.
    panel = Box(
        RACK10_PANEL_WIDTH,
        panel_height,
        PANEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    panel = fillet(panel.edges().filter_by(Axis.Z), PANEL_CORNER_RADIUS)

    ear_slots = [
        Pos(
            sx * (RACK10_PANEL_WIDTH / 2 - RACK10_EAR_HOLE_INSET),
            panel_height / 2 + sy * RACK_EAR_HOLE_OFFSET,
        )
        * SlotOverall(EAR_SLOT_LENGTH, EAR_SLOT_HEIGHT)
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    panel -= extrude(Sketch() + ear_slots, PANEL_THICKNESS)

    # 2. Tray cavity and boundary.
    cavity_width = SWITCH_WIDTH + 2 * FIT_CLEARANCE
    tray_width = cavity_width + 2 * WALL_THICKNESS
    x_walls = (-tray_width / 2, tray_width / 2)
    x0 = -cavity_width / 2
    x1 = cavity_width / 2

    plate_bottom = PLATE_INSET
    plate_top = plate_bottom + PLATE_THICKNESS
    wall_top = panel_height

    z_front = BEZEL_THICKNESS
    hook_face = z_front + SWITCH_DEPTH + 2 * FIT_CLEARANCE
    end = hook_face + WALL_THICKNESS

    # 3. Outer tray body with rear hooks.
    body = Part() + [slab(wall_root_fill(x), plate_bottom, wall_top) for x in x_walls]
    body += slab(
        plan_rect(*x_walls, PANEL_THICKNESS, end, REAR_CORNER_RADIUS, REAR_CORNER_RADIUS),
        plate_bottom,
        wall_top,
    )

    # 4. Cavity cutout (open at top and rear opening between hooks).
    inner = REAR_CORNER_RADIUS - WALL_THICKNESS
    cavity = plan_rect(x0, x1, z_front, hook_face, inner, inner)
    if cavity_width > 2 * inner:
        cavity += plan_rect(x0 + inner, x1 - inner, hook_face - 1, end + 1)
    body -= slab(cavity, plate_top, wall_top + 1)

    # 5. Base ventilation grille.
    grille = vents(
        0,
        cavity_width - 2 * OPENING_LIP,
        PANEL_THICKNESS + VENT_END_MARGIN,
        end - VENT_END_MARGIN,
    )
    if grille is not None:
        body -= slab(grille, plate_bottom - 1, plate_top + 1)

    # 6. Front opening: open above the tray floor all the way through the top.
    panel -= Pos(0, plate_top, 0) * Box(
        cavity_width - 2 * OPENING_LIP,
        panel_height - plate_top + 1,
        PANEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    rebate = Pos(0, plate_top, BEZEL_THICKNESS) * Box(
        cavity_width,
        panel_height - plate_top + 1,
        PANEL_THICKNESS - BEZEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    # 7. Side wall cable/plug windows.
    for x_wall in x_walls:
        wall_x = sorted(
            (x_wall, x_wall - WALL_THICKNESS if x_wall > 0 else x_wall + WALL_THICKNESS)
        )
        win = _wall_window(
            *wall_x,
            plate_top,
            PANEL_THICKNESS + WINDOW_END_MARGIN,
            hook_face - WINDOW_END_MARGIN,
        )
        if win is not None:
            body -= win

    return (panel + body) - rebate
