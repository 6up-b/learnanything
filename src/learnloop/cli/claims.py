from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

claims_app = typer.Typer(no_args_is_help=True, help="Inspect, export, or delete local claim telemetry.")

@claims_app.command("export")
def claims_export(
    output: Annotated[Path | None, typer.Option("--output", help="Optional JSON output path.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Explicitly export the vault-local hypothesis event ledger."""

    payload = {"version": 1, "events": export_claim_events(_repository(_root(vault)))}
    rendered = jsonlib.dumps(payload, sort_keys=True, indent=2)
    if output is None:
        typer.echo(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    typer.echo(f"Exported {len(payload['events'])} claim events to {output}")

@claims_app.command("purge")
def claims_purge(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Delete all local hypothesis presentations and responses."""

    purged = purge_claim_events(_repository(_root(vault)))
    typer.echo(f"Purged {purged} claim events.")

__all__ = [name for name in globals() if not name.startswith("__")]
