# SXS Control

[简体中文](README.md) · [Provenance](docs/PROVENANCE.md) · [Tool reference](docs/TOOLS.md) · [Validation](docs/VALIDATION.md)

Local Windows automation for AI clients: 39 MCP tool names covering screenshots, mouse and keyboard, files, processes, registry, windows and accessibility trees. Some names are compatibility aliases. The current source version is 0.1.1 (alpha).

0.1.1 checks nested source paths and effective destination paths before copying a directory, including paths redirected by links. Regression coverage includes rejected escapes, cycles, and successful ordinary copies. See [CHANGELOG.md](CHANGELOG.md).

Run through MCP stdio, the CLI, or opt-in loopback HTTP. No SXS account, cloud gateway, polling, telemetry or cloud fallback is built in. The URL-fetching tool makes network requests only when called. This project does not include an AI model.

## Install

Windows 10/11, an interactive desktop, Python 3.10+. Source installation only; no PyPI release is claimed.

```powershell
git clone https://github.com/wenmingsun60-bit/sxs-control.git
cd sxs-control
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m sxs_control init
.\.venv\Scripts\python.exe -m sxs_control doctor
```

Configure an MCP client to launch the virtual environment's Python with arguments `-X utf8 -m sxs_control --stdio`. See `examples/mcp-stdio.json`. A cloud-only connector cannot reach your computer's localhost. A client such as Grok must offer local execution to use the CLI; official Grok integration is not claimed.

```powershell
'{}' | .\.venv\Scripts\python.exe -X utf8 -m sxs_control call windows_device_status --args-stdin
```

The default configuration is `%LOCALAPPDATA%\SXSControl\config.json`, with `~/SXSWorkspace` as the only allowed file root. Override the config location with `SXS_CONTROL_CONFIG` or `--config`. File-root checks are not a sandbox for PowerShell, launched programs, registry or desktop input. These tools act with the current Windows user's permissions.

## Optional local HTTP

`sxs-control http --port 18790` binds only to `127.0.0.1`. Every request requires `X-SXS-Local: 1`. JSON POST endpoints are `/call` and `/mcp`; GET endpoints are `/health` and `/tools`. Host checking, browser-Origin rejection and no CORS prevent ordinary cross-site browser calls. The fixed header is not authentication against other local processes. No SSE, persistent sessions, remote authorization or automatic startup is provided.

## Development

```text
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_release.py
python scripts/windows_smoke.py
```

The Windows smoke test reads local system/UI metadata and exercises file operations only inside a temporary directory. It does not click, type, replace clipboard content or modify existing files or registry entries. See the validation report for exact coverage and limitations.

## Attribution

Maintained by Sun Wenming. Earlier SXS workflows used Windows-MCP and drew on Desktop Commander workflows. The public adapter is newly organized and does not ship the private prototype scripts or their cloud deployment code. Known upstream notices are retained in `LICENSES/`; runtime dependencies keep their own licenses. See `THIRD_PARTY_NOTICES.md` and `docs/PROVENANCE.md`.

MIT for the new SXS source. No affiliation with OpenAI, xAI, Microsoft or the referenced upstream projects is implied.

