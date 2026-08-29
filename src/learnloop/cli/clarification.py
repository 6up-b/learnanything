from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

clarification_app = typer.Typer(
    no_args_is_help=True,
    help="A8 clarification channel: pending questions, answers, expiry, rate (spec_measurement_efficiency §3.A8).",
)

@clarification_app.command("list")
def clarification_list_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Clarification requests and their derived status (pending / answered / timed_out)."""

    from learnloop.clock import utc_now_iso
    from learnloop.attempts.clarification import row_to_clarification

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    now = utc_now_iso()
    rows = [
        row_to_clarification(row).as_dict(now=now)
        for row in repository.unanswered_grading_clarifications()
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "clarifications": rows}))
        return
    if not rows:
        typer.echo("No unanswered clarification requests.")
        return
    for row in rows:
        typer.echo(
            f"  {row['status']:<10} {row['attempt_id']} trigger={row['trigger']} "
            f"reason={row['reason']} expires={row['expires_at']}"
        )
        typer.echo(f"    {row['question_md']}")

@clarification_app.command("retry")
def clarification_retry_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Re-grade answers whose regrade never ran (spec_measurement_efficiency §3.A8).

    The learner's answer is persisted BEFORE the re-grade is attempted, because
    the answer is the un-backfillable half and the re-grade can always be re-run.
    A provider outage between the two leaves the exchange complete and
    unconsumed: the learner cannot resubmit (an answer exists) and nothing
    retries (every other route looks for *pending* work). This drains that
    queue, rebuilding the exchange from the stored question and response.
    """

    from learnloop.attempts.clarification import resolve_awaiting_regrades

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    _provider_name, runtime, client = _ready_provider_for_task(
        loaded.root, loaded.config, "grading"
    )
    results = resolve_awaiting_regrades(loaded, repository, runtime=runtime, client=client)
    backlog = repository.grading_clarifications_awaiting_regrade()
    if json_output:
        typer.echo(_dump({"version": 1, "resolved": results, "remaining": len(backlog)}))
        return
    if client is None:
        typer.echo(
            f"No grader available; {len(backlog)} answered clarification(s) still "
            "awaiting a re-grade (their answers are safe and will be retried)."
        )
        return
    for entry in results:
        typer.echo(f"  {entry['outcome']:<16}{entry['clarification_id']}")
    typer.echo(f"Resolved {len(results)}; {len(backlog)} remaining.")

@clarification_app.command("expire")
def clarification_expire_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Close the window on unanswered questions.

    Writes no grade: the provisional grade already recorded the hedge or
    abstention that triggered the question, so timing out to "the abstention
    that triggered it" means changing nothing about the grade at all. All this
    clears is the attempt's `provisional_pending_clarification` review state.
    """

    from learnloop.attempts.clarification import expire_clarifications

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    expired = expire_clarifications(repository)
    if json_output:
        typer.echo(_dump({"version": 1, "expired": expired}))
        return
    typer.echo(f"Expired {len(expired)} clarification(s).")

@clarification_app.command("rate")
def clarification_rate_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """§3.A8's revert criterion: clarifications per model-graded attempt.

    A rate above the threshold is evidence of MACHINE-resident uncertainty
    misclassified as learner-resident, which principle 8's unamended half says
    must be fixed machine-side rather than paid for with learner questions.
    """

    from learnloop.attempts.clarification import clarification_rate

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = _repository(loaded.root)
    report = clarification_rate(repository)
    if json_output:
        typer.echo(_dump({"version": 1, **report}))
        return
    if not report["available"]:
        typer.echo(
            f"clarification_rate unavailable ({report['unavailable_reason']}): "
            f"{report['gradeable_attempts']} model-graded attempt(s), "
            f"{report['clarifications']} clarification(s) — too few to report a rate."
        )
        return
    typer.echo(
        f"clarification_rate {report['rate']:.1%} "
        f"[{report['clarifications']}/{report['gradeable_attempts']}], "
        f"{report['answered']} answered; threshold {report['threshold']:.0%}"
    )
    if report["over_threshold"]:
        typer.echo(
            "  OVER THRESHOLD — this is machine-resident uncertainty misclassified "
            "as learner-resident. Fix it machine-side (grader prompt, item contract), "
            "not by asking the learner more."
        )

__all__ = [name for name in globals() if not name.startswith("__")]
