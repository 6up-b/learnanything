"""Read-only boundary between persisted grading facts and store-free replay.

Phase 2's canonical attempt outcome view should replace this adapter, not the
harness. No compatibility scheduling state or fitted item-difficulty state is
read: both can contain information from after a predicted attempt.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

from learnloop.attempts.attempts import fsrs_rating_for_attempt
from learnloop.attempts.effective_observation import build_effective_observation
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.attempts.reveal_ledger import production_admissibility
from learnloop.clock import parse_utc
from learnloop.db.stores.families import family_judge_models
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.offline_outcomes import OutcomeRow, PredictionRow
from learnloop.learner.mastery import resolve_item_irt_params
from learnloop.scheduling.fsrs import rating_from_score
from learnloop.vault.models import PracticeItem


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()[:32]


def _graded_item(connection, attempt, evidence):
    """Require the selected snapshot AND the graded contract to agree."""
    contract_ids = {e.assessment_contract_version_id for e in evidence}
    if len(contract_ids) != 1 or None in contract_ids:
        return None, None
    contract_row = connection.execute(
        "SELECT contract_json FROM assessment_contract_versions WHERE id = ?",
        (next(iter(contract_ids)),),
    ).fetchone()
    if contract_row is None:
        return None, None
    contract = json.loads(contract_row[0])
    candidate_id = attempt.get("scheduler_candidate_id")
    if not candidate_id:
        return None, contract
    snapshots = connection.execute(
        """SELECT s.item_json, s.content_hash FROM decision_features d
           JOIN practice_item_snapshots s
             ON s.content_hash = json_extract(d.item_demand_vector_json, '$.content_hash')
           WHERE d.decision_id = ? AND d.decision_type = 'selection'
             AND s.practice_item_id = ? AND s.created_at <= ?""",
        (candidate_id, attempt["practice_item_id"], attempt["created_at"]),
    ).fetchall()
    if len(snapshots) != 1:
        return None, contract
    raw, content_hash = snapshots[0]
    if hashlib.sha256(raw.encode()).hexdigest() != content_hash:
        return None, contract
    item = PracticeItem.model_validate_json(raw)
    if (item.id != attempt["practice_item_id"]
            or contract.get("practice_item_id") != item.id):
        return None, contract
    if _canonical_hash({"prompt": item.prompt, "expected_answer": item.expected_answer}) != contract.get("item_content_hash"):
        return None, contract
    if item.grading_rubric and _canonical_hash(item.grading_rubric.model_dump(mode="json")) != contract.get("rubric_content_hash"):
        return None, contract
    return item, contract


def load_rows(vault, repository, *, legacy_fallback: str = "exclude",
              for_projection: bool = False) -> tuple[list[OutcomeRow], dict]:
    if legacy_fallback not in {"exclude", "current_content"}:
        raise ValueError("legacy_fallback must be exclude or current_content")
    rows = []
    statuses: Counter = Counter()
    policies = repository.all_causal_activity_classifications()
    # These are authored groupings, deliberately retrospective for the experiment.
    families = getattr(vault, "activity_families", {})
    with repository.connection() as connection:
        judge_models = family_judge_models(connection)
    prior_item_attempt: dict[str, str] = {}
    attempts = sorted(repository.list_all_attempts(),
                      key=lambda a: (a["created_at"], a["id"]))
    for attempt in attempts:
        aid = attempt["id"]
        at = parse_utc(attempt["created_at"])
        exclusion = None if at else "invalid_timestamp"
        at = at or datetime(1970, 1, 1, tzinfo=timezone.utc)
        current = vault.practice_items.get(attempt["practice_item_id"])
        evidence = repository.fetch_grading_evidence(aid)
        with repository.connection() as connection:
            item, contract = _graded_item(connection, attempt, evidence)
        revision = "exact" if item else "excluded"
        if item is None and legacy_fallback == "current_content" and current is not None:
            item, revision = current, "reconstructed_current"
        if item is None:
            exclusion = exclusion or ("missing_item" if current is None else "missing_graded_revision")
        statuses[revision] += 1
        # A later corrected label must not be trained at its original timestamp.
        # The projection is retrospective; evaluation conservatively drops such
        # attempts until Phase 2 supplies event-time correction observations.
        if repository.attempt_regrade_marker(aid) and not for_projection:
            exclusion = exclusion or "regraded_after_attempt"
        kind = attempt["attempt_type"]
        policy = resolve_attempt_activity_policy(
            attempt_type=kind, hints_used=int(attempt.get("hints_used") or 0),
            primed=bool(attempt.get("primed")), recorded=policies.get(aid))
        cold = not policy.counts_as_assisted and policy.eligible_for_fsrs
        if kind not in {"independent_attempt", "dont_know", "exam_attempt"}:
            cold = False
        # Ordinary submissions use the same since-last-item-attempt window as
        # attempts.reveal_total_for_submission. Receipt-backed cold measurements
        # instead own their explicit interval and unassisted/leakage findings.
        # Never use a full-history reveal veto: old exposure is absorbed by the
        # next attempt, not a permanent prohibition on spaced retrieval.
        since = prior_item_attempt.get(attempt["practice_item_id"])
        with repository.connection() as connection:
            receipt_rows = connection.execute(
                """SELECT dimensions_json, telemetry_coverage_json
                   FROM coldness_receipts
                   WHERE cold_attempt_id = ? AND stage = 'final'""", (aid,)).fetchall()
        receipt_starts = []
        for receipt in receipt_rows:
            dimensions = json.loads(receipt["dimensions_json"])
            interval = json.loads(receipt["telemetry_coverage_json"]).get("interval") or {}
            start = parse_utc(interval.get("from"))
            end = parse_utc(interval.get("to"))
            valid_interval = start is not None and end == at and start <= at
            if valid_interval:
                receipt_starts.append(start)
            cold = cold and valid_interval and all(
                dimensions.get(name, {}).get("status") == "pass"
                for name in ("unassisted", "answer_leakage"))
        if receipt_starts:
            # Multiple receipts cannot narrow one another's absence claims.
            since = min(receipt_starts).isoformat()
        # Research fails on unknown coldness instead of taking the helper's
        # live best-effort fallback.
        cold = cold and production_admissibility(
            repository, practice_item_id=attempt["practice_item_id"],
            learning_object_id=attempt["learning_object_id"],
            since=since, produced_at=attempt["created_at"], strict=True).admissible
        prior_item_attempt[attempt["practice_item_id"]] = attempt["created_at"]
        observation = repository.observation_by_attempt(aid)
        interpretation = (
            repository.active_interpretation_for_observation(observation["id"])
            if observation else None)
        if interpretation and interpretation.get("quarantine_state") == "quarantined":
            exclusion = exclusion or "quarantined"
        if kind in {"skip", "guided_walkthrough", "self_report", "open_text", "teach_back"}:
            exclusion = exclusion or "not_graded_retrieval"
        effective = build_effective_observation(
            repository, interpretation=interpretation, score_fraction={},
            attempt_type_mass=attempt_evidence_mass(kind, vault.config.evidence))
        mass = effective.effective_mass
        if kind == "dont_know" and exclusion is None:
            # An explicit inability to answer is observed failure, not an
            # uncertain LLM grade. Field §4.3 gives it full predictor mass.
            mass = 1.0
        # Missing calibration never becomes fabricated ability evidence.
        # Graded cold memory eligibility is independent of this mass.
        rubric = vault.rubric_for_item(item) if item else None
        max_points = float(contract.get("rubric_max_points", 4)) if contract else (
            float(rubric.max_points) if rubric else 4)
        if kind == "dont_know":
            fraction = 0.0
        elif evidence and contract:
            total = float(contract.get("rubric_total") or max_points)
            fraction = sum(e.points_awarded for e in evidence)/max(total, 1e-9)
        elif attempt.get("rubric_score") is not None:
            fraction = float(attempt["rubric_score"])/max(max_points, 1e-9)
        else:
            fraction = 0.0
            exclusion = exclusion or "ungraded"
        fraction = min(1.0, max(0.0, fraction))
        # FSRS consumes the persisted rounded, max-point/fatal-capped grade,
        # not the continuous criterion fraction used for prediction metrics.
        # Keep the authored hint cap too (including a cap at zero hints).
        score = 0 if kind == "dont_know" else attempt.get("rubric_score")
        if score is None:
            exclusion = exclusion or "missing_fsrs_grade"
            score = 0
        rating = (fsrs_rating_for_attempt(item, score, max_points,
                                         int(attempt.get("hints_used") or 0))
                  if item else rating_from_score(score, max_points))
        lo = vault.learning_objects.get(attempt["learning_object_id"])
        # Never use a full-log EB posterior to predict an earlier answer.
        difficulty_variance = 0.0
        irt_item = item
        if item and item.difficulty_source == "llm_estimate":
            irt_item = item.model_copy(update={"difficulty": None})
            difficulty_variance = 1.0
        a, b = resolve_item_irt_params(irt_item, lo, vault.config.mastery)
        if attempt.get("primed"):
            b -= vault.config.mastery.irt.priming_b_offset
        family_id = getattr(current, "family_id", None)
        relation = getattr(current, "variant_relation", None)
        if family_id not in families:
            family_id, relation = None, None
        origin = "unknown"
        if attempt.get("collection_version") != "legacy-unversioned":
            if attempt.get("probe_presentation_id"):
                origin = "system_probe"
            elif attempt.get("scheduler_candidate_id"):
                with repository.connection() as connection:
                    offer = connection.execute(
                        """SELECT 1 FROM scheduler_slate_candidates c
                           JOIN scheduler_offer_receipts o ON o.slate_id = c.slate_id
                           JOIN json_each(o.returned_candidate_ids_json) j ON j.value = c.id
                           WHERE c.id = ?""", (attempt["scheduler_candidate_id"],)).fetchone()
                if offer:
                    origin = "learner_pick"
        model = "unknown"
        if observation:
            events = repository.raw_grade_events_for_observation(observation["id"])
            if events:
                latest = events[-1]
                model = str(latest.get("grader_model_revision") or latest.get("grader_provider") or "unknown")
        features = PredictionRow(
            aid, at, attempt["practice_item_id"], attempt["learning_object_id"],
            family_id=family_id, variant_relation=relation,
            subject=attempt.get("subject") or "unknown",
            topic=attempt.get("concept") or "unknown", serving_origin=origin,
            revision_status=revision, grader_model=model,
            observation_status=effective.calibration_status, discrimination=a, difficulty=b,
            difficulty_variance=difficulty_variance, effective_mass=mass,
            family_judge_models=judge_models.get(family_id, ()))
        rows.append(OutcomeRow(features, fraction, int(rating),
                               exclusion=exclusion, cold=cold))
    return rows, {"revision_counts": dict(sorted(statuses.items())),
                  "family_judge_models": sorted({model for family_id, models in judge_models.items()
                                                 if family_id in families for model in models}),
                  "legacy_fallback": legacy_fallback,
                  "distance_source": "unavailable: PF-b skeleton measurements not present",
                  "difficulty_source": "historical authored/LO prior; no full-log EB posterior",
                  "outcome": "criterion points / pinned rubric total; legacy fallback: rubric_score / max_points",
                  "memory_rating": "persisted rounded/fatal-capped rubric_score with authored hint cap",
                  "coldness_window": "receipt interval when present; otherwise since prior item attempt, item-or-LO reveals through production"}
