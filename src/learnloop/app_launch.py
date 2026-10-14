"""Application-level launchers shared by entry-point adapters."""

from __future__ import annotations

from pathlib import Path


def launch_tui(vault_root: Path) -> None:
    """Launch the Textual frontend without coupling another adapter to it."""

    from learnloop.tui.app import run

    run(Path(vault_root))


def serve_mcp(vault_root: Path, **options) -> None:
    """Serve the vault to chat hosts over MCP (spec_mcp_frontend_c1).

    The ``learnloop_mcp`` adapter and the SDK it needs (the optional ``mcp``
    extra) load only here, so the CLI stays independent of them; the one
    exempted import edge is named in the ``domain-does-not-import-mcp``
    import-linter contract."""

    from learnloop_mcp.cli import serve

    serve(Path(vault_root), **options)


__all__ = ["launch_tui", "serve_mcp"]
