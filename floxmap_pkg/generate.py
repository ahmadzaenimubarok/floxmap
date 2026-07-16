"""floxmap generate — validate flows and render flow-map.json + flow-viewer.html."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from floxmap_pkg.registry import _load_meta, PROJECTS_DIR

FLOXMAP_HOME = Path.home() / ".floxmap"
SCHEMA_PATH = FLOXMAP_HOME / "flow-schema.yaml"

VIEWER_TEMPLATE = Path(__file__).parent / "flow-viewer.html"


def _load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)


def _get_flows_dir(meta: dict, name: str) -> Path:
    if meta.get("mode") == "in-project":
        return Path(meta["root"]) / "flows"
    return PROJECTS_DIR / name / "flows"


def _validate_flow(flow: dict, schema: dict) -> list[str]:
    errors = []
    fields = schema.get("fields", {})
    for field_name, spec in fields.items():
        if spec.get("required") and field_name not in flow:
            errors.append(f"missing required field '{field_name}'")
        if field_name in flow:
            expected = spec.get("type")
            val = flow[field_name]
            if expected == "list" and not isinstance(val, list):
                errors.append(f"'{field_name}' must be a list")
            elif expected == "string" and not isinstance(val, str):
                errors.append(f"'{field_name}' must be a string")
            elif expected == "enum" and val not in spec.get("values", []):
                errors.append(f"'{field_name}' must be one of {spec['values']}")
    return errors


def _build_graph(flows: list[dict]) -> dict:
    nodes = []
    node_ids = set()
    edges = []

    for flow in flows:
        fid = flow["id"]
        nodes.append({
            "id": fid,
            "name": flow.get("name", fid),
            "source": flow.get("source", "code"),
        })
        node_ids.add(fid)

        for dep in flow.get("dependency", []):
            edges.append({"from": fid, "to": dep})
            if dep not in node_ids:
                nodes.append({
                    "id": dep,
                    "name": dep.replace("-", " ").title(),
                    "source": "derived",
                })
                node_ids.add(dep)

    return {"nodes": nodes, "edges": edges}


def generate_project(name: str) -> None:
    meta = _load_meta(name)
    if meta is None:
        print(f"Error: project '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    flows_dir = _get_flows_dir(meta, name)
    if not flows_dir.exists():
        print(f"Error: flows directory '{flows_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Output always goes to centralized location
    out_dir = PROJECTS_DIR / name

    schema = _load_schema()
    flow_files = sorted(flows_dir.glob("*.flow.yaml"))

    if not flow_files:
        print("No flow files found.")
        return

    print(f"Validating {len(flow_files)} flow file(s)...")

    flows = []
    for ff in flow_files:
        with open(ff) as f:
            flow = yaml.safe_load(f)
        errors = _validate_flow(flow, schema)
        if errors:
            print(f"  FAIL {ff.name}: {', '.join(errors)}", file=sys.stderr)
            sys.exit(1)
        flows.append(flow)
        print(f"  OK   {ff.name}")

    # Build graph
    graph = _build_graph(flows)
    flow_map = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": name,
        "nodes": graph["nodes"],
        "edges": graph["edges"],
    }

    # Write flow-map.json
    out_dir.mkdir(parents=True, exist_ok=True)
    map_path = out_dir / "flow-map.json"
    with open(map_path, "w") as f:
        json.dump(flow_map, f, indent=2)
    print(f"\nWritten: {map_path}")

    # Write flow-viewer.html
    viewer_path = out_dir / "flow-viewer.html"
    if VIEWER_TEMPLATE.exists():
        import shutil
        shutil.copy2(VIEWER_TEMPLATE, viewer_path)
        print(f"Written: {viewer_path}")
    else:
        print("Warning: flow-viewer.html template not found, skipping")
