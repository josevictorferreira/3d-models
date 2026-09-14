"""1U 10-inch rackmount shelf for the full-size Intel NUC (133 x 131 x 48 mm, calipers).

Not a `_tray.py` tray. This machine breathes through its sides, so the tray's tall side walls
are gone: what is left is the vented plate it stands on, a 3 mm lip round the sides and back
that stops it wandering, and the faceplate in front of it. Every face except the bottom one
has open air against it.

The faceplate is solid apart from the front port window, measured off the machine's own face:
13 mm up from its base, 15 mm down from its top, 17 mm in from each side, so 99 x 20 mm, opened
out by the fit clearance all round so the slop in the bay cannot crop it.

1U of panel, but not 1U of rack. Standing on the plate the NUC's top is 8.85 mm above the
panel's top edge, so the unit above has to be free where it sits. That is the trade for not
making this a 2U part; `UNITS = 2` closes it in at the cost of a mostly blank panel.

With no walls there is nothing for the tray's gussets to brace against, so there are none. The
plate is a cantilever off the panel, held by the 4 mm band at the panel's foot and the root
fillets at its sides. Fine for a NUC sitting still; do not lift the loaded shelf by the panel.

The NUC drops in from above and slides forward until its front face meets the panel back.
Print panel face down, no supports.
"""

from _tray import (
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
    plan_rect,
    slab,
    vents,
    wall_root_fill,
)
from build123d import Align, Axis, Box, Part, Pos, Sketch, SlotOverall, extrude, fillet

from cadlib.hardware import (
    RACK10_EAR_HOLE_INSET,
    RACK10_PANEL_WIDTH,
    RACK_EAR_HOLE_OFFSET,
    rack_height,
)

# Intel NUC, full size, outside measurements with feet.
NUC_WIDTH = 133.0
NUC_DEPTH = 131.0
NUC_HEIGHT = 48.0

# Front port window, as insets from the machine's own front face.
PORT_INSET_BOTTOM = 13.0
PORT_INSET_TOP = 15.0
PORT_INSET_SIDE = 17.0

LIP_HEIGHT = 3.0  # retaining lip above the plate: enough to locate the NUC, low enough to breathe

UNITS = 1


def build() -> Part:
    panel_height = rack_height(UNITS)
    plate_bottom = PLATE_INSET
    plate_top = plate_bottom + PLATE_THICKNESS
    lip_top = plate_top + LIP_HEIGHT

    cavity_width = NUC_WIDTH + 2 * FIT_CLEARANCE
    tray_width = cavity_width + 2 * WALL_THICKNESS
    x_walls = (-tray_width / 2, tray_width / 2)
    rear_face = PANEL_THICKNESS + NUC_DEPTH + 2 * FIT_CLEARANCE
    end = rear_face + WALL_THICKNESS

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

    panel -= Pos(0, plate_top + PORT_INSET_BOTTOM - FIT_CLEARANCE, 0) * Box(
        NUC_WIDTH - 2 * PORT_INSET_SIDE + 2 * FIT_CLEARANCE,
        NUC_HEIGHT - PORT_INSET_BOTTOM - PORT_INSET_TOP + 2 * FIT_CLEARANCE,
        PANEL_THICKNESS,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    footprint = plan_rect(*x_walls, PANEL_THICKNESS, end, REAR_CORNER_RADIUS, REAR_CORNER_RADIUS)
    inner = REAR_CORNER_RADIUS - WALL_THICKNESS
    cavity = plan_rect(
        -cavity_width / 2, cavity_width / 2, PANEL_THICKNESS, rear_face, inner, inner
    )

    body = slab(footprint, plate_bottom, plate_top)
    body += slab(footprint - cavity, plate_top, lip_top)  # the lip: sides and back, open in front
    body += [slab(wall_root_fill(x), plate_bottom, lip_top) for x in x_walls]

    grille = vents(
        0,
        cavity_width - 2 * OPENING_LIP,
        PANEL_THICKNESS + VENT_END_MARGIN,
        end - VENT_END_MARGIN,
    )
    if grille is not None:
        body -= slab(grille, plate_bottom - 1, plate_top + 1)

    return panel + body
