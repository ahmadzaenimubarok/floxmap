"""floxmap registry — project add/list/remove."""

import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml

FLOXMAP_HOME = Path.home() / ".floxmap"
PROJECTS_DIR = FLOXMAP_HOME / "projects"


def _project_dir(name: str) -> Path:
    return PROJECTS_DIR / name


def _meta_path(name: str) -> Path:
    return _project_dir(name) / "meta.yaml"


def _load_meta(name: str) -> dict | None:
    p = _meta_path(name)
    if not p.exists():
        return None
    with open(p) as f:
        return yaml.safe_load(f)


def _save_meta(name: str, data: dict) -> None:
    d = _project_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "flows").mkdir(exist_ok=True)
    with open(_meta_path(name), "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def project_add(name: str, root: str, in_project: bool = False) -> None:
    root_path = Path(root).resolve()
    if not root_path.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if _load_meta(name) is not None:
        print(f"Error: project '{name}' already exists.", file=sys.stderr)
        sys.exit(1)

    meta = {
        "name": name,
        "root": str(root_path),
        "mode": "in-project" if in_project else "centralized",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_meta(name, meta)
    print(f"Project '{name}' added (mode: {meta['mode']}).")


def project_list() -> None:
    if not PROJECTS_DIR.exists():
        print("No projects registered.")
        return

    projects = sorted(p for p in PROJECTS_DIR.iterdir() if p.is_dir())
    if not projects:
        print("No projects registered.")
        return

    print(f"{'NAME':<20} {'ROOT':<40} {'MODE':<15} {'FLOWS':<6}")
    print("-" * 81)
    for proj in projects:
        meta = _load_meta(proj.name)
        if not meta:
            continue
        flows_dir = proj / "flows"
        flow_count = len(list(flows_dir.glob("*.flow.yaml"))) if flows_dir.exists() else 0
        root = meta.get("root", "?")
        mode = meta.get("mode", "?")
        print(f"{proj.name:<20} {root:<40} {mode:<15} {flow_count:<6}")


def project_remove(name: str) -> None:
    meta = _load_meta(name)
    if meta is None:
        print(f"Error: project '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    confirm = input(f"Remove project '{name}'? This deletes docs from ~/.floxmap only (repo untouched) [y/N]: ")
    if confirm.strip().lower() != "y":
        print("Aborted.")
        return

    import shutil
    shutil.rmtree(_project_dir(name))
    print(f"Project '{name}' removed.")
