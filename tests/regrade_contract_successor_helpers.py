"""What other test files use from ``tests/test_regrade_contract_successor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import REGRADE_CONTRACT_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.split_live_helpers import split_vault
from tests.held_grade_evidence_helpers import T


VERSION = REGRADE_CONTRACT_ALGORITHM_VERSION
JOINT = "[diagnosis]\nsplit_enabled = false"


def _vault(tmp_path, *, version=VERSION, config=""):
    return split_vault(tmp_path, version=version, config=config)


def _rebuild(vault, repository, days=30):
    return rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=days)))


def _settle(vault, repository, days=30):
    """Rebuild to the fixed point. A rebuild reaches it in one pass after a
    regrade (which replays in its own transaction) and in two after a write
    that does not replay (an adjudication, a label move): replay reads the
    canonical projection as each attempt's prior, so the first pass reads the
    projection the change made stale (shown identical at mvp-0.25 in
    ``test_rebuild_converges_after_an_adjudication_as_it_did_before``)."""

    _rebuild(vault, repository, days)
    _rebuild(vault, repository, days)


def as_graded_before_contracts(repository, attempt_id):
    """Rewrite an attempt's grade as a vault below the canonical state (mvp-0.7)
    wrote it (test construction only): no grading revision, no assessment
    contract and no observation id. Today's attempt step stamps them on every
    vault; checked against the mvp-0.6 attempt step on the code before refactor
    D4 (``docs/reviews/refactor-d4.md``): the same grading rows, ids and stamps
    aside (the contract snapshot it took is left, cited by nothing)."""

    with repository.connection() as connection:
        connection.execute(
            "UPDATE grading_evidence SET grading_revision = NULL, assessment_contract_version_id = NULL, "
            "observation_id = NULL WHERE attempt_id = ?",
            (attempt_id,),
        )
        connection.commit()


def as_regraded_before_contracts(repository, attempt_id, *, supersede_tiers=(1,), grade=None):
    """Rewrite an attempt's latest regrade as a regrade before regrade
    contracts (mvp-0.26) wrote it (test construction only): its rows cite no
    contract and carry no grading revision, and it superseded only the rows
    of ``supersede_tiers`` (an ordinary regrade: the self tier, so the model
    rows it replaced stay live; a regrade of a held, partial or clarified
    grade: tiers 1 and 3). ``grade``: the (score, correctness) the
    predecessor's replay left on the attempt row, where a test reads it.

    No vault that opens is below that tag, so that writer is gone, but a vault
    at the floor still holds the rows it wrote and replay must read them. The
    construction was checked against the predecessor's own writer on the code
    before refactor D4 (``docs/reviews/refactor-d4.md``): the same grading
    rows, ids and stamps aside."""

    rows = repository.fetch_grading_evidence(attempt_id, include_superseded=True)
    latest = max(row.grading_revision for row in rows if row.grading_revision is not None)
    new_ids = [row.id for row in rows if row.grading_revision == latest]
    marks = ",".join("?" for _ in new_ids)
    tiers = ",".join("?" for _ in supersede_tiers)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE grading_evidence SET superseded_at = NULL, superseded_by_evidence_id = NULL "
            f"WHERE attempt_id = ? AND superseded_by_evidence_id IN ({marks}) AND grader_tier NOT IN ({tiers})",
            (attempt_id, *new_ids, *supersede_tiers),
        )
        connection.execute(
            "UPDATE grading_evidence SET grading_revision = NULL, assessment_contract_version_id = NULL "
            f"WHERE id IN ({marks})",
            new_ids,
        )
        if grade is not None:
            connection.execute(
                "UPDATE practice_attempts SET rubric_score = ?, correctness = ? WHERE id = ?", (*grade, attempt_id)
            )
        connection.commit()
