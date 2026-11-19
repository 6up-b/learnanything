"""The evidence reading fixes, mvp-0.61 (refactor bug ledger G3-1, ER-2, K5-3, K5-11, K5-12;
``docs/reviews/algorithm-mvp-0.61.md``).

Each fix is on at mvp-0.61 and later and exactly mvp-0.60's below it, and each has a test that runs the same stored
history at both tags: the mvp-0.61 arm is the fix (it failed before the fix), the mvp-0.60 arm pins today's result.
ER-2's pair is in ``tests/test_causal_trace_consistency_p2.py`` beside the strict xfail it replaces. The upgrade test
at the end builds one vault holding every case at mvp-0.60, upgrades it and rebuilds it again. Fakes only; no model
call.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.ai.runtime import AIRuntimeReport
from learnloop.algorithm_versions import (
    EVIDENCE_READING_FIX_ALGORITHM_VERSION,
    GRADE_CHANNEL_FIX_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    evidence_reading_fixes_on,
)
from learnloop.attempts.ai_contracts import CriterionEvidence, GradingContext, GradingProposal
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.structured_ai import JointGraderAlsoBlind, StructuredClientFake

TAG = EVIDENCE_READING_FIX_ALGORITHM_VERSION
BELOW = GRADE_CHANNEL_FIX_ALGORITHM_VERSION
BOTH_TAGS = pytest.mark.parametrize("tag", [BELOW, TAG])
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def test_the_successor_is_one_constant_after_the_grade_channel_fixes():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == BELOW == "mvp-0.60"
    assert TAG == "mvp-0.61" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert not evidence_reading_fixes_on(_Config(BELOW)) and evidence_reading_fixes_on(_Config(TAG))


class _Config:
    def __init__(self, tag):
        self.algorithms = type("Algorithms", (), {"algorithm_version": tag})()


def _vault(tmp_path, tag, name="vault"):
    paths = create_basic_vault(tmp_path / name)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _rows(paths, sql, *args):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, args).fetchall()]


def _rebuild(paths):
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, Repository(paths.sqlite_path), clock=FrozenClock(NOW + timedelta(days=1)))


class _Grader(JointGraderAlsoBlind, StructuredClientFake):
    """A model grader that answers ``points`` on ``correctness`` with ``confidence``."""

    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"

    def __init__(self, *, points: float, confidence: float = 0.9):
        self.points = points
        self.confidence = confidence

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=int(self.points),
            criterion_evidence=[
                CriterionEvidence(criterion_id="correctness", points_awarded=self.points, evidence="Graded.")
            ],
            grader_confidence=self.confidence,
        )


def _ready_runtime() -> AIRuntimeReport:
    return AIRuntimeReport(status="ready", active_provider="deepseek_flash", provider_type="openai_chat",
                           model="deepseek-v4-flash")


def _model_graded(vault, repository, *, points, confidence, clock=CLOCK):
    return complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="SVD factors a matrix as U Sigma V transpose."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        runtime=_ready_runtime(), ai_client=_Grader(points=points, confidence=confidence), clock=clock,
    )


def _raw_events(paths, attempt_id):
    return _rows(paths, "SELECT grader_provider, model_confidence, raw_output_json FROM raw_grade_events "
                        "WHERE attempt_id = ? ORDER BY created_at, id", attempt_id)


# -- K5-12: a grader confidence of 0.0 is legal and stays 0.0 on replay -------------------------------------------


@BOTH_TAGS
def test_k5_12_a_zero_confidence_survives_a_rebuild(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, tag)
    result = _model_graded(vault, repository, points=4, confidence=0.0)
    attempt_id = result.attempt_id
    assert repository.fetch_practice_attempt(attempt_id)["grader_confidence"] == 0.0
    assert [row["model_confidence"] for row in _raw_events(paths, attempt_id)] == [0.0]

    _rebuild(paths)
    _rebuild(paths)

    stored = repository.fetch_practice_attempt(attempt_id)["grader_confidence"]
    confidences = [row["model_confidence"] for row in _raw_events(paths, attempt_id)]
    if tag == TAG:
        # The live grade's 0.0 is what replay reads: nothing to append, so the grade channel is the live one.
        assert stored == 0.0
        assert confidences == [0.0]
    else:
        # mvp-0.60, today: replay read 0.0 as missing and wrote 1.0 back to the attempt; its first rebuild took the
        # changed confidence for a regrade and appended a raw grade event at 1.0 (ledger K5-12).
        assert stored == 1.0
        assert confidences == [0.0, 1.0]


@BOTH_TAGS
def test_k5_12_a_missing_confidence_still_reads_as_full(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, tag)
    result = _model_graded(vault, repository, points=4, confidence=0.7)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET grader_confidence = NULL WHERE id = ?", (result.attempt_id,))
        connection.commit()

    _rebuild(paths)

    # A legacy NULL is the one value replay fills, at both tags.
    assert repository.fetch_practice_attempt(result.attempt_id)["grader_confidence"] == 1.0
