"""What other test files use from ``tests/test_cold_retry_reschedule.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import timedelta

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item
from tests.remediation_cold_retry_helpers import _drive_to_cold_scheduled, _setup
from tests.ux_phase1_support import set_config


TAG = LATEST_ALGORITHM_VERSION
THIRD_ITEM = "pi_svd_define_003"
LO_ITEMS = {"pi_svd_define_001", "pi_svd_define_002", THIRD_ITEM}


def _repair(tmp_path, *, version=TAG, switch: bool | None = None, converts: bool = True, third: bool = True):
    """A repair episode at ``cold_scheduled`` with a third item for a fresh surface."""

    vault, repository, misconception_id = _setup(tmp_path)
    if third:
        add_followup_item(vault.root, THIRD_ITEM)
    updates = {("algorithms", "algorithm_version"): version, ("ask", "cold_help_converts"): converts}
    if switch is not None:
        updates[("practice", "reschedule_cold_after_assist")] = switch
    set_config(vault.root, updates)
    vault = load_vault(vault.root)
    episode, primed, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    return vault, repository, episode, primed, cold_item


def _spare(repository, episode) -> str:
    """The repair's one item on neither surface it already used (primed, cold)."""

    used = {str(episode["primed_item_id"]), str(episode["cold_item_id"])}
    [spare] = LO_ITEMS - used
    return spare


def _answer(vault, repository, item_id, moment, *, hints: int = 0):
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt", hints_used=hints),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(moment),
    )


def _tasks(repository, episode_id):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id FROM followup_tasks WHERE kind = 'cold_retry' AND remediation_episode_id = ? "
            "ORDER BY created_at, id", (episode_id,)).fetchall()
    return [repository.followup_task(str(row["id"])) for row in rows]


def _table(repository, sql):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql)]


ASSISTED_AT = NOW + timedelta(days=1, hours=1)
