"""floxmap serve — local HTTP server for the flow viewer."""

import sys
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from floxmap_pkg.registry import _load_meta, PROJECTS_DIR


def serve_project(name: str, port: int = 8731, open_browser: bool = False) -> None:
    meta = _load_meta(name)
    if meta is None:
        print(f"Error: project '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    serve_dir = PROJECTS_DIR / name
    if not serve_dir.exists():
        print(f"Error: project directory '{serve_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    handler = partial(SimpleHTTPRequestHandler, directory=str(serve_dir))

    server = HTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/flow-viewer.html"

    print(f"Serving '{name}' at {url}")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
