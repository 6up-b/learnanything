from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

controller_app = typer.Typer(
    no_args_is_help=True,
    help="Staged-controller inspection: the open-world §14.1 dependency gate.",
)

@controller_app.command("open-world-gate")
def controller_open_world_gate(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON gate report.")] = False,
) -> None:
    """Evaluate the six §14.1 dependency conditions that gate open-world HypothesisCard
    expansion. Open-world is intentionally LAST and is NOT implemented; this check makes
    the deferral inspectable. Exit non-zero while the gate is NOT MET (CI-usable): no
    expansion worker or successor-set UI may be enabled until every condition passes."""

    from learnloop.scheduling import open_world_gate as owg

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    report = owg.evaluate_gate(loaded, repository)
    if json_output:
        typer.echo(_dump(report.as_dict()))
    else:
        typer.echo(
            "Open-world dependency gate (§14.1): "
            + ("MET" if report.met else "NOT MET")
        )
        typer.echo(f"  open_world_schema_present: {report.open_world_schema_present}")
        for condition in report.conditions:
            mark = "PASS" if condition.met else "GAP "
            typer.echo(f"  [{mark}] {condition.spec_ref} {condition.key}: {condition.detail}")
        typer.echo(f"  -> {report.as_dict()['enablement']}")
    if not report.met:
        raise typer.Exit(code=1)

__all__ = [name for name in globals() if not name.startswith("__")]
