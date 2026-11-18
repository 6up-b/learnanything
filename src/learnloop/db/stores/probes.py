"""Diagnostic probe episodes, instruments and evaluation.

Owns probe state, presentations and observations, diagnostic packs and evaluation ledgers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import (
    ProbeObservationRecord,
    ProbePresentationRecord,
    ProbeStateRecord,
    _decode_hypothesis_set,
    _insert_probe_presentation_row,
    _probe_observation_record,
    _probe_presentation_record,
    _probe_state_record,
)
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


@dataclass(frozen=True)
class ProbeEpisodeRecord:
    """One first-class diagnostic episode (probe redesign spec §5.1)."""

    id: str
    learning_object_id: str
    status: str
    trigger: str
    hypothesis_set_id: str | None
    active_state_segment_id: str | None
    target_decision: dict[str, Any] | None
    origin: str | None
    required_facets: list[str]
    minimum_independent_observations: int
    maximum_observations: int
    entered_at: str | None
    completed_at: str | None
    completion_reason: str | None
    algorithm_version: str
    created_at: str
    updated_at: str
    # mvp-0.8 robust cutover (migration 071): the calibration channel + coarse
    # mapping pinned at episode open. NULL for legacy mvp-0.6/0.7 episodes.
    calibration_model_id: str | None = None
    calibration_model_hash: str | None = None
    probe_mapping_version: str | None = None


@dataclass(frozen=True)
class ProbeStateSegmentRecord:
    """A learner-state segment boundary event (probe redesign spec §5.1)."""

    id: str
    learning_object_id: str
    probe_episode_id: str | None
    sequence: int
    reason: str
    opened_by_attempt_id: str | None
    created_at: str


@dataclass(frozen=True)
class ProbeFamilyTemplateRecord:
    id: str
    version: int
    status: str
    template: dict[str, Any]
    schema_hash: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True)
class ProbeInstrumentCardRecord:
    id: str
    version: int
    probe_family_template_id: str
    probe_family_template_version: int
    learning_object_id: str
    hypothesis_scope: list[str]
    card: dict[str, Any]
    compiled_likelihood_hash: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True)
class ProbeItemFamilyLinkRecord:
    practice_item_id: str
    instrument_card_id: str
    instrument_card_version: int
    generator_id: str | None
    generator_version: str | None
    generation_seed: str | None
    instance_metadata: dict[str, Any] | None
    created_at: str


@dataclass(frozen=True)
class ProbeGenerationNeedRecord:
    id: str
    probe_episode_id: str
    learning_object_id: str
    target_key: str
    missing_capability: str
    status: str
    created_at: str
    resolved_at: str | None


@dataclass(frozen=True)
class ProbeCalibrationSessionRecord:
    """A learner-initiated calibration session (probe redesign spec §5.9)."""

    id: str
    session_id: str
    goal_id: str | None
    learning_object_ids: list[str]
    planned_episode_ids: list[str]
    time_budget_minutes: int
    status: str
    started_at: str
    ended_at: str | None
    created_at: str
    updated_at: str


def _decode_persona_realism_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["feature_manifest"] = _loads(data.pop("feature_manifest_json"), {})
    return data


def _decode_diagnostic_eval_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["metrics"] = _loads(data.pop("metrics_json"), {})
    data["cross_model_separated"] = bool(data["cross_model_separated"])
    data["realism_licensed"] = bool(data["realism_licensed"])
    return data


def _decode_diagnostic_eval_case(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["planted_anchor"] = _loads(data.pop("planted_anchor_json"), None)
    data["system_snapshot"] = _loads(data.pop("system_snapshot_json"), {})
    for key in (
        "planted_should_abstain",
        "system_abstained",
        "anchor_correct",
        "abstention_correct",
        "realism_licensed",
        "cross_model_separated",
    ):
        if key in data:
            data[key] = bool(data[key])
    for key in ("cause_correct", "repair_correct"):
        if data.get(key) is not None:
            data[key] = bool(data[key])
    return data


def _probe_episode_record(row: sqlite3.Row) -> ProbeEpisodeRecord:
    return ProbeEpisodeRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        status=row["status"],
        trigger=row["trigger"],
        hypothesis_set_id=row["hypothesis_set_id"],
        active_state_segment_id=row["active_state_segment_id"],
        target_decision=_loads(row["target_decision_json"], None),
        origin=row["origin"],
        required_facets=_loads(row["required_facets_json"], []),
        minimum_independent_observations=row["minimum_independent_observations"],
        maximum_observations=row["maximum_observations"],
        entered_at=row["entered_at"],
        completed_at=row["completed_at"],
        completion_reason=row["completion_reason"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        calibration_model_id=row["calibration_model_id"] if "calibration_model_id" in row.keys() else None,
        calibration_model_hash=row["calibration_model_hash"] if "calibration_model_hash" in row.keys() else None,
        probe_mapping_version=row["probe_mapping_version"] if "probe_mapping_version" in row.keys() else None,
    )


def _probe_state_segment_record(row: sqlite3.Row) -> ProbeStateSegmentRecord:
    return ProbeStateSegmentRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        probe_episode_id=row["probe_episode_id"],
        sequence=row["sequence"],
        reason=row["reason"],
        opened_by_attempt_id=row["opened_by_attempt_id"],
        created_at=row["created_at"],
    )


def _probe_family_template_record(row: sqlite3.Row) -> ProbeFamilyTemplateRecord:
    return ProbeFamilyTemplateRecord(
        id=row["id"],
        version=row["version"],
        status=row["status"],
        template=_loads(row["template_json"], {}),
        schema_hash=row["schema_hash"],
        created_at=row["created_at"],
        retired_at=row["retired_at"],
    )


def _probe_instrument_card_record(row: sqlite3.Row) -> ProbeInstrumentCardRecord:
    return ProbeInstrumentCardRecord(
        id=row["id"],
        version=row["version"],
        probe_family_template_id=row["probe_family_template_id"],
        probe_family_template_version=row["probe_family_template_version"],
        learning_object_id=row["learning_object_id"],
        hypothesis_scope=_loads(row["hypothesis_scope_json"], []),
        card=_loads(row["card_json"], {}),
        compiled_likelihood_hash=row["compiled_likelihood_hash"],
        created_at=row["created_at"],
        retired_at=row["retired_at"],
    )


def _probe_item_family_link_record(row: sqlite3.Row) -> ProbeItemFamilyLinkRecord:
    return ProbeItemFamilyLinkRecord(
        practice_item_id=row["practice_item_id"],
        instrument_card_id=row["instrument_card_id"],
        instrument_card_version=row["instrument_card_version"],
        generator_id=row["generator_id"],
        generator_version=row["generator_version"],
        generation_seed=row["generation_seed"],
        instance_metadata=_loads(row["instance_metadata_json"], None),
        created_at=row["created_at"],
    )


def _probe_generation_need_record(row: sqlite3.Row) -> ProbeGenerationNeedRecord:
    return ProbeGenerationNeedRecord(
        id=row["id"],
        probe_episode_id=row["probe_episode_id"],
        learning_object_id=row["learning_object_id"],
        target_key=row["target_key"],
        missing_capability=row["missing_capability"],
        status=row["status"],
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
    )


def _probe_calibration_session_record(row: sqlite3.Row) -> ProbeCalibrationSessionRecord:
    return ProbeCalibrationSessionRecord(
        id=row["id"],
        session_id=row["session_id"],
        goal_id=row["goal_id"],
        learning_object_ids=_loads(row["learning_object_ids_json"], []),
        planned_episode_ids=_loads(row["planned_episode_ids_json"], []),
        time_budget_minutes=row["time_budget_minutes"],
        status=row["status"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class ProbeStoreMixin:

    def probe_state(self, learning_object_id: str) -> ProbeStateRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM lo_probe_state WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        return _probe_state_record(row) if row is not None else None

    def upsert_probe_state(
        self,
        *,
        learning_object_id: str,
        status: str,
        algorithm_version: str,
        probe_phase_id: str | None = None,
        hypothesis_set_id: str | None = None,
        probe_attempts_completed: int = 0,
        probe_attempts_target: int = 3,
        families_converged: list[str] | None = None,
        entered_at: str | None = None,
        completed_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO lo_probe_state(
                  learning_object_id, status, probe_phase_id, hypothesis_set_id,
                  probe_attempts_completed, probe_attempts_target,
                  families_converged_json, entered_at, completed_at,
                  algorithm_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learning_object_id) DO UPDATE SET
                  status = excluded.status,
                  probe_phase_id = excluded.probe_phase_id,
                  hypothesis_set_id = excluded.hypothesis_set_id,
                  probe_attempts_completed = excluded.probe_attempts_completed,
                  probe_attempts_target = excluded.probe_attempts_target,
                  families_converged_json = excluded.families_converged_json,
                  entered_at = excluded.entered_at,
                  completed_at = excluded.completed_at,
                  algorithm_version = excluded.algorithm_version,
                  updated_at = excluded.updated_at
                """,
                (
                    learning_object_id,
                    status,
                    probe_phase_id,
                    hypothesis_set_id,
                    probe_attempts_completed,
                    probe_attempts_target,
                    _json(families_converged or []),
                    entered_at,
                    completed_at,
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()

    def insert_hypothesis_set(
        self,
        *,
        learning_object_id: str,
        probe_phase_id: str | None,
        hypotheses: list[Mapping[str, Any]],
        prior: Mapping[str, float],
        algorithm_version: str,
        prior_basis: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        hypothesis_set_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO hypothesis_sets(
                  id, learning_object_id, probe_phase_id, hypotheses_json,
                  prior_json, algorithm_version, prior_basis, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hypothesis_set_id,
                    learning_object_id,
                    probe_phase_id,
                    _json(list(hypotheses)),
                    _json(dict(prior)),
                    algorithm_version,
                    prior_basis,
                    now,
                ),
            )
            connection.commit()
        return hypothesis_set_id

    def fetch_hypothesis_set(self, hypothesis_set_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM hypothesis_sets WHERE id = ?",
                (hypothesis_set_id,),
            ).fetchone()
        return _decode_hypothesis_set(row) if row is not None else None

    # --- Probe episodes (probe redesign spec §5) -------------------------------

    def insert_probe_episode(
        self,
        *,
        learning_object_id: str,
        status: str,
        trigger: str,
        hypothesis_set_id: str | None,
        active_state_segment_id: str | None,
        algorithm_version: str,
        target_decision: Mapping[str, Any] | None = None,
        origin: str | None = None,
        required_facets: list[str] | None = None,
        minimum_independent_observations: int = 2,
        maximum_observations: int = 4,
        entered_at: str | None = None,
        episode_id: str | None = None,
        target_contract_version_id: str | None = None,
        target_support_hash: str | None = None,
        calibration_model_id: str | None = None,
        calibration_model_hash: str | None = None,
        probe_mapping_version: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        episode_id = episode_id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_episodes(
                  id, learning_object_id, status, trigger, hypothesis_set_id,
                  active_state_segment_id, target_decision_json, origin, required_facets_json,
                  minimum_independent_observations, maximum_observations,
                  entered_at, completed_at, completion_reason, algorithm_version,
                  target_contract_version_id, target_support_hash,
                  calibration_model_id, calibration_model_hash, probe_mapping_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    learning_object_id,
                    status,
                    trigger,
                    hypothesis_set_id,
                    active_state_segment_id,
                    _json(dict(target_decision)) if target_decision is not None else None,
                    origin,
                    _json(list(required_facets or [])),
                    minimum_independent_observations,
                    maximum_observations,
                    entered_at or now,
                    algorithm_version,
                    target_contract_version_id,
                    target_support_hash,
                    calibration_model_id,
                    calibration_model_hash,
                    probe_mapping_version,
                    now,
                    now,
                ),
            )
            connection.commit()
        return episode_id

    def probe_episode(self, episode_id: str) -> ProbeEpisodeRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_episodes WHERE id = ?", (episode_id,)
            ).fetchone()
        return _probe_episode_record(row) if row is not None else None

    def open_probe_episode(self, learning_object_id: str) -> ProbeEpisodeRecord | None:
        """The single open (`pending_items` / `in_progress`) episode for an LO, if any."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_episodes
                WHERE learning_object_id = ?
                  AND status IN ('pending_items', 'in_progress')
                ORDER BY created_at DESC LIMIT 1
                """,
                (learning_object_id,),
            ).fetchone()
        return _probe_episode_record(row) if row is not None else None

    def open_probe_episodes(self) -> dict[str, ProbeEpisodeRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_episodes WHERE status IN ('pending_items', 'in_progress')"
            ).fetchall()
        return {row["learning_object_id"]: _probe_episode_record(row) for row in rows}

    def probe_episodes_for_learning_object(self, learning_object_id: str) -> list[ProbeEpisodeRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_episodes WHERE learning_object_id = ? ORDER BY created_at, id",
                (learning_object_id,),
            ).fetchall()
        return [_probe_episode_record(row) for row in rows]

    def update_probe_episode_status(
        self,
        episode_id: str,
        *,
        status: str,
        completion_reason: str | None = None,
        completed_at: str | None = None,
        active_state_segment_id: str | None = None,
        completion_posterior_json: str | None = None,
        completion_detail_json: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        assignments = ["status = ?", "updated_at = ?"]
        parameters: list[Any] = [status, now]
        if completion_reason is not None:
            assignments.append("completion_reason = ?")
            parameters.append(completion_reason)
        if completed_at is not None:
            assignments.append("completed_at = ?")
            parameters.append(completed_at)
        if active_state_segment_id is not None:
            assignments.append("active_state_segment_id = ?")
            parameters.append(active_state_segment_id)
        if completion_posterior_json is not None:
            assignments.append("completion_posterior_json = ?")
            parameters.append(completion_posterior_json)
        if completion_detail_json is not None:
            # mvp-0.21 (migration 200): the decision that ended the episode
            # (a value-of-information stop with its forecast).
            assignments.append("completion_detail_json = ?")
            parameters.append(completion_detail_json)
        parameters.append(episode_id)
        with self.connection() as connection:
            connection.execute(
                f"UPDATE probe_episodes SET {', '.join(assignments)} WHERE id = ?",
                parameters,
            )
            connection.commit()

    def latest_completed_probe_episode(self, learning_object_id: str) -> dict[str, Any] | None:
        """Latest complete episode's conclusion for entry-rung selection:
        completion_reason plus the argmax of the persisted completion posterior."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT completion_reason, completion_posterior_json
                FROM probe_episodes
                WHERE learning_object_id = ? AND status = 'complete'
                ORDER BY completed_at DESC, id DESC LIMIT 1
                """,
                (learning_object_id,),
            ).fetchone()
        if row is None:
            return None
        posterior = _loads(row["completion_posterior_json"], None)
        top_hypothesis = None
        if isinstance(posterior, dict) and posterior:
            top_hypothesis = max(posterior, key=lambda k: float(posterior[k]))
        return {
            "completion_reason": row["completion_reason"],
            "top_hypothesis": top_hypothesis,
            "posterior": posterior if isinstance(posterior, dict) else None,
        }

    # --- State segments (§5.1) -------------------------------------------------

    def open_state_segment(
        self,
        *,
        learning_object_id: str,
        probe_episode_id: str | None,
        reason: str,
        opened_by_attempt_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Mint the next state segment for an LO and persist its opening event."""

        segment_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS seq FROM probe_state_segments WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO probe_state_segments(
                  id, learning_object_id, probe_episode_id, sequence, reason,
                  opened_by_attempt_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    segment_id,
                    learning_object_id,
                    probe_episode_id,
                    int(row["seq"]) + 1,
                    reason,
                    opened_by_attempt_id,
                    now,
                ),
            )
            if probe_episode_id is not None:
                connection.execute(
                    "UPDATE probe_episodes SET active_state_segment_id = ?, updated_at = ? WHERE id = ?",
                    (segment_id, now, probe_episode_id),
                )
            connection.commit()
        return segment_id

    def state_segments_for_learning_object(self, learning_object_id: str) -> list[ProbeStateSegmentRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_state_segments WHERE learning_object_id = ? ORDER BY sequence",
                (learning_object_id,),
            ).fetchall()
        return [_probe_state_segment_record(row) for row in rows]

    # --- Probe presentations (§5.1) ---------------------------------------------

    def insert_probe_presentation(
        self,
        *,
        probe_episode_id: str,
        practice_item_id: str,
        state_segment_id: str,
        scheduler_candidate_id: str | None = None,
        probe_family_template_id: str | None = None,
        probe_family_template_version: int | None = None,
        instrument_card_id: str | None = None,
        instrument_card_version: int | None = None,
        instrument_card_snapshot: Mapping[str, Any] | None = None,
        target_hypothesis_pairs: list[list[str]] | None = None,
        target_facets: list[str] | None = None,
        posterior_at_selection: Mapping[str, float] | None = None,
        entropy_at_selection: float | None = None,
        expected_information_gain: float | None = None,
        selection_policy_version: str | None = None,
        selection_components: Mapping[str, Any] | None = None,
        expires_at: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        presentation_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            _insert_probe_presentation_row(
                connection,
                presentation_id=presentation_id,
                now=now,
                values={
                    "probe_episode_id": probe_episode_id,
                    "practice_item_id": practice_item_id,
                    "scheduler_candidate_id": scheduler_candidate_id,
                    "state_segment_id": state_segment_id,
                    "probe_family_template_id": probe_family_template_id,
                    "probe_family_template_version": probe_family_template_version,
                    "instrument_card_id": instrument_card_id,
                    "instrument_card_version": instrument_card_version,
                    "instrument_card_snapshot": instrument_card_snapshot,
                    "target_hypothesis_pairs": target_hypothesis_pairs,
                    "target_facets": target_facets,
                    "posterior_at_selection": posterior_at_selection,
                    "entropy_at_selection": entropy_at_selection,
                    "expected_information_gain": expected_information_gain,
                    "selection_policy_version": selection_policy_version,
                    "selection_components": selection_components,
                    "expires_at": expires_at,
                },
            )
            connection.commit()
        return presentation_id

    def probe_presentation(self, presentation_id: str) -> ProbePresentationRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_presentations WHERE id = ?", (presentation_id,)
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def probe_presentations_for_episode(self, probe_episode_id: str) -> list[ProbePresentationRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_presentations WHERE probe_episode_id = ? ORDER BY created_at, id",
                (probe_episode_id,),
            ).fetchall()
        return [_probe_presentation_record(row) for row in rows]

    def active_probe_presentation(
        self, probe_episode_id: str, practice_item_id: str | None = None
    ) -> ProbePresentationRecord | None:
        """The most recent committed-but-unconsumed presentation for an episode."""

        clauses = ["probe_episode_id = ?", "status IN ('selected', 'served')"]
        parameters: list[Any] = [probe_episode_id]
        if practice_item_id is not None:
            clauses.append("practice_item_id = ?")
            parameters.append(practice_item_id)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM probe_presentations
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                parameters,
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def active_probe_presentation_for_item(self, practice_item_id: str) -> ProbePresentationRecord | None:
        """The latest committed-but-unconsumed diagnostic presentation of an
        item, in any episode (Reader CA1: the item is being measured on your
        own, so nothing may locate it)."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_presentations
                WHERE practice_item_id = ? AND status IN ('selected', 'served')
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        return _probe_presentation_record(row) if row is not None else None

    def mark_probe_presentation_served(self, presentation_id: str, *, clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'served', served_at = COALESCE(served_at, ?), updated_at = ?
                WHERE id = ? AND status = 'selected'
                """,
                (now, now, presentation_id),
            )
            connection.commit()

    def consume_probe_presentation(self, presentation_id: str, *, clock: Clock | None = None) -> bool:
        """Atomically move a presentation to `submitted`; False if not consumable."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'submitted', submitted_at = ?, updated_at = ?
                WHERE id = ? AND status IN ('selected', 'served')
                """,
                (now, now, presentation_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def end_probe_presentation(
        self, presentation_id: str, *, end_reason: str, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_presentations
                SET status = 'ended', end_reason = ?, ended_at = ?, updated_at = ?
                WHERE id = ? AND status IN ('selected', 'served')
                """,
                (end_reason, now, now, presentation_id),
            )
            connection.commit()

    # --- Probe observations (§5.1) ----------------------------------------------

    def insert_probe_observation(
        self,
        *,
        attempt_id: str,
        posterior_before: Mapping[str, float],
        posterior_after: Mapping[str, float],
        entropy_before: float,
        entropy_after: float,
        realized_information_gain: float,
        independent_evidence_discount: float | None = None,
        contamination: Mapping[str, Any] | None = None,
        grader_channel: Mapping[str, Any] | None = None,
        updates_belief: bool = True,
        eligible_for_completion: bool = False,
        features: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        observation_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_observations(
                  id, attempt_id, posterior_before_json, posterior_after_json,
                  entropy_before, entropy_after, realized_information_gain,
                  independent_evidence_discount, contamination_json, grader_channel_json,
                  updates_belief, eligible_for_completion, features_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    attempt_id,
                    _json(dict(posterior_before)),
                    _json(dict(posterior_after)),
                    entropy_before,
                    entropy_after,
                    realized_information_gain,
                    independent_evidence_discount,
                    _json(dict(contamination)) if contamination is not None else None,
                    _json(dict(grader_channel)) if grader_channel is not None else None,
                    1 if updates_belief else 0,
                    1 if eligible_for_completion else 0,
                    _json(dict(features)) if features is not None else None,
                    now,
                ),
            )
            connection.commit()
        return observation_id

    def qualifying_probe_observation_count(self) -> int:
        """Qualifying diagnostic observations across the whole vault (§5.9
        time-to-first-ordinary-practice ceiling), held ones excluded (review F3)."""

        from learnloop.held_grades import held_for_review_attempts

        with self.connection() as connection:
            attempt_ids = [
                str(row["attempt_id"])
                for row in connection.execute(
                    "SELECT attempt_id FROM probe_observations WHERE eligible_for_completion = 1"
                ).fetchall()
            ]
            # Every held attempt in one read (the set is small); none when
            # nothing qualifies.
            held = held_for_review_attempts(connection) if attempt_ids else frozenset()
        return sum(1 for attempt_id in attempt_ids if attempt_id not in held)

    def ordinary_practice_attempt_count(self) -> int:
        """Attempts recorded outside the diagnostic/exam channels (§5.9): the
        signal that ordinary practice has started in this vault."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM practice_attempts
                WHERE probe_presentation_id IS NULL
                  AND attempt_type NOT IN ('diagnostic_probe', 'exam_attempt', 'exam_evidence')
                """
            ).fetchone()
        return int(row["count"])

    def probe_observation_for_attempt(self, attempt_id: str) -> ProbeObservationRecord | None:
        """One observation AS RECORDED (its receipt): existence checks and the
        grader-agreement regrade check read it. Readers of episode evidence read
        :meth:`probe_observations_for_episode`, the effective view."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_observations WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
        return _probe_observation_record(row) if row is not None else None

    def list_probe_episodes(self, *, statuses: tuple[str, ...] | None = None) -> list[ProbeEpisodeRecord]:
        """All episodes, oldest first, optionally filtered by status."""

        query = "SELECT * FROM probe_episodes"
        params: tuple[Any, ...] = ()
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            params = tuple(statuses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_probe_episode_record(row) for row in rows]

    # --- Probe families and Instrument Cards (§9) --------------------------------

    def upsert_probe_family_template(
        self,
        *,
        family_id: str,
        version: int,
        status: str,
        template: Mapping[str, Any],
        schema_hash: str,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_family_templates(id, version, status, template_json, schema_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id, version) DO UPDATE SET
                  status = excluded.status
                """,
                (family_id, version, status, _json(dict(template)), schema_hash, now),
            )
            connection.commit()

    def probe_family_template(self, family_id: str, version: int) -> ProbeFamilyTemplateRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_family_templates WHERE id = ? AND version = ?",
                (family_id, version),
            ).fetchone()
        return _probe_family_template_record(row) if row is not None else None

    def latest_probe_family_template(
        self, family_id: str, *, statuses: tuple[str, ...] = ("provisional", "trusted")
    ) -> ProbeFamilyTemplateRecord | None:
        placeholders = ", ".join("?" for _ in statuses)
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM probe_family_templates
                WHERE id = ? AND status IN ({placeholders})
                ORDER BY version DESC LIMIT 1
                """,
                (family_id, *statuses),
            ).fetchone()
        return _probe_family_template_record(row) if row is not None else None

    def update_probe_family_template_status(
        self, family_id: str, version: int, *, status: str, clock: Clock | None = None
    ) -> None:
        """Lifecycle transition for one family version (§9.7, Checkpoint 4.7).

        ``retired_at`` is stamped when entering ``retired`` and cleared
        otherwise; historical observations keep replaying against the version
        they persisted (§9.1), so this never rewrites template_json.
        """

        now = utc_now_iso(clock)
        retired_at = now if status == "retired" else None
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_family_templates SET status = ?, retired_at = ? WHERE id = ? AND version = ?",
                (status, retired_at, family_id, version),
            )
            connection.commit()

    def all_probe_family_templates(self) -> list[ProbeFamilyTemplateRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_family_templates ORDER BY id, version"
            ).fetchall()
        return [_probe_family_template_record(row) for row in rows]

    def insert_probe_family_lifecycle_event(
        self,
        *,
        probe_family_template_id: str,
        probe_family_template_version: int,
        from_status: str,
        to_status: str,
        reason: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_family_lifecycle_events(
                  id, probe_family_template_id, probe_family_template_version,
                  from_status, to_status, reason_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    from_status,
                    to_status,
                    _json(dict(reason)) if reason is not None else None,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def probe_family_lifecycle_events(
        self, probe_family_template_id: str, probe_family_template_version: int | None = None
    ) -> list[dict[str, Any]]:
        query = (
            "SELECT * FROM probe_family_lifecycle_events WHERE probe_family_template_id = ?"
        )
        params: tuple[Any, ...] = (probe_family_template_id,)
        if probe_family_template_version is not None:
            query += " AND probe_family_template_version = ?"
            params = (*params, probe_family_template_version)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        results = []
        for row in rows:
            payload = dict(row)
            payload["reason"] = _loads(row["reason_json"], None)
            results.append(payload)
        return results

    def insert_probe_instrument_card(
        self,
        *,
        card_id: str,
        version: int,
        probe_family_template_id: str,
        probe_family_template_version: int,
        learning_object_id: str,
        hypothesis_scope: list[str],
        card: Mapping[str, Any],
        compiled_likelihood_hash: str,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_instrument_cards(
                  id, version, probe_family_template_id, probe_family_template_version,
                  learning_object_id, hypothesis_scope_json, card_json,
                  compiled_likelihood_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    version,
                    probe_family_template_id,
                    probe_family_template_version,
                    learning_object_id,
                    _json(list(hypothesis_scope)),
                    _json(dict(card)),
                    compiled_likelihood_hash,
                    now,
                ),
            )
            connection.commit()

    def probe_instrument_card(self, card_id: str, version: int) -> ProbeInstrumentCardRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_instrument_cards WHERE id = ? AND version = ?",
                (card_id, version),
            ).fetchone()
        return _probe_instrument_card_record(row) if row is not None else None

    def probe_instrument_cards_for_learning_object(
        self, learning_object_id: str
    ) -> list[ProbeInstrumentCardRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM probe_instrument_cards
                WHERE learning_object_id = ? AND retired_at IS NULL
                ORDER BY id, version
                """,
                (learning_object_id,),
            ).fetchall()
        return [_probe_instrument_card_record(row) for row in rows]

    def link_probe_item_family(
        self,
        *,
        practice_item_id: str,
        instrument_card_id: str,
        instrument_card_version: int,
        generator_id: str | None = None,
        generator_version: str | None = None,
        generation_seed: str | None = None,
        instance_metadata: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO probe_item_family_links(
                  practice_item_id, instrument_card_id, instrument_card_version,
                  generator_id, generator_version, generation_seed,
                  instance_metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    practice_item_id,
                    instrument_card_id,
                    instrument_card_version,
                    generator_id,
                    generator_version,
                    generation_seed,
                    _json(dict(instance_metadata)) if instance_metadata is not None else None,
                    now,
                ),
            )
            connection.commit()

    def probe_item_family_links(self, practice_item_id: str) -> list[ProbeItemFamilyLinkRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_item_family_links WHERE practice_item_id = ? ORDER BY created_at",
                (practice_item_id,),
            ).fetchall()
        return [_probe_item_family_link_record(row) for row in rows]

    def probe_items_for_card(self, instrument_card_id: str, instrument_card_version: int) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT practice_item_id FROM probe_item_family_links
                WHERE instrument_card_id = ? AND instrument_card_version = ?
                ORDER BY created_at
                """,
                (instrument_card_id, instrument_card_version),
            ).fetchall()
        return [row["practice_item_id"] for row in rows]

    def upsert_probe_family_calibration(
        self,
        *,
        probe_family_template_id: str,
        probe_family_template_version: int,
        evidence_source: str,
        parameter_posterior: Mapping[str, Any],
        sample_size: int,
        effective_sample_size: float | None = None,
        generator_version: str | None = None,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(generator_version, '') = COALESCE(?, '')
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    probe_family_template_id,
                    probe_family_template_version,
                    generator_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE probe_family_calibrations
                    SET parameter_posterior_json = ?, sample_size = ?, effective_sample_size = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (_json(dict(parameter_posterior)), sample_size, effective_sample_size, now, existing["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO probe_family_calibrations(
                      id, probe_family_template_id, probe_family_template_version,
                      generator_version, grader_version, evidence_source,
                      parameter_posterior_json, sample_size, effective_sample_size, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        probe_family_template_id,
                        probe_family_template_version,
                        generator_version,
                        grader_version,
                        evidence_source,
                        _json(dict(parameter_posterior)),
                        sample_size,
                        effective_sample_size,
                        now,
                    ),
                )
            connection.commit()

    def probe_family_calibration(
        self,
        probe_family_template_id: str,
        probe_family_template_version: int,
        *,
        evidence_source: str,
        generator_version: str | None = None,
        grader_version: str | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(generator_version, '') = COALESCE(?, '')
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    probe_family_template_id,
                    probe_family_template_version,
                    generator_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
        return payload

    def probe_family_calibrations_for_family(
        self, probe_family_template_id: str, probe_family_template_version: int
    ) -> list[dict[str, Any]]:
        """Every calibration row for one family version, all evidence sources."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM probe_family_calibrations
                WHERE probe_family_template_id = ? AND probe_family_template_version = ?
                ORDER BY evidence_source, COALESCE(grader_version, ''), COALESCE(generator_version, '')
                """,
                (probe_family_template_id, probe_family_template_version),
            ).fetchall()
        results = []
        for row in rows:
            payload = dict(row)
            payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
            results.append(payload)
        return results

    def upsert_probe_item_calibration(
        self,
        *,
        practice_item_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        evidence_source: str,
        parameter_posterior: Mapping[str, Any],
        sample_size: int,
        effective_sample_size: float | None = None,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Item-instance residual layer under the family posterior (§9.7)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM probe_item_calibrations
                WHERE practice_item_id = ?
                  AND probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    practice_item_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE probe_item_calibrations
                    SET parameter_posterior_json = ?, sample_size = ?, effective_sample_size = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (_json(dict(parameter_posterior)), sample_size, effective_sample_size, now, existing["id"]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO probe_item_calibrations(
                      id, practice_item_id, probe_family_template_id, probe_family_template_version,
                      grader_version, evidence_source,
                      parameter_posterior_json, sample_size, effective_sample_size, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        practice_item_id,
                        probe_family_template_id,
                        probe_family_template_version,
                        grader_version,
                        evidence_source,
                        _json(dict(parameter_posterior)),
                        sample_size,
                        effective_sample_size,
                        now,
                    ),
                )
            connection.commit()

    def probe_item_calibration(
        self,
        practice_item_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        *,
        evidence_source: str,
        grader_version: str | None = None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM probe_item_calibrations
                WHERE practice_item_id = ?
                  AND probe_family_template_id = ? AND probe_family_template_version = ?
                  AND COALESCE(grader_version, '') = COALESCE(?, '')
                  AND evidence_source = ?
                """,
                (
                    practice_item_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    evidence_source,
                ),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["parameter_posterior"] = _loads(row["parameter_posterior_json"], {})
        return payload

    # --- Probe regrade checks (§7.6, Checkpoint 4.4) ------------------------------

    def insert_probe_regrade_check(
        self,
        *,
        attempt_id: str,
        probe_family_template_id: str,
        probe_family_template_version: int,
        original_outcome: str,
        regrade_outcome: str,
        grader_version: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        check_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_regrade_checks(
                  id, attempt_id, probe_family_template_id, probe_family_template_version,
                  grader_version, original_outcome, regrade_outcome, agreement, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check_id,
                    attempt_id,
                    probe_family_template_id,
                    probe_family_template_version,
                    grader_version,
                    original_outcome,
                    regrade_outcome,
                    1 if original_outcome == regrade_outcome else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return check_id

    def probe_regrade_checks(
        self,
        probe_family_template_id: str | None = None,
        probe_family_template_version: int | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM probe_regrade_checks"
        clauses: list[str] = []
        params: list[Any] = []
        if probe_family_template_id is not None:
            clauses.append("probe_family_template_id = ?")
            params.append(probe_family_template_id)
        if probe_family_template_version is not None:
            clauses.append("probe_family_template_version = ?")
            params.append(probe_family_template_version)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    # --- Probe generation needs (§10) --------------------------------------------

    def upsert_probe_generation_need(
        self,
        *,
        probe_episode_id: str,
        learning_object_id: str,
        target_key: str,
        missing_capability: str,
        clock: Clock | None = None,
    ) -> str:
        """Create one deduplicated pending generation need per episode target."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM probe_generation_needs WHERE probe_episode_id = ? AND target_key = ?",
                (probe_episode_id, target_key),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO probe_generation_needs(
                  id, probe_episode_id, learning_object_id, target_key,
                  missing_capability, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (need_id, probe_episode_id, learning_object_id, target_key, missing_capability, now),
            )
            connection.commit()
        return need_id

    def probe_generation_needs(
        self,
        *,
        learning_object_id: str | None = None,
        probe_episode_id: str | None = None,
        status: str | None = None,
    ) -> list[ProbeGenerationNeedRecord]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("learning_object_id", learning_object_id),
            ("probe_episode_id", probe_episode_id),
            ("status", status),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM probe_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [_probe_generation_need_record(row) for row in rows]

    def resolve_probe_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
                (status, now, need_id),
            )
            connection.commit()

    # --- diagnostic-surface replenishment needs (migration 147) ---------------

    def upsert_diagnostic_surface_generation_need(
        self,
        *,
        learning_object_id: str,
        consumed_practice_item_id: str,
        target_key: str,
        missing_capability: str = "diagnostic_probe_surface",
        facet_ids: list[str] | None = None,
        misconception_ids: list[str] | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Record one deduplicated replacement need per consumed diagnostic surface.

        Mirrors ``upsert_probe_generation_need`` but consumption-scoped: a
        single-use ``diagnostic_probe`` surface carried its one administration,
        so the learning object needs a fresh never-before-seen replacement
        targeting the same facets/misconception pairs. Deduped on the consumed
        item id, so the derive-from-attempts sweep is idempotent and replay-safe.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM diagnostic_surface_generation_needs "
                "WHERE consumed_practice_item_id = ?",
                (consumed_practice_item_id,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_surface_generation_needs(
                  id, learning_object_id, consumed_practice_item_id, target_key,
                  missing_capability, facet_ids_json, misconception_ids_json,
                  status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    need_id,
                    learning_object_id,
                    consumed_practice_item_id,
                    target_key,
                    missing_capability,
                    _json(list(facet_ids or [])),
                    _json(list(misconception_ids or [])),
                    now,
                ),
            )
            connection.commit()
        return need_id

    def diagnostic_surface_generation_needs(
        self,
        *,
        learning_object_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("learning_object_id", learning_object_id),
            ("status", status),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM diagnostic_surface_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "learning_object_id": row["learning_object_id"],
                "consumed_practice_item_id": row["consumed_practice_item_id"],
                "target_key": row["target_key"],
                "missing_capability": row["missing_capability"],
                "facet_ids": _loads(row["facet_ids_json"], []),
                "misconception_ids": _loads(row["misconception_ids_json"], []),
                "status": row["status"],
                "created_at": row["created_at"],
                "resolved_at": row["resolved_at"],
            }
            for row in rows
        ]

    def resolve_diagnostic_surface_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE diagnostic_surface_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
                (status, now, need_id),
            )
            connection.commit()

    def update_probe_item_family_metadata(
        self,
        *,
        practice_item_id: str,
        instrument_card_id: str,
        instrument_card_version: int,
        instance_metadata: Mapping[str, Any],
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_item_family_links
                SET instance_metadata_json = ?
                WHERE practice_item_id = ? AND instrument_card_id = ? AND instrument_card_version = ?
                """,
                (_json(dict(instance_metadata)), practice_item_id, instrument_card_id, instrument_card_version),
            )
            connection.commit()

    def probe_instance_ids_with_review_status(self, review_status: str) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT practice_item_id FROM probe_item_family_links
                WHERE json_extract(instance_metadata_json, '$.review_status') = ?
                """,
                (review_status,),
            ).fetchall()
        return {row["practice_item_id"] for row in rows}

    # --- Calibration sessions (§5.9) ---------------------------------------------

    def insert_probe_calibration_session(
        self,
        *,
        session_id: str,
        learning_object_ids: list[str],
        planned_episode_ids: list[str],
        time_budget_minutes: int,
        goal_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        calibration_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO probe_calibration_sessions(
                  id, session_id, goal_id, learning_object_ids_json,
                  planned_episode_ids_json, time_budget_minutes, status,
                  started_at, ended_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, NULL, ?, ?)
                """,
                (
                    calibration_id,
                    session_id,
                    goal_id,
                    _json(list(learning_object_ids)),
                    _json(list(planned_episode_ids)),
                    time_budget_minutes,
                    now,
                    now,
                    now,
                ),
            )
            connection.commit()
        return calibration_id

    def probe_calibration_session(self, calibration_id: str) -> ProbeCalibrationSessionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_calibration_sessions WHERE id = ?", (calibration_id,)
            ).fetchone()
        return _probe_calibration_session_record(row) if row is not None else None

    def active_probe_calibration_session(self, session_id: str) -> ProbeCalibrationSessionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_calibration_sessions WHERE session_id = ? AND status = 'active'",
                (session_id,),
            ).fetchone()
        return _probe_calibration_session_record(row) if row is not None else None

    def end_probe_calibration_session(
        self, calibration_id: str, *, status: str, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE probe_calibration_sessions
                SET status = ?, ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ? AND status = 'active'
                """,
                (status, now, now, calibration_id),
            )
            connection.commit()

    def list_all_probe_presentations(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_presentations ORDER BY created_at, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def list_all_probe_instrument_cards(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM probe_instrument_cards ORDER BY created_at, id, version"
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P2 DIAGNOSTIC track -- diagnostic pack + two-tier triage
    # (spec_p2 §5, §6, U-027, U-028; migration 083)
    # ------------------------------------------------------------------

    def ensure_diagnostic_pack(
        self,
        *,
        pack_slug: str,
        blueprint_version_id: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register/return the stable diagnostic pack row. Idempotent on ``pack_slug``
        AND content_hash: a re-register of the byte-identical pack returns the existing
        row (``already_exists=True``) so pack assembly is deterministic (§5.1)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE pack_slug = ?", (pack_slug,)
            ).fetchone()
            if existing is not None:
                return {"pack": dict(existing), "already_exists": True}
            pack_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_packs(
                  id, pack_slug, blueprint_version_id, status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?)
                """,
                (pack_id, pack_slug, blueprint_version_id, content_hash, now),
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, 'registered', ?, 'owner', ?)
                """,
                (new_ulid(), pack_id, _json({"content_hash": content_hash}), now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE id = ?", (pack_id,)
            ).fetchone()
            return {"pack": dict(row), "already_exists": False}

    def register_diagnostic_pack_card(
        self,
        *,
        pack_id: str,
        card_slug: str,
        coverage_json: str,
        content_hash: str,
        instrument_ref: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Register a candidate diagnostic-purpose card. Idempotent on
        ``UNIQUE(pack_id, card_slug)``."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM diagnostic_pack_cards WHERE pack_id = ? AND card_slug = ?",
                (pack_id, card_slug),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            card_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_pack_cards(
                  id, pack_id, card_slug, purpose, coverage_json, instrument_ref,
                  admission_status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'diagnostic', ?, ?, 'candidate', ?, ?)
                """,
                (card_id, pack_id, card_slug, coverage_json, instrument_ref, content_hash, now),
            )
            connection.commit()
            return card_id

    def set_diagnostic_pack_card_admission(
        self,
        *,
        pack_id: str,
        card_slug: str,
        admission_status: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        kind = "admitted" if admission_status == "admitted" else "rejected"
        with self.connection() as connection:
            connection.execute(
                "UPDATE diagnostic_pack_cards SET admission_status = ? WHERE pack_id = ? AND card_slug = ?",
                (admission_status, pack_id, card_slug),
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), pack_id, card_slug, kind, detail_json, author, now),
            )
            connection.commit()

    def transition_diagnostic_pack(
        self,
        *,
        pack_id: str,
        status: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE diagnostic_packs SET status = ? WHERE id = ?", (status, pack_id)
            )
            connection.execute(
                """
                INSERT INTO diagnostic_pack_events(
                  id, pack_id, card_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (new_ulid(), pack_id, kind, detail_json, author, now),
            )
            connection.commit()

    def diagnostic_pack(self, pack_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE id = ?", (pack_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def diagnostic_packs_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_packs WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def diagnostic_pack_cards_for(self, pack_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_pack_cards WHERE pack_id = ? ORDER BY card_slug",
                (pack_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def diagnostic_pack_events_for(self, pack_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM diagnostic_pack_events WHERE pack_id = ? ORDER BY created_at, id",
                (pack_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def pin_diagnostic_pack(
        self,
        *,
        run_id: str,
        pack_id: str,
        goal_contract_version_id: str,
        visible_cap: int,
        probe_episode_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Pin exactly one reviewed pack to a run at diagnostic entry (§5.2).
        Idempotent on ``UNIQUE(run_id)`` -- a re-pin returns the existing pin."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE run_id = ?", (run_id,)
            ).fetchone()
            if existing is not None:
                return {"pin": dict(existing), "already_exists": True}
            pin_id = new_ulid()
            connection.execute(
                """
                INSERT INTO diagnostic_pack_pins(
                  id, run_id, pack_id, goal_contract_version_id, probe_episode_id,
                  visible_cap, pinned_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pin_id, run_id, pack_id, goal_contract_version_id, probe_episode_id, visible_cap, now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE id = ?", (pin_id,)
            ).fetchone()
            return {"pin": dict(row), "already_exists": False}

    def diagnostic_pack_pin_for_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_pack_pins WHERE run_id = ?", (run_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # --- Diagnostic augmentation Stage 7 (migration 144) -----------------

    def insert_persona_realism_run(
        self,
        values: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str:
        """Append one blinded B2 matcher result.

        The matcher consumes text only; labels and feature rows are deliberately
        absent from this API so a persisted result cannot retain an accidental
        copy of a learner trace.
        """

        row_id = str(values.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO persona_realism_runs(
                  id, matcher_version, corpus_hash, persona_corpus_hash,
                  real_corpus_hash, persona_source,
                  generator_provider, generator_model, generator_family,
                  persona_count, real_count, folds, matcher_correct,
                  matcher_total, balanced_accuracy, separation_threshold,
                  verdict, feature_manifest_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    values["matcher_version"],
                    values["corpus_hash"],
                    values.get("persona_corpus_hash") or values["corpus_hash"],
                    values.get("real_corpus_hash") or values["corpus_hash"],
                    values["persona_source"],
                    values.get("generator_provider"),
                    values.get("generator_model"),
                    values.get("generator_family"),
                    int(values.get("persona_count") or 0),
                    int(values.get("real_count") or 0),
                    int(values.get("folds") or 0),
                    int(values.get("matcher_correct") or 0),
                    int(values.get("matcher_total") or 0),
                    values.get("balanced_accuracy"),
                    float(values["separation_threshold"]),
                    values["verdict"],
                    _json(values.get("feature_manifest") or {}),
                    values.get("created_at") or utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def persona_realism_run_rows(
        self,
        *,
        generator_family: str | None = None,
        persona_source: str | None = None,
        persona_corpus_hash: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if generator_family:
            clauses.append("generator_family = ?")
            args.append(generator_family)
        if persona_source:
            clauses.append("persona_source = ?")
            args.append(persona_source)
        if persona_corpus_hash:
            clauses.append("persona_corpus_hash = ?")
            args.append(persona_corpus_hash)
        clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM persona_realism_runs
                {clause}
                ORDER BY created_at, id
                """,
                tuple(args),
            ).fetchall()
        return [_decode_persona_realism_run(row) for row in rows]

    def latest_persona_realism_run(
        self,
        *,
        generator_family: str | None = None,
        persona_source: str | None = None,
        persona_corpus_hash: str | None = None,
    ) -> dict[str, Any] | None:
        rows = self.persona_realism_run_rows(
            generator_family=generator_family,
            persona_source=persona_source,
            persona_corpus_hash=persona_corpus_hash,
        )
        return rows[-1] if rows else None

    def real_attempt_trace_rows(self, *, limit: int = 500) -> list[dict[str, Any]]:
        """Recent non-empty real learner traces for B2, newest first.

        No grades, diagnoses, or labels are returned.  B2 is a matcher over the
        observable trace distribution, and handing it outcome metadata would
        create an easier task than the blind matcher the spec requires.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id AS attempt_id, practice_item_id, learner_answer_md,
                       created_at
                FROM practice_attempts
                WHERE learner_answer_md IS NOT NULL
                  AND TRIM(learner_answer_md) != ''
                  AND attempt_type NOT IN ('skip', 'dont_know')
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (max(0, int(limit)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_diagnostic_eval_run(
        self,
        values: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str:
        row_id = str(values.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO diagnostic_eval_runs(
                  id, harness_version, grading_prompt_version,
                  generator_provider, generator_model, generator_family,
                  diagnostician_provider, diagnostician_model,
                  diagnostician_family, cross_model_separated,
                  persona_realism_run_id, realism_licensed, status,
                  case_count, metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    values["harness_version"],
                    values["grading_prompt_version"],
                    values.get("generator_provider"),
                    values.get("generator_model"),
                    values["generator_family"],
                    values.get("diagnostician_provider"),
                    values.get("diagnostician_model"),
                    values["diagnostician_family"],
                    1 if values.get("cross_model_separated") else 0,
                    values.get("persona_realism_run_id"),
                    1 if values.get("realism_licensed") else 0,
                    values["status"],
                    int(values.get("case_count") or 0),
                    _json(values.get("metrics") or {}),
                    values.get("created_at") or utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def insert_diagnostic_eval_case(
        self,
        values: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str:
        row_id = str(values.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO diagnostic_eval_cases(
                  id, run_id, case_key, attempt_id, regression_shape, source,
                  practice_item_id, profile_id, learner_trace_md,
                  planted_should_abstain, planted_anchor_json,
                  planted_anchor_key, planted_cause_key,
                  planted_repair_class_id, planted_repair_equivalence_id,
                  system_snapshot_json, system_abstained, system_anchor_key,
                  system_cause_key, system_repair_class_id,
                  system_repair_equivalence_id, anchor_correct, cause_correct,
                  repair_correct, abstention_correct, created_at
                ) VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    row_id,
                    values["run_id"],
                    values["case_key"],
                    values.get("attempt_id"),
                    values["regression_shape"],
                    values["source"],
                    values["practice_item_id"],
                    values.get("profile_id"),
                    values["learner_trace_md"],
                    1 if values.get("planted_should_abstain") else 0,
                    (
                        _json(values["planted_anchor"])
                        if values.get("planted_anchor") is not None
                        else None
                    ),
                    values["planted_anchor_key"],
                    values.get("planted_cause_key"),
                    values.get("planted_repair_class_id"),
                    values.get("planted_repair_equivalence_id"),
                    _json(values.get("system_snapshot") or {}),
                    1 if values.get("system_abstained") else 0,
                    values["system_anchor_key"],
                    values.get("system_cause_key"),
                    values.get("system_repair_class_id"),
                    values.get("system_repair_equivalence_id"),
                    1 if values.get("anchor_correct") else 0,
                    (
                        None
                        if values.get("cause_correct") is None
                        else (1 if values.get("cause_correct") else 0)
                    ),
                    (
                        None
                        if values.get("repair_correct") is None
                        else (1 if values.get("repair_correct") else 0)
                    ),
                    1 if values.get("abstention_correct") else 0,
                    values.get("created_at") or utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def diagnostic_eval_run_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM diagnostic_eval_runs
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_diagnostic_eval_run(row) for row in rows]

    def diagnostic_eval_case_rows(
        self,
        *,
        run_id: str | None = None,
        licensed_only: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if run_id is not None:
            clauses.append("c.run_id = ?")
            args.append(run_id)
        if licensed_only:
            clauses.append("r.status = 'licensed'")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT c.*, r.status AS run_status,
                       r.realism_licensed, r.cross_model_separated
                FROM diagnostic_eval_cases c
                JOIN diagnostic_eval_runs r ON r.id = c.run_id
                {where}
                ORDER BY c.created_at, c.id
                """,
                tuple(args),
            ).fetchall()
        return [_decode_diagnostic_eval_case(row) for row in rows]
