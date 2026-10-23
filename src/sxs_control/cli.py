"""Console entry points; only JSON-RPC messages are written in stdio mode."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path

from . import __version__
from .catalog import TOOLS
from .config import config_path, load_config
from .server import Server, make_http_server, parse_json, serve_stdio


def main(argv=None):
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="sxs-control")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--stdio", action="store_true", help="start the local MCP stdio server")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("stdio", help="start the local MCP stdio server")
    commands.add_parser("list", help="list all tools as JSON")
    commands.add_parser("doctor", help="check platform, configuration and installed dependencies")
    commands.add_parser("init", help="create a conservative per-user configuration")
    call = commands.add_parser("call", help="call one local tool")
    call.add_argument("tool")
    source = call.add_mutually_exclusive_group()
    source.add_argument("--arguments", default="{}", help="JSON arguments (use --args-stdin in Windows PowerShell)")
    source.add_argument("--args-stdin", action="store_true")
    source.add_argument("--arguments-file", type=Path)
    http = commands.add_parser("http", help="start an opt-in loopback HTTP server")
    http.add_argument("--port", type=int, default=18790)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            path = args.config or config_path()
            if path.exists():
                raise FileExistsError("configuration already exists; edit it explicitly")
            workspace = Path.home() / "SXSWorkspace"
            workspace.mkdir(parents=True, exist_ok=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"allowed_roots": [str(workspace.resolve())]}, indent=2), encoding="utf-8")
            print(json.dumps({"config": str(path), "workspace": str(workspace)}, ensure_ascii=False))
            return 0
        if args.command == "list":
            print(json.dumps({"version": __version__, "count": len(TOOLS), "tools": TOOLS}, ensure_ascii=False, indent=2))
            return 0
        cfg = load_config(args.config)
        if args.command == "doctor":
            dependencies = {}
            for name in ("Pillow", "psutil", "pywin32", "uiautomation"):
                try:
                    dependencies[name] = importlib.metadata.version(name)
                except importlib.metadata.PackageNotFoundError:
                    dependencies[name] = None
            ok = os.name == "nt" and all(dependencies.values())
            print(json.dumps({"ok": ok, "version": __version__, "platform": sys.platform,
                              "mode": "local-only", "cloud_fallback": False, "tool_count": len(TOOLS),
                              "config": str(args.config or config_path()), "allowed_roots": cfg["allowed_roots"],
                              "dependencies": dependencies}, ensure_ascii=False, indent=2))
            return 0 if ok else 1
        server = Server(cfg)
        if args.stdio or args.command == "stdio":
            serve_stdio(server, sys.stdin, sys.stdout)
            return 0
        if args.command == "call":
            raw = sys.stdin.read() if args.args_stdin else args.arguments_file.read_text(encoding="utf-8-sig") if args.arguments_file else args.arguments
            result = server.call(args.tool, parse_json(raw.lstrip("\ufeff")))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result["isError"] else 0
        if args.command == "http":
            if not 1 <= args.port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            httpd = make_http_server(server, args.port)
            print(f"SXS Control listening on http://127.0.0.1:{args.port}; X-SXS-Local: 1 required", file=sys.stderr)
            try:
                httpd.serve_forever(poll_interval=0.2)
            finally:
                httpd.server_close()
            return 0
        parser.print_help()
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError) as error:
        print(json.dumps({"error": f"{type(error).__name__}: {error}"}, ensure_ascii=False), file=sys.stderr)
        return 2

