# SXS Control

[English](README.en.md) · [首次运行与排错](docs/QUICKSTART.md) · [工具清单](docs/TOOLS.md) · [来源与许可证](docs/PROVENANCE.md) · [贡献指南](CONTRIBUTING.md)

面向本地 AI 客户端的 Windows 自动化工具集。通过 MCP stdio、命令行或可选的本机 HTTP 接口，访问截图、鼠标键盘、文件、进程、注册表和窗口辅助功能树。

**本机执行，无需 SXS 账号、云端网关、设备轮询或云端兜底。**访问网页只发生在明确调用网页抓取工具时。项目不包含模型，需要配合能调用本地工具的 AI 客户端。

当前源码版本 **0.1.1 / Alpha**。保留早期 SXS 本地版的 **39 个工具名称**，其中截图、点击和滚动包含兼容别名。开源版重新编写了适配代码，没有打包早期私有版本的云端实现和配置。部分参数校验比旧版本严格，见[迁移说明](docs/MIGRATION.md)。

0.1.1 修复了目录复制时对嵌套源路径和实际目标路径检查不完整的问题，并增加链接、循环路径和正常合并复制的回归测试。变更见 [CHANGELOG.md](CHANGELOG.md)。

## 安装

要求 Windows 10/11、交互式桌面、Python 3.10 或更高版本。推荐在独立虚拟环境安装。协议和文件操作测试也可以在 Linux 上运行，Windows 桌面工具需要 Windows。

```powershell
git clone https://github.com/wenmingsun60-bit/sxs-control.git
cd sxs-control
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m sxs_control init
.\.venv\Scripts\python.exe -m sxs_control doctor
```

`init` 创建当前用户的配置和 `~/SXSWorkspace` 工作目录。默认文件工具仅访问这个目录。已存在的配置不会被覆盖。尚未发布到 PyPI，请从仓库或源码包安装。

## 连接支持本地 MCP 的客户端

把下方配置放入客户端的 MCP 配置处，并将 Python 路径替换成实际安装路径：

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

这里只配置本地进程，不配置远程连接地址。仅支持云端 MCP URL 的客户端无法直接访问用户电脑的 localhost。Grok 等客户端需要具备本地执行能力，才能使用命令行入口；这不是已经完成的官方 Grok 集成。

## 命令行调用

在 Windows PowerShell 中，用标准输入传 JSON 可以避免引号被原生命令参数解析吃掉：

```powershell
'{}' | .\.venv\Scripts\python.exe -X utf8 -m sxs_control call windows_device_status --args-stdin
.\.venv\Scripts\python.exe -m sxs_control list
```

也可以使用 `--arguments-file args.json`。`scripts/sxs-local.ps1` 是本地命令行辅助入口。

## 配置

Windows 默认位置为 `%LOCALAPPDATA%\SXSControl\config.json`。用环境变量 `SXS_CONTROL_CONFIG` 或全局选项 `--config` 指定其他位置。仓库提供 `examples/config.example.json`，实际配置不要提交。

```json
{"allowed_roots": ["C:\\Users\\YourName\\SXSWorkspace"]}
```

`allowed_roots` 对所有文件工具生效，包括复制的两端、搜索和删除；它不是系统沙箱。PowerShell、启动程序、注册表和桌面输入仍然拥有当前 Windows 用户的权限。只把工具连接给受信任的客户端，并在客户端确认有副作用的操作。

## 可选本机 HTTP 接口

```powershell
.\.venv\Scripts\python.exe -m sxs_control http --port 18790
Invoke-RestMethod http://127.0.0.1:18790/health -Headers @{'X-SXS-Local'='1'}
```

仅绑定 `127.0.0.1`，提供 `GET /health`、`GET /tools`、`POST /call` 和 `POST /mcp`。请求必须带 `X-SXS-Local: 1`；POST 必须使用 `application/json`。服务检查 Host 并拒绝浏览器 Origin/CORS 请求。该固定请求头用于阻止网页误调用，**不是身份认证口令**；同一电脑上的其他进程仍可能访问服务。

默认端口 18790，便于与旧本机版并存。HTTP 为无会话的 JSON 响应模式，不提供 SSE、持久会话、远程认证或后台安装。优先使用 stdio；HTTP 客户端需要支持上述请求头和协议模式。

## 开发与验证

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_release.py
.\.venv\Scripts\python.exe scripts/windows_smoke.py
```

最后一个命令只在 Windows 上做状态、屏幕信息、辅助功能树和临时文件的检查，不操作键盘、剪贴板、现有文件或注册表。测试覆盖和已知限制见 [VALIDATION.md](docs/VALIDATION.md)。

## 致谢与许可

SXS Control 是由孙文明维护的 Windows 本地工具整合与适配项目。早期工作流使用过 [Windows-MCP](https://github.com/CursorTouch/Windows-MCP)，并参考过 [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP) 的工具组织。感谢这些项目及各运行时依赖的作者。

本仓库新增代码采用 [MIT](LICENSE)。已知上游版权声明保存在 `LICENSES/`；依赖保留各自许可证，详细范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。项目不代表 OpenAI、xAI、Microsoft 或上游项目，不承诺任何第三方资助申请会获批。

