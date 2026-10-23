"""Windows system adapters; requests run with the invoking user's privileges."""

from __future__ import annotations

import base64
import json
import os
import platform
import socket
import subprocess
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def require_windows():
    if os.name != "nt":
        raise RuntimeError("this tool requires an interactive Windows session")


def powershell(script: str, timeout=30) -> dict:
    require_windows()
    prefix = "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); $OutputEncoding=[Console]::OutputEncoding; "
    encoded = base64.b64encode((prefix + script).encode("utf-16-le")).decode("ascii")
    proc = subprocess.run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-STA",
                           "-EncodedCommand", encoded], timeout=timeout, capture_output=True,
                          encoding="utf-8", errors="replace", shell=False)
    return {"returncode": proc.returncode, "stdout": proc.stdout[:200000], "stderr": proc.stderr[:50000]}


def clipboard(mode: str, text=None) -> dict:
    if mode == "set":
        if not isinstance(text, str):
            raise ValueError("text is required for clipboard set")
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        script = f"Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}')))"
    else:
        script = "Get-Clipboard -Raw | ConvertTo-Json -Compress"
    result = powershell(script, timeout=10)
    if result["returncode"]:
        raise RuntimeError("Windows clipboard operation failed")
    return {"mode": mode, "characters": len(text)} if mode == "set" else {"mode": mode, "text": json.loads(result["stdout"] or '""') or ""}


def processes(args: dict) -> dict:
    import psutil
    mode = args.get("mode", "list")
    query = args.get("name", "").casefold()
    pid = args.get("pid")
    if mode == "kill":
        if pid is None and not query:
            raise ValueError("pid or process name is required")
        results = []
        for process in psutil.process_iter(["pid", "name"]):
            if (pid is not None and process.pid != pid) or (pid is None and process.info["name"].casefold() != query):
                continue
            item = {"pid": process.pid, "name": process.info["name"]}
            try:
                process.kill() if args.get("force", False) else process.terminate()
                item["terminated"] = True
            except psutil.Error as error:
                item["error"] = type(error).__name__
            results.append(item)
        if not results:
            raise ProcessLookupError("no matching process")
        return {"results": results}
    rows = []
    for process in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            data = process.info
            if query and query not in (data["name"] or "").casefold():
                continue
            rows.append({"pid": data["pid"], "name": data["name"] or "",
                         "memory": data["memory_info"].rss if data["memory_info"] else 0,
                         "cpu": data["cpu_percent"] or 0.0})
        except (psutil.Error, OSError):
            continue
    order = args.get("sort_by", "memory")
    rows.sort(key=lambda row: row[order], reverse=order != "name")
    return {"processes": rows[:args.get("limit", 20)], "count": len(rows)}


def registry(args: dict) -> dict:
    import winreg as reg
    hives = {"HKCU": reg.HKEY_CURRENT_USER, "HKLM": reg.HKEY_LOCAL_MACHINE,
             "HKCR": reg.HKEY_CLASSES_ROOT, "HKU": reg.HKEY_USERS, "HKCC": reg.HKEY_CURRENT_CONFIG}
    for name, value in list(hives.items()):
        hives[{"HKCU": "HKEY_CURRENT_USER", "HKLM": "HKEY_LOCAL_MACHINE", "HKCR": "HKEY_CLASSES_ROOT",
               "HKU": "HKEY_USERS", "HKCC": "HKEY_CURRENT_CONFIG"}[name]] = value
    head, _, subkey = args["path"].replace("/", "\\").partition("\\")
    if head.upper() not in hives:
        raise ValueError("unsupported registry hive")
    hive = hives[head.upper()]
    name = args.get("name", "")
    mode = args["mode"]
    if mode == "set":
        if "value" not in args:
            raise ValueError("value is required for registry set")
        types = {"String": reg.REG_SZ, "ExpandString": reg.REG_EXPAND_SZ, "Binary": reg.REG_BINARY,
                 "DWord": reg.REG_DWORD, "MultiString": reg.REG_MULTI_SZ, "QWord": reg.REG_QWORD}
        kind = types[args.get("type", "String")]
        value = args["value"]
        if kind == reg.REG_BINARY:
            value = bytes(value)
        with reg.CreateKeyEx(hive, subkey, 0, reg.KEY_SET_VALUE) as key:
            reg.SetValueEx(key, name, 0, kind, value)
        return {"written": True}
    if mode == "delete":
        if "name" in args:
            with reg.OpenKey(hive, subkey, 0, reg.KEY_SET_VALUE) as key:
                reg.DeleteValue(key, name)
        elif subkey:
            reg.DeleteKey(hive, subkey)
        else:
            raise ValueError("cannot delete a registry hive")
        return {"deleted": True}
    with reg.OpenKey(hive, subkey, 0, reg.KEY_READ) as key:
        if mode == "get":
            value, kind = reg.QueryValueEx(key, name)
            return {"value": list(value) if isinstance(value, bytes) else value, "type": kind}
        children, values = [], []
        for index in range(reg.QueryInfoKey(key)[0]):
            children.append(reg.EnumKey(key, index))
        for index in range(reg.QueryInfoKey(key)[1]):
            label, value, kind = reg.EnumValue(key, index)
            values.append({"name": label, "value": list(value) if isinstance(value, bytes) else value, "type": kind})
        return {"subkeys": children, "values": values}


def run(action: str, cfg: dict, args: dict) -> dict:
    if action == "status":
        return {"hostname": socket.gethostname(), "platform": platform.platform(), "python": platform.python_version(),
                "mode": "local-only", "cloud_fallback": False, "allowed_roots": cfg["allowed_roots"],
                "windows_session": os.name == "nt"}
    if action == "wait":
        seconds = args.get("seconds", 1)
        time.sleep(seconds)
        return {"waited": seconds}
    if action == "scrape_url":
        if urlsplit(args["url"]).scheme not in ("http", "https"):
            raise ValueError("only HTTP(S) URLs are supported")
        request = Request(args["url"], headers={"User-Agent": "SXS-Control/0.1"})
        with urlopen(request, timeout=args.get("timeout", 20)) as response:
            data = response.read(200001)
            encoding = response.headers.get_content_charset() or "utf-8"
            return {"url": response.url, "status_code": response.status, "text": data[:200000].decode(encoding, errors="replace"),
                    "truncated": len(data) > 200000}
    require_windows()
    if action == "powershell":
        return powershell(args["command"], args.get("timeout", 30))
    if action == "clipboard":
        return clipboard(args["mode"], args.get("text"))
    if action in ("process", "kill_process", "list_processes"):
        return processes({**args, "mode": "kill"} if action == "kill_process" else args)
    if action == "registry":
        return registry(args)
    if action == "open_app":
        path = os.path.expandvars(os.path.expanduser(args["path"]))
        if args.get("args"):
            subprocess.Popen([path, *args["args"]], shell=False)
        else:
            os.startfile(path)
        return {"opened": args["path"]}
    raise ValueError("unsupported system action")

