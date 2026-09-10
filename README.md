# 3d-models

Parametric 3D-printable parts, written in Python with [build123d](https://build123d.readthedocs.io) and exported to STL.

## Setup

```
nix develop          # Python 3.13, uv, build123d; syncs .venv on entry
```

## Usage

```
nix run .#preview <part>      # e.g. network_switch: build it and open the preview in the browser
```

Inside `nix develop`, parts can be named by file stem or path:

```
cad list                      # every part under projects/
cad build                     # all parts -> out/, mirroring projects/
cad build projects/<path>     # one file or one directory; add --step for a STEP file too
cad preview <part>            # build one part and open it in the browser
cad show projects/<path>.py   # send a part to the viewer (start it first: python -m ocp_vscode)
pytest -q                     # every part builds and is a valid solid
```

## Layout

- `projects/<project>/...` one `.py` per part, each exposing `build() -> Part`; `_*.py` files are shared helpers.
- `cadlib/` shared package: STL/STEP export, hardware dimensions, the `cad` CLI.
- `out/` generated files, not committed.

Design decisions and setup history: [project_setup_plan.md](project_setup_plan.md).
