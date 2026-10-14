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
    route: Annotated[list[str], typer.Option("--route", help="A configured [ai.providers.*] profile to score as the grader; repeatable. Each is also scored along the production path (PF-c's gate and the own-route rule).")],
    cases: Annotated[Path | None, typer.Option("--cases", help="Gold-set JSON (default: fixtures/grading_hardcases/cases_v3.json).")] = None,
    ablations: Annotated[bool, typer.Option("--ablations", help="Grade under all four R2 arms: the reference shown or solve-first, crossed with the final-answer check shown to the grader or withheld (the gate still applies it). Default: the production arm only.")] = False,
    repeats: Annotated[int, typer.Option("--repeats", min=1, help="Fresh, separately identified repetitions of every call; 2 or more report a repeat-run noise floor.")] = 1,
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Report destination.")] = Path("fixtures-local/reports/grading-hardcases"),
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan calls, tokens and cost; build no client and send nothing.")] = False,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Cap on metered spend (reservations: each request reserves its full output budget).")] = 3.0,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 200,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Cap on metered tokens (input plus reserved output; each request reserves its route's policy output budget, 16,384 by default).")] = 4_000_000,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Counted retries of a failed transport request.")] = 4,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="One USD rate for input and output tokens (an upper bound). Metered routes need a price.")] = None,
    input_price_per_million: Annotated[float | None, typer.Option("--input-price-per-million", min=0)] = None,
    output_price_per_million: Annotated[float | None, typer.Option("--output-price-per-million", min=0)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Wrong-rejection and wrong-acceptance rates per judge route on hard cases.

    The gold set fills P2's four cells: valid alternatives with a checkable
    answer, valid alternative proofs, correct answers with flawed reasoning
    and wrong proofs that look right (linear algebra, probability), plus a
    fifth: items requiring a method answered by another valid method (the
    method criteria fail, the facts pass), reported apart; reports label it
    synthetic smoke coverage until real traces fill cells 3-4. Each
    --route is scored as the blind grader alone, with the production prompt
    (the own-route rules in the grader's one call), on its raw output and
    along the production path (PF-c's gate and the own-route rule). Every
    verdict goes to judgment_ledger. Run it on a backup-API copy, --dry-run
    first. Spend is admitted before every request.
    """

    from learnloop.ai.spend import SpendCaps
    from learnloop.cli.embeddings import _cancellation
    from learnloop.diagnosis.grading_hardcases import ALL_ARMS, PRODUCTION_ARM, run_hardcases, write_report
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
                arms=ALL_ARMS if ablations else (PRODUCTION_ARM,), repeats=repeats,
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
        summary = {
            key: report.get(key)
            for key in ("status", "reason", "cases", "cells", "arms", "repeats", "estimate", "limitations", "reports")
            if key in report
        }
        typer.echo(_dump(summary))
    if report["status"] not in {"complete", "dry_run"}:
        raise typer.Exit(code=1)

@grading_app.command("method-phrasing")
def grading_method_phrasing(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    judge: Annotated[str, typer.Option("--judge", help="auto (the Decider, else the LLM judge, else the heuristic: the first that is ready), decider, llm or heuristic.")] = "auto",
    item: Annotated[list[str] | None, typer.Option("--item", help="Read only this practice item; repeatable. Default: every active item with its own rubric.")] = None,
    propose: Annotated[bool, typer.Option("--propose", help="Persist the repairs as one pending proposal (never auto-applied; review with `learnloop proposals`).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan every request the run may send (the Decider's classification and the writer's rewrites, or the LLM judge's) with its estimated cost, and show the heuristic's flags; build no client and send nothing. Exits 1 when a metered route has no price.")] = False,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Cap on metered spend.")] = 0.50,
    max_calls: Annotated[int | None, typer.Option("--max-calls", min=0, help="Cap on requests (default: two per item).")] = None,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="USD per million tokens for a metered LLM judge or writer (an upper bound; without it their requests are refused); the Decider's listed price is known.")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir", help="Also write the JSON report here.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Rubric criteria phrased by method, and their repair proposals.

    Owner rule 2026-10-13: a criterion names the fact a step establishes, not
    the method used; a method is required only when the item's target is that
    method, and the item's statement then says "Use {method} in your
    answer.". The judge is the Decider (ai.routing.rubric_phrasing_judge, or
    the code-default openrouter_decider), else the LLM judge, else the
    conservative heuristic; the report says which. --propose drafts one
    update per item through the normal proposal/confirm path: rephrase the
    criterion by fact, or add the required method and its instruction when
    the item's target really is that method. Nothing is applied until you
    accept it; an item changed after the report is refused at acceptance.
    --dry-run first (it estimates the cost); spend is admitted before every
    request.
    """

    from learnloop.ai.spend import SpendCaps
    from learnloop.cli.embeddings import _cancellation
    from learnloop.content.proposals.method_phrasing import candidate_items, default_caps, run_method_phrasing, write_report
    from learnloop.vault.loader import load_vault

    root = _root(vault)
    try:
        loaded = load_vault(root, load_environment=not dry_run)
        items = candidate_items(loaded, item or None)
        base = default_caps(len(items))
        caps = SpendCaps(
            max_candidates=0, max_pairs=0, max_retries=base.max_retries,
            max_calls=base.max_calls if max_calls is None else max_calls,
            max_total_tokens=base.max_total_tokens, max_estimated_usd=max_cost_usd,
        )
        with _cancellation() as stop:
            report = run_method_phrasing(
                loaded, judge=judge, item_ids=item or None, propose=propose, dry_run=dry_run, caps=caps,
                price_per_million=price_per_million, cancelled=stop.is_set,
            )
        if output_dir is not None:
            report["reports"] = write_report(report, output_dir)
    except ValueError as exc:
        typer.echo(_dump({"status": "invalid", "reason": str(exc)}))
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:  # a forced judge that is not ready
        typer.echo(_dump({"status": "unavailable", "reason": str(exc), "error_type": type(exc).__name__}))
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(_dump(report))
    else:
        summary = {
            key: report.get(key)
            for key in ("status", "judge", "judge_plan", "estimate", "items", "criteria", "flagged_items",
                        "proposal_id", "failures", "writer_failures")
            if key in report
        }
        summary["flagged"] = [
            f"{row['item_id']}#{row['criterion_id']}: {row.get('method') or 'method'}"
            for row in report.get("flagged") or report.get("heuristic_flags") or []
        ]
        typer.echo(_dump(summary))
    if report.get("status") == "refused":
        # A dry run whose plan includes a metered route with no price.
        raise typer.Exit(code=1)


__all__ = [name for name in globals() if not name.startswith("__")]
