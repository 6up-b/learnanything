"""An explicit mark on the owner's live working vaults (storage S0).

Before S0 a working vault was recognised by git tracking its database
(``fixtures/linear_algebra``, ``probability``, ``arxiv_v2``), and
``learnloop ai compare`` refused to write receipts and judgments into one in
place. S0 moves those vaults out of the checkout to ``~/learnloop-vaults/``,
where git tracks nothing, so ``scripts/s0_landing.py move-out`` marks each one
here instead (Codex review of S0, F3).

The mark names the vault it was written for: its resolved path and its
directory's device and inode. A vault is a working vault when either still
matches, so renaming the live vault keeps it marked (a rename keeps the
inode), while a copy that carries the file along (a backup-API copy, a
``--copy-from`` copy, ``cp -a``) is a different directory and is not. A mark
that cannot be read counts as a working vault: the check fails closed.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

MARKER_PARTS = (".learnloop", "working-vault.json")


def marker_path(root: Path) -> Path:
    return Path(root).joinpath(*MARKER_PARTS)


def mark_working_vault(root: Path, *, reason: str) -> Path:
    """Mark ``root`` as a live working vault (idempotent; rewrites the identity)."""

    root = Path(root).resolve()
    status = os.stat(root)
    path = marker_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "path": str(root),
        "device": status.st_dev,
        "inode": status.st_ino,
        "reason": reason,
        "marked_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
    }
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def working_vault_marker_reason(root: Path) -> str | None:
    """Why ``root`` is a marked live working vault, or None (no mark, or a copy's)."""

    root = Path(root).resolve()
    path = marker_path(root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        marked_path = str(payload["path"])
        device, inode = int(payload["device"]), int(payload["inode"])
        reason = str(payload.get("reason") or "marked as a live working vault")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return f"its working-vault mark {path} could not be read ({type(exc).__name__}), so it is treated as one"
    status = os.stat(root)
    if marked_path == str(root) or (status.st_dev, status.st_ino) == (device, inode):
        return f"{reason} (marked in {path})"
    return None


__all__ = ["MARKER_PARTS", "mark_working_vault", "marker_path", "working_vault_marker_reason"]
