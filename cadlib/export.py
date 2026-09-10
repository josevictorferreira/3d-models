"""Export a build123d Part to files suitable for slicing."""

from pathlib import Path

from build123d import Part, export_step, export_stl

# Linear deviation in mm and angular deviation in radians between the true
# surface and the mesh. Fine enough for FDM printing, small enough files.
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.1


def export_part(part: Part, path: Path, *, step: bool = False) -> None:
    """Write `part` as STL to `path`; optionally also a STEP file next to it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(
        part,
        str(path),
        tolerance=STL_TOLERANCE,
        angular_tolerance=STL_ANGULAR_TOLERANCE,
    )
    if step:
        export_step(part, str(path.with_suffix(".step")))
