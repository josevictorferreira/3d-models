"""The `cad` command: list, build and show the parts under projects/."""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from build123d import Part

from cadlib.export import export_part
from cadlib.preview import write_preview

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
OUT = ROOT / "out"


def find_parts(path: Path = PROJECTS) -> list[Path]:
    """Every part module under `path`: a .py file whose name does not start with `_`."""
    if path.is_file():
        return [path.resolve()]
    return sorted(p.resolve() for p in path.rglob("*.py") if not p.name.startswith("_"))


def resolve(target: str) -> Path:
    """A path under projects/, or the bare name of a part (its file stem)."""
    path = Path(target)
    if path.exists():
        return path
    matches = [p for p in find_parts() if p.stem == target]
    if len(matches) != 1:
        sys.exit(f"{target}: {'no part' if not matches else 'several parts'} with that name")
    return matches[0]


def out_path(source: Path) -> Path:
    return OUT / source.relative_to(PROJECTS).with_suffix(".stl")


def load_part(source: Path) -> Part:
    """Import `source` and return the result of its build().

    While importing, the part's directory and its parents inside projects/ are on sys.path,
    so a part can `from _common import ...` a helper from any level of its own project.
    Modules imported from projects/ are dropped afterwards so `_common` names never
    leak between projects when building several parts in one process.
    """
    saved_path, saved_modules = sys.path[:], set(sys.modules)
    sys.path[:0] = [str(d) for d in source.parents if PROJECTS in d.parents]
    try:
        spec = importlib.util.spec_from_file_location(source.stem, source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        part = module.build()
    finally:
        sys.path[:] = saved_path
        for name in set(sys.modules) - saved_modules:
            file = getattr(sys.modules[name], "__file__", None)
            if file and Path(file).is_relative_to(PROJECTS):
                del sys.modules[name]
    if not isinstance(part, Part):
        raise TypeError(f"{source}: build() returned {type(part).__name__}, expected Part")
    return part


def cmd_list(_: argparse.Namespace) -> None:
    for source in find_parts():
        print(source.relative_to(ROOT))


def cmd_build(args: argparse.Namespace) -> None:
    sources = find_parts() if args.target == "all" else find_parts(resolve(args.target))
    if not sources:
        sys.exit(f"no parts found in {args.target}")
    for source in sources:
        part = load_part(source)
        target = out_path(source)
        export_part(part, target, step=args.step)
        size = part.bounding_box().size
        print(
            f"{target.relative_to(ROOT)}  "
            f"{size.X:.1f} x {size.Y:.1f} x {size.Z:.1f} mm  "
            f"volume {part.volume / 1000:.1f} cm3"
        )


def cmd_show(args: argparse.Namespace) -> None:
    from ocp_vscode import show

    (source,) = find_parts(resolve(args.target))
    show(load_part(source), names=[source.stem])


def cmd_preview(args: argparse.Namespace) -> None:
    (source,) = find_parts(resolve(args.target))
    page = write_preview(load_part(source), out_path(source))
    print(page.relative_to(ROOT))
    subprocess.run(["xdg-open", str(page)], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(prog="cad", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list every part module").set_defaults(func=cmd_list)

    build = sub.add_parser("build", help="export parts to out/ as STL")
    build.add_argument(
        "target", nargs="?", default="all", help="part name, file, directory, or 'all'"
    )
    build.add_argument("--step", action="store_true", help="also write a STEP file")
    build.set_defaults(func=cmd_build)

    show = sub.add_parser("show", help="send one part to the running ocp-vscode viewer")
    show.add_argument("target", help="part name or file")
    show.set_defaults(func=cmd_show)

    preview = sub.add_parser("preview", help="build one part and open it in the browser")
    preview.add_argument("target", help="part name or file")
    preview.set_defaults(func=cmd_preview)

    args = parser.parse_args()
    args.func(args)
