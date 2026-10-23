"""Configuration belongs to the user, outside the installed source package."""

from __future__ import annotations

import json
import os
from pathlib import Path


def config_path() -> Path:
    value = os.environ.get("SXS_CONTROL_CONFIG")
    if value:
        return Path(value).expanduser().resolve()
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".config")
    return base / "SXSControl" / "config.json"


def load_config(path: Path | None = None) -> dict:
    path = path or config_path()
    if path.exists():
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("configuration must be a JSON object")
    else:
        value = {"allowed_roots": [str(Path.home() / "SXSWorkspace")]}
    roots = value.get("allowed_roots")
    if not isinstance(roots, list) or not roots:
        raise ValueError("allowed_roots must be a non-empty list")
    cleaned = []
    for root in roots:
        if not isinstance(root, str) or not root.strip():
            raise ValueError("each allowed root must be a non-empty absolute path")
        p = Path(os.path.expandvars(root)).expanduser()
        if not p.is_absolute():
            raise ValueError("each allowed root must be absolute")
        cleaned.append(str(p.resolve()))
    # Cloud settings from old installations are deliberately not consumed.
    return {"allowed_roots": cleaned}


def checked_path(value: str, cfg: dict) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("an absolute path is required")
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        raise ValueError("an absolute path is required")
    path = path.resolve()
    for root in cfg["allowed_roots"]:
        try:
            path.relative_to(Path(root).resolve())
            return path
        except ValueError:
            pass
    raise PermissionError("path is outside allowed_roots")

