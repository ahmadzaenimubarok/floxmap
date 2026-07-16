"""floxmap export — copy docs to a repo for portability."""

import shutil
import sys
from pathlib import Path

from floxmap_pkg.registry import _load_meta, PROJECTS_DIR

FLOXMAP_HOME = Path.home() / ".floxmap"
SCHEMA_PATH = FLOXMAP_HOME / "flow-schema.yaml"


def export_project(name: str, target_path: str) -> None:
    meta = _load_meta(name)
    if meta is None:
        print(f"Error: project '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    target = Path(target_path).resolve()
    if not target.exists():
        print(f"Error: target path '{target}' does not exist.", file=sys.stderr)
        sys.exit(1)

    source_dir = PROJECTS_DIR / name

    # Copy flow-schema.yaml
    if SCHEMA_PATH.exists():
        shutil.copy2(SCHEMA_PATH, target / "flow-schema.yaml")
        print(f"  Copied flow-schema.yaml")

    # Copy flows/
    flows_src = source_dir / "flows"
    if flows_src.exists():
        flows_dst = target / "flows"
        if flows_dst.exists():
            shutil.rmtree(flows_dst)
        shutil.copytree(flows_src, flows_dst)
        count = len(list(flows_dst.glob("*.flow.yaml")))
        print(f"  Copied flows/ ({count} file(s))")

    # Copy flow-map.json if exists
    map_src = source_dir / "flow-map.json"
    if map_src.exists():
        shutil.copy2(map_src, target / "flow-map.json")
        print(f"  Copied flow-map.json")

    # Copy flow-viewer.html if exists
    viewer_src = source_dir / "flow-viewer.html"
    if viewer_src.exists():
        shutil.copy2(viewer_src, target / "flow-viewer.html")
        print(f"  Copied flow-viewer.html")

    print(f"\nExported to {target}/")
