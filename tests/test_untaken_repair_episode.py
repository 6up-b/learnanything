"""A repair episode whose primed attempt is never taken: what the sweep does with it, and what the routine queue
withholds while it is open."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import (
    SECTION_END_ALGORITHM_VERSION,
    UNTAKEN_EPISODE_END_ALGORITHM_VERSION,
    untaken_episode_end_on,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.diagnosis.machine_checks import sweep_machine_checks
from learnloop.diagnosis.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.scheduling.scheduler import build_due_queue, exclusion_now
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, add_followup_item, create_basic_vault, seed_due_item, set_algorithm_version

LO_ID = "lo_svd_definition"
MISSED_ITEM = "pi_svd_define_001"
#: The episode opens a minute after the miss its diagnosis came from.
OPENED = NOW + timedelta(minutes=1)
#: The tag below which an untaken episode has no end, and the tag that ends it.
BEFORE, AT = SECTION_END_ALGORITHM_VERSION, UNTAKEN_EPISODE_END_ALGORITHM_VERSION


def _world(tmp_path, version: str):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths, version=version)
    add_followup_item(root)
    add_followup_item(root, "pi_svd_define_003")
    set_algorithm_version(paths, version)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix; eigendecomposition needs a square one.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    miss = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=MISSED_ITEM, learner_answer_md="A diagonal matrix.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, fatal_errors=[], confidence=2),
        clock=FrozenClock(NOW),
    )
    return vault, repository, misconception_id, miss.attempt_id


def _diagnose(repository: Repository, misconception_id: str, attempt_id: str) -> None:
    """The error event that ties the miss to the misconception the episode repairs."""

    repository.insert_error_event({
        "attempt_id": attempt_id, "learning_object_id": LO_ID, "error_type": "misconception", "severity": 0.8,
        "is_misconception": True, "created_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "misconception_id": misconception_id,
    })


def _open_episode(vault, repository, misconception_id: str, attempt_id: str, state: str) -> dict:
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(OPENED))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(OPENED))
    if state == "treatment":
        start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(OPENED))
    _diagnose(repository, misconception_id, attempt_id)
    stored = repository.remediation_episode(episode["id"])
    assert stored["state"] == state and stored["primed_attempt_id"] is None
    return stored


def _missed_item_due(repository: Repository) -> datetime:
    """The missed item's next ordinary review, as its own miss scheduled it."""

    due = parse_utc(repository.practice_item_state(MISSED_ITEM).due_at)
    assert due is not None and due > OPENED
    return due


def _sweep(vault, repository, at: datetime) -> None:
    sweep_machine_checks(vault, repository, LO_ID, clock=FrozenClock(at))


def _iso(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def _queued(vault, repository, item_id: str, at: datetime) -> bool:
    return item_id in [item.practice_item_id for item in build_due_queue(vault, repository, clock=FrozenClock(at))]


# -- below the tag: the episode has no end ------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["prescribed", "treatment"])
def test_below_the_tag_an_untaken_episode_stays_open_past_its_items_review(tmp_path, state):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, BEFORE)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, state)
    due = _missed_item_due(repository)
    for at in (due + timedelta(minutes=1), due + timedelta(days=60)):
        _sweep(vault, repository, at)
        stored = repository.remediation_episode(episode["id"])
        assert stored["state"] == state and stored["primed_attempt_id"] is None


def test_below_the_tag_the_routine_queue_serves_an_untaken_episodes_cold_item(tmp_path):
    """Only an open cold retry withholds the cold item from Today's queue; an untaken episode does not, at any
    time, while the learner-initiated selectors' wider set holds it."""

    vault, repository, misconception_id, attempt_id = _world(tmp_path, BEFORE)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    cold_item = str(episode["cold_item_id"])
    assert cold_item and cold_item != MISSED_ITEM
    due = _missed_item_due(repository)
    assert cold_item in repository.open_remediation_cold_item_ids()
    assert cold_item not in repository.pending_remediation_cold_item_ids()
    for at in (OPENED, due + timedelta(minutes=1)):
        _sweep(vault, repository, at)
        assert _queued(vault, repository, cold_item, at)
    assert cold_item in repository.open_remediation_cold_item_ids()


# -- at the tag: the episode ends at its item's next ordinary review -----------------------------------------------


def test_the_tag():
    assert AT == "mvp-0.64"
    for version, on in ((BEFORE, False), (AT, True)):
        assert untaken_episode_end_on(SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=version))) is on
    assert untaken_episode_end_on(SimpleNamespace()) is False


@pytest.mark.parametrize("state", ["prescribed", "treatment"])
def test_at_the_tag_an_untaken_episode_ends_once_its_items_review_is_due(tmp_path, state):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, state)
    due = _missed_item_due(repository)
    _sweep(vault, repository, due - timedelta(minutes=1))
    assert repository.remediation_episode(episode["id"])["state"] == state
    ended_at = due + timedelta(minutes=1)
    _sweep(vault, repository, ended_at)
    stored = repository.remediation_episode(episode["id"])
    assert stored["state"] == "abandoned"
    assert stored["updated_at"] == _iso(ended_at) and stored["completed_at"] is None
    assert stored["primed_attempt_id"] is None and stored["cold_item_id"] == episode["cold_item_id"]
    # Idempotent: a later sweep finds nothing to end and writes nothing.
    _sweep(vault, repository, due + timedelta(days=3))
    assert repository.remediation_episode(episode["id"]) == stored


def test_at_the_tag_the_routine_queue_withholds_the_cold_item_while_the_episode_is_open(tmp_path):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    cold_item = str(episode["cold_item_id"])
    assert cold_item and cold_item != MISSED_ITEM
    due = _missed_item_due(repository)
    for at in (OPENED, due - timedelta(minutes=1)):
        _sweep(vault, repository, at)
        assert not _queued(vault, repository, cold_item, at)
    assert exclusion_now(vault, repository, cold_item) == "cold_check_reserved"
    after = due + timedelta(minutes=1)
    _sweep(vault, repository, after)
    assert repository.remediation_episode(episode["id"])["state"] == "abandoned"
    assert cold_item not in repository.open_remediation_cold_item_ids()
    assert _queued(vault, repository, cold_item, after)


def test_an_ordinary_review_taken_the_moment_it_fell_due_ends_the_episode(tmp_path):
    """The sweep runs after attempts: when the learner's first attempt after the item fell due is that item's own
    review, the review has moved its due date by the time the sweep looks, and the episode still ends."""

    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    due = _missed_item_due(repository)
    review_at = due + timedelta(minutes=1)
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=MISSED_ITEM, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=FrozenClock(review_at),
    )
    assert parse_utc(repository.practice_item_state(MISSED_ITEM).due_at) > review_at
    _sweep(vault, repository, review_at)
    assert repository.remediation_episode(episode["id"])["state"] == "abandoned"


def test_a_primed_answer_on_the_item_is_no_ordinary_review(tmp_path):
    """A primed answer on the item writes no FSRS state, so it is not the item's review and ends nothing."""

    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "prescribed")
    due = _missed_item_due(repository)
    early = OPENED + timedelta(minutes=5)
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=MISSED_ITEM, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt", primed=True),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=FrozenClock(early),
    )
    _sweep(vault, repository, early)
    assert repository.remediation_episode(episode["id"])["state"] == "prescribed"
    assert parse_utc(repository.practice_item_state(MISSED_ITEM).due_at) == due


def test_an_episode_whose_primed_attempt_was_taken_is_untouched(tmp_path):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    due = _missed_item_due(repository)
    primed = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=str(episode["primed_item_id"]), learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt", primed=True),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=FrozenClock(OPENED + timedelta(minutes=2)),
    )
    taken = repository.remediation_episode(episode["id"])
    assert taken["state"] == "cold_scheduled" and taken["primed_attempt_id"] == primed.attempt_id
    _sweep(vault, repository, due + timedelta(days=1))
    assert repository.remediation_episode(episode["id"]) == taken


@pytest.mark.parametrize("state", ["diagnosis", "cold_scheduled", "completed"])
def test_an_episode_in_any_other_state_is_untouched(tmp_path, state):
    vault, repository, misconception_id, attempt_id = _world(tmp_path, AT)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "prescribed")
    repository.update_remediation_episode(episode["id"], state=state, clock=FrozenClock(OPENED))
    before = repository.remediation_episode(episode["id"])
    _sweep(vault, repository, _missed_item_due(repository) + timedelta(days=1))
    assert repository.remediation_episode(episode["id"]) == before


def test_a_diagnosis_case_ends_at_its_hypothesis_attempts_item(tmp_path):
    vault, repository, _misconception_id, attempt_id = _world(tmp_path, AT)
    hypothesis = repository.append_causal_hypothesis(
        episode_key="k94-case", attempt_id=attempt_id, learning_object_id=LO_ID, cause_scope="learner_state",
        statement="Treats SVD as an eigendecomposition.", statement_normalized="treats svd as eigendecomposition",
        clock=FrozenClock(NOW),
    )
    episode = repository.create_remediation_episode(
        case_kind="diagnosis", case_ref=str(hypothesis["id"]), state="prescribed", clock=FrozenClock(OPENED))
    due = _missed_item_due(repository)
    _sweep(vault, repository, due - timedelta(minutes=1))
    assert repository.remediation_episode(episode["id"])["state"] == "prescribed"
    _sweep(vault, repository, due + timedelta(minutes=1))
    assert repository.remediation_episode(episode["id"])["state"] == "abandoned"


def test_an_episode_whose_item_cannot_be_resolved_stays_open(tmp_path):
    """No diagnosing attempt, no date to end it by."""

    vault, repository, _misconception_id, _attempt_id = _world(tmp_path, AT)
    episode = repository.create_remediation_episode(
        case_kind="diagnosis", case_ref="no-such-hypothesis", state="prescribed", clock=FrozenClock(OPENED))
    _sweep(vault, repository, _missed_item_due(repository) + timedelta(days=60))
    assert repository.remediation_episode(episode["id"])["state"] == "prescribed"


def test_an_episode_open_at_the_upgrade_is_ended_by_the_first_sweep_after_it(tmp_path):
    """Future events only: the episode is ended when a sweep at the tag first sees it, dated by that sweep, never
    by the review date that passed below the tag."""

    vault, repository, misconception_id, attempt_id = _world(tmp_path, BEFORE)
    episode = _open_episode(vault, repository, misconception_id, attempt_id, "treatment")
    due = _missed_item_due(repository)
    _sweep(vault, repository, due + timedelta(days=1))
    assert repository.remediation_episode(episode["id"])["state"] == "treatment"
    root = tmp_path / "vault"
    text = (root / "learnloop.toml").read_text(encoding="utf-8")
    (root / "learnloop.toml").write_text(text.replace(f'"{BEFORE}"', f'"{AT}"'), encoding="utf-8")
    upgraded = load_vault(root)
    assert untaken_episode_end_on(upgraded.config)
    first = due + timedelta(days=2)
    _sweep(upgraded, repository, first)
    stored = repository.remediation_episode(episode["id"])
    assert stored["state"] == "abandoned" and stored["updated_at"] == _iso(first)


@pytest.mark.parametrize("uncommitted", [0.90, 0.80])
def test_the_sweeps_due_read_is_the_plans(tmp_path, uncommitted):
    """``ordinary_due_reader`` gives every item the due ``IntentServing.effective`` gives it, at the stored target
    and at a scaled one."""

    from learnloop.scheduling.intent.recall_targets import ordinary_due_reader
    from learnloop.scheduling.intent.serving import intent_serving

    vault, repository, _misconception_id, _attempt_id = _world(tmp_path, AT)
    root = tmp_path / "vault"
    with (root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n[intent.recall_targets]\nkeep_in_touch = 0.8\nmaster_tasks_like_these = 0.92\n"
            f"remember_key_ideas = 0.85\nwork_fluently = 0.9\nuncommitted = {uncommitted}\n"
        )
    vault = load_vault(root)
    later = NOW + timedelta(days=1)
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_define_002", learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=FrozenClock(later),
    )
    view = intent_serving(vault, repository, now=later, force=True)
    read = ordinary_due_reader(vault, repository)
    dues = {}
    for item_id in vault.practice_items:
        state = repository.practice_item_state(item_id)
        dues[item_id] = read(item_id, state)
        assert dues[item_id] == view.effective(item_id, state).due
    assert dues[MISSED_ITEM] is not None and dues["pi_svd_define_002"] is not None
    if uncommitted != 0.90:
        stored = parse_utc(repository.practice_item_state(MISSED_ITEM).due_at)
        assert dues[MISSED_ITEM] != stored  # the scaled arm, not the stored date
