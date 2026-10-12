"""Owner decision 2026-10-12 (Slice A Phase 6 open question 3): the 14-day
first-review check, and lapses in maintenance, are decided by the diagnosis,
not by full marks.

- A miss returns the topic to learning only when the diagnosis attributes it to
  a knowledge gap (Slice 1 M2: ``causal_class = learner_state`` on a
  ``valid_measurement`` attribution).
- A slip, an item-contract (or grader-interpretation) problem, the
  interaction rather than knowledge, or an unassessed PF-c criterion keeps the
  topic (assumed before the check, in maintenance at and after it), with the
  reason on the receipt. A diagnosis that attributes no cause does not (Codex
  review F5).
- While the asynchronous diagnosis is pending the decision waits, at most
  DIAGNOSIS_WAIT_DAYS (F3); if no diagnosis can arrive (split off, the
  diagnoser failed, budget-skipped, a joint grade) today's rule applies and
  the receipt says so. A miss is decided once (F4); learner-side help does not
  wait on an earlier miss (F8).
- Report 3 counts outcomes by reason, and keeps the raw full-marks miss rate.

Real grading door and job drain with the M1/M2 fakes; no network.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.placement.decisions import record_self_report
from learnloop.placement.report import placement_report
from learnloop.placement.rules import (
    MISS_KEPT,
    MISS_TO_LEARNING,
    AnswerFacts,
    MissVerdict,
    decide_miss,
    diagnosis_reason,
)
from learnloop.placement.state import load_placement_state
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at
from tests.split_live_helpers import append_config, drain_jobs, split_vault, submit

LO = "lo_svd_compute"
WRONG = "A = U Sigma V wrong"
CORRECT = "B = U Sigma V^T"
DUE_HOURS = 14 * 24


def _iso(hours: float) -> str:
    return utc_now_iso(FrozenClock(at(hours)))


#: When the tests read placement state: after every answer they record, and
#: within placement.rules.DIAGNOSIS_WAIT_DAYS of every diagnosis they queue.
READ_AT = _iso(DUE_HOURS + 100)


class _Diagnosed(ReviewFakeClient):
    """The fake grader and diagnoser with a chosen validity and causal class.

    ``validity_scope`` lands on every blind-grade error attribution;
    ``causal_class`` on every event the diagnoser writes (the M2 validator
    still forces ``unknown`` off a valid measurement)."""

    def __init__(self, *, validity_scope="valid_measurement", causal_class="learner_state", **kwargs):
        super().__init__(**kwargs)
        self.validity_scope = validity_scope
        self.causal_class = causal_class

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        return result.model_copy(update={
            "error_attributions": [
                row.model_copy(update={"validity_scope": self.validity_scope}) for row in result.error_attributions
            ],
        })

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        return result.model_copy(update={
            "event_diagnoses": [
                event.model_copy(update={"causal_class": self.causal_class}) for event in result.event_diagnoses
            ],
        })


def _assumed(tmp_path, *, config="", los=(LO,)):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.11", seed=False, config=config)
    result = record_self_report(
        vault, repository, learning_object_ids=list(los), report="know_this", clock=FrozenClock(at(0)),
    )
    assert {row["status"] for row in result["results"]} == {"assumed"}
    return paths, vault, repository


def _state(vault, repository, lo=LO, *, now_iso=READ_AT):
    state = load_placement_state(vault, repository, now_iso=now_iso)
    (assumption,) = [a for a in state.assumptions if a.learning_object_id == lo]
    return assumption, state.intent_by_lo[lo]


def _routine(queue) -> set[str]:
    """Items served by routine scheduling (not an explicit follow-up lane)."""

    return {s.practice_item_id for s in queue if s.followup_kind is None}


def _miss(vault, repository, client, *, item="pi_svd_compute_001", hours=DUE_HOURS + 1, drain=True):
    result = submit(vault, repository, client, item_id=item, answer=WRONG, when=at(hours))
    if drain:
        drain_jobs(vault, repository, client, clock=FrozenClock(at(hours)))
    return result


# ── The check ─────────────────────────────────────────────────────────────────


def test_a_knowledge_gap_on_the_check_returns_the_lo_to_learning(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(causal_class="learner_state"))

    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "failed", miss.attempt_id, "knowledge_gap",
    )
    receipt = assumption.resolution
    assert receipt.outcome == MISS_TO_LEARNING and receipt.fallback is None
    assert receipt.diagnosis_id == repository.current_live_diagnosis(miss.attempt_id)["id"]
    assert receipt.events == ((0, "valid_measurement", "learner_state"),)
    assert (intent.intent, intent.reason, intent.outcome_reason) == ("learning", "check_missed", "knowledge_gap")


@pytest.mark.parametrize(
    ("validity", "causal", "reason"),
    [
        ("valid_measurement", "transient_execution", "slip"),
        ("item_contract", "learner_state", "item_contract"),
        ("grader_interpretation", "learner_state", "item_contract"),
        ("interaction_context", "learner_state", "interaction_context"),
    ],
    ids=["slip", "item-contract", "grader-interpretation", "interaction-context"],
)
def test_a_miss_the_diagnosis_does_not_call_a_gap_keeps_the_topic_in_maintenance(
    tmp_path, validity, causal, reason
):
    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(validity_scope=validity, causal_class=causal))

    assumption, intent = _state(vault, repository)
    assert (assumption.status, intent.intent) == ("passed", "maintenance")  # not back to learning
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "passed", miss.attempt_id, reason,
    )
    assert assumption.resolution.outcome == MISS_KEPT and assumption.resolution.diagnosis_id
    # The M2 validator keeps a causal class off anything but a valid measurement.
    (event,) = assumption.resolution.events
    assert event[1] == validity and (validity == "valid_measurement" or event[2] == "unknown")
    assert (intent.intent, intent.reason, intent.outcome_reason) == ("maintenance", "check_passed", reason)
    # In maintenance: the LO's remaining learning items stay withheld from
    # routine serving (the miss's own follow-up lane is the explicit exception).
    queue = build_due_queue(vault, repository, clock=FrozenClock(at(DUE_HOURS + 2)), persist_explanations=False)
    assert "pi_svd_compute_002" not in _routine(queue)


def test_a_kept_miss_before_the_check_leaves_the_topic_assumed_and_a_gap_returns_it_early(tmp_path):
    _paths, vault, repository = _assumed(tmp_path, los=(LO, "lo_transpose"))
    slip = _miss(vault, repository, _Diagnosed(causal_class="transient_execution"), hours=2)
    assumption, intent = _state(vault, repository)
    assert (assumption.status, intent.intent) == ("open", "assumed")
    assert (assumption.status, assumption.kept_answers, intent.intent) == (
        "open", ((slip.attempt_id, "slip"),), "assumed",
    )
    gap = _miss(vault, repository, _Diagnosed(causal_class="learner_state"), item="pi_transpose_001", hours=3)
    assumption, intent = _state(vault, repository, "lo_transpose")
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason, intent.intent) == (
        "failed", gap.attempt_id, "knowledge_gap", "learning",
    )


# ── Pending: the decision waits ──────────────────────────────────────────────


def test_the_decision_waits_while_the_diagnosis_is_pending(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    before = build_due_queue(vault, repository, clock=FrozenClock(at(DUE_HOURS + 0.5)), persist_explanations=False)
    assert [s.learning_object_id for s in before if s.components.get("assumed_check")] == [LO]

    client = _Diagnosed(causal_class="transient_execution")
    miss = _miss(vault, repository, client, drain=False)
    state = load_placement_state(vault, repository, now_iso=READ_AT)
    (assumption,) = state.assumptions
    assert (assumption.status, state.intent_by_lo[LO].intent) == ("open", "assumed")
    # The topic stays in its current state: assumed, its check taken.
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id) == ("open", miss.attempt_id)
    assert state.intent_by_lo[LO].intent == "assumed"
    assert state.awaiting_diagnosis_learning_object_ids == {LO}
    assert LO in state.open_by_lo and LO in state.due_learning_object_ids("2027-01-01T00:00:00Z")
    queue = build_due_queue(vault, repository, clock=FrozenClock(at(DUE_HOURS + 1.5)), persist_explanations=False)
    # No second check meanwhile (the miss's own follow-up lane aside).
    assert not [s for s in queue if s.learning_object_id == LO and s.followup_kind is None]

    drain_jobs(vault, repository, client, clock=FrozenClock(at(DUE_HOURS + 2)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent.intent) == ("passed", "slip", "maintenance")


def test_i_dont_know_this_does_not_wait_on_a_pending_diagnosis(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    _miss(vault, repository, _Diagnosed(), drain=False)
    record_self_report(
        vault, repository, learning_object_ids=[LO], report="dont_know_this", clock=FrozenClock(at(DUE_HOURS + 2)),
    )
    state = load_placement_state(vault, repository, now_iso=READ_AT)
    (assumption,) = state.assumptions
    assert (assumption.status, assumption.resolution_reason) == ("returned", "i_dont_know_this")
    assert LO not in state.open_by_lo and state.intent_by_lo[LO].intent == "learning"
    assert state.awaiting_diagnosis_learning_object_ids == frozenset()


# ── No diagnosis can arrive: today's rule, said so ───────────────────────────


@pytest.mark.parametrize(
    ("config", "client_kwargs", "fallback"),
    [
        ("", {}, "split_disabled"),
        ("[diagnosis]\nmax_attempts = 1", {"fail_purposes": ("diagnosis",)}, "diagnosis_failed"),
        ("[diagnosis]\nmax_calls_per_day = 0", {}, "diagnosis_budget_skipped"),
    ],
    ids=["split-disabled", "diagnoser-failed", "budget-skipped"],
)
def test_no_diagnosis_can_arrive_falls_back_to_todays_rule(tmp_path, config, client_kwargs, fallback):
    paths, vault, repository = _assumed(tmp_path, config=config)
    client = _Diagnosed(causal_class="transient_execution", **client_kwargs)
    miss = _miss(vault, repository, client, drain=fallback != "split_disabled")
    if fallback == "split_disabled":
        # A queued diagnosis never runs with the kill switch off.
        append_config(paths.root, "[diagnosis]\nsplit_enabled = false")
        vault = load_vault(paths.root)
        assert repository.post_attempt_jobs(attempt_id=miss.attempt_id, kind="diagnose", states=("queued",))

    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, assumption.resolution.fallback) == (
        "failed", "no_diagnosis", fallback,
    )
    assert (intent.intent, intent.outcome_reason) == ("learning", "no_diagnosis")


def test_a_joint_grade_falls_back_to_todays_rule(tmp_path):
    """With the split off from the start the attempt is graded jointly: no
    diagnosis can ever arrive for it."""

    _paths, vault, repository = _assumed(tmp_path, config="[diagnosis]\nsplit_enabled = false")
    miss = _miss(vault, repository, _Diagnosed(causal_class="transient_execution"))
    assert repository.latest_blind_grade_record(miss.attempt_id) is None
    assumption, _intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution.fallback) == ("failed", "not_blind_graded")


def test_learner_side_help_is_not_a_grading_question():
    """Hints, priming, "don't know" or assistance: the learner's own signal, so
    today's rule applies whatever a diagnosis says."""

    graded = {"a1": MissVerdict("a1", MISS_KEPT, "slip")}
    hinted = AnswerFacts(
        attempt_id="a1", learning_object_id=LO, practice_item_id="pi", created_at="2026-05-20T00:00:00Z",
        attempt_type="hinted_attempt", correctness=0.5, hints_used=1, primed=False, dont_know=False,
        manual_review=False, assisted_class=False,
    )
    verdict = decide_miss(hinted, graded)
    assert (verdict.outcome, verdict.reason) == (MISS_TO_LEARNING, "learner_side")
    plain = AnswerFacts(**{**hinted.__dict__, "attempt_type": "independent_attempt", "hints_used": 0})
    assert decide_miss(plain, graded).reason == "slip"
    assert decide_miss(plain, {}).fallback == "not_diagnosed"


def test_the_diagnosis_reading_is_the_m2_vocabulary():
    assert diagnosis_reason({0: "valid_measurement"}, {0: "learner_state"}) == "knowledge_gap"
    # One gap among several events is enough.
    assert diagnosis_reason(
        {0: "valid_measurement", 1: "item_contract"}, {0: "learner_state", 1: "unknown"},
    ) == "knowledge_gap"
    assert diagnosis_reason({0: "item_contract"}, {0: "unknown"}) == "item_contract"
    assert diagnosis_reason({0: "grader_interpretation"}, {}) == "item_contract"
    assert diagnosis_reason({0: "valid_measurement"}, {0: "transient_execution"}) == "slip"
    assert diagnosis_reason({0: "interaction_context"}, {0: "unknown"}) == "interaction_context"
    assert diagnosis_reason({0: "valid_measurement"}, {0: "unknown"}) == "no_gap_attributed"
    assert diagnosis_reason({0: "unknown"}, {0: "learner_state"}) == "no_gap_attributed"
    assert diagnosis_reason({}, {}) == "no_gap_attributed"


# ── Lapses in maintenance ────────────────────────────────────────────────────


def test_lapses_in_maintenance_are_decided_by_the_diagnosis(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001", answer=CORRECT, when=at(DUE_HOURS + 1))
    assert _state(vault, repository)[1].intent == "maintenance"

    slip = _miss(vault, repository, _Diagnosed(causal_class="transient_execution"), item="pi_svd_compute_001",
                 hours=DUE_HOURS + 30)
    _assumption, intent = _state(vault, repository)
    assert intent.intent == "maintenance"
    assert intent.kept_misses == ((slip.attempt_id, "slip"),)

    pending = _miss(vault, repository, _Diagnosed(causal_class="learner_state"), item="pi_svd_compute_001",
                    hours=DUE_HOURS + 60, drain=False)
    _assumption, intent = _state(vault, repository)
    assert (intent.intent, intent.awaiting_diagnosis_attempt_id) == ("maintenance", pending.attempt_id)

    drain_jobs(vault, repository, _Diagnosed(causal_class="learner_state"), clock=FrozenClock(at(DUE_HOURS + 61)))
    _assumption, intent = _state(vault, repository)
    assert (intent.intent, intent.reason, intent.outcome_reason) == (
        "learning", "missed_in_maintenance", "knowledge_gap",
    )
    assert intent.resolution.attempt_id == pending.attempt_id
    assert intent.kept_misses == ((slip.attempt_id, "slip"),)


# ── Kill switch ──────────────────────────────────────────────────────────────


def test_the_kill_switch_ignores_diagnosis_decided_outcomes(tmp_path):
    """With placement on, a slip keeps the topic in maintenance (its learning
    item withheld); with ``placement.enabled = false`` serving is the
    predecessor's, exactly."""

    paths, vault, repository = _assumed(tmp_path)
    _miss(vault, repository, _Diagnosed(causal_class="transient_execution"))
    moment = FrozenClock(at(DUE_HOURS + 2))
    assert _state(vault, repository)[1].intent == "maintenance"
    on = build_due_queue(vault, repository, clock=moment, persist_explanations=False)
    assert not [s for s in on if s.learning_object_id == LO and s.components.get("new_material")]

    def fingerprint(v, r):
        queue = build_due_queue(v, r, clock=moment, session=SchedulerSession(), persist_explanations=False)
        return [(s.practice_item_id, round(s.priority, 12), sorted(s.components)) for s in queue]

    append_config(paths.root, "[placement]\nenabled = false")
    off = load_vault(paths.root)
    from learnloop.placement.state import placement_active
    from tests.helpers import set_algorithm_version

    assert not placement_active(off)
    off_print = fingerprint(off, repository)
    set_algorithm_version(type("P", (), {"root": paths.root})(), "mvp-0.10")
    predecessor = load_vault(paths.root)
    assert fingerprint(predecessor, repository) == off_print


# ── Report 3 ──────────────────────────────────────────────────────────────────


def test_report3_counts_first_review_outcomes_by_reason(tmp_path):
    paths, vault, repository = _assumed(tmp_path, los=(LO, "lo_transpose", "lo_eigen", "lo_unrelated"))
    _miss(vault, repository, _Diagnosed(causal_class="transient_execution"))  # kept: slip
    _miss(vault, repository, _Diagnosed(causal_class="learner_state"), item="pi_transpose_001")  # gap
    _miss(vault, repository, _Diagnosed(validity_scope="item_contract"), item="pi_eigen_001")  # kept
    _miss(vault, repository, _Diagnosed(), item="pi_unrelated_001", drain=False)  # pending

    with repository.connection() as connection:
        report = placement_report(connection, vault, now_iso=READ_AT)
    source = report["sources"]["self_report"]
    assert report["manifest"]["report_version"] == "placement-report-3-v3"
    assert source["outcomes_by_reason"] == {
        "failed:knowledge_gap": 1, "passed:item_contract": 1, "passed:slip": 1,
    }
    assert (source["passed"], source["failed"], source["open"]) == (2, 1, 1)
    assert (source["passed_clean"], source["kept_by_diagnosis"], source["awaiting_diagnosis"]) == (0, 2, 1)
    assert source["first_review_miss_rate"] == pytest.approx(1 / 3)
    assert report["maintenance"]["lapses_by_reason"] == {}


# ── Codex review fixes (2026-10-12) ──────────────────────────────────────────


def _dont_know(vault, repository, *, item="pi_svd_compute_002", hours):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"setup": 0, "result": 0}, confidence=1),
        clock=FrozenClock(at(hours)),
    )


def test_a_diagnosis_that_never_lands_stops_holding_the_check(tmp_path):
    """F3: the provider is never ready (released ``provider_not_ready``, attempt
    refunded, queued forever). The decision waits at most DIAGNOSIS_WAIT_DAYS
    from the miss's diagnose job, then today's rule applies, decided at the
    deadline; a diagnosis that lands later does not change it."""

    from learnloop.placement.rules import DIAGNOSIS_WAIT_DAYS

    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(), drain=False)
    drain_jobs(vault, repository, None, clock=FrozenClock(at(DUE_HOURS + 2)))
    (job,) = repository.post_attempt_jobs(attempt_id=miss.attempt_id, kind="diagnose")
    assert (job["state"], job["last_error"]) == ("queued", "provider_not_ready")
    deadline_hours = DUE_HOURS + 1 + 24 * DIAGNOSIS_WAIT_DAYS

    assumption, intent = _state(vault, repository, now_iso=_iso(deadline_hours - 1))
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id, intent.intent) == (
        "open", miss.attempt_id, "assumed",
    )
    waiting = build_due_queue(vault, repository, clock=FrozenClock(at(deadline_hours - 1)), persist_explanations=False)
    assert not [s for s in waiting if s.learning_object_id == LO and s.followup_kind is None]
    late = FrozenClock(at(deadline_hours + 1))
    assumption, intent = _state(vault, repository, now_iso=_iso(deadline_hours + 1))
    assert (assumption.status, assumption.resolution_reason, assumption.resolution.fallback) == (
        "failed", "no_diagnosis", "diagnosis_unavailable",
    )
    assert assumption.resolution.decided_at == _iso(deadline_hours)
    assert (intent.intent, intent.outcome_reason) == ("learning", "no_diagnosis")
    state = load_placement_state(vault, repository, now_iso=_iso(deadline_hours + 1))
    assert state.awaiting_diagnosis_learning_object_ids == frozenset()
    queue = build_due_queue(vault, repository, clock=late, persist_explanations=False)
    # Back to learning: routine serving reaches the LO again.
    assert [s for s in queue if s.learning_object_id == LO and s.followup_kind is None]

    # The provider comes back and the diagnosis reads a slip: too late, decided.
    drain_jobs(vault, repository, _Diagnosed(causal_class="transient_execution"), clock=late)
    assert repository.current_live_diagnosis(miss.attempt_id) is not None
    assumption, _intent = _state(vault, repository, now_iso=_iso(deadline_hours + 2))
    assert (assumption.status, assumption.resolution.fallback) == ("failed", "diagnosis_unavailable")


def test_a_decided_miss_is_not_reopened_by_a_retry(tmp_path):
    """F4: ``diagnose retry`` after the miss was decided re-queues the
    diagnosis; the assumption does not go back to waiting, and the new
    diagnosis does not change the decision (decided once)."""

    from learnloop.diagnosis.split.jobs import enqueue_diagnosis

    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(causal_class="learner_state"))
    first = repository.current_live_diagnosis(miss.attempt_id)["id"]
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent.intent) == ("failed", "knowledge_gap", "learning")

    assert enqueue_diagnosis(vault, repository, attempt_id=miss.attempt_id, rediagnose=True,
                             clock=FrozenClock(at(DUE_HOURS + 30)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.awaiting_diagnosis_attempt_id, intent.intent) == ("failed", None, "learning")

    drain_jobs(vault, repository, _Diagnosed(causal_class="transient_execution"), clock=FrozenClock(at(DUE_HOURS + 31)))
    assert repository.current_live_diagnosis(miss.attempt_id)["id"] != first
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, assumption.resolution.diagnosis_id) == (
        "failed", "knowledge_gap", first,
    )
    assert intent.intent == "learning"


def test_a_decided_miss_is_not_reopened_by_a_regrade(tmp_path):
    """F4: a regrade that leaves the answer a miss re-queues its diagnosis; the
    kept topic stays in maintenance (its learning items stay withheld) and the
    re-diagnosis does not flip it."""

    from learnloop.attempts.regrade import regrade_attempt

    from tests.split_live_helpers import ReadyRuntime

    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(causal_class="transient_execution"))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent.intent) == ("passed", "slip", "maintenance")

    row = repository.fetch_practice_attempt(miss.attempt_id)
    regrade_attempt(vault, repository, row, runtime=ReadyRuntime(), client=_Diagnosed(), grading_source="ai",
                    clock=FrozenClock(at(DUE_HOURS + 30)))
    assert repository.post_attempt_jobs(attempt_id=miss.attempt_id, kind="diagnose", states=("queued",))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent.intent) == ("passed", "slip", "maintenance")
    assert intent.awaiting_diagnosis_attempt_id is None

    drain_jobs(vault, repository, _Diagnosed(causal_class="learner_state"), clock=FrozenClock(at(DUE_HOURS + 31)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolution_reason, intent.intent) == ("passed", "slip", "maintenance")


def test_turning_the_split_back_on_does_not_reopen_held_misses(tmp_path):
    """F4: while the switch is off the worker releases the held job
    ``split_disabled`` and today's rule applies; switching it back on does not
    send the LO back to waiting. The held diagnosis decides when it lands."""

    paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(causal_class="transient_execution"), drain=False)
    append_config(paths.root, "[diagnosis]\nsplit_enabled = false")
    off = load_vault(paths.root)
    drain_jobs(off, repository, _Diagnosed(), clock=FrozenClock(at(DUE_HOURS + 2)))
    (job,) = repository.post_attempt_jobs(attempt_id=miss.attempt_id, kind="diagnose")
    assert job["last_error"] == "split_disabled"
    assumption, intent = _state(off, repository)
    assert (assumption.resolution.fallback, intent.intent) == ("split_disabled", "learning")

    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text().replace("split_enabled = false", "split_enabled = true"))
    on = load_vault(paths.root)
    assumption, intent = _state(on, repository)
    assert (assumption.status, assumption.resolution.fallback, intent.intent) == ("failed", "split_disabled", "learning")


@pytest.mark.parametrize(
    ("validity", "causal"),
    [("valid_measurement", "unknown"), ("unknown", "learner_state")],
    ids=["diagnoser-abstains", "validity-unknown"],
)
def test_no_gap_attributed_is_not_a_pass(tmp_path, validity, causal):
    """F5: a diagnosis that attributes no cause did not decide the miss, so
    today's rule returns the LO to learning (fail closed)."""

    _paths, vault, repository = _assumed(tmp_path)
    miss = _miss(vault, repository, _Diagnosed(validity_scope=validity, causal_class=causal))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "failed", miss.attempt_id, "no_gap_attributed",
    )
    assert assumption.resolution.outcome == MISS_TO_LEARNING and assumption.resolution.diagnosis_id
    assert (intent.intent, intent.outcome_reason) == ("learning", "no_gap_attributed")


def test_report3_keeps_the_raw_full_marks_miss_rate(tmp_path):
    """F5: report 3 keeps the rate before the diagnosis decides beside the
    returns-to-learning rate the learned q is fitted to (field §11)."""

    _paths, vault, repository = _assumed(tmp_path, los=(LO, "lo_transpose"))
    _miss(vault, repository, _Diagnosed(causal_class="transient_execution"))  # kept: slip
    _miss(vault, repository, _Diagnosed(causal_class="learner_state"), item="pi_transpose_001")  # gap
    with repository.connection() as connection:
        report = placement_report(connection, vault, now_iso=READ_AT)
    source = report["sources"]["self_report"]
    assert source["first_review_miss_rate"] == pytest.approx(1 / 2)
    assert (source["first_review_full_marks_misses"], source["first_review_full_marks_miss_rate"]) == (2, 1.0)
    assert report["overall"]["first_review_full_marks_miss_rate"] == 1.0


def test_learner_side_help_does_not_wait_on_an_earlier_pending_miss(tmp_path):
    """F8: a later "don't know" answer on the LO returns it while the check
    miss's diagnosis is pending, and stays the decision when that diagnosis
    lands (it landed after the help)."""

    _paths, vault, repository = _assumed(tmp_path)
    _miss(vault, repository, _Diagnosed(causal_class="transient_execution"), drain=False)
    helped = _dont_know(vault, repository, hours=DUE_HOURS + 3)
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, assumption.resolution_reason) == (
        "failed", helped.attempt_id, "learner_side",
    )
    assert intent.intent == "learning" and assumption.awaiting_diagnosis_attempt_id is None

    drain_jobs(vault, repository, _Diagnosed(causal_class="transient_execution"), clock=FrozenClock(at(DUE_HOURS + 4)))
    assumption, intent = _state(vault, repository)
    assert (assumption.status, assumption.resolving_attempt_id, intent.intent) == (
        "failed", helped.attempt_id, "learning",
    )


def test_learner_side_help_in_maintenance_does_not_wait_on_a_pending_lapse(tmp_path):
    _paths, vault, repository = _assumed(tmp_path)
    submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001", answer=CORRECT, when=at(DUE_HOURS + 1))
    _miss(vault, repository, _Diagnosed(causal_class="transient_execution"), hours=DUE_HOURS + 30, drain=False)
    _assumption, intent = _state(vault, repository)
    assert intent.intent == "maintenance" and intent.awaiting_diagnosis_attempt_id is not None
    helped = _dont_know(vault, repository, hours=DUE_HOURS + 31)
    _assumption, intent = _state(vault, repository)
    assert (intent.intent, intent.reason, intent.outcome_reason, intent.resolution.attempt_id) == (
        "learning", "missed_in_maintenance", "learner_side", helped.attempt_id,
    )


def test_the_state_loader_requires_the_split_reading_and_the_time(tmp_path):
    """F9: a caller (DL1, or any new one) cannot silently default to waiting
    on held jobs, or to waiting forever."""

    from learnloop.placement.state import load_placement_state_from_connection

    _paths, _vault, repository = _assumed(tmp_path)
    with repository.connection() as connection:
        with pytest.raises(TypeError):
            load_placement_state_from_connection(connection, active=True)
        with pytest.raises(TypeError):
            load_placement_state_from_connection(connection, active=True, diagnosis_live=True)
        state = load_placement_state_from_connection(connection, active=True, diagnosis_live=True, now_iso=READ_AT)
    assert LO in state.open_by_lo
