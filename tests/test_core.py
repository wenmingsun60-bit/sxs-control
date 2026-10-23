from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener

from sxs_control import desktop
from sxs_control.catalog import TOOLS
from sxs_control.config import checked_path, load_config
from sxs_control.server import Server, make_http_server, serve_stdio


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._link_unavailable = {}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.allowed = self.root / "allowed"
        self.allowed.mkdir()
        self.cfg = {"allowed_roots": [str(self.allowed)]}
        self.server = Server(self.cfg)

    def call(self, name, arguments=None):
        return self.server.call(name, arguments or {})

    def skip_unavailable_link(self, kind, reason=None):
        if reason is not None:
            type(self)._link_unavailable[kind] = reason
        if kind in type(self)._link_unavailable:
            self.skipTest(type(self)._link_unavailable[kind])

    def directory_link(self, link, target):
        if os.name == "nt":
            self.skip_unavailable_link("directory")
            # Junctions exercise directory redirection without Developer Mode.
            try:
                process = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                                         capture_output=True, timeout=5)
            except subprocess.TimeoutExpired:
                self.skip_unavailable_link("directory", "directory junction creation timed out after 5 seconds")
            if process.returncode:
                self.skip_unavailable_link("directory", "directory junction creation is unavailable")
        else:
            link.symlink_to(target, target_is_directory=True)

    def file_link(self, link, target):
        if os.name == "nt":
            self.skip_unavailable_link("file")
            # Some hosts stall in CreateSymbolicLink; bound fixture creation.
            try:
                process = subprocess.run([sys.executable, "-c",
                                          "import os, sys; os.symlink(sys.argv[1], sys.argv[2])",
                                          str(target), str(link)], capture_output=True, timeout=5)
            except subprocess.TimeoutExpired:
                self.skip_unavailable_link("file", "file symlink creation timed out after 5 seconds")
            if process.returncode:
                self.skip_unavailable_link("file", "file symlink creation is unavailable")
            return
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("file symlink creation is unavailable")

    def test_directory_copy_rejects_destination_directory_link_escape(self):
        source = self.allowed / "source"
        (source / "nested").mkdir(parents=True)
        (source / "ordinary.txt").write_text("new", encoding="utf-8")
        (source / "nested" / "sample.txt").write_text("new", encoding="utf-8")
        target = self.allowed / "destination"
        target.mkdir()
        (target / "ordinary.txt").write_text("original", encoding="utf-8")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "sample.txt").write_text("original", encoding="utf-8")
        self.directory_link(target / "nested", outside)
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target), "overwrite": True})
        self.assertTrue(result["isError"])
        self.assertEqual((outside / "sample.txt").read_text(encoding="utf-8"), "original")
        self.assertEqual((target / "ordinary.txt").read_text(encoding="utf-8"), "original")

    def test_directory_copy_rejects_destination_file_link_escape(self):
        source = self.allowed / "source"
        source.mkdir()
        (source / "sample.txt").write_text("new", encoding="utf-8")
        target = self.allowed / "destination"
        target.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("original", encoding="utf-8")
        self.file_link(target / "sample.txt", outside)
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target), "overwrite": True})
        self.assertTrue(result["isError"])
        self.assertEqual(outside.read_text(encoding="utf-8"), "original")

    def test_file_copy_into_directory_checks_effective_destination(self):
        source = self.allowed / "sample.txt"
        source.write_text("new", encoding="utf-8")
        target = self.allowed / "destination"
        target.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("original", encoding="utf-8")
        self.file_link(target / source.name, outside)
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target), "overwrite": True})
        self.assertTrue(result["isError"])
        self.assertEqual(outside.read_text(encoding="utf-8"), "original")

    def test_directory_copy_checks_files_beneath_source_directory_links(self):
        source = self.allowed / "source"
        source.mkdir()
        shared = self.allowed / "shared"
        shared.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        self.file_link(shared / "sample.txt", outside)
        self.directory_link(source / "linked", shared)
        target = self.allowed / "destination"
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target)})
        self.assertTrue(result["isError"])
        self.assertFalse(target.exists())

    def test_directory_copy_merges_regular_destination(self):
        source = self.allowed / "source"
        (source / "nested").mkdir(parents=True)
        (source / "nested" / "sample.txt").write_text("孙小圣 SXS", encoding="utf-8")
        target = self.allowed / "destination"
        (target / "nested").mkdir(parents=True)
        (target / "nested" / "keep.txt").write_text("keep", encoding="utf-8")
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target), "overwrite": True})
        self.assertFalse(result["isError"], result)
        self.assertEqual((target / "nested" / "sample.txt").read_text(encoding="utf-8"), "孙小圣 SXS")
        self.assertEqual((target / "nested" / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_directory_copy_preserves_allowed_source_link_workflow(self):
        source = self.allowed / "source"
        source.mkdir()
        shared = self.allowed / "shared"
        shared.mkdir()
        (shared / "sample.txt").write_text("allowed", encoding="utf-8")
        self.directory_link(source / "linked", shared)
        target = self.allowed / "destination"
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target)})
        self.assertFalse(result["isError"], result)
        self.assertEqual((target / "linked" / "sample.txt").read_text(encoding="utf-8"), "allowed")

    def test_directory_copy_rejects_source_link_cycles_before_writing(self):
        source = self.allowed / "source"
        source.mkdir()
        self.directory_link(source / "loop", source)
        target = self.allowed / "destination"
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target)})
        self.assertTrue(result["isError"])
        self.assertFalse(target.exists())

    def test_directory_copy_rejects_destination_inside_linked_source(self):
        source = self.allowed / "source"
        source.mkdir()
        shared = self.allowed / "shared"
        shared.mkdir()
        self.directory_link(source / "linked", shared)
        target = shared / "destination"
        result = self.call("windows_copy_file", {"source": str(source), "destination": str(target)})
        self.assertTrue(result["isError"])
        self.assertFalse(target.exists())

    def test_legacy_tool_names_preserved(self):
        expected = set((Path(__file__).parent / "legacy_tools.txt").read_text().splitlines())
        names = [tool["name"] for tool in TOOLS]
        self.assertEqual(set(names), expected)
        self.assertEqual(len(names), 39)
        self.assertEqual(len(set(names)), len(names))

    def test_stdio_recovers_from_parse_error_and_ignores_notifications(self):
        messages = ['{broken', json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                    json.dumps({"jsonrpc": "2.0", "id": "a", "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}),
                    json.dumps({"jsonrpc": "2.0", "method": "ping"}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})]
        output = io.StringIO()
        serve_stdio(self.server, io.StringIO("\n".join(messages) + "\n"), output)
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(replies), 3)
        self.assertEqual(replies[0]["error"]["code"], -32700)
        self.assertEqual(replies[1]["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(len(replies[2]["result"]["tools"]), 39)

    def test_rpc_invalid_params_do_not_crash(self):
        for params in ([], None, "bad"):
            result = self.server.dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})
            self.assertEqual(result["error"]["code"], -32602)
        self.assertEqual(self.server.dispatch([])["error"]["code"], -32600)
        self.assertIsNone(self.server.dispatch({"jsonrpc": "2.0", "method": "unknown"}))

    def test_arguments_are_validated_before_dispatch(self):
        cases = [("windows_click", {"x": True, "y": 0}), ("windows_wait", {"seconds": -1}),
                 ("windows_wait", {"seconds": float("nan")}), ("windows_read_file", {}),
                 ("windows_wait", {"unexpected": 1}), ("windows_write_file", {"path": "a", "content": "b", "append": "false"})]
        for name, args in cases:
            with self.subTest(name=name, args=args):
                self.assertTrue(self.server.call(name, args)["isError"])
        self.assertTrue(self.server.call("windows_wait", [])["isError"])
        self.assertTrue(self.server.call("unknown", {})["isError"])

    def test_zero_wait_is_valid(self):
        result = self.call("windows_wait", {"seconds": 0})
        self.assertFalse(result["isError"])
        self.assertEqual(json.loads(result["content"][0]["text"])["waited"], 0)

    def test_unicode_file_workflow(self):
        source = self.allowed / "unicode.txt"
        copied = self.allowed / "copy.txt"
        moved = self.allowed / "moved.txt"
        self.assertFalse(self.call("windows_write_file", {"path": str(source), "content": "孙小圣 SXS\n"})["isError"])
        self.assertFalse(self.call("windows_copy_file", {"source": str(source), "destination": str(copied)})["isError"])
        self.assertTrue(self.call("windows_copy_file", {"source": str(source), "destination": str(copied)})["isError"])
        self.assertFalse(self.call("windows_move_file", {"source": str(copied), "destination": str(moved)})["isError"])
        result = self.call("windows_read_file", {"path": str(moved)})
        self.assertEqual(json.loads(result["content"][0]["text"])["content"], "孙小圣 SXS\n")
        self.assertFalse(self.call("windows_delete_path", {"path": str(moved)})["isError"])
        self.assertFalse(moved.exists())

    def test_all_file_routes_check_roots(self):
        outside = self.root / "outside.txt"
        outside.write_text("outside")
        cases = [("windows_read_file", {"path": str(outside)}), ("windows_file_info", {"path": str(outside)}),
                 ("windows_write_file", {"path": str(outside), "content": "changed"}),
                 ("windows_copy_file", {"source": str(outside), "destination": str(self.allowed / "x")}),
                 ("windows_copy_file", {"source": str(self.allowed / "x"), "destination": str(outside)}),
                 ("windows_move_file", {"source": str(outside), "destination": str(self.allowed / "x")}),
                 ("windows_delete_path", {"path": str(outside)}), ("windows_search_files", {"root": str(self.root)})]
        for name, args in cases:
            with self.subTest(name=name):
                self.assertTrue(self.server.call(name, args)["isError"])
        self.assertEqual(outside.read_text(), "outside")
        self.assertTrue(self.call("windows_delete_path", {"path": str(self.allowed), "recursive": True})["isError"])

    def test_path_traversal_and_symlink_escape(self):
        with self.assertRaises(PermissionError):
            checked_path(str(self.allowed / ".." / "outside.txt"), self.cfg)
        link = self.allowed / "link"
        self.directory_link(link, self.root)
        with self.assertRaises(PermissionError):
            checked_path(str(link / "outside.txt"), self.cfg)

    def test_invalid_configuration_fails_closed(self):
        config = self.root / "bad.json"
        for data in ({"allowed_roots": []}, {"allowed_roots": ["relative"]}, [], {"allowed_roots": "C:"}):
            config.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_config(config)

    def test_cli_stdio_has_no_logging_on_stdout(self):
        request = json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/list"}) + "\n"
        process = subprocess.run([sys.executable, "-m", "sxs_control", "--stdio"], input=request,
                                 capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(process.stdout.splitlines()), 1)
        self.assertEqual(len(json.loads(process.stdout)["result"]["tools"]), 39)

    def test_click_zero_never_emits_mouse_button_events(self):
        from unittest.mock import patch, Mock
        native = Mock()
        with patch.object(desktop.ctypes, "windll", create=True) as library:
            library.user32 = native
            result = desktop.click({"x": 10, "y": 20, "clicks": 0})
        native.mouse_event.assert_not_called()
        self.assertTrue(result["hovered"])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = make_http_server(Server({"allowed_roots": [str(Path.home())]}), 0)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.httpd.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def request(self, path="/health", data=None, extra=None):
        headers = {"X-SXS-Local": "1", "Content-Type": "application/json"}
        headers.update(extra or {})
        request = Request(self.base + path, data=data, headers=headers)
        try:
            response = build_opener(ProxyHandler({})).open(request, timeout=5)
        except HTTPError as response:
            return response.code, response.read()
        with response:
            return response.status, response.read()

    def test_valid_health_and_tool_call(self):
        status, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["tool_count"], 39)
        data = json.dumps({"tool": "windows_wait", "arguments": {"seconds": 0}}).encode()
        status, body = self.request("/call", data)
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["isError"])

    def test_host_origin_and_required_header(self):
        for extra in ({"Host": "attacker.invalid"}, {"Origin": "http://attacker.invalid"},
                      {"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"}, {"X-SXS-Local": ""}):
            with self.subTest(headers=extra):
                self.assertEqual(self.request(extra=extra)[0], 403)

    def test_http_malformed_payloads(self):
        self.assertEqual(self.request("/call", b"{broken")[0], 400)
        self.assertEqual(self.request("/call", b"{}", {"Content-Type": "text/plain"})[0], 415)
        status, body = self.request("/call", b'{"tool":"windows_wait","arguments":[]}')
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["isError"])

    def test_http_notifications_have_empty_202_response(self):
        status, body = self.request("/mcp", b'{"jsonrpc":"2.0","method":"notifications/initialized"}')
        self.assertEqual(status, 202)
        self.assertEqual(body, b"")


if __name__ == "__main__":
    unittest.main()

