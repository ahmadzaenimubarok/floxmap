#!/usr/bin/env python3
"""floxmap — Business Flow Documentation CLI."""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="floxmap",
        description="Business Flow Documentation CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # --- project ---
    proj = sub.add_parser("project", help="Manage projects")
    proj_sub = proj.add_subparsers(dest="action")

    proj_add = proj_sub.add_parser("add", help="Register a project")
    proj_add.add_argument("name", help="Project name")
    proj_add.add_argument("--path", required=True, help="Path to repo root")
    proj_add.add_argument("--in-project", action="store_true",
                          help="Store flows inside the repo")

    proj_sub.add_parser("list", help="List registered projects")

    proj_rm = proj_sub.add_parser("remove", help="Remove a project")
    proj_rm.add_argument("name", help="Project name")

    # --- config ---
    cfg = sub.add_parser("config", help="Manage LLM config")
    cfg_sub = cfg.add_subparsers(dest="action")
    cfg_sub.add_parser("set", help="Set config interactively")
    cfg_sub.add_parser("get", help="Show current config")

    # --- screen ---
    scr = sub.add_parser("screen", help="Scan repo and generate flow YAMLs (requires LLM)")
    scr.add_argument("name", help="Project name")
    scr.add_argument("--dry-run", action="store_true", help="Print proposed YAML without writing")

    # --- generate ---
    gen = sub.add_parser("generate", help="Render flows to JSON + HTML")
    gen.add_argument("name", help="Project name")

    # --- serve ---
    srv = sub.add_parser("serve", help="Serve viewer in browser")
    srv.add_argument("name", help="Project name")
    srv.add_argument("--port", type=int, default=8731, help="Port (default: 8731)")
    srv.add_argument("--open", action="store_true", help="Open browser (Linux only)")

    # --- export ---
    exp = sub.add_parser("export", help="Export docs to repo")
    exp.add_argument("name", help="Project name")
    exp.add_argument("--path", required=True, help="Target repo path")

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
