"""Read-only CLI view of the capture inbox."""
from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

inbox_app = typer.Typer(no_args_is_help=True, help="Captured references waiting for desktop routing.")


@inbox_app.command("list")
def inbox_list(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    all_states: Annotated[bool, typer.Option("--all", help="Include routed, dismissed and purged captures.")] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 100,
    offset: Annotated[int, typer.Option("--offset", min=0)] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List captures newest first; listing never starts processing or practice."""
    from learnloop.capture import list_captures

    rows = list_captures(_repository(_root(vault)), status=None if all_states else "new", limit=limit, offset=offset)
    if json_output:
        typer.echo(_dump({"version": 1, "captures": rows}))
        return
    if not rows:
        typer.echo("No captures.")
    for row in rows:
        preview = " ".join((row.get("text") or row.get("url") or row.get("note") or "").split())
        typer.echo(f"{row['capture_id']} [{row['status']}] {row['kind']} {preview[:120]}")
