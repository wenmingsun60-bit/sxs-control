"""Interactive Windows input and accessibility; no remote broker or telemetry."""

from __future__ import annotations

import base64
import ctypes
import io
import time
from collections import deque
from contextlib import contextmanager

from .system import clipboard, require_windows

BROWSERS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
BUTTONS = {"left": (0x0002, 0x0004), "right": (0x0008, 0x0010), "middle": (0x0020, 0x0040)}


def windows():
    import psutil
    import win32gui
    import win32process
    result = []

    def collect(hwnd, _):
        try:
            title = win32gui.GetWindowText(hwnd)
            if not title or not win32gui.IsWindowVisible(hwnd):
                return
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            try:
                process = psutil.Process(pid).name()
            except psutil.Error:
                process = ""
            result.append({"hwnd": hwnd, "title": title, "pid": pid, "process": process,
                           "x": left, "y": top, "width": right - left, "height": bottom - top})
        except OSError:
            return

    win32gui.EnumWindows(collect, None)
    return result


def select_window(args):
    import win32gui
    rows = windows()
    if args.get("browser"):
        rows = [row for row in rows if row["process"].lower() in BROWSERS]
    if args.get("hwnd") is not None:
        rows = [row for row in rows if row["hwnd"] == args["hwnd"]]
    query = (args.get("window_name") or args.get("title") or "").casefold()
    if query:
        rows = [row for row in rows if query in row["title"].casefold()]
    if not rows:
        raise ValueError("no matching visible window")
    foreground = win32gui.GetForegroundWindow()
    return next((row for row in rows if row["hwnd"] == foreground), rows[0])


@contextmanager
def automation():
    import uiautomation as auto
    with auto.UIAutomationInitializerInThread():
        yield auto


def accessibility(args, target=None):
    window = select_window(args)
    limit = args.get("max_elements", 300)
    result = []
    scanned = 0
    with automation() as auto:
        root = auto.ControlFromHandle(window["hwnd"])
        queue = deque(root.GetChildren())
        deadline = time.monotonic() + 8
        while queue and scanned < 5000 and time.monotonic() < deadline:
            control = queue.popleft()
            label = scanned
            scanned += 1
            try:
                # Labels use traversal order before visibility filtering.
                queue.extend(control.GetChildren())
                box = control.BoundingRectangle
                item = {"label": label, "name": control.Name or "", "type": control.ControlTypeName,
                        "automation_id": control.AutomationId or "", "x": box.left, "y": box.top,
                        "width": box.right - box.left, "height": box.bottom - box.top,
                        "enabled": bool(control.IsEnabled), "focused": bool(control.HasKeyboardFocus),
                        "offscreen": bool(control.IsOffscreen)}
                if target is not None and label == target:
                    if item["offscreen"] or item["width"] <= 0 or item["height"] <= 0:
                        raise ValueError("target is not visible; take another snapshot")
                    return window, item
                if target is None and (args.get("include_offscreen", False) or not item["offscreen"]):
                    result.append(item)
                    if len(result) >= limit:
                        break
            except ValueError:
                raise
            except Exception:
                continue
    if target is not None:
        raise ValueError("UI label is no longer available; refresh the snapshot")
    return {"window": window, "elements": result, "returned": len(result), "scanned": scanned, "truncated": bool(queue)}


def shortcut(combination):
    user = ctypes.windll.user32
    aliases = {"ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
               "enter": 0x0D, "tab": 0x09, "escape": 0x1B, "esc": 0x1B, "space": 0x20,
               "backspace": 0x08, "delete": 0x2E, "left": 0x25, "up": 0x26, "right": 0x27,
               "down": 0x28, "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22}
    codes = []
    for key in combination.lower().split("+"):
        key = key.strip()
        if key in aliases:
            codes.append(aliases[key])
        elif len(key) == 1 and key.isascii() and key.isalnum():
            codes.append(ord(key.upper()))
        elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
            codes.append(0x6F + int(key[1:]))
        else:
            raise ValueError("unsupported shortcut key")
    pressed = []
    try:
        for code in codes:
            user.keybd_event(code, 0, 0, 0)
            pressed.append(code)
    finally:
        for code in reversed(pressed):
            user.keybd_event(code, 0, 0x0002, 0)


def click(args):
    user = ctypes.windll.user32
    user.SetCursorPos(args["x"], args["y"])
    count = args.get("clicks", 1)
    down, up = BUTTONS[args.get("button", "left")]
    for index in range(count):
        user.mouse_event(down, 0, 0, 0, 0)
        user.mouse_event(up, 0, 0, 0, 0)
        if index + 1 < count:
            time.sleep(0.08)
    return {"x": args["x"], "y": args["y"], "clicks": count, "hovered": count == 0}


def run(action, cfg, args):
    require_windows()
    user = ctypes.windll.user32
    try:
        user.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        pass
    if action == "display_inventory":
        import win32api
        monitors = []
        for handle, _, _ in win32api.EnumDisplayMonitors():
            data = win32api.GetMonitorInfo(handle)
            monitors.append({"bounds": list(data["Monitor"]), "work_area": list(data["Work"]), "primary": bool(data["Flags"] & 1)})
        return {"monitors": monitors, "monitor_count": len(monitors)}
    if action == "screenshot":
        from PIL import ImageGrab
        region = args.get("region")
        if region and (region[2] <= region[0] or region[3] <= region[1]):
            raise ValueError("region must be [left, top, right, bottom]")
        image = ImageGrab.grab(bbox=tuple(region) if region else None, all_screens=True)
        max_width = args.get("max_width", 1440)
        if image.width > max_width:
            image = image.resize((max_width, max(1, round(image.height * max_width / image.width))))
        stream = io.BytesIO()
        fmt = args.get("format", "jpeg")
        image.convert("RGB").save(stream, format="PNG" if fmt == "png" else "JPEG", **({} if fmt == "png" else {"quality": args.get("quality", 72)}))
        return {"image_base64": base64.b64encode(stream.getvalue()).decode("ascii"), "mime_type": "image/png" if fmt == "png" else "image/jpeg",
                "width": image.width, "height": image.height, "region": region}
    if action == "mouse_move":
        user.SetCursorPos(args["x"], args["y"])
        return {"moved": True}
    if action == "click":
        return click(args)
    if action == "shortcut":
        shortcut(args["shortcut"])
        return {"pressed": True}
    if action == "scroll":
        if "x" in args and "y" in args:
            user.SetCursorPos(args["x"], args["y"])
        horizontal = args.get("type", "vertical") == "horizontal"
        direction = args.get("direction", "down")
        amount = args.get("amount", 0) if "wheel_times" not in args else args["wheel_times"] * (1 if direction in ("up", "right") else -1)
        user.mouse_event(0x1000 if horizontal else 0x0800, 0, 0, amount * 120, 0)
        return {"scrolled": amount, "horizontal": horizontal}
    if action == "type_text":
        if "x" in args and "y" in args:
            click({"x": args["x"], "y": args["y"]})
        if args.get("clear", False):
            shortcut("ctrl+a")
        clipboard("set", args["text"])
        shortcut("ctrl+v")
        if args.get("press_enter", False):
            time.sleep(0.05)
            shortcut("enter")
        return {"typed": True, "characters": len(args["text"])}
    if action in ("ui_snapshot", "browser_ui"):
        return accessibility({**args, "browser": action == "browser_ui" or args.get("browser", False)})
    if action in ("ui_click", "browser_click", "ui_type", "browser_type"):
        row, element = accessibility({**args, "browser": action.startswith("browser") or args.get("browser", False)}, target=args["label"])
        local = {**args, "x": int(element["x"] + element["width"] / 2), "y": int(element["y"] + element["height"] / 2)}
        if not element["enabled"]:
            raise ValueError("target is disabled")
        result = run("type_text" if action.endswith("type") else "click", cfg, local)
        return {**result, "label": element["label"], "window": row["title"]}
    if action == "mouse_drag":
        down, up = BUTTONS[args.get("button", "left")]
        start = (args["from_x"], args["from_y"])
        end = (args["to_x"], args["to_y"])
        duration = args.get("duration", 0.5)
        steps = max(1, round(duration * 30))
        user.SetCursorPos(*start)
        user.mouse_event(down, 0, 0, 0, 0)
        try:
            for step in range(1, steps + 1):
                user.SetCursorPos(*(round(a + (b - a) * step / steps) for a, b in zip(start, end)))
                time.sleep(duration / steps)
        finally:
            user.mouse_event(up, 0, 0, 0, 0)
        return {"dragged": True}
    if action in ("multi_select", "multi_edit"):
        ctrl = action == "multi_select" and args.get("press_ctrl", True)
        if ctrl:
            user.keybd_event(0x11, 0, 0, 0)
        results = []
        try:
            for item in args["items"]:
                local = {key: value for key, value in args.items() if key in ("hwnd", "window_name", "title", "browser")}
                local.update(item)
                if action == "multi_edit":
                    next_action = "ui_type" if "label" in item else "type_text"
                else:
                    next_action = "ui_click" if "label" in item else "click"
                results.append(run(next_action, cfg, local))
        finally:
            if ctrl:
                user.keybd_event(0x11, 0, 0x0002, 0)
        return {"count": len(results), "results": results}
    if action == "window":
        import win32con
        import win32gui
        mode = args.get("mode", "list")
        if mode == "list":
            query = (args.get("name") or args.get("window_name") or "").casefold()
            return {"windows": [row for row in windows() if not query or query in row["title"].casefold()]}
        row = select_window(args)
        if mode == "switch":
            win32gui.ShowWindow(row["hwnd"], win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(row["hwnd"])
        else:
            win32gui.SetWindowPos(row["hwnd"], 0, args.get("x", row["x"]), args.get("y", row["y"]), args.get("width", row["width"]), args.get("height", row["height"]), win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
        return {"ok": True, "window": row}
    if action == "wait_for":
        deadline = time.monotonic() + args.get("timeout", 10)
        query = args.get("text", "").casefold()
        condition = args.get("condition", "text_exists")
        while True:
            try:
                if condition == "active_window":
                    import win32gui
                    foreground = win32gui.GetForegroundWindow()
                    title = win32gui.GetWindowText(foreground)
                    if (not query or query in title.casefold()) and (not args.get("hwnd") or foreground == args["hwnd"]):
                        return {"matched": True, "hwnd": foreground}
                else:
                    snapshot = accessibility({**args, "include_offscreen": True})
                    for item in snapshot["elements"]:
                        text_matches = not query or query in item["name"].casefold()
                        state_matches = condition in ("text_exists", "element_exists") or (condition == "element_enabled" and item["enabled"]) or (condition == "focused_element" and item["focused"])
                        if text_matches and state_matches:
                            return {"matched": True, "element": item}
            except (ValueError, OSError):
                pass
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"matched": False}
            time.sleep(min(args.get("interval", 0.5), remaining))
    raise ValueError("unsupported desktop action")

