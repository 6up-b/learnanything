"""One serve/administration eligibility decision (``learnloop.serve_eligibility``,
``docs/reviews/serve-eligibility-decision.md``).

Every serve path asks the one decision submit asks, so an item served as a cold
check is accepted as one, and an item submit would prime is never served as a
cold check: it is served as ordinary practice and its cold task re-timed, never
left due to expire. Fakes only; no network, no paid call.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest
from typer.testing import CliRunner

from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    auto_primed_draft,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop import serve_eligibility as se

START = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)


def _iso(moment: datetime) -> str:
    return utc_now_iso(FrozenClock(moment))


def _one_cold_item_plan(tmp_path, *, reveal_kind: str = "tutor_answer", reveal_ago=timedelta(hours=26), start=START):
    """§12.9's reproduction (``test_f1k_a_non_routine_reveal_never_starves_the_plan``'s
    setup): one eligible item, a cold retry created a day ago and due for an
    hour, and a non-routine reveal of the item made before the task."""

    from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_c": [("pi_cold", 1.0)]})
    clock = MovableClock(start)
    env = make_env(paths.root, [scheduled("pi_cold", "lo_c", priority=0.9, followup_kind="cold_retry")],
                   clock=clock, session_id="s_one")
    seed_due(env.repository, "pi_cold", due=start - timedelta(days=2), last=start - timedelta(days=9))
    task = env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_one",
        not_before=_iso(start - timedelta(hours=1)), expires_at=_iso(start + timedelta(days=30)),
        selected_item_id="pi_cold", clock=FrozenClock(start - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_cold", "learning_object_id": "lo_c", "source_kind": reveal_kind,
         "amount": 1.0, "basis": reveal_kind},
        clock=FrozenClock(start - reveal_ago),
    )
    return env, clock, task


def _answer(env, item_id: str, moment: datetime, *, hints: int = 0):
    return complete_self_graded_attempt(
        env.vault, env.repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", hints_used=hints),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
        clock=FrozenClock(moment),
    )


# -- §12.9 (1): the cold lane and submit agree on a non-routine reveal ---------------------------


def test_the_12_9_reproduction_is_served_as_practice_and_accepted(tmp_path):
    """The plan serves the item, as ordinary practice with an honest label: its
    cold task is re-timed one cold delay on, so the answer is accepted (primed,
    as submit has always recorded it), never refused after it was written.
    The cold check then comes back cold, and is accepted as the cold check."""

    from learnloop.daily_plan.engine import advance, get_or_create_today

    env, clock, task = _one_cold_item_plan(tmp_path)
    get_or_create_today(env)
    _record, step = advance(env, serve=True)

    assert step.get("practice_item_id") == "pi_cold"
    # On main: "a cold retry must be unassisted and unprimed", after the answer was written.
    result = _answer(env, "pi_cold", clock.instant)
    attempt = env.repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["primed"]
    assert step["eligibility"]["verdict"] == se.SERVE_AS_ORDINARY
    assert step["eligibility"]["reason"] == se.COLD_CHECK_ANSWER_SHOWN

    later = clock.instant + se.COLD_RETRIEVAL_DELAY + timedelta(minutes=1)
    retimed = env.repository.followup_task(task["id"])
    assert retimed["status"] in {"pending", "served"} and retimed["not_before"] <= _iso(later)
    cold = se.decide(se.gather(env.repository, practice_item_id="pi_cold", learning_object_id="lo_c",
                               at=_iso(later)), se.COLD_CHECK)
    assert cold.verdict == se.SERVE, cold.record()
    answered = _answer(env, "pi_cold", later)
    assert not env.repository.fetch_practice_attempt(answered.attempt_id)["primed"]


def test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice(tmp_path):
    """The queue's cold lane: a tutor answer on the cold item before its task
    was created (the scheduler's deferral never saw it) primes the item at
    submit, so the lane does not serve it as the cold retry. The item is in
    the queue as practice, with the reason, and its answer is accepted."""

    from learnloop.scheduling.scheduler import build_due_queue
    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled, _setup

    vault, repository, misconception_id = _setup(tmp_path)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    repository.insert_reveal_event(
        {"practice_item_id": cold_item, "learning_object_id": vault.practice_items[cold_item].learning_object_id,
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(NOW - timedelta(hours=2)),
    )
    moment = NOW + timedelta(days=1, hours=1)

    queue = build_due_queue(vault, repository, clock=FrozenClock(moment))

    by_id = {item.practice_item_id: item for item in queue}
    assert cold_item in by_id
    assert by_id[cold_item].followup_kind != "cold_retry"
    assert any("seen this answer" in reason for reason in by_id[cold_item].plain_english)
    # Re-timed, it stays offered as practice on the next build.
    again = {item.practice_item_id: item for item in build_due_queue(
        vault, repository, clock=FrozenClock(moment + timedelta(minutes=5)))}
    assert cold_item in again and any("seen this answer" in reason for reason in again[cold_item].plain_english)
    complete_self_graded_attempt(
        vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="an answer"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3), clock=FrozenClock(moment + timedelta(minutes=6)),
    )
    # The practice attempt absorbed the exposure: no longer pushed as practice,
    # and the cold check is back a cold delay after the re-time.
    after = build_due_queue(vault, repository, clock=FrozenClock(moment + timedelta(minutes=7)))
    assert not any(
        reason.startswith("Practice: you've seen") for item in after for reason in item.plain_english
    )
    cold_again = [item.practice_item_id for item in build_due_queue(
        vault, repository, clock=FrozenClock(moment + timedelta(days=1, minutes=1))) if item.followup_kind == "cold_retry"]
    assert cold_item in cold_again


def test_submit_refusal_names_the_change_since_the_serve(tmp_path):
    """Served as the cold check; then the tutor shows the answer before the
    learner submits. Submit refuses, and says why: the reveal, by kind and time."""

    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled, _setup

    vault, repository, misconception_id = _setup(tmp_path)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    moment = NOW + timedelta(days=1, hours=1)
    served = se.decide(se.gather(repository, practice_item_id=cold_item, learning_object_id=None, at=_iso(moment)),
                       se.COLD_CHECK)
    assert served.verdict == se.SERVE
    repository.insert_reveal_event(
        {"practice_item_id": cold_item, "learning_object_id": None, "source_kind": "tutor_answer",
         "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(moment + timedelta(minutes=1)),
    )

    with pytest.raises(AttemptValidationError, match="unassisted and unprimed: its answer was shown .tutor answer at"):
        complete_self_graded_attempt(
            vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="an answer"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=3),
            clock=FrozenClock(moment + timedelta(minutes=2)),
        )


# -- §12.9 (2): the CLI validates before it prompts -------------------------------------------------


def _cli(*args: str):
    from learnloop.cli.app import app

    return CliRunner().invoke(app, list(args))


def test_the_cli_attempt_refuses_an_inadmissible_type_without_prompting(tmp_path):
    """§12.9's reproduction: ``--attempt-type diagnostic_probe`` used to print
    ``Answer []:``, wait for the answer, then exit 1."""

    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)

    result = _cli("attempt", "pi_svd_define_001", "--attempt-type", "diagnostic_probe", "--vault", str(paths.root))

    assert result.exit_code == 1
    assert "Answer" not in result.output
    assert "diagnostic_probe is not allowed" in result.output


def test_the_cli_attempt_refuses_an_assisted_cold_check_without_prompting(tmp_path):
    from learnloop.db.repositories import Repository
    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    now = datetime.now(UTC).replace(microsecond=0)
    Repository(paths.sqlite_path).create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_cli",
        not_before=_iso(now - timedelta(hours=1)), expires_at=_iso(now + timedelta(days=30)),
        selected_item_id="pi_svd_define_001", clock=FrozenClock(now - timedelta(days=1)),
    )

    result = _cli("attempt", "pi_svd_define_001", "--hints-used", "1", "--vault", str(paths.root))

    assert result.exit_code == 1
    assert "Answer" not in result.output
    assert "a cold retry must be unassisted and unprimed: hints were used" in result.output


def test_the_cli_attempt_records_a_primed_cold_check_as_practice(tmp_path):
    """The CLI's attempt is a serve too: a due cold retry whose answer a tutor
    showed is re-timed and the answer recorded as practice, with a note."""

    from learnloop.db.repositories import Repository
    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    repository = Repository(paths.sqlite_path)
    now = datetime.now(UTC).replace(microsecond=0)
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_cli",
        not_before=_iso(now - timedelta(hours=1)), expires_at=_iso(now + timedelta(days=30)),
        selected_item_id="pi_svd_define_001", clock=FrozenClock(now - timedelta(days=1)),
    )
    repository.insert_reveal_event(
        {"practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(now - timedelta(hours=26)),
    )

    result = _cli("attempt", "pi_svd_define_001", "--answer", "U Sigma V^T", "--criterion-points", "correctness=4",
                  "--vault", str(paths.root))

    assert result.exit_code == 0, result.output
    assert "seen this answer" in result.output
    assert repository.followup_task(task["id"])["not_before"] > _iso(now)


def test_a_refused_cli_attempt_writes_nothing(tmp_path):
    """A refusal before the prompt leaves the cold task as it was: the serve's
    re-time is persisted only once the draft passes."""

    from learnloop.db.repositories import Repository
    from tests.helpers import create_basic_vault, seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    repository = Repository(paths.sqlite_path)
    now = datetime.now(UTC).replace(microsecond=0)
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_cli",
        not_before=_iso(now - timedelta(hours=1)), expires_at=_iso(now + timedelta(days=30)),
        selected_item_id="pi_svd_define_001", clock=FrozenClock(now - timedelta(days=1)),
    )
    repository.insert_reveal_event(
        {"practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(now - timedelta(hours=26)),
    )

    result = _cli("attempt", "pi_svd_define_001", "--attempt-type", "diagnostic_probe", "--vault", str(paths.root))

    assert result.exit_code == 1 and "Answer" not in result.output
    assert repository.followup_task(task["id"])["not_before"] == task["not_before"]


# -- Q33: a historical writer counts only reveals at or before its instant --------------------------


def test_q33_an_exam_seeded_before_a_later_reveal_is_not_primed(tmp_path):
    """Exam seeding writes at the exam's past instant. A tutor answer shown
    after the exam was not in view when it was sat: the seeded answer is not
    primed. Live submit keeps its window (the clock-went-back rule)."""

    from learnloop.goals.exam_seeding import seed_exam_attempts
    from tests.test_exam_seeding import LIVE_NOW, _exam_vault, _outcomes

    _root, loaded, repository = _exam_vault(tmp_path)
    repository.insert_reveal_event(
        {"practice_item_id": "pi_exam_q1", "learning_object_id": "lo_svd_definition",
         "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
        clock=FrozenClock(LIVE_NOW),
    )

    seed_exam_attempts(loaded, repository, outcomes=_outcomes())

    by_item = {row["practice_item_id"]: row for row in repository.list_attempts_by_learning_object("lo_svd_definition")}
    assert not by_item["pi_exam_q1"]["primed"]
    # A live draft at the exam's instant still counts the later row (unbounded).
    draft, _total = auto_primed_draft(
        repository, AttemptDraft(practice_item_id="pi_exam_q2", learner_answer_md="x"),
        clock=FrozenClock(LIVE_NOW - timedelta(days=30)),
    )
    assert not draft.primed  # no reveal on q2 at all: control


def test_q33_the_bounded_window_also_bounds_the_last_attempt(tmp_path):
    """At instant T the window starts at the last attempt at or before T: a
    reveal between that attempt and T counts, one after T does not, and an
    attempt after T does not absorb the earlier reveal."""

    from tests.test_remediation_cold_retry import _setup

    vault, repository, _misconception = _setup(tmp_path)
    item = "pi_svd_define_001"
    t = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    _answer_at = lambda moment: complete_self_graded_attempt(  # noqa: E731
        vault, repository, AttemptDraft(practice_item_id=item, learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=3), clock=FrozenClock(moment),
    )
    _answer_at(t - timedelta(days=5))
    repository.insert_reveal_event(
        {"practice_item_id": item, "learning_object_id": None, "source_kind": "tutor_answer", "amount": 1.0,
         "basis": "tutor_answer"}, clock=FrozenClock(t - timedelta(days=2)),
    )
    _answer_at(t + timedelta(days=5))

    bounded = se.submit_exposure(se.gather(repository, practice_item_id=item, learning_object_id=None,
                                           at=_iso(t), window_until=_iso(t)))
    live = se.submit_exposure(se.gather(repository, practice_item_id=item, learning_object_id=None, at=_iso(t)))

    assert bounded.primed_by_ledger
    assert not live.primed_by_ledger  # the live window starts at the latest attempt


# -- the consistency property: every serve agrees with submit at the same instant ----------------


def _random_inputs(rng: random.Random) -> se.EligibilityInputs:
    base = datetime(2026, 6, 1, tzinfo=UTC)

    def stamp() -> str:
        return _iso(base + timedelta(minutes=rng.randint(0, 6 * 1440)))

    reveals = []
    for index in range(rng.randint(0, 5)):
        routine = rng.random() < 0.5
        on_item = rng.random() < 0.7
        kind = "answer_display" if routine else rng.choice(["tutor_answer", "repair_display", "guided_redo",
                                                            "source_review", "answer_display"])
        reveals.append(se.RevealRow(
            id=f"r{index}", practice_item_id="pi" if on_item else "pi_sibling", learning_object_id="lo",
            source_kind=kind, basis=("feedback_full_answer:desktop:d" if routine else kind),
            amount=rng.choice([0.2, 0.4, 1.0]), created_at=stamp(), attempt_id=None,
        ))
    tasks = []
    for index in range(rng.randint(0, 2)):
        created = base + timedelta(minutes=rng.randint(0, 5 * 1440))
        tasks.append(se.FollowupTask(
            id=f"t{index}", kind=rng.choice(["cold_retry", "certification_cold_probe", "intervention_followup"]),
            created_at=_iso(created), not_before=_iso(created + timedelta(minutes=rng.randint(0, 2 * 1440))),
            expires_at=_iso(created + timedelta(days=30)),
        ))
    tasks.sort(key=lambda task: (task.not_before, task.created_at, task.id))
    last = ("a1", stamp()) if rng.random() < 0.6 else None
    return se.EligibilityInputs(
        practice_item_id="pi", learning_object_id="lo", at=stamp(), reveals=tuple(reveals),
        last_attempt=last, tasks=tuple(tasks),
    )


def _after_retimes(inputs: se.EligibilityInputs, decision: se.EligibilityDecision) -> se.EligibilityInputs:
    from dataclasses import replace

    pushes = dict(decision.retimes)
    tasks = tuple(
        replace(task, not_before=max(task.not_before or "", pushes[task.id])) if task.id in pushes else task
        for task in inputs.tasks
    )
    return replace(inputs, tasks=tuple(sorted(tasks, key=lambda task: (task.not_before, task.created_at, task.id))))


@pytest.mark.parametrize("seed", range(400))
def test_every_serve_agrees_with_submit_at_the_same_instant(seed):
    """For random reveal, task and attempt histories: whatever a serve path
    decides for an item's cold check, an unassisted answer at that instant,
    after the decision's re-times, is admissible; and a serve as the cold
    check is never one submit would prime. A probe or quick-check offer is
    never made on an item submit would prime."""

    rng = random.Random(seed)
    inputs = _random_inputs(rng)
    cold = se.decide(inputs, se.COLD_CHECK)
    submit_after = se.decide(_after_retimes(inputs, cold), se.SUBMIT)
    exposure = se.submit_exposure(inputs)

    assert submit_after.verdict == se.SERVE, (cold.record(), submit_after.record())
    if cold.verdict == se.SERVE and se.active_task(inputs) is not None and se.active_task(inputs).cold:
        assert not exposure.primed_by_ledger
    if cold.verdict == se.SERVE_AS_ORDINARY:
        assert exposure.primed_by_ledger and exposure.lapses_at is None
    if cold.verdict == se.DEFER_UNTIL:
        assert cold.until is not None and cold.until > inputs.at
    for request in (se.PROBE, se.QUICK_CHECK):
        if se.decide(inputs, request).verdict == se.SERVE:
            assert not exposure.primed_by_ledger


@pytest.mark.parametrize("seed", range(8))
def test_submit_exposure_is_the_sql_total_row_for_row(tmp_path, seed):
    """Submit's rule is persisted meaning: the decision's total equals the
    repository's SQL total (``total_reveal_amount`` with submit's arguments)
    on random ledgers, live and bounded."""

    from learnloop.attempts.reveal_ledger import POST_ATTEMPT_REVEAL_KINDS, ROUTINE_ANSWER_DISPLAY_BASES
    from learnloop.reveal_coverage import routine_covered_from
    from tests.test_remediation_cold_retry import _setup

    rng = random.Random(seed)
    vault, repository, _misconception = _setup(tmp_path)
    item = "pi_svd_define_001"
    base = datetime(2026, 6, 1, tzinfo=UTC)
    for index in range(rng.randint(1, 8)):
        moment = base + timedelta(minutes=rng.randint(0, 4 * 1440))
        if rng.random() < 0.3:
            complete_self_graded_attempt(
                vault, repository, AttemptDraft(practice_item_id=item, learner_answer_md=f"x{index}"),
                SelfGradeInput(criterion_points={"correctness": 2}, confidence=3), clock=FrozenClock(moment),
            )
            continue
        routine = rng.random() < 0.5
        repository.insert_reveal_event(
            {"practice_item_id": item, "learning_object_id": "lo_svd_definition",
             "source_kind": "answer_display" if routine else rng.choice(["tutor_answer", "guided_redo"]),
             "amount": rng.choice([0.1, 0.25, 0.4, 1.0]),
             "basis": "feedback_full_answer:desktop:d" if routine else "x"},
            clock=FrozenClock(moment),
        )
    for _probe in range(10):
        at = _iso(base + timedelta(minutes=rng.randint(0, 5 * 1440)))
        bounded = rng.random() < 0.5
        until = at if bounded else None
        attempts = repository.list_recent_attempts_by_practice_item(item, limit=1, until=until)
        sql = repository.total_reveal_amount(
            item, since=attempts[0]["created_at"] if attempts else None, until=until,
            linked_attempt_id=str(attempts[0]["id"]) if attempts else None, linked_kinds=POST_ATTEMPT_REVEAL_KINDS,
            routine_basis_prefixes=ROUTINE_ANSWER_DISPLAY_BASES, routine_covered_from=routine_covered_from(at),
        )
        exposure = se.submit_exposure(se.gather(repository, practice_item_id=item, learning_object_id="lo_svd_definition",
                                                at=at, window_until=until))
        assert exposure.total == pytest.approx(max(sql, 0.0), abs=1e-12)
        assert (exposure.total >= se.AUTO_PRIME_REVEAL_THRESHOLD) == (sql >= se.AUTO_PRIME_REVEAL_THRESHOLD)


@pytest.mark.parametrize("seed", range(5))
def test_the_real_serve_paths_agree_with_submit(tmp_path, seed):
    """The property on a real vault: reveals of every kind at random moments
    around a real cold task, and at random later moments the queue's cold
    lane, the serve-time hold and the session-free open asked. Whenever the
    queue serves the cold retry, submit at that instant is not primed; and an
    unassisted answer after any serve path's decision is never refused."""

    from learnloop.scheduling.scheduler import build_due_queue, cold_check_serve_hold
    from tests.test_remediation_cold_retry import NOW, _drive_to_cold_scheduled, _setup

    rng = random.Random(seed)
    vault, repository, misconception_id = _setup(tmp_path)
    _episode, _primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    lo = vault.practice_items[cold_item].learning_object_id
    events = [("reveal", NOW + timedelta(minutes=rng.randint(-1500, 3000))) for _ in range(rng.randint(1, 4))]
    events += [("serve", NOW + timedelta(minutes=rng.randint(1440, 4400))) for _ in range(6)]
    submitted = False
    for index, (kind, moment) in enumerate(sorted(events, key=lambda event: event[1])):
        clock = FrozenClock(moment)
        if kind == "reveal":
            routine = rng.random() < 0.5
            repository.insert_reveal_event(
                {"practice_item_id": cold_item if rng.random() < 0.8 else "pi_svd_define_002",
                 "learning_object_id": lo,
                 "source_kind": "answer_display" if routine else "tutor_answer", "amount": 1.0,
                 "basis": f"feedback_full_answer:desktop:d{seed}_{index}" if routine else "tutor_answer"},
                clock=clock,
            )
            continue
        if submitted:
            continue
        cold_lane = [item.practice_item_id for item in build_due_queue(vault, repository, clock=clock)
                     if item.followup_kind == "cold_retry"]
        if cold_item in cold_lane:
            draft, _total = auto_primed_draft(
                repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"), clock=clock,
            )
            assert not draft.primed, f"the queue served the cold retry primed at {moment}"
        cold_check_serve_hold(vault, repository, cold_item, clock=clock)
        if rng.random() < 0.3:
            complete_self_graded_attempt(
                vault, repository, AttemptDraft(practice_item_id=cold_item, learner_answer_md="x"),
                SelfGradeInput(criterion_points={"correctness": 2}, confidence=3), clock=clock,
            )
            submitted = True


def test_the_cold_delay_is_the_remediation_delay_and_the_constants_are_one():
    from learnloop.attempts import attempts, reveal_ledger
    from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY

    assert se.COLD_RETRIEVAL_DELAY == COLD_RETRIEVAL_DELAY
    assert attempts.AUTO_PRIME_REVEAL_THRESHOLD is se.AUTO_PRIME_REVEAL_THRESHOLD
    assert attempts.COLD_FOLLOWUP_TASK_KINDS is se.COLD_FOLLOWUP_TASK_KINDS
    assert reveal_ledger.POST_ATTEMPT_REVEAL_KINDS is se.POST_ATTEMPT_REVEAL_KINDS


# -- the other serve paths ask the same decision ---------------------------------------------------


def test_the_tui_open_serves_a_cold_check_submit_would_prime_as_practice(tmp_path):
    """The TUI's open is its serve: a tutor answer shown (after the list was
    built) since the item's last attempt re-times the due cold retry, so the
    answer is an ordinary one, accepted."""

    import asyncio

    from learnloop.db.repositories import Repository
    from learnloop.tui.app import LearnLoopApp
    from learnloop.tui.screens.practice import PracticeScreen
    from tests.helpers import begin_session, create_basic_vault, seed_due_item

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    repository = Repository(paths.sqlite_path)
    now = datetime.now(UTC).replace(microsecond=0)
    task = repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_tui",
        not_before=_iso(now - timedelta(hours=1)), expires_at=_iso(now + timedelta(days=30)),
        selected_item_id="pi_svd_define_001", clock=FrozenClock(now - timedelta(days=1)),
    )

    async def scenario() -> None:
        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            repository.insert_reveal_event({
                "practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
                "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer",
            })
            await today.open_practice()
            await pilot.pause()
            assert isinstance(app.screen, PracticeScreen)
            assert app.screen.item.practice_item_id == "pi_svd_define_001"
            assert repository.active_followup_task_for_item("pi_svd_define_001", kind="cold_retry") is None
            assert repository.followup_task(task["id"])["not_before"] > _iso(datetime.now(UTC) + timedelta(hours=23))

    asyncio.run(scenario())


@pytest.mark.parametrize("revealed", [False, True], ids=["control", "tutor_answer"])
def test_no_probe_is_committed_for_an_item_submit_would_prime(tmp_path, revealed):
    """The probe commit asks the same decision: a tutor answer of a
    never-attempted probe item, at any age (only an attempt absorbs it), means
    a probe of it cannot test the learner, so none is committed."""

    from learnloop.diagnosis.probe_episodes import commit_item_presentation, enter_episode, episode_hypothesis_set
    from tests.test_probe_orchestration_remainder import CLOCK, ITEM_ID, LO_ID, _setup

    _root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    if revealed:
        repository.insert_reveal_event(
            {"practice_item_id": ITEM_ID, "learning_object_id": LO_ID, "source_kind": "tutor_answer",
             "amount": 1.0, "basis": "tutor_answer"},
            clock=FrozenClock(CLOCK.now() - timedelta(days=10)),
        )

    presentation = commit_item_presentation(
        loaded, repository, episode, loaded.practice_items[ITEM_ID], episode_hypothesis_set(repository, episode),
        clock=CLOCK,
    )

    assert (presentation is None) is revealed


def test_a_learners_pick_of_a_cold_check_submit_would_prime_is_served_as_practice(tmp_path):
    """The pick revalidates through the same decision (``revalidate_cold_check``)."""

    from learnloop_sidecar.handlers.queue import revalidate_cold_check

    env, clock, task = _one_cold_item_plan(tmp_path, start=datetime.now(UTC).replace(microsecond=0))
    decision = revalidate_cold_check(env.vault, env.repository, "pi_cold")

    assert decision is not None and decision.verdict == se.SERVE_AS_ORDINARY
    assert env.repository.followup_task(task["id"])["not_before"] > _iso(datetime.now(UTC))
