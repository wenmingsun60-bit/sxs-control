<h1 align="center">SXS Control</h1>

<p align="center"><strong>让 AI 在你的 Windows 电脑上动手做事</strong></p>
<p align="center">查看界面 · 操作应用 · 整理文件</p>

<p align="center">
  <a href="#开始使用">开始使用</a> ·
  <a href="docs/TOOLS.md">工具清单</a> ·
  <a href="docs/QUICKSTART.md">遇到问题</a> ·
  <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/wenmingsun60-bit/sxs-control/actions/workflows/ci.yml"><img src="https://github.com/wenmingsun60-bit/sxs-control/actions/workflows/ci.yml/badge.svg?branch=main" alt="自动化检查状态"></a>
  &nbsp; 本机执行 · <a href="LICENSE">MIT 许可</a> · 0.1.1 Alpha
</p>

SXS Control 把截图、鼠标键盘和文件操作，接入支持本地工具调用的 AI 助手。**AI 助手理解你的请求，SXS Control 在当前电脑上执行操作。**

电脑操作在本机完成。你使用的 AI 模型是否联网、会接收哪些内容，由所连接的客户端决定。

## 能帮你做什么

| 你要完成的事 | 提供的能力 |
| --- | --- |
| 查看当前界面 | 获取屏幕截图、窗口信息和可访问控件，为 AI 提供操作依据。 |
| 操作桌面应用 | 点击、输入、滚动、快捷键，以及可访问控件操作。 |
| 整理本地文件 | 在允许目录内查找、读取、写入、复制、移动和删除文件。 |
| 排查系统状态 | 查看进程、执行 PowerShell，按需要读写注册表。 |

共提供 **39 个工具入口**，包含部分兼容别名。具体参数见[完整工具清单](docs/TOOLS.md)。

## 开始使用

需要 **Windows 10/11、Python 3.10 或更高版本，以及 Git**。桌面操作需要电脑处于可正常交互的状态。目前采用源码安装。

### 1. 安装并检查环境

在 PowerShell 中依次执行：

```powershell
git clone https://github.com/wenmingsun60-bit/sxs-control.git
cd sxs-control
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m sxs_control init
.\.venv\Scripts\python.exe -m sxs_control doctor
```

`doctor` 显示 `ok: true`、`tool_count: 39`，且依赖都有版本号，表示环境检查通过。已有配置的用户跳过 `init`，保留原有设置。

### 2. 试一次电脑状态查询

```powershell
'{}' | .\.venv\Scripts\python.exe -X utf8 -m sxs_control call windows_device_status --args-stdin
```

结果中的 `isError: false` 表示调用成功。这一步只查询状态，方便你先确认工具能够运行。

### 3. 接入你的 AI 助手

客户端需要支持在本机启动工具进程，通常通过 **MCP stdio** 连接。把下方配置加入客户端，并将 `command` 替换为刚才虚拟环境中 Python 的实际路径：

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

只接受云端 MCP 链接的客户端，无法直接连接这份本地版本。命令行和本机 HTTP 的用法见[配置与连接方式](docs/CONFIGURATION.md)。

安装报错、依赖缺失或连接失败，请看[首次运行与排错](docs/QUICKSTART.md)。

## 工作目录与权限

首次初始化会创建 `~/SXSWorkspace`，文件工具默认只访问这个目录。可以在配置中调整允许目录，具体方法见[配置说明](docs/CONFIGURATION.md#工作目录)。

**工具以当前 Windows 用户的权限运行。** 文件目录限制只约束文件工具；PowerShell、鼠标键盘、应用启动和注册表操作可以影响目录之外的内容。请连接受信任的客户端，并在客户端确认有副作用的操作。

## 项目进展与参与

当前源码为 **0.1.1 Alpha**，仍在完善。自动化测试包含 23 项用例；真实电脑、桌面操作和不同客户端的验证范围见[验证记录](docs/VALIDATION.md)。

| 你想了解的内容 | 从这里开始 |
| --- | --- |
| 版本改了什么 | [更新日志](CHANGELOG.md) |
| 从早期本地版迁移 | [迁移说明](docs/MIGRATION.md) |
| 报告问题或提出建议 | [提交 Issue](https://github.com/wenmingsun60-bit/sxs-control/issues/new/choose) |
| 开发、测试或贡献代码 | [贡献指南](CONTRIBUTING.md) |
| 了解权限与安全边界 | [安全说明](SECURITY.md) |

## 致谢与许可

由 **孙文明（Sun Wenming）**维护。早期工作流使用过 [Windows-MCP](https://github.com/CursorTouch/Windows-MCP)，并参考过 [Desktop Commander](https://github.com/wonderwhy-er/DesktopCommanderMCP) 的工具组织，感谢上游作者。

本仓库新增代码采用 [MIT 许可](LICENSE)，外部依赖保留各自许可证。代码来源和许可范围见[来源说明](docs/PROVENANCE.md)与[第三方声明](THIRD_PARTY_NOTICES.md)。
