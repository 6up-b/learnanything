"""PF-c unassessed criteria, read the same way outside the grade (Codex review).

The stage made a PF-c unverified criterion unassessed in the grade, the
canonical projection, the evidence timeline and the attempt step. The review
found readers that still turned it into evidence:

* F1: the attempt step and the learner field fell back to "every facet gets
  the attempt's outcome" when an item has no criterion -> facet map, so the
  unverified criterion's facet still got credit there;
* F2: an attempt with NOTHING assessed (correct only for scheduling) could
  confirm a repair through the cold-retry hook;
* F3: a pinned probe's deterministic sensor read the unverified criterion's
  raw points as a measured feature;
* F4: the diagnoser's history listed it as a failed criterion and accepted a
  recurrence citation on it;
* F5: records written before the rule carried no mark of the interpretation
  they were written under;
* F6: retention eligibility still read the informational review flag as an
  unresolved grade.

Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
    assessed_rubric_score,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.grading_support import UNVERIFIED_REVIEW_REASON
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.field.outcomes import load_facet_rows
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import (
    UNVERIFIED_CRITERION_BLOCK,
    project_canonical_facet_state,
    unassessed_evidence_row,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at
from tests.split_live_helpers import ReadyRuntime, split_vault, submit
from tests.test_field_split_outcomes import _ZeroEverythingWithoutAttribution
from tests.test_pfc_unverified_unassessed import (
    CLOCK,
    ITEM,
    VERIFYING_ANSWER,
    _PartialWithoutAttribution,
    _mass,
    _mapped_split_vault,
)


def _field_outcomes(vault, repository, attempt_id: str) -> dict[str, float]:
    with repository.connection() as connection:
        return {
            row.facet_id: row.outcome
            for row in load_facet_rows(connection, vault, legacy_fallback="current_content")
            if row.attempt_id == attempt_id
        }


def _apply_graded(
    vault,
    repository,
    item_id: str,
    *,
    points: dict[str, float],
    unverified: tuple[str, ...] = (),
    clock,
    attempt_type: str = "independent_attempt",
    presentation_id: str | None = None,
    primed: bool = False,
):
    """One graded attempt through the shared step, as the live door hands it:
    the grade over the assessed criteria, the unverified ones stamped."""

    item = vault.practice_items[item_id]
    rubric = resolved_rubric(vault, item)
    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U Sigma V^T",
                attempt_type=attempt_type,
                probe_presentation_id=presentation_id,
                primed=primed,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=assessed_rubric_score(rubric, points, [], unassessed_criterion_ids=unverified),
                criterion_points=dict(points),
                evidence_rows=[
                    {
                        "id": new_ulid(),
                        "criterion_id": criterion_id,
                        "points_awarded": float(awarded),
                        "evidence": "graded",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 3,
                        "created_at": now_iso,
                    }
                    for criterion_id, awarded in points.items()
                ],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=UNVERIFIED_REVIEW_REASON if unverified else None,
                feedback_md="",
                repair_suggestions=[],
            ),
            unverified_criterion_ids=tuple(unverified),
        ),
        clock=clock,
    )


# -- F1: the criterion -> facet map comes from the rubric's targets --------------------


def test_an_ordinary_item_gives_the_unverified_criterion_s_facet_nothing(tmp_path):
    """No ``criterion_facet_weights`` and no lexical match: before the fix the
    attempt step and the field gave ``recall`` the attempt's outcome (1.0)
    while the projection, reading the criteria's targets, skipped it."""

    from learnloop.learner.recall_coverage import criterion_facet_weights_for_item

    _paths, vault, repository = split_vault(tmp_path)
    item = vault.practice_items[ITEM]
    rubric = resolved_rubric(vault, item)
    assert not item.criterion_facet_weights
    assert criterion_facet_weights_for_item(item, rubric) == {}
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")

    result = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)

    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["unassessed_criteria"] == ["result"]
    assert set(debug["covered_facets"]) == {"compute"}
    assert debug["facet_outcomes"] == {"compute": 1.0}
    assert _field_outcomes(vault, repository, result.attempt_id) == {"compute": 1.0}
    assert _mass(repository, "recall") == pytest.approx(recall_before)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    replayed = repository.attempt_debug_payload(result.attempt_id)
    assert replayed["facet_outcomes"] == {"compute": 1.0}
    assert set(replayed["covered_facets"]) == {"compute"}
    assert _mass(repository, "recall") == pytest.approx(recall_before)


def test_a_criterion_without_targets_shares_its_facets_with_the_assessed_one(tmp_path):
    """Legacy criteria (no targets, no map) each measure every item facet, as
    the projection compiles them: the assessed criterion alone carries both
    facets' outcome, and their mass is its share of the rubric."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from learnloop.vault.loader import load_vault

    paths, _vault, repository = split_vault(tmp_path)
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    raw = read_yaml(item_path)
    for criterion in raw["grading_rubric"]["criteria"]:
        criterion.pop("targets", None)
    write_yaml(item_path, raw)
    vault = load_vault(paths.root)

    result = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)

    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["facet_outcomes"] == {"recall": 1.0, "compute": 1.0}
    scaling = debug["coverage_trace"]["graded_criterion_scaling"]
    assert scaling["ungraded_criteria"] == ["result"]
    assert scaling["facet_scales"] == pytest.approx({"recall": 0.5, "compute": 0.5})
    assert _field_outcomes(vault, repository, result.attempt_id) == {"recall": 1.0, "compute": 1.0}


# -- F2: an attempt with nothing assessed never verifies a repair ------------------------


@pytest.mark.parametrize("assessed", [True, False], ids=["assessed", "nothing_assessed"])
def test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair(tmp_path, assessed):
    from learnloop.attempts.attempts import SelfGradeInput, complete_self_graded_attempt
    from learnloop.diagnosis.causal_orchestrator import causal_repair_status
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
    from learnloop.diagnosis.remediation import prescribe_remediation, start_remediation_treatment
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW, create_basic_vault, set_algorithm_version
    from tests.test_causal_orchestrator import CLOCK as START, _add_probe_item, _seed_factor

    # PF-c rows exist only in the split successor (a canonical-state vault).
    paths = create_basic_vault(tmp_path / "vault")
    _add_probe_item(paths.root)
    set_algorithm_version(paths, "mvp-0.10")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )
    status = causal_repair_status(vault, repository, misconception_id=first_id, clock=START)
    assert status.status == "safe_common_repair_available"
    episode_id = status.episode["id"]
    prescribe_remediation(vault, repository, episode_id, clock=START)
    treatment = start_remediation_treatment(vault, repository, episode_id, clock=START)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=treatment["primed_item_id"], learner_answer_md="U Sigma Q", primed=True),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=START,
    )
    later = FrozenClock(NOW + timedelta(days=2))
    cold_item = vault.practice_items[treatment["cold_item_id"]]
    criteria = [criterion.id for criterion in resolved_rubric(vault, cold_item).criteria]
    if assessed:
        cold = _apply_graded(
            vault, repository, cold_item.id,
            points={cid: float(c.points) for cid, c in zip(criteria, resolved_rubric(vault, cold_item).criteria)},
            clock=later,
        )
    else:
        # The verified answer took a route no criterion measured.
        cold = _apply_graded(
            vault, repository, cold_item.id,
            points={cid: 0.0 for cid in criteria}, unverified=tuple(criteria), clock=later,
        )
    attempt = repository.fetch_practice_attempt(cold.attempt_id)
    assert attempt["correctness"] == 1.0  # correct for scheduling either way
    rows = repository.fetch_grading_evidence(cold.attempt_id)
    assert all(unassessed_evidence_row(row.attribution_json) for row in rows) is (not assessed)
    task = repository.consumed_followup_task_for_attempt(cold.attempt_id, kind="cold_retry")
    assert task is not None

    evaluate_attempt_intervention_followup(vault, repository, result=cold, clock=later)

    factor = repository.unresolved_cause_factor(factor_id)
    disposition = repository.causal_cold_outcome_for_task(str(task["id"]))
    verification = repository.causal_cold_verification_for_attempt(cold.attempt_id)
    if assessed:
        assert verification is not None and verification["success"] is True
        assert disposition["outcome"] == "cold_success"
        assert factor["status"] == "resolved" and factor["resolution_kind"] == "repair_confirmed"
        return
    # No success and no failure: no verification, a typed non-measurement, and
    # the factor and its candidate beliefs exactly as they were.
    assert verification is None
    assert disposition["outcome"] == "missing_chain"
    assert disposition["cold_verification_id"] is None
    assert disposition["detail"]["reason"] == "cold_attempt_unassessed"
    assert factor["status"] == "open" and factor.get("resolution_kind") is None
    for hypothesis_id in (first_id, second_id):
        hypothesis = repository.causal_hypothesis(hypothesis_id)
        head = repository.latest_causal_hypothesis_for_episode(hypothesis["episode_key"])
        assert head["status"] == "candidate"


def test_the_cold_verification_guard_refuses_an_unassessed_attempt_directly(tmp_path):
    """The guard sits in ``record_delayed_cold_verification`` itself, so no
    caller can turn a nothing-assessed attempt into repair evidence."""

    from learnloop.diagnosis.causal_probe_coherence import (
        ColdVerificationPrecondition,
        record_delayed_cold_verification,
    )
    from tests.test_causal_factor_deferral import (
        ITEM_A,
        ITEM_B,
        _clock,
        _factor_repair_class,
        _failed_diagnostic,
        _open_factor,
        _vault as deferral_vault,
    )

    vault, repository = deferral_vault(tmp_path)
    _failed_diagnostic(vault, repository, attempt_id="att_src", item_id=ITEM_A, clock=_clock())
    factor = _open_factor(repository, "att_src")
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)
    cold = _apply_graded(
        vault, repository, ITEM_B, points={"correctness": 0.0}, unverified=("correctness",), clock=_clock(days=2),
    )
    with pytest.raises(ColdVerificationPrecondition) as raised:
        record_delayed_cold_verification(
            vault,
            repository,
            source_attempt_id="att_src",
            cold_attempt_id=cold.attempt_id,
            repair_class_id=repair_class_id,
            hypothesis_ids=hypothesis_ids,
            avoided_affordances=["primed_repair_context"],
            clock=_clock(days=2),
        )
    assert raised.value.reason == "missing_chain"
    assert raised.value.detail["reason"] == "cold_attempt_unassessed"
    assert repository.causal_cold_verification_for_attempt(cold.attempt_id) is None
    assert repository.unresolved_cause_factor(str(factor["id"]))["status"] == "open"


# -- F3: a pinned probe never reads an unassessed criterion as a feature ----------------


@pytest.mark.parametrize(
    ("points", "unverified"),
    [(0.0, False), (0.0, True), (2.0, True)],
    ids=["assessed_zero", "unverified_zero", "unverified_partial"],
)
def test_a_pinned_probe_declines_to_classify_an_unassessed_criterion(tmp_path, points, unverified):
    from learnloop.diagnosis.causal_orchestrator import (
        auto_classify_pinned_probe,
        deterministic_probe_features,
    )
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
    from tests.test_causal_p2_acceptance import CLOCK as P2_CLOCK
    from tests.test_causal_p2_acceptance import PROBE_ITEM, _acceptance_vault, _offered_probe

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _result, factor_id, first_id, _second_id, offer = _offered_probe(
        vault,
        repository,
        features=(
            {"criterion:correctness:passed": False},
            {"criterion:correctness:passed": True},
        ),
    )
    probe = _apply_graded(
        vault, repository, PROBE_ITEM, points={"correctness": points},
        unverified=("correctness",) if unverified else (),
        attempt_type="diagnostic_probe", presentation_id=offer.presentation_id, clock=P2_CLOCK,
    )
    features = deterministic_probe_features(vault, repository, probe.attempt_id)

    evaluate_attempt_intervention_followup(vault, repository, result=probe, clock=P2_CLOCK)

    observations = repository.causal_discriminating_observations(factor_id=factor_id)
    if not unverified:
        # The control: an assessed zero is a measured feature and classifies.
        assert features["criterion:correctness:passed"] is False
        assert [row["classified_as"] for row in observations] == [[first_id]]
        assert repository.unresolved_cause_factor(factor_id)["status"] == "resolved"
        return
    # The unassessed criterion supplies no feature, so the declared-feature
    # completeness check declines: nothing is recorded, the factor stays open.
    assert observations == []
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"
    assert not any(key.startswith("criterion:correctness:") for key in features)
    assert auto_classify_pinned_probe(vault, repository, attempt_id=probe.attempt_id, clock=P2_CLOCK) is None


# -- F4: the diagnoser's history never reads an unassessed criterion as a failure ---------


def test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence(tmp_path):
    from learnloop.diagnosis.split.context import assemble_diagnosis_context, current_attempt_from
    from learnloop.diagnosis.split.contract import DiagnosisProposal
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.live import live_history_store
    from learnloop.diagnosis.split.settings import DiagnosisSettings
    from learnloop.diagnosis.split.validation import validate_diagnosis_proposal

    _paths, vault, repository = split_vault(tmp_path)
    earlier = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER, when=at(100))
    record = repository.latest_blind_grade_record(earlier.attempt_id)["record"]
    assert record["grading_support"]["unverified_criterion_ids"] == ["result"]
    assert record["error_attributions"] == []
    later = submit(
        vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002",
        answer="B = U Sigma V nope", when=at(101),
    )

    store = live_history_store(vault, repository)
    prior = store.attempt(earlier.attempt_id)
    # Unassessed is neither a failure nor a pass, read from the blind record...
    assert "result" not in prior.failed_criteria and "result" not in prior.passed_criteria
    assert prior.failed_criteria == () and not prior.non_pass
    assert prior.recurrence_invalid_reason({"recall"}) == "cited_attempt_passed"
    # ...and from the stored rows when no blind overlay is at hand.
    stored = VaultHistoryStore(vault, repository).attempt(earlier.attempt_id)
    assert "result" not in stored.failed_criteria and "result" not in stored.passed_criteria
    assert stored.recurrence_invalid_reason({"recall"}) is not None

    # The later diagnosis cites the earlier answer as the same mistake on recall.
    item = vault.practice_items["pi_svd_compute_002"]
    current_attempt = store.attempt(later.attempt_id)
    current = current_attempt_from(
        vault, item, attempt_id=later.attempt_id, completed_at=current_attempt.completed_at,
        learner_answer_md="B = U Sigma V nope",
        blind_grade=repository.latest_blind_grade_record(later.attempt_id)["record"],
    )
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full")
    proposal = DiagnosisProposal.model_validate({
        "analysis_md": "The final factor is not transposed, as before.",
        "evidence_attempt_ids": [earlier.attempt_id],
        "event_diagnoses": [{
            "event_index": 0,
            "causal_class": "learner_state",
            "candidate_causes": [{
                "statement": "Believes V needs no transpose.",
                "cause_scope": "learner_state",
                "prior_weight": 2,
                "target_ref": {"kind": "facet_capability", "facet_id": "recall"},
            }],
            "registry_match": {"kind": "abstain"},
            "history_changed_cause": {"changed": False, "note": ""},
        }],
        "pattern_claims": [{
            "hypothesis_ref": "cause:0:0", "relation": "same_mechanism",
            "cited": [{"attempt_id": earlier.attempt_id, "quote": "A different route."}],
        }],
    })
    result = validate_diagnosis_proposal(
        proposal, assembled=assembled, current=current, vault=vault, item=item,
        rubric=resolved_rubric(vault, item), store=store,
    )
    reasons = {
        issue["attempt_id"]: issue["reason"]
        for issue in result.report["issues"]
        if issue["rule"] == "citation_not_valid_for_recurrence"
    }
    assert reasons == {earlier.attempt_id: "cited_attempt_passed"}
    assert result.validated_citations == ()


# -- F5: each record names the interpretation it was written under ------------------------


_BASE_BLOCK = json.dumps(
    {"targets": [], "negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK},
    sort_keys=True, separators=(",", ":"),
)


def _as_the_base_implementation_wrote_it(patch) -> None:
    """The live door exactly as ``mvp-0.10`` shipped before the rule (22023ab4).

    The three write-time differences, and nothing else: the unverified row's
    block carried no interpretation mark; the grade was the grader's own
    derived score (kept points included); the gate recorded no
    ``assessed_shortfall``. The shared step got no unassessed set (the base
    door handed the unverified ids to ``apply_attempt`` only for stamping),
    which the wrapper reproduces by stamping the base block itself.
    """

    from dataclasses import replace

    from learnloop.attempts import attempts as attempts_module
    from learnloop.attempts import grading_support as support_module

    original_apply = attempts_module.apply_attempt

    def base_apply(vault, repository, attempt, *, clock=None, **kwargs):
        unverified = set(attempt.unverified_criterion_ids)
        if unverified:
            rows = [
                {**row, "attribution_json": _BASE_BLOCK}
                if row.get("criterion_id") in unverified and row.get("attribution_json") is None
                else row
                for row in attempt.grade.evidence_rows
            ]
            attempt = replace(
                attempt, grade=replace(attempt.grade, evidence_rows=rows), unverified_criterion_ids=()
            )
        return original_apply(vault, repository, attempt, clock=clock, **kwargs)

    def base_score(rubric, points, fatal_errors, *, unassessed_criterion_ids):
        return attempts_module.calculate_rubric_score(rubric, dict(points), list(fatal_errors))

    original_run = support_module.request_blind_grading_run

    def base_run(*args, **kwargs):
        run = original_run(*args, **kwargs)
        for key in ("assessed_shortfall", "unverified_interpretation"):
            run.grading_support.pop(key, None)
        return run

    patch.setattr(attempts_module, "apply_attempt", base_apply)
    patch.setattr(attempts_module, "assessed_rubric_score", base_score)
    patch.setattr(support_module, "request_blind_grading_run", base_run)


def test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded(tmp_path, monkeypatch):
    """F5: replay never reinterprets a base-implementation PF-c record (its
    persisted 3/4 and its M2 evidence stay paired); a new record carries the
    unassessed mark; a regrade is the upgrade path."""

    _paths, vault, repository = _mapped_split_vault(tmp_path)
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")
    with monkeypatch.context() as patch:
        _as_the_base_implementation_wrote_it(patch)
        base = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)
    support = repository.latest_blind_grade_record(base.attempt_id)["record"]["grading_support"]
    assert "assessed_shortfall" not in support and "unverified_interpretation" not in support
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(base.attempt_id)}
    assert json.loads(rows["result"].attribution_json) == json.loads(_BASE_BLOCK)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    attempt = repository.fetch_practice_attempt(base.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (3, 0.75)
    debug = repository.attempt_debug_payload(base.attempt_id)
    assert "unassessed_criteria" not in debug
    assert debug["facet_outcomes"]["recall"] == pytest.approx(0.5)
    # The M2 projection: the kept point is credited, the shortfall is no failure.
    positive, negative = _mass(repository, "recall")
    assert positive > recall_before[0]
    assert negative == pytest.approx(recall_before[1])
    m2_recall = (positive, negative)
    # Identified: an unverified row, but not one written under the unassessed rule.
    from learnloop.substrate.canonical_projection import unverified_evidence_row

    assert unverified_evidence_row(rows["result"].attribution_json)
    assert not unassessed_evidence_row(rows["result"].attribution_json)

    # An identical answer graded now is written under the rule, and marked so.
    new = submit(
        vault, repository, _PartialWithoutAttribution(), item_id="pi_svd_compute_002",
        answer="Another route.\nFinal answer: U Sigma V^T",
    )
    new_rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(new.attempt_id)}
    assert unassessed_evidence_row(new_rows["result"].attribution_json)
    new_support = repository.latest_blind_grade_record(new.attempt_id)["record"]["grading_support"]
    assert new_support["unverified_interpretation"] == "unassessed"
    assert (repository.fetch_practice_attempt(new.attempt_id)["rubric_score"]) == 4
    assert _mass(repository, "recall") == pytest.approx(m2_recall)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.fetch_practice_attempt(base.attempt_id)["rubric_score"] == 3
    assert _mass(repository, "recall") == pytest.approx(m2_recall)

    # The upgrade path: a regrade writes the record again under the rule.
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(base.attempt_id),
        runtime=ReadyRuntime(), client=_PartialWithoutAttribution(), grading_source="ai", clock=None,
    )
    upgraded = repository.fetch_practice_attempt(base.attempt_id)
    assert (upgraded["rubric_score"], upgraded["correctness"]) == (4, 1.0)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(base.attempt_id)}
    assert unassessed_evidence_row(rows["result"].attribution_json)
    assert repository.attempt_debug_payload(base.attempt_id)["unassessed_criteria"] == ["result"]
    assert _mass(repository, "recall") == pytest.approx(recall_before)
