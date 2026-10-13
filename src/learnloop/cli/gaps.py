"""`learnloop gaps`: learner-text gaps (implementation_handoffs §4).

* ``run``: drain the gap queue (tutor questions, diagnoses and stuck answers
  read for a named gap), ``--backlog`` first queues unread stuck answers
  (``--history``: also earlier tutor questions and diagnoses). Paid:
  ``--dry-run`` prints the plan and sends nothing; one command budget caps
  every call.
* ``list``: what was read and done (no call).
* ``undo``: an owner reversal (undo an edge, a creation, or "not what I meant").
* ``report``: per kind and chooser: matched, created, undone, the created
  prerequisites' first-check pass rate, "not what I meant" taps, and whether
  the Decider or the LLM chooses better (no call; ``--dry-run`` first).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.receipts import bind_command_repository, bind_command_vault
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

gaps_app = typer.Typer(
    no_args_is_help=True,
    help="Learner-text gaps: read questions, stuck answers and diagnoses for named prerequisites and misconceptions.",
)


def _load(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    bind_command_vault(loaded.root)
    return loaded


def _repository(loaded, *, read_only: bool):
    from learnloop.db.repositories import Repository

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if read_only:
        return Repository.attach(sqlite_path, read_only=True)
    repository = open_vault_repository(loaded.root, sqlite_path)
    bind_command_repository(repository)
    return repository


def _echo(payload: object, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, default=str, indent=None if json_output else 2))


VaultOption = Annotated[Path, typer.Option("--vault", help="Vault root.")]
JsonOption = Annotated[bool, typer.Option("--json", help="One-line JSON.")]


@gaps_app.command("run")
def gaps_run(
    vault: VaultOption,
    backlog: Annotated[bool, typer.Option("--backlog", help="First queue unread stuck answers.")] = False,
    history: Annotated[bool, typer.Option("--history", help="With --backlog: also earlier tutor questions and diagnoses.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the plan; send and write nothing.")] = False,
    max_texts: Annotated[int, typer.Option("--max-texts", min=1, help="Learner texts to read in this run.")] = 20,
    max_calls: Annotated[int, typer.Option("--max-calls", min=1, help="Paid requests across the run.")] = 120,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 20,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=1, help="Metered tokens across the run.")] = 2_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0.0, help="Metered dollars across the run.")] = 0.50,
    price_per_million: Annotated[
        float | None,
        typer.Option("--price-per-million", help="Owner price for a metered chat route without a published one."),
    ] = None,
    json_output: JsonOption = False,
) -> None:
    from learnloop.diagnosis.offline_review.spend import ReviewSpend
    from learnloop.diagnosis.text_gaps.jobs import plan, run_pending, sweep_backlog
    from learnloop.diagnosis.text_gaps.judges import TextBudget

    loaded = _load(vault)
    repository = _repository(loaded, read_only=dry_run)
    caps = SpendCaps(max_candidates=max_calls, max_pairs=max_calls, max_retries=max_retries, max_calls=max_calls,
                     max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd)
    swept = sweep_backlog(loaded, repository, include_history=history, dry_run=dry_run) if backlog else None
    planned = plan(loaded, repository)
    if dry_run:
        if swept:
            planned["queued"] += sum(swept.values())
            planned["max_calls_ceiling"] = planned["queued"] * int(loaded.config.learner_text_gaps.max_calls_per_text)
        _echo({"dry_run": True, "would_queue": swept, "plan": planned, "caps": caps.as_dict(),
               "texts_this_run": min(max_texts, planned["queued"])}, json_output)
        return
    price = price_per_million if price_per_million is not None else loaded.config.learner_text_gaps.metered_price_per_million
    shared = TextBudget(ReviewSpend(caps, price_per_million=price))
    outcomes = run_pending(loaded.root, repository, owner=f"cli:{new_ulid()}", max_jobs=max_texts,
                           budget_factory=lambda _vault: shared)
    _echo({"queued_by_backlog": swept, "outcomes": [outcome.as_dict() for outcome in outcomes],
           "spend": shared.spend.summary()}, json_output)


@gaps_app.command("list")
def gaps_list(
    vault: VaultOption,
    since: Annotated[str | None, typer.Option("--since", help="ISO time; only gaps read since then.")] = None,
    show_text: Annotated[bool, typer.Option("--show-text", help="Include the learner's text.")] = False,
    json_output: JsonOption = False,
) -> None:
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores import learner_gaps as store

    loaded = _load(vault)
    repository = _repository(loaded, read_only=True)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = store.gaps(connection, since=since)
        reversals = store.reversals(connection, [row["id"] for row in rows])
    undone: dict[str, list[str]] = {}
    for row in reversals:
        undone.setdefault(row["gap_id"], []).append(row["reversal"])
    keys = ("id", "created_at", "source_kind", "kind", "context_kind", "decider_kind", "chooser", "action",
            "target_kind", "target_id", "edge_id", "created_learning_object_id", "seed_status")
    out = []
    for row in rows:
        entry = {key: row.get(key) for key in keys}
        entry["named"] = row.get("named")
        entry["reversals"] = undone.get(row["id"], [])
        if show_text:
            entry["learner_text"] = row["learner_text"]
        out.append(entry)
    _echo({"gaps": out}, json_output)


@gaps_app.command("undo")
def gaps_undo(
    gap_id: Annotated[str, typer.Argument(help="The learner_text_gaps id.")],
    vault: VaultOption,
    reversal: Annotated[str, typer.Option("--reversal", help="undo_edge | undo_creation | not_this_belief")],
    json_output: JsonOption = False,
) -> None:
    from learnloop.diagnosis.text_gaps.actions import UndoError, reverse_gap

    loaded = _load(vault)
    repository = _repository(loaded, read_only=False)
    try:
        result = reverse_gap(loaded.root, repository, gap_id, reversal, actor="owner")
    except UndoError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _echo(result, json_output)


@gaps_app.command("report")
def gaps_report(
    vault: VaultOption,
    since: Annotated[str | None, typer.Option("--since", help="ISO time; only gaps read since then.")] = None,
    out: Annotated[Path | None, typer.Option("--out", help="Write the Markdown report (with the batch review) here.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Population sizes only; write nothing.")] = False,
    json_output: JsonOption = False,
) -> None:
    from learnloop.diagnosis.text_gaps.report import build_report, plan_report, write_report

    loaded = _load(vault)
    repository = _repository(loaded, read_only=True)
    if dry_run:
        _echo(plan_report(repository, since=since), json_output)
        return
    report = write_report(loaded, repository, out, since=since) if out is not None else build_report(
        loaded, repository, since=since)
    _echo(report, json_output)


__all__ = ["gaps_app"]
