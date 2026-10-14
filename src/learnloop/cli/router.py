"""`learnloop router log`, `card` and `embed-decisions`: the router's logged decisions.

``log`` lists router R1's logged decisions and their outcomes; ``card`` prints
the learner-state card a decision stored (router R2a). Both are read-only: the
database is opened read-only, never migrated, and no model is called.
Outcomes are derived on the fly from the ledgers (the same derivation the
``router_outcomes`` replayer caches), so the listing is current even when the
cache was last rebuilt days ago. ``embed-decisions`` (router R2c) backfills
the ``decision/context`` vectors of logged decisions that have none: a paid
embedding call behind ``embedding.enabled``, with ``--dry-run`` to count and
estimate first.
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
        "stored; R2c: the decision/context embedding backfill)."
    ),
)


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


@router_app.command("embed-decisions")
def router_embed_decisions(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Count the decisions without a vector and estimate; send and write nothing.")
    ] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Embed at most this many decisions.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Backfill the decision/context vectors similar-decision retrieval reads (router R2c).

    Each logged plan decision whose learner-state card is still stored gets
    the embedding of its canonical context. Needs embedding.enabled (a paid,
    metered call on the embedding route); --dry-run first."""

    from learnloop.daily_plan import router_retrieval
    from learnloop.db.repositories import Repository

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=not dry_run)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        if not path.exists():
            raise ValueError("the vault has no state database")
        repository = Repository.attach(path)
        client = None
        if not dry_run and loaded.config.embedding.enabled:
            from learnloop.ai.execution import record_model_calls
            from learnloop.ai.routing import ready_client_for_task
            from learnloop.ids import new_ulid

            resolved = ready_client_for_task(loaded.root, loaded.config, "embedding")
            client = resolved.client if resolved.ready else None
            with record_model_calls(repository, owner_kind="cli", owner_id=f"router_embed_decisions:{new_ulid()}"):
                report = router_retrieval.backfill(loaded, repository, client, dry_run=False, limit=limit)
        else:
            report = router_retrieval.backfill(loaded, repository, None, dry_run=True, limit=limit)
            if not dry_run:
                report["status"] = "disabled"
                report["reason"] = "embedding.enabled is off: nothing was sent"
        report["embedding_enabled"] = bool(loaded.config.embedding.enabled)
        _emit(report, json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
