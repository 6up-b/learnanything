"""Placement (mvp-0.11) reads grades as the Slice 1 split records them.

mvp-0.11 is mvp-0.10's split plus placement, so every answer placement reads in
a split vault is blind-graded. The merge pins three readings:

- a blind grade lands on the attempt row like a joint one, and a clean
  full-marks blind answer passes an assumed LO's first review;
- a regrade (which supersedes the evidence and re-queues the diagnosis) is
  read live: the check follows the regraded grade;
- PF-c's unverified criteria are no failure evidence: an answer whose only
  shortfall is an unverified criterion keeps the topic in maintenance at the
  check (reason ``unassessed``, owner decision 2026-10-12), is not a lapse in
  maintenance, and neither counts toward nor blocks fast-track. A located
  error on the same item is decided by its diagnosis (a knowledge gap returns
  the LO to learning; while the diagnosis is pending the decision waits).

Fakes only; no network.
"""

from __future__ import annotations

from learnloop.attempts.blind_grading import BlindErrorAttribution
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.field.types import RegionEstimate
from learnloop.placement.decisions import record_self_report
from learnloop.placement.rules import (
    CHECK_FAIL,
    CHECK_INELIGIBLE,
    CHECK_PASS,
    PFC_UNVERIFIED_BLOCK,
    AnswerFacts,
    check_verdict,
    fast_track_verdict,
)
from learnloop.placement.state import load_placement_state, pfc_unverified_attempt_ids
from learnloop.substrate.canonical_projection import UNVERIFIED_CRITERION_BLOCK

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at
from tests.split_live_helpers import ReadyRuntime, drain_jobs, split_vault, submit
from tests.test_grading_support import _ZeroWithoutAttribution

LO = "lo_svd_compute"
CORRECT = "B = U Sigma V^T"
# A different route to the reference's final answer: PF-c's final-answer check
# verifies it, so an unlocated mark-down is recorded unverified.
VERIFYING = "A different route.\nFinal answer: U Sigma V^T"
DUE_HOURS = 14 * 24
#: When the tests read placement state: within the diagnosis wait of every miss.
READ_AT = utc_now_iso(FrozenClock(at(DUE_HOURS + 100)))


class _LocatedResultError(ReviewFakeClient):
    """Zeroes ``result`` at an error quoted verbatim from the answer (located)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 0.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        quote = str(context["learner_answer_md"]).splitlines()[-1]
        attribution = {
            "error_type": "conceptual_slip",
            "evidence": "The final factor is wrong.",
            "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": quote},
            "target_evidence_families": ["recall"],
            "resolution_status": "unresolved",
            "validity_scope": "valid_measurement",
        }
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [BlindErrorAttribution.model_validate(attribution)],
            }
        )


def _assumed(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.11", seed=False)
    result = record_self_report(
        vault, repository, learning_object_ids=[LO], report="know_this", clock=FrozenClock(at(0)),
    )
    assert result["results"][0]["status"] == "assumed"
    return paths, vault, repository


def _state(vault, repository):
    state = load_placement_state(vault, repository, now_iso=READ_AT)
    (assumption,) = [a for a in state.assumptions if a.learning_object_id == LO]
    return assumption, state.intent_by_lo[LO].intent


def test_the_pinned_block_reason_is_pfcs():
    assert PFC_UNVERIFIED_BLOCK == UNVERIFIED_CRITERION_BLOCK


def test_a_clean_blind_grade_passes_the_check(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    attempt = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001",
                     answer=CORRECT, when=at(DUE_HOURS + 1))
    assert repository.latest_blind_grade_record(attempt.attempt_id) is not None
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, intent) == (
        "passed", attempt.attempt_id, "maintenance",
    )


def test_an_unverified_pfc_grade_on_the_check_keeps_the_topic_in_maintenance(tmp_path):
    """Owner decision 2026-10-12: an unassessed (PF-c) criterion is no failure
    evidence, so it keeps the topic: assumed before the check, in maintenance
    at the check, with the reason on the receipt."""

    _paths, vault, repository = _assumed(tmp_path)
    early = submit(vault, repository, _ZeroWithoutAttribution(), item_id="pi_svd_compute_002",
                   answer=VERIFYING, when=at(2))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.kept_answers, intent) == (
        "open", ((early.attempt_id, "unassessed"),), "assumed",
    )

    unverified = submit(vault, repository, _ZeroWithoutAttribution(), item_id="pi_svd_compute_001",
                        answer=VERIFYING, when=at(DUE_HOURS + 1))
    row = repository.fetch_practice_attempt(unverified.attempt_id)
    assert row["manual_review"] and float(row["correctness"]) < 1.0
    with repository.connection() as connection:
        assert unverified.attempt_id in pfc_unverified_attempt_ids(connection)

    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason, intent) == (
        "passed", unverified.attempt_id, "unassessed", "maintenance",
    )
    entry = load_placement_state(vault, repository, now_iso=READ_AT).intent_by_lo[LO]
    assert (entry.reason, entry.outcome_reason) == ("check_passed", "unassessed")


def test_a_located_error_is_decided_by_its_diagnosis(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    located = submit(vault, repository, _LocatedResultError(), item_id="pi_svd_compute_001",
                     answer=VERIFYING, when=at(DUE_HOURS + 1))
    with repository.connection() as connection:
        assert located.attempt_id not in pfc_unverified_attempt_ids(connection)
    # The diagnosis is queued: the decision waits and the LO stays assumed.
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id, intent) == (
        "open", located.attempt_id, "assumed",
    )
    # The fake diagnoser reads a durable learner state: a knowledge gap.
    drain_jobs(vault, repository, ReviewFakeClient(), clock=FrozenClock(at(DUE_HOURS + 1)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent) == ("failed", "knowledge_gap", "learning")
def test_an_unverified_answer_in_maintenance_is_not_a_lapse(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001",
           answer=CORRECT, when=at(DUE_HOURS + 1))
    kept = submit(vault, repository, _ZeroWithoutAttribution(), item_id="pi_svd_compute_002",
                  answer=VERIFYING, when=at(DUE_HOURS + 30))
    assert _state(vault, repository)[1] == "maintenance"
    entry = load_placement_state(vault, repository, now_iso=READ_AT).intent_by_lo[LO]
    assert entry.kept_misses == ((kept.attempt_id, "unassessed"),)


def test_the_check_follows_a_regrade_that_requeues_the_diagnosis(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    attempt = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001",
                     answer=VERIFYING, when=at(DUE_HOURS + 1))
    assert _state(vault, repository)[0].status == "passed"

    row = repository.fetch_practice_attempt(attempt.attempt_id)
    regrade_attempt(vault, repository, row, runtime=ReadyRuntime(), client=_LocatedResultError(),
                    grading_source="ai", clock=FrozenClock(at(DUE_HOURS + 2)))
    assert repository.latest_blind_grade_record(attempt.attempt_id)["supersedes_id"] is not None
    assert repository.post_attempt_jobs(attempt_id=attempt.attempt_id, kind="diagnose", states=("queued",))
    # The regrade re-queued the diagnosis: the check waits on it.
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id, intent) == (
        "open", attempt.attempt_id, "assumed",
    )
    drain_jobs(vault, repository, ReviewFakeClient(), clock=FrozenClock(at(DUE_HOURS + 2)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent) == ("failed", "knowledge_gap", "learning")


def test_a_regrade_to_unverified_keeps_the_topic_in_maintenance(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    attempt = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001",
                     answer=VERIFYING, when=at(DUE_HOURS + 1))
    row = repository.fetch_practice_attempt(attempt.attempt_id)
    regrade_attempt(vault, repository, row, runtime=ReadyRuntime(), client=_ZeroWithoutAttribution(),
                    grading_source="ai", clock=FrozenClock(at(DUE_HOURS + 2)))
    with repository.connection() as connection:
        assert attempt.attempt_id in pfc_unverified_attempt_ids(connection)
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent) == ("passed", "unassessed", "maintenance")


def _facts(attempt_id, *, correctness=1.0, unverified=False, hints=0, manual_review=False):
    return AnswerFacts(
        attempt_id=attempt_id, learning_object_id=LO, practice_item_id=f"pi_{attempt_id}",
        created_at=f"2026-05-01T09:0{attempt_id[-1]}:00Z", attempt_type="independent_attempt",
        correctness=correctness, hints_used=hints, primed=False, dont_know=False,
        manual_review=manual_review or unverified, assisted_class=False,
        independent=True, grade_unverified=unverified,
    )


def test_rules_read_an_unverified_grade_as_unassessed():
    unverified = _facts("a1", correctness=0.5, unverified=True)
    assert unverified.unassessed and not unverified.learner_clean and not unverified.is_miss
    assert check_verdict(unverified) == CHECK_INELIGIBLE
    # Learner-side help is a miss whatever the grade says.
    hinted = _facts("a2", correctness=0.5, unverified=True, hints=1)
    assert not hinted.unassessed and hinted.is_miss and check_verdict(hinted) == CHECK_FAIL
    assert check_verdict(_facts("a3")) == CHECK_PASS

    region = RegionEstimate(4.0, 0.1, 6.0, False)
    kwargs = dict(blocking_signal_ids=(), region=region, min_correct=2, q=0.8, known_threshold=1.0986)
    # Skipped: it neither counts toward the minimum nor blocks.
    assert fast_track_verdict([_facts("a4"), unverified], **kwargs).reason == "too_few_answers"
    fires = fast_track_verdict([_facts("a4"), unverified, _facts("a5")], **kwargs)
    assert fires.fires and fires.clean_answers == 2
    assert fast_track_verdict([_facts("a4"), _facts("a6", correctness=0.5), _facts("a5")], **kwargs).reason == (
        "non_clean_answer"
    )
    # A replayed receipt (G8) reads the flag back; old receipts default to verified.
    assert AnswerFacts.from_dict(unverified.as_dict()) == unverified
    legacy = {key: value for key, value in _facts("a7").as_dict().items() if key != "grade_unverified"}
    assert AnswerFacts.from_dict(legacy).grade_unverified is False
