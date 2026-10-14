"""`learnloop router log` and `learnloop router card`: the router's logged decisions.

``log`` lists router R1's logged decisions and their outcomes; ``card`` prints
the learner-state card a decision stored (router R2a). Read-only: the
database is opened read-only, never migrated, and no model is called.
Outcomes are derived on the fly from the ledgers (the same derivation the
``router_outcomes`` replayer caches), so the listing is current even when the
cache was last rebuilt days ago.
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
    help="Action router (R1: logged decisions and their outcomes; R2a: the learner-state card each decision stored).",
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
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The newest logged router decisions, with their R_next / R_cold / S outcomes."""

    from learnloop.db.stores.router import router_decision_rows
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
