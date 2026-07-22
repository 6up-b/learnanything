"""P4 steps 1-2 -- persistence for the staged-controller substrate (spec §3.2).

Thin SQL layer over the ``controller_*`` / ``attention_*`` tables (migration 096).
Kept out of the 18k-line ``repositories.py`` because these are all NEW controller
tables; every function operates through the public ``repository.connection()`` so no
existing repository method is touched.

Two bounded bulk readers (``bulk_commitment_rows`` / ``bulk_exposure_events``) back
the ``ControllerSnapshot`` builder's §3.1 operability bar: one full-table read each,
never one query per candidate.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.activities import _json

# ---------------------------------------------------------------------------
# Bounded bulk reads (§3.1: no per-candidate query).
# ---------------------------------------------------------------------------


def bulk_commitment_rows(repository: Repository) -> list[dict[str, Any]]:
    """All commitment header rows in one read."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, learner_id, created_action, created_at FROM commitments "
            "ORDER BY created_at, id"
        ).fetchall()
    return [dict(r) for r in rows]


def bulk_exposure_events(repository: Repository) -> list[dict[str, Any]]:
    """The whole ``activity_exposure_events`` ledger in one read (the ONE ledger,
    §3.6). Indexed in-memory by surface hash/fingerprint for feasibility checks so no
    per-candidate exposure query is issued during selection."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT surface_id, surface_hash, fingerprint, kind, purpose, "
            "consumes_unseen, created_at FROM activity_exposure_events "
            "ORDER BY created_at, id"
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Snapshot (§3.1 / §3.2).
# ---------------------------------------------------------------------------


def upsert_snapshot(
    repository: Repository,
    *,
    snapshot_hash: str,
    session_id: str | None,
    body: Mapping[str, Any],
    param_manifest_hash: str | None,
    projection_versions: Mapping[str, Any],
    clock: Clock | None = None,
) -> str:
    """Persist a snapshot, deduped on its content hash. Identical inputs reuse the
    same row -- the snapshot is an immutable content-addressed object."""

    with repository.connection() as connection:
        existing = connection.execute(
            "SELECT id FROM controller_snapshots WHERE snapshot_hash = ?",
            (snapshot_hash,),
        ).fetchone()
        if existing is not None:
            return existing["id"]
        snapshot_id = new_ulid()
        connection.execute(
            "INSERT INTO controller_snapshots(id, snapshot_hash, session_id, body_json, "
            "param_manifest_hash, projection_versions_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                snapshot_id, snapshot_hash, session_id, _json(dict(body)),
                param_manifest_hash, _json(dict(projection_versions)), utc_now_iso(clock),
            ),
        )
        connection.commit()
    return snapshot_id


def snapshot_row(repository: Repository, snapshot_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM controller_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# Constraint manifest (§5).
# ---------------------------------------------------------------------------


def upsert_constraint_manifest(
    repository: Repository,
    *,
    manifest_hash: str,
    definitions: Any,
    clock: Clock | None = None,
) -> str:
    with repository.connection() as connection:
        existing = connection.execute(
            "SELECT id FROM controller_constraint_manifests WHERE manifest_hash = ?",
            (manifest_hash,),
        ).fetchone()
        if existing is not None:
            return existing["id"]
        manifest_id = new_ulid()
        connection.execute(
            "INSERT INTO controller_constraint_manifests(id, manifest_hash, "
            "definitions_json, created_at) VALUES (?, ?, ?, ?)",
            (manifest_id, manifest_hash, _json(definitions), utc_now_iso(clock)),
        )
        connection.commit()
    return manifest_id


# ---------------------------------------------------------------------------
# Attention blocks (§4.1).
# ---------------------------------------------------------------------------


def create_attention_block(
    repository: Repository,
    *,
    session_id: str | None,
    commitment_id: str | None,
    action: str,
    subtype: str | None,
    budget_minutes: float,
    neighborhood: Mapping[str, Any],
    exit_rules: Any,
    short_circuit_reason: str | None,
    content_hash: str,
    clock: Clock | None = None,
) -> str:
    block_id = new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO attention_blocks(id, session_id, commitment_id, action, subtype, "
            "budget_minutes, neighborhood_json, exit_rules_json, short_circuit_reason, "
            "content_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                block_id, session_id, commitment_id, action, subtype, budget_minutes,
                _json(dict(neighborhood)), _json(exit_rules), short_circuit_reason,
                content_hash, utc_now_iso(clock),
            ),
        )
        connection.commit()
    return block_id


def append_block_event(
    repository: Repository,
    *,
    block_id: str,
    kind: str,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    connection = repository.connection()
    try:
        connection.execute("BEGIN")
        row = connection.execute(
            "SELECT COALESCE(MAX(event_ordinal), 0) AS m FROM attention_block_events "
            "WHERE block_id = ?",
            (block_id,),
        ).fetchone()
        ordinal = int(row["m"]) + 1
        event_id = new_ulid()
        connection.execute(
            "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, "
            "detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, block_id, ordinal, kind,
             _json(dict(detail)) if detail is not None else None, utc_now_iso(clock)),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return event_id


def block_events(repository: Repository, block_id: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM attention_block_events WHERE block_id = ? ORDER BY event_ordinal",
            (block_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Decisions + candidates (§3.2 / §3.3). One idempotent boundary keyed on
# receipt_key: a retry after commit returns the standing decision (§14.4).
# ---------------------------------------------------------------------------


def decision_by_receipt_key(
    repository: Repository, receipt_key: str
) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM controller_decisions WHERE receipt_key = ?", (receipt_key,)
        ).fetchone()
    return dict(row) if row is not None else None


def persist_decision(
    repository: Repository,
    *,
    receipt_key: str | None,
    snapshot_id: str,
    snapshot_hash: str,
    session_id: str | None,
    mode: str,
    commitment_id: str | None,
    staged_rule: str,
    action: str,
    subtype: str | None,
    attention_block_id: str | None,
    chosen_candidate_ref: str | None,
    stop_reason: str | None,
    constraint_manifest_hash: str | None,
    decision_params_hash: str | None,
    policy_version: str | None,
    comparator: Mapping[str, Any] | None,
    trace: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Write the decision + all candidate rows in one transaction. Idempotent on
    ``receipt_key``: a replayed decision returns the standing row without a second
    write, and never a different candidate (§14.4)."""

    now = utc_now_iso(clock)
    connection = repository.connection()
    try:
        connection.execute("BEGIN")
        if receipt_key is not None:
            existing = connection.execute(
                "SELECT * FROM controller_decisions WHERE receipt_key = ?", (receipt_key,)
            ).fetchone()
            if existing is not None:
                connection.commit()
                return {"decision_id": existing["id"], "already": True,
                        "chosen_candidate_ref": existing["chosen_candidate_ref"]}
        decision_id = new_ulid()
        connection.execute(
            "INSERT INTO controller_decisions(id, receipt_key, snapshot_id, snapshot_hash, "
            "session_id, mode, commitment_id, staged_rule, action, subtype, "
            "attention_block_id, chosen_candidate_ref, stop_reason, constraint_manifest_hash, "
            "decision_params_hash, policy_version, comparator_json, trace_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                decision_id, receipt_key, snapshot_id, snapshot_hash, session_id, mode,
                commitment_id, staged_rule, action, subtype, attention_block_id,
                chosen_candidate_ref, stop_reason, constraint_manifest_hash,
                decision_params_hash, policy_version,
                _json(dict(comparator)) if comparator is not None else None,
                _json(dict(trace)), now,
            ),
        )
        for cand in candidates:
            connection.execute(
                "INSERT INTO controller_candidates(id, decision_id, candidate_ref, "
                "learning_object_id, feasible, exclusion_reasons_json, "
                "within_mode_metrics_json, comparator_score, selected, rank_ordinal, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_ulid(), decision_id, cand["candidate_ref"],
                    cand.get("learning_object_id"),
                    1 if cand.get("feasible") else 0,
                    _json(cand.get("exclusion_reasons", [])),
                    _json(cand.get("within_mode_metrics", {})),
                    cand.get("comparator_score"),
                    1 if cand.get("selected") else 0,
                    cand.get("rank_ordinal"), now,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"decision_id": decision_id, "already": False,
            "chosen_candidate_ref": chosen_candidate_ref}


def decision_row(repository: Repository, decision_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM controller_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
    return dict(row) if row is not None else None


def candidates_for_decision(
    repository: Repository, decision_id: str
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_candidates WHERE decision_id = ? "
            "ORDER BY rank_ordinal IS NULL, rank_ordinal, id",
            (decision_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Shadow predictions (§7, invariant 3): zero authority.
# ---------------------------------------------------------------------------


def persist_shadow_prediction(
    repository: Repository,
    *,
    decision_id: str | None,
    snapshot_hash: str,
    scorer_kind: str,
    model_version: str | None,
    prediction: Mapping[str, Any],
    usable: bool = True,
    clock: Clock | None = None,
) -> str:
    prediction_id = new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO controller_shadow_predictions(id, decision_id, snapshot_hash, "
            "scorer_kind, model_version, authority, prediction_json, usable, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'none', ?, ?, ?)",
            (
                prediction_id, decision_id, snapshot_hash, scorer_kind, model_version,
                _json(dict(prediction)), 1 if usable else 0, utc_now_iso(clock),
            ),
        )
        connection.commit()
    return prediction_id


def shadow_predictions_for_decision(
    repository: Repository, decision_id: str
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_shadow_predictions WHERE decision_id = ? "
            "ORDER BY created_at, id",
            (decision_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Randomization layer (§9.3, U-024, migration 098). The true propensity is written
# BEFORE selection so off-policy joins stay valid across the whole controller seam.
# ---------------------------------------------------------------------------


def persist_experiment_assignment(
    repository: Repository,
    *,
    experiment_id: str,
    decision_id: str | None,
    unit_kind: str,
    unit_id: str | None,
    variant: str,
    propensity: float,
    seed: str,
    draw: float | None,
    epsilon_margin: float | None,
    near_equivalent: bool,
    design: str,
    grade: str,
    candidate_refs: Any = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Write one randomization assignment with its true propensity (§9.3)."""

    assignment_id = new_ulid()
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO policy_experiment_assignments(id, experiment_id, decision_id, "
            "unit_kind, unit_id, variant, propensity, seed, draw, epsilon_margin, "
            "near_equivalent, design, grade, candidate_refs_json, detail_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                assignment_id, experiment_id, decision_id, unit_kind, unit_id, variant,
                float(propensity), seed, draw, epsilon_margin,
                1 if near_equivalent else 0, design, grade,
                _json(candidate_refs if candidate_refs is not None else []),
                _json(dict(detail) if detail is not None else {}), utc_now_iso(clock),
            ),
        )
        connection.commit()
    return assignment_id


def assignment_row(repository: Repository, assignment_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM policy_experiment_assignments WHERE id = ?", (assignment_id,)
        ).fetchone()
    return dict(row) if row is not None else None


def assignments_for_experiment(
    repository: Repository, experiment_id: str
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM policy_experiment_assignments WHERE experiment_id = ? "
            "ORDER BY created_at, id",
            (experiment_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Delayed outcome windows (§3.2/§9.3): anchored to the NEXT SPACED COLD REVIEW.
# ---------------------------------------------------------------------------


def open_outcome_window(
    repository: Repository,
    *,
    decision_id: str | None,
    assignment_id: str | None,
    candidate_ref: str | None,
    commitment_id: str | None,
    card_ref: str | None,
    anchor_kind: str,
    anchor_ref: str | None,
    due_at: str | None,
    hypothesis_grade: bool,
    clock: Clock | None = None,
) -> str:
    window_id = new_ulid()
    now = utc_now_iso(clock)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO controller_outcome_windows(id, decision_id, assignment_id, "
            "candidate_ref, commitment_id, card_ref, horizon_kind, anchor_kind, "
            "anchor_ref, opened_at, due_at, status, hypothesis_grade, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'next_spaced_cold_review', ?, ?, ?, ?, 'pending', ?, ?)",
            (
                window_id, decision_id, assignment_id, candidate_ref, commitment_id,
                card_ref, anchor_kind, anchor_ref, now, due_at,
                1 if hypothesis_grade else 0, now,
            ),
        )
        connection.commit()
    return window_id


def resolve_outcome_window(
    repository: Repository,
    window_id: str,
    *,
    outcome: Mapping[str, Any],
    status: str = "resolved",
    clock: Clock | None = None,
) -> None:
    with repository.connection() as connection:
        connection.execute(
            "UPDATE controller_outcome_windows SET status = ?, outcome_json = ?, "
            "resolved_at = ? WHERE id = ?",
            (status, _json(dict(outcome)), utc_now_iso(clock), window_id),
        )
        connection.commit()


def outcome_window_row(repository: Repository, window_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM controller_outcome_windows WHERE id = ?", (window_id,)
        ).fetchone()
    return dict(row) if row is not None else None


def outcome_windows_for_decision(
    repository: Repository, decision_id: str
) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_outcome_windows WHERE decision_id = ? "
            "ORDER BY created_at, id",
            (decision_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def pending_outcome_windows(repository: Repository) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM controller_outcome_windows WHERE status = 'pending' "
            "ORDER BY due_at IS NULL, due_at, id"
        ).fetchall()
    return [dict(r) for r in rows]
