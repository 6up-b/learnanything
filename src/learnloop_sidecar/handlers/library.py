from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

# Directories never worth surfacing in the Library tree.
_IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", ".mypy_cache"}
_MAX_FILE_BYTES = 512 * 1024


def _kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".yaml", ".yml"}:
        return "yaml"
    if ext in {".md", ".markdown"}:
        return "md"
    if ext == ".toml":
        return "toml"
    if ext == ".json":
        return "json"
    if ext == ".txt":
        return "text"
    if ext in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    if ext in {".cfg", ".ini"}:
        return "text"
    return "binary"


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _build_tree(directory: Path, root: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if child.is_dir():
            if child.name in _IGNORE_DIRS:
                continue
            nodes.append(
                {
                    "type": "dir",
                    "name": child.name,
                    "path": _relative(child, root),
                    "children": _build_tree(child, root),
                }
            )
        else:
            nodes.append(
                {
                    "type": "file",
                    "name": child.name,
                    "path": _relative(child, root),
                    "kind": _kind(child),
                }
            )
    return nodes


@method("get_vault_tree")
def get_vault_tree(ctx: SidecarContext, _params) -> dict[str, Any]:
    """The on-disk vault file tree for the Library screen."""

    vault, _repository = ctx.require_vault()
    root = vault.root.resolve()
    return versioned({"root": str(root), "tree": _build_tree(root, root)})


def _resolve_in_vault(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise SidecarError("invalid_path", "Path escapes the vault root.")
    return target


class ReadFileInput(ParamsModel):
    path: str


@method("read_vault_file", ReadFileInput)
def read_vault_file(ctx: SidecarContext, params: ReadFileInput) -> dict[str, Any]:
    """Read a single vault file, sandboxed to the vault root.

    Binary files (e.g. ``state.sqlite``) and oversized files return metadata with a
    null body rather than dumping bytes into the UI.
    """

    vault, _repository = ctx.require_vault()
    root = vault.root.resolve()
    target = _resolve_in_vault(root, params.path)
    if not target.is_file():
        raise SidecarError("not_found", f"{params.path} is not a file in the vault.")

    kind = _kind(target)
    size = target.stat().st_size
    base = {
        "path": _relative(target, root),
        "name": target.name,
        "kind": kind,
        "size": size,
        "editable": kind not in {"binary", "sqlite"},
        "database": kind == "sqlite",
    }
    # SQLite databases are edited through the dedicated table browser / SQL console
    # (see sqlite_admin.py), never as text — so we hand back metadata with the
    # ``database`` flag set and no body.
    if kind == "sqlite":
        return versioned({**base, "binary": False, "truncated": False, "body": None})
    if kind == "binary":
        return versioned({**base, "binary": True, "truncated": False, "body": None})
    if size > _MAX_FILE_BYTES:
        return versioned({**base, "binary": False, "truncated": True, "body": None})
    body = target.read_text(encoding="utf-8", errors="replace")
    return versioned({**base, "binary": False, "truncated": False, "body": body})


class WriteFileInput(ParamsModel):
    path: str
    body: str


@method("write_vault_file", WriteFileInput)
def write_vault_file(ctx: SidecarContext, params: WriteFileInput) -> dict[str, Any]:
    """Overwrite an existing text file in the vault, sandboxed to the vault root.

    Refuses binary files and creating new paths — this is an editor for the files
    the tree already surfaces, not a general write primitive. Returns the saved
    content so the caller can refresh in place.
    """

    vault, _repository = ctx.require_vault()
    root = vault.root.resolve()
    target = _resolve_in_vault(root, params.path)
    if not target.is_file():
        raise SidecarError("not_found", f"{params.path} is not a file in the vault.")
    kind = _kind(target)
    if kind in {"binary", "sqlite"}:
        raise SidecarError("not_editable", f"{params.path} is a {kind} file and cannot be edited as text.")

    target.write_text(params.body, encoding="utf-8")
    return versioned(
        {
            "path": _relative(target, root),
            "name": target.name,
            "kind": kind,
            "size": target.stat().st_size,
            "editable": True,
            "binary": False,
            "truncated": False,
            "database": False,
            "body": params.body,
        }
    )


class CreateFileInput(ParamsModel):
    path: str
    body: str = ""


@method("create_vault_file", CreateFileInput)
def create_vault_file(ctx: SidecarContext, params: CreateFileInput) -> dict[str, Any]:
    """Create a new text file in the vault (e.g. a markdown note), sandboxed to the root.

    Refuses paths that already exist and non-text kinds (binary/sqlite); parent
    directories inside the vault are created as needed. Returns the new file's
    content in the same shape as :func:`read_vault_file` so the caller can open it
    straight into the editor.
    """

    vault, _repository = ctx.require_vault()
    root = vault.root.resolve()
    target = _resolve_in_vault(root, params.path)
    if target.exists():
        raise SidecarError("already_exists", f"{params.path} already exists in the vault.")
    kind = _kind(target)
    if kind in {"binary", "sqlite"}:
        raise SidecarError("not_editable", f"Cannot create a {kind} file as text.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(params.body, encoding="utf-8")
    return versioned(
        {
            "path": _relative(target, root),
            "name": target.name,
            "kind": kind,
            "size": target.stat().st_size,
            "editable": True,
            "binary": False,
            "truncated": False,
            "database": False,
            "body": params.body,
        }
    )
