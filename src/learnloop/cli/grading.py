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


@grading_app.command("hardcases")
def grading_hardcases(
    vault: Annotated[Path, typer.Option("--vault", help="A backup-API copy of a vault (receipts and checkpoints are written there).")],
    route: Annotated[list[str], typer.Option("--route", help="A configured [ai.providers.*] profile to score as a judge; repeatable. Every ordered pair is also scored as the gate (grader route, checker route).")],
    cases: Annotated[Path | None, typer.Option("--cases", help="Gold-set JSON (default: fixtures/grading_hardcases/cases_v1.json).")] = None,
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Report destination.")] = Path("fixtures-local/reports/grading-hardcases"),
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan calls, tokens and cost; build no client and send nothing.")] = False,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Cap on metered spend (reservations: each request reserves its full output budget).")] = 3.0,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 200,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Cap on metered tokens (input plus reserved output).")] = 2_000_000,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Counted retries of a failed transport request.")] = 4,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="One USD rate for input and output tokens (an upper bound). Metered routes need a price.")] = None,
    input_price_per_million: Annotated[float | None, typer.Option("--input-price-per-million", min=0)] = None,
    output_price_per_million: Annotated[float | None, typer.Option("--output-price-per-million", min=0)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Wrong-rejection and wrong-acceptance rates per judge route on hard cases.

    The gold set holds valid alternative proofs, correct answers with flawed
    reasoning and wrong proofs that look right (linear algebra, probability).
    Each --route is scored as the blind grader, the mvp-0.15 route checker and
    the proof-like item reader, with the production prompts; every ordered
    pair of routes is also scored as the live gate. Run it on a backup-API
    copy, --dry-run first. Spend is admitted before every request.
    """

    from learnloop.ai.spend import SpendCaps
    from learnloop.cli.embeddings import _cancellation
    from learnloop.diagnosis.grading_hardcases import run_hardcases, write_report
    from learnloop.vault.loader import load_vault

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml; use a backup-API copy.")
        # A dry run reads only the vault TOML; a paid run loads like the app,
        # which reads its own keys.
        loaded = load_vault(vault, load_environment=not dry_run)
        caps = SpendCaps(
            max_candidates=0, max_pairs=0, max_retries=max_retries, max_calls=max_calls,
            max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        with _cancellation() as stop:
            report = run_hardcases(
                loaded, routes=route, caps=caps, cases_path=cases, dry_run=dry_run,
                price_per_million=price_per_million, input_price_per_million=input_price_per_million,
                output_price_per_million=output_price_per_million, cancelled=stop.is_set,
            )
        if report["status"] == "complete":
            report["reports"] = write_report(report, output_dir)
    except (ValueError, OSError) as exc:
        typer.echo(_dump({"status": "invalid", "reason": str(exc)}))
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:  # PFUnavailable, AIProviderUnavailable: a route cannot serve
        typer.echo(_dump({"status": "unavailable", "reason": str(exc), "error_type": type(exc).__name__}))
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(_dump(report))
    else:
        summary = {key: report.get(key) for key in ("status", "reason", "cases", "estimate", "reports") if key in report}
        typer.echo(_dump(summary))
    if report["status"] not in {"complete", "dry_run"}:
        raise typer.Exit(code=1)

__all__ = [name for name in globals() if not name.startswith("__")]
