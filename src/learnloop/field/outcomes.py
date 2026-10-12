"""Read-only outcome projection over grading ledgers, never the debug trace.

The public loaders derive rows rather than trusting a possibly stale cache.
Only ``rebuild_outcome_view`` writes, and only to this module's DERIVED table.
Missing or ambiguous historical item/rubric provenance fails closed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import nullcontext
from dataclasses import fields, replace
import hashlib
import json
import sqlite3
from types import SimpleNamespace
from typing import Any

from learnloop.algorithm_versions import P0_SUCCESSOR_VERSIONS, P0_ALGORITHM_VERSION
from learnloop.attempts.attempts import fsrs_rating_for_attempt
from learnloop.attempts.effective_observation import (
    build_effective_observation,
    effective_observation_from_posterior,
    load_effective_observation_references,
)
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.attempts.reveal_ledger import production_admissibility
from learnloop.attempts.stuck import stuck_answer_summary
from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.db.stores.families import family_judge_models
from learnloop.db.stores.field import replace_facet_outcomes
from learnloop.db.stores.observation_ledger import load_authoritative_observation_ledger
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.field.types import AttemptRow, FacetRow, ItemFeatures
from learnloop.field.signals import enrich_attempts, load_interaction_signals
from learnloop.learner.assessment_contracts import compile_assessment_contract, rubric_from_contract
from learnloop.learner.mastery import resolve_item_irt_params
from learnloop.learner.recall_coverage import (
    derive_facet_outcomes,
    familiarity_discount_from_attempts,
    resolve_coverage,
    resolve_reliability,
    scale_coverage_for_graded_criteria,
)
from learnloop.substrate.canonical_projection import UNVERIFIED_CRITERION_BLOCK, surface_group_id
from learnloop.vault.models import LoadedVault, PracticeItem

OUTCOME_VIEW_VERSION = "facet-outcomes-v1"


class _ReadRepository(Repository):
    """Borrow the caller's transaction; repository reads must not commit it."""

    def __init__(self, connection: sqlite3.Connection):
        self._borrowed = connection

    def connection(self):
        return nullcontext(self._borrowed)


def borrowed_repository(connection: sqlite3.Connection) -> Repository:
    """A repository view that reads inside the caller's open snapshot."""
    return _ReadRepository(connection)


def _json(value: str | None, default: Any = None) -> Any:
    return json.loads(value) if value else default


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _serving(connection, attempt):
    candidate_id = attempt.get("scheduler_candidate_id")
    intent = connection.execute(
        "SELECT * FROM submission_intents WHERE submission_id=? AND practice_item_id=?",
        (attempt.get("submission_id"), attempt["practice_item_id"]),
    ).fetchone()
    if intent:
        candidate_id = intent["scheduler_candidate_id"]
    # No inference from old queue ordering or today's mutable task state.
    if attempt.get("collection_version") == "legacy-unversioned":
        return "unknown", None, candidate_id
    presentation = connection.execute(
        "SELECT * FROM probe_presentations WHERE id=? AND practice_item_id=?",
        (attempt.get("probe_presentation_id"), attempt["practice_item_id"]),
    ).fetchone()
    if presentation:
        candidate_id = presentation["scheduler_candidate_id"] or candidate_id
        # The actual candidate schema has selection_propensity and
        # propensity_kind, but its only producer records
        # unavailable_composed_offer (older rows: legacy-unverified).
        # Neither proves a system-probe action probability. No verified
        # kind exists yet, so even a non-null number is not usable.
        return "system_probe", None, candidate_id
    candidate = connection.execute(
        "SELECT * FROM scheduler_slate_candidates WHERE id=? AND practice_item_id=?",
        (candidate_id, attempt["practice_item_id"]),
    ).fetchone()
    if candidate:
        components = _json(candidate["components_json"], {})
        if any(components.get(key, 0) for key in (
            "intervention_followup", "negative_surprise_followup",
        )):
            return "forced_followup", None, candidate_id
        offer = connection.execute(
            "SELECT returned_candidate_ids_json FROM scheduler_offer_receipts WHERE slate_id=?",
            (candidate["slate_id"],),
        ).fetchone()
        if intent and offer and candidate_id in _json(offer[0], []):
            return "learner_pick", None, candidate_id
    # Current immutable receipts record an entry surface, not a request kind.
    # Neither free text nor mutable task state proves a direct request.
    return "unknown", None, candidate_id


def _revision(connection, vault, attempt, evidence, candidate_id, fallback):
    contract_ids = {r["assessment_contract_version_id"] for r in evidence}
    contract = None
    if len(contract_ids) == 1 and None not in contract_ids:
        stored = connection.execute(
            "SELECT contract_json FROM assessment_contract_versions WHERE id=? AND practice_item_id=?",
            (next(iter(contract_ids)), attempt["practice_item_id"]),
        ).fetchone()
        if stored:
            contract = _json(stored[0])
    demand = connection.execute(
        """SELECT item_demand_vector_json FROM decision_features
        WHERE decision_type='selection' AND decision_id=? AND created_at<=?""",
        (candidate_id, attempt["created_at"]),
    ).fetchone()
    digest = _json(demand[0], {}).get("content_hash") if demand else None
    snapshot = connection.execute(
        """SELECT item_json FROM practice_item_snapshots
        WHERE content_hash=? AND practice_item_id=? AND created_at<=?""",
        (digest, attempt["practice_item_id"], attempt["created_at"]),
    ).fetchone()
    if snapshot and contract:
        raw = snapshot[0]
        if hashlib.sha256(raw.encode()).hexdigest() == digest:
            item = PracticeItem.model_validate_json(raw)
            rubric = rubric_from_contract(contract)
            # The selection receipt alone does not prove that the selected
            # revision was graded: an edit can happen before submission.
            content_matches = _hash({
                "prompt": item.prompt, "expected_answer": item.expected_answer,
            }) == contract.get("item_content_hash")
            # A contract freezes the rubric even for mode-level rubrics.
            # Explicit item rubrics must agree with that frozen revision.
            rubric_matches = item.grading_rubric is None or (
                _hash(item.grading_rubric.model_dump(mode="json"))
                == contract.get("rubric_content_hash")
            )
            receipt_matches = (
                item.id == attempt["practice_item_id"]
                and item.learning_object_id == attempt["learning_object_id"]
                and item.practice_mode == attempt["practice_mode"]
                and item.evidence_facets == _json(attempt.get("evidence_facets_json"))
                and item.evidence_weights == _json(attempt.get("evidence_weights_json"))
            )
            # Compile solely from the selected item and frozen rubric, never
            # today's LO/mode configuration. Authored targets must match too.
            selected_contract = compile_assessment_contract(
                SimpleNamespace(learning_objects={}), item,
                rubric=item.grading_rubric or rubric,
            )
            contract_matches = all(
                selected_contract[key] == contract.get(key)
                for key in (
                    "practice_item_id", "learning_object_id", "practice_mode",
                    "criteria", "evidence_fingerprint", "surface_family",
                    "trace_contract", "variant_contract", "assistance",
                )
            )
            # No immutable graded full-item hash exists. Contracts retain
            # target identities, but not numeric criterion_facet_weights.
            # Only a single-facet positive mapping has a unique normalized
            # allocation; multi-facet receipts cannot prove numeric weights.
            single_facet = len(item.evidence_facets) == 1
            unique_mapping = single_facet and all(
                not mapping or (
                    set(mapping) == set(item.evidence_facets)
                    and all(weight > 0 for weight in mapping.values())
                )
                for mapping in item.criterion_facet_weights.values()
            )
            if content_matches and rubric_matches and receipt_matches and contract_matches and unique_mapping:
                return item, rubric, digest, "exact"
    if fallback == "current_content":
        item = vault.practice_items.get(attempt["practice_item_id"])
        if item is not None:
            rubric = vault.rubric_for_item(item)
            if rubric is not None:
                return item, rubric, None, "reconstructed_current"
    return None, None, digest, "excluded"


# Graded retrievals that can be FSRS reviews; everything else is never memory.
GRADED_RETRIEVAL_TYPES = frozenset({"independent_attempt", "dont_know", "exam_attempt"})


def resolve_legacy_fallback(vault, legacy_fallback=None) -> str:
    """The single revision policy: an explicit option, else ``field.legacy_fallback``."""
    fallback = legacy_fallback or getattr(getattr(vault.config, "field", None), "legacy_fallback", "exclude")
    if fallback not in {"exclude", "current_content"}:
        raise ValueError("legacy_fallback must be exclude or current_content")
    return fallback


def _unverified(record) -> bool:
    """A criterion the PF-c valid-alternative gate recorded as unverified."""
    attribution = record.get("attribution_json")
    return isinstance(attribution, dict) and (
        attribution.get("negative_evidence_blocked") == UNVERIFIED_CRITERION_BLOCK
    )


def _grader_models(connection) -> dict[str, str]:
    """Latest raw grade event of each attempt's latest observation (no text)."""
    rows = connection.execute(
        """WITH ranked AS (
               SELECT o.id, o.attempt_id, ROW_NUMBER() OVER (
                   PARTITION BY o.attempt_id ORDER BY o.created_at DESC, o.id DESC
               ) AS replay_rank
                 FROM activity_observations AS o WHERE o.attempt_id IS NOT NULL)
           SELECT ranked.attempt_id, r.grader_model_revision, r.grader_provider
             FROM ranked JOIN raw_grade_events AS r ON r.observation_id = ranked.id
            WHERE ranked.replay_rank = 1
            ORDER BY r.created_at, r.id"""
    )
    return {row[0]: str(row[1] or row[2] or "unknown") for row in rows}


def _retrieval_cold(connection, repository, attempt, policy, since):
    """Strict research coldness for memory arms; returns (cold, window start).

    Ordinary submissions use the since-last-item-attempt window. A final
    coldness receipt instead owns its explicit interval and its unassisted and
    answer-leakage findings. Old exposure is absorbed by the next attempt,
    never a permanent veto. Unknown coldness fails: the reveal lookup is
    strict, unlike the live best-effort helper.
    """
    at = parse_utc(attempt["created_at"])
    cold = (
        at is not None and not policy.counts_as_assisted and policy.eligible_for_fsrs
        and attempt["attempt_type"] in GRADED_RETRIEVAL_TYPES
    )
    receipt_starts = []
    for receipt in connection.execute(
        """SELECT dimensions_json, telemetry_coverage_json FROM coldness_receipts
           WHERE cold_attempt_id = ? AND stage = 'final' ORDER BY id""",
        (attempt["id"],),
    ):
        dimensions = _json(receipt[0], {})
        interval = _json(receipt[1], {}).get("interval") or {}
        start, end = parse_utc(interval.get("from")), parse_utc(interval.get("to"))
        valid_interval = start is not None and at is not None and end == at and start <= at
        if valid_interval:
            receipt_starts.append(start)
        cold = cold and valid_interval and all(
            dimensions.get(name, {}).get("status") == "pass"
            for name in ("unassisted", "answer_leakage")
        )
    if receipt_starts:
        # Multiple receipts cannot narrow one another's absence claims.
        since = min(receipt_starts).isoformat()
    return cold and production_admissibility(
        repository, practice_item_id=attempt["practice_item_id"],
        learning_object_id=attempt["learning_object_id"],
        since=since, produced_at=attempt["created_at"], strict=True,
    ).admissible


def _load(connection, vault, *, legacy_fallback=None, as_of=None, retrieval=False, diagnostics=None):
    """Derive attempt and facet rows; ``retrieval`` adds the memory-arm fields.

    The family grouping is the CURRENT authored assignment, deliberately
    retrospective (PF-a applies families after the fact); it never retargets a
    row's LO, outcome or revision status.
    """
    fallback = resolve_legacy_fallback(vault, legacy_fallback)
    repository = _ReadRepository(connection)
    ledger = {r["attempt_id"]: r for r in load_authoritative_observation_ledger(connection)}
    references = load_effective_observation_references(
        repository, (r.get("active_interpretation") for r in ledger.values()),
    )
    activity_by_attempt = repository.all_causal_activity_classifications()
    merges = dict(connection.execute("SELECT retired_facet_id,surviving_facet_id FROM facet_merges"))

    def canonical(facet):
        current = vault.canonical_facet_id(facet)
        seen = set()
        while current in merges:
            if current in seen:
                raise ValueError("cyclic facet merge")
            seen.add(current)
            current = vault.canonical_facet_id(merges[current])
        return current

    families = getattr(vault, "activity_families", {}) or {}
    judge_models = family_judge_models(connection) if families else {}
    grader_models = _grader_models(connection) if retrieval else {}
    attempts, facets = [], []
    recent_by_lo = defaultdict(list)
    prior_item_attempt: dict[str, str] = {}
    ungraded = Counter()
    unverified_attempts: set[str] = set()
    for raw_attempt in connection.execute("SELECT * FROM practice_attempts ORDER BY created_at,id"):
        attempt = dict(raw_attempt)
        if as_of is not None and attempt["created_at"] > as_of:
            continue
        source = ledger[attempt["id"]]
        evidence = source["evidence"]
        # Every earlier attempt on the item closes a reveal window, graded or not.
        since = prior_item_attempt.get(attempt["practice_item_id"])
        prior_item_attempt[attempt["practice_item_id"]] = attempt["created_at"]
        if not evidence or attempt["attempt_type"] == "skip":
            ungraded["skip" if attempt["attempt_type"] == "skip" else "no_grading_evidence"] += 1
            continue
        # Partial supersession is cumulative: select the latest surviving
        # record for each criterion, not merely the largest revision number.
        evidence = list({
            r["criterion_id"]: r
            for r in sorted(evidence, key=lambda r: r["grading_revision"] or -1)
        }.values())
        # PF-c (Slice 1 M2): a criterion the valid-alternative gate recorded as
        # unverified (the final answer verifies; the grader marked it down
        # without locating an error) is not a measurement until it is reviewed.
        # The projection banks no negative mass for it; here it is unassessed,
        # like a criterion the grader never scored, so its shortfall is never a
        # failure outcome and its kept points are not credited either.
        unverified = {r["criterion_id"] for r in evidence if _unverified(r)}
        if unverified:
            unverified_attempts.add(attempt["id"])
            if all(r["criterion_id"] in unverified for r in evidence):
                ungraded[UNVERIFIED_CRITERION_BLOCK] += 1
                continue
        origin, propensity, candidate_id = _serving(connection, attempt)
        item, rubric, digest, status = _revision(
            connection, vault, attempt, evidence, candidate_id, fallback,
        )
        primed = bool(attempt.get("primed"))
        hints = int(attempt["hints_used"] or 0)
        policy = resolve_attempt_activity_policy(
            attempt_type=attempt["attempt_type"], hints_used=hints, primed=primed,
            recorded=activity_by_attempt.get(attempt["id"]),
        )
        lo_id = attempt["learning_object_id"]
        points = {
            r["criterion_id"]: float(r["points_awarded"])
            for r in evidence if r["criterion_id"] not in unverified
        }
        dont_know = attempt["attempt_type"] == "dont_know" or bool(attempt.get("declared_dont_know"))
        outcome = 0.0
        covered = {}
        effective_mass = mass_without_assistance = 0.0
        calibration_status = "excluded_revision"
        outcomes = {}
        if item is not None:
            assessed_max = sum(float(c.points) for c in rubric.criteria if c.id in points)
            assessed_points = sum(
                min(float(c.points), max(0.0, points[c.id]))
                for c in rubric.criteria if c.id in points
            )
            outcome = (
                min(1.0, max(0.0, assessed_points / assessed_max))
                if assessed_max > 0 and not dont_know else 0.0
            )
            coverage = resolve_coverage(
                item, rubric, attempt_type=attempt["attempt_type"], hints_used=hints,
                learner_answer_md=attempt.get("learner_answer_md") or "", evidence=vault.config.evidence,
                declared_stuck=bool(attempt.get("declared_stuck")),
            )
            coverage = scale_coverage_for_graded_criteria(coverage, item, rubric, criterion_points=points)
            covered = coverage.covered_facets
            # A dont_know answer is still a measurement even with no engagement.
            if dont_know:
                covered = coverage.normalized_facet_weights
            reliability = resolve_reliability(
                item, attempt_type=attempt["attempt_type"], hints_used=hints,
                grader_confidence=1.0, evidence=vault.config.evidence,
            )
            familiarity = familiarity_discount_from_attempts(
                recent_by_lo[lo_id][-vault.config.recall_coverage.familiarity_recent_attempt_window:],
                item, covered_facets=covered, config=vault.config,
            ).independent_evidence_discount
            kwargs = dict(
                attempt_type_mass=attempt_evidence_mass(attempt["attempt_type"], vault.config.evidence),
                assistance_discount=1.0 if dont_know else reliability.trace["hint_mastery_factor"],
                familiarity_discount=1.0 if dont_know else familiarity,
                score_fraction={}, unassessable=attempt["attempt_type"] == "unassessable",
            )
            interpretation = source.get("active_interpretation")
            if interpretation is not None or vault.config.algorithms.algorithm_version in (
                P0_ALGORITHM_VERSION, *P0_SUCCESSOR_VERSIONS,
            ):
                effective = build_effective_observation(
                    repository, interpretation=interpretation, references=references, **kwargs,
                )
            else:
                # Pre-calibration evidence remains readable: the criterion
                # ledger is the deterministic observation, not a debug copy.
                effective = effective_observation_from_posterior(
                    observation_id=None, posterior={"graded": 1.0}, certainty_lcb=1.0, **kwargs,
                )
            effective_mass = effective.effective_mass
            calibration_status = effective.calibration_status
            mass_without_assistance = replace(
                effective, assistance_discount=1.0,
                attempt_type_mass=(
                    attempt_evidence_mass("independent_attempt", vault.config.evidence)
                    if attempt["attempt_type"] == "hinted_attempt" else effective.attempt_type_mass
                ),
            ).effective_mass
            attributions = []
            for record in evidence:
                attribution = record.get("attribution_json")
                if not isinstance(attribution, dict) or attribution.get("negative_evidence_blocked"):
                    continue
                targets = set(attribution.get("target_evidence_families") or [])
                targets.update(
                    target["facet"] for target in attribution.get("targets", [])
                    if isinstance(target, dict) and target.get("facet")
                )
                canonical_targets = {canonical(target) for target in targets}
                # Derive on historical item IDs; canonicalize only the result.
                # Error targets may already use the surviving alias/merge ID.
                attributions.append(SimpleNamespace(target_evidence_families=[
                    facet for facet in item.evidence_facets
                    if canonical(facet) in canonical_targets
                ]))
            outcomes = derive_facet_outcomes(
                item, rubric, criterion_points=points, covered_facets=covered,
                correctness=outcome, attempt_type="dont_know" if dont_know else attempt["attempt_type"],
                error_attributions=attributions,
            )
        else:
            # Preserve exclusion accounting at facet granularity where the
            # attempt itself retained coverage. These are zero-mass placeholders,
            # not guessed outcomes and never reads of today's content.
            recorded_weights = _json(attempt.get("evidence_weights_json"), {})
            recorded_facets = _json(attempt.get("evidence_facets_json"), [])
            covered = {
                facet: max(0.0, float(recorded_weights.get(facet, 1.0)))
                for facet in recorded_facets
            }
            outcomes = {facet: 0.0 for facet in covered}
        # Today's LO is not a historical demand receipt.
        difficulty_source = (item.difficulty_source or "authored") if item else "missing"
        llm_estimate = difficulty_source == "llm_estimate"
        a, b = resolve_item_irt_params(
            None if llm_estimate else item, None, vault.config.mastery,
        )
        demand = {}
        if status == "exact":
            stored_demand = connection.execute(
                """SELECT item_demand_vector_json FROM decision_features
                WHERE decision_type='selection' AND decision_id=? AND created_at<=?""",
                (candidate_id, attempt["created_at"]),
            ).fetchone()
            demand = _json(stored_demand[0], {}) if stored_demand else {}
            # Captured authored/LO demand, not today's LO defaults. The
            # scheduler did not historically record empirical-Bayes state.
            a = float(demand.get("discrimination_a", a))
            b = float(demand.get("difficulty_b", b))
        if "difficulty_b" not in demand and (
            item is None or item.difficulty is None or llm_estimate
        ):
            difficulty_source += "_missing_historical_prior"
        # Retrospective PF-a grouping from today's authored families (above).
        current = vault.practice_items.get(attempt["practice_item_id"])
        family_id = getattr(current, "family_id", None)
        relation = getattr(current, "variant_relation", None)
        if family_id not in families:
            family_id, relation = None, None
        # FSRS consumes the persisted rounded, max-point/fatal-capped grade with
        # the authored hint cap, not the continuous criterion fraction.
        fsrs_rating = None
        score = 0 if dont_know else attempt.get("rubric_score")
        quarantined = (source.get("quarantine_state") == "quarantined")
        if (retrieval and item is not None and score is not None and not quarantined
                and attempt["attempt_type"] in GRADED_RETRIEVAL_TYPES):
            fsrs_rating = int(fsrs_rating_for_attempt(item, score, rubric.max_points, hints))
        retrieval_cold = bool(
            retrieval and fsrs_rating is not None
            and _retrieval_cold(connection, repository, attempt, policy, since)
        )
        # Captured demand stays fixed, including LLM estimates. Uncertainty
        # widens the observation, never replaces b with today's LO prior.
        feature = ItemFeatures(
            item_id=attempt["practice_item_id"], lo_id=lo_id,
            observed_at=attempt["created_at"], subject_id=attempt["subject"] or "default",
            a=a, b=b, primed=primed, cold=not policy.counts_as_assisted and not primed,
            capability=item.capability if item else None,
            family_id=family_id, variant_relation=relation,
            difficulty_source=difficulty_source, difficulty_variance=1.0 if llm_estimate else 0.0,
        )
        row = AttemptRow(
            attempt_id=attempt["id"], features=feature, outcome=outcome,
            effective_mass=effective_mass, mass_without_assistance=mass_without_assistance,
            revision_status=status, assisted=policy.counts_as_assisted, hints_used=hints,
            serving_origin=origin, serving_propensity=propensity, scheduler_candidate_id=candidate_id,
            surface_group_id=surface_group_id(item) if item else None, item_snapshot_hash=digest,
            fsrs_rating=fsrs_rating, retrieval_cold=retrieval_cold,
            grader_model=grader_models.get(attempt["id"], "unknown"),
            calibration_status=calibration_status,
            family_judge_models=judge_models.get(family_id, ()) if family_id else (),
        )
        attempts.append(row)
        merged = defaultdict(lambda: [0.0, 0.0])
        for facet, weight in covered.items():
            merged[canonical(facet)][0] += weight
            merged[canonical(facet)][1] += weight * outcomes[facet]
        total = sum(v[0] for v in merged.values())
        for facet, (weight, positive) in sorted(merged.items()):
            if weight <= 0:
                continue
            values = {f.name: getattr(row, f.name) for f in fields(AttemptRow)}
            values["outcome"] = positive / weight
            facets.append(FacetRow(**values, facet_id=facet, facet_share=weight / total))
        if row.effective_mass > 0:
            recent_by_lo[lo_id].append({
                "id": row.attempt_id, "practice_item_id": feature.item_id, "attempt_type": attempt["attempt_type"],
                "correctness": outcome, "surface_family": item.surface_family if item else None,
                "evidence_facets": list(covered),
            })
    if diagnostics is not None:
        diagnostics["attempts_without_outcome_row"] = dict(sorted(ungraded.items()))
        diagnostics["unverified_criterion_attempts"] = unverified_attempts
    return tuple(attempts), tuple(facets)


def load_attempt_rows(
    connection, vault: LoadedVault, *, legacy_fallback=None, as_of=None, retrieval=False,
) -> tuple[AttemptRow, ...]:
    """Immutable attempt rows, including zero-mass exclusions for accounting.

    ``as_of`` is an attempt-completion cutoff, not a point-in-time reconstruction
    of grader knowledge: the latest surviving grading epoch remains authoritative.
    ``retrieval`` also derives the memory-arm fields (FSRS rating, strict
    coldness, grader model); the DERIVED facet cache never needs them.
    """
    return _load(connection, vault, legacy_fallback=legacy_fallback, as_of=as_of, retrieval=retrieval)[0]


def load_replay_rows(connection, vault: LoadedVault, *, legacy_fallback=None):
    """Attempt and facet rows for one prequential replay, read in one pass."""
    return _load(connection, vault, legacy_fallback=legacy_fallback, retrieval=True)


def load_effective_replay_rows(connection, vault: LoadedVault, *, legacy_fallback=None):
    """``(attempts, facets, signals)`` with the complete coldness derivation.

    The one place interaction signals (linked leak telemetry, help before work)
    are folded into replay rows. Evaluation and the family-memory projection
    both read it, so they fold the same effective history (review F7).
    """
    attempts, facets = load_replay_rows(connection, vault, legacy_fallback=legacy_fallback)
    signals = load_interaction_signals(connection, vault, attempts)
    return enrich_attempts(attempts, signals), enrich_attempts(facets, signals), signals


def load_facet_rows(connection, vault: LoadedVault, *, legacy_fallback=None, as_of=None) -> tuple[FacetRow, ...]:
    return _load(connection, vault, legacy_fallback=legacy_fallback, as_of=as_of)[1]


def rebuild_outcome_view(connection, vault: LoadedVault, *, legacy_fallback=None) -> int:
    """Replace only the outcome cache; transaction ownership stays with caller."""
    rows = load_facet_rows(connection, vault, legacy_fallback=legacy_fallback)
    replace_facet_outcomes(
        connection,
        [(r.attempt_id, r.facet_id, r.features.item_id, r.item_snapshot_hash, r.revision_status,
          r.features.observed_at, r.outcome, r.facet_share, r.effective_mass, int(r.features.cold),
          int(r.assisted), int(r.features.primed), r.surface_group_id, r.serving_origin,
          r.serving_propensity, r.scheduler_candidate_id) for r in rows],
    )
    return len(rows)


def data_check(connection, vault: LoadedVault, *, legacy_fallback=None) -> dict[str, Any]:
    """Aggregate-only diagnostic; no learner answers, prompts or debug text."""
    load_diagnostics: dict[str, Any] = {}
    attempts, facets = _load(
        connection, vault, legacy_fallback=legacy_fallback, retrieval=True, diagnostics=load_diagnostics,
    )
    interaction_diagnostics: dict[str, Any] = {}
    signals = load_interaction_signals(connection, vault, attempts, diagnostics=interaction_diagnostics)
    # Count with the same leak-aware coldness the reports and projection use.
    attempts = enrich_attempts(attempts, signals)
    direct = [r for r in facets if r.effective_mass > 0]
    by_lo = defaultdict(set)
    for row in direct:
        by_lo[row.features.lo_id].add(row.facet_id)
    by_attempt = defaultdict(list)
    for row in direct:
        by_attempt[row.attempt_id].append(row)
    separate_by_lo = defaultdict(set)
    for rows in by_attempt.values():
        if len(rows) == 1:
            separate_by_lo[rows[0].lo_id].add(rows[0].facet_id)
    # Validation only. A corrupt/stale debug payload cannot affect any row.
    debug_by_attempt = {}
    invalid_debug = 0
    for stored in connection.execute("SELECT attempt_id,payload_json FROM attempt_debug_payloads"):
        try:
            payload = _json(stored["payload_json"], {})
            outcomes = payload.get("facet_outcomes", {})
            if not isinstance(outcomes, dict):
                raise ValueError("non-object debug outcomes")
            debug_by_attempt[stored["attempt_id"]] = outcomes
        except (ValueError, AttributeError):
            invalid_debug += 1
    compared = mismatched = 0
    unverified_attempts = load_diagnostics["unverified_criterion_attempts"]
    for row in facets:
        # The live debug outcome scores a PF-c unverified criterion; the field
        # leaves it unassessed (above), so the two are not comparable there.
        if row.attempt_id in unverified_attempts:
            continue
        recorded = debug_by_attempt.get(row.attempt_id, {}).get(row.facet_id)
        if row.revision_status == "exact" and isinstance(recorded, (float, int)):
            compared += 1
            mismatched += abs(recorded - row.outcome) > 1e-10
    return {
        "outcome_view_version": OUTCOME_VIEW_VERSION,
        "interaction_signals": interaction_diagnostics,
        # mvp-0.11: the share of stuck answers with text and their grading wait.
        "stuck_answers": stuck_answer_summary(connection),
        "legacy_fallback": resolve_legacy_fallback(vault, legacy_fallback),
        "graded_attempts": len(attempts),
        "eligible_attempts": sum(r.effective_mass > 0 for r in attempts),
        "attempts_without_outcome_row": load_diagnostics["attempts_without_outcome_row"],
        "pf_c_unverified_attempts": len(unverified_attempts),
        "memory": {
            "graded_cold_retrievals": sum(r.memory_scored for r in attempts),
            "memory_training_rows": sum(r.memory_eligible for r in attempts),
            "familied_attempts": sum(r.features.family_id is not None for r in attempts),
            "fsrs_rated_attempts": sum(r.fsrs_rating is not None for r in attempts),
        },
        "revision_status": dict(Counter(r.revision_status for r in attempts)),
        "serving_origin": dict(Counter(r.serving_origin for r in attempts)),
        "serving_propensity_availability": {
            "available": sum(r.serving_propensity is not None for r in attempts),
            "unavailable": sum(r.serving_propensity is None for r in attempts),
            "system_probe_unavailable": sum(
                r.serving_origin == "system_probe" and r.serving_propensity is None for r in attempts
            ),
        },
        "learning_objects_with_direct_evidence": len(by_lo),
        "facets_with_direct_evidence": len({r.facet_id for r in direct}),
        "measured_facets_per_lo_histogram": dict(Counter(len(v) for v in by_lo.values())),
        "separately_measured_facets_per_lo_histogram": dict(Counter(
            len(separate_by_lo[lo]) for lo in by_lo
        )),
        "separate_measurement_definition": "Conservative lower bound: facets measured alone in an attempt.",
        "zero_mass_attempts": sum(r.effective_mass == 0 for r in attempts),
        "missing_covariates": {
            "historical_retrievability": sum(r.features.retrievability is None for r in attempts),
            "historical_empirical_bayes_difficulty": len(attempts),
            "historical_difficulty_prior": sum(
                r.features.difficulty_source.endswith("_missing_historical_prior") for r in attempts
            ),
        },
        "debug_validation": {"compared": compared, "mismatched": mismatched},
        "invalid_debug_payloads": invalid_debug,
        "prequential": True,
        "limitations": [
            "Latest surviving grading epochs; later regrades retrospectively replace earlier outcomes.",
            "Historical item snapshots require a linked selection receipt and matching grading contract.",
            "No immutable full graded-item hash or numeric criterion-facet weights are logged; "
            "exact is restricted to matching single-facet receipts with unique normalized allocation. "
            "Multifacet revisions fail closed unless current_content reconstruction is explicitly enabled.",
            "No logged propensity_kind proves a system-probe action probability; "
            "legacy-unverified and unavailable_composed_offer numbers are unusable.",
            "Requested origin is unavailable: current immutable receipts have no machine-readable request marker.",
            "Current fitted item parameters and FSRS heads are not used: they would leak future outcomes.",
            "PF-c unverified criteria are unassessed until reviewed (no failure outcome, no credit); "
            "the memory arm's FSRS rating still reads the persisted grade, as the live scheduler does.",
        ],
    }
