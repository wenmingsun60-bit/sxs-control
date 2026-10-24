# 配置与连接方式

先按 [README](../README.md) 完成安装和状态查询，再选择适合客户端的连接方式。

## 工作目录

Windows 默认配置位于 `%LOCALAPPDATA%\SXSControl\config.json`。首次运行 `init` 时创建配置及 `~/SXSWorkspace` 工作目录；已有配置会保留。

允许文件工具访问其他目录时，修改 `allowed_roots`，使用实际存在或计划使用的绝对路径：

```json
{"allowed_roots": ["C:\\Users\\YourName\\SXSWorkspace"]}
```

配置示例见 [config.example.json](../examples/config.example.json)。可用环境变量 `SXS_CONTROL_CONFIG` 或全局选项 `--config` 指定其他配置文件。路径检查覆盖所有文件工具，包括复制的源和实际目标路径；它不是 PowerShell、桌面操作或应用程序的系统沙箱。

## MCP stdio

让客户端启动虚拟环境中的 Python，并传入 `-X utf8 -m sxs_control --stdio`。完整示例见 [mcp-stdio.json](../examples/mcp-stdio.json)。该服务等待客户端请求，stdout 仅输出 JSON-RPC。

这里只配置本机进程，不配置远程服务器地址。只接收云端 MCP URL 的客户端无法直接启动这个进程。Grok 等客户端需要具备本地执行能力；本项目没有声明完成官方 Grok 集成。

## 命令行

在仓库根目录的 PowerShell 中执行：

```powershell
'{}' | .\.venv\Scripts\python.exe -X utf8 -m sxs_control call windows_device_status --args-stdin
.\.venv\Scripts\python.exe -m sxs_control list
```

`--args-stdin` 从标准输入读取 JSON，减少 PowerShell 原生命令参数中的引号问题。复杂或含中文的参数可写入 UTF-8 JSON 文件，再通过 `--arguments-file args.json` 读取。`scripts/sxs-local.ps1` 提供命令行辅助入口。

## 可选本机 HTTP 接口

仅当客户端需要 HTTP 时启动：

```powershell
.\.venv\Scripts\python.exe -m sxs_control http --port 18790
Invoke-RestMethod http://127.0.0.1:18790/health -Headers @{'X-SXS-Local'='1'}
```

| 接口 | 用途 |
| --- | --- |
| `GET /health` | 查询服务状态 |
| `GET /tools` | 列出工具 |
| `POST /call` | 调用工具 |
| `POST /mcp` | 接收 MCP JSON 请求 |

服务只绑定 `127.0.0.1`，默认端口为 `18790`。所有请求需带 `X-SXS-Local: 1`；POST 使用 `application/json`。服务检查 Host、拒绝浏览器 Origin/CORS 请求，以阻止普通网页跨站调用。

固定请求头不是身份认证口令，同一电脑上的其他进程仍可能访问服务。HTTP 采用无会话的 JSON 响应，不提供 SSE、持久会话、远程认证或自动启动。通常优先使用 stdio。

## English reference

- **Config:** `%LOCALAPPDATA%\SXSControl\config.json`; override with `SXS_CONTROL_CONFIG` or the global `--config` option. Initialization creates `~/SXSWorkspace`, the default allowed file root. Existing configuration is preserved.
- **MCP stdio:** launch the virtual environment's Python with `-X utf8 -m sxs_control --stdio`. Use [mcp-stdio.json](../examples/mcp-stdio.json). Cloud-only connectors cannot launch a local process. Clients such as Grok need local execution; official integration is not claimed.
- **CLI:** use `call TOOL --args-stdin` with JSON on stdin, or `--arguments-file args.json` for a UTF-8 JSON file. `list` prints the tool catalog. See the commands above and `scripts/sxs-local.ps1`.
- **HTTP:** opt in with `http --port 18790`. The server binds to `127.0.0.1`; GET endpoints are `/health` and `/tools`, and JSON POST endpoints are `/call` and `/mcp`. Every request requires `X-SXS-Local: 1`. Host checks, Origin rejection, and no CORS block ordinary cross-site browser calls. This fixed header does not authenticate other local processes. SSE, persistent sessions, remote authorization, and automatic startup are not provided.
- **Scope:** file-root checks apply to file operations, including effective copy destinations. They are not an OS sandbox for PowerShell, launched apps, desktop input, or the registry. Use trusted clients and retain approval for operations with side effects.

Computer operations run locally without an SXS account, cloud gateway, polling, telemetry, or cloud fallback built into this package. The URL-fetching tool makes network requests when called. Your AI client separately determines its model's network use and the information sent to it.
