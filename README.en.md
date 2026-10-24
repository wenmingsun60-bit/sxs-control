<h1 align="center">SXS Control</h1>

<p align="center"><strong>Let your AI assistant work on your Windows PC</strong></p>
<p align="center">See the screen · Use apps · Organize files</p>

<p align="center">
  <a href="#get-started">Get started</a> ·
  <a href="docs/TOOLS.md">Tool reference</a> ·
  <a href="docs/VALIDATION.md">Validation</a> ·
  <a href="README.md">简体中文</a>
</p>

<p align="center">
  <a href="https://github.com/wenmingsun60-bit/sxs-control/actions/workflows/ci.yml"><img src="https://github.com/wenmingsun60-bit/sxs-control/actions/workflows/ci.yml/badge.svg?branch=main" alt="Automated checks status"></a>
  &nbsp; Runs locally · <a href="LICENSE">MIT license</a> · 0.1.1 Alpha
</p>

SXS Control gives AI assistants access to screenshots, mouse and keyboard actions, and local files. **Your AI client interprets the request; SXS Control performs the operation on the current computer.** The client must support local tool execution.

Computer operations run locally. Your chosen AI client determines whether its model uses the network and what content it receives.

## What you can do

| Your task | Available capabilities |
| --- | --- |
| Inspect the current screen | Capture screenshots and read windows and accessible controls. |
| Work with desktop apps | Click, type, scroll, use keyboard shortcuts, and interact with accessible controls. |
| Organize local files | Search, read, write, copy, move, and delete within configured file roots. |
| Diagnose system state | Inspect processes, run PowerShell, and read or modify the registry when needed. |

There are **39 tool entries**, including compatibility aliases. See the [tool reference](docs/TOOLS.md) for parameters.

## Get started

You need **Windows 10/11, Python 3.10 or later, and Git**. Desktop actions require an interactive desktop. Installation is currently from source.

### 1. Install and check the environment

Run in PowerShell:

```powershell
git clone https://github.com/wenmingsun60-bit/sxs-control.git
cd sxs-control
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m sxs_control init
.\.venv\Scripts\python.exe -m sxs_control doctor
```

The environment check passes when `doctor` reports `ok: true`, `tool_count: 39`, and a version for each dependency. Skip `init` if you already have a configuration.

### 2. Try a computer status query

```powershell
$sxsPython = ".\.venv\Scripts\python.exe"
'{}' | & $sxsPython -X utf8 -m sxs_control call windows_device_status --args-stdin
```

An outer result of `isError: false` confirms the call succeeded. This first call only reads status.

### 3. Connect your AI assistant

Use a client that can launch a local tool process, usually through **MCP stdio**. Add the configuration below and replace `command` with the absolute path to the Python executable in your virtual environment:

```json
{
  "mcpServers": {
    "sxs-control": {
      "command": "C:\\path\\to\\sxs-control\\.venv\\Scripts\\python.exe",
      "args": ["-X", "utf8", "-m", "sxs_control", "--stdio"]
    }
  }
}
```

A client that only accepts a cloud MCP URL cannot directly connect to this local version. CLI usage, configuration, and opt-in loopback HTTP are documented in [Configuration and connections](docs/CONFIGURATION.md#english-reference).

## Workspace and permissions

Initialization creates `~/SXSWorkspace`. File tools are restricted to this directory by default; configure `allowed_roots` to change it.

**Tools run with the current Windows user's permissions.** File-root checks apply to file tools. PowerShell, desktop input, app launches, and registry operations can affect other parts of the computer. Connect trusted clients and keep client-side approval for operations with side effects.

## Project status and contributions

The source version is **0.1.1 Alpha** and is still evolving. The automated suite contains 23 tests. See [validation coverage](docs/VALIDATION.md) for native-PC results, desktop limitations, and client compatibility limits.

| What you need | Where to go |
| --- | --- |
| Version changes | [Changelog](CHANGELOG.md) |
| Migration from the earlier local version | [Migration guide](docs/MIGRATION.md) |
| Report a problem or suggest a change | [Open an issue](https://github.com/wenmingsun60-bit/sxs-control/issues/new/choose) |
| Develop, test, or contribute code | [Contributing](CONTRIBUTING.md) |
| Understand permission boundaries | [Security](SECURITY.md) |

## Credits and license

Maintained by **Sun Wenming**. Earlier workflows used [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) and drew on [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP). Thanks to their authors.

New SXS source is [MIT licensed](LICENSE). Dependencies retain their own licenses. See [provenance](docs/PROVENANCE.md) and [third-party notices](THIRD_PARTY_NOTICES.md) for scope and attribution.
