"""FG1's records (migration 241). No policy here; ``learnloop.followup_serve`` owns it.

Every writer runs on the caller's connection. The workflow row is mutable state
(WORKFLOW) with its moves appended to ``followup_workflow_events``; the identity, burn
and binding tables are append-only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import sqlite3
from typing import Any

from learnloop.ids import new_ulid

WORKFLOW_TABLE = "followup_workflows"
#: A state a workflow never leaves: its intervention has its one outcome.
TERMINAL_STATES: frozenset[str] = frozenset({"refused", "failed", "skipped", "settled"})
OPEN_STATES: frozenset[str] = frozenset({"pending", "ready", "waiting"})
#: Fields a transition may set alongside the state.
WORKFLOW_FIELDS: frozenset[str] = frozenset({
    "settled_reason", "lane", "factor_id", "decision_id", "chosen_ref", "practice_item_id", "probe_candidate_id",
    "hypothesis_set_id", "probe_episode_id", "presentation_id", "feedback_held", "feedback_released_at",
    "release_reason", "shown_anyway_at", "exposed_at", "next_requested_at", "feedback_debited_at",
})


def present(connection: sqlite3.Connection, table: str = WORKFLOW_TABLE) -> bool:
    row = connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None


def _row(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _rows(cursor: Iterable[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor]


# -- the workflow --------------------------------------------------------------------


def insert_workflow(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """The workflow's row; a repeat of its attempt and revision is a no-op (retry and
    crash recovery reuse the identity). Returns whether a row was written."""

    cursor = connection.execute(
        "INSERT INTO followup_workflows (id, source_attempt_id, revision_key, learning_object_id, session_id, "
        "surface, origin, state, lane, feedback_held, created_at, updated_at) "
        "VALUES (:id, :source_attempt_id, :revision_key, :learning_object_id, :session_id, :surface, :origin, "
        "'pending', :lane, :feedback_held, :created_at, :created_at) "
        "ON CONFLICT(source_attempt_id, revision_key) DO NOTHING",
        {"lane": None, **row},
    )
    if cursor.rowcount > 0:
        insert_event(connection, str(row["id"]), None, "pending", "opened", {"origin": row["origin"]},
                     str(row["created_at"]))
        return True
    return False


def workflow(connection: sqlite3.Connection, workflow_id: str) -> dict[str, Any] | None:
    return _row(connection.execute("SELECT * FROM followup_workflows WHERE id = ?", (workflow_id,)).fetchone())


def workflow_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None:
    """The attempt's newest workflow (a regrade's revision is the newest)."""

    return _row(connection.execute(
        "SELECT * FROM followup_workflows WHERE source_attempt_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (attempt_id,),
    ).fetchone())


def workflow_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        "SELECT * FROM followup_workflows WHERE practice_item_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (practice_item_id,),
    ).fetchone())


def any_feedback_held(connection: sqlite3.Connection) -> bool:
    """A miss's causes are still held from the learner, somewhere."""

    return connection.execute(
        "SELECT 1 FROM followup_workflows WHERE feedback_held = 1 AND feedback_released_at IS NULL LIMIT 1"
    ).fetchone() is not None


def workflow_for_presentation(connection: sqlite3.Connection, presentation_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        "SELECT * FROM followup_workflows WHERE presentation_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (presentation_id,),
    ).fetchone())


def open_workflows(connection: sqlite3.Connection, *, session_id: str | None = None,
                   states: Iterable[str] = OPEN_STATES) -> list[dict[str, Any]]:
    wanted = sorted(states)
    marks = ",".join("?" for _ in wanted)
    if session_id is None:
        return _rows(connection.execute(
            f"SELECT * FROM followup_workflows WHERE state IN ({marks}) ORDER BY created_at, id", wanted))
    return _rows(connection.execute(
        f"SELECT * FROM followup_workflows WHERE session_id = ? AND state IN ({marks}) ORDER BY created_at, id",
        [session_id, *wanted],
    ))


def update_workflow(connection: sqlite3.Connection, workflow_id: str, *, at: str, **fields: Any) -> None:
    unknown = set(fields) - WORKFLOW_FIELDS
    if unknown:
        raise ValueError(f"not workflow fields: {sorted(unknown)}")
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    connection.execute(
        f"UPDATE followup_workflows SET {assignments}, updated_at = ? WHERE id = ?",
        [*fields.values(), at, workflow_id],
    )


def move_workflow(connection: sqlite3.Connection, workflow_id: str, *, from_states: Iterable[str], to_state: str,
                  reason: str, at: str, detail: Mapping[str, Any] | None = None, **fields: Any) -> bool:
    """Move a workflow from one of ``from_states``: a compare-and-set, so a late
    generator or diagnosis cannot move a workflow a fallback or a skip has settled."""

    unknown = set(fields) - WORKFLOW_FIELDS
    if unknown:
        raise ValueError(f"not workflow fields: {sorted(unknown)}")
    allowed = sorted(from_states)
    current = workflow(connection, workflow_id)
    if current is None or current["state"] not in allowed:
        return False
    assignments = "".join(f", {name} = ?" for name in fields)
    marks = ",".join("?" for _ in allowed)
    cursor = connection.execute(
        f"UPDATE followup_workflows SET state = ?, updated_at = ?{assignments} WHERE id = ? AND state IN ({marks})",
        [to_state, at, *fields.values(), workflow_id, *allowed],
    )
    if cursor.rowcount <= 0:
        return False
    insert_event(connection, workflow_id, str(current["state"]), to_state, reason, detail or {}, at)
    return True


def insert_event(connection: sqlite3.Connection, workflow_id: str, from_state: str | None, to_state: str,
                 reason: str, detail: Mapping[str, Any], at: str) -> None:
    connection.execute(
        "INSERT INTO followup_workflow_events (id, workflow_id, from_state, to_state, reason, detail_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_ulid(), workflow_id, from_state, to_state, reason, json.dumps(dict(detail), sort_keys=True), at),
    )


def workflow_events(connection: sqlite3.Connection, workflow_id: str) -> list[dict[str, Any]]:
    return _rows(connection.execute(
        "SELECT * FROM followup_workflow_events WHERE workflow_id = ? ORDER BY created_at, id", (workflow_id,)))


# -- the generation queue --------------------------------------------------------------


def enqueue_generation_job(connection: sqlite3.Connection, *, kind: str, dedupe_key: str, at: str,
                           workflow_id: str | None = None, probe_episode_id: str | None = None,
                           need_id: str | None = None, not_before: str | None = None) -> str | None:
    """One row per deduplicated key; returns the new id, None for a repeat."""

    job_id = new_ulid()
    cursor = connection.execute(
        "INSERT INTO followup_generation_jobs (id, kind, dedupe_key, workflow_id, probe_episode_id, need_id, state, "
        "not_before, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?) "
        "ON CONFLICT(dedupe_key) DO NOTHING",
        (job_id, kind, dedupe_key, workflow_id, probe_episode_id, need_id, not_before, at, at),
    )
    return job_id if cursor.rowcount > 0 else None


def lease_next_generation_job(connection: sqlite3.Connection, *, owner: str, now: str, lease_expires_at: str
                              ) -> dict[str, Any] | None:
    """Lease the oldest runnable job, or reclaim one whose lease lapsed. A serial
    claim: the caller runs it in an immediate transaction."""

    row = connection.execute(
        "SELECT * FROM followup_generation_jobs "
        "WHERE (state = 'queued' AND (not_before IS NULL OR not_before <= ?)) "
        "   OR (state = 'leased' AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?) "
        "ORDER BY created_at, id LIMIT 1",
        (now, now),
    ).fetchone()
    if row is None:
        return None
    connection.execute(
        "UPDATE followup_generation_jobs SET state = 'leased', lease_owner = ?, lease_expires_at = ?, "
        "lease_epoch = lease_epoch + 1, attempt_count = attempt_count + 1, updated_at = ? WHERE id = ?",
        (owner, lease_expires_at, now, row["id"]),
    )
    return _row(connection.execute("SELECT * FROM followup_generation_jobs WHERE id = ?", (row["id"],)).fetchone())


def finish_generation_job(connection: sqlite3.Connection, job: Mapping[str, Any], *, state: str, at: str,
                          error: str | None = None, not_before: str | None = None) -> bool:
    """Settle or requeue a leased job, fenced on its lease epoch."""

    cursor = connection.execute(
        "UPDATE followup_generation_jobs SET state = ?, last_error = ?, not_before = ?, lease_owner = NULL, "
        "lease_expires_at = NULL, updated_at = ? WHERE id = ? AND lease_epoch = ?",
        (state, error, not_before, at, job["id"], job["lease_epoch"]),
    )
    return cursor.rowcount > 0


def cancel_generation_jobs(connection: sqlite3.Connection, *, workflow_id: str | None = None,
                           probe_episode_id: str | None = None, reason: str, at: str) -> int:
    """Queued work whose reason has gone (its hypotheses closed, a skip): never run."""

    clauses, values = [], []
    if workflow_id is not None:
        clauses.append("workflow_id = ?")
        values.append(workflow_id)
    if probe_episode_id is not None:
        clauses.append("probe_episode_id = ?")
        values.append(probe_episode_id)
    if not clauses:
        return 0
    cursor = connection.execute(
        f"UPDATE followup_generation_jobs SET state = 'skipped', last_error = ?, updated_at = ? "
        f"WHERE state = 'queued' AND ({' OR '.join(clauses)})",
        [reason, at, *values],
    )
    return int(cursor.rowcount)


def runnable_generation_jobs(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM followup_generation_jobs WHERE state IN ('queued', 'leased')").fetchone()
    return int(row[0]) if row is not None else 0


def generation_job(connection: sqlite3.Connection, dedupe_key: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        "SELECT * FROM followup_generation_jobs WHERE dedupe_key = ?", (dedupe_key,)).fetchone())


# -- the single-use identity -------------------------------------------------------------


def insert_generated_probe(connection: sqlite3.Connection, *, practice_item_id: str, item_revision: str, source: str,
                           at: str, workflow_id: str | None = None, probe_episode_id: str | None = None) -> bool:
    cursor = connection.execute(
        "INSERT INTO generated_probe_items (practice_item_id, item_revision, source, workflow_id, probe_episode_id, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(practice_item_id) DO NOTHING",
        (practice_item_id, item_revision, source, workflow_id, probe_episode_id, at),
    )
    return cursor.rowcount > 0


def generated_probe(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    return _row(connection.execute(
        "SELECT * FROM generated_probe_items WHERE practice_item_id = ?", (practice_item_id,)).fetchone())


def unclosed_probes_of_workflow(connection: sqlite3.Connection, workflow_id: str) -> list[str]:
    """A workflow's generated probes with no burn: what an interrupted run left behind."""

    return [str(row[0]) for row in connection.execute(
        "SELECT i.practice_item_id FROM generated_probe_items i WHERE i.workflow_id = ? AND NOT EXISTS "
        "(SELECT 1 FROM generated_probe_burns b WHERE b.practice_item_id = i.practice_item_id) "
        "ORDER BY i.created_at, i.practice_item_id",
        (workflow_id,),
    )]


def administration_ended(connection: sqlite3.Connection, practice_item_id: str) -> bool:
    """Some presentation of this item was answered or ended: its one administration is over."""

    return connection.execute(
        "SELECT 1 FROM probe_presentations WHERE practice_item_id = ? AND status IN ('submitted', 'ended') LIMIT 1",
        (practice_item_id,),
    ).fetchone() is not None


def generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]:
    return frozenset(str(row[0]) for row in connection.execute("SELECT practice_item_id FROM generated_probe_items"))


def insert_burn(connection: sqlite3.Connection, *, practice_item_id: str, kind: str, item_revision: str, reason: str,
                at: str, surface: str | None = None, presentation_id: str | None = None,
                workflow_id: str | None = None) -> bool:
    """The atomic claim: the UNIQUE (item, kind) decides the one winner."""

    cursor = connection.execute(
        "INSERT INTO generated_probe_burns (id, practice_item_id, kind, item_revision, surface, presentation_id, "
        "workflow_id, reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(practice_item_id, kind) DO NOTHING",
        (new_ulid(), practice_item_id, kind, item_revision, surface, presentation_id, workflow_id, reason, at),
    )
    return cursor.rowcount > 0


def burns_for_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, dict[str, Any]]:
    return {
        str(row["kind"]): dict(row)
        for row in connection.execute(
            "SELECT * FROM generated_probe_burns WHERE practice_item_id = ?", (practice_item_id,))
    }


def closed_generated_probe_ids(connection: sqlite3.Connection) -> frozenset[str]:
    """Every generated probe with a burn or a retirement."""

    return frozenset(
        str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM generated_probe_burns"))


# -- the router binding ------------------------------------------------------------------


def append_binding(connection: sqlite3.Connection, *, decision_id: str, workflow_id: str, binding_kind: str, at: str,
                   practice_item_id: str | None = None, probe_presentation_id: str | None = None,
                   plan_presentation_id: str | None = None, outcome: str | None = None) -> bool:
    cursor = connection.execute(
        "INSERT INTO router_decision_bindings (id, decision_id, workflow_id, binding_kind, practice_item_id, "
        "probe_presentation_id, plan_presentation_id, outcome, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(decision_id, binding_kind) DO NOTHING",
        (new_ulid(), decision_id, workflow_id, binding_kind, practice_item_id, probe_presentation_id,
         plan_presentation_id, outcome, at),
    )
    return cursor.rowcount > 0


def bindings_for_decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, dict[str, Any]]:
    return {
        str(row["binding_kind"]): dict(row)
        for row in connection.execute("SELECT * FROM router_decision_bindings WHERE decision_id = ?", (decision_id,))
    }


def all_bindings(connection: sqlite3.Connection) -> dict[str, dict[str, dict[str, Any]]]:
    """Every decision's bindings, keyed by decision id and then kind (the outcome join's one read)."""

    if not present(connection, "router_decision_bindings"):
        return {}
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for row in connection.execute("SELECT * FROM router_decision_bindings ORDER BY created_at, id"):
        out.setdefault(str(row["decision_id"]), {})[str(row["binding_kind"])] = dict(row)
    return out
