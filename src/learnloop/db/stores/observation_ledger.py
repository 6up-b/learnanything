"""Bulk read models for the canonical evidence projection.

The canonical facet projection replays every attempt, so its persistence seam
must not issue queries from inside the replay loop.  This module owns the SQL
and row assembly for that read model; :mod:`learnloop.db.repositories` only
opens the connection and delegates here.

All ordering that can affect replay has an explicit primary-key tie-breaker.
The authoritative reader also chooses the newest observation for an attempt
when legacy/corrupt data contains more than one.  New writes intend a one-to-one
relationship, but the schema does not enforce it, so an unordered ``LIMIT 1``
would make the projected evidence depend on SQLite's query plan.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from typing import Any, Iterable


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


def load_canonical_observation_ledger(
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Load attempts plus live grading evidence in two queries.

    The old implementation queried ``grading_evidence`` once per attempt.  A
    complete replay is now a pair of ordered scans regardless of history size.
    """

    attempt_rows = connection.execute(
        """
        SELECT id, practice_item_id, learning_object_id, attempt_type,
               practice_mode, hints_used, primed, created_at
          FROM practice_attempts
         ORDER BY created_at ASC, id ASC
        """
    ).fetchall()
    if not attempt_rows:
        return []

    evidence_by_attempt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence_rows = connection.execute(
        """
        SELECT id, attempt_id, criterion_id, points_awarded, attribution_json,
               correlation_group, recipe_id, observation_id, grading_revision,
               assessment_contract_version_id, created_at
          FROM grading_evidence
         WHERE superseded_at IS NULL
         ORDER BY attempt_id ASC, created_at ASC, criterion_id ASC, id ASC
        """
    ).fetchall()
    for row in evidence_rows:
        evidence_by_attempt[str(row["attempt_id"])].append(
            {
                "criterion_id": row["criterion_id"],
                "points_awarded": row["points_awarded"],
                "attribution_json": _loads(row["attribution_json"], None),
                "correlation_group": row["correlation_group"],
                "recipe_id": row["recipe_id"],
                "observation_id": row["observation_id"],
                "grading_revision": row["grading_revision"],
                "assessment_contract_version_id": row[
                    "assessment_contract_version_id"
                ],
            }
        )

    return [
        {
            "attempt_id": row["id"],
            "practice_item_id": row["practice_item_id"],
            "learning_object_id": row["learning_object_id"],
            "attempt_type": row["attempt_type"],
            "practice_mode": row["practice_mode"],
            "hints_used": row["hints_used"] or 0,
            # Priming is evidence provenance, not a mastery cache field.  The
            # certification policy needs it to keep a repair-assisted retry out
            # of the unassisted evidence lane during replay.
            "primed": bool(row["primed"]),
            "created_at": row["created_at"],
            "evidence": evidence_by_attempt.get(str(row["id"]), []),
        }
        for row in attempt_rows
    ]


_LATEST_OBSERVATIONS = """
WITH ranked_observations AS (
    SELECT o.*,
           ROW_NUMBER() OVER (
               PARTITION BY o.attempt_id
               ORDER BY o.created_at DESC, o.id DESC
           ) AS replay_rank
      FROM activity_observations AS o
     WHERE o.attempt_id IS NOT NULL
)
"""


def load_authoritative_observation_ledger(
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Load the P0 authoritative ledger with a fixed six-query budget.

    Interpretations, adjudications, and administrations are loaded in bulk and
    joined in memory.  Every query runs on the caller's connection so the
    repository can hold one read transaction across the complete snapshot.
    """

    ledger = load_canonical_observation_ledger(connection)
    if not ledger:
        return []

    observation_rows = connection.execute(
        _LATEST_OBSERVATIONS
        + """
        SELECT *
          FROM ranked_observations
         WHERE replay_rank = 1
         ORDER BY attempt_id ASC
        """
    ).fetchall()
    observations_by_attempt: dict[str, dict[str, Any]] = {}
    for row in observation_rows:
        payload = dict(row)
        payload.pop("replay_rank", None)
        observations_by_attempt[str(payload["attempt_id"])] = payload

    interpretation_rows = connection.execute(
        _LATEST_OBSERVATIONS
        + """
        SELECT gi.*
          FROM ranked_observations AS o
          JOIN grade_interpretations AS gi
            ON gi.id = o.active_interpretation_id
         WHERE o.replay_rank = 1
         ORDER BY gi.id ASC
        """
    ).fetchall()
    interpretations_by_id = {str(row["id"]): dict(row) for row in interpretation_rows}

    adjudication_rows = connection.execute(
        _LATEST_OBSERVATIONS
        + """
        , ranked_adjudications AS (
            SELECT ga.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY ga.observation_id
                       ORDER BY ga.created_at DESC, ga.id DESC
                   ) AS replay_rank
              FROM grade_adjudications AS ga
        )
        SELECT ga.*
          FROM ranked_observations AS o
          JOIN ranked_adjudications AS ga
            ON ga.observation_id = o.id
         WHERE o.replay_rank = 1 AND ga.replay_rank = 1
         ORDER BY ga.observation_id ASC
        """
    ).fetchall()
    adjudications_by_observation: dict[str, dict[str, Any]] = {}
    for row in adjudication_rows:
        payload = dict(row)
        payload.pop("replay_rank", None)
        adjudications_by_observation[str(payload["observation_id"])] = payload

    administration_rows = connection.execute(
        _LATEST_OBSERVATIONS
        + """
        SELECT aa.*
          FROM ranked_observations AS o
          JOIN activity_administrations AS aa ON aa.id = o.administration_id
         WHERE o.replay_rank = 1
         ORDER BY aa.id ASC
        """
    ).fetchall()
    administrations_by_id = {str(row["id"]): dict(row) for row in administration_rows}

    for attempt in ledger:
        observation = observations_by_attempt.get(str(attempt["attempt_id"]))
        interpretation = None
        adjudication = None
        administration = None
        if observation is not None:
            active_id = observation.get("active_interpretation_id")
            if active_id:
                interpretation = interpretations_by_id.get(str(active_id))
            adjudication = adjudications_by_observation.get(str(observation["id"]))
            administration = administrations_by_id.get(
                str(observation["administration_id"])
            )

        lineage: list[str] = []
        if interpretation is not None and interpretation.get("reference_prior_ids_json"):
            lineage = _loads(interpretation["reference_prior_ids_json"], [])
        attempt["administration_id"] = (
            observation["administration_id"] if observation is not None else None
        )
        attempt["target_contract_version_id"] = (
            administration.get("target_contract_version_id")
            if administration is not None
            else None
        )
        attempt["active_interpretation"] = interpretation
        attempt["active_adjudication"] = adjudication
        attempt["adjudication_trust_weight"] = (
            adjudication.get("bounded_trust_weight")
            if adjudication is not None
            else None
        )
        attempt["calibration_lineage"] = lineage
        attempt["calibration_model_id"] = (
            interpretation.get("calibration_model_id")
            if interpretation is not None
            else None
        )
        attempt["calibration_model_hash"] = (
            interpretation.get("calibration_model_hash")
            if interpretation is not None
            else None
        )
        attempt["quarantine_state"] = (
            interpretation.get("quarantine_state")
            if interpretation is not None
            else None
        )
        attempt["projection_algorithm_version"] = (
            interpretation.get("projection_algorithm_version")
            if interpretation is not None
            else None
        )
    return ledger


def load_effective_assessment_contracts(
    connection: sqlite3.Connection,
    source_version_ids: Iterable[str],
    *,
    projection_version: str,
) -> dict[str, dict[str, Any]]:
    """Resolve immutable contract snapshots for a replay in one bulk query.

    The returned mapping is keyed by the source version recorded on grading
    evidence even when an explicit correction redirects that source to another
    contract for this projection version.
    """

    version_ids = sorted({str(value) for value in source_version_ids if value})
    if not version_ids:
        return {}
    placeholders = ",".join("?" for _ in version_ids)
    rows = connection.execute(
        f"""
        SELECT source.id AS replay_source_version_id, effective.*
          FROM assessment_contract_versions AS source
          LEFT JOIN measurement_contract_corrections AS correction
            ON correction.source_contract_version_id = source.id
           AND correction.consuming_projection_version = ?
           AND correction.historical_evidence_policy = 'reinterpret_measurement'
          JOIN assessment_contract_versions AS effective
            ON effective.id = COALESCE(
                correction.corrected_contract_version_id, source.id
            )
         WHERE source.id IN ({placeholders})
         ORDER BY source.id ASC
        """,
        [projection_version, *version_ids],
    ).fetchall()
    resolved: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = dict(row)
        source_id = str(payload.pop("replay_source_version_id"))
        payload["contract"] = _loads(payload["contract_json"], {})
        resolved[source_id] = payload
    return resolved
