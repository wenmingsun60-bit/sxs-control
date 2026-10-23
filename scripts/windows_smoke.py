"""Read-only native checks plus disposable file operations; no real desktop input."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from sxs_control.server import Server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-ui", action="store_true", help="for Windows CI runners without an interactive desktop")
    args = parser.parse_args()
    if os.name != "nt":
        print(json.dumps({"skipped": "requires Windows"}))
        return 0
    passed = []
    with tempfile.TemporaryDirectory(prefix="sxs-smoke-") as temp:
        server = Server({"allowed_roots": [temp]})

        def check(name, arguments=None):
            result = server.call(name, arguments or {})
            if result["isError"]:
                raise RuntimeError(name + ": " + result["content"][0]["text"])
            passed.append(name)
            return result

        check("windows_device_status")
        file = str(Path(temp) / "unicode.txt")
        copy = str(Path(temp) / "copy.txt")
        moved = str(Path(temp) / "moved.txt")
        check("windows_write_file", {"path": file, "content": "孙小圣 SXS\n"})
        value = check("windows_read_file", {"path": file})
        assert json.loads(value["content"][0]["text"])["content"] == "孙小圣 SXS\n"
        check("windows_file_info", {"path": file})
        check("windows_list_directory", {"path": temp})
        check("windows_copy_file", {"source": file, "destination": copy})
        check("windows_move_file", {"source": copy, "destination": moved})
        check("windows_search_files", {"root": temp, "pattern": "*.txt"})
        check("windows_delete_path", {"path": moved})
        ps = check("windows_powershell", {"command": "Write-Output 'SXS smoke test'"})
        assert json.loads(ps["content"][0]["text"])["returncode"] == 0
        check("windows_process", {"limit": 1})
        if not args.skip_ui:
            check("windows_display_inventory")
            check("windows_ui_snapshot", {"max_elements": 3})
        print(json.dumps({"ok": True, "passed_count": len(passed), "passed": passed, "ui_checked": not args.skip_ui}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

