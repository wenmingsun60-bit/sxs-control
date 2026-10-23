"""Small JSON-RPC stdio transport and opt-in, loopback-only HTTP transport."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__, desktop, files, system
from .catalog import ACTIONS, INDEX, TOOLS, validate

PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")
FILE_ACTIONS = {"list_directory", "read_file", "write_file", "file_info", "file_copy", "file_move", "file_delete", "file_search"}
DESKTOP_ACTIONS = {"screenshot", "display_inventory", "click", "mouse_move", "scroll", "shortcut", "type_text", "ui_snapshot", "browser_ui", "ui_click", "browser_click", "ui_type", "browser_type", "mouse_drag", "multi_select", "multi_edit", "window", "wait_for"}


def parse_json(text):
    def invalid(_):
        raise ValueError("non-finite JSON number")
    return json.loads(text, parse_constant=invalid)


def text_result(value, error=False):
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, allow_nan=False)}], "isError": error}


class Server:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.RLock()

    def call(self, name, arguments=None):
        if name not in INDEX:
            return text_result({"error": "unknown tool"}, True)
        try:
            if not isinstance(arguments, dict):
                raise ValueError("arguments must be a JSON object")
            arguments = dict(arguments)
            # Retained solely for clients migrating from the earlier cloud contract.
            arguments.pop("device_id", None)
            validate(arguments, INDEX[name]["inputSchema"])
            action = ACTIONS[name]
            module = files if action in FILE_ACTIONS else desktop if action in DESKTOP_ACTIONS else system
            with self.lock:
                result = module.run(action, self.cfg, arguments)
            if action == "screenshot":
                return {"content": [{"type": "image", "mimeType": result.pop("mime_type"), "data": result.pop("image_base64")},
                                    {"type": "text", "text": json.dumps(result)}], "isError": False}
            return text_result(result)
        except Exception as error:
            return text_result({"error": f"{type(error).__name__}: {error}"}, True)

    @staticmethod
    def error(id_, code, message):
        return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}

    def dispatch(self, message):
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return self.error(None, -32600, "Invalid Request")
        id_ = message.get("id")
        if id_ is not None and (isinstance(id_, bool) or not isinstance(id_, (int, str))):
            return self.error(None, -32600, "Invalid request id")
        # A JSON-RPC notification, including an unknown notification, has no response.
        if "id" not in message:
            return None
        method = message["method"]
        params = message.get("params", {})
        if not isinstance(params, dict):
            return self.error(id_, -32602, "Invalid params")
        if method == "initialize":
            requested = params.get("protocolVersion")
            result = {"protocolVersion": requested if requested in PROTOCOLS else PROTOCOLS[-1],
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "sxs-control", "version": __version__},
                      "instructions": "Tools execute on this Windows computer. No SXS cloud broker, account login, polling or fallback is used."}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            if not isinstance(params.get("name"), str) or not isinstance(params.get("arguments", {}), dict):
                return self.error(id_, -32602, "Invalid tool parameters")
            result = self.call(params["name"], params.get("arguments", {}))
        else:
            return self.error(id_, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": id_, "result": result}


def serve_stdio(server, input_stream, output_stream):
    for line in input_stream:
        if not line.strip():
            continue
        try:
            result = server.dispatch(parse_json(line))
        except (ValueError, RecursionError):
            result = server.error(None, -32700, "Parse error")
        except Exception:
            result = server.error(None, -32603, "Internal error")
        if result is not None:
            output_stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
            output_stream.flush()


def make_http_server(server, port=18790):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SXS-Control/" + __version__

        def setup(self):
            super().setup()
            self.connection.settimeout(30)

        def log_message(self, *args):
            pass

        def send_json(self, status, payload):
            raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def permitted(self):
            actual_port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
            if self.headers.get("Host", "").lower() not in hosts:
                self.send_json(403, {"error": "invalid local Host"})
                return False
            if "Origin" in self.headers or "Sec-Fetch-Site" in self.headers:
                self.send_json(403, {"error": "browser-origin requests are not allowed"})
                return False
            if self.headers.get("X-SXS-Local") != "1":
                self.send_json(403, {"error": "X-SXS-Local: 1 header is required"})
                return False
            return True

        def do_GET(self):
            if not self.permitted():
                return
            if self.path == "/health":
                self.send_json(200, {"ok": True, "version": __version__, "mode": "local-only", "cloud_fallback": False, "tool_count": len(TOOLS)})
            elif self.path == "/tools":
                self.send_json(200, {"tools": TOOLS})
            elif self.path == "/mcp":
                self.send_json(405, {"error": "SSE streaming is not provided; use JSON POST"})
            else:
                self.send_json(404, {"error": "not found"})

        def do_OPTIONS(self):
            self.send_json(403, {"error": "browser CORS access is not provided"})

        def do_POST(self):
            if not self.permitted():
                return
            if self.headers.get_content_type() != "application/json":
                self.send_json(415, {"error": "application/json is required"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 2_000_000 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("invalid body size")
                payload = parse_json(self.rfile.read(size).decode("utf-8"))
            except (ValueError, OSError):
                self.send_json(400, {"error": "invalid JSON request"})
                return
            if self.path == "/mcp":
                result = server.dispatch(payload)
                if result is None:
                    self.send_response(202)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                else:
                    self.send_json(200, result)
            elif self.path == "/call":
                if not isinstance(payload, dict) or not isinstance(payload.get("tool"), str):
                    self.send_json(400, {"error": "tool and arguments object are required"})
                else:
                    self.send_json(200, server.call(payload["tool"], payload.get("arguments", {})))
            else:
                self.send_json(404, {"error": "not found"})

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    return httpd

