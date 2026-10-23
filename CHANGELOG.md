# Changelog

## 0.1.1 — Unreleased

- Fixed recursive copies checking only the top-level destination. All effective destination paths are checked before copying, including a source filename appended to an existing directory.
- Checked descendants reached through source directory links, rejected directory cycles and destinations inside linked source directories, and preserved ordinary merges and allowed internal links.
- Added eight regression tests. Four focused escape cases reproduced the defect on 0.1.0 and pass with the fix; all 23 tests pass locally on Linux.
- Added first-run success criteria and troubleshooting guidance, and expanded the bug report template to capture reproducible environment and client details.
- File checks remain subject to concurrent filesystem changes; this is not an OS sandbox or a formal security audit.

## 0.1.0 — 2026-10-23

- Initial public alpha release of SXS Control, preserving 39 local tool names including compatibility aliases.
- Reimplemented package structure, MCP stdio adapter, CLI and opt-in loopback JSON HTTP adapter.
- Added explicit configuration, file-root checks, parameter validation and Host/Origin/header checks for HTTP.
- Added provenance and third-party notices, Chinese/English documentation, contributor guidance and validation checks.
- No cloud deployment, account system, private configuration or old runtime history is included.

