"""floxmap screen — AI step: scan repo, extract flows via LLM."""

import re
import sys
from pathlib import Path
from collections import Counter

import yaml

from floxmap_pkg.registry import _load_meta, PROJECTS_DIR
from floxmap_pkg.llm import get_provider

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".floxmap", "vendor", "target",
}
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".rb", ".php", ".cs", ".vue", ".svelte",
}

SYSTEM_PROMPT = """\
You are a business flow extractor. Given a source file, identify all business flows \
(endpoints, event handlers, entry points, commands) and return them as a YAML list.

Each flow must have these fields:
- id: unique slug, kebab-case (e.g. "login", "create-order")
- name: human-readable name
- description: 1-2 sentence summary
- trigger: what triggers this flow (HTTP method+path, event name, CLI command, etc.)
- steps: ordered list of steps (strings)
- dependency: (optional) list of other service/node ids this flow connects to
- source: one of "code", "md", or "brief"

Return ONLY the YAML list, no markdown fences, no explanation. Example:

- id: login
  name: User Login
  description: Authenticate user via email/password
  trigger: POST /api/login
  steps:
    - validate input
    - check credentials
    - create session
    - return token
  dependency:
    - auth-service
  source: code
"""

USER_PROMPT_TEMPLATE = """\
File: {path}
Source type: code

---
{content}
---

Extract all business flows from this file. Return YAML list only."""


def _scan_source_files(root: Path) -> list[Path]:
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(skip in p.parts for skip in SKIP_DIRS):
            continue
        if p.suffix in SOURCE_EXTS:
            files.append(p)
    return files


def _parse_flows_from_text(text: str) -> list[dict]:
    text = text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:yaml)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        result = yaml.safe_load(text)
    except yaml.YAMLError as e:
        print(f"  YAML parse error: {e}", file=sys.stderr)
        return []

    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return [result]
    return []


def _dedupe_ids(flows: list[dict]) -> list[dict]:
    seen: Counter = Counter()
    for flow in flows:
        fid = flow.get("id", "unnamed")
        if seen[fid] > 0:
            flow["id"] = f"{fid}-{seen[fid] + 1}"
        seen[fid] += 1
    return flows


def _validate_flow(flow: dict) -> list[str]:
    errors = []
    required = ["id", "name", "description", "trigger", "steps", "source"]
    for field in required:
        if field not in flow:
            errors.append(f"missing field '{field}'")
    if "steps" in flow and not isinstance(flow["steps"], list):
        errors.append("'steps' must be a list")
    if "source" in flow and flow["source"] not in ("code", "md", "brief"):
        errors.append(f"invalid source '{flow['source']}', must be code/md/brief")
    return errors


def _load_hints(meta: dict) -> str | None:
    hints_path = meta.get("hints_path")
    if not hints_path:
        return None
    p = Path(hints_path)
    if not p.exists():
        print(f"  Warning: hints_path '{hints_path}' not found, skipping", file=sys.stderr)
        return None
    return p.read_text()


def screen_project(name: str, dry_run: bool = False) -> None:
    meta = _load_meta(name)
    if meta is None:
        print(f"Error: project '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    root = Path(meta["root"])
    if not root.exists():
        print(f"Error: repo path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    provider = get_provider()

    # Determine output location
    if meta.get("mode") == "in-project":
        flows_dir = root / "flows"
    else:
        flows_dir = PROJECTS_DIR / name / "flows"
    flows_dir.mkdir(parents=True, exist_ok=True)

    # Load optional hints
    hints = _load_hints(meta)
    hints_section = ""
    if hints:
        hints_section = f"\n\nScope hints:\n{hints}"

    # Scan source files
    files = _scan_source_files(root)
    if not files:
        print("No source files found.")
        return

    print(f"Found {len(files)} source file(s). Screening...")

    all_flows: list[dict] = []

    for i, filepath in enumerate(files, 1):
        rel = filepath.relative_to(root)
        content = filepath.read_text(errors="replace")

        # Truncate very large files
        if len(content) > 15000:
            content = content[:15000] + "\n... (truncated)"

        user_prompt = USER_PROMPT_TEMPLATE.format(
            path=str(rel),
            content=content,
        ) + hints_section

        print(f"  [{i}/{len(files)}] {rel}...", end=" ", flush=True)

        try:
            response = provider.chat(SYSTEM_PROMPT, user_prompt)
            flows = _parse_flows_from_text(response)
            for f in flows:
                if "source" not in f:
                    f["source"] = "code"
            all_flows.extend(flows)
            print(f"({len(flows)} flow(s))")
        except Exception as e:
            print(f"ERROR: {e}")
            continue

    if not all_flows:
        print("No flows extracted.")
        return

    # Dedupe IDs
    all_flows = _dedupe_ids(all_flows)

    # Validate
    valid_flows = []
    for flow in all_flows:
        errors = _validate_flow(flow)
        if errors:
            print(f"  Skipping invalid flow '{flow.get('id', '?')}': {', '.join(errors)}")
            continue
        valid_flows.append(flow)

    if not valid_flows:
        print("No valid flows after validation.")
        return

    print(f"\n{len(valid_flows)} valid flow(s) total.")

    if dry_run:
        print("\n--- DRY RUN (not writing) ---\n")
        for flow in valid_flows:
            print(yaml.dump(flow, default_flow_style=False, sort_keys=False))
        return

    # Write flows (overwrite)
    # Remove old flows first
    for old in flows_dir.glob("*.flow.yaml"):
        old.unlink()

    for flow in valid_flows:
        out = flows_dir / f"{flow['id']}.flow.yaml"
        with open(out, "w") as f:
            yaml.dump(flow, f, default_flow_style=False, sort_keys=False)

    print(f"Written to {flows_dir}/")
