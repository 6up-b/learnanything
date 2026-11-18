"""Database records and row helpers shared by the repository and its stores."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from dataclasses import field  # noqa: F401  Keeps the moved field-shadowing directives valid.
from typing import Any, Mapping

from learnloop.db.row_serialization import _json, _loads


_UNSET: Any = object()  # sentinel: "argument not supplied" vs an explicit None


def _projection_id(prefix: str, *identity: object) -> str:
    """Content-addressed identity for a row recreated by deterministic replay."""

    encoded = _json(identity).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:26]}"


def _insert_probe_presentation_row(
    connection: sqlite3.Connection,
    *,
    presentation_id: str,
    now: str,
    values: Mapping[str, Any],
) -> None:
    """Insert one frozen diagnostic assignment using the caller's transaction."""

    connection.execute(
        """
        INSERT INTO probe_presentations(
          id, probe_episode_id, practice_item_id, scheduler_candidate_id,
          state_segment_id, probe_family_template_id, probe_family_template_version,
          instrument_card_id, instrument_card_version, instrument_card_snapshot_json,
          target_hypothesis_pairs_json, target_facets_json, posterior_at_selection_json,
          entropy_at_selection, expected_information_gain, selection_policy_version,
          selection_components_json,
          status, end_reason, served_at, submitted_at, expires_at, ended_at,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'selected',
                NULL, NULL, NULL, ?, NULL, ?, ?)
        """,
        (
            presentation_id,
            values["probe_episode_id"],
            values["practice_item_id"],
            values.get("scheduler_candidate_id"),
            values["state_segment_id"],
            values.get("probe_family_template_id"),
            values.get("probe_family_template_version"),
            values.get("instrument_card_id"),
            values.get("instrument_card_version"),
            _json(dict(values["instrument_card_snapshot"]))
            if values.get("instrument_card_snapshot") is not None
            else None,
            _json(list(values.get("target_hypothesis_pairs") or [])),
            _json(list(values.get("target_facets") or [])),
            _json(dict(values.get("posterior_at_selection") or {})),
            values.get("entropy_at_selection"),
            values.get("expected_information_gain"),
            values.get("selection_policy_version"),
            _json(dict(values["selection_components"]))
            if values.get("selection_components") is not None
            else None,
            values.get("expires_at"),
            now,
            now,
        ),
    )


@dataclass(frozen=True)
class PracticeItemState:
    practice_item_id: str
    difficulty: float | None
    stability: float | None
    retrievability: float | None
    due_at: str | None
    active: bool
    content_hash: str | None
    last_attempt_at: str | None
    updated_at: str


@dataclass(frozen=True)
class MasteryState:
    learning_object_id: str
    logit_mean: float
    logit_variance: float
    evidence_count: int
    last_evidence_at: str | None
    algorithm_version: str
    updated_at: str


@dataclass(frozen=True)
class ItemParameterState:
    """Per-item empirical-Bayes difficulty posterior (b in the 2PL link)."""

    practice_item_id: str
    b_mean: float
    b_var: float
    evidence_count: int
    algorithm_version: str
    updated_at: str


@dataclass(frozen=True)
class ProbeStateRecord:
    learning_object_id: str
    status: str
    probe_phase_id: str | None
    hypothesis_set_id: str | None
    probe_attempts_completed: int
    probe_attempts_target: int
    families_converged: list[str]
    entered_at: str | None
    completed_at: str | None
    algorithm_version: str
    updated_at: str


@dataclass(frozen=True)
class ProbePresentationRecord:
    """A durable committed probe assignment (probe redesign spec §5.1)."""

    id: str
    probe_episode_id: str
    practice_item_id: str
    scheduler_candidate_id: str | None
    state_segment_id: str
    probe_family_template_id: str | None
    probe_family_template_version: int | None
    instrument_card_id: str | None
    instrument_card_version: int | None
    instrument_card_snapshot: dict[str, Any] | None
    target_hypothesis_pairs: list[list[str]]
    target_facets: list[str]
    posterior_at_selection: dict[str, float]
    entropy_at_selection: float | None
    expected_information_gain: float | None
    selection_policy_version: str | None
    selection_components: dict[str, Any]
    status: str
    end_reason: str | None
    served_at: str | None
    submitted_at: str | None
    expires_at: str | None
    ended_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ProbeObservationRecord:
    """The grading result + posterior transition for one consumed presentation (§5.1)."""

    id: str
    attempt_id: str
    posterior_before: dict[str, float]
    posterior_after: dict[str, float]
    entropy_before: float
    entropy_after: float
    realized_information_gain: float
    independent_evidence_discount: float | None
    contamination: dict[str, Any] | None
    grader_channel: dict[str, Any] | None
    updates_belief: bool
    eligible_for_completion: bool
    created_at: str
    # Logged-only observation features (§7.1) and the long-form structured
    # trace (§8.2). Never read by posterior replay.
    features: dict[str, Any] | None = None


def _decode_learning_outcome_label(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["metadata"] = _loads(payload.pop("metadata_json"), {})
    return payload


def _probe_state_record(row: sqlite3.Row) -> ProbeStateRecord:
    return ProbeStateRecord(
        learning_object_id=row["learning_object_id"],
        status=row["status"],
        probe_phase_id=row["probe_phase_id"],
        hypothesis_set_id=row["hypothesis_set_id"],
        probe_attempts_completed=row["probe_attempts_completed"],
        probe_attempts_target=row["probe_attempts_target"],
        families_converged=_loads(row["families_converged_json"], []),
        entered_at=row["entered_at"],
        completed_at=row["completed_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _probe_presentation_record(row: sqlite3.Row) -> ProbePresentationRecord:
    return ProbePresentationRecord(
        id=row["id"],
        probe_episode_id=row["probe_episode_id"],
        practice_item_id=row["practice_item_id"],
        scheduler_candidate_id=row["scheduler_candidate_id"],
        state_segment_id=row["state_segment_id"],
        probe_family_template_id=row["probe_family_template_id"],
        probe_family_template_version=row["probe_family_template_version"],
        instrument_card_id=row["instrument_card_id"],
        instrument_card_version=row["instrument_card_version"],
        instrument_card_snapshot=_loads(row["instrument_card_snapshot_json"], None),
        target_hypothesis_pairs=_loads(row["target_hypothesis_pairs_json"], []),
        target_facets=_loads(row["target_facets_json"], []),
        posterior_at_selection=_loads(row["posterior_at_selection_json"], {}),
        entropy_at_selection=row["entropy_at_selection"],
        expected_information_gain=row["expected_information_gain"],
        selection_policy_version=row["selection_policy_version"],
        selection_components=_loads(
            row["selection_components_json"] if "selection_components_json" in row.keys() else None, {}
        ),
        status=row["status"],
        end_reason=row["end_reason"],
        served_at=row["served_at"],
        submitted_at=row["submitted_at"],
        expires_at=row["expires_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _probe_observation_record(row: sqlite3.Row) -> ProbeObservationRecord:
    return ProbeObservationRecord(
        id=row["id"],
        attempt_id=row["attempt_id"],
        posterior_before=_loads(row["posterior_before_json"], {}),
        posterior_after=_loads(row["posterior_after_json"], {}),
        entropy_before=row["entropy_before"],
        entropy_after=row["entropy_after"],
        realized_information_gain=row["realized_information_gain"],
        independent_evidence_discount=row["independent_evidence_discount"],
        contamination=_loads(row["contamination_json"], None),
        grader_channel=_loads(row["grader_channel_json"], None),
        updates_belief=bool(row["updates_belief"]),
        eligible_for_completion=bool(row["eligible_for_completion"]),
        created_at=row["created_at"],
        features=_loads(row["features_json"], None) if "features_json" in row.keys() else None,
    )


def _decode_observation_template(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["emits_attempt"] = bool(payload["emits_attempt"])
    payload["active"] = bool(payload["active"])
    return payload


def _decode_observation_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["response"] = _loads(payload.pop("response_json"), {})
    return payload


def _decode_hypothesis_set(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["hypotheses"] = _loads(payload.pop("hypotheses_json"), [])
    payload["prior"] = _loads(payload.pop("prior_json"), {})
    return payload


def _decode_intervention_need(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_facets"] = _loads(payload.pop("target_facets_json"), [])
    payload["error_types"] = _loads(payload.pop("error_types_json"), [])
    payload["candidate_requirements"] = _loads(payload.pop("candidate_requirements_json"), {})
    payload["diagnostic_focus"] = _loads(payload.pop("diagnostic_focus_json", None), None)
    return payload


def _decode_attempt(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["evidence_facets"] = _loads(payload.pop("evidence_facets_json"), [])
    payload["evidence_weights"] = _loads(payload.pop("evidence_weights_json"), {})
    payload["manual_review"] = bool(payload["manual_review"])
    payload["primed"] = bool(payload.get("primed", 0))
    payload["declared_dont_know"] = bool(payload.get("declared_dont_know", 0))
    payload["declared_stuck"] = bool(payload.get("declared_stuck", 0))
    return payload


def _decode_followup_task(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    # Migration 124: the cold-verification inputs ride on the task itself.
    # Migration 139: so does the §5.7 certificate receipt.
    payload["context"] = _loads(payload.pop("context_json", None), None)
    return payload


def _decode_error_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["is_misconception"] = bool(payload["is_misconception"])
    payload["repair_plan"] = _loads(payload.pop("repair_plan_json"), None)
    return payload


def _decode_causal_hypothesis(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for field in (  # noqa: F402  a local loop variable; this function never calls dataclasses.field()
        "target_ref",
        "applicability",
        "postdictive_claims",
        "evidence",
    ):
        payload[field] = _loads(payload.pop(f"{field}_json"), None)
    return payload


def _decode_misconception_candidate(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "learning_object_id": row["learning_object_id"],
        "concept_id": row["concept_id"],
        "statement": row["statement"],
        "statement_normalized": row["statement_normalized"],
        "signature": row["signature"],
        "mechanism": row["mechanism"],
        "operation": row["operation"],
        "target_facet": row["target_facet"],
        "confused_with_facet": row["confused_with_facet"],
        "facet_ids": _loads(row["facet_ids_json"], []),
        "source_error_event_ids": _loads(row["source_error_event_ids_json"], []),
        "surface_families": _loads(row["surface_families_json"], []),
        "item_ids": _loads(row["item_ids_json"], []),
        "occurrence_count": row["occurrence_count"],
        "severity": row["severity"],
        "status": row["status"],
        "promoted_misconception_id": row["promoted_misconception_id"],
        "promotion_reason": row["promotion_reason"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _decode_surprise(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["predicted_score_dist"] = _loads(payload.pop("predicted_score_dist_json"), None)
    payload["predicted_error_type_dist"] = _loads(payload.pop("predicted_error_type_dist_json"), None)
    payload["observed_joint_bucket"] = _loads(payload.pop("observed_joint_bucket_json"), {})
    payload["posterior_delta"] = _loads(payload.pop("posterior_delta_json"), None)
    payload["triggered_actions"] = _loads(payload.pop("triggered_actions_json"), [])
    payload["suppressed_actions"] = _loads(payload.pop("suppressed_actions_json"), [])
    payload["gate_diagnostics"] = _loads(payload.pop("gate_diagnostics_json"), None)
    return payload


def _decode_scheduler_slate(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["session_context"] = _loads(payload.pop("session_context_json"), {})
    payload["config_snapshot"] = _loads(payload.pop("config_snapshot_json"), {})
    return payload
