from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

grading_app = typer.Typer(
    no_args_is_help=True, help="Adjudication queue: pending reviews, adjudicate, measurement receipt."
)

@grading_app.command("reviews")
def grading_reviews(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List pending grade reviews, influence-ordered (§5). Reads P0.2 review flags
    and quarantine state; quarantined first, then influence-flagged, then oldest."""

    root = _root(vault)
    repository = _repository(root)
    rows = repository.pending_grade_reviews()
    if json_output:
        typer.echo(_dump({"version": 1, "reviews": rows}))
        return
    if not rows:
        typer.echo("No pending grade reviews.")
        return
    for r in rows:
        typer.echo(
            f"{r['id']}\tobs={r.get('observation_id')}\tquarantine={r.get('quarantine_state')}"
            f"\tinfluence={r.get('influence_flag')}\treview={r.get('review_flag')}"
        )

@grading_app.command("adjudicate")
def grading_adjudicate(
    interpretation_id: Annotated[str, typer.Argument(help="Grade interpretation id (from `grading reviews`).")],
    resolved_class: Annotated[str | None, typer.Option("--resolved-class")] = None,
    source: Annotated[str, typer.Option("--source", help="human_owner|independent_expert|learner_clarification|deterministic_key")] = "human_owner",
    rationale: Annotated[str | None, typer.Option("--rationale")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Adjudicate one grade append-only (§4.4/§5): appends a new interpretation head,
    repoints the observation, emits measurement events, and rebuilds projections.
    Never overwrites raw history. Thin adapter over the P0.2 append_adjudication."""

    from learnloop.attempts.grade_resolution import append_adjudication
    from learnloop.substrate.p0_projection import record_reinterpretation_if_changed
    from learnloop.vault.loader import load_vault

    root = _root(vault)
    repository = _repository(root)
    interp = repository.grade_interpretation(interpretation_id)
    if interp is None:
        typer.echo(f"No grade interpretation {interpretation_id!r}.")
        raise typer.Exit(code=1)
    observation_id = interp["observation_id"]
    administration_id = interp["administration_id"]
    raws = repository.raw_grade_events_for_observation(observation_id)
    adj = append_adjudication(
        repository,
        observation_id=observation_id,
        administration_id=administration_id,
        reviewed_raw_event_ids=[r["id"] for r in raws],
        adjudicator_source=source,
        resolved_class=resolved_class,
        rationale=rationale,
        # Ruling A: a direction flip must land as a superseding grading_evidence
        # revision; the vault supplies rubric points where contract lineage is
        # absent (legacy attempts).
        vault=load_vault(root),
    )
    new_head = repository.grade_interpretation(adj["interpretation_id"])
    event_id = record_reinterpretation_if_changed(
        repository,
        administration_id=administration_id,
        observation_id=observation_id,
        from_interpretation=interp,
        to_interpretation=new_head,
    )
    payload = {"adjudication": adj, "reinterpretation_event_id": event_id}
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(f"Adjudicated {interpretation_id} -> new head {adj['interpretation_id']}")
    if event_id:
        typer.echo(f"Reinterpretation event: {event_id} (downstream state rebuilt)")

@grading_app.command("receipt")
def grading_receipt(
    attempt_id: Annotated[str, typer.Argument(help="Attempt id to trace.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = True,
) -> None:
    """The §5 measurement receipt: response -> raw grade -> interpretation ->
    projection, plus the calibration lineage. Read-only trace."""

    root = _root(vault)
    repository = _repository(root)
    observation = repository.observation_by_attempt(attempt_id)
    if observation is None:
        typer.echo(f"No observation for attempt {attempt_id!r}.")
        raise typer.Exit(code=1)
    observation_id = observation["id"]
    raws = repository.raw_grade_events_for_observation(observation_id)
    active = repository.active_interpretation_for_observation(observation_id)

    # §5 decision lineage: the administration's pinned decision_params_hash, the
    # calibration model id+hash the active interpretation was resolved under, and the
    # resolved decision-parameter registry rows (when the projection is populated).
    administration_id = observation.get("administration_id")
    administration = (
        repository.fetch_administration(administration_id) if administration_id else None
    )
    decision_params_hash = administration.get("decision_params_hash") if administration else None
    calibration = {
        "calibration_model_id": active.get("calibration_model_id") if active else None,
        "calibration_model_hash": active.get("calibration_model_hash") if active else None,
    }
    registry_entries = repository.parameter_registry_entries()

    receipt = {
        "attempt_id": attempt_id,
        "observation": observation,
        "administration_id": administration_id,
        "decision_params_hash": decision_params_hash,
        "raw_grade_events": raws,
        "active_interpretation": active,
        "calibration": calibration,
        "interpretation_history": repository.grade_interpretations_for_observation(observation_id),
        "registry_entries": registry_entries,
    }
    typer.echo(_dump(receipt))

__all__ = [name for name in globals() if not name.startswith("__")]
