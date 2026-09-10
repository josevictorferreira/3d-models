---
name: build123d-modeling
description: Create, change and verify parametric 3D-printable parts in this repo with build123d (Python) and the `cad` CLI. Covers the nix/uv environment, part-file conventions, build123d algebra-mode behaviour that is easy to get wrong, copying the style of an existing STL by measuring its mesh, verifying geometry with ray probes and section images, browser preview, and the shared 10-inch rackmount tray. Use when adding a part under projects/, mounting a new device in the homelab rack, analysing or measuring an STL/3MF, or debugging a build123d/OCP error or a part that builds but looks wrong.
---

# build123d modeling in this repo

Every part is a Python module exposing `build() -> Part`. STLs are outputs, never committed.
Read `AGENTS.md` first for the repo conventions; this skill adds what those rules do not say.

## Environment

- Every Python command must run inside `nix develop` (or direnv). Outside it the venv fails with
  `libstdc++.so.6: cannot open shared object file`. Non-interactive form:
  `nix develop --command bash -c "ruff format . && ruff check . && cad build <part> && pytest -q"`.
- `nix run .#preview <name>` builds one part and opens a self-contained HTML viewer in the
  browser. `cad build|show|preview` accept a bare part name (file stem) or a path.
- Lines starting `Fontconfig warning:` on stderr are noise. Filter them, never fix them.
- `nix flake check` after touching `flake.nix`. Untracked files are invisible to `nix run`
  from a clean clone: `git add` new files before relying on flake apps elsewhere.

## Workflow for a new part

1. Get the numbers: outside dimensions of the device (with feet), what it must clear, how it
   is inserted. Put them as named constants at the top of the file. Name clearances as such.
2. If the part must match an existing object's style, measure that object's mesh first (below).
   Decide the axes up front and state them in the docstring. Prefer the print orientation as
   the model's frame.
3. Build in plan-view sketches extruded between named heights, not by stacking boxes. Booleans
   in this order: solid outer body, subtract cavities, subtract patterns (vents, windows),
   then union the panel and cut anything that crosses both.
4. Verify (below). A part is done when it builds, `pytest -q` passes, and bounding box and
   volume are sane for the physical object. Report the printed numbers, not "should work".

## build123d algebra mode: verified behaviour

Checked in build123d 0.11. Trust these over memory.

- `Plane.XZ`: local x = +X, local y = +Z, normal = -Y. `extrude(Plane.XZ * sketch, amount=-t)`
  grows towards +Y from Y=0. Wrap it: `Pos(0, y0, 0) * extrude(..., amount=-(y1 - y0))`.
- `Plane.YZ`: local x = +Y, local y = +Z, normal = +X.
- `Rectangle`, `Circle`, `SlotOverall`, `RegularPolygon` are centred; place with `Pos(x, y) *`.
  `Polygon(*points)` is also centred by default: pass `align=None` for absolute coordinates.
- `RegularPolygon(r, 6, rotation=30)` puts the flats vertical (tips along local y); `r` is the
  circumradius, so flat-to-flat `f` needs `r = f / sqrt(3)`.
- Union a list: `Sketch() + [s1, s2, ...]`, `Part() + [...]`. Intersect sketches with `&`.
- 2D fillet: `fillet(sketch.vertices().group_by(Axis.Y)[-1], r)` rounds the two max-Y corners.
  Safer than filleting 3D edges that end against other faces; where a fillet must stop at a
  gusset or rib, model the fillet material as a sketch (square minus circle) and extrude it.
- Face from curves: `make_face(Line(a, b) + ThreePointArc(b, m, c) + Line(c, a))`. The arc's
  midpoint must keep the loop simple; a self-intersecting loop gives a tiny area, not an error.
- `part.is_valid` and `part.volume` are properties. `part.bounding_box().size` for dimensions.
- Ray probe a solid: `part.intersect(Line(p, p + dir * 300)).vertices()` returns the entry and
  exit points along the ray. `None` means the ray missed everything.
- STL export is binary. `export_stl` tolerance lives in `cadlib/export.py`; do not override
  it per part.

## Copying the style of an existing STL

Do not eyeball a mesh. Measure it with `scripts/stl_inspect.py` (numpy only, run inside
`nix develop`), in this order:

1. `planes`: every axis-aligned face with position, normal direction and area. This gives
   plate thicknesses, wall positions, slot pitches and, from area / known thickness, feature
   lengths. Read `-1` then `+1` as solid between them, `+1` then `-1` as a gap.
2. `slice AXIS LEVEL...`: PNG cross-sections; view them with the Read tool. Use them to
   understand topology (what is a wall, a gusset, a hook), not for numbers.
3. `verts X0 X1 Y0 Y1 Z0 Z1`: unique vertices inside a box, with a least-squares circle fit
   in the box's thinnest plane. Fillet and hook radii, slot ends, arc sagittas come from here.
   A residual under 0.01 means a true arc; larger means several arcs or a straight edge.
4. `probe AXIS U V ...`: exact entry/exit coordinates of a ray. Use it to confirm the layer
   stack at a point. Slice images lie at grazing edges; probes do not.

Then write the measured numbers as constants with the original's value in a comment when you
change it. Worked example and the resulting geometry: [references/rackmount-tray.md](references/rackmount-tray.md).

## Verifying a built part

- `cad build <part>` prints bounding box and volume. Compare with the object: a tray for a
  100 mm device that is 90 mm wide is wrong before anything else is checked.
- Ray-probe the features that matter (cavity width, wall positions, slot separation, layer
  stacks) with `part.intersect(Line(...))`, in a throwaway script that imports the part module
  from `projects/...` (add its directory to `sys.path` so `_helper` imports work).
- Render section images of `out/.../part.stl` with `stl_inspect.py slice` and read them.
- `nix run .#preview <part>` for a look in the browser; a screenshot of the page through the
  chrome-devtools tools is enough to confirm it renders when the user cannot look.
- Before claiming done: `ruff format`, `ruff check`, `pytest -q`, and the `cad build` numbers
  in the final message.

## Homelab rackmounts

New devices for the 10-inch rack use the shared tray in
`projects/homelab-rack/rackmounts/_tray.py`: measure the device, add a five-line part calling
`tray(width, depth, height)`. Limits, what scales with the device and what does not, and the
reference geometry of the original NUC mount are in
[references/rackmount-tray.md](references/rackmount-tray.md).
