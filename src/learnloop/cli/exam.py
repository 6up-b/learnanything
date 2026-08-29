from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

exam_app = typer.Typer(no_args_is_help=True, help="Held-out practice-exam pool, session, and calibration.")

@exam_app.command("reserve")
def exam_reserve_command(
    goal: Annotated[str, typer.Option("--goal", help="Goal id to reserve a held-out exam pool for.")],
    item_count: Annotated[int | None, typer.Option("--item-count", help="Override the goal's exam item_count.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    goal_obj = _goal_or_exit(loaded, goal, json_output=json_output)
    # An explicit `exam reserve` reserves whatever the pool can give; only the
    # automatic hook in `get_exam_status` defers on a thin pool.
    report = reserve_exam_pool(loaded, repository, goal_obj, item_count=item_count)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_pool": report.as_dict()}))
        return
    typer.echo(
        f"Reserved {len(report.reserved_item_ids)} items for {goal} "
        f"(already_reserved={report.already_reserved}); "
        f"covered {len(report.covered_facets)} facets, uncovered {report.uncovered_facets}."
    )

@exam_app.command("start")
def exam_start_command(
    goal: Annotated[str, typer.Option("--goal", help="Goal id to start a held-out exam for.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    _goal_or_exit(loaded, goal, json_output=json_output)
    try:
        session = start_exam(loaded, repository, goal)
    except ExamSessionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_session_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_session": session}))
        return
    typer.echo(
        f"Exam session {session['session_id']} ({session['status']}) with "
        f"{len(session['item_order'])} items; already_started={session['already_started']}."
    )

@exam_app.command("answer")
def exam_answer_command(
    session: Annotated[str, typer.Option("--session", help="Exam session id.")],
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id being answered.")],
    answer: Annotated[str | None, typer.Option("--answer", help="Learner answer markdown.")] = None,
    criterion_points: Annotated[str | None, typer.Option("--criterion-points", help="REFUSED: a held-out exam is not self-graded.")] = None,
    fatal_errors: Annotated[str | None, typer.Option("--fatal-errors", help="REFUSED: a held-out exam is not self-graded.")] = None,
    confidence: Annotated[int | None, typer.Option("--confidence", min=1, max=5, help="REFUSED: a held-out exam is not self-graded.")] = None,
    error_type: Annotated[str | None, typer.Option("--error-type", help="REFUSED: a held-out exam is not self-graded.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for grading.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Answer one held-out exam item. AI-graded only -- see ``EXAM_SELF_GRADE_REFUSAL``.

    The self-grade options are kept so an existing caller gets the typed refusal
    rather than an unknown-option error; ordinary practice (``learnloop attempt``)
    still self-grades, because practice is not the measurement the exam is.
    """

    self_grade_flags = [
        name
        for name, value in (
            ("--criterion-points", criterion_points),
            ("--fatal-errors", fatal_errors),
            ("--confidence", confidence),
            ("--error-type", error_type),
        )
        if value is not None
    ]
    if self_grade_flags:
        _exam_answer_refusal(
            "exam_self_grade_refused",
            f"{', '.join(self_grade_flags)} self-grade a held-out exam. "
            + EXAM_SELF_GRADE_REFUSAL,
            json_output=json_output,
        )
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    item = loaded.practice_items.get(practice_item_id)
    if item is None:
        typer.echo(f"No Practice Item found for {practice_item_id}.", err=True)
        raise typer.Exit(code=1)
    provider_name, runtime, client = _ready_provider_for_task(
        vault_root, loaded.config, "grading", ai_provider
    )
    if provider_name == "manual" or not runtime.ready or client is None:
        _exam_answer_refusal(
            "exam_grading_unavailable", EXAM_SELF_GRADE_REFUSAL, json_output=json_output
        )
    answer_text = answer if answer is not None else typer.prompt("Answer", default="")
    from learnloop.attempts.attempts import resolved_codex_grade
    from learnloop.attempts.grading import (
        GradingValidationError,
        build_grading_context,
        request_grading_proposal,
        validate_codex_grading_proposal,
    )

    grading_attempt_id = new_ulid()
    context = build_grading_context(
        loaded, item, attempt_id=grading_attempt_id, learner_answer_md=answer_text
    )
    try:
        validated = validate_codex_grading_proposal(
            request_grading_proposal(client, context),
            attempt_id=grading_attempt_id,
            item=item,
            vault=loaded,
            learner_answer_md=answer_text,
        )
    except GradingValidationError as exc:
        _exam_answer_refusal(
            "exam_grading_failed", str(exc), json_output=json_output
        )
    except Exception as exc:  # provider transport failures
        _exam_answer_refusal(
            "exam_grading_unavailable",
            f"AI grading failed: {exc}. Retry when the provider is available.",
            json_output=json_output,
        )
    try:
        result = record_exam_answer(
            loaded,
            repository,
            session,
            practice_item_id,
            answer_md=answer_text,
            resolved_grade=resolved_codex_grade(
                validated, agent_run_id=None, clock=None
            ),
        )
    except (ExamSessionError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_answer_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_answer": result}))
        return
    typer.echo(
        f"Recorded exam answer for {practice_item_id}: score={result['rubric_score']} "
        f"correctness={result['correctness']:.2f}"
    )

@exam_app.command("finish")
def exam_finish_command(
    session: Annotated[str, typer.Option("--session", help="Exam session id to finish.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    sync_vault_state(loaded, repository)
    try:
        report = finish_exam(loaded, repository, session)
    except ExamSessionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_session_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_report": report}))
        return
    typer.echo(
        f"Exam {session} finished: answered={report['answered_count']}/{report['item_count']} "
        f"overall_score={report['overall_score']} brier={report['brier']}"
    )

__all__ = [name for name in globals() if not name.startswith("__")]
