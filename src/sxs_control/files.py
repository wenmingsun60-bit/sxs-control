"""Bounded file operations. These checks do not sandbox PowerShell or desktop apps."""

from __future__ import annotations

import fnmatch
import os
import shutil
from itertools import islice

from .config import checked_path


def info(path) -> dict:
    stat = path.stat()
    return {"path": str(path), "is_dir": path.is_dir(), "size": stat.st_size,
            "modified": int(stat.st_mtime)}


def check_directory_copy(source, target, cfg):
    """Preflight the paths copytree follows, including redirected destinations."""
    def visit(current, destination, ancestors):
        current = checked_path(str(current), cfg)
        checked_path(str(destination), cfg)
        if current in ancestors:
            raise ValueError("source contains a directory link cycle")
        if current == target or current in target.parents:
            raise ValueError("destination cannot be inside source, including linked directories")
        with os.scandir(current) as entries:
            for entry in entries:
                child = checked_path(entry.path, cfg)
                child_target = destination / entry.name
                checked_path(str(child_target), cfg)
                if entry.is_dir(follow_symlinks=True):
                    visit(child, child_target, ancestors + (current,))

    visit(source, target, ())


def run(action: str, cfg: dict, args: dict) -> dict:
    if action == "file_copy" or action == "file_move":
        source = checked_path(args["source"], cfg)
        target = checked_path(args["destination"], cfg)
        if source == target:
            raise ValueError("source and destination must differ")
        if source.is_dir() and source in target.parents:
            raise ValueError("destination cannot be inside source")
        if not source.exists():
            raise FileNotFoundError(str(source))
        if target.exists() and not args.get("overwrite", False):
            raise FileExistsError(str(target))
        if action == "file_copy":
            if source.is_dir():
                check_directory_copy(source, target, cfg)
            else:
                # copy2 appends the source name when the destination is a directory.
                checked_path(str(target / source.name if target.is_dir() else target), cfg)
        elif source.is_dir():
            for directory, names, filenames in os.walk(source):
                for name in names + filenames:
                    checked_path(str(source.__class__(directory) / name), cfg)
        target.parent.mkdir(parents=True, exist_ok=True)
        if action == "file_copy":
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=args.get("overwrite", False))
            else:
                shutil.copy2(source, target)
        else:
            if target.exists():
                if target.is_dir():
                    raise IsADirectoryError("move does not replace an existing directory")
                target.unlink()
            shutil.move(str(source), str(target))
        return {"source": str(source), "destination": str(target), "ok": True}

    if action == "file_search":
        root = checked_path(args["root"], cfg)
        if not root.is_dir():
            raise NotADirectoryError(str(root))
        matches = []
        limit = args.get("limit", 200)
        for directory, names, filenames in os.walk(root, followlinks=False):
            names[:] = [name for name in names if not (root.__class__(directory) / name).is_symlink()]
            for name in names + filenames:
                if fnmatch.fnmatch(name, args.get("pattern", "*")):
                    try:
                        path = checked_path(str(root.__class__(directory) / name), cfg)
                        matches.append(info(path))
                    except (OSError, PermissionError):
                        continue
                    if len(matches) >= limit:
                        return {"matches": matches, "truncated": True}
            if not args.get("recursive", True):
                break
        return {"matches": matches, "truncated": False}

    path = checked_path(args["path"], cfg)
    if action == "list_directory":
        if not path.is_dir():
            raise NotADirectoryError(str(path))
        items = []
        with os.scandir(path) as entries:
            for entry in islice(entries, 201):
                try:
                    item = info(checked_path(entry.path, cfg))
                    item["name"] = entry.name
                    items.append(item)
                except (OSError, PermissionError):
                    items.append({"name": entry.name, "unavailable": True})
        return {"path": str(path), "items": items[:200], "truncated": len(items) > 200}
    if action == "read_file":
        with path.open("rb") as stream:
            raw = stream.read(250_001)
        if len(raw) > 250_000:
            raise ValueError("text file exceeds 250000 bytes")
        try:
            content = raw.decode("utf-8-sig")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = raw.decode("gb18030")
            encoding = "gb18030"
        return {"path": str(path), "content": content, "encoding": encoding}
    if action == "write_file":
        if len(args["content"].encode("utf-8")) > 1_000_000:
            raise ValueError("text exceeds 1 MB")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a" if args.get("append", False) else "w", encoding="utf-8", newline="") as stream:
            stream.write(args["content"])
        return {"path": str(path), "ok": True}
    if action == "file_info":
        return {**info(path), "exists": True}
    if action == "file_delete":
        if path in [path.__class__(root).resolve() for root in cfg["allowed_roots"]]:
            raise PermissionError("cannot delete an allowed root itself")
        if path.is_dir():
            if args.get("recursive", False):
                shutil.rmtree(path)
            else:
                path.rmdir()
        else:
            path.unlink()
        return {"path": str(path), "deleted": True}
    raise ValueError("unsupported file action")

