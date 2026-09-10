# Project Setup Plan

Goal: a reproducible repo where Python + [build123d](https://build123d.readthedocs.io) source files
under `projects/` are turned into printable STL files with a single command, inside a `nix develop` shell.

Written 2026-09-10 and executed the same day. All five phases are done; the fresh-clone check in
Phase 5 passes. Corrections discovered while executing are recorded in section 5.

## 0. Findings that shape the plan

| Fact | Consequence |
|---|---|
| `build123d`, `cadquery-ocp`, `ocp-vscode` are **not in nixpkgs** (checked registry pin and `nixos-unstable`) | Python deps must come from PyPI wheels. Nix supplies the interpreter, tools and native libs. |
| build123d 0.11.1 requires Python `>=3.10,<3.15` and `cadquery-ocp-novtk>=7.9,<8.0` | Pin Python 3.13 (nixpkgs `python313`, 3.13.14). The `novtk` OCP wheel means no VTK and far fewer native libs. |
| OCP wheels are `manylinux_2_28`; host is **NixOS** (nix-ld enabled) | The dev shell must set `LD_LIBRARY_PATH` for libstdc++, zlib, libGL, X11 and expat so wheels load with the nix Python. |
| `uv` 0.12.11 and `ruff` 0.15.22 are in nixpkgs | uv manages the venv and lockfile; nix just provides it. |
| STL export in build123d is `export_stl(part, path, tolerance, angular_tolerance)`, headless, no display required | Builds can run in CI or over SSH. |

## 1. Decisions

1. **Package management: `uv` inside the nix shell** (`pyproject.toml` + `uv.lock`, committed).
   Alternatives considered: `uv2nix` (pure nix, but heavy and slow to iterate on) and community
   `cq-flake` (stale, CadQuery-centric). uv can be swapped for uv2nix later without changing the Python code.
2. **Python 3.13** via nixpkgs, `UV_PYTHON_DOWNLOADS=never` so uv never fetches its own interpreter.
3. **Generated STLs are not committed.** `out/` is gitignored and regenerated with one command.
   Tradeoff: no direct download from GitHub. If that is wanted later, attach STLs to a git tag/release instead of tracking them.
4. **One part per Python file.** Any `*.py` under `projects/` whose name does not start with `_` is a part
   and must expose `build() -> Part`. Files starting with `_` (e.g. `_common.py`) are shared helpers
   and are skipped by the builder. This supports arbitrary nesting of project folders.
5. **Output mirrors input.** `projects/homelab-rack/rackmounts/switch_tray.py` -> `out/homelab-rack/rackmounts/switch_tray.stl`.
6. **Units are millimetres**, build123d's default. Every dimension is a named constant at the top of the part file.
7. **Viewer: `ocp-vscode`** (works as a VS Code extension and as a standalone browser viewer via `python -m ocp_vscode`).
   Only used interactively; never imported by part files so headless builds stay dependency-light.

## 2. Target layout

```
3d-models/
├── flake.nix, flake.lock        # nix develop: python313, uv, ruff, native libs, shell hook
├── .envrc                       # `use flake` (direnv, optional)
├── pyproject.toml, uv.lock      # build123d, ocp-vscode, pytest, ruff config
├── .gitignore                   # .venv/ out/ .direnv/ __pycache__/ *.stl
├── README.md, AGENTS.md, project_setup_plan.md
│
├── cadlib/                      # shared Python package, installed editable by uv
│   ├── __init__.py
│   ├── export.py                # export_part(part, path): STL (+ optional STEP), print-oriented tolerances
│   ├── hardware.py              # reusable dimensions: M3/M4 clearance, heat-set inserts, 19" rack unit maths
│   └── cli.py                   # `cad build [PATH|all]`, `cad show PATH`, `cad list`
│
├── projects/                    # one folder per physical project, nest as deep as you like
│   ├── examples/
│   │   └── calibration_cube.py  # toolchain smoke test, 20 mm cube
│   └── homelab-rack/
│       ├── README.md            # what the project is, print settings, BOM
│       ├── _common.py           # project-wide constants (rack width, ear thickness, ...)
│       └── rackmounts/
│           └── <part>.py        # each exposes build() -> Part
│
├── out/                         # generated, gitignored, mirrors projects/
└── tests/
    └── test_parts.py            # every part builds, is a valid solid, has volume > 0
```

## 3. Phases

Each phase ends with a verification command. Do not start the next phase until it passes.

### Phase 1: Nix dev shell

Create `flake.nix` with a single `devShells.default`:

- inputs: `nixpkgs` (nixos-unstable), `flake-utils` or plain `forAllSystems`.
- packages: `python313`, `uv`, `ruff`, `nixfmt-rfc-style`.
- env: `UV_PYTHON=<python313>/bin/python3`, `UV_PYTHON_DOWNLOADS=never`, `UV_PROJECT_ENVIRONMENT=.venv`.
- `LD_LIBRARY_PATH` = `lib.makeLibraryPath [ stdenv.cc.cc.lib zlib libGL xorg.libX11 xorg.libXrender xorg.libXext fontconfig freetype expat glib ]`.
  Start with this list; add libs only when an import error names one.
- shellHook: `uv sync --frozen` if `uv.lock` exists, then `source .venv/bin/activate`.

Also add `.envrc` (`use flake`) and `.gitignore`.

Verify:
```
nix flake check
nix develop -c python --version        # Python 3.13.x
```

### Phase 2: Python project and lockfile

- `pyproject.toml`: project `three-d-models`, `requires-python = ">=3.13,<3.14"`,
  deps `build123d`, dev group `ocp-vscode`, `pytest`; `[tool.ruff]` line-length 100;
  `[project.scripts] cad = "cadlib.cli:main"`; build backend `hatchling` with `cadlib` as the package.
- `cadlib/__init__.py`, `cadlib/export.py` with `export_part(part, path, *, step=False)` calling
  `export_stl(part, path, tolerance=0.01, angular_tolerance=0.1)` (fine enough for FDM, keeps files small).
- `uv lock`, commit `uv.lock`.

Verify:
```
nix develop -c python -c "import build123d, OCP; print(build123d.__version__)"
```
If this fails with a `.so` loading error, the missing lib goes into the `LD_LIBRARY_PATH` list in Phase 1.

### Phase 3: Builder CLI

`cadlib/cli.py`:

- `cad list`: walk `projects/`, print every part module (non-underscore `.py`).
- `cad build [PATH|all]`: import each module by file path, call `build()`, write to the mirrored path under `out/`.
  Fail loudly on any exception and exit non-zero; print the output path and part volume on success.
- `cad show PATH`: build one part and send it to the running ocp-vscode viewer.

Verify:
```
nix develop -c cad build projects/examples/calibration_cube.py
ls -la out/examples/calibration_cube.stl     # non-empty
```

### Phase 4: Example part and tests

- `projects/examples/calibration_cube.py`: `SIZE = 20`, `build()` returns `Box(SIZE, SIZE, SIZE)`.
- `tests/test_parts.py`: parametrised over `cad list`; for each part assert `build()` returns a `Part`,
  `part.is_valid()`, `part.volume > 0`.

Verify:
```
nix develop -c pytest -q
nix develop -c ruff check .
```

### Phase 5: Project scaffolding and docs

- `projects/homelab-rack/README.md` and `_common.py` (constants only, no parts yet).
- Update `README.md` and `AGENTS.md` to match what was actually built; remove the "in progress" notes.
- Optional: GitHub Actions job running `nix develop -c cad build all && pytest` on push.

Verify: a fresh clone + `nix develop -c cad build all && pytest -q` passes with no manual steps.

## 4. Out of scope for now

- The actual rackmount parts.
- Committing or publishing STLs, slicer profiles, multi-material/colour.
- uv2nix or any fully-pure Nix packaging of OCP.

## 5. What changed during execution

- **Native libs.** The verified minimal `LD_LIBRARY_PATH` set is `stdenv.cc.cc.lib zlib libGL libx11
  libxrender libxext expat`. Dropping any one fails the import naming the missing `.so`.
  fontconfig, freetype and glib were removed: the wheel bundles fontconfig and freetype, and the
  nix copies shadowed them. nixpkgs also renamed `xorg.libX11` and friends to `libx11` etc.
- **Fontconfig warnings.** The bundled fontconfig (soname 1.12) reads the host `/etc/fonts/conf.d`,
  which uses newer syntax, and prints ~44 `Fontconfig warning:` lines per process. It ignores
  `FONTCONFIG_FILE`/`FONTCONFIG_PATH`. Text rendering and export still work. Left as is.
- **build123d 0.11 API.** `Part.is_valid` is a property, not a method. Tests use `part.is_valid`.
- **`cad build` default.** `cad build` with no target builds everything; a file or directory
  narrows it. `--step` also writes a STEP file.
- **Nested helpers.** Verified: a part three directories deep can `from _common import X` a helper
  at its project root, and modules from `projects/` are unloaded after each part so names do not
  leak between projects in one process.
- **homelab-rack.** Only `README.md` was added. `_common.py` is deferred until the first part
  needs a project-wide constant, to avoid inventing dimensions.
