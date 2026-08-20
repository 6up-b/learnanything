from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

surfaces_app = typer.Typer(
    no_args_is_help=True, help="Inspect activity-surface exposure and burn history (P0.4 §5)."
)

@surfaces_app.command("audit")
def surfaces_audit(
    surface_id: Annotated[str, typer.Argument(help="Surface id.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """A surface's full reserve->expose->consume->quarantine->retire timeline plus
    the current held-out eligibility verdict."""

    from learnloop.substrate.activities import evaluate_held_out_eligibility

    _, repository = _contracts_env(vault)
    surface = repository.fetch_surface(surface_id)
    if surface is None:
        typer.echo(_dump({"version": 1, "error": "unknown_surface", "surface_id": surface_id}))
        raise typer.Exit(code=1)
    exposures = repository.exposures_for_surface(surface_id)
    lifecycle = repository.surface_lifecycle_history(surface_id)
    eligibility = evaluate_held_out_eligibility(repository, surface=surface, purpose="assessment")
    typer.echo(
        _dump(
            {
                "version": 1,
                "surface_id": surface_id,
                "surface_hash": surface.get("surface_hash"),
                "fingerprint": surface.get("fingerprint"),
                "exposures": [
                    {"kind": e["kind"], "purpose": e["purpose"],
                     "consumes_unseen": e["consumes_unseen"], "created_at": e["created_at"]}
                    for e in exposures
                ],
                "lifecycle": [
                    {"kind": e["kind"], "reason": e.get("reason"), "created_at": e["created_at"]}
                    for e in lifecycle
                ],
                "current_eligibility": eligibility.as_dict(),
            }
        )
    )

@surfaces_app.command("retire")
def surfaces_retire(
    surface_id: Annotated[str, typer.Argument(help="Surface id to retire.")],
    reason: Annotated[str, typer.Option("--reason", help="Taxonomy retirement reason (§3.7/§3.8).")],
    scope: Annotated[str, typer.Option("--scope", help="surface | card | family.")] = "surface",
    provenance: Annotated[str, typer.Option("--provenance")] = "owner_tooling",
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Retire a bad prompt from the CLI with a taxonomy reason (Journey 12, §5).

    Deletes NOTHING: learner state and facet evidence survive; the reason lands in
    ``interaction_events`` and a ``retirement_records`` row (§3.7/§3.8). Thin adapter
    over the P0.1 retire_with_reason service."""

    from learnloop.substrate.activities import retire_with_reason

    _, repository = _contracts_env(vault)
    record_id = retire_with_reason(
        repository, scope=scope, reason=reason, provenance=provenance, surface_id=surface_id,
    )
    typer.echo(_dump({"version": 1, "retirement_record_id": record_id, "surface_id": surface_id, "reason": reason}))

__all__ = [name for name in globals() if not name.startswith("__")]
