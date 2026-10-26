"""The Codex review of the one eligibility decision (job 20261017-004842-PHYZEz,
``docs/reviews/serve-eligibility-decision-codex-review.md``).

* F1: an auto-primed draft is refused a cold check like any primed draft, also
  when its cold task fell due (or its routine display lapsed) during grading.
* F2: a cold check its item can no longer take cold is withdrawn with its typed
  disposition, never re-timed into a check the practice answer contaminates.
* F3: nothing is anchored to a queue build: a delayed open or a delayed submit
  after a withdrawing build is plain practice, and a cold check is never served
  on an item practised since the check was set.
* F4: the successor ``mvp-0.27`` and its kill switch ``eligibility.enabled``;
  below the tag, or off, every path serves and admits exactly as ``mvp-0.26``.

Fakes only; no network, no paid call.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop import serve_eligibility as se
from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    auto_primed_draft,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock, utc_now_iso
from tests.test_serve_eligibility import SUCCESSOR, _at_version, _basic, _one_cold_item_plan, _repair

ITEM = "pi_svd_define_001"
T0 = datetime(2026, 10, 12, 10, 0, 0, tzinfo=UTC)
PREDECESSORS = [("mvp-0.26", True), (SUCCESSOR, False)]
PREDECESSOR_IDS = ["below_the_tag", "switch_off"]


def _iso(moment: datetime) -> str:
    return utc_now_iso(FrozenClock(moment))


def _self_grade(vault, repository, draft, moment):
    return complete_self_graded_attempt(
        vault, repository, draft, SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
        clock=FrozenClock(moment),
    )


def _cold_task(repository, *, not_before: datetime, created: datetime, item: str = ITEM, kind: str = "cold_retry"):
    return repository.create_followup_task(
        kind=kind, case_kind="certification" if kind == "certification_cold_probe" else "misconception",
        case_ref=f"ep_{kind}", not_before=_iso(not_before), expires_at=_iso(not_before + timedelta(days=30)),
        selected_item_id=item, clock=FrozenClock(created),
    )


# -- F1: an auto-primed draft is not exempt ----------------------------------------------------------


def _routine_display_lapsing_at(repository, release: datetime) -> None:
    """A routine display of ITEM whose coverage releases it at ``release``."""

    stamp = release - se.ROUTINE_DISPLAY_COVERAGE - timedelta(seconds=1)
    repository.insert_reveal_event(
        {"practice_item_id": ITEM, "learning_object_id": None, "source_kind": "answer_display",
         "amount": 1.0, "basis": "feedback_full_answer:desktop:review_f1"},
        clock=FrozenClock(stamp),
    )


@pytest.mark.parametrize(("version", "enabled"), [(SUCCESSOR, True), *PREDECESSORS],
                         ids=["successor", *PREDECESSOR_IDS])
def test_f1_an_auto_primed_draft_is_refused_when_its_cold_task_falls_due_during_grading(tmp_path, version, enabled):
    """Codex F1's transition: a routine display covers the item until 10:00:01,
    when its deferred cold task becomes due. An ordinary answer starts grading
    at 10:00:00 and is auto-primed; grading finishes at 10:02, when the ledger
    no longer primes it and the task is due. The draft is still primed, so it
    is refused the cold task (the base guard, kept); at the successor the
    refusal says why. Fail-first: the branch accepted it and let the primed
    answer consume the cold task."""

    vault, repository, _misconception = _repair(tmp_path, version, enabled=enabled)
    _routine_display_lapsing_at(repository, T0 + timedelta(seconds=1))
    task = _cold_task(repository, not_before=T0 + timedelta(seconds=1), created=T0 - timedelta(days=2))

    draft, total = auto_primed_draft(
        repository, AttemptDraft(practice_item_id=ITEM, learner_answer_md="an answer"), clock=FrozenClock(T0)
    )
    assert draft.primed and draft.auto_primed_reveal_total == total
    with pytest.raises(AttemptValidationError, match="a cold retry must be unassisted and unprimed") as refused:
        _self_grade(vault, repository, draft, T0 + timedelta(minutes=2))
    if enabled and version == SUCCESSOR:
        assert "still shown when this answer was started" in str(refused.value)
    else:
        assert str(refused.value) == "a cold retry must be unassisted and unprimed"
    after = repository.followup_task(task["id"])
    assert after["status"] in {"pending", "served"} and after["consumed_attempt_id"] is None


def test_f1_the_decision_refuses_any_primed_draft_and_names_its_provenance():
    inputs = se.EligibilityInputs(
        practice_item_id="pi", learning_object_id=None, at="2026-10-12T10:02:00Z",
        tasks=(se.FollowupTask(id="t", kind="cold_retry", created_at="2026-10-10T10:00:00Z",
                               not_before="2026-10-12T10:00:01Z", expires_at="2026-11-12T10:00:00Z"),),
    )
    from dataclasses import replace

    assert se.decide(inputs, se.SUBMIT).verdict == se.SERVE
    auto = se.decide(replace(inputs, declared_primed=True, auto_primed=True), se.SUBMIT)
    assert (auto.verdict, auto.reason) == (se.REFUSE, se.COLD_CHECK_AUTO_PRIMED)
    declared = se.decide(replace(inputs, declared_primed=True), se.SUBMIT)
    assert (declared.verdict, declared.reason) == (se.REFUSE, se.COLD_CHECK_ASSISTED)
    assert declared.message.endswith("it was declared primed")


# -- F2: the measurement ends honestly, the practice item is not its target -------------------------


def test_f2_every_open_cold_check_on_an_item_whose_answer_stands_is_withdrawn():
    """Due or not: an unpractised item stays primed (only an attempt absorbs a
    non-routine reveal) and a practised one is a hard exposure, so a later
    check on it can never be cold either."""

    tasks = (
        se.FollowupTask(id="due", kind="cold_retry", created_at="2026-10-10T10:00:00Z",
                        not_before="2026-10-11T10:00:00Z", expires_at="2026-11-10T10:00:00Z"),
        se.FollowupTask(id="later", kind="certification_cold_probe", created_at="2026-10-10T10:00:00Z",
                        not_before="2026-10-30T10:00:00Z", expires_at="2026-11-06T10:00:00Z"),
        se.FollowupTask(id="practice", kind="intervention_followup", created_at="2026-10-10T10:00:00Z",
                        not_before="2026-10-11T10:00:00Z", expires_at=None),
    )
    reveal = se.RevealRow(id="r", practice_item_id="pi", learning_object_id="lo", source_kind="tutor_answer",
                          basis="tutor_answer", amount=1.0, created_at="2026-10-09T10:00:00Z")
    decision = se.decide(se.EligibilityInputs(practice_item_id="pi", learning_object_id="lo",
                                              at="2026-10-12T10:00:00Z", reveals=(reveal,), tasks=tasks),
                         se.COLD_CHECK)
    assert decision.verdict == se.SERVE_AS_ORDINARY
    assert dict(decision.withdrawals) == {"due": se.COLD_CHECK_ANSWER_SHOWN, "later": se.COLD_CHECK_ANSWER_SHOWN}
    assert not decision.retimes and decision.until is None and decision.reveal_event_ids == ("r",)


def test_f2_a_certification_probe_whose_answer_was_shown_expires_unmeasured(tmp_path):
    """The certification lane's own door for a probe whose claim no longer
    stands (``_cancel_stale_probes``): expired, read as unmeasured by the rate;
    no repair disposition is written for it."""

    from learnloop.scheduling.scheduler import cold_check_serve_decision

    vault, repository, _misconception = _repair(tmp_path)
    task = _cold_task(repository, not_before=T0 - timedelta(hours=1), created=T0 - timedelta(days=21),
                      kind="certification_cold_probe")
    repository.insert_reveal_event(
        {"practice_item_id": ITEM, "learning_object_id": None, "source_kind": "tutor_answer", "amount": 1.0,
         "basis": "tutor_answer"}, clock=FrozenClock(T0 - timedelta(days=3)),
    )

    decision = cold_check_serve_decision(vault, repository, ITEM, clock=FrozenClock(T0))

    assert decision.verdict == se.SERVE_AS_ORDINARY
    assert repository.followup_task(task["id"])["status"] == "expired"
    assert repository.causal_cold_outcomes() == []
    practice = _self_grade(vault, repository, AttemptDraft(practice_item_id=ITEM, learner_answer_md="x"), T0)
    assert repository.consumed_followup_task_for_attempt(practice.attempt_id) is None


def test_f2_a_non_persisting_read_withdraws_nothing(tmp_path):
    from learnloop.scheduling.scheduler import build_due_queue, cold_check_serve_decision

    vault, repository, _misconception = _repair(tmp_path)
    task = _cold_task(repository, not_before=T0 - timedelta(hours=1), created=T0 - timedelta(days=1))
    repository.insert_reveal_event(
        {"practice_item_id": ITEM, "learning_object_id": None, "source_kind": "tutor_answer", "amount": 1.0,
         "basis": "tutor_answer"}, clock=FrozenClock(T0 - timedelta(days=2)),
    )

    read = cold_check_serve_decision(vault, repository, ITEM, clock=FrozenClock(T0), persist=False)
    queue = build_due_queue(vault, repository, clock=FrozenClock(T0), persist_explanations=False)

    assert read.verdict == se.SERVE_AS_ORDINARY and read.withdrawals
    assert ITEM not in [item.practice_item_id for item in queue if item.followup_kind == "cold_retry"]
    assert repository.followup_task(task["id"])["status"] in {"pending", "served"}
    assert repository.causal_cold_outcomes() == []


# -- F3: nothing is anchored to a queue build ------------------------------------------------------


def _f3_setup(tmp_path):
    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair(tmp_path)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    (task,) = repository.open_followup_tasks_for_item(cold_item)
    return vault, repository, cold_item, task, NOW


def test_f3_a_delayed_open_and_submit_after_a_withdrawing_build_are_plain_practice(tmp_path):
    """Codex F3's timeline: a build on Monday at 10:00 meets a revealed item
    (on the branch it re-timed the check to Tuesday 10:00). The learner opens
    it Tuesday at 09:59 and submits at 10:00, or at 09:59:30: plain practice
    either way, accepted, and no cold check follows thirty seconds later.
    Fail-first: the branch refused the 10:00 submit as a primed cold retry."""

    from learnloop.scheduling.scheduler import build_due_queue, cold_check_serve_decision

    for submit_offset in (timedelta(0), timedelta(seconds=-30)):
        root = tmp_path / f"run{abs(int(submit_offset.total_seconds()))}"
        root.mkdir()
        vault, repository, cold_item, task, now = _f3_setup(root)
        repository.insert_reveal_event(
            {"practice_item_id": cold_item, "learning_object_id": vault.practice_items[cold_item].learning_object_id,
             "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
            clock=FrozenClock(now - timedelta(hours=2)),
        )
        monday = now + timedelta(days=1, hours=1)
        build_due_queue(vault, repository, clock=FrozenClock(monday))
        assert repository.followup_task(task["id"])["status"] == "expired"

        tuesday = monday + timedelta(days=1)
        opened = cold_check_serve_decision(vault, repository, cold_item,
                                           clock=FrozenClock(tuesday - timedelta(minutes=1)))
        assert (opened.verdict, opened.reason) == (se.SERVE, se.NO_COLD_CHECK)
        answered = _self_grade(vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"),
                               tuesday + submit_offset)
        assert repository.consumed_followup_task_for_attempt(answered.attempt_id) is None
        soon = build_due_queue(vault, repository, clock=FrozenClock(tuesday + timedelta(seconds=30)))
        assert cold_item not in [item.practice_item_id for item in soon if item.followup_kind == "cold_retry"]


def test_f3_a_cold_check_is_never_served_on_an_item_practised_since_it_was_set(tmp_path):
    """No reveal at all: the learner practised the cold item (served as
    practice by a path that wrote nothing, or ranked as ordinary practice)
    thirty seconds before its check fell due. The coldness receipt reads that
    attempt as a hard exposure and the retrieval delay fails, so the check is
    withdrawn when it falls due instead of being served."""

    from learnloop.scheduling.scheduler import build_due_queue

    vault, repository, cold_item, task, now = _f3_setup(tmp_path)
    due = now + timedelta(days=1)
    _self_grade(vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"),
                due - timedelta(seconds=30))
    assert repository.followup_task(task["id"])["status"] in {"pending", "served"}

    queue = build_due_queue(vault, repository, clock=FrozenClock(due + timedelta(seconds=30)))

    assert cold_item not in [item.practice_item_id for item in queue if item.followup_kind == "cold_retry"]
    assert repository.followup_task(task["id"])["status"] == "expired"
    (outcome,) = [row for row in repository.causal_cold_outcomes() if row["followup_task_id"] == task["id"]]
    assert outcome["outcome"] == "unmeasurable_no_held_out_surface"
    assert outcome["detail"]["reason"] == se.COLD_CHECK_PRACTISED_SINCE_SCHEDULED


def test_f3_a_cold_check_served_unpractised_is_still_served(tmp_path):
    """Control: no reveal, no practice since the check was set: the cold lane
    serves the cold retry when it falls due, and its answer consumes it."""

    from learnloop.scheduling.scheduler import build_due_queue

    vault, repository, cold_item, task, now = _f3_setup(tmp_path)
    due = now + timedelta(days=1, minutes=5)

    queue = build_due_queue(vault, repository, clock=FrozenClock(due))

    assert cold_item in [item.practice_item_id for item in queue if item.followup_kind == "cold_retry"]
    answered = _self_grade(vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"), due)
    assert repository.followup_task(task["id"])["consumed_attempt_id"] == answered.attempt_id


# -- F4: the successor and its kill switch ---------------------------------------------------------


def test_f4_the_successor_follows_regrade_contracts_and_keeps_every_predecessor():
    from learnloop.algorithm_versions import (
        ELIGIBILITY_DECISION_ALGORITHM_VERSION,
        ELIGIBILITY_DECISION_VERSIONS,
        LATEST_ALGORITHM_VERSION,
        METHOD_EXPLICIT_VERSIONS,
        P0_PROJECTION_VERSIONS,
        REGRADE_CONTRACT_ALGORITHM_VERSION,
        REGRADE_CONTRACT_VERSIONS,
        ROUTER_MIXTURE_VERSIONS,
        SUCCESSOR_CHAIN,
    )
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version

    assert ELIGIBILITY_DECISION_ALGORITHM_VERSION == "mvp-0.27" == SUCCESSOR_CHAIN[18]
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.35"
    assert SUCCESSOR_CHAIN[17] == REGRADE_CONTRACT_ALGORITHM_VERSION
    assert ELIGIBILITY_DECISION_VERSIONS == frozenset({"mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32", "mvp-0.33", "mvp-0.34", "mvp-0.35"})
    for versions in (REGRADE_CONTRACT_VERSIONS, METHOD_EXPLICIT_VERSIONS, ROUTER_MIXTURE_VERSIONS,
                     P0_PROJECTION_VERSIONS):
        assert "mvp-0.27" in versions
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.27"] == defaults_fingerprint_for_version("mvp-0.27")


def test_f4_the_gate_reads_the_version_and_the_switch(tmp_path):
    from learnloop.vault.loader import load_vault

    paths = _basic(tmp_path)
    assert se.decision_active(load_vault(paths.root))
    _at_version(paths.root, SUCCESSOR, enabled=False)
    assert not se.decision_active(load_vault(paths.root))
    _at_version(paths.root, "mvp-0.26")
    assert not se.decision_active(load_vault(paths.root))
    assert not se.decision_active(None)


def test_f4_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app
    from learnloop.eligibility_decision_upgrade import upgrade_to_mvp027
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_placement_vault

    clock = FrozenClock(T0)
    direct = create_placement_vault(tmp_path / "direct", version="mvp-0.26")
    result = upgrade_to_mvp027(direct.root, clock=clock)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.26", "mvp-0.27")
    assert load_vault(direct.root).config.algorithms.algorithm_version == "mvp-0.27"
    again = upgrade_to_mvp027(direct.root, clock=clock)
    assert not again.upgraded and again.problems == ["vault is already mvp-0.27"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.24")
    assert upgrade_to_mvp027(chained.root, clock=clock).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == "mvp-0.27"

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_mvp027(old.root, clock=clock)
    assert not refused.upgraded and "only 'mvp-0.26'" in refused.problems[0]
    assert load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version="mvp-0.26")
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root), "--to", "mvp-0.27"])
    assert invoked.exit_code == 0, invoked.output
    assert "mvp-0.26 -> mvp-0.27" in invoked.output


def test_f4_new_vaults_start_at_the_successor_with_the_switch_on(tmp_path):
    from learnloop.bootstrap import init_vault
    from learnloop.vault.loader import load_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(T0))
    fresh = load_vault(tmp_path / "fresh")
    # A new vault starts at the latest successor (mvp-0.35 since Reader CA2, after rebuild equivalence's
    # mvp-0.34, LP-min (a)'s mvp-0.33, RW7b's mvp-0.32, RW2d's mvp-0.31, AD2+AD3's mvp-0.30 and the intent successor mvp-0.29),
    # which keeps this one.
    assert fresh.config.algorithms.algorithm_version == "mvp-0.35"
    assert fresh.config.eligibility.enabled
    assert se.decision_active(fresh)


@pytest.mark.parametrize(("version", "enabled"), PREDECESSORS, ids=PREDECESSOR_IDS)
def test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026(tmp_path, version, enabled):
    """The predecessor exactly: the queue's cold lane serves the cold retry
    (the reveal predates the task), submit then refuses the primed answer with
    the bare message, the task stays open, and no disposition is written."""

    from learnloop.scheduling.scheduler import build_due_queue, cold_check_serve_decision
    from learnloop_sidecar.handlers.queue import revalidate_cold_check
    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair(tmp_path, version, enabled=enabled)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    (task,) = repository.open_followup_tasks_for_item(cold_item)
    repository.insert_reveal_event(
        {"practice_item_id": cold_item, "learning_object_id": vault.practice_items[cold_item].learning_object_id,
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(NOW - timedelta(hours=2)),
    )
    moment = NOW + timedelta(days=1, hours=1)

    queue = build_due_queue(vault, repository, clock=FrozenClock(moment))
    served = cold_check_serve_decision(vault, repository, cold_item, clock=FrozenClock(moment))

    assert cold_item in [item.practice_item_id for item in queue if item.followup_kind == "cold_retry"]
    assert (served.verdict, served.reason) == (se.SERVE, se.ELIGIBLE)
    assert revalidate_cold_check(vault, repository, cold_item) is None
    with pytest.raises(AttemptValidationError) as refused:
        _self_grade(vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"), moment)
    assert str(refused.value) == "a cold retry must be unassisted and unprimed"
    assert repository.followup_task(task["id"])["status"] in {"pending", "served"}
    assert repository.causal_cold_outcomes() == []


@pytest.mark.parametrize(("version", "enabled"), PREDECESSORS, ids=PREDECESSOR_IDS)
def test_f4_below_the_tag_or_switched_off_a_practised_cold_check_is_served(tmp_path, version, enabled):
    """F3's withdrawal is the successor's: below it the cold retry is served
    after a practice attempt, as before."""

    from learnloop.scheduling.scheduler import build_due_queue
    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled

    vault, repository, misconception_id = _repair(tmp_path, version, enabled=enabled)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = NOW + timedelta(days=1)
    _self_grade(vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"),
                due - timedelta(seconds=30))

    queue = build_due_queue(vault, repository, clock=FrozenClock(due + timedelta(seconds=30)))

    assert cold_item in [item.practice_item_id for item in queue if item.followup_kind == "cold_retry"]
    assert repository.causal_cold_outcomes() == []


@pytest.mark.parametrize(("version", "enabled"), [(SUCCESSOR, True), *PREDECESSORS],
                         ids=["successor", *PREDECESSOR_IDS])
def test_f4_a_probe_of_an_item_submit_would_prime_is_refused_only_at_the_successor(tmp_path, version, enabled):
    from learnloop.diagnosis.probe_episodes import commit_item_presentation, enter_episode, episode_hypothesis_set
    from learnloop.vault.loader import load_vault
    from tests.test_probe_orchestration_remainder import CLOCK, ITEM_ID, LO_ID, _setup

    root, loaded, repository = _setup(tmp_path)
    _at_version(root, version, enabled=enabled)
    loaded = load_vault(root)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    repository.insert_reveal_event(
        {"practice_item_id": ITEM_ID, "learning_object_id": LO_ID, "source_kind": "tutor_answer",
         "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(CLOCK.now() - timedelta(days=10)),
    )

    presentation = commit_item_presentation(
        loaded, repository, episode, loaded.practice_items[ITEM_ID], episode_hypothesis_set(repository, episode),
        clock=CLOCK,
    )

    assert (presentation is None) is (version == SUCCESSOR and enabled)


@pytest.mark.parametrize(("version", "enabled"), [(SUCCESSOR, True), *PREDECESSORS],
                         ids=["successor", *PREDECESSOR_IDS])
def test_f4_q33s_bounded_window_is_the_successors(tmp_path, version, enabled):
    """A seeded exam answer before a later tutor answer: unprimed at the
    successor (Q33), primed below it or with the switch off (as before)."""

    from learnloop.goals.exam_seeding import seed_exam_attempts
    from learnloop.vault.loader import load_vault
    from tests.test_exam_seeding import LIVE_NOW, _exam_vault, _outcomes

    root, _loaded, repository = _exam_vault(tmp_path)
    _at_version(root, version, enabled=enabled)
    loaded = load_vault(root)
    repository.insert_reveal_event(
        {"practice_item_id": "pi_exam_q1", "learning_object_id": "lo_svd_definition",
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(LIVE_NOW),
    )

    seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    by_item = {row["practice_item_id"]: row for row in repository.list_attempts_by_learning_object("lo_svd_definition")}
    assert bool(by_item["pi_exam_q1"]["primed"]) is not (version == SUCCESSOR and enabled)


def test_f4_the_plan_serves_the_12_9_case_as_mvp_026_with_the_switch_off(tmp_path):
    """The plan's serve with the switch off: the cold check is served (no
    eligibility on the step), and submit refuses the primed answer, as before."""

    from learnloop.daily_plan.engine import advance, get_or_create_today

    env, clock, task = _one_cold_item_plan(tmp_path, enabled=False)
    get_or_create_today(env)
    _record, step = advance(env, serve=True)

    assert step.get("practice_item_id") == "pi_cold" and "eligibility" not in step
    with pytest.raises(AttemptValidationError, match="^a cold retry must be unassisted and unprimed$"):
        _self_grade(env.vault, env.repository, AttemptDraft(practice_item_id="pi_cold", learner_answer_md="x"),
                    clock.instant)
    assert env.repository.followup_task(task["id"])["status"] in {"pending", "served"}


# -- the direct opens at the successor (the landing test's successor half) -------------------------


@pytest.fixture()
def successor_ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = _basic(tmp_path)
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    context.paths = paths
    return context


def test_a_cold_check_on_a_direct_open_is_withdrawn_when_its_item_can_no_longer_take_it_cold(successor_ctx):
    """``test_ux_phase4_landing``'s direct opens, at the successor: a due cold
    retry after a NON-routine reveal (a tutor answer after the item's last
    attempt, before the task was created) is one submit would prime, so both
    direct opens serve the item as ordinary practice, labelled: no error, no
    cold administration, and the retry withdrawn with its disposition (the
    answer is accepted, never refused)."""

    from learnloop.attempts.attempts import AUTO_PRIME_REVEAL_THRESHOLD, reveal_total_for_submission
    from learnloop.attempts.reveal_ledger import record_reveal
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.test_ux_phase4_feedback import _administration_receipts, _due_cold_task, _feedback_answer, _later

    ctx = successor_ctx

    def call(method: str, params: dict):
        spec = METHOD_REGISTRY[method]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    _vault, repository = ctx.require_vault()
    _feedback_answer(ctx, then=_later(days=-2))
    record_reveal(repository, practice_item_id=ITEM, source_kind="tutor_answer", amount=1.0,
                  clock=_later(days=-1, hours=-12))
    task = _due_cold_task(ctx, case_ref="ep_landing")
    session_id = call("start_session", {"availableMinutes": 20})["sessionId"]

    assert reveal_total_for_submission(repository, ITEM) >= AUTO_PRIME_REVEAL_THRESHOLD
    detail = call("get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})
    assert detail["id"] == ITEM
    assert detail["eligibility"]["verdict"] == se.SERVE_AS_ORDINARY
    assert detail["eligibility"]["checkDueAt"] is None
    assert call("open_queue_item", {"practiceItemId": ITEM})["id"] == ITEM
    assert repository.followup_task(task["id"])["status"] == "expired"
    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is None
    assert _administration_receipts(repository) == 0


# -- re-review F5: a withdrawal decides on the task as it stands under the lock ----------------------


def test_f5_a_withdrawal_racing_a_consume_leaves_the_consume_time_disposition_free(tmp_path, monkeypatch):
    """Codex re-review F5: a submit that consumes the cold retry between the
    withdrawal's look at the task and its transaction (its post-attempt
    verification still to run) must win. The withdrawal reads the task inside
    its BEGIN IMMEDIATE, sees it consumed and writes nothing, so the consume's
    own disposition (here ``contaminated_or_assisted``) is the task's one row."""

    from contextlib import contextmanager

    from learnloop.diagnosis.causal_probe_coherence import record_causal_cold_outcome
    from learnloop.diagnosis.remediation import withdraw_cold_measurement

    vault, repository, _misconception = _repair(tmp_path)
    earlier = _self_grade(vault, repository, AttemptDraft(practice_item_id=ITEM, learner_answer_md="x"),
                          T0 - timedelta(days=2))
    task = _cold_task(repository, not_before=T0 - timedelta(hours=1), created=T0 - timedelta(days=1))
    assert repository.followup_task(task["id"])["status"] in {"pending", "served"}

    real_atomic = repository.atomic
    raced: list[str] = []

    @contextmanager
    def atomic_after_a_concurrent_consume():
        if not raced:  # the concurrent submit commits its consume first
            raced.append(task["id"])
            repository.consume_followup_task(task["id"], earlier.attempt_id, clock=FrozenClock(T0))
        with real_atomic():
            yield

    monkeypatch.setattr(repository, "atomic", atomic_after_a_concurrent_consume)

    withdrawn = withdraw_cold_measurement(
        vault, repository, task["id"], reason=se.COLD_CHECK_ANSWER_SHOWN, clock=FrozenClock(T0),
    )

    assert raced == [task["id"]]
    assert withdrawn is None
    assert repository.followup_task(task["id"])["status"] == "consumed"
    assert repository.causal_cold_outcome_for_task(task["id"]) is None
    monkeypatch.setattr(repository, "atomic", real_atomic)
    recorded = record_causal_cold_outcome(
        repository, outcome="contaminated_or_assisted", followup_task_id=task["id"],
        cold_attempt_id=earlier.attempt_id, servable_opportunity=True, detail={"stage": "consume"},
        clock=FrozenClock(T0),
    )
    assert recorded is not None
    assert repository.causal_cold_outcome_for_task(task["id"])["outcome"] == "contaminated_or_assisted"
