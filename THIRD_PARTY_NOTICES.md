# Third-party notices

This repository distinguishes earlier project references from actual runtime dependencies. Crediting an upstream project does not claim ownership of its code or imply endorsement.

## Earlier project references

| Project | Verified license | Relationship to this release |
| --- | --- | --- |
| [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | MIT; Copyright (c) 2025 JEOMON GEORGE | Present in the earlier Windows environment as 0.8.7; used as a workflow and API reference. The full backend and its dependency tree are not shipped or imported by this release. |
| [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | MIT; Copyright (c) 2024–2025 Eduard Ruzga and Desktop Commander Contributors | Earlier workflow reference; its TypeScript implementation is not bundled here. |

Full upstream notices are retained in `LICENSES/Windows-MCP-MIT.txt` and `LICENSES/DesktopCommander-MIT.txt`. The checked license blob IDs were respectively `a3077dae7e3dcd61e31a775f24678f338bda7a6e` and `cc6ce4fa68f26cd5db3dc1ff83c8163094f28451` on 2026-10-23. These identify license texts, not a claim that a particular source commit was copied.

## Runtime dependencies

These packages are installed separately by pip; their source trees and binary wheels are not vendored into this repository or source archive.

| Package | Observed version during Windows verification | License declared by the installed distribution | Purpose |
| --- | --- | --- | --- |
| Pillow | 12.3.0 | MIT-CMU; retain the distribution's additional third-party notices | Screenshots and image encoding |
| psutil | 7.2.2 | BSD-3-Clause | Process metadata and termination |
| pywin32 | 312 | PSF; see the distribution's license and embedded notices | Window enumeration and window management |
| uiautomation | 2.0.29 | Apache-2.0 | Windows UI Automation access |
| comtypes | Determined by the installed uiautomation dependency | MIT, subject to its distribution notices | COM interoperability, installed transitively |

The Python interpreter, Windows, PowerShell and native APIs remain under their respective terms. Dependencies may change within the version ranges in `pyproject.toml`; check their actual release notices when creating bundled binaries. This release contains source and a Python wheel for SXS itself, not a bundled executable with all dependencies.

