# AGENTS.md

Guidance for coding agents working in this repo.

## What this repo is

Python + build123d source that generates STL files for 3D printing. Every part is code; STLs are
build outputs and are never committed.

## Environment

- Always work inside `nix develop` (or direnv). Never `pip install`; deps live in
  `pyproject.toml` / `uv.lock`. Add with `uv add <pkg>` (or `uv add --dev`) and commit the lock.
- Host is NixOS. If an import fails with a missing `.so`, add the library to `nativeLibs` in
  `flake.nix`. Never add fontconfig or freetype there: the OCP wheel bundles its own.
- Python 3.13. build123d 0.11 pins the `cadquery-ocp-novtk` 7.9 wheels; do not add VTK.
- `Fontconfig warning:` lines on stderr are harmless: the wheel's bundled fontconfig is older
  than the host's font configuration. Do not add code to silence them.

## Conventions

- One part per file under `projects/`, nested as needed. A part module exposes `build() -> Part`.
  Files whose name starts with `_` are shared helpers and are not built. A part may
  `from _common import ...` a helper in its own directory or any parent directory within
  `projects/`; the CLI puts those directories on `sys.path` during import.
- Dimensions are named constants (millimetres) at the top of the file, not magic numbers in
  geometry calls. Print-related allowances (clearances, tolerances) are named as such.
- Reusable dimensions (screw clearances, heat-set inserts, rack unit maths) go in
  `cadlib/hardware.py`, not copied between projects.
- Part files stay headless: never import `ocp_vscode` in them. Use `cad preview` (browser) or
  `cad show` (ocp-vscode) to view.
- Output path mirrors source path: `projects/a/b/c.py` -> `out/a/b/c.stl`.
- build123d 0.11 API notes: `part.is_valid` and `part.volume` are properties, not methods.
- Style: `ruff check .` and `ruff format .` clean, line length 100.

## Verifying work

```
cad build <file>      # exports; prints bounding box and volume; non-zero exit on failure
pytest -q             # every part: builds, is_valid, volume > 0
nix flake check       # after touching flake.nix
```

A change to a part is done when its STL builds, tests pass, and the printed bounding box and
volume are sane for the physical object. Report the actual output, not "should work".

## Do not

- Commit `out/`, `.venv/`, or any `.stl` / `.step`.
- Add abstractions, CLI flags or config for a single use. Keep parts readable by a human with calipers.
- Change tolerances in `cadlib/export.py` for one part; pass overrides explicitly if truly needed.
