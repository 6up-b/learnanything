"""Application-level launchers shared by entry-point adapters."""

from __future__ import annotations

from pathlib import Path


def launch_tui(vault_root: Path) -> None:
    """Launch the Textual frontend without coupling another adapter to it."""

    from learnloop.tui.app import run

    run(Path(vault_root))


__all__ = ["launch_tui"]
