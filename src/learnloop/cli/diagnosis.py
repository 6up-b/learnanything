from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

diagnosis_app = typer.Typer(
    no_args_is_help=True,
    help="Diagnosis adjudication: the queue, one verdict, the scoreboard.",
)

@diagnosis_app.command("queue")
def diagnosis_queue(
    learning_object: Annotated[
        str | None, typer.Option("--learning-object", help="Restrict to one learning object.")
    ] = None,
    reason: Annotated[
        str | None,
        typer.Option(
            "--reason",
            help=(
                "Comma-separated queue strata: learner_contest, system_abstention, "
                "anchor_disagreement, incomplete_repair_mapping, sampled."
            ),
        ),
    ] = None,
    limit: Annotated[int, typer.Option("--limit")] = 20,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Attempts owed a diagnosis verdict, highest information first.

    Contested diagnoses lead (the learner already paid the attention cost),
    then abstentions (an eval set without them selects toward over-filling),
    then cases the system itself flagged, then an unflagged stratum so the set
    is not purely adversarially selected."""

    from learnloop.diagnosis.diagnosis_adjudication import adjudication_queue

    root = _root(vault)
    repository = _repository(root)
    try:
        entries = adjudication_queue(
            repository,
            learning_object_id=learning_object,
            reasons=_split_items(reason),
            limit=limit,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(
            _dump({"version": 1, "queue": [entry.as_dict() for entry in entries]})
        )
        return
    if not entries:
        typer.echo("No attempts are awaiting a diagnosis verdict.")
        return
    for entry in entries:
        system = entry.snapshot
        anchor = system.system_anchor or {}
        typer.echo(
            f"{entry.attempt_id}\t{entry.queue_reason}"
            f"\tabstained={'yes' if system.system_abstained else 'no'}"
            f"\tanchor={anchor.get('anchor_kind') or '-'}"
            f"\trepair={system.system_repair_class_id or '-'}"
        )
        typer.echo(f"    {entry.detail}")

@diagnosis_app.command("adjudicate")
def diagnosis_adjudicate(
    attempt_id: Annotated[str, typer.Argument(help="Attempt id (from `diagnosis queue`).")],
    verdict: Annotated[
        str,
        typer.Option(
            "--verdict",
            help=(
                "correct | wrong_anchor | wrong_repair | should_have_abstained | "
                "correctly_abstained | should_not_have_abstained"
            ),
        ),
    ],
    anchor_kind: Annotated[
        str | None,
        typer.Option(
            "--anchor-kind",
            help="span|between_spans|missing_required_step|whole_answer|none. "
            "Omit on `correct`/`wrong_repair` to inherit the system's anchor.",
        ),
    ] = None,
    anchor_criterion: Annotated[
        str | None, typer.Option("--anchor-criterion", help="Rubric criterion the anchor sits in.")
    ] = None,
    anchor_quote: Annotated[
        str | None, typer.Option("--anchor-quote", help="Verbatim span from the learner's answer.")
    ] = None,
    anchor_checkpoint: Annotated[
        str | None,
        typer.Option("--anchor-checkpoint", help="Required for anchor kind missing_required_step."),
    ] = None,
    anchor_start: Annotated[
        int | None, typer.Option("--anchor-start", help="Character offset into the answer.")
    ] = None,
    anchor_end: Annotated[int | None, typer.Option("--anchor-end")] = None,
    repair: Annotated[
        str | None, typer.Option("--repair", help="The minimal repair, in prose.")
    ] = None,
    repair_class: Annotated[
        str | None,
        typer.Option("--repair-class", help="Repair class id, when the episode offered the right one."),
    ] = None,
    queue_reason: Annotated[
        str | None,
        typer.Option("--queue-reason", help="Defaults to the stratum this attempt is in."),
    ] = None,
    source: Annotated[
        str, typer.Option("--source", help="human_owner|independent_expert|deterministic_verifier")
    ] = "human_owner",
    rationale: Annotated[str | None, typer.Option("--rationale")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record one considered verdict on one diagnosis, append-only (A4).

    This is the eval set, the few-shot pool, and the eventual fine-tune set.
    `--verdict correct` needs nothing else: the adjudicated anchor and repair
    are the system's own, which is exactly what `correct` asserts.

    Distinct from the learner's ⚑ contest on the feedback screen: that is
    bounded typed evidence about a diagnosis, this is a full-authority verdict
    that also names the anchor and the repair. A contest on the attempt is
    linked here as provenance and never sets the verdict."""

    from learnloop.diagnosis.diagnosis_adjudication import (
        append_diagnosis_adjudication,
    )

    root = _root(vault)
    repository = _repository(root)

    anchor: dict[str, Any] | None = None
    if any(
        value is not None
        for value in (anchor_kind, anchor_criterion, anchor_quote, anchor_checkpoint, anchor_start)
    ):
        if not anchor_kind:
            typer.echo("--anchor-kind is required when supplying anchor fields.", err=True)
            raise typer.Exit(code=1)
        if (anchor_start is None) != (anchor_end is None):
            typer.echo("--anchor-start and --anchor-end must be supplied together.", err=True)
            raise typer.Exit(code=1)
        anchor = {"anchor_kind": anchor_kind, "criterion_id": anchor_criterion or ""}
        if anchor_quote:
            anchor["quote"] = anchor_quote
        if anchor_checkpoint:
            anchor["checkpoint_id"] = anchor_checkpoint
        if anchor_start is not None:
            anchor["char_start"] = anchor_start
            anchor["char_end"] = anchor_end
        if anchor_kind == "missing_required_step" and not anchor_checkpoint:
            typer.echo(
                "--anchor-checkpoint is required for a missing_required_step anchor.",
                err=True,
            )
            raise typer.Exit(code=1)

    try:
        record = append_diagnosis_adjudication(
            repository,
            attempt_id=attempt_id,
            verdict=verdict,
            adjudicated_anchor=anchor,
            adjudicated_repair_md=repair,
            adjudicated_repair_class_id=repair_class,
            queue_reason=queue_reason,
            adjudicator_source=source,
            rationale=rationale,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(_dump({"version": 1, "adjudication": record}))
        return
    typer.echo(
        f"Adjudicated {attempt_id}: {record['verdict']} "
        f"(queue={record['queue_reason']}, id={record['id']})"
    )
    if record.get("supersedes_id"):
        typer.echo(f"Supersedes {record['supersedes_id']} (prior verdict retained).")
    if record.get("learner_report_id"):
        typer.echo(
            f"Learner contest {record['learner_report_id']} linked as provenance."
        )

@diagnosis_app.command("scoreboard")
def diagnosis_scoreboard(
    group_by: Annotated[
        str,
        typer.Option("--group-by", help="version | queue_reason | none"),
    ] = "version",
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The §3 B5 metrics this store owns, over the active verdicts.

    Abstention precision/recall report `null` on an empty denominator rather
    than a flattering 1.0, and `abstention_cases_present` says outright whether
    the eval set contains any abstention case at all."""

    from learnloop.diagnosis.diagnosis_adjudication import (
        diagnosis_adjudication_scoreboard,
    )

    root = _root(vault)
    repository = _repository(root)
    try:
        report = diagnosis_adjudication_scoreboard(
            repository, group_by=None if group_by == "none" else group_by
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump(report))
        return
    if not report["overall"]["records"]:
        typer.echo("No diagnosis adjudications have been recorded.")
        return

    def _rate(value: float | None) -> str:
        return "n/a" if value is None else f"{value:.3f}"

    for group in [report["overall"], *report["groups"]]:
        label = (
            "overall"
            if group.get("scope") == "overall"
            else " / ".join(
                str(group[key])
                for key in ("grading_prompt_version", "grader_model", "queue_reason")
                if key in group
            )
        )
        confusion = group["abstention_confusion"]
        typer.echo(f"{label}: {group['records']} adjudications")
        typer.echo(
            "  first_divergence_anchor_accuracy="
            f"{_rate(group['first_divergence_anchor_accuracy'])}"
            f" (n={group['anchor_scored']})"
        )
        typer.echo(
            f"  repair_class_match_rate={_rate(group['repair_class_match_rate'])}"
            f"  repair_class_id_match_rate={_rate(group['repair_class_id_match_rate'])}"
        )
        typer.echo(
            f"  abstention_precision={_rate(group['abstention_precision'])}"
            f"  abstention_recall={_rate(group['abstention_recall'])}"
            f"  (tp={confusion['tp']} fp={confusion['fp']} fn={confusion['fn']}"
            f" tn={confusion['tn']})"
        )
        if not group["abstention_cases_present"]:
            typer.echo(
                "  WARNING: no abstention cases in this slice — the abstention "
                "metrics cannot fail here (spec §3 B1)."
            )

__all__ = [name for name in globals() if not name.startswith("__")]
