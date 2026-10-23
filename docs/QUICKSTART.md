# 首次运行与排错

先在 Windows 10/11 上验证命令行，再连接支持本地 MCP stdio 的客户端。以下命令在仓库根目录的 PowerShell 中执行。完整环境和测试范围见 [验证记录](VALIDATION.md)。

## 安装并检查环境

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m sxs_control --version
.\.venv\Scripts\python.exe -m sxs_control init
.\.venv\Scripts\python.exe -m sxs_control doctor
```

当前源码的版本输出应为 `0.1.1`。`doctor` 应报告 `ok: true`、`tool_count: 39`、`mode: local-only`，且四个依赖都有版本号。它确认平台、配置可解析和依赖可发现，不代表所有桌面动作都已验证。

`init` 只在首次使用时运行。若提示 `configuration already exists`，保留已有配置并继续执行 `doctor`；不要为重新安装而删除配置。

## 确认第一个调用成功

```powershell
.\.venv\Scripts\python.exe -m sxs_control list |
    ConvertFrom-Json | Select-Object version, count
'{}' | .\.venv\Scripts\python.exe -X utf8 -m sxs_control call windows_device_status --args-stdin
```

工具列表应显示 `count: 39`。状态调用的外层结果应显示 `isError: false`，此调用不点击、输入或修改注册表。PowerShell 中优先使用 `--args-stdin` 传 JSON；含中文的复杂参数可存成 UTF-8 JSON 文件后使用 `--arguments-file`，避免原生命令参数与管道编码问题。

如需检查临时文件读写和本机调用，可运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/windows_smoke.py --skip-ui
```

不带 `--skip-ui` 时还会读取显示器信息及最多三个辅助功能元素，需要可访问的交互式桌面。两种模式都不点击、输入或改变剪贴板；文件操作仅在新建的临时目录内进行。

## 接入本地客户端

使用 [mcp-stdio.json](../examples/mcp-stdio.json)，将 `command` 替换为刚才虚拟环境中 Python 的绝对路径，参数保持 `-X utf8 -m sxs_control --stdio`。同一 Python 路径下，命令行状态调用应先成功。

`--stdio` 是等待客户端请求的服务入口，手动启动后没有提示语属于正常现象。它的 stdout 专用于 JSON-RPC。仅接收云端 MCP URL 的客户端无法直接启动这一本地进程。

## 常见问题

| 现象 | 检查方式 |
| --- | --- |
| 找不到 `py` 或 Python | 先准备 Python 3.10 或更高版本；创建虚拟环境后，所有命令使用同一个 `.venv\Scripts\python.exe`。 |
| `doctor` 中某个依赖为 `null` | 用上述虚拟环境的 Python 重新执行 `-m pip install .`，确认安装没有报错。 |
| 命令行能运行，客户端提示找不到模块 | 核对客户端 `command` 是否指向相同的 Python 绝对路径。 |
| 读取文件提示 `outside allowed_roots` | 在 `doctor` 中确认允许目录；默认是 `~/SXSWorkspace`。复制会检查源文件、实际目标文件和递归涉及的路径。 |
| 复制目录提示链接循环或目标位于源内 | 改用不包含循环、也不写入自身子目录的源和目标；允许范围内的普通目录链接仍可复制。 |
| 桌面标签找不到或界面没有响应 | 先确认桌面可交互，再读取新的 UI 快照；按最新标签操作。命令行成功不等于所有应用的 UI 自动化都兼容。 |

## 提交能复现的反馈

使用仓库的 Bug report 模板，填写 SXS、Windows、Python、PowerShell 和客户端版本、调用方式、最小步骤、预期与实际结果。明确哪些步骤成功、从哪一步开始失败。提供脱敏后的错误文字；不要上传真实配置、凭据、私人截图或完整日志。
