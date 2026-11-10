"""`learnloop router log`, `card`, `report`, `trace`, `objective-report` and `embed-decisions`: the router's logged decisions.

``log`` lists router R1's logged decisions and their outcomes; ``card`` prints
the learner-state card a decision stored (router R2a). Both are read-only: the
database is opened read-only, never migrated, and no model is called.
Outcomes are derived on the fly from the ledgers (the same derivation the
``router_outcomes`` replayer caches), so the listing is current even when the
cache was last rebuilt days ago. ``embed-decisions`` (router R2c) backfills
the ``decision/context`` vectors of logged decisions that have none: paid,
metered embedding calls through the shared embedding backfill, under its
enforced caps (``--max-cost-usd`` and the rest) and both embedding switches,
with a priced ``--dry-run`` first. ``report`` (follow-ups batch 6, teacher TE1b) prints the lesson
suggestion decisions' intention-to-treat split by arm, read-only like ``log``. ``trace`` (router objective
RO4) prints one decision's objective trace, and ``objective-report`` the objective's report, both read-only.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Annotated, Any

import typer

from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

router_app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Action router (R1: logged decisions and their outcomes; R2a: the learner-state card each decision "
        "stored; R2c: the decision/context embedding backfill; TE1b: the lesson suggestions' report; RO4: the "
        "objective's trace and report)."
    ),
)


def _reader_exposures(connection: sqlite3.Connection, loaded: Any, path: Path) -> list[tuple[str, str]] | None:
    """What this vault's outcome version reads of the Reader (read-only, like everything here)."""

    from learnloop.data_capture import reading_exposures
    from learnloop.db.repositories import Repository
    from learnloop.router.outcomes import outcome_version_for

    return reading_exposures.for_version(connection, loaded, Repository.attach(path, read_only=True),
                                         outcome_version_for(loaded.config))


def _emit(payload: dict, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2))


def _summary(row: dict[str, Any], outcome: dict[str, Any] | None, *, candidates: bool) -> dict[str, Any]:
    detail = json.loads(row.get("detail_json") or "{}")
    exclusions = json.loads(row.get("exclusions_json") or "{}")
    summary: dict[str, Any] = {
        "id": row["id"],
        "created_at": row["created_at"],
        "decision_kind": row["decision_kind"],
        "surface": row["surface"],
        "mode": row["mode"],
        "policy": row["policy"],
        "algorithm_version": row["algorithm_version"],
        "session_id": row["session_id"],
        "parent_decision_id": row["parent_decision_id"],
        "chosen_ref": row["chosen_ref"],
        "chosen_practice_item_id": row["chosen_practice_item_id"],
        "propensity": row["propensity"],
        "propensity_kind": row["propensity_kind"],
        "design": row["design"],
        "learner_pick": bool(row["learner_pick"]),
        "candidate_count": row["candidate_count"],
        "card_hash": row.get("card_hash"),
        # Router R2b: the mixture's draw (which component drew, a model's fallback).
        "fallback": row.get("fallback"),
        "question_set_version": row.get("question_set_version"),
        "drawn_component": (detail.get("mixture") or {}).get("drawn_component"),
        "latency_ms": row.get("latency_ms"),
        "cost_usd": row.get("cost_usd"),
        "head_distribution": detail.get("head_distribution"),
        "exclusion_counts": {
            **{reason: len(ids) for reason, ids in (exclusions.get("named") or {}).items()},
            **(exclusions.get("counts") or {}),
        },
    }
    if candidates:
        summary["candidates"] = json.loads(row.get("candidates_json") or "[]")
        summary["exclusions"] = exclusions
        summary["detail"] = detail
    if outcome is not None:
        summary["outcome"] = {
            key: outcome[key]
            for key in (
                "action_status",
                "action_binding",
                "r_next_status",
                "r_next_value",
                "r_cold_status",
                "r_cold_value",
                "s_status",
                "s_value",
                "observed_through",
            )
        }
    return summary


@router_app.command("log")
def router_log(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    limit: Annotated[int, typer.Option("--limit", min=1, help="Newest decisions to show.")] = 20,
    candidates: Annotated[
        bool, typer.Option("--candidates", help="Include each decision's full candidate set.")
    ] = False,
    decision: Annotated[
        str | None,
        typer.Option(
            "--decision",
            help=(
                "Show this one decision in full: its candidates, the mixture's weights, both models' answers, "
                "sensors and similar decisions, and the payloads stored beside it (the receipt a block's "
                "details line names)."
            ),
        ),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The newest logged router decisions, with their R_next / R_cold / S outcomes."""

    from learnloop.db.stores.router import router_decision_rows, router_payloads_present
    from learnloop.router.outcomes import (
        derive_router_outcomes,
        outcome_version_for,
        servable_items_by_learning_object,
    )
    from learnloop.substrate.canonical_projection import held_for_review_attempts, pfc_assessments

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        with closing(connect(path, read_only=True)) as connection:
            connection.execute("BEGIN")
            present = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decisions'"
            ).fetchone()
            if present is None:
                raise ValueError("this database predates router decision logging (migration 181)")
            payload_kinds: list[str] = []
            if decision is not None:
                found = connection.execute("SELECT * FROM router_decisions WHERE id = ?", (decision,)).fetchone()
                if found is None:
                    raise ValueError(f"no router decision {decision!r}")
                rows = [dict(found)]
                if router_payloads_present(connection):
                    payload_kinds = [
                        str(row[0]) for row in connection.execute(
                            "SELECT kind FROM router_decision_payloads WHERE decision_id = ? ORDER BY kind",
                            (decision,),
                        )
                    ]
            else:
                rows = router_decision_rows(connection, limit=limit)
            attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
            outcomes = {
                row["decision_id"]: row
                for row in derive_router_outcomes(
                    connection,
                    pfc_states=pfc_assessments(connection, attempt_ids),
                    servable_items_by_lo=servable_items_by_learning_object(loaded),
                    held_attempt_ids=held_for_review_attempts(connection),
                    outcome_version=outcome_version_for(loaded.config),
                    reader_exposures=_reader_exposures(connection, loaded, path),
                )
            }
            total = connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0]
        if decision is not None:
            # Router R2b: one decision's receipt in full.
            row = rows[0]
            full = _summary(row, outcomes.get(row["id"]), candidates=True)
            for column in ("mixture_weights_json", "model_distributions_json", "sensor_answers_json",
                           "model_ids_json", "similar_decision_ids_json"):
                value = row.get(column)
                full[column.removesuffix("_json")] = json.loads(value) if value else None
            full["seed"] = row.get("seed")
            full["payload_kinds"] = payload_kinds
            _emit({"algorithm_version": loaded.config.algorithms.algorithm_version, "decision": full}, json_output)
            return
        payload = {
            "algorithm_version": loaded.config.algorithms.algorithm_version,
            "router": loaded.config.router.model_dump(mode="json"),
            "total_decisions": total,
            "decisions": [
                _summary(row, outcomes.get(row["id"]), candidates=candidates) for row in rows
            ],
        }
        _emit(payload, json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@router_app.command("report")
def router_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Lesson suggestions (teacher TE1b) by randomized arm (card shown or not): offered, accepted,
    opened and completed over every decision (intention to treat), and the mean R_cold on the drawn
    topic among outcomes observed so far (descriptive, not an ITT estimate), weighted by the logged
    arm propensity (read-only; no model call)."""

    from learnloop.db.stores import router_suggestions
    from learnloop.router.outcomes import derive_router_outcomes, outcome_version_for, servable_items_by_learning_object
    from learnloop.router.suggestion_report import itt_split, lines
    from learnloop.substrate.canonical_projection import held_for_review_attempts, pfc_assessments

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        with closing(connect(path, read_only=True)) as connection:
            connection.execute("BEGIN")
            if not router_suggestions.tables_present(connection):
                raise ValueError("this database predates lesson suggestions (migration 236)")
            decisions = router_suggestions.decisions(connection)
            responses = router_suggestions.responses(connection)
            releases = router_suggestions.releases(connection)
            lessons = {
                str(row["id"]): dict(row) for row in connection.execute(
                    "SELECT id, origin_ref, closed_at, close_reason FROM lessons WHERE origin = 'router'")
            }
            attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
            wanted = {str(decision["id"]) for decision in decisions}
            outcomes = {
                str(row["decision_id"]): row
                for row in derive_router_outcomes(
                    connection,
                    pfc_states=pfc_assessments(connection, attempt_ids),
                    servable_items_by_lo=servable_items_by_learning_object(loaded),
                    held_attempt_ids=held_for_review_attempts(connection),
                    outcome_version=outcome_version_for(loaded.config),
                    reader_exposures=_reader_exposures(connection, loaded, path),
                )
                if str(row["decision_id"]) in wanted
            }
        split = itt_split(decisions, responses, releases, lessons, outcomes)
        if json_output:
            _emit({"algorithm_version": loaded.config.algorithms.algorithm_version, "lesson_suggestions": split},
                  True)
        else:
            for line in lines(split):
                typer.echo(line)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@router_app.command("card")
def router_card(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    decision: Annotated[str, typer.Option("--decision", help="A router decision id (learnloop router log).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The learner-state card a decision stored (router R2a): its text, or with --json the typed card."""

    from learnloop.db.stores.router import router_payload

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        with closing(connect(path, read_only=True)) as connection:
            row = connection.execute(
                "SELECT id, decision_kind, card_hash, created_at FROM router_decisions WHERE id = ?", (decision,)
            ).fetchone() if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decisions'"
            ).fetchone() else None
            if row is None:
                raise ValueError(f"no router decision {decision!r}")
            payload = router_payload(connection, decision, "card")
        if payload is None:
            reason = "no card was stored" if row["card_hash"] is None else "the stored card was pruned (its hash remains)"
            raise ValueError(f"decision {decision}: {reason}")
        if json_output:
            _emit(
                {
                    "decision_id": decision,
                    "decision_kind": row["decision_kind"],
                    "created_at": row["created_at"],
                    "card_hash": row["card_hash"],
                    "card_version": payload["format_version"],
                    "card": json.loads(payload["content_json"] or "null"),
                },
                True,
            )
        else:
            typer.echo(f"# decision {decision} ({row['decision_kind']}, {row['created_at']})")
            typer.echo(f"# {payload['format_version']} {row['card_hash']}")
            typer.echo(payload["content_text"] or "", nl=False)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@router_app.command("trace")
def router_trace(
    decision: Annotated[str, typer.Argument(help="A router decision id (learnloop router log), or a trace id.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Router objective RO4's trace of one decision (spec §8.8): each sensor, the objective's terms, both
    policies, the mix and the output; in plain words, or with --json the whole trace (read-only)."""

    from learnloop.router_objective.trace import explain
    from learnloop.why.reader import objective_trace

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        with closing(connect(path, read_only=True)) as connection:
            # The same reader as `learnloop why`, whose answer for a router decision names this trace.
            row, offer_binding = objective_trace(connection, decision)
        if row is None:
            raise ValueError(f"no router objective trace for {decision!r} (a decision below mvp-0.47, with "
                             "[router_objective] enabled off, or a deterministic pick has none)")
        if json_output:
            _emit({"decision_id": row["decision_id"], "decision_kind": row["decision_kind"],
                   "created_at": row["created_at"], "trace_version": row["trace_version"],
                   "content_hash": row["content_hash"], "trace": row["trace"],
                   **({"offer_binding": offer_binding} if offer_binding is not None else {})}, True)
        else:
            typer.echo(f"# decision {row['decision_id']} ({row['decision_kind']}, {row['created_at']})")
            for line in explain(row):
                typer.echo(line)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


def _objective_forecasts(connection: Any, loaded: Any, path: Path, now: str) -> dict[str, Any] | None:
    """RO4 §8.9's forecast evaluation (the LLM policy's forecasts through RO2's resolver); None when it cannot be
    read here (the report says so), never a failed report."""

    from learnloop.adaptive_difficulty.history_resolve import resolve_curves
    from learnloop.db.repositories import Repository
    from learnloop.router_objective import forecast_resolve

    try:
        return forecast_resolve.resolve(connection, loaded, Repository.attach(path, read_only=True), now=now,
                                        resolve_curves=resolve_curves)
    except Exception:  # noqa: BLE001 - one evaluation never fails the report
        import logging

        logging.getLogger(__name__).warning("router objective: the forecast evaluation was not read", exc_info=True)
        return None


def _objective_weight(loaded: Any, path: Path, now: str) -> dict[str, Any] | None:
    """RO4's open item 2 (landing ruling R5): the weight the next decision would serve and its posterior, read by the
    chooser's own ``current_weight`` over a read-only repository; None when it cannot be read (the report then
    prints none), never a failed report."""

    from learnloop.daily_plan.objective_chooser import current_weight
    from learnloop.db.repositories import Repository

    try:
        w, record = current_weight(Repository.attach(path, read_only=True), loaded.config, at=now)
        return {"w": w, "posterior": record.get("posterior") or {}, "note": record.get("note")}
    except Exception:  # noqa: BLE001 - one evaluation never fails the report
        import logging

        logging.getLogger(__name__).warning("router objective: the weight was not read", exc_info=True)
        return None


@router_app.command("objective-report")
def router_objective_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Router objective RO4's report (spec §8.9): serving (stop's share at each boundary, session length, each
    policy's share, by day), and the forecast, action-value and recommendation-value evaluations kept apart, with
    counts and versioned comparators; at RO5's tag, its calibration (the arms per day and their minutes, the price,
    the return model, the weight's scores, the goal-date read, the no_intervention floor); at RO6's tag, the learned
    tail (its narrow claim, the fits by version and their change points, w^'s history, the partial-history
    cross-check). Read-only; no model call."""

    from learnloop.clock import utc_now_iso
    from learnloop.router_objective import objective_report

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        now = utc_now_iso()
        from learnloop.router_objective_switches import calibration_tag

        with closing(connect(path, read_only=True)) as connection:
            forecasts = _objective_forecasts(connection, loaded, path, now)
            report = objective_report.build(connection, now=now, forecasts=forecasts,
                                            weight=_objective_weight(loaded, path, now))
            if calibration_tag(loaded.config) and report.get("status") != "no_traces_table":
                # Router objective RO5 (spec §9): each arm per day and its minutes, the price, the return model, the
                # weight's scores, the goal-date read and the no_intervention floor.
                from learnloop.router_objective import calibration_report

                report["calibration"] = calibration_report.build(connection, loaded, now=now)
            from learnloop.router_objective_switches import learned_tail_tag

            if learned_tail_tag(loaded.config) and report.get("status") != "no_traces_table":
                # Router objective RO6 (spec §10): the narrow claim, the fits by version and their change points,
                # w^'s history, the residual's share and the partial-history cross-check.
                from learnloop.router_objective import tail_report

                report["learned_tail"] = tail_report.build(connection, loaded, now=now)
            from learnloop.router_objective_switches import lesson_offers_tag

            if lesson_offers_tag(loaded.config) and report.get("status") != "no_traces_table":
                # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): offers shown, mu and P(accept), the responses, the
                # lessons they opened and the lesson curve's posterior.
                from learnloop.router_objective import offer_report

                report["lesson_offers"] = offer_report.build(connection)
        if json_output:
            _emit({"algorithm_version": loaded.config.algorithms.algorithm_version, "router_objective": report}, True)
        else:
            for line in objective_report.lines(report):
                typer.echo(line)
            if "calibration" in report:
                from learnloop.router_objective import calibration_report

                for line in calibration_report.lines(report["calibration"]):
                    typer.echo(line)
            if "learned_tail" in report:
                from learnloop.router_objective import tail_report

                for line in tail_report.lines(report["learned_tail"]):
                    typer.echo(line)
            if "lesson_offers" in report:
                from learnloop.router_objective import offer_report

                for line in offer_report.lines(report["lesson_offers"]):
                    typer.echo(line)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@router_app.command("embed-decisions")
def router_embed_decisions(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Count the decisions without a vector and estimate calls, tokens and "
                                             "cost; send and write nothing.")
    ] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Embed at most this many decisions.")] = None,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1, max=256)] = 32,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 2_000,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 2_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 0.25,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive USD input-token estimate for an unknown/changed model price; still subject to the cost cap.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Backfill the decision/context vectors similar-decision retrieval reads (router R2c).

    Each logged plan decision whose learner-state card is still stored gets
    the embedding of its canonical context. A paid, metered call on the
    embedding route, through the shared embedding backfill: the caps are
    enforced before each request, and paid work needs embedding.enabled and
    embedding.backfill_enabled. --dry-run first: it prices the run."""

    from learnloop.ai.spend import SpendCaps
    from learnloop.daily_plan import router_retrieval
    from learnloop.db.repositories import Repository

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=0, max_retries=max_retries, max_calls=max_calls,
            max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        loaded = load_vault(vault, load_environment=not dry_run)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        if not path.exists():
            raise ValueError("the vault has no state database")
        report = router_retrieval.backfill(
            loaded, Repository.attach(path), caps=caps, dry_run=dry_run, limit=limit, batch_size=batch_size,
            price_per_million=price_per_million,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
    _emit(report, json_output)
    if report.get("status") == "cancelled":
        raise typer.Exit(code=130)
    if report.get("status") not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)
