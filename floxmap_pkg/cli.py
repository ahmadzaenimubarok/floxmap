#!/usr/bin/env python3
"""floxmap — Business Flow Documentation CLI."""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="floxmap",
        description="Generate and manage business flow documentation from source code.",
        epilog="""\
workflow:
  1. floxmap config set              # configure LLM provider
  2. floxmap project add <name> --path /path/to/repo
  3. floxmap screen <name>           # scan repo, extract flows via LLM
  4. floxmap generate <name>         # render flow-map.json + viewer
  5. floxmap serve <name> --open     # open viewer in browser

docs stored in: ~/.floxmap/projects/<name>/""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # --- project ---
    proj = sub.add_parser(
        "project",
        help="Register, list, or remove projects",
        description="Manage project registrations. Each project maps a name to a repo path.",
        epilog="""\
examples:
  floxmap project add myapp --path ~/repos/myapp
  floxmap project add myapp --path ~/repos/myapp --in-project
  floxmap project list
  floxmap project remove myapp""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    proj_sub = proj.add_subparsers(dest="action")

    proj_add = proj_sub.add_parser(
        "add",
        help="Register a new project",
        description="Register a repo path under a project name. Flows will be stored in ~/.floxmap/projects/<name>/.",
        epilog="example: floxmap project add myapp --path ~/repos/myapp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    proj_add.add_argument("name", help="Unique project name (used in all other commands)")
    proj_add.add_argument("--path", required=True, help="Absolute path to the repo root directory")
    proj_add.add_argument("--in-project", action="store_true",
                          help="Store flows inside the repo instead of ~/.floxmap/")

    proj_ls = proj_sub.add_parser(
        "list",
        help="List all registered projects",
        description="Show all registered projects with their root path, mode, and flow count.",
    )

    proj_rm = proj_sub.add_parser(
        "remove",
        help="Remove a project registration",
        description="Delete a project from the registry. Only removes docs from ~/.floxmap/, the original repo is never touched.",
        epilog="example: floxmap project remove myapp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    proj_rm.add_argument("name", help="Name of the project to remove")

    # --- config ---
    cfg = sub.add_parser(
        "config",
        help="View or set LLM configuration",
        description="Manage the LLM provider settings used by the 'screen' command.",
        epilog="""\
examples:
  floxmap config set                    # interactive setup
  floxmap config get                    # show current config (key masked)""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cfg_sub = cfg.add_subparsers(dest="action")
    cfg_sub.add_parser("set", help="Set config interactively (prompts for each field)")
    cfg_sub.add_parser("get", help="Show current config (API key is masked)")

    # --- screen ---
    scr = sub.add_parser(
        "screen",
        help="Scan a repo and extract business flows via LLM",
        description="""\
Scan the registered repo for source files, send each to the LLM,
and write the extracted flows as YAML files. Requires a configured LLM provider.

By default, existing flows are overwritten. Use --dry-run to preview without writing.""",
        epilog="""\
examples:
  floxmap screen myapp                  # scan and write flows
  floxmap screen myapp --dry-run        # preview flows without writing""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scr.add_argument("name", help="Registered project name")
    scr.add_argument("--dry-run", action="store_true",
                     help="Print proposed flow YAMLs to stdout without writing files")

    # --- generate ---
    gen = sub.add_parser(
        "generate",
        help="Validate flows and render flow-map.json + viewer",
        description="""\
Read all flows/*.flow.yaml, validate against the schema,
build the edge graph, and write flow-map.json + flow-viewer.html.

Fails immediately if any flow file is invalid.""",
        epilog="example: floxmap generate myapp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gen.add_argument("name", help="Registered project name")

    # --- serve ---
    srv = sub.add_parser(
        "serve",
        help="Serve the flow viewer in a local browser",
        description="Start a local HTTP server and open the interactive flow viewer.",
        epilog="example: floxmap serve myapp --open",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    srv.add_argument("name", help="Registered project name")
    srv.add_argument("--port", type=int, default=8731,
                     help="Port number (default: 8731)")
    srv.add_argument("--open", action="store_true",
                     help="Automatically open the viewer in the default browser")

    # --- export ---
    exp = sub.add_parser(
        "export",
        help="Copy flow docs into a repo for portability",
        description="""\
Copy flow-schema.yaml, flows/, and optionally flow-map.json + viewer
into a target repo. The project stays in centralized mode (meta unchanged).
Use this when you want others to access the docs by cloning the repo.""",
        epilog="example: floxmap export myapp --path ~/repos/myapp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    exp.add_argument("name", help="Registered project name")
    exp.add_argument("--path", required=True, help="Target repo path to copy docs into")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "project":
        if args.action is None:
            proj.print_help()
            sys.exit(0)
        from floxmap_pkg.registry import project_add, project_list, project_remove
        if args.action == "add":
            project_add(args.name, args.path, args.in_project)
        elif args.action == "list":
            project_list()
        elif args.action == "remove":
            project_remove(args.name)

    elif args.command == "config":
        from floxmap_pkg.config import config_set_interactive, get_masked
        if args.action == "set":
            config_set_interactive()
        elif args.action == "get":
            cfg = get_masked()
            for k, v in cfg.items():
                print(f"  {k}: {v}")
        else:
            cfg.print_help()

    elif args.command == "screen":
        from floxmap_pkg.screen import screen_project
        screen_project(args.name, dry_run=args.dry_run)

    elif args.command == "generate":
        from floxmap_pkg.generate import generate_project
        generate_project(args.name)

    elif args.command == "serve":
        from floxmap_pkg.serve import serve_project
        serve_project(args.name, port=args.port, open_browser=args.open)

    elif args.command == "export":
        from floxmap_pkg.export import export_project
        export_project(args.name, args.path)


if __name__ == "__main__":
    main()
