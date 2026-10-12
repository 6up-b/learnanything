"""Persistence for authored family revisions and append-only membership."""
from __future__ import annotations

import json
import sqlite3
from typing import Any
from uuid import uuid4


def restore_proposal(connection: sqlite3.Connection, *, proposal_id: str,
                     family_id: str, state: str, plan_json: str, created_at: str) -> None:
    """Replace only the mutable workflow cache from an authoritative ledger plan."""
    connection.execute(
        "INSERT INTO family_proposals(id,family_id,state,plan_json,created_at) VALUES (?,?,?,?,?) "
        "ON CONFLICT(id) DO UPDATE SET family_id=excluded.family_id,state=excluded.state,"
        "plan_json=excluded.plan_json,created_at=excluded.created_at",
        (proposal_id, family_id, state, plan_json, created_at),
    )


def ensure_authored_identity(connection: sqlite3.Connection, *, family_id: str,
                             title: str, created_at: str) -> None:
    validate_authored_identity(connection, family_id)
    connection.execute(
        "INSERT OR IGNORE INTO activity_families(id,purpose,title,created_at) VALUES (?,'practice',?,?)",
        (family_id, title, created_at),
    )


def create_proposal(connection: sqlite3.Connection, *, proposal_id: str,
                    family_id: str, plan_json: str, created_at: str) -> None:
    connection.execute("INSERT INTO family_proposals VALUES (?,?,?,?,?)",
                       (proposal_id, family_id, "applying", plan_json, created_at))


def update_proposal_state(connection: sqlite3.Connection, *, proposal_id: str,
                          state: str, plan_json: str | None = None) -> None:
    if plan_json is None:
        connection.execute("UPDATE family_proposals SET state=? WHERE id=?", (state, proposal_id))
    else:
        connection.execute("UPDATE family_proposals SET state=?,plan_json=? WHERE id=?",
                           (state, plan_json, proposal_id))


def validate_authored_identity(connection: sqlite3.Connection, family_id: str) -> None:
    existing = connection.execute("SELECT purpose,legacy_kind FROM activity_families WHERE id=?", (family_id,)).fetchone()
    if existing is not None and (existing["purpose"] != "practice" or existing["legacy_kind"] is not None):
        raise ValueError("Authored family identity collides with a legacy or other-purpose family")
    for row in connection.execute(
        "SELECT family_spec_json FROM activity_family_versions WHERE family_id=?", (family_id,),
    ):
        spec = json.loads(row["family_spec_json"])
        if not isinstance(spec, dict) or not {
            "id", "learning_object_id", "idea_statement", "retrieval_target", "source_kind", "reference",
        } <= spec.keys() or spec["id"] != family_id:
            raise ValueError("Authored family identity collides with another version namespace")


def record_revision(connection: sqlite3.Connection, *, family_id: str,
                    spec_json: str, title: str, created_at: str) -> str:
    ensure_authored_identity(connection, family_id=family_id, title=title, created_at=created_at)
    latest = connection.execute(
        "SELECT * FROM activity_family_versions WHERE family_id=? ORDER BY version DESC LIMIT 1",
        (family_id,),
    ).fetchone()
    if latest is not None and latest["family_spec_json"] == spec_json:
        return str(latest["id"])
    revision_id = str(uuid4())
    connection.execute(
        "INSERT INTO activity_family_versions(id,family_id,version,family_spec_json,created_at) VALUES (?,?,?,?,?)",
        (revision_id, family_id, 1 if latest is None else latest["version"] + 1, spec_json, created_at),
    )
    return revision_id


def append_membership(connection: sqlite3.Connection, *, family_id: str,
                      member: dict[str, Any], action: str, proposal_id: str,
                      judgment_id: str, created_at: str) -> None:
    purpose = connection.execute(
        "SELECT f.purpose FROM activity_cards c JOIN activity_families f ON f.id=c.family_id WHERE c.id=?",
        (member["card_id"],),
    ).fetchone()
    if purpose is None or purpose["purpose"] != "practice":
        raise ValueError("Family membership is restricted to practice cards")
    existing = connection.execute(
        "SELECT * FROM activity_family_membership_events WHERE proposal_id=? AND card_id=? AND action=?",
        (proposal_id, member["card_id"], action),
    ).fetchone()
    if existing is not None:
        expected = (family_id, member["item_id"], member["variant_relation"], judgment_id)
        if tuple(existing[key] for key in ("family_id", "practice_item_id", "variant_relation", "judgment_id")) != expected:
            raise ValueError("Membership retry disagrees with immutable event")
        return
    connection.execute(
        "INSERT INTO activity_family_membership_events "
        "(id,family_id,card_id,practice_item_id,variant_relation,action,proposal_id,judgment_id,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (str(uuid4()), family_id, member["card_id"], member["item_id"],
         member["variant_relation"], action, proposal_id, judgment_id, created_at),
    )


def current_memberships(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Latest event wins; removals do not fall back to an older addition."""
    return [dict(row) for row in connection.execute(
        "SELECT e.* FROM activity_family_membership_events e "
        "WHERE e.seq=(SELECT MAX(n.seq) FROM activity_family_membership_events n WHERE n.card_id=e.card_id) "
        "AND e.action='add' ORDER BY e.card_id"
    )]


def family_judge_models(connection: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
    """Resolved producer IDs from immutable accept plans, never workflow caches."""
    models: dict[str, set[str]] = {}
    for row in connection.execute(
        "SELECT rationale FROM judgment_ledger WHERE task='family_decision' AND verdict='accept'"
    ):
        plan = json.loads(row["rationale"])["plan"]
        family_id = plan["family"]["id"]
        found = models.setdefault(family_id, set())
        for judgment_id in plan["judgment_ids"]:
            judgment = connection.execute(
                "SELECT judge_model FROM judgment_ledger WHERE id=?", (judgment_id,),
            ).fetchone()
            if judgment is not None and judgment["judge_model"]:
                found.add(judgment["judge_model"])
    return {key: tuple(sorted(value)) for key, value in models.items()}
