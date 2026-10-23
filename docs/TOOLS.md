# 工具清单

39 个工具名称，包含截图、点击和滚动的兼容别名。参数的完整 JSON Schema 可通过 `sxs-control list` 查看。

| 工具 | 功能 |
| --- | --- |
| `windows_device_status` | Read this local computer's status; no paired cloud device is required. |
| `windows_list_directory` | List at most 200 directory entries. |
| `windows_read_file` | Read a UTF-8 or GB18030 text file up to 250 KB. |
| `windows_write_file` | Write or append UTF-8 text (up to 1 MB). |
| `windows_list_processes` | Read process names, PIDs and resource use. |
| `windows_open_app` | Open a local program, document or folder; executable arguments stay separate. |
| `windows_take_screenshot` | Capture the desktop or a selected region. |
| `windows_click` | Click physical screen coordinates; clicks=0 moves without clicking. |
| `windows_type_text` | Paste text into the focused input, optionally at coordinates. |
| `windows_powershell` | Execute PowerShell as the current Windows user; allowed_roots is not a shell sandbox. |
| `windows_file_info` | Read file or directory metadata. |
| `windows_copy_file` | Copy a file or directory. |
| `windows_move_file` | Move a file or directory. |
| `windows_delete_path` | Delete a file or directory; recursive deletion must be explicitly enabled. |
| `windows_search_files` | Find file and directory names using a glob pattern. |
| `windows_kill_process` | Terminate a process selected by PID or name. |
| `windows_registry` | Read, list, write or delete Windows registry values or keys. |
| `windows_mouse_move` | Move the mouse cursor without clicking. |
| `windows_scroll` | Scroll vertically or horizontally, optionally at coordinates. |
| `windows_keyboard_shortcut` | Press a key combination such as ctrl+c, alt+tab or enter. |
| `windows_clipboard` | Get or replace plain text on the Windows clipboard. |
| `windows_scrape_url` | Fetch an explicitly requested HTTP(S) URL as text, up to 200 KB. |
| `windows_display_inventory` | Read display bounds and monitor count. |
| `windows_wait` | Wait for a bounded number of seconds. |
| `windows_screenshot` | Alias of windows_take_screenshot. |
| `windows_mouse_click` | Alias of windows_click. |
| `windows_scroll_advanced` | Alias of windows_scroll, with direction and horizontal scrolling. |
| `windows_ui_snapshot` | Window accessibility tree with temporary numeric element labels. |
| `windows_browser_ui` | Browser accessibility tree with temporary numeric element labels. |
| `windows_ui_click` | Click an accessibility label from a recent snapshot; refresh after UI changes. |
| `windows_browser_click` | Click an accessibility label from a recent snapshot; refresh after UI changes. |
| `windows_ui_type` | Paste into an accessibility label from a recent snapshot. |
| `windows_browser_type` | Paste into an accessibility label from a recent snapshot. |
| `windows_mouse_drag` | Drag between physical screen coordinates. |
| `windows_multi_select` | Select several coordinate or label targets. |
| `windows_multi_edit` | Paste text into several coordinate or label targets. |
| `windows_window` | List visible windows, activate a window or resize it. |
| `windows_process` | List processes or terminate a selected process. |
| `windows_wait_for` | Wait for a window or accessibility condition. |
