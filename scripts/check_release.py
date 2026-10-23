"""Check the source publication boundary; never print matched secret values."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sxs_control.catalog import TOOLS

BLOCKED = {"config.json", "agent.log", "windows-control-agent.py", "windows_control_mcp_schema_source.py"}
PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})"),
    "api-token": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}"),
    "credential-literal": re.compile(r'''(?i)(?:api[_-]?key|password|client[_-]?secret|device[_-]?token)\s*[=:]\s*["'][^"'\n]{12,}["']'''),
}
EXCLUDED = {".git", ".venv", "venv", "__pycache__", "build", "dist"}


def main():
    candidates = [p for p in ROOT.rglob("*") if p.is_file() and not any(part in EXCLUDED or part.endswith(".egg-info") for part in p.relative_to(ROOT).parts)]
    problems = []
    for path in candidates:
        rel = str(path.relative_to(ROOT))
        if path.name in BLOCKED or path.suffix.lower() in (".pem", ".key", ".pfx", ".p12", ".log") or ".bak" in path.name:
            problems.append({"file": rel, "rule": "private-runtime-file"})
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            problems.append({"file": rel, "rule": "unexpected-binary"})
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                problems.append({"file": rel, "rule": label})
    for required in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md", "README.en.md", "SECURITY.md", "CONTRIBUTING.md", "docs/PROVENANCE.md"):
        if not (ROOT / required).is_file():
            problems.append({"file": required, "rule": "missing-release-file"})
    if len(TOOLS) != 39:
        problems.append({"rule": "tool-contract-count"})
    print(json.dumps({"ok": not problems, "files_checked": len(candidates), "tool_count": len(TOOLS), "problems": problems}, ensure_ascii=False))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())

