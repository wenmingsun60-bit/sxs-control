"""The public SXS tool contract; no executable schemas or cloud imports."""

from __future__ import annotations

TOOLS: list[dict] = []
ACTIONS: dict[str, str] = {}


def string(description="", **kwargs):
    return {"type": "string", "description": description, **kwargs}


def integer(**kwargs):
    return {"type": "integer", **kwargs}


def number(**kwargs):
    return {"type": "number", **kwargs}


def boolean(default=False):
    return {"type": "boolean", "default": default}


def add(name, action, description, properties=None, required=(), read_only=False):
    TOOLS.append({"name": name, "description": description,
                  "inputSchema": {"type": "object", "properties": properties or {},
                                  "required": list(required), "additionalProperties": False},
                  "annotations": {"readOnlyHint": read_only, "destructiveHint": not read_only,
                                  "openWorldHint": action == "scrape_url"}})
    ACTIONS[name] = action


PATH = string("Absolute local path inside an allowed root.")
XY = {"x": integer(), "y": integer()}
WINDOW = {"hwnd": integer(minimum=1), "window_name": string(), "title": string()}
BUTTON = string(enum=["left", "right", "middle"], default="left")
UI = {**WINDOW, "label": integer(minimum=0), "browser": boolean()}
SCREENSHOT = {"region": {"type": "array", "items": integer(), "minItems": 4, "maxItems": 4},
              "max_width": integer(minimum=320, maximum=3840, default=1440),
              "quality": integer(minimum=30, maximum=95, default=72),
              "format": string(enum=["jpeg", "png"], default="jpeg")}
CLICK = {**XY, "button": BUTTON, "clicks": integer(minimum=0, maximum=3, default=1)}
SCROLL = {**XY, "amount": integer(minimum=-100, maximum=100),
          "wheel_times": integer(minimum=0, maximum=100),
          "direction": string(enum=["up", "down", "left", "right"], default="down"),
          "type": string(enum=["vertical", "horizontal"], default="vertical")}
TYPING = {**XY, "text": string(maxLength=10000), "clear": boolean(), "press_enter": boolean()}
PROCESS = {"mode": string(enum=["list", "kill"], default="list"), "pid": integer(minimum=1),
           "name": string(), "force": boolean(), "sort_by": string(enum=["memory", "cpu", "name"], default="memory"),
           "limit": integer(minimum=1, maximum=200, default=20)}

add("windows_device_status", "status", "Read this local computer's status; no paired cloud device is required.", read_only=True)
add("windows_list_directory", "list_directory", "List at most 200 directory entries.", {"path": PATH}, ["path"], True)
add("windows_read_file", "read_file", "Read a UTF-8 or GB18030 text file up to 250 KB.", {"path": PATH}, ["path"], True)
add("windows_write_file", "write_file", "Write or append UTF-8 text (up to 1 MB).", {"path": PATH, "content": string(), "append": boolean()}, ["path", "content"])
add("windows_list_processes", "list_processes", "Read process names, PIDs and resource use.", read_only=True)
add("windows_open_app", "open_app", "Open a local program, document or folder; executable arguments stay separate.", {"path": string(), "args": {"type": "array", "items": string(), "maxItems": 32}}, ["path"])
add("windows_take_screenshot", "screenshot", "Capture the desktop or a selected region.", SCREENSHOT, read_only=True)
add("windows_click", "click", "Click physical screen coordinates; clicks=0 moves without clicking.", CLICK, ["x", "y"])
add("windows_type_text", "type_text", "Paste text into the focused input, optionally at coordinates.", TYPING, ["text"])
add("windows_powershell", "powershell", "Execute PowerShell as the current Windows user; allowed_roots is not a shell sandbox.", {"command": string(maxLength=50000), "timeout": number(minimum=1, maximum=120, default=30)}, ["command"])
add("windows_file_info", "file_info", "Read file or directory metadata.", {"path": PATH}, ["path"], True)
for name, action, description in [("windows_copy_file", "file_copy", "Copy a file or directory."), ("windows_move_file", "file_move", "Move a file or directory.")]:
    add(name, action, description, {"source": PATH, "destination": PATH, "overwrite": boolean()}, ["source", "destination"])
add("windows_delete_path", "file_delete", "Delete a file or directory; recursive deletion must be explicitly enabled.", {"path": PATH, "recursive": boolean()}, ["path"])
add("windows_search_files", "file_search", "Find file and directory names using a glob pattern.", {"root": PATH, "pattern": string(default="*"), "recursive": boolean(True), "limit": integer(minimum=1, maximum=1000, default=200)}, ["root"], True)
add("windows_kill_process", "kill_process", "Terminate a process selected by PID or name.", {"pid": integer(minimum=1), "name": string(), "force": boolean()})
add("windows_registry", "registry", "Read, list, write or delete Windows registry values or keys.", {"mode": string(enum=["get", "list", "set", "delete"]), "path": string(), "name": string(), "value": {}, "type": string(enum=["String", "ExpandString", "Binary", "DWord", "MultiString", "QWord"], default="String")}, ["mode", "path"])
add("windows_mouse_move", "mouse_move", "Move the mouse cursor without clicking.", XY, ["x", "y"])
add("windows_scroll", "scroll", "Scroll vertically or horizontally, optionally at coordinates.", SCROLL)
add("windows_keyboard_shortcut", "shortcut", "Press a key combination such as ctrl+c, alt+tab or enter.", {"shortcut": string()}, ["shortcut"])
add("windows_clipboard", "clipboard", "Get or replace plain text on the Windows clipboard.", {"mode": string(enum=["get", "set"]), "text": string(maxLength=1000000)}, ["mode"])
add("windows_scrape_url", "scrape_url", "Fetch an explicitly requested HTTP(S) URL as text, up to 200 KB.", {"url": string(), "timeout": number(minimum=1, maximum=60, default=20)}, ["url"], True)
add("windows_display_inventory", "display_inventory", "Read display bounds and monitor count.", read_only=True)
add("windows_wait", "wait", "Wait for a bounded number of seconds.", {"seconds": number(minimum=0, maximum=30, default=1)}, read_only=True)
add("windows_screenshot", "screenshot", "Alias of windows_take_screenshot.", SCREENSHOT, read_only=True)
add("windows_mouse_click", "click", "Alias of windows_click.", CLICK, ["x", "y"])
add("windows_scroll_advanced", "scroll", "Alias of windows_scroll, with direction and horizontal scrolling.", SCROLL)
for name, action, browser in [("windows_ui_snapshot", "ui_snapshot", False), ("windows_browser_ui", "browser_ui", True)]:
    add(name, action, ("Browser" if browser else "Window") + " accessibility tree with temporary numeric element labels.", {**WINDOW, "max_elements": integer(minimum=1, maximum=1200, default=300), "include_offscreen": boolean(), "browser": boolean(browser)}, read_only=True)
for name, action in [("windows_ui_click", "ui_click"), ("windows_browser_click", "browser_click")]:
    add(name, action, "Click an accessibility label from a recent snapshot; refresh after UI changes.", {**UI, "button": BUTTON, "clicks": integer(minimum=0, maximum=3, default=1)}, ["label"])
for name, action in [("windows_ui_type", "ui_type"), ("windows_browser_type", "browser_type")]:
    add(name, action, "Paste into an accessibility label from a recent snapshot.", {**UI, "text": string(maxLength=10000), "clear": boolean(), "press_enter": boolean()}, ["label", "text"])
add("windows_mouse_drag", "mouse_drag", "Drag between physical screen coordinates.", {"from_x": integer(), "from_y": integer(), "to_x": integer(), "to_y": integer(), "duration": number(minimum=0, maximum=5, default=0.5), "button": BUTTON}, ["from_x", "from_y", "to_x", "to_y"])
add("windows_multi_select", "multi_select", "Select several coordinate or label targets.", {**WINDOW, "browser": boolean(), "press_ctrl": boolean(True), "items": {"type": "array", "items": {"type": "object", "properties": {**UI, **CLICK}, "additionalProperties": False}, "minItems": 1, "maxItems": 50}}, ["items"])
add("windows_multi_edit", "multi_edit", "Paste text into several coordinate or label targets.", {**WINDOW, "browser": boolean(), "items": {"type": "array", "items": {"type": "object", "properties": {**UI, **TYPING}, "required": ["text"], "additionalProperties": False}, "minItems": 1, "maxItems": 30}}, ["items"])
add("windows_window", "window", "List visible windows, activate a window or resize it.", {**WINDOW, "mode": string(enum=["list", "switch", "resize"], default="list"), "name": string(), **XY, "width": integer(minimum=1), "height": integer(minimum=1)})
add("windows_process", "process", "List processes or terminate a selected process.", PROCESS)
add("windows_wait_for", "wait_for", "Wait for a window or accessibility condition.", {**WINDOW, "condition": string(enum=["text_exists", "active_window", "element_exists", "element_enabled", "focused_element"], default="text_exists"), "text": string(), "timeout": number(minimum=0, maximum=60, default=10), "interval": number(minimum=0.1, maximum=5, default=0.5), "browser": boolean(), "max_elements": integer(minimum=1, maximum=1200, default=800) }, read_only=True)

INDEX = {tool["name"]: tool for tool in TOOLS}


def validate(value, schema, location="arguments"):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if kind and (not isinstance(value, types[kind]) or (kind in ("integer", "number") and isinstance(value, bool))):
        raise ValueError(f"{location} must be {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{location} is not a supported value")
    if kind == "object":
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{location}.{key} is required")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key not in properties:
                if schema.get("additionalProperties") is False:
                    raise ValueError(f"unexpected field: {location}.{key}")
            else:
                validate(item, properties[key], f"{location}.{key}")
    if kind == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", float("inf")):
            raise ValueError(f"{location} has an invalid length")
        for item in value:
            validate(item, schema.get("items", {}), location + "[]")
    if kind in ("number", "integer"):
        import math
        if not math.isfinite(value) or value < schema.get("minimum", -float("inf")) or value > schema.get("maximum", float("inf")):
            raise ValueError(f"{location} is out of range")
    if kind == "string" and len(value) > schema.get("maxLength", float("inf")):
        raise ValueError(f"{location} is too long")

